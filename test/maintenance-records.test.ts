import { expect, test } from "bun:test";
import { resolve } from "node:path";

test("maintenance runtime preserves originals and evaluation artifacts through public operations", () => {
  const runtime = resolve(import.meta.dir, "../skills/reflect/runtime");
  const result = Bun.spawnSync(["uv", "run", "--locked", "--project", runtime, "python", "-m", "unittest", "discover", "-s", "test/maintenance_records", "-v"], {
    cwd: resolve(import.meta.dir, ".."),
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", PYTHONPATH: runtime },
    stdout: "pipe", stderr: "pipe",
  });
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  expect(result.exitCode).toBe(0);
  expect(result.stderr.toString()).toContain("OK");
}, 60_000);
