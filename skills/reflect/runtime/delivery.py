"""Accepted commit delivery through the existing installer; dry-run by default."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from evaluation import identifier, private_directory
from records import RecordError, digest, encoded


class Delivery:
    def __init__(self, reviews, runner, installer_repository, source_repository, home, control, *, mode="isolated"):
        self.reviews, self.runner = reviews, runner
        self.tools = Path(installer_repository).resolve(strict=True)
        self.source = Path(source_repository).resolve(strict=True)
        self.home = Path(home).resolve(strict=True)
        if mode not in ("isolated", "active") or self.home.stat().st_uid != os.getuid() or (mode == "isolated" and self.home == Path.home().resolve()):
            raise RecordError("invalid-delivery-target")
        self.mode = mode
        self.control = private_directory(control)
        self.state = self.home / ".local/share/mstack"
        info = self.home.stat()
        expected = {"home": str(self.home), "device": info.st_dev, "inode": info.st_ino, "owner": os.getuid(), "mode": mode}
        marker = self.control / "target.json"
        if marker.exists():
            self.target = json.loads(marker.read_text())
            if {k: v for k, v in self.target.items() if k != "id"} != expected:
                raise RecordError("delivery-target-changed")
        else:
            self.target = {"id": uuid.uuid4().hex, **expected}
            from collector import _write_json
            _write_json(marker, self.target)

    @staticmethod
    def _schema(db):
        db.execute("CREATE TABLE IF NOT EXISTS delivery_plans(id TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL) STRICT")
        db.execute("""CREATE TABLE IF NOT EXISTS delivery_events(
            plan_id TEXT NOT NULL REFERENCES delivery_plans(id),revision INTEGER NOT NULL,
            payload TEXT NOT NULL,sha256 TEXT NOT NULL,PRIMARY KEY(plan_id,revision)) STRICT""")

    def _current(self):
        path = self.state / "current.json"
        return json.loads(path.read_text()) if path.exists() else None

    def _invoke(self, command, commit, *, apply=False, expected_generation=None):
        args = [sys.executable, str(self.tools / "install/mstack.py"), command, "--home", str(self.home), "--repo", str(self.source), "--ref", commit]
        if apply:
            args.append("--apply")
        if expected_generation is not None:
            args += ["--expected-generation", expected_generation]
        result = subprocess.run(args, cwd=self.tools, capture_output=True, timeout=60)
        if result.returncode != 0:
            # Installer journals and backups remain authoritative if the acknowledgement failed.
            raise RecordError("installer-operation-unconfirmed")
        return {"command": command, "apply": apply, "exit_code": 0, "output_sha256": digest(result.stdout + result.stderr)}

    def _git(self, *args):
        try:
            return subprocess.check_output(["git", "-C", str(self.source), *args], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise RecordError("delivery-source-unavailable") from None

    def _managed_changes(self, before, after):
        # Reuse the installer's source selection, including manifests and defaults.
        sys.path.insert(0, str(self.tools / "install"))
        try:
            import mstack_source
            if Path(mstack_source.__file__).resolve() != self.tools / "install/mstack_source.py":
                raise RecordError("installer-source-conflict")
            _, old = mstack_source.source(self.source, before)
            _, new = mstack_source.source(self.source, after)
        finally:
            sys.path.pop(0)
        paths = set(old) | set(new)
        changed = self._git("diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-only", "-z", before, after, "--", *sorted(paths))
        return paths, {value.decode() for value in changed.split(b'\0') if value}

    def prepare(self, identity, review_id, behavior_id, destination_id, commit):
        identifier(identity)
        review = self.reviews.get(review_id)
        items = {v["id"]: v for v in review["record"]["opportunities"]}
        accepted = {"keep", "adjust", "add", "remove", "summarize", "move"}
        for key, domain in ((behavior_id, "behavior"), (destination_id, "destination")):
            if key not in items or items[key]["decision"]["status"] not in accepted or review["options"]["decision_domains"][key] != domain:
                raise RecordError("delivery-acceptance-pending")
        commit = self._git("rev-parse", "--verify", "--end-of-options", commit + "^{commit}").decode().strip()
        previous = self._current()
        if previous is None:
            raise RecordError("stable-installation-required-for-delivery-cycle")
        artifacts = review["options"]["artifacts"]
        if not artifacts:
            raise RecordError("missing-complete-candidate")
        for artifact in artifacts:
            exists = self._git("ls-tree", "-z", commit, "--", artifact["destination"])
            content = self._git("show", commit + ":" + artifact["destination"]) if exists else b""
            if content != artifact["content"].encode():
                raise RecordError("candidate-artifact-mismatch")
            actual_diff = self._git("diff", "--no-ext-diff", "--no-textconv", previous["commit"], commit, "--", artifact["destination"]).decode()
            if actual_diff.strip() != artifact["diff"].strip():
                raise RecordError("candidate-diff-mismatch")
        managed, changed = self._managed_changes(previous["commit"], commit)
        declared = {artifact["destination"] for artifact in artifacts}
        if declared - managed:
            raise RecordError("candidate-destination-not-managed")
        if changed - declared:
            raise RecordError("undeclared-installed-change")
        basis = items[behavior_id]["basis"]
        evidence = "explicit-preference-or-fact" if basis in ("user-preference", "technical-fact") else "evaluation-required"
        if evidence == "evaluation-required":
            from comparisons import Comparisons
            supported = False
            for result in review["evaluations"]:
                if result.get("stage") != "executed" or result.get("review_sources_changed") or result.get("opportunity_id") != behavior_id:
                    continue
                comparison = Comparisons(self.reviews, self.runner).get(result["comparison_id"])["plan"]
                if comparison["opportunity_id"] != behavior_id or comparison["review_id"] != review_id:
                    continue
                for alternative in comparison["alternatives"]:
                    matched = next((v for v in result["alternatives"] if v["id"] == alternative["id"]), None)
                    if matched and matched["evidence"] == "case-supported" and alternative["protocols"] and all(self.runner.load(sha, check_execution=False)["profile"]["source_commit"] == commit for sha in alternative["protocols"]):
                        supported = True
            if not supported:
                raise RecordError("candidate-behavior-evidence-pending")
        if self.mode == "active" and not self._rehearsed(commit):
            raise RecordError("isolated-behavioral-rehearsal-required")
        # The installer dry-run has an independent, already tested no-HOME-writes contract.
        dry = self._invoke("setup", commit, expected_generation=previous["generation"] if previous else "none")
        payload = {"schema_version": 1, "id": identity, "review_id": review_id, "review_sha256": review["sha256"], "review_sources": review["record"]["sources"], "behavior_id": behavior_id, "destination_id": destination_id,
                   "commit": commit, "previous": previous, "target": self.target, "source_repository": str(self.source), "installer_sources": self._installer_sources(), "artifacts": artifacts, "basis": evidence, "dry_run": dry}
        payload["accepted_opportunities"] = {key: items[key] for key in (behavior_id, destination_id)}
        payload["decision_sources"] = {key: review["options"]["decision_sources"][key] for key in (behavior_id, destination_id)}
        relevant = set(review["options"]["dependencies"][behavior_id] + review["options"]["dependencies"][destination_id]) | {ref for artifact in artifacts for ref in artifact["source_refs"]}
        payload["relevant_sources"] = {value["reference"]: value["sha256"] for value in review["record"]["sources"] if value["reference"] in relevant}
        body = encoded(payload).decode()
        with self.reviews.records._transaction() as db:
            self._schema(db)
            old = db.execute("SELECT payload FROM delivery_plans WHERE id=?", (identity,)).fetchone()
            if old and old[0] != body:
                raise RecordError("delivery-plan-conflict")
            db.execute("INSERT OR IGNORE INTO delivery_plans VALUES(?,?,?)", (identity, body, digest(body.encode())))
        return {"stage": "prepared", "plan": payload, "sha256": digest(body.encode())}

    def get(self, identity):
        info = self.home.stat()
        if (info.st_dev, info.st_ino, info.st_uid) != (self.target["device"], self.target["inode"], self.target["owner"]) or json.loads((self.control / "target.json").read_text()) != self.target:
            raise RecordError("delivery-target-changed")
        with self.reviews.records._connection() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='delivery_plans'").fetchone():
                raise RecordError("delivery-not-found")
            row = db.execute("SELECT * FROM delivery_plans WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise RecordError("delivery-not-found")
            plan = json.loads(row["payload"])
            if plan["target"] != self.target or plan["source_repository"] != str(self.source):
                raise RecordError("delivery-target-changed")
            if plan["installer_sources"] != self._installer_sources():
                raise RecordError("installer-code-changed")
            events = [json.loads(v[0]) for v in db.execute("SELECT payload FROM delivery_events WHERE plan_id=? ORDER BY revision", (identity,))]
            return {"plan": plan, "sha256": row["sha256"], "events": events}

    def _installer_sources(self):
        return {name: digest((self.tools / "install" / name).read_bytes()) for name in ("mstack.py", "mstack_source.py", "mstack_config.py", "mstack_fs.py")}

    def _event(self, identity, value):
        with self.reviews.records._transaction() as db:
            self._schema(db)
            revision = db.execute("SELECT COALESCE(MAX(revision),0)+1 FROM delivery_events WHERE plan_id=?", (identity,)).fetchone()[0]
            body = encoded(value).decode()
            old = db.execute("SELECT payload FROM delivery_events WHERE plan_id=? ORDER BY revision DESC LIMIT 1", (identity,)).fetchone()
            if old and old[0] == body:
                return value
            db.execute("INSERT INTO delivery_events VALUES(?,?,?,?)", (identity, revision, body, digest(body.encode())))
        return value

    def _grant(self, plan, grant, action):
        if (not isinstance(grant, dict) or set(grant) != {"kind", "source", "answer", "home", "commit", "actions"} or grant["kind"] not in ("user", "fixture") or
                (self.mode == "active" and grant["kind"] != "user") or grant["home"] != str(self.home) or grant["commit"] != plan["commit"] or
                any(not isinstance(grant[v], str) or not grant[v].strip() for v in ("source", "answer")) or not isinstance(grant["actions"], list) or
                set(grant["actions"]) - {"promote", "rollback"} or action not in grant["actions"]):
            raise RecordError("delivery-authorization-missing")

    def promote(self, identity, grant):
        value = self.get(identity); plan = value["plan"]
        self._grant(plan, grant, "promote")
        review = self.reviews.get(plan["review_id"])
        current_items = {v["id"]: v for v in review["record"]["opportunities"]}
        sources = {v["reference"]: v["sha256"] for v in review["record"]["sources"]}
        current_artifacts = {v["id"]: v for v in review["options"]["artifacts"]}
        if (any(current_items.get(key) != value or review["options"]["decision_sources"].get(key) != plan["decision_sources"][key] for key, value in plan["accepted_opportunities"].items()) or
                any(key not in sources or sources[key] != sha for key, sha in plan["relevant_sources"].items()) or
                any(current_artifacts.get(v["id"]) != v for v in plan["artifacts"])):
            raise RecordError("delivery-review-changed")
        if any(v.get("stage") == "promoted-check-pending" for v in value["events"]):
            current = self._current()
            if current and current["commit"] == plan["commit"]:
                self._invoke("verify", plan["commit"])
                return {"stage": "already-promoted", "generation": current["generation"]}
            raise RecordError("delivery-state-changed")
        expected = plan["previous"]["generation"] if plan["previous"] else "none"
        self._event(identity, {"stage": "promotion-started", "grant": grant})
        self._invoke("setup", plan["commit"], apply=True, expected_generation=expected)
        self._invoke("verify", plan["commit"])
        receipt = self._current()
        if receipt["commit"] != plan["commit"]:
            raise RecordError("delivery-receipt-mismatch")
        return self._event(identity, {"stage": "promoted-check-pending", "commit": receipt["commit"], "generation": receipt["generation"], "bundle_sha256": receipt["bundle_sha256"], "previous_generation": expected})

    def rollback(self, identity, grant):
        value = self.get(identity); plan = value["plan"]
        self._grant(plan, grant, "rollback")
        promoted = next((v for v in reversed(value["events"]) if v["stage"] == "promoted-check-pending"), None)
        if promoted is None:
            raise RecordError("promotion-receipt-unavailable")
        if any(v["stage"] == "restored-check-pending" for v in value["events"]):
            self._invoke("verify", plan["previous"]["commit"])
            return {"stage": "already-restored"}
        self._event(identity, {"stage": "rollback-started", "grant": grant})
        self._invoke("rollback", plan["commit"], apply=True, expected_generation=promoted["generation"])
        receipt = self._current()
        if receipt != plan["previous"]:
            raise RecordError("restoration-receipt-mismatch")
        if receipt:
            self._invoke("verify", receipt["commit"])
        return self._event(identity, {"stage": "restored-check-pending", "commit": receipt["commit"] if receipt else None, "generation": receipt["generation"] if receipt else None})

    def installed_profile(self, delivery_id, environment, *, identity, model, reasoning, seconds):
        plan = self.get(delivery_id)["plan"]
        receipt = self._current()
        if receipt is None:
            raise RecordError("installed-profile-unavailable")
        if receipt["commit"] not in {plan["commit"], plan["previous"]["commit"]}:
            raise RecordError("delivery-state-changed")
        self._invoke("verify", receipt["commit"])
        from evaluation_source import git_profile
        env = {**environment, "installation": {"target_id": self.target["id"], "mode": self.mode, "commit": receipt["commit"], "generation": receipt["generation"], "bundle_sha256": receipt["bundle_sha256"]}}
        if model is None:
            env.setdefault("codex", "fixture")
        profile = git_profile(self.source, receipt["commit"], env, identity=identity, model=model, reasoning=reasoning, seconds=seconds, tool_repository=self.tools)
        for path in list(profile["source_files"]):
            if path.startswith("skills/"):
                actual = (Path(receipt["roots"]["codex"]) / path).read_bytes().decode()
                if actual != profile["source_files"][path]:
                    raise RecordError("installed-content-mismatch")
                profile["source_files"][path] = actual
        instructions = (Path(receipt["roots"]["codex"]) / "AGENTS.md").read_bytes().decode()
        profile["instructions"] = {"AGENTS.md" if model is None else "global/AGENTS.md": instructions}
        if model is None:
            profile.update({"kind": "fixture", "harness": {"name": "fixture-process", "version": "1"}})
        return profile

    def record_check(self, identity, attempt_id, stage, assessment_id=None):
        if stage not in ("post-promotion", "post-rollback"):
            raise RecordError("invalid-delivery-check-stage")
        plan = self.get(identity)["plan"]
        current = self._current()
        if current is None:
            raise RecordError("installed-profile-unavailable")
        expected_commit = plan["commit"] if stage == "post-promotion" else (plan["previous"] or {}).get("commit")
        if current["commit"] != expected_commit:
            raise RecordError("delivery-check-state-changed")
        self._invoke("verify", current["commit"])
        db = self.runner._ledger()
        try:
            row = db.execute("SELECT result FROM attempts WHERE id=?", (attempt_id,)).fetchone()
            if row is None or row[0] is None:
                raise RecordError("behavioral-receipt-unavailable")
            result = json.loads(row[0])
            protocol = self.runner.load(result["protocol_sha256"], check_execution=False)
            installed = protocol["profile"]["environment"].get("installation", {})
            if installed.get("target_id") != self.target["id"] or installed.get("generation") != current["generation"] or installed.get("commit") != current["commit"]:
                raise RecordError("check-not-from-installed-state")
            if protocol["profile"]["kind"] == "fixture":
                behavior = {"passed": "fixture-verified", "failed": "failed"}.get(result["behavioral_status"], "inconclusive")
            else:
                judgment = db.execute("SELECT payload FROM assessments WHERE id=? AND attempt_id=?", (assessment_id, attempt_id)).fetchone() if assessment_id else None
                behavior = {"passed": "verified", "failed": "failed", "invalidated": "failed"}.get(json.loads(judgment[0])["task_result"], "inconclusive") if judgment else "pending"
        finally:
            db.close()
        recommendation = "Continue the accepted workflow." if behavior in ("verified", "fixture-verified") else "Recommend rollback or investigation; this result grants no new permission." if behavior == "failed" else "Complete missing assessment or investigate infrastructure; no behavioral failure is established."
        return self._event(identity, {"stage": stage, "behavior": behavior, "attempt_id": attempt_id, "assessment_id": assessment_id, "protocol_sha256": result["protocol_sha256"], "generation": current["generation"], "recommendation": recommendation})

    def _rehearsed(self, commit):
        with self.reviews.records._connection() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='delivery_plans'").fetchone():
                return False
            for row in db.execute("SELECT id,payload FROM delivery_plans"):
                plan = json.loads(row["payload"])
                if plan["commit"] == commit and plan["target"]["mode"] == "isolated":
                    events = [json.loads(v[0]) for v in db.execute("SELECT payload FROM delivery_events WHERE plan_id=?", (row["id"],))]
                    if all(any(v.get("stage") == stage and v.get("behavior") == "verified" for v in events) for stage in ("post-promotion", "post-rollback")):
                        return True
        return False

    def reconcile(self, identity):
        value = self.get(identity); plan = value["plan"]
        current = self._current()
        if current is not None:
            self._invoke("verify", current["commit"])
        if current == plan["previous"] and any(v["stage"] == "rollback-started" for v in value["events"]):
            return self._event(identity, {"stage": "restored-check-pending", "commit": current["commit"], "generation": current["generation"], "recovery": "installer-state-observed", "actor": None})
        prior = current.get("previous") if current else None
        if current and current["commit"] == plan["commit"] and prior and prior["generation"] == plan["previous"]["generation"] and any(v["stage"] == "promotion-started" for v in value["events"]):
            return self._event(identity, {"stage": "promoted-check-pending", "commit": current["commit"], "generation": current["generation"], "bundle_sha256": current["bundle_sha256"], "recovery": "installer-state-observed", "actor": None})
        raise RecordError("delivery-state-not-reconciled")
