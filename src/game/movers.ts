/**
 * Things that move across the road on a fixed beat of the race clock (Hearthglow Hollow),
 * so every race and time trial sees exactly the same ones:
 *
 *   snowball  { "type": "snowball", "ax", "ay", "az", "bx", "by", "bz", "r": 2.4,
 *               "period": 7, "offset": 0, "travel": 3.2 }
 *             A giant snowball rolls from A to B (across the road, downhill) over
 *             `travel` seconds once every period, then it's gone until the next one.
 *   sleigh    { "type": "sleigh", "ax", "ay", "az", "bx", "by", "bz",
 *               "period": 13, "offset": 0, "travel": 5, "warn": 2.5 }
 *             A sleigh pulled by two reindeer crosses from A to B over `travel` seconds
 *             once every period, its bells jingling for `warn` seconds before it sets off.
 *   bell      { "type": "bell", "x", "y", "z", "heading", "period": 16, "offset": 0,
 *               "ring": 3.2 }
 *             The bell tower's bell, swinging and ringing for `ring` seconds each period.
 *
 * Everything here is pure: where a thing is depends only on the race clock.
 */

export interface Point3 {
  x: number;
  y: number;
  z: number;
}

export interface CrossingConfig {
  a: Point3;
  b: Point3;
  period: number;
  offset: number;
  travel: number;
  /** Seconds of warning before it sets off (the sleigh's bells). */
  warn: number;
  /** The snowball's radius. */
  r: number;
}

export interface BellConfig extends Point3 {
  heading: number;
  period: number;
  offset: number;
  ring: number;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** A snowball or sleigh from a track.json entity (defaults for anything missing). */
export function parseCrossing(e: Record<string, unknown>, sleigh = false): CrossingConfig {
  const travel = Math.max(0.5, num(e.travel, sleigh ? 5 : 3.2));
  const warn = Math.max(0, num(e.warn, sleigh ? 2.5 : 0));
  return {
    a: { x: num(e.ax, 0), y: num(e.ay, 0), z: num(e.az, 0) },
    b: { x: num(e.bx, 0), y: num(e.by, 0), z: num(e.bz, 0) },
    // Always a moment with the road clear between crossings.
    period: Math.max(num(e.period, sleigh ? 13 : 7), travel + warn + 1.5),
    offset: num(e.offset, 0),
    travel,
    warn,
    r: Math.max(0.5, num(e.r, 2.4)),
  };
}

export type CrossingPhase = "idle" | "warning" | "crossing";

/**
 * Where a crossing is at race time `clock`: its phase, how far along its path (0..1,
 * only while crossing) and that point (heights interpolated from A to B; the caller
 * puts it on the ground). Each period: idle, then `warn` seconds of warning, then the
 * crossing itself, which ends the period.
 */
export function crossingAt(
  c: CrossingConfig,
  clock: number,
): { phase: CrossingPhase; u: number; x: number; y: number; z: number; heading: number } {
  const t = (((clock - c.offset) % c.period) + c.period) % c.period;
  const start = c.period - c.travel;
  const heading = Math.atan2(c.b.x - c.a.x, c.b.z - c.a.z);
  if (t >= start) {
    const u = (t - start) / c.travel;
    return {
      phase: "crossing",
      u,
      x: c.a.x + (c.b.x - c.a.x) * u,
      y: c.a.y + (c.b.y - c.a.y) * u,
      z: c.a.z + (c.b.z - c.a.z) * u,
      heading,
    };
  }
  return {
    phase: t >= start - c.warn ? "warning" : "idle",
    u: 0,
    x: c.a.x,
    y: c.a.y,
    z: c.a.z,
    heading,
  };
}

/** How far a crossing's path runs, metres (horizontal). */
export const crossingLength = (c: CrossingConfig) => Math.hypot(c.b.x - c.a.x, c.b.z - c.a.z);

/** The bell tower's bell from a track.json entity. */
export function parseBell(e: Record<string, unknown>): BellConfig {
  const ring = Math.max(0.5, num(e.ring, 3.2));
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    period: Math.max(num(e.period, 16), ring + 1),
    offset: num(e.offset, 0),
    ring,
  };
}

/** The bell's swing angle at race time `clock` (radians; 0 at rest), and whether it's
 * ringing. A swing a second, dying away over the ring. */
export function bellSwing(
  b: BellConfig,
  clock: number,
): { ringing: boolean; angle: number; t: number } {
  const t = (((clock - b.offset) % b.period) + b.period) % b.period;
  if (t >= b.ring) return { ringing: false, angle: 0, t: 0 };
  const fade = 1 - t / b.ring;
  return { ringing: true, angle: 0.6 * Math.sin(t * Math.PI * 2 * 0.9) * fade, t: t / b.ring };
}
