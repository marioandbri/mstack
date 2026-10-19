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
    comparison = commands.add_parser("comparison")
    comparison.add_argument("--runner-root", required=True)
    compare_commands = comparison.add_subparsers(dest="action", required=True)
    compare_commands.add_parser("prepare").add_argument("--plan", required=True)
    compare_commands.add_parser("get").add_argument("--id", required=True)
    compare_result = compare_commands.add_parser("result")
    compare_result.add_argument("--id", required=True)
    compare_result.add_argument("--result-id", required=True)
    compare_result.add_argument("--assessments", required=True)
    delivery = commands.add_parser("delivery")
    for key in ("runner-root", "installer-repository", "source-repository", "home", "control"):
        delivery.add_argument("--" + key, required=True)
    delivery.add_argument("--target-mode", choices=("isolated", "active"), default="isolated")
    delivery_commands = delivery.add_subparsers(dest="action", required=True)
    delivery_prepare = delivery_commands.add_parser("prepare")
    for key in ("id", "review-id", "behavior-id", "destination-id", "commit"):
        delivery_prepare.add_argument("--" + key, required=True)
    for action in ("get", "reconcile"):
        delivery_commands.add_parser(action).add_argument("--id", required=True)
    for action in ("promote", "rollback"):
        operation = delivery_commands.add_parser(action)
        operation.add_argument("--id", required=True); operation.add_argument("--grant", required=True)
    installed = delivery_commands.add_parser("profile")
    for key in ("id", "environment", "profile-id"):
        installed.add_argument("--" + key, required=True)
    installed.add_argument("--kind", choices=("fixture", "agent"), required=True)
    installed.add_argument("--model"); installed.add_argument("--reasoning"); installed.add_argument("--seconds", type=int, required=True)
    checked = delivery_commands.add_parser("check")
    for key in ("id", "attempt", "stage"):
        checked.add_argument("--" + key, required=True)
    checked.add_argument("--assessment-id")
    archive = commands.add_parser("archive").add_subparsers(dest="action", required=True)
    archive.add_parser("import").add_argument("--manifest", required=True, help="JSON list of {kind, path} historical files; initialize the destination first")
    archive.add_parser("export").add_argument("--destination", required=True)
    archive.add_parser("inspect").add_argument("--source", required=True)
    restore = archive.add_parser("restore")
    restore.add_argument("--source", required=True); restore.add_argument("--destination", required=True)
    archive.add_parser("restored-status")
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
    if args.command == "comparison":
        from comparisons import Comparisons
        from evaluation import Runner
        from reviews import Reviews
        comparisons = Comparisons(Reviews(store), Runner(args.runner_root))
        if args.action == "prepare":
            plan = json.loads(Path(args.plan).read_text())
            return comparisons.prepare(**plan)
        if args.action == "result":
            return comparisons.record_result(args.id, args.result_id, json.loads(Path(args.assessments).read_text()))
        return comparisons.get(args.id)
    if args.command == "delivery":
        from delivery import Delivery
        from evaluation import Runner
        from reviews import Reviews
        delivery = Delivery(Reviews(store), Runner(args.runner_root), args.installer_repository, args.source_repository, args.home, args.control, mode=args.target_mode)
        if args.action == "prepare":
            return delivery.prepare(args.id, args.review_id, args.behavior_id, args.destination_id, args.commit)
        if args.action in ("promote", "rollback"):
            return getattr(delivery, args.action)(args.id, json.loads(Path(args.grant).read_text()))
        if args.action == "profile":
            if (args.kind == "agent" and (not args.model or not args.reasoning)) or (args.kind == "fixture" and (args.model or args.reasoning)):
                raise RecordError("invalid-installed-profile-kind")
            return delivery.installed_profile(args.id, json.loads(Path(args.environment).read_text()), identity=args.profile_id, model=args.model, reasoning=args.reasoning, seconds=args.seconds)
        if args.action == "check":
            return delivery.record_check(args.id, args.attempt, args.stage, args.assessment_id)
        return delivery.reconcile(args.id) if args.action == "reconcile" else delivery.get(args.id)
    if args.command == "archive":
        from archives import Archives, import_legacy
        archive = Archives(store)
        if args.action == "import":
            entries = json.loads(Path(args.manifest).read_text())
            if not isinstance(entries, list) or any(not isinstance(v, dict) or set(v) != {"kind", "path"} for v in entries):
                raise RecordError("invalid-legacy-manifest")
            return import_legacy(store, [(v["kind"], v["path"]) for v in entries])
        if args.action == "export":
            return archive.export(args.destination)
        if args.action == "inspect":
            return archive.inspect(args.source)
        if args.action == "restore":
            return archive.restore(args.source, args.destination)
        return archive.restored_status()
    raise RecordError("unknown-operation")


def main():
    args = parser().parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, allow_nan=False))
    except RecordError as error:
        print(json.dumps({"error": str(error), "acknowledged": False, "persistence": "unconfirmed"}), file=sys.stderr)
        return 1
    except Exception as error:
        from evaluation import EvaluationError
        if isinstance(error, EvaluationError):
            print(json.dumps({"error": str(error), "acknowledged": False, "persistence": "unconfirmed"}), file=sys.stderr)
        else:
            print(json.dumps({"error": "invalid-input-or-storage", "acknowledged": False, "persistence": "unconfirmed"}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
