"""Check evidence identity and proposed labels without running an embedding model."""
import argparse
import json
from pathlib import Path

from prepare import HERE, build_labels, pointer, sha


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-snapshots", type=Path, required=True)
    args = parser.parse_args()
    manifest, sources, labels = (read(name) for name in ("manifest.json", "sources.json", "labels.json"))
    for category in ("inputs", "outputs"):
        for name, expected in manifest[category].items():
            assert sha(HERE / name) == expected, name
    records, queries = read("records.json"), read("queries.json")
    assert records["embedding_input_fields"] == ["text"]
    assert labels == build_labels(records["records"], queries)
    assert not labels["user_approved"] and not labels["frozen_for_execution"]
    assert manifest["new_embedding_calls"] == manifest["new_hosted_model_calls"] == 0
    assert manifest["status"] == "prepared-not-executed"
    for identity, source in sources["sources"].items():
        suffix = Path(source["path"]).suffix
        snapshot = args.private_snapshots / (identity + suffix)
        assert sha(snapshot) == source["sha256"], identity
        source["snapshot"] = snapshot
    proved = set()
    for item in sources["evidence"]:
        snapshot = sources["sources"][item["source_id"]]["snapshot"]
        if "json_pointer" in item["location"]:
            value = pointer(json.loads(snapshot.read_text()), item["location"]["json_pointer"])
            assert value == item["excerpt"], item["record_id"]
        else:
            assert item["excerpt"] in snapshot.read_text(), item["record_id"]
            assert item["location"]["exact_quote"] == item["excerpt"]
        proved.add(item["record_id"])
    assert proved == {row["id"] for row in records["records"]}
    assert all(row["source_session"] is None for row in records["records"])
    assert len(records["records"]) == 33 and len(sources["sources"]) == 20
    scenarios = [row for row in records["records"] if row["kind"] == "prepared-scenario"]
    assert {row["id"] for row in scenarios} == {"R31", "R32", "R33"}
    assert {row["source"] for row in scenarios} == {"S17", "S18", "S19"}
    assert all(row["execution_status"] == "not-executed" and row["evidence_scope"] in {"governing-procedure-only", "procedure-and-review-only"}
               and row["origin"] == "user-requested-scenario" and row["harness"] is None for row in scenarios)
    assert manifest["counts"]["unexecuted_scenarios"] == len(scenarios) == 3
    assert len(labels["queries"]) == 52 and len(labels["held_out_for_review"]) == 5
    assert {row["case_id"] for row in labels["held_out_for_review"]} == {"V01", "V02", "V03", "V04", "V06"}
    assert len(labels["excluded_from_comparison"]) == 1
    excluded = labels["excluded_from_comparison"][0]
    assert excluded["case_id"] == "V05" and excluded["judgment_status"] == "out-of-scope"
    assert sum(row["expected_no_match"] for row in labels["queries"]) == 6
    scope_controls = [row for row in labels["queries"] if row["case_id"] == "C16"]
    assert all(row["candidate_ids"] == [] and row["grades"] == {} for row in scope_controls)
    semantic_absence = [row for row in labels["queries"] if row["case_id"] in ("C17", "C18")]
    assert all(len(row["candidate_ids"]) == len(records["records"]) and set(row["grades"].values()) == {0} for row in semantic_absence)
    assert all(row["grades"] is None and not row["include_in_scoring"] for row in labels["held_out_for_review"] + labels["excluded_from_comparison"])
    for case in queries["cases"]:
        versions = [row for row in labels["queries"] if row["case_id"] == case["id"]]
        assert {row["language"] for row in versions} == {"es", "en"}
        assert versions[0]["grades"] == versions[1]["grades"]
        assert versions[0].get("workflow_expectation") == versions[1].get("workflow_expectation")
    workflow_cases = [row for row in queries["cases"] if "workflow_expectation" in row]
    assert {row["id"] for row in workflow_cases} == {"C19", "C20", "C21", "C22", "C23", "C24", "C25", "C26"}
    assert {row["workflow_expectation"]["label"] for row in workflow_cases} == set(queries["workflow_label_definitions"])
    assert labels["workflow_label_definitions"] == queries["workflow_label_definitions"]
    for omitted, control in (("C19", "C20"), ("C21", "C22"), ("C23", "C24")):
        pair = [row for row in workflow_cases if row["id"] in (omitted, control)]
        assert len(pair) == 2 and pair[0]["direct"] == pair[1]["direct"]
        assert pair[0]["workflow_expectation"]["label"] != pair[1]["workflow_expectation"]["label"]
    feedback = read("review-feedback.json")
    assert not feedback["user_approved_relevance_labels"]
    assert {row["case_id"] for row in feedback["decisions"]} == {"V02", "V04", "V05", "V06"}
    assert {row["review_feedback"] for row in queries["review_cases"] if "review_feedback" in row} == {row["id"] for row in feedback["decisions"]}
    print("PASS 33 sourced records, 20 frozen sources/quotes/pointers, 52 bilingual proposed judgments, 3 unexecuted workflow scenarios, 8 distinct behavior expectations, 6 no-match queries, 5 ungraded review cases and 1 excluded historical control; no embeddings executed. Relevance and behavioral expectations remain provisional.")


if __name__ == "__main__":
    main()
