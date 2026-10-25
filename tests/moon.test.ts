// Celestial Dragon Festival, painted as the Moonstone Kingdom (Dragon Kingdom, course 4;
// tools/blender/prehistoric/celestial_dragon_festival.py, moon_scenery.py): the v3
// greybox's lap, exactly (the Star Leap, the zippers); dressed (torches, crystal glows,
// the courtyard fountain, the night air); an AI gets round without falling in.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { trackById } from "../src/game/tracks";
import { WORLDS } from "../src/game/worlds";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "celestial_dragon_festival";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;

describe("Celestial Dragon Festival (Moonstone Kingdom)", () => {
  it("closes the Dragon Kingdom, painted, with the old lap kept aside", () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks.at(-1)).toBe(id);
    expect(trackById(id)!.theme).toBe("moonstone_kingdom");
    expect(trackById("celestial_dragon_festival_v2")?.load).toEqual({
      scene: "track",
      packageId: "celestial_dragon_festival_v2",
    });
  });

  it("drives as the greybox did: the Star Leap and its zippers", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBe(5);
    const es = (p.meta.entities ?? []) as Entity[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
  });

  it("is dressed: torches, crystal glows, the fountain, the night air", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("torch")).toBeGreaterThan(30);
    expect(n("glow")).toBeGreaterThan(5);
    expect(n("fountain")).toBe(1);
    expect(n("atmosphere")).toBe(1);
  });

  it("an AI gets round two laps without a respawn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(2);
    expect(r.respawns).toBe(0);
    for (const t of laps) {
      expect(t).toBeGreaterThan(60);
      expect(t).toBeLessThan(105);
    }
  }, 300_000);
});
