// Canyon Dash (Desert World, course 1): the Desert World opens with it (three more
// courses to come), with its own theme, mesa skyline and music; it loads cleanly with
// its waterfalls, dust, windmill, birds and the butte slot's twin gate; the slot counts
// as the lap it skips; it's fast (a desert dirt road at full speed, sand off it); and
// the AI drives it in 60-85 s a lap without ever falling into the canyon.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import {
  birdAt,
  dustRate,
  parseBirds,
  parseDust,
  parseWindmill,
  windAt,
  windmillAngle,
} from "../src/game/desert";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "canyon_dash";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

// The butte slot shortcut (game coordinates), from canyon_dash.py's BUTTE_SHORT.
const BUTTE_SLOT: [number, number, number][] = [
  [363.6, 49.77, 151.6],
  [341.7, 50.32, 150.3],
  [319.7, 50.72, 148.3],
  [297.8, 51.18, 148.5],
  [275.8, 52.18, 151.4],
  [253.9, 53.02, 154.3],
  [231.9, 53.43, 154.5],
  [210.0, 53.79, 152.5],
  [188.1, 54.22, 151.2],
];

describe("Canyon Dash", () => {
  it("opens the Desert World, with its own theme and music", () => {
    const w = WORLDS.find((x) => x.id === "desert")!;
    expect(w.tracks).toEqual([id]);
    const tiles = trackTilesOf(w);
    expect(tiles).toHaveLength(4);
    expect(tiles.filter((t) => t.comingSoon)).toHaveLength(3);
    const t = trackById(id)!;
    expect(t.theme).toBe("canyon_dash");
    expect(SONGS[t.music]?.id).toBe("canyon");
    expect(SONGS.canyon!.bpm).toBeGreaterThan(150);
  });

  it("has a fast dirt road and slower sand off it", () => {
    expect(SURFACES.packed_dirt?.road).toBe(true);
    expect(SURFACES.packed_dirt!.speed).toBe(1);
    expect(SURFACES.loose_sand?.road).toBe(false);
    expect(SURFACES.loose_sand!.speed!).toBeLessThan(0.8);
    expect(SURFACES.loose_sand!.speed!).toBeGreaterThan(SURFACES.sand!.speed!);
  });

  it("loads cleanly: boosts, pickups, waterfalls, dust, the windmill, birds, a mesa skyline", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(6);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(10);
    expect(p.look.skyDome?.hills?.style).toBe("mesas");
    const es = entitiesOf(p);
    expect(es.filter((e) => e.type === "waterfall").length).toBeGreaterThanOrEqual(4);
    expect(es.some((e) => e.type === "dust")).toBe(true);
    expect(es.some((e) => e.type === "dustwind")).toBe(true);
    expect(es.filter((e) => e.type === "windmill")).toHaveLength(1);
    expect(es.filter((e) => e.type === "birds").length).toBeGreaterThanOrEqual(3);
    const routes = new Set((p.trackData.gates ?? []).map((g) => g.route));
    expect(routes.has("butte_slot")).toBe(true);
  });

  it("counts the butte slot shortcut as the stretch it skips", async () => {
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
    const cut = BUTTE_SLOT;
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

  it("is fast: three AI laps of 60-85 s, never falling into the canyon", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 120 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(60);
      expect(t).toBeLessThan(85);
    }
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(300);
  }, 240000);
});

describe("desert life", () => {
  it("kicks up dust on dirt and sand, more with speed, none on planks or when slow", () => {
    const d = parseDust({ color: "#d89a6a" });
    expect(dustRate(d, "packed_dirt", 3)).toBe(0);
    expect(dustRate(d, "road", 25)).toBe(0);
    expect(dustRate(d, "packed_dirt", 25)).toBeGreaterThan(0);
    expect(dustRate(d, "loose_sand", 25)).toBeGreaterThan(dustRate(d, "packed_dirt", 25));
    expect(dustRate(d, "packed_dirt", 25)).toBeGreaterThan(dustRate(d, "packed_dirt", 12));
    expect(dustRate(d, undefined, 25)).toBe(0);
  });

  it("blows a steady, gusting wind, and turns the windmill with it", () => {
    for (let t = 0; t < 300; t += 7.3) {
      const w = windAt(t);
      const s = Math.hypot(w.x, w.z);
      expect(s).toBeGreaterThan(0.5);
      expect(s).toBeLessThan(10);
    }
    const c = parseWindmill({ x: 1, y: 2, z: 3, speed: 1.4 });
    expect(windmillAngle(c, 10)).toBeGreaterThan(windmillAngle(c, 0));
  });

  it("keeps the birds circling high over their spot", () => {
    const c = parseBirds({ x: 100, y: 120, z: -50, radius: 70, count: 3, speed: 0.2 });
    for (let k = 0; k < c.count; k++)
      for (let t = 0; t < 120; t += 3.1) {
        const b = birdAt(c, k, t);
        expect(Math.hypot(b.x - c.x, b.z - c.z)).toBeLessThan(c.radius * 1.4);
        expect(Math.abs(b.y - c.y)).toBeLessThan(12);
        expect(Math.abs(b.beat)).toBeLessThanOrEqual(1);
      }
  });
});
