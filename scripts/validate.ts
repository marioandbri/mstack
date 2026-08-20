import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

type SkillRecord = {
  name: string;
  owner: "original" | "forked";
  source: string;
  sourcePath: string;
  importRef: string;
  license: string;
};

type Manifest = {
  schemaVersion: number;
  targets: string[];
  skills: SkillRecord[];
};

export type ValidationResult = {
  errors: string[];
  skillCount: number;
  markdownCount: number;
};

function frontmatterValue(frontmatter: string, key: string): string {
  const lines = frontmatter.split("\n");
  const prefix = `${key}:`;
  const index = lines.findIndex((line) => line.startsWith(prefix));
  if (index === -1) return "";

  const raw = lines[index]!.slice(prefix.length).trim();
  if (raw === ">" || raw === "|") {
    const values: string[] = [];
    for (const line of lines.slice(index + 1)) {
      if (/^[a-zA-Z][\w-]*:/.test(line)) break;
      if (line.trim()) values.push(line.trim());
    }
    return values.join(raw === ">" ? " " : "\n");
  }

  return raw.replace(/^(["'])(.*)\1$/, "$2");
}

function markdownFiles(root: string): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...markdownFiles(path));
    else if (entry.isFile() && entry.name.endsWith(".md")) files.push(path);
  }
  return files;
}

function validateMarkdownLinks(file: string, errors: string[]): void {
  const text = readFileSync(file, "utf8").replace(/^(```|~~~)[^\n]*\n[\s\S]*?^\1\s*$/gm, "");
  const linkPattern = /\[[^\]]*\]\(([^)]+)\)/g;
  for (const match of text.matchAll(linkPattern)) {
    const target = match[1]!.trim().replace(/^<|>$/g, "");
    if (!target || target.startsWith("#") || /^[a-z]+:/i.test(target)) continue;
    const withoutAnchor = target.split("#", 1)[0]!;
    if (!withoutAnchor || /[?*]/.test(withoutAnchor)) continue;
    const resolved = resolve(dirname(file), decodeURIComponent(withoutAnchor));
    if (!existsSync(resolved)) errors.push(`${relative(process.cwd(), file)}: broken link ${target}`);
  }
}

export function validateRepository(root: string): ValidationResult {
  const errors: string[] = [];
  const manifestPath = join(root, "skills.json");
  if (!existsSync(manifestPath)) return { errors: ["skills.json is missing"], skillCount: 0, markdownCount: 0 };

  let manifest: Manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, "utf8")) as Manifest;
  } catch (error) {
    return { errors: [`skills.json is invalid: ${String(error)}`], skillCount: 0, markdownCount: 0 };
  }

  if (manifest.schemaVersion !== 1) errors.push(`unsupported schemaVersion ${manifest.schemaVersion}`);
  const requiredTargets = ["agents", "claude", "codex", "pi"];
  for (const target of requiredTargets) {
    if (!manifest.targets.includes(target)) errors.push(`missing target ${target}`);
  }

  const manifestNames = manifest.skills.map((skill) => skill.name);
  const uniqueNames = new Set(manifestNames);
  if (uniqueNames.size !== manifestNames.length) errors.push("skills.json contains duplicate names");

  const skillsRoot = join(root, "skills");
  const directoryNames = readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();

  for (const name of manifestNames) {
    if (!directoryNames.includes(name)) errors.push(`manifest skill missing directory: ${name}`);
  }
  for (const name of directoryNames) {
    if (!uniqueNames.has(name)) errors.push(`unmanaged skill directory: ${name}`);
  }

  let markdownCount = 0;
  for (const skill of manifest.skills) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(skill.name) || skill.name.length > 64) {
      errors.push(`${skill.name}: invalid Agent Skills name`);
    }
    if (!skill.source || !skill.sourcePath || !skill.importRef) errors.push(`${skill.name}: incomplete provenance`);
    if (skill.owner === "original" && skill.source !== "self") errors.push(`${skill.name}: original skill source must be self`);
    if (skill.owner === "forked" && skill.source === "self") errors.push(`${skill.name}: forked skill needs external source`);

    const licensePath = join(root, "licenses", `${skill.license}.txt`);
    if (!existsSync(licensePath)) errors.push(`${skill.name}: missing license notice ${skill.license}`);

    const directory = join(skillsRoot, skill.name);
    const skillFile = join(directory, "SKILL.md");
    if (!existsSync(skillFile)) {
      errors.push(`${skill.name}: SKILL.md is missing`);
      continue;
    }

    const text = readFileSync(skillFile, "utf8");
    if (!text.startsWith("---\n")) {
      errors.push(`${skill.name}: frontmatter must start on first line`);
      continue;
    }
    const closing = text.indexOf("\n---\n", 4);
    if (closing === -1) {
      errors.push(`${skill.name}: frontmatter closing delimiter missing`);
      continue;
    }
    const frontmatter = text.slice(4, closing);
    const declaredName = frontmatterValue(frontmatter, "name");
    const description = frontmatterValue(frontmatter, "description");
    if (declaredName !== skill.name) errors.push(`${skill.name}: frontmatter name is ${declaredName || "missing"}`);
    if (!description) errors.push(`${skill.name}: description is missing`);
    if (description.length > 1024) errors.push(`${skill.name}: description exceeds 1024 characters`);

    const files = markdownFiles(directory);
    markdownCount += files.length;
    for (const file of files) validateMarkdownLinks(file, errors);
  }

  for (const license of readdirSync(join(root, "licenses"))) {
    const path = join(root, "licenses", license);
    if (!statSync(path).isFile()) errors.push(`license entry is not a file: ${license}`);
  }

  return { errors, skillCount: manifest.skills.length, markdownCount };
}

if (import.meta.main) {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const result = validateRepository(root);
  if (result.errors.length) {
    for (const error of result.errors) console.error(`ERROR ${error}`);
    process.exit(1);
  }
  console.log(`PASS ${result.skillCount} skills, ${result.markdownCount} Markdown files`);
}
