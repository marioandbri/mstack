"""Synthetic probes through the public LanceDB Python API, in separate processes."""
from __future__ import annotations

import argparse
from datetime import timedelta
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text())
CONTEXT = mp.get_context("spawn")


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def schema():
    import pyarrow as pa
    return pa.schema([
        ("id", pa.string()), ("operation_id", pa.string()),
        ("project", pa.string()), ("harness", pa.string()),
        ("source_session", pa.string()), ("capture_session", pa.string()),
        ("event_id", pa.string()), ("text", pa.string()),
        ("content_sha256", pa.string()), ("revision", pa.int64()),
        ("decision", pa.string()), ("vector", pa.list_(pa.float32(), 3)),
    ])


def record(identity, writer="a", text="Synthetic observation", vector=None, project="mstack"):
    return {
        "id": identity, "operation_id": identity, "project": project,
        "harness": "synthetic-python", "source_session": "source-" + writer,
        "capture_session": "capture-" + writer, "event_id": "event-" + identity,
        "text": text, "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "revision": 0, "decision": "pending", "vector": vector,
    }


def connect(uri, refresh=True):
    import lancedb
    if refresh:
        return lancedb.connect(str(uri), read_consistency_interval=timedelta(0))
    return lancedb.connect(str(uri))


def table(uri, refresh=True):
    return connect(uri, refresh).open_table("observations")


def create(uri, rows=()):
    result = connect(uri).create_table("observations", schema=schema())
    if rows:
        result.add(list(rows))
    return result


def read(uri):
    return table(uri).to_arrow().to_pylist()


def worker(uri, operation, payload, barrier, pipe, mode):
    try:
        target = table(uri)
        before = target.count_rows()
        barrier.wait(timeout=30)
        results = []
        for item in payload:
            if mode == "guarded":
                from guarded_store import GuardedStore
                store = GuardedStore(uri)
                result = store.capture(item) if operation in ("append", "merge") else store.decide(**item)
                results.append(result)
            elif operation == "append":
                target.add([item])
                results.append({"status": "acknowledged", "id": item["id"]})
            elif operation == "merge":
                outcome = target.merge_insert("operation_id").when_not_matched_insert_all().execute([item])
                results.append({"status": "acknowledged", "id": item["id"], "sdk_result": str(outcome)})
            elif operation == "decide":
                outcome = target.update(
                    where=f"id = '{item['identity']}' AND revision = {item['expected_revision']}",
                    values={"decision": item["decision"], "revision": item["expected_revision"] + 1},
                )
                results.append({
                    "status": "accepted" if outcome.rows_updated == 1 else "conflict",
                    "rows_updated": outcome.rows_updated, "version": outcome.version,
                })
            else:
                raise ValueError(operation)
        pipe.send({"before_rows": before, "results": results, "pid": os.getpid()})
    except BaseException:
        pipe.send({"error": traceback.format_exc(), "pid": os.getpid()})
    finally:
        pipe.close()


def run_workers(uri, operation, payloads, mode="native"):
    barrier = CONTEXT.Barrier(2)
    processes = []
    pipes = []
    for payload in payloads:
        parent, child = CONTEXT.Pipe(duplex=False)
        process = CONTEXT.Process(target=worker, args=(str(uri), operation, payload, barrier, child, mode))
        process.start()
        child.close()
        processes.append(process)
        pipes.append(parent)
    deadline = time.monotonic() + PROTOCOL["worker_deadline_seconds"]
    outcomes = []
    for process, pipe in zip(processes, pipes):
        remaining = max(0, deadline - time.monotonic())
        if pipe.poll(remaining):
            try:
                outcome = pipe.recv()
            except EOFError:
                outcome = {"error": "Worker exited without a result"}
        else:
            outcome = {"error": "Worker deadline exceeded"}
            process.kill()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join(timeout=5)
            outcome["cleanup_error"] = "Worker did not exit after sending a result"
        outcome["exitcode"] = process.exitcode
        outcomes.append(outcome)
        pipe.close()
    return outcomes


def capture_without_embedding(root, mode):
    uri = root / "capture"
    original = record("origin-001", text="Approval was requested again after it had been granted.")
    create(uri)
    if mode == "native":
        table(uri).add([original])
    else:
        from guarded_store import GuardedStore
        GuardedStore(uri).capture(original)
    actual = read(uri)
    return {"pass": actual == [original], "rows": actual, "expected_count": 1}


def concurrent_append(root, mode):
    repetitions = []
    for iteration in range(3):
        uri = root / f"append-{iteration}"
        create(uri)
        payloads = [[record(f"{writer}-{n:02d}", writer) for n in range(30)] for writer in ("a", "b")]
        outcomes = run_workers(uri, "append", payloads, mode)
        actual = read(uri)
        expected = payloads[0] + payloads[1]
        ok = not any("error" in x for x in outcomes) and sorted(actual, key=lambda x: x["id"]) == sorted(expected, key=lambda x: x["id"])
        repetitions.append({"pass": ok, "expected_count": 60, "actual_count": len(actual), "workers": outcomes})
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def sequential_retry(root, mode):
    uri = root / "retry-sequential"
    create(uri)
    original = record("retry-001")
    results = []
    for _ in range(4):
        if mode == "native":
            result = table(uri).merge_insert("operation_id").when_not_matched_insert_all().execute([original])
            results.append(str(result))
        else:
            from guarded_store import GuardedStore
            results.append(GuardedStore(uri).capture(original))
    actual = read(uri)
    return {"pass": actual == [original], "actual_count": len(actual), "outcomes": results}


def concurrent_retry(root, mode):
    repetitions = []
    for iteration in range(10):
        uri = root / f"retry-{iteration}"
        create(uri)
        original = record("shared-operation")
        outcomes = run_workers(uri, "merge", [[original], [original]], mode)
        actual = read(uri)
        repetitions.append({
            "pass": not any("error" in x for x in outcomes) and actual == [original],
            "expected_count": 1, "actual_count": len(actual), "workers": outcomes,
        })
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def conflicting_revision(root, mode):
    repetitions = []
    for iteration in range(10):
        uri = root / f"decision-{iteration}"
        create(uri, [record("review-001")])
        payloads = [[{"identity": "review-001", "expected_revision": 0, "decision": decision}] for decision in ("keep", "defer")]
        outcomes = run_workers(uri, "decide", payloads, mode)
        actual = read(uri)
        statuses = [x["results"][0]["status"] for x in outcomes if "results" in x]
        ok = sorted(statuses) == ["accepted", "conflict"] and len(actual) == 1 and actual[0]["revision"] == 1
        repetitions.append({"pass": ok, "statuses": statuses, "final_revision": actual[0]["revision"], "final_decision": actual[0]["decision"], "workers": outcomes})
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def reader_freshness(root, mode):
    uri = root / "freshness"
    create(uri)
    default_reader = table(uri, refresh=False)
    refreshing_reader = table(uri)
    initial = [default_reader.count_rows(), refreshing_reader.count_rows()]
    original = record("writer-001")
    outcomes = run_workers(uri, "append", [[original], []], mode)
    default_count = default_reader.count_rows()
    fresh_count = refreshing_reader.count_rows()
    default_reader.checkout_latest()
    manual_count = default_reader.count_rows()
    return {
        "pass": initial == [0, 0] and fresh_count == manual_count == 1 and not any("error" in x for x in outcomes),
        "initial_counts": initial, "default_count_after_other_process_commit": default_count,
        "refreshing_count": fresh_count, "manual_refresh_count": manual_count, "workers": outcomes,
    }


def interrupted_worker(uri, pipe):
    try:
        target = table(uri)
        for n in range(6):
            target.add([record(f"confirmed-{n}")])
            pipe.send({"event": "acknowledged", "id": f"confirmed-{n}"})
        batch = [record(f"batch-{n:05d}", text="Synthetic batch record " + "x" * 1024) for n in range(12000)]
        pipe.send({"event": "batch_started"})
        target.add(batch)
        pipe.send({"event": "batch_acknowledged"})
    except BaseException:
        pipe.send({"error": traceback.format_exc()})
    finally:
        pipe.close()


def interrupted_write(root, mode):
    if mode != "native":
        return {"status": "not-repeated", "reason": "Native table commit probe; guarded API interruption is a separate case"}
    repetitions = []
    for iteration, delay in enumerate((0.0, 0.005, 0.02)):
        uri = root / f"interrupted-{iteration}"
        create(uri)
        parent, child = CONTEXT.Pipe(duplex=False)
        process = CONTEXT.Process(target=interrupted_worker, args=(str(uri), child))
        process.start()
        child.close()
        events = []
        deadline = time.monotonic() + 45
        reached = False
        while time.monotonic() < deadline and parent.poll(max(0, deadline - time.monotonic())):
            event = parent.recv()
            events.append(event)
            if event.get("event") == "batch_started":
                reached = True
                break
            if "error" in event:
                break
        time.sleep(delay)
        process.kill()
        process.join(timeout=5)
        parent.close()
        rows = read(uri)
        confirmed = {r["id"] for r in rows if r["id"].startswith("confirmed-")}
        batch_ids = {r["id"] for r in rows if r["id"].startswith("batch-")}
        expected_batch = {f"batch-{n:05d}" for n in range(12000)}
        confirmed_ok = confirmed == {f"confirmed-{n}" for n in range(6)}
        atomic_ok = not batch_ids or batch_ids == expected_batch
        repetitions.append({
            "pass": reached and confirmed_ok and atomic_ok and process.exitcode == -signal.SIGKILL,
            "delay_seconds": delay, "exitcode": process.exitcode,
            "confirmed_rows": len(confirmed), "interrupted_batch_rows": len(batch_ids), "events": events,
            "injection": "After public batch-start notification; exact native commit phase not observable",
        })
    return {"pass": all(x["pass"] for x in repetitions), "repetitions": repetitions}


def hybrid_retrieval(root, mode):
    uri = root / "retrieval"
    rows = [
        record("approval", text="approval permission requested again", vector=[1.0, 0.0, 0.0]),
        record("tests", text="regression tests preserve behavior", vector=[0.0, 1.0, 0.0]),
        record("references", text="documentation reference unavailable", vector=[0.0, 0.0, 1.0]),
        record("other-project", text="approval permission requested again", vector=[1.0, 0.0, 0.0], project="other"),
        record("pending-vector", text="approval pending embedding"),
    ]
    target = create(uri, rows)
    target.create_fts_index("text")
    vector = target.search([1.0, 0.0, 0.0]).where("project = 'mstack'").limit(1).to_list()
    lexical = target.search("approval", query_type="fts").where("project = 'mstack'").limit(10).to_list()
    hybrid = target.search(query_type="hybrid").vector([1.0, 0.0, 0.0]).text("approval").where("project = 'mstack'").limit(3).to_list()
    ids = lambda results: [r["id"] for r in results]
    ok = ids(vector) == ["approval"] and set(ids(lexical)) == {"approval", "pending-vector"} and "approval" in ids(hybrid) and "other-project" not in ids(hybrid)
    return {"pass": ok, "vector_ids": ids(vector), "lexical_ids": ids(lexical), "hybrid_ids": ids(hybrid), "fixed_vectors_only": True}


CASES = {function.__name__: function for function in (
    capture_without_embedding, concurrent_append, sequential_retry, concurrent_retry,
    conflicting_revision, reader_freshness, interrupted_write, hybrid_retrieval,
)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=list(CASES), action="append")
    parser.add_argument("--mode", choices=["native", "guarded"], default="native")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    database_root = args.output / args.mode / "databases"
    database_root.mkdir(parents=True, exist_ok=True)
    versions = {name: importlib.metadata.version(name) for name in ("lancedb", "pyarrow", "numpy", "pydantic")}
    summary = {"mode": args.mode, "python": platform.python_version(), "platform": platform.platform(), "packages": versions, "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(), "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "results": {}}
    for case in args.case or CASES:
        started = time.monotonic()
        try:
            result = CASES[case](database_root, args.mode)
            if "pass" in result:
                result["status"] = "pass" if result["pass"] else "contract-failure"
        except Exception:
            result = {"status": "infrastructure-error", "error": traceback.format_exc()}
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        summary["results"][case] = result
        save(args.output / args.mode / f"{case}.json", result)
        print(json.dumps({"mode": args.mode, "case": case, "status": result["status"], "duration_seconds": result["duration_seconds"]}), flush=True)
    save(args.output / args.mode / "summary.json", summary)
    return 0 if all(result["status"] in ("pass", "not-repeated") for result in summary["results"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
