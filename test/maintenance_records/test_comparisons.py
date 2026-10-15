import copy
import json
from pathlib import Path
import tempfile
import unittest

from comparisons import Comparisons
from evaluation import Runner, EvaluationError
from records import RecordStore
from reviews import Reviews
from selection import Trace, save_assessment
from fixture_evaluation import FixtureProcess
from test_records import observation
from test_reviews import review, options
from test_evaluation import case, profile


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.records = RecordStore(root / "records.sqlite3", "project"); self.records.initialize(); self.records.capture("raw", observation())
        self.reviews = Reviews(self.records); self.reviews.save(review(), options(), 0, "review")
        self.runner = Runner(root / "runner")
        value = case(); value["id"] = "comparison-fixture"
        value["fixture"][".evaluation/fixture.py"] = "from pathlib import Path\nimport json\nvalue=int(Path('AGENTS.md').read_text().split('answer=')[1].strip())\nPath('answer.json').write_text(json.dumps({'answer':value}))\n"
        value["rubric"] = {"skills": [], "criteria": {"task": "Return the configured expected answer."}, "invariants": {"source-evidence": "Preserve evidence."}, "expected_stop": "completed"}
        self.base = profile(); self.base["id"] = "baseline"; self.base["instructions"]["AGENTS.md"] = "answer=41\n"
        self.candidate = copy.deepcopy(self.base); self.candidate["id"] = "candidate"; self.candidate["instructions"]["AGENTS.md"] = "answer=42\n"
        self.case = value
        self.baseline = self.runner.prepare(value, self.base)["protocol_sha256"]
        self.changed = self.runner.prepare(value, self.candidate)["protocol_sha256"]
        self.comparisons = Comparisons(self.reviews, self.runner)

    def plan(self):
        return self.comparisons.prepare("comparison-1", "REVIEW-1", "behavior", 1, [self.baseline],
             [{"id": "instruction-change", "kind": "global", "reason": "Test the relevant bounded instruction change.", "targets": ["instructions/AGENTS.md"], "protocols": [self.changed]},
              {"id": "none", "kind": "none", "reason": "Keep current behavior if evidence does not support a change.", "targets": [], "protocols": []}], repetitions=1)

    def run_and_assess(self, sha, identity, passed):
        grant = {"schema_version": 1, "id": "grant-" + identity, "protocols": [sha], "kind": "fixture", "source": "test", "answer": "Run local mechanical fixture.", "max_attempts": 1, "max_turns": 1, "max_seconds": 5}
        receipt = self.runner.execute(sha, identity, grant, FixtureProcess())
        trace = Trace(Path(receipt["collection_path"]) / "workspace", self.runner.load(sha)["profile"], complete=True)
        result = trace.reference("answer.json", 1, "42" if passed else "41")
        evidence = trace.reference("evidence.txt", 1, "preserved evidence")
        judgment = {"schema_version": 1, "assessor": {"name": "fixture-reviewer", "version": "1"}, "criteria": [{"id": "task", "result": "passed" if passed else "failed", "reason": "Observed actual fixture result.", "evidence": [result]}], "invariants": [{"id": "source-evidence", "result": "passed", "reason": "Evidence remains intact.", "evidence": [evidence]}], "human_interventions": 0, "unnecessary_actions": []}
        return save_assessment(self.runner, identity, identity + "-judgment", judgment)["id"]

    def test_comparison_retains_metrics_and_links_result_without_promoting(self):
        plan = self.plan()
        self.assertEqual(plan["stage"], "prepared")
        base = self.run_and_assess(self.baseline, "baseline", False)
        candidate = self.run_and_assess(self.changed, "candidate", True)
        result = self.comparisons.record_result("comparison-1", "result-1", [base, candidate])
        self.assertEqual(result["baseline_reproduction"], "reproduced")
        self.assertEqual(result["alternatives"][0]["evidence"], "case-supported")
        self.assertEqual(result["alternatives"][0]["metrics"][0]["human_interventions"], 0)
        self.assertEqual(self.reviews.get("REVIEW-1")["record"]["promotion"], "none")
        self.assertEqual(self.reviews.get("REVIEW-1")["evaluations"][0]["id"], "result-1")

    def test_prepared_and_nonreproducing_baseline_do_not_claim_a_mitigation(self):
        self.plan()
        result = self.comparisons.record_result("comparison-1", "pending", [])
        self.assertEqual(result["stage"], "prepared")
        self.assertEqual(result["baseline_reproduction"], "inconclusive")
        self.assertEqual(result["alternatives"][0]["evidence"], "unestablished")
        self.comparisons.prepare("keep-current", "REVIEW-1", "behavior", 1, [self.changed], [{"id": "none", "kind": "none", "reason": "Keep current behavior when no failure is reproduced.", "targets": [], "protocols": []}], repetitions=1)
        baseline = self.run_and_assess(self.changed, "already-passing-baseline", True)
        retained = self.comparisons.record_result("keep-current", "no-change", [baseline])
        self.assertEqual(retained["baseline_reproduction"], "not-reproduced")
        self.assertEqual(retained["alternatives"][0]["evidence"], "baseline-retained")
        self.assertIn("historical evidence is retained", retained["recommendation"])

    def test_changed_fixture_or_reasoning_is_not_a_comparable_intervention(self):
        changed_case = copy.deepcopy(self.case); changed_case["request"] = "An easier task."
        wrong = self.runner.prepare(changed_case, self.candidate)["protocol_sha256"]
        with self.assertRaisesRegex(EvaluationError, "comparison-conditions-differ"):
            self.comparisons.prepare("bad", "REVIEW-1", "behavior", 1, [self.baseline], [{"id": "changed", "kind": "skill", "reason": "Changed candidate.", "targets": ["instructions/AGENTS.md"], "protocols": [wrong]}], repetitions=1)


if __name__ == "__main__":
    unittest.main()
