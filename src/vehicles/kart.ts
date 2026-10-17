/**
 * Arcade kart handling on a flat plane.
 *
 * The kart tracks two directions separately:
 * - heading: where the nose points
 * - velAngle: where the kart is actually travelling
 *
 * Grip is how quickly velAngle swings round to match heading. Normal driving has high
 * grip, so the kart goes where it points. Drifting drops to low grip, so the body slides
 * wide while the nose points into the turn. See docs/milestones/M1-drive-a-box.md.
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
  driftGrip: number;
  driftTurnTight: number;
  driftTurnLoose: number;
  driftMinSpeed: number;
  driftStartSteer: number;
  driftStartWindow: number;
  /** Top speed multiplier while drifting, e.g. 1.15 = 15% faster. */
  driftSpeedMult: number;
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
}

/** Below this forward speed, holding brake reverses instead of braking. */
const REVERSE_BELOW = 0.5;
/** Brake input above this cancels a drift. */
const BRAKE_CANCELS_DRIFT = 0.5;

export function createKartState(x = 0, z = 0, heading = 0): KartState {
  return {
    x,
    z,
    heading,
    velAngle: heading,
    speed: 0,
    driftDir: 0,
    driftTime: 0,
    driftPressAge: Infinity,
  };
}

export const wrapAngle = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

const moveToward = (v: number, target: number, maxDelta: number) =>
  Math.abs(target - v) <= maxDelta ? target : v + Math.sign(target - v) * maxDelta;

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
    s.speed >= cfg.driftMinSpeed;
  if (canStart) {
    s.driftDir = Math.sign(input.steer);
    s.driftTime = 0;
  }
}

/** Advance one fixed step. Mutates and returns s. */
export function stepKart(s: KartState, input: InputState, cfg: KartConfig, dt: number): KartState {
  updateDrift(s, input, cfg, dt);
  const drifting = s.driftDir !== 0;
  // Drifting is the fast way round: it raises top speed. After the drift, the extra
  // speed bleeds off at the drag rate rather than vanishing.
  const cap = drifting ? cfg.topSpeed * cfg.driftSpeedMult : cfg.topSpeed;

  // Longitudinal: throttle, brake, reverse, coast.
  if (input.brake > 0 && s.speed > REVERSE_BELOW) {
    s.speed = moveToward(s.speed, 0, cfg.brake * input.brake * dt);
  } else if (input.brake > input.throttle) {
    s.speed = moveToward(s.speed, -cfg.reverseSpeed, cfg.reverseAccel * input.brake * dt);
  } else if (input.throttle > 0) {
    // Above the cap (just left a drift) bleeds back down rather than snapping.
    s.speed =
      s.speed < cap
        ? Math.min(cap, s.speed + cfg.accel * input.throttle * dt)
        : moveToward(s.speed, cap, cfg.drag * dt);
  } else {
    s.speed = moveToward(s.speed, 0, cfg.drag * dt);
  }

  if (drifting) {
    // The stick no longer steers left/right. It picks the arc: into the drift is
    // tight, countersteer is loose, but the kart always keeps turning the locked way.
    const into = input.steer * s.driftDir; // -1 full countersteer .. 1 full into the drift
    const t = (into + 1) / 2;
    const rate = cfg.driftTurnLoose + (cfg.driftTurnTight - cfg.driftTurnLoose) * t;
    s.heading = wrapAngle(s.heading - s.driftDir * rate * dt);
    s.driftTime += dt;
  } else {
    // Sharp at low speed, steadier at top speed, and none at a standstill.
    const abs = Math.abs(s.speed);
    const atSpeed = Math.min(1, abs / cfg.topSpeed);
    const rolling = Math.min(1, abs / cfg.turnFullSpeed);
    const rate = (cfg.turnRate + (cfg.turnRateAtTop - cfg.turnRate) * atSpeed) * rolling;
    // Reversing flips steering, as in a real car.
    s.heading = wrapAngle(s.heading - input.steer * rate * Math.sign(s.speed) * dt);
  }

  // Grip: swing the travel direction toward the nose. Low grip while drifting is what
  // makes the kart slide wide of where it points. Exponential, so it's the same at any
  // physics rate.
  const pull = 1 - Math.exp(-(drifting ? cfg.driftGrip : cfg.grip) * dt);
  s.velAngle = wrapAngle(s.velAngle + slipAngle(s) * pull);

  s.x += Math.sin(s.velAngle) * s.speed * dt;
  s.z += Math.cos(s.velAngle) * s.speed * dt;
  return s;
}
