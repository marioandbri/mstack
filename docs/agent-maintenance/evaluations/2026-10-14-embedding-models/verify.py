"""Reopen real indexes and compare SQLite distances against NumPy cosine."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import sqlite3

import numpy as np
import sqlite_vec
from run import retrieval_prompts

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def connection(path):
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.enable_load_extension(True)
    try:
        sqlite_vec.load(db)
    finally:
        db.enable_load_extension(False)
    return db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private", type=Path, required=True)
    args = parser.parse_args()
    private = args.private
    protocol = read(private / "protocol.json")
    assert protocol == read(HERE / "protocol.json")
    for name, expected in protocol["corpus_hashes"].items():
        assert sha(private / "corpus" / name) == expected
    for name, expected in protocol["execution_sources"].items():
        assert sha(private / "execution-sources" / name) == expected
        assert sha(HERE / name) == expected
    assert {name: metadata.version(name) for name in protocol["runtime"]["packages"]} == protocol["runtime"]["packages"]
    corpus = read(private / "corpus/records.json")["records"]
    labels = read(private / "corpus/labels.json")
    assert not labels["user_approved"]
    queries = {row["id"]: row for row in labels["queries"]}
    assert len(corpus) == 33 and len(queries) == 52
    assert sum(bool(row["direct_ids"]) for row in queries.values()) == 46
    assert all(row["grades"] is None for row in labels["held_out_for_review"] + labels["excluded_from_comparison"])
    baseline = read(private / "fts5-results.json")
    downloads = read(private / "downloads.json")
    assert set(downloads) == set(protocol["models"])
    repeated_sqlite_queries = 0
    for label, expected in protocol["models"].items():
        result = read(private / (label + "-result.json"))
        assert result["status"] == "complete" and result["model"] == expected
        assert result["actual"]["device"] == "cpu" and result["actual"]["dtype"] == "torch.float32"
        assert result["actual"]["max_seq_length"] == expected["max_seq_length"]
        prompt_file = Path(downloads[label]["local_path"]) / "config_sentence_transformers.json"
        serialized_prompts = read(prompt_file).get("prompts", {}) if prompt_file.exists() else {}
        assert result["actual"]["prompts"] == retrieval_prompts(expected, serialized_prompts)
        assert result["resources"]["encoded_documents"] == 33 and result["resources"]["encoded_queries"] == 50
        assert result["resources"]["scope_skipped_queries"] == 2
        assert result["resources"]["warmup_calls"] == 2
        assert len(result["results"]) == 156
        assert [row for row in result["results"] if row["method"] == "fts5"] == baseline
        vectors = np.load(private / (label + "-vectors.npz"), allow_pickle=False)
        documents, query_vectors = vectors["documents"], vectors["queries"]
        identities = vectors["query_ids"].tolist()
        assert documents.shape == (33, expected["dimension"])
        assert query_vectors.shape == (50, expected["dimension"])
        assert documents.dtype == query_vectors.dtype == np.float32
        assert np.isfinite(documents).all() and np.isfinite(query_vectors).all()
        assert np.allclose(np.linalg.norm(documents, axis=1), 1, atol=1e-5)
        assert np.allclose(np.linalg.norm(query_vectors, axis=1), 1, atol=1e-5)
        lookup = dict(zip(identities, query_vectors))
        db = connection(private / (label + ".sqlite"))
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT count(*) FROM records").fetchone()[0] == 33
        assert db.execute("SELECT count(*) FROM embeddings").fetchone()[0] == 33
        for row, source in zip(db.execute("SELECT id,text,project FROM records ORDER BY rowid"), corpus):
            assert row == (source["id"], source["text"], "mstack")
        for row in result["results"]:
            query = queries[row["query_id"]]
            ranked = row["ranked"]
            ids = [value["id"] for value in ranked]
            assert set(ids) <= set(query["candidate_ids"])
            assert len(ids) == len(set(ids))
            if query["case_id"] == "C16":
                assert not ranked
            if not query["direct_ids"]:
                assert row["metrics"]["hit_at_3"] is row["metrics"]["ndcg_at_5"] is None
            else:
                assert row["metrics"]["hit_at_3"] == bool(set(ids[:3]) & set(query["direct_ids"]))
                assert row["metrics"]["hit_at_5"] == bool(set(ids[:5]) & set(query["direct_ids"]))
            if row["method"] != "vector" or not query["candidate_ids"]:
                continue
            vector = lookup[row["query_id"]]
            independent = 1 - (documents @ vector) / (np.linalg.norm(documents, axis=1) * np.linalg.norm(vector))
            expected_ranks = sorted(range(33), key=lambda index: (float(independent[index]), corpus[index]["id"]))[:10]
            assert ids == [corpus[index]["id"] for index in expected_ranks], row["query_id"]
            assert np.allclose([item["distance"] for item in ranked], independent[expected_ranks], atol=2e-5)
            repeated = db.execute("""SELECT r.id,e.distance FROM embeddings e JOIN records r ON r.rowid=e.rowid
                                      WHERE e.embedding MATCH ? AND e.k=10 AND e.project=? ORDER BY e.distance,r.id""",
                                  (vector.tobytes(), query["filters"]["project"])).fetchall()
            assert [item[0] for item in repeated] == ids
            assert np.allclose([item[1] for item in repeated], [item["distance"] for item in ranked], atol=1e-7)
            repeated_sqlite_queries += 1
        db.close()
    for label, model in downloads.items():
        assert model["revision"] == protocol["models"][label]["revision"]
        for artifact in model["artifacts"]:
            assert sha(Path(model["local_path"]) / artifact["path"]) == artifact["sha256"]
    value = {"status": "PASS", "models": len(protocol["models"]), "sqlite_vector_queries_reopened": repeated_sqlite_queries,
             "finite_normalized_vectors": True, "project_filters": "PASS", "held_out_excluded": True,
             "source_model_artifact_hashes": "PASS", "labels": "provisional; source verification cannot approve semantic judgments"}
    (private / "independent-verification.json").write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps(value))


if __name__ == "__main__":
    main()
