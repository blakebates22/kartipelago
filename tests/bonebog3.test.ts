// Bonebog Pyramid v3, the greybox of the new layout (tools/blender/prehistoric/bonebog_v3.py):
// weaving the swamp, a spiral up the great tree, a hilly pyramid with a jump over its river.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "bonebog_pyramid_v3";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Bonebog Pyramid v3 (greybox)", () => {
  it("loads cleanly, and the spiral really climbs over itself", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    const pts = p.trackData.points;
    expect(Math.max(...pts.map((q) => q.y ?? 0))).toBeGreaterThan(17);
    // Somewhere the road passes right over itself (the spiral's upper turn).
    let over = false;
    for (const a of pts)
      for (const b of pts)
        if (Math.hypot(a.x - b.x, a.z - b.z) < 4 && (a.y ?? 0) - (b.y ?? 0) > 7) over = true;
    expect(over).toBe(true);
  });

  it("an AI lap gets round without falling in, over the hall's jump too", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    expect(r.race.racers[0]!.lapTimes.length).toBe(2);
    expect(r.respawns).toBe(0);
  }, 240_000);
});
