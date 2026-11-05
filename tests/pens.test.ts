// The Beast Market's pens of hatchlings (Blake, Nov 4: "the animals look bad"; he picked
// "baby dinos in pens"): they waddle about inside their fences, stop to peck, look round,
// sit and squeak, and never get out.
import { describe, expect, it } from "vitest";
import { babyAt, parsePen, penBabies, penRng, stepPen } from "../src/game/pens";

describe("the pens", () => {
  it("reads a pen", () => {
    const c = parsePen({
      x: 1,
      y: 2,
      z: 3,
      w: 5,
      d: 4,
      heading: 0.5,
      species: "stego",
      count: 9,
      seed: 4,
    });
    expect(c).toMatchObject({
      x: 1,
      y: 2,
      z: 3,
      w: 5,
      d: 4,
      heading: 0.5,
      kind: "stego",
      count: 6,
      seed: 4,
    });
    expect(parsePen({ species: "unicorn" }).kind).toBe("raptor");
  });

  it("keeps its babies busy and inside the fence", () => {
    const c = parsePen({
      x: 10,
      z: 20,
      w: 5,
      d: 3.6,
      heading: 1.2,
      species: "raptor",
      count: 4,
      seed: 9,
    });
    const rnd = penRng(c.seed);
    const babies = penBabies(c, rnd);
    const acts = new Set<string>();
    let moved = 0;
    for (let t = 0; t < 120; t += 1 / 30) {
      const before = babies.map((b) => [b.u, b.v]);
      stepPen(c, babies, 1 / 30, rnd);
      babies.forEach((b, k) => {
        acts.add(b.act);
        moved += Math.hypot(b.u - before[k]![0]!, b.v - before[k]![1]!);
        expect(Math.abs(b.u)).toBeLessThanOrEqual(c.w / 2);
        expect(Math.abs(b.v)).toBeLessThanOrEqual(c.d / 2);
        // (and in the world, inside the pen's circle)
        const w = babyAt(c, b);
        expect(Math.hypot(w.x - c.x, w.z - c.z)).toBeLessThanOrEqual(
          Math.hypot(c.w, c.d) / 2 + 1e-6,
        );
      });
    }
    expect(moved).toBeGreaterThan(10);
    for (const a of ["walk", "peck", "look"]) expect(acts).toContain(a);
  });
});
