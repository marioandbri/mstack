import { afterEach, expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { inventory } from "../scripts/maintenance/inventory";
import { auditReport, prepareAudit } from "../scripts/maintenance/audit";

const roots: string[] = [];
afterEach(() => roots.splice(0).forEach(root => rmSync(root, { recursive: true, force: true })));
const cli = resolve(import.meta.dir, "../scripts/maintenance.ts");

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "mstack-audit-")); roots.push(root);
  mkdirSync(join(root, "skills")); mkdirSync(join(root, "licenses"));
  writeFileSync(join(root, "skills.json"), JSON.stringify({ schemaVersion: 1, targets: ["agents", "claude", "codex", "pi"], skills: [] }));
  writeFileSync(join(root, "mstack.json"), JSON.stringify({ schemaVersion: 1, managed: [] }));
  writeFileSync(join(root, "old.md"), "# Prior policy\n\nFor project Alpha, use Chroma for observations.\n");
  writeFileSync(join(root, "decision.md"), "# Current decision\n\nFor project Alpha, use SQLite with sqlite-vec. This replaces the earlier Chroma selection.\n");
  const request = { scope: "project-alpha", repository: root, sources: [{ id: "prior-policy", path: "old.md", owner: "repository" }, { id: "current-decision", path: "decision.md", owner: "repository" }] };
  return { root, request, inventory: inventory(request) };
}

function run(root: string, command: string, request: unknown, outputName: string) {
  const input = join(root, outputName + ".request.json"); const output = join(root, outputName + ".json");
  writeFileSync(input, JSON.stringify(request));
  const result = Bun.spawnSync(["bun", cli, command, "--request", input, "--output", output], { stdout: "pipe", stderr: "pipe" });
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  return JSON.parse(readFileSync(output, "utf8"));
}

function analysisFor(bundle: any) {
  const refs = [
    { source_id: "prior-policy", sha256: bundle.sources.find((s: any) => s.id === "prior-policy").sha256, excerpt: "For project Alpha, use Chroma for observations." },
    { source_id: "current-decision", sha256: bundle.sources.find((s: any) => s.id === "current-decision").sha256, excerpt: "For project Alpha, use SQLite with sqlite-vec. This replaces the earlier Chroma selection." },
  ];
  return { schema_version: 1, id: "audit-1", scope: "project-alpha", inventory_sha256: bundle.inventory_sha256,
    analyst: { provider: "agent-procedure", version: "1" }, coverage: { reviewed: ["prior-policy", "current-decision"], limits: [] },
    findings: [{ id: "F-1", scope: "project-alpha", target: "prior-policy", claim: "obsolescence", evidence_type: "semantic", source_refs: refs,
      observation: "The earlier backend selection is superseded by the current decision for the same project.", suspected_cause: null,
      impact: "The old policy can misdirect implementation.", uncertainty: ["No behavioral failure has been measured."],
      recommendation: { operation: "MOVE", reason: "Preserve the prior decision as history and reference the current one." },
      semantic_basis: null, priority_reason: "Affects the backend selected for implementation." }], priority_order: ["F-1"] };
}

test("requested semantic audit preserves versioned evidence and hands one opportunity to review without applying it", () => {
  const f = fixture();
  const bundle = run(f.root, "audit-prepare", f, "bundle");
  const analysis = analysisFor(bundle);
  const report = run(f.root, "audit-report", { ...f, analysis }, "report");
  expect(report.analysis.findings[0].recommendation.operation).toBe("MOVE");
  expect(report.coverage.unreviewed).toEqual([]);
  expect(report.allowed_actions).toEqual(["review"]);
  const handoff = run(f.root, "audit-handoff", { ...f, analysis, selected_id: "F-1" }, "handoff");
  expect(handoff.selected.id).toBe("F-1");
  expect(handoff.allowed_actions).toEqual(["review"]);
  expect(handoff.user_decisions).toEqual([]);
  expect(readFileSync(join(f.root, "old.md"), "utf8")).toContain("use Chroma");
});

test("audit rejects unsupported scope, source versions, excerpts and semantic coverage", () => {
  const f = fixture(); const bundle = prepareAudit(f.request, f.inventory);
  const scenarios = [
    (a: any) => { a.scope = "another-project"; },
    (a: any) => { a.findings[0].source_refs[0].sha256 = "0".repeat(64); },
    (a: any) => { a.findings[0].source_refs[0].excerpt = "The source never said this."; },
    (a: any) => { a.coverage.reviewed = []; },
    (a: any) => { a.findings[0].source_refs.pop(); },
    (a: any) => { a.findings[0].recommendation.operation = "MERGE"; },
    (a: any) => { a.priority_order = []; },
  ];
  for (const change of scenarios) {
    const analysis = structuredClone(analysisFor(bundle)); change(analysis);
    expect(() => auditReport(f.request, f.inventory, analysis)).toThrow();
  }
});

test("source drift prevents a stale semantic finding while empty findings retain coverage gaps", () => {
  const f = fixture(); const before = prepareAudit(f.request, f.inventory);
  writeFileSync(join(f.root, "old.md"), "# Changed policy\n");
  const changed = prepareAudit(f.request, f.inventory);
  expect(changed.sources.find(s => s.id === "prior-policy")?.state).toBe("changed-source");
  expect(changed.sources.find(s => s.id === "prior-policy")?.text).toBeNull();
  expect(() => auditReport(f.request, f.inventory, analysisFor(before))).toThrow();
  const empty = analysisFor(before); empty.findings = []; empty.priority_order = []; empty.coverage.reviewed = [];
  const report = auditReport(f.request, f.inventory, empty);
  expect(report.analysis.findings).toEqual([]);
  expect(report.coverage.unreviewed).toContain("current-decision");
});

test("configuration changes and removed references remain explicit source gaps", () => {
  const f = fixture(); const home = join(f.root, "home"); mkdirSync(join(home, ".codex"), { recursive: true });
  writeFileSync(join(home, ".codex/config.toml"), 'model = "before"\n');
  writeFileSync(join(f.root, "mstack.json"), JSON.stringify({ schemaVersion: 1, managed: [{ target: "codex/config.toml", keys: ["model"] }] }));
  const request = { ...f.request, home, configuration: [{ path: "codex/config.toml", format: "toml" as const, keys: ["model"] }] };
  const frozen = inventory(request);
  writeFileSync(join(home, ".codex/config.toml"), 'model = "after"\n');
  const changed = prepareAudit(request, frozen);
  expect(changed.sources.find(s => s.id === "configuration:codex/config.toml")?.state).toBe("changed-source");
  expect(changed.sources.find(s => s.id === "configuration:codex/config.toml")?.text).toBeNull();

  mkdirSync(join(f.root, "skills/example"));
  writeFileSync(join(f.root, "skills/example/SKILL.md"), '---\nname: example\ndescription: Fixture.\n---\n[Support](support.md)\n');
  writeFileSync(join(f.root, "skills/example/support.md"), 'Use an owned checkout.\n');
  writeFileSync(join(f.root, "licenses/MIT.txt"), "MIT\n");
  writeFileSync(join(f.root, "skills.json"), JSON.stringify({ schemaVersion: 1, targets: ["agents", "claude", "codex", "pi"], skills: [{ name: "example", owner: "original", source: "self", sourcePath: "skills/example", importRef: "test", license: "MIT" }] }));
  const beforeRemoval = inventory(f.request);
  rmSync(join(f.root, "skills/example/support.md"));
  const removed = prepareAudit(f.request, beforeRemoval);
  expect(removed.sources.find(s => s.id === "skill:example:skills/example/support.md")?.state).toBe("unavailable");
});

test("two contradictory clauses can be evidenced within the same instruction source", () => {
  const f = fixture();
  writeFileSync(join(f.root, "old.md"), "# Capture policy\n\nCreate originals exclusively.\n\nOverwrite originals when a retry arrives.\n");
  const frozen = inventory(f.request); const bundle = prepareAudit(f.request, frozen);
  const analysis = analysisFor(bundle); const finding = analysis.findings[0]!;
  const hash = bundle.sources.find(s => s.id === "prior-policy")!.sha256;
  finding.claim = "contradiction"; finding.recommendation.operation = "MECHANIZE";
  finding.source_refs = ["Create originals exclusively.", "Overwrite originals when a retry arrives."].map(excerpt => ({ source_id: "prior-policy", sha256: hash, excerpt }));
  finding.observation = "These clauses impose incompatible retry behavior under the same capture policy.";
  const report = auditReport(f.request, frozen, analysis);
  expect(report.analysis.findings[0].claim).toBe("contradiction");
});

test("audit supports every proposed operation while preserving a severe first opportunity", () => {
  const f = fixture(); const bundle = prepareAudit(f.request, f.inventory);
  for (const operation of ["KEEP", "REMOVE", "MOVE", "MERGE", "SPLIT", "ADD", "MECHANIZE"]) {
    const analysis: any = analysisFor(bundle); const finding = analysis.findings[0];
    finding.claim = "opportunity"; finding.recommendation.operation = operation;
    finding.impact = "A conflicting active storage policy could lead to loss of evidence. No recurrence is established.";
    finding.semantic_basis = { responsibility: "Both sources govern observation storage.", scope_compatibility: "Same project and capture operation.", meaning: "Keep the selected SQLite behavior and preserve the earlier choice as history when consolidating ownership." };
    const report = auditReport(f.request, f.inventory, analysis);
    expect(report.analysis.findings[0].recommendation.operation).toBe(operation);
    expect(report.analysis.priority_order).toEqual(["F-1"]);
    expect(report.allowed_actions).toEqual(["review"]);
  }
});

test("similar language does not merge complementary capture and review responsibilities", () => {
  const f = fixture();
  const capture = "Capture observations during ordinary work and return to that task.";
  const review = "Review observations when the user requests reflection; capture alone does not start review.";
  writeFileSync(join(f.root, "old.md"), capture + "\n"); writeFileSync(join(f.root, "decision.md"), review + "\n");
  const frozen = inventory(f.request); const bundle = prepareAudit(f.request, frozen); const analysis = analysisFor(bundle);
  const finding = analysis.findings[0]!;
  finding.claim = "complementarity"; finding.recommendation = { operation: "KEEP", reason: "The two procedures have different activation contexts and complementary responsibilities." };
  finding.observation = "Shared observation language does not imply the same workflow.";
  finding.source_refs = [["prior-policy", capture], ["current-decision", review]].map(([id, excerpt]) => ({ source_id: id!, sha256: bundle.sources.find(s => s.id === id)!.sha256, excerpt: excerpt! }));
  const report = auditReport(f.request, frozen, analysis);
  expect(report.analysis.findings[0].recommendation.operation).toBe("KEEP");
  expect(report.analysis.findings[0].source_refs).toHaveLength(2);
});

test("reformatting the inventory object cannot invalidate an unchanged source set", () => {
  const f = fixture(); const bundle = prepareAudit(f.request, f.inventory);
  const reordered = Object.fromEntries(Object.entries(f.inventory).reverse()) as typeof f.inventory;
  const report = auditReport(f.request, reordered, analysisFor(bundle));
  expect(report.inventory_sha256).toBe(bundle.inventory_sha256);
});

test("external providers keep distinct identities and changed metadata remains a gap", () => {
  const f = fixture();
  const request = { ...f.request, external_metadata: [{ name: "same-name", owner: "provider-one", description: "Former trigger." }, { name: "same-name", owner: "provider-two", description: "A complementary capability." }] };
  const frozen = inventory(request); const bundle = prepareAudit(request, frozen);
  const external = bundle.sources.filter(s => s.kind === "external-metadata");
  expect(new Set(external.map(s => s.id)).size).toBe(2);
  const changedRequest = { ...request, external_metadata: [{ ...request.external_metadata[0]!, description: "New trigger." }, request.external_metadata[1]!] };
  const changed = prepareAudit(changedRequest, frozen);
  expect(changed.sources.find(s => s.kind === "external-metadata" && s.owner === "provider-one")?.state).toBe("changed-source");
  expect(changed.sources.find(s => s.kind === "external-metadata" && s.owner === "provider-one")?.text).toBeNull();
  expect(changed.sources.find(s => s.kind === "external-metadata" && s.owner === "provider-two")?.state).toBe("available");
});
