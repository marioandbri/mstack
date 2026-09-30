import { afterEach, describe, expect, test } from "bun:test";
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { checkOwnedDatabase, identity, validateState } from "../skills/local-env/scripts/state.mjs";

const repository = resolve(import.meta.dir, "..");
const helper = join(repository, "skills/local-env/scripts/state.mjs");
const roots: string[] = [];
afterEach(() => {
  for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true });
});
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "local-env-"));
  roots.push(root);
  const workspace = join(root, "workspace");
  mkdirSync(workspace);
  const id = identity(workspace, "My Project", "run_01");
  const state = {
    schemaVersion: 1, workspace: id.workspace, workspaceHash: id.workspaceHash, project: id.project,
    runId: "run_01", revision: 0, status: "preparing",
    services: [{ baseName: id.routeBase, url: null, pid: null, startToken: null, ownedBy: null, logPath: join(root, "logs/web.log") }],
    database: { mode: "disposable", engine: "postgresql", host: "127.0.0.1", port: 5432, name: id.databaseName, serverId: null, createdBy: null, creationReceipt: null },
    checks: { http: "pending", database: "pending", smoke: "pending" }, logsDirectory: join(root, "logs"),
  };
  return { root, workspace, state };
}
function run(root: string, args: string[], input?: unknown) {
  return Bun.spawnSync(["node", helper, ...args], {
    env: { ...process.env, XDG_STATE_HOME: join(root, "state") },
    stdin: input === undefined ? "ignore" : Buffer.from(typeof input === "string" ? input : JSON.stringify(input)),
    stdout: "pipe", stderr: "pipe",
  });
}
function save(root: string, state: unknown) {
  const result = run(root, ["save"], state);
  expect(result.stderr.toString()).toBe("");
  expect(result.exitCode).toBe(0);
  return JSON.parse(result.stdout.toString());
}
function owned(state: any) {
  state.database.serverId = "123456789";
  state.database.createdBy = state.runId;
  state.database.creationReceipt = { existedBefore: false, createdAt: "2026-01-01T00:00:00.000Z", serverId: "123456789" };
  return state;
}

describe("local-env metadata helper", () => {
  test("canonical identity is stable, symlink-aware, bounded, and checkout-specific", () => {
    const { root, workspace } = fixture();
    const alias = join(root, "alias");
    symlinkSync(workspace, alias);
    expect(identity(alias, "My Project")).toEqual(identity(workspace, "My Project"));
    const second = join(root, "other");
    mkdirSync(second);
    expect(identity(second, "My Project").workspaceHash).not.toBe(identity(workspace, "My Project").workspaceHash);
    expect(identity(workspace, "x".repeat(100), "r".repeat(16)).databaseName.length).toBeLessThanOrEqual(63);
    expect(() => identity(workspace, "project", "../escape")).toThrow("Invalid run ID");
    expect(() => identity(workspace, "!!!")).toThrow("ASCII");
  });

  test("Git identity uses worktree root from nested package and ignores ambient Git redirection", () => {
    const { root, workspace } = fixture();
    expect(Bun.spawnSync(["git", "init", "--quiet", workspace]).exitCode).toBe(0);
    const nested = join(workspace, "apps", "web");
    mkdirSync(nested, { recursive: true });
    expect(identity(nested, "project").workspace).toBe(identity(workspace, "project").workspace);
    const other = join(root, "other-git");
    mkdirSync(other);
    expect(Bun.spawnSync(["git", "init", "--quiet", other]).exitCode).toBe(0);
    const redirected = Bun.spawnSync(["node", helper, "identity", nested, "project"], {
      env: { ...process.env, GIT_DIR: join(other, ".git"), GIT_WORK_TREE: other },
    });
    expect(redirected.exitCode).toBe(0);
    expect(JSON.parse(redirected.stdout.toString()).workspace).toBe(identity(workspace, "project").workspace);
  });

  test("private atomic state saves reuse run, reject stale revisions and immutable target changes", () => {
    const { root, workspace, state } = fixture();
    const first = save(root, state);
    expect(lstatSync(first.path).mode & 0o777).toBe(0o600);
    expect(lstatSync(resolve(first.path, "..")).mode & 0o777).toBe(0o700);
    expect(first.state.revision).toBe(1);
    const updated = save(root, { ...first.state, checks: { ...state.checks, smoke: "failed" } });
    expect(updated.path).toBe(first.path);
    expect(updated.state.revision).toBe(2);
    expect(run(root, ["save"], first.state).stderr.toString()).toContain("Stale state revision");
    const changed = structuredClone(updated.state);
    changed.database.host = "localhost";
    expect(run(root, ["save"], changed).stderr.toString()).toContain("destination is immutable");
    expect(JSON.parse(run(root, ["read", workspace, "my_project", "run_01"]).stdout.toString())).toEqual(updated.state);
    expect(existsSync(`${first.path}.lock`)).toBeFalse();
  });

  test("reads do not create state; locks and symlinks fail closed", () => {
    const { root, workspace, state } = fixture();
    expect(run(root, ["read", workspace, "my_project", "run_01"]).exitCode).toBe(1);
    expect(existsSync(join(root, "state"))).toBeFalse();
    const first = save(root, state);
    writeFileSync(`${first.path}.lock`, "active writer", { mode: 0o600 });
    expect(run(root, ["save"], first.state).stderr.toString()).toContain("EEXIST");
    expect(readFileSync(`${first.path}.lock`, "utf8")).toBe("active writer");
    rmSync(`${first.path}.lock`);
    rmSync(first.path);
    symlinkSync(join(root, "missing"), first.path);
    expect(run(root, ["save"], first.state).stderr.toString()).toContain("not a symlink");
    expect(existsSync(join(root, "missing"))).toBeFalse();
  });

  test("rejects nonprivate/symlinked state directories and state inside project", () => {
    const { root, workspace, state } = fixture();
    const parent = join(root, "state");
    mkdirSync(parent);
    const target = join(root, "wrong-root");
    mkdirSync(target, { mode: 0o700 });
    symlinkSync(target, join(parent, "local-env"));
    expect(run(root, ["save"], state).exitCode).toBe(1);
    expect(existsSync(join(target, state.workspaceHash))).toBeFalse();
    rmSync(join(parent, "local-env"));
    mkdirSync(join(parent, "local-env"), { mode: 0o755 });
    expect(run(root, ["save"], state).exitCode).toBe(1);
    const internal = Bun.spawnSync(["node", helper, "save"], {
      env: { ...process.env, XDG_STATE_HOME: join(workspace, "state") }, stdin: Buffer.from(JSON.stringify(state)),
    });
    expect(internal.exitCode).toBe(1);
    expect(internal.stderr.toString()).toContain("outside the workspace");
    expect(existsSync(join(workspace, "state"))).toBeFalse();
  });

  test("simultaneous stale writes cannot overwrite one another", async () => {
    const { root, state } = fixture();
    const first = save(root, state);
    const start = () => Bun.spawn(["node", helper, "save"], {
      env: { ...process.env, XDG_STATE_HOME: join(root, "state") }, stdin: Buffer.from(JSON.stringify(first.state)), stdout: "pipe", stderr: "pipe",
    });
    const jobs = [start(), start()];
    const codes = await Promise.all(jobs.map((job) => job.exited));
    expect(codes.sort()).toEqual([0, 1]);
    expect(JSON.parse(readFileSync(first.path, "utf8")).revision).toBe(2);
    expect(existsSync(`${first.path}.lock`)).toBeFalse();
  });

  test("independent runs keep state and database names separate when one closes", () => {
    const { root, workspace, state } = fixture();
    const a = save(root, owned(state));
    const bInput = structuredClone(state);
    bInput.runId = "run_02";
    bInput.database.name = identity(workspace, "my_project", "run_02").databaseName;
    bInput.database.createdBy = "run_02" as any;
    const b = save(root, bInput);
    expect(b.path).not.toBe(a.path);
    expect(b.state.database.name).not.toBe(a.state.database.name);
    save(root, { ...a.state, status: "closed" });
    expect(JSON.parse(run(root, ["read", workspace, "my_project", "run_02"]).stdout.toString())).toEqual(b.state);
  });

  test("metadata rejects secret fields, credential URLs, and parser errors without echoing secrets", () => {
    const { root, state } = fixture();
    expect(() => validateState({ ...state, password: "secret" })).toThrow("metadata fields");
    state.services[0]!.url = "https://user:secret@app.localhost" as any;
    expect(() => validateState(state)).toThrow("credential-free");
    state.services[0]!.url = "https://app.localhost/?token=secret" as any;
    expect(() => validateState(state)).toThrow("credential-free");
    const invalid = run(root, ["save"], '{"password":"never_echo_me",');
    expect(invalid.exitCode).toBe(1);
    expect(invalid.stderr.toString()).toBe("Invalid JSON metadata\n");
    expect(invalid.stdout.toString()).toBe("");
  });

  test("ownership requires receipt and exact freshly observed server/database; names never suffice", () => {
    const { state } = fixture();
    const observed = { engine: "postgresql", host: "127.0.0.1", port: 5432, name: state.database.name, serverId: "123456789" };
    expect(() => checkOwnedDatabase(state, observed)).toThrow("not owned");
    owned(state);
    expect(checkOwnedDatabase(state, observed).eligible).toBeTrue();
    for (const key of ["engine", "host", "port", "name", "serverId"]) {
      expect(() => checkOwnedDatabase(state, { ...observed, [key]: "other" })).toThrow("does not match");
    }
    state.database.createdBy = "other" as any;
    expect(() => checkOwnedDatabase(state, observed)).toThrow("another run");
    state.database.createdBy = state.runId as any;
    state.status = "closed";
    expect(() => checkOwnedDatabase(state, observed)).toThrow("not owned");
  });

  test("existing database cannot become owned; disposable names and local endpoints are checked", () => {
    const { state } = fixture();
    owned(state);
    state.database.mode = "existing";
    expect(() => validateState(state)).toThrow("cannot be owned");
    state.database.mode = "disposable";
    state.database.name = "agent_unknown_name";
    expect(() => validateState(state)).toThrow("name mismatch");
    state.database.host = "production.internal";
    expect(() => validateState(state)).toThrow("loopback");
    state.database.host = "127.0.0.1";
    state.database.port = 6432;
    expect(() => validateState(state)).toThrow("shared SQL server port");
  });

  test("ready requires real check results; SQL-only readiness is supported", () => {
    const { state } = fixture();
    state.status = "ready";
    expect(() => validateState(state)).toThrow("Ready requires");
    state.database.serverId = "123" as any;
    state.services[0]!.url = "http://app.localhost:1355" as any;
    state.checks = { http: "passed", database: "passed", smoke: "passed" };
    expect(validateState(state)).toBe(state);
    state.services = [];
    state.checks.http = "pending";
    expect(validateState(state)).toBe(state);
  });

  test("HTTP-only tasks need no database; absent SQL cannot pass ownership check", () => {
    const { root, state } = fixture();
    const http = { ...state, database: null, status: "ready", services: [{ ...state.services[0], url: "http://app.localhost:1355" }], checks: { http: "passed", database: "pending", smoke: "passed" } };
    expect(validateState(http)).toBe(http);
    const first = save(root, http);
    expect(run(root, ["save"], { ...first.state, status: "preparing", database: state.database }).stderr.toString()).toContain("destination is immutable");
    expect(() => checkOwnedDatabase(http, { engine: "postgresql", host: "127.0.0.1", port: 5432, name: state.database.name, serverId: "123" })).toThrow("not owned");
    expect(() => validateState({ ...http, services: [], checks: { ...http.checks, http: "pending" } })).toThrow("Ready requires");
  });

  test("owned processes need identity; closed receipts and server identity cannot be overwritten", () => {
    const { root, state } = fixture();
    state.services[0]!.ownedBy = "run_01" as any;
    expect(() => validateState(state)).toThrow("PID and start token");
    state.services[0]!.pid = 123 as any;
    state.services[0]!.startToken = "Mon Jan 1 10:00:00 2026" as any;
    const first = save(root, owned(state));
    const changed = structuredClone(first.state);
    changed.database.creationReceipt.createdAt = "2026-01-02T00:00:00.000Z";
    expect(run(root, ["save"], changed).stderr.toString()).toContain("receipt is immutable");
    const closed = save(root, { ...first.state, status: "closed" });
    expect(run(root, ["save"], { ...closed.state, status: "preparing" }).stderr.toString()).toContain("cannot be reopened");
  });
});

test("local-env documents required guardrails, helper limitations, and isolation acceptance", () => {
  const skill = readFileSync(join(repository, "skills/local-env/SKILL.md"), "utf8");
  const operations = readFileSync(join(repository, "skills/local-env/references/operations.md"), "utf8");
  const state = readFileSync(join(repository, "skills/local-env/references/state.md"), "utf8");
  expect(skill.split("\n").length).toBeLessThanOrEqual(100);
  for (const required of ["existing", "disposable", "portless doctor", "portless get", "PORTLESS_URL", "process", "0.15.6", "credentials"]) expect(skill).toContain(required);
  for (const required of ["PORTLESS_SYNC_HOSTS=0", "IF NOT EXISTS", "shadow", "borrowed consumer", "two simultaneous workspaces", "HTTP-only fixtures do not satisfy SQL isolation"]) expect(operations).toContain(required);
  expect(state).toContain("does NOT authorize DROP");
  expect(state).toContain("never steal stale-looking locks");
});
