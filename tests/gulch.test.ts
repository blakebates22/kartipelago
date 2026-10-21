// Dry Gulch Ghost Town (Desert World, course 3): it's the Desert World's third course
// with its own night theme (a full moon, a skull-shaped cloud) and music; it loads
// cleanly with its haunting (ghosts, the ghost rider, wisps and mist, the runaway ore
// cart in the mine, tumbleweeds, the saloon doors, flickering lanterns) and the haunted
// mine's twin gate; the mine counts as the lap it skips and is a real short cut when the
// AI drives through it; and the AI drives the lap in 75-100 s without falling into the
// chasm.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import {
  doorSwing,
  ghostAt,
  openPath,
  parseAmbience,
  parseDoor,
  parseGhost,
  parseRailcart,
  parseRider,
  parseWisps,
  pathPoint,
  railcartAt,
  riderAt,
  underground,
  wispAt,
} from "../src/game/haunt";
import { windmillAngle, parseWindmill } from "../src/game/desert";
import { crossingAt, parseCrossing } from "../src/game/movers";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { skullShown } from "../src/render/skyDome";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader, type TrackPackage } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "dry_gulch";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
const dt = 1 / 120;

/** The shortcut through the mine (route.json's "Haunted Mine Path"), game coordinates. */
const minePath = (p: TrackPackage) =>
  p.route.routes
    .find((r) => r.id === "Haunted Mine Path")!
    .points.map((q) => ({ x: q.x, y: q.y, z: q.z }));

describe("Dry Gulch Ghost Town", () => {
  it("is the Desert World's third course, with its own night sky and music", async () => {
    const w = WORLDS.find((x) => x.id === "desert")!;
    expect(w.tracks).toEqual(["canyon_dash", "oasis_haven", id]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe("dry_gulch");
    expect(SONGS[t.music]?.id).toBe("ghost");
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.look.skyDome?.sun?.face).toBe("moon");
    expect(p.look.skyDome?.skull?.period).toBeGreaterThan(20);
    expect(p.look.skyDome?.stars?.count).toBeGreaterThan(100);
  });

  it("loads cleanly: the haunting, the runaway cart, flickering lanterns, the mine's twin gate", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(6);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(10);
    const es = entitiesOf(p);
    const n = (t: string) => es.filter((e) => e.type === t).length;
    expect(n("minecart")).toBe(1);
    expect(n("ghostrider")).toBe(1);
    expect(n("railcart")).toBe(1);
    expect(n("door")).toBeGreaterThanOrEqual(1);
    expect(n("bell")).toBe(1);
    expect(n("windmill")).toBe(1);
    expect(n("tumbleweed")).toBeGreaterThanOrEqual(4);
    expect(n("lantern")).toBeGreaterThanOrEqual(20);
    expect(n("wisps")).toBeGreaterThanOrEqual(3);
    expect(n("mist")).toBeGreaterThanOrEqual(3);
    expect(n("whispers")).toBeGreaterThanOrEqual(2);
    for (const look of ["window", "float", "miner", "shadow"])
      expect(
        es.some((e) => e.type === "ghost" && e.look === look),
        look,
      ).toBe(true);
    const amb = es.find((e) => e.type === "ambience")!;
    expect(parseAmbience(amb).caves.length).toBeGreaterThan(5);
    // The routes the moving things follow are there.
    for (const r of ["Railway", "Ghost Rider Path", "Haunted Mine Path"])
      expect(
        p.route.routes.some((q) => q.id === r),
        r,
      ).toBe(true);
    const routes = new Set((p.trackData.gates ?? []).map((g) => g.route));
    expect(routes.has("haunted_mine")).toBe(true);
    // Lanterns and lit windows flicker: read the materials' extras from the GLB's JSON.
    const glb = new Uint8Array(await reader("visual.glb"));
    const len = new DataView(glb.buffer, glb.byteOffset).getUint32(12, true);
    const json = JSON.parse(new TextDecoder().decode(glb.subarray(20, 20 + len))) as {
      materials: { extras?: { kp_fx?: { flicker?: number } } }[];
    };
    expect(json.materials.some((m) => (m.extras?.kp_fx?.flicker ?? 0) > 0)).toBe(true);
  });

  it("counts the haunted mine as the stretch it skips", async () => {
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
    const cut = minePath(p);
    const sIn = along(cut[0]!.x, cut[0]!.z);
    const sOut = along(cut.at(-1)!.x, cut.at(-1)!.z);
    expect(sOut - sIn).toBeGreaterThan(400);
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

  it("drives well: three AI laps of 75-100 s, never into the chasm", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 130 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(75);
      expect(t).toBeLessThan(100);
    }
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(300);
  }, 240000);

  it("makes the haunted mine a real short cut: the AI driven through it laps faster", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const main = p.trackData.points;
    const cut = minePath(p);
    const near = (x: number, z: number) => {
      let bi = 0;
      let bd = Infinity;
      main.forEach((q, i) => {
        const d = Math.hypot(q.x - x, q.z - z);
        if (d < bd) {
          bd = d;
          bi = i;
        }
      });
      return bi;
    };
    const a = near(cut[0]!.x, cut[0]!.z);
    const b = near(cut.at(-1)!.x, cut.at(-1)!.z);
    const points = [
      ...main.slice(0, a),
      ...cut.slice(1, -1).map((q) => ({ x: q.x, y: q.y, z: q.z, width: 10, bank: 0 })),
      ...main.slice(b + 1),
    ];
    const viaMine = { ...p, trackData: { ...p.trackData, points } };
    const r = await aiLap(viaMine, { laps: 2, surfaces: true, lapSeconds: 130 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(2);
    expect(r.respawns).toBe(0);
    expect(r.surfaces.has("abyss")).toBe(false);
    const main3 = await aiLap(p, { laps: 2, surfaces: true, lapSeconds: 130 });
    const mainLap = main3.race.racers[0]!.lapTimes[1]!;
    const mineLap = racer.lapTimes[1]!;
    // Several seconds faster when driven well (before the cart's held anyone up).
    expect(mainLap - mineLap).toBeGreaterThan(2);
    expect(mainLap - mineLap).toBeLessThan(12);
  }, 300000);
});

describe("the haunting", () => {
  it("shows each ghost for a few seconds of its period, fading in and out", () => {
    const g = parseGhost({ x: 0, y: 0, z: 0, look: "window", period: 11, offset: 2 });
    let seen = 0;
    let max = 0;
    for (let t = 0; t < 11; t += 0.05) {
      const a = ghostAt(g, t).alpha;
      if (a > 0.01) seen += 0.05;
      max = Math.max(max, a);
      expect(a).toBeGreaterThanOrEqual(0);
      expect(a).toBeLessThanOrEqual(1);
    }
    expect(max).toBeGreaterThan(0.9);
    expect(seen).toBeGreaterThan(2);
    expect(seen).toBeLessThan(6);
    expect(parseGhost({ look: "nonsense" }).look).toBe("float");
  });

  it("fades the ghostly miners away as a kart comes close", () => {
    const g = parseGhost({ look: "miner", period: 10, offset: 0, vanish: 20 });
    const t = 3;
    expect(ghostAt(g, t, 100).alpha).toBeGreaterThan(0.5);
    expect(ghostAt(g, t, 5).alpha).toBe(0);
  });

  it("gallops the ghost rider along his ridge once a period, out of the mist and back into it", () => {
    const r = parseRider({ route: "x", period: 38, offset: 10, travel: 14 });
    expect(riderAt(r, 5).u).toBe(-1);
    const mid = riderAt(r, 17);
    expect(mid.u).toBeGreaterThan(0.4);
    expect(mid.alpha).toBe(1);
    expect(riderAt(r, 10.2).alpha).toBeLessThan(0.3);
    const path = openPath([
      { x: 0, y: 0, z: 0 },
      { x: 0, y: 0, z: 10 },
      { x: 10, y: 0, z: 10 },
    ]);
    expect(path.length).toBeCloseTo(20);
    const p = pathPoint(path, 15);
    expect(p.x).toBeCloseTo(5);
    expect(p.z).toBeCloseTo(10);
  });

  it("rolls the rail cart out, pauses, rolls it back", () => {
    const c = parseRailcart({ route: "x", period: 34, offset: 0, travel: 13, pause: 4 });
    expect(railcartAt(c, 0).u).toBe(0);
    expect(railcartAt(c, 6.5).moving).toBe(true);
    expect(railcartAt(c, 15).u).toBe(1);
    expect(railcartAt(c, 15).moving).toBe(false);
    expect(railcartAt(c, 33).u).toBe(0);
  });

  it("swings the saloon's doors open now and then, and lets them settle shut", () => {
    const d = parseDoor({ period: 9 });
    let open = 0;
    for (let t = 0; t < 9; t += 0.05) open = Math.max(open, Math.abs(doorSwing(d, t)));
    expect(open).toBeGreaterThan(0.5);
    expect(doorSwing(d, 6)).toBe(0);
  });

  it("keeps the wisps wandering about their spot", () => {
    const w = parseWisps({ x: 10, y: 5, z: -20, radius: 12, count: 6 });
    for (let k = 0; k < w.count; k++)
      for (let t = 0; t < 60; t += 1.7) {
        const p = wispAt(w, k, t);
        expect(Math.hypot(p.x - w.x, p.z - w.z)).toBeLessThan(w.radius + 4);
        expect(p.glow).toBeGreaterThanOrEqual(0);
      }
  });

  it("knows when you're underground, for the sound", () => {
    const a = parseAmbience({ wind: 0.5, caves: [[0, 0, 0, 10]] });
    expect(underground(a, 0, 0, 0)).toBe(1);
    expect(underground(a, 30, 0, 0)).toBe(0);
  });

  it("sends the runaway cart across on a beat, waiting (and warning) first", () => {
    const c = parseCrossing(
      { ax: 0, ay: 0, az: 0, bx: 40, by: 0, bz: 0, period: 7, travel: 3, warn: 1.8 },
      false,
      true,
    );
    expect(c.r).toBeCloseTo(1.3);
    const phases = new Set<string>();
    for (let t = 0; t < 7; t += 0.1) phases.add(crossingAt(c, t).phase);
    expect([...phases].sort()).toEqual(["crossing", "idle", "warning"]);
    // A clear moment every period: the road isn't blocked for good.
    let clear = 0;
    for (let t = 0; t < 7; t += 0.1) if (crossingAt(c, t).phase !== "crossing") clear += 0.1;
    expect(clear).toBeGreaterThan(3);
  });

  it("turns the windmill fitfully, and gathers the skull cloud now and then", () => {
    const w = parseWindmill({ speed: 0.6, gusty: true });
    expect(windmillAngle(w, 120)).toBeGreaterThan(windmillAngle(w, 0));
    let shown = 0;
    for (let t = 0; t < 46; t += 0.5) if (skullShown(t, 46) > 0) shown += 0.5;
    expect(shown).toBeGreaterThan(15);
    expect(shown).toBeLessThan(30);
  });
});
