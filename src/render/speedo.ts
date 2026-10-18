/**
 * Speedometer maths (no DOM, so it can be tested).
 *
 * The readout is unitless. It is the kart's true ground speed times one fixed scale,
 * chosen so the fastest push in the game (an enhanced boost at the base top speed)
 * reads `speedoFastest` (150). The scale is the same for every racer, so a faster
 * character really does read higher.
 */

export interface SpeedoConfig {
  /** What the fastest boost reads. */
  speedoFastest: number;
  /** The last number on the dial; faster speeds peg the needle. */
  speedoDialMax: number;
}

export interface SpeedoBase {
  /** Base top speed (m/s), before character stats and bananas. */
  topSpeed: number;
  /** Enhanced boost target as a multiple of top speed. */
  zipEnhancedMult: number;
}

/** Display units per m/s. */
export const speedoScale = (cfg: SpeedoConfig, base: SpeedoBase) =>
  cfg.speedoFastest / Math.max(1e-6, base.topSpeed * base.zipEnhancedMult);

/** The number shown for a signed speed in m/s (reversing reads as positive). */
export const speedoValue = (speedMps: number, cfg: SpeedoConfig, base: SpeedoBase) =>
  Math.abs(speedMps) * speedoScale(cfg, base);

/** The dial sweeps 270°: 0 at the lower left, dial max at the lower right. */
export const DIAL_SWEEP_DEG = 270;
/** How far past the last mark the needle can push before it stops at the peg. */
export const PEG_OVERSHOOT_DEG = 6;

/** Needle angle in degrees, clockwise from straight up. */
export function needleDeg(value: number, dialMax: number) {
  const f = Math.max(0, value) / Math.max(1e-6, dialMax);
  const deg = -DIAL_SWEEP_DEG / 2 + f * DIAL_SWEEP_DEG;
  return Math.min(deg, DIAL_SWEEP_DEG / 2 + PEG_OVERSHOOT_DEG);
}

/** Lit chevrons (0..n) on the boost sign: how much of the boost is left. */
export function boostChevrons(active: boolean, timeLeft: number, total: number, n = 4) {
  if (!active || total <= 0 || timeLeft <= 0) return 0;
  return Math.max(1, Math.min(n, Math.ceil((timeLeft / total) * n)));
}
