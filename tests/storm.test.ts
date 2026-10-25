// The thunderstorm (game/storm.ts): its settings parse with sane limits, and a strike
// flashes twice and fades.
import { describe, expect, it } from "vitest";
import { flashAt, parseStorm } from "../src/game/storm";
import { SURFACES } from "../src/world/trackPackage";

describe("storm", () => {
  it("parses with sane limits", () => {
    const s = parseStorm({ period: 1, spread: 9, distance: 10 });
    expect(s.period).toBe(2);
    expect(s.spread).toBeLessThan(s.period);
    expect(s.distance).toBe(200);
    expect(parseStorm({}).period).toBe(9);
  });

  it("flashes twice and fades", () => {
    expect(flashAt(-0.1)).toBe(0);
    expect(flashAt(0.03)).toBe(1);
    expect(flashAt(0.1)).toBeLessThan(0.3);
    expect(flashAt(0.16)).toBeGreaterThan(0.5);
    expect(flashAt(1.5)).toBeLessThan(0.01);
  });
});

describe("Emberdeep's ground", () => {
  it("rubble handles exactly like deep snow (without the powder)", () => {
    const pick = (k: string) => {
      const s = SURFACES[k]!;
      return [s.road, s.speed, s.accel, s.grip];
    };
    expect(pick("rubble")).toEqual(pick("deep_snow"));
  });
});
