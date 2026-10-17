import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";

// Guards against typos and broken values in hand-edited tuning data.
describe("tuning.json", () => {
  it("has only finite numbers, booleans or hex colors as leaf values", () => {
    for (const [group, values] of Object.entries(tuning)) {
      for (const [key, value] of Object.entries(values)) {
        const where = `${group}.${key}`;
        if (typeof value === "number") expect(Number.isFinite(value), where).toBe(true);
        else if (typeof value === "string") expect(value, where).toMatch(/^#[0-9a-fA-F]{6}$/);
        else expect(typeof value, where).toBe("boolean");
      }
    }
  });

  it("uses a sensible physics rate", () => {
    expect(tuning.loop.physicsHz).toBeGreaterThanOrEqual(30);
    expect(tuning.loop.physicsHz).toBeLessThanOrEqual(240);
  });
});
