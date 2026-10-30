// A small glTF-binary reader for the tests: every mesh node's triangles in world space,
// with its name (no three.js loader, no images).
import { readFile } from "node:fs/promises";

type Mat = number[]; // column-major 4x4

const ident = (): Mat => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

function mul(a: Mat, b: Mat): Mat {
  const o = new Array(16).fill(0);
  for (let c = 0; c < 4; c++)
    for (let r = 0; r < 4; r++)
      for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r]! * b[c * 4 + k]!;
  return o;
}

function trs(n: {
  translation?: number[];
  rotation?: number[];
  scale?: number[];
  matrix?: number[];
}): Mat {
  if (n.matrix) return n.matrix.slice();
  const [tx = 0, ty = 0, tz = 0] = n.translation ?? [];
  const [x = 0, y = 0, z = 0, w = 1] = n.rotation ?? [];
  const [sx = 1, sy = 1, sz = 1] = n.scale ?? [];
  return [
    (1 - 2 * (y * y + z * z)) * sx,
    2 * (x * y + z * w) * sx,
    2 * (x * z - y * w) * sx,
    0,
    2 * (x * y - z * w) * sy,
    (1 - 2 * (x * x + z * z)) * sy,
    2 * (y * z + x * w) * sy,
    0,
    2 * (x * z + y * w) * sz,
    2 * (y * z - x * w) * sz,
    (1 - 2 * (x * x + y * y)) * sz,
    0,
    tx,
    ty,
    tz,
    1,
  ];
}

export interface GlbMesh {
  name: string;
  /** World positions, xyz per vertex. */
  pos: Float32Array;
  /** Triangles: vertex indices, three each. */
  tris: Uint32Array;
}

export async function readGlb(path: string | URL): Promise<GlbMesh[]> {
  const buf = await readFile(path);
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  let off = 12;
  let json: any;
  let bin: DataView | undefined;
  while (off < buf.byteLength) {
    const len = dv.getUint32(off, true);
    const type = dv.getUint32(off + 4, true);
    const start = off + 8;
    if (type === 0x4e4f534a)
      json = JSON.parse(new TextDecoder().decode(buf.subarray(start, start + len)));
    else if (type === 0x004e4942) bin = new DataView(buf.buffer, buf.byteOffset + start, len);
    off = start + len;
  }
  if (!json || !bin) return [];
  const access = (i: number) => {
    const a = json.accessors[i];
    const bv = json.bufferViews[a.bufferView];
    const comps = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[a.type as string] ?? 1;
    const size = { 5126: 4, 5125: 4, 5123: 2, 5121: 1 }[a.componentType as number] ?? 4;
    const stride = bv.byteStride ?? comps * size;
    const base = (bv.byteOffset ?? 0) + (a.byteOffset ?? 0);
    const out = new Float64Array(a.count * comps);
    for (let k = 0; k < a.count; k++)
      for (let c = 0; c < comps; c++) {
        const p = base + k * stride + c * size;
        out[k * comps + c] =
          a.componentType === 5126
            ? bin!.getFloat32(p, true)
            : a.componentType === 5125
              ? bin!.getUint32(p, true)
              : a.componentType === 5123
                ? bin!.getUint16(p, true)
                : bin!.getUint8(p);
      }
    return out;
  };
  const meshes: GlbMesh[] = [];
  const visit = (ni: number, parent: Mat) => {
    const n = json.nodes[ni];
    const m = mul(parent, trs(n));
    if (n.mesh !== undefined) {
      for (const prim of json.meshes[n.mesh].primitives) {
        if (prim.attributes.POSITION === undefined) continue;
        const p = access(prim.attributes.POSITION);
        const pos = new Float32Array(p.length);
        for (let k = 0; k < p.length; k += 3) {
          const x = p[k]!;
          const y = p[k + 1]!;
          const z = p[k + 2]!;
          pos[k] = m[0]! * x + m[4]! * y + m[8]! * z + m[12]!;
          pos[k + 1] = m[1]! * x + m[5]! * y + m[9]! * z + m[13]!;
          pos[k + 2] = m[2]! * x + m[6]! * y + m[10]! * z + m[14]!;
        }
        const idx = prim.indices !== undefined ? access(prim.indices) : undefined;
        const tris = new Uint32Array(idx ? idx.length : pos.length / 3);
        for (let k = 0; k < tris.length; k++) tris[k] = idx ? idx[k]! : k;
        meshes.push({ name: n.name ?? "", pos, tris });
      }
    }
    for (const c of n.children ?? []) visit(c, m);
  };
  const scene = json.scenes[json.scene ?? 0];
  for (const r of scene.nodes) visit(r, ident());
  return meshes;
}

/** The highest surface of `meshes` under (x, z) below height y, or undefined: a grid of
 * their triangles for quick lookups. */
export function heightField(meshes: GlbMesh[], cell = 8) {
  const grid = new Map<string, { m: GlbMesh; t: number }[]>();
  for (const m of meshes)
    for (let t = 0; t < m.tris.length; t += 3) {
      let x0 = Infinity,
        x1 = -Infinity,
        z0 = Infinity,
        z1 = -Infinity;
      for (let k = 0; k < 3; k++) {
        const i = m.tris[t + k]! * 3;
        x0 = Math.min(x0, m.pos[i]!);
        x1 = Math.max(x1, m.pos[i]!);
        z0 = Math.min(z0, m.pos[i + 2]!);
        z1 = Math.max(z1, m.pos[i + 2]!);
      }
      for (let gx = Math.floor(x0 / cell); gx <= Math.floor(x1 / cell); gx++)
        for (let gz = Math.floor(z0 / cell); gz <= Math.floor(z1 / cell); gz++) {
          const k = `${gx},${gz}`;
          const l = grid.get(k);
          if (l) l.push({ m, t });
          else grid.set(k, [{ m, t }]);
        }
    }
  return (x: number, z: number, below: number): number | undefined => {
    let best: number | undefined;
    for (const { m, t } of grid.get(`${Math.floor(x / cell)},${Math.floor(z / cell)}`) ?? []) {
      const a = m.tris[t]! * 3;
      const b = m.tris[t + 1]! * 3;
      const c = m.tris[t + 2]! * 3;
      const ax = m.pos[a]!,
        az = m.pos[a + 2]!;
      const bx = m.pos[b]!,
        bz = m.pos[b + 2]!;
      const cx = m.pos[c]!,
        cz = m.pos[c + 2]!;
      const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
      if (Math.abs(d) < 1e-9) continue;
      const u = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d;
      const v = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d;
      const w = 1 - u - v;
      if (u < -1e-6 || v < -1e-6 || w < -1e-6) continue;
      const y = u * m.pos[a + 1]! + v * m.pos[b + 1]! + w * m.pos[c + 1]!;
      if (y <= below && (best === undefined || y > best)) best = y;
    }
    return best;
  };
}
