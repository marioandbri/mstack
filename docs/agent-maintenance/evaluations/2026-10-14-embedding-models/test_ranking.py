"""Protect retrieval grades and project filtering with worked examples."""
from pathlib import Path
import tempfile
import unittest

from ranking import RetrievalIndex, measure


class RetrievalTests(unittest.TestCase):
    def test_context_is_not_a_direct_hit(self):
        grades = {"direct": 2, "context": 1, "other": 0}
        actual = measure(["context", "other", "direct"], grades)
        self.assertFalse(actual["hit_at_1"])
        self.assertTrue(actual["hit_at_3"])
        self.assertEqual(actual["recall_at_3"], 1)
        self.assertAlmostEqual(actual["mrr_at_5"], 1 / 3)
        # Gain 3 for direct, 1 for context. Ideal order is direct, context.
        self.assertAlmostEqual(actual["ndcg_at_5"], 0.68852888094)

    def test_absent_target_is_not_given_a_success_score(self):
        actual = measure(["nearby"], {"nearby": 0})
        self.assertIsNone(actual["hit_at_3"])
        self.assertIsNone(actual["ndcg_at_5"])
        self.assertTrue(actual["returned_candidates_without_direct_target"])

    def test_sqlite_queries_preserve_scope_and_rank_real_vectors(self):
        with tempfile.TemporaryDirectory() as directory:
            index = RetrievalIndex(Path(directory) / "index.sqlite", 3)
            records = [
                {"id": "match", "text": "permisos revisión", "project": "mstack"},
                {"id": "neighbor", "text": "modelo vectorial", "project": "mstack"},
                {"id": "foreign", "text": "permisos revisión", "project": "different"},
            ]
            index.load(records, [[1, 0, 0], [0, 1, 0], [1, 0, 0]])
            self.assertEqual(index.vector([1, 0, 0], "mstack", 3)[0]["id"], "match")
            self.assertEqual([row["id"] for row in index.lexical("permisos", "mstack", 3)], ["match"])
            self.assertEqual(index.vector([1, 0, 0], "absent", 3), [])
            self.assertEqual(index.lexical("permisos", "absent", 3), [])
            self.assertNotIn("foreign", [row["id"] for row in index.hybrid([1, 0, 0], "permisos", "mstack", 3)])
            index.close()


if __name__ == "__main__":
    unittest.main()
