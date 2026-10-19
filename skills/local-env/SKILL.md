---
name: local-env
description: Prepares, starts, verifies, reuses, and closes isolated local environments using Portless for application HTTP and existing Docker SQL servers for existing or disposable databases. Use when running an application, integration/E2E tests, preparing a test database, or diagnosing local services. Do not use for tasks that need no running services.
---

# Local environment

Use project runtimes and scripts. Reuse shared MySQL on loopback port `3306` and PostgreSQL on `5432`; verify their actual availability. Portless routes HTTP only, never SQL.

Read [operations](references/operations.md) before starting services or writing SQL. Read [state and helpers](references/state.md) before recording resources or checking cleanup eligibility. Resolve bundled paths relative to this skill directory, not the target project.

## Safety boundaries

- Inspect before modifying. Do not guess containers, admin users, passwords, or SQL grants.
- Use globally validated Portless `0.15.6` with Node.js `24+`. Report absent or mismatched versions; never install or update it during a task.
- Global proxy, CA trust, and network setup need separate approval. Do not invoke commands that might auto-elevate. If proxy is absent or unhealthy, report the exact blocker before launch.
- Reuse healthy shared proxy configuration, including already configured HTTP. Do not disable TLS validation or change TLS mode to get past a failure.
- No public tunnels, new LAN exposure, global network changes, container creation, shared container shutdown, or volume deletion by default. Starting a verified, needed, existing shared SQL container is allowed with its already authorized configuration; it remains shared, not owned.
- Never automatically use `--force`, `portless clean`, `portless prune`, or `portless proxy stop`. No broad process kills or name-prefix-based database drops.
- Never print credentials, connection strings containing secrets, full process environments, or unsanitized configuration/logs. State stores metadata only.

## Workflow

1. **Inspect.** Read governing repository docs, workspace layout, `package.json` or equivalent runtime manifest, `portless.json` and package Portless settings, env examples, migration/seed/test scripts, and ignored local overrides. Identify necessary services and effective configuration loaders.
2. **Preflight.** Run these read-only checks:

   ```fish
   portless --version
   portless doctor
   portless list
   ```

   Confirm healthy, loopback-only proxy with no inherited sharing settings. Inspect shared SQL availability without revealing container secrets. If needed shared `postgres` or `mysql` container is stopped, verify its identity/image/port bindings and start only that existing container with `docker start <verified-id>`. Wait for SQL readiness; never restart a running/unhealthy server. Missing containers, bindings, credentials, or grants are blockers, not invitations to invent replacements.
3. **Identify and reuse.** Resolve canonical workspace and run ID. Read existing state before launch. Reuse only when workspace, SQL destination, process identity, expected HTTP response, and task compatibility match. Borrowed resources stay unowned. Independent checkouts with colliding base names use a stable workspace hash. Linked worktrees keep Portless's branch prefix.
4. **Choose SQL mode when needed.** If task needs no database, skip SQL setup and report it as not applicable. `existing` uses configured local development database; no automatic reset, truncation, or destructive changes. Prefer `disposable` for migrations, seeds, writing tests, or concurrent independent tasks. Use `agent_<project>_<workspace_hash>`, with run suffix for extra isolation. Create only with authorized credentials after proving absence. A name collision does not grant ownership.
5. **Verify targets before writes.** Resolve effective application AND migration/seed/test connections through their real loaders. Compare engine, host, port, database, and SQL server identity using read-only SQL. Dedicated test databases and shadow databases count too. If any destination cannot be established, stop before any write or migration. Override only database target; preserve authorized auth and other options.
6. **Configure once, override per run.** Respect injected `PORT`/`HOST`; reject hardcoded ports and unsafe startup hooks. Map `PORTLESS_URL` inside child process to project URL variables. Resolve other HTTP services with `portless get`. Prefer process overrides; local files must be ignored and must not overwrite other runs. Durable project adaptation requires approval, not repeated automatic edits.
7. **Start exactly once.** From the relevant workspace/package, choose one alternative:

   ```fish
   # dev does NOT already wrap Portless:
   env PORTLESS_SYNC_HOSTS=0 portless run bun run dev
   # dev ALREADY wraps Portless, instead:
   env PORTLESS_SYNC_HOSTS=0 bun run dev
   # Resolve registered base name from this same worktree:
   portless get nombre-base
   ```

   Substitute the project's actual runtime and script. For a collision, use `portless run --name <base-with-workspace-hash> <command>`. Do not double-wrap nested scripts. Record owned process identity and log location immediately. Use a harness-tracked long-lived job; no fire-and-forget process without ownership evidence.
8. **Check and report.** Verify returned URL serves expected application, selected SQL database is reachable, and a project-specific smoke test passes. Starting a process or resolving a URL is not readiness. Record checks and update private state. For database-only tasks, report HTTP as not applicable.
9. **Close owned resources only.** Read current state, verify PID/start token and process/workspace association, stop this run's owned launcher gracefully, and wait for its tree to exit. Borrowed services remain running. Recheck SQL server and database against creation receipt, ensure no remaining consumers, then drop only this run's disposable database. On uncertainty, leave resource intact and report it. Mark closed only after cleanup is verified. Shared SQL containers stay running even if this run started them.

## Output contract

Every execution reports:

- Run ID and canonical workspace.
- Verified application URLs, or not applicable for SQL-only tasks.
- SQL mode, engine, database name, and ownership without credentials, or not applicable.
- HTTP, SQL, and smoke check results, including blockers or skipped checks.
- State path and sanitized log location.
- Exact run-specific close instructions; borrowed resources excluded.

Do not claim full isolation acceptance without checking two simultaneous workspaces, distinct verified URLs, independent disposable databases, and cleanup of one while the other still passes HTTP and SQL checks.
