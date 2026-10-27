/**
 * Static triangle-mesh collision for imported tracks (see docs/track-pipeline.md).
 *
 * The collision GLB is split into two sets of triangles:
 * - floors: anything flatter than FLOOR_MIN_NY (~57°) that isn't a wall surface. The
 *   kart drives on these.
 * - walls: steeper triangles, and anything whose surface is a wall. The kart is pushed
 *   out of these with the same `hitWall` as every other wall in the game.
 *
 * Both sets are indexed by a uniform grid over x/z, so a lookup only tests the few
 * triangles in one or two cells. Heights are never "the terrain under x/z": a lookup
 * takes the kart's own height and picks the highest floor at or just below it, so
 * bridges, tunnels and overlapping roads each keep their own surface.
 *
 * Plain data (no Three.js objects), so physics can run in tests and workers.
 */
import * as THREE from "three";
import type { GroundQuery, Surface } from "../physics/ground";

export interface SurfaceDef {
  /** Counts as on the track (off it, closed tracks put you back). */
  road?: boolean;
  /** Always collides as a wall, however flat. */
  wall?: boolean;
  /** Driving onto it starts a zipper boost. */
  boost?: boolean;
  /** Touching it puts you back on the track (lava). */
  respawn?: boolean;
  /** Multipliers on the kart's top speed, acceleration and grip. */
  speed?: number;
  accel?: number;
  grip?: number;
  /** Multiplier on the kart's drag: how fast speed above the surface's top speed bleeds
   * away (soft sand stops a fast kart that cuts across it within a few metres). */
  drag?: number;
}

export type SurfaceTable = Record<string, SurfaceDef>;

/** Triangles flatter than this (normal y) are floors; steeper ones are walls. */
export const FLOOR_MIN_NY = 0.55;
/** A floor this far above the kart can still be stepped up onto (slopes at speed), m. */
export const STEP_UP = 0.5;
/** Grid cell size, metres. */
const CELL = 4;
/** Height used when there's no floor at all under the kart (it falls). */
export const NO_FLOOR = -1000;

export interface TriSet {
  /** 9 floats per triangle: x, y, z of each corner. */
  pos: Float32Array;
  /** 9 floats per triangle: unit vertex normals (floors: always pointing up). */
  nrm: Float32Array;
  /** Surface index (into `surfaces`) per triangle. */
  surf: Uint16Array;
  /** Per-triangle height range, for quick rejects. */
  minY: Float32Array;
  maxY: Float32Array;
  /** Grid: triangle indices per cell. */
  cells: Map<number, number[]>;
  count: number;
}

export interface CollisionMesh {
  floors: TriSet;
  walls: TriSet;
  /** Surface ids, indexed by TriSet.surf. */
  surfaces: string[];
  defs: SurfaceTable;
  bounds: { minX: number; maxX: number; minY: number; maxY: number; minZ: number; maxZ: number };
}

const cellKey = (cx: number, cz: number) => (cx + 32768) * 65536 + (cz + 32768);
const cellOf = (v: number) => Math.floor(v / CELL);

function makeSet(tris: number[][], normals: number[][], surf: number[]): TriSet {
  const n = tris.length;
  const set: TriSet = {
    pos: new Float32Array(n * 9),
    nrm: new Float32Array(n * 9),
    surf: new Uint16Array(n),
    minY: new Float32Array(n),
    maxY: new Float32Array(n),
    cells: new Map(),
    count: n,
  };
  for (let t = 0; t < n; t++) {
    set.pos.set(tris[t]!, t * 9);
    set.nrm.set(normals[t]!, t * 9);
    set.surf[t] = surf[t]!;
    const p = tris[t]!;
    set.minY[t] = Math.min(p[1]!, p[4]!, p[7]!);
    set.maxY[t] = Math.max(p[1]!, p[4]!, p[7]!);
    const x0 = cellOf(Math.min(p[0]!, p[3]!, p[6]!));
    const x1 = cellOf(Math.max(p[0]!, p[3]!, p[6]!));
    const z0 = cellOf(Math.min(p[2]!, p[5]!, p[8]!));
    const z1 = cellOf(Math.max(p[2]!, p[5]!, p[8]!));
    for (let cx = x0; cx <= x1; cx++)
      for (let cz = z0; cz <= z1; cz++) {
        const k = cellKey(cx, cz);
        let list = set.cells.get(k);
        if (!list) set.cells.set(k, (list = []));
        list.push(t);
      }
  }
  return set;
}

/**
 * Build collision from a loaded scene (the collision GLB). Each mesh's world transform
 * is applied. A material's surface comes from its `kp_surface` extra (glTF extras land
 * in material.userData). Returns the mesh and any problems found.
 */
export function buildCollisionMesh(
  root: THREE.Object3D,
  defs: SurfaceTable,
): { mesh: CollisionMesh; warnings: string[] } {
  const warnings: string[] = [];
  const surfaces: string[] = [];
  const surfaceIndex = (id: string) => {
    let i = surfaces.indexOf(id);
    if (i < 0) i = surfaces.push(id) - 1;
    return i;
  };
  const floor: [number[][], number[][], number[]] = [[], [], []];
  const wall: [number[][], number[][], number[]] = [[], [], []];
  const bounds = {
    minX: Infinity,
    maxX: -Infinity,
    minY: Infinity,
    maxY: -Infinity,
    minZ: Infinity,
    maxZ: -Infinity,
  };
  const warned = new Set<string>();
  const warnOnce = (msg: string) => {
    if (!warned.has(msg)) (warnings.push(msg), warned.add(msg));
  };

  root.updateMatrixWorld(true);
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const na = new THREE.Vector3();
  const nb = new THREE.Vector3();
  const nc = new THREE.Vector3();
  const face = new THREE.Vector3();
  const normalMatrix = new THREE.Matrix3();

  root.traverse((obj) => {
    const m = obj as THREE.Mesh;
    if (!m.isMesh || !m.geometry) return;
    const geo = m.geometry;
    const pos = geo.getAttribute("position") as THREE.BufferAttribute | undefined;
    if (!pos) return;
    const nrm = geo.getAttribute("normal") as THREE.BufferAttribute | undefined;
    const index = geo.getIndex();
    normalMatrix.getNormalMatrix(m.matrixWorld);
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    const groups = geo.groups.length
      ? geo.groups
      : [{ start: 0, count: index ? index.count : pos.count, materialIndex: 0 }];

    for (const g of groups) {
      const mat = mats[g.materialIndex ?? 0];
      let id = (mat?.userData?.kp_surface as string | undefined) ?? undefined;
      if (id === undefined) {
        warnOnce(`"${m.name}": material "${mat?.name ?? "none"}" has no kp_surface; using asphalt`);
        id = "asphalt";
      } else if (!defs[id]) {
        warnOnce(`"${m.name}": unknown surface "${id}"; using asphalt`);
        id = "asphalt";
      }
      const def = defs[id]!;
      const si = surfaceIndex(id);
      for (let k = g.start; k + 2 < g.start + g.count; k += 3) {
        const i0 = index ? index.getX(k) : k;
        const i1 = index ? index.getX(k + 1) : k + 1;
        const i2 = index ? index.getX(k + 2) : k + 2;
        a.fromBufferAttribute(pos, i0).applyMatrix4(m.matrixWorld);
        b.fromBufferAttribute(pos, i1).applyMatrix4(m.matrixWorld);
        c.fromBufferAttribute(pos, i2).applyMatrix4(m.matrixWorld);
        face.subVectors(c, b).cross(na.subVectors(a, b));
        const len = face.length();
        if (len < 1e-9) continue; // degenerate
        face.divideScalar(len);
        for (const v of [a, b, c]) {
          bounds.minX = Math.min(bounds.minX, v.x);
          bounds.maxX = Math.max(bounds.maxX, v.x);
          bounds.minY = Math.min(bounds.minY, v.y);
          bounds.maxY = Math.max(bounds.maxY, v.y);
          bounds.minZ = Math.min(bounds.minZ, v.z);
          bounds.maxZ = Math.max(bounds.maxZ, v.z);
        }
        const isFloor = !def.wall && Math.abs(face.y) >= FLOOR_MIN_NY;
        if (nrm) {
          na.fromBufferAttribute(nrm, i0).applyMatrix3(normalMatrix).normalize();
          nb.fromBufferAttribute(nrm, i1).applyMatrix3(normalMatrix).normalize();
          nc.fromBufferAttribute(nrm, i2).applyMatrix3(normalMatrix).normalize();
        } else {
          na.copy(face);
          nb.copy(face);
          nc.copy(face);
        }
        const tri = [a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z];
        if (isFloor) {
          // Floors face up whichever way the triangle was wound.
          const flip = face.y < 0 ? -1 : 1;
          for (const n of [na, nb, nc]) {
            n.multiplyScalar(flip);
            // A smoothed normal that leans too far from the face (a hard edge) is replaced.
            if (n.dot(face) * flip < 0.7) n.copy(face).multiplyScalar(flip);
          }
          floor[0].push(tri);
          floor[1].push([na.x, na.y, na.z, nb.x, nb.y, nb.z, nc.x, nc.y, nc.z]);
          floor[2].push(si);
        } else if (Math.abs(face.y) < FLOOR_MIN_NY || def.wall) {
          wall[0].push(tri);
          wall[1].push([face.x, face.y, face.z, face.x, face.y, face.z, face.x, face.y, face.z]);
          wall[2].push(si);
        }
      }
    }
  });
  const floors = makeSet(...floor);
  if (floors.count === 0) warnings.push("collision has no floor triangles: nothing to drive on");
  return { mesh: { floors, walls: makeSet(...wall), surfaces, defs, bounds }, warnings };
}

/** The floor at (x, z) closest below `refY + STEP_UP`, or the lowest one above it. */
export function floorAt(mesh: CollisionMesh, x: number, z: number, refY: number) {
  const f = mesh.floors;
  const list = f.cells.get(cellKey(cellOf(x), cellOf(z)));
  let best = -1;
  let bestH = -Infinity;
  let bestW = [0, 0, 0];
  let above = -1;
  let aboveH = Infinity;
  let aboveW = [0, 0, 0];
  if (list) {
    for (const t of list) {
      if (f.minY[t]! > refY + 60 || f.maxY[t]! < refY - 400) continue;
      const o = t * 9;
      const p = f.pos;
      // Barycentric coordinates in x/z.
      const x0 = p[o]!;
      const z0 = p[o + 2]!;
      const x1 = p[o + 3]!;
      const z1 = p[o + 5]!;
      const x2 = p[o + 6]!;
      const z2 = p[o + 8]!;
      const det = (z1 - z2) * (x0 - x2) + (x2 - x1) * (z0 - z2);
      if (Math.abs(det) < 1e-12) continue;
      const w0 = ((z1 - z2) * (x - x2) + (x2 - x1) * (z - z2)) / det;
      const w1 = ((z2 - z0) * (x - x2) + (x0 - x2) * (z - z2)) / det;
      const w2 = 1 - w0 - w1;
      const E = -1e-6;
      if (w0 < E || w1 < E || w2 < E) continue;
      const h = w0 * p[o + 1]! + w1 * p[o + 4]! + w2 * p[o + 7]!;
      if (h <= refY + STEP_UP) {
        if (h > bestH) {
          bestH = h;
          best = t;
          bestW = [w0, w1, w2];
        }
      } else if (h < aboveH) {
        aboveH = h;
        above = t;
        aboveW = [w0, w1, w2];
      }
    }
  }
  // Sunk a little into the ground (e.g. after a hard landing): come back up onto it.
  if (best < 0 && above >= 0 && aboveH - refY < 3) return { tri: above, height: aboveH, w: aboveW };
  if (best < 0) return undefined;
  return { tri: best, height: bestH, w: bestW };
}

/**
 * "What's under me?" on an imported track. Pass the kart's height so it picks the
 * right layer; without one it uses the height it last answered with.
 */
export function createMeshGround(mesh: CollisionMesh): GroundQuery {
  let last = 0;
  return {
    at(x: number, z: number, y?: number): Surface {
      const hit = floorAt(mesh, x, z, y ?? last);
      if (!hit) return { height: NO_FLOOR, nx: 0, ny: 1, nz: 0, onRoad: false };
      last = hit.height;
      const n = mesh.floors.nrm;
      const o = hit.tri * 9;
      const [w0, w1, w2] = hit.w as [number, number, number];
      let nx = w0 * n[o]! + w1 * n[o + 3]! + w2 * n[o + 6]!;
      let ny = w0 * n[o + 1]! + w1 * n[o + 4]! + w2 * n[o + 7]!;
      let nz = w0 * n[o + 2]! + w1 * n[o + 5]! + w2 * n[o + 8]!;
      const l = Math.hypot(nx, ny, nz) || 1;
      nx /= l;
      ny /= l;
      nz /= l;
      const surface = mesh.surfaces[mesh.floors.surf[hit.tri]!]!;
      const def = mesh.defs[surface];
      return { height: hit.height, nx, ny, nz, onRoad: Boolean(def?.road), surface };
    },
  };
}

/** Closest point on triangle abc to p (Ericson, Real-Time Collision Detection 5.1.5). */
function closestOnTriangle(
  px: number,
  py: number,
  pz: number,
  t: Float32Array,
  o: number,
  out: Float64Array,
) {
  const ax = t[o]!,
    ay = t[o + 1]!,
    az = t[o + 2]!;
  const bx = t[o + 3]!,
    by = t[o + 4]!,
    bz = t[o + 5]!;
  const cx = t[o + 6]!,
    cy = t[o + 7]!,
    cz = t[o + 8]!;
  const abx = bx - ax,
    aby = by - ay,
    abz = bz - az;
  const acx = cx - ax,
    acy = cy - ay,
    acz = cz - az;
  const apx = px - ax,
    apy = py - ay,
    apz = pz - az;
  const d1 = abx * apx + aby * apy + abz * apz;
  const d2 = acx * apx + acy * apy + acz * apz;
  const set = (x: number, y: number, z: number) => {
    out[0] = x;
    out[1] = y;
    out[2] = z;
  };
  if (d1 <= 0 && d2 <= 0) return set(ax, ay, az);
  const bpx = px - bx,
    bpy = py - by,
    bpz = pz - bz;
  const d3 = abx * bpx + aby * bpy + abz * bpz;
  const d4 = acx * bpx + acy * bpy + acz * bpz;
  if (d3 >= 0 && d4 <= d3) return set(bx, by, bz);
  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) {
    const v = d1 / (d1 - d3);
    return set(ax + abx * v, ay + aby * v, az + abz * v);
  }
  const cpx = px - cx,
    cpy = py - cy,
    cpz = pz - cz;
  const d5 = abx * cpx + aby * cpy + abz * cpz;
  const d6 = acx * cpx + acy * cpy + acz * cpz;
  if (d6 >= 0 && d5 <= d6) return set(cx, cy, cz);
  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) {
    const w = d2 / (d2 - d6);
    return set(ax + acx * w, ay + acy * w, az + acz * w);
  }
  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) {
    const w = (d4 - d3) / (d4 - d3 + (d5 - d6));
    return set(bx + (cx - bx) * w, by + (cy - by) * w, bz + (cz - bz) * w);
  }
  const denom = 1 / (va + vb + vc);
  const v = vb * denom;
  const w = vc * denom;
  set(ax + abx * v + acx * w, ay + aby * v + acy * w, az + abz * v + acz * w);
}

export interface WallContact {
  /** Unit horizontal direction from the kart into the wall. */
  wx: number;
  wz: number;
  /** How far the kart's circle overlaps the wall, m. */
  out: number;
}

/**
 * The slice of wall that blocks a kart standing at height y: from STEP_OVER above its
 * wheels (lower ledges are driven over, like kerbs) to its roof. A wall only stops a
 * flying kart while its top is above the kart's wheels plus STEP_OVER.
 */
export const WALL_BAND = { low: 0.25, high: 1.4 };
const tmp = new Float64Array(3);

/**
 * The deepest wall the kart (a circle of `radius` at height y) is overlapping, or null.
 * Walls lower than WALL_BAND.low above the kart's feet can be driven over.
 */
export function deepestWall(
  mesh: CollisionMesh,
  x: number,
  y: number,
  z: number,
  radius: number,
  /** The way the kart's moving (horizontal, any length), when it is: a middle right on a
   * wall's plane is pushed back out the side it came from, not always the face's front
   * (a thin wall or rail, met edge on or dropped onto, pushed karts out its far side). */
  vx = 0,
  vz = 0,
): WallContact | null {
  const w = mesh.walls;
  const low = y + WALL_BAND.low;
  const high = y + WALL_BAND.high;
  let best: WallContact | null = null;
  const seen = new Set<number>();
  for (let cx = cellOf(x - radius); cx <= cellOf(x + radius); cx++)
    for (let cz = cellOf(z - radius); cz <= cellOf(z + radius); cz++) {
      const list = w.cells.get(cellKey(cx, cz));
      if (!list) continue;
      for (const t of list) {
        if (seen.has(t)) continue;
        seen.add(t);
        if (w.maxY[t]! < low || w.minY[t]! > high) continue;
        const o = t * 9;
        // Test at the middle of the part of the wall that overlaps the kart's slice.
        const mid = (Math.max(low, w.minY[t]!) + Math.min(high, w.maxY[t]!)) / 2;
        closestOnTriangle(x, mid, z, w.pos, o, tmp);
        if (tmp[1]! < low - 1e-6 || tmp[1]! > high + 1e-6) continue;
        let dx = x - tmp[0]!;
        let dz = z - tmp[2]!;
        let d = Math.hypot(dx, dz);
        if (d >= radius) continue;
        if (d < 1e-5) {
          // Centre right on the wall's plane: push out along its horizontal normal, on the
          // side the kart came from.
          dx = w.nrm[o]!;
          dz = w.nrm[o + 2]!;
          const l = Math.hypot(dx, dz) || 1;
          dx /= l;
          dz /= l;
          if (dx * vx + dz * vz > 0) {
            dx = -dx;
            dz = -dz;
          }
          d = 0;
        } else {
          dx /= d;
          dz /= d;
        }
        const out = radius - d;
        if (!best || out > best.out) best = { wx: -dx, wz: -dz, out };
      }
    }
  return best;
}

/** A kart's config on a surface: its speed, acceleration and grip scaled. */
export function applySurface<
  T extends { topSpeed: number; accel: number; grip: number; drag?: number },
>(cfg: T, def: SurfaceDef | undefined): T {
  if (
    !def ||
    ((def.speed ?? 1) === 1 &&
      (def.accel ?? 1) === 1 &&
      (def.grip ?? 1) === 1 &&
      (def.drag ?? 1) === 1)
  )
    return cfg;
  return {
    ...cfg,
    topSpeed: cfg.topSpeed * (def.speed ?? 1),
    accel: cfg.accel * (def.accel ?? 1),
    grip: cfg.grip * (def.grip ?? 1),
    ...(cfg.drag !== undefined && def.drag !== undefined ? { drag: cfg.drag * def.drag } : {}),
  };
}
