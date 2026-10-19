"""Reopen experimental Chroma artifacts without using the writer implementation."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import chromadb
from chromadb.config import Settings

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-10-13-lancedb"))
from probe import record


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(collection):
    data = collection.get(include=["metadatas", "documents", "embeddings"])
    if not data["ids"]:
        return []
    return [dict(metadata, id=identity, text=document, vector=embedding.tolist())
            for identity, metadata, document, embedding in zip(
                data["ids"], data["metadatas"], data["documents"], data["embeddings"])]


def point(identity, writer="a", **kwargs):
    return record(identity, writer, vector=[1.0, 0.0, 0.0], **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-run", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    results = json.loads((HERE / "results.json").read_text())
    assert sha(HERE / "results.json") == manifest["results_sha256"]
    assert chromadb.__version__ == manifest["runtime"]["chromadb"] == "1.5.9"
    for name, expected in manifest["inputs"].items():
        assert sha(HERE / name) == expected, name
    for reference in manifest["comparison_sources"]:
        assert sha(HERE / reference["path"]) == reference["sha256"], reference["path"]
    api = json.loads((HERE / "api-surface.json").read_text())
    from chromadb.api.models.Collection import Collection
    assert not api["collection_has_conditional"] and not hasattr(Collection, "conditional")
    verified_databases = 0
    for mode, summary in results["modes"].items():
        assert summary == json.loads((args.raw_run / mode / "summary.json").read_text())
        for key, source in (("source_sha256", "chroma_probe.py"),
                            ("actor_sha256", "chroma_actor.py"),
                            ("protocol_sha256", "protocol.json")):
            assert summary[key] == manifest["inputs"][source]
        cases = summary["results"]
        assert len(cases) == 10
        expected_failures = {"capture_without_embedding"}
        if mode == "native":
            expected_failures |= {"conflicting_revision", "identity_conflicts"}
        assert {name for name, case in cases.items() if case["status"] != "pass"} == expected_failures
        assert all(cases[name]["status"] == "contract-failure" for name in expected_failures)
        for name, case in cases.items():
            assert case == json.loads((args.raw_run / mode / f"{name}.json").read_text())
        assert cases["capture_without_embedding"]["actual_count"] == 0
        rejection = cases["capture_without_embedding"]["outcome"]["results"][0]
        assert rejection["status"] == "rejected" and rejection["exception"] == "ValueError"
        expected_statuses = (["returned"] * 4 if mode == "native" else
                             ["returned", "already-captured", "operation-conflict", "identity-conflict"])
        assert cases["identity_conflicts"]["statuses"] == expected_statuses
        for repetition in cases["conflicting_revision"]["repetitions"]:
            expected = ["accepted", "accepted"] if mode == "native" else ["accepted", "conflict"]
            assert sorted(repetition["statuses"]) == expected
        root = args.raw_run / mode / "databases"
        paths = sorted(path for path in root.iterdir() if path.is_dir())
        assert len(paths) == 32
        for path in paths:
            db = sqlite3.connect((path / "chroma.sqlite3").resolve().as_uri() + "?mode=ro", uri=True)
            try:
                assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path.name
            finally:
                db.close()
            client = chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))
            try:
                collection = client.get_collection("observations", embedding_function=None)
                actual = rows(collection)
                assert collection.count() == len(actual)
                name = path.name
                if name == "missing-embedding":
                    assert actual == []
                elif name.startswith("append-"):
                    expected = [point(f"{writer}-{i:02d}", writer) for writer in ("a", "b") for i in range(30)]
                    assert sorted(actual, key=lambda r: r["id"]) == sorted(expected, key=lambda r: r["id"])
                elif name == "sequential":
                    assert actual == [point("retry-001")]
                elif name.startswith("retry-"):
                    assert actual == [point("shared-operation")]
                elif name.startswith("decision-"):
                    assert len(actual) == 1 and actual[0]["revision"] == 1
                    final = actual[0]
                    assert final == dict(point("review-001"), revision=1, decision=final["decision"])
                    assert final["decision"] in ("keep", "defer")
                elif name == "freshness":
                    assert actual == [point("writer-001")]
                elif name.startswith("interrupted-"):
                    repetition = cases["interrupted_write"]["repetitions"][int(name.rsplit("-", 1)[1])]
                    assert repetition["exitcode"] == -9 and repetition["batch_rows"] == 5461
                    assert repetition["interrupted_batch_rows"] == 0
                    assert sorted(actual, key=lambda r: r["id"]) == [point(f"confirmed-{i}") for i in range(6)]
                elif name == "retrieval":
                    assert len(actual) == 4 and {r["id"] for r in actual} == {"approval", "tests", "references", "other-project"}
                    neighbors = collection.query(query_embeddings=[[1.0, 0.0, 0.0]], where={"project": "mstack"}, n_results=1)
                    assert neighbors["ids"][0] == ["approval"]
                    text = collection.get(where={"project": "mstack"}, where_document={"$contains": "approval"})
                    assert text["ids"] == ["approval"]
                elif name == "identity":
                    assert actual == [point("original-001")]
                elif name == "invalid-vector":
                    assert actual == [point("vector-001")]
                else:
                    raise AssertionError(name)
                verified_databases += 1
            finally:
                client.close()
    print(f"PASS source/results/API bindings and {verified_databases} reopened databases: integrity, originals/provenance, retries, revision outcomes, interruption and filtered retrieval. Expected contract gaps remain failures.")


if __name__ == "__main__":
    main()
