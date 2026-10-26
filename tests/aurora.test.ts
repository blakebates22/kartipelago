// Aurora Rift (v2), the first lap (Snow Kingdom' course 4 until 2026-10-24): its world slot
// keeps the name; it has its own night theme (with the aurora) and music; it loads
// cleanly with the Rift Loop, its living cavern
// (falling icicles, cracking lake ice, flaring crystals, ice motes) and both shortcuts'
// twin gates; the icicles and thin ice keep to their rules; either shortcut counts as
// the lap it skips; and the AI drives it, through the Loop every lap.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { buildLoop, loopEntities, loopFrame, loopHeight } from "../src/game/loops";
import {
  icicleAt,
  icicleLanded,
  onThinIce,
  parseIcicle,
  parseThinIce,
  stepThinIce,
  THIN_ICE_PASSES,
  underIcicle,
} from "../src/game/rift";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "aurora_rift_v2";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

// The shortcuts (game coordinates), from aurora_rift.py's MONO_SHORT and LAKE_SHORT.
const CRYSTAL_ARCH: [number, number, number][] = [
  [4.0, 24.0, -80.9],
  [-11.8, 24.0, -79.9],
  [-30.8, 24.0, -81.3],
  [-49.0, 24.0, -86.9],
  [-63.4, 24.0, -93.4],
];
const THIN_ICE: [number, number, number][] = [
  [-394.3, 11.25, -136.7],
  [-422.5, 11.25, -124.1],
  [-450.7, 11.25, -111.4],
  [-478.8, 11.25, -98.8],
  [-507.0, 11.25, -86.1],
  [-535.2, 11.25, -73.5],
  [-563.3, 11.25, -60.8],
];

describe("Aurora Rift", () => {
  it("was Snow Kingdom' fourth and last course (the slot keeps the name), with its own night theme and music", () => {
    const w = WORLDS.find((x) => x.id === "frostveil")!;
    expect(w.tracks).toEqual([
      "frostveil_citadel",
      "snowy_summit",
      "hearthglow_hollow",
      "aurora_rift",
    ]);
    const tiles = trackTilesOf(w);
    expect(tiles).toHaveLength(4);
    expect(tiles.some((t) => t.comingSoon)).toBe(false);
    const t = trackById(id)!;
    expect(t.theme).toBe("aurora_rift");
    expect(SONGS[t.music]?.id).toBe("aurora");
  });

  it("loads cleanly: the Rift Loop, boosts, pickups, an aurora in the sky", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(6);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(10);
    expect(p.look.skyDome?.aurora?.count).toBeGreaterThan(3);
    expect(p.look.skyDome?.stars?.count).toBeGreaterThan(300);
    const loops = loopEntities(entitiesOf(p));
    expect(loops).toHaveLength(1);
    const lp = buildLoop(loops[0]!);
    // A big loop: over 45 m tall, a booster on entry, a minimum speed that carries you.
    expect(loopHeight(lp)).toBeGreaterThan(45);
    expect(lp.boostMult).toBeGreaterThan(1);
    expect(lp.minSpeed).toBeGreaterThan(10);
    // The game's curve is the one the Blender kit built the visible road on.
    const raw = entitiesOf(p).find((e) => e.type === "loop")!;
    for (const [s, x, y, z] of raw.probe as number[][]) {
      const f = loopFrame(lp, s!);
      expect(Math.hypot(f.px - x!, f.py - y!, f.pz - z!)).toBeLessThan(0.02);
    }
    // The living cavern.
    const es = entitiesOf(p);
    expect(es.filter((e) => e.type === "icicle" && !e.decor).length).toBeGreaterThanOrEqual(3);
    expect(es.filter((e) => e.type === "thin_ice").length).toBeGreaterThanOrEqual(3);
    expect(es.filter((e) => e.type === "shimmer").length).toBeGreaterThan(10);
    expect(es.some((e) => e.type === "sparkles")).toBe(true);
    expect(es.filter((e) => e.type === "lantern").length).toBeGreaterThan(10);
    expect(es.filter((e) => e.type === "waterfall").length).toBeGreaterThanOrEqual(3);
    // Twin gates across both shortcuts.
    const routes = new Set((p.trackData.gates ?? []).map((g) => g.route));
    expect(routes.has("crystal_arch")).toBe(true);
    expect(routes.has("thin_ice")).toBe(true);
  });

  for (const [name, cut] of [
    ["the crystal arch", CRYSTAL_ARCH],
    ["the thin ice", THIN_ICE],
  ] as const)
    it(`counts ${name} shortcut as the stretch it skips`, async () => {
      const p = await loadTrackPackage(reader, { visual: false });
      const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
      const rc = { ...tuning.race, laps: 2 };
      const race = createRace(track, rc, 1);
      const s0 = track.samples[0]!;
      const k = createKartState(s0.pos.x, s0.pos.z, track.start.heading, s0.pos.y);
      while (race.phase === "countdown") {
        tickRace(race, dt);
        stepRacer(race, 0, k, true, 0, rc, dt);
      }
      const along = (x: number, z: number) => {
        let best = track.samples[0]!;
        let bd = Infinity;
        for (const q of track.samples) {
          const d = Math.hypot(q.pos.x - x, q.pos.z - z);
          if (d < bd) {
            bd = d;
            best = q;
          }
        }
        return best.dist;
      };
      const sIn = along(cut[0]![0], cut[0]![2]);
      const sOut = along(cut.at(-1)![0], cut.at(-1)![2]);
      expect(sOut).toBeGreaterThan(sIn);
      const path: { x: number; y: number; z: number }[] = [];
      for (const q of track.samples)
        if (q.dist < sIn) path.push({ x: q.pos.x, y: q.pos.y, z: q.pos.z });
      for (let i = 0; i + 1 < cut.length; i++)
        for (let f = 0; f < 1; f += 0.1) {
          const [ax, ay, az] = cut[i]!;
          const [bx, by, bz] = cut[i + 1]!;
          path.push({ x: ax + (bx - ax) * f, y: ay + (by - ay) * f, z: az + (bz - az) * f });
        }
      for (const q of track.samples)
        if (q.dist > sOut) path.push({ x: q.pos.x, y: q.pos.y, z: q.pos.z });
      let tookShortcut = false;
      let i = 0;
      let carry = 0;
      for (let n = 0; n < 300 * 120 && !race.racers[0]!.finished; n++) {
        tickRace(race, dt);
        carry += 24 * dt;
        for (;;) {
          const a = path[i % path.length]!;
          const b = path[(i + 1) % path.length]!;
          const seg = Math.hypot(b.x - a.x, b.z - a.z);
          if (carry < seg) break;
          carry -= seg;
          i++;
        }
        const a = path[i % path.length]!;
        const b = path[(i + 1) % path.length]!;
        const f = Math.min(1, carry / Math.max(1e-6, Math.hypot(b.x - a.x, b.z - a.z)));
        k.x = a.x + (b.x - a.x) * f;
        k.y = a.y + (b.y - a.y) * f + 0.4;
        k.z = a.z + (b.z - a.z) * f;
        if (race.racers[0]!.activeRoute !== "main") tookShortcut = true;
        stepRacer(race, 0, k, true, 1, rc, dt);
      }
      expect(tookShortcut).toBe(true);
      expect(race.racers[0]!.lapTimes.length, `passed ${race.racers[0]!.passed}`).toBe(2);
    });

  it("can be driven: three AI laps, through the Loop every lap, never falling off", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(80);
      expect(t).toBeLessThan(125);
    }
    expect(r.respawns).toBe(0);
    expect(r.loopsRidden).toBe(3);
    expect(r.inverted).toBeGreaterThan(100);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(300);
  }, 240000);
});

describe("falling icicles", () => {
  const ic = parseIcicle({ x: 10, y: 20, z: 30, top: 34, period: 9, offset: 1, warn: 1.6, r: 3 });

  it("hang, shake, drop and shatter on a fixed beat of the race clock", () => {
    const seen = new Set<string>();
    let last = icicleAt(ic, 0).phase;
    const order: string[] = [];
    for (let t = 0; t < 20; t += 0.01) {
      const s = icicleAt(ic, t);
      seen.add(s.phase);
      if (s.phase !== last) order.push(s.phase);
      last = s.phase;
      expect(s.tip).toBeGreaterThanOrEqual(ic.y - 1e-9);
      expect(s.tip).toBeLessThanOrEqual(ic.top + 1e-9);
    }
    expect([...seen].sort()).toEqual(["falling", "hanging", "shattered", "warning"]);
    // Shaking always comes just before it falls, and it lands where it shatters.
    expect(order.join(" ")).toContain("warning falling shattered");
    // Exactly one landing per beat, at offset + k * period.
    let landings = 0;
    for (let t = 0; t < 90; t += dt) if (icicleLanded(ic, t, t + dt)) landings++;
    expect(landings).toBe(10);
    expect(icicleLanded(ic, 0.99, 1.01)).toBe(true);
  });

  it("only knocks a kart right under it, and never the decorative ones", () => {
    expect(underIcicle(ic, 11, 20.4, 31)).toBe(true);
    expect(underIcicle(ic, 16, 20.4, 30)).toBe(false);
    expect(underIcicle(ic, 10, 40, 30)).toBe(false);
    expect(underIcicle({ ...ic, decor: true }, 10, 20, 30)).toBe(false);
  });
});

describe("cracking lake ice", () => {
  it("cracks once per pass, gives way on the third, then freezes over again", () => {
    const p = parseThinIce({ x: 0, y: 10, z: 0, r: 6, hold: 4 }, 2);
    const on = { x: 0, y: 10.3, z: 0, grounded: true };
    const off = { x: 30, y: 10.3, z: 0, grounded: true };
    const events: string[] = [];
    const run = (karts: (typeof on)[], seconds: number) => {
      for (let t = 0; t < seconds; t += dt) {
        const ev = stepThinIce(p, karts, dt);
        if (ev) events.push(ev);
      }
    };
    // Sitting on it counts once: it's driving onto it that cracks it.
    run([on, off], 1);
    expect(p.stage).toBe(1);
    run([off, off], 0.2);
    run([on, off], 0.2);
    expect(p.stage).toBe(2);
    expect(p.broken).toBe(0);
    run([off, off], 0.2);
    run([off, on], 0.2);
    expect(p.stage).toBe(THIN_ICE_PASSES);
    expect(p.broken).toBeGreaterThan(0);
    expect(events).toEqual(["crack", "crack", "break"]);
    // While broken, more karts don't add cracks; then it freezes, whole again.
    run([on, on], 2);
    run([off, off], 3);
    expect(p.broken).toBe(0);
    expect(p.stage).toBe(0);
    expect(events.at(-1)).toBe("freeze");
  });

  it("heals slowly when left alone, and ignores karts in the air or far away", () => {
    const p = parseThinIce({ x: 0, y: 10, z: 0, r: 6 }, 1);
    stepThinIce(p, [{ x: 0, y: 10, z: 0, grounded: false }], dt);
    expect(p.stage).toBe(0);
    stepThinIce(p, [{ x: 0, y: 10, z: 0, grounded: true }], dt);
    expect(p.stage).toBe(1);
    for (let t = 0; t < 11; t += dt) stepThinIce(p, [{ x: 50, y: 10, z: 0, grounded: true }], dt);
    expect(p.stage).toBe(0);
    expect(onThinIce(p, 0, 30, 0)).toBe(false);
  });
});
