/**
 * Snow Dragon Pass: the blizzard, the prayer flags, the bells and the avalanches
 * (track.json entities, written by tools/blender/prehistoric/snow_town.py).
 *
 *   blizzard      { "wind": [x, z], "keys": [[x, y, z, strength], ...] }
 *                 How hard it snows (0..1) all along every road, and which way the wind
 *                 blows (a horizontal direction). Wherever the camera is, the nearest
 *                 keys say how thick the snow is: fierce on the exposed heights, gentler
 *                 in the village, none in the tunnels. On top of that the storm ebbs and
 *                 gusts on its own slow rhythm. Purely visual: it never touches a kart or
 *                 changes the road, so time trials are fair.
 *   prayer_flags  { "lines": [[ax, ay, az, bx, by, bz, sag], ...] }
 *                 Lines of little flags in five colours strung from a to b, sagging,
 *                 flapping in the wind.
 *   bells         { "list": [[x, y, z], ...] }  Monastery bells swaying; one tolls now
 *                 and then when you're near.
 *   avalanches    { "list": [[ax, ay, az, bx, by, bz, period, offset], ...] }
 *                 Snow pouring down a far slope from a to b, every `period` seconds of
 *                 the race clock (starting `offset` in): a roar and a rolling cloud of
 *                 powder. Never on the road; always on the same beat.
 *
 * Everything here is pure (no three.js); game/snowLife.ts draws it.
 */

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export interface V3 {
  x: number;
  y: number;
  z: number;
}

export interface BlizzardConfig {
  /** Unit horizontal wind direction (game x, z). */
  wind: { x: number; z: number };
  keys: (V3 & { k: number })[];
}

export function parseBlizzard(e: Record<string, unknown>): BlizzardConfig {
  const w = Array.isArray(e.wind) ? e.wind : [1, 0];
  const wx = num(w[0], 1);
  const wz = num(w[1], 0);
  const l = Math.hypot(wx, wz) || 1;
  const keys: BlizzardConfig["keys"] = [];
  if (Array.isArray(e.keys))
    for (const k of e.keys) {
      if (!Array.isArray(k) || k.length < 4) continue;
      keys.push({
        x: num(k[0], 0),
        y: num(k[1], 0),
        z: num(k[2], 0),
        k: Math.max(0, Math.min(1, num(k[3], 0.5))),
      });
    }
  return { wind: { x: wx / l, z: wz / l }, keys };
}

/** How hard it snows at a point (0..1): the two nearest keys, weighted by nearness
 * (height counts for more, so a tunnel under a ridge has its own air). */
export function snowAt(cfg: BlizzardConfig, x: number, y: number, z: number): number {
  let d1 = Infinity;
  let d2 = Infinity;
  let k1 = 0;
  let k2 = 0;
  for (const k of cfg.keys) {
    const d = (k.x - x) ** 2 + ((k.y - y) * 3) ** 2 + (k.z - z) ** 2;
    if (d < d1) {
      d2 = d1;
      k2 = k1;
      d1 = d;
      k1 = k.k;
    } else if (d < d2) {
      d2 = d;
      k2 = k.k;
    }
  }
  if (!Number.isFinite(d1)) return 0.5;
  if (!Number.isFinite(d2)) return k1;
  const a = Math.sqrt(d1);
  const b = Math.sqrt(d2);
  return (k1 * b + k2 * a) / (a + b || 1);
}

/** The storm's own rhythm: ebbing and swelling slowly, with sharper gusts (0.55..1.4). */
export function gust(t: number): number {
  const ebb = 0.82 + 0.18 * Math.sin(t * 0.21) + 0.1 * Math.sin(t * 0.53 + 1.7);
  const g = Math.max(0, Math.sin(t * 0.9 + 1.3)) ** 6;
  return Math.max(0.55, Math.min(1.4, ebb + 0.35 * g));
}

export interface FlagLine {
  a: V3;
  b: V3;
  sag: number;
}

export function parseFlags(e: Record<string, unknown>): FlagLine[] {
  const out: FlagLine[] = [];
  if (!Array.isArray(e.lines)) return out;
  for (const l of e.lines) {
    if (!Array.isArray(l) || l.length < 6) continue;
    out.push({
      a: { x: num(l[0], 0), y: num(l[1], 0), z: num(l[2], 0) },
      b: { x: num(l[3], 0), y: num(l[4], 0), z: num(l[5], 0) },
      sag: Math.max(0, num(l[6], 1.5)),
    });
  }
  return out;
}

/** A point along a sagging line, t in 0..1 (a parabola below the straight line). */
export function linePoint(f: FlagLine, t: number): V3 {
  return {
    x: f.a.x + (f.b.x - f.a.x) * t,
    y: f.a.y + (f.b.y - f.a.y) * t - 4 * f.sag * t * (1 - t),
    z: f.a.z + (f.b.z - f.a.z) * t,
  };
}

export function parsePoints(e: Record<string, unknown>): V3[] {
  const out: V3[] = [];
  if (!Array.isArray(e.list)) return out;
  for (const p of e.list)
    if (Array.isArray(p) && p.length >= 3)
      out.push({ x: num(p[0], 0), y: num(p[1], 0), z: num(p[2], 0) });
  return out;
}

export interface Avalanche {
  a: V3;
  b: V3;
  period: number;
  offset: number;
}

export function parseAvalanches(e: Record<string, unknown>): Avalanche[] {
  const out: Avalanche[] = [];
  if (!Array.isArray(e.list)) return out;
  for (const l of e.list) {
    if (!Array.isArray(l) || l.length < 6) continue;
    out.push({
      a: { x: num(l[0], 0), y: num(l[1], 0), z: num(l[2], 0) },
      b: { x: num(l[3], 0), y: num(l[4], 0), z: num(l[5], 0) },
      period: Math.max(4, num(l[6], 25)),
      offset: num(l[7], 0),
    });
  }
  return out;
}

/** An avalanche's run lasts this share of its period. */
export const AVALANCHE_RUN = 0.28;

/**
 * Where an avalanche's front is at race-clock time t: `running` while it pours down,
 * `u` how far (0 at the top .. 1 at the foot, easing in like a slide gathering speed).
 * Before the race starts (t < 0) nothing falls.
 */
export function avalancheAt(
  av: Avalanche,
  t: number,
): { running: boolean; u: number; start: boolean } {
  if (t < 0) return { running: false, u: 0, start: false };
  const ph = (((t - av.offset) % av.period) + av.period) % av.period;
  const run = av.period * AVALANCHE_RUN;
  if (ph > run) return { running: false, u: 0, start: false };
  const f = ph / run;
  return { running: true, u: f * f * (3 - 2 * f), start: ph < 0.1 };
}
