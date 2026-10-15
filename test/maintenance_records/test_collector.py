import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from collector import CollectionError, collect_workspace, create_workspace


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "workspace"
        create_workspace(self.source, "attempt-1")

    def test_nested_skill_with_historical_0200_mode_exports_readable_bytes_and_hashes(self):
        path = self.source / ".agents/skills/example/SKILL.md"
        path.parent.mkdir(parents=True)
        body = b"---\nname: example\ndescription: Synthetic evaluation skill.\n---\n"
        path.write_bytes(body)
        (self.source / "result.json").write_text('{"status":"completed"}\n')
        (self.source / "events.jsonl").write_text('{"method":"turn/completed"}\n')
        path.chmod(0o200)
        self.addCleanup(path.chmod, 0o600)
        if not os.access(path, os.R_OK):
            with self.assertRaises(PermissionError):
                hashlib.sha256(path.read_bytes()).hexdigest()
        destination = self.root / "collected"
        report = collect_workspace(self.source, destination, "attempt-1", "completed")
        exported = destination / "workspace/.agents/skills/example/SKILL.md"
        self.assertEqual(report["collection_status"], "complete")
        self.assertEqual(exported.read_bytes(), body)
        self.assertEqual(stat.S_IMODE(exported.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o200)
        artifact = next(a for a in report["artifacts"] if a["path"] == ".agents/skills/example/SKILL.md")
        self.assertEqual(artifact["sha256"], "4ac2b6180a8baef08a3e38c41033c085da750802b568fcbb71287bc690f4c9ff")
        self.assertEqual(artifact["original_mode"], "0200")
        self.assertTrue(artifact["owner_read_added"])
        self.assertEqual(report["behavioral_status"], "ungraded")

    def test_partial_trace_missing_result_and_terminal_state_remain_distinct(self):
        (self.source / "events.jsonl").write_text('{"method":"turn/completed"}\n{"partial":')
        report = collect_workspace(self.source, self.root / "partial", "attempt-1", "timeout")
        self.assertEqual(report["execution_status"], "timeout")
        self.assertEqual(report["stage"], "inconclusive")
        self.assertIn("missing-result", report["infrastructure_states"])
        self.assertIn("partial-trace", report["infrastructure_states"])
        self.assertTrue((self.root / "partial/workspace/events.jsonl").read_text().endswith('{"partial":'))

    def test_collection_cannot_disable_its_timeout_with_nonfinite_numbers(self):
        for value in (float("inf"), float("nan"), -1, True):
            with self.assertRaisesRegex(CollectionError, "invalid-collection-request"):
                collect_workspace(self.source, self.root / "invalid", "attempt-1", "completed", timeout_seconds=value)

    def test_export_does_not_read_external_links_private_files_or_shared_inodes(self):
        private = "fixture-private-content-never-exported"
        outside = self.root / "outside.txt"; outside.write_text(private)
        (self.source / "linked.txt").symlink_to(outside)
        os.link(outside, self.source / "shared.txt")
        (self.source / "auth.json").write_text(json.dumps({"token": private}))
        report = collect_workspace(self.source, self.root / "bounded", "attempt-1", "completed")
        self.assertFalse((self.root / "bounded/workspace/linked.txt").exists())
        self.assertFalse((self.root / "bounded/workspace/auth.json").exists())
        self.assertFalse((self.root / "bounded/workspace/shared.txt").exists())
        self.assertNotIn(private, json.dumps(report))
        self.assertEqual(next(a for a in report["artifacts"] if a["path"] == "shared.txt")["status"], "unavailable")
        self.assertIn("unavailable-artifact", report["infrastructure_states"])

    def test_timeout_preserves_a_readable_incomplete_receipt_and_execution_interruption(self):
        report = collect_workspace(self.source, self.root / "timed-out", "attempt-1", "interrupted", timeout_seconds=0)
        self.assertEqual(report["execution_status"], "interrupted")
        self.assertEqual(report["collection_status"], "timeout")
        self.assertEqual(json.loads((self.root / "timed-out/collection.json").read_text()), report)
        self.assertIn("collection-timeout", report["infrastructure_states"])

    def test_recovery_keeps_the_failed_attempt_and_original_receipt_unchanged(self):
        (self.source / "result.json").write_text('{"status":"completed"}\n')
        (self.source / "events.jsonl").write_text('{"method":"turn/completed"}\n')
        original = collect_workspace(self.source, self.root / "original", "attempt-1", "infrastructure-error")
        previous = (self.root / "original/collection.json").read_bytes()
        recovered = collect_workspace(self.source, self.root / "recovered", "attempt-1", "completed", recovery_of="attempt-1")
        self.assertEqual(original["execution_status"], "infrastructure-error")
        self.assertEqual(recovered["stage"], "recovered")
        self.assertEqual(recovered["recovery_of"], "attempt-1")
        self.assertEqual(recovered["behavioral_status"], "ungraded")
        self.assertEqual((self.root / "original/collection.json").read_bytes(), previous)

    def test_public_cli_creates_an_owned_workspace_and_collects_a_complete_attempt(self):
        cli = Path(__file__).resolve().parents[2] / "skills/reflect/runtime/collector.py"
        workspace = self.root / "cli-workspace"
        created = subprocess.run([sys.executable, str(cli), "create", "--workspace", str(workspace), "--attempt", "cli-attempt"], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(created.stdout)["status"], "created")
        (workspace / "result.json").write_text('{"status":"completed"}\n')
        (workspace / "events.jsonl").write_text('{"method":"turn/completed"}\n')
        result = subprocess.run([sys.executable, str(cli), "collect", "--source", str(workspace), "--destination", str(self.root / "cli-output"), "--attempt", "cli-attempt", "--terminal", "completed"], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["collection_status"], "complete")


if __name__ == "__main__":
    unittest.main()
