import copy
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from records import RecordError, RecordStore
from reviews import Reviews
from summaries import Summaries
from test_records import observation
from test_summaries import summary


def review():
    return {"schemaVersion": 1, "id": "REVIEW-1", "phase": "reviewing", "mode": "inbox", "scope": "project", "promotion": "none",
            "sources": [{"reference": "source:behavior", "sha256": "a" * 64}, {"reference": "source:destination", "sha256": "b" * 64}], "coverage": [],
            "opportunities": [{"id": key, "basis": "observed-failure", "observation": "The convention was omitted.",
                               "evidence": [{"source": "observation:OBS-1", "summary": "The original records the omission."}],
                               "suspectedCause": None, "recommendation": recommendation, "question": question,
                               "decision": {"status": "pending", "answer": None, "scope": key}, "observationIds": ["OBS-1"]}
                              for key, recommendation, question in [("behavior", "Load applicable conventions before editing.", "¿Adoptar esta conducta?"),
                                                                   ("destination", "Review the existing owning skill.", "¿Dónde debe vivir la conducta?")]]}


def options():
    return {"active_question": "behavior", "decision_domains": {"behavior": "behavior", "destination": "destination"},
            "dependencies": {"behavior": ["source:behavior"], "destination": ["source:destination"]}, "decision_sources": {},
            "artifacts": [], "request": {"answer": "Reflect on OBS-1; propose without applying.", "source": "user:request"}}


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.records = RecordStore(Path(self.temp.name) / "records.sqlite3", "project")
        self.records.initialize(); self.records.capture("original", observation())
        self.reviews = Reviews(self.records)

    def test_resume_separates_behavior_from_destination_and_keeps_retained_facts(self):
        ctx = Summaries(self.records).prepare("OBS-1")
        Summaries(self.records).save(ctx, summary(ctx), 0, "summary")
        document, extra = review(), options()
        self.reviews.save(document, extra, 0, "start")
        document["opportunities"][0]["decision"] = {"status": "adjust", "answer": "Yes, adopt that behavior.", "scope": "behavior"}
        extra["decision_sources"]["behavior"] = "user:answer-1"; extra["active_question"] = "destination"
        self.reviews.save(document, extra, 1, "answer")
        resumed = Reviews(RecordStore(self.records.path, "project")).get("REVIEW-1")
        self.assertEqual(resumed["revision"], 2)
        self.assertEqual(resumed["active_question"]["id"], "destination")
        self.assertEqual(resumed["record"]["opportunities"][0]["decision"]["answer"], "Yes, adopt that behavior.")
        self.assertEqual(resumed["context"]["observations"][0]["summary"]["revision"], 1)
        self.assertIsNotNone(resumed["context"]["observations"][0]["summary"]["evidence"])
        self.assertEqual(resumed["allowed_actions"], ["review", "prepare-proposal"])
        self.assertEqual(resumed["record"]["promotion"], "none")

    def test_only_affected_decision_reopens_and_old_answer_is_retained(self):
        document, extra = review(), options()
        for item in document["opportunities"]:
            item["decision"] = {"status": "keep", "answer": "Keep this part.", "scope": item["id"]}
            extra["decision_sources"][item["id"]] = "user:keep-" + item["id"]
        extra["active_question"] = None
        self.reviews.save(document, extra, 0, "start")
        result = self.reviews.reconcile("REVIEW-1", [{"reference": "source:destination", "sha256": "c" * 64, "evidence": "file:checked-current"}], 1, "drift")
        self.assertEqual(result["reopened"], ["destination"])
        resumed = self.reviews.get("REVIEW-1")
        self.assertEqual(resumed["record"]["opportunities"][0]["decision"]["status"], "keep")
        self.assertEqual(resumed["record"]["opportunities"][1]["decision"]["status"], "pending")
        self.assertEqual(self.reviews.history("REVIEW-1")[0]["payload"]["record"]["opportunities"][1]["decision"]["answer"], "Keep this part.")
        self.assertEqual(resumed["source_changes"][0]["previous_sha256"], "b" * 64)

    def test_chat_only_does_not_even_initialize_storage(self):
        path = Path(self.temp.name) / "missing" / "records.sqlite3"
        result = Reviews(RecordStore(path, "project")).save(review(), options(), 0, "chat", chat_only=True)
        self.assertEqual(result["persistence"], "chat-only")
        self.assertFalse(path.parent.exists())
        record_path = Path(self.temp.name) / "review.json"; record_path.write_text(json.dumps(review()))
        options_path = Path(self.temp.name) / "options.json"; options_path.write_text(json.dumps(options()))
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "skills/reflect/runtime/record_cli.py"), "--database", str(path), "--project", "project", "review", "save", "--record", str(record_path), "--options", str(options_path), "--expected-revision", "0", "--operation", "chat-cli", "--chat-only"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["persistence"], "chat-only")
        self.assertFalse(path.parent.exists())

    def test_proposal_without_apply_keeps_candidate_and_question_with_partial_context(self):
        document, extra = review(), options()
        extra["artifacts"] = [{"id": "candidate", "destination": "skills/conventions-aware-engineering/SKILL.md", "content": "Complete proposed skill text.", "diff": "+Read the applicable convention.", "source_refs": ["source:behavior"]}]
        self.reviews.save(document, extra, 0, "proposal-only")
        resumed = self.reviews.get("REVIEW-1")
        self.assertEqual(resumed["options"]["artifacts"], extra["artifacts"])
        self.assertEqual(resumed["context"]["observations"][0]["summary"]["state"], "pending")
        self.assertEqual(resumed["active_question"]["id"], "behavior")
        self.assertEqual(resumed["record"]["promotion"], "none")

    def test_rejections_stale_writers_and_one_question_are_enforced(self):
        document, extra = review(), options()
        document["opportunities"][0]["decision"] = {"status": "reject", "answer": "Do not change this.", "scope": "behavior"}
        extra["decision_sources"]["behavior"] = "user:reject"; extra["active_question"] = "destination"
        self.reviews.save(document, extra, 0, "start")
        with self.assertRaisesRegex(RecordError, "review-revision-conflict"):
            self.reviews.save(document, extra, 0, "stale")
        changed = copy.deepcopy(document); changed["opportunities"][0]["decision"]["status"] = "adjust"
        with self.assertRaisesRegex(RecordError, "resolved-decision-changed"):
            self.reviews.save(changed, extra, 1, "overwrite-rejection")
        extra["active_question"] = ["behavior", "destination"]
        with self.assertRaisesRegex(RecordError, "invalid-active-question"):
            self.reviews.save(document, extra, 1, "two-questions")


if __name__ == "__main__":
    unittest.main()
