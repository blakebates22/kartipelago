// Emberdeep Hold (Dragon Kingdom, course 3; it keeps Snow Dragon Pass's id): the v3
// greybox's lap painted as a fortress built into a dark mountain on a stormy night
// (tools/blender/prehistoric/snow_dragon_pass.py, ember_scenery.py). It drives as the
// greybox did (the jump, both other roads' gates, the zippers; deep snow became rubble,
// which handles the same); it's dressed (torches, falls, the storm, the hall's air); and
// an AI gets round without falling in.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { parseAtmosphere } from "../src/game/depths";
import { trackById } from "../src/game/tracks";
import { WORLDS } from "../src/game/worlds";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "snow_dragon_pass";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;

describe("Emberdeep Hold", () => {
  it("is the Dragon Kingdom's third course, painted, with the old lap kept aside", () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks[2]).toBe(id);
    const t = trackById(id)!;
    expect(t.name).toBe("Emberdeep Hold");
    expect(t.theme).toBe("emberdeep_hold");
    expect(trackById("snow_dragon_pass_v2")?.load).toEqual({
      scene: "track",
      packageId: "snow_dragon_pass_v2",
    });
  });

  it("drives as the greybox did: its jump, its zippers and both other roads' gates", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(5);
    const es = (p.meta.entities ?? []) as Entity[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
    for (const g of ["frozen_supply_road", "frozen_aqueduct"])
      expect(
        p.trackData.gates?.some((x) => x.route === g),
        g,
      ).toBe(true);
    // No snow left to throw powder: the off-road is rubble.
    expect(p.collision.surfaces).toContain("rubble");
    expect(p.collision.surfaces).not.toContain("deep_snow");
  });

  it("is dressed: torches, falls, the storm and the hall's air", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("torch")).toBeGreaterThan(40);
    expect(n("waterfall")).toBeGreaterThanOrEqual(4);
    expect(n("storm")).toBe(1);
    expect(n("snowfall")).toBe(0);
    const air = parseAtmosphere(es.find((e) => e.type === "atmosphere")!);
    expect(Object.keys(air.zones)).toContain("hall");
  });

  it("an AI gets round two laps without a respawn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(2);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(55);
      expect(t).toBeLessThan(100);
    }
  }, 300_000);
});
