// The ruined courses (Adventure's treasure map challenge: each course after the dragons'
// attack): riverbend_ruins.py, cascade_ruins.py, bonebog_ruins.py. The same places,
// wrecked: shorter laps through them, offered in dev builds from each course's own menu
// entry, quicker to drive, smoke and ash in the air.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { trackById } from "../src/game/tracks";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
const lapLength = (pts: { x: number; z: number }[]) =>
  pts.reduce(
    (a, p, i) =>
      a + Math.hypot(p.x - pts[(i + 1) % pts.length]!.x, p.z - pts[(i + 1) % pts.length]!.z),
    0,
  );
type Entity = { type: string } & Record<string, unknown>;

// [course, its ruin, its theme, the longest the ruin's lap may be (of the full lap's)]
const RUINS: [string, string, string, number][] = [
  ["riverbend_palms", "riverbend_palms_ruin", "riverbend_ruins", 0.9],
  ["cascade_caverns", "cascade_caverns_ruin", "cascade_ruins", 0.92],
  ["bonebog_pyramid", "bonebog_pyramid_ruin", "bonebog_ruins", 0.92],
];

describe.each(RUINS)("%s's ruin", (full, ruin, theme, most) => {
  it("is offered from the course's own entry, in its own theme", () => {
    expect(trackById(full)!.ruin).toBe(ruin);
    expect(trackById(ruin)!.theme).toBe(theme);
  });

  it("loads cleanly: a shorter lap, smoke and ash", async () => {
    const p = await loadTrackPackage(reader(ruin), { visual: false });
    const f = await loadTrackPackage(reader(full), { visual: false });
    expect(p.warnings).toEqual([]);
    const a = lapLength(p.trackData.points);
    const b = lapLength(f.trackData.points);
    expect(a).toBeLessThan(most * b);
    expect(a).toBeGreaterThan(0.7 * b);
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("ashfall")).toBe(1);
    expect(n("campfire")).toBeGreaterThan(2);
  });

  it("an AI drives it without a respawn, well inside the full lap's time", async () => {
    const lap = async (id: string) => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 90 });
      expect(r.respawns).toBe(0);
      return r.race.racers[0]!.lapTimes[1]!;
    };
    expect(await lap(ruin)).toBeLessThan(0.93 * (await lap(full)));
  }, 300_000);
});
