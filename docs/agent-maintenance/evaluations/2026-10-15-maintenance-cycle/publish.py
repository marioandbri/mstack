"""Publish sanitized AM-030 evidence without executing agents or changing receipts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY / "skills/reflect/runtime"))
from evaluation import Runner
from selection import Trace


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def database(path):
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def reference(value):
    return {key: value[key] for key in ("path", "line", "sha256")}


def publish(campaign):
    manifest = read(campaign / "manifest.json")
    grant = read(campaign / "authorization.json")
    runner = Runner(campaign / "runner")
    with database(runner.root / "execution.sqlite3") as ledger:
        budget = dict(ledger.execute("SELECT * FROM grants WHERE id=?", (grant["id"],)).fetchone())
        assert (budget["attempts"], budget["turns"], budget["seconds"]) == (14, 14, 2520)
        entries = manifest["entries"]
        assert len(entries) == len({entry["protocol_sha256"] for entry in entries}) == 14
        assert set(grant["protocols"]) == {entry["protocol_sha256"] for entry in entries}
        assert len(list(ledger.execute("SELECT id FROM attempts"))) == 14
        cases = []
        for position, entry in enumerate(entries, 1):
            attempt_id = f"cycle-{position:02d}-" + entry["case_id"]
            attempt = runner.root / "attempts" / attempt_id
            receipt = read(attempt / "receipt.json")
            row = ledger.execute("SELECT result FROM attempts WHERE id=?", (attempt_id,)).fetchone()
            assert json.loads(row["result"]) == receipt
            protocol = runner.load(entry["protocol_sha256"], check_execution=False)
            assessment_id = f"cycle-{position:02d}-assessment"
            row = ledger.execute("SELECT * FROM assessments WHERE id=?", (assessment_id,)).fetchone()
            assert hashlib.sha256(row["payload"].encode()).hexdigest() == row["sha256"]
            assessment = json.loads(row["payload"])
            assert assessment["protocol_sha256"] == receipt["protocol_sha256"] == entry["protocol_sha256"]
            root = attempt / "collected/workspace"
            trace = Trace(root, protocol["profile"], complete=not receipt["infrastructure_states"])
            starts = sum(value.get("method") == "turn/start" for _, value in trace.requests)
            terminal = read(root / "agent-result.json")
            assert starts == 1 and terminal["status"] == "completed"
            # Validate every retained judgment reference before publishing its identity.
            for finding in assessment["criteria"] + assessment["invariants"] + assessment["unnecessary_actions"]:
                for ref in finding["evidence"]:
                    assert trace.reference(ref["path"], ref["line"], ref["excerpt"]) == ref
            usage = trace.usage()
            if usage:
                usage = {**usage, "source_ref": reference(usage["source_ref"])}
            cases.append({
                "position": position, "attempt_id": attempt_id, "case_id": entry["case_id"],
                "role": entry["role"], "case_kind": protocol["case"]["kind"],
                "incident_id": protocol["case"]["incident_id"], "source_commit": entry["source_commit"],
                "protocol_sha256": entry["protocol_sha256"], "receipt_sha256": sha(attempt / "receipt.json"),
                "assessment_id": assessment_id, "assessment_sha256": row["sha256"],
                "assessor": assessment["assessor"], "task_result": assessment["task_result"],
                "execution_status": receipt["execution_status"], "stage": receipt["stage"],
                "receipt_context": receipt["context"]["state"],
                "retained_context": read(root / "context.json")["state"],
                "collection_status": receipt["collection"]["collection_status"],
                "infrastructure_states": dict(Counter(receipt["infrastructure_states"])),
                "mechanical_checks": [{k: check[k] for k in ("id", "passed")} for check in receipt["checks"]],
                "criteria": [{"id": value["id"], "result": value["result"], "evidence": [reference(ref) for ref in value["evidence"]]} for value in assessment["criteria"] + assessment["invariants"]],
                "skills": [{key: value[key] for key in ("name", "trigger_compatible", "selection", "selected", "selected_automatically", "read", "exposed", "attribution")} for value in assessment["skills"]],
                "seconds": receipt["seconds"], "agent_turns_requested": starts,
                "terminal_status": terminal["status"], "human_interventions": assessment["human_interventions"],
                "unnecessary_actions": [{"action": value["action"], "reason": value["reason"], "evidence": [reference(ref) for ref in value["evidence"]]} for value in assessment["unnecessary_actions"]],
                "tokens": usage,
                "artifact_hashes": {name: sha(root / name) for name in ("events.jsonl", "requests.jsonl", "context.json", "agent-result.json")},
            })
    with database(campaign / "records.sqlite3") as records:
        row = records.execute("SELECT payload,sha256 FROM review_evidence WHERE id='capture-comparison-result'").fetchone()
        comparison = json.loads(row["payload"])
        comparison_result = {key: comparison[key] for key in ("stage", "baseline_reproduction", "promotion", "recommendation")}
        comparison_result.update({"sha256": row["sha256"], "alternatives": [{key: alternative[key] for key in ("id", "kind", "evidence")} for alternative in comparison["alternatives"]]})
        delivery = []
        for row in records.execute("SELECT revision,payload,sha256 FROM delivery_events WHERE plan_id='label-delivery' ORDER BY revision"):
            payload = json.loads(row["payload"])
            if payload["stage"] in ("post-promotion", "post-rollback"):
                delivery.append({"revision": row["revision"], "sha256": row["sha256"], **payload})
    recovery_path = runner.root / "recoveries/cycle-12-filtered-runtime/recovery.json"
    recovery = read(recovery_path)
    assert recovery["collection"]["collection_status"] == "complete" and not recovery["collection"]["infrastructure_states"]
    fault_path = campaign.parent / "transport-finalization/results.json"
    fault = read(fault_path)
    image_path = campaign.parent / "shell-path/full-recipe-verification.json"
    image = read(image_path)
    assert image["exit_code"] == image["model_calls"] == 0
    checks_path = campaign.parent / "final-checks.log"
    checks = checks_path.read_text()
    assert all(value in checks for value in ("PASS 30 skills, 70 Markdown files", "43 pass", "1 skip", "0 fail", "376 expect() calls", "owned content and configuration verified"))
    outcome_counts = dict(Counter(case["task_result"] for case in cases))
    assert outcome_counts == {"passed": 11, "inconclusive": 3}
    return {
        "schema_version": 1, "campaign": "AM-030/campaign-02", "date": "2026-10-15",
        "implementation_commit": manifest["implementation_commit"],
        "source_hashes": {"manifest": sha(campaign / "manifest.json"), "authorization": sha(campaign / "authorization.json"), "publisher": sha(Path(__file__))},
        "environment": {key: manifest["environment"][key] for key in ("image_digest", "codex", "python", "bun", "uv", "git", "node", "platform", "architecture", "sqlite")},
        "model": manifest["model"], "reasoning": manifest["reasoning"],
        "budget": {"attempts_reserved": budget["attempts"], "turns_reserved": budget["turns"], "seconds_reserved": budget["seconds"], "automatic_retries": 0},
        "summary": {"attempts": len(cases), "task_results": outcome_counts,
                    "agent_turns_requested": sum(case["agent_turns_requested"] for case in cases),
                    "agent_terminal_completed": sum(case["terminal_status"] == "completed" for case in cases),
                    "all_mechanical_checks_passed": sum(all(check["passed"] is True for check in case["mechanical_checks"]) for case in cases),
                    "all_observed_criteria_passed": sum(all(value["result"] == "passed" for value in case["criteria"]) for case in cases),
                    "human_interventions": sum(case["human_interventions"] for case in cases),
                    "unnecessary_actions": sum(len(case["unnecessary_actions"]) for case in cases),
                    "attempt_wall_seconds": round(sum(case["seconds"] for case in cases), 3),
                    "usage_available": sum(case["tokens"] is not None for case in cases), "provider_calls": None},
        "cases": cases, "comparison": comparison_result, "isolated_delivery": delivery,
        "native_recovery": {"sha256": sha(recovery_path), "recovery_of": recovery["recovery_of"], "collection_status": recovery["collection"]["collection_status"], "original_receipt_preserved": read(campaign / "recovery-verification.json")["original_receipt_unchanged"], "execution_sources": recovery["recovery_execution_sources"], "model_calls": 0},
        "native_finalization": {"sha256": sha(fault_path), **fault},
        "native_environment_fix": {"sha256": sha(image_path), **image},
        "required_checks": {"log_sha256": sha(checks_path), "bun_version": "1.3.14", "commands": ["bun run check", "bun test", "fish install/verify.fish", "git diff --check"], "exit_code": 0, "bun_pass": 43, "bun_optional_skip": 1, "bun_fail": 0, "bun_assertions": 376},
        "limits": ["One pass in one frozen environment, reviewed by the implementing agent; no independent judge or statistical reliability claim.",
                   "Original infrastructure outcomes remain inconclusive; native recovery and fault injection are not new model trials.",
                   "The precise original cause of the two transport finalization failures was not reproduced.",
                   "Token counts are reported cumulative harness usage; cache and reasoning counts are subsets. Internal provider calls and monetary cost are unknown.",
                   "The active HOME and installed global/skills were not changed. No Laya inference or classification was used."],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.campaign.resolve())
    destination = Path(__file__).with_name("results.json")
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["summary"]))
