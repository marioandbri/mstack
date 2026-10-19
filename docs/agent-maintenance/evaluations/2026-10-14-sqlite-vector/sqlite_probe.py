"""SQLite/FTS5/sqlite-vec comparison through synthetic real-process probes."""
import argparse
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import signal
import sqlite3
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-10-13-lancedb"))
# The existing constructor uses only the standard library. No LanceDB imports.
from probe import record
from sqlite_store import SqliteStore, decode, encode

CONTEXT = mp.get_context("spawn")
PROTOCOL = json.loads((HERE / "protocol.json").read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def create(path, records=()):
    store = SqliteStore(path)
    store.initialize()
    for original in records:
        store.capture(original)
    return store


def worker(path, operation, payload, barrier, pipe):
    try:
        store = SqliteStore(path)
        before = len(store.rows())
        barrier.wait(timeout=30)
        outcomes = [store.capture(item) if operation == "capture" else store.decide(**item) for item in payload]
        pipe.send({"before_rows": before, "results": outcomes, "pid": os.getpid()})
    except BaseException:
        pipe.send({"error": traceback.format_exc(), "pid": os.getpid()})
    finally:
        pipe.close()


def run_workers(path, operation, payloads):
    barrier = CONTEXT.Barrier(2)
    processes, pipes = [], []
    for payload in payloads:
        parent, child = CONTEXT.Pipe(duplex=False)
        process = CONTEXT.Process(target=worker, args=(str(path), operation, payload, barrier, child))
        process.start()
        child.close()
        processes.append(process)
        pipes.append(parent)
    outcomes = []
    deadline = time.monotonic() + 45
    for process, pipe in zip(processes, pipes):
        if pipe.poll(max(0, deadline - time.monotonic())):
            try:
                outcome = pipe.recv()
            except EOFError:
                outcome = {"error": "Worker exited without output"}
        else:
            outcome = {"error": "Worker deadline exceeded"}
            process.kill()
        process.join(5)
        if process.is_alive():
            process.kill()
            process.join(5)
            outcome["cleanup_error"] = "Worker did not exit after output"
        outcome["exitcode"] = process.exitcode
        outcomes.append(outcome)
        pipe.close()
    return outcomes


def capture_without_embedding(root):
    path = root / "capture.sqlite"
    create(path)
    original = record("origin-001", text="Approval was requested again after it had been granted.")
    outcome = SqliteStore(path, vectors=False).capture(original)
    actual = SqliteStore(path, vectors=False).rows()
    return {"pass": outcome["status"] == "acknowledged" and actual == [original], "rows": actual, "extension_loaded_for_capture": False}


def concurrent_append(root):
    repetitions = []
    for iteration in range(3):
        path = root / f"append-{iteration}.sqlite"
        store = create(path)
        payloads = [[record(f"{writer}-{n:02d}", writer) for n in range(30)] for writer in ("a", "b")]
        outcomes = run_workers(path, "capture", payloads)
        actual = store.rows()
        expected = payloads[0] + payloads[1]
        ok = not any("error" in x for x in outcomes) and sorted(actual, key=lambda x: x["id"]) == sorted(expected, key=lambda x: x["id"])
        repetitions.append({"pass": ok, "actual_count": len(actual), "expected_count": 60, "workers": outcomes})
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def sequential_retry(root):
    store = create(root / "retry-sequential.sqlite")
    original = record("retry-001")
    outcomes = [store.capture(original) for _ in range(4)]
    return {"pass": store.rows() == [original] and [r["status"] for r in outcomes] == ["acknowledged"] + ["already-captured"] * 3, "actual_count": len(store.rows()), "outcomes": outcomes}


def concurrent_retry(root):
    repetitions = []
    for iteration in range(10):
        path = root / f"retry-{iteration}.sqlite"
        store = create(path)
        original = record("shared-operation")
        outcomes = run_workers(path, "capture", [[original], [original]])
        statuses = [x["results"][0]["status"] for x in outcomes if "results" in x]
        actual = store.rows()
        repetitions.append({"pass": actual == [original] and sorted(statuses) == ["acknowledged", "already-captured"], "expected_count": 1, "actual_count": len(actual), "workers": outcomes})
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def conflicting_revision(root):
    repetitions = []
    for iteration in range(10):
        path = root / f"decision-{iteration}.sqlite"
        store = create(path, [record("review-001")])
        payloads = [[{"identity": "review-001", "expected_revision": 0, "decision": decision}] for decision in ("keep", "defer")]
        outcomes = run_workers(path, "decide", payloads)
        statuses = [x["results"][0]["status"] for x in outcomes if "results" in x]
        actual = store.rows()
        ok = sorted(statuses) == ["accepted", "conflict"] and len(actual) == 1 and actual[0]["revision"] == 1
        repetitions.append({"pass": ok, "statuses": statuses, "final_revision": actual[0]["revision"], "final_decision": actual[0]["decision"], "workers": outcomes})
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def reader_freshness(root):
    path = root / "freshness.sqlite"
    store = create(path)
    auto = store.connect()
    snapshot = store.connect()
    try:
        snapshot.execute("BEGIN")
        initial = [auto.execute("SELECT count(*) FROM observations").fetchone()[0], snapshot.execute("SELECT count(*) FROM observations").fetchone()[0]]
        outcomes = run_workers(path, "capture", [[record("writer-001")], []])
        auto_count = auto.execute("SELECT count(*) FROM observations").fetchone()[0]
        snapshot_count = snapshot.execute("SELECT count(*) FROM observations").fetchone()[0]
        snapshot.commit()
        after_count = snapshot.execute("SELECT count(*) FROM observations").fetchone()[0]
        return {"pass": initial == [0, 0] and auto_count == after_count == 1 and snapshot_count == 0 and not any("error" in x for x in outcomes), "initial_counts": initial, "autocommit_count": auto_count, "open_snapshot_count": snapshot_count, "after_transaction_count": after_count, "workers": outcomes}
    finally:
        auto.close()
        snapshot.close()


def interrupted_worker(path, pipe, known_phase):
    try:
        store = SqliteStore(path)
        for n in range(6):
            store.capture(record(f"confirmed-{n}"))
            pipe.send({"event": "acknowledged", "id": f"confirmed-{n}"})
        batch = [record(f"batch-{n:05d}", text="Synthetic batch record " + "x" * 1024) for n in range(12000)]
        if known_phase:
            with store.transaction() as db:
                for original in batch[:37]:
                    store._insert(db, original)
                pipe.send({"event": "uncommitted_rows_inserted", "count": 37})
                while True:
                    time.sleep(1)
        else:
            pipe.send({"event": "batch_started"})
            store.capture_batch(batch)
            pipe.send({"event": "batch_acknowledged"})
    except BaseException:
        pipe.send({"error": traceback.format_exc()})
    finally:
        pipe.close()


def kill_case(root, name, delay, known_phase=False):
    path = root / (name + ".sqlite")
    store = create(path)
    parent, child = CONTEXT.Pipe(duplex=False)
    process = CONTEXT.Process(target=interrupted_worker, args=(str(path), child, known_phase))
    process.start()
    child.close()
    events = []
    reached = False
    try:
        deadline = time.monotonic() + 45
        while parent.poll(max(0, deadline - time.monotonic())):
            event = parent.recv()
            events.append(event)
            if event.get("event") in ("batch_started", "uncommitted_rows_inserted"):
                reached = True
                break
            if "error" in event:
                break
        time.sleep(delay)
        process.kill()
        process.join(5)
    finally:
        if process.is_alive():
            process.kill()
            process.join(5)
        parent.close()
    rows = store.rows()
    confirmed = {row["id"] for row in rows if row["id"].startswith("confirmed-")}
    batch_ids = {row["id"] for row in rows if row["id"].startswith("batch-")}
    atomic = not batch_ids or batch_ids == {f"batch-{n:05d}" for n in range(12000)}
    ok = reached and confirmed == {f"confirmed-{n}" for n in range(6)} and atomic and process.exitcode == -signal.SIGKILL
    if known_phase:
        ok = ok and not batch_ids
    return {"pass": ok, "delay_seconds": delay, "exitcode": process.exitcode, "confirmed_rows": len(confirmed), "interrupted_batch_rows": len(batch_ids), "events": events, "known_uncommitted_phase": known_phase}


def interrupted_write(root):
    repetitions = [kill_case(root, f"interrupted-{n}", delay) for n, delay in enumerate((0.0, 0.005, 0.02))]
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def transaction_rollback(root):
    return kill_case(root, "known-transaction", 0, known_phase=True)


def hybrid_retrieval(root):
    rows = [
        record("approval", text="approval permission requested again", vector=[1.0, 0.0, 0.0]),
        record("tests", text="regression tests preserve behavior", vector=[0.0, 1.0, 0.0]),
        record("references", text="documentation reference unavailable", vector=[0.0, 0.0, 1.0]),
        record("other-project", text="approval permission requested again", vector=[1.0, 0.0, 0.0], project="other"),
        record("pending-vector", text="approval pending embedding"),
    ]
    store = create(root / "retrieval.sqlite", rows)
    vector = store.vector_search([1.0, 0.0, 0.0], "mstack", 1)
    lexical = store.text_search("approval", "mstack", 10)
    hybrid = store.hybrid_search([1.0, 0.0, 0.0], "approval", "mstack", 3)
    ids = lambda items: [row["id"] for row in items]
    ok = ids(vector) == ["approval"] and set(ids(lexical)) == {"approval", "pending-vector"} and "approval" in ids(hybrid) and "other-project" not in ids(hybrid)
    return {"pass": ok, "vector_ids": ids(vector), "lexical_ids": ids(lexical), "hybrid_ids": ids(hybrid), "fixed_vectors_only": True, "hybrid_implementation": "Custom RRF, k=60; ties sorted by record ID"}


def identity_conflicts(root):
    store = create(root / "identity-conflicts.sqlite")
    original = record("original-001")
    outcomes = [store.capture(original), store.capture(original), store.capture(record("original-001", text="Different incident with same operation ID")), store.capture(dict(original, operation_id="another-operation"))]
    expected = ["acknowledged", "already-captured", "operation-conflict", "identity-conflict"]
    return {"pass": [row["status"] for row in outcomes] == expected and store.rows() == [original], "outcomes": outcomes, "original_unchanged": store.rows() == [original]}


def embedding_failure(root):
    store = create(root / "embedding-failure.sqlite", [record("raw-001")])
    error = None
    try:
        store.attach_embedding("raw-001", [1, 0])
    except sqlite3.OperationalError as failure:
        error = str(failure)
    before = store.rows()
    store.attach_embedding("raw-001", [1, 0, 0])
    hits = store.vector_search([1, 0, 0], "mstack", 1)
    return {"pass": error is not None and before == [record("raw-001")] and [row["id"] for row in hits] == ["raw-001"], "invalid_vector_error": error, "raw_preserved_before_recovery": before == [record("raw-001")], "valid_vector_query_ids": [row["id"] for row in hits]}


def index_atomicity(root):
    store = create(root / "index-atomicity.sqlite", [record("atomic-001")])
    try:
        with store.transaction() as db:
            db.execute("UPDATE observations SET vector=? WHERE id=?", (encode([1, 0, 0]), "atomic-001"))
            raise RuntimeError("Synthetic interruption before vector-index publication")
    except RuntimeError:
        pass
    before = store.rows()
    no_hits = store.vector_search([1, 0, 0], "mstack", 1)
    store.attach_embedding("atomic-001", [1, 0, 0])
    rows = store.rows()
    hits = store.vector_search([1, 0, 0], "mstack", 1)
    return {"pass": before == [record("atomic-001")] and no_hits == [] and rows[0]["vector"] == [1, 0, 0] and [row["id"] for row in hits] == ["atomic-001"], "rollback_preserved_null_vector": before[0]["vector"] is None, "index_empty_after_failure": no_hits == [], "published_ids": [row["id"] for row in hits]}


CASES = {function.__name__: function for function in (
    capture_without_embedding, concurrent_append, sequential_retry, concurrent_retry,
    conflicting_revision, reader_freshness, interrupted_write, hybrid_retrieval,
    transaction_rollback, identity_conflicts, embedding_failure, index_atomicity,
)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=list(CASES), action="append")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    root = args.output / "databases"
    root.mkdir(exist_ok=True)
    summary = {"python": platform.python_version(), "platform": platform.platform(), "sqlite": sqlite3.sqlite_version, "sqlite_vec": importlib.metadata.version("sqlite-vec"), "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "adapter_sha256": hashlib.sha256((HERE / "sqlite_store.py").read_bytes()).hexdigest(), "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(), "results": {}}
    for name in args.case or CASES:
        started = time.monotonic()
        try:
            result = CASES[name](root)
            result["status"] = "pass" if result["pass"] else "contract-failure"
        except Exception:
            result = {"status": "infrastructure-error", "error": traceback.format_exc()}
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        summary["results"][name] = result
        save(args.output / f"{name}.json", result)
        print(json.dumps({"case": name, "status": result["status"], "duration_seconds": result["duration_seconds"]}), flush=True)
    save(args.output / "summary.json", summary)
    return 0 if all(result["status"] == "pass" for result in summary["results"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
