// Splash Lagoon, the beach world's fourth course (working name), a greybox
// (tools/blender/prehistoric/splash_lagoon.py): the Big Curl wave loop, the slide tower's
// ramp and flume, and the lazy river's bend with its plank across (a lap near 33 s).
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "splash_lagoon";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Splash Lagoon (greybox)", () => {
  it("loads cleanly, with its loop and the plank's twin gate", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(3);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "loop")).toHaveLength(1);
    // Off the road it's soft sand (cutting across mustn't pay), the shoulders plain sand.
    expect(p.collision.surfaces).toContain("soft_sand");
    expect(p.collision.surfaces).toContain("sand");
    expect(SURFACES.soft_sand!.drag).toBeGreaterThan(2);
  });

  it("an AI's laps take about 33 s, without a respawn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 50 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(3);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(26);
      expect(t).toBeLessThan(42);
    }
  }, 120_000);
});
