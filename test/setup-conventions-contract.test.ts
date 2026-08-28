import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(import.meta.dir, "..");
const skillRoot = join(root, "skills", "setup-conventions-aware-engineering");

function read(name: string): string {
  return readFileSync(join(skillRoot, name), "utf8");
}

describe("setup-conventions-aware-engineering contract", () => {
  test("classifies repository posture from evidence and keeps it transient", () => {
    const skill = read("SKILL.md");
    const posture = read("REPOSITORY-POSTURE-AND-STACK.md");

    expect(skill).toContain("[REPOSITORY-POSTURE-AND-STACK.md](REPOSITORY-POSTURE-AND-STACK.md)");
    expect(posture).toContain("## Greenfield");
    expect(posture).toContain("## Brownfield");
    expect(posture).toContain("## Ambiguous evidence");
    expect(posture).toContain("Do not persist");
    expect(posture).toContain("installed skills");
    expect(posture).toContain("manifests");
    expect(posture).toContain("lockfiles");
    expect(posture).toContain("A dependency is not a convention");
    expect(posture).toContain("Do not create one document per package");
    expect(posture).toContain("official documentation");
  });

  test("uses separate safe branches for greenfield and brownfield setup", () => {
    const skill = read("SKILL.md");

    expect(skill).toContain("### Greenfield");
    expect(skill).toContain("### Brownfield");
    expect(skill).toContain("Do not create empty");
    expect(skill).toContain("route existing documents before proposing moves or merges");
    expect(skill).toContain("Show exact proposed changes before writing");
    expect(skill).toContain("After approval");
    expect(skill).toContain("only paths that exist");
    expect(skill).toContain("rerun safely");
    expect(skill).toContain("overwriting user-owned docs");
  });

  test("assigns design and architecture conventions distinct ownership", () => {
    const layout = read("DOCUMENT-LAYOUT.md");
    const map = read("DOCUMENTATION-MAP-TEMPLATE.md");

    expect(layout).toContain("`docs/conventions/design.md`");
    expect(layout).toContain("`docs/conventions/architecture.md`");
    expect(layout).toContain("UI/UX");
    expect(layout).toContain("dependency direction");
    expect(layout).toContain("Durable decisions and rationale belong in ADRs");
    expect(map).toContain("Design-system or UI change");
    expect(map).toContain("Architecture-sensitive change");
    expect(map).toContain("List only paths that exist");
    expect(map).toContain("This map does not list package manuals");
  });
});
