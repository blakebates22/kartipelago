/**
 * Bananas held by a kart, and the speed they're worth.
 *
 * Two separate numbers:
 * - the count held (no upper limit, never negative), and
 * - the effective count that adds speed, capped at `bananaMaxEffective`.
 * So bananas beyond the cap are a reserve: losing a couple from 12 still leaves 10
 * effective, and the speed bonus doesn't change.
 *
 * The bonus is a multiplier, 1 + bananaStep per effective banana (1.25 at ten with the
 * default 0.025). It isn't applied to speed directly. It feeds the normal driving model
 * in two places, each with its own share of it:
 * - acceleration under throttle (bananaAccelShare), and
 * - the top speed the throttle can reach (bananaTopShare).
 * The kart then accelerates naturally toward the new top speed: collecting a banana
 * never changes the current speed, and losing one lets the extra speed bleed off at the
 * normal drag rate. Steering, grip, drifting and zipper pushes are untouched.
 */

export interface BananaConfig {
  /** Multiplier added per effective banana. */
  bananaStep: number;
  /** Bananas beyond this many still count as held, but add no more speed. */
  bananaMaxEffective: number;
  /** Share of the multiplier's extra applied to acceleration (1 = all of it). */
  bananaAccelShare: number;
  /** Share of the multiplier's extra applied to top speed. */
  bananaTopShare: number;
}

export interface BananaHolder {
  bananas: number;
}

/** How much the losing kart drops, per kind of event. */
export interface BananaLossConfig {
  lossWeapon: number;
  lossSpin: number;
  lossSquash: number;
  lossDebug: number;
}

export type BananaLossEvent = "weapon" | "spin" | "squash" | "debug";

const LOSS_KEY: Record<BananaLossEvent, keyof BananaLossConfig> = {
  weapon: "lossWeapon",
  spin: "lossSpin",
  squash: "lossSquash",
  debug: "lossDebug",
};

export function effectiveBananas(count: number, cfg: BananaConfig): number {
  return Math.max(0, Math.min(Math.floor(count), cfg.bananaMaxEffective));
}

/** The banana multiplier: 1 with none, 1 + step × effective count otherwise. */
export function bananaMult(count: number, cfg: BananaConfig): number {
  return 1 + cfg.bananaStep * effectiveBananas(count, cfg);
}

/** What the multiplier does to acceleration and to top speed. */
export function bananaScales(count: number, cfg: BananaConfig) {
  const extra = bananaMult(count, cfg) - 1;
  return { accel: 1 + extra * cfg.bananaAccelShare, top: 1 + extra * cfg.bananaTopShare };
}

export function addBananas(s: BananaHolder, n = 1): number {
  s.bananas = Math.max(0, s.bananas + Math.max(0, Math.floor(n)));
  return s.bananas;
}

/** Remove up to `n` bananas (never below zero). Returns how many were actually lost. */
export function removeBananas(s: BananaHolder, n: number): number {
  const lost = Math.max(0, Math.min(s.bananas, Math.floor(n)));
  s.bananas -= lost;
  return lost;
}

/** Remove the bananas a given event costs. Returns how many were lost (to drop). */
export function loseBananas(
  s: BananaHolder,
  event: BananaLossEvent,
  cfg: BananaLossConfig,
): number {
  return removeBananas(s, cfg[LOSS_KEY[event]]);
}
