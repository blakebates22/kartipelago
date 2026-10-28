/**
 * Writes the Adventure script (src/adventure/script.ts) to docs/adventure-script.txt:
 *
 *   AUDIT_FILE=tools/audit/script.audit.ts npx vitest run --config tools/audit/vitest.config.ts
 */
import { writeFileSync } from "node:fs";
import { it } from "vitest";
import { scriptText } from "../../src/adventure/script";

it("script", () => {
  writeFileSync(new URL("../../docs/adventure-script.txt", import.meta.url), scriptText());
});
