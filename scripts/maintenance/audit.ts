import { createHash } from "node:crypto";
import { readFileSync, realpathSync } from "node:fs";
import { isAbsolute, relative, resolve, sep } from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import schema from "../../skills/reflect/audit-analysis.schema.json";
import { inventory, type InventoryRequest } from "./inventory";

type Inventory = ReturnType<typeof inventory>;
type AuditSource = { id: string; owner: string; location: string; kind: string; sha256: string | null; state: string; text: string | null };
const sha = (data: string | Buffer) => createHash("sha256").update(data).digest("hex");
const reviewable = (path: string) => path.endsWith(".md") || path.endsWith(".schema.json") || path.endsWith("/agents/openai.yaml");
const validate = new Ajv2020({ strict: true, allErrors: true }).compile(schema);

function ordered(value: any): any {
  if (Array.isArray(value)) return value.map(ordered);
  if (value !== null && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(key => [key, ordered(value[key])]));
  return value;
}

function within(root: string, path: string) {
  const rel = relative(root, path);
  return rel === "" || (!isAbsolute(rel) && rel !== ".." && !rel.startsWith(`..${sep}`));
}

export function prepareAudit(request: InventoryRequest, frozen: Inventory) {
  if (frozen.schema_version !== 1 || frozen.scope !== request.scope) throw new Error("Audit scope differs from inventory");
  const current = inventory({ ...request, verify_installation: false });
  const repository = realpathSync(request.repository);
  const sources: AuditSource[] = [];
  const limits = [...frozen.coverage.limits, "Semantic snapshots cover Markdown, schemas and invocation policies. Other resources retain inventory hashes without a semantic-review claim."];
  const oldSources = new Map(frozen.sources.map(s => [s.id, s]));
  const resourceId = (source: any, path: string) => path === source.location?.replace(/^repo:/, "") ? source.id : `${source.id}:${path}`;
  function addFile(id: string, path: string, owner: string, kind: string, expected: string | null, explicit = false) {
    const location = within(repository, path) ? `repo:${relative(repository, path)}` : `selected:${id}`;
    const source: AuditSource = { id, owner, location, kind, sha256: expected, state: "unavailable", text: null };
    if (expected === null) { source.state = "unversioned"; sources.push(source); limits.push(`${id}: no frozen version`); return; }
    try {
      if (!explicit && !within(repository, realpathSync(path))) throw new Error("Outside scope");
      const bytes = readFileSync(path);
      if (sha(bytes) !== expected) source.state = "changed-source";
      else { source.state = "available"; source.text = bytes.toString("utf8"); }
    } catch { /* Inaccessible evidence stays explicit. */ }
    if (source.state !== "available") limits.push(`${id}: ${source.state}`);
    sources.push(source);
  }
  for (const source of current.sources) {
    const old = oldSources.get(source.id);
    if (source.kind === "skill") {
      const files = source.files.filter((f: any) => reviewable(f.path));
      for (const file of files) {
        const id = resourceId(source, file.path);
        const expected = old?.files?.find((f: any) => f.path === file.path)?.sha256 ?? null;
        addFile(id, resolve(repository, file.path), source.owner, "instructions", expected);
      }
      if (!files.length) sources.push({ id: source.id, owner: source.owner, kind: "instructions", location: source.location, sha256: old?.sha256 ?? null, state: "unavailable", text: null });
    } else {
      const selected = request.sources?.find(s => s.id === source.id);
      const path = selected ? resolve(repository, selected.path) : source.location?.startsWith("repo:") ? resolve(repository, source.location.slice(5)) : null;
      if (path && reviewable(path)) addFile(source.id, path, source.owner, source.kind, old?.sha256 ?? null, selected !== undefined);
      else sources.push({ id: source.id, owner: source.owner, kind: source.kind, location: source.location ?? `selected:${source.id}`, sha256: old?.sha256 ?? null, state: "unavailable", text: null });
    }
  }
  const present = new Set(sources.map(s => s.id));
  for (const old of frozen.sources) {
    const missing = old.kind === "skill" && old.files?.length ? old.files.filter((f: any) => reviewable(f.path)).map((f: any) => ({ id: resourceId(old, f.path), location: `repo:${f.path}`, sha256: f.sha256 })) : [{ id: old.id, location: old.location ?? `selected:${old.id}`, sha256: old.sha256 ?? null }];
    for (const item of missing) if (!present.has(item.id)) {
      sources.push({ ...item, owner: old.owner, kind: old.kind, state: "unavailable", text: null });
      limits.push(`${item.id}: no longer available in the requested inventory`); present.add(item.id);
    }
  }
  for (const config of frozen.configuration) {
    const text = JSON.stringify(ordered(config.values), null, 2);
    const latest = current.configuration.find(c => c.path === config.path);
    const state = config.state !== "inspected-owned-keys" || latest?.state !== "inspected-owned-keys" ? "unavailable" : JSON.stringify(ordered(latest.values)) === JSON.stringify(ordered(config.values)) ? "available" : "changed-source";
    const id = `configuration:${config.path}`;
    sources.push({ id, owner: "managed-keys", location: config.path, kind: "selected-keys", sha256: config.state === "inspected-owned-keys" ? sha(text) : null, state, text: state === "available" ? text : null });
    if (state !== "available") limits.push(`${id}: ${state}`);
  }
  const externalId = (metadata: any) => `external:${encodeURIComponent(metadata.owner)}:${encodeURIComponent(metadata.name)}`;
  const externalValue = (metadata: any) => ordered({ version: null, source: null, ...metadata });
  for (const metadata of frozen.external_metadata) {
    const id = externalId(metadata);
    const text = JSON.stringify(externalValue(metadata), null, 2);
    const latest = current.external_metadata.find(m => externalId(m) === id);
    const state = !latest ? "unavailable" : JSON.stringify(externalValue(latest)) === JSON.stringify(externalValue(metadata)) ? "available" : "changed-source";
    sources.push({ id, owner: metadata.owner, location: "supplied-metadata", kind: "external-metadata", sha256: sha(text), state, text: state === "available" ? text : null });
    if (state !== "available") limits.push(`${id}: ${state}`);
  }
  for (const metadata of current.external_metadata) if (!frozen.external_metadata.some(m => externalId(m) === externalId(metadata))) {
    sources.push({ id: externalId(metadata), owner: metadata.owner, location: "supplied-metadata", kind: "external-metadata", sha256: null, state: "unversioned", text: null });
    limits.push(`${externalId(metadata)}: no frozen version`);
  }
  if (new Set(sources.map(s => s.id)).size !== sources.length) throw new Error("Ambiguous source identities");
  if (frozen.manifest_sha256 !== current.manifest_sha256) limits.push("Managed catalog changed; refresh inventory before claiming complete coverage.");
  return { schema_version: 1, scope: frozen.scope, inventory_sha256: sha(JSON.stringify(ordered(frozen))), inventory_captured_at: frozen.captured_at, repository_commit: frozen.repository_commit, environment: frozen.environment, installation: frozen.installation, sources, structural_findings: frozen.findings, limits };
}

function checkedAnalysis(bundle: ReturnType<typeof prepareAudit>, analysis: any) {
  if (!validate(analysis)) throw new Error("Invalid audit analysis");
  if (analysis.scope !== bundle.scope || analysis.inventory_sha256 !== bundle.inventory_sha256) throw new Error("Audit input mismatch");
  const sources = new Map(bundle.sources.map(s => [s.id, s]));
  const ids = analysis.findings.map((f: any) => f.id);
  if (new Set(ids).size !== ids.length || analysis.priority_order.length !== ids.length || analysis.priority_order.some((id: string) => !ids.includes(id))) throw new Error("Incomplete priority order");
  for (const id of analysis.coverage.reviewed) if (sources.get(id)?.state !== "available") throw new Error("Unverified coverage");
  for (const finding of analysis.findings) {
    if (finding.scope !== bundle.scope || !sources.has(finding.target)) throw new Error("Finding outside scope");
    const references = new Set<string>();
    const clauses = new Set<string>();
    for (const reference of finding.source_refs) {
      const source = sources.get(reference.source_id);
      if (!source || source.sha256 !== reference.sha256) throw new Error("Unknown source or version");
      if (finding.evidence_type !== "structural" && source.state === "available" && !analysis.coverage.reviewed.includes(source.id)) throw new Error("Unreviewed semantic source");
      if (reference.excerpt !== null && (!source.text || !source.text.includes(reference.excerpt))) throw new Error("Unsupported excerpt");
      if (source.state !== "available" && reference.excerpt !== null) throw new Error("Unavailable source excerpt");
      if (source.state === "available" && reference.excerpt === null) throw new Error("Available evidence needs an excerpt");
      if (source.state !== "available" && !finding.uncertainty.length) throw new Error("Missing evidence needs an explicit limit");
      if (reference.excerpt !== null) clauses.add(`${reference.source_id}:${reference.excerpt}`);
      references.add(reference.source_id);
    }
    if (!references.has(finding.target)) throw new Error("Finding target lacks evidence");
    if (["contradiction", "obsolescence"].includes(finding.claim) && clauses.size < 2) throw new Error("Claim needs both evidenced clauses");
    if (["MERGE", "SPLIT"].includes(finding.recommendation.operation) && !finding.semantic_basis) throw new Error("Similarity alone does not justify this operation");
    if (["REMOVE", "MOVE", "MERGE", "SPLIT"].includes(finding.recommendation.operation) && (sources.get(finding.target)?.state !== "available" || sources.get(finding.target)?.kind === "external-metadata" || !analysis.coverage.reviewed.includes(finding.target))) throw new Error("Target body not reviewed");
    if (finding.evidence_type === "behavioral" && !finding.source_refs.some((r: any) => sources.get(r.source_id)?.kind === "evidence")) throw new Error("No behavioral evidence supplied");
  }
  return structuredClone(analysis);
}

export function auditReport(request: InventoryRequest, frozen: Inventory, analysis: any) {
  const bundle = prepareAudit(request, frozen);
  const checked = checkedAnalysis(bundle, analysis);
  return { schema_version: 1, scope: bundle.scope, inventory_sha256: bundle.inventory_sha256, inventory_captured_at: bundle.inventory_captured_at, repository_commit: bundle.repository_commit, environment: bundle.environment, installation: bundle.installation, analysis: checked,
    sources: bundle.sources.map(({ text, ...source }) => source),
    coverage: { reviewed: checked.coverage.reviewed, unreviewed: bundle.sources.filter(s => !checked.coverage.reviewed.includes(s.id)).map(s => s.id), limits: [...bundle.limits, ...checked.coverage.limits, "Semantic review is the analyst's recorded assessment; source availability is not proof of behavior."] }, allowed_actions: ["review"] };
}

export function auditHandoff(request: InventoryRequest, frozen: Inventory, analysis: any, selectedId: string) {
  const report = auditReport(request, frozen, analysis);
  const selected = report.analysis.findings.find((f: any) => f.id === selectedId);
  if (!selected) throw new Error("Unknown selected finding");
  return { schema_version: 1, scope: report.scope, audit_id: analysis.id, selected, sources: report.sources.filter(s => selected.source_refs.some((r: any) => r.source_id === s.id)), limits: report.coverage.limits, user_decisions: [], allowed_actions: ["review"], automatic_interview: false };
}
