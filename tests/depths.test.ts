// Impact Depths (Desert World, course 4): it's the Desert World's fourth course with
// its own theme and music; it loads cleanly with its creatures and hazards (the
// obsidian dragon over the bridge, lava geysers, falling rocks and meteor debris,
// triceratops, raptors, sauropods, pterosaurs, the core, the meteors, the air); the
// lap goes down through every world in order and comes back up; the dragon's fire
// covers only part of its broad bridge; the Ancient Way counts as the lap it skips and
// is a real short cut; and the AI drives the lap in 100-130 s without falling in.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import {
  airAt,
  corePulse,
  grazerAt,
  introAt,
  parseAtmosphere,
  parseTriceratops,
} from "../src/game/depths";
import { dragonBurns, dragonPhase, inFireZone, parseDragon } from "../src/game/dragon";
import { geyserBurns, geyserLifts, parseGeyser } from "../src/game/geyser";
import { crossingAt, parseCrossing } from "../src/game/movers";
import { parseIcicle } from "../src/game/rift";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader, type TrackPackage } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "impact_depths";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

/** The shortcut (route.json's "Ancient Way Path"), game coordinates. */
const wayPath = (p: TrackPackage) =>
  p.route.routes
    .find((r) => r.id === "Ancient Way Path")!
    .points.map((q) => ({ x: q.x, y: q.y, z: q.z }));

describe("Impact Depths", () => {
  it("is the Desert World's fourth course, with its own theme and music", async () => {
    const w = WORLDS.find((x) => x.id === "desert")!;
    expect(w.tracks).toEqual(["canyon_dash", "oasis_haven", "dry_gulch", id]);
    expect(w.comingSoon ?? []).toEqual([]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe(id);
    expect(SONGS[t.music]?.id).toBe("depths");
    expect(SONGS.depths!.loop).toBe(true);
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.look.sun?.intensity).toBeGreaterThan(2);
  });

  it("loads cleanly, with every creature and hazard and the Ancient Way's twin gate", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(8);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(10);
    const es = entitiesOf(p);
    const n = (f: (e: Entity) => boolean) => es.filter(f).length;
    expect(n((e) => e.type === "dragon" && e.look === "obsidian")).toBe(1);
    expect(n((e) => e.type === "geyser" && e.lava === true)).toBeGreaterThanOrEqual(3);
    expect(n((e) => e.type === "icicle" && e.look === "rock")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "icicle" && e.look === "meteor")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "triceratops")).toBeGreaterThanOrEqual(3);
    expect(n((e) => e.type === "raptors")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "dinosaur")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "pterosaur")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "core")).toBe(1);
    expect(n((e) => e.type === "meteors" && e.intro === true)).toBe(1);
    expect(n((e) => e.type === "plume")).toBe(1);
    expect(n((e) => e.type === "waterfall")).toBeGreaterThanOrEqual(3);
    expect(n((e) => e.type === "glow")).toBeGreaterThan(20);
    expect(n((e) => e.type === "motes")).toBeGreaterThanOrEqual(5);
    const atm = parseAtmosphere(es.find((e) => e.type === "atmosphere")!);
    for (const z of [
      "desert",
      "crater",
      "crystal",
      "jungle",
      "hidden",
      "volcanic",
      "lair",
      "core",
      "ascent",
    ])
      expect(atm.zones[z], z).toBeDefined();
    expect(atm.keys.length).toBeGreaterThan(200);
    for (const r of ["Ancient Way Path", "Sauropod Path", "Lake Wade Path"])
      expect(
        p.route.routes.some((q) => q.id === r),
        r,
      ).toBe(true);
    const routes = new Set((p.trackData.gates ?? []).map((g) => g.route));
    expect(routes.has("ancient_way")).toBe(true);
  });

  it("goes down through every world in turn, and back up into the sun", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const pts = p.trackData.points;
    const atm = parseAtmosphere(entitiesOf(p).find((e) => e.type === "atmosphere")!);
    // Which world the air is mostly, at each route point, in lap order.
    const worlds: string[] = [];
    const key = (q: { x: number; y?: number; z: number }) => {
      let best = atm.keys[0]!;
      let bd = Infinity;
      for (const k of atm.keys) {
        const d = (k.x - q.x) ** 2 + (k.y - (q.y ?? 0)) ** 2 + (k.z - q.z) ** 2;
        if (d < bd) {
          bd = d;
          best = k;
        }
      }
      return best.t < 0.5 ? best.a : best.b;
    };
    for (const q of pts) {
      const w = key(q);
      if (worlds.at(-1) !== w) worlds.push(w);
    }
    expect(worlds).toEqual([
      "desert",
      "crater",
      "crystal",
      "jungle",
      "volcanic",
      "lair",
      "core",
      "ascent",
      "desert",
    ]);
    const ys = pts.map((q) => q.y ?? 0);
    expect(ys[0]).toBeGreaterThan(25);
    expect(Math.min(...ys)).toBeLessThan(-10);
    // The deepest point is in the Heart of the Earth, past the dragon.
    const deepest = ys.indexOf(Math.min(...ys));
    expect(deepest / ys.length).toBeGreaterThan(0.7);
    // Underground the sun hardly reaches; in the desert it blazes.
    const start = airAt(atm, pts[0]!.x, pts[0]!.y ?? 0, pts[0]!.z)!;
    const deep = airAt(atm, pts[deepest]!.x, ys[deepest]!, pts[deepest]!.z)!;
    expect(start.sun).toBeGreaterThan(2);
    expect(deep.sun).toBeLessThan(1);
    expect(deep.far).toBeLessThan(start.far);
  });

  it("breathes fire across part of the broad bridge, on a beat, with a warning first", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const d = parseDragon(entitiesOf(p).find((e) => e.type === "dragon")!);
    // The zone sits on the road...
    let near = track.samples[0]!;
    let bd = Infinity;
    for (const q of track.samples) {
      const dd = Math.hypot(q.pos.x - d.fire.x, q.pos.z - d.fire.z);
      if (dd < bd) {
        bd = dd;
        near = q;
      }
    }
    expect(bd).toBeLessThan(near.width / 2);
    // ...but only part of it: one edge of the road is safe while the other burns.
    const r = near.right;
    const edge = (side: number) =>
      near.pos.clone().addScaledVector(r, side * (near.width / 2 - 1.5));
    const a = edge(-1);
    const b = edge(1);
    const burnsA = inFireZone(d, a.x, a.y, a.z);
    const burnsB = inFireZone(d, b.x, b.y, b.z);
    expect(burnsA !== burnsB).toBe(true);
    // It only burns while breathing, and warns first.
    const phases: string[] = [];
    for (let t = 0; t < d.period; t += 0.05) {
      const ph = dragonPhase(d, t).phase;
      if (phases.at(-1) !== ph) phases.push(ph);
      const z = burnsA ? a : b;
      expect(dragonBurns(d, t, z.x, z.y, z.z)).toBe(ph === "breathing");
    }
    expect(phases.join(" ")).toContain("warning breathing");
  });

  it("counts the Ancient Way as the stretch it skips", async () => {
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
    const along = (x: number, y: number, z: number) => {
      let best = track.samples[0]!;
      let bd = Infinity;
      for (const q of track.samples) {
        const d = Math.hypot(q.pos.x - x, (q.pos.y - y) * 2, q.pos.z - z);
        if (d < bd) {
          bd = d;
          best = q;
        }
      }
      return best.dist;
    };
    const cut = wayPath(p);
    const sIn = along(cut[0]!.x, cut[0]!.y, cut[0]!.z);
    const sOut = along(cut.at(-1)!.x, cut.at(-1)!.y, cut.at(-1)!.z);
    expect(sOut - sIn).toBeGreaterThan(450);
    const path: { x: number; y: number; z: number }[] = [];
    for (const q of track.samples)
      if (q.dist < sIn) path.push({ x: q.pos.x, y: q.pos.y, z: q.pos.z });
    for (let i = 0; i + 1 < cut.length; i++)
      for (let f = 0; f < 1; f += 0.1) {
        const a = cut[i]!;
        const b = cut[i + 1]!;
        path.push({ x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f, z: a.z + (b.z - a.z) * f });
      }
    for (const q of track.samples)
      if (q.dist > sOut) path.push({ x: q.pos.x, y: q.pos.y, z: q.pos.z });
    let tookShortcut = false;
    let i = 0;
    let carry = 0;
    for (let n = 0; n < 400 * 120 && !race.racers[0]!.finished; n++) {
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

  it("drives well: three AI laps of 100-130 s, never off into the lava or the abyss", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(100);
      expect(t).toBeLessThan(130);
    }
    expect(r.respawns).toBe(0);
    expect(r.surfaces.has("lava")).toBe(false);
    expect(r.surfaces.has("abyss")).toBe(false);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(300);
  }, 300000);

  it("makes the Ancient Way a real short cut: the AI driven along it laps faster", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const main = p.trackData.points;
    const cut = wayPath(p);
    const near = (x: number, y: number, z: number) => {
      let bi = 0;
      let bd = Infinity;
      main.forEach((q, i) => {
        const d = Math.hypot(q.x - x, ((q.y ?? 0) - y) * 2, q.z - z);
        if (d < bd) {
          bd = d;
          bi = i;
        }
      });
      return bi;
    };
    const a = near(cut[0]!.x, cut[0]!.y, cut[0]!.z);
    const b = near(cut.at(-1)!.x, cut.at(-1)!.y, cut.at(-1)!.z);
    const points = [
      ...main.slice(0, a),
      ...cut.slice(1, -1).map((q) => ({ x: q.x, y: q.y, z: q.z, width: 11, bank: 0 })),
      ...main.slice(b + 1),
    ];
    const viaWay = { ...p, trackData: { ...p.trackData, points } };
    const r = await aiLap(viaWay, { laps: 2, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(2);
    expect(r.respawns).toBe(0);
    const mainRun = await aiLap(p, { laps: 2, surfaces: true, lapSeconds: 160 });
    const mainLap = mainRun.race.racers[0]!.lapTimes[1]!;
    const wayLap = racer.lapTimes[1]!;
    expect(mainLap - wayLap).toBeGreaterThan(2);
    expect(mainLap - wayLap).toBeLessThan(12);
  }, 400000);
});

describe("the world under the desert", () => {
  it("blends the air from one world into the next", () => {
    const atm = parseAtmosphere({
      zones: {
        a: {
          fog: "#ff0000",
          near: 100,
          far: 1000,
          sun: 3,
          sky: "#ffffff",
          ground: "#000000",
          hemi: 1,
          sound: "wind",
        },
        b: {
          fog: "#0000ff",
          near: 50,
          far: 500,
          sun: 0.2,
          sky: "#000000",
          ground: "#ffffff",
          hemi: 2,
          sound: "rumble",
        },
      },
      keys: [
        [0, 0, 0, "a", "a", 0],
        [50, 0, 0, "a", "b", 0.5],
        [100, 0, 0, "b", "b", 0],
      ],
    });
    const at = (x: number) => airAt(atm, x, 0, 0)!;
    expect(at(0).sun).toBeCloseTo(3, 0);
    expect(at(100).sun).toBeCloseTo(0.2, 0);
    // Going across, it changes steadily (no jumps).
    let prev = at(0).sun;
    for (let x = 1; x <= 100; x++) {
      const s = at(x).sun;
      expect(s).toBeLessThanOrEqual(prev + 1e-6);
      expect(prev - s).toBeLessThan(0.3);
      prev = s;
    }
    const mid = at(50);
    expect(mid.sound.wind + mid.sound.rumble).toBeCloseTo(1, 5);
    expect(mid.sound.wind).toBeGreaterThan(0.2);
    expect(mid.sound.rumble).toBeGreaterThan(0.2);
    // Bad keys and zones are skipped, not trusted.
    expect(
      parseAtmosphere({
        zones: { a: {} },
        keys: [[0, 0, 0, "a", "nope", 0], "x", [1, 2, 3, "a", "a", 0]],
      }).keys,
    ).toHaveLength(1);
  });

  it("burns karts in a lava geyser's column only while it blows", () => {
    const g = parseGeyser({
      x: 0,
      y: 0,
      z: 0,
      r: 3.6,
      height: 16,
      period: 6.5,
      warn: 1.5,
      blast: 1.6,
      launch: 0,
      lava: true,
    });
    let burnt = 0;
    let clear = 0;
    for (let t = 0; t < g.period; t += 0.05) {
      if (geyserBurns(g, t, 0, 0.5, 0)) burnt += 0.05;
      else clear += 0.05;
      expect(geyserBurns(g, t, 10, 0.5, 0)).toBe(false);
      expect(geyserLifts(g, t, 0, 0.5, 0)).toBe(false);
    }
    expect(burnt).toBeGreaterThan(1);
    expect(clear).toBeGreaterThan(4);
    expect(geyserBurns(parseGeyser({ period: 7 }), 6.5, 0, 0, 0)).toBe(false);
  });

  it("drops rocks and meteor debris on the icicles' beat", () => {
    const rock = parseIcicle({ x: 0, y: 0, z: 0, top: 20, look: "rock" });
    const meteor = parseIcicle({ x: 0, y: 0, z: 0, top: 120, look: "meteor" });
    expect(rock.look).toBe("rock");
    expect(meteor.look).toBe("meteor");
    expect(parseIcicle({ look: "lava" }).look).toBe("ice");
    // The meteor falls from much higher, so takes longer, but still leaves a clear road.
    expect(meteor.fall).toBeGreaterThan(rock.fall);
    expect(meteor.period).toBeGreaterThan(meteor.warn + meteor.fall + 2);
  });

  it("sends raptors across on a beat, chirping first, with a clear road between", () => {
    const c = parseCrossing({
      ax: 0,
      ay: 0,
      az: 0,
      bx: 40,
      by: 0,
      bz: 0,
      period: 9,
      travel: 2.2,
      warn: 1.4,
    });
    const phases = new Set<string>();
    let clear = 0;
    for (let t = 0; t < 9; t += 0.05) {
      const ph = crossingAt(c, t).phase;
      phases.add(ph);
      if (ph !== "crossing") clear += 0.05;
    }
    expect([...phases].sort()).toEqual(["crossing", "idle", "warning"]);
    expect(clear).toBeGreaterThan(5);
  });

  it("keeps the triceratops grazing round their own patch, heads down, bellowing now and then", () => {
    const c = parseTriceratops({ x: 100, y: 0, z: -50, roam: 6, seed: 2 });
    let grazed = 0;
    let bellowed = 0;
    for (let t = 0; t < 120; t += 0.1) {
      const g = grazerAt(c, t);
      expect(Math.hypot(g.x - c.x, g.z - c.z)).toBeLessThanOrEqual(c.roam + 0.01);
      if (g.graze > 0.5) grazed += 0.1;
      if (g.bellow > 0.5) bellowed += 0.1;
    }
    expect(grazed).toBeGreaterThan(30);
    expect(bellowed).toBeGreaterThan(0.5);
  });

  it("beats the core like a heart, and drops the fireball before the start", () => {
    let hi = 0;
    let lo = 1;
    for (let t = 0; t < 3.2; t += 0.02) {
      hi = Math.max(hi, corePulse(t));
      lo = Math.min(lo, corePulse(t));
    }
    expect(hi).toBeGreaterThan(0.9);
    expect(lo).toBeLessThan(0.05);
    expect(introAt(-5)).toBeNull();
    expect(introAt(-1)).not.toBeNull();
    expect(introAt(2)).toBeNull();
  });
});
