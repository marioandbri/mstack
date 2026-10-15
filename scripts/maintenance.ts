import { readFileSync, writeFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { inventory } from "./maintenance/inventory";

export function main(args = process.argv.slice(2)) {
  const { values, positionals } = parseArgs({ args, allowPositionals: true, options: { request: { type: "string" }, output: { type: "string" } } });
  if (positionals[0] !== "inventory" || !values.request) throw new Error("Usage: bun scripts/maintenance.ts inventory --request REQUEST.json [--output REPORT.json]");
  const result = inventory(JSON.parse(readFileSync(values.request, "utf8")));
  const encoded = JSON.stringify(result, null, 2) + "\n";
  if (values.output) writeFileSync(values.output, encoded, { flag: "wx", mode: 0o600 });
  else process.stdout.write(encoded);
}

if (import.meta.main) {
  try { main(); } catch { console.error("Maintenance operation failed. Check the request, source access and unused output path."); process.exitCode = 1; }
}
