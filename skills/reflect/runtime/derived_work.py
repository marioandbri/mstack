"""Rebuildable status of derived work; accepted versions remain authoritative."""
from datetime import datetime, timezone


def states(db, identity):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='derived_work' AND type='table'").fetchone():
        return {}
    return {row["kind"]: dict(row) for row in db.execute("SELECT * FROM derived_work WHERE record_id=?", (identity,))}


def mark(db, identity, kind, status, input_sha256, operation_id, error_code=None):
    db.execute("""CREATE TABLE IF NOT EXISTS derived_work(
        record_id TEXT NOT NULL REFERENCES originals(id), kind TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('ready','pending')), input_sha256 TEXT NOT NULL,
        operation_id TEXT NOT NULL, error_code TEXT, updated_at TEXT NOT NULL,
        PRIMARY KEY(record_id,kind)) STRICT""")
    db.execute("INSERT OR REPLACE INTO derived_work VALUES(?,?,?,?,?,?,?)", (identity, kind, status, input_sha256, operation_id, error_code, datetime.now(timezone.utc).isoformat()))


def save(records, kind, context, output, expected_revision, operation_id, fresh, validate):
    """Validate outside the lock; publish a version and its status atomically."""
    from records import RecordError
    if (not isinstance(context, dict) or context.get("project") != records.project or
            not isinstance(context.get("primary_id"), str) or not isinstance(context.get("input_sha256"), str)):
        raise RecordError("derived-input-outside-scope")
    if type(expected_revision) is not int or expected_revision < 0:
        raise RecordError("invalid-revision")
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise RecordError("missing-operation")
    failure = None
    try:
        if output is None:
            raise RecordError("provider-unavailable")
        validate(context, output)
    except RecordError as error:
        failure = error
    identity = context["primary_id"]
    with records._transaction() as db:
        payload = {"input": context, "output": output}
        if db.execute("SELECT 1 FROM versions WHERE operation_id=?", (operation_id,)).fetchone():
            return records._append(db, kind, identity, expected_revision, payload, operation_id)
        if not db.execute("SELECT 1 FROM originals WHERE id=?", (identity,)).fetchone():
            raise RecordError("not-found")
        revision = db.execute("SELECT COALESCE(MAX(revision),0) FROM versions WHERE kind=? AND record_id=?", (kind, identity)).fetchone()[0]
        if revision != expected_revision:
            raise RecordError("revision-conflict")
        try:
            if fresh(context) != context:
                raise RecordError("derived-input-stale")
        except (KeyError, TypeError):
            raise RecordError("invalid-derived-context") from None
        if failure:
            mark(db, identity, kind, "pending", context["input_sha256"], operation_id, str(failure))
        else:
            result = records._append(db, kind, identity, expected_revision, payload, operation_id)
            mark(db, identity, kind, "ready", context["input_sha256"], operation_id)
    if failure:
        raise failure
    return result
