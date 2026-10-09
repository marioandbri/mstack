# Environment diagnostics

Read only the section matching a reported failure. These notes relocate facts
from Mario's former global instructions. They do not authorize reconfiguration,
login, restart or a change in network exposure. Check the installed version,
actual symptom and current primary source before applying a version-specific fix.
No recurrence count is established by copies of the same global note.

## Pi MCP configuration and sign-in

For missing MCP tools or sign-in failures, distinguish configuration discovery
from remote-server OAuth and provider authentication. Pi 1.0.0's local mcp help
and bundled docs/mcp.md confirm user configuration at ~/.pi/agent/mcp.json and
trusted-project configuration at .pi/mcp.json. Project entries can override the
same server name. Inspect only the affected sanitized entry, never token files.

The previously used Linear entry was {"url":"https://mcp.linear.app/mcp"}.
Use pi mcp list for state and errors. If the named server needs sign-in, arrange
user login with pi mcp login <server>; use /reload after changing configuration
outside an existing session. OAuth credentials belong to the server identity and
are separate from older adapter storage. Do not copy or print those credentials.

The old global said auth: oauth was invalid and auth selected a provider
credential. That statement is version-specific, not a general MCP schema rule.
Check the current Pi schema instead of adding or deleting auth based on this note.
Local version/source check for this relocation: 2026-10-09, Pi 1.0.0, bundled
@earendil-works/pi-coding-agent docs/mcp.md and pi mcp --help. No live sign-in was tested.

## Bitbucket repository permissions

For a permission query failing despite working PR reads, distinguish endpoint,
identity, scope and repository access. The authenticated user's effective
repository-permission endpoint is GET /2.0/user/workspaces/{workspace}/permissions/repositories.
It reports effective access in that workspace; it is not the workspace-admin
permissions endpoint. Verify required scopes and the actual response rather than
inferring a missing account permission from a legacy endpoint's 404.

[Official endpoint documentation](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-user-workspaces-workspace-permissions-repositories-get)
was checked for this relocation on 2026-10-09. The legacy endpoint failure is a
historical observation, not a newly reproduced bug. Use the configured Bitbucket
client for the task; never expose its auth profile or tokens.

## T3 remote-access failures

Check the host, selected route and server before changing configuration. A local
LAN success does not demonstrate the managed relay route. A saved CLI login or
exposure preference does not prove a running listener or live reachability.
Follow the installed version and [official remote-access guide](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md),
checked on 2026-10-09; pairing and command names can change between versions.

- For sleep-related failures on this Mac, compare the incident with pmset -g log.
  Distinguish idle sleep, lid-triggered Clamshell Sleep, screen lock and logout.
  An idle-sleep assertion does not by itself establish operation with the lid
  closed. Correlate Touch ID and sleep events instead of assuming causality.
- Identify the route actually used on the remote client. Check the relevant
  desktop connection, listener and T3-owned tunnel status. The old investigation
  used /ready and /config; verify availability on the installed version and
  redact responses before retaining evidence.
- For Tailscale, verify both clients are connected to the intended tailnet and
  inspect tailscale status --json and tailscale serve status without publishing
  private peers or addresses. Saved desktop settings alone are insufficient.
- A previous incident associated Cloudflare 403/error 1010 with a User-Agent.
  Treat it as a hypothesis to reproduce for the current request, not the default
  cause of every 403. Distinguish it from relay failure; keep a sanitized Ray ID
  and exact error when reporting it. Do not change firewall or relay policy from
  this note alone.

These observations are useful diagnostic distinctions, not proof that the host's
current remote-access configuration is correct. No live T3 connection or sleep
experiment was performed in this relocation.
