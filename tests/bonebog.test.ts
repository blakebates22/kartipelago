// Bonebog Pyramid: raised, railed routes over deep swamp water, and a long drive
// straight through the pyramid. It loads cleanly; the swamp water puts you back on the
// road; nearly every raised stretch is fenced in; about ten seconds of the lap is
// inside the pyramid; and the race's AI drives three clean laps.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import { deepestWall, floorAt } from "../src/world/collisionMesh";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { trackById } from "../src/game/tracks";
import { aiLap } from "./aiLap";

const id = "bonebog_pyramid";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

describe("Bonebog Pyramid", () => {
  it("is listed with its swamp theme and loads cleanly, with plenty to pick up", async () => {
    expect(trackById(id)?.theme).toBe("bonebog_swamp");
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(4);
    expect(p.trackData.bananas?.length).toBeGreaterThanOrEqual(6);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(6);
    expect(Math.min(...p.trackData.points.map((q) => q.width ?? 0))).toBeGreaterThanOrEqual(14);
    const types = new Set((p.meta.entities ?? []).map((e) => (e as { type: string }).type));
    for (const t of ["torch", "waterfall", "bubbles", "fireflies", "pterosaur"])
      expect(types.has(t), t).toBe(true);
  });

  it("is raised above deep water that puts you back, and fenced in where it's raised", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const m = p.collision;
    const pts = p.trackData.points;
    // Every road point is at least 2 m above the water.
    expect(Math.min(...pts.map((q) => q.y ?? 0))).toBeGreaterThan(2);
    let drops = 0;
    let fenced = 0;
    for (let i = 0; i < pts.length; i += 4) {
      const a = pts[i]!;
      const b = pts[(i + 1) % pts.length]!;
      const tx = b.x - a.x;
      const tz = b.z - a.z;
      const l = Math.hypot(tx, tz) || 1;
      const rx = -tz / l;
      const rz = tx / l;
      const y = a.y ?? 0;
      const half = (a.width ?? 14) / 2;
      for (const sd of [-1, 1]) {
        // Over the side: deep water (or nothing) just beyond the road?
        const ox = a.x + rx * sd * (half + 6);
        const oz = a.z + rz * sd * (half + 6);
        const f = floorAt(m, ox, oz, y);
        const s = f ? m.surfaces[m.floors.surf[f.tri]!] : undefined;
        if (f && !(s && SURFACES[s]?.respawn) && f.height > y - 1.5) continue;
        drops++;
        // A rail or wall between the road and the drop?
        for (let o = half - 0.5; o <= half + 4; o += 0.5)
          if (deepestWall(m, a.x + rx * sd * o, y, a.z + rz * sd * o, 0.7)) {
            fenced++;
            break;
          }
      }
    }
    expect(drops).toBeGreaterThan(300);
    expect(fenced / drops).toBeGreaterThan(0.97);
  });

  it("spends about ten seconds inside the pyramid", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const pts = p.trackData.points;
    // Under the pyramid there's solid stone (its stepped tiers) high overhead.
    let run = 0;
    let best = 0;
    for (let i = 1; i < pts.length * 2; i++) {
      const a = pts[(i - 1) % pts.length]!;
      const q = pts[i % pts.length]!;
      const above = floorAt(p.collision, q.x, q.z, (q.y ?? 0) + 200);
      if (above && above.height > (q.y ?? 0) + 8) run += Math.hypot(q.x - a.x, q.z - a.z);
      else run = 0;
      best = Math.max(best, run);
    }
    // ~200 m at racing speed (20-24 m/s) is a good nine or ten seconds.
    expect(best).toBeGreaterThan(180);
  });

  it("can be driven: three clean AI laps", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(55);
      expect(t).toBeLessThan(90);
    }
    expect(r.respawns).toBe(0);
  }, 120000);
});
