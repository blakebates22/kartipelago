// The Prehistoric World courses: each loads, and the race's own AI drives three full
// laps on it, through every checkpoint, with the surfaces applied, without falling out
// of the world or getting stuck.
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { WORLDS } from "../src/game/worlds";
import { trackById } from "../src/game/tracks";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const COURSES = WORLDS.find((w) => w.id === "prehistoric")!.tracks;
// The longest lap allowed (seconds). Ember Peak is the epic one: 2.4 km round, up, into
// and down its volcano.
const MAX_LAP: Record<string, number> = { ember_peak: 120 };

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

describe.each(COURSES)("%s", (id) => {
  it("is a Blender package listed in the registry", () => {
    expect(trackById(id)?.load.packageId).toBe(id);
    expect(existsSync(new URL(`../public/tracks/${id}/route.json`, import.meta.url))).toBe(true);
  });

  it("loads cleanly, with zippers, bananas and balloons placed", async () => {
    const p = await loadTrackPackage(reader(id), { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.meta.race?.laps).toBe(3);
    expect(p.trackData.zippers?.length).toBeGreaterThan(0);
    expect(p.trackData.bananas?.length).toBeGreaterThan(0);
    expect(p.trackData.balloons?.length).toBeGreaterThan(0);
    // Wide enough to race: at least 12 m (six to seven karts abreast) everywhere.
    expect(Math.min(...p.trackData.points.map((q) => q.width ?? 0))).toBeGreaterThanOrEqual(12);
  });

  it("can be driven: three AI laps through every checkpoint", async () => {
    const p = await loadTrackPackage(reader(id), { visual: false });
    const max = MAX_LAP[id] ?? 90;
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: max + 10 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(25);
      expect(t).toBeLessThan(max);
    }
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(150);
  }, 120000);
});
