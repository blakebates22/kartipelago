/**
 * Every floor triangle over one spot, top to bottom (height, surface, triangle's slope):
 * for working out what a kart drove in under.
 *   AUDIT_FILE=tools/audit/column.audit.ts AUDIT_TRACK=<id> AT=x,z[;x,z...] npx vitest run \
 *     --config tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";

it("column", async () => {
  const T = process.env.AUDIT_TRACK!;
  const reader: PackageReader = async (f) => {
    const b = await readFile(new URL(`../../public/tracks/${T}/${f}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const f = p.collision.floors;
  for (const at of process.env.AT!.split(";")) {
    const [x, z] = at.split(",").map(Number) as [number, number];
    const out: string[] = [];
    for (let t = 0; t < f.count; t++) {
      const o = t * 9;
      const q = f.pos;
      const [x0, z0, x1, z1, x2, z2] = [
        q[o]!,
        q[o + 2]!,
        q[o + 3]!,
        q[o + 5]!,
        q[o + 6]!,
        q[o + 8]!,
      ];
      const det = (z1 - z2) * (x0 - x2) + (x2 - x1) * (z0 - z2);
      if (Math.abs(det) < 1e-12) continue;
      const w0 = ((z1 - z2) * (x - x2) + (x2 - x1) * (z - z2)) / det;
      const w1 = ((z2 - z0) * (x - x2) + (x0 - x2) * (z - z2)) / det;
      const w2 = 1 - w0 - w1;
      if (w0 < 0 || w1 < 0 || w2 < 0) continue;
      const h = w0 * q[o + 1]! + w1 * q[o + 4]! + w2 * q[o + 7]!;
      out.push(`${h.toFixed(2)} ${p.collision.surfaces[f.surf[t]!]} tri ${t}`);
    }
    out.sort((a, b) => parseFloat(b) - parseFloat(a));
    console.log(`${T} @ ${x},${z}:\n  ${out.join("\n  ")}`);
  }
}, 120000);
