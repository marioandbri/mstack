import { expect, test } from "bun:test";
import { resolve } from "node:path";

const repository = resolve(import.meta.dir, "..");

test("snapshot installer passes real Git, temporary HOME, configuration, rollback and recovery cases", () => {
  const result = Bun.spawnSync([
    "uv", "run", "--locked", "--project", "install", "python", "-m", "unittest",
    "discover", "-s", "install", "-p", "test_mstack.py", "-v",
  ], { cwd: repository, stdout: "pipe", stderr: "pipe" });
  if (result.exitCode !== 0) {
    throw new Error(result.stderr.toString());
  }
  expect(result.exitCode).toBe(0);
  expect(result.stderr.toString()).toContain("OK");
}, 60_000);
