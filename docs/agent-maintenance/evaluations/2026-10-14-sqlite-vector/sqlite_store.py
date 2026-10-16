"""Experimental SQLite capture/query adapter, never installed into active skills."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import struct


FIELDS = (
    "id", "operation_id", "project", "harness", "source_session", "capture_session",
    "event_id", "text", "content_sha256", "revision", "decision", "vector",
)


def encode(vector):
    return None if vector is None else struct.pack(f"<{len(vector)}f", *vector)


def decode(row):
    result = {key: row[key] for key in FIELDS}
    vector = result["vector"]
    if vector is not None:
        result["vector"] = list(struct.unpack(f"<{len(vector) // 4}f", vector))
    return result


class SqliteStore:
    def __init__(self, path, vectors=True):
        self.path = Path(path)
        self.vectors = vectors

    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA busy_timeout=5000")
        if self.vectors:
            import sqlite_vec
            db.enable_load_extension(True)
            try:
                sqlite_vec.load(db)
            finally:
                db.enable_load_extension(False)
        return db

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = self.connect()
        try:
            assert db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
            db.executescript("""
                CREATE TABLE observations (
                    id TEXT NOT NULL UNIQUE,
                    operation_id TEXT NOT NULL UNIQUE,
                    project TEXT NOT NULL,
                    harness TEXT NOT NULL,
                    source_session TEXT NOT NULL,
                    capture_session TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 0),
                    decision TEXT NOT NULL,
                    vector BLOB
                ) STRICT;
                CREATE INDEX observations_project ON observations(project);
                CREATE VIRTUAL TABLE observations_fts USING fts5(
                    text, content='observations', content_rowid='rowid'
                );
                CREATE TRIGGER observations_fts_insert AFTER INSERT ON observations BEGIN
                    INSERT INTO observations_fts(rowid, text) VALUES(new.rowid, new.text);
                END;
            """)
            db.execute("CREATE VIRTUAL TABLE observations_vec USING vec0(vector float[3], project text)")
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _insert(self, db, original):
        values = [original[key] if key != "vector" else encode(original[key]) for key in FIELDS]
        try:
            inserted = db.execute(
                f"INSERT INTO observations({','.join(FIELDS)}) VALUES({','.join('?' for _ in FIELDS)}) "
                "ON CONFLICT(operation_id) DO NOTHING RETURNING rowid",
                values,
            ).fetchone()
        except sqlite3.IntegrityError:
            if db.execute("SELECT 1 FROM observations WHERE id=?", (original["id"],)).fetchone():
                return {"status": "identity-conflict", "id": original["id"]}
            raise
        if inserted is None:
            previous = decode(db.execute(
                "SELECT * FROM observations WHERE operation_id=?", (original["operation_id"],),
            ).fetchone())
            immutable = set(FIELDS) - {"revision", "decision", "vector"}
            same = all(previous[key] == original[key] for key in immutable)
            return {"status": "already-captured" if same else "operation-conflict", "id": original["id"]}
        if original["vector"] is not None:
            db.execute(
                "INSERT INTO observations_vec(rowid,vector,project) VALUES(?,?,?)",
                (inserted[0], encode(original["vector"]), original["project"]),
            )
        return {"status": "acknowledged", "id": original["id"]}

    def capture(self, original):
        with self.transaction() as db:
            return self._insert(db, original)

    def capture_batch(self, originals):
        with self.transaction() as db:
            return [self._insert(db, original) for original in originals]

    def decide(self, identity, expected_revision, decision):
        with self.transaction() as db:
            result = db.execute(
                "UPDATE observations SET decision=?, revision=? WHERE id=? AND revision=?",
                (decision, expected_revision + 1, identity, expected_revision),
            )
            return {"status": "accepted" if result.rowcount == 1 else "conflict", "rows_updated": result.rowcount}

    def rows(self):
        db = self.connect()
        try:
            return [decode(row) for row in db.execute("SELECT * FROM observations ORDER BY rowid")]
        finally:
            db.close()

    def attach_embedding(self, identity, vector):
        with self.transaction() as db:
            original = db.execute("SELECT rowid,project FROM observations WHERE id=?", (identity,)).fetchone()
            if original is None:
                raise KeyError(identity)
            blob = encode(vector)
            db.execute("UPDATE observations SET vector=? WHERE rowid=?", (blob, original["rowid"]))
            db.execute("DELETE FROM observations_vec WHERE rowid=?", (original["rowid"],))
            db.execute(
                "INSERT INTO observations_vec(rowid,vector,project) VALUES(?,?,?)",
                (original["rowid"], blob, original["project"]),
            )

    def vector_search(self, vector, project, limit=10):
        db = self.connect()
        try:
            return [dict(row) for row in db.execute("""
                SELECT o.id,v.distance FROM observations_vec v
                JOIN observations o ON o.rowid=v.rowid
                WHERE v.vector MATCH ? AND v.k=? AND v.project=?
                ORDER BY v.distance,o.id
            """, (encode(vector), limit, project))]
        finally:
            db.close()

    def text_search(self, query, project, limit=10):
        db = self.connect()
        try:
            return [dict(row) for row in db.execute("""
                SELECT o.id,bm25(observations_fts) AS score FROM observations_fts
                JOIN observations o ON o.rowid=observations_fts.rowid
                WHERE observations_fts MATCH ? AND o.project=?
                ORDER BY score,o.id LIMIT ?
            """, (query, project, limit))]
        finally:
            db.close()

    def hybrid_search(self, vector, query, project, limit=10):
        # RRF is adapter behavior, not a built-in sqlite-vec capability.
        ranks = {}
        for results in (self.vector_search(vector, project, limit), self.text_search(query, project, limit)):
            for rank, result in enumerate(results, start=1):
                ranks[result["id"]] = ranks.get(result["id"], 0.0) + 1.0 / (60 + rank)
        return [{"id": identity, "score": score} for identity, score in sorted(ranks.items(), key=lambda x: (-x[1], x[0]))[:limit]]
