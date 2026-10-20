// Ember Peak, the Volcanic Apocalypse: a real climb up the volcano, a long drive
// through its caverns, the dragon's fire on its bridge, the eruption, and its own music.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { SONGS } from "../src/audio/songs";
import { dragonPhase, parseDragon } from "../src/game/dragon";
import { trackById } from "../src/game/tracks";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";

const id = "ember_peak";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Ent = { type: string } & Record<string, unknown>;

describe("Ember Peak", () => {
  it("is still in the Prehistoric World, with its own soundtrack", () => {
    const t = trackById(id)!;
    expect(t.load.packageId).toBe(id);
    expect(SONGS[t.music]!.bpm).toBeGreaterThanOrEqual(145);
    expect(SONGS[t.music]!.bpm).toBeLessThanOrEqual(165);
  });

  it("loads cleanly, and really climbs the volcano", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    const ys = p.trackData.points.map((q) => q.y ?? 0);
    expect(Math.min(...ys)).toBeLessThan(5);
    expect(Math.max(...ys)).toBeGreaterThan(70);
    // Five to seven karts wide nearly everywhere.
    expect(Math.min(...p.trackData.points.map((q) => q.width ?? 0))).toBeGreaterThanOrEqual(14);
  });

  it("spends 15-25 seconds inside the mountain", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const pts = p.trackData.points;
    // The volcano stands on the origin; its heart (where the caverns are) is a rock
    // 192 m round the middle. Every metre of road in there is under the mountain.
    let inside = 0;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1]!;
      const q = pts[i]!;
      if (Math.hypot(q.x, q.z) < 192) inside += Math.hypot(q.x - a.x, q.z - a.z);
    }
    // At racing speed (about 22 m/s): 15-25 s.
    expect(inside / 22).toBeGreaterThan(15);
    expect(inside / 22).toBeLessThan(25);
  });

  it("has the dragon breathing fire across its bridge, and the eruption", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const ents = (p.meta.entities ?? []) as Ent[];
    const dragon = ents.find((e) => e.type === "dragon")!;
    expect(dragon).toBeDefined();
    const d = parseDragon(dragon);
    // The burn zone sits on the road, across all of it.
    const road = p.trackData.points.reduce((b, q) =>
      Math.hypot(q.x - d.fire.x, q.z - d.fire.z) < Math.hypot(b.x - d.fire.x, b.z - d.fire.z)
        ? q
        : b,
    );
    expect(Math.hypot(road.x - d.fire.x, road.z - d.fire.z)).toBeLessThan(2);
    expect(d.fire.width).toBeGreaterThanOrEqual((road.width ?? 14) + 2);
    expect(Math.abs((road.y ?? 0) - d.fire.y)).toBeLessThan(1);
    // A warning before every breath, and fire less than a third of the time.
    let fire = 0;
    for (let t = 0; t < 90; t += 0.01) if (dragonPhase(d, t).phase === "breathing") fire++;
    expect(fire / 9000).toBeLessThan(0.33);
    expect(d.warn).toBeGreaterThanOrEqual(1.5);
    for (const t of ["eruption", "ashfall", "steam", "torch", "respawn"])
      expect(
        ents.some((e) => e.type === t),
        t,
      ).toBe(true);
  });
});
