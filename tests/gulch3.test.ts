// Dry Gulch's new lap (v3, tools/blender/prehistoric/dry_gulch.py), dressed like the first:
// through the graveyard, drifting between the buildings, the broken trestle, the ravine,
// and the haunted mine (the shortcut) a little quicker than the way round.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "dry_gulch";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Dry Gulch (the new lap)", () => {
  it("loads cleanly, with a jump on the trestle and a gate in the mine", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
    expect(p.trackData.gates?.some((g) => g.route === "haunted_mine")).toBe(true);
  });

  it("an AI lap gets round the long way without a respawn, over the broken span too", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 2, surfaces: true, zippers: true, lapSeconds: 150 });
    expect(r.race.racers[0]!.lapTimes.length).toBe(2);
    expect(r.respawns).toBe(0);
  }, 240_000);
});
