// Oasis Haven v3, the greybox of the new lap (tools/blender/prehistoric/oasis_v3.py): back
// in the desert, round the pool, through the camp, round the butte, over the dune sea and
// up round the watchtower, with a palm-grove shortcut and a jump down the chute.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "oasis_haven_v3";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Oasis Haven v3 (greybox)", () => {
  it("loads cleanly, with a bright sky, and the spiral climbs over itself", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    expect(p.look.skyDome?.top).toBe("#0f8fb0");
    const pts = p.trackData.points;
    let over = false;
    for (const a of pts)
      for (const b of pts)
        if (Math.hypot(a.x - b.x, a.z - b.z) < 4 && (a.y ?? 0) - (b.y ?? 0) > 6) over = true;
    expect(over).toBe(true);
  });

  it("an AI lap gets round without a respawn, over the chute's jump too", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    expect(r.race.racers[0]!.lapTimes.length).toBe(2);
    expect(r.respawns).toBe(0);
  }, 240_000);
});
