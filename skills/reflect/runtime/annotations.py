"""Validate and version advice from the agent procedure; never execute it."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from records import RecordError, digest, encoded
import derived_work

CATEGORIES = ("ephemeral", "project-fact", "architectural-decision", "reusable-procedure", "global-invariant", "agent-failure", "uncertain")
COMPONENTS = {"records": "records.md", "instruction-review": "instruction-review.md", "skill-support": "skill-support.md", "evaluation": "failure-evaluation.md", "research": "research.md", "system-audit": "system-audit.md"}
SCHEMA = Path(__file__).parent.parent / "annotation.schema.json"
VALIDATOR = Draft202012Validator(json.loads(SCHEMA.read_text()))


class Annotations:
    def __init__(self, records):
        self.records = records

    def prepare(self, identity, related_ids=(), *, provider=None, categories=None, component_ids=None):
        related_ids = sorted(set(related_ids) - {identity})
        values = [self.records.get(key) for key in [identity, *related_ids]]
        provider = {"name": "agent-procedure", "version": "classification.v1"} if provider is None else provider
        if (not isinstance(provider, dict) or set(provider) != {"name", "version"} or
                any(not isinstance(v, str) or not v.strip() for v in provider.values())):
            raise RecordError("invalid-provider")
        categories = list(CATEGORIES if categories is None else categories)
        if not categories or len(set(categories)) != len(categories) or set(categories) - set(CATEGORIES):
            raise RecordError("invalid-categories")
        references = Path(__file__).parent.parent / "references"
        available = {name: digest((references / filename).read_bytes()) for name, filename in COMPONENTS.items() if (references / filename).is_file()}
        component_ids = sorted(available if component_ids is None else component_ids)
        if len(set(component_ids)) != len(component_ids) or set(component_ids) - set(available):
            raise RecordError("unknown-component")
        snapshots, decisions, sources = [], [], []
        for value in values:
            snapshots.append({"id": value["id"], "scope": value["scope"], "raw_sha256": value["raw_sha256"], "observation": value["observation"], "provenance": value["provenance"], "state": value["state"], "state_revision": value["revision"]})
            sources.append({"id": "observation:" + value["id"], "sha256": value["raw_sha256"]})
            for decision in self.records.history(value["id"], "state"):
                decisions.append({"record_id": value["id"], "revision": decision["revision"], **decision["payload"]})
                sources.append({"id": f'decision:{value["id"]}:{decision["revision"]}', "sha256": decision["sha256"]})
            from decision_history import review_decisions
            with self.records._connection() as db:
                for decision in review_decisions(db, value["id"], history=True):
                    decisions.append(decision)
                    source = {"id": f'review:{decision["review_id"]}:{decision["revision"]}', "sha256": decision["sha256"]}
                    if source not in sources:
                        sources.append(source)
        for name in component_ids:
            sources.append({"id": "component:" + name, "sha256": available[name]})
        context = {"schema_version": 1, "project": self.records.project, "scope": values[0]["scope"], "primary_id": identity, "related_ids": related_ids, "provider": provider, "records": snapshots, "user_decisions": decisions, "sources": sources, "allowed_categories": categories, "component_ids": component_ids, "retrieval_limits": ["Only explicitly selected records are included; no global absence or recurrence claim.", "Component resources are available, not proven selected or executed by a harness."]}
        return {**context, "input_sha256": digest(encoded(context))}

    def _validate_output(self, context, output):
        try:
            VALIDATOR.validate(output)
        except ValidationError:
            raise RecordError("invalid-classification") from None
        if output["input_sha256"] != context["input_sha256"] or output["provider"] != context["provider"]:
            raise RecordError("classification-input-mismatch")
        if output["category"] is not None and output["category"] not in context["allowed_categories"]:
            raise RecordError("invalid-category")
        if output["category"] is None and output["abstention_reason"] is None:
            raise RecordError("missing-abstention-reason")
        if output["opportunity"]["scope"] != context["scope"]:
            raise RecordError("classification-outside-scope")
        if output["suggested_component"] is not None and output["suggested_component"] not in context["component_ids"]:
            raise RecordError("unknown-component")
        sources = {source["id"]: source["sha256"] for source in context["sources"]}

        def references(values):
            for reference in values:
                if reference["id"] not in sources or reference["sha256"] != sources[reference["id"]]:
                    raise RecordError("unknown-source")
            return {value["id"] for value in values}

        cited = references(output["source_refs"])
        if "observation:" + context["primary_id"] not in cited:
            raise RecordError("missing-primary-evidence")
        self._validate_relations(context, output, references)
        observations = {value["id"]: value["observation"] for value in context["records"]}
        all_refs = cited | {ref["id"] for link in output["relations"] for ref in link["source_refs"]}
        if output["category"] == "agent-failure" and not any(value["basis"] == "observed-failure" and "observation:" + identity in all_refs for identity, value in observations.items()):
            raise RecordError("unsupported-agent-failure")

    def _validate_relations(self, context, output, references):
        records = {value["id"]: value for value in context["records"]}
        parents = {identity: identity for identity in records}

        def root(identity):
            while parents[identity] != identity:
                parents[identity] = parents[parents[identity]]
                identity = parents[identity]
            return identity

        for link in output["relations"]:
            a, b = link["from_id"], link["to_id"]
            if a not in records or b not in records or a == b:
                raise RecordError("unknown-related-record")
            if not {"observation:" + a, "observation:" + b}.issubset(references(link["source_refs"])):
                raise RecordError("unsupported-relation")
            if link["relation"] == "same-incident":
                parents[root(b)] = root(a)
        adjacent = {root(identity): set() for identity in records}
        for link in output["relations"]:
            if link["relation"] != "recurrence":
                continue
            a, b = root(link["from_id"]), root(link["to_id"])
            if a == b:
                raise RecordError("invalid-occurrence")
            if link["scope_match"] != "equivalent":
                raise RecordError("incompatible-recurrence-scope")
            adjacent[a].add(b); adjacent[b].add(a)
        reachable = {root(context["primary_id"])}
        pending = list(reachable)
        while pending:
            for identity in adjacent[pending.pop()] - reachable:
                reachable.add(identity); pending.append(identity)
        counted = set()
        for identity in output["occurrence_ids"]:
            if identity not in records or records[identity]["observation"]["basis"] != "observed-failure":
                raise RecordError("invalid-occurrence")
            group = root(identity)
            if group not in reachable or group in counted:
                raise RecordError("invalid-occurrence")
            counted.add(group)

    def save(self, context, output, expected_revision, operation_id):
        return derived_work.save(self.records, "annotation", context, output, expected_revision, operation_id,
            lambda ctx: self.prepare(ctx["primary_id"], ctx["related_ids"], provider=ctx["provider"], categories=ctx["allowed_categories"], component_ids=ctx["component_ids"]), self._validate_output)

    def history(self, identity):
        return self.records.history(identity, "annotation")

    def latest(self, identity):
        versions = self.history(identity)
        if not versions:
            return {"state": "pending", "revision": 0, "annotation": None}
        last = versions[-1]
        output = last["payload"]["output"]
        pending = "classification" in self.records.get(identity)["pending"]
        context = last["payload"]["input"]
        try:
            fresh = self.prepare(context["primary_id"], context["related_ids"], provider=context["provider"], categories=context["allowed_categories"], component_ids=context["component_ids"])
            stale = fresh != context
        except RecordError:
            stale = True
        return {"state": "pending" if pending or stale else "provisional", "revision": last["revision"], "annotation": output, "input": context, "sources_changed": stale, "occurrence_count": len(output["occurrence_ids"]) if output["occurrence_ids"] else None}
