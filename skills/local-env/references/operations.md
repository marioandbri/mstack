# Operations

If a noninteractive shell cannot find a tool, check fish resolution and ~/.bun/bin
before declaring it absent. Use an already installed compatible Node through a
process-local PATH override. Keep the user's global Node selection unchanged.


## Project inspection

Follow applicable agent instructions and project conventions first. With `devenv.nix`, use the project's devenv workflow rather than bypassing it. Non-JavaScript applications still use their own runtime; Portless does not require replacing it.

Trace scripts recursively. Check composite commands, workspace orchestrators, automatic migrations, seeds, application initialization writes, and test-global setup. Resolve configuration precedence: shell, local files, runtime loaders, ORM config, test config, and command-specific overrides. Never dump these values indiscriminately.

Workspaces are canonical Git worktree roots, not the shared Git common directory or branch name. For non-Git projects use the canonical project directory. A service package can have its own Portless base name but shares its worktree's environment identity. Different branches are not proof of different data destinations.

## Portless preflight and lifecycle

Validated CLI baseline is `0.15.6`, not a claim about the latest release. Verify version, Node.js `24+`, doctor, and list before launch. Different pre-1.0 versions can have incompatible shared state. Do not use a per-project version against the shared proxy without deliberate validation.

`doctor` is read-only. In contrast, app launch can auto-start proxy, generate/trust certificates, prompt for sudo, and update hosts. Never use launch as global setup. Launch without a TTY so a proxy disappearing after preflight cannot trigger an interactive sudo/trust prompt. If the harness cannot guarantee noninteractive execution, establish a safe launch method before proceeding. Require already healthy proxy, inspect current mode/bindings and inherited settings, and block when initialization or privileged repair is needed. Use `PORTLESS_SYNC_HOSTS=0` for agent launches to avoid implicit hosts modifications; verify actual hostname resolution without changing system files. If resolution fails, report it for separate approved setup.

Inherited `PORTLESS_TAILSCALE`, `PORTLESS_FUNNEL`, `PORTLESS_NGROK`, `PORTLESS_LAN`, flags in scripts, or persisted LAN proxy configuration can expose services despite a local command. Do not launch with sharing enabled. Disable per-process sharing requests when appropriate, but never silently reconfigure an already shared proxy. Request loopback-only setup separately. Child servers should respect loopback `HOST`.

`portless run` infers base name from config and applies branch prefix in linked worktrees. `portless get <base-name>` applies the same worktree detection. Resolve from the correct package/worktree and use the actual registered base name. Do not manually add the branch twice or reconstruct protocol, suffix, or proxy port. `get` alone does not prove a route or application is healthy.

When separate checkouts collide, use helper's stable `routeBase`, optionally prefixed by a short service label. With an already Portless-integrated script, use its supported name override once or request a durable adaptation. Do not resolve collision by nesting another proxy wrapper or claiming another route.

Portless injects `PORT`, `HOST`, `PORTLESS_URL`, and HTTPS CA support into its child. It cannot configure every framework or project-specific variable. Compound scripts, delegation, env prefixes, wrapper flags, and fixed `appPort` settings need inspection. Dynamic URL variables must be set inside the child, after injection. Fish example for a verified Bun project:

```fish
# Only if dev does not already contain Portless.
env PORTLESS_SYNC_HOSTS=0 portless run fish -c 'env APP_URL="$PORTLESS_URL" bun run dev'
```

`APP_URL` is an example, not a universal variable. That wrapper can prevent framework flag auto-injection; use only after confirming the script directly honors `PORT` and `HOST`. If adaptation is needed, propose one approved script/config change, not per-run rewrites.

Resolve backend origins with `portless get` before starting dependent services. Verify CORS, OAuth callback URLs, cookies, WebSocket/HMR, and browser origins through project configuration. HTTP proxying to another Portless app must rewrite `Host`, for example Vite `changeOrigin: true`, or it can loop. Honor provided CA trust; never use `curl -k` or `NODE_TLS_REJECT_UNAUTHORIZED=0`.

## Database selection and creation

Shared servers are expected on local `3306` and `5432`; check actual published bindings. An existing Docker container with only `3306/tcp` in `docker ps` is not evidence that host port `3306` is published. Do not repair Docker/network settings or create a replacement container automatically.

### Shared SQL server startup

The user has identified existing shared containers `postgres` for PostgreSQL on `5432` and `mysql` for MySQL 8 on `3306`. These names are discovery hints, not proof of identity or ownership. Do not persist short container IDs as permanent identities; a replacement container needs fresh verification.

1. Identify which engine the task actually needs. If no SQL is needed, do not start either container. If Docker daemon is unavailable, report it; do not launch/reconfigure Docker Desktop automatically.
2. Inspect only the necessary named container, including stopped containers. Use a narrow format that excludes environment variables and secrets:

   ```fish
   # Choose only the container required by the task.
   docker inspect --format '{{.Id}} {{.Name}} {{.Config.Image}} {{.State.Status}} {{json .HostConfig.PortBindings}}' postgres
   # Alternative when the task needs MySQL:
   docker inspect --format '{{.Id}} {{.Name}} {{.Config.Image}} {{.State.Status}} {{json .HostConfig.PortBindings}}' mysql
   ```

3. Verify container name, expected engine/image, existing published host port, and approved Docker context. Resolve the full ID from this inspection. A missing or ambiguous container, mismatched engine, or missing expected binding is a blocker; do not create/recreate it or modify its ports, volumes, credentials, network, or restart policy.
4. For an existing stopped container in `exited` or `created` state, starting it is authorized when that engine is needed. Run `docker start <verified-id>` using the actual full ID, not the illustrative placeholder. Start only the needed container. Reuse one that is already running; wait with a bounded timeout for one already starting/restarting. Do not automatically restart a running or unhealthy server, unpause a paused container, or repair a dead/removing container.
5. Verify running status and available Docker healthcheck, then perform an authenticated read-only SQL readiness check with authorized project/management connection settings. Docker `running` or an open TCP port alone is not SQL readiness. If readiness fails, report sanitized diagnostics and missing credentials/permissions; do not restart or reset the shared server as recovery.
6. Report whether the container was started or reused. Starting it never grants ownership. Leave it running after task success, failure, or cleanup; never stop it to restore its earlier stopped state. Helper remains metadata-only and does not execute Docker commands.

Use SQL clients through loopback even if an existing binding listens elsewhere. The user-provided MySQL configuration publishes `3306` on all host interfaces, whereas PostgreSQL publishes `5432` on loopback. Startup permission covers these existing shared configurations, not new or widened exposure. Report non-loopback bindings as a security concern; do not silently change firewall/network configuration. An unfamiliar exposure or changed configuration requires clarification before startup.

Discover authorized credential sources from project docs and local configuration. Never infer admin users from image defaults. Use supported secret files, protected client configuration, or scoped environment injection; no secrets in command arguments, state, reports, or shell tracing. If CREATE/DROP grants are unavailable, report the exact required grant and intended server/database without printing credentials.

### Existing

Use configured local database for development tasks that accept its data. Read-only probes are allowed. Writing tests, resets, destructive migrations, or seeds default to disposable instead. If the user explicitly chooses existing for writes, explain effects and require authorization for destructive operations. The database and borrowed application remain unowned.

### Disposable

1. Generate bounded, lowercase identifier. Helper limits project slug to 20 characters, hashes canonical path to 16 hex characters, and optional run suffix to 16 characters. Result fits PostgreSQL's 63-byte identifier limit and MySQL's 64-character database limit.
2. Use distinct run suffix for simultaneous independent sessions in one workspace. Reuse base database only when its prior creation receipt, current consumers, and task compatibility are established. Existence, naming convention, and matching branch are insufficient.
3. Read server identity and check database absence before CREATE. Do not use `CREATE DATABASE IF NOT EXISTS` as ownership proof. CREATE must confirm it created a new database; if a concurrent creator wins, stop and choose a new run/name.
4. Register the confirmed creation immediately with server identity, run ID, and receipt. Partial setup failures still leave owned database available for safe cleanup. If CREATE succeeded but recording failed, report uncertain resource; never guess ownership or drop it from its prefix.
5. Respect project encoding, collation, extensions, and grants. Reuse approved roles; no new users or broad grants by default. Do not copy development/production data unless approved and sanitized.
6. Override database name only using project's loader, retaining host, port, authorized user/password, TLS options, and other query options. Parse connection URLs structurally, never regex-replace or print them. ORM test and shadow database configurations must also be isolated and recorded as separate resources before use. Helper currently records one database per run; use a separately identified run/receipt for each additional database and report all of them.
7. Re-verify actual application, migration, seed, and test targets BEFORE commands that may write. Use real configuration loaders or instrument a read-only probe through the exact client path. A SQL client aimed manually at the intended database does not prove the application uses it.
8. Apply approved project migrations and minimal fixtures. No reset/truncate/drop against preexisting databases. On failure, mark checks failed, report sanitized logs, and clean only confirmed owned resources.

Read-only identity queries, executed with authorized connection configuration:

```sql
-- PostgreSQL: connected destination
SELECT current_database(), inet_server_addr(), inet_server_port();
-- PostgreSQL cluster identity, if permitted
SELECT system_identifier FROM pg_control_system();

-- MySQL: connected destination and server identity
SELECT DATABASE(), @@hostname, @@port, @@server_uuid;
```

Server-side addresses/ports may differ from Docker's host endpoint. Verify both the resolved client loopback destination and returned server/database identity. If PostgreSQL identity query is not permitted, use another authorized stable server/cluster identity backed by evidence, or report the missing permission. Host/port alone cannot distinguish a replaced server. Avoid grants changes to make the probe pass.

## Ownership, reuse, and closing

State is an agent-maintained ledger, not a security boundary or proof by itself. A valid receipt must come from confirmed creation by this run, not from observing an existing name. Helper checks metadata and fresh destination equality, but cannot attest SQL execution or consumer absence.

Concurrent consumers must not lose their services/database. Reuse another run's environment as borrowed, record its owner state location in the handoff/report, and arrange a lease or explicit consumer coordination before owner cleanup. If consumer tracking is unavailable, do not claim safe automatic cleanup. For independent writes, choose a disposable run instead of borrowing.

For owned processes, record PID and OS start token such as sanitized `ps -o lstart= -p <pid>`. Recheck both and working-directory/launcher association before signaling. PID alone is unsafe because it can be reused. Do not store full command lines containing secrets. Prefer sending Ctrl+C to the owned harness session so Portless can close its descendants and unregister its route. Wait for exit; never use global `pkill` or `killall`. Escalation applies only to revalidated owned descendants after graceful stop fails.

Drop eligibility requires all of:

- Recorded disposable mode, exact database/server target, and this run's confirmed creation receipt.
- Fresh SQL evidence matching engine, configured loopback host/port, database name, and stable server identity.
- No active application, test, migration, or borrowed consumer using the database.
- Rechecked creation evidence if the database was removed/recreated externally. Lost continuity or changed server identity means stop, not adopt the new database.

Database names alone cannot detect an externally recreated database. When no server-side identity marker exists, preserve creation continuity through controlled ownership and stop on suspected external changes. Do not advertise metadata validation as a guarantee against arbitrary external database replacement.

Use engine-safe identifier quoting and the authorized client to drop this exact database. Avoid broad termination of SQL sessions. Verify disappearance, own process exit, and own route removal; leave shared proxy and SQL containers running. If process exit leaves stale proxy state, report the exact route; no automatic global cleanup commands.

Mark state `closing` before cleanup and `closed` only after verification. Keep sanitized receipts for investigation. Locked state, missing state, changed process identity, or uncertain creation all fail closed. Report leftover resources and precise next action.

## Acceptance

Run actual project with two simultaneous workspaces. Verify URLs differ and return each workspace's expected application. Create independent disposable databases on the same authorized shared server; apply project migrations/fixtures and write distinct markers through each app/test client. Confirm neither reads the other's marker. Close workspace A, prove its owned process and database are gone, then repeat B's HTTP and SQL smoke check. B, shared SQL server, and shared proxy must remain healthy.

Unit tests or HTTP-only fixtures do not satisfy SQL isolation acceptance. Record skipped checks and missing credentials separately.

## Technical sources

- [Portless 0.15.6 README](https://cdn.jsdelivr.net/npm/portless@0.15.6/README.md), pinned behavior reference.
- [Portless commands](https://portless.sh/commands), supplementary live documentation; check against validated version.
- [PostgreSQL system information functions](https://www.postgresql.org/docs/current/functions-info.html).
- [PostgreSQL control data functions](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-CONTROL).
- [MySQL server system variables](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_server_uuid).
