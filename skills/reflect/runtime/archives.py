"""Explicit legacy import and consistent private SQLite exports/restores."""
import base64
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import sqlite3
import uuid

from jsonschema.exceptions import ValidationError

from collector import _write_json
from evaluation import private_directory
from records import RecordStore, RecordError, original, digest, encoded
from reviews import Reviews, VALIDATOR

TABLES = {"metadata", "originals", "versions", "review_versions", "comparison_plans", "review_evidence", "delivery_plans", "delivery_events", "legacy_artifacts", "legacy_sources", "restorations"}
CACHES = {"derived_work", "observation_vectors", "observation_fts", "observation_fts_data", "observation_fts_idx", "observation_fts_content", "observation_fts_docsize", "observation_fts_config"}


def legacy_schema(db):
    db.execute("CREATE TABLE IF NOT EXISTS legacy_artifacts(kind TEXT NOT NULL,raw_sha256 TEXT NOT NULL,raw BLOB NOT NULL,canonical_id TEXT NOT NULL,PRIMARY KEY(kind,raw_sha256)) STRICT")
    db.execute("CREATE TABLE IF NOT EXISTS legacy_sources(kind TEXT NOT NULL,source TEXT NOT NULL,raw_sha256 TEXT NOT NULL,canonical_id TEXT NOT NULL,PRIMARY KEY(kind,source,raw_sha256)) STRICT")


def import_legacy(records, entries, *, after_each=None):
    prepared = []
    for kind, filename in entries:
        path = Path(filename).absolute()
        if path.is_symlink() or not path.is_file() or kind not in ("observation", "review"):
            raise RecordError("invalid-legacy-source")
        raw = path.read_bytes()
        if len(raw) > 4 * 1024 * 1024:
            raise RecordError("legacy-source-too-large")
        try:
            value = original(raw) if kind == "observation" else json.loads(raw)
            if kind == "review":
                VALIDATOR.validate(value)
        except (ValueError, ValidationError):
            raise RecordError("invalid-legacy-source") from None
        prepared.append((kind, str(path), raw, value, digest(raw)))
    created, reviews_created = 0, 0
    with records._transaction() as db:
        legacy_schema(db)
        Reviews._schema(db)
        for kind, source, raw, value, sha in prepared:
            identity = value["id"]
            if kind == "observation":
                previous = db.execute("SELECT raw FROM originals WHERE id=?", (identity,)).fetchone()
                if previous:
                    if json.loads(previous[0]) != value:
                        raise RecordError("legacy-observation-identity-conflict")
                else:
                    records._capture(db, "legacy-observation:" + sha, raw, {"origin": [{"references": [source]}]})
                    created += 1
            else:
                previous = db.execute("SELECT payload FROM review_versions WHERE review_id=? ORDER BY revision DESC LIMIT 1", (identity,)).fetchone()
                if previous and json.loads(previous[0])["record"] != value:
                    raise RecordError("legacy-review-identity-conflict")
                if not previous:
                    items = value["opportunities"]
                    pending = next((v["id"] for v in items if v["decision"]["status"] == "pending"), None)
                    options = {"active_question": pending, "decision_domains": {v["id"]: "unknown" for v in items}, "dependencies": {v["id"]: [s["reference"] for s in value["sources"]] for v in items},
                               "decision_sources": {v["id"]: f'legacy:{sha}#/opportunities/{index}/decision' for index, v in enumerate(items) if v["decision"]["status"] != "pending"}, "artifacts": [], "request": None}
                    payload = {"schema_version": 1, "project": records.project, "record": value, "options": options, "context": {"observations": [], "limits": ["Historical context not reconstructed during import."]}, "source_changes": [],
                               "legacy": {"source": source, "raw_sha256": sha, "author": None, "request_source": None, "domain_assignment": "unknown", "artifact_coverage": "not-imported"}}
                    body = encoded(payload).decode()
                    db.execute("INSERT INTO review_versions VALUES(?,?,?,?,?,?)", (identity, 1, "legacy-review:" + sha, body, digest(body.encode()), datetime.now(timezone.utc).isoformat()))
                    reviews_created += 1
            db.execute("INSERT OR IGNORE INTO legacy_artifacts VALUES(?,?,?,?)", (kind, sha, raw, identity))
            db.execute("INSERT OR IGNORE INTO legacy_sources VALUES(?,?,?,?)", (kind, source, sha, identity))
            if after_each:
                after_each(identity)
    return {"status": "imported", "observations_created": created, "reviews_created": reviews_created, "sources": len(prepared), "recurrence": "not-inferred", "next": "return-to-task"}


def pack(value):
    return {"base64": base64.b64encode(value).decode()} if isinstance(value, bytes) else value


def snapshot(db):
    names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    unknown = {name for name in names - TABLES - CACHES if not name.startswith("sqlite_")}
    if unknown:
        raise RecordError("unsupported-record-tables")
    data = {name: sorted([{key: pack(value) for key, value in dict(row).items()} for row in db.execute('SELECT * FROM "' + name + '"')], key=encoded) for name in sorted(names & TABLES) if name != "restorations"}
    return {"sha256": digest(encoded(data)), "originals": [{"id": row["id"], "raw_sha256": row["raw_sha256"]} for row in db.execute("SELECT id,raw_sha256 FROM originals ORDER BY id")], "tables": data}


def fsync_file(path):
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Archives:
    def __init__(self, records):
        self.records = records

    def export(self, destination, *, progress=None):
        destination = Path(destination).absolute()
        if destination.exists() or destination.is_symlink():
            raise RecordError("archive-destination-exists")
        destination.mkdir(parents=True, mode=0o700)
        identity = uuid.uuid4().hex
        manifest = {"schema_version": 1, "id": identity, "status": "in-progress", "project": self.records.project, "created_at": datetime.now(timezone.utc).isoformat()}
        _write_json(destination / "manifest.json", manifest)
        partial = destination / "records.sqlite3.partial"
        fd = os.open(partial, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600); os.close(fd)
        target = sqlite3.connect(partial)
        try:
            with self.records._connection() as source:
                source.execute("BEGIN")
                declared = snapshot(source)
                source.backup(target, pages=32, progress=progress, sleep=.01)
            target.execute("PRAGMA journal_mode=DELETE")
        finally:
            target.close()
        fsync_file(partial)
        database = destination / "records.sqlite3"
        os.rename(partial, database)
        exported = RecordStore(database, self.records.project)
        with exported._connection() as db:
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchone():
                raise RecordError("archive-integrity-failed")
            actual = snapshot(db)
            if actual != declared:
                raise RecordError("archive-snapshot-mismatch")
            versions = [dict(v, payload=json.loads(v["payload"])) for v in db.execute("SELECT * FROM versions ORDER BY kind,record_id,revision")]
            reviews = [dict(v, payload=json.loads(v["payload"])) for v in db.execute("SELECT * FROM review_versions ORDER BY review_id,revision")] if "review_versions" in actual["tables"] else []
        readable = {"schema_version": 1, "project": self.records.project, "observations": exported.list(), "versions": versions, "reviews": reviews, "component_tables": actual["tables"], "authority": "SQLite backup is authoritative; this file is a checked readable export, not a writable second store."}
        _write_json(destination / "records.json", readable)
        manifest.update({"status": "ready", "authoritative_sha256": actual["sha256"], "confirmed_originals": actual["originals"], "files": {name: digest((destination / name).read_bytes()) for name in ("records.sqlite3", "records.json")}})
        sync_directory(destination)
        _write_json(destination / "manifest.json", manifest)
        sync_directory(destination)
        return manifest

    def inspect(self, source):
        source = Path(source).resolve(strict=True)
        if (source / "manifest.json").is_symlink():
            raise RecordError("unsafe-archive-manifest")
        try:
            manifest = json.loads((source / "manifest.json").read_text())
        except (ValueError, OSError):
            return {"status": "incomplete", "reason": "manifest-unavailable"}
        if not isinstance(manifest, dict):
            raise RecordError("invalid-archive-manifest")
        if manifest.get("schema_version") != 1 or manifest.get("status") != "ready":
            return {"status": "incomplete", "reason": "archive-not-ready", "id": manifest.get("id")}
        if set(manifest) != {"schema_version", "id", "status", "project", "created_at", "authoritative_sha256", "confirmed_originals", "files"} or not isinstance(manifest["files"], dict) or not isinstance(manifest["confirmed_originals"], list) or not isinstance(manifest["id"], str) or not re.fullmatch(r'[0-9a-f]{32}', manifest["id"]):
            raise RecordError("invalid-archive-manifest")
        if manifest["project"] != self.records.project:
            raise RecordError("project-mismatch")
        if set(manifest["files"]) != {"records.sqlite3", "records.json"} or any((source / name).is_symlink() or digest((source / name).read_bytes()) != sha for name, sha in manifest["files"].items()):
            raise RecordError("archive-content-changed")
        archived = RecordStore(source / "records.sqlite3", self.records.project)
        with archived._connection() as db:
            current = snapshot(db)
            if current["sha256"] != manifest["authoritative_sha256"] or current["originals"] != manifest["confirmed_originals"] or db.execute("PRAGMA quick_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchone():
                raise RecordError("archive-integrity-failed")
        return manifest

    def restore(self, source, destination, *, progress=None):
        manifest = self.inspect(source)
        if manifest["status"] != "ready":
            raise RecordError("archive-not-ready")
        destination = Path(destination).absolute()
        if destination.exists() or destination.is_symlink():
            raise RecordError("restore-destination-exists")
        private_directory(destination.parent)
        staging = destination.with_name("." + destination.name + "." + uuid.uuid4().hex + ".partial")
        with staging.open("xb") as output:
            staging.chmod(0o600)
            with (Path(source) / "records.sqlite3").open("rb") as input_file:
                while block := input_file.read(1024 * 1024):
                    output.write(block)
            output.flush(); os.fsync(output.fileno())
        if digest(staging.read_bytes()) != manifest["files"]["records.sqlite3"]:
            raise RecordError("archive-content-changed")
        restored = RecordStore(staging, self.records.project)
        restored.initialize()
        from search import SearchIndex
        SearchIndex(restored).reset_vectors()
        SearchIndex(restored).rebuild_text()
        with restored._transaction() as db:
            if snapshot(db)["sha256"] != manifest["authoritative_sha256"]:
                raise RecordError("restore-history-mismatch")
            db.execute("CREATE TABLE IF NOT EXISTS restorations(id TEXT PRIMARY KEY,payload TEXT NOT NULL) STRICT")
            db.execute("INSERT INTO restorations VALUES(?,?)", (uuid.uuid4().hex, encoded({"archive_id": manifest["id"], "source_sha256": manifest["authoritative_sha256"], "restored_at": datetime.now(timezone.utc).isoformat(), "actor": None}).decode()))
        with restored._connection(write=True) as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        fsync_file(staging)
        if progress:
            progress("staged")
        try:
            os.link(staging, destination)
        except FileExistsError:
            raise RecordError("restore-destination-exists") from None
        staging.unlink()
        sync_directory(destination.parent)
        if progress:
            progress("published")
        return {"status": "restored", "database": str(destination), "archive_id": manifest["id"], "confirmed_originals": manifest["confirmed_originals"], "vector_index": "pending", "text_index": "rebuilt"}

    def restored_status(self):
        with self.records._connection() as db:
            values = [json.loads(row[0]) for row in db.execute("SELECT payload FROM restorations ORDER BY rowid")] if db.execute("SELECT 1 FROM sqlite_master WHERE name='restorations'").fetchone() else []
        return {"project": self.records.project, "database": str(self.records.path), "restorations": values}
