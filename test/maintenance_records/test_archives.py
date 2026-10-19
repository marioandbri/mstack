import base64
import json
from pathlib import Path
import tempfile
import unittest
import multiprocessing

from archives import Archives, import_legacy
from records import RecordError, RecordStore
from reviews import Reviews
from annotations import Annotations
from summaries import Summaries
from search import SearchIndex
from test_records import observation
from test_summaries import summary
from test_annotations import annotation
from test_reviews import review, options


def interrupted_import(path, entries, channel):
    def inside(identity):
        channel.send("inside-transaction"); channel.recv()
    import_legacy(RecordStore(path, "project"), entries, after_each=inside)


def interrupted_export(path, destination, channel):
    def progress(*args):
        channel.send("copying"); channel.recv()
    Archives(RecordStore(path, "project")).export(destination, progress=progress)


def interrupted_restore(source_database, bundle, destination, channel, stop_phase):
    def progress(phase):
        if phase == stop_phase:
            channel.send(phase); channel.recv()
    Archives(RecordStore(source_database, "project")).restore(bundle, destination, progress=progress)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = RecordStore(self.root / "records.sqlite3", "project")
        self.store.initialize(); self.store.capture("raw", observation())

    def test_export_backup_and_restore_preserve_originals_versions_decisions_and_rebuildable_indexes(self):
        ctx = Summaries(self.store).prepare("OBS-1"); Summaries(self.store).save(ctx, summary(ctx), 0, "summary")
        Reviews(self.store).save(review(), options(), 0, "review")
        ctx = Annotations(self.store).prepare("OBS-1"); Annotations(self.store).save(ctx, annotation(ctx), 0, "classify")
        self.store.transition("OBS-1", 0, "deferred", {"answer": "Defer integration.", "source": "user:8"}, "defer")
        SearchIndex(self.store).rebuild_text()
        bundle = self.root / "backup"
        result = Archives(self.store).export(bundle)
        self.assertEqual(result["status"], "ready")
        readable = json.loads((bundle / "records.json").read_text())
        self.assertEqual(readable["observations"][0]["observation"]["id"], "OBS-1")
        restored = Archives(self.store).restore(bundle, self.root / "restored.sqlite3")
        reopened = RecordStore(restored["database"], "project")
        self.assertEqual(base64.b64decode(reopened.get("OBS-1")["raw_base64"]), observation())
        self.assertEqual(reopened.get("OBS-1")["state"], "deferred")
        self.assertEqual(len(Summaries(reopened).history("OBS-1")), 1)
        self.assertEqual(len(Annotations(reopened).history("OBS-1")), 1)
        self.assertEqual(Reviews(reopened).get("REVIEW-1")["active_question"]["id"], "behavior")
        self.assertIn("indexing", reopened.get("OBS-1")["pending"])
        self.assertEqual(SearchIndex(reopened).search("convenciones")["matches"][0]["id"], "OBS-1")
        with self.assertRaisesRegex(RecordError, "restore-destination-exists"):
            Archives(self.store).restore(bundle, self.store.path)

    def test_legacy_copies_preserve_raw_bytes_without_adding_occurrences_or_inventing_metadata(self):
        one = self.root / "original.json"; one.write_bytes(observation("LEGACY"))
        copy = self.root / "copy.json"; copy.write_text(json.dumps(json.loads(one.read_bytes()), ensure_ascii=False))
        result = import_legacy(self.store, [("observation", one), ("observation", copy)])
        self.assertEqual(result["observations_created"], 1)
        self.assertEqual(len(self.store.list()), 2)
        self.assertEqual(import_legacy(self.store, [("observation", copy)])["observations_created"], 0)
        self.assertEqual(base64.b64decode(self.store.get("LEGACY")["raw_base64"]), one.read_bytes())
        self.assertIsNone(self.store.get("LEGACY")["provenance"]["origin"][0]["harness"])
        self.assertEqual(len(self.store.get("LEGACY")["legacy_sources"]), 2)

    def test_legacy_review_retains_answers_with_unknown_request_and_missing_original_explicit(self):
        document = review(); document["id"] = "LEGACY-REVIEW"
        document["opportunities"][0]["observationIds"] = ["UNAVAILABLE"]
        document["opportunities"][0]["decision"] = {"status": "reject", "answer": "Do not change this.", "scope": "original free-text scope"}
        path = self.root / "old.review.json"; path.write_text(json.dumps(document))
        import_legacy(self.store, [("review", path)])
        result = Reviews(self.store).get("LEGACY-REVIEW")
        self.assertIsNone(result["options"]["request"])
        self.assertEqual(result["record"]["opportunities"][0]["decision"]["answer"], "Do not change this.")
        self.assertTrue(any(v["id"] == "UNAVAILABLE" for v in result["context"]["limits"]))
        self.assertIsNone(result["legacy"]["author"])
        self.assertEqual(result["allowed_actions"], ["read-evidence"])
        extra = result["options"]
        extra["request"] = {"answer": "Resume this historical review.", "source": "user:new-request"}
        Reviews(self.store).save(result["record"], extra, 1, "resume-legacy")
        resumed = Reviews(self.store).get("LEGACY-REVIEW")
        self.assertEqual(resumed["legacy"], result["legacy"])
        self.assertEqual(resumed["allowed_actions"], ["review", "prepare-proposal"])

    def test_review_answers_invalidate_classification_and_remain_visible_in_search(self):
        reviews = Reviews(self.store)
        document, extra = review(), options()
        reviews.save(document, extra, 0, "start")
        classifier = Annotations(self.store)
        context = classifier.prepare("OBS-1")
        classifier.save(context, annotation(context), 0, "before-decision")
        document["opportunities"][0]["decision"] = {"status": "reject", "answer": "Keep the current behavior.", "scope": "behavior"}
        extra["decision_sources"]["behavior"] = "user:reject"; extra["active_question"] = "destination"
        reviews.save(document, extra, 1, "reject")
        self.assertEqual(classifier.latest("OBS-1")["state"], "pending")
        self.assertIn("classification", self.store.get("OBS-1")["pending"])
        fresh = classifier.prepare("OBS-1")
        self.assertTrue(any(v.get("decision", {}).get("answer") == "Keep the current behavior." and v["source"] == "user:reject" for v in fresh["user_decisions"]))
        self.store.transition("OBS-1", 0, "resolved", {"answer": "Close this observation.", "source": "user:close"}, "close")
        match = SearchIndex(self.store).search("convenciones")["matches"][0]
        self.assertEqual(match["state"], "resolved")
        self.assertEqual(match["review_disposition"], "historical")
        self.assertEqual(match["review_decisions"][0]["decision"]["status"], "reject")

    def test_backup_declares_a_consistent_snapshot_while_another_writer_commits(self):
        written = False
        def progress(*args):
            nonlocal written
            if not written:
                written = True
                self.store.capture("concurrent", observation("CONCURRENT"))
        bundle = self.root / "concurrent-backup"
        manifest = Archives(self.store).export(bundle, progress=progress)
        self.assertEqual([v["id"] for v in manifest["confirmed_originals"]], ["OBS-1"])
        self.assertEqual(self.store.get("CONCURRENT")["id"], "CONCURRENT")
        destination = self.root / "snapshot.sqlite3"
        Archives(self.store).restore(bundle, destination)
        self.assertEqual([v["id"] for v in RecordStore(destination, "project").list()], ["OBS-1"])
        self.assertEqual(len(self.store.list()), 2)

    def test_process_death_during_import_or_export_never_marks_partial_work_ready(self):
        context = multiprocessing.get_context("spawn")
        legacy = self.root / "legacy.json"; legacy.write_bytes(observation("LEGACY"))
        for target, args in [(interrupted_import, (str(self.store.path), [("observation", str(legacy))])),
                             (interrupted_export, (str(self.store.path), str(self.root / "partial-export")))]:
            parent, child = context.Pipe()
            process = context.Process(target=target, args=(*args, child)); process.start()
            self.assertTrue(parent.poll(10)); parent.recv(); process.kill(); process.join(5)
            self.assertFalse(process.is_alive())
            self.assertEqual([v["id"] for v in self.store.list()], ["OBS-1"])
        self.assertEqual(Archives(self.store).inspect(self.root / "partial-export")["status"], "incomplete")
        with self.assertRaisesRegex(RecordError, "archive-not-ready"):
            Archives(self.store).restore(self.root / "partial-export", self.root / "not-created.sqlite3")
        self.assertFalse((self.root / "not-created.sqlite3").exists())

    def test_interrupted_restore_publishes_either_nothing_or_a_complete_recoverable_database(self):
        context = multiprocessing.get_context("spawn")
        bundle = self.root / "complete"; manifest = Archives(self.store).export(bundle)
        for phase in ("staged", "published"):
            destination = self.root / (phase + ".sqlite3")
            parent, child = context.Pipe()
            process = context.Process(target=interrupted_restore, args=(str(self.store.path), str(bundle), str(destination), child, phase)); process.start()
            self.assertTrue(parent.poll(10)); self.assertEqual(parent.recv(), phase); process.kill(); process.join(5)
            self.assertFalse(process.is_alive())
            if phase == "staged":
                self.assertFalse(destination.exists())
            else:
                restored = RecordStore(destination, "project")
                self.assertEqual(base64.b64decode(restored.get("OBS-1")["raw_base64"]), observation())
                self.assertEqual(Archives(restored).restored_status()["restorations"][-1]["archive_id"], manifest["id"])


if __name__ == "__main__":
    unittest.main()
