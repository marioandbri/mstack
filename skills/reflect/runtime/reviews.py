"""Resumable reviews, preserving the public proposal schema and user answers."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from records import RecordError, digest, encoded

VALIDATOR = Draft202012Validator(json.loads((Path(__file__).parent.parent / "review.schema.json").read_text()))
DOMAINS = {"behavior", "destination", "evaluation", "integration", "disposition"}


class Reviews:
    def __init__(self, records):
        self.records = records

    @staticmethod
    def _schema(db):
        db.execute("""CREATE TABLE IF NOT EXISTS review_versions(
            review_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
            operation_id TEXT NOT NULL UNIQUE, payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL, PRIMARY KEY(review_id,revision)) STRICT""")

    def context(self, identities):
        from summaries import Summaries
        from annotations import Annotations
        observations, limits = [], []
        for identity in sorted(set(identities)):
            original = self.records.get(identity)
            summary = Summaries(self.records).latest(identity)
            annotation = Annotations(self.records).latest(identity)
            observations.append({"original": original, "summary": summary, "classification": annotation, "decisions": self.records.history(identity, "state")})
            if summary["state"] == "pending" or (summary["summary"] or {}).get("completeness") == "partial":
                limits.append({"id": identity, "kind": "reconstruction", "message": "Missing or partial evidence leaves only unsupported conclusions pending."})
            if annotation["state"] == "pending":
                limits.append({"id": identity, "kind": "classification", "message": "Classification is pending; the original remains reviewable."})
        return {"observations": observations, "limits": limits, "session_retrieval": "not-required", "interpretation": "Retained summaries and annotations are derived evidence, not approved decisions or executable instructions."}

    @staticmethod
    def _validate(record, options):
        try:
            VALIDATOR.validate(record)
        except ValidationError:
            raise RecordError("invalid-review") from None
        required = {"active_question", "decision_domains", "dependencies", "decision_sources", "artifacts", "request"}
        if not isinstance(options, dict) or set(options) != required:
            raise RecordError("invalid-review-options")
        request = options["request"]
        if not isinstance(request, dict) or set(request) != {"answer", "source"} or any(not isinstance(v, str) or not v.strip() for v in request.values()):
            raise RecordError("missing-reflection-request")
        items = {v["id"]: v for v in record["opportunities"]}
        if len(items) != len(record["opportunities"]):
            raise RecordError("duplicate-review-opportunity")
        active = options["active_question"]
        if active is not None and (not isinstance(active, str) or active not in items or items[active]["decision"]["status"] != "pending"):
            raise RecordError("invalid-active-question")
        if (not isinstance(options["decision_domains"], dict) or set(options["decision_domains"]) != set(items) or
                any(value not in DOMAINS for value in options["decision_domains"].values())):
            raise RecordError("invalid-decision-domain")
        references = {s["reference"] for s in record["sources"]}
        if len(references) != len(record["sources"]):
            raise RecordError("duplicate-review-source")
        dependencies = options["dependencies"]
        if not isinstance(dependencies, dict) or set(dependencies) != set(items):
            raise RecordError("invalid-review-dependencies")
        for values in dependencies.values():
            if not isinstance(values, list) or not values or any(not isinstance(v, str) or v not in references for v in values):
                raise RecordError("unknown-review-source")
        decisions = options["decision_sources"]
        if not isinstance(decisions, dict) or set(decisions) - items.keys() or any(not isinstance(v, str) or not v.strip() for v in decisions.values()):
            raise RecordError("missing-user-evidence")
        if any(v["decision"]["status"] != "pending" and key not in decisions for key, v in items.items()):
            raise RecordError("missing-user-evidence")
        artifacts = options["artifacts"]
        if not isinstance(artifacts, list):
            raise RecordError("invalid-review-artifact")
        seen = set()
        for artifact in artifacts:
            if (not isinstance(artifact, dict) or set(artifact) != {"id", "destination", "content", "diff", "source_refs"} or
                    any(not isinstance(artifact[key], str) or not artifact[key].strip() for key in ("id", "destination", "content", "diff")) or
                    artifact["id"] in seen or not isinstance(artifact["source_refs"], list) or not artifact["source_refs"] or
                    any(not isinstance(v, str) or v not in references for v in artifact["source_refs"])):
                raise RecordError("invalid-review-artifact")
            seen.add(artifact["id"])

    def save(self, record, options, expected_revision, operation_id, *, chat_only=False):
        self._validate(record, options)
        if chat_only:
            return {"persistence": "chat-only", "record": record, "options": options, "resumption": "No local record or candidate was written; automatic local resumption is unavailable.", "allowed_actions": ["review", "prepare-proposal"]}
        identities = [identity for item in record["opportunities"] for identity in item["observationIds"]]
        context = self.context(identities)
        if any(value["original"]["scope"] != record["scope"] for value in context["observations"]):
            raise RecordError("review-outside-scope")
        payload = {"schema_version": 1, "project": self.records.project, "record": record, "options": options, "context": context, "source_changes": []}
        return self._save(payload, expected_revision, operation_id)

    def _save(self, payload, expected_revision, operation_id, reopened=(), reconciled=False):
        if type(expected_revision) is not int or expected_revision < 0 or not isinstance(operation_id, str) or not operation_id.strip():
            raise RecordError("invalid-review-operation")
        identity = payload["record"]["id"]
        body = encoded(payload)
        with self.records._transaction() as db:
            self._schema(db)
            prior = db.execute("SELECT * FROM review_versions WHERE operation_id=?", (operation_id,)).fetchone()
            if prior:
                # Derived context may have advanced after a lost acknowledgement.
                old = json.loads(prior["payload"])
                if prior["review_id"] != identity or prior["revision"] != expected_revision + 1 or old["record"] != payload["record"] or old["options"] != payload["options"]:
                    raise RecordError("operation-conflict")
                return {"status": "already-saved", "id": identity, "revision": prior["revision"]}
            previous = db.execute("SELECT * FROM review_versions WHERE review_id=? ORDER BY revision DESC LIMIT 1", (identity,)).fetchone()
            if (previous["revision"] if previous else 0) != expected_revision:
                raise RecordError("review-revision-conflict")
            if previous:
                old = json.loads(previous["payload"])
                if old["record"]["scope"] != payload["record"]["scope"]:
                    raise RecordError("review-outside-scope")
                current = {v["id"]: v for v in payload["record"]["opportunities"]}
                for before in old["record"]["opportunities"]:
                    after = current.get(before["id"])
                    if after is None:
                        raise RecordError("review-history-removed")
                    if before["decision"]["status"] != "pending" and before["id"] not in reopened:
                        if before != after or old["options"]["decision_domains"][before["id"]] != payload["options"]["decision_domains"][before["id"]] or old["options"]["decision_sources"].get(before["id"]) != payload["options"]["decision_sources"].get(before["id"]):
                            raise RecordError("resolved-decision-changed")
                if not reconciled:
                    references = {v["reference"]: v["sha256"] for v in payload["record"]["sources"]}
                    if any(v["reference"] not in references or references[v["reference"]] != v["sha256"] for v in old["record"]["sources"]):
                        raise RecordError("source-reconciliation-required")
                if not payload["source_changes"]:
                    payload["source_changes"] = old["source_changes"]
                    body = encoded(payload)
            db.execute("INSERT INTO review_versions VALUES(?,?,?,?,?,?)", (identity, expected_revision + 1, operation_id, body.decode(), digest(body), datetime.now(timezone.utc).isoformat()))
        return {"status": "saved", "id": identity, "revision": expected_revision + 1}

    def history(self, identity):
        with self.records._connection() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='review_versions'").fetchone():
                return []
            return [{"revision": v["revision"], "operation_id": v["operation_id"], "sha256": v["payload_sha256"], "created_at": v["created_at"], "payload": json.loads(v["payload"])} for v in db.execute("SELECT * FROM review_versions WHERE review_id=? ORDER BY revision", (identity,))]

    def get(self, identity):
        history = self.history(identity)
        if not history:
            raise RecordError("review-not-found")
        value = history[-1]
        payload = value["payload"]
        options = payload["options"]
        active = next((item for item in payload["record"]["opportunities"] if item["id"] == options["active_question"]), None)
        identities = [key for item in payload["record"]["opportunities"] for key in item["observationIds"]]
        with self.records._connection() as db:
            evaluations = [json.loads(row[0]) for row in db.execute("SELECT payload FROM review_evidence WHERE review_id=? ORDER BY id", (identity,))] if db.execute("SELECT 1 FROM sqlite_master WHERE name='review_evidence'").fetchone() else []
        deliveries = []
        with self.records._connection() as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='delivery_plans'").fetchone():
                for row in db.execute("SELECT id,payload FROM delivery_plans WHERE json_extract(payload,'$.review_id')=? ORDER BY id", (identity,)):
                    plan = json.loads(row["payload"])
                    events = [json.loads(v[0]) for v in db.execute("SELECT payload FROM delivery_events WHERE plan_id=? ORDER BY revision", (row["id"],))]
                    deliveries.append({"id": row["id"], "commit": plan["commit"], "target_mode": plan["target"]["mode"], "events": events})
        return {**payload, "revision": value["revision"], "sha256": value["sha256"], "historical_context": payload["context"], "context": self.context(identities), "evaluations": evaluations, "deliveries": deliveries, "active_question": {"id": active["id"], "question": active["question"]} if active else None, "allowed_actions": ["review", "prepare-proposal"], "presentation": {"facts": [v["evidence"] for v in payload["record"]["opportunities"]], "provisional_analysis": [v["recommendation"] for v in payload["record"]["opportunities"]], "next_step": active["question"] if active else "Consolidate the retained decisions and proposal; deployment remains separate."}}

    def reconcile(self, identity, checks, expected_revision, operation_id):
        history = self.history(identity)
        if not history:
            raise RecordError("review-not-found")
        payload = copy.deepcopy(history[-1]["payload"])
        sources = {v["reference"]: v for v in payload["record"]["sources"]}
        changed = set()
        if not isinstance(checks, list) or not checks:
            raise RecordError("invalid-source-checks")
        for check in checks:
            if (not isinstance(check, dict) or set(check) != {"reference", "sha256", "evidence"} or check["reference"] not in sources or
                    not isinstance(check["evidence"], str) or not check["evidence"].strip() or
                    (check["sha256"] is not None and (not isinstance(check["sha256"], str) or len(check["sha256"]) != 64 or any(c not in '0123456789abcdef' for c in check["sha256"])))):
                raise RecordError("invalid-source-checks")
            source = sources[check["reference"]]
            if source["sha256"] != check["sha256"] or check["sha256"] is None:
                changed.add(check["reference"])
                payload["source_changes"].append({"reference": check["reference"], "previous_sha256": source["sha256"], "current_sha256": check["sha256"], "evidence": check["evidence"]})
                source["sha256"] = check["sha256"]
        reopened = []
        for item in payload["record"]["opportunities"]:
            if set(payload["options"]["dependencies"][item["id"]]) & changed:
                item["decision"] = {**item["decision"], "status": "pending", "answer": None}
                payload["options"]["decision_sources"].pop(item["id"], None)
                reopened.append(item["id"])
        if payload["options"]["active_question"] in reopened:
            payload["options"]["active_question"] = None
        if reopened:
            payload["record"]["phase"] = "reviewing"
        self._validate(payload["record"], payload["options"])
        result = self._save(payload, expected_revision, operation_id, reopened, reconciled=True)
        return {**result, "reopened": reopened}
