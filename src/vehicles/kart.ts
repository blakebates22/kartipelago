/**
 * Arcade kart handling on a flat plane.
 *
 * The kart tracks two directions separately:
 * - heading: where the nose points
 * - velAngle: where the kart is actually travelling
 *
 * Grip is how quickly velAngle swings round to match heading. With high grip the kart
 * goes where it points (grippy arcade feel). The M1 drift lowers grip so the body slides
 * wide while the nose points into the turn; see docs/milestones/M1-drive-a-box.md.
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
}

export interface KartState {
  x: number;
  z: number;
  heading: number;
  velAngle: number;
  /** Signed speed along velAngle, m/s. Negative when reversing. */
  speed: number;
}

/** Below this forward speed, holding brake reverses instead of braking. */
const REVERSE_BELOW = 0.5;

export function createKartState(x = 0, z = 0, heading = 0): KartState {
  return { x, z, heading, velAngle: heading, speed: 0 };
}

export const wrapAngle = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

const moveToward = (v: number, target: number, maxDelta: number) =>
  Math.abs(target - v) <= maxDelta ? target : v + Math.sign(target - v) * maxDelta;

/** Angle between where the nose points and where the kart is going. */
export const slipAngle = (s: KartState) => wrapAngle(s.heading - s.velAngle);

/** Advance one fixed step. Mutates and returns s. */
export function stepKart(s: KartState, input: InputState, cfg: KartConfig, dt: number): KartState {
  // Longitudinal: throttle, brake, reverse, coast.
  if (input.brake > 0 && s.speed > REVERSE_BELOW) {
    s.speed = moveToward(s.speed, 0, cfg.brake * input.brake * dt);
  } else if (input.brake > input.throttle) {
    s.speed = moveToward(s.speed, -cfg.reverseSpeed, cfg.reverseAccel * input.brake * dt);
  } else if (input.throttle > 0) {
    // Above top speed (a boost, later) bleeds back down to it rather than snapping.
    s.speed =
      s.speed < cfg.topSpeed
        ? Math.min(cfg.topSpeed, s.speed + cfg.accel * input.throttle * dt)
        : moveToward(s.speed, cfg.topSpeed, cfg.drag * dt);
  } else {
    s.speed = moveToward(s.speed, 0, cfg.drag * dt);
  }

  // Steering: sharp at low speed, steadier at top speed, and none at a standstill
  // (karts pivot around their wheels, not on the spot).
  const abs = Math.abs(s.speed);
  const atSpeed = Math.min(1, abs / cfg.topSpeed);
  const rolling = Math.min(1, abs / cfg.turnFullSpeed);
  const rate = (cfg.turnRate + (cfg.turnRateAtTop - cfg.turnRate) * atSpeed) * rolling;
  // Reversing flips steering, as in a real car.
  s.heading = wrapAngle(s.heading - input.steer * rate * Math.sign(s.speed) * dt);

  // Grip: swing the travel direction toward the nose. Exponential so it's the same
  // at any physics rate.
  const pull = 1 - Math.exp(-cfg.grip * dt);
  s.velAngle = wrapAngle(s.velAngle + slipAngle(s) * pull);

  s.x += Math.sin(s.velAngle) * s.speed * dt;
  s.z += Math.cos(s.velAngle) * s.speed * dt;
  return s;
}
