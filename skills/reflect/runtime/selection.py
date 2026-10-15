"""Selection evidence and rubric judgments, separate from textual trigger analysis."""
import json
from pathlib import Path

from evaluation import EvaluationError, identifier
from records import digest, encoded


class Trace:
    def __init__(self, root, profile, *, complete):
        self.root = Path(root).resolve()
        self.profile = profile
        self.complete = complete
        self.events = self._lines("events.jsonl")
        self.requests = self._lines("requests.jsonl")
        try:
            self.catalog = json.loads((self.root / "catalog.json").read_text())
        except (OSError, ValueError):
            self.catalog = None; self.complete = False

    def _lines(self, name):
        try:
            lines = (self.root / name).read_text().splitlines()
            values = []
            for number, line in enumerate(lines, 1):
                try:
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError()
                    values.append((number, value))
                except ValueError:
                    self.complete = False
            return values
        except (OSError, ValueError):
            self.complete = False
            return []

    def reference(self, path, line, excerpt):
        file = self.root / path
        if type(line) is not int or line < 1 or not isinstance(excerpt, str) or not excerpt.strip() or len(excerpt) > 4000 or file.is_symlink() or not file.resolve().is_relative_to(self.root):
            raise EvaluationError("invalid-assessment-reference")
        try:
            raw = file.read_bytes()
            if excerpt not in raw.decode().splitlines()[line - 1]:
                raise ValueError()
        except (OSError, ValueError, IndexError):
            raise EvaluationError("invalid-assessment-reference") from None
        return {"path": path, "line": line, "excerpt": excerpt, "sha256": digest(raw)}

    def skill(self, skill):
        name = skill["name"]
        actual = [value for entry in (self.catalog or {}).get("data", []) for value in entry.get("skills", []) if value.get("name") == name]
        expected_path = "/workspace/.agents/skills/" + name + "/SKILL.md"
        exposed = any(value.get("enabled", True) and value.get("path") == expected_path for value in actual) if self.catalog is not None else None
        evidence, read = [], "not-observed" if self.complete else "unknown"
        body = self.profile["source_files"][skill["path"]].strip()
        for number, event in self.events:
            item = event.get("params", {}).get("item", {})
            if event.get("method") != "item/completed" or item.get("type") != "commandExecution" or item.get("exitCode") != 0:
                continue
            command, output = item.get("command", ""), item.get("aggregatedOutput", "") or ""
            if not isinstance(command, str) or not isinstance(output, str) or f"skills/{name}/SKILL.md" not in command:
                continue
            portion = "full" if body in output else "partial" if any(line.strip() and len(line.strip()) > 20 and line.strip() in output for line in body.splitlines()) else None
            if portion:
                if read != "full":
                    read = portion
                evidence.append({"path": "events.jsonl", "line": number, "sha256": digest((self.root / "events.jsonl").read_bytes()), "item_id": item.get("id"), "read_portion": portion})
        explicit = []
        for number, request in self.requests:
            if request.get("method") == "turn/start" and any(value.get("type") == "skill" and value.get("name") == name and value.get("path") == expected_path for value in request.get("params", {}).get("input", [])):
                explicit.append({"path": "requests.jsonl", "line": number, "sha256": digest((self.root / "requests.jsonl").read_bytes()), "source_sha256": skill["sha256"]})
        selected = True if evidence or explicit else False if self.complete else None
        return {"name": name, "available_in_frozen_catalog": True, "exposed": exposed, "selected": selected,
                "selected_automatically": None if explicit else selected, "selection_method": "explicit-injection" if explicit else "read-proxy" if evidence else "not-observed" if self.complete else "unknown",
                "read": read, "loaded": True if explicit or evidence else False if self.complete else None,
                "evidence": evidence + explicit, "limits": ["A read is observable use, not proof of compliance or of the harness's internal routing rationale."]}


def assess(protocol, receipt, root, judgment):
    rubric = protocol["case"].get("rubric")
    if not rubric:
        raise EvaluationError("case-has-no-semantic-rubric")
    if (not isinstance(judgment, dict) or set(judgment) != {"schema_version", "assessor", "criteria", "invariants", "human_interventions", "unnecessary_actions"} or judgment["schema_version"] != 1 or
            not isinstance(judgment["assessor"], dict) or set(judgment["assessor"]) != {"name", "version"} or any(not isinstance(v, str) or not v.strip() for v in judgment["assessor"].values())):
        raise EvaluationError("invalid-assessment")
    complete = receipt["execution_status"] == "completed" and not receipt["infrastructure_states"]
    trace = Trace(root, protocol["profile"], complete=complete)

    def findings(items, expected):
        if not isinstance(items, list) or {item.get("id") for item in items if isinstance(item, dict)} != set(expected) or len(items) != len(expected):
            raise EvaluationError("assessment-rubric-mismatch")
        result = []
        for item in items:
            if (not isinstance(item, dict) or set(item) != {"id", "result", "reason", "evidence"} or item["result"] not in ("passed", "failed", "inconclusive") or
                    not isinstance(item["reason"], str) or not item["reason"].strip() or not isinstance(item["evidence"], list) or (item["result"] != "inconclusive" and not item["evidence"])):
                raise EvaluationError("invalid-assessment-finding")
            refs = []
            for ref in item["evidence"]:
                if not isinstance(ref, dict) or set(ref) != {"path", "line", "excerpt", "sha256"}:
                    raise EvaluationError("invalid-assessment-reference")
                checked = trace.reference(ref["path"], ref["line"], ref["excerpt"])
                if checked != ref:
                    raise EvaluationError("assessment-source-changed")
                refs.append(checked)
            result.append({**item, "evidence": refs})
        return result

    criteria = findings(judgment["criteria"], rubric["criteria"])
    invariants = findings(judgment["invariants"], rubric["invariants"])
    count = judgment["human_interventions"]
    if count is not None and (type(count) is not int or count < 0):
        raise EvaluationError("invalid-intervention-count")
    actions = judgment["unnecessary_actions"]
    if not isinstance(actions, list):
        raise EvaluationError("invalid-unnecessary-actions")
    for action in actions:
        if not isinstance(action, dict) or set(action) != {"action", "reason", "evidence"} or any(not isinstance(action[k], str) or not action[k].strip() for k in ("action", "reason")) or not isinstance(action["evidence"], list) or not action["evidence"]:
            raise EvaluationError("invalid-unnecessary-actions")
        for ref in action["evidence"]:
            if trace.reference(ref["path"], ref["line"], ref["excerpt"]) != ref:
                raise EvaluationError("assessment-source-changed")
    expected_stop = rubric.get("expected_stop", "completed")
    reached_boundary = receipt["execution_status"] == "completed" if expected_stop == "completed" else receipt["execution_status"] == "completed" or receipt.get("stop_reason") == expected_stop
    valid_context = receipt["context"]["state"] in ("verified", "verified-fixture")
    checks = {value["id"]: value for value in receipt["checks"]}
    preservation_failed = any(check["kind"] in ("unchanged", "same-as-fixture") and checks.get(check["id"], {}).get("passed") is False for check in protocol["case"].get("checks", []))
    invalidated = any(value["result"] == "failed" for value in invariants) or preservation_failed or receipt.get("global_instructions_preserved") is False
    inconclusive = not reached_boundary or not valid_context or receipt["infrastructure_states"] or any(value["result"] == "inconclusive" for value in criteria + invariants)
    task = "invalidated" if invalidated else "inconclusive" if inconclusive else "failed" if any(value["result"] == "failed" for value in criteria) or any(value["passed"] is False for value in receipt["checks"]) else "passed"
    skills = []
    catalog = {value["name"]: value for value in protocol["profile"]["catalog"]}
    for expected in rubric["skills"]:
        if expected["name"] not in catalog:
            skills.append({**expected, "available_in_frozen_catalog": False, "exposed": False, "selected": None, "read": "unknown", "attribution": "catalog-gap"})
            continue
        value = trace.skill(catalog[expected["name"]])
        compatible = expected["trigger_compatible"]
        attribution = "not-applicable" if compatible is False and value["selected"] is not True else "availability-gap" if value["exposed"] is not True else "trigger-ambiguous" if compatible is None else "overactivation" if compatible is False else "selection-not-observed" if expected["selection"] == "required" and value["selected"] is False else "observed-use" if value["selected"] else "undetermined"
        skills.append({**expected, **value, "attribution": attribution, "compliance": {v["id"]: v["result"] for v in criteria if v["id"] in expected["criteria"]}})
    environment = {key: protocol["profile"][key] for key in ("harness", "environment", "model", "reasoning")}
    return {"schema_version": 1, "attempt_id": receipt["attempt_id"], "protocol_sha256": receipt["protocol_sha256"], "case_id": protocol["case"]["id"], "case_kind": protocol["case"]["kind"], "incident_id": protocol["case"]["incident_id"], "environment_sha256": digest(encoded(environment)), "environment": environment, "task_result": task, "skills": skills, "criteria": criteria, "invariants": invariants, "human_interventions": count, "unnecessary_actions": actions, "metrics": {"seconds": receipt["seconds"], "tokens": receipt.get("tokens"), "agent_turns_started": receipt.get("agent_turns_started"), "provider_calls": receipt.get("model_calls")}, "assessor": judgment["assessor"], "limits": ["Complementary skills are not competitors merely because they were used together.", "Textual trigger hypotheses and behavioral evidence remain separate; no universal harness reliability claim."]}


def save_assessment(runner, attempt_id, assessment_id, judgment):
    identifier(attempt_id); identifier(assessment_id)
    db = runner._ledger()
    try:
        row = db.execute("SELECT result FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        if row is None or row["result"] is None:
            raise EvaluationError("attempt-receipt-unavailable")
        receipt = json.loads(row["result"])
        protocol = runner.load(receipt["protocol_sha256"], check_execution=False)
        root = Path(receipt["collection_path"]) / "workspace"
        for artifact in receipt["collection"]["artifacts"]:
            if artifact["status"] != "collected":
                continue
            path = root / artifact["path"]
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or digest(path.read_bytes()) != artifact["sha256"]:
                raise EvaluationError("collected-evidence-changed")
        value = assess(protocol, receipt, root, judgment)
        payload = encoded(value).decode()
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY,attempt_id TEXT NOT NULL,payload TEXT NOT NULL,sha256 TEXT NOT NULL) STRICT")
        old = db.execute("SELECT payload FROM assessments WHERE id=?", (assessment_id,)).fetchone()
        if old and old[0] != payload:
            raise EvaluationError("assessment-identity-conflict")
        db.execute("INSERT OR IGNORE INTO assessments VALUES(?,?,?,?)", (assessment_id, attempt_id, payload, digest(payload.encode())))
        db.commit()
        return {"status": "already-saved" if old else "saved", "id": assessment_id, "assessment": value, "sha256": digest(payload.encode())}
    except BaseException:
        db.rollback(); raise
    finally:
        db.close()


def assessment_report(runner):
    db = runner._ledger()
    try:
        values = [dict(row) for row in db.execute("SELECT * FROM assessments ORDER BY id")] if db.execute("SELECT 1 FROM sqlite_master WHERE name='assessments'").fetchone() else []
    finally:
        db.close()
    groups = {}
    for row in values:
        value = json.loads(row["payload"])
        groups.setdefault(value["environment_sha256"], []).append({"assessment_id": row["id"], "sha256": row["sha256"], **value})
    return {"groups": [{"environment_sha256": key, "assessments": values} for key, values in sorted(groups.items())], "attempts": runner.report()["attempts"], "limits": ["Multiple judgments of the same attempt are retained and are not independent trials.", "An unavailable skill or incomplete trace cannot establish trigger failure."]}
