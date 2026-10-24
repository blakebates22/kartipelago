// Impact Depths v3, the greybox of the new lap (tools/blender/prehistoric/impact_v3.py):
// all the way down the pit's terraces to the core, and the updraft (a ride) back up to
// the rim in under 8 s.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "impact_depths_v3";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Ride = { type: string; points?: number[][]; minSpeed?: number };

describe("Impact Depths v3 (greybox)", () => {
  it("loads cleanly, goes over 100 m down, and the updraft takes under 8 s", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    const ys = p.trackData.points.map((q) => q.y ?? 0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(100);
    const ride = ((p.meta.entities ?? []) as Ride[]).find((e) => e.type === "ride")!;
    expect(ride).toBeTruthy();
    let len = 0;
    const pts = ride.points!;
    for (let i = 1; i < pts.length; i++)
      len += Math.hypot(
        pts[i]![0]! - pts[i - 1]![0]!,
        pts[i]![1]! - pts[i - 1]![1]!,
        pts[i]![2]! - pts[i - 1]![2]!,
      );
    expect(len / ride.minSpeed!).toBeLessThan(8);
  });

  it("an AI lap gets round without a respawn, up the updraft too", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 160 });
    expect(r.race.racers[0]!.lapTimes.length).toBe(2);
    expect(r.respawns).toBe(0);
  }, 240_000);
});
