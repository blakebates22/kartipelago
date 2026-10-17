import * as THREE from "three";
import { wrapAngle } from "../vehicles/kart";

export interface ChaseConfig {
  distance: number;
  height: number;
  lookHeight: number;
  /** How far ahead to aim at top speed, metres. */
  lookAhead: number;
  /** 0 = sit behind the nose, 1 = sit behind the travel direction. */
  followTravel: number;
  /** How fast the camera swings round behind the kart, per second. */
  yawFollow: number;
  /** How fast position catches up, per second. Lower = more sense of speed. */
  posFollow: number;
}

export interface ChaseTarget {
  x: number;
  /** Height of the kart's base. */
  y: number;
  z: number;
  heading: number;
  velAngle: number;
  /** 0..1+ of top speed, for look-ahead. */
  speedFrac: number;
}

/** Frame-rate independent smoothing factor for an exponential follow. */
export const follow = (rate: number, dt: number) => 1 - Math.exp(-rate * dt);

/** Move an angle toward a target the short way round. */
export const dampAngle = (current: number, target: number, rate: number, dt: number) =>
  wrapAngle(current + wrapAngle(target - current) * follow(rate, dt));

/**
 * Third-person camera. Purely visual, so it runs per render frame, not on the fixed step.
 *
 * Sitting partly behind the travel direction (not just the nose) keeps a drift readable:
 * the kart visibly angles into the turn instead of the whole world swinging round.
 */
export function createChaseCamera(camera: THREE.PerspectiveCamera) {
  let yaw = 0;
  let ready = false;
  const pos = new THREE.Vector3();
  const look = new THREE.Vector3();
  const want = new THREE.Vector3();

  return {
    update(t: ChaseTarget, cfg: ChaseConfig, dt: number) {
      const travelYaw = t.heading + wrapAngle(t.velAngle - t.heading) * cfg.followTravel;
      yaw = ready ? dampAngle(yaw, travelYaw, cfg.yawFollow, dt) : travelYaw;

      want.set(
        t.x - Math.sin(yaw) * cfg.distance,
        t.y + cfg.height,
        t.z - Math.cos(yaw) * cfg.distance,
      );
      if (ready) pos.lerp(want, follow(cfg.posFollow, dt));
      else pos.copy(want);

      const ahead = cfg.lookAhead * Math.max(0, t.speedFrac);
      want.set(
        t.x + Math.sin(t.velAngle) * ahead,
        t.y + cfg.lookHeight,
        t.z + Math.cos(t.velAngle) * ahead,
      );
      if (ready) look.lerp(want, follow(cfg.posFollow, dt));
      else look.copy(want);

      ready = true;
      camera.position.copy(pos);
      camera.lookAt(look);
    },
  };
}
