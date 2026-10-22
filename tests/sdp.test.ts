// Snow Dragon Pass (Dragon Kingdom, course 3): the kingdom's third course, with its own
// theme and music; a road network where about half the lap is shared and half is a
// choice of two branches at each of two splits; every branch has its own checkpoints and
// respawns you on itself; the roads never touch where they pass over and under each
// other; the rivals can drive every combination cleanly; one combination (the High
// Cliff Road and the Frozen Aqueduct) is a little faster than the rest, but only a
// little; and the kingdom (its people, its weather, its dragon) is all there.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { parseAtmosphere } from "../src/game/depths";
import { parseIslesDragon, parseVillagers } from "../src/game/isles";
import {
  AVALANCHE_RUN,
  avalancheAt,
  gust,
  parseAvalanches,
  parseBlizzard,
  parseFlags,
  snowAt,
} from "../src/game/snow";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, respawnSpot, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader, type TrackPackage } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "snow_dragon_pass";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;
const LAPS = ["Lap Cliff Aqueduct", "Lap Supply Ridge", "Lap Supply Aqueduct"];

let pkg: TrackPackage | undefined;
const load = async () => (pkg ??= await loadTrackPackage(reader, { visual: false }));
const routePts = (p: TrackPackage, rid: string) => p.route.routes.find((r) => r.id === rid)!.points;

/** Share of a route's points that lie on another route (within a metre, same height). */
function sharedWith(
  a: { x: number; y: number; z: number }[],
  b: { x: number; y: number; z: number }[],
) {
  const grid = new Map<string, { x: number; y: number; z: number }[]>();
  const key = (x: number, z: number) => `${Math.floor(x / 5)},${Math.floor(z / 5)}`;
  for (const q of b) {
    const k = key(q.x, q.z);
    if (!grid.has(k)) grid.set(k, []);
    grid.get(k)!.push(q);
  }
  let on = 0;
  for (const p of a) {
    let hit = false;
    for (let i = -1; i <= 1 && !hit; i++)
      for (let j = -1; j <= 1 && !hit; j++)
        for (const q of grid.get(`${Math.floor(p.x / 5) + i},${Math.floor(p.z / 5) + j}`) ?? [])
          if (Math.hypot(q.x - p.x, q.z - p.z) < 1.5 && Math.abs(q.y - p.y) < 1) {
            hit = true;
            break;
          }
    if (hit) on++;
  }
  return on / a.length;
}

describe("Snow Dragon Pass", () => {
  it("is the Dragon Kingdom's third course, with its own theme and music", async () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks).toEqual(["dragon_isles", "dragon_canyon", id, "celestial_dragon_festival"]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe(id);
    expect(SONGS[t.music]?.id).toBe("snow_dragon");
    const p = await load();
    expect(p.look.fog?.far).toBeLessThan(1200); // the blizzard closes in (but see below)
    expect(p.look.fog?.far).toBeGreaterThan(700); // ...never so close you can't see the road
  });

  it("loads cleanly: its four laps, its people, its weather and its dragon", async () => {
    const p = await load();
    expect(p.warnings).toEqual([]);
    expect(p.lapRoutes.map((r) => r.id).sort()).toEqual([...LAPS].sort());
    const es = entitiesOf(p);
    const one = (type: string) => es.find((e) => e.type === type)!;
    const people = parseVillagers(one("villagers"));
    const count = (r: string) => people.filter((v) => v.role === r).length;
    expect(count("queue"), "ration lines").toBeGreaterThanOrEqual(20);
    expect(count("huddle"), "by the fires").toBeGreaterThanOrEqual(10);
    expect(count("guard"), "guards").toBeGreaterThanOrEqual(15);
    expect(count("monk"), "monks").toBeGreaterThanOrEqual(5);
    expect(count("hauler") + count("worker"), "labour").toBeGreaterThanOrEqual(5);
    const dragon = parseIslesDragon(one("isles_dragon"))!;
    expect(dragon.colors?.body).toMatch(/^#[0-9a-f]{6}$/);
    const atm = parseAtmosphere(one("atmosphere"));
    expect(atm.zones.cliff!.sound).toBe("blizzard");
    expect(atm.zones.monastery!.sound).toBe("bells");
    expect(atm.zones.cavern!.sun).toBeLessThan(1);
    for (const z of Object.values(atm.zones)) expect(z.far).toBeGreaterThan(250);
    expect(parseFlags(one("prayer_flags")).length).toBeGreaterThanOrEqual(15);
    expect(parseAvalanches(one("avalanches")).length).toBeGreaterThanOrEqual(1);
    expect(es.filter((e) => e.type === "campfire").length).toBeGreaterThanOrEqual(6);
  });

  it("snows hardest on the heights, gently in the village, not at all in the tunnels", async () => {
    const p = await load();
    const b = parseBlizzard(entitiesOf(p).find((e) => e.type === "blizzard")!);
    expect(Math.hypot(b.wind.x, b.wind.z)).toBeCloseTo(1);
    const ks = b.keys.map((k) => k.k);
    expect(Math.max(...ks)).toBe(1);
    expect(Math.min(...ks)).toBe(0); // the tunnels
    // The storm's own rhythm stays within bounds, and is the same at the same moment.
    for (let t = 0; t < 120; t += 0.37) {
      expect(gust(t)).toBeGreaterThanOrEqual(0.55);
      expect(gust(t)).toBeLessThanOrEqual(1.4);
    }
    const k0 = b.keys[0]!;
    expect(snowAt(b, k0.x, k0.y, k0.z)).toBeCloseTo(k0.k, 1);
    // Avalanches run on the race clock's beat: never before GO, the same every race.
    for (const av of parseAvalanches(entitiesOf(p).find((e) => e.type === "avalanches")!)) {
      expect(avalancheAt(av, -5).running).toBe(false);
      const t = av.offset + av.period * 3 + 0.3;
      expect(avalancheAt(av, t)).toEqual(avalancheAt(av, t));
      expect(avalancheAt(av, av.offset + av.period * (AVALANCHE_RUN + 0.05)).running).toBe(false);
    }
  });

  it("shares about half of every lap and splits the rest between two roads, twice", async () => {
    const p = await load();
    const main = routePts(p, "main");
    const all = LAPS.map((l) => routePts(p, l));
    const everyone = all.reduce((acc, r) => acc.filter((q) => sharedWith([q], r) > 0), main);
    for (const [k, r] of [main, ...all].entries()) {
      const shared = sharedWith(r, everyone);
      expect(shared, `route ${k}`).toBeGreaterThan(0.45);
      expect(shared, `route ${k}`).toBeLessThan(0.62);
    }
    // Supply + Aqueduct takes neither of the main route's branches.
    expect(sharedWith(all[2]!, main)).toBeLessThan(0.62);
  });

  it("gives each branch its own checkpoints, numbered with the other branch's, and respawns there", async () => {
    const p = await load();
    const gates = p.trackData.gates!;
    const byIndex = new Map<number, typeof gates>();
    for (const g of gates) byIndex.set(g.index, [...(byIndex.get(g.index) ?? []), g]);
    const split = [...byIndex.values()].filter((gs) => gs.length > 1);
    expect(split.length).toBe(8); // four on each branch of each split
    for (const gs of split) {
      expect(gs.length).toBe(2);
      const alt = gs.find((g) => g.route !== "main")!;
      const lap = alt.route === "supply" ? "Lap Supply Ridge" : "Lap Cliff Aqueduct";
      const near = (
        pts: { x: number; y: number; z: number }[],
        q: { x: number; y: number; z: number },
      ) => Math.min(...pts.map((r) => Math.hypot(r.x - q.x, r.z - q.z) + Math.abs(r.y - q.y)));
      // The branch gate and its respawn are on the branch, well off the main road.
      expect(near(routePts(p, lap), alt)).toBeLessThan(3);
      expect(near(routePts(p, "main"), alt.respawn)).toBeGreaterThan(10);
      expect(near(routePts(p, lap), alt.respawn)).toBeLessThan(3);
    }
  });

  it("puts you back on your own branch if you fall off it", async () => {
    const p = await load();
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    for (const lap of ["Lap Supply Ridge", "Lap Cliff Aqueduct"]) {
      const race = createRace(track, tuning.race, 1);
      while (race.phase === "countdown") tickRace(race, dt);
      const pts = routePts(p, lap);
      // Drive along the lap's route to past the second branch gate it reaches.
      const alts = p.trackData.gates!.filter(
        (g) => g.route === (lap.includes("Supply R") ? "supply" : "aqueduct"),
      );
      const target = alts.sort((a, b) => a.index - b.index)[1]!;
      let i = 0;
      for (; i < pts.length - 1; i++) {
        tickRace(race, dt);
        stepRacer(
          race,
          0,
          createKartState(pts[i]!.x, pts[i]!.z, 0, pts[i]!.y),
          true,
          1,
          tuning.race,
          dt,
        );
        if (race.racers[0]!.last === target.index) break;
      }
      expect(race.racers[0]!.last, lap).toBe(target.index);
      const spot = respawnSpot(race, 0);
      expect(Math.hypot(spot.x - target.respawn.x, spot.z - target.respawn.z)).toBeLessThan(0.01);
    }
  });

  it("never lets two roads touch where they pass over and under each other", async () => {
    const p = await load();
    const pts = ["main", ...LAPS].flatMap((rid, k) =>
      routePts(p, rid)
        .filter((_, i) => i % 2 === 0)
        .map((q, i) => ({ ...q, k, i })),
    );
    for (const a of pts)
      for (const b of pts) {
        if (b.x < a.x - 30 || b.x > a.x + 30) continue;
        const d = Math.hypot(a.x - b.x, a.z - b.z);
        if (d > a.width / 2 + b.width / 2 + 3) continue;
        const dy = Math.abs(a.y - b.y);
        // The same road (no steeper than 25% between the two points), or well clear
        // above or below it.
        expect(
          dy < 1 + 0.25 * d || dy > 9,
          `(${a.x.toFixed(0)}, ${a.z.toFixed(0)}) dy ${dy.toFixed(1)} at ${d.toFixed(1)} m`,
        ).toBe(true);
      }
  });

  it("lets the rivals drive every combination cleanly, the fastest only a little faster", async () => {
    const p = await load();
    const times: Record<string, number> = {};
    for (const route of [undefined, ...LAPS]) {
      const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, route, lapSeconds: 150 });
      const rc = r.race.racers[0]!;
      const name = route ?? "main";
      expect(rc.lapTimes.length, name).toBe(3);
      expect(r.respawns, name).toBe(0);
      for (const t of rc.lapTimes) {
        expect(t, name).toBeGreaterThan(90);
        expect(t, name).toBeLessThan(110);
      }
      times[name] = (rc.lapTimes[1]! + rc.lapTimes[2]!) / 2; // flying laps
    }
    const best = Math.min(...Object.values(times));
    expect(times["Lap Cliff Aqueduct"]).toBe(best);
    for (const [name, t] of Object.entries(times)) {
      if (t === best) continue;
      expect((t - best) / best, name).toBeGreaterThan(0.002);
      expect((t - best) / best, name).toBeLessThan(0.035);
    }
  }, 600000);
});
