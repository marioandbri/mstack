"""Small decision references shared by capture, classification and review."""
import json


def review_decisions(db, identity, *, history=False):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='review_versions'").fetchone():
        return []
    rows = db.execute("""SELECT r.*,r.revision=(SELECT MAX(revision) FROM review_versions WHERE review_id=r.review_id) AS current
        FROM review_versions r WHERE EXISTS (
          SELECT 1 FROM json_each(r.payload,'$.record.opportunities') o,
                        json_each(o.value,'$.observationIds') i WHERE i.value=?)
        ORDER BY r.review_id,r.revision""", (identity,))
    result = []
    for row in rows:
        if not history and not row["current"]:
            continue
        payload = json.loads(row["payload"])
        for item in payload["record"]["opportunities"]:
            if identity in item["observationIds"]:
                result.append({"kind": "review", "record_id": identity, "review_id": row["review_id"], "revision": row["revision"], "opportunity_id": item["id"],
                    "domain": payload["options"]["decision_domains"].get(item["id"], "unknown"), "decision": item["decision"], "source": payload["options"]["decision_sources"].get(item["id"]),
                    "sha256": row["payload_sha256"], "active": bool(row["current"])})
    return result
