// The overworlds' villagers (src/overworld/villagers.ts): they walk about round their
// homes, never onto ground they can't stand on, get out of a kart's way, stop and look at
// you when you stop by, and every region's build gives them homes.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { createVillagers, parseHomes } from "../src/overworld/villagers";
import { REGIONS } from "../src/overworld/regions";
import type { Solid } from "../src/world/solids";

const home = { type: "villager_home", x: 0, z: 0, y: 0, r: 14, n: 3, folk: "valley", heading: 0 };

describe("villagers", () => {
  it("walk about round their home, never into the water", () => {
    const solids: Solid[] = [];
    // Water east of x = 8.
    const v = createVillagers({
      homes: parseHomes([home]),
      solids,
      ground: (x) => ({ height: 0, ok: x < 8 }),
    });
    expect(v.count).toBe(3);
    expect(solids).toHaveLength(3);
    const start = v.spots.map((s) => ({ ...s }));
    let moved = 0;
    for (let k = 0; k < 60 * 60; k++) {
      v.step(1 / 60, k / 60, { x: 500, z: 500, speed: 0 });
      for (const s of v.spots) {
        expect(s.x).toBeLessThan(8.5);
        expect(Math.hypot(s.x, s.z)).toBeLessThan(14 + 8);
      }
    }
    v.spots.forEach((s, i) => (moved += Math.hypot(s.x - start[i]!.x, s.z - start[i]!.z)));
    expect(moved).toBeGreaterThan(2);
    v.dispose();
    expect(solids).toHaveLength(0);
  });

  it("step out of a kart's way, and stop for one that's stopped (and say hello)", () => {
    const v = createVillagers({
      homes: parseHomes([{ ...home, n: 1 }]),
      solids: [],
      ground: () => ({ height: 0, ok: true }),
    });
    const p = v.spots[0]!;
    // A kart coming straight at it.
    for (let k = 0; k < 60; k++) v.step(1 / 60, k / 60, { x: p.x + 4, z: p.z, speed: 15 });
    const q = v.spots[0]!;
    expect(q.x).toBeLessThan(p.x - 0.5);
    // Stopped beside it.
    for (let k = 0; k < 30; k++) v.step(1 / 60, k / 60, { x: q.x + 3, z: q.z, speed: 0 });
    expect(v.near()?.name.length).toBeGreaterThan(2);
    expect(v.near()?.line.length).toBeGreaterThan(5);
  });

  it("have homes in every kingdom's region and every journey (standard and ruined)", async () => {
    for (const r of REGIONS.filter((r) => r.kingdom || r.journey)) {
      for (const id of [r.packageId, r.ruinPackageId].filter(Boolean) as string[]) {
        const bytes = await readFile(new URL(`../public/tracks/${id}/track.json`, import.meta.url));
        const meta = JSON.parse(new TextDecoder().decode(bytes)) as { entities: unknown[] };
        const homes = parseHomes(meta.entities);
        expect(homes.length, id).toBeGreaterThanOrEqual(r.journey ? 1 : 8);
      }
    }
  });
});
