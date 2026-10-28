// The Adventure script (Blake, Oct 27: the whole script, like an actor would get):
// docs/adventure-script.txt is the story's own scenes written out, kept up to date
// (tools/audit/script.audit.ts writes it).
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { scriptText } from "../src/adventure/script";
import { SCENES } from "../src/adventure/scenes";

describe("the script", () => {
  it("has every scene, and docs/adventure-script.txt is up to date", () => {
    const text = scriptText();
    for (const id of Object.keys(SCENES)) expect(text, id).toContain(`[${id}]`);
    expect(
      readFileSync("docs/adventure-script.txt", "utf8"),
      "rewrite it: tools/audit/script.audit.ts",
    ).toBe(text);
  });
});
