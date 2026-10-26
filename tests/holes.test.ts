// No holes in the world: from the road, walk (a 1 m grid) over every floor a kart could
// reach (stopping at walls, and at the bottom of bottomless drops, which put you back
// on the road), and check there's always ground underneath. A hole is somewhere a kart
// could drive or fall to and keep falling.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { deepestWall, floorAt } from "../src/world/collisionMesh";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

async function holes(id: string) {
  const p = await loadTrackPackage(reader(id), { visual: false });
  const m = p.collision;
  const pts = p.trackData.points;
  const key = (i: number, j: number) => i * 100000 + j;
  const seen = new Set<number>();
  const queue: [number, number, number][] = [];
  for (const q of pts) {
    const i = Math.round(q.x);
    const j = Math.round(q.z);
    const f = floorAt(m, i, j, (q.y ?? 0) + 1);
    if (f && !seen.has(key(i, j))) {
      seen.add(key(i, j));
      queue.push([i, j, f.height]);
    }
  }
  const near = (i: number, j: number) => {
    let best = Infinity;
    for (let k = 0; k < pts.length; k += 3)
      best = Math.min(best, Math.hypot(pts[k]!.x - i, pts[k]!.z - j));
    return best;
  };
  const found: string[] = [];
  for (let n = 0; n < queue.length && n < 600000; n++) {
    const [i, j, h] = queue[n]!;
    for (const [di, dj] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ] as const) {
      const a = i + di;
      const b = j + dj;
      if (seen.has(key(a, b))) continue;
      seen.add(key(a, b));
      if (deepestWall(m, a, h + 0.6, b, 0.7)) {
        seen.delete(key(a, b)); // may be reachable from another side
        continue;
      }
      const f = floorAt(m, a, b, h + 1);
      if (!f) {
        // Ground only higher up is a cliff face, not a hole.
        if (!floorAt(m, a, b, h + 60) && near(a, b) < 40) found.push(`${a},${b}`);
        continue;
      }
      const s = m.surfaces[m.floors.surf[f.tri]!] ?? "";
      if (SURFACES[s]?.respawn || near(a, b) > 45) continue;
      queue.push([a, b, f.height]);
    }
  }
  return found;
}

describe("no holes in the world", () => {
  for (const id of [
    "frostveil_citadel",
    "snowy_summit",
    "hearthglow_hollow",
    "aurora_rift",
    "aurora_rift_v2",
    "canyon_dash",
    "oasis_haven",
    "dry_gulch",
    "impact_depths",
    "impact_depths_v2",
    "dragon_isles",
    "dragon_canyon",
    "snow_dragon_pass",
    "celestial_dragon_festival",
    "loop_lab",
    "cascade_caverns",
    "bonebog_pyramid",
    "ember_peak",
    "coral_cove",
    "coral_cove_v2",
    "shipwreck_bay",
    "shipwreck_bay_v2",
    "volcano_isle",
    "volcano_isle_v2",
    "splash_lagoon",
    "splash_lagoon_v2",
  ])
    it(
      id,
      async () => {
        const h = await holes(id);
        expect(h.slice(0, 20), `${h.length} holes`).toEqual([]);
      },
      120000,
    );
});
