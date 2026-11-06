/**
 * Ducks on the Burnt Gorge's river (Blake, Nov 6, review journey_gorge 1 note 17: "can we
 * get some high fidelity ducks swimming in the river?"): a family to each stretch, the
 * drake and the hen paddling up and down it and the ducklings in a line behind the hen;
 * now and then one dabbles (tail up, head under) or looks about. Drawn by render/duck.ts.
 *
 *   ducks  { "type": "ducks", "points": [[x, y, z], ...], "count": 5, "seed": 11 }
 *          (points: the stretch of water, game space, at its surface)
 */

export type DuckKind = "drake" | "hen" | "duckling";
export type DuckAct = "swim" | "dabble" | "look";

export interface Ducks {
  points: { x: number; y: number; z: number }[];
  /** Distance along the stretch at each point (m). */
  cum: number[];
  length: number;
  count: number;
  seed: number;
}

export interface DuckPose {
  x: number;
  y: number;
  z: number;
  heading: number;
  act: DuckAct;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export function parseDucks(e: Record<string, unknown>): Ducks {
  const pts = (Array.isArray(e.points) ? e.points : [])
    .filter((p): p is unknown[] => Array.isArray(p) && p.length >= 3)
    .map((p) => ({ x: num(p[0], 0), y: num(p[1], 0), z: num(p[2], 0) }));
  if (pts.length < 2)
    pts.push({ ...(pts[0] ?? { x: 0, y: 0, z: 0 }) }, { ...(pts[0] ?? { x: 1, y: 0, z: 0 }) });
  const cum = [0];
  for (let i = 1; i < pts.length; i++)
    cum.push(cum[i - 1]! + Math.hypot(pts[i]!.x - pts[i - 1]!.x, pts[i]!.z - pts[i - 1]!.z));
  return {
    points: pts,
    cum,
    length: Math.max(0.01, cum[cum.length - 1]!),
    count: Math.max(1, Math.min(8, Math.round(num(e.count, 4)))),
    seed: Math.round(num(e.seed, 1)),
  };
}

/** Who each one is: the drake, the hen, then her ducklings. */
export function duckKind(i: number): DuckKind {
  return i === 0 ? "drake" : i === 1 ? "hen" : "duckling";
}

/** The point at distance s along the stretch, and its direction (unit, in x and z). */
export function along(d: Ducks, s: number) {
  const c = Math.max(0, Math.min(d.length, s));
  let i = 1;
  while (i < d.cum.length - 1 && d.cum[i]! < c) i++;
  const a = d.points[i - 1]!;
  const b = d.points[i]!;
  const seg = d.cum[i]! - d.cum[i - 1]! || 1;
  const t = (c - d.cum[i - 1]!) / seg;
  const dx = (b.x - a.x) / seg;
  const dz = (b.z - a.z) / seg;
  return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t, dx, dz };
}

const SPEED = 0.45;

/** Where duck i is at time t: up the stretch and back; the ducklings trailing the hen. */
export function duckAt(d: Ducks, i: number, t: number): DuckPose {
  const L = d.length;
  const lead = i === 0 ? 0 : 1; // (the drake's own way; the ducklings follow the hen)
  const phase = d.seed * 7.3 + (lead ? 0 : 3.1);
  const run = (t * SPEED * (lead ? 0.92 : 1) + phase) % (2 * L);
  const back = run > L;
  let s = back ? 2 * L - run : run;
  const dir = back ? -1 : 1;
  // (ducklings in a line behind the hen, each a little to one side)
  if (i >= 2) s -= dir * 0.65 * (i - 1);
  s = Math.max(0, Math.min(L, s));
  const p = along(d, s);
  const side = i === 0 ? 1.4 : i === 1 ? 0 : 0.25 * Math.sin(i * 2.1 + t * 0.8);
  const wob = 0.18 * Math.sin(t * 0.7 + i * 1.9);
  const nx = -p.dz;
  const nz = p.dx;
  const heading = Math.atan2(p.dx * dir, p.dz * dir) + 0.12 * Math.sin(t * 0.5 + i);
  const k = Math.sin(t * 0.37 + i * 2.1 + d.seed);
  const act: DuckAct = k > 0.93 ? "dabble" : k > 0.78 ? "look" : "swim";
  return { x: p.x + nx * (side + wob), y: p.y, z: p.z + nz * (side + wob), heading, act };
}
