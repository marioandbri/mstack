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
