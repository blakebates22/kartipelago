import { readFile } from "node:fs/promises";
import { it } from "vitest";
import { createMeshGround, deepestWall } from "../../src/world/collisionMesh";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
it("grid", async () => {
  const T = process.env.AUDIT_TRACK!;
  const reader: PackageReader = async (f) => {
    const b = await readFile(`/home/claude/kp2/public/tracks/${T}/${f}`);
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };
  const p = await loadTrackPackage(reader, { visual: false });
  const g = createMeshGround(p.collision);
  const [x0, z0] = process.env.AT!.split(",").map(Number) as [number, number];
  for (let dz = -2; dz <= 2; dz += 0.5) {
    let row = "";
    for (let dx = -2; dx <= 2; dx += 0.5) {
      const h = g.at(x0 + dx, z0 + dz, 4).height;
      const w = deepestWall(p.collision, x0 + dx, h, z0 + dz, 0.3);
      row += (h.toFixed(2) + (w ? "W" : " ")).padStart(7);
    }
    console.log(row);
  }
}, 60000);
