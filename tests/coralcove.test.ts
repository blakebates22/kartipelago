// Coral Cove (greybox, v2): the beach world's first course before its paint (kept aside,
// tools/blender/prehistoric/coral_cove_v2.py): a really short lap, all three laps under a
// minute; the boardwalk's jump over the channel.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "coral_cove_v2";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Coral Cove (greybox, v2)", () => {
  it("loads cleanly, with its jump", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(2);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
    // Off the road it's soft sand (cutting across mustn't pay), the shoulders plain sand.
    expect(p.collision.surfaces).toContain("soft_sand");
    expect(p.collision.surfaces).toContain("sand");
    expect(SURFACES.soft_sand!.drag).toBeGreaterThan(2);
  });

  it("is quick: an AI's three laps take under a minute, without a respawn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 40 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(3);
    expect(r.respawns).toBe(0);
    expect(laps.reduce((a, b) => a + b, 0)).toBeLessThan(60);
    for (const t of laps) expect(t).toBeGreaterThan(14);
  }, 120_000);
});
