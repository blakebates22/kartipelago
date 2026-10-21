/**
 * Oasis Haven's living water, from track.json entities. Purely visual: nothing here
 * changes how a kart drives.
 *
 *   boat      { "type": "boat", "route": "Boat Path 1", "speed": 4, "start": 0,
 *             "colors": ["#e02a2a", "#f6c03a"], "scale": 1 }
 *             A little sailing boat going round a path from route.json (drawn in
 *             Blender as a curve on the water), bobbing and heeling, a wake behind it.
 *   fountain  { "type": "fountain", "x", "y", "z", "height": 6, "jets": 6,
 *             "radius": 3.5 }: jets of spray: one straight up `height` metres, and a
 *             ring of `jets` arcing out to land `radius` metres away (the basin is
 *             scenery). Splashes where they land.
 *
 * The timing is pure (no three.js) here; render/oasisFx.ts draws them.
 */
import type { RouteFile } from "../world/trackPackage";

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export interface BoatPath {
  pts: { x: number; y: number; z: number; d: number }[];
  length: number;
}

export interface BoatConfig {
  path: BoatPath;
  speed: number;
  start: number;
  colors: string[];
  scale: number;
}

export function parseBoat(
  e: Record<string, unknown>,
  routes: RouteFile["routes"],
): BoatConfig | undefined {
  const r = routes.find((q) => q.id === e.route);
  if (!r || r.points.length < 3) return undefined;
  let d = 0;
  const pts = r.points.map((p, k) => {
    if (k) d += Math.hypot(p.x - r.points[k - 1]!.x, p.z - r.points[k - 1]!.z);
    return { x: p.x, y: p.y, z: p.z, d };
  });
  const a = r.points[0]!;
  const b = r.points[r.points.length - 1]!;
  const colors = Array.isArray(e.colors)
    ? e.colors.filter((c): c is string => typeof c === "string")
    : [];
  return {
    path: { pts, length: d + Math.hypot(a.x - b.x, a.z - b.z) },
    speed: num(e.speed, 4),
    start: num(e.start, 0),
    colors: colors.length ? colors : ["#e02a2a", "#f6f2e6"],
    scale: Math.max(0.3, num(e.scale, 1)),
  };
}

/** Where a boat is at time t: position on its loop, heading (game: 0 = +Z), and its
 * bob, heel and pitch on the little waves. */
export function boatAt(c: BoatConfig, t: number) {
  const { pts, length } = c.path;
  const d = (((c.start + c.speed * t) % length) + length) % length;
  let i = 0;
  while (i + 1 < pts.length && pts[i + 1]!.d <= d) i++;
  const a = pts[i]!;
  const b = pts[(i + 1) % pts.length]!;
  const span = (i + 1 < pts.length ? b.d : length) - a.d;
  const f = span > 0 ? (d - a.d) / span : 0;
  const x = a.x + (b.x - a.x) * f;
  const z = a.z + (b.z - a.z) * f;
  const heading = Math.atan2(b.x - a.x, b.z - a.z);
  const ph = c.start * 0.37;
  return {
    x,
    y: a.y + (b.y - a.y) * f + 0.12 * Math.sin(t * 1.6 + ph),
    z,
    heading,
    heel: 0.12 + 0.05 * Math.sin(t * 0.9 + ph),
    pitch: 0.04 * Math.sin(t * 1.3 + ph * 2),
  };
}

export interface FountainConfig {
  x: number;
  y: number;
  z: number;
  height: number;
  jets: number;
  radius: number;
}

export function parseFountain(e: Record<string, unknown>): FountainConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    height: Math.max(0.5, num(e.height, 6)),
    jets: Math.max(0, Math.min(16, Math.round(num(e.jets, 6)))),
    radius: Math.max(0.5, num(e.radius, 3.5)),
  };
}

/** Arcade gravity for spray, m/s². */
export const SPRAY_GRAVITY = 14;

/**
 * The launch velocity of jet k (k = 0: the middle one, straight up; then the ring) so
 * that it peaks at the right height and lands at the right place: [vx, vy, vz] in
 * game axes, and its flight time.
 */
export function jetVelocity(
  c: FountainConfig,
  k: number,
): { v: [number, number, number]; t: number } {
  if (k === 0) {
    const vy = Math.sqrt(2 * SPRAY_GRAVITY * c.height);
    return { v: [0, vy, 0], t: (2 * vy) / SPRAY_GRAVITY };
  }
  const a = ((k - 1) / Math.max(1, c.jets)) * Math.PI * 2;
  const h = c.height * 0.45;
  const vy = Math.sqrt(2 * SPRAY_GRAVITY * h);
  const t = (2 * vy) / SPRAY_GRAVITY;
  const vh = c.radius / t;
  return { v: [Math.sin(a) * vh, vy, Math.cos(a) * vh], t };
}
