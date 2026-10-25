// Where does the AI get stuck? Traces a 2-lap AI run (every 2 s) on AUDIT_TRACK.
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { aiLap } from "../../tests/aiLap";
const id = process.env.AUDIT_TRACK ?? "dragon_isles";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
it("trace", async () => {
  const p = await loadTrackPackage(reader, { visual: false });
  const r = await aiLap(p, {
    laps: 2,
    surfaces: true,
    zippers: true,
    lapSeconds: 150,
    trace: Number(process.env.TRACE ?? 2),
  });
  console.log(
    id,
    "laps",
    r.race.racers[0]!.lapTimes.map((t) => t.toFixed(1)),
    "resp",
    r.respawns,
    "walls",
    r.walls,
  );
  for (const q of r.path)
    console.log(
      q.t.toFixed(0),
      q.x.toFixed(0),
      q.y.toFixed(1),
      q.z.toFixed(0),
      "v",
      q.v.toFixed(1),
      "gate",
      q.gate,
    );
}, 600000);
