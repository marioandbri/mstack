"""Public record operations; capture never starts reflection or model calls."""
import argparse
import json
from pathlib import Path
import sys

from records import RecordError, RecordStore


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--database", required=True)
    result.add_argument("--project", required=True)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    capture = commands.add_parser("capture")
    capture.add_argument("--operation", required=True)
    capture.add_argument("--original", required=True)
    capture.add_argument("--provenance")
    get = commands.add_parser("get")
    get.add_argument("--id", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--scope")
    listing.add_argument("--state")
    transition = commands.add_parser("transition")
    transition.add_argument("--id", required=True)
    transition.add_argument("--expected-revision", type=int, required=True)
    transition.add_argument("--state", required=True)
    transition.add_argument("--evidence", required=True)
    transition.add_argument("--operation", required=True)
    history = commands.add_parser("history")
    history.add_argument("--id", required=True)
    history.add_argument("--kind", required=True)
    classification = commands.add_parser("classification").add_subparsers(dest="action", required=True)
    prepare = classification.add_parser("prepare")
    prepare.add_argument("--id", required=True)
    prepare.add_argument("--related", action="append", default=[])
    save = classification.add_parser("save")
    save.add_argument("--context", required=True)
    save.add_argument("--output", required=True, help="JSON output or null when the provider is unavailable")
    save.add_argument("--expected-revision", type=int, required=True)
    save.add_argument("--operation", required=True)
    classification.add_parser("get").add_argument("--id", required=True)
    summary = commands.add_parser("summary").add_subparsers(dest="action", required=True)
    prepare_summary = summary.add_parser("prepare")
    prepare_summary.add_argument("--id", required=True)
    prepare_summary.add_argument("--evidence")
    prepare_summary.add_argument("--related", action="append", default=[])
    save_summary = summary.add_parser("save")
    save_summary.add_argument("--context", required=True)
    save_summary.add_argument("--output", required=True)
    save_summary.add_argument("--expected-revision", type=int, required=True)
    save_summary.add_argument("--operation", required=True)
    summary.add_parser("get").add_argument("--id", required=True)
    search = commands.add_parser("search")
    search.add_argument("--text", required=True)
    search.add_argument("--scope")
    search.add_argument("--state")
    search.add_argument("--category")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--semantic", action="store_true")
    search.add_argument("--model-path")
    indexing = commands.add_parser("index").add_subparsers(dest="action", required=True)
    indexing.add_parser("status")
    indexing.add_parser("text")
    indexing.add_parser("reset-vectors")
    indexing.add_parser("vectors").add_argument("--model-path", required=True)
    review = commands.add_parser("review").add_subparsers(dest="action", required=True)
    for action in ("get", "history"):
        review.add_parser(action).add_argument("--id", required=True)
    save_review = review.add_parser("save")
    save_review.add_argument("--record", required=True)
    save_review.add_argument("--options", required=True)
    save_review.add_argument("--expected-revision", required=True, type=int)
    save_review.add_argument("--operation", required=True)
    save_review.add_argument("--chat-only", action="store_true")
    reconcile = review.add_parser("reconcile")
    reconcile.add_argument("--id", required=True)
    reconcile.add_argument("--checks", required=True)
    reconcile.add_argument("--expected-revision", required=True, type=int)
    reconcile.add_argument("--operation", required=True)
    return result


def run(args):
    store = RecordStore(args.database, args.project)
    if args.command in ("init", "capture"):
        store.initialize()
    if args.command == "init":
        return {"status": "initialized", "project": args.project}
    if args.command == "capture":
        origin = json.loads(Path(args.provenance).read_text()) if args.provenance else None
        return {**store.capture(args.operation, Path(args.original).read_bytes(), origin), "next": "return-to-task"}
    if args.command == "get":
        return store.get(args.id)
    if args.command == "list":
        return store.list(args.scope, args.state)
    if args.command == "transition":
        return store.transition(args.id, args.expected_revision, args.state, json.loads(Path(args.evidence).read_text()), args.operation)
    if args.command == "history":
        return store.history(args.id, args.kind)
    if args.command == "classification":
        from annotations import Annotations
        annotations = Annotations(store)
        if args.action == "prepare":
            return annotations.prepare(args.id, args.related)
        if args.action == "save":
            return annotations.save(json.loads(Path(args.context).read_text()), json.loads(Path(args.output).read_text()), args.expected_revision, args.operation)
        return annotations.latest(args.id)
    if args.command == "summary":
        from summaries import Summaries
        summaries = Summaries(store)
        if args.action == "prepare":
            return summaries.prepare(args.id, json.loads(Path(args.evidence).read_text()) if args.evidence else None, args.related)
        if args.action == "save":
            return summaries.save(json.loads(Path(args.context).read_text()), json.loads(Path(args.output).read_text()), args.expected_revision, args.operation)
        return summaries.latest(args.id)
    if args.command in ("search", "index"):
        from search import SearchIndex
        from embeddings import Gemma
        index = SearchIndex(store)
        if args.command == "search":
            encoder, unavailable = None, None
            if args.semantic and args.model_path:
                try:
                    encoder = Gemma(args.model_path)
                except RecordError as error:
                    unavailable = str(error)
            result = index.search(args.text, scope=args.scope, state=args.state, category=args.category, limit=args.limit, semantic=args.semantic, encoder=encoder)
            if unavailable:
                result["semantic_error"] = unavailable
            return result
        if args.action == "text":
            return index.rebuild_text()
        if args.action == "vectors":
            return index.index_pending(Gemma(args.model_path))
        if args.action == "reset-vectors":
            return index.reset_vectors()
        return index.status()
    if args.command == "review":
        from reviews import Reviews
        reviews = Reviews(store)
        if args.action == "save":
            return reviews.save(json.loads(Path(args.record).read_text()), json.loads(Path(args.options).read_text()), args.expected_revision, args.operation, chat_only=args.chat_only)
        if args.action == "reconcile":
            return reviews.reconcile(args.id, json.loads(Path(args.checks).read_text()), args.expected_revision, args.operation)
        return reviews.get(args.id) if args.action == "get" else reviews.history(args.id)
    raise RecordError("unknown-operation")


def main():
    args = parser().parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, allow_nan=False))
    except RecordError as error:
        print(json.dumps({"error": str(error), "acknowledged": False, "persistence": "unconfirmed"}), file=sys.stderr)
        return 1
    except (ValueError, OSError, TypeError):
        print(json.dumps({"error": "invalid-input-or-storage", "acknowledged": False, "persistence": "unconfirmed"}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
