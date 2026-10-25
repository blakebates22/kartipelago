// Dragon Canyon, repainted as the Emerald Kingdom (Blake's boards, Oct 25;
// tools/blender/prehistoric/emerald.py): the same lap as the first paint (dragon_canyon_v2),
// the same surfaces under new textures, and dressed as an overgrown jungle castle: no
// villagers, no jade serpent, no desert dust; crystals glowing in the caverns, the
// jungle's fireflies; an AI drives it as before.
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

describe("Dragon Canyon (Emerald Kingdom)", () => {
  it("has its new theme, with the first paint kept aside", () => {
    expect(trackById("dragon_canyon")!.theme).toBe("emerald_kingdom");
    expect(trackById("dragon_canyon_v2")!.theme).toBe("dragon_canyon");
  });

  it("is the same lap on the same ground", async () => {
    const a = await loadTrackPackage(reader("dragon_canyon"), { visual: false });
    const b = await loadTrackPackage(reader("dragon_canyon_v2"), { visual: false });
    expect(a.warnings).toEqual([]);
    expect(a.trackData.points.length).toBe(b.trackData.points.length);
    a.trackData.points.forEach((p, i) => {
      const q = b.trackData.points[i]!;
      expect(Math.hypot(p.x - q.x, (p.y ?? 0) - (q.y ?? 0), p.z - q.z)).toBeLessThan(0.01);
    });
    expect(a.trackData.zippers?.length).toBe(b.trackData.zippers?.length);
    expect([...a.collision.surfaces].sort()).toEqual([...b.collision.surfaces].sort());
  });

  it("is dressed as the Emerald Kingdom: no villagers, serpent or dust; crystals and fireflies", async () => {
    const p = await loadTrackPackage(reader("dragon_canyon"), { visual: false });
    const es = (p.meta.entities ?? []) as Entity[];
    const n = (type: string) => es.filter((e) => e.type === type).length;
    for (const gone of ["villagers", "isles_dragon", "dust", "dustwind", "little_dragons"])
      expect(n(gone), gone).toBe(0);
    expect(n("fireflies")).toBe(1);
    expect(es.filter((e) => e.type === "glow" && e.color === "#6affa0").length).toBeGreaterThan(5);
  });

  it("an AI drives it without falling in", async () => {
    const p = await loadTrackPackage(reader("dragon_canyon"), { visual: false });
    const r = await aiLap(p, { laps: 1, surfaces: true, zippers: true, lapSeconds: 160 });
    expect(r.race.racers[0]!.lapTimes.length).toBe(1);
    expect(r.respawns).toBe(0);
  }, 300_000);
});
