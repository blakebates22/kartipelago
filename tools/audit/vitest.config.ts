// The track audits (tools/audit/): not part of `npm test`. AUDIT_FILE picks one.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: { include: [process.env.AUDIT_FILE ?? "tools/audit/oob.audit.ts"], testTimeout: 600_000 },
});
