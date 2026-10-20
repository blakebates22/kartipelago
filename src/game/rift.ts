/**
 * Aurora Rift's living cavern: track.json entities for the things that react to the
 * racers or keep their own time.
 *
 *   icicle    { "type": "icicle", "x", "y", "z", "top": 14, "period": 9, "offset": 0,
 *               "warn": 1.6, "r": 3.2, "decor": false }
 *             A great icicle hanging over the road at (x, z), its point at `top`. On a
 *             fixed beat of the race clock it shakes and creaks for `warn` seconds (a
 *             ring glows on the road where it will land), drops, and shatters on the
 *             road at (x, y, z). A kart within `r` of the spot at that moment is
 *             knocked (slower, a hop). It grows back while the beat comes round again.
 *             "decor": true ones hang over the abyss: they fall, but hit nothing.
 *   thin_ice  { "type": "thin_ice", "x", "y", "z", "r": 6, "hold": 7 }
 *             A cracked patch of lake ice. Each time a kart drives over it the cracks
 *             spread (three passes and it gives way); while it's broken it's slush that
 *             slows anything in it, then it freezes over again. Left alone for a while,
 *             the cracks slowly heal. Never closes the road: it only slows.
 *   shimmer   { "type": "shimmer", "x", "y", "z", "size": 1.4, "color": "#5ae8ff" }
 *             A crystal by the road that flares bright as a kart passes and slowly
 *             fades: in a row, they light up one after another as you go.
 *   sparkles  { "type": "sparkles", "rate": 36, "radius": 34 }
 *             Tiny ice crystals glinting in the air round the camera.
 *
 * The timing and state here are pure (no three.js); render/riftFx.ts draws them.
 */

export interface IcicleConfig {
  x: number;
  y: number;
  z: number;
  /** Height of its point when hanging (absolute). */
  top: number;
  period: number;
  offset: number;
  warn: number;
  /** How long the drop takes, seconds (from the height, under strong arcade gravity). */
  fall: number;
  r: number;
  decor: boolean;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** Arcade gravity for falling ice, m/s² (the karts' own). */
export const ICE_GRAVITY = 30;

export function parseIcicle(e: Record<string, unknown>): IcicleConfig {
  const y = num(e.y, 0);
  const top = Math.max(y + 2, num(e.top, y + 14));
  const fall = Math.sqrt((2 * (top - y)) / ICE_GRAVITY);
  const warn = Math.max(0, num(e.warn, 1.6));
  return {
    x: num(e.x, 0),
    y,
    z: num(e.z, 0),
    top,
    // Room for the warning, the drop and a moment of clear road every beat.
    period: Math.max(num(e.period, 9), warn + fall + 2.5),
    offset: num(e.offset, 0),
    warn,
    fall,
    r: Math.max(0.5, num(e.r, 3.2)),
    decor: e.decor === true,
  };
}

export type IciclePhase = "hanging" | "warning" | "falling" | "shattered";

/** How long the shards lie on the road after it lands, seconds. */
const SHATTERED = 1.4;

/**
 * Where an icicle is at race time `clock`. Each beat: it hangs (growing back after the
 * last one), shakes for `warn` seconds, drops for `fall` seconds, and lands at the end
 * of the beat; the shards lie there for a moment at the start of the next.
 * `u` is how far through the phase (0..1); `tip` the height of its point.
 */
export function icicleAt(
  c: IcicleConfig,
  clock: number,
): { phase: IciclePhase; u: number; tip: number } {
  const t = (((clock - c.offset) % c.period) + c.period) % c.period;
  const drop = c.period - c.fall;
  const shake = drop - c.warn;
  if (t >= drop) {
    const f = (t - drop) / c.fall;
    // Accelerating: under gravity from rest.
    return { phase: "falling", u: f, tip: c.top - (c.top - c.y) * f * f };
  }
  if (t >= shake) return { phase: "warning", u: (t - shake) / Math.max(1e-6, c.warn), tip: c.top };
  if (t < SHATTERED) return { phase: "shattered", u: t / SHATTERED, tip: c.y };
  return { phase: "hanging", u: Math.min(1, (t - SHATTERED) / 2), tip: c.top };
}

/** Did it land between race times `a` and `b` (a < b)? */
export function icicleLanded(c: IcicleConfig, a: number, b: number): boolean {
  if (b <= a) return false;
  // Landings are at offset + k·period.
  const k = Math.floor((b - c.offset) / c.period);
  const at = c.offset + k * c.period;
  return at > a && at <= b;
}

/** Is a kart at (x, y, z) caught where it lands? */
export function underIcicle(c: IcicleConfig, x: number, y: number, z: number): boolean {
  return !c.decor && Math.hypot(x - c.x, z - c.z) < c.r && Math.abs(y - c.y) < 3;
}

// ---- thin ice ------------------------------------------------------------------------

export interface ThinIce {
  x: number;
  y: number;
  z: number;
  r: number;
  /** Seconds it stays broken. */
  hold: number;
  /** Cracks so far: 0 (whole) .. 3 (gives way). */
  stage: number;
  /** Seconds of being broken left (0 = frozen). */
  broken: number;
  /** Seconds since anyone last cracked it (for healing). */
  quiet: number;
  /** Per kart: inside it last step (a pass counts once, on the way in). */
  inside: boolean[];
}

/** Passes that break it. */
export const THIN_ICE_PASSES = 3;
/** With nobody on it, a crack heals every this many seconds. */
const HEAL = 10;

export function parseThinIce(e: Record<string, unknown>, karts: number): ThinIce {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    r: Math.max(1, num(e.r, 6)),
    hold: Math.max(1, num(e.hold, 7)),
    stage: 0,
    broken: 0,
    quiet: 0,
    inside: Array.from({ length: karts }, () => false),
  };
}

export const onThinIce = (p: ThinIce, x: number, y: number, z: number) =>
  Math.hypot(x - p.x, z - p.z) < p.r && Math.abs(y - p.y) < 2;

/**
 * Advance a patch by dt with the karts where they are. Returns what happened: "crack"
 * (one more crack), "break" (it gave way), "freeze" (it froze over again).
 */
export function stepThinIce(
  p: ThinIce,
  karts: { x: number; y: number; z: number; grounded: boolean }[],
  dt: number,
): "crack" | "break" | "freeze" | undefined {
  let ev: "crack" | "break" | "freeze" | undefined;
  if (p.broken > 0) {
    p.broken = Math.max(0, p.broken - dt);
    if (p.broken === 0) {
      p.stage = 0;
      p.quiet = 0;
      ev = "freeze";
    }
  } else {
    p.quiet += dt;
    if (p.stage > 0 && p.quiet > HEAL) {
      p.stage -= 1;
      p.quiet = 0;
    }
  }
  karts.forEach((k, i) => {
    const now = k.grounded && onThinIce(p, k.x, k.y, k.z);
    if (now && !p.inside[i] && p.broken === 0) {
      p.stage += 1;
      p.quiet = 0;
      ev = "crack";
      if (p.stage >= THIN_ICE_PASSES) {
        p.stage = THIN_ICE_PASSES;
        p.broken = p.hold;
        ev = "break";
      }
    }
    p.inside[i] = now;
  });
  return ev;
}

/** The slush's drag on a kart in a broken patch: share of speed kept per second. */
export const SLUSH_KEEP = 0.45;
