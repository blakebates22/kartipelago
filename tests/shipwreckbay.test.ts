// Shipwreck Bay, the beach world's second course (working name), a greybox
// (tools/blender/prehistoric/shipwreck_bay.py): the rolling pier, through the galleon's
// hold, up the fallen mast and its jump over the river mouth (a lap around 28 s).
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "shipwreck_bay";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Shipwreck Bay (greybox)", () => {
  it("loads cleanly, with its jump", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(3);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
    // Off the road it's soft sand (cutting across mustn't pay), the shoulders plain sand.
    expect(p.collision.surfaces).toContain("soft_sand");
    expect(p.collision.surfaces).toContain("sand");
    expect(SURFACES.soft_sand!.drag).toBeGreaterThan(2);
  });

  it("is quick: an AI's laps take about 28 s, without a respawn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 40 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(3);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(22);
      expect(t).toBeLessThan(34);
    }
  }, 120_000);
});
