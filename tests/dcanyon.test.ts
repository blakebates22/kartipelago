// Dragon Canyon (Dragon Kingdom, course 2): the Dragon Kingdom's second course with its
// own theme and music; it loads cleanly with its frontier (the dragon, the workers and
// guards, the cranes, waterfalls, the air); it turns harder per kilometre than any other
// course, with at least five hairpins; its roads never touch where they pass over and
// under each other; the lap runs through every part in order; the Quarry Service Road
// counts as the stretch it skips; drifting really is the fast way round; and the AI
// drives it cleanly.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { parseAtmosphere } from "../src/game/depths";
import { craneLoad, parseCrane, parseVillagers } from "../src/game/isles";
import { trackById } from "../src/game/tracks";
import { VISIBLE_WORLDS, WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader, type TrackPackage } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "dragon_canyon";
const readerFor =
  (track: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${track}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
const reader = readerFor(id);
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

const servicePath = (p: TrackPackage) =>
  p.route.routes
    .find((r) => r.id === "Quarry Service Road Path")!
    .points.map((q) => ({ x: q.x, y: q.y, z: q.z }));

/** Degrees of turning per kilometre of the main route, and its hairpins (150°+ of
 * turning within 110 m). */
function twistiness(points: { x: number; z: number }[]) {
  const n = points.length;
  const head: number[] = [];
  const seg: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = points[i]!;
    const b = points[(i + 1) % n]!;
    head.push(Math.atan2(b.x - a.x, b.z - a.z));
    seg.push(Math.hypot(b.x - a.x, b.z - a.z));
  }
  const turn: number[] = [];
  let total = 0;
  let length = 0;
  for (let i = 0; i < n; i++) {
    let d = head[(i + 1) % n]! - head[i]!;
    d = ((((d + Math.PI) % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2)) - Math.PI;
    turn.push(d);
    total += Math.abs(d);
    length += seg[i]!;
  }
  // Hairpins: windows of 110 m whose turning sums past 150° one way.
  let hairpins = 0;
  let i = 0;
  while (i < n) {
    let sum = 0;
    let len = 0;
    let j = i;
    let found = false;
    while (len < 110 && j < i + n) {
      sum += turn[j % n]!;
      len += seg[j % n]!;
      if (Math.abs(sum) > (150 * Math.PI) / 180) {
        found = true;
        break;
      }
      j++;
    }
    if (found) {
      hairpins++;
      i = j + 1;
    } else i++;
  }
  return { perKm: ((total * 180) / Math.PI / length) * 1000, hairpins, length };
}

describe("Dragon Canyon", () => {
  it("is the Dragon Kingdom's second course, with its own theme and music", async () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks).toEqual(["dragon_isles", id]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe(id);
    expect(SONGS[t.music]?.id).toBe("dragon_canyon");
    expect(SONGS.dragon_canyon!.bpm).toBeGreaterThan(SONGS.dragon!.bpm);
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.look.sun?.intensity).toBeGreaterThan(2);
  });

  it("loads cleanly, with its frontier and the Service Road's twin gate", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(6);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(10);
    const es = entitiesOf(p);
    const n = (f: (e: Entity) => boolean) => es.filter(f).length;
    expect(n((e) => e.type === "isles_dragon")).toBe(1);
    expect(n((e) => e.type === "crane")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "waterfall")).toBeGreaterThanOrEqual(2);
    expect(n((e) => e.type === "dust")).toBe(1);
    expect(n((e) => e.type === "dustwind")).toBe(1);
    expect(n((e) => e.type === "glow")).toBeGreaterThan(10);
    const people = parseVillagers(es.find((e) => e.type === "villagers")!);
    for (const r of ["worker", "hauler", "guard"] as const)
      expect(people.filter((v) => v.role === r).length, r).toBeGreaterThanOrEqual(3);
    const atm = parseAtmosphere(es.find((e) => e.type === "atmosphere")!);
    expect(atm.zones.quarry!.sound).toBe("quarry");
    expect(atm.zones.caverns!.sun).toBeLessThan(1);
    expect(p.route.routes.some((q) => q.id === "Quarry Service Road Path")).toBe(true);
    const routes = new Set((p.trackData.gates ?? []).map((g) => g.route));
    expect(routes.has("service_road")).toBe(true);
    // The cranes lift and lower their loads, which stay well clear of the ground.
    for (const e of es.filter((x) => x.type === "crane")) {
      const c = parseCrane(e);
      const lows = [0, 1, 2, 3, 4, 5].map((t) => craneLoad(c, t * c.period * 0.1).block.y);
      expect(Math.max(...lows) - Math.min(...lows)).toBeGreaterThan(2);
    }
  });

  it("turns harder per kilometre than any other course in the game, with at least five hairpins", async () => {
    const mine = twistiness((await loadTrackPackage(reader, { visual: false })).trackData.points);
    expect(mine.hairpins).toBeGreaterThanOrEqual(5);
    const others = VISIBLE_WORLDS.flatMap((w) => w.tracks).filter((t) => t !== id);
    for (const t of others) {
      const p = await loadTrackPackage(readerFor(t), { visual: false }).catch(() => undefined);
      if (!p) continue;
      const theirs = twistiness(p.trackData.points);
      expect(mine.perKm, `${t}: ${theirs.perKm.toFixed(0)}°/km`).toBeGreaterThan(theirs.perKm);
    }
  }, 120000);

  it("never lets its roads touch where they pass over and under each other", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const ss = track.samples;
    for (let i = 0; i < ss.length; i += 2)
      for (let j = i + 2; j < ss.length; j += 2) {
        const a = ss[i]!;
        const b = ss[j]!;
        const along = Math.min(Math.abs(a.dist - b.dist), track.length - Math.abs(a.dist - b.dist));
        if (along < 60) continue;
        const d = Math.hypot(a.pos.x - b.pos.x, a.pos.z - b.pos.z);
        if (d < (a.width + b.width) / 2 + 3)
          expect(
            Math.abs(a.pos.y - b.pos.y),
            `at ${a.dist.toFixed(0)} / ${b.dist.toFixed(0)}`,
          ).toBeGreaterThan(9);
      }
  });

  it("counts the Quarry Service Road as the stretch it skips", async () => {
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
    const cut = servicePath(p);
    const sIn = along(cut[0]!.x, cut[0]!.y, cut[0]!.z);
    const sOut = along(cut.at(-1)!.x, cut.at(-1)!.y, cut.at(-1)!.z);
    expect(sOut - sIn).toBeGreaterThan(60);
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
      carry += 22 * dt;
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

  it("drives cleanly: three AI laps, no falls, few scrapes", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(LAP_MIN);
      expect(t).toBeLessThan(LAP_MAX);
    }
    expect(r.respawns).toBe(0);
    expect(r.surfaces.has("deep_water")).toBe(false);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(400);
  }, 300000);

  it("rewards drifting: the AI laps faster drifting than steering every corner", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const drifting = await aiLap(p, { laps: 2, surfaces: true, lapSeconds: 160 });
    const steering = await aiLap(p, { laps: 2, surfaces: true, lapSeconds: 160, ai: { drift: 0 } });
    const d = drifting.race.racers[0]!.lapTimes[1]!;
    const s = steering.race.racers[0]!.lapTimes[1]!;
    expect(steering.race.racers[0]!.lapTimes).toHaveLength(2);
    // (The AI's drifting is cautious; a player chaining drifts gains far more.)
    expect(s - d, `drifting ${d.toFixed(1)} s, steering ${s.toFixed(1)} s`).toBeGreaterThan(0.3);
  }, 400000);
});

const LAP_MIN = 80;
const LAP_MAX = 110;
