// Ducks on the Burnt Gorge's river (Blake, Nov 6, review journey_gorge 1 note 17: "can we
// get some high fidelity ducks swimming in the river?").
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { duckAt, duckKind, parseDucks } from "../src/game/ducks";

const stretch = parseDucks({
  type: "ducks",
  points: [
    [0, 1, 0],
    [10, 1, 0],
    [20, 1, 10],
  ],
  count: 5,
  seed: 3,
});

describe("ducks", () => {
  it("parses its stretch of water, a family of up to eight", () => {
    expect(stretch.points).toHaveLength(3);
    expect(stretch.length).toBeCloseTo(10 + Math.hypot(10, 10));
    expect(stretch.count).toBe(5);
    expect(parseDucks({ points: [[0, 0, 0]], count: 40 }).count).toBe(8);
    expect([0, 1, 2, 3].map(duckKind)).toEqual(["drake", "hen", "duckling", "duckling"]);
  });

  it("keeps them on the water, near their stretch, the ducklings close behind the hen", () => {
    for (let t = 0; t < 200; t += 1.7)
      for (let i = 0; i < stretch.count; i++) {
        const d = duckAt(stretch, i, t);
        expect(d.y).toBeCloseTo(1, 5);
        const near = Math.min(
          ...[0, 0.25, 0.5, 0.75, 1].flatMap((u) => [
            Math.hypot(d.x - 10 * u, d.z),
            Math.hypot(d.x - 10 - 10 * u, d.z - 10 * u),
          ]),
        );
        expect(near).toBeLessThan(2.5);
        if (i >= 2) {
          const hen = duckAt(stretch, 1, t);
          expect(Math.hypot(d.x - hen.x, d.z - hen.z)).toBeLessThan(0.7 * (i - 1) + 1.0);
        }
      }
  });

  it("swims up and back, now and then dabbling or looking about", () => {
    const acts = new Set<string>();
    let moved = 0;
    for (let t = 0; t < 120; t += 0.5) {
      acts.add(duckAt(stretch, 1, t).act);
      const a = duckAt(stretch, 1, t);
      const b = duckAt(stretch, 1, t + 0.5);
      moved += Math.hypot(b.x - a.x, b.z - a.z);
    }
    expect(acts).toEqual(new Set(["swim", "dabble", "look"]));
    expect(moved).toBeGreaterThan(30);
  });

  it("swims on the Burnt Gorge's river, three families of them", () => {
    const t = JSON.parse(
      readFileSync(new URL("../public/tracks/journey_gorge/track.json", import.meta.url), "utf8"),
    ) as { entities: ({ type: string } & Record<string, unknown>)[] };
    const flocks = t.entities.filter((e) => e.type === "ducks");
    expect(flocks.length).toBeGreaterThanOrEqual(3);
    // (and the rest of the pass: no lava pools floating; the waystations' travellers from
    // every world)
    expect(t.entities.filter((e) => e.type === "bubbles" && e.molten)).toHaveLength(0);
    const folk = new Set(t.entities.filter((e) => e.type === "folk_poses").map((e) => e.folk));
    for (const f of ["desert", "beach", "dragon", "pilgrim"]) expect(folk).toContain(f);
  });
});
