// Coral Cove, painted (the Tropic Isles, Oct 25; tools/blender/prehistoric/coral_cove.py and
// cove_scenery.py): the greybox's lap exactly (kept as coral_cove_v2), the same surfaces
// under new textures, the same jump; Blake: "i dont want it to change at all how it feels
// whatsoever". Dressed as a sunny cove: tiki torches, gulls, the sea's sparkles.
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
type Entity = { type: string } & Record<string, unknown>;

describe("Coral Cove (painted)", () => {
  it("has its new theme, with the greybox kept aside", () => {
    expect(trackById("coral_cove")!.theme).toBe("coral_cove");
    expect(trackById("coral_cove_v2")!.theme).toBe("beach_party");
  });

  it("is the same lap on the same ground, with the same jump, pads and gates", async () => {
    const a = await loadTrackPackage(reader("coral_cove"), { visual: false });
    const b = await loadTrackPackage(reader("coral_cove_v2"), { visual: false });
    expect(a.warnings).toEqual([]);
    expect(a.trackData.points.length).toBe(b.trackData.points.length);
    a.trackData.points.forEach((p, i) => {
      const q = b.trackData.points[i]!;
      expect(Math.hypot(p.x - q.x, (p.y ?? 0) - (q.y ?? 0), p.z - q.z)).toBeLessThan(0.01);
    });
    expect(a.trackData.zippers).toEqual(b.trackData.zippers);
    expect([...a.collision.surfaces].sort()).toEqual([...b.collision.surfaces].sort());
    const ents = (p: typeof a) => (p.meta.entities ?? []) as Entity[];
    const respawn = (p: typeof a) => ents(p).filter((e) => e.type === "respawn");
    expect(respawn(a)).toEqual(respawn(b));
  });

  it("is dressed: torches, gulls and sparkles", async () => {
    const p = await loadTrackPackage(reader("coral_cove"), { visual: false });
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    expect(n("torch")).toBeGreaterThan(4);
    expect(n("birds")).toBe(2);
    expect(n("sparkles")).toBe(1);
  });

  it("an AI's laps match the greybox's", async () => {
    const lap = async (id: string) => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 40 });
      expect(r.respawns).toBe(0);
      return r.race.racers[0]!.lapTimes;
    };
    const [a, b] = [await lap("coral_cove"), await lap("coral_cove_v2")];
    a.forEach((t, i) => expect(Math.abs(t - b[i]!)).toBeLessThan(0.25));
  }, 240_000);
});
