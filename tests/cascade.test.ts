// Cascade Caverns: a race can always be finished. Every checkpoint gate counts whatever
// line you take (hugging either edge of the road, or high in the air over the leap), and
// a missed jump puts you back on the far side, never behind a gate you'd have to redo.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";

const id = "cascade_caverns";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
const dt = 1 / 120;
const cfg = { ...tuning.race, laps: 3 };

/** Glide a "kart" along the route at `across` (-1..1 of the half-width) and `up` metres
 * above the road, for three laps; the gates passed and laps counted. */
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
  let gates = 0;
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
    const ev = stepRacer(race, 0, k, true, 1, cfg, dt);
    if (ev.checkpoint) gates++;
  }
  return { race, gates, track };
}

describe("Cascade Caverns can always be finished", () => {
  for (const across of [-1, -0.5, 0, 0.5, 1])
    it(`counts every gate and all three laps on a line ${across} across the road`, async () => {
      const { race } = await ghost(across, 0);
      expect(race.racers[0]!.lapTimes).toHaveLength(3);
      expect(race.racers[0]!.finished).toBe(true);
    });

  it("counts the gates even high in the air (the top of the leap's arc)", async () => {
    for (const across of [-0.8, 0, 0.8]) {
      const { race } = await ghost(across, 6.5);
      expect(race.racers[0]!.lapTimes, `across ${across}`).toHaveLength(3);
    }
  });

  it("puts a missed jump back past the gap, ahead of the last gate before it", async () => {
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const zone = (p.meta.entities ?? []).find(
      (e): e is { type: string; from: number; to: number; at: number } =>
        typeof e === "object" && e !== null && (e as { type?: string }).type === "respawn",
    );
    expect(zone).toBeDefined();
    const gates = (p.trackData.gates ?? []).map((g) => {
      // Each gate's distance along the lap: the nearest route sample.
      let best = track.samples[0]!;
      let bd = Infinity;
      for (const s of track.samples) {
        const dd = (s.pos.x - g.x) ** 2 + (s.pos.z - g.z) ** 2 + (s.pos.y - g.y) ** 2;
        if (dd < bd) ((bd = dd), (best = s));
      }
      return best.dist;
    });
    // The respawn point is past the gap, and no gate sits inside the gap zone (so falling
    // in can never strand you behind one).
    expect(zone!.at).toBeGreaterThan(zone!.to);
    for (const g of gates) expect(g < zone!.from + 30 || g > zone!.to).toBe(true);
    // And the spot is on the road, within the lap.
    expect(zone!.at).toBeLessThan(track.length);
  });
});
