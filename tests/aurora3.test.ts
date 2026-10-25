// Aurora Rift, the second lap (tools/blender/prehistoric/aurora_rift.py, dressed by
// aurora_scenery.py): about 20% shorter, the cave's jump and loop, the frozen lake and
// the Great Rift Bridge; it drives as its greybox did.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "aurora_rift";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Aurora Rift (the second lap)", () => {
  it("loads cleanly, with its loop and its jump", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(4);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "loop")).toHaveLength(1);
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
  });

  it("an AI gets round two laps without a respawn, the loop and the jump and all", async () => {
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
