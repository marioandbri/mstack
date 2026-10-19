# State and helpers

Bundled helper uses Node.js standard library only. It only invokes read-only Git inspection for workspace identity. It never launches application services, signals processes, executes SQL, installs tools, or changes proxy configuration. Validate input before saving; unknown fields are rejected rather than silently retaining secrets.

## Commands

Set `helper` to the absolute installed skill path. For this canonical checkout:

```fish
set helper ~/personal/engineering-skills/skills/local-env/scripts/state.mjs
node $helper identity "$PWD" my_project
# Add session only when an independent same-workspace database is needed:
node $helper identity "$PWD" my_project run_01

# metadata.json must follow schema below and contain no secrets.
node $helper save < metadata.json
node $helper read "$PWD" my_project run_01
# observed.json comes from fresh, authorized SQL probes, not a copy of state.
node $helper check-db "$PWD" my_project run_01 < observed.json
```

Use canonical project/worktree root for non-Git projects. Identity discovers Git worktree root even from a package subdirectory. Symlink aliases to one workspace produce the same hash; different paths produce different hashes even on the same branch. Moving a checkout changes identity; do not adopt old state automatically.

Default state path is `$XDG_STATE_HOME/local-env/<workspace_hash>/<run_id>/state.json`, falling back to `~/.local/state/local-env/...`. Outside repository and never tracked. Saving under the current workspace is rejected, including redirected state roots resolving into that workspace. Only this subtree is created; existing parent configuration is not rewritten. Helper creates directories with `0700` and files with `0600`, rejects symlinked/unowned/nonprivate state descendants, writes atomically, and serializes saves with an exclusive lock. `read` creates nothing.

`save` accepts complete metadata on stdin, checks immutable identity/database target and optimistic revision, increments revision, and returns `{path, state}`. Initial revision is `0`; later saves use last returned/read revision. On contention, reload and reconcile. Never blindly retry an old write. Unknown fields, credential-bearing URLs, invalid ownership, and incomplete readiness fail closed. Parser errors do not echo input.

Lock left by interrupted writer is a blocker. Verify no live writer owns it before any manual repair; never steal stale-looking locks automatically. Helper does not automatically detect liveness, scan all runs, manage leases, or garbage-collect state. Before launch, inspect candidate runs in this workspace's private directory and validate each against actual resources. No state means no cleanup authority.

## Metadata schema

Replace illustrative identity and paths with actual `identity` output. This template is not executable configuration:

```json
{
  "schemaVersion": 1,
  "workspace": "/absolute/project/worktree",
  "workspaceHash": "0123456789abcdef",
  "project": "my_project",
  "runId": "run_01",
  "revision": 0,
  "status": "preparing",
  "services": [
    {
      "baseName": "my-project-0123456789abcdef",
      "url": null,
      "pid": null,
      "startToken": null,
      "ownedBy": null,
      "logPath": "/absolute/private/logs/web.log"
    }
  ],
  "database": {
    "mode": "disposable",
    "engine": "postgresql",
    "host": "127.0.0.1",
    "port": 5432,
    "name": "agent_my_project_0123456789abcdef_run_01",
    "serverId": null,
    "createdBy": null,
    "creationReceipt": null
  },
  "checks": {
    "http": "pending",
    "database": "pending",
    "smoke": "pending"
  },
  "logsDirectory": "/absolute/private/logs"
}
```

- `project` is helper's normalized slug. `runId` uses 1-16 lowercase letters, digits, or underscores and starts with a letter/digit. Prefer a stable task/session ID. Different concurrent tasks use different IDs; retry/resume uses existing ID.
- `status` is `preparing`, `ready`, `closing`, or `closed`. Closed runs cannot be reopened; create a new ID. Readiness requires SQL/smoke `passed` plus every service URL and HTTP `passed`. For SQL-only tasks, services are empty and HTTP remains `pending`, reported as not applicable.
- `baseName` is the registered Portless base without a manually prepended branch. `url` is resolved HTTP origin only, no credentials/query/fragment/path. Verify its app identity separately; helper cannot attest routing or restrict every custom local TLD.
- `pid` and sanitized OS `startToken` identify actual launcher. Set `ownedBy` only after this run starts it and verifies association. Borrowed processes use `ownedBy: null`; never inherit another run's ownership. Preserve harness session handle in the execution handoff/report, not arbitrary secret-bearing metadata.
- `logPath` and `logsDirectory` are absolute paths. Create private log storage separately. Filter/redact logs before displaying them; filenames must not contain credentials. Helper validates paths but does not inspect file contents.
- `database` is null when task needs no SQL. Keep SQL check `pending` and report not applicable. Do not create a database just to satisfy metadata. At least one HTTP service or SQL database is required for `ready`.
- `database.engine` is `postgresql` or `mysql`; ports are `5432` or `3306` respectively. Host must be explicit loopback. Existing identifiers outside helper's ASCII letter/digit/underscore/hyphen, 63-character subset are blocked by this helper; do not rename a preexisting database to make validation pass.
- `database.serverId` comes from authorized stable server/cluster identity probe. Record configured client endpoint separately from container's reported internal address.
- `createdBy` and `creationReceipt` stay null for `existing` and for any preexisting/borrowed database. Disposable names must match helper's base or run-suffixed name, but matching never establishes ownership.

Only after successful CREATE confirmed a newly created database by this run, update `serverId`, `createdBy` and receipt, then immediately save:

```json
{
  "createdBy": "run_01",
  "creationReceipt": {
    "existedBefore": false,
    "createdAt": "2026-01-01T00:00:00.000Z",
    "serverId": "1234567890123456789"
  }
}
```

This is a partial example, merge into complete `database` object. Timestamp is actual creation time. Receipt is agent-attested evidence, not a signed SQL proof. Never fabricate it from an existing database. Once recorded, receipt and non-null SQL server identity are immutable. Database engine/endpoint/name/mode, run identity, and log directory cannot change within a run. Use another run for a different target.

## Cleanup eligibility

`check-db` reads state and accepts only fresh observed target on stdin:

```json
{
  "engine": "postgresql",
  "host": "127.0.0.1",
  "port": 5432,
  "name": "agent_my_project_0123456789abcdef_run_01",
  "serverId": "1234567890123456789"
}
```

Success means matching metadata and recorded ownership only. It does NOT authorize DROP by itself. Recheck process ownership, database creation continuity, and absence of active/borrowed consumers as required by operations. Helper neither contacts SQL server nor drops anything. Copying state into observed input defeats the check and is prohibited.

On partial cleanup failure, retain `closing` state and report remaining resources. Do not erase receipt or claim closed merely because helper validated metadata.
