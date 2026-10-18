/**
 * Solid things on open tracks, which karts collide with like walls: the rock either
 * side of a tunnel, the boundary round the edge of the map, and trees.
 *
 * Open tracks have no walls along the road. You can drive anywhere on the grass; only
 * these stop you.
 */
import type { Track } from "./track";

/** A box standing on the ground, turned to `heading` (its length runs along it). */
export interface SolidBox {
  kind: "box";
  /** What it is, for drawing. */
  look: "rock" | "boundary";
  x: number;
  z: number;
  heading: number;
  halfLength: number;
  halfWidth: number;
  height: number;
}

/** An upright cylinder: a tree trunk. */
export interface SolidCircle {
  kind: "circle";
  look: "tree";
  x: number;
  z: number;
  radius: number;
  height: number;
}

export type Solid = SolidBox | SolidCircle;

export interface TunnelSpot {
  /** Where the tunnel starts and ends, metres along the lap. Must be a straight. */
  from: number;
  to: number;
  /** Rock thickness either side of the road, metres (default 18). */
  thickness?: number;
  /** Height of the roof above the road, metres (default 9). */
  height?: number;
}

export interface Tunnel {
  /** Centre of the road through the tunnel, its direction and size. */
  x: number;
  y: number;
  z: number;
  heading: number;
  halfLength: number;
  roadHalfWidth: number;
  thickness: number;
  height: number;
}

export interface SceneryConfig {
  /** How many trees to try to place. */
  trees: number;
  /** Seed for tree placement, so the layout is the same every time. */
  seed: number;
  /** Trees stay at least this far from the road edge, metres. */
  treeClearance: number;
  /** Trees stay within this far from the road edge, metres (so they frame the course). */
  treeSpread: number;
  /** Tree trunk radius (the part you hit), metres. */
  treeRadius: number;
  /** Boundary distance outside the course, metres. */
  boundaryMargin: number;
}

const sampleAt = (track: Track, at: number) => {
  const n = track.samples.length;
  return track.samples[((Math.round((at / track.length) * n) % n) + n) % n]!;
};

export function buildTunnel(track: Track, spot: TunnelSpot): Tunnel {
  const a = sampleAt(track, spot.from);
  const b = sampleAt(track, spot.to);
  const length = Math.hypot(b.pos.x - a.pos.x, b.pos.z - a.pos.z);
  return {
    x: (a.pos.x + b.pos.x) / 2,
    y: Math.min(a.pos.y, b.pos.y),
    z: (a.pos.z + b.pos.z) / 2,
    heading: Math.atan2(b.pos.x - a.pos.x, b.pos.z - a.pos.z),
    halfLength: length / 2,
    roadHalfWidth: Math.max(a.width, b.width) / 2,
    thickness: spot.thickness ?? 18,
    height: spot.height ?? 9,
  };
}

/** The two blocks of rock either side of a tunnel (the roof is only drawn). */
export function tunnelSolids(t: Tunnel): SolidBox[] {
  const off = t.roadHalfWidth + t.thickness / 2;
  // Across the road: perpendicular to forward (sin h, cos h).
  const rx = Math.cos(t.heading);
  const rz = -Math.sin(t.heading);
  return [-1, 1].map((side) => ({
    kind: "box",
    look: "rock",
    x: t.x + rx * off * side,
    z: t.z + rz * off * side,
    heading: t.heading,
    halfLength: t.halfLength,
    halfWidth: t.thickness / 2,
    height: t.height + 3,
  }));
}

/** Square-cornered boundary round the whole course, `margin` outside it. */
export function boundarySolids(track: Track, margin: number): SolidBox[] {
  let minX = Infinity;
  let maxX = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;
  for (const s of track.samples) {
    const r = s.width / 2;
    minX = Math.min(minX, s.pos.x - r);
    maxX = Math.max(maxX, s.pos.x + r);
    minZ = Math.min(minZ, s.pos.z - r);
    maxZ = Math.max(maxZ, s.pos.z + r);
  }
  minX -= margin;
  maxX += margin;
  minZ -= margin;
  maxZ += margin;
  const T = 4; // thickness
  const H = 5; // height
  const cx = (minX + maxX) / 2;
  const cz = (minZ + maxZ) / 2;
  const hx = (maxX - minX) / 2 + T;
  const hz = (maxZ - minZ) / 2 + T;
  const box = (x: number, z: number, heading: number, halfLength: number): SolidBox => ({
    kind: "box",
    look: "boundary",
    x,
    z,
    heading,
    halfLength,
    halfWidth: T / 2,
    height: H,
  });
  return [
    box(cx, maxZ + T / 2, Math.PI / 2, hx), // north (runs along x)
    box(cx, minZ - T / 2, Math.PI / 2, hx),
    box(maxX + T / 2, cz, 0, hz), // east (runs along z)
    box(minX - T / 2, cz, 0, hz),
  ];
}

/** A small deterministic random number generator (mulberry32). */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Distance from (x, z) to the road edge (negative = on the road). */
function edgeDistance(track: Track, x: number, z: number): number {
  let best = Infinity;
  for (const s of track.samples) {
    const d = Math.hypot(s.pos.x - x, s.pos.z - z) - s.width / 2;
    if (d < best) best = d;
  }
  return best;
}

/**
 * Trees scattered beside the course: near enough to frame it, never on the road, in a
 * tunnel's rock, or too close to each other or the boundary.
 */
export function placeTrees(track: Track, cfg: SceneryConfig, avoid: Solid[]): SolidCircle[] {
  const rand = rng(cfg.seed);
  const trees: SolidCircle[] = [];
  const n = track.samples.length;
  for (let attempt = 0; attempt < cfg.trees * 6 && trees.length < cfg.trees; attempt++) {
    const s = track.samples[Math.floor(rand() * n)]!;
    const side = rand() < 0.5 ? -1 : 1;
    const out = s.width / 2 + cfg.treeClearance + rand() * cfg.treeSpread;
    const rh = Math.hypot(s.right.x, s.right.z);
    const x = s.pos.x + (s.right.x / rh) * out * side;
    const z = s.pos.z + (s.right.z / rh) * out * side;
    if (edgeDistance(track, x, z) < cfg.treeClearance) continue;
    if (trees.some((t) => Math.hypot(t.x - x, t.z - z) < 7)) continue;
    if (avoid.some((b) => b.kind === "box" && insideBox(b, x, z, 6))) continue;
    trees.push({ kind: "circle", look: "tree", x, z, radius: cfg.treeRadius, height: 8 });
  }
  return trees;
}

/** Whether (x, z) is inside a box grown by `grow` metres on every side. */
export function insideBox(b: SolidBox, x: number, z: number, grow = 0): boolean {
  const dx = x - b.x;
  const dz = z - b.z;
  const along = dx * Math.sin(b.heading) + dz * Math.cos(b.heading);
  const across = dx * Math.cos(b.heading) - dz * Math.sin(b.heading);
  return Math.abs(along) <= b.halfLength + grow && Math.abs(across) <= b.halfWidth + grow;
}
