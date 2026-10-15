"""Compare only declared interventions; results never authorize installation."""
import json

from evaluation import EvaluationError, identifier
from records import digest, encoded


def resources(profile):
    return {**profile["source_files"], **{"instructions/" + key: value for key, value in profile["instructions"].items()}}


class Comparisons:
    def __init__(self, reviews, runner):
        self.reviews, self.runner = reviews, runner

    @staticmethod
    def _schema(db):
        db.execute("CREATE TABLE IF NOT EXISTS comparison_plans(id TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL) STRICT")
        db.execute("CREATE TABLE IF NOT EXISTS review_evidence(id TEXT PRIMARY KEY,review_id TEXT NOT NULL,opportunity_id TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,sha256 TEXT NOT NULL) STRICT")

    def prepare(self, identity, review_id, opportunity_id, expected_review_revision, baseline_protocols, alternatives, *, repetitions):
        identifier(identity)
        review = self.reviews.get(review_id)
        if review["revision"] != expected_review_revision:
            raise EvaluationError("comparison-review-stale")
        opportunity = next((value for value in review["record"]["opportunities"] if value["id"] == opportunity_id), None)
        if opportunity is None:
            raise EvaluationError("unknown-review-opportunity")
        if type(repetitions) is not int or repetitions < 1 or not isinstance(baseline_protocols, list) or not baseline_protocols or len(set(baseline_protocols)) != len(baseline_protocols):
            raise EvaluationError("invalid-comparison-baseline")
        baseline = {sha: self.runner.load(sha) for sha in baseline_protocols}
        by_case = {value["case"]["id"]: value for value in baseline.values()}
        if len(by_case) != len(baseline):
            raise EvaluationError("duplicate-comparison-case")
        if not isinstance(alternatives, list) or not alternatives:
            raise EvaluationError("missing-relevant-alternative")
        seen = set()
        for alternative in alternatives:
            if (not isinstance(alternative, dict) or set(alternative) != {"id", "kind", "reason", "targets", "protocols"} or
                    alternative["kind"] not in ("global", "skill", "check", "none") or not isinstance(alternative["reason"], str) or not alternative["reason"].strip() or
                    not isinstance(alternative["targets"], list) or not isinstance(alternative["protocols"], list)):
                raise EvaluationError("invalid-comparison-alternative")
            identifier(alternative["id"])
            if alternative["id"] in seen:
                raise EvaluationError("duplicate-comparison-alternative")
            seen.add(alternative["id"])
            if alternative["kind"] == "none":
                if alternative["protocols"] or alternative["targets"]:
                    raise EvaluationError("no-change-reuses-baseline")
                continue
            if not alternative["targets"] or any(not isinstance(v, str) or not v.strip() for v in alternative["targets"]):
                raise EvaluationError("undeclared-intervention")
            candidates = [self.runner.load(sha) for sha in alternative["protocols"]]
            if len(candidates) != len(by_case) or {value["case"]["id"] for value in candidates} != by_case.keys():
                raise EvaluationError("comparison-cases-differ")
            for candidate in candidates:
                before = by_case[candidate["case"]["id"]]
                common = ("model", "reasoning", "harness", "environment", "budget_seconds", "max_turns")
                case_keys = ("id", "request", "initial_state", "expected_behavior", "fixture", "checks", "rubric", "setup_commands", "explicit_skills")
                if (any(before["profile"].get(key) != candidate["profile"].get(key) for key in common) or
                        any(before["case"].get(key) != candidate["case"].get(key) for key in case_keys) or
                        before["execution_sources"] != candidate["execution_sources"]):
                    raise EvaluationError("comparison-conditions-differ")
                a, b = resources(before["profile"]), resources(candidate["profile"])
                changed = {key for key in a.keys() | b.keys() if a.get(key) != b.get(key)}
                if not changed or changed - set(alternative["targets"]):
                    raise EvaluationError("undeclared-intervention")
        payload = {"schema_version": 1, "id": identity, "review_id": review_id, "review_revision": review["revision"], "review_sha256": review["sha256"], "review_sources": review["record"]["sources"], "opportunity_id": opportunity_id, "opportunity": opportunity, "baseline_protocols": baseline_protocols, "alternatives": alternatives, "repetitions": repetitions,
                   "allowed_actions": ["prepare-evaluation", "review-results"], "authorization": "No model execution or installation is granted by this plan."}
        body = encoded(payload).decode()
        with self.reviews.records._transaction() as db:
            self._schema(db)
            latest = db.execute("SELECT MAX(revision) FROM review_versions WHERE review_id=?", (review_id,)).fetchone()[0]
            if latest != expected_review_revision:
                raise EvaluationError("comparison-review-stale")
            old = db.execute("SELECT payload FROM comparison_plans WHERE id=?", (identity,)).fetchone()
            if old and old[0] != body:
                raise EvaluationError("comparison-identity-conflict")
            db.execute("INSERT OR IGNORE INTO comparison_plans VALUES(?,?,?)", (identity, body, digest(body.encode())))
        return {"stage": "prepared", "id": identity, "sha256": digest(body.encode()), "plan": payload}

    def get(self, identity):
        with self.reviews.records._connection() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='comparison_plans'").fetchone():
                raise EvaluationError("comparison-not-found")
            row = db.execute("SELECT * FROM comparison_plans WHERE id=?", (identity,)).fetchone()
            if row is None:
                raise EvaluationError("comparison-not-found")
            return {"plan": json.loads(row["payload"]), "sha256": row["sha256"]}

    def record_result(self, identity, result_id, assessment_ids):
        identifier(result_id)
        frozen = self.get(identity); plan = frozen["plan"]
        if not isinstance(assessment_ids, list) or any(not isinstance(v, str) for v in assessment_ids) or len(set(assessment_ids)) != len(assessment_ids):
            raise EvaluationError("invalid-comparison-assessments")
        db = self.runner._ledger()
        try:
            values = []
            for key in assessment_ids:
                row = db.execute("SELECT * FROM assessments WHERE id=?", (key,)).fetchone()
                if row is None:
                    raise EvaluationError("assessment-not-found")
                values.append({"id": key, "sha256": row["sha256"], **json.loads(row["payload"])})
        finally:
            db.close()
        allowed = set(plan["baseline_protocols"]) | {sha for alt in plan["alternatives"] for sha in alt["protocols"]}
        if any(value["protocol_sha256"] not in allowed for value in values) or len({value["attempt_id"] for value in values}) != len(values):
            raise EvaluationError("assessment-outside-comparison")
        expected = plan["repetitions"]
        baseline = [v for v in values if v["protocol_sha256"] in plan["baseline_protocols"]]
        baseline_complete = all(sum(v["protocol_sha256"] == sha for v in baseline) == expected for sha in plan["baseline_protocols"])
        reproduced = any(any(c["result"] == "failed" for c in v["criteria"]) and v["task_result"] == "failed" for v in baseline)
        reproduction = "reproduced" if reproduced else "not-reproduced" if baseline_complete and all(v["task_result"] == "passed" for v in baseline) else "inconclusive"
        alternatives = []
        all_complete = baseline_complete
        for alternative in plan["alternatives"]:
            rows = [v for v in values if v["protocol_sha256"] in alternative["protocols"]]
            complete = all(sum(v["protocol_sha256"] == sha for v in rows) == expected for sha in alternative["protocols"])
            all_complete = all_complete and complete
            invalid = any(v["task_result"] == "invalidated" for v in rows)
            supported = reproduction == "reproduced" and baseline_complete and complete and bool(rows) and all(v["task_result"] == "passed" for v in rows)
            alternatives.append({"id": alternative["id"], "kind": alternative["kind"], "evidence": "invalidated" if invalid else "case-supported" if supported else "baseline-retained" if alternative["kind"] == "none" else "unestablished", "coverage_complete": complete, "metrics": [{"attempt_id": v["attempt_id"], "assessment_id": v["id"], "task_result": v["task_result"], "human_interventions": v["human_interventions"], "unnecessary_actions": v["unnecessary_actions"], **v["metrics"]} for v in rows]})
        current = self.reviews.get(plan["review_id"])
        stale = current["record"]["sources"] != plan["review_sources"]
        attempts = [value for value in self.runner.report()["attempts"] if value["protocol_sha256"] in allowed]
        assessment_attempts = {value["attempt_id"] for value in values}
        unassessed = [value["attempt_id"] for value in attempts if value["attempt_id"] not in assessment_attempts]
        result = {"schema_version": 1, "id": result_id, "comparison_id": identity, "plan_sha256": frozen["sha256"], "review_id": plan["review_id"], "opportunity_id": plan["opportunity_id"], "stage": "executed" if all_complete and not unassessed and values else "inconclusive" if attempts else "prepared", "baseline_reproduction": reproduction,
                  "baseline_metrics": [{"assessment_id": v["id"], "task_result": v["task_result"], "human_interventions": v["human_interventions"], "unnecessary_actions": v["unnecessary_actions"], **v["metrics"]} for v in baseline], "alternatives": alternatives, "assessments": [{"id": v["id"], "sha256": v["sha256"]} for v in values], "unassessed_attempts": unassessed, "review_sources_changed": stale,
                  "recommendation": "Keep current behavior or investigate; historical evidence is retained." if reproduction != "reproduced" else "Review the bounded case evidence and select a decision; no statistical reliability claim.", "allowed_actions": ["continue-review"], "promotion": "none", "limits": ["Passing these cases does not authorize installation.", "An unreproduced historical failure is not disproved.", "Missing, infrastructure and unassessed attempts remain separate; repeated judgments are not extra trials."]}
        body = encoded(result).decode()
        with self.reviews.records._transaction() as db:
            self._schema(db)
            old = db.execute("SELECT payload FROM review_evidence WHERE id=?", (result_id,)).fetchone()
            if old and old[0] != body:
                raise EvaluationError("comparison-result-conflict")
            db.execute("INSERT OR IGNORE INTO review_evidence VALUES(?,?,?,?,?,?)", (result_id, plan["review_id"], plan["opportunity_id"], "comparison", body, digest(body.encode())))
        return result
