"""Compatibility experiment for embedded Chroma, including process ownership."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
from pathlib import Path
import platform
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-10-13-lancedb"))
from probe import record
from chroma_actor import actor

CONTEXT = mp.get_context("spawn")
PROTOCOL = json.loads((HERE / "protocol.json").read_text())


def point(identity, writer="a", **kwargs):
    return record(identity, writer, vector=[1.0, 0.0, 0.0], **kwargs)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def finish(process, pipe, timeout=45):
    if pipe.poll(timeout):
        try:
            outcome = pipe.recv()
        except EOFError:
            outcome = {"error": "SDK process exited without a result"}
    else:
        process.kill()
        outcome = {"error": "SDK process deadline exceeded"}
    process.join(5)
    if process.is_alive():
        process.kill()
        process.join(5)
        outcome["cleanup_error"] = "SDK process did not exit after result"
    outcome["exitcode"] = process.exitcode
    pipe.close()
    return outcome


def invoke(path, operation, payload=(), guarded=False):
    parent, child = CONTEXT.Pipe(duplex=False)
    process = CONTEXT.Process(target=actor, args=(str(path), operation, payload, None, child, guarded))
    process.start()
    child.close()
    return finish(process, parent)


def create(path, originals=()):
    path.mkdir(parents=True)
    outcome = invoke(path, "create")
    assert outcome.get("created") and outcome["exitcode"] == 0, outcome
    if originals:
        outcome = invoke(path, "capture", list(originals))
        assert "error" not in outcome and outcome["exitcode"] == 0, outcome
    return outcome


def read(path):
    outcome = invoke(path, "read")
    assert "error" not in outcome and outcome["exitcode"] == 0, outcome
    return outcome["rows"]


def coordinator(path, operation, payload, barrier, pipe):
    try:
        barrier.wait(timeout=30)
        # This process never imports Chroma. The lock covers SDK initialization,
        # operations, public close(), and child process exit, not just add().
        with (Path(path) / ".mstack-owner.lock").open("a+b") as lock:
            deadline = time.monotonic() + 35
            while True:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Chroma owner deadline exceeded")
                    time.sleep(0.01)
            try:
                pipe.send(invoke(path, operation, payload, guarded=True))
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    except BaseException:
        pipe.send({"error": traceback.format_exc()})
    finally:
        pipe.close()


def pair(path, operation, payloads, mode):
    barrier = CONTEXT.Barrier(2)
    processes, pipes = [], []
    for payload in payloads:
        parent, child = CONTEXT.Pipe(duplex=False)
        target = actor if mode == "native" else coordinator
        args = (str(path), operation, payload, barrier, child)
        process = CONTEXT.Process(target=target, args=args)
        process.start()
        child.close()
        processes.append(process)
        pipes.append(parent)
    deadline = time.monotonic() + 90
    return [finish(process, pipe, max(0, deadline - time.monotonic())) for process, pipe in zip(processes, pipes)]


def capture_without_embedding(root, mode):
    path = root / "missing-embedding"
    create(path)
    original = record("origin-001", text="Approval was requested again after it had been granted.")
    outcome = invoke(path, "missing_embedding", [original], guarded=mode != "native")
    rows = read(path)
    return {"pass": rows == [original], "actual_count": len(rows), "outcome": outcome, "no_dummy_vector": True}


def concurrent_append(root, mode):
    repetitions = []
    for n in range(3):
        path = root / f"append-{n}"
        create(path)
        payloads = [[point(f"{writer}-{i:02d}", writer) for i in range(30)] for writer in ("a", "b")]
        outcomes = pair(path, "capture", payloads, mode)
        actual = read(path)
        expected = payloads[0] + payloads[1]
        ok = not any("error" in result for result in outcomes) and sorted(actual, key=lambda x: x["id"]) == sorted(expected, key=lambda x: x["id"])
        repetitions.append({"pass": ok, "actual_count": len(actual), "expected_count": 60, "workers": outcomes})
    return {"pass": all(result["pass"] for result in repetitions), "repetitions": repetitions, "explicit_vector_fixtures": True}


def sequential_retry(root, mode):
    path = root / "sequential"
    create(path)
    original = point("retry-001")
    outcomes = [invoke(path, "capture", [original], guarded=mode != "native") for _ in range(4)]
    rows = read(path)
    return {"pass": rows == [original] and not any("error" in outcome for outcome in outcomes), "actual_count": len(rows), "outcomes": outcomes}


def concurrent_retry(root, mode):
    repetitions = []
    for n in range(10):
        path = root / f"retry-{n}"
        create(path)
        original = point("shared-operation")
        outcomes = pair(path, "capture", [[original], [original]], mode)
        actual = read(path)
        repetitions.append({"pass": actual == [original] and not any("error" in result for result in outcomes), "actual_count": len(actual), "expected_count": 1, "workers": outcomes})
    return {"pass": all(result["pass"] for result in repetitions), "repetitions": repetitions}


def conflicting_revision(root, mode):
    repetitions = []
    for n in range(10):
        path = root / f"decision-{n}"
        create(path, [point("review-001")])
        payloads = [[{"identity": "review-001", "expected_revision": 0, "decision": decision}] for decision in ("keep", "defer")]
        outcomes = pair(path, "decide", payloads, mode)
        statuses = [result["results"][0]["status"] for result in outcomes if "results" in result]
        rows = read(path)
        ok = sorted(statuses) == ["accepted", "conflict"] and len(rows) == 1 and rows[0]["revision"] == 1
        repetitions.append({"pass": ok, "statuses": statuses, "final_revision": rows[0]["revision"], "final_decision": rows[0]["decision"], "workers": outcomes})
    return {"pass": all(result["pass"] for result in repetitions), "repetitions": repetitions}


def reader_freshness(root, mode):
    path = root / "freshness"
    create(path)
    original = point("writer-001")
    outcome = invoke(path, "capture", [original], guarded=mode != "native")
    rows = read(path)
    return {"pass": rows == [original] and "error" not in outcome, "fresh_process_count": len(rows)}


def interrupted_write(root, mode):
    repetitions = []
    for n, delay in enumerate((0.0, 0.005, 0.02)):
        path = root / f"interrupted-{n}"
        limits = create(path)
        batch_size = min(12000, limits["max_batch_size"])
        payload = {"prefix": [point(f"confirmed-{i}") for i in range(6)], "batch": [point(f"batch-{i:05d}", text="Synthetic batch record " + "x" * 1024) for i in range(batch_size)]}
        parent, child = CONTEXT.Pipe(duplex=False)
        process = CONTEXT.Process(target=actor, args=(str(path), "interrupted", payload, None, child))
        process.start()
        child.close()
        events, reached = [], False
        try:
            deadline = time.monotonic() + 45
            while parent.poll(max(0, deadline - time.monotonic())):
                event = parent.recv()
                events.append(event)
                if event.get("event") == "batch_started":
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
        rows = read(path)
        confirmed = {row["id"] for row in rows if row["id"].startswith("confirmed-")}
        batches = {row["id"] for row in rows if row["id"].startswith("batch-")}
        ok = reached and confirmed == {f"confirmed-{i}" for i in range(6)} and (not batches or batches == {f"batch-{i:05d}" for i in range(batch_size)}) and process.exitcode == -signal.SIGKILL
        repetitions.append({"pass": ok, "confirmed_rows": len(confirmed), "batch_rows": batch_size, "interrupted_batch_rows": len(batches), "events": events, "exitcode": process.exitcode})
    return {"pass": all(result["pass"] for result in repetitions), "repetitions": repetitions, "scope": "One writer only; batch bounded by SDK maximum"}


def retrieval(root, mode):
    path = root / "retrieval"
    rows = [
        record("approval", text="approval permission requested again", vector=[1.0, 0.0, 0.0]),
        record("tests", text="regression tests preserve behavior", vector=[0.0, 1.0, 0.0]),
        record("references", text="documentation reference unavailable", vector=[0.0, 0.0, 1.0]),
        record("other-project", text="approval permission requested again", vector=[1.0, 0.0, 0.0], project="other"),
    ]
    create(path, rows)
    result = invoke(path, "retrieval")
    ok = result.get("vector_ids") == ["approval"] and set(result.get("substring_ids", [])) == {"approval"} and result.get("combined_filter_ids") == ["approval"]
    return {"pass": ok, "queries": result, "missing_vector_fixture_excluded_and_reported": True, "no_hybrid_rank_fusion": True}


def identity_conflicts(root, mode):
    path = root / "identity"
    create(path)
    original = point("original-001")
    guarded = mode != "native"
    outcomes = [invoke(path, "capture", [r], guarded=guarded) for r in (
        original, original, point("original-001", text="Different incident with same operation ID"), dict(original, operation_id="another-operation"),
    )]
    rows = read(path)
    statuses = [result["results"][0]["status"] for result in outcomes if "results" in result]
    ok = rows == [original] and statuses == ["returned", "already-captured", "operation-conflict", "identity-conflict"]
    return {"pass": ok, "statuses": statuses, "original_unchanged": rows == [original], "outcomes": outcomes}


def embedding_failure(root, mode):
    path = root / "invalid-vector"
    original = point("vector-001")
    create(path, [original])
    result = invoke(path, "embedding_failure", [original])
    return {"pass": bool(result.get("error_message")) and result.get("unchanged") and read(path) == [original], "outcome": result, "requires_original_vector": True}


CASES = {function.__name__: function for function in (
    capture_without_embedding, concurrent_append, sequential_retry, concurrent_retry,
    conflicting_revision, reader_freshness, interrupted_write, retrieval,
    identity_conflicts, embedding_failure,
)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["native", "serialized-owner"], default="native")
    parser.add_argument("--case", choices=list(CASES), action="append")
    args = parser.parse_args()
    root = args.output / args.mode / "databases"
    root.mkdir(parents=True, exist_ok=True)
    summary = {"mode": args.mode, "python": platform.python_version(), "platform": platform.platform(), "chromadb": importlib.metadata.version("chromadb"), "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "actor_sha256": hashlib.sha256((HERE / "chroma_actor.py").read_bytes()).hexdigest(), "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(), "results": {}}
    for name in args.case or CASES:
        started = time.monotonic()
        try:
            result = CASES[name](root, args.mode)
            result["status"] = "pass" if result["pass"] else "contract-failure"
        except Exception:
            result = {"status": "infrastructure-error", "error": traceback.format_exc()}
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        summary["results"][name] = result
        save(args.output / args.mode / f"{name}.json", result)
        print(json.dumps({"mode": args.mode, "case": name, "status": result["status"], "duration_seconds": result["duration_seconds"]}), flush=True)
    save(args.output / args.mode / "summary.json", summary)
    return 0 if all(result["status"] == "pass" for result in summary["results"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
