"""Retain a factual reconstruction without inventing a missing conversation."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

import derived_work
from records import RecordError, digest, encoded

SCHEMA = json.loads((Path(__file__).parent.parent / "summary.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
EVIDENCE = Draft202012Validator({"$ref": "#/$defs/evidence", "$defs": SCHEMA["$defs"]})
FACT_LISTS = ("constraints", "actions", "results", "corrections", "authorizations", "hypotheses", "contradictions")


class Summaries:
    def __init__(self, records):
        self.records = records

    def prepare(self, identity, evidence=None, related_ids=()):
        value = self.records.get(identity)
        evidence = {"sources": [], "excerpts": []} if evidence is None else evidence
        try:
            EVIDENCE.validate(evidence)
        except ValidationError:
            raise RecordError("invalid-summary-evidence") from None
        sources = [{"id": "observation:" + identity, "sha256": value["raw_sha256"], "kind": "observation", "temporal_role": "historical", "availability": "retained"}, *evidence["sources"]]
        excerpts = [{"id": "original-observation", "source_id": "observation:" + identity, "text": value["observation"]["observation"], "sanitized": True, "kind": "record-text"}, *evidence["excerpts"]]
        known = {source["id"]: source for source in sources}
        if len(known) != len(sources) or len({v["id"] for v in excerpts}) != len(excerpts):
            raise RecordError("duplicate-summary-source")
        if any(e["source_id"] not in known or known[e["source_id"]]["availability"] != "retained" for e in excerpts):
            raise RecordError("unknown-summary-source")
        related_ids = sorted(set(related_ids) - {identity})
        linked = [{"id": key, "raw_sha256": self.records.get(key)["raw_sha256"]} for key in related_ids]
        previous = self.history(identity)
        context = {"schema_version": 1, "project": self.records.project, "primary_id": identity, "scope": value["scope"], "raw_sha256": value["raw_sha256"], "provenance": value["provenance"], "previous_revision": previous[-1]["revision"] if previous else 0, "previous_sha256": previous[-1]["sha256"] if previous else None, "related_ids": related_ids, "related_records": linked, "additional_evidence": evidence, "evidence": {"sources": sources, "excerpts": excerpts}}
        return {**context, "input_sha256": digest(encoded(context))}

    def _validate(self, context, output):
        try:
            VALIDATOR.validate(output)
        except ValidationError:
            raise RecordError("invalid-summary") from None
        if output["input_sha256"] != context["input_sha256"] or output["previous_revision"] != context["previous_revision"]:
            raise RecordError("summary-input-mismatch")
        if output["scope"] != context["scope"] or set(output["linked_observation_ids"]) - {context["primary_id"], *context["related_ids"]} or context["primary_id"] not in output["linked_observation_ids"]:
            raise RecordError("summary-outside-scope")
        sources = {s["id"]: s for s in context["evidence"]["sources"]}
        retained = {e["source_id"] for e in context["evidence"]["excerpts"]}
        facts = [fact for name in FACT_LISTS for fact in output[name]] + [output[k] for k in ("request", "expected") if output[k] is not None]
        for fact in facts:
            if set(fact["source_ids"]) - sources.keys():
                raise RecordError("unknown-summary-source")
            if not set(fact["source_ids"]) & retained:
                raise RecordError("missing-retained-evidence")
        for fact in output["authorizations"] + output["corrections"]:
            if fact["actor"] != "user" or not any(sources[key]["kind"] == "message" for key in fact["source_ids"]):
                raise RecordError("unsupported-user-decision")
        for value in output["instructions"]:
            source = sources.get(value["source_id"])
            if source is None or set(value["evidence_ids"]) - sources.keys():
                raise RecordError("unknown-summary-source")
            if value["temporal_role"] == "historical":
                if source["temporal_role"] != "historical":
                    raise RecordError("unsupported-historical-context")
                if value["availability"] in ("selected", "read", "loaded") and not any(sources[key]["kind"] in ("runtime-evidence", "message") and sources[key]["temporal_role"] == "historical" and key in retained for key in value["evidence_ids"]):
                    raise RecordError("unsupported-historical-context")
        for key in ("request", "expected", "author"):
            if output[key] is None and key not in output["unknowns"]:
                raise RecordError("unreported-summary-gap")
        if output["unknowns"] and output["completeness"] != "partial":
            raise RecordError("unreported-summary-gap")
        if output["mode"] == "posthoc" and not output["limits"]:
            raise RecordError("unreported-summary-gap")

    def save(self, context, output, expected_revision, operation_id):
        return derived_work.save(self.records, "summary", context, output, expected_revision, operation_id,
            lambda ctx: self.prepare(ctx["primary_id"], ctx["additional_evidence"], ctx["related_ids"]), self._validate)

    def history(self, identity):
        return self.records.history(identity, "summary")

    def latest(self, identity):
        versions = self.history(identity)
        if not versions:
            return {"state": "pending", "revision": 0, "summary": None, "evidence": None}
        last = versions[-1]
        return {"state": "pending" if "reconstruction" in self.records.get(identity)["pending"] else "available", "revision": last["revision"], "sha256": last["sha256"], "summary": last["payload"]["output"], "evidence": last["payload"]["input"]["evidence"]}
