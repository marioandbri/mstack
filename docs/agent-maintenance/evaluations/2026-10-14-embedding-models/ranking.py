"""Evaluation-only SQLite retrieval and relevance metrics."""
import math
from pathlib import Path
import re
import sqlite3
import struct

import sqlite_vec


def measure(ranked, grades):
    direct = {identity for identity, grade in grades.items() if grade == 2}
    result = {"returned_candidates_without_direct_target": bool(ranked and not direct)}
    for cutoff in (1, 3, 5):
        found = set(ranked[:cutoff]) & direct
        result[f"hit_at_{cutoff}"] = bool(found) if direct else None
        result[f"recall_at_{cutoff}"] = len(found) / len(direct) if direct else None
    first = next((rank for rank, identity in enumerate(ranked[:5], 1) if identity in direct), None)
    result["mrr_at_5"] = (1 / first if first else 0) if direct else None
    actual = sum((2 ** grades[identity] - 1) / math.log2(rank + 1) for rank, identity in enumerate(ranked[:5], 1))
    ideal = sum((2 ** grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(sorted(grades.values(), reverse=True)[:5], 1))
    result["ndcg_at_5"] = actual / ideal if direct else None
    return result


def vector_blob(values):
    return struct.pack(f"<{len(values)}f", *values)


class RetrievalIndex:
    def __init__(self, path, dimension=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.enable_load_extension(True)
        try:
            sqlite_vec.load(self.db)
        finally:
            self.db.enable_load_extension(False)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS records(id TEXT UNIQUE NOT NULL, text TEXT NOT NULL, project TEXT NOT NULL);
            CREATE VIRTUAL TABLE IF NOT EXISTS lexical USING fts5(text, content='records', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');
            CREATE TRIGGER IF NOT EXISTS records_insert AFTER INSERT ON records BEGIN
                INSERT INTO lexical(rowid,text) VALUES(new.rowid,new.text);
            END;
        """)
        if dimension is not None:
            assert isinstance(dimension, int) and 0 < dimension <= 4096
            self.db.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(embedding float[{dimension}] distance_metric=cosine, project text)")

    def load(self, records, vectors=None):
        assert self.db.execute("SELECT count(*) FROM records").fetchone()[0] == 0
        assert vectors is None or len(vectors) == len(records)
        with self.db:
            for index, record in enumerate(records):
                cursor = self.db.execute("INSERT INTO records(id,text,project) VALUES(?,?,?)", (record["id"], record["text"], record["project"]))
                if vectors is not None:
                    vector = vectors[index]
                    assert len(vector) == self.dimension and all(math.isfinite(value) for value in vector)
                    self.db.execute("INSERT INTO embeddings(rowid,embedding,project) VALUES(?,?,?)", (cursor.lastrowid, vector_blob(vector), record["project"]))

    def vector(self, vector, project, limit=10):
        assert self.dimension == len(vector)
        return [dict(row) for row in self.db.execute("""
            SELECT r.id,e.distance FROM embeddings e JOIN records r ON r.rowid=e.rowid
            WHERE e.embedding MATCH ? AND e.k=? AND e.project=?
            ORDER BY e.distance,r.id
        """, (vector_blob(vector), limit, project))]

    def lexical(self, text, project, limit=10):
        terms = sorted(set(re.findall(r"[^\W_]+", text.casefold())))
        if not terms:
            return []
        expression = " OR ".join('"' + term + '"' for term in terms)
        return [dict(row) for row in self.db.execute("""
            SELECT r.id,bm25(lexical) AS score FROM lexical JOIN records r ON r.rowid=lexical.rowid
            WHERE lexical MATCH ? AND r.project=? ORDER BY score,r.id LIMIT ?
        """, (expression, project, limit))]

    def hybrid(self, vector, text, project, limit=10):
        scores = {}
        for ranking in (self.vector(vector, project, limit), self.lexical(text, project, limit)):
            for rank, row in enumerate(ranking, 1):
                scores[row["id"]] = scores.get(row["id"], 0) + 1 / (60 + rank)
        return [{"id": identity, "score": score} for identity, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]]

    def close(self):
        self.db.close()
