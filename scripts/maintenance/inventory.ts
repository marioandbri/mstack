import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync, readdirSync, realpathSync } from "node:fs";
import { isAbsolute, join, relative, resolve, sep } from "node:path";
import { frontmatterValue, validateMarkdownLinks, validateRepository } from "../validate";

type Evidence = { state: string; evidence?: string };
type CatalogEntry = { name: string; description?: string; owner?: string };
export type InventoryRequest = {
  scope: string;
  repository: string;
  home?: string;
  verify_installation?: boolean;
  sources?: { id: string; path: string; owner: string }[];
  environment?: { harness: string; session_id?: string | null; catalog?: CatalogEntry[] };
  external_metadata?: CatalogEntry[];
  configuration?: { path: string; format: "json" | "toml"; keys: string[] }[];
};

const roots: Record<string, string> = { agents: ".agents", claude: ".claude", codex: ".codex", pi: ".pi/agent" };
const digest = (bytes: Uint8Array) => createHash("sha256").update(bytes).digest("hex");
const unknown = (): Evidence => ({ state: "unknown" });
function inside(parent: string, child: string) {
  const rel = relative(parent, child);
  return rel === "" || (!isAbsolute(rel) && rel !== ".." && !rel.startsWith(`..${sep}`));
}
function readable(path: string): Buffer {
  if (!(lstatSync(realpathSync(path)).mode & 0o444)) throw new Error("unreadable");
  return readFileSync(path);
}
function object(value: unknown): value is Record<string, any> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function inventory(request: InventoryRequest) {
  if (!object(request) || !request.scope || typeof request.repository !== "string") throw new Error("Inventory requires a scope and repository");
  if (request.environment?.catalog && !Array.isArray(request.environment.catalog)) throw new Error("Catalog must be a list");
  const repo = realpathSync(request.repository);
  const findings: Record<string, any>[] = [];
  const limits: string[] = [];
  const sources: Record<string, any>[] = [];
  function finding(kind: string, source: string, detail: string) {
    findings.push({ id: `structural:${findings.length + 1}`, kind, source, detail, evidence_type: "structural", suspected_cause: null });
  }
  function file(path: string, allowed: string) {
    const actual = realpathSync(path);
    if (!inside(allowed, actual)) throw new Error("outside-scope");
    const bytes = readable(path);
    return { path: relative(repo, path), sha256: digest(bytes) };
  }
  let manifest: any;
  try { manifest = JSON.parse(readable(join(repo, "skills.json")).toString()); }
  catch { throw new Error("Cannot read managed skill inventory"); }
  if (manifest.schemaVersion !== 1 || !Array.isArray(manifest.skills)) throw new Error("Invalid managed skill inventory");
  let installManifest: any = {};
  try { installManifest = JSON.parse(readable(join(repo, "mstack.json")).toString()); }
  catch { limits.push("Installation manifest unavailable; owned configuration keys are unknown."); }
  const configKeys = new Map<string, string[]>();
  for (const entry of installManifest.managed ?? []) if (Array.isArray(entry.keys)) configKeys.set(entry.target, entry.keys);
  const environment = request.environment ? { harness: request.environment.harness, session_id: request.environment.session_id ?? null, catalog_supplied: request.environment.catalog !== undefined } : null;
  const catalog = request.environment?.catalog;
  let validationSafe = true;
  for (const skill of manifest.skills) {
    if (typeof skill.name !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(skill.name)) {
      validationSafe = false; finding("invalid-skill-name", "skills.json", "Name cannot identify a managed skill directory."); continue;
    }
    const id = `skill:${skill.name}`;
    const path = join(repo, "skills", skill.name, "SKILL.md");
    const source: Record<string, any> = { id, kind: "skill", name: skill.name, owner: skill.owner, provenance: { source: skill.source, ref: skill.importRef }, location: `repo:skills/${skill.name}/SKILL.md`, declaration: { state: "declared", evidence: "skills.json" }, exposure: catalog === undefined ? unknown() : { state: catalog.some(e => e.name === skill.name) ? "listed" : "not-listed", evidence: "supplied-catalog" }, selection: unknown(), reading: unknown(), execution: unknown(), files: [] };
    try {
      source.sha256 = file(path, repo).sha256;
      const text = readable(path).toString();
      const frontmatter = text.startsWith("---\n") ? text.slice(4, text.indexOf("\n---\n", 4)) : "";
      source.description = frontmatterValue(frontmatter, "description");
      source.activation = { disable_model_invocation: frontmatterValue(frontmatter, "disable-model-invocation") === "true" };
      source.state = "accessible";
      function walk(directory: string) {
        for (const entry of readdirSync(directory, { withFileTypes: true })) {
          if ([".venv", "node_modules", "__pycache__", ".git"].includes(entry.name)) continue;
          const child = join(directory, entry.name);
          if (entry.isSymbolicLink()) { validationSafe = false; finding("excluded-link", id, `Symlink excluded: ${relative(repo, child)}`); }
          else if (entry.isDirectory()) walk(child);
          else if (entry.isFile()) source.files.push(file(child, repo));
        }
      }
      walk(join(repo, "skills", skill.name));
    } catch {
      source.state = "inaccessible"; validationSafe = false;
      finding("inaccessible-source", id, "Source could not be fully read within the requested repository.");
    }
    source.installations = Object.entries(roots).map(([harness, suffix]) => {
      if (!request.home) return { harness, ...unknown() };
      const installed = join(resolve(request.home), suffix, "skills", skill.name, "SKILL.md");
      try {
        const sha256 = digest(readable(installed));
        const matches_source = source.sha256 ? sha256 === source.sha256 : null;
        if (matches_source === false) finding("installation-differs", id, `${harness} installed content differs from canonical content.`);
        return { harness, state: "present", sha256, matches_source };
      } catch { return { harness, state: existsSync(installed) ? "inaccessible" : "absent", matches_source: null }; }
    });
    sources.push(source);
  }
  const extra = request.sources ?? [{ id: "repository-instructions", path: join(repo, "AGENTS.md"), owner: "repository" }, { id: "global-instructions", path: join(repo, "instructions/global/AGENTS.md"), owner: "mstack" }];
  for (const entry of extra) {
    const path = resolve(repo, entry.path);
    try {
      if (!request.sources) file(path, repo);
      sources.push({ id: entry.id, kind: "instructions", owner: entry.owner, state: "accessible", sha256: digest(readable(path)), location: inside(repo, path) ? `repo:${relative(repo, path)}` : `selected:${entry.id}`, semantic_review: "not-performed" });
      const errors: string[] = [];
      validateMarkdownLinks(path, errors);
      for (const error of errors) finding("broken-reference", entry.id, error.replaceAll(repo, "repo:"));
    }
    catch { sources.push({ id: entry.id, kind: "instructions", owner: entry.owner, state: "inaccessible", sha256: null }); finding("inaccessible-source", entry.id, "Selected instruction source is unavailable."); }
  }
  let validation: any = { state: "unavailable" };
  if (validationSafe) {
    try {
      const result = validateRepository(repo);
      validation = { state: result.errors.length ? "findings" : "passed", ...result };
      for (const error of result.errors) finding(error.includes("broken link") ? "broken-reference" : "invalid-structure", "repository-validator", error.replaceAll(repo, "repo:"));
    } catch { limits.push("Repository validator could not complete; accessible source hashes remain available."); }
  } else limits.push("Repository validation incomplete because a source is inaccessible or contains excluded links.");
  const configuration = (request.configuration ?? []).map(config => {
    const allowed = configKeys.get(config.path) ?? [];
    const permitted = config.keys.filter(key => allowed.includes(key));
    const unknown_keys = config.keys.filter(key => !allowed.includes(key));
    const result: any = { path: config.path, values: {}, unknown_keys, state: "unknown" };
    const [root, ...parts] = config.path.split("/");
    if (!request.home || !root || !roots[root] || !permitted.length) return result;
    try {
      const content = readable(join(resolve(request.home), roots[root]!, ...parts)).toString();
      const parsed = config.format === "toml" ? Bun.TOML.parse(content) : JSON.parse(content);
      for (const key of permitted) if (Object.hasOwn(parsed, key)) result.values[key] = parsed[key];
      result.state = "inspected-owned-keys";
    } catch { finding("unknown-configuration", config.path, "Requested owned keys could not be read."); }
    return result;
  });
  if (configuration.some(c => c.state === "unknown" || c.unknown_keys.length)) limits.push("Some configuration is unknown; only declared owned keys were inspected.");
  let installation: any = { state: "not-requested" };
  if (request.verify_installation) {
    if (!request.home) throw new Error("Installation verification requires an explicit home");
    const result = Bun.spawnSync(["fish", resolve(import.meta.dir, "../../install/verify.fish"), "--home", resolve(request.home)], { stdout: "pipe", stderr: "pipe", timeout: 30_000 });
    const summary = /PASS commit=([0-9a-f]+); skills=(\d+); targets=(\d+)/.exec(result.stdout.toString());
    installation = summary && result.exitCode === 0 ? { state: "verified", commit: summary[1], skills: Number(summary[2]), targets: Number(summary[3]) } : { state: "unverified", exit_code: result.exitCode };
    if (installation.state === "unverified") limits.push("Installer verification failed or is unavailable; presence does not prove a valid installation.");
  }
  let commit: string | null = null;
  const git = Bun.spawnSync(["git", "-C", repo, "rev-parse", "HEAD"], { stdout: "pipe", stderr: "pipe" });
  if (git.exitCode === 0) commit = git.stdout.toString().trim();
  return { schema_version: 1, scope: request.scope, captured_at: new Date().toISOString(), repository_commit: commit, manifest_sha256: digest(readable(join(repo, "skills.json"))), environment, sources, external_metadata: (request.external_metadata ?? []).map(e => ({ name: e.name, description: e.description ?? null, owner: e.owner ?? "external", evidence_type: "supplied-metadata", body_review: "not-performed" })), configuration, installation, validation, findings, coverage: { managed_skills: manifest.skills.length, accessible_skills: sources.filter(s => s.kind === "skill" && s.state === "accessible").length, external_metadata: request.external_metadata?.length ?? 0, semantic_review: "not-performed", selection: "unknown", execution: "unknown", limits: [...limits, "Catalog evidence applies only to the supplied environment.", "Hashes and structural checks do not prove semantic review, selection, reading or execution.", "External metadata is supplied explicitly; no external skill bodies or unrelated sessions were inspected."] } };
}
