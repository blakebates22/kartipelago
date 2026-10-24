// Hearthglow Hollow (Frostveil Peaks, course 3): it's in the world with its own evening
// theme (with stars) and music; it loads cleanly; its moving parts are where they should
// be and keep to the race clock (snowballs and the sleigh cross the road, presents sit
// by it, the bell swings); a snowball or the sleigh is a solid bump, a present bursts (for a boost) and
// comes back; the rooftop shortcut counts as the lap it skips (and saves a lot); and the AI
// drives it, in under a minute and a half.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { createHazards, type HazardConfig, type Spot } from "../src/game/hazards";
import { bellSwing, crossingAt, parseBell, parseCrossing } from "../src/game/movers";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import type { GroundQuery } from "../src/physics/ground";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "hearthglow_hollow";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

// The rooftop shortcut (game coordinates), from hearthglow_hollow.py's roof_points(): off
// the west lane, up the alley ramp, along the rooftops, and the leap off the last roof
// onto the finish street.
const SHORTCUT: [number, number, number][] = [
  [-274.0, 4.0, -0.0],
  [-267.2, 6.5, 19.0],
  [-251.4, 10.4, 31.5],
  [-235.0, 10.4, 42.9],
  [-218.6, 10.4, 54.4],
  [-202.2, 10.4, 65.9],
  [-185.8, 10.4, 77.3],
  [-169.5, 10.4, 88.8],
  [-153.1, 10.4, 100.3],
  [-136.7, 8.9, 111.8],
  [-120.3, 8.9, 123.2],
  [-103.9, 8.9, 134.7],
  [-87.5, 8.9, 146.2],
  [-70.4, 7.4, 156.4],
  [-50.6, 7.4, 159.8],
  [-31.2, 7.4, 155.1],
  [-15.1, 7.4, 143.2],
  [-11.4, 7.4, 138.5],
  [-3.3, 3.0, 127.0],
];

describe("Hearthglow Hollow", () => {
  it("is Frostveil Peaks' third course, with its own evening theme and music", () => {
    const w = WORLDS.find((x) => x.id === "frostveil")!;
    expect(w.tracks.slice(0, 3)).toEqual(["frostveil_citadel", "snowy_summit", id]);
    const tiles = trackTilesOf(w);
    expect(tiles).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe("hearthglow");
    expect(SONGS[t.music]?.id).toBe("hearthglow");
  });

  it("loads cleanly: pickups, zippers, a jump with a catch, a climb, a starry sky", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    expect(p.trackData.bananas?.length).toBeGreaterThan(0);
    expect(p.trackData.balloons?.length).toBeGreaterThan(0);
    expect(entitiesOf(p).filter((e) => e.type === "respawn")).toHaveLength(1);
    const ys = p.trackData.points.map((q) => q.y ?? 0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(20);
    expect(Math.min(...p.trackData.points.map((q) => q.width ?? 0))).toBeGreaterThanOrEqual(13);
    expect(p.look.skyDome?.stars?.count).toBeGreaterThan(100);
  });

  it("has its moving parts where they belong", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const es = entitiesOf(p);
    const pts = p.trackData.points;
    // Does a straight path cross the road?
    const crosses = (e: Entity) => {
      const c = parseCrossing(e);
      for (let k = 0; k <= 40; k++) {
        const x = c.a.x + ((c.b.x - c.a.x) * k) / 40;
        const z = c.a.z + ((c.b.z - c.a.z) * k) / 40;
        if (pts.some((q) => Math.hypot(q.x - x, q.z - z) < 3)) return true;
      }
      return false;
    };
    const balls = es.filter((e) => e.type === "snowball");
    expect(balls.length).toBeGreaterThanOrEqual(4);
    for (const b of balls) expect(crosses(b)).toBe(true);
    const sleighs = es.filter((e) => e.type === "sleigh");
    expect(sleighs).toHaveLength(1);
    expect(crosses(sleighs[0]!)).toBe(true);
    // Presents: beside the road, off the middle of it.
    const presents = es.filter((e) => e.type === "present");
    expect(presents.length).toBeGreaterThanOrEqual(10);
    for (const g of presents) {
      let near = pts[0]!;
      let nd = Infinity;
      for (const q of pts) {
        const d = Math.hypot(q.x - (g.x as number), q.z - (g.z as number));
        if (d < nd) {
          nd = d;
          near = q;
        }
      }
      expect(nd).toBeGreaterThan((near.width ?? 15) / 2 - 1);
      expect(nd).toBeLessThan((near.width ?? 15) / 2 + 4);
    }
    expect(es.filter((e) => e.type === "bell")).toHaveLength(1);
    expect(es.filter((e) => e.type === "ornament").length).toBeGreaterThanOrEqual(8);
    expect(es.filter((e) => e.type === "lantern").length).toBeGreaterThan(20);
    expect(es.filter((e) => e.type === "chimney").length).toBeGreaterThan(20);
    expect(es.some((e) => e.type === "snowfall")).toBe(true);
  });

  it("counts the rooftop shortcut as the stretch it skips, and it saves at least 150 m", async () => {
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
    // Where the shortcut leaves and rejoins the road, along the lap.
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
    const sIn = along(SHORTCUT[0]![0], SHORTCUT[0]![2]);
    const sOut = along(SHORTCUT.at(-1)![0], SHORTCUT.at(-1)![2]);
    let roofs = 0;
    for (let i = 0; i + 1 < SHORTCUT.length; i++)
      roofs += Math.hypot(
        SHORTCUT[i + 1]![0] - SHORTCUT[i]![0],
        SHORTCUT[i + 1]![2] - SHORTCUT[i]![2],
      );
    expect(sOut - sIn - roofs).toBeGreaterThan(150);
    // One lap's path: the road to the shortcut, the shortcut, the road from it.
    const path: { x: number; y: number; z: number }[] = [];
    for (const q of track.samples)
      if (q.dist < sIn) path.push({ x: q.pos.x, y: q.pos.y, z: q.pos.z });
    for (let i = 0; i + 1 < SHORTCUT.length; i++)
      for (let f = 0; f < 1; f += 0.1) {
        const [ax, ay, az] = SHORTCUT[i]!;
        const [bx, by, bz] = SHORTCUT[i + 1]!;
        path.push({ x: ax + (bx - ax) * f, y: ay + (by - ay) * f, z: az + (bz - az) * f });
      }
    for (const q of track.samples)
      if (q.dist > sOut) path.push({ x: q.pos.x, y: q.pos.y, z: q.pos.z });
    let tookShortcut = false;
    let i = 0;
    let carry = 0;
    const speed = 24;
    for (let n = 0; n < 300 * 120 && !race.racers[0]!.finished; n++) {
      tickRace(race, dt);
      carry += speed * dt;
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
    expect(
      race.racers[0]!.lapTimes.length,
      `passed ${race.racers[0]!.passed} laps ${race.racers[0]!.lapTimes.map((t) => t.toFixed(1))}`,
    ).toBe(2);
  });

  it("can be driven: three AI laps through every checkpoint", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(55);
      expect(t).toBeLessThan(90);
    }
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(200);
  }, 240000);
});

describe("snowballs, the sleigh and the bell", () => {
  const ball = parseCrossing({
    ax: 0,
    ay: 5,
    az: 30,
    bx: 0,
    by: 1,
    bz: -30,
    r: 2.5,
    period: 8,
    offset: 1,
    travel: 4,
  });
  const sleigh = parseCrossing(
    { ax: 40, ay: 0, az: 0, bx: -40, by: 0, bz: 0, period: 13, offset: 2, travel: 5, warn: 2.5 },
    true,
  );

  it("cross on a fixed beat of the race clock, the sleigh jingling first", () => {
    const seen: string[] = [];
    for (let t = 2; t < 15; t += 0.02) {
      const ph = crossingAt(sleigh, t).phase;
      if (seen.at(-1) !== ph) seen.push(ph);
    }
    expect(seen).toEqual(["idle", "warning", "crossing"]);
    for (const t of [-1.3, 0, 7.7, 123.4]) {
      const a = crossingAt(ball, t);
      const b = crossingAt(ball, t + 8 * 11);
      expect(b.phase).toBe(a.phase);
      expect(b.u).toBeCloseTo(a.u, 6);
    }
    // Rolling from A to B, steadily.
    const mid = crossingAt(ball, 1 + 4 + 2);
    expect(mid.phase).toBe("crossing");
    expect(mid.u).toBeCloseTo(0.5, 6);
    expect(mid.z).toBeCloseTo(0, 6);
    // The road is clear most of the time.
    let busy = 0;
    for (let t = 0; t < 80; t += 0.01) if (crossingAt(sleigh, t).phase === "crossing") busy++;
    expect(busy / 8000).toBeLessThan(0.45);
  });

  it("rings the bell for a while each period, swinging", () => {
    const b = parseBell({ x: 0, y: 20, z: 0, period: 14, offset: 3, ring: 3.4 });
    expect(bellSwing(b, 3.2).ringing).toBe(true);
    expect(Math.abs(bellSwing(b, 3.3).angle)).toBeGreaterThan(0);
    expect(bellSwing(b, 10).ringing).toBe(false);
    expect(bellSwing(b, 10).angle).toBe(0);
  });

  it("bumps a kart that meets a snowball, and bursts a present driven into", () => {
    const track = buildTrack(
      {
        name: "ring",
        defaultWidth: 14,
        points: Array.from({ length: 24 }, (_, i) => ({
          x: 100 * Math.cos((i / 24) * Math.PI * 2) - 100,
          z: 100 * Math.sin((i / 24) * Math.PI * 2),
        })),
      },
      2,
    );
    const flat = {
      at: () => ({ height: 0, nx: 0, ny: 1, nz: 0, onRoad: true }),
    } as unknown as GroundQuery;
    let clock = 1 + 4 + 2; // the snowball is half-way across, at z = 0
    const h = createHazards({
      root: undefined as never,
      track,
      entities: [
        {
          type: "snowball",
          ax: 0,
          ay: 0,
          az: 30,
          bx: 0,
          by: 0,
          bz: -30,
          r: 2.5,
          period: 8,
          offset: 1,
          travel: 4,
        },
        { type: "present", x: 20, y: 0, z: 0, size: 2.4 },
      ],
      routes: [],
      makeGround: () => flat,
      cfg: tuning.hazards as HazardConfig,
      karts: 1,
      quiet: true,
      headless: true,
      clock: () => clock,
    });
    const gate: Spot = { x: 0, y: 0, z: -20, heading: 0 };
    h.step([], dt);
    // Its solid is where the ball is, and a kart touching it is slowed.
    const solid = h.solids.find((s) => s.x < 1e5)!;
    expect(Math.hypot(solid.x, solid.z)).toBeLessThan(0.5);
    const k = createKartState(2.5, 0, 0, 0);
    k.grounded = true;
    k.speed = 20;
    const ev = h.stepKart(0, k, "road", gate, dt);
    expect(ev.bumped).toBe(true);
    expect(k.speed).toBeLessThan(20);
    // Between rolls the ball (and its solid) is gone.
    clock = 2;
    h.step([], dt);
    expect(h.solids.every((s) => s.x > 1e5)).toBe(true);
    // The present: drive into it and it bursts (the session gives the boost); it's back later.
    const q = createKartState(20, 0, 0, 0);
    q.grounded = true;
    q.speed = 20;
    expect(h.stepKart(0, q, "road", gate, dt).smashed).toBe(true);
    expect(q.speed).toBeCloseTo(20, 5);
    expect(h.stepKart(0, q, "road", gate, dt).smashed).toBeUndefined();
    for (let t = 0; t < 15; t += 0.1) h.step([], 0.1);
    expect(h.stepKart(0, q, "road", gate, dt).smashed).toBe(true);
  });
});
