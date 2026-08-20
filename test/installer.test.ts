import { afterEach, describe, expect, test } from "bun:test";
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, readlinkSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";

const repository = resolve(import.meta.dir, "..");
const setup = join(repository, "install", "setup.fish");
const verify = join(repository, "install", "verify.fish");
const homes: string[] = [];

afterEach(() => {
  for (const home of homes.splice(0)) rmSync(home, { recursive: true, force: true });
});

function run(script: string, home: string, ...args: string[]) {
  return Bun.spawnSync(["fish", script, "--home", home, "--repo", repository, ...args], {
    cwd: repository,
    stdout: "pipe",
    stderr: "pipe",
  });
}

function snapshot(root: string): string[] {
  if (!existsSync(root)) return [];
  return readdirSync(root, { recursive: true, encoding: "utf8" }).map(String).sort();
}

function findMarker(root: string): string | undefined {
  if (!existsSync(root)) return undefined;
  for (const relative of snapshot(root)) {
    const path = join(root, relative);
    if (!lstatSync(path).isFile()) continue;
    if (readFileSync(path, "utf8") === "preserve me") return path;
  }
}

describe("cross-harness installer", () => {
  test("dry-runs, backs up conflicts, links all targets, and is idempotent", () => {
    const home = mkdtempSync(join(tmpdir(), "engineering-skills-home-"));
    homes.push(home);

    const conflict = join(home, ".agents", "skills", "code-review");
    mkdirSync(conflict, { recursive: true });
    writeFileSync(join(conflict, "marker.txt"), "preserve me");

    const wrongLink = join(home, ".claude", "skills", "code-review");
    mkdirSync(dirname(wrongLink), { recursive: true });
    symlinkSync(join(home, "wrong-target"), wrongLink);

    const correctLink = join(home, ".codex", "skills", "code-review");
    mkdirSync(dirname(correctLink), { recursive: true });
    symlinkSync(join(repository, "skills", "code-review"), correctLink);

    const before = snapshot(home);
    const dry = run(setup, home);
    expect(dry.exitCode).toBe(0);
    expect(dry.stdout.toString()).toContain("MODE dry-run");
    expect(snapshot(home)).toEqual(before);
    expect(existsSync(join(conflict, "marker.txt"))).toBeTrue();

    const apply = run(setup, home, "--apply");
    expect(apply.exitCode).toBe(0);
    expect(apply.stdout.toString()).toContain("MODE apply");
    expect(findMarker(join(home, ".engineering-skills-backups"))).toBeDefined();

    const check = run(verify, home);
    expect(check.exitCode).toBe(0);
    expect(check.stdout.toString()).toContain("PASS checked=96 canonical skill links");

    const installed = join(home, ".pi", "agent", "skills", "code-review");
    expect(lstatSync(installed).isSymbolicLink()).toBeTrue();
    expect(resolve(dirname(installed), readlinkSync(installed))).toBe(join(repository, "skills", "code-review"));

    const second = run(setup, home, "--apply");
    expect(second.exitCode).toBe(0);
    expect(second.stdout.toString()).toContain("linked=0 unchanged=96 backed_up=0");

    const duplicate = join(home, ".agents", "skills", "legacy", "skills", "code-review", "SKILL.md");
    mkdirSync(dirname(duplicate), { recursive: true });
    writeFileSync(duplicate, "---\nname: code-review\ndescription: Duplicate.\n---\n");
    const duplicateCheck = run(verify, home);
    expect(duplicateCheck.exitCode).toBe(1);
    expect(duplicateCheck.stderr.toString()).toContain("ERROR duplicate agents/code-review");
  });

  test("rejects upstream ownership lock entries for managed skills", () => {
    const home = mkdtempSync(join(tmpdir(), "engineering-skills-lock-home-"));
    homes.push(home);
    const apply = run(setup, home, "--apply");
    expect(apply.exitCode).toBe(0);

    const lock = join(home, ".agents", ".skill-lock.json");
    writeFileSync(lock, JSON.stringify({ version: 3, skills: { "code-review": { source: "upstream" } } }));
    const check = run(verify, home);
    expect(check.exitCode).toBe(1);
    expect(check.stderr.toString()).toContain("managed skill remains upstream-owned");
  });
});
