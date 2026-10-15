"""Scoped, rebuildable retrieval. Rankings are candidates, never decisions."""
import json
import re
import math
import struct
import sqlite3

import derived_work
from records import RecordError, digest, encoded
from embeddings import PROFILE, PROFILE_SHA


def vector_blob(vector):
    if (not isinstance(vector, (list, tuple)) or len(vector) != PROFILE["dimensions"] or
            any(type(v) not in (float, int) or not math.isfinite(v) for v in vector) or
            abs(sum(v * v for v in vector) - 1) > 0.001):
        raise RecordError("invalid-vector")
    return struct.pack(f'<{len(vector)}f', *vector)


def load_vec(db):
    try:
        import sqlite_vec
        db.enable_load_extension(True)
        try:
            sqlite_vec.load(db)
        finally:
            db.enable_load_extension(False)
    except (ImportError, AttributeError, sqlite3.Error):
        raise RecordError("vector-extension-unavailable") from None


class SearchIndex:
    def __init__(self, records):
        self.records = records

    def by_id(self, identity, scope=None):
        value = self.records.get(identity)
        if scope is not None and value["scope"] != scope:
            raise RecordError("not-found-in-scope")
        return value

    @staticmethod
    def _match(value, details):
        decisions = value["review_decisions"]
        historical = value["state"] in ("resolved", "discarded") or bool(decisions) and all(v["decision"]["status"] != "pending" for v in decisions)
        return {"id": value["id"], "scope": value["scope"], "raw_sha256": value["raw_sha256"], "state": value["state"],
                "review_decisions": decisions, "review_disposition": "historical" if historical else "unresolved",
                "match": details, "status": "candidate"}

    def rebuild_text(self):
        with self.records._transaction() as db:
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS observation_fts USING fts5(id UNINDEXED,text,tokenize='unicode61 remove_diacritics 2')")
            db.execute("DELETE FROM observation_fts")
            db.execute("INSERT INTO observation_fts(rowid,id,text) SELECT rowid,id,json_extract(CAST(raw AS TEXT),'$.observation') FROM originals")
            db.execute("""CREATE TRIGGER IF NOT EXISTS observation_fts_insert AFTER INSERT ON originals BEGIN
                INSERT INTO observation_fts(rowid,id,text) VALUES(new.rowid,new.id,json_extract(CAST(new.raw AS TEXT),'$.observation'));
            END""")
        return self.status()

    def _candidates(self, scope=None, state=None, category=None):
        values = self.records.list(scope, state)
        if category is not None:
            from annotations import Annotations
            current = [(value, Annotations(self.records).latest(value["id"])) for value in values]
            values = [value for value, annotation in current if annotation["state"] == "provisional" and (annotation["annotation"] or {}).get("category") == category]
        return {value["id"]: value for value in values}

    def status(self, scope=None):
        values = self._candidates(scope)
        with self.records._connection() as db:
            lexical = bool(db.execute("SELECT 1 FROM sqlite_master WHERE name='observation_fts'").fetchone())
            current = {row["record_id"] for row in db.execute("SELECT record_id,raw_sha256 FROM observation_vectors WHERE profile_sha256=?", (PROFILE_SHA,)) if row["record_id"] in values and row["raw_sha256"] == values[row["record_id"]]["raw_sha256"]} if self._vectors_exist(db) else set()
        return {"project": self.records.project, "scope": scope, "originals": len(values), "text_index": "ready" if lexical else "absent", "profile_sha256": PROFILE_SHA, "vector_pending_ids": sorted(values.keys() - current), "vector_current_ids": sorted(current), "limits": ["Similarity does not establish an incident, classification, recurrence or authorization.", "No calibrated abstention threshold; no-match queries may return nearby candidates."]}

    @staticmethod
    def _vectors_exist(db):
        return db.execute("SELECT 1 FROM sqlite_master WHERE name='observation_vectors'").fetchone() is not None

    def prepare_embedding(self, identity):
        value = self.records.get(identity)
        text = value["observation"]["observation"]
        return {"schema_version": 1, "project": self.records.project, "id": identity, "raw_sha256": value["raw_sha256"], "text": text, "input_sha256": digest(text.encode()), "profile_sha256": PROFILE_SHA}

    def publish_embedding(self, context, vector, generation, operation_id):
        blob = vector_blob(vector)
        if (not isinstance(generation, dict) or set(generation) != {"kind", "version", "token_count", "truncated"} or
                generation["kind"] not in ("gemma", "fixture") or not isinstance(generation["version"], str) or
                not generation["version"].strip() or type(generation["truncated"]) is not bool or
                (generation["token_count"] is not None and (type(generation["token_count"]) is not int or generation["token_count"] < 1)) or
                (generation["kind"] == "gemma" and generation["version"] != PROFILE["revision"])):
            raise RecordError("invalid-embedding-generation")
        if not isinstance(context, dict) or context.get("project") != self.records.project or not isinstance(context.get("id"), str):
            raise RecordError("embedding-outside-scope")
        with self.records._transaction() as db:
            if self.prepare_embedding(context["id"]) != context:
                raise RecordError("embedding-input-stale")
            db.execute("""CREATE TABLE IF NOT EXISTS observation_vectors(
                record_id TEXT NOT NULL REFERENCES originals(id), profile_sha256 TEXT NOT NULL,
                raw_sha256 TEXT NOT NULL, input_sha256 TEXT NOT NULL, vector BLOB NOT NULL,
                generation TEXT NOT NULL, PRIMARY KEY(record_id,profile_sha256)) STRICT""")
            payload = {"input": context, "vector_sha256": digest(blob), "generation": generation}
            previous = db.execute("SELECT * FROM versions WHERE operation_id=?", (operation_id,)).fetchone()
            revision = previous["revision"] - 1 if previous else db.execute("SELECT COALESCE(MAX(revision),0) FROM versions WHERE kind='embedding' AND record_id=?", (context["id"],)).fetchone()[0]
            result = self.records._append(db, "embedding", context["id"], revision, payload, operation_id)
            latest = db.execute("SELECT MAX(revision) FROM versions WHERE kind='embedding' AND record_id=?", (context["id"],)).fetchone()[0]
            if result["revision"] < latest:
                return {"status": "already-indexed", "id": context["id"], "revision": result["revision"], "cache_state": "historical"}
            db.execute("INSERT OR REPLACE INTO observation_vectors VALUES(?,?,?,?,?,?)", (context["id"], PROFILE_SHA, context["raw_sha256"], context["input_sha256"], blob, encoded(generation).decode()))
            derived_work.mark(db, context["id"], "embedding", "ready", context["input_sha256"], operation_id)
        return {"status": "already-indexed" if result["status"] == "already-saved" else "indexed", "id": context["id"], "revision": result["revision"]}

    def index_pending(self, encoder):
        results = []
        for identity in self.status()["vector_pending_ids"]:
            context = self.prepare_embedding(identity)
            vector, generation = encoder.encode(context["text"], "document")
            operation = "embedding:" + digest(encoded({"context": context, "vector_sha256": digest(vector_blob(vector)), "generation": generation}))
            results.append(self.publish_embedding(context, vector, generation, operation))
        return {"results": results, "coverage": self.status()}

    def reset_vectors(self):
        with self.records._transaction() as db:
            if self._vectors_exist(db):
                db.execute("DELETE FROM observation_vectors")
            for row in db.execute("SELECT id,raw_sha256 FROM originals").fetchall():
                derived_work.mark(db, row["id"], "embedding", "pending", row["raw_sha256"], "reset-vectors")
        return self.status()

    def vector(self, vector, *, scope=None, state=None, category=None, limit=10):
        blob = vector_blob(vector)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise RecordError("invalid-search")
        candidates = self._candidates(scope, state, category)
        with self.records._connection() as db:
            rows = []
            if self._vectors_exist(db) and candidates:
                load_vec(db)
                rows = list(db.execute("""SELECT v.record_id AS id,vec_distance_cosine(v.vector,?) AS distance,v.generation
                    FROM observation_vectors v JOIN originals o ON o.id=v.record_id
                    WHERE v.profile_sha256=? AND v.raw_sha256=o.raw_sha256
                    AND v.record_id IN (SELECT value FROM json_each(?)) ORDER BY distance,v.record_id LIMIT ?""", (blob, PROFILE_SHA, json.dumps(list(candidates)), limit)))
        return {"method": "sqlite-vec-cosine", "matches": [self._match(candidates[r["id"]], {"distance": r["distance"], "excerpt": candidates[r["id"]]["observation"]["observation"], "generation": json.loads(r["generation"])}) for r in rows], "coverage": self.status(scope)}

    def search(self, text, *, scope=None, state=None, category=None, limit=10, semantic=False, encoder=None):
        if not isinstance(text, str) or not text.strip() or type(limit) is not int or not 1 <= limit <= 100:
            raise RecordError("invalid-search")
        candidates = self._candidates(scope, state, category)
        semantic_error = None
        if semantic:
            try:
                if encoder is None:
                    raise RecordError("embedding-model-unavailable")
                vector, _ = encoder.encode(text, "query")
                return self.vector(vector, scope=scope, state=state, category=category, limit=limit)
            except RecordError as error:
                semantic_error = str(error)
        terms = sorted(set(re.findall(r"[^\W_]+", text.casefold())))[:128]
        rows, fallback = [], False
        if terms and candidates:
            with self.records._connection() as db:
                if db.execute("SELECT 1 FROM sqlite_master WHERE name='observation_fts'").fetchone():
                    expression = " OR ".join('"' + term + '"' for term in terms)
                    rows = [dict(row) for row in db.execute("SELECT id,bm25(observation_fts) AS score FROM observation_fts WHERE observation_fts MATCH ? ORDER BY score,id", (expression,)) if row["id"] in candidates][:limit]
                else:
                    fallback = True
                    rows = [{"id": identity, "score": None} for identity, value in candidates.items() if any(term in value["observation"]["observation"].casefold() for term in terms)][:limit]
        return {"method": "text-fallback" if fallback or semantic_error else "fts5", "semantic_error": semantic_error, "matches": [self._match(candidates[row["id"]], {"score": row["score"], "excerpt": candidates[row["id"]]["observation"]["observation"]}) for row in rows], "coverage": self.status(scope)}
