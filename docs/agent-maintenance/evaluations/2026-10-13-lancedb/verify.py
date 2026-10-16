"""Verify recorded results, source bindings and persisted synthetic datasets."""
import argparse
import hashlib
import json
from pathlib import Path

from probe import read

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
    assert sha(HERE / "uv.lock") == manifest["dependency_lock_sha256"]
    for name, expected in manifest["inputs"].items():
        assert sha(HERE / name) == expected, name
    for mode in ("native", "guarded"):
        raw = json.loads((args.raw_run / mode / "summary.json").read_text())
        assert raw == results[mode]
        assert raw["source_sha256"] == manifest["inputs"]["probe.py"]
        assert raw["protocol_sha256"] == manifest["inputs"]["protocol.json"]
        assert raw["python"] == "3.13.2" and raw["packages"]["lancedb"] == "0.40.0"
        for iteration in range(3):
            rows = read(args.raw_run / mode / "databases" / f"append-{iteration}")
            expected = {f"{writer}-{n:02d}" for writer in ("a", "b") for n in range(30)}
            assert len(rows) == 60 and {r["id"] for r in rows} == expected
            assert all(r["source_session"] == "source-" + r["id"][0] for r in rows)
        for iteration in range(10):
            rows = read(args.raw_run / mode / "databases" / f"retry-{iteration}")
            assert len(rows) == (2 if mode == "native" else 1)
            assert {r["operation_id"] for r in rows} == {"shared-operation"}
            review = read(args.raw_run / mode / "databases" / f"decision-{iteration}")
            assert len(review) == 1 and review[0]["revision"] == 1
            outcome = raw["results"]["conflicting_revision"]["repetitions"][iteration]
            assert sorted(outcome["statuses"]) == ["accepted", "conflict"]
    for iteration in range(3):
        rows = read(args.raw_run / "native/databases" / f"interrupted-{iteration}")
        assert len(rows) == 6 and {r["id"] for r in rows} == {f"confirmed-{n}" for n in range(6)}
    extra = json.loads((args.raw_run / "adapter-checks.json").read_text())
    assert extra == results["additional_adapter_checks"]
    assert all(result["pass"] for result in extra.values())
    original = read(args.raw_run / "adapter-conflicts")
    assert len(original) == 1 and original[0]["text"] == "Synthetic observation"
    assert read(args.raw_run / "adapter-lock-release")[0]["id"] == "after-terminated-writer"
    print("PASS frozen sources, exact recorded results, persisted IDs/provenance, native duplicates, guarded uniqueness and update conflicts")


if __name__ == "__main__":
    main()
