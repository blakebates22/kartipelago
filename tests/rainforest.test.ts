// Rainforest Rush, the Tropic Isles' fourth course (it replaced Splash Lagoon: Blake, Nov 1,
// "maybe this becomes a super fast island tropical jungle course";
// tools/blender/prehistoric/rainforest_rush.py). v2, a rollercoaster (Blake, Nov 2: "this course
// has to be incredibly exciting from a driving perspective"): the Temple Leap, the Canopy Dive,
// the River Run's whoops, the Falls Cave, the Rope Bridge, the Hollow Log, the Kapok Turn, the
// Avenue of Giants' slalom, the Ruins Hairpin, the Ruins Leap, the Temple Run. Eight boost pads.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

describe("Rainforest Rush", () => {
  it("loads cleanly: its boost pads, its fireflies, its falls, the Ruins Leap", async () => {
    const p = await loadTrackPackage(reader("rainforest_rush"), { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(8);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "fireflies")).toHaveLength(1);
    expect(es.filter((e) => e.type === "waterfall").length).toBeGreaterThan(0);
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
  });

  it("is fast: an AI's laps take about 42 s, without a respawn", async () => {
    const p = await loadTrackPackage(reader("rainforest_rush"), { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 80 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(3);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(32);
      expect(t).toBeLessThan(50);
    }
  }, 180_000);
});
