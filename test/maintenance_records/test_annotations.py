import base64
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from annotations import Annotations
from records import RecordError, RecordStore
from test_records import observation


def annotation(context):
    return {"schema_version": 1, "input_sha256": context["input_sha256"], "provider": context["provider"],
            "category": "agent-failure", "abstention_reason": None,
            "opportunity": {"observed": "A project convention was not loaded.", "expected": None,
                            "scope": "project", "suspected_cause": None, "uncertainty": ["Cause is unknown."]},
            "rationale": "The original records an observed failure; classification is provisional.",
            "source_refs": [context["sources"][0]], "relations": [], "occurrence_ids": ["OBS-1"],
            "priority": {"impact": "Could affect subsequent implementation.", "reason": "Relevant first incident; no repetition is required."},
            "limits": ["Only selected records were compared."], "suggested_component": "evaluation"}


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = RecordStore(Path(self.temp.name) / "records.sqlite3", "project-identity")
        self.store.initialize(); self.store.capture("capture", observation())
        self.annotations = Annotations(self.store)

    def test_annotation_versions_preserve_original_and_previous_user_decision(self):
        evidence = {"source": "user:message:8", "answer": "Defer this observation for later review."}
        self.store.transition("OBS-1", 0, "deferred", evidence, "defer")
        context = self.annotations.prepare("OBS-1")
        self.assertEqual(context["provider"]["name"], "agent-procedure")
        self.assertEqual(context["user_decisions"][0]["evidence"], evidence)
        self.assertIn("agent-failure", context["allowed_categories"])
        self.assertIn("evaluation", context["component_ids"])
        result = self.annotations.save(context, annotation(context), 0, "classify-1")
        self.assertEqual(result["revision"], 1)
        second = annotation(context); second["rationale"] = "Same finding, more explicit uncertainty."
        self.annotations.save(context, second, 1, "classify-2")
        self.assertEqual(len(self.annotations.history("OBS-1")), 2)
        self.assertEqual(self.annotations.latest("OBS-1")["revision"], 2)
        self.assertEqual(self.store.get("OBS-1")["state"], "deferred")
        self.assertEqual(base64.b64decode(self.store.get("OBS-1")["raw_base64"]), observation())
        self.assertNotIn("classification", self.store.get("OBS-1")["pending"])

    def test_duplicates_recurrences_and_conflicts_retain_distinct_records_and_scopes(self):
        self.store.capture("copy", observation("COPY"))
        repeated = json.loads(observation("REPEAT"))
        repeated["evidence"][0]["source"] = "session:independent/turn:9"
        self.store.capture("repeat", json.dumps(repeated).encode())
        repeated["id"] = "REPEAT-COPY"
        self.store.capture("repeat-copy", json.dumps(repeated).encode())
        self.store.capture("different-scope", observation("CONFLICT", scope="another-feature"))
        context = self.annotations.prepare("OBS-1", ["COPY", "REPEAT", "REPEAT-COPY", "CONFLICT"])
        sources = {source["id"]: source for source in context["sources"]}
        output = annotation(context)
        output["relations"] = [
            {"from_id": origin, "to_id": key, "relation": relation, "scope_match": match, "reason": reason,
             "source_refs": [sources["observation:" + origin], sources["observation:" + key]]}
            for origin, key, relation, match, reason in [
                ("OBS-1", "COPY", "same-incident", "equivalent", "Both records refer to the same source event."),
                ("OBS-1", "REPEAT", "recurrence", "equivalent", "Same behavior and scope, with a separate event source."),
                ("REPEAT", "REPEAT-COPY", "same-incident", "equivalent", "A second description of the independent event."),
                ("OBS-1", "CONFLICT", "conflict", "different", "Another scope has potentially contradictory evidence; preserve both."),
            ]]
        output["occurrence_ids"] = ["OBS-1", "REPEAT"]
        self.annotations.save(context, output, 0, "classify-group")
        latest = self.annotations.latest("OBS-1")
        self.assertEqual(latest["occurrence_count"], 2)
        self.assertEqual(len(self.store.list()), 5)
        self.assertEqual(self.store.get("CONFLICT")["scope"], "another-feature")
        self.assertEqual(latest["annotation"]["relations"][3]["relation"], "conflict")

    def test_a_copy_cannot_count_as_an_independent_recurrence(self):
        self.store.capture("copy", observation("COPY"))
        context = self.annotations.prepare("OBS-1", ["COPY"])
        sources = {source["id"]: source for source in context["sources"]}
        output = annotation(context)
        output["relations"] = [{"from_id": "OBS-1", "to_id": "COPY", "relation": "same-incident", "scope_match": "equivalent", "reason": "Same source event.", "source_refs": [sources["observation:OBS-1"], sources["observation:COPY"]]}]
        output["occurrence_ids"] = ["OBS-1", "COPY"]
        with self.assertRaisesRegex(RecordError, "invalid-occurrence"):
            self.annotations.save(context, output, 0, "wrong-count")
        self.assertEqual(self.annotations.history("OBS-1"), [])

    def test_failed_provider_keeps_previous_annotation_but_marks_work_pending(self):
        context = self.annotations.prepare("OBS-1")
        self.annotations.save(context, annotation(context), 0, "first")
        with self.assertRaisesRegex(RecordError, "provider-unavailable"):
            self.annotations.save(context, None, 1, "failed-provider")
        self.assertEqual(len(self.annotations.history("OBS-1")), 1)
        self.assertEqual(self.annotations.latest("OBS-1")["state"], "pending")
        self.assertIn("classification", self.store.get("OBS-1")["pending"])
        self.annotations.save(context, annotation(context), 1, "retry")
        self.assertNotIn("classification", self.store.get("OBS-1")["pending"])
        # A late failure and an acknowledged old retry cannot change newer state.
        with self.assertRaisesRegex(RecordError, "revision-conflict"):
            self.annotations.save(context, None, 1, "late-failure")
        self.assertEqual(self.annotations.save(context, annotation(context), 0, "first")["status"], "already-saved")
        self.assertEqual(self.annotations.latest("OBS-1")["state"], "provisional")

    def test_new_user_decision_marks_old_classification_stale_without_erasing_it(self):
        context = self.annotations.prepare("OBS-1")
        self.annotations.save(context, annotation(context), 0, "first")
        self.store.transition("OBS-1", 0, "discarded", {"answer": "Reject this proposal.", "source": "user:later"}, "later-decision")
        self.assertEqual(self.annotations.latest("OBS-1")["state"], "pending")
        self.assertEqual(self.annotations.latest("OBS-1")["revision"], 1)
        self.assertEqual(self.store.get("OBS-1")["state"], "discarded")

    def test_untrusted_advice_and_changed_decisions_cannot_overwrite_a_version(self):
        context = self.annotations.prepare("OBS-1", categories=["agent-failure", "uncertain"])
        for field, value in [("category", "global-invariant"), ("suggested_component", "../../install"),
                             ("source_refs", [{"id": "unknown", "sha256": None}]), ("install", True)]:
            output = annotation(context); output[field] = value
            with self.subTest(field=field), self.assertRaises(RecordError):
                self.annotations.save(context, output, 0, "invalid-" + field)
        self.assertEqual(self.annotations.history("OBS-1"), [])
        self.store.transition("OBS-1", 0, "discarded", {"answer": "Reject this proposal.", "source": "user:12"}, "reject")
        with self.assertRaisesRegex(RecordError, "derived-input-stale"):
            self.annotations.save(context, annotation(context), 0, "stale")
        new = self.annotations.prepare("OBS-1")
        output = annotation(new); output["category"] = None
        output["abstention_reason"] = "Evidence is insufficient to choose a destination."
        self.annotations.save(new, output, 0, "abstain")
        self.assertIsNone(self.annotations.latest("OBS-1")["annotation"]["category"])
        self.assertEqual(self.store.get("OBS-1")["state"], "discarded")

    def test_cli_prepares_and_persists_provisional_advice(self):
        root = Path(__file__).resolve().parents[2]
        command = [sys.executable, str(root / "skills/reflect/runtime/record_cli.py"), "--database", str(self.store.path), "--project", self.store.project, "classification"]
        result = subprocess.run([*command, "prepare", "--id", "OBS-1"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)
        ctx = Path(self.temp.name) / "context.json"; ctx.write_text(json.dumps(context))
        out = Path(self.temp.name) / "output.json"; out.write_text(json.dumps(annotation(context)))
        saved = subprocess.run([*command, "save", "--context", str(ctx), "--output", str(out), "--expected-revision", "0", "--operation", "cli"], capture_output=True, text=True)
        self.assertEqual(saved.returncode, 0, saved.stderr)
        resumed = subprocess.run([*command, "get", "--id", "OBS-1"], capture_output=True, text=True)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(json.loads(resumed.stdout)["state"], "provisional")


if __name__ == "__main__":
    unittest.main()
