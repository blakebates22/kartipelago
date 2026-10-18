/**
 * Arcade kart handling on a flat plane.
 *
 * The kart tracks two directions separately:
 * - heading: where the nose points
 * - velAngle: where the kart is actually travelling
 *
 * Normal driving: grip swings velAngle round to match heading quickly, so the kart goes
 * where it points.
 *
 * Drifting has two models, chosen by `driftModel` so they can be compared live:
 *
 * - 0 (legacy, M1): the stick steers the travel direction directly, and the nose angle
 *   follows the stick.
 * - 1 (offset model): the stick steers the body, smoothed, as a curvature with an
 *   assisted shape (a natural inward turn hands-off, diminishing extra turn into the
 *   drift, widening on countersteer). The path is the body direction plus a drift
 *   offset that builds gradually to a fixed angle and doesn't follow the stick. On
 *   release the offset eases back to zero, so the path settles onto where the nose
 *   points. Sustained hard countersteer can spin the kart out (optional).
 *
 * See docs/milestones/M1-drive-a-box.md and docs/drift-model.md.
 *
 * Angles are radians around +Y. Forward is (sin h, cos h) on the X/Z plane, so h = 0
 * faces +Z. Positive steer is "right" from the driver's seat, which lowers heading.
 */
import type { InputState } from "../core/input";

export interface KartConfig {
  accel: number;
  brake: number;
  reverseAccel: number;
  topSpeed: number;
  reverseSpeed: number;
  drag: number;
  turnRate: number;
  turnRateAtTop: number;
  turnFullSpeed: number;
  grip: number;
  /** Travel turn rate with full steer into the drift, rad/s. */
  driftTurnTight: number;
  /** Travel turn rate with the stick centred, rad/s. */
  driftTurnNeutral: number;
  /** Travel turn rate at full countersteer, rad/s. Negative bends the path the other way. */
  driftTurnCounter: number;
  /** Nose angle into the drift with full steer in, degrees. */
  driftNoseTightDeg: number;
  /** Nose angle into the drift at full countersteer, degrees. */
  driftNoseCounterDeg: number;
  /** How fast the nose swings to its drift angle, per second. */
  driftNoseRate: number;
  driftMinSpeed: number;
  driftStartSteer: number;
  driftStartWindow: number;
  /** Top speed multiplier while drifting, e.g. 1.15 = 15% faster. */
  driftSpeedMult: number;
  /** Top speed multiplier while a boost pad's effect lasts. */
  padSpeedMult: number;
  /** How long a boost pad's effect lasts after leaving it, seconds. */
  padBoostSec: number;
  /** After a drift, how fast the leftover slide angle eases out, per second. */
  driftRecoverRate: number;
  /**
   * Share of that easing that turns your path toward the nose (0..1). The rest turns
   * the nose back toward your path. Low = smooth exit that keeps your line.
   */
  driftRecoverTurn: number;
  /** 0 = legacy drift (stick steers the path), 1 = offset model (stick steers the body). */
  driftModel: number;
  /** Offset model: smoothing time for the steering command, seconds. */
  driftSteerSmooth: number;
  /** Offset model: arc radius with the stick centred (the natural inward turn), m. */
  driftRadiusNeutral: number;
  /** Offset model: tightest arc, at full steer into the drift (the limit), m. */
  driftRadiusTight: number;
  /** Offset model: arc at full countersteer, m. Large = still slightly inward; negative = bends outward. */
  driftRadiusCounter: number;
  /** Offset model: >1 makes early steer into the drift count most, extra steer less. */
  driftInCurve: number;
  /** Offset model: >1 gives finer widening near centre, stronger at full countersteer. */
  driftCounterCurve: number;
  /** Offset model: angle between body and path the drift builds to, degrees. */
  driftOffsetDeg: number;
  /** Offset model: how fast the offset builds on entry, per second. */
  driftOffsetRate: number;
  /** Offset model: how fast the offset eases back to zero after release, per second. */
  driftOffsetReturnRate: number;
  /**
   * Offset model: share of normal steering available the instant a drift is released,
   * rising to full as the offset eases out. 1 = full steering throughout.
   */
  driftRecoverSteer: number;
  /** Throttle tapping: top speed bonus at full tap charge (0.1 = 10% faster). */
  tapBonus: number;
  /** Charge gained per well-timed tap (0..1). */
  tapGain: number;
  /** Fastest and slowest press-to-press interval that counts as a tap, seconds. */
  tapMinInterval: number;
  tapMaxInterval: number;
  /** Longest release between presses that still counts as a tap, seconds. */
  tapMaxGap: number;
  /** How fast tap charge fades once you stop tapping, per second. */
  tapDecay: number;
  /** Offset model: extra arc curvature at full brake while drifting (0.35 = 35% tighter). */
  driftBrakeTighten: number;
  /** Offset model: share of normal braking applied while drifting, so a dab doesn't kill the drift. */
  driftBrakeDecel: number;
  /** Countersteer beyond this (0..1) counts toward a spin-out. */
  spinThreshold: number;
  /** Seconds of sustained hard countersteer before a spin-out; 0 turns spin-outs off. */
  spinOutAfterSec: number;
  /** How long a spin-out lasts, seconds. */
  spinSec: number;
  /** Fraction of speed kept by a spin-out. */
  spinSpeedKeep: number;
  /** Fraction of steering available while spinning. */
  spinSteer: number;
  /** Fraction of normal steering available in the air (small: line up a landing only). */
  airSteer: number;
  /** Top speed change per unit of slope, m/s: lower uphill, higher downhill. */
  slopeSpeed: number;
}

export interface KartState {
  x: number;
  z: number;
  heading: number;
  velAngle: number;
  /** Signed speed along velAngle, m/s. Negative when reversing. */
  speed: number;
  /** 0 when not drifting, 1 drifting right, -1 drifting left. */
  driftDir: number;
  /** Seconds the current drift has lasted. */
  driftTime: number;
  /** Seconds since the drift button was pressed; Infinity while released. */
  driftPressAge: number;
  /** Seconds of boost effect left (boost pads, start boost). */
  boostTime: number;
  /** Top speed multiplier while boostTime lasts. */
  boostMult: number;
  /** Easing out of a drift: the slide angle is being smoothed away. */
  recovering: boolean;
  /** Offset model: smoothed steering command, -1..1. */
  steerSmooth: number;
  /** Offset model: path direction minus body direction, radians. */
  driftOffset: number;
  /** Seconds of sustained hard countersteer in the current drift. */
  counterTime: number;
  /** Seconds of spin-out left, and which way it spins (+1 / -1). */
  spinTime: number;
  spinDir: number;
  // Throttle tapping.
  /** 0..1: how much of the tapping bonus is built up. */
  tapCharge: number;
  /** Whether the throttle was down last step. */
  throttleOn: boolean;
  /** Seconds since the throttle was last pressed, and since it was last released. */
  sincePress: number;
  releasedFor: number;
  // Wall impacts, owned by physics/walls.ts.
  /** Yaw rate from a wall hit, rad/s; fades out. */
  yawKick: number;
  /** Seconds of crash disruption left. */
  crashTime: number;
  /** Seconds since last touching a wall. */
  wallContactAge: number;
  /** Hardest into-wall speed judged during the current contact, m/s. */
  impactPeak: number;
  /** Last judged impact, for the debug readout. */
  lastImpactSpeed: number;
  lastImpactTier: number;
  /** Steering and grip scales set by crash recovery (1 = normal). */
  controlScale: number;
  gripScale: number;
  // Vertical state, owned by physics/vertical.ts.
  y: number;
  vy: number;
  grounded: boolean;
  /** Rise per metre along the travel direction; 0 in the air. */
  slope: number;
  /** Normal of the surface last touched, for tilting the mesh. */
  nx: number;
  ny: number;
  nz: number;
}

/** Below this forward speed, holding brake reverses instead of braking. */
const REVERSE_BELOW = 0.5;
/** Slide angle (radians) below which a drift exit counts as finished. */
const RECOVERED = 0.01;
/** Brake input above this cancels a drift. */
const BRAKE_CANCELS_DRIFT = 0.5;

export function createKartState(x = 0, z = 0, heading = 0, y = 0): KartState {
  return {
    x,
    z,
    heading,
    velAngle: heading,
    speed: 0,
    driftDir: 0,
    driftTime: 0,
    driftPressAge: Infinity,
    boostTime: 0,
    boostMult: 1,
    recovering: false,
    steerSmooth: 0,
    driftOffset: 0,
    counterTime: 0,
    spinTime: 0,
    spinDir: 0,
    tapCharge: 0,
    throttleOn: false,
    sincePress: Infinity,
    releasedFor: 0,
    yawKick: 0,
    crashTime: 0,
    wallContactAge: Infinity,
    impactPeak: 0,
    lastImpactSpeed: 0,
    lastImpactTier: 0,
    controlScale: 1,
    gripScale: 1,
    y,
    vy: 0,
    grounded: true,
    slope: 0,
    nx: 0,
    ny: 1,
    nz: 0,
  };
}

export const wrapAngle = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

const moveToward = (v: number, target: number, maxDelta: number) =>
  Math.abs(target - v) <= maxDelta ? target : v + Math.sign(target - v) * maxDelta;

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const DEG = Math.PI / 180;

/** Angle between where the nose points and where the kart is going. */
export const slipAngle = (s: KartState) => wrapAngle(s.heading - s.velAngle);

function updateDrift(s: KartState, input: InputState, cfg: KartConfig, dt: number) {
  const released = !input.drift && s.driftPressAge !== Infinity;
  s.driftPressAge = input.drift
    ? s.driftPressAge === Infinity
      ? 0
      : s.driftPressAge + dt
    : Infinity;

  if (s.driftDir !== 0) {
    // In the legacy model braking cancels a drift; in the offset model it tightens it.
    const brakeCancels = cfg.driftModel < 1 && input.brake > BRAKE_CANCELS_DRIFT;
    if (released || s.speed < cfg.driftMinSpeed || brakeCancels) {
      s.driftDir = 0;
      s.recovering = true;
    }
    return;
  }

  // Start: a fresh press (within a short window, so pressing just before steering
  // still counts) plus enough steering to pick a side. The side then stays locked.
  const canStart =
    input.drift &&
    s.driftPressAge <= cfg.driftStartWindow &&
    Math.abs(input.steer) >= cfg.driftStartSteer &&
    s.speed >= cfg.driftMinSpeed &&
    s.grounded &&
    s.spinTime <= 0 &&
    s.crashTime <= 0;
  if (canStart) {
    s.driftDir = Math.sign(input.steer);
    s.driftTime = 0;
    s.recovering = false;
    s.counterTime = 0;
    // Start from whatever slide there already is, so entry is continuous.
    s.driftOffset = wrapAngle(s.velAngle - s.heading);
  }
}

/** Boost: jump to a multiple of top speed and hold that cap for a while. */
export function applyBoost(s: KartState, cfg: KartConfig, mult: number, seconds: number) {
  s.boostMult = s.boostTime > 0 ? Math.max(s.boostMult, mult) : mult;
  s.boostTime = Math.max(s.boostTime, seconds);
  s.speed = Math.max(s.speed, cfg.topSpeed * mult);
}

/**
 * Offset model: arc curvature (1/m, positive = into the drift) for a steer amount
 * `into` (-1 full countersteer .. 0 centred .. 1 full into the drift).
 *
 * Into the drift: 1 - (1 - u)^q rises fast at first and flattens toward the tight
 * limit, so the first bit of steer does most of the work and full lock can't
 * over-rotate. Countersteer: |u|^p widens gently near centre, more at full lock.
 */
export function driftCurvature(into: number, cfg: KartConfig): number {
  const kn = 1 / cfg.driftRadiusNeutral;
  const kt = 1 / cfg.driftRadiusTight;
  const kc = 1 / cfg.driftRadiusCounter;
  const u = Math.max(-1, Math.min(1, into));
  if (u >= 0) return kn + (kt - kn) * (1 - Math.pow(1 - u, cfg.driftInCurve));
  return kn - (kn - kc) * Math.pow(-u, cfg.driftCounterCurve);
}

/** The steer amount (into the drift) that gives a curvature: inverse of driftCurvature. */
export function driftSteerFor(curvature: number, cfg: KartConfig): number {
  const kn = 1 / cfg.driftRadiusNeutral;
  const kt = 1 / cfg.driftRadiusTight;
  const kc = 1 / cfg.driftRadiusCounter;
  if (curvature >= kn) {
    const r = Math.min(1, (curvature - kn) / (kt - kn));
    return 1 - Math.pow(1 - r, 1 / cfg.driftInCurve);
  }
  const r = Math.min(1, (kn - curvature) / (kn - kc));
  return -Math.pow(r, 1 / cfg.driftCounterCurve);
}

/** Driving over a boost pad. */
export function applyPadBoost(s: KartState, cfg: KartConfig) {
  applyBoost(s, cfg, cfg.padSpeedMult, cfg.padBoostSec);
}

/**
 * Throttle tapping: pressing the throttle again shortly after letting go, at a steady
 * moderate rhythm, builds a tap charge that raises top speed (it stacks with the drift
 * bonus). Mashing too fast or tapping too slowly doesn't count. Once you stop tapping
 * the charge fades, so the extra speed bleeds away gradually.
 */
export function updateTapping(s: KartState, input: InputState, cfg: KartConfig, dt: number) {
  const on = input.throttle > 0.5;
  if (on && !s.throttleOn) {
    const rhythm = s.sincePress >= cfg.tapMinInterval && s.sincePress <= cfg.tapMaxInterval;
    if (rhythm && s.releasedFor <= cfg.tapMaxGap)
      s.tapCharge = Math.min(1, s.tapCharge + cfg.tapGain);
    s.sincePress = 0;
  } else {
    s.sincePress += dt;
  }
  s.releasedFor = on ? 0 : s.releasedFor + dt;
  s.throttleOn = on;
  if (s.sincePress > cfg.tapMaxInterval) s.tapCharge = Math.max(0, s.tapCharge - cfg.tapDecay * dt);
}

/** Advance one fixed step. Mutates and returns s. */
export function stepKart(s: KartState, input: InputState, cfg: KartConfig, dt: number): KartState {
  updateDrift(s, input, cfg, dt);
  updateTapping(s, input, cfg, dt);
  const drifting = s.driftDir !== 0;
  // Drifting is the fast way round: it raises top speed, and so does a boost pad. When
  // either ends, the extra speed bleeds off at the drag rate rather than vanishing.
  const mult = Math.max(drifting ? cfg.driftSpeedMult : 1, s.boostTime > 0 ? s.boostMult : 1);
  // Tapping stacks on top of drifting and boosts.
  const tapMult = 1 + cfg.tapBonus * s.tapCharge;
  const cap = Math.max(0, cfg.topSpeed * mult * tapMult - s.slope * cfg.slopeSpeed);
  s.boostTime = Math.max(0, s.boostTime - dt);

  // Smoothed steering command (offset model): small nudges blend instead of jolting.
  s.steerSmooth +=
    (input.steer - s.steerSmooth) * (1 - Math.exp(-dt / Math.max(1e-3, cfg.driftSteerSmooth)));

  // Longitudinal: throttle, brake, reverse, coast. None of it applies in the air:
  // speed (including drift and boost speed) carries through a jump untouched.
  // Air allows only a little steering; a crash takes some away until it wears off.
  const steer = (s.grounded ? 1 : cfg.airSteer) * s.controlScale;
  if (!s.grounded) {
    // no change
  } else if (input.brake > 0 && s.speed > REVERSE_BELOW) {
    // Braking mid-drift (offset model) is gentler: it's for tightening the line.
    const share = drifting && cfg.driftModel >= 1 ? cfg.driftBrakeDecel : 1;
    s.speed = moveToward(s.speed, 0, cfg.brake * input.brake * share * dt);
  } else if (input.brake > input.throttle) {
    s.speed = moveToward(s.speed, -cfg.reverseSpeed, cfg.reverseAccel * input.brake * dt);
  } else if (input.throttle > 0) {
    // Above the cap (a drift or boost just ended) bleeds back down rather than snapping.
    s.speed =
      s.speed < cap
        ? Math.min(cap, s.speed + cfg.accel * input.throttle * dt)
        : moveToward(s.speed, cap, cfg.drag * dt);
  } else if (s.tapCharge > 0 && s.releasedFor <= cfg.tapMaxGap) {
    // The short lift between well-timed taps doesn't cost speed: momentum carries you.
  } else {
    s.speed = moveToward(s.speed, 0, cfg.drag * dt);
  }

  const offsetModel = cfg.driftModel >= 1;
  if (drifting && offsetModel) {
    // The stick steers the body, as a curvature, so a given stick position carves the
    // same arc at any speed.
    const into = s.steerSmooth * s.driftDir;
    // Braking tightens the arc on top of the stick, for extra bite when you need it.
    const tighten = 1 + cfg.driftBrakeTighten * input.brake;
    const bodyRate = -s.driftDir * Math.abs(s.speed) * driftCurvature(into, cfg) * tighten;
    s.heading = wrapAngle(s.heading + bodyRate * steer * dt);
    // The path is the body plus an offset that builds to a fixed angle, independent of
    // the stick, so steering doesn't swing the kart's visible angle around.
    const target = s.driftDir * cfg.driftOffsetDeg * DEG;
    s.driftOffset += (target - s.driftOffset) * (1 - Math.exp(-cfg.driftOffsetRate * dt));
    s.velAngle = wrapAngle(s.heading + s.driftOffset);
    s.driftTime += dt;
    // Sustained hard countersteer spins you out; easing off resets the count.
    s.counterTime = into < -cfg.spinThreshold ? s.counterTime + dt : 0;
    if (cfg.spinOutAfterSec > 0 && s.counterTime >= cfg.spinOutAfterSec) {
      s.driftDir = 0;
      s.recovering = true;
      s.counterTime = 0;
      s.spinTime = cfg.spinSec;
      s.spinDir = -Math.sign(target); // spins the way the countersteer was pulling
      s.speed *= cfg.spinSpeedKeep;
    }
  } else if (drifting) {
    // into: -1 full countersteer, 0 stick centred, 1 full steer into the drift.
    const into = input.steer * s.driftDir;
    const turn =
      into >= 0
        ? lerp(cfg.driftTurnNeutral, cfg.driftTurnTight, into)
        : lerp(cfg.driftTurnNeutral, cfg.driftTurnCounter, -into);
    // The nose is held into the drift, deeper when steering in. Easing the angle
    // relative to travel (not the absolute heading) means it settles exactly on target
    // instead of trailing behind a turning path.
    const nose = lerp(cfg.driftNoseCounterDeg, cfg.driftNoseTightDeg, (into + 1) / 2) * DEG;
    const offset = slipAngle(s);
    const swing = 1 - Math.exp(-cfg.driftNoseRate * dt);
    const nextOffset = offset + (-s.driftDir * nose - offset) * swing;
    // The stick steers where the kart goes, and the nose rides along with it.
    s.velAngle = wrapAngle(s.velAngle - s.driftDir * turn * steer * dt);
    s.heading = wrapAngle(s.velAngle + nextOffset);
    s.driftTime += dt;
  } else {
    // Sharp at low speed, steadier at top speed, and none at a standstill.
    const abs = Math.abs(s.speed);
    const atSpeed = Math.min(1, abs / cfg.topSpeed);
    const rolling = Math.min(1, abs / cfg.turnFullSpeed);
    const rate = (cfg.turnRate + (cfg.turnRateAtTop - cfg.turnRate) * atSpeed) * rolling;
    // After an offset-model drift, normal steering can optionally fade back in as the
    // offset goes (driftRecoverSteer < 1); a spin-out restricts it further.
    let authority = 1;
    if (offsetModel && s.recovering) {
      const left = Math.min(1, Math.abs(s.driftOffset) / (cfg.driftOffsetDeg * DEG));
      authority = 1 - left * (1 - cfg.driftRecoverSteer);
    }
    if (s.spinTime > 0) authority = Math.min(authority, cfg.spinSteer);
    // Reversing flips steering, as in a real car.
    const turn = input.steer * rate * Math.sign(s.speed) * steer * authority * dt;
    s.heading = wrapAngle(s.heading - turn);
    // In the air there's no grip; a little steering turns kart and path together.
    if (!s.grounded) s.velAngle = wrapAngle(s.velAngle - turn);
  }

  if (s.spinTime > 0) {
    // Spinning: the body whirls round while the kart slides on along its path.
    s.spinTime = Math.max(0, s.spinTime - dt);
    s.heading = wrapAngle(s.heading + s.spinDir * ((2 * Math.PI) / cfg.spinSec) * dt);
    s.driftOffset = wrapAngle(s.velAngle - s.heading);
  } else if (!drifting && s.grounded && offsetModel && s.recovering) {
    // Released: the offset eases back to zero, so the path settles smoothly onto where
    // the nose points. No snap, and no pendulum swing of the body.
    s.driftOffset *= Math.exp(-cfg.driftOffsetReturnRate * dt);
    s.velAngle = wrapAngle(s.heading + s.driftOffset);
    if (Math.abs(s.driftOffset) < RECOVERED) {
      s.recovering = false;
      s.driftOffset = 0;
    }
  } else if (!drifting && s.grounded) {
    if (s.recovering) {
      // Just left a drift: ease the leftover slide angle away, mostly by bringing the
      // nose round to the path, so the exit is smooth instead of a sudden snap.
      const offset = slipAngle(s);
      const ease = offset * (1 - Math.exp(-cfg.driftRecoverRate * dt));
      s.velAngle = wrapAngle(s.velAngle + ease * cfg.driftRecoverTurn);
      s.heading = wrapAngle(s.heading - ease * (1 - cfg.driftRecoverTurn));
      if (Math.abs(slipAngle(s)) < RECOVERED) s.recovering = false;
    } else {
      // Grip: swing the travel direction toward the nose. Exponential, so it's the same
      // at any physics rate.
      const pull = 1 - Math.exp(-cfg.grip * s.gripScale * dt);
      s.velAngle = wrapAngle(s.velAngle + slipAngle(s) * pull);
    }
  }

  s.x += Math.sin(s.velAngle) * s.speed * dt;
  s.z += Math.cos(s.velAngle) * s.speed * dt;
  return s;
}
