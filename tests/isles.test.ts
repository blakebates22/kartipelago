// Dragon Isles (Dragon Kingdom, course 1): it opens a new world with its own theme and
// music; it loads cleanly with its kingdom (the great dragon, the villagers, mill
// wheels, little dragons, waterfalls, boats, birds, the air); the lap runs through the
// festival, the cliffs, the temple, the sky paths, the harbour and the passage in
// order; the great dragon keeps pace with the race, never flies backwards and never
// comes down to the road; the villagers bow together and the guards never move; the
// Courtyard Passage counts as the lap it skips and is a real short cut; and the AI
// drives the lap in 100-130 s without falling in.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { parseAtmosphere } from "../src/game/depths";
import {
  awe,
  dragonHead,
  dragonTarget,
  DRAGON_MAX_SPEED,
  loopPoint,
  nearestSample,
  parseIslesDragon,
  parseVillagers,
  ROLES,
  stepDragon,
  villagerPose,
  type DragonFlight,
} from "../src/game/isles";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader, type TrackPackage } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "dragon_isles";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

/** The shortcut (route.json's "Courtyard Passage Path"), game coordinates. */
const passagePath = (p: TrackPackage) =>
  p.route.routes
    .find((r) => r.id === "Courtyard Passage Path")!
    .points.map((q) => ({ x: q.x, y: q.y, z: q.z }));

describe("Dragon Isles", () => {
  it("opens the Dragon Kingdom, with its own theme and music", async () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks).toEqual([id]);
    expect(w.comingSoon).toHaveLength(3);
    expect(w.hidden).toBeFalsy();
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe(id);
    expect(SONGS[t.music]?.id).toBe("dragon");
    expect(SONGS.dragon!.loop).toBe(true);
    expect(SONGS.dragon!.bpm).toBeGreaterThan(140);
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.look.sun?.intensity).toBeGreaterThan(2);
  });

  it("loads cleanly, with its whole kingdom and the Courtyard Passage's twin gate", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(6);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(10);
    const es = entitiesOf(p);
    const n = (f: (e: Entity) => boolean) => es.filter(f).length;
    expect(n((e) => e.type === "isles_dragon")).toBe(1);
    expect(n((e) => e.type === "villagers")).toBe(1);
    expect(n((e) => e.type === "waterwheel")).toBeGreaterThanOrEqual(1);
    expect(n((e) => e.type === "little_dragons")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "waterfall")).toBeGreaterThanOrEqual(4);
    expect(n((e) => e.type === "boat")).toBeGreaterThanOrEqual(1);
    expect(n((e) => e.type === "birds")).toBeGreaterThanOrEqual(3);
    expect(n((e) => e.type === "glow")).toBeGreaterThan(20);
    expect(n((e) => e.type === "motes")).toBeGreaterThanOrEqual(4);
    const people = parseVillagers(es.find((e) => e.type === "villagers")!);
    expect(people.length).toBeGreaterThan(300);
    for (const r of ROLES)
      expect(
        people.some((v) => v.role === r),
        r,
      ).toBe(true);
    const atm = parseAtmosphere(es.find((e) => e.type === "atmosphere")!);
    for (const z of ["gate", "village", "cliff", "temple", "sky", "harbour", "passage", "reveal"])
      expect(atm.zones[z], z).toBeDefined();
    expect(atm.zones.village!.sound).toBe("festival");
    expect(atm.zones.temple!.sound).toBe("garden");
    expect(atm.zones.harbour!.sound).toBe("harbour");
    expect(atm.zones.cliff!.sound).toBe("falls");
    expect(p.route.routes.some((q) => q.id === "Courtyard Passage Path")).toBe(true);
    const routes = new Set((p.trackData.gates ?? []).map((g) => g.route));
    expect(routes.has("courtyard_passage")).toBe(true);
  });

  it("runs the festival, the cliffs, the temple, the sky paths, the harbour and the passage in turn", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const pts = p.trackData.points;
    const atm = parseAtmosphere(entitiesOf(p).find((e) => e.type === "atmosphere")!);
    const zones: string[] = [];
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
      const z = key(q);
      if (zones.at(-1) !== z) zones.push(z);
    }
    expect(zones).toEqual([
      "gate",
      "village",
      "cliff",
      "temple",
      "sky",
      "harbour",
      "passage",
      "reveal",
      "gate",
    ]);
    // Up the cliffs to the highland and back down to the sea.
    const ys = pts.map((q) => q.y ?? 0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(35);
  });

  it("flies the great dragon in step with the race: forwards only, never down to the road", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const cfg = parseIslesDragon(entitiesOf(p).find((e) => e.type === "isles_dragon")!)!;
    expect(cfg.keys.length).toBeGreaterThan(10);
    const f: DragonFlight = { u: 0, speed: 20 };
    let lastU = f.u;
    let lowest = Infinity;
    let worstLag = 0;
    const step = 1 / 30;
    // Two laps at a steady 24 m/s.
    for (let t = 0; t < (2 * track.length) / 24; t += step) {
      const s = (t * 24) % track.length;
      stepDragon(cfg, f, s, step);
      expect(f.u).toBeGreaterThanOrEqual(lastU);
      expect(f.speed).toBeLessThanOrEqual(DRAGON_MAX_SPEED + 1e-6);
      lastU = f.u;
      const h = dragonHead(cfg, f.u, t);
      const i = nearestSample(track.samples, h.x, h.z, 0);
      const q = track.samples[i]!;
      if (Math.hypot(q.pos.x - h.x, q.pos.z - h.z) < 30) lowest = Math.min(lowest, h.y - q.pos.y);
      // After the first few seconds it keeps within a key or so of where it should be.
      if (t > 20) {
        const n = cfg.keys.length;
        const want = dragonTarget(cfg, s);
        const lag = Math.abs(((((want - f.u) % n) + n + n / 2) % n) - n / 2);
        worstLag = Math.max(worstLag, lag);
      }
    }
    expect(lowest).toBeGreaterThan(12);
    expect(worstLag).toBeLessThan(1.5);
    // The signature pass: straight over the long bridge, low enough to fill the sky.
    const over = cfg.keys.reduce(
      (best, k) => {
        const i = nearestSample(track.samples, k.x, k.z, 0);
        const q = track.samples[i]!;
        const d = Math.hypot(q.pos.x - k.x, q.pos.z - k.z);
        return d < best.d ? { d, up: k.y - q.pos.y } : best;
      },
      { d: Infinity, up: 0 },
    );
    expect(over.d).toBeLessThan(5);
    expect(over.up).toBeGreaterThan(15);
    expect(over.up).toBeLessThan(40);
    // The loop passes through its keys.
    const k3 = loopPoint(cfg.keys, 3);
    expect(Math.hypot(k3.x - cfg.keys[3]!.x, k3.z - cfg.keys[3]!.z)).toBeLessThan(1e-6);
  });

  it("bows together as the dragon passes, while the guards never move", () => {
    const people = parseVillagers({
      list: [
        [0, 0, 0, 0, 1, "cheer", 0],
        [5, 0, 0, 1, 0, "merchant", 3],
        [9, 0, 0, 0, 1, "guard", 1],
      ],
    });
    for (let t = 0; t < 10; t += 0.37) {
      const a = villagerPose(people[0]!, 0, t, 1);
      const b = villagerPose(people[1]!, 1, t, 1);
      expect(a.lean).toBeCloseTo(b.lean, 6);
      expect(a.lean).toBeGreaterThan(0.6);
      const g = villagerPose(people[2]!, 2, t, 1);
      expect(g).toEqual({ hop: 0, lean: 0, armL: 0, armR: 0, turn: 0 });
    }
    // Awe fades with distance and height.
    expect(awe(10, 30)).toBeGreaterThan(0.9);
    expect(awe(400, 30)).toBe(0);
    expect(awe(10, 200)).toBe(0);
  });

  it("counts the Courtyard Passage as the stretch it skips", async () => {
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
    const cut = passagePath(p);
    const sIn = along(cut[0]!.x, cut[0]!.y, cut[0]!.z);
    const sOut = along(cut.at(-1)!.x, cut.at(-1)!.y, cut.at(-1)!.z);
    expect(sOut - sIn).toBeGreaterThan(300);
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

  it("drives well: three AI laps of 100-130 s, never off into the lagoon", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(100);
      expect(t).toBeLessThan(130);
    }
    expect(r.respawns).toBe(0);
    expect(r.surfaces.has("deep_water")).toBe(false);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(300);
  }, 300000);

  it("makes the Courtyard Passage a real short cut: the AI driven through it laps faster", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const main = p.trackData.points;
    const cut = passagePath(p);
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
    const viaPassage = { ...p, trackData: { ...p.trackData, points } };
    const r = await aiLap(viaPassage, { laps: 2, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(2);
    expect(r.respawns).toBe(0);
    const mainRun = await aiLap(p, { laps: 2, surfaces: true, lapSeconds: 160 });
    const mainLap = mainRun.race.racers[0]!.lapTimes[1]!;
    const cutLap = racer.lapTimes[1]!;
    expect(mainLap - cutLap).toBeGreaterThan(2);
    expect(mainLap - cutLap).toBeLessThan(12);
  }, 400000);
});
