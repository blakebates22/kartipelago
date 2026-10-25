import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { aiLap } from "../../tests/aiLap";
import { STEADY } from "../../src/ai/driver";
import { TIERS } from "../../src/ai/skill";
import { PLAYERS } from "../../tests/raceSim";
const ids = (process.env.TRACKS ?? "riverbend_palms").split(",");
it("drift vs not", async () => {
  for (const id of ids) {
    const reader: PackageReader = async (file) => {
      const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
      return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
    };
    const p = await loadTrackPackage(reader, { visual: false });
    for (const [name, sk] of Object.entries({
      steady: STEADY,
      tap: { ...STEADY, tapping: 1 },
      boost: { ...STEADY, boosting: 1 },
      both: { ...STEADY, tapping: 1, boosting: 1 },
      strong: TIERS.strong,
      good: TIERS.good,
      weak: TIERS.weak,
      novice: PLAYERS.novice,
      competent: PLAYERS.competent,
      expert: PLAYERS.expert,
    })) {
      const r = await aiLap(p, {
        laps: 2,
        surfaces: true,
        zippers: true,
        lapSeconds: 160,
        skill: sk,
      });
      console.log(
        id,
        "drift",
        name,
        r.race.racers[0]!.lapTimes.map((t) => t.toFixed(1)),
        "walls",
        r.walls,
      );
    }
  }
}, 3_600_000);
