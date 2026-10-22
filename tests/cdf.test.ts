// Celestial Dragon Festival (Dragon Kingdom, course 4): the kingdom's grand finale, with
// its own theme and its three-layer music; a night sky of stars over a sacred city full
// of worshippers; the imperial dragon with its own grand-finale flight; and the festival
// itself: fireworks that grow lap by lap (the city's own rockets more often, bigger and
// more varied each stage, the same every race), set pieces that fire once as you reach
// their landmarks and only on their laps (the golden dragon over the observatory as you
// cross the Star Bridge on the last lap; the grand finale over the finish), lanterns
// rising, all purely visual. And the course: a clean lap for the rivals, about two
// minutes, the spiral passing well clear over the Star Bridge.
import { readFile } from "node:fs/promises";
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { SONGS } from "../src/audio/songs";
import { parseAtmosphere } from "../src/game/depths";
import {
  AMBIENT,
  ambientAt,
  festivalLevel,
  festivalStage,
  parseFestival,
  patternPoints,
  piecesDue,
  TICK,
  type Stage,
} from "../src/game/festival";
import { createFestivalLife, hasFestivalLife } from "../src/game/festivalLife";
import { parseIslesDragon, parseVillagers } from "../src/game/isles";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader, type TrackPackage } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const id = "celestial_dragon_festival";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
type Entity = { type: string } & Record<string, unknown>;
const entitiesOf = (p: { meta: { entities?: unknown[] } }) => (p.meta.entities ?? []) as Entity[];
let pkg: TrackPackage | undefined;
const load = async () => (pkg ??= await loadTrackPackage(reader, { visual: false }));
const one = (p: TrackPackage, type: string) => entitiesOf(p).find((e) => e.type === type)!;

describe("Celestial Dragon Festival", () => {
  it("is the Dragon Kingdom's fourth course, with its own theme and its three-layer music", async () => {
    const w = WORLDS.find((x) => x.id === "dragon")!;
    expect(w.tracks.at(-1)).toBe(id);
    expect(w.comingSoon ?? []).toEqual([]);
    expect(trackTilesOf(w)).toHaveLength(4);
    const t = trackById(id)!;
    expect(t.theme).toBe(id);
    const song = SONGS[t.music]!;
    expect(song.id).toBe("celestial");
    expect(song.stems).toEqual(["rise", "finale"]);
    for (const stem of ["base", "rise", "finale"])
      expect(
        song.parts.some((q) => q.stem === stem && q.notes.length > 0),
        stem,
      ).toBe(true);
    const p = await load();
    // Night: a dark sky full of stars, a crescent moon.
    expect(p.look.skyDome?.stars?.count).toBeGreaterThanOrEqual(800);
    expect(p.look.skyDome?.sun?.face).toBe("crescent");
  });

  it("loads cleanly: worshippers, the dragon and its finale flight, the festival, the air", async () => {
    const p = await load();
    expect(p.warnings).toEqual([]);
    const people = parseVillagers(one(p, "villagers"));
    const count = (r: string) => people.filter((v) => v.role === r).length;
    expect(people.length).toBeGreaterThan(500);
    expect(people.length).toBeLessThan(1600);
    expect(count("worship"), "kneeling before the altar").toBeGreaterThanOrEqual(40);
    expect(count("bow")).toBeGreaterThanOrEqual(30);
    expect(count("monk")).toBeGreaterThanOrEqual(6);
    expect(count("dancer")).toBeGreaterThanOrEqual(15);
    const dragon = parseIslesDragon(one(p, "isles_dragon"))!;
    expect(dragon.finale?.keys.length).toBeGreaterThanOrEqual(dragon.keys.length - 2);
    // Both flights meet at the line, so switching to the finale's doesn't jump.
    const [a, b] = [dragon.keys.at(-1)!, dragon.finale!.keys.at(-1)!];
    expect(Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z)).toBeLessThan(1);
    const f = parseFestival(one(p, "festival"));
    expect(f.length).toBeGreaterThan(2500);
    expect(f.length).toBeLessThan(2900);
    expect(f.sites.length).toBeGreaterThanOrEqual(30);
    expect(f.lanterns.length).toBeGreaterThanOrEqual(4);
    expect(f.observatory?.r).toBeGreaterThan(10);
    for (const s of [1, 2, 3] as Stage[])
      expect(
        f.pieces.filter((q) => q.stages.includes(s)).length,
        `stage ${s}`,
      ).toBeGreaterThanOrEqual(3);
    // Lap 3 has more set pieces than lap 2, which has more than lap 1.
    const n = (s: Stage) => f.pieces.filter((q) => q.stages.includes(s)).length;
    expect(n(3)).toBeGreaterThan(n(2));
    expect(n(2)).toBeGreaterThan(n(1));
    const atm = parseAtmosphere(one(p, "atmosphere"));
    expect(atm.zones.gate!.sound).toBe("festival");
    for (const z of Object.values(atm.zones)) expect(z.far).toBeGreaterThan(1500);
    expect(entitiesOf(p).filter((e) => e.type === "glow").length).toBeGreaterThan(100);
  });

  it("grows lap by lap: opening, intensifying, grand finale, building to the line", () => {
    expect(festivalStage(1, 3)).toBe(1);
    expect(festivalStage(2, 3)).toBe(2);
    expect(festivalStage(3, 3)).toBe(3);
    expect(festivalStage(4, 3, true)).toBe(3);
    expect(festivalStage(2, 2)).toBe(3);
    expect(festivalLevel(1, 0.9)).toBeLessThan(festivalLevel(2, 0));
    expect(festivalLevel(2, 0.9)).toBeLessThan(festivalLevel(3, 0));
    expect(festivalLevel(3, 1)).toBeCloseTo(1);
    expect(festivalLevel(3, 0.95)).toBeGreaterThan(festivalLevel(3, 0.5));
  });

  it("launches the city's own rockets more often, bigger and more varied each stage, the same every race", async () => {
    const f = parseFestival(one(await load(), "festival"));
    const run = (stage: Stage, level: number) => {
      const out = [];
      for (let k = 0; k < 6000; k++) out.push(...ambientAt(f, k, stage, level));
      return out;
    };
    const s1 = run(1, festivalLevel(1, 0.5));
    const s2 = run(2, festivalLevel(2, 0.5));
    const s3 = run(3, festivalLevel(3, 0.5));
    const s3end = run(3, 1);
    const secs = 6000 * TICK;
    expect(s1.length / secs).toBeGreaterThan(0.25);
    expect(s1.length / secs).toBeLessThan(0.8);
    expect(s2.length).toBeGreaterThan(s1.length * 2.5);
    expect(s3.length).toBeGreaterThan(s2.length * 1.3);
    expect(s3end.length).toBeGreaterThan(s3.length * 1.15);
    const mean = (xs: { size: number }[]) => xs.reduce((a, x) => a + x.size, 0) / xs.length;
    expect(mean(s2)).toBeGreaterThan(mean(s1));
    expect(mean(s3)).toBeGreaterThan(mean(s2));
    expect(new Set(s3.map((x) => x.pattern)).size).toBeGreaterThan(
      new Set(s1.map((x) => x.pattern)).size,
    );
    expect(AMBIENT[3].patterns.length).toBeGreaterThan(AMBIENT[1].patterns.length);
    // The same show every time.
    expect(run(2, 0.55)).toEqual(run(2, 0.55));
  });

  it("fires each set piece as you reach its place, only on its laps; the dragon over the Star Bridge on the last", async () => {
    const p = await load();
    const f = parseFestival(one(p, "festival"));
    const L = f.length;
    const piece = (pid: string) => f.pieces.find((q) => q.id === pid)!;
    const dragon = piece("star_bridge_dragon");
    expect(dragon.stages).toEqual([3]);
    expect(dragon.bursts.some((b) => b.pattern === "dragon" && b.size >= 60)).toBe(true);
    expect(piece("grand_finale").at).toBeGreaterThan(L * 0.85);
    expect(piece("grand_finale").bursts.length).toBeGreaterThanOrEqual(20);
    const at = dragon.at;
    expect(piecesDue(f, at - 3, at + 3, 3).map((q) => q.id)).toContain("star_bridge_dragon");
    expect(piecesDue(f, at - 3, at + 3, 2).map((q) => q.id)).not.toContain("star_bridge_dragon");
    // Backwards, or a jump (a respawn), fires nothing.
    expect(piecesDue(f, at + 3, at - 3, 3)).toEqual([]);
    expect(piecesDue(f, at - 400, at + 3, 3)).toEqual([]);
    // Across the line.
    const opening = piece("opening");
    expect(piecesDue(f, L - 2, opening.at + 1, 1).map((q) => q.id)).toContain("opening");
    // The shapes: a dragon of hundreds of stars, within its frame; a ring of equal radius.
    const d = patternPoints("dragon", 420, 1);
    expect(d.w.length).toBeGreaterThan(300);
    for (let i = 0; i < d.p.length; i += 3) {
      expect(Math.abs(d.p[i]!)).toBeLessThan(1.6);
      expect(Math.abs(d.p[i + 1]!)).toBeLessThan(1);
    }
    const r = patternPoints("ring", 60, 2);
    for (let i = 0; i < r.p.length; i += 3) expect(Math.hypot(r.p[i]!, r.p[i + 1]!)).toBeCloseTo(1);
  });

  it("puts on the show as you drive (and never touches a kart)", async () => {
    const p = await load();
    expect(hasFestivalLife(entitiesOf(p))).toBe(true);
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    let lap = 1;
    let clock = -3;
    const life = createFestivalLife({
      group: new THREE.Group(),
      entities: entitiesOf(p),
      track,
      volume: () => 0,
      clock: () => clock,
      lap: () => ({ lap, laps: 3, finished: false }),
      headless: true,
    });
    const route = p.route.routes.find((r) => r.id === "main")!.points;
    const drive = () => {
      for (let i = 0; i < route.length; i += 6) {
        const q = route[i]!;
        clock += 0.25;
        life.render(clock, 0.25, { x: q.x, y: q.y + 2, z: q.z });
      }
    };
    drive();
    expect(life.stage()).toBe(1);
    const lap1 = [...life.fired];
    lap = 2;
    drive();
    expect(life.stage()).toBe(2);
    lap = 3;
    drive();
    expect(life.stage()).toBe(3);
    expect(life.fired).toContain("star_bridge_dragon");
    expect(life.fired).toContain("grand_finale");
    expect(lap1).not.toContain("star_bridge_dragon");
    // Every piece fired once on each of its laps, no more.
    const f = parseFestival(one(p, "festival"));
    for (const q of f.pieces)
      expect(life.fired.filter((x) => x === q.id).length, q.id).toBe(q.stages.length);
    expect(life.live).toBeGreaterThan(0);
    life.dispose();
  });

  it("keeps the spiral well clear over the Star Bridge, and the roads apart elsewhere", async () => {
    const p = await load();
    const pts = p.route.routes.find((r) => r.id === "main")!.points.map((q, i) => ({ ...q, i }));
    const n = pts.length;
    for (const a of pts)
      for (const b of pts) {
        const gap = Math.min(Math.abs(a.i - b.i), n - Math.abs(a.i - b.i));
        if (gap < 60) continue; // (the same stretch of road)
        const d = Math.hypot(a.x - b.x, a.z - b.z);
        if (d > a.width / 2 + b.width / 2 + 3) continue;
        expect(Math.abs(a.y - b.y), `(${a.x.toFixed(0)}, ${a.z.toFixed(0)})`).toBeGreaterThan(10);
      }
  });

  it("lets the rivals drive it cleanly, in about two minutes a lap", async () => {
    const p = await load();
    const r = await aiLap(p, { laps: 3, surfaces: true, zippers: true, lapSeconds: 160 });
    const rc = r.race.racers[0]!;
    expect(rc.lapTimes.length).toBe(3);
    expect(r.respawns).toBe(0);
    for (const t of rc.lapTimes.slice(1)) {
      expect(t).toBeGreaterThan(100);
      expect(t).toBeLessThan(125);
    }
  }, 300000);
});
