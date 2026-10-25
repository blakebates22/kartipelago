// Boss race prototypes (tools/blender/prehistoric/boss_races.py): one greybox per world,
// three of 3 laps and two of one long lap (track.json's race.laps, which the race uses).
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

const BOSSES: [string, number][] = [
  ["boss_prehistoric", 3],
  ["boss_snowy", 1],
  ["boss_desert", 3],
  ["boss_dragon", 1],
  ["boss_tropic", 3],
];

describe.each(BOSSES)("%s", (id, laps) => {
  it(`races ${laps} lap(s), and says so in the menus`, async () => {
    const p = await loadTrackPackage(reader(id), { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.meta.race?.laps).toBe(laps);
    expect(trackById(id)!.laps ?? 3).toBe(laps);
  });

  it("an AI drives a lap of it without a respawn", async () => {
    const p = await loadTrackPackage(reader(id), { visual: false });
    const r = await aiLap(p, { laps: 1, surfaces: true, zippers: true, lapSeconds: 150 });
    expect(r.race.racers[0]!.lapTimes.length).toBe(1);
    expect(r.respawns).toBe(0);
  }, 300_000);
});
