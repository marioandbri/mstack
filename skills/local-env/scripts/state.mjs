#!/usr/bin/env node
// Metadata only. Never starts/stops services or executes SQL.
import { createHash, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { closeSync, lstatSync, mkdirSync, openSync, readFileSync, realpathSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}
function keys(value, expected) {
  requireValue(value && typeof value === "object" && !Array.isArray(value), "Expected object");
  requireValue(Object.keys(value).sort().join(",") === [...expected].sort().join(","), "Unexpected or missing metadata fields");
}
function token(value, max = 80) {
  return typeof value === "string" && new RegExp(`^[a-zA-Z0-9_-]{1,${max}}$`).test(value);
}
function runId(value) {
  requireValue(typeof value === "string" && /^[a-z0-9][a-z0-9_]{0,15}$/.test(value), "Invalid run ID; use 1-16 lowercase letters, digits, underscores");
}
function absolutePath(value) {
  return typeof value === "string" && isAbsolute(value) && !/[\x00-\x1f\x7f]/.test(value);
}
function date(value) {
  return typeof value === "string" && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value) && !Number.isNaN(Date.parse(value));
}

export function identity(directory, project, session) {
  let workspace = realpathSync(directory);
  requireValue(lstatSync(workspace).isDirectory(), "Workspace must be a directory");
  try {
    workspace = realpathSync(execFileSync("git", ["-C", workspace, "rev-parse", "--show-toplevel"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], env: Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_"))) }).trim());
  } catch { /* Non-Git projects use their canonical directory. */ }
  requireValue(typeof project === "string" && project.length > 0, "Project name is required");
  const slug = project.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 20).replace(/_+$/g, "");
  requireValue(slug.length > 0, "Project name needs ASCII letters or digits");
  if (session !== undefined) runId(session);
  const workspaceHash = createHash("sha256").update(workspace).digest("hex").slice(0, 16);
  return {
    workspace, workspaceHash, project: slug,
    routeBase: `${slug.replaceAll("_", "-")}-${workspaceHash}`,
    databaseName: `agent_${slug}_${workspaceHash}${session === undefined ? "" : `_${session}`}`,
  };
}

export function validateState(state) {
  keys(state, ["schemaVersion", "workspace", "workspaceHash", "project", "runId", "revision", "status", "services", "database", "checks", "logsDirectory"]);
  requireValue(state.schemaVersion === 1, "Unsupported schemaVersion");
  runId(state.runId);
  const expected = identity(state.workspace, state.project);
  requireValue(["workspace", "workspaceHash", "project"].every((key) => state[key] === expected[key]), "Workspace identity mismatch");
  requireValue(Number.isSafeInteger(state.revision) && state.revision >= 0, "Invalid revision");
  requireValue(["preparing", "ready", "closing", "closed"].includes(state.status), "Invalid status");
  requireValue(absolutePath(state.logsDirectory), "Invalid logs directory");
  requireValue(Array.isArray(state.services), "Invalid services");
  const names = new Set();
  for (const service of state.services) {
    keys(service, ["baseName", "url", "pid", "startToken", "ownedBy", "logPath"]);
    requireValue(typeof service.baseName === "string" && service.baseName.length <= 200 && service.baseName.split(".").every((label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label)), "Invalid service base name");
    requireValue(!names.has(service.baseName), "Duplicate service");
    names.add(service.baseName);
    if (service.url !== null) {
      requireValue(typeof service.url === "string", "Invalid service URL");
      let url;
      try { url = new URL(service.url); } catch { throw new Error("Invalid service URL"); }
      requireValue(["http:", "https:"].includes(url.protocol) && !url.username && !url.password && url.pathname === "/" && !url.search && !url.hash, "Store only credential-free HTTP origins");
    }
    requireValue(service.pid === null || (Number.isSafeInteger(service.pid) && service.pid > 1), "Invalid process ID");
    requireValue(service.startToken === null || (typeof service.startToken === "string" && /^[a-zA-Z0-9 :.+_-]{1,80}$/.test(service.startToken)), "Invalid process start token");
    requireValue(service.ownedBy === null || service.ownedBy === state.runId, "Process belongs to another run");
    if (service.ownedBy !== null) requireValue(service.pid !== null && service.startToken !== null, "Owned process needs PID and start token");
    requireValue(absolutePath(service.logPath), "Invalid log path");
  }
  const db = state.database;
  if (db !== null) {
    keys(db, ["mode", "engine", "host", "port", "name", "serverId", "createdBy", "creationReceipt"]);
    requireValue(["existing", "disposable"].includes(db.mode), "Invalid database mode");
    requireValue(["postgresql", "mysql"].includes(db.engine), "Invalid database engine");
    requireValue(["127.0.0.1", "localhost", "::1"].includes(db.host), "Database host must be local loopback");
    requireValue(db.port === (db.engine === "postgresql" ? 5432 : 3306), "Use the shared SQL server port");
    requireValue(typeof db.name === "string" && /^[a-zA-Z0-9_-]{1,63}$/.test(db.name), "Unsupported database identifier");
    requireValue(db.serverId === null || token(db.serverId), "Invalid server identity");
    requireValue(db.createdBy === null || db.createdBy === state.runId, "Database belongs to another run");
    if (db.mode === "existing") requireValue(db.createdBy === null && db.creationReceipt === null, "Existing databases cannot be owned");
    else requireValue([expected.databaseName, identity(state.workspace, state.project, state.runId).databaseName].includes(db.name), "Disposable database name mismatch");
    if (db.createdBy === null) requireValue(db.creationReceipt === null, "Unowned database cannot have creation receipt");
    else {
      keys(db.creationReceipt, ["existedBefore", "createdAt", "serverId"]);
      requireValue(db.creationReceipt.existedBefore === false && date(db.creationReceipt.createdAt) && db.serverId !== null && db.creationReceipt.serverId === db.serverId, "Invalid database creation receipt");
    }
  }
  keys(state.checks, ["http", "database", "smoke"]);
  requireValue(Object.values(state.checks).every((value) => ["pending", "passed", "failed"].includes(value)), "Invalid checks");
  if (state.status === "ready") {
    const httpReady = state.services.length === 0 ? state.checks.http === "pending" : state.services.every((service) => service.url !== null) && state.checks.http === "passed";
    const sqlReady = db === null ? state.checks.database === "pending" : db.serverId !== null && state.checks.database === "passed";
    requireValue((state.services.length > 0 || db !== null) && httpReady && sqlReady && state.checks.smoke === "passed", "Ready requires applicable HTTP, SQL, and smoke checks");
  }
  return state;
}

function present(path) {
  try { lstatSync(path); return true; }
  catch (error) { if (error.code === "ENOENT") return false; throw error; }
}
function privateDirectory(path) {
  if (!present(path)) mkdirSync(path, { mode: 0o700 });
  const stat = lstatSync(path);
  requireValue(stat.isDirectory() && !stat.isSymbolicLink() && (stat.mode & 0o077) === 0 && (process.getuid === undefined || stat.uid === process.getuid()), "State directory must be private, owned, and not a symlink");
}
export function statePath(workspaceHash, session) {
  requireValue(typeof workspaceHash === "string" && /^[a-f0-9]{16}$/.test(workspaceHash), "Invalid workspace hash");
  runId(session);
  const parent = resolve(process.env.XDG_STATE_HOME || join(homedir(), ".local", "state"));
  return join(parent, "local-env", workspaceHash, session, "state.json");
}
function outsideWorkspace(path, workspace) {
  const location = relative(workspace, path);
  requireValue(location === ".." || location.startsWith(`..${sep}`) || isAbsolute(location), "State must be outside the workspace");
}
function canonicalFuturePath(path) {
  let ancestor = path;
  while (!present(ancestor)) ancestor = dirname(ancestor);
  return resolve(realpathSync(ancestor), relative(ancestor, path));
}
function prepareDirectories(path, workspace) {
  outsideWorkspace(canonicalFuturePath(dirname(path)), workspace);
  const parent = resolve(process.env.XDG_STATE_HOME || join(homedir(), ".local", "state"));
  mkdirSync(parent, { recursive: true, mode: 0o700 });
  outsideWorkspace(join(realpathSync(parent), "local-env"), workspace);
  const root = join(parent, "local-env");
  privateDirectory(root);
  privateDirectory(resolve(path, "..", ".."));
  privateDirectory(resolve(path, ".."));
}
function readFile(path) {
  const stat = lstatSync(path);
  requireValue(stat.isFile() && !stat.isSymbolicLink() && (stat.mode & 0o077) === 0 && (process.getuid === undefined || stat.uid === process.getuid()), "State file must be private, owned, and not a symlink");
  return validateState(JSON.parse(readFileSync(path, "utf8")));
}
export function loadState(directory, project, session) {
  const expected = identity(directory, project);
  const path = statePath(expected.workspaceHash, session);
  // Validate ancestors without creating directories on reads.
  for (const directoryPath of [resolve(path, "../../.."), resolve(path, "../.."), resolve(path, "..")]) {
    const stat = lstatSync(directoryPath);
    requireValue(stat.isDirectory() && !stat.isSymbolicLink() && (stat.mode & 0o077) === 0 && (process.getuid === undefined || stat.uid === process.getuid()), "Unsafe state directory");
  }
  const state = readFile(path);
  requireValue(state.workspace === expected.workspace && state.project === expected.project && state.runId === session, "State identity mismatch");
  return state;
}
export function saveState(input) {
  validateState(input);
  const path = statePath(input.workspaceHash, input.runId);
  prepareDirectories(path, input.workspace);
  const lock = `${path}.lock`;
  const fd = openSync(lock, "wx", 0o600); // Concurrent writers fail closed; never steal locks.
  let temporary;
  try {
    if (present(path)) {
      const previous = readFile(path);
      requireValue(input.revision === previous.revision, "Stale state revision; reload before saving");
      requireValue(["workspace", "workspaceHash", "project", "runId", "logsDirectory"].every((key) => previous[key] === input[key]), "Run identity is immutable");
      requireValue((previous.database === null) === (input.database === null), "Database destination is immutable; create another run");
      if (previous.database !== null) {
        requireValue(["mode", "engine", "host", "port", "name"].every((key) => previous.database[key] === input.database[key]), "Database destination is immutable; create another run");
        requireValue(previous.database.serverId === null || input.database.serverId === previous.database.serverId, "SQL server identity changed");
        if (previous.database.createdBy !== null) requireValue(JSON.stringify(input.database.creationReceipt) === JSON.stringify(previous.database.creationReceipt) && input.database.createdBy === previous.database.createdBy, "Database ownership receipt is immutable");
      }
      requireValue(previous.status !== "closed" || JSON.stringify(input) === JSON.stringify(previous), "Closed run cannot be reopened");
    } else requireValue(input.revision === 0, "New state requires revision 0");
    const next = { ...input, revision: input.revision + 1 };
    temporary = `${path}.${randomUUID()}.tmp`;
    writeFileSync(temporary, `${JSON.stringify(next, null, 2)}\n`, { flag: "wx", mode: 0o600 });
    renameSync(temporary, path);
    temporary = undefined;
    return { path, state: next };
  } finally {
    if (temporary) unlinkSync(temporary);
    closeSync(fd);
    unlinkSync(lock);
  }
}

export function checkOwnedDatabase(state, observed) {
  validateState(state);
  keys(observed, ["engine", "host", "port", "name", "serverId"]);
  requireValue(state.status !== "closed" && state.database !== null && state.database.mode === "disposable" && state.database.createdBy === state.runId && state.database.creationReceipt !== null, "Database is not owned by this active run");
  requireValue(Object.keys(observed).every((key) => observed[key] === state.database[key]), "Observed SQL destination does not match ownership receipt");
  // Eligibility only. Caller must obtain fresh SQL evidence and verify no consumers.
  return { eligible: true, name: state.database.name, runId: state.runId };
}

const usage = "Usage: node state.mjs identity WORKSPACE PROJECT [SESSION] | save < metadata.json | read WORKSPACE PROJECT RUN | check-db WORKSPACE PROJECT RUN < observed.json";
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const [command, ...args] = process.argv.slice(2);
    let result;
    if (command === "identity" && [2, 3].includes(args.length)) result = identity(...args);
    else if (command === "save" && args.length === 0) result = saveState(JSON.parse(readFileSync(0, "utf8")));
    else if (command === "read" && args.length === 3) result = loadState(...args);
    else if (command === "check-db" && args.length === 3) result = checkOwnedDatabase(loadState(...args), JSON.parse(readFileSync(0, "utf8")));
    else throw new Error(usage);
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    // Do not echo input, parser errors, SQL connection strings, or credentials.
    console.error(error instanceof SyntaxError ? "Invalid JSON metadata" : error.code ? `Filesystem or process error: ${error.code}` : error.message);
    process.exitCode = 1;
  }
}
