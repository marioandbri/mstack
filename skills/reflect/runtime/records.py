"""Durable, project-scoped observation originals. Derived work is separate."""
from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from derived_work import states

SCHEMA_VERSION = 1
APPLICATION_ID = 0x4D53544B
OBSERVATION = Draft202012Validator(json.loads((Path(__file__).parent.parent / "observation.schema.json").read_text()))
IDENTITY_FIELDS = ("harness", "harness_version", "session_id", "event_id", "turn_id", "timestamp")


class RecordError(Exception):
    """A stable error code that never includes raw evidence or credentials."""


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def provenance(value=None):
    value = {} if value is None else value
    if not isinstance(value, dict) or set(value) - {"schema_version", "origin", "capture"}:
        raise RecordError("invalid-provenance")
    if type(value.get("schema_version", 1)) is not int or value.get("schema_version", 1) != 1:
        raise RecordError("invalid-provenance")

    def identity(item):
        if not isinstance(item, dict) or set(item) - set(IDENTITY_FIELDS) - {"references"}:
            raise RecordError("invalid-provenance")
        if any(v is not None and (not isinstance(v, str) or not v.strip()) for k, v in item.items() if k != "references"):
            raise RecordError("invalid-provenance")
        refs = item.get("references", [])
        if not isinstance(refs, list) or any(not isinstance(v, str) or not v.strip() for v in refs):
            raise RecordError("invalid-provenance")
        return {**{key: item.get(key) for key in IDENTITY_FIELDS}, "references": refs}

    origins = value.get("origin", [{}])
    if not isinstance(origins, list) or not origins:
        raise RecordError("invalid-provenance")
    return {"schema_version": 1, "origin": [identity(v) for v in origins], "capture": identity(value.get("capture", {}))}


def original(raw):
    if not isinstance(raw, bytes) or len(raw) > 4 * 1024 * 1024:
        raise RecordError("invalid-original")
    try:
        value = json.loads(raw)
        OBSERVATION.validate(value)
        encoded(value)
    except (ValueError, TypeError, UnicodeError, ValidationError):
        raise RecordError("invalid-original") from None
    return value


class RecordStore:
    def __init__(self, path, project):
        candidate = Path(path).absolute()
        if candidate.is_symlink():
            raise RecordError("unsafe-database")
        self.path = candidate.parent.resolve() / candidate.name
        if not isinstance(project, str) or not project.strip():
            raise RecordError("missing-project")
        self.project = project

    def _check_file(self):
        try:
            info = self.path.lstat()
        except FileNotFoundError:
            raise RecordError("not-initialized") from None
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise RecordError("unsafe-database")

    @contextmanager
    def _connection(self, write=False, initialized=True):
        self._check_file()
        db = sqlite3.connect(self.path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True, isolation_level=None, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA busy_timeout=5000")
            if write:
                db.execute("PRAGMA synchronous=FULL")
            if initialized:
                if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                    raise RecordError("unsupported-database")
                row = db.execute("SELECT value FROM metadata WHERE key='project'").fetchone()
                if row is None or row[0] != self.project:
                    raise RecordError("project-mismatch")
            yield db
        except sqlite3.Error:
            raise RecordError("database-unavailable") from None
        finally:
            db.close()

    @contextmanager
    def _transaction(self):
        with self._connection(write=True) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        parent = self.path.parent.stat()
        if parent.st_uid != os.getuid() or parent.st_mode & 0o022:
            raise RecordError("unsafe-database-directory")
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        except FileExistsError:
            pass
        with self._connection(write=True, initialized=False) as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                app = db.execute("PRAGMA application_id").fetchone()[0]
                version = db.execute("PRAGMA user_version").fetchone()[0]
                tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                if app not in (0, APPLICATION_ID) or version not in (0, SCHEMA_VERSION) or (app == 0 and tables):
                    raise RecordError("unsupported-database")
                db.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT")
                db.execute("INSERT OR IGNORE INTO metadata VALUES('project',?)", (self.project,))
                if db.execute("SELECT value FROM metadata WHERE key='project'").fetchone()[0] != self.project:
                    raise RecordError("project-mismatch")
                db.execute("""CREATE TABLE IF NOT EXISTS originals(
                    id TEXT PRIMARY KEY, operation_id TEXT NOT NULL UNIQUE, scope TEXT NOT NULL,
                    raw BLOB NOT NULL, raw_sha256 TEXT NOT NULL, provenance TEXT NOT NULL,
                    identity_sha256 TEXT NOT NULL, captured_at TEXT NOT NULL) STRICT""")
                db.execute("CREATE INDEX IF NOT EXISTS originals_scope ON originals(scope)")
                db.execute("""CREATE TABLE IF NOT EXISTS versions(
                    kind TEXT NOT NULL, record_id TEXT NOT NULL REFERENCES originals(id),
                    revision INTEGER NOT NULL CHECK(revision>0), operation_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(kind, record_id, revision)) STRICT""")
                db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                db.commit()
            except BaseException:
                db.rollback()
                raise
            if db.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
                db.execute("PRAGMA journal_mode=WAL")

    def _capture(self, db, operation_id, raw, origin):
        if not isinstance(operation_id, str) or not operation_id.strip():
            raise RecordError("missing-operation")
        value = original(raw)
        origin = provenance(origin)
        identity_sha = digest(encoded({"raw_sha256": digest(raw), "provenance": origin}))
        previous = db.execute("SELECT id,identity_sha256 FROM originals WHERE operation_id=?", (operation_id,)).fetchone()
        if previous:
            if previous["identity_sha256"] != identity_sha:
                raise RecordError("operation-conflict")
            return {"status": "already-captured", "id": previous["id"]}
        if db.execute("SELECT 1 FROM originals WHERE id=?", (value["id"],)).fetchone():
            raise RecordError("identity-conflict")
        db.execute("INSERT INTO originals VALUES(?,?,?,?,?,?,?,?)", (value["id"], operation_id, value["scope"], raw, digest(raw), encoded(origin).decode(), identity_sha, datetime.now(timezone.utc).isoformat()))
        return {"status": "captured", "id": value["id"]}

    def capture(self, operation_id, raw, origin=None):
        with self._transaction() as db:
            return self._capture(db, operation_id, raw, origin)

    def capture_many(self, observations):
        """Atomically capture an iterable of operation, raw bytes and provenance triples."""
        with self._transaction() as db:
            return [self._capture(db, *item) for item in observations]

    def _view(self, db, row):
        kinds = {v[0] for v in db.execute("SELECT DISTINCT kind FROM versions WHERE record_id=?", (row["id"],))}
        work = states(db, row["id"])
        if "embedding" in kinds:
            cache = db.execute("SELECT 1 FROM sqlite_master WHERE name='observation_vectors'").fetchone()
            if not cache or not db.execute("SELECT 1 FROM observation_vectors WHERE record_id=? AND raw_sha256=?", (row["id"], row["raw_sha256"])).fetchone():
                kinds.discard("embedding")
        state = db.execute("SELECT revision,payload FROM versions WHERE kind='state' AND record_id=? ORDER BY revision DESC LIMIT 1", (row["id"],)).fetchone()
        return {"id": row["id"], "project": self.project, "scope": row["scope"], "observation": json.loads(row["raw"]), "raw_base64": base64.b64encode(row["raw"]).decode(), "raw_sha256": row["raw_sha256"], "provenance": json.loads(row["provenance"]), "captured_at": row["captured_at"], "revision": state["revision"] if state else 0, "state": json.loads(state["payload"])["state"] if state else "inbox", "pending": [label for label, kind in (("classification", "annotation"), ("reconstruction", "summary"), ("indexing", "embedding")) if kind not in kinds or work.get(kind, {}).get("status") == "pending"]}

    def get(self, identity):
        with self._connection() as db:
            row = db.execute("SELECT * FROM originals WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise RecordError("not-found")
            return self._view(db, row)

    def list(self, scope=None, state=None):
        with self._connection() as db:
            rows = db.execute("SELECT * FROM originals WHERE ? IS NULL OR scope=? ORDER BY id", (scope, scope)).fetchall()
            values = [self._view(db, row) for row in rows]
            return values if state is None else [value for value in values if value["state"] == state]

    def _append(self, db, kind, identity, expected_revision, payload, operation_id):
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 0:
            raise RecordError("invalid-revision")
        if not isinstance(operation_id, str) or not operation_id.strip():
            raise RecordError("missing-operation")
        body = encoded(payload)
        previous = db.execute("SELECT * FROM versions WHERE operation_id=?", (operation_id,)).fetchone()
        if previous:
            if (previous["kind"] != kind or previous["record_id"] != identity or
                    previous["revision"] != expected_revision + 1 or previous["payload_sha256"] != digest(body)):
                raise RecordError("operation-conflict")
            return {"status": "already-saved", "revision": previous["revision"]}
        if not db.execute("SELECT 1 FROM originals WHERE id=?", (identity,)).fetchone():
            raise RecordError("not-found")
        revision = db.execute("SELECT COALESCE(MAX(revision),0) FROM versions WHERE kind=? AND record_id=?", (kind, identity)).fetchone()[0]
        if revision != expected_revision:
            raise RecordError("revision-conflict")
        db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?)", (kind, identity, revision + 1, operation_id, body.decode(), digest(body), datetime.now(timezone.utc).isoformat()))
        return {"status": "saved", "revision": revision + 1}

    def transition(self, identity, expected_revision, state, evidence, operation_id):
        if state not in ("inbox", "reviewing", "resolved", "deferred", "discarded"):
            raise RecordError("invalid-state")
        if (not isinstance(evidence, dict) or set(evidence) != {"answer", "source"} or
                any(not isinstance(v, str) or not v.strip() for v in evidence.values())):
            raise RecordError("missing-user-evidence")
        with self._transaction() as db:
            return self._append(db, "state", identity, expected_revision, {"state": state, "evidence": evidence}, operation_id)

    def history(self, identity, kind):
        with self._connection() as db:
            if not db.execute("SELECT 1 FROM originals WHERE id=?", (identity,)).fetchone():
                raise RecordError("not-found")
            return [{"revision": row["revision"], "payload": json.loads(row["payload"]), "operation_id": row["operation_id"], "sha256": row["payload_sha256"], "created_at": row["created_at"]} for row in db.execute("SELECT * FROM versions WHERE record_id=? AND kind=? ORDER BY revision", (identity, kind))]
