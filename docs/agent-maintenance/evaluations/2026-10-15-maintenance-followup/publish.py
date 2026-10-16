"""Verify and publish AM-031 records without modifying AM-030 or running agents."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY / "skills/reflect/runtime"))
from evaluation import Runner
from selection import Trace


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(campaign):
    manifest = read(campaign / "manifest.json")
    authorization = read(campaign / "authorization.json")
    runner = Runner(campaign / "runner")
    previous = campaign.parent / "campaign-02"
    old_results = read(Path(__file__).parent / "../2026-10-15-maintenance-cycle/results.json")
    originals = read(campaign / "previous-receipts.json")
    assert len(originals) == 14 and all(sha(previous / name) == expected for name, expected in originals.items())
    assert all(sha(previous / "runner/attempts" / case["attempt_id"] / "receipt.json") == case["receipt_sha256"] for case in old_results["cases"])
    assert read(campaign / "previous-receipts-verification.json")["all_14_preserved"]
    entries = manifest["entries"]
    assert len(entries) == len({entry["protocol_sha256"] for entry in entries}) == 3
    assert set(authorization["protocols"]) == {entry["protocol_sha256"] for entry in entries}
    cases = []
    with closing(sqlite3.connect((runner.root / "execution.sqlite3").as_uri() + "?mode=ro", uri=True)) as ledger:
        ledger.row_factory = sqlite3.Row
        budget = dict(ledger.execute("SELECT * FROM grants WHERE id=?", (authorization["id"],)).fetchone())
        assert (budget["attempts"], budget["turns"], budget["seconds"]) == (3, 3, 540)
        assert ledger.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 3
        for number, entry in enumerate(entries, 1):
            attempt_id = f"followup-{number:02d}-" + entry["case_id"]
            attempt = runner.root / "attempts" / attempt_id
            receipt = read(attempt / "receipt.json")
            assert receipt == json.loads(ledger.execute("SELECT result FROM attempts WHERE id=?", (attempt_id,)).fetchone()[0])
            protocol = runner.load(entry["protocol_sha256"], check_execution=False)
            row = ledger.execute("SELECT payload,sha256 FROM assessments WHERE id=? AND attempt_id=?", (f"followup-{number:02d}-assessment", attempt_id)).fetchone()
            assert row and hashlib.sha256(row["payload"].encode()).hexdigest() == row["sha256"]
            assessment = json.loads(row["payload"])
            assert assessment["protocol_sha256"] == receipt["protocol_sha256"] == entry["protocol_sha256"]
            root = attempt / "collected/workspace"
            for artifact in receipt["collection"]["artifacts"]:
                if artifact["status"] == "collected":
                    assert sha(root / artifact["path"]) == artifact["sha256"]
            trace = Trace(root, protocol["profile"], complete=not receipt["infrastructure_states"])
            for finding in assessment["criteria"] + assessment["invariants"] + assessment["unnecessary_actions"]:
                for ref in finding["evidence"]:
                    assert trace.reference(ref["path"], ref["line"], ref["excerpt"]) == ref
            cases.append({
                "attempt_id": attempt_id, "case_id": entry["case_id"], "previous_attempt_id": entry["previous_attempt_id"],
                "case_kind": protocol["case"]["kind"], "incident_id": protocol["case"]["incident_id"],
                "protocol_sha256": entry["protocol_sha256"], "previous_protocol_sha256": entry["previous_protocol_sha256"],
                "receipt_sha256": sha(attempt / "receipt.json"), "assessment_sha256": row["sha256"],
                "task_result": assessment["task_result"], "execution_status": receipt["execution_status"],
                "stage": receipt["stage"], "context": receipt["context"]["state"],
                "collection_status": receipt["collection"]["collection_status"],
                "infrastructure_states": dict(Counter(receipt["infrastructure_states"])),
                "checks": [{"id": value["id"], "passed": value["passed"]} for value in receipt["checks"]],
                "criteria": [{"id": value["id"], "result": value["result"], "evidence": [{key: ref[key] for key in ("path", "line", "sha256")} for ref in value["evidence"]]} for value in assessment["criteria"] + assessment["invariants"]],
                "skills": [{key: value[key] for key in ("name", "trigger_compatible", "selection", "selected", "selected_automatically", "read", "exposed", "attribution")} for value in assessment["skills"]],
                "seconds": receipt["seconds"], "tokens": trace.usage(),
                "agent_turns_requested": sum(value.get("method") == "turn/start" for _, value in trace.requests),
                "terminal_status": read(root / "agent-result.json")["status"],
                "human_interventions": assessment["human_interventions"],
                "unnecessary_actions": [{"action": value["action"], "reason": value["reason"], "evidence": [{key: ref[key] for key in ("path", "line", "sha256")} for ref in value["evidence"]]} for value in assessment["unnecessary_actions"]],
                "artifact_hashes": {name: sha(root / name) for name in ("events.jsonl", "requests.jsonl", "context.json", "agent-result.json")},
            })
    checks_path = campaign.parent / "followup-checks.log"
    checks = checks_path.read_text()
    assert all(value in checks for value in ("PASS 30 skills, 70 Markdown files", "43 pass", "1 skip", "0 fail", "376 expect() calls", "owned content and configuration verified"))
    return {
        "schema_version": 1, "campaign": "AM-031/campaign-03", "date": "2026-10-15",
        "source_commit": manifest["implementation_commit"], "model": manifest["model"], "reasoning": manifest["reasoning"],
        "environment": {key: manifest["environment"][key] for key in ("image_digest", "codex", "python", "bun", "uv", "git", "node", "sqlite", "platform")},
        "budget": manifest["budget"], "authorization_answer": authorization["answer"],
        "source_hashes": {"manifest": sha(campaign / "manifest.json"), "authorization": sha(campaign / "authorization.json"), "publisher": sha(Path(__file__)), "native_readback": sha(campaign / "native-readback.json"), "previous_results": sha(Path(__file__).parent / "../2026-10-15-maintenance-cycle/results.json")},
        "summary": {"attempts": len(cases), "task_results": dict(Counter(case["task_result"] for case in cases)),
                    "agent_turns_requested": sum(case["agent_turns_requested"] for case in cases),
                    "terminal_completed": sum(case["terminal_status"] == "completed" for case in cases),
                    "all_mechanical_checks_passed": sum(all(value["passed"] is True for value in case["checks"]) for case in cases),
                    "human_interventions": sum(case["human_interventions"] for case in cases),
                    "unnecessary_actions": sum(len(case["unnecessary_actions"]) for case in cases),
                    "attempt_wall_seconds": round(sum(case["seconds"] for case in cases), 3), "provider_calls": None},
        "cases": cases, "previous_14_receipts_preserved": True,
        "native_readback": read(campaign / "native-readback.json"),
        "required_checks": {"log_sha256": sha(checks_path), "commands": ["bun run check", "bun test", "fish install/verify.fish", "git diff --check"], "exit_code": 0, "bun_pass": 43, "bun_optional_skip": 1, "bun_fail": 0, "bun_assertions": 376},
        "limits": ["Three targeted attempts after AM-030, not a single rerun of all 14 cases or a new A/B comparison.", "Manual assessment by the implementing agent, no independent judge or statistical reliability claim.", "Original infrastructure outcomes remain unchanged. This campaign does not establish the precise cause of the old intermittent close failures.", "Cumulative token usage includes cached input and reasoning output as subsets. Provider call counts and monetary cost are unknown.", "No active installation, PR publication or remote merge was performed."],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.campaign.resolve())
    Path(__file__).with_name("results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["summary"]))
