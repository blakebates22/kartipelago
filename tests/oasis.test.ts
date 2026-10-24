// Oasis Haven (Desert World, course 2): it's the Desert World's second course with its
// own bright theme and music; it loads cleanly under its turquoise sky, the spiral round
// the watchtower passes over itself, there's a twin gate across the palm grove and the
// grove counts as the stretch it skips; and the AI drives it without a respawn (over
// the chute's jump too). The boats and fountains (oasis life) are the first version's,
// kept as oasis_haven_v2.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { boatAt, jetVelocity, parseBoat, parseFountain, SPRAY_GRAVITY } from "../src/game/oasis";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "oasis_haven";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
const dt = 1 / 120;

// The palm-grove shortcut (game coordinates), from oasis_haven.py's SHORTCUT.
const GROVE: [number, number, number][] = [
  [100.0, 2.4, 153.6],
  [136.0, 2.4, 150.6],
  [192.9, 2.4, 148.6],
  [249.9, 2.4, 150.6],
  [285.9, 2.4, 153.6],
];

describe("Oasis Haven", () => {
  it("is the Desert World's second course, with its own theme and music", () => {
    const w = WORLDS.find((x) => x.id === "desert")!;
    expect(w.tracks.slice(0, 2)).toEqual(["canyon_dash", id]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe("oasis_haven");
    expect(SONGS[t.music]?.id).toBe("oasis");
  });

  it("loads cleanly under a turquoise sky; the spiral passes over itself; the grove has its twin gate", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    expect(p.trackData.balloons?.length).toBeGreaterThanOrEqual(8);
    expect(p.look.skyDome?.top).toBe("#0f8fb0");
    const pts = p.trackData.points;
    let over = false;
    for (const a of pts)
      for (const b of pts)
        if (Math.hypot(a.x - b.x, a.z - b.z) < 4 && (a.y ?? 0) - (b.y ?? 0) > 6) over = true;
    expect(over).toBe(true);
    const es = (p.meta.entities ?? []) as { type: string }[];
    expect(es.filter((e) => e.type === "respawn")).toHaveLength(1);
    expect(es.filter((e) => e.type === "torch").length).toBeGreaterThan(8);
    expect(new Set((p.trackData.gates ?? []).map((g) => g.route)).has("palm_grove")).toBe(true);
  });

  it("counts the palm grove as the stretch it skips", async () => {
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
    const cut = GROVE;
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

  it("drives well: three AI laps of 55-80 s, no respawns, hardly a wall", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 130 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(55);
      expect(t).toBeLessThan(80);
    }
    expect(r.respawns).toBe(0);
    expect(r.walls).toBeLessThan(100);
  }, 240000);
});

describe("oasis life", () => {
  const routes = [
    {
      id: "Loop",
      closed: true,
      points: Array.from({ length: 24 }, (_, k) => ({
        x: 30 * Math.cos((k / 24) * Math.PI * 2),
        y: 0,
        z: 20 * Math.sin((k / 24) * Math.PI * 2),
        width: 4,
        bank: 0,
      })),
    },
  ];

  it("sails boats round their loops, bobbing gently on the water, facing the way they go", () => {
    const b = parseBoat({ route: "Loop", speed: 5 }, routes as never)!;
    expect(parseBoat({ route: "Nowhere" }, routes as never)).toBeUndefined();
    let prev = boatAt(b, 0);
    for (let t = 0.5; t < 60; t += 0.5) {
      const s = boatAt(b, t);
      expect(Math.abs(s.y)).toBeLessThan(0.3);
      expect(Math.hypot(s.x / 30, s.z / 20)).toBeLessThan(1.05);
      const moved = Math.atan2(s.x - prev.x, s.z - prev.z);
      const d = Math.abs(((moved - s.heading + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
      expect(d).toBeLessThan(0.6);
      prev = s;
    }
    // Back where it started after one lap.
    const lap = b.path.length / b.speed;
    expect(
      Math.hypot(boatAt(b, lap).x - boatAt(b, 0).x, boatAt(b, lap).z - boatAt(b, 0).z),
    ).toBeLessThan(0.5);
  });

  it("throws fountain jets to the right height and lands the ring on the basin's edge", () => {
    const f = parseFountain({ x: 0, y: 0, z: 0, height: 8, jets: 6, radius: 4 });
    const up = jetVelocity(f, 0);
    expect((up.v[1] * up.v[1]) / (2 * SPRAY_GRAVITY)).toBeCloseTo(8);
    for (let k = 1; k <= f.jets; k++) {
      const { v, t } = jetVelocity(f, k);
      expect(Math.hypot(v[0] * t, v[2] * t)).toBeCloseTo(4);
      expect(v[1] * t - (SPRAY_GRAVITY * t * t) / 2).toBeCloseTo(0);
    }
  });
});
