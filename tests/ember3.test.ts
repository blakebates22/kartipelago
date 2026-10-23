// Ember Peak v3, the greybox of the redo (tools/blender/prehistoric/ember_v3.py): a short,
// fast lap with a big jump over the lava river, a cave through the volcano and the
// dragon from beyond the valley.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { parseIslesDragon } from "../src/game/isles";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "ember_peak_v3";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Ent = { type: string } & Record<string, unknown>;

describe("Ember Peak v3 (greybox)", () => {
  it("loads cleanly: a short lap, wide everywhere, with the jump's respawn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    const ents = (p.meta.entities ?? []) as Ent[];
    expect(ents.some((e) => e.type === "respawn")).toBe(true);
    expect(Math.min(...p.trackData.points.map((q) => q.width ?? 0))).toBeGreaterThanOrEqual(14);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(3);
  });

  it("has the dragon from beyond the valley, flying the whole lap", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const e = ((p.meta.entities ?? []) as Ent[]).find((x) => x.type === "isles_dragon")!;
    const d = parseIslesDragon(e)!;
    expect(d.keys.length).toBeGreaterThanOrEqual(6);
  });

  it("an AI lap clears the jump every time and takes about 30 seconds", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 60 });
    const laps = r.race.racers[0]!.lapTimes;
    expect(laps.length).toBe(3);
    expect(r.respawns).toBe(0);
    // A flying lap (not the first, from the grid).
    const lap = laps[2]!;
    expect(lap).toBeGreaterThan(24);
    expect(lap).toBeLessThan(42);
  }, 120_000);
});
