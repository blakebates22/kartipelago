// Hearthglow Hollow (Frostveil Peaks, course 3): it's in the world with its own evening
// theme (with stars) and music; it loads cleanly; its moving parts are where they should
// be and keep to the race clock (snowballs and the sleigh cross the road, presents sit
// by it, the bell swings); a snowball or the sleigh is a solid bump, a present bursts and
// comes back; the frozen-river shortcut counts as the lap it skips; and the AI drives it.
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

// The frozen-river shortcut (game coordinates), from hearthglow_hollow.py's SHORTCUT.
const SHORTCUT: [number, number, number][] = [
  [-57, 2.6, -100],
  [-61, 2.0, -116],
  [-78, 0.2, -136],
  [-100, -1.2, -150],
  [-122, -1.4, -156],
  [-138, -1.3, -162],
  [-145, -0.6, -180],
  [-148, 1.4, -205],
  [-155, 3.0, -228],
  [-166, 3.6, -238.5],
  [-180, 3.7, -241],
];

describe("Hearthglow Hollow", () => {
  it("is Frostveil Peaks' third course, with its own evening theme and music", () => {
    const w = WORLDS.find((x) => x.id === "frostveil")!;
    expect(w.tracks).toEqual(["frostveil_citadel", "snowy_summit", id]);
    const tiles = trackTilesOf(w);
    expect(tiles).toHaveLength(4);
    expect(tiles.filter((t) => t.comingSoon)).toHaveLength(1);
    const t = trackById(id)!;
    expect(t.theme).toBe("hearthglow");
    expect(SONGS[t.music]?.id).toBe("hearthglow");
  });

  it("loads cleanly: pickups, zippers, two jumps with catches, a climb, a starry sky", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    expect(p.trackData.bananas?.length).toBeGreaterThan(0);
    expect(p.trackData.balloons?.length).toBeGreaterThan(0);
    expect(entitiesOf(p).filter((e) => e.type === "respawn")).toHaveLength(2);
    const ys = p.trackData.points.map((q) => q.y ?? 0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(40);
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

  it("counts the frozen-river shortcut as the stretch it skips", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const race = createRace(track, { ...tuning.race, laps: 2 }, 1);
    const s0 = track.samples[0]!;
    const k = createKartState(s0.pos.x, s0.pos.z, track.start.heading, s0.pos.y);
    while (race.phase === "countdown") {
      tickRace(race, dt);
      stepRacer(race, 0, k, true, 0, tuning.race, dt);
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
      stepRacer(race, 0, k, true, 1, tuning.race, dt);
    }
    expect(tookShortcut).toBe(true);
    expect(race.racers[0]!.lapTimes.length, `passed ${race.racers[0]!.passed}`).toBe(2);
  });

  it("can be driven: three AI laps through every checkpoint", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(85);
      expect(t).toBeLessThan(130);
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
    // The present: drive into it and it bursts, slowing you a little; it's back later.
    const q = createKartState(20, 0, 0, 0);
    q.grounded = true;
    q.speed = 20;
    expect(h.stepKart(0, q, "road", gate, dt).smashed).toBe(true);
    expect(q.speed).toBeCloseTo(18, 5);
    expect(h.stepKart(0, q, "road", gate, dt).smashed).toBeUndefined();
    for (let t = 0; t < 15; t += 0.1) h.step([], 0.1);
    expect(h.stepKart(0, q, "road", gate, dt).smashed).toBe(true);
  });
});
