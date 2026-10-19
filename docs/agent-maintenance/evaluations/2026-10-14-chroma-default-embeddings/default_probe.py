"""Repeat the local persistence experiment with automatic real default embeddings."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import math
from pathlib import Path
import platform
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-10-13-lancedb"))
from probe import record
from default_actor import actor

CONTEXT = mp.get_context("spawn")
PROTOCOL = json.loads((HERE / "protocol.json").read_text())
CORPUS = json.loads((HERE / "corpus.json").read_text())
CACHE = None


def point(identity, writer="a", **kwargs):
    return record(identity, writer, **kwargs)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def finish(process, pipe, timeout=120):
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
    process = CONTEXT.Process(target=actor, args=(str(path), operation, payload, None, child, str(CACHE), guarded))
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


def coordinator(path, operation, payload, barrier, pipe, cache):
    global CACHE
    CACHE = Path(cache)
    try:
        barrier.wait(timeout=60)
        # This process never imports Chroma. The lock covers SDK initialization,
        # operations, public close(), and child process exit, not just add().
        with (Path(path) / ".mstack-owner.lock").open("a+b") as lock:
            deadline = time.monotonic() + 125
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
        args = (str(path), operation, payload, barrier, child, str(CACHE))
        process = CONTEXT.Process(target=target, args=args)
        process.start()
        child.close()
        processes.append(process)
        pipes.append(parent)
    deadline = time.monotonic() + 250
    return [finish(process, pipe, max(0, deadline - time.monotonic())) for process, pipe in zip(processes, pipes)]


def valid_vector(vector):
    return len(vector) == 384 and all(math.isfinite(v) for v in vector) and abs(sum(v * v for v in vector) ** 0.5 - 1) < 1e-5


def matches(actual, expected):
    return len(actual) == len(expected) and all(valid_vector(row["vector"]) for row in actual) and sorted([dict(row, vector=None) for row in actual], key=lambda row: row["id"]) == sorted(expected, key=lambda row: row["id"])


def capture_documents(root, mode):
    path = root / "automatic-embedding"
    create(path)
    original = record("origin-001", text="Approval was requested again after it had been granted.")
    outcome = invoke(path, "capture", [original], guarded=mode != "native")
    rows = read(path)
    return {"pass": matches(rows, [original]), "actual_count": len(rows), "embedding_dimensions": [len(r["vector"]) for r in rows], "outcome": outcome, "supplied_vectors": False}


def concurrent_append(root, mode):
    repetitions = []
    for n in range(3):
        path = root / f"append-{n}"
        create(path)
        payloads = [[point(f"{writer}-{i:02d}", writer) for i in range(30)] for writer in ("a", "b")]
        outcomes = pair(path, "capture", payloads, mode)
        actual = read(path)
        expected = payloads[0] + payloads[1]
        ok = not any("error" in result for result in outcomes) and matches(actual, expected)
        repetitions.append({"pass": ok, "actual_count": len(actual), "expected_count": 60, "workers": outcomes})
    return {"pass": all(result["pass"] for result in repetitions), "repetitions": repetitions, "supplied_vectors": False}


def sequential_retry(root, mode):
    path = root / "sequential"
    create(path)
    original = point("retry-001")
    outcomes = [invoke(path, "capture", [original], guarded=mode != "native") for _ in range(4)]
    rows = read(path)
    return {"pass": matches(rows, [original]) and not any("error" in outcome for outcome in outcomes), "actual_count": len(rows), "outcomes": outcomes}


def concurrent_retry(root, mode):
    repetitions = []
    for n in range(10):
        path = root / f"retry-{n}"
        create(path)
        original = point("shared-operation")
        outcomes = pair(path, "capture", [[original], [original]], mode)
        actual = read(path)
        repetitions.append({"pass": matches(actual, [original]) and not any("error" in result for result in outcomes), "actual_count": len(actual), "expected_count": 1, "workers": outcomes})
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
    return {"pass": matches(rows, [original]) and "error" not in outcome, "fresh_process_count": len(rows)}


def interrupted_write(root, mode):
    repetitions = []
    for n, delay in enumerate((0.0, 0.005, 0.02)):
        path = root / f"interrupted-{n}"
        limits = create(path)
        batch_size = min(12000, limits["max_batch_size"])
        payload = {"prefix": [point(f"confirmed-{i}") for i in range(6)], "batch": [point(f"batch-{i:05d}", text="Synthetic batch record " + "x" * 1024) for i in range(batch_size)]}
        parent, child = CONTEXT.Pipe(duplex=False)
        process = CONTEXT.Process(target=actor, args=(str(path), "interrupted", payload, None, child, str(CACHE)))
        process.start()
        child.close()
        events, reached = [], False
        try:
            deadline = time.monotonic() + 120
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
    originals = [record(item["id"], text=item["text"], project=item["project"]) for item in CORPUS["records"]]
    create(path, originals)
    result = invoke(path, "retrieval", CORPUS)
    queries = result.get("queries", [])
    ok = len(queries) == 8 and all(q["hit_at_3"] and not any(identity.startswith("other-") for identity in q["ids"]) for q in queries)
    metrics = {language: {"queries": len([q for q in queries if q["language"] == language]), "hit_at_1": sum(q["hit_at_1"] for q in queries if q["language"] == language), "hit_at_3": sum(q["hit_at_3"] for q in queries if q["language"] == language), "mean_recall_at_3": sum(q["recall_at_3"] for q in queries if q["language"] == language) / 4} for language in ("en", "es")}
    return {"pass": ok, "queries": result, "metrics": metrics, "corpus_size": len(originals), "supplied_vectors": False, "no_database_semantic_quality_comparison": True}


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
    ok = matches(rows, [original]) and statuses == ["returned", "already-captured", "operation-conflict", "identity-conflict"]
    return {"pass": ok, "statuses": statuses, "original_unchanged": matches(rows, [original]), "outcomes": outcomes}


def embedding_failure(root, mode):
    path = root / "invalid-vector"
    original = point("vector-001")
    create(path, [original])
    result = invoke(path, "embedding_failure", [original])
    return {"pass": bool(result.get("error_message")) and result.get("unchanged") and matches(read(path), [original]), "outcome": result, "original_embedding_generated_automatically": True}


def capture_embedding_unavailable(root, mode):
    path = root / "embedding-unavailable"
    create(path)
    original = record("failure-origin", text="A valuable observation must survive an embedding failure.")
    outcome = invoke(path, "capture_embedding_unavailable", [original])
    actual = read(path)
    assert outcome.get("rejected") and outcome.get("persisted_rows") == 0 and actual == [], outcome
    return {"pass": matches(actual, [original]), "expected_raw_count": 1, "actual_count": len(actual), "outcome": outcome, "deliberate_fault_injection": True, "interpretation": "Automatic embedding is performed before the SDK persists the document; this is not deferred raw capture"}


CASES = {function.__name__: function for function in (
    capture_documents, concurrent_append, sequential_retry, concurrent_retry,
    conflicting_revision, reader_freshness, interrupted_write, retrieval,
    identity_conflicts, embedding_failure, capture_embedding_unavailable,
)}


def main():
    global CACHE
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["native", "serialized-owner"], default="native")
    parser.add_argument("--case", choices=list(CASES), action="append")
    args = parser.parse_args()
    CACHE = args.output / "model-cache" / "all-MiniLM-L6-v2"
    assert (CACHE / "onnx" / "model.onnx").exists(), "Run bootstrap first"
    root = args.output / args.mode / "databases"
    root.mkdir(parents=True, exist_ok=True)
    summary = {"mode": args.mode, "python": platform.python_version(), "platform": platform.platform(), "chromadb": importlib.metadata.version("chromadb"), "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "actor_sha256": hashlib.sha256((HERE / "default_actor.py").read_bytes()).hexdigest(), "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(), "corpus_sha256": hashlib.sha256((HERE / "corpus.json").read_bytes()).hexdigest(), "bootstrap_sha256": hashlib.sha256((args.output / "bootstrap.json").read_bytes()).hexdigest(), "results": {}}
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
