import json
from pathlib import Path
import tempfile
import unittest
import os
import subprocess
import sys

from records import RecordError, RecordStore
from search import SearchIndex
from test_records import observation


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.records = RecordStore(Path(self.temp.name) / "records.sqlite3", "project")
        self.records.initialize(); self.records.capture("one", observation())
        self.index = SearchIndex(self.records)

    def test_text_and_id_remain_available_without_vectors_and_respect_scope(self):
        self.index.rebuild_text()
        other = json.loads(observation("OTHER", scope="other")); other["observation"] = "An unrelated networking problem."
        self.records.capture("other", json.dumps(other).encode())
        self.assertEqual(self.index.by_id("OBS-1")["id"], "OBS-1")
        self.assertEqual([v["id"] for v in self.index.search("convenciones", scope="project")["matches"]], ["OBS-1"])
        self.assertEqual(self.index.search("networking", scope="project")["matches"], [])
        self.assertEqual([v["id"] for v in self.index.search("networking", scope="other")["matches"]], ["OTHER"])
        self.assertEqual(self.index.status()["vector_pending_ids"], ["OBS-1", "OTHER"])
        with self.assertRaisesRegex(RecordError, "project-mismatch"):
            SearchIndex(RecordStore(self.records.path, "another-project")).search("convention")

    def test_vectors_publish_atomically_and_filter_before_top_k(self):
        self.records.capture("other", observation("OTHER", scope="other"))
        one = self.index.prepare_embedding("OBS-1")
        other = self.index.prepare_embedding("OTHER")
        vector = [1.0] + [0.0] * 767
        self.index.publish_embedding(one, vector, {"kind": "fixture", "version": "test-1", "token_count": None, "truncated": False}, "one")
        self.index.publish_embedding(other, vector, {"kind": "fixture", "version": "test-1", "token_count": None, "truncated": False}, "other")
        result = self.index.vector(vector, scope="project", limit=1)
        self.assertEqual([value["id"] for value in result["matches"]], ["OBS-1"])
        self.assertAlmostEqual(result["matches"][0]["match"]["distance"], 0)
        self.assertEqual(self.index.status()["vector_pending_ids"], [])
        self.assertNotIn("indexing", self.records.get("OBS-1")["pending"])
        self.index.reset_vectors()
        self.assertEqual(self.index.status()["vector_pending_ids"], ["OBS-1", "OTHER"])
        self.assertEqual(len(self.records.list()), 2)
        self.assertIn("indexing", self.records.get("OBS-1")["pending"])
        self.assertEqual(self.index.publish_embedding(one, vector, {"kind": "fixture", "version": "test-1", "token_count": None, "truncated": False}, "rebuild")["status"], "indexed")

    def test_invalid_or_stale_vectors_never_replace_current_metadata(self):
        context = self.index.prepare_embedding("OBS-1")
        meta = {"kind": "fixture", "version": "test-1", "token_count": None, "truncated": False}
        for vector in ([0.] * 768, [float("nan")] * 768, [1., 0.]):
            with self.subTest(length=len(vector)), self.assertRaisesRegex(RecordError, "invalid-vector"):
                self.index.publish_embedding(context, vector, meta, "bad")
        stale = dict(context); stale["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(RecordError, "embedding-input-stale"):
            self.index.publish_embedding(stale, [1.] + [0.] * 767, meta, "stale")
        self.assertEqual(self.index.status()["vector_pending_ids"], ["OBS-1"])
        self.assertEqual(self.index.search("convenciones", semantic=True)["method"], "text-fallback")

    def test_encoding_holds_no_writer_lock_and_late_retry_cannot_replace_newer_vector(self):
        records = self.records
        class FixtureEncoder:
            def encode(self, text, role):
                records.capture("during-encoding", observation("DURING"))
                return [1.] + [0.] * 767, {"kind": "fixture", "version": "1", "token_count": None, "truncated": False}
        self.index.index_pending(FixtureEncoder())
        self.assertIn("DURING", self.index.status()["vector_pending_ids"])
        ctx = self.index.prepare_embedding("OBS-1")
        meta = {"kind": "fixture", "version": "2", "token_count": None, "truncated": False}
        first = [0., 1.] + [0.] * 766
        self.index.publish_embedding(ctx, first, meta, "first")
        second = [0., 0., 1.] + [0.] * 765
        self.index.publish_embedding(ctx, second, meta, "second")
        self.index.publish_embedding(ctx, first, meta, "first")
        self.assertAlmostEqual(self.index.vector(second)["matches"][0]["match"]["distance"], 0)

    def test_category_filter_does_not_use_an_annotation_with_changed_related_decisions(self):
        from annotations import Annotations
        from test_annotations import annotation
        self.records.capture("related", observation("RELATED"))
        annotations = Annotations(self.records)
        context = annotations.prepare("OBS-1", ["RELATED"])
        annotations.save(context, annotation(context), 0, "classification")
        self.assertEqual(len(self.index.search("convenciones", category="agent-failure")["matches"]), 1)
        self.records.transition("RELATED", 0, "discarded", {"answer": "Reject the related proposal.", "source": "user:later"}, "related-decision")
        self.assertEqual(annotations.latest("OBS-1")["state"], "pending")
        self.assertEqual(self.index.search("convenciones", category="agent-failure")["matches"], [])

    @unittest.skipUnless(os.environ.get("MSTACK_GEMMA_MODEL_PATH"), "Real Gemma smoke requires its already accepted offline snapshot and embeddings extra")
    def test_real_selected_gemma_profile_through_public_index_and_cli(self):
        from embeddings import Gemma
        root = Path(__file__).resolve().parents[2]
        corpus = json.loads((root / "docs/agent-maintenance/evaluations/2026-10-14-embedding-corpus/records.json").read_text())
        # Frozen exploratory records remain unchanged; these temporary wrappers are fixtures.
        for item in corpus["records"]:
            if item["id"] in ("R02", "R08", "R09"):
                value = json.loads(observation(item["id"], "reflect-smoke"))
                value["basis"] = "technical-fact"; value["observation"] = item["text"]
                value["evidence"] = [{"source": "embedding-corpus:" + item["id"], "summary": "Temporary functional fixture; existing proposed labels are not approved gold."}]
                self.records.capture("fixture:" + item["id"], json.dumps(value).encode())
        encoder = Gemma(os.environ["MSTACK_GEMMA_MODEL_PATH"])
        self.index.index_pending(encoder)
        result = self.index.search("La revisión sin aplicar dejó el trabajo sólo en el chat y perdió las decisiones entre sesiones.", scope="reflect-smoke", semantic=True, encoder=encoder)
        self.assertEqual(result["method"], "sqlite-vec-cosine")
        self.assertEqual(result["matches"][0]["id"], "R02")
        self.assertEqual(result["coverage"]["vector_pending_ids"], [])
        no_match = self.index.search("Renovar certificados TLS del servidor de producción.", scope="reflect-smoke", semantic=True, encoder=encoder)
        self.assertTrue(all(v["status"] == "candidate" for v in no_match["matches"]))
        cli = subprocess.run([sys.executable, str(root / "skills/reflect/runtime/record_cli.py"), "--database", str(self.records.path), "--project", "project", "search", "--text", "La revisión perdió las decisiones entre sesiones.", "--scope", "reflect-smoke", "--semantic", "--model-path", os.environ["MSTACK_GEMMA_MODEL_PATH"]], capture_output=True, text=True, timeout=45)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertEqual(json.loads(cli.stdout)["matches"][0]["id"], "R02")
        print(json.dumps({"gemma_smoke": "passed", "positive_top_1": "R02", "nearby_context": ["R08", "R09"], "no_match_returned_candidates": len(no_match["matches"]), "confirmed_incidents": 0, "threshold_tuned": False, "hosted_model_calls": 0}))


if __name__ == "__main__":
    unittest.main()
