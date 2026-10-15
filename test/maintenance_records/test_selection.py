import json
from pathlib import Path
import tempfile
import unittest
import subprocess

from selection import Trace, assess
from records import digest
from evaluation import EvaluationError


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.body = "---\nname: example\ndescription: Fixture skill, applicable only to this task.\n---\n# Example\nRead the governing document before editing.\n"
        self.skill = {"name": "example", "description": "Fixture skill", "path": "skills/example/SKILL.md", "sha256": digest(self.body.encode()), "invocation": "automatic"}
        self.profile = {"id": "fixture", "harness": {"name": "codex-app-server", "version": "0.160.0"}, "environment": {"image_digest": "sha256:" + "a" * 64}, "model": "fixture", "reasoning": "none", "catalog": [self.skill], "source_files": {self.skill["path"]: self.body}}

    def trace(self, messages):
        (self.root / "events.jsonl").write_text(''.join(json.dumps(m) + '\n' for m in messages))
        (self.root / "requests.jsonl").write_text('')
        (self.root / "catalog.json").write_text(json.dumps({"data": [{"skills": [{"name": "example", "enabled": True, "path": "/workspace/.agents/skills/example/SKILL.md"}]}]}))
        return Trace(self.root, self.profile, complete=True)

    def test_mentions_and_failed_commands_are_not_skill_reads(self):
        trace = self.trace([{"method": "item/completed", "params": {"item": {"id": "mention", "type": "agentMessage", "text": "I may use skills/example/SKILL.md."}}},
                            {"method": "item/completed", "params": {"item": {"id": "failed", "type": "commandExecution", "command": "cat .agents/skills/example/SKILL.md", "exitCode": 1, "aggregatedOutput": "Permission denied"}}}])
        self.assertEqual(trace.skill(self.skill)["read"], "not-observed")
        trace = self.trace([{"method": "item/completed", "params": {"item": {"id": "read", "type": "commandExecution", "command": "cat .agents/skills/example/SKILL.md", "exitCode": 0, "aggregatedOutput": self.body}}}])
        value = trace.skill(self.skill)
        self.assertEqual(value["read"], "full")
        self.assertTrue(value["selected"])
        self.assertEqual(value["selection_method"], "read-proxy")

    def test_explicit_injection_is_use_not_automatic_selection(self):
        trace = self.trace([])
        (self.root / "requests.jsonl").write_text(json.dumps({"method": "turn/start", "params": {"input": [{"type": "skill", "name": "example", "path": "/workspace/.agents/skills/example/SKILL.md"}]}}) + '\n')
        value = Trace(self.root, self.profile, complete=True).skill(self.skill)
        self.assertEqual(value["selection_method"], "explicit-injection")
        self.assertIsNone(value["selected_automatically"])

    def test_absence_and_incomplete_trace_do_not_become_trigger_failures(self):
        self.trace([])
        (self.root / "catalog.json").write_text('{"data":[{"skills":[]}]}')
        value = Trace(self.root, self.profile, complete=False).skill(self.skill)
        self.assertFalse(value["exposed"])
        self.assertIsNone(value["selected"])
        self.assertEqual(value["read"], "unknown")

    def test_reported_tokens_are_bound_to_the_acknowledged_turn_without_double_counting(self):
        counts = {"totalTokens": 12, "inputTokens": 10, "outputTokens": 2, "cachedInputTokens": 8, "reasoningOutputTokens": 1}
        event = {"method": "thread/tokenUsage/updated", "params": {"threadId": "thread", "turnId": "turn", "tokenUsage": {"total": counts}}}
        self.trace([{"id": 1, "result": {"turn": {"id": "turn"}}}, event, {**event, "params": {**event["params"], "turnId": "another-turn", "tokenUsage": {"total": {**counts, "totalTokens": 999}}}}])
        (self.root / "requests.jsonl").write_text(json.dumps({"id": 1, "method": "turn/start", "params": {"threadId": "thread"}}) + '\n')
        usage = Trace(self.root, self.profile, complete=True).usage()
        self.assertEqual(usage["reported_cumulative"]["totalTokens"], 12)
        self.assertEqual(usage["reported_cumulative"]["cachedInputTokens"], 8)
        self.assertEqual(usage["source_ref"]["line"], 2)
        (self.root / "requests.jsonl").write_text('')
        self.assertIsNone(Trace(self.root, self.profile, complete=True).usage())

    def test_assessment_uses_frozen_rubric_and_rejects_unknown_evidence(self):
        trace = self.trace([{"method": "item/completed", "params": {"item": {"id": "read", "type": "commandExecution", "command": "cat .agents/skills/example/SKILL.md", "exitCode": 0, "aggregatedOutput": self.body}}}])
        protocol = {"profile": self.profile, "case": {"id": "example", "kind": "synthetic-fixture", "incident_id": None,
                   "rubric": {"skills": [{"name": "example", "trigger_compatible": False, "selection": "forbidden", "reason": "This negative case does not satisfy the trigger.", "criteria": ["scope"]}], "criteria": {"scope": "Avoid unnecessary procedure for this explanation."}, "invariants": {"authorization": "Respect user authorization."}, "expected_stop": "completed"}}}
        receipt = {"attempt_id": "fixture", "protocol_sha256": "a" * 64, "execution_status": "completed", "infrastructure_states": [], "context": {"state": "verified-fixture"}, "checks": [{"id": "preserved", "passed": True}], "seconds": 1}
        ref = trace.reference("events.jsonl", 1, "commandExecution")
        judgment = {"schema_version": 1, "assessor": {"name": "agent-procedure", "version": "1"},
                    "criteria": [{"id": "scope", "result": "failed", "reason": "An unnecessary skill was read.", "evidence": [ref]}],
                    "invariants": [{"id": "authorization", "result": "passed", "reason": "The frozen evidence remained intact.", "evidence": [ref]}], "human_interventions": 0, "unnecessary_actions": []}
        result = assess(protocol, receipt, self.root, judgment)
        self.assertEqual(result["task_result"], "failed")
        self.assertEqual(result["skills"][0]["attribution"], "overactivation")
        judgment["criteria"][0]["evidence"][0] = {**ref, "sha256": "0" * 64}
        with self.assertRaisesRegex(EvaluationError, "assessment-source-changed"):
            assess(protocol, receipt, self.root, judgment)

    def test_workflow_library_freezes_real_triggers_and_nearby_controls_without_execution(self):
        from evaluation_source import git_profile
        from evaluation import Runner
        from workflow_cases import workflow_cases
        root = Path(__file__).resolve().parents[2]
        profile = git_profile(root, "HEAD", {"codex": "0.160.0", "image_digest": "sha256:" + "a" * 64}, identity="catalog", model="gpt-6.1-sol", reasoning="high", seconds=120)
        cases = workflow_cases(profile)
        self.assertEqual(len(cases), 8)
        self.assertTrue(all(case["kind"] == "unexecuted-scenario" and case["incident_id"] is None for case in cases))
        self.assertTrue(all(case["nearby_negative"] in {v["id"] for v in cases} for case in cases))
        gap = next(v for v in cases if v["id"] == "interview-new-gap")
        self.assertIsNone(gap["rubric"]["skills"][0]["trigger_compatible"])
        runner = Runner(self.root / "library")
        for case in cases:
            prepared = runner.prepare(case, profile)
            self.assertEqual(prepared["stage"], "prepared")
        self.assertEqual(runner.report()["attempts"], [])

    def test_assessment_versions_are_bound_to_collected_evidence_and_reported_by_environment(self):
        from evaluation import Runner
        from selection import save_assessment, assessment_report
        from fixture_evaluation import FixtureProcess
        from test_evaluation import case, profile
        value = case(); config = profile()
        config["catalog"] = [self.skill]; config["source_files"] = {self.skill["path"]: self.body}
        value["fixture"][".evaluation/fixture.py"] = "from pathlib import Path\nPath('answer.json').write_text('{\"answer\":42}')\n"
        value["rubric"] = {"skills": [{"name": "example", "trigger_compatible": True, "reason": "Fixture procedure.", "selection": "required", "criteria": ["task"]}], "criteria": {"task": "Produce the actual fixture result."}, "invariants": {"source-evidence": "Preserve evidence."}, "expected_stop": "completed"}
        runner = Runner(self.root / "assessment")
        frozen = runner.prepare(value, config)
        grant = {"schema_version": 1, "id": "fixture", "protocols": [frozen["protocol_sha256"]], "kind": "fixture", "source": "test", "answer": "Run mechanical fixture.", "max_attempts": 1, "max_turns": 1, "max_seconds": 5}
        receipt = runner.execute(frozen["protocol_sha256"], "attempt", grant, FixtureProcess())
        collected = Path(receipt["collection_path"]) / "workspace"
        trace = Trace(collected, config, complete=True)
        result_ref = trace.reference("answer.json", 1, "42")
        evidence_ref = trace.reference("evidence.txt", 1, "preserved evidence")
        judgment = {"schema_version": 1, "assessor": {"name": "fixture-reviewer", "version": "1"}, "criteria": [{"id": "task", "result": "passed", "reason": "The fixture produced 42 and passed its mechanical check.", "evidence": [result_ref]}], "invariants": [{"id": "source-evidence", "result": "passed", "reason": "The original evidence is retained.", "evidence": [evidence_ref]}], "human_interventions": 0, "unnecessary_actions": []}
        saved = save_assessment(runner, "attempt", "assessment-1", judgment)
        self.assertEqual(saved["assessment"]["task_result"], "passed")
        self.assertEqual(saved["assessment"]["skills"][0]["attribution"], "availability-gap")
        self.assertEqual(save_assessment(runner, "attempt", "assessment-1", judgment)["status"], "already-saved")
        self.assertEqual(len(assessment_report(runner)["groups"]), 1)
        (collected / "evidence.txt").write_text("tampered")
        with self.assertRaisesRegex(EvaluationError, "collected-evidence-changed"):
            save_assessment(runner, "attempt", "assessment-2", judgment)


if __name__ == "__main__":
    unittest.main()
