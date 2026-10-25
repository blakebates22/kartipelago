// An AI's lap times on a course: AUDIT_TRACK=<id> LAPS=3 (tools/audit/vitest.config.ts).
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { aiLap } from "../../tests/aiLap";
it("laps", async () => {
  const id = process.env.AUDIT_TRACK ?? "coral_cove";
  const reader: PackageReader = async (file) => {
    const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const r = await aiLap(p, {
    laps: Number(process.env.LAPS ?? 3),
    surfaces: true,
    zippers: true,
    lapSeconds: 200,
  });
  const laps = r.race.racers[0]!.lapTimes;
  console.log(
    id,
    "laps",
    laps.map((t) => t.toFixed(2)).join(" "),
    "total",
    laps.reduce((a, b) => a + b, 0).toFixed(2),
    "respawns",
    r.respawns,
  );
});
