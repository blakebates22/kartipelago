import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { aiLap } from "../../tests/aiLap";
import { PLAYERS } from "../../tests/raceSim";
const id = process.env.AUDIT_TRACK ?? "bonebog_pyramid";
it("gates", async () => {
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const rows: Record<number, number[]> = {};
  for (const drift of [0, 1]) {
    const r = await aiLap(p, {
      laps: 2,
      surfaces: true,
      zippers: true,
      lapSeconds: 160,
      trace: 0.1,
      skill: { ...PLAYERS.expert, drift, mistakes: 0 },
    });
    const seen = new Set<number>();
    for (const q of r.path) {
      if (q.t < r.race.racers[0]!.lapTimes[0]!) continue; // the second (flying) lap
      if (!seen.has(q.gate)) {
        seen.add(q.gate);
        (rows[q.gate] ??= []).push(q.t);
      }
    }
    console.log("drift", drift, r.race.racers[0]!.lapTimes.map((t) => t.toFixed(1)).join(" "));
  }
  let prev: number[] | undefined;
  for (const [g, ts] of Object.entries(rows)) {
    if (prev && ts.length === 2 && prev.length === 2)
      console.log(
        "gate",
        g,
        "steer",
        (ts[0]! - prev[0]!).toFixed(2),
        "drift",
        (ts[1]! - prev[1]!).toFixed(2),
      );
    prev = ts;
  }
}, 600000);
