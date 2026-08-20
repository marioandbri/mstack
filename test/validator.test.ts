import { afterEach, describe, expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { validateRepository } from "../scripts/validate";

const roots: string[] = [];
afterEach(() => {
  for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true });
});

function fixture(markdown = "# Example\n"): string {
  const root = mkdtempSync(join(tmpdir(), "engineering-skills-validator-"));
  roots.push(root);
  mkdirSync(join(root, "skills", "example"), { recursive: true });
  mkdirSync(join(root, "licenses"));
  writeFileSync(
    join(root, "skills.json"),
    JSON.stringify({
      schemaVersion: 1,
      targets: ["agents", "claude", "codex", "pi"],
      skills: [
        {
          name: "example",
          owner: "original",
          source: "self",
          sourcePath: "skills/example",
          importRef: "initial",
          license: "MIT-Example",
        },
      ],
    }),
  );
  writeFileSync(join(root, "licenses", "MIT-Example.txt"), "MIT License\n");
  writeFileSync(
    join(root, "skills", "example", "SKILL.md"),
    `---\nname: example\ndescription: Example skill. Use for validator tests.\n---\n\n${markdown}`,
  );
  return root;
}

describe("validateRepository", () => {
  test("accepts valid Agent Skills repository", () => {
    const result = validateRepository(fixture());
    expect(result.errors).toEqual([]);
    expect(result.skillCount).toBe(1);
  });

  test("rejects broken relative links", () => {
    const result = validateRepository(fixture("Read [missing](REFERENCE.md).\n"));
    expect(result.errors.some((error) => error.includes("broken link REFERENCE.md"))).toBeTrue();
  });

  test("rejects frontmatter name mismatch", () => {
    const root = fixture();
    const path = join(root, "skills", "example", "SKILL.md");
    writeFileSync(path, "---\nname: wrong\ndescription: Wrong name. Use for tests.\n---\n");
    const result = validateRepository(root);
    expect(result.errors).toContain("example: frontmatter name is wrong");
  });
});
