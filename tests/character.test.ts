import { describe, expect, it } from "vitest";
import roster from "../assets/data/characters.json";
import tuning from "../assets/data/tuning.json";
import { applyCharacter, type Character } from "../src/vehicles/character";

const base = tuning.vehicle;
const scale = tuning.stats;
const find = (id: string) => roster.characters.find((c) => c.id === id) as Character;

describe("characters.json", () => {
  it("rates every stat between 1 and 5 and has a valid default", () => {
    for (const c of roster.characters) {
      for (const v of [c.speed, c.accel, c.handling]) {
        expect(v).toBeGreaterThanOrEqual(1);
        expect(v).toBeLessThanOrEqual(5);
      }
      expect(c.color).toMatch(/^#[0-9a-fA-F]{6}$/);
    }
    expect(find(roster.default)).toBeDefined();
  });

  it("makes the speedster the fastest and quickest to accelerate", () => {
    const all = roster.characters.map((c) => applyCharacter(base, c as Character, scale));
    const speedster = applyCharacter(base, find("speedster"), scale);
    expect(speedster.topSpeed).toBe(Math.max(...all.map((k) => k.topSpeed)));
    expect(speedster.accel).toBe(Math.max(...all.map((k) => k.accel)));
  });

  it("lets other characters out-handle the speedster", () => {
    const speedster = applyCharacter(base, find("speedster"), scale);
    const nimble = applyCharacter(base, find("nimble"), scale);
    expect(nimble.turnRate).toBeGreaterThan(speedster.turnRate);
    expect(Math.abs(nimble.driftTurnCounter)).toBeGreaterThan(Math.abs(speedster.driftTurnCounter));
  });
});

describe("applyCharacter", () => {
  it("leaves the base kart unchanged for an all-3s character", () => {
    const flat = { id: "x", name: "x", color: "#000000", speed: 3, accel: 3, handling: 3 };
    expect(applyCharacter(base, flat, scale)).toEqual(base);
  });
});
