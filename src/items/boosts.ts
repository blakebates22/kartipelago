/**
 * Blue balloon boosts.
 *
 * All three levels use the same boost as a zipper pad (vehicles/zipper.ts): the same
 * acceleration toward the same target speeds, the same released-throttle enhanced
 * flag, early-press cost, rainbow window and recovery. The only mechanical difference
 * between levels is the boost timer: blue1Sec / blue2Sec / blue3Sec (0.58 / 0.92 /
 * 1.25 s by default, from the original's timer values at 30 updates a second).
 *
 * The timer starts the moment the balloon fires. Level 3's charging sound and delayed
 * boost sound are presentation only (blue3ChargeSec); they never delay the physics.
 */
import { BOOST_SOURCE, startBoost, type ZipperConfig, type ZipperState } from "../vehicles/zipper";
import type { ItemsConfig } from "./config";

export function blueSeconds(level: number, cfg: ItemsConfig): number {
  return [0, cfg.blue1Sec, cfg.blue2Sec, cfg.blue3Sec][level] ?? cfg.blue1Sec;
}

/** Fire a blue balloon of this level, with the throttle as it is right now. */
export function activateBlue(
  s: ZipperState,
  level: number,
  throttle: number,
  kartCfg: ZipperConfig,
  cfg: ItemsConfig,
): boolean {
  const sec = blueSeconds(level, cfg);
  const source = [BOOST_SOURCE.BLUE1, BOOST_SOURCE.BLUE2, BOOST_SOURCE.BLUE3][level - 1];
  return startBoost(
    s,
    throttle,
    kartCfg,
    source ?? BOOST_SOURCE.BLUE1,
    sec,
    sec * cfg.blueEnhancedScale,
  );
}
