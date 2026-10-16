"""Additional failure/retry checks through the experimental capture API."""
import argparse
import json
from pathlib import Path
import signal
import time

from guarded_store import GuardedStore
from probe import CONTEXT, create, read, record, save


def hold_lock(uri, pipe):
    with GuardedStore(uri).locked_table():
        pipe.send("locked")
        while True:
            time.sleep(1)


def waiting_capture(uri, pipe):
    pipe.send("starting")
    pipe.send(GuardedStore(uri).capture(record("after-terminated-writer")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = {}

    uri = args.output / "adapter-conflicts"
    create(uri)
    store = GuardedStore(uri)
    original = record("original-001")
    first = store.capture(original)
    repeated = store.capture(original)
    changed = record("original-001", text="Different incident with same operation ID")
    operation_conflict = store.capture(changed)
    collision = dict(original, operation_id="another-operation")
    identity_conflict = store.capture(collision)
    actual = read(uri)
    results["conflicts_preserve_original"] = {
        "pass": first["status"] == "acknowledged" and repeated["status"] == "already-captured"
        and operation_conflict["status"] == "operation-conflict"
        and identity_conflict["status"] == "identity-conflict" and actual == [original],
        "outcomes": [first, repeated, operation_conflict, identity_conflict],
        "original_unchanged": actual == [original],
    }

    uri = args.output / "adapter-lock-release"
    create(uri)
    holder_pipe, holder_child = CONTEXT.Pipe(duplex=False)
    waiter_pipe, waiter_child = CONTEXT.Pipe(duplex=False)
    holder = CONTEXT.Process(target=hold_lock, args=(str(uri), holder_child))
    waiter = CONTEXT.Process(target=waiting_capture, args=(str(uri), waiter_child))
    try:
        holder.start()
        holder_child.close()
        assert holder_pipe.poll(30) and holder_pipe.recv() == "locked"
        waiter.start()
        waiter_child.close()
        assert waiter_pipe.poll(30) and waiter_pipe.recv() == "starting"
        # The holder still owns the lock while the second process begins capture.
        holder.kill()
        holder.join(5)
        assert waiter_pipe.poll(30)
        outcome = waiter_pipe.recv()
        waiter.join(5)
        actual = read(uri)
        results["terminated_lock_holder"] = {
            "pass": holder.exitcode == -signal.SIGKILL and waiter.exitcode == 0
            and outcome["status"] == "acknowledged"
            and actual == [record("after-terminated-writer")],
            "holder_exitcode": holder.exitcode, "waiter_exitcode": waiter.exitcode,
            "capture": outcome, "actual_count": len(actual),
        }
    finally:
        for process in (holder, waiter):
            if process.pid and process.is_alive():
                process.kill()
                process.join(5)
        for pipe in (holder_pipe, waiter_pipe):
            pipe.close()

    save(args.output / "adapter-checks.json", results)
    for name, result in results.items():
        print(json.dumps({"case": name, "pass": result["pass"]}), flush=True)
    return 0 if all(result["pass"] for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
