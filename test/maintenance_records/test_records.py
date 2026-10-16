import base64
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from records import RecordError, RecordStore


def observation(identity="OBS-1", scope="project"):
    return json.dumps({"schemaVersion": 1, "id": identity, "status": "inbox", "scope": scope,
                       "basis": "observed-failure", "observation": "No cargó las convenciones del proyecto.",
                       "evidence": [{"source": "session:origin/turn:7", "summary": "El usuario señaló la omisión."}],
                       "suspectedCause": None}, ensure_ascii=False, indent=2).encode() + b"\n"


def concurrent_writer(path, barrier, results, identity, operation):
    try:
        store = RecordStore(path, "project-identity")
        barrier.wait(timeout=10)
        store.initialize()
        results.put(store.capture(operation, observation(identity)))
    except Exception as error:
        results.put({"error": str(error)})


def interrupted_writer(path, channel, after_commit):
    store = RecordStore(path, "project-identity")
    if after_commit:
        store.capture("interrupted", observation("INTERRUPTED"))
        channel.send("committed")
        channel.recv()
    else:
        def pending_batch():
            yield "interrupted", observation("INTERRUPTED"), None
            channel.send("before-commit")
            channel.recv()
        store.capture_many(pending_batch())


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "records.sqlite3"
        self.store = RecordStore(self.path, "project-identity")
        self.store.initialize()

    def test_capture_preserves_raw_bytes_and_origin_separately_from_capture(self):
        raw = observation()
        provenance = {"origin": [{"harness": "pi", "session_id": "origin-session", "event_id": "7"}],
                      "capture": {"harness": "codex", "session_id": "capture-session"}}
        self.assertEqual(self.store.capture("operation-1", raw, provenance)["status"], "captured")
        recovered = RecordStore(self.path, "project-identity").get("OBS-1")
        self.assertEqual(base64.b64decode(recovered["raw_base64"]), raw)
        self.assertEqual(recovered["provenance"]["origin"][0]["session_id"], "origin-session")
        self.assertEqual(recovered["provenance"]["capture"]["session_id"], "capture-session")
        self.assertIsNone(recovered["provenance"]["origin"][0]["harness_version"])
        self.assertEqual(recovered["pending"], ["classification", "reconstruction", "indexing"])
        self.assertEqual(self.store.capture("operation-1", raw, provenance)["status"], "already-captured")
        self.assertEqual(self.store.capture("operation-1", raw, recovered["provenance"])["status"], "already-captured")
        self.assertEqual(len(self.store.list()), 1)
        with self.assertRaisesRegex(RecordError, "operation-conflict"):
            self.store.capture("operation-1", observation("OBS-2"), provenance)
        with self.assertRaisesRegex(RecordError, "identity-conflict"):
            self.store.capture("operation-2", observation(), provenance)
        self.assertEqual(base64.b64decode(self.store.get("OBS-1")["raw_base64"]), raw)

    def test_parallel_distinct_writes_and_same_operation_retry_do_not_lose_originals(self):
        context = multiprocessing.get_context("spawn")
        for same in (False, True):
            barrier = context.Barrier(2); results = context.Queue()
            processes = [context.Process(target=concurrent_writer, args=(self.path, barrier, results, "SAME" if same else f"PARALLEL-{i}", "same-operation" if same else f"parallel-{i}")) for i in range(2)]
            for process in processes: process.start()
            for process in processes:
                process.join(15)
                self.assertFalse(process.is_alive())
                self.assertEqual(process.exitcode, 0)
            statuses = sorted(results.get(timeout=2)["status"] for _ in processes)
            self.assertEqual(statuses, ["already-captured", "captured"] if same else ["captured", "captured"])
            results.close(); results.join_thread()
        self.assertEqual([row["id"] for row in self.store.list()], ["PARALLEL-0", "PARALLEL-1", "SAME"])

    def test_stale_update_cannot_replace_a_saved_decision_or_original(self):
        self.store.capture("capture", observation())
        evidence = {"source": "user:message:8", "answer": "Aplazar esta observación."}
        result = self.store.transition("OBS-1", 0, "deferred", evidence, "decision-1")
        self.assertEqual(result["revision"], 1)
        with self.assertRaisesRegex(RecordError, "revision-conflict"):
            self.store.transition("OBS-1", 0, "resolved", evidence, "decision-2")
        self.assertEqual(self.store.get("OBS-1")["state"], "deferred")
        self.assertEqual(self.store.history("OBS-1", "state")[0]["payload"]["evidence"], evidence)
        self.assertEqual(base64.b64decode(self.store.get("OBS-1")["raw_base64"]), observation())
        with self.assertRaisesRegex(RecordError, "project-mismatch"):
            RecordStore(self.path, "other-project").get("OBS-1")

    def test_process_interruption_before_commit_rolls_back_and_after_commit_is_recoverable(self):
        context = multiprocessing.get_context("spawn")
        for after_commit in (False, True):
            parent, child = context.Pipe()
            process = context.Process(target=interrupted_writer, args=(self.path, child, after_commit))
            process.start(); child.close()
            try:
                self.assertTrue(parent.poll(10))
                self.assertEqual(parent.recv(), "committed" if after_commit else "before-commit")
                process.kill(); process.join(5)
                self.assertFalse(process.is_alive())
                self.assertEqual(len(self.store.list()), 1 if after_commit else 0)
            finally:
                if process.is_alive(): process.kill(); process.join(5)
                parent.close()
        self.assertEqual(self.store.capture("interrupted", observation("INTERRUPTED"))["status"], "already-captured")

    def test_cli_capture_and_reopen_need_no_classifier_summary_or_vectors(self):
        original_file = Path(self.temp.name) / "original.json"
        original_file.write_bytes(observation("CLI"))
        cli = Path(__file__).resolve().parents[2] / "skills/reflect/runtime/record_cli.py"
        command = [sys.executable, str(cli), "--database", str(self.path), "--project", "project-identity"]
        capture = subprocess.run(command + ["capture", "--operation", "cli-operation", "--original", str(original_file)], capture_output=True, text=True)
        self.assertEqual(capture.returncode, 0, capture.stderr)
        self.assertEqual(json.loads(capture.stdout)["next"], "return-to-task")
        read = subprocess.run(command + ["get", "--id", "CLI"], capture_output=True, text=True, check=True)
        value = json.loads(read.stdout)
        self.assertEqual(base64.b64decode(value["raw_base64"]), observation("CLI"))
        self.assertEqual(value["pending"], ["classification", "reconstruction", "indexing"])
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)

    def test_invalid_provenance_cannot_be_silently_replaced_with_unknowns(self):
        with self.assertRaisesRegex(RecordError, "invalid-provenance"):
            self.store.capture("bad-origin", observation(), [])
        self.assertEqual(self.store.list(), [])

    def test_concurrent_initialization_and_first_capture_use_one_project_database(self):
        context = multiprocessing.get_context("spawn")
        path = self.path.parent / "first-capture.sqlite3"
        barrier = context.Barrier(2); results = context.Queue()
        processes = [context.Process(target=concurrent_writer, args=(path, barrier, results, f"FIRST-{n}", f"first-{n}")) for n in range(2)]
        try:
            for process in processes: process.start()
            for process in processes:
                process.join(15)
                self.assertFalse(process.is_alive())
                self.assertEqual(process.exitcode, 0)
            outcomes = [results.get(timeout=2) for _ in processes]
            self.assertTrue(all(row.get("status") == "captured" for row in outcomes), outcomes)
            self.assertEqual(len(RecordStore(path, "project-identity").list()), 2)
        finally:
            for process in processes:
                if process.is_alive(): process.kill(); process.join(5)
            results.close(); results.join_thread()


if __name__ == "__main__":
    unittest.main()
