import { expect, test } from "bun:test";
import { closeSync, mkdirSync, mkdtempSync, openSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { identity } from "../skills/local-env/scripts/state.mjs";

// Opt-in: uses an already healthy local shared proxy, never initializes it.
// HTTP/workspace isolation only. Does not claim SQL/migration acceptance.
test.skipIf(process.env.LOCAL_ENV_HTTP_E2E !== "1")("two real Portless workspaces survive independent HTTP cleanup", async () => {
  const env = { ...process.env, CI: "1", PORTLESS: "1", PORTLESS_SYNC_HOSTS: "0", PORTLESS_TAILSCALE: "0", PORTLESS_FUNNEL: "0", PORTLESS_NGROK: "0", PORTLESS_LAN: "0" };
  delete env.PORTLESS_APP_PORT;
  const version = Bun.spawnSync(["portless", "--version"], { env });
  expect(version.exitCode).toBe(0);
  expect(version.stdout.toString().trim()).toBe("0.15.6");
  const doctor = Bun.spawnSync(["portless", "doctor"], { env });
  expect(doctor.exitCode).toBe(0);
  expect(doctor.stdout.toString()).toContain("Proxy is responding");
  expect(doctor.stdout.toString()).toMatch(/^Mode: HTTPS?, \.localhost$/m);

  const root = mkdtempSync(join(tmpdir(), "local-env-http-e2e-"));
  const jobs: ReturnType<typeof Bun.spawn>[] = [];
  const descriptors: number[] = [];
  const workspaces = [join(root, "checkout-a"), join(root, "checkout-b")];
  async function stop(job: ReturnType<typeof Bun.spawn>) {
    if (job.exitCode !== null) return;
    job.kill("SIGINT");
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      await Promise.race([job.exited, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("Owned fixture failed graceful shutdown")), 10000); })]);
    } finally { clearTimeout(timer); }
  }
  try {
    for (const workspace of workspaces) {
      mkdirSync(workspace);
      expect(Bun.spawnSync(["git", "init", "--quiet", workspace]).exitCode).toBe(0);
      writeFileSync(join(workspace, "package.json"), JSON.stringify({ name: "same-project", scripts: { dev: "node server.mjs" } }));
      writeFileSync(join(workspace, "server.mjs"), `import http from "node:http";
const server = http.createServer((req, res) => {
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify({ workspace: process.cwd(), url: process.env.PORTLESS_URL }));
});
server.listen(Number(process.env.PORT), process.env.HOST);
process.on("SIGINT", () => server.close(() => process.exit(0)));
process.on("SIGTERM", () => server.close(() => process.exit(0)));
`);
      const fd = openSync(join(root, `${identity(workspace, "e2e").workspaceHash}.log`), "w", 0o600);
      descriptors.push(fd);
      jobs.push(Bun.spawn(["portless", "run", "--name", identity(workspace, "e2e").routeBase, "bun", "run", "dev"], { cwd: workspace, env, stdout: fd, stderr: fd }));
    }
    const urls: string[] = [];
    async function response(index: number) {
      const url = urls[index]!;
      const result = await fetch(url, { signal: AbortSignal.timeout(2000) });
      expect(result.ok).toBeTrue();
      const body = await result.json() as { workspace: string; url: string };
      expect(body.workspace).toBe(identity(workspaces[index]!, "e2e").workspace);
      expect(body.url).toBe(url);
    }
    for (let index = 0; index < workspaces.length; index++) {
      const workspace = workspaces[index]!;
      const get = Bun.spawnSync(["portless", "get", identity(workspace, "e2e").routeBase], { cwd: workspace, env });
      expect(get.exitCode).toBe(0);
      urls.push(get.stdout.toString().trim());
      let ready = false;
      for (let attempt = 0; attempt < 80; attempt++) {
        if (jobs[index]!.exitCode !== null) throw new Error("Owned Portless fixture exited before readiness");
        try { await response(index); ready = true; break; } catch { await Bun.sleep(100); }
      }
      expect(ready).toBeTrue();
    }
    expect(urls[0]).not.toBe(urls[1]);
    await stop(jobs[0]!);
    await response(1);
    const list = Bun.spawnSync(["portless", "list"], { env });
    expect(list.exitCode).toBe(0);
    expect(list.stdout.toString()).not.toContain(identity(workspaces[0]!, "e2e").routeBase);
    expect(list.stdout.toString()).toContain(identity(workspaces[1]!, "e2e").routeBase);
    const after = Bun.spawnSync(["portless", "doctor"], { env });
    expect(after.exitCode).toBe(0);
    expect(after.stdout.toString()).toContain("Proxy is responding");
  } finally {
    const cleanup = await Promise.allSettled(jobs.map(stop));
    for (const fd of descriptors) closeSync(fd);
    if (cleanup.some((result) => result.status === "rejected")) throw new Error(`Owned fixture cleanup failed; logs retained at ${root}`);
    rmSync(root, { recursive: true, force: true });
  }
}, 60000);
