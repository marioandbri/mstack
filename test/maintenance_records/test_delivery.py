import copy
import json
from pathlib import Path
import sys
import unittest

from delivery import Delivery
from records import RecordError, RecordStore, digest
from reviews import Reviews
from evaluation import Runner
from fixture_evaluation import FixtureProcess
from test_records import observation
from test_reviews import review, options
from test_evaluation import case


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(root / "install"))
        import test_mstack as installer_tests
        from mstack_fs import signature
        sys.path.pop(0)
        self.signature = signature
        self.fixture = installer_tests.InstallerTests(methodName="runTest")
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.fixture.home.chmod(0o700)
        self.fixture.write("evals/deepswe/auth_state.py", (root / "evals/deepswe/auth_state.py").read_text())
        self.fixture.write("instructions/global/AGENTS.md", "Maintenance label: stable\n")
        self.stable = self.fixture.commit(); self.fixture.apply()
        self.fixture.write("instructions/global/AGENTS.md", "Maintenance label: candidate\n")
        self.candidate = self.fixture.commit()
        self.records = RecordStore(self.fixture.base / "records.sqlite3", "fixture-project")
        self.records.initialize(); self.records.capture("original", observation())
        self.reviews = Reviews(self.records)
        document, extra = review(), options()
        for item in document["opportunities"]:
            item["basis"] = "user-preference"
            item["decision"] = {"status": "adjust", "answer": "Accept this explicit fixture preference.", "scope": item["id"]}
            extra["decision_sources"][item["id"]] = "fixture:user:" + item["id"]
        extra["active_question"] = None
        extra["artifacts"] = [{"id": "global", "destination": "instructions/global/AGENTS.md", "content": "Maintenance label: candidate\n", "diff": self.fixture.git("diff", self.stable, self.candidate, "--", "instructions/global/AGENTS.md"), "source_refs": ["source:behavior"]}]
        self.reviews.save(document, extra, 0, "accepted-fixture")
        self.runner = Runner(self.fixture.base / "runner")
        self.delivery = Delivery(self.reviews, self.runner, root, self.fixture.repo, self.fixture.home, self.fixture.base / "delivery", mode="isolated")

    def grant(self, actions=None):
        return {"kind": "fixture", "source": "fixture:user:delivery", "answer": "Promote and roll back only this accepted fixture.", "home": str(self.fixture.home), "commit": self.candidate, "actions": actions or ["promote", "rollback"]}

    def test_real_installer_dry_run_promotion_behavior_and_rollback_preserve_unowned_settings(self):
        before = self.signature(self.fixture.home)
        plan = self.delivery.prepare("delivery-1", "REVIEW-1", "behavior", "destination", self.candidate)
        self.assertEqual(self.signature(self.fixture.home), before)
        self.assertEqual(plan["stage"], "prepared")
        result = self.delivery.promote("delivery-1", self.grant())
        self.assertEqual(result["stage"], "promoted-check-pending")
        self.assertEqual((self.fixture.home / ".agents/AGENTS.md").read_text(), "Maintenance label: candidate\n")
        profile = self.delivery.installed_profile("delivery-1", {"python": "3.13.2"}, identity="post", model=None, reasoning=None, seconds=5)
        value = case(); value["fixture"][".evaluation/fixture.py"] = "from pathlib import Path\nimport json\nlabel=Path('AGENTS.md').read_text().split(':')[1].strip()\nPath('answer.json').write_text(json.dumps({'label':label}))\n"
        value["checks"][0]["expected"] = {"label": "candidate"}
        frozen = self.runner.prepare(value, profile)
        grant = {"schema_version": 1, "id": "post-check", "protocols": [frozen["protocol_sha256"]], "kind": "fixture", "source": "test", "answer": "Run the installed fixture behavior.", "max_attempts": 1, "max_turns": 1, "max_seconds": 5}
        checked = self.runner.execute(frozen["protocol_sha256"], "post-check", grant, FixtureProcess())
        recorded = self.delivery.record_check("delivery-1", "post-check", "post-promotion")
        self.assertEqual(recorded["behavior"], "fixture-verified")
        # Later unowned configuration must survive rollback.
        config = self.fixture.home / ".pi/agent/settings.json"
        settings = json.loads(config.read_text()); settings["later"] = "preserve"; config.write_text(json.dumps(settings))
        restored = self.delivery.rollback("delivery-1", self.grant())
        self.assertEqual(restored["stage"], "restored-check-pending")
        self.assertEqual((self.fixture.home / ".agents/AGENTS.md").read_text(), "Maintenance label: stable\n")
        self.assertEqual(json.loads(config.read_text())["later"], "preserve")
        self.assertIn("fixture-secret-never-logged", (self.fixture.home / ".codex/config.toml").read_text())
        profile = self.delivery.installed_profile("delivery-1", {"python": "3.13.2"}, identity="rollback", model=None, reasoning=None, seconds=5)
        value["checks"][0]["expected"] = {"label": "stable"}
        frozen = self.runner.prepare(value, profile)
        grant.update({"id": "rollback-check", "protocols": [frozen["protocol_sha256"]]})
        self.runner.execute(frozen["protocol_sha256"], "rollback-check", grant, FixtureProcess())
        self.assertEqual(self.delivery.record_check("delivery-1", "rollback-check", "post-rollback")["behavior"], "fixture-verified")
        self.assertEqual(self.reviews.get("REVIEW-1")["deliveries"][0]["events"][-1]["stage"], "post-rollback")

    def test_missing_install_authorization_and_drift_cannot_overwrite_targets(self):
        self.delivery.prepare("delivery-1", "REVIEW-1", "behavior", "destination", self.candidate)
        before = self.signature(self.fixture.home)
        with self.assertRaisesRegex(RecordError, "delivery-authorization-missing"):
            self.delivery.promote("delivery-1", None)
        self.assertEqual(self.signature(self.fixture.home), before)
        (self.fixture.home / ".agents/AGENTS.md").write_text("Later local memory.\n")
        with self.assertRaisesRegex(RecordError, "installer-operation-unconfirmed"):
            self.delivery.promote("delivery-1", self.grant())
        self.assertEqual((self.fixture.home / ".agents/AGENTS.md").read_text(), "Later local memory.\n")

    def test_candidate_must_match_the_accepted_complete_artifact(self):
        self.fixture.write("instructions/global/AGENTS.md", "An unaccepted candidate.\n")
        unrelated = self.fixture.commit()
        with self.assertRaisesRegex(RecordError, "candidate-artifact-mismatch"):
            self.delivery.prepare("wrong", "REVIEW-1", "behavior", "destination", unrelated)

    def test_continuing_the_same_review_does_not_erase_applicable_install_acceptance(self):
        self.delivery.prepare("delivery-1", "REVIEW-1", "behavior", "destination", self.candidate)
        state = self.reviews.get("REVIEW-1")
        extra = copy.deepcopy(state["options"])
        extra["request"] = {"answer": "Continue the already requested review.", "source": "fixture:user:resume"}
        self.reviews.save(state["record"], extra, state["revision"], "resume")
        self.assertEqual(self.delivery.promote("delivery-1", self.grant())["stage"], "promoted-check-pending")

    def test_rollback_drift_stays_pending_and_preserves_later_local_memory(self):
        self.delivery.prepare("delivery-1", "REVIEW-1", "behavior", "destination", self.candidate)
        self.delivery.promote("delivery-1", self.grant())
        path = self.fixture.home / ".agents/AGENTS.md"; path.write_text("Later accepted local memory.\n")
        with self.assertRaisesRegex(RecordError, "installer-operation-unconfirmed"):
            self.delivery.rollback("delivery-1", self.grant())
        self.assertEqual(path.read_text(), "Later accepted local memory.\n")
        self.assertEqual(self.delivery.get("delivery-1")["events"][-1]["stage"], "rollback-started")

    def test_incomplete_post_check_is_not_a_behavioral_failure_or_rollback_permission(self):
        self.delivery.prepare("delivery-1", "REVIEW-1", "behavior", "destination", self.candidate)
        self.delivery.promote("delivery-1", self.grant())
        profile = self.delivery.installed_profile("delivery-1", {"python": "3.13.2"}, identity="incomplete", model=None, reasoning=None, seconds=5)
        frozen = self.runner.prepare(case(), profile)
        class MissingTrace:
            def run(self, *args):
                return {"execution_status": "completed", "context": {"state": "verified-fixture"}, "model_calls": 0}
        grant = {"schema_version": 1, "id": "missing-trace", "protocols": [frozen["protocol_sha256"]], "kind": "fixture", "source": "test", "answer": "Exercise missing trace.", "max_attempts": 1, "max_turns": 1, "max_seconds": 5}
        self.runner.execute(frozen["protocol_sha256"], "missing-trace", grant, MissingTrace())
        result = self.delivery.record_check("delivery-1", "missing-trace", "post-promotion")
        self.assertEqual(result["behavior"], "inconclusive")
        self.assertEqual((self.fixture.home / ".agents/AGENTS.md").read_text(), "Maintenance label: candidate\n")


if __name__ == "__main__":
    unittest.main()
