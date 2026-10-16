import base64
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from summaries import Summaries
from records import RecordError, RecordStore
from test_records import observation


def summary(context):
    fact = {"text": "Project conventions were not loaded.", "source_ids": ["observation:OBS-1"], "actor": "agent", "order": None}
    return {"schema_version": 1, "input_sha256": context["input_sha256"], "previous_revision": context["previous_revision"],
            "mode": "posthoc", "prepared_at": "2026-10-15T12:00:00Z", "author": "reviewing-agent",
            "linked_observation_ids": ["OBS-1"], "request": None, "scope": "project", "constraints": [],
            "actions": [fact], "results": [], "corrections": [], "authorizations": [], "instructions": [],
            "expected": None, "hypotheses": [], "contradictions": [], "unknowns": ["request", "expected", "action order", "outcome"],
            "completeness": "partial", "limits": ["Original session is unavailable. Only the retained observation is known."]}


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.records = RecordStore(Path(self.temp.name) / "records.sqlite3", "project")
        self.records.initialize(); self.records.capture("raw", observation())
        self.summaries = Summaries(self.records)

    def test_posthoc_summary_can_be_reopened_without_the_origin_session(self):
        cli = [sys.executable, str(Path(__file__).resolve().parents[2] / "skills/reflect/runtime/record_cli.py"), "--database", str(self.records.path), "--project", "project", "summary"]
        prepared = subprocess.run([*cli, "prepare", "--id", "OBS-1"], capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        ctx = json.loads(prepared.stdout)
        ctx_file = Path(self.temp.name) / "input.json"; ctx_file.write_text(json.dumps(ctx))
        output_file = Path(self.temp.name) / "output.json"; output_file.write_text(json.dumps(summary(ctx)))
        saved = subprocess.run([*cli, "save", "--context", str(ctx_file), "--output", str(output_file), "--expected-revision", "0", "--operation", "summary-1"], capture_output=True, text=True)
        self.assertEqual(saved.returncode, 0, saved.stderr)
        reopened = Summaries(RecordStore(self.records.path, "project")).latest("OBS-1")
        self.assertEqual(reopened["revision"], 1)
        self.assertEqual(reopened["summary"]["mode"], "posthoc")
        self.assertEqual(reopened["evidence"]["sources"][0]["sha256"], self.records.get("OBS-1")["raw_sha256"])
        self.assertTrue(reopened["evidence"]["excerpts"][0]["text"])
        self.assertNotIn("reconstruction", self.records.get("OBS-1")["pending"])

    def test_correction_adds_a_version_and_preserves_decisions_and_contradictions(self):
        ctx = self.summaries.prepare("OBS-1")
        self.summaries.save(ctx, summary(ctx), 0, "summary-1")
        self.records.transition("OBS-1", 0, "deferred", {"answer": "Defer installation.", "source": "user:9"}, "defer")
        evidence = {"sources": [{"id": "user:10", "sha256": None, "kind": "message", "temporal_role": "historical", "availability": "retained"}],
                    "excerpts": [{"id": "correction", "source_id": "user:10", "text": "The agent read the convention before implementing.", "sanitized": True, "kind": "quote"}]}
        ctx2 = self.summaries.prepare("OBS-1", evidence)
        revised = summary(ctx2)
        revised["corrections"] = [{"text": "The original omission was contradicted.", "source_ids": ["user:10"], "actor": "user", "order": None}]
        revised["contradictions"] = [{"text": "Original and correction disagree on whether conventions were read.", "source_ids": ["user:10", "observation:OBS-1"], "actor": None, "order": None}]
        self.summaries.save(ctx2, revised, 1, "summary-2")
        self.assertEqual(len(self.summaries.history("OBS-1")), 2)
        self.assertEqual(len(self.records.list()), 1)
        self.assertEqual(self.records.get("OBS-1")["state"], "deferred")
        self.assertEqual(base64.b64decode(self.records.get("OBS-1")["raw_base64"]), observation())
        self.assertEqual(self.summaries.latest("OBS-1")["summary"]["contradictions"], revised["contradictions"])

    def test_missing_provider_and_invented_sources_leave_raw_reconstruction_pending(self):
        ctx = self.summaries.prepare("OBS-1")
        with self.assertRaisesRegex(RecordError, "provider-unavailable"):
            self.summaries.save(ctx, None, 0, "unavailable")
        bad = summary(ctx); bad["actions"][0]["source_ids"] = ["invented:session"]
        with self.assertRaisesRegex(RecordError, "unknown-summary-source"):
            self.summaries.save(ctx, bad, 0, "invalid")
        self.assertEqual(self.summaries.history("OBS-1"), [])
        self.assertIn("reconstruction", self.records.get("OBS-1")["pending"])
        self.assertEqual(self.records.get("OBS-1")["state"], "inbox")

    def test_later_document_read_is_not_proof_of_historical_loading(self):
        evidence = {"sources": [{"id": "current:skill", "sha256": "a" * 64, "kind": "instruction", "temporal_role": "consulted-after", "availability": "retained"}],
                    "excerpts": [{"id": "current-trigger", "source_id": "current:skill", "text": "Load conventions before engineering.", "sanitized": True, "kind": "quote"}]}
        ctx = self.summaries.prepare("OBS-1", evidence)
        bad = summary(ctx); bad["instructions"] = [{"source_id": "current:skill", "availability": "loaded", "temporal_role": "historical", "evidence_ids": ["current:skill"]}]
        with self.assertRaisesRegex(RecordError, "unsupported-historical-context"):
            self.summaries.save(ctx, bad, 0, "claim")


if __name__ == "__main__":
    unittest.main()
