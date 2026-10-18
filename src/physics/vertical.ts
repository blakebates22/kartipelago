/**
 * The vertical half of kart motion: following the ground, leaving it, flying, landing.
 *
 * The horizontal half (speed, steering, drifting) lives in vehicles/kart.ts and doesn't
 * change between ground and air, apart from reading `grounded`. There is no ramp or jump
 * code: the kart leaves the ground whenever the surface falls away faster than gravity
 * (plus a little stickiness) could pull it down, so crests and ramp lips launch you on
 * their own, harder the faster you hit them.
 */
import type { KartState } from "../vehicles/kart";
import type { GroundQuery } from "./ground";

/** How far below the falling kart the road can be and still count as touching, m. */
const HOVER = 0.03;

export interface VerticalConfig {
  /** Downward acceleration in the air, m/s². Arcade-strong, so jumps feel snappy. */
  gravity: number;
  /** Extra downward pull allowed while grounded before the kart takes off, m/s². */
  groundStick: number;
}

/** Rise of the surface per metre travelled in the kart's direction of travel. */
function slopeAlong(nx: number, ny: number, nz: number, velAngle: number) {
  return -(nx * Math.sin(velAngle) + nz * Math.cos(velAngle)) / ny;
}

/** Call after stepKart has moved the kart horizontally for this step. */
export function stepVertical(s: KartState, ground: GroundQuery, cfg: VerticalConfig, dt: number) {
  const surf = ground.at(s.x, s.z, s.y);
  const slope = slopeAlong(surf.nx, surf.ny, surf.nz, s.velAngle);
  // Vertical speed the kart would need to stay glued to the surface here.
  const follow = s.speed * slope;

  if (s.grounded) {
    // Where the kart would be if the ground let go this step, falling as hard as
    // gravity plus stickiness allow. If the road is no lower than that (within a few
    // centimetres), stay on it. Judging by heights, not by surface normals, avoids
    // false take-offs from the small steps in normal between road segments on banked,
    // rolling sections.
    const pulled = s.y + s.vy * dt - 0.5 * (cfg.gravity + cfg.groundStick) * dt * dt;
    if (surf.height >= pulled - HOVER) {
      s.y = surf.height;
      s.vy = follow;
      s.slope = slope;
      s.nx = surf.nx;
      s.ny = surf.ny;
      s.nz = surf.nz;
      return;
    }
    // The ground fell away faster than we can fall: take off with the speed we had.
    s.grounded = false;
  }

  s.vy -= cfg.gravity * dt;
  s.y += s.vy * dt;
  s.slope = 0;
  if (s.y <= surf.height) {
    // Landing never costs horizontal speed; only the vertical part is absorbed.
    s.y = surf.height;
    s.vy = follow;
    s.grounded = true;
    s.slope = slope;
    s.nx = surf.nx;
    s.ny = surf.ny;
    s.nz = surf.nz;
  }
}
