/**
 * Ledges you can get caught on: walks a course's lap and, across the road at every
 * metre, looks for a wall of its collision inside the road (a kart's height off the
 * floor) or a step in the floor big enough to catch on. Prints the worst spots.
 *
 *   AUDIT_FILE=tools/audit/ledge.audit.ts AUDIT_TRACK=ember_peak [FROM=500 TO=700] \
 *     npx vitest run --config tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { buildTrack } from "../../src/world/track";
import { createMeshGround, deepestWall } from "../../src/world/collisionMesh";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

const T = process.env.AUDIT_TRACK ?? "ember_peak";
const reader: PackageReader = async (file) => {
  const b = await readFile(new URL(`../../public/tracks/${T}/${file}`, import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
};

it("ledges", async () => {
  const pkg = await loadTrackPackage(reader, { visual: false });
  const track = buildTrack(pkg.trackData, 1);
  const ground = createMeshGround(pkg.collision);
  const from = Number(process.env.FROM ?? 0);
  const to = Number(process.env.TO ?? 1e9);
  const out: { s: number; x: number; z: number; across: number; what: string; size: number }[] = [];
  for (const smp of track.samples) {
    if (smp.dist < from || smp.dist > to) continue;
    const half = smp.width / 2 + 0.5;
    let prev: number | undefined;
    for (let a = -half; a <= half + 1e-6; a += 0.5) {
      const x = smp.pos.x + smp.right.x * a;
      const z = smp.pos.z + smp.right.z * a;
      const g = ground.at(x, z, smp.pos.y + 3);
      const y = g.height;
      if (!Number.isFinite(y) || y < smp.pos.y - 6) continue;
      // A step across the road.
      if (prev !== undefined && Math.abs(y - prev) > 0.3)
        out.push({ s: smp.dist, x, z, across: a, what: "step across", size: Math.abs(y - prev) });
      prev = y;
      // A step along it (a metre on).
      const x2 = x + smp.forward.x;
      const z2 = z + smp.forward.z;
      const y2 = ground.at(x2, z2, y + 3).height;
      if (Number.isFinite(y2) && Math.abs(y2 - y) > 0.3 && Math.abs(y2 - y) < 6)
        out.push({ s: smp.dist, x, z, across: a, what: "step along", size: Math.abs(y2 - y) });
      // A wall standing in the road (kart radius 1).
      const w = deepestWall(pkg.collision, x, y, z, 1.0);
      if (w && Math.abs(a) < smp.width / 2 - 0.5)
        out.push({ s: smp.dist, x, z, across: a, what: "wall in road", size: w.out });
    }
  }
  out.sort((p, q) => q.size - p.size);
  console.log(`${T}: ${out.length} spots (lap ${track.length.toFixed(0)} m)`);
  for (const o of out.slice(0, 40))
    console.log(
      `${o.what.padEnd(13)} s=${o.s.toFixed(0)} across=${o.across.toFixed(1)} at ${o.x.toFixed(1)},${o.z.toFixed(1)} size ${o.size.toFixed(2)}`,
    );
}, 300000);
