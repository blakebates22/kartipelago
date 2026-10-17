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
 * Drifting flips that around. The stick steers the travel direction directly, over a
 * range that crosses zero (into the drift curves hard, countersteer bends the path the
 * other way), and the nose is held at an angle into the drift. So drifting right and
 * countersteering left moves the kart left while the nose still points right.
 * See docs/milestones/M1-drive-a-box.md.
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
  /** Seconds of boost-pad effect left. */
  boostTime: number;
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
    if (released || s.speed < cfg.driftMinSpeed || input.brake > BRAKE_CANCELS_DRIFT) {
      s.driftDir = 0;
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
    s.grounded;
  if (canStart) {
    s.driftDir = Math.sign(input.steer);
    s.driftTime = 0;
  }
}

/** Driving over a boost pad: jump to boosted speed and hold it for a moment. */
export function applyPadBoost(s: KartState, cfg: KartConfig) {
  s.boostTime = cfg.padBoostSec;
  s.speed = Math.max(s.speed, cfg.topSpeed * cfg.padSpeedMult);
}

/** Advance one fixed step. Mutates and returns s. */
export function stepKart(s: KartState, input: InputState, cfg: KartConfig, dt: number): KartState {
  updateDrift(s, input, cfg, dt);
  const drifting = s.driftDir !== 0;
  // Drifting is the fast way round: it raises top speed, and so does a boost pad. When
  // either ends, the extra speed bleeds off at the drag rate rather than vanishing.
  const mult = Math.max(drifting ? cfg.driftSpeedMult : 1, s.boostTime > 0 ? cfg.padSpeedMult : 1);
  const cap = Math.max(0, cfg.topSpeed * mult - s.slope * cfg.slopeSpeed);
  s.boostTime = Math.max(0, s.boostTime - dt);

  // Longitudinal: throttle, brake, reverse, coast. None of it applies in the air:
  // speed (including drift and boost speed) carries through a jump untouched.
  const steer = s.grounded ? 1 : cfg.airSteer;
  if (!s.grounded) {
    // no change
  } else if (input.brake > 0 && s.speed > REVERSE_BELOW) {
    s.speed = moveToward(s.speed, 0, cfg.brake * input.brake * dt);
  } else if (input.brake > input.throttle) {
    s.speed = moveToward(s.speed, -cfg.reverseSpeed, cfg.reverseAccel * input.brake * dt);
  } else if (input.throttle > 0) {
    // Above the cap (a drift or boost just ended) bleeds back down rather than snapping.
    s.speed =
      s.speed < cap
        ? Math.min(cap, s.speed + cfg.accel * input.throttle * dt)
        : moveToward(s.speed, cap, cfg.drag * dt);
  } else {
    s.speed = moveToward(s.speed, 0, cfg.drag * dt);
  }

  if (drifting) {
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
    // Reversing flips steering, as in a real car.
    const turn = input.steer * rate * Math.sign(s.speed) * steer * dt;
    s.heading = wrapAngle(s.heading - turn);
    // In the air there's no grip; a little steering turns kart and path together.
    if (!s.grounded) s.velAngle = wrapAngle(s.velAngle - turn);
  }

  if (!drifting && s.grounded) {
    // Grip: swing the travel direction toward the nose. Exponential, so it's the same at
    // any physics rate.
    const pull = 1 - Math.exp(-cfg.grip * dt);
    s.velAngle = wrapAngle(s.velAngle + slipAngle(s) * pull);
  }

  s.x += Math.sin(s.velAngle) * s.speed * dt;
  s.z += Math.cos(s.velAngle) * s.speed * dt;
  return s;
}
