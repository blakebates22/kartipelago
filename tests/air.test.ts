// The overworld's air (src/overworld/air.ts; Blake, Oct 28: each area of a region in its
// own course's lighting and sky): the nearest area's look holds, the two nearest blend
// evenly where they're equally far, and every region's areas have looks to lend.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { airAt, airOf, hex, mixAir } from "../src/overworld/air";
import { REGIONS } from "../src/overworld/regions";
import { trackById } from "../src/game/tracks";
import { parseLook } from "../src/world/trackPackage";

const spots = [
  { x: 0, z: 0, look: { sky: "#000000" } },
  { x: 400, z: 0, look: { sky: "#ffffff" } },
  { x: 0, z: 400, look: { sky: "#ff0000" } },
];

describe("the overworld's air", () => {
  it("holds the nearest area's look, and blends half and half halfway", () => {
    expect(airAt(spots, 10, 5)).toMatchObject({ a: 0, t: 0 });
    expect(airAt(spots, 390, 0)).toMatchObject({ a: 1, t: 0 });
    const mid = airAt(spots, 200, -50);
    expect([mid.a, mid.b].sort()).toEqual([0, 1]);
    expect(mid.t).toBeCloseTo(0.5, 5);
    // Moving across, the blend never jumps.
    let last = 0;
    for (let x = 100; x <= 300; x += 2) {
      const r = airAt(spots, x, -50);
      const share = r.a === 1 ? 1 - r.t : r.t;
      expect(Math.abs(share - last) < 0.05 || x === 100).toBe(true);
      last = share;
    }
  });

  it("mixes colours, fog and light", () => {
    const a = airOf({
      sky: "#000000",
      fog: { enabled: true, color: "#000000", near: 100, far: 500 },
    });
    const b = airOf({
      sky: "#ffffff",
      fog: { enabled: true, color: "#ffffff", near: 300, far: 900 },
    });
    const m = mixAir(a, b, 0.25);
    expect(m.sky[0]).toBeCloseTo(0.25);
    expect(m.fog.near).toBeCloseTo(150);
    expect(m.fog.far).toBeCloseTo(600);
    expect(hex("#ff8000")).toEqual([1, 128 / 255, 0]);
  });

  it("every region's courses have a look to lend (standard and ruined)", () => {
    for (const r of REGIONS.filter((r) => r.kingdom))
      for (const g of r.gateways.filter((g) => !g.boss && !g.king)) {
        const t = trackById(g.track)!;
        for (const id of [g.track, t.ruin].filter(Boolean) as string[]) {
          const look = parseLook(JSON.parse(readFileSync(`public/tracks/${id}/look.json`, "utf8")));
          expect(look.sky, id).toBeDefined();
          expect(look.fog, id).toBeDefined();
        }
      }
  });
});
