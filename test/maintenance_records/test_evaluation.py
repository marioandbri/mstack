import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from evaluation import Runner, EvaluationError


def case():
    return {"schema_version": 1, "id": "collector-smoke", "kind": "synthetic-fixture", "incident_id": None,
            "request": "Write the task result and retain evidence.", "initial_state": "A new isolated workspace.",
            "expected_behavior": ["Produce the result without changing source evidence."],
            "sources": [{"reference": "synthetic:collector", "sha256": None}], "nearby_negative": None,
            "fixture": {"evidence.txt": "preserved evidence\n"},
            "checks": [{"id": "result", "kind": "json-equals", "path": "answer.json", "expected": {"answer": 42}},
                       {"id": "evidence", "kind": "unchanged", "path": "evidence.txt"}]}


def profile():
    return {"schema_version": 1, "id": "fixture", "kind": "fixture", "source_commit": None,
            "model": None, "reasoning": None, "harness": {"name": "fixture-process", "version": "1"},
            "environment": {"python": "3.13.2"}, "budget_seconds": 5, "max_turns": 1,
            "instructions": {"AGENTS.md": "Preserve evidence.\n"}, "catalog": [], "source_files": {}}


class FixtureTransport:
    def run(self, workspace, protocol, seconds):
        import subprocess, sys
        script = "import json,pathlib; pathlib.Path('answer.json').write_text(json.dumps({'answer':42})); pathlib.Path('events.jsonl').write_text(json.dumps({'type':'fixture-completed'})+'\\n')"
        subprocess.run([sys.executable, "-c", script], cwd=workspace, timeout=seconds, check=True)
        return {"execution_status": "completed", "context": {"state": "verified-fixture", "instructions": ["AGENTS.md"]}, "model_calls": 0}


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.runner = Runner(Path(self.temp.name) / "runner")
        self.prepared = self.runner.prepare(case(), profile())

    def grant(self, attempts=1):
        return {"schema_version": 1, "id": "test-budget", "protocols": [self.prepared["protocol_sha256"]],
                "kind": "fixture", "source": "implementation:test-fixtures", "answer": "Run the local mechanical fixture.",
                "max_attempts": attempts, "max_turns": attempts, "max_seconds": attempts * 5}

    def test_public_runner_collects_a_real_process_without_manual_repair(self):
        result = self.runner.execute(self.prepared["protocol_sha256"], "attempt-1", self.grant(), FixtureTransport())
        self.assertEqual(result["execution_status"], "completed")
        self.assertEqual(result["behavioral_status"], "passed")
        self.assertEqual(result["collection"]["collection_status"], "complete")
        self.assertEqual(result["stage"], "executed")
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual((Path(result["collection_path"]) / "workspace/answer.json").read_text(), '{"answer": 42}')
        self.assertEqual(self.runner.report()["attempts"][0]["attempt_id"], "attempt-1")

    def test_no_approval_or_exhausted_budget_cannot_start_a_process(self):
        class Forbidden:
            def run(self, *args):
                raise AssertionError("The runner must reject before launching.")
        with self.assertRaisesRegex(EvaluationError, "missing-authorization"):
            self.runner.execute(self.prepared["protocol_sha256"], "denied", None, Forbidden())
        self.runner.execute(self.prepared["protocol_sha256"], "attempt-1", self.grant(), FixtureTransport())
        with self.assertRaisesRegex(EvaluationError, "budget-exhausted"):
            self.runner.execute(self.prepared["protocol_sha256"], "attempt-2", self.grant(), Forbidden())

    def test_source_drift_and_missing_result_are_inconclusive_not_behavioral_success(self):
        frozen = Path(self.prepared["path"]) / "protocol.json"
        value = json.loads(frozen.read_text()); value["case"]["request"] = "changed"
        frozen.write_text(json.dumps(value))
        with self.assertRaisesRegex(EvaluationError, "frozen-input-changed"):
            self.runner.execute(self.prepared["protocol_sha256"], "drift", self.grant(), FixtureTransport())

    def test_missing_trace_timeout_and_parallel_budget_stay_distinct(self):
        class NoTrace:
            def run(self, *args):
                return {"execution_status": "completed", "context": {"state": "verified-fixture"}, "model_calls": 0}
        result = self.runner.execute(self.prepared["protocol_sha256"], "missing-trace", self.grant(2), NoTrace())
        self.assertEqual(result["behavioral_status"], "inconclusive")
        self.assertIn("missing-events", result["infrastructure_states"])
        class TimedOut:
            def run(self, *args):
                raise TimeoutError()
        result = self.runner.execute(self.prepared["protocol_sha256"], "timeout", self.grant(2), TimedOut())
        self.assertEqual(result["execution_status"], "timeout")
        self.assertEqual(len(self.runner.report()["attempts"]), 2)
        other = Runner(Path(self.temp.name) / "parallel")
        frozen = other.prepare(case(), profile())
        def execute(identity):
            try:
                return other.execute(frozen["protocol_sha256"], identity, self.grant(), FixtureTransport())["stage"]
            except EvaluationError as error:
                return str(error)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(execute, ["parallel-1", "parallel-2"]))
        self.assertCountEqual(results, ["executed", "budget-exhausted"])

    def test_stdio_rpc_keeps_early_events_until_the_turn_consumer_reads_them(self):
        from codex_rpc import RPC
        root = Path(self.temp.name) / "rpc"; root.mkdir()
        program = "import json,sys\nfor line in sys.stdin:\n m=json.loads(line)\n if 'id' in m:\n  print(json.dumps({'method':'turn/completed','params':{'early':True}}),flush=True)\n  print(json.dumps({'id':m['id'],'result':{'ok':True}}),flush=True)\n"
        rpc = RPC([sys.executable, "-c", program], root)
        try:
            self.assertEqual(rpc.call("initialize", timeout=2), {"ok": True})
            self.assertEqual(rpc.next(timeout=2)["method"], "turn/completed")
        finally:
            rpc.close()
        self.assertEqual(len((root / "events.jsonl").read_text().splitlines()), 2)

    def test_public_cli_runs_a_frozen_mechanical_fixture_and_keeps_recovery_separate(self):
        value = case()
        value["fixture"][".evaluation/fixture.py"] = "from pathlib import Path\nPath('answer.json').write_text('{\"answer\":42}')\n"
        frozen = self.runner.prepare(value, profile())
        grant = self.grant(); grant["protocols"] = [frozen["protocol_sha256"]]
        path = Path(self.temp.name) / "grant.json"; path.write_text(json.dumps(grant))
        cli = Path(__file__).resolve().parents[2] / "skills/reflect/runtime/evaluation_cli.py"
        result = subprocess.run([sys.executable, str(cli), "--root", str(self.runner.root), "execute", "--protocol", frozen["protocol_sha256"], "--attempt", "cli", "--grant", str(path), "--transport", "fixture"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["behavioral_status"], "passed")
        before = (self.runner.root / "attempts/cli/receipt.json").read_bytes()
        recovery = self.runner.recover("cli", "recovered-cli", "Fixture process exited and no consumers remain.")
        self.assertEqual(recovery["stage"], "recovered")
        self.assertEqual(before, (self.runner.root / "attempts/cli/receipt.json").read_bytes())

    def test_git_profile_uses_committed_managed_sources_and_existing_auth_helper(self):
        from evaluation_source import git_profile
        root = Path(__file__).resolve().parents[2]
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        result = git_profile(root, commit, {"codex": "0.160.0", "image_digest": "sha256:" + "a" * 64}, identity="frozen", model="gpt-6.1-sol", reasoning="high", seconds=120)
        self.assertEqual(result["source_commit"], commit)
        manifest = json.loads(subprocess.check_output(["git", "show", commit + ":skills.json"], cwd=root))
        self.assertEqual(len(result["catalog"]), len(manifest["skills"]))
        self.assertEqual(next(v for v in result["catalog"] if v["name"] == "reflect")["invocation"], "explicit-only")
        self.assertEqual(result["source_files"]["helpers/auth_state.py"], subprocess.check_output(["git", "show", commit + ":evals/deepswe/auth_state.py"], cwd=root).decode())


if __name__ == "__main__":
    unittest.main()
