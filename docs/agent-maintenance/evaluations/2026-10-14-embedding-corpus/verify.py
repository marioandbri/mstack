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
    assert len(labels["queries"]) == 36 and len(labels["held_out_for_review"]) == 6
    assert sum(row["expected_no_match"] for row in labels["queries"]) == 6
    scope_controls = [row for row in labels["queries"] if row["case_id"] == "C16"]
    assert all(row["candidate_ids"] == [] and row["grades"] == {} for row in scope_controls)
    semantic_absence = [row for row in labels["queries"] if row["case_id"] in ("C17", "C18")]
    assert all(len(row["candidate_ids"]) == 30 and set(row["grades"].values()) == {0} for row in semantic_absence)
    assert all(row["grades"] is None and not row["include_in_scoring"] for row in labels["held_out_for_review"])
    for case in queries["cases"]:
        versions = [row for row in labels["queries"] if row["case_id"] == case["id"]]
        assert {row["language"] for row in versions} == {"es", "en"}
        assert versions[0]["grades"] == versions[1]["grades"]
    print("PASS 30 sourced records, 16 frozen sources/quotes/pointers, 36 bilingual proposed judgments, 6 no-match queries and 6 ungraded review cases; no embeddings executed. Semantic relevance remains provisional.")


if __name__ == "__main__":
    main()
