// Can the AI drive a shortcut? Splices an open route from route.json (AUDIT_PATH) into
// the main lap as a whole-lap route and traces an AI lap along it. Or AUDIT_PTS: a JSON
// file of route points ({x, y, z, width, bank}, game coordinates) for the shortcut.
//   AUDIT_FILE=tools/audit/shortcut.audit.ts AUDIT_TRACK=dry_gulch AUDIT_PATH="Haunted Mine Path" \
//     npx vitest run --config tools/audit/vitest.config.ts --disableConsoleIntercept
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { aiLap } from "../../tests/aiLap";

const id = process.env.AUDIT_TRACK ?? "dry_gulch";
const pathId = process.env.AUDIT_PATH ?? "Haunted Mine Path";
type P = { x: number; y: number; z: number };
const d2 = (a: P, b: P) => (a.x - b.x) ** 2 + (a.z - b.z) ** 2;
const enc = (o: unknown) => {
  const b = new TextEncoder().encode(JSON.stringify(o));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
  if (file === "track.json") {
    const j = JSON.parse(b.toString());
    j.lapRoutes = ["kp_shortcut"];
    return enc(j);
  }
  if (file.endsWith("route.json")) {
    const j = JSON.parse(b.toString());
    const main = j.routes.find((r: { id: string }) => r.id === "main");
    const cut = process.env.AUDIT_PTS
      ? { points: JSON.parse(await readFile(process.env.AUDIT_PTS, "utf8")) }
      : j.routes.find((r: { id: string }) => r.id === pathId);
    const near = (p: P) => {
      let k = 0;
      main.points.forEach((q: P, i: number) => d2(q, p) < d2(main.points[k], p) && (k = i));
      return k;
    };
    const a = near(cut.points[0]);
    const z = near(cut.points[cut.points.length - 1]);
    const pts =
      a < z
        ? [...main.points.slice(0, a), ...cut.points, ...main.points.slice(z + 1)]
        : [...main.points.slice(z + 1, a), ...cut.points];
    console.log("splice main", a, "->", z, "points", pts.length);
    j.routes.push({ id: "kp_shortcut", closed: true, points: pts });
    return enc(j);
  }
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};
it("shortcut", async () => {
  const p = await loadTrackPackage(reader, { visual: false });
  const r = await aiLap(p, {
    laps: 1,
    surfaces: true,
    route: "kp_shortcut",
    lapSeconds: 150,
    trace: Number(process.env.TRACE ?? 1),
  });
  console.log(id, "lap", r.race.racers[0]!.lapTimes, "resp", r.respawns, "walls", r.walls);
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
