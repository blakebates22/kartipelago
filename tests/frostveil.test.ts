// Frostveil Peaks: the world is listed with its first course and three locked ones, and
// Frostveil Citadel can be raced: it loads cleanly, the race's AI drives three laps,
// every checkpoint gate counts whatever line you take (hugging either edge, or high in
// the air over the jump), and the deep drops put you back on the road.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { trackById } from "../src/game/tracks";
import { WORLDS, trackTilesOf } from "../src/game/worlds";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { SURFACES, loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { SONGS } from "../src/audio/songs";
import { aiLap } from "./aiLap";

const id = "frostveil_citadel";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
const dt = 1 / 120;
const cfg = { ...tuning.race, laps: 3 };

describe("Frostveil Peaks", () => {
  it("is a world with Frostveil Citadel first, Snowy Summit Pass, and two Coming Soon slots", () => {
    const w = WORLDS.find((x) => x.id === "frostveil")!;
    expect(w.tracks[0]).toBe(id);
    const tiles = trackTilesOf(w);
    expect(tiles).toHaveLength(4);
    expect(tiles[0]!.id).toBe(id);
    expect(tiles[1]!.id).toBe("snowy_summit");
    expect(tiles.slice(2).every((t) => t.comingSoon && !t.load.packageId)).toBe(true);
    expect(trackById(id)?.load.packageId).toBe(id);
    expect(SONGS[trackById(id)!.music]).toBeDefined();
  });

  it("has the snow and ice surfaces, separate from how they look", () => {
    expect(SURFACES.snow_stone?.road).toBe(true);
    expect(SURFACES.icy_stone!.grip!).toBeLessThan(SURFACES.snow_stone!.grip!);
    expect(SURFACES.packed_snow!.speed!).toBeLessThan(1);
    expect(SURFACES.deep_snow?.road).toBe(false);
    expect(SURFACES.abyss?.respawn).toBe(true);
  });
});

describe("Frostveil Citadel", () => {
  it("loads cleanly, with pickups, zippers and a catch for the jump", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    expect(p.warnings).toEqual([]);
    expect(p.trackData.zippers?.length).toBeGreaterThanOrEqual(4);
    expect(p.trackData.bananas?.length).toBeGreaterThan(0);
    expect(p.trackData.balloons?.length).toBeGreaterThan(0);
    expect((p.meta.entities ?? []).some((e) => (e as { type: string }).type === "respawn")).toBe(
      true,
    );
    // A real climb: at least 50 m from the valley floor to the courtyard.
    const ys = p.trackData.points.map((q) => q.y ?? 0);
    expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(50);
    expect(Math.min(...p.trackData.points.map((q) => q.width ?? 0))).toBeGreaterThanOrEqual(13);
  });

  it("can be driven: three AI laps through every checkpoint", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 150 });
    const racer = r.race.racers[0]!;
    expect(racer.lapTimes, `laps (respawns ${r.respawns})`).toHaveLength(3);
    for (const t of racer.lapTimes) {
      expect(t).toBeGreaterThan(60);
      expect(t).toBeLessThan(120);
    }
    expect(r.respawns).toBe(0);
    expect(r.worstAbove).toBeLessThan(2.5);
    expect(r.walls).toBeLessThan(200);
  }, 180000);

  async function ghost(across: number, up: number, speed = 26) {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const race = createRace(track, cfg, 1);
    const s0 = track.samples[0]!;
    const k = createKartState(s0.pos.x, s0.pos.z, track.start.heading, s0.pos.y);
    while (race.phase === "countdown") {
      tickRace(race, dt);
      stepRacer(race, 0, k, true, 0, cfg, dt);
    }
    const ss = track.samples;
    let d = 0;
    for (let n = 0; n < (3 * track.length) / speed / dt + 600 && !race.racers[0]!.finished; n++) {
      tickRace(race, dt);
      d += speed * dt;
      const at = d % track.length;
      let i = 0;
      while (i + 1 < ss.length && ss[i + 1]!.dist <= at) i++;
      const a = ss[i]!;
      const b = ss[(i + 1) % ss.length]!;
      const f = Math.min(
        1,
        Math.max(0, (at - a.dist) / Math.max(1e-6, (b.dist || track.length) - a.dist)),
      );
      const w = (a.width / 2) * 0.95 * across;
      k.x = a.pos.x + (b.pos.x - a.pos.x) * f + a.right.x * w;
      k.z = a.pos.z + (b.pos.z - a.pos.z) * f + a.right.z * w;
      k.y = a.pos.y + (b.pos.y - a.pos.y) * f + 0.4 + up;
      stepRacer(race, 0, k, true, 1, cfg, dt);
    }
    return race.racers[0]!;
  }

  it("counts every gate on any line: both edges, the middle, and high over the jump", async () => {
    for (const [across, up] of [
      [-1, 0],
      [0, 0],
      [1, 0],
      [0, 6.5],
    ] as const) {
      const r = await ghost(across, up);
      expect(r.lapTimes, `line ${across}, ${up} m up`).toHaveLength(3);
    }
  }, 120000);
});
