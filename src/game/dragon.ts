/**
 * The dragon of Ember Peak: a reusable fire-breathing hazard, timed by the race clock
 * so that every race (and every time trial) sees exactly the same attacks.
 *
 * From the track.json entity:
 *
 *   { "type": "dragon", "x", "y", "z", "heading",        where it perches and faces
 *     "fire": { "x", "y", "z", "heading", "length", "width", "height" },
 *                                                      the stretch of road it burns
 *     "period": 9, "offset": 0, "aim": 1.2, "warn": 1.6, "breathe": 2.0, "cool": 1.0,
 *     "scale": 1 }
 *
 * Each period runs IDLE -> AIMING (it turns its head to the road) -> WARNING (it rears
 * up, its throat glows, a roar, and the burn zone glows on the road) -> BREATHING_FIRE
 * (the zone is on fire) -> COOLDOWN, then IDLE again. Only BREATHING_FIRE hurts, and
 * only inside the zone's box, which is exactly where the flames are drawn. A kart
 * caught in it gets the same burning bounce as lava (game/hazards.ts).
 */

export type DragonPhase = "idle" | "aiming" | "warning" | "breathing" | "cooldown";

export interface DragonConfig {
  x: number;
  y: number;
  z: number;
  /** The way the dragon faces (radians, 0 = +z). */
  heading: number;
  scale: number;
  /** The burn zone: a box on the road. heading: along the road (radians, 0 = +z). */
  fire: {
    x: number;
    y: number;
    z: number;
    heading: number;
    length: number;
    width: number;
    height: number;
  };
  /** Seconds per attack, and when in the race clock the first one starts. */
  period: number;
  offset: number;
  aim: number;
  warn: number;
  breathe: number;
  cool: number;
}

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** A dragon from a track.json entity (defaults for anything missing). */
export function parseDragon(e: Record<string, unknown>): DragonConfig {
  const f = isObj(e.fire) ? e.fire : {};
  const cfg: DragonConfig = {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    scale: Math.max(0.1, num(e.scale, 1)),
    fire: {
      x: num(f.x, 0),
      y: num(f.y, 0),
      z: num(f.z, 0),
      heading: num(f.heading, 0),
      length: Math.max(1, num(f.length, 14)),
      width: Math.max(1, num(f.width, 20)),
      height: Math.max(1, num(f.height, 5)),
    },
    period: 0,
    offset: num(e.offset, 0),
    aim: Math.max(0, num(e.aim, 1.2)),
    warn: Math.max(0.5, num(e.warn, 1.6)),
    breathe: Math.max(0.2, num(e.breathe, 2.0)),
    cool: Math.max(0, num(e.cool, 1.0)),
  };
  // At least a moment of rest between attacks.
  cfg.period = Math.max(num(e.period, 9), cfg.aim + cfg.warn + cfg.breathe + cfg.cool + 0.5);
  return cfg;
}

/** Where the dragon is in its attack at race time `clock`: the phase, and how far
 * through it (0..1). Pure: the same clock always gives the same answer. */
export function dragonPhase(d: DragonConfig, clock: number): { phase: DragonPhase; t: number } {
  const u = (((clock - d.offset) % d.period) + d.period) % d.period;
  const idle = d.period - d.aim - d.warn - d.breathe - d.cool;
  const steps: [DragonPhase, number][] = [
    ["idle", idle],
    ["aiming", d.aim],
    ["warning", d.warn],
    ["breathing", d.breathe],
    ["cooldown", d.cool],
  ];
  let at = 0;
  for (const [phase, len] of steps) {
    if (u < at + len) return { phase, t: len > 0 ? (u - at) / len : 1 };
    at += len;
  }
  return { phase: "idle", t: 0 };
}

/** Is (x, y, z) inside the burn zone's box? (Whether it's burning is dragonPhase.) */
export function inFireZone(d: DragonConfig, x: number, y: number, z: number): boolean {
  const f = d.fire;
  const dx = x - f.x;
  const dz = z - f.z;
  // Along the road (+z rotated by heading) and across it.
  const along = dx * Math.sin(f.heading) + dz * Math.cos(f.heading);
  const across = dx * Math.cos(f.heading) - dz * Math.sin(f.heading);
  return (
    Math.abs(along) <= f.length / 2 &&
    Math.abs(across) <= f.width / 2 &&
    y >= f.y - 1.5 &&
    y <= f.y + f.height
  );
}

/** Does the dragon's fire burn a kart at (x, y, z) at race time `clock`? */
export function dragonBurns(
  d: DragonConfig,
  clock: number,
  x: number,
  y: number,
  z: number,
): boolean {
  return dragonPhase(d, clock).phase === "breathing" && inFireZone(d, x, y, z);
}
