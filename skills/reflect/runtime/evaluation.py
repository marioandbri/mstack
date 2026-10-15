"""Freeze cases, reserve bounded authorization, execute once and collect evidence."""
from datetime import datetime, timezone
from contextlib import contextmanager
import fcntl
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import subprocess
import time

from collector import create_workspace, collect_workspace, _write_json
from records import digest, encoded

HERE = Path(__file__).resolve().parent


def execution_sources():
    paths = [*HERE.glob("*.py"), *HERE.glob("*.json"), *HERE.glob("*.toml"), *HERE.glob("*.lock"), *HERE.parent.glob("*.schema.json")]
    return {path.relative_to(HERE.parent).as_posix(): digest(path.read_bytes()) for path in sorted(paths)}


class EvaluationError(Exception):
    pass


class ExecutionFailure(EvaluationError):
    """Preserve observed execution facts when transport finalization fails."""
    def __init__(self, code, partial, *, consumers_stopped):
        super().__init__(code)
        self.partial, self.consumers_stopped = partial, consumers_stopped


def safe_path(value):
    if not isinstance(value, str) or not value or PurePosixPath(value).is_absolute() or any(p in ('', '.', '..') for p in value.split('/')) or '\\' in value:
        raise EvaluationError("invalid-fixture-path")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,100}', value):
        raise EvaluationError("invalid-identifier")
    return value


def private_directory(path):
    path = Path(path).absolute()
    if path.is_symlink():
        raise EvaluationError("unsafe-evaluation-directory")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise EvaluationError("unsafe-evaluation-directory")
    return path.resolve()


def validate_case(case, profile):
    required = {"schema_version", "id", "kind", "incident_id", "request", "initial_state", "expected_behavior", "sources", "nearby_negative", "fixture", "checks"}
    if not isinstance(case, dict) or set(case) - {"explicit_skills", "setup_commands", "rubric"} != required or case["schema_version"] != 1 or case["kind"] not in ("real-episode", "unexecuted-scenario", "synthetic-fixture", "variant"):
        raise EvaluationError("invalid-case")
    identifier(case["id"])
    if (any(not isinstance(case[key], str) or not case[key].strip() for key in ("request", "initial_state")) or
            not isinstance(case["expected_behavior"], list) or not case["expected_behavior"] or any(not isinstance(v, str) or not v.strip() for v in case["expected_behavior"]) or
            not isinstance(case["sources"], list) or not case["sources"] or
            (case["kind"] in ("real-episode", "variant") and not case["incident_id"])):
        raise EvaluationError("invalid-case")
    for source in case["sources"]:
        if not isinstance(source, dict) or set(source) != {"reference", "sha256"} or not isinstance(source["reference"], str) or not source["reference"].strip() or (source["sha256"] is not None and not re.fullmatch(r'[0-9a-f]{64}', source["sha256"])):
            raise EvaluationError("invalid-case-source")
    required_profile = {"schema_version", "id", "kind", "source_commit", "model", "reasoning", "harness", "environment", "budget_seconds", "max_turns", "instructions", "catalog", "source_files"}
    if not isinstance(profile, dict) or set(profile) != required_profile or profile["schema_version"] != 1 or profile["kind"] not in ("fixture", "agent"):
        raise EvaluationError("invalid-profile")
    identifier(profile["id"])
    if (type(profile["budget_seconds"]) not in (int, float) or not math.isfinite(profile["budget_seconds"]) or not 0 < profile["budget_seconds"] <= 3600 or
            type(profile["max_turns"]) is not int or profile["max_turns"] != 1):
        raise EvaluationError("invalid-profile-budget")
    if not isinstance(profile["harness"], dict) or set(profile["harness"]) != {"name", "version"} or any(not isinstance(v, str) or not v for v in profile["harness"].values()):
        raise EvaluationError("invalid-harness")
    environment = profile["environment"]
    text_keys = {"image_digest", "codex", "python", "bun", "uv", "git", "node", "platform", "architecture", "sqlite", "docker_endpoint"}
    if not isinstance(environment, dict) or set(environment) - text_keys - {"docker_plugin_directories", "versions_observed", "freeze_tool", "installation"}:
        raise EvaluationError("unknown-environment-field")
    if any(not isinstance(environment[k], str) or not environment[k].strip() for k in text_keys & environment.keys()):
        raise EvaluationError("invalid-environment-field")
    for key in ("docker_plugin_directories", "versions_observed"):
        if key in environment and (not isinstance(environment[key], list) or any(not isinstance(v, str) or not v.strip() for v in environment[key])):
            raise EvaluationError("invalid-environment-field")
    if "freeze_tool" in environment:
        value = environment["freeze_tool"]
        if (not isinstance(value, dict) or set(value) != {"commit", "files"} or not re.fullmatch(r'[0-9a-f]{40,64}', value["commit"]) or
                not isinstance(value["files"], dict) or set(value["files"]) != {"install/mstack_source.py", "install/mstack_config.py", "install/mstack_fs.py"} or
                any(not isinstance(v, str) or not re.fullmatch(r'[0-9a-f]{64}', v) for v in value["files"].values())):
            raise EvaluationError("invalid-source-freeze-provenance")
    if "installation" in environment:
        value = environment["installation"]
        if (not isinstance(value, dict) or set(value) != {"target_id", "mode", "commit", "generation", "bundle_sha256"} or value["mode"] not in ("isolated", "active") or
                any(not isinstance(value[k], str) or not re.fullmatch(pattern, value[k]) for k, pattern in (("target_id", r'[0-9a-f]{32}'), ("commit", r'[0-9a-f]{40,64}'), ("generation", r'[0-9a-f]{32}'), ("bundle_sha256", r'[0-9a-f]{64}')))):
            raise EvaluationError("invalid-installation-provenance")
    if profile["kind"] == "agent" and (not re.fullmatch(r'[0-9a-f]{40,64}', profile["source_commit"] or '') or any(not isinstance(profile[key], str) or not profile[key].strip() for key in ("model", "reasoning")) or not isinstance(profile["environment"], dict) or not re.fullmatch(r'sha256:[0-9a-f]{64}', profile["environment"].get("image_digest", ''))):
        raise EvaluationError("unfrozen-agent-profile")
    for files in (case["fixture"], profile["instructions"], profile["source_files"]):
        if not isinstance(files, dict):
            raise EvaluationError("invalid-fixture")
        for path, content in files.items():
            safe_path(path)
            if not isinstance(content, str):
                raise EvaluationError("invalid-fixture")
    if set(case["fixture"]) & {".mstack-evaluation.json", "result.json", "events.jsonl", "requests.jsonl", "catalog.json", "thread.json", "context.json", "agent-result.json"}:
        raise EvaluationError("reserved-fixture-path")
    if set(case["fixture"]) & set(profile["instructions"]):
        raise EvaluationError("fixture-instruction-collision")
    if not isinstance(profile["catalog"], list):
        raise EvaluationError("invalid-catalog")
    names = set()
    for skill in profile["catalog"]:
        if (not isinstance(skill, dict) or set(skill) != {"name", "description", "path", "sha256", "invocation"} or
                skill["name"] in names or skill["invocation"] not in ("automatic", "explicit-only") or
                not isinstance(skill["description"], str) or not skill["description"]):
            raise EvaluationError("invalid-catalog")
        names.add(skill["name"])
        path = safe_path(skill["path"])
        if path not in profile["source_files"] or digest(profile["source_files"][path].encode()) != skill["sha256"]:
            raise EvaluationError("catalog-source-mismatch")
    if not isinstance(case.get("explicit_skills", []), list) or any(not isinstance(name, str) or name not in names for name in case.get("explicit_skills", [])):
        raise EvaluationError("unavailable-explicit-skill")
    setup = case.get("setup_commands", [])
    if not isinstance(setup, list) or len(setup) > 16 or any(not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg or '\x00' in arg for arg in argv) for argv in setup):
        raise EvaluationError("invalid-fixture-setup")
    if not isinstance(case["checks"], list) or not case["checks"]:
        raise EvaluationError("missing-case-checks")
    for check in case["checks"]:
        shapes = {"command": {"id", "kind", "argv", "cwd"}, "json-equals": {"id", "kind", "path", "expected"}, "same-as-fixture": {"id", "kind", "path", "fixture_path"}}
        if not isinstance(check, dict) or check.get("kind") not in ("command", "same-as-fixture", "json-equals", "exists", "absent", "unchanged") or set(check) != shapes.get(check["kind"], {"id", "kind", "path"}):
            raise EvaluationError("invalid-case-check")
        identifier(check["id"])
        if check["kind"] == "command":
            if not isinstance(check["argv"], list) or not check["argv"] or any(not isinstance(v, str) or not v or '\x00' in v for v in check["argv"]):
                raise EvaluationError("invalid-check-command")
            if check["cwd"] != '.':
                safe_path(check["cwd"])
        else:
            safe_path(check["path"])
            if check["kind"] == "same-as-fixture" and check["fixture_path"] not in case["fixture"]:
                raise EvaluationError("unknown-fixture-source")
    if len({check["id"] for check in case["checks"]}) != len(case["checks"]):
        raise EvaluationError("duplicate-case-check")
    if "rubric" in case:
        rubric = case["rubric"]
        if not isinstance(rubric, dict) or set(rubric) != {"skills", "criteria", "invariants", "expected_stop"} or rubric["expected_stop"] not in ("completed", "awaiting-user-input"):
            raise EvaluationError("invalid-semantic-rubric")
        for key in ("criteria", "invariants"):
            if not isinstance(rubric[key], dict) or not rubric[key] or any(not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k, v in rubric[key].items()):
                raise EvaluationError("invalid-semantic-rubric")
        if not isinstance(rubric["skills"], list):
            raise EvaluationError("invalid-semantic-rubric")
        for skill in rubric["skills"]:
            if (not isinstance(skill, dict) or set(skill) != {"name", "trigger_compatible", "reason", "selection", "criteria"} or skill["name"] not in names or
                    (skill["trigger_compatible"] is not None and type(skill["trigger_compatible"]) is not bool) or skill["selection"] not in ("required", "forbidden", "optional") or
                    not isinstance(skill["reason"], str) or not skill["reason"].strip() or not isinstance(skill["criteria"], list) or set(skill["criteria"]) - rubric["criteria"].keys()):
                raise EvaluationError("invalid-skill-rubric")


class Runner:
    def __init__(self, root):
        self.root = Path(root).absolute()

    @contextmanager
    def _lease(self, attempt_id):
        identifier(attempt_id)
        directory = private_directory(self.root / "leases")
        fd = os.open(directory / (attempt_id + ".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise EvaluationError("unsafe-attempt-lease")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise EvaluationError("attempt-active") from None
            yield
        finally:
            os.close(fd)

    def prepare(self, case, profile):
        validate_case(case, profile)
        protocol = {"schema_version": 1, "case": case, "profile": profile, "source_hashes": {path: digest(body.encode()) for path, body in profile["source_files"].items()}, "execution_sources": execution_sources(), "grading": "Frozen mechanical checks plus separately evidenced semantic rubric; never infer behavior from instruction wording."}
        sha = digest(encoded(protocol))
        root = private_directory(self.root)
        destination = root / "prepared" / sha
        if destination.exists():
            self.load(sha)
        else:
            destination.mkdir(mode=0o700, parents=True)
            for relative in protocol["execution_sources"]:
                output = destination / "execution" / relative
                output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with output.open("xb") as stream:
                    output.chmod(0o600); stream.write((HERE.parent / relative).read_bytes())
            _write_json(destination / "protocol.json", protocol)
        return {"stage": "prepared", "protocol_sha256": sha, "path": str(destination), "case_id": case["id"], "model_calls": 0}

    def load(self, sha, *, check_execution=True):
        if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
            raise EvaluationError("invalid-protocol")
        try:
            value = json.loads((self.root / "prepared" / sha / "protocol.json").read_text())
        except (ValueError, OSError):
            raise EvaluationError("prepared-protocol-unavailable") from None
        if digest(encoded(value)) != sha:
            raise EvaluationError("frozen-input-changed")
        if check_execution and value.get("execution_sources") != execution_sources():
            raise EvaluationError("execution-source-changed")
        if not check_execution:
            for relative, expected in value["execution_sources"].items():
                path = self.root / "prepared" / sha / "execution" / safe_path(relative)
                if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected:
                    raise EvaluationError("frozen-execution-unavailable")
        validate_case(value["case"], value["profile"])
        return value

    def _ledger(self):
        root = private_directory(self.root)
        path = root / "execution.sqlite3"
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600); os.close(fd)
        except FileExistsError:
            if path.is_symlink() or path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
                raise EvaluationError("unsafe-execution-ledger")
        db = sqlite3.connect(path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        app = db.execute("PRAGMA application_id").fetchone()[0]
        if app not in (0, 0x4D534556) or (app == 0 and db.execute("SELECT 1 FROM sqlite_master WHERE type='table'").fetchone()):
            db.rollback(); db.close()
            raise EvaluationError("unowned-execution-ledger")
        db.execute("CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY,sha256 TEXT NOT NULL,attempts INTEGER NOT NULL,turns INTEGER NOT NULL,seconds REAL NOT NULL) STRICT")
        db.execute("CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,protocol_sha256 TEXT NOT NULL,grant_id TEXT NOT NULL,status TEXT NOT NULL,result TEXT) STRICT")
        db.execute("PRAGMA application_id=1297302870")
        db.commit()
        return db

    def _reserve(self, sha, attempt_id, grant, profile):
        required = {"schema_version", "id", "protocols", "kind", "source", "answer", "max_attempts", "max_turns", "max_seconds"}
        if profile["kind"] == "agent":
            required.add("execution_root")
        if (not isinstance(grant, dict) or set(grant) != required or
                grant["schema_version"] != 1 or grant["kind"] != ("user" if profile["kind"] == "agent" else "fixture") or
                any(not isinstance(grant[key], str) or not grant[key].strip() for key in ("id", "source", "answer")) or
                not isinstance(grant["protocols"], list) or sha not in grant["protocols"]):
            raise EvaluationError("missing-authorization")
        if profile["kind"] == "agent" and grant["execution_root"] != str(self.root.resolve()):
            raise EvaluationError("authorization-outside-execution-root")
        for key in ("max_attempts", "max_turns", "max_seconds"):
            if type(grant[key]) is not int or grant[key] < 1:
                raise EvaluationError("invalid-authorized-budget")
        body_sha = digest(encoded(grant))
        db = self._ledger()
        try:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM grants WHERE id=?", (grant["id"],)).fetchone()
            if prior and prior["sha256"] != body_sha:
                raise EvaluationError("authorization-changed")
            attempts, turns, seconds = (prior["attempts"], prior["turns"], prior["seconds"]) if prior else (0, 0, 0)
            if attempts + 1 > grant["max_attempts"] or turns + profile["max_turns"] > grant["max_turns"] or seconds + profile["budget_seconds"] > grant["max_seconds"]:
                raise EvaluationError("budget-exhausted")
            if db.execute("SELECT 1 FROM attempts WHERE id=?", (attempt_id,)).fetchone():
                raise EvaluationError("attempt-already-reserved")
            db.execute("INSERT OR REPLACE INTO grants VALUES(?,?,?,?,?)", (grant["id"], body_sha, attempts + 1, turns + profile["max_turns"], seconds + profile["budget_seconds"]))
            db.execute("INSERT INTO attempts VALUES(?,?,?,?,NULL)", (attempt_id, sha, grant["id"], "reserved"))
            db.commit()
        except BaseException:
            db.rollback(); raise
        finally:
            db.close()

    @staticmethod
    def _populate(workspace, protocol):
        files = {**protocol["case"]["fixture"], **{k: v for k, v in protocol["profile"]["instructions"].items() if not k.startswith("global/")}}
        for path, content in protocol["profile"]["source_files"].items():
            if path.startswith("skills/"):
                files[".agents/skills/" + path.removeprefix("skills/")] = content
        for relative, content in files.items():
            path = workspace / safe_path(relative)
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with path.open("x") as stream:
                path.chmod(0o600); stream.write(content)

    @staticmethod
    def _grade(workspace, protocol, transport):
        checks = []
        for check in protocol["case"]["checks"]:
            if check["kind"] == "command":
                try:
                    result = transport.check(workspace, protocol, check)
                    checks.append({"id": check["id"], **result})
                except Exception:
                    checks.append({"id": check["id"], "passed": None, "infrastructure_state": "check-infrastructure-error"})
                continue
            path = workspace / check["path"]
            passed = False
            try:
                if path.is_symlink() or not path.resolve().is_relative_to(workspace.resolve()):
                    raise OSError()
                if check["kind"] == "json-equals":
                    passed = json.loads(path.read_text()) == check["expected"]
                elif check["kind"] == "exists":
                    passed = path.is_file()
                elif check["kind"] == "absent":
                    passed = not path.exists()
                elif check["kind"] == "unchanged":
                    original = protocol["case"]["fixture"].get(check["path"])
                    passed = original is not None and path.read_bytes() == original.encode()
                elif check["kind"] == "same-as-fixture":
                    passed = path.read_bytes() == protocol["case"]["fixture"][check["fixture_path"]].encode()
            except (OSError, ValueError):
                pass
            checks.append({"id": check["id"], "passed": passed})
        return checks

    def execute(self, sha, attempt_id, grant, transport):
        with self._lease(attempt_id):
            return self._execute(sha, attempt_id, grant, transport)

    def _execute(self, sha, attempt_id, grant, transport):
        identifier(attempt_id)
        protocol = self.load(sha)
        self._reserve(sha, attempt_id, grant, protocol["profile"])
        attempt = self.root / "attempts" / attempt_id
        workspace = create_workspace(attempt / "workspace", attempt_id)
        self._populate(workspace, protocol)
        _write_json(attempt / "authorization.json", grant)
        start = time.monotonic()
        result = {"schema_version": 1, "attempt_id": attempt_id, "protocol_sha256": sha, "case_id": protocol["case"]["id"], "profile_id": protocol["profile"]["id"], "stage": "inconclusive", "execution_status": "infrastructure-error", "behavioral_status": "ungraded", "grading_scope": "mechanical-fixture" if protocol["profile"]["kind"] == "fixture" else "mechanical-checks-only; semantic rubric pending", "context": {"state": "unverified"}, "model_calls": None, "infrastructure_states": [], "created_at": datetime.now(timezone.utc).isoformat()}
        consumers_stopped = True
        try:
            execution = transport.run(workspace, protocol, protocol["profile"]["budget_seconds"])
            result.update(execution)
            if result["execution_status"] not in ("completed", "timeout", "interrupted", "infrastructure-error"):
                raise EvaluationError("invalid-transport-result")
        except ExecutionFailure as error:
            result.update(error.partial)
            consumers_stopped = error.consumers_stopped
            result["infrastructure_states"].append(str(error))
        except (TimeoutError, subprocess.TimeoutExpired):
            result["execution_status"] = "timeout"
        except KeyboardInterrupt:
            result["execution_status"] = "interrupted"
        except Exception:
            result["execution_status"] = "infrastructure-error"
            result["infrastructure_states"].append("transport-failed")
        result["seconds"] = round(time.monotonic() - start, 3)
        if execution_sources() != protocol["execution_sources"]:
            result["infrastructure_states"].append("execution-source-changed")
        result["checks"] = self._grade(workspace, protocol, transport) if consumers_stopped else []
        result["infrastructure_states"] += [value["infrastructure_state"] for value in result["checks"] if value.get("infrastructure_state")]
        expected_context = "verified-fixture" if protocol["profile"]["kind"] == "fixture" else "verified"
        if result["context"]["state"] != expected_context:
            result["infrastructure_states"].append("loaded-context-unverified")
        if result["execution_status"] == "completed" and not result["infrastructure_states"]:
            passed = all(v["passed"] for v in result["checks"])
            result["mechanical_status"] = "passed" if passed else "failed"
            result["behavioral_status"] = ("passed" if passed else "failed") if protocol["profile"]["kind"] == "fixture" else "ungraded"
        collection_path = attempt / "collected"
        if consumers_stopped:
            _write_json(workspace / "result.json", result)
            collection = collect_workspace(workspace, collection_path, attempt_id, result["execution_status"])
        else:
            collection = {"collection_status": "deferred", "artifacts": [], "infrastructure_states": ["consumers-not-stopped"]}
        result["collection"] = collection; result["collection_path"] = str(collection_path)
        result["infrastructure_states"] += collection["infrastructure_states"]
        if result["execution_status"] == "completed" and not result["infrastructure_states"]:
            result["stage"] = "executed"
        else:
            result["behavioral_status"] = "inconclusive"
        _write_json(attempt / "receipt.json", result)
        db = self._ledger()
        try:
            db.execute("UPDATE attempts SET status=?,result=? WHERE id=?", (result["stage"], encoded(result).decode(), attempt_id))
        finally:
            db.close()
        return result

    def report(self):
        if not (self.root / "execution.sqlite3").exists():
            return {"attempts": [], "coverage": "prepared-only"}
        db = self._ledger()
        try:
            return {"attempts": [json.loads(v["result"]) if v["result"] else {"attempt_id": v["id"], "protocol_sha256": v["protocol_sha256"], "stage": "inconclusive", "infrastructure_states": ["reserved-attempt-without-receipt"]} for v in db.execute("SELECT * FROM attempts ORDER BY id")], "budgets": [dict(row) for row in db.execute("SELECT id,attempts,turns,seconds FROM grants ORDER BY id")]}
        finally:
            db.close()

    def recover(self, attempt_id, recovery_id, termination_evidence):
        with self._lease(attempt_id):
            return self._recover(attempt_id, recovery_id, termination_evidence)

    def _recover(self, attempt_id, recovery_id, termination_evidence):
        identifier(attempt_id); identifier(recovery_id)
        if not isinstance(termination_evidence, str) or not termination_evidence.strip():
            raise EvaluationError("missing-termination-evidence")
        attempt = self.root / "attempts" / attempt_id
        if not (attempt / "workspace").is_dir():
            raise EvaluationError("attempt-workspace-unavailable")
        destination = self.root / "recoveries" / recovery_id
        result = collect_workspace(attempt / "workspace", destination, attempt_id, "interrupted", recovery_of=attempt_id)
        receipt = {"stage": "recovered", "recovery_id": recovery_id, "recovery_of": attempt_id, "termination_evidence": termination_evidence, "recovery_execution_sources": execution_sources(), "collection": result, "behavioral_status": "ungraded", "model_calls": 0}
        _write_json(destination / "recovery.json", receipt)
        return receipt
