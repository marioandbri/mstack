import { afterEach, expect, test } from "bun:test";
import { chmodSync, mkdtempSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const roots: string[] = [];
afterEach(() => roots.splice(0).forEach(root => rmSync(root, { recursive: true, force: true })));
const cli = resolve(import.meta.dir, "../scripts/maintenance.ts");

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "mstack-inventory-")); roots.push(root);
  const repo = join(root, "repo"); const home = join(root, "home");
  mkdirSync(join(repo, "skills", "example"), { recursive: true });
  mkdirSync(join(repo, "licenses")); mkdirSync(home);
  writeFileSync(join(repo, "skills.json"), JSON.stringify({ schemaVersion: 1, targets: ["agents", "claude", "codex", "pi"], skills: [{ name: "example", owner: "original", source: "self", sourcePath: "skills/example", importRef: "test", license: "MIT" }] }));
  writeFileSync(join(repo, "licenses", "MIT.txt"), "MIT\n");
  writeFileSync(join(repo, "mstack.json"), JSON.stringify({ schemaVersion: 1, managed: [] }));
  writeFileSync(join(repo, "AGENTS.md"), "# Repository rules\n");
  writeFileSync(join(repo, "skills", "example", "SKILL.md"), "---\nname: example\ndescription: Example. Use when testing inventory.\ndisable-model-invocation: true\n---\n\n[Missing reference](missing.md)\n");
  return { root, repo, home };
}

function run(root: string, request: unknown) {
  const input = join(root, "request.json"); const output = join(root, "inventory.json");
  writeFileSync(input, JSON.stringify(request));
  const result = Bun.spawnSync(["bun", cli, "inventory", "--request", input, "--output", output], { stdout: "pipe", stderr: "pipe" });
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  return JSON.parse(readFileSync(output, "utf8"));
}

test("requested audit inventories canonical, installed and exposed evidence separately without an incident", () => {
  const f = fixture(); const installed = join(f.home, ".codex/skills/example");
  mkdirSync(installed, { recursive: true }); writeFileSync(join(installed, "SKILL.md"), "# Older installed version\n");
  const canonical = readFileSync(join(f.repo, "skills/example/SKILL.md"));
  const report = run(f.root, { scope: "project-test", repository: f.repo, home: f.home, environment: { harness: "codex", session_id: "test", catalog: [] } });
  expect(report.schema_version).toBe(1);
  const skill = report.sources.find((s: any) => s.id === "skill:example");
  expect(skill.sha256).toHaveLength(64);
  expect(skill.owner).toBe("original");
  expect(skill.activation.disable_model_invocation).toBe(true);
  expect(skill.exposure).toEqual({ state: "not-listed", evidence: "supplied-catalog" });
  expect(skill.selection.state).toBe("unknown");
  expect(skill.execution.state).toBe("unknown");
  expect(skill.installations.find((i: any) => i.harness === "codex").matches_source).toBe(false);
  expect(report.findings.some((x: any) => x.kind === "broken-reference")).toBe(true);
  expect(report.coverage.semantic_review).toBe("not-performed");
  expect(readFileSync(join(f.repo, "skills/example/SKILL.md"))).toEqual(canonical);
});

test("partial audit preserves accessible sources and excludes private configuration and escaped sources", () => {
  const f = fixture(); const privateText = "private-fixture-value-must-not-be-exported";
  const secret = join(f.root, "private.txt"); writeFileSync(secret, privateText);
  rmSync(join(f.repo, "AGENTS.md")); symlinkSync(secret, join(f.repo, "AGENTS.md"));
  mkdirSync(join(f.home, ".codex"));
  writeFileSync(join(f.home, ".codex/config.toml"), `model = "fixture-model"\napi_key = "${privateText}"\n`);
  writeFileSync(join(f.repo, "mstack.json"), JSON.stringify({ schemaVersion: 1, managed: [{ target: "codex/config.toml", keys: ["model", "model_reasoning_effort"] }] }));
  const hidden = join(f.repo, "skills/example/private.md"); writeFileSync(hidden, "unreadable"); chmodSync(hidden, 0o000);
  try {
    const report = run(f.root, { scope: "partial", repository: f.repo, home: f.home,
      configuration: [{ path: "codex/config.toml", format: "toml", keys: ["model", "api_key"] }, { path: "codex/unknown.toml", format: "toml", keys: ["other"] }],
      external_metadata: [{ name: "external-example", description: "Only supplied metadata", owner: "external", private: privateText }] });
    expect(report.configuration[0].values).toEqual({ model: "fixture-model" });
    expect(report.configuration[0].unknown_keys).toEqual(["api_key"]);
    expect(report.configuration[1].state).toBe("unknown");
    expect(report.sources.find((s: any) => s.id === "repository-instructions").state).toBe("inaccessible");
    expect(report.findings.some((s: any) => s.kind === "inaccessible-source")).toBe(true);
    expect(report.external_metadata[0].body_review).toBe("not-performed");
    expect(JSON.stringify(report)).not.toContain(privateText);
  } finally { chmodSync(hidden, 0o600); }
});

test("selected instruction references are checked without treating a source read as execution", () => {
  const f = fixture();
  writeFileSync(join(f.repo, "AGENTS.md"), "# Rules\n\nSee [missing policy](no-policy.md).\n");
  const report = run(f.root, { scope: "instructions", repository: f.repo });
  expect(report.findings.some((x: any) => x.kind === "broken-reference" && x.source === "repository-instructions")).toBe(true);
  expect(report.sources.find((x: any) => x.id === "skill:example").reading.state).toBe("unknown");
});
