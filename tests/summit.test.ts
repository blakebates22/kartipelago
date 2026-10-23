// Snowy Summit Pass (Frostveil Peaks, course 2): it's in the world with its own theme
// and music; it loads cleanly; the road really spirals up inside the great tree (each
// turn passing over the one below); every jump has a catch; the geysers blow on a fixed
// beat of the race clock and throw a kart in the column into the air (keeping its speed);
// the mammoths walk their path on the lake; and the AI drives it lap after lap.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { geyserLifts, geyserPhase, inColumn, parseGeyser } from "../src/game/geyser";
import { createHazards, type HazardConfig, type Spot } from "../src/game/hazards";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import type { GroundQuery } from "../src/physics/ground";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "snowy_summit";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];

describe("Snowy Summit Pass", () => {
  it("is Frostveil Peaks' second course, with its own bright theme and music", () => {
    const w = WORLDS.find((x) => x.id === "frostveil")!;
    expect(w.tracks.slice(0, 2)).toEqual(["frostveil_citadel", id]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.load.packageId).toBe(id);
    expect(t.theme).toBe("summit_pass");
    expect(SONGS[t.music]?.id).toBe("summit");
  });

  it("loads cleanly, with pickups, zippers, three jumps with catches, and a real climb", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(5);
    expect(p.trackData.bananas?.length).toBeGreaterThan(0);
    expect(p.trackData.balloons?.length).toBeGreaterThan(0);
    expect(entitiesOf(p).filter((e) => e.type === "respawn")).toHaveLength(3);
    const ys = p.trackData.points.map((q) => q.y ?? 0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(40);
    // Wide everywhere but the rope bridge out of the great tree, which is narrow (10 m).
    const widths = p.trackData.points.map((q) => q.width ?? 0);
    expect(Math.min(...widths)).toBeGreaterThanOrEqual(10);
    expect(widths.filter((w) => w < 13).length).toBeLessThan(40);
  });

  it("spirals up inside the great tree: two whole turns, each over the one below", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const pts = p.trackData.points;
    // Points of the lap that pass almost exactly over another point of the lap.
    let stacked = 0;
    let maxStack = 0;
    for (let i = 0; i < pts.length; i += 4) {
      const a = pts[i]!;
      const over = pts.filter(
        (b) => Math.hypot(b.x - a.x, b.z - a.z) < 2.5 && (b.y ?? 0) - (a.y ?? 0) > 12,
      );
      if (over.length) stacked++;
      maxStack = Math.max(
        maxStack,
        over.length ? new Set(over.map((b) => Math.round((b.y ?? 0) / 10))).size : 0,
      );
    }
    // Most of a turn's worth of road has road over it (two turns: the first has the
    // second above it, and some of the second the exit high above).
    expect(stacked * 4).toBeGreaterThan(150);
    expect(maxStack).toBeGreaterThanOrEqual(1);
  });

  it("has geysers on a fixed beat (one in the road that throws you up) and two mammoths", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const es = entitiesOf(p);
    const gs = es.filter((e) => e.type === "geyser").map((e) => parseGeyser(e));
    expect(gs.length).toBeGreaterThanOrEqual(5);
    expect(gs.filter((g) => g.launch > 0).length).toBeGreaterThanOrEqual(2);
    const mammoths = es.filter((e) => e.type === "dinosaur" && e.model === "mammoth");
    expect(mammoths).toHaveLength(2);
    expect(p.route.routes.find((r) => r.id === "Mammoth Path")?.points.length).toBeGreaterThan(20);
  });

  it("can be driven: three AI laps through every checkpoint", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 160 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(80);
      expect(t).toBeLessThan(125);
    }
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(200);
  }, 240000);
});

describe("geysers", () => {
  const g = parseGeyser({
    x: 0,
    y: 1,
    z: 0,
    r: 4,
    height: 20,
    period: 7,
    offset: 2,
    warn: 1.4,
    blast: 2.2,
    launch: 15,
  });

  it("rest, warn, then blow, every period, from the race clock", () => {
    const seen: string[] = [];
    for (let t = 2; t < 9; t += 0.02) {
      const ph = geyserPhase(g, t).phase;
      if (seen.at(-1) !== ph) seen.push(ph);
    }
    expect(seen).toEqual(["idle", "warning", "blast"]);
    for (const t of [-3.3, 0, 5.55, 99.1]) {
      const a = geyserPhase(g, t);
      const b = geyserPhase(g, t + 7 * 9);
      expect(b.phase).toBe(a.phase);
      expect(b.t).toBeCloseTo(a.t, 6);
    }
  });

  it("only lifts inside the column, while it blows", () => {
    const blowing = 2 + 7 - 2.2 + 0.3;
    expect(geyserPhase(g, blowing).phase).toBe("blast");
    expect(geyserLifts(g, blowing, 0, 1, 0)).toBe(true);
    expect(geyserLifts(g, blowing, 3.9, 6, 0)).toBe(true); // in the air, over the vent
    expect(geyserLifts(g, blowing, 4.5, 1, 0)).toBe(false); // beside it
    expect(geyserLifts(g, blowing, 0, 30, 0)).toBe(false); // high above it
    expect(geyserLifts(g, blowing - 1.0, 0, 1, 0)).toBe(false); // still warning
    expect(inColumn(g, 0, 1, 0)).toBe(true);
    // A geyser without a launch is only scenery.
    expect(geyserLifts({ ...g, launch: 0 }, blowing, 0, 1, 0)).toBe(false);
  });

  it("throws a kart up, keeping its speed and heading, then not again for a moment", () => {
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
      at: () => ({ height: 1, nx: 0, ny: 1, nz: 0, onRoad: true }),
    } as unknown as GroundQuery;
    let clock = 2 + 7 - 2.2 + 0.3;
    const h = createHazards({
      root: undefined as never,
      track,
      entities: [
        { type: "geyser", x: 0, y: 1, z: 0, r: 4, height: 20, period: 7, offset: 2, launch: 15 },
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
    const k = createKartState(0, 0, 0.3, 1);
    k.grounded = true;
    k.speed = 21;
    k.velAngle = 0.3;
    const ev = h.stepKart(0, k, "road", gate, 1 / 120);
    expect(ev.launched).toBe(true);
    expect(k.vy).toBe(15);
    expect(k.grounded).toBe(false);
    expect(k.speed).toBe(21);
    expect(k.velAngle).toBe(0.3);
    // Not again straight away...
    k.vy = 0;
    k.grounded = true;
    expect(h.stepKart(0, k, "road", gate, 1 / 120).launched).toBeUndefined();
    // ...and never while it rests.
    clock = 3;
    for (let t = 0; t < 1.5; t += 1 / 120) h.stepKart(0, k, "road", gate, 1 / 120);
    expect(h.stepKart(0, k, "road", gate, 1 / 120).launched).toBeUndefined();
  });
});
