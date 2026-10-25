import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { aiLap } from "../../tests/aiLap";
import { PLAYERS } from "../../tests/raceSim";
const ids = (process.env.TRACKS ?? "riverbend_palms").split(",");
it("drift", async () => {
  for (const id of ids) {
    const reader: PackageReader = async (file) => {
      const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
      return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
    };
    const p = await loadTrackPackage(reader, { visual: false });
    for (const drift of [0, 0.5, 0.95, 1]) {
      const r = await aiLap(p, {
        laps: 3,
        surfaces: true,
        zippers: true,
        lapSeconds: 160,
        skill: { ...PLAYERS.expert, drift, mistakes: 0 },
      });
      console.log(
        id,
        "drift",
        drift,
        r.race.racers[0]!.lapTimes.map((t) => t.toFixed(1)).join(" "),
        "walls",
        r.walls,
      );
    }
  }
}, 1200000);
