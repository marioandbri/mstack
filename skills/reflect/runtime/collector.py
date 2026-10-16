"""Collect terminated, owned evaluation workspaces without model calls."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import time
import uuid

MARKER = ".mstack-evaluation.json"
TERMINAL_STATES = {"completed", "timeout", "interrupted", "infrastructure-error", "not-executed"}
PRIVATE_NAMES = {".git", ".ssh", ".aws", ".codex", ".netrc", "auth.json", "credentials.json"}
RUNTIME_NAMES = {".cache", ".venv", "node_modules", "__pycache__"}


class CollectionError(Exception):
    pass


def _write_json(path, value):
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex)
    try:
        with temporary.open("x", encoding="utf-8") as output:
            temporary.chmod(0o600)
            json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n"); output.flush(); os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def create_workspace(path, attempt_id):
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise CollectionError("invalid-attempt")
    root = Path(path).resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    info = root.stat()
    _write_json(root / MARKER, {"schema_version": 1, "attempt_id": attempt_id, "owner": os.getuid(), "device": info.st_dev, "inode": info.st_ino})
    return root


def _owned_workspace(path, attempt_id):
    root = Path(path).resolve(strict=True)
    info = root.stat()
    try:
        marker = json.loads((root / MARKER).read_text())
    except (OSError, ValueError):
        raise CollectionError("unowned-workspace") from None
    expected = {"schema_version": 1, "attempt_id": attempt_id, "owner": os.getuid(), "device": info.st_dev, "inode": info.st_ino}
    if marker != expected or info.st_uid != os.getuid():
        raise CollectionError("unowned-workspace")
    return root


@contextmanager
def _owner_access(path, required):
    info = path.lstat()
    if info.st_uid != os.getuid() or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
        raise CollectionError("unowned-or-special-artifact")
    if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
        raise CollectionError("shared-artifact-inode")
    mode = stat.S_IMODE(info.st_mode)
    changed = mode & required != required
    if changed:
        path.chmod(mode | required, follow_symlinks=False)
    try:
        yield mode, changed
    finally:
        if changed:
            path.chmod(mode, follow_symlinks=False)


def _copy_file(source, destination, deadline):
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = destination.with_name("." + destination.name + "." + uuid.uuid4().hex + ".partial")
    sha = hashlib.sha256()
    size = 0
    try:
        with _owner_access(source, 0o400) as (mode, changed):
            descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as incoming, temporary.open("xb") as outgoing:
                temporary.chmod(0o600)
                while block := incoming.read(1024 * 1024):
                    if time.monotonic() >= deadline:
                        raise CollectionError("collection-timeout")
                    outgoing.write(block); sha.update(block); size += len(block)
                outgoing.flush(); os.fsync(outgoing.fileno())
            temporary.chmod(0o700 if mode & 0o100 else 0o600)
            os.replace(temporary, destination)
            with destination.open("rb") as exported:
                if hashlib.file_digest(exported, "sha256").hexdigest() != sha.hexdigest():
                    raise CollectionError("export-hash-mismatch")
        return {"sha256": sha.hexdigest(), "bytes": size, "original_mode": f"{mode:04o}", "owner_read_added": changed, "status": "collected"}
    finally:
        temporary.unlink(missing_ok=True)


def _inspect_result(destination, report):
    try:
        result = json.loads((destination / "workspace/result.json").read_text())
        if not isinstance(result, dict):
            raise ValueError()
    except FileNotFoundError:
        report["infrastructure_states"].append("missing-result")
    except (ValueError, OSError):
        report["infrastructure_states"].append("invalid-result")
    try:
        count = 0
        with (destination / "workspace/events.jsonl").open() as events:
            for line in events:
                if not isinstance(json.loads(line), dict):
                    raise ValueError()
                count += 1
        report["event_count"] = count
        if not count:
            report["infrastructure_states"].append("missing-events")
    except FileNotFoundError:
        report["infrastructure_states"].append("missing-events")
    except (ValueError, OSError):
        report["infrastructure_states"].append("partial-trace")


def collect_workspace(source, destination, attempt_id, terminal, *, recovery_of=None, timeout_seconds=30):
    """The caller must have stopped all consumers of this owned workspace."""
    if (not isinstance(terminal, str) or terminal not in TERMINAL_STATES or
            type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds) or timeout_seconds < 0):
        raise CollectionError("invalid-collection-request")
    source = _owned_workspace(source, attempt_id)
    destination = Path(destination).resolve()
    if source == destination or source in destination.parents:
        raise CollectionError("destination-inside-source")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"schema_version": 1, "attempt_id": attempt_id, "recovery_of": recovery_of, "stage": "recovered" if recovery_of else "executed" if terminal == "completed" else "inconclusive", "execution_status": terminal, "behavioral_status": "ungraded", "collection_status": "in-progress", "captured_at": datetime.now(timezone.utc).isoformat(), "artifacts": [], "infrastructure_states": []}
    _write_json(destination / "collection.json", report)
    deadline = time.monotonic() + timeout_seconds

    def walk(directory):
        if time.monotonic() >= deadline:
            raise CollectionError("collection-timeout")
        with _owner_access(directory, 0o500):
            for path in sorted(directory.iterdir()):
                if time.monotonic() >= deadline:
                    raise CollectionError("collection-timeout")
                rel = path.relative_to(source).as_posix()
                if path.name == MARKER:
                    continue
                if path.name in PRIVATE_NAMES or path.name == ".env" or path.name.startswith(".env."):
                    report["artifacts"].append({"path": rel, "status": "excluded-private"}); continue
                if path.is_symlink():
                    report["artifacts"].append({"path": rel, "status": "excluded-link"}); continue
                if path.is_dir() and (path.name in RUNTIME_NAMES or not (path / "pyvenv.cfg").is_symlink() and (path / "pyvenv.cfg").is_file()):
                    report["artifacts"].append({"path": rel, "status": "excluded-runtime"}); continue
                try:
                    if path.is_dir():
                        walk(path)
                    else:
                        report["artifacts"].append({"path": rel, **_copy_file(path, destination / "workspace" / rel, deadline)})
                except CollectionError as error:
                    if str(error) == "collection-timeout":
                        raise
                    report["artifacts"].append({"path": rel, "status": "unavailable", "error": str(error)})
                    report["infrastructure_states"].append("unavailable-artifact")
                except OSError:
                    report["artifacts"].append({"path": rel, "status": "unavailable", "error": "artifact-access-failed"})
                    report["infrastructure_states"].append("unavailable-artifact")

    try:
        walk(source)
        report["collection_status"] = "partial" if report["infrastructure_states"] else "complete"
    except CollectionError as error:
        report["collection_status"] = "timeout" if str(error) == "collection-timeout" else "partial"
        report["infrastructure_states"].append(str(error))
    except KeyboardInterrupt:
        report["collection_status"] = "interrupted"
        report["infrastructure_states"].append("collection-interrupted")
    except OSError:
        report["collection_status"] = "partial"
        report["infrastructure_states"].append("unavailable-artifact")
    _inspect_result(destination, report)
    if report["infrastructure_states"]:
        report["stage"] = "recovered" if recovery_of else "inconclusive"
    _write_json(destination / "collection.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--workspace", required=True)
    create.add_argument("--attempt", required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--source", required=True)
    collect.add_argument("--destination", required=True)
    collect.add_argument("--attempt", required=True)
    collect.add_argument("--terminal", required=True, choices=sorted(TERMINAL_STATES))
    collect.add_argument("--timeout", type=float, default=30)
    collect.add_argument("--recovery-of")
    args = parser.parse_args()
    try:
        if args.command == "create":
            create_workspace(args.workspace, args.attempt)
            print(json.dumps({"status": "created", "attempt_id": args.attempt}))
            return 0
        report = collect_workspace(args.source, args.destination, args.attempt, args.terminal, recovery_of=args.recovery_of, timeout_seconds=args.timeout)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["collection_status"] == "complete" and not report["infrastructure_states"] else 1
    except CollectionError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
    except (OSError, ValueError):
        print(json.dumps({"error": "collection-access-failed"}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
