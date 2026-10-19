"""Reopen SQLite artifacts and verify source bindings and recorded outcomes."""
import argparse
import hashlib
import json
from pathlib import Path

from sqlite_store import SqliteStore

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-run", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    results = json.loads((HERE / "results.json").read_text())
    assert sha(HERE / "results.json") == manifest["results_sha256"]
    for name, expected in manifest["inputs"].items():
        assert sha(HERE / name) == expected, name
    for reference in (manifest["shared_fixture_source"], manifest["lancedb_comparison_results"]):
        assert sha(HERE / reference["path"]) == reference["sha256"]
    assert results == json.loads((args.raw_run / "summary.json").read_text())
    assert results["source_sha256"] == manifest["inputs"]["sqlite_probe.py"]
    assert results["adapter_sha256"] == manifest["inputs"]["sqlite_store.py"]
    assert results["protocol_sha256"] == manifest["inputs"]["protocol.json"]
    assert len(results["results"]) == 12
    assert all(case["status"] == "pass" for case in results["results"].values())
    root = args.raw_run / "databases"
    for path in root.glob("*.sqlite"):
        db = SqliteStore(path).connect()
        try:
            assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path
            assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal", path
            assert db.execute("PRAGMA synchronous").fetchone()[0] == 2, path
        finally:
            db.close()
    for n in range(3):
        rows = SqliteStore(root / f"append-{n}.sqlite").rows()
        assert len(rows) == 60 and {r["id"] for r in rows} == {f"{writer}-{i:02d}" for writer in ("a", "b") for i in range(30)}
        assert all(r["source_session"] == "source-" + r["id"][0] for r in rows)
        interrupted = SqliteStore(root / f"interrupted-{n}.sqlite").rows()
        assert len(interrupted) in (6, 12006)
        assert {r["id"] for r in interrupted if r["id"].startswith("confirmed-")} == {f"confirmed-{i}" for i in range(6)}
    for n in range(10):
        rows = SqliteStore(root / f"retry-{n}.sqlite").rows()
        assert len(rows) == 1 and rows[0]["operation_id"] == "shared-operation"
        review = SqliteStore(root / f"decision-{n}.sqlite").rows()
        assert len(review) == 1 and review[0]["revision"] == 1
        outcome = results["results"]["conflicting_revision"]["repetitions"][n]
        assert sorted(outcome["statuses"]) == ["accepted", "conflict"]
    rollback = SqliteStore(root / "known-transaction.sqlite").rows()
    assert len(rollback) == 6 and {r["id"] for r in rollback} == {f"confirmed-{i}" for i in range(6)}
    store = SqliteStore(root / "retrieval.sqlite")
    assert [r["id"] for r in store.vector_search([1, 0, 0], "mstack", 1)] == ["approval"]
    assert {r["id"] for r in store.text_search("approval", "mstack")} == {"approval", "pending-vector"}
    original = SqliteStore(root / "identity-conflicts.sqlite").rows()
    assert len(original) == 1 and original[0]["text"] == "Synthetic observation"
    print("PASS exact source/results bindings, SQLite integrity, persisted IDs/provenance, retry uniqueness, revision conflicts, rollback and filtered vector/text retrieval")


if __name__ == "__main__":
    main()
