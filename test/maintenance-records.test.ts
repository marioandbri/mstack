import { expect, test } from "bun:test";
import { resolve } from "node:path";

test("maintenance runtime preserves originals and evaluation artifacts through public operations", () => {
  const runtime = resolve(import.meta.dir, "../skills/reflect/runtime");
  const extras = process.env.MSTACK_GEMMA_MODEL_PATH ? ["--extra", "embeddings"] : [];
  const result = Bun.spawnSync(["uv", "run", "--locked", "--project", runtime, ...extras, "python", "-m", "unittest", "discover", "-s", "test/maintenance_records", "-v"], {
    cwd: resolve(import.meta.dir, ".."),
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", PYTHONPATH: runtime },
    stdout: "pipe", stderr: "pipe",
  });
  if (result.exitCode !== 0) throw new Error(result.stderr.toString());
  expect(result.exitCode).toBe(0);
  expect(result.stderr.toString()).toContain("OK");
}, process.env.MSTACK_GEMMA_MODEL_PATH ? 180_000 : 60_000);
