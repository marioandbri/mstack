"""Public CLI integration across independent processes and a real temporary install."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from test_annotations import annotation
from test_evaluation import case, profile
from test_reviews import review, options
from test_summaries import summary
from selection import Trace


class CycleTests(unittest.TestCase):
    def setUp(self):
        self.tools = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(self.tools / "install"))
        import test_mstack as installer_tests
        sys.path.pop(0)
        self.fixture = installer_tests.InstallerTests(methodName="runTest")
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.root, self.repo, self.home = self.fixture.base, self.fixture.repo, self.fixture.home
        self.home.chmod(0o700)
        inventory = json.loads((self.repo / "skills.json").read_text()); inventory["schemaVersion"] = 1
        for entry in inventory["skills"]:
            entry.update({"owner": "original", "source": "self", "sourcePath": "skills/" + entry["name"], "importRef": "synthetic-fixture", "license": "MIT"})
        self.fixture.write("skills.json", json.dumps(inventory))
        self.fixture.write("evals/deepswe/auth_state.py", (self.tools / "evals/deepswe/auth_state.py").read_text())
        self.fixture.write("instructions/global/AGENTS.md", "Maintenance label: stable\n")
        self.fixture.write("prior.md", "For this isolated fixture, the maintenance label is stable.\n")
        self.fixture.write("decision.md", "For this isolated fixture, the maintenance label must be candidate. This replaces stable.\n")
        self.stable = self.fixture.commit(); self.fixture.apply()
        self.fixture.write("instructions/global/AGENTS.md", "Maintenance label: candidate\n")
        self.candidate = self.fixture.commit()
        self.database = self.root / "records.sqlite3"
        self.counter = 0

    def file(self, value):
        self.counter += 1
        path = self.root / f"input-{self.counter}.json"
        path.write_text(json.dumps(value)); path.chmod(0o600)
        return str(path)

    def execute(self, command):
        result = subprocess.run(command, cwd=self.tools, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def records(self, *args, database=None):
        return self.execute([sys.executable, str(self.tools / "skills/reflect/runtime/record_cli.py"), "--database", str(database or self.database), "--project", "cycle-fixture", *map(str, args)])

    def evaluation(self, *args):
        return self.execute([sys.executable, str(self.tools / "skills/reflect/runtime/evaluation_cli.py"), "--root", str(self.root / "runner"), *map(str, args)])

    def audit(self, command, request):
        return self.execute(["bun", str(self.tools / "scripts/maintenance.ts"), command, "--request", self.file(request)])

    def delivery(self, *args):
        return self.records("delivery", "--runner-root", self.root / "runner", "--installer-repository", self.tools, "--source-repository", self.repo,
                            "--home", self.home, "--control", self.root / "delivery", *args)

    def assess(self, receipt, passed):
        frozen = json.loads((self.root / "runner/prepared" / receipt["protocol_sha256"] / "protocol.json").read_text())
        trace = Trace(Path(receipt["collection_path"]) / "workspace", frozen["profile"], complete=True)
        answer = trace.reference("answer.json", 1, "candidate" if passed else "stable")
        evidence = trace.reference("evidence.txt", 1, "preserved evidence")
        judgment = {"schema_version": 1, "assessor": {"name": "mechanical-cycle-fixture", "version": "1"},
                    "criteria": [{"id": "label", "result": "passed" if passed else "failed", "reason": "The fixture read the installed instruction label.", "evidence": [answer]}],
                    "invariants": [{"id": "evidence", "result": "passed", "reason": "Original evidence is preserved.", "evidence": [evidence]}], "human_interventions": 0, "unnecessary_actions": []}
        identity = receipt["attempt_id"] + "-judgment"
        self.evaluation("assess", "--attempt", receipt["attempt_id"], "--id", identity, "--judgment", self.file(judgment))
        return identity

    def test_audit_to_review_comparison_install_rollback_and_recovery_between_processes(self):
        request = {"scope": "project", "repository": str(self.repo), "sources": [{"id": "prior", "path": "prior.md", "owner": "fixture"}, {"id": "decision", "path": "decision.md", "owner": "fixture"}]}
        inventory = self.audit("inventory", request)
        bundle = self.audit("audit-prepare", {"request": request, "inventory": inventory})
        selected = {v["id"]: v for v in bundle["sources"]}
        finding = {"id": "F-1", "scope": "project", "target": "prior", "claim": "obsolescence", "evidence_type": "semantic",
                   "source_refs": [{"source_id": key, "sha256": selected[key]["sha256"], "excerpt": selected[key]["text"].strip()} for key in ("prior", "decision")],
                   "observation": "The earlier fixture label contradicts the current bounded decision.", "suspected_cause": None, "impact": "The fixture may return the old label.",
                   "uncertainty": ["No agent failure is established by this synthetic case."], "recommendation": {"operation": "REMOVE", "reason": "Replace the obsolete fixture label after review."}, "semantic_basis": None, "priority_reason": "Directly governs the fixture result."}
        analysis = {"schema_version": 1, "id": "cycle-audit", "scope": "project", "inventory_sha256": bundle["inventory_sha256"], "analyst": {"provider": "synthetic-fixture", "version": "1"},
                    "coverage": {"reviewed": ["prior", "decision"], "limits": ["Only these selected fixture clauses were assessed."]}, "findings": [finding], "priority_order": ["F-1"]}
        handoff = self.audit("audit-handoff", {"request": request, "inventory": inventory, "analysis": analysis, "selected_id": "F-1"})
        self.assertEqual(handoff["allowed_actions"], ["review"])
        self.assertFalse(self.database.exists())
        raw = {"schemaVersion": 1, "id": "OBS-1", "status": "inbox", "scope": "project", "basis": "static-risk", "observation": finding["observation"],
               "evidence": [{"source": "audit:cycle-audit/F-1", "summary": finding["observation"]}], "suspectedCause": None}
        origin = {"origin": [{"harness": "synthetic-audit", "session_id": "unavailable-origin", "references": ["audit:cycle-audit/F-1"]}], "capture": {"harness": "public-cli", "session_id": "capture-fixture"}}
        self.records("capture", "--operation", "audit-finding", "--original", self.file(raw), "--provenance", self.file(origin))
        context = self.records("summary", "prepare", "--id", "OBS-1")
        output = summary(context); output["actions"][0]["text"] = finding["observation"]; output["actions"][0]["actor"] = None
        self.records("summary", "save", "--context", self.file(context), "--output", self.file(output), "--expected-revision", 0, "--operation", "reconstruct")
        context = self.records("classification", "prepare", "--id", "OBS-1")
        output = annotation(context); output["category"] = "uncertain"; output["occurrence_ids"] = []
        self.records("classification", "save", "--context", self.file(context), "--output", self.file(output), "--expected-revision", 0, "--operation", "classify")
        self.records("index", "text")
        self.assertEqual(self.records("search", "--text", "fixture label")["matches"][0]["id"], "OBS-1")

        document, extra = review(), options()
        document["sources"] = [{"reference": "source:behavior", "sha256": selected["prior"]["sha256"]}, {"reference": "source:destination", "sha256": selected["decision"]["sha256"]}]
        for item in document["opportunities"]:
            item["basis"] = "static-risk"; item["observation"] = finding["observation"]
        rejected = copy.deepcopy(document["opportunities"][0]); rejected["id"] = "global-rewrite"
        rejected["decision"] = {"status": "reject", "answer": "Do not broaden this into a global rewrite.", "scope": "disposition"}
        document["opportunities"].append(rejected)
        extra["decision_domains"]["global-rewrite"] = "disposition"; extra["dependencies"]["global-rewrite"] = ["source:behavior"]; extra["decision_sources"]["global-rewrite"] = "fixture:user:reject"
        self.records("review", "save", "--record", self.file(document), "--options", self.file(extra), "--expected-revision", 0, "--operation", "start-review")
        document["opportunities"][0]["decision"] = {"status": "adjust", "answer": "Accept only this bounded label behavior.", "scope": "behavior"}
        extra["decision_sources"]["behavior"] = "fixture:user:behavior"; extra["active_question"] = "destination"
        self.records("review", "save", "--record", self.file(document), "--options", self.file(extra), "--expected-revision", 1, "--operation", "accept-behavior")
        resumed = self.records("review", "get", "--id", "REVIEW-1")
        self.assertEqual(resumed["active_question"]["id"], "destination")
        self.assertEqual(resumed["context"]["observations"][0]["summary"]["summary"]["completeness"], "partial")
        drift = self.records("review", "reconcile", "--id", "REVIEW-1", "--checks", self.file([{"reference": "source:destination", "sha256": None, "evidence": "fixture:source-temporarily-unavailable"}]), "--expected-revision", 2, "--operation", "source-drift")
        self.assertEqual(drift["reopened"], ["destination"])
        resumed = self.records("review", "get", "--id", "REVIEW-1")
        self.assertEqual(resumed["record"]["opportunities"][2]["decision"]["status"], "reject")
        self.records("review", "reconcile", "--id", "REVIEW-1", "--checks", self.file([{"reference": "source:destination", "sha256": selected["decision"]["sha256"], "evidence": "fixture:source-rechecked"}]), "--expected-revision", 3, "--operation", "source-rechecked")
        resumed = self.records("review", "get", "--id", "REVIEW-1"); document, extra = resumed["record"], resumed["options"]
        document["opportunities"][1]["decision"] = {"status": "adjust", "answer": "Accept the complete bounded fixture candidate at this destination.", "scope": "destination"}
        extra["decision_sources"]["destination"] = "fixture:user:destination"; extra["active_question"] = None
        extra["artifacts"] = [{"id": "global", "destination": "instructions/global/AGENTS.md", "content": "Maintenance label: candidate\n", "diff": self.fixture.git("diff", self.stable, self.candidate, "--", "instructions/global/AGENTS.md"), "source_refs": ["source:behavior"]}]
        self.records("review", "save", "--record", self.file(document), "--options", self.file(extra), "--expected-revision", 4, "--operation", "accept-destination")

        behavior = case(); behavior["id"] = "cycle-label"
        behavior["fixture"][".evaluation/fixture.py"] = "from pathlib import Path\nimport json\nlabel=Path('AGENTS.md').read_text().split(':')[1].strip()\nPath('answer.json').write_text(json.dumps({'label':label}))\n"
        behavior["checks"][0]["expected"] = {"label": "candidate"}
        behavior["rubric"] = {"skills": [], "criteria": {"label": "Use the requested label."}, "invariants": {"evidence": "Preserve original evidence."}, "expected_stop": "completed"}
        baseline = profile(); baseline["id"] = "baseline"; baseline["source_commit"] = self.stable; baseline["instructions"]["AGENTS.md"] = "Maintenance label: stable\n"
        candidate = copy.deepcopy(baseline); candidate["id"] = "candidate"; candidate["source_commit"] = self.candidate; candidate["instructions"]["AGENTS.md"] = "Maintenance label: candidate\n"
        protocols = [self.evaluation("prepare", "--case", self.file(behavior), "--profile", self.file(p))["protocol_sha256"] for p in (baseline, candidate)]
        plan = {"identity": "cycle-comparison", "review_id": "REVIEW-1", "opportunity_id": "behavior", "expected_review_revision": 5, "baseline_protocols": [protocols[0]],
                "alternatives": [{"id": "bounded-global", "kind": "global", "reason": "Check the relevant fixture instruction change.", "targets": ["instructions/AGENTS.md"], "protocols": [protocols[1]]}, {"id": "none", "kind": "none", "reason": "Keep current instructions if no improvement is established.", "targets": [], "protocols": []}], "repetitions": 1}
        self.records("comparison", "--runner-root", self.root / "runner", "prepare", "--plan", self.file(plan))
        grant = {"schema_version": 1, "id": "cycle-native-budget", "protocols": protocols, "kind": "fixture", "source": "test:synthetic-cycle", "answer": "Run only these mechanical fixtures.", "max_attempts": 4, "max_turns": 4, "max_seconds": 20}
        judgments = []
        for identity, protocol, passed in zip(("baseline", "candidate"), protocols, (False, True)):
            receipt = self.evaluation("execute", "--protocol", protocol, "--attempt", identity, "--grant", self.file(grant), "--transport", "fixture")
            judgments.append(self.assess(receipt, passed))
        result = self.records("comparison", "--runner-root", self.root / "runner", "result", "--id", "cycle-comparison", "--result-id", "cycle-result", "--assessments", self.file(judgments))
        self.assertEqual(result["alternatives"][0]["evidence"], "case-supported")
        self.delivery("prepare", "--id", "cycle-delivery", "--review-id", "REVIEW-1", "--behavior-id", "behavior", "--destination-id", "destination", "--commit", self.candidate)
        authorization = self.file({"kind": "fixture", "source": "test:synthetic-cycle", "answer": "Promote and revert only this isolated fixture.", "home": str(self.home), "commit": self.candidate, "actions": ["promote", "rollback"]})
        self.delivery("promote", "--id", "cycle-delivery", "--grant", authorization)
        # Retain an unrelated later setting across the real rollback.
        config = self.home / ".pi/agent/settings.json"; settings = json.loads(config.read_text()); settings["later"] = "preserve"; config.write_text(json.dumps(settings))
        for identity, stage, label in (("post", "post-promotion", "candidate"), ("rollback", "post-rollback", "stable")):
            if stage == "post-rollback":
                self.delivery("rollback", "--id", "cycle-delivery", "--grant", authorization)
            installed = self.delivery("profile", "--id", "cycle-delivery", "--environment", self.file({"python": "3.13.2"}), "--profile-id", identity, "--kind", "fixture", "--seconds", 5)
            behavior["checks"][0]["expected"] = {"label": label}
            frozen = self.evaluation("prepare", "--case", self.file(behavior), "--profile", self.file(installed))["protocol_sha256"]
            post_grant = {**grant, "id": identity + "-grant", "protocols": [frozen], "max_attempts": 1, "max_turns": 1, "max_seconds": 5}
            receipt = self.evaluation("execute", "--protocol", frozen, "--attempt", identity, "--grant", self.file(post_grant), "--transport", "fixture")
            self.assertEqual(receipt["behavioral_status"], "passed")
            self.assertEqual(self.delivery("check", "--id", "cycle-delivery", "--attempt", identity, "--stage", stage)["behavior"], "fixture-verified")
        self.assertEqual(json.loads(config.read_text())["later"], "preserve")
        self.records("archive", "export", "--destination", self.root / "backup")
        restored = self.root / "restored.sqlite3"
        self.records("archive", "restore", "--source", self.root / "backup", "--destination", restored)
        resumed = self.records("review", "get", "--id", "REVIEW-1", database=restored)
        self.assertEqual(resumed["record"]["promotion"], "none")
        self.assertEqual(resumed["evaluations"][0]["id"], "cycle-result")
        self.assertEqual(resumed["deliveries"][0]["events"][-1]["behavior"], "fixture-verified")
        self.assertEqual(len(resumed["context"]["observations"]), 1)
        self.assertEqual(self.records("list", database=restored)[0]["id"], "OBS-1")
        chat = self.records("review", "save", "--record", self.file(document), "--options", self.file(extra), "--expected-revision", 0, "--operation", "chat", "--chat-only", database=self.root / "chat-only/records.sqlite3")
        self.assertEqual(chat["persistence"], "chat-only")
        self.assertFalse((self.root / "chat-only").exists())
        self.assertTrue(all(v["model_calls"] == 0 for v in self.evaluation("report")["attempts"]))


if __name__ == "__main__":
    unittest.main()
