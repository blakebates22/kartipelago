/**
 * Desert World's living parts, from track.json entities. All purely visual: nothing
 * here changes how a kart drives.
 *
 *   dust      { "type": "dust", "color": "#d89a6a", "rate": 1 }
 *             Dust kicked up behind karts driving on dirt and sand: a reddish puff
 *             trail that grows with speed, and a bigger cloud off-road.
 *   dustwind  { "type": "dustwind", "rate": 10, "radius": 60, "color": "#e0a878" }
 *             Wisps of dust blowing across the land round the camera on the wind.
 *   windmill  { "type": "windmill", "x", "y", "z", "heading": 0, "radius": 3.2,
 *             "speed": 1.4 }: a ranch windmill's wheel (the tower is scenery), its hub
 *             at (x, y, z), facing `heading`, turning `speed` radians a second.
 *   birds     { "type": "birds", "x", "y", "z", "radius": 70, "count": 3,
 *             "speed": 0.2, "seed": 1, "color": "#2a201c" }: a few big birds circling
 *             high over the canyon on the thermals, wings beating now and then (white
 *             ones make gulls over water).
 *
 * The timing is pure (no three.js) here; render/desertFx.ts draws them.
 */

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** Surfaces that throw up dust, and how much (share of the full trail). */
export const DUSTY: Record<string, number> = {
  packed_dirt: 0.55,
  dirt: 0.8,
  loose_sand: 1,
  sand: 1,
};

export interface DustConfig {
  color: string;
  rate: number;
}

export function parseDust(e: Record<string, unknown>): DustConfig {
  return {
    color: typeof e.color === "string" ? e.color : "#d89a6a",
    rate: Math.max(0, Math.min(3, num(e.rate, 1))),
  };
}

/**
 * Puffs per second behind a kart on `surface` at `speed` (m/s): none when slow or on a
 * clean surface, rising with speed.
 */
export function dustRate(cfg: DustConfig, surface: string | undefined, speed: number): number {
  const k = surface ? (DUSTY[surface] ?? 0) : 0;
  const v = Math.abs(speed);
  if (!k || v < 6) return 0;
  return cfg.rate * k * Math.min(1, (v - 6) / 16) * 26;
}

export interface WindConfig {
  rate: number;
  radius: number;
  color: string;
}

export function parseWind(e: Record<string, unknown>): WindConfig {
  return {
    rate: Math.max(0, num(e.rate, 10)),
    radius: Math.max(10, num(e.radius, 60)),
    color: typeof e.color === "string" ? e.color : "#e0a878",
  };
}

/** The desert wind (game x, z): a steady breeze that gusts and veers slowly. */
export function windAt(t: number): { x: number; z: number } {
  const a = 0.6 + 0.35 * Math.sin(t * 0.05);
  const s = 5 + 2.5 * Math.sin(t * 0.21) + 1.5 * Math.sin(t * 0.73);
  return { x: Math.cos(a) * s, z: Math.sin(a) * s };
}

export interface WindmillConfig {
  x: number;
  y: number;
  z: number;
  heading: number;
  radius: number;
  speed: number;
}

export function parseWindmill(e: Record<string, unknown>): WindmillConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    radius: Math.max(0.5, num(e.radius, 3.2)),
    speed: num(e.speed, 1.4),
  };
}

/** The wheel's angle at time t: it follows the gusts. */
export function windmillAngle(c: WindmillConfig, t: number): number {
  return c.speed * t + 0.6 * Math.sin(t * 0.21);
}

export interface BirdsConfig {
  /** Body colour (dark soaring birds by default; white for gulls over water). */
  color: string;
  x: number;
  y: number;
  z: number;
  radius: number;
  count: number;
  speed: number;
  seed: number;
}

export function parseBirds(e: Record<string, unknown>): BirdsConfig {
  return {
    color: typeof e.color === "string" ? e.color : "#2a201c",
    x: num(e.x, 0),
    y: num(e.y, 80),
    z: num(e.z, 0),
    radius: Math.max(10, num(e.radius, 70)),
    count: Math.max(1, Math.min(8, Math.round(num(e.count, 3)))),
    speed: num(e.speed, 0.2),
    seed: num(e.seed, 1),
  };
}

/**
 * Bird k of a flock at time t: where it is, which way it's heading (radians, the
 * game's convention: 0 = +Z), its bank, and its wing beat (-1..1; gliding = 0).
 */
export function birdAt(c: BirdsConfig, k: number, t: number) {
  const ph = c.seed * 2.3 + (k * Math.PI * 2) / c.count;
  // Each circles its own loop, a little off the flock's centre, rising and sinking.
  const r = c.radius * (0.7 + 0.3 * Math.sin(ph * 1.7));
  const a = ph + c.speed * t * (1 + 0.15 * Math.sin(k + c.seed));
  const cx = c.x + 0.25 * c.radius * Math.cos(ph * 0.9 + t * 0.03);
  const cz = c.z + 0.25 * c.radius * Math.sin(ph * 1.3 + t * 0.03);
  const x = cx + Math.cos(a) * r;
  const z = cz + Math.sin(a) * r;
  const y = c.y + 6 * Math.sin(t * 0.17 + ph) + 3 * Math.sin(t * 0.5 + k);
  // Moving round anticlockwise (seen from above): tangent (-sin a, cos a).
  const heading = Math.atan2(-Math.sin(a), Math.cos(a));
  // Flap in bursts, then glide.
  const burst = Math.sin(t * 0.4 + ph * 3) > 0.55;
  const beat = burst ? Math.sin(t * 9 + ph) : 0;
  return { x, y, z, heading, bank: -0.35, beat };
}
