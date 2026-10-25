/**
 * Catch-up: a very small, bounded nudge to a rival's top speed by how far it is from
 * the player along the lap, so a race doesn't fall apart if someone gets a bad start or
 * a missile. Off inside a comfortable band (most of every race); outside it, it eases
 * in over a long distance and never goes past its caps (a couple of percent). It never
 * reacts to the player leading as such: a rival far ahead of you is eased back just as
 * a rival far behind is helped. Positive gap = the rival is ahead of the player.
 */
export interface CatchUpConfig {
  /** Off while within this many metres of the player either way. */
  catchupBand: number;
  /** Over this many metres beyond the band it eases to its cap. */
  catchupRamp: number;
  /** Top-speed caps: the most it helps a rival behind, and slows one ahead (fractions). */
  catchupMaxHelp: number;
  catchupMaxHold: number;
}

export function catchUp(gap: number, cfg: CatchUpConfig | undefined): number {
  if (!cfg || !Number.isFinite(gap)) return 1;
  const over = Math.abs(gap) - cfg.catchupBand;
  if (over <= 0) return 1;
  const t = Math.min(1, over / Math.max(1, cfg.catchupRamp));
  const ease = t * t * (3 - 2 * t);
  return gap < 0 ? 1 + cfg.catchupMaxHelp * ease : 1 - cfg.catchupMaxHold * ease;
}
