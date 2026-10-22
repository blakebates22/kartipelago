/**
 * Zipper boosts for the car: an original take on a timing challenge.
 *
 * Phases:
 * - NORMAL: no boost.
 * - ACTIVATION happens in startZipper, on the step a kart enters a zipper pad. If the
 *   throttle is released at that moment the boost is ENHANCED; if held, ORDINARY.
 *   Releasing afterwards doesn't upgrade it.
 * - ACTIVE: the zipper drives the kart toward a boosted target speed, with or without
 *   throttle. During an enhanced boost, pressing the throttle early cuts the rest of the
 *   enhanced benefit, more the earlier you press.
 * - ENDING (enhanced only): the last moments of the boost. The exhaust turns rainbow:
 *   this is the moment to press the throttle again.
 * - RECOVERY: the push is over and the extra speed decays back toward normal. Pressing
 *   in the rainbow window gives the slow, "carry" decay; anything else decays faster,
 *   and coasting above top speed with no throttle decays faster still.
 *
 * Steering and drifting stay fully available; hard turning at boosted speed costs speed
 * through the kart's general turn scrub, and bleeds an enhanced boost's power.
 *
 * The same boost state serves every boost source: zipper pads and blue balloons (see
 * items/boosts.ts). They share one acceleration model and differ only in how long they
 * push (and how they look). One boost at a time: starting a new one replaces the active
 * timer (or, with boostOverlap = 1, keeps whichever has longer left).
 */
export const ZIP = { NORMAL: 0, ACTIVE: 1, ENDING: 2, RECOVERY: 3 } as const;

/** Where the active boost came from: a zipper pad, a blue balloon of level 1-3, or a
 * start boost (race.ts). */
export const BOOST_SOURCE = { ZIPPER: 0, BLUE1: 1, BLUE2: 2, BLUE3: 3, START: 4 } as const;

export interface ZipperConfig {
  /** Ordinary boost: target speed as a multiple of top speed, and duration (s). */
  zipOrdinaryMult: number;
  zipOrdinarySec: number;
  /** Enhanced boost: target speed multiple and duration (s). */
  zipEnhancedMult: number;
  zipEnhancedSec: number;
  /** How hard the zipper accelerates the kart toward its target, m/s². */
  zipAccel: number;
  /** Share of the remaining enhanced benefit lost by pressing throttle at the very start. */
  zipEarlyPenalty: number;
  /** Length of the rainbow window at the end of an enhanced boost, s. */
  zipRainbowSec: number;
  /** The rainbow window never takes more than this share of a (short) boost. */
  zipRainbowMaxShare: number;
  /** Starting a boost while one is active: 0 = replace its timer, 1 = keep the longer. */
  boostOverlap: number;
  /** Recovery time constant after a well-timed press in the rainbow window, s. */
  zipCarrySec: number;
  /** Recovery time constant otherwise, s. */
  zipRecoverSec: number;
  /** Deceleration above top speed with no throttle after a boost, m/s². */
  zipCoastDrag: number;
  /** Share of a boost's extra speed kept after a severe crash. */
  zipCrashKeep: number;
  /** Lost enhanced power per second per m/s² of excess sideways force while boosting. */
  zipTurnBleed: number;
}

export interface ZipperState {
  zipPhase: number;
  zipEnhanced: boolean;
  /** Seconds of push left (ACTIVE/ENDING), or seconds into RECOVERY. */
  zipTime: number;
  /** 0..1 how much of the enhanced extra is still available. */
  zipPower: number;
  zipPressedEarly: boolean;
  zipPressedInRainbow: boolean;
  zipReleasedAtStart: boolean;
  /** Speed when recovery began, and its decay time constant. */
  zipExitSpeed: number;
  zipTau: number;
  /** Whether the kart was on a zipper pad last step (pads fire on entry only). */
  zipOnPad: boolean;
  /** Set by a severe wall crash; handled on the kart's next step. */
  zipCrashed: boolean;
  /** Which kind of boost this is (BOOST_SOURCE), and how long it pushes in total, s. */
  zipSource: number;
  zipTotal: number;
}

export function zipperState(): ZipperState {
  return {
    zipPhase: ZIP.NORMAL,
    zipEnhanced: false,
    zipTime: 0,
    zipPower: 1,
    zipPressedEarly: false,
    zipPressedInRainbow: false,
    zipReleasedAtStart: false,
    zipExitSpeed: 0,
    zipTau: 1,
    zipOnPad: false,
    zipCrashed: false,
    zipSource: BOOST_SOURCE.ZIPPER,
    zipTotal: 0,
  };
}

/** Activation: called on the step a kart enters a zipper pad. */
export function startZipper(s: ZipperState, throttle: number, cfg: ZipperConfig) {
  return startBoost(s, throttle, cfg, BOOST_SOURCE.ZIPPER, cfg.zipOrdinarySec, cfg.zipEnhancedSec);
}

/**
 * Start a boost of any source. Throttle released at this moment = enhanced. Returns
 * false if an active boost was kept instead (boostOverlap = 1 and it has longer left).
 * The kart's speed is never changed here: the boost accelerates it from where it is.
 */
export function startBoost(
  s: ZipperState,
  throttle: number,
  cfg: ZipperConfig,
  source: number,
  ordinarySec: number,
  enhancedSec: number,
): boolean {
  const released = throttle <= 0.5;
  const seconds = released ? enhancedSec : ordinarySec;
  const active = s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING;
  if (active && cfg.boostOverlap >= 1 && s.zipTime >= seconds) return false;
  s.zipPhase = ZIP.ACTIVE;
  s.zipEnhanced = released;
  s.zipReleasedAtStart = released;
  s.zipTime = seconds;
  s.zipTotal = seconds;
  s.zipSource = source;
  s.zipPower = 1;
  s.zipPressedEarly = false;
  s.zipPressedInRainbow = false;
  return true;
}

/** Length of the rainbow window for the active boost, s. */
export function rainbowWindow(s: ZipperState, cfg: ZipperConfig): number {
  return Math.min(cfg.zipRainbowSec, s.zipTotal * cfg.zipRainbowMaxShare);
}

/** The speed the zipper is pushing toward right now. */
export function zipperTarget(s: ZipperState, topSpeed: number, cfg: ZipperConfig): number {
  if (!s.zipEnhanced) return topSpeed * cfg.zipOrdinaryMult;
  const extra = (cfg.zipEnhancedMult - cfg.zipOrdinaryMult) * s.zipPower;
  return topSpeed * (cfg.zipOrdinaryMult + extra);
}

/**
 * Advance the zipper phases by one step. Returns the speed to push toward this step
 * (ACTIVE / ENDING), or undefined when the zipper isn't pushing.
 */
export function stepZipper(
  s: ZipperState & { speed: number },
  throttle: number,
  topSpeed: number,
  cfg: ZipperConfig,
  dt: number,
  /** Normal top speed to settle back to afterwards (top speed with bananas). */
  normalTop = topSpeed,
): number | undefined {
  const pressed = throttle > 0.5;
  if (s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING) {
    if (s.zipEnhanced && s.zipPhase === ZIP.ENDING && pressed) s.zipPressedInRainbow = true;
    if (s.zipEnhanced && s.zipPhase === ZIP.ACTIVE && pressed && !s.zipPressedEarly) {
      // Pressed before the rainbow: lose part of the remaining enhanced benefit, more
      // the earlier it was.
      s.zipPressedEarly = true;
      const left = Math.min(1, s.zipTime / Math.max(1e-6, s.zipTotal));
      s.zipPower *= 1 - cfg.zipEarlyPenalty * left;
    }
    s.zipTime -= dt;
    if (s.zipEnhanced && s.zipTime <= rainbowWindow(s, cfg)) s.zipPhase = ZIP.ENDING;
    if (s.zipTime <= 0) {
      s.zipPhase = ZIP.RECOVERY;
      s.zipExitSpeed = s.speed;
      s.zipTau = s.zipPressedInRainbow && !s.zipPressedEarly ? cfg.zipCarrySec : cfg.zipRecoverSec;
      s.zipTime = 0;
      return undefined;
    }
    return zipperTarget(s, topSpeed, cfg);
  }
  if (s.zipPhase === ZIP.RECOVERY) {
    s.zipTime += dt;
    if (s.speed <= normalTop + 0.05 || zipperRecoveryCap(s, normalTop) <= normalTop + 0.05) {
      s.zipPhase = ZIP.NORMAL;
    }
  }
  return undefined;
}

/** During recovery: the top speed allowed while holding the throttle (decays to normal). */
export function zipperRecoveryCap(s: ZipperState, topSpeed: number): number {
  if (s.zipPhase !== ZIP.RECOVERY) return 0;
  const extra = Math.max(0, s.zipExitSpeed - topSpeed);
  return topSpeed + extra * Math.exp(-s.zipTime / Math.max(1e-3, s.zipTau));
}

/** A severe crash: end the push and keep only part of the extra speed. */
export function crashZipper(
  s: ZipperState & { speed: number },
  topSpeed: number,
  cfg: ZipperConfig,
) {
  if (s.zipPhase === ZIP.NORMAL) return;
  s.zipPhase = ZIP.RECOVERY;
  s.zipTime = 0;
  s.zipTau = cfg.zipRecoverSec;
  s.zipExitSpeed = topSpeed + Math.max(0, s.speed - topSpeed) * cfg.zipCrashKeep;
}
