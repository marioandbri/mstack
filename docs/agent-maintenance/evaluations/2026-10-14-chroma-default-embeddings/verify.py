"""Verify frozen evidence and generated vectors through fresh public SDK reads."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys

import chromadb
import numpy as np
from chromadb.config import Settings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-10-13-lancedb"))
from probe import record


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(collection):
    data = collection.get(include=["metadatas", "documents", "embeddings"])
    return [dict(data["metadatas"][i], id=identity, text=data["documents"][i],
                 vector=data["embeddings"][i].tolist()) for i, identity in enumerate(data["ids"])]


def same_originals(actual, expected):
    assert len(actual) == len(expected)
    for row in actual:
        assert len(row["vector"]) == 384 and all(math.isfinite(v) for v in row["vector"])
        assert abs(sum(v * v for v in row["vector"]) ** 0.5 - 1) < 1e-5
    assert sorted([dict(r, vector=None) for r in actual], key=lambda r: r["id"]) == sorted(expected, key=lambda r: r["id"])


def integrity(path):
    db = sqlite3.connect((path / "chroma.sqlite3").resolve().as_uri() + "?mode=ro", uri=True)
    try:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-run", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    results = json.loads((HERE / "results.json").read_text())
    bootstrap = json.loads((HERE / "bootstrap.json").read_text())
    corpus = json.loads((HERE / "corpus.json").read_text())
    assert sha(HERE / "results.json") == manifest["results_sha256"]
    assert sha(HERE / "bootstrap.json") == manifest["bootstrap_sha256"]
    for name, expected in manifest["inputs"].items():
        assert sha(HERE / name) == expected, name
    for reference in manifest["comparison_sources"]:
        assert sha(HERE / reference["path"]) == reference["sha256"], reference["path"]
    assert bootstrap == json.loads((args.raw_run / "bootstrap.json").read_text())
    assert bootstrap["artifact_recovered"] and bootstrap["cold_add_including_download_seconds"] is None
    attempt = json.loads((HERE / "bootstrap-attempt.json").read_text())
    assert attempt == json.loads((args.raw_run / "attempt-01" / "attempt.json").read_text())
    assert sha(args.raw_run / "attempt-01" / "bootstrap.py") == attempt["source_sha256"]
    assert sha(args.raw_run / "attempt-01" / "protocol.json") == attempt["protocol_sha256"]
    cache = args.raw_run / "model-cache" / "all-MiniLM-L6-v2"
    for name, binding in bootstrap["model_files"].items():
        assert sha(cache / name) == binding["sha256"] and (cache / name).stat().st_size == binding["bytes"]
    assert bootstrap["archive_sha256"] == ONNXMiniLM_L6_V2._MODEL_SHA256
    assert bootstrap["collection_configuration"]["embedding_function"]["name"] == "default"
    assert bootstrap["collection_configuration"]["hnsw"]["space"] == "l2"
    ONNXMiniLM_L6_V2.DOWNLOAD_PATH = cache
    verified = 0
    for mode, summary in results["modes"].items():
        assert summary == json.loads((args.raw_run / mode / "summary.json").read_text())
        for field, source in (("source_sha256", "default_probe.py"), ("actor_sha256", "default_actor.py"),
                              ("protocol_sha256", "protocol.json"), ("corpus_sha256", "corpus.json")):
            assert summary[field] == manifest["inputs"][source]
        assert summary["bootstrap_sha256"] == manifest["bootstrap_sha256"]
        cases = summary["results"]
        expected_gaps = {"capture_embedding_unavailable"}
        if mode == "native":
            expected_gaps |= {"conflicting_revision", "identity_conflicts"}
        assert len(cases) == 11
        assert {name for name, case in cases.items() if case["status"] != "pass"} == expected_gaps
        assert all(cases[name]["status"] == "contract-failure" for name in expected_gaps)
        for name, case in cases.items():
            assert case == json.loads((args.raw_run / mode / f"{name}.json").read_text())
        paths = sorted((args.raw_run / mode / "databases").iterdir())
        assert len(paths) == 33
        for path in paths:
            integrity(path)
            client = chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))
            try:
                collection = client.get_collection(name="observations")
                assert collection.configuration_json["embedding_function"]["name"] == "default"
                actual = read(collection)
                assert collection.count() == len(actual)
                name = path.name
                if name == "automatic-embedding":
                    same_originals(actual, [record("origin-001", text="Approval was requested again after it had been granted.")])
                    regenerated = DefaultEmbeddingFunction()([actual[0]["text"]])[0]
                    assert np.allclose(actual[0]["vector"], regenerated, atol=1e-6, rtol=1e-6)
                elif name.startswith("append-"):
                    same_originals(actual, [record(f"{writer}-{i:02d}", writer) for writer in ("a", "b") for i in range(30)])
                elif name == "sequential":
                    same_originals(actual, [record("retry-001")])
                elif name.startswith("retry-"):
                    same_originals(actual, [record("shared-operation")])
                elif name.startswith("decision-"):
                    assert len(actual) == 1 and actual[0]["decision"] in ("keep", "defer")
                    same_originals(actual, [dict(record("review-001"), revision=1, decision=actual[0]["decision"])])
                    repetition = cases["conflicting_revision"]["repetitions"][int(name.rsplit("-", 1)[1])]
                    expected = ["accepted", "accepted"] if mode == "native" else ["accepted", "conflict"]
                    assert sorted(repetition["statuses"]) == expected
                elif name == "freshness":
                    same_originals(actual, [record("writer-001")])
                elif name.startswith("interrupted-"):
                    same_originals(actual, [record(f"confirmed-{i}") for i in range(6)])
                    repetition = cases["interrupted_write"]["repetitions"][int(name.rsplit("-", 1)[1])]
                    assert repetition["exitcode"] == -9 and repetition["interrupted_batch_rows"] == 0
                elif name == "identity":
                    same_originals(actual, [record("original-001")])
                elif name == "invalid-vector":
                    same_originals(actual, [record("vector-001")])
                elif name == "embedding-unavailable":
                    assert actual == [] and cases["capture_embedding_unavailable"]["outcome"]["rejected"]
                elif name == "retrieval":
                    same_originals(actual, [record(r["id"], text=r["text"], project=r["project"]) for r in corpus["records"]])
                    recorded = cases["retrieval"]["queries"]["queries"]
                    for query, expected in zip(corpus["queries"], recorded):
                        found = collection.query(query_texts=[query["text"]], n_results=3, where={"project": "mstack"})
                        assert found["ids"][0] == expected["ids"]
                        assert np.allclose(found["distances"][0], expected["distances"], atol=1e-6)
                        assert set(expected["ids"]) & set(query["relevant_ids"])
                        assert not any(i.startswith("other-") for i in expected["ids"])
                else:
                    raise AssertionError(name)
                verified += 1
            finally:
                client.close()
    integrity(args.raw_run / "bootstrap-db")
    client = chromadb.PersistentClient(path=str(args.raw_run / "bootstrap-db"), settings=Settings(anonymized_telemetry=False))
    try:
        collection = client.get_collection(name="observations")
        assert collection.count() == 1
        assert collection.query(query_texts=["The agent asked for permission twice."], n_results=1)["ids"][0] == ["origin-001"]
    finally:
        client.close()
    print(f"PASS source/model/attempt bindings and {verified + 1} reopened databases: default function, real vectors, originals/provenance, retries, revisions, interruption and reproduced bilingual retrieval. Raw-before-embedding gaps remain failures.")


if __name__ == "__main__":
    main()
