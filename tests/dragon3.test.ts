// The greyboxes of the dragon courses' new laps (tools/blender/prehistoric/*_v3.py): about
// 20% shorter than the dressed courses, nearly all corners, a jump or two each.
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

const COURSES: { id: string; respawns: number; gates: string[]; lap: [number, number] }[] = [
  {
    id: "snow_dragon_pass_v3",
    respawns: 1,
    gates: ["frozen_supply_road", "frozen_aqueduct"],
    lap: [55, 100],
  },
  { id: "celestial_dragon_festival_v3", respawns: 1, gates: [], lap: [60, 105] },
];

describe.each(COURSES)("$id (greybox)", ({ id, respawns, gates, lap }) => {
  it("loads cleanly, with its jumps and the other roads' gates", async () => {
    const p = await loadTrackPackage(reader(id), { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(respawns);
    for (const g of gates)
      expect(
        p.trackData.gates?.some((x) => x.route === g),
        g,
      ).toBe(true);
  });

  it("an AI gets round two laps without a respawn, jumps and all", async () => {
    const p = await loadTrackPackage(reader(id), { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(2);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(lap[0]);
      expect(t).toBeLessThan(lap[1]);
    }
  }, 300_000);
});
