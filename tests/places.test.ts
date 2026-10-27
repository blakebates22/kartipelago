// Places follow the road (Blake, Oct 27: in the 1-on-1 against Rex and in the boss races
// the HUD said 2nd for a second while he was 1st). A long, bending stretch between two
// checkpoints: the next gate's plane cut back across the road before it, and the last
// gate's plane cut across the far side of a hairpin, so a kart further on could rank
// behind one further back. Driving along any stretch must only ever gain ground.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { segmentProgress } from "../src/race/checkpoints";
import { createRace } from "../src/race/race";
import { buildTrack } from "../src/world/track";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";

const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

const COURSES = [
  "boss_prehistoric",
  "boss_snowy",
  "boss_desert",
  "boss_tropic",
  "boss_dragon",
  "valley_region",
  "snow_region",
  "desert_region",
  "beach_region",
  "dragon_region",
];

describe("places along every stretch", () => {
  for (const id of COURSES)
    it(`${id}: further along the road always ranks further on`, async () => {
      const p = await loadTrackPackage(reader(id), { visual: false });
      const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
      const race = createRace(track, tuning.race, 1);
      const ss = track.samples;
      const n = ss.length;
      const nearest = (g: { x: number; y: number; z: number }) => {
        let best = 0;
        for (let i = 1; i < n; i++) {
          const d = (q: (typeof ss)[0]) =>
            (q.pos.x - g.x) ** 2 + (q.pos.z - g.z) ** 2 + 4 * (q.pos.y - g.y) ** 2;
          if (d(ss[i]!) < d(ss[best]!)) best = i;
        }
        return best;
      };
      const r = race.racers[0]!;
      const c = race.course;
      let checked = 0;
      const bad: string[] = [];
      for (let k = 0; k < c.length; k++) {
        const ia = nearest(c[k]!.gates[0]!);
        const ib = nearest(c[(k + 1) % c.length]!.gates[0]!);
        const steps = (ib - ia + n) % n;
        if (steps < 4 || steps > n / 2) continue;
        Object.assign(r, {
          passed: k + 1,
          last: k,
          lastGate: c[k]!.gates[0]!,
          next: (k + 1) % c.length,
          activeRoute: "main",
        });
        let prev = -Infinity;
        // From a few samples past the gate to a few before the next (the road's middle).
        for (let j = 2; j <= steps - 2; j++) {
          const q = ss[(ia + j) % n]!.pos;
          const v = segmentProgress(c, r, { x: q.x, y: q.y, z: q.z });
          checked++;
          if (v < prev - 0.02)
            bad.push(`${c[k]!.gates[0]!.id} +${j}: ${prev.toFixed(3)} -> ${v.toFixed(3)}`);
          prev = Math.max(prev, v);
        }
      }
      expect(checked).toBeGreaterThan(20);
      expect(bad).toEqual([]);
    });
});
