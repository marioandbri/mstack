"""Experimental cooperative adapter. Not installed or used by active capture."""
from contextlib import contextmanager
import fcntl
from pathlib import Path
import time


def literal(value):
    return "'" + value.replace("'", "''") + "'"


class GuardedStore:
    def __init__(self, uri):
        self.uri = Path(uri).resolve()

    @contextmanager
    def locked_table(self):
        from datetime import timedelta
        import lancedb

        # All cooperating writers use one canonical path and refresh under the lock.
        with (self.uri / ".mstack-probe.lock").open("a+b") as lock:
            deadline = time.monotonic() + 5
            while True:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Storage writer lock deadline exceeded") from None
                    time.sleep(0.01)
            try:
                yield lancedb.connect(
                    str(self.uri), read_consistency_interval=timedelta(0),
                ).open_table("observations")
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def capture(self, original):
        with self.locked_table() as target:
            matches = target.search().where(
                "operation_id = " + literal(original["operation_id"]),
            ).limit(2).to_list()
            if matches:
                immutable = set(original) - {"revision", "decision", "vector"}
                same = len(matches) == 1 and all(matches[0][key] == original[key] for key in immutable)
                return {"status": "already-captured" if same else "operation-conflict", "id": original["id"]}
            if target.count_rows("id = " + literal(original["id"])):
                return {"status": "identity-conflict", "id": original["id"]}
            target.add([original])
            return {"status": "acknowledged", "id": original["id"]}

    def decide(self, identity, expected_revision, decision):
        with self.locked_table() as target:
            result = target.update(
                where=f"id = {literal(identity)} AND revision = {expected_revision}",
                values={"decision": decision, "revision": expected_revision + 1},
            )
            return {
                "status": "accepted" if result.rows_updated == 1 else "conflict",
                "rows_updated": result.rows_updated, "version": result.version,
            }
