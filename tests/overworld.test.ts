// The overworld's regions (src/overworld/regions.ts): every gateway opens a course that
// exists, ids are unique, and the trigger is a circle round the arch.
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { REGIONS, inGateway, regionById } from "../src/overworld/regions";
import { trackById } from "../src/game/tracks";
import { KINGDOMS } from "../src/adventure/data";
import { regionOfKingdom } from "../src/overworld/regions";
import { gateSolid, newPuzzleState, stepPuzzle } from "../src/overworld/puzzles";

describe("overworld regions", () => {
  it("open courses that exist, on land that exists", () => {
    for (const r of REGIONS) {
      expect(existsSync(`public/tracks/${r.packageId}/track.json`), r.id).toBe(true);
      expect(new Set(r.gateways.map((g) => g.id)).size).toBe(r.gateways.length);
      for (const g of r.gateways) expect(trackById(g.track), g.id).toBeDefined();
    }
    expect(new Set(REGIONS.map((r) => r.id)).size).toBe(REGIONS.length);
  });

  it("open a gateway's card only inside its circle", () => {
    const g = regionById("test_valley")!.gateways[0]!;
    expect(inGateway(g, g.x, g.z)).toBe(true);
    expect(inGateway(g, g.x + g.radius - 0.1, g.z)).toBe(true);
    expect(inGateway(g, g.x + g.radius + 0.1, g.z)).toBe(false);
    expect(inGateway(g, g.x + g.radius + 0.1, g.z, 3)).toBe(true);
  });

  it("gives a kingdom's region a gateway for each of its courses (Adventure tours them)", () => {
    for (const k of KINGDOMS) {
      const r = regionOfKingdom(k.id);
      if (!r) continue;
      const courses = r.gateways.filter((g) => !g.boss).map((g) => g.track);
      expect(courses.sort(), k.id).toEqual(k.courses.map((c) => c.track).sort());
      // ...and its dragon's lair.
      expect(r.gateways.find((g) => g.boss)?.track, k.id).toBe(k.boss!.track);
    }
    expect(regionOfKingdom("valley")?.id).toBe("dinosaur_valley");
  });

  it("put each puzzle's gate and switches where the region's build put them", () => {
    for (const r of REGIONS)
      for (const p of r.puzzles ?? []) {
        const meta = JSON.parse(readFileSync(`public/tracks/${r.packageId}/track.json`, "utf8"));
        const ents = (meta.entities as Record<string, unknown>[]).filter((e) => e.puzzle === p.id);
        const gate = ents.find((e) => e.type === "puzzle_gate")!;
        expect(gate, p.id).toBeDefined();
        expect(
          Math.hypot(p.gate.x - (gate.x as number), p.gate.z - (gate.z as number)),
        ).toBeLessThan(0.1);
        expect(Math.abs(p.gate.heading - (gate.heading as number))).toBeLessThan(0.01);
        expect(p.gate.width).toBe(gate.width);
        if (p.prize)
          expect(
            Math.hypot(p.prize.x - (gate.prize_x as number), p.prize.z - (gate.prize_z as number)),
          ).toBeLessThan(0.1);
        const sw = ents.filter((e) => e.type === "puzzle_switch");
        expect(sw.length, p.id).toBe(p.switches.length);
        for (const e of sw) {
          const s = p.switches[e.index as number]!;
          expect(Math.hypot(s.x - (e.x as number), s.z - (e.z as number))).toBeLessThan(0.1);
          expect(s.lanterns).toBe(e.lanterns);
        }
      }
  });
});

describe("overworld puzzles", () => {
  const p = regionById("dinosaur_valley")!.puzzles![0]!;
  const at = (i: number) => [p.switches[i]!.x, p.switches[i]!.z] as const;

  it("open the gate once every switch is pressed in time, in any order", () => {
    const st = newPuzzleState(p);
    expect(stepPuzzle(p, st, ...at(2), 0.1)).toEqual([{ kind: "press", index: 2, count: 1 }]);
    expect(st.left).toBe(p.seconds);
    stepPuzzle(p, st, 0, 0, p.seconds / 2);
    // (Standing on a pressed one again does nothing.)
    expect(stepPuzzle(p, st, ...at(2), 0.1)).toEqual([]);
    stepPuzzle(p, st, ...at(0), 0.1);
    const last = stepPuzzle(p, st, ...at(1), 0.1);
    expect(last.map((e) => e.kind)).toEqual(["press", "solved"]);
    expect(st.solved).toBe(true);
    expect(stepPuzzle(p, st, ...at(0), 0.1)).toEqual([]);
  });

  it("raise every stone again when the drums stop", () => {
    const st = newPuzzleState(p);
    stepPuzzle(p, st, ...at(0), 0.1);
    stepPuzzle(p, st, ...at(1), 0.1);
    expect(stepPuzzle(p, st, 0, 0, p.seconds).map((e) => e.kind)).toEqual(["reset"]);
    expect(st.pressed).toEqual([false, false, false]);
    expect(st.left).toBe(0);
    // Nothing runs down until one's pressed again.
    expect(stepPuzzle(p, st, 0, 0, 100)).toEqual([]);
  });

  it("start solved when the save says so, and shut the gateway with a box until then", () => {
    expect(newPuzzleState(p, true)).toEqual({
      pressed: [true, true, true],
      left: 0,
      solved: true,
      on: -1,
    });
    const b = gateSolid(p, 2);
    expect(b.halfLength).toBeGreaterThan(p.gate.width / 2);
    // Across the gateway: the box's length runs at right angles to the way the gate faces.
    expect(Math.abs(Math.cos(b.heading - p.gate.heading))).toBeLessThan(1e-9);
    expect(b.height).toBe(9);
  });
});

describe("an ordered puzzle (the Ice Bells)", () => {
  const p = regionById("snow_kingdom")!.puzzles![0]!;
  const at = (i: number) => [p.switches[i]!.x, p.switches[i]!.z] as const;

  it("opens when the bells go from the fewest lanterns to the most, with no clock", () => {
    expect(p.switches.map((s) => s.lanterns)).toEqual([1, 2, 3]);
    const st = newPuzzleState(p);
    stepPuzzle(p, st, ...at(0), 0.1);
    expect(st.left).toBe(0);
    stepPuzzle(p, st, 0, 0, 1000); // (no clock: nothing runs out)
    stepPuzzle(p, st, ...at(1), 0.1);
    expect(stepPuzzle(p, st, ...at(2), 0.1).map((e) => e.kind)).toEqual(["press", "solved"]);
  });

  it("goes quiet again at a wrong bell, and only counts a bell as you arrive at it", () => {
    const st = newPuzzleState(p);
    stepPuzzle(p, st, ...at(0), 0.1);
    expect(stepPuzzle(p, st, ...at(2), 0.1)).toEqual([{ kind: "reset", wrong: true }]);
    expect(st.pressed).toEqual([false, false, false]);
    // Sitting on it does nothing more; nor does sitting on the first after pressing it.
    expect(stepPuzzle(p, st, ...at(2), 0.1)).toEqual([]);
    stepPuzzle(p, st, ...at(0), 0.1);
    expect(stepPuzzle(p, st, ...at(0), 0.1)).toEqual([]);
    expect(st.pressed).toEqual([true, false, false]);
  });
});
