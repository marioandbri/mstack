import { readFileSync, writeFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { inventory } from "./maintenance/inventory";
import { auditHandoff, auditReport, prepareAudit } from "./maintenance/audit";

export function main(args = process.argv.slice(2)) {
  const { values, positionals } = parseArgs({ args, allowPositionals: true, options: { request: { type: "string" }, output: { type: "string" } } });
  if (!values.request) throw new Error("A request file is required");
  const request = JSON.parse(readFileSync(values.request, "utf8"));
  let result: unknown;
  switch (positionals[0]) {
    case "inventory": result = inventory(request); break;
    case "audit-prepare": result = prepareAudit(request.request, request.inventory); break;
    case "audit-report": result = auditReport(request.request, request.inventory, request.analysis); break;
    case "audit-handoff": result = auditHandoff(request.request, request.inventory, request.analysis, request.selected_id); break;
    default: throw new Error("Unknown maintenance operation");
  }
  const encoded = JSON.stringify(result, null, 2) + "\n";
  if (values.output) writeFileSync(values.output, encoded, { flag: "wx", mode: 0o600 });
  else process.stdout.write(encoded);
}

if (import.meta.main) {
  try { main(); } catch { console.error("Maintenance operation failed. Check the request, source access and unused output path."); process.exitCode = 1; }
}
