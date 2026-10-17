/**
 * Walls along both road edges. When the kart pokes past one, push it back inside and
 * take away the part of its velocity going into the wall. A glancing hit keeps almost
 * all its speed and slides along; a head-on hit loses nearly all of it. Karts high
 * enough in the air clear the wall entirely.
 */
import type { KartState } from "../vehicles/kart";
import type { GroundQuery } from "./ground";

export interface WallConfig {
  /** Half the kart's width, metres: how close its centre can get to a wall. */
  kartRadius: number;
  /** Wall height above the road edge, metres. */
  wallHeight: number;
  /** How fast a wall turns the nose to run along it, per second. Stops karts sticking. */
  wallAlign: number;
}

/** Further outside the edge than this, the kart is off the track and walls ignore it. */
const OUTSIDE = 4;

/** Call after stepKart moves the kart. Returns true if it hit a wall this step. */
export function stepWalls(s: KartState, ground: GroundQuery, cfg: WallConfig, dt: number): boolean {
  const road = ground.at(s.x, s.z).road;
  if (!road) return false;
  const limit = road.halfWidth - cfg.kartRadius;
  const out = Math.abs(road.across) - limit;
  if (out <= 0 || out > cfg.kartRadius + OUTSIDE) return false;

  const side = Math.sign(road.across); // +1 right wall, -1 left wall
  const edgeY = road.centreY + side * road.halfWidth * road.rise;
  if (s.y > edgeY + cfg.wallHeight) return false; // flying over it

  // Back inside.
  s.x -= road.rx * side * out;
  s.z -= road.rz * side * out;

  // Remove velocity into the wall; keep the rest.
  let vx = Math.sin(s.velAngle) * s.speed;
  let vz = Math.cos(s.velAngle) * s.speed;
  const into = (vx * road.rx + vz * road.rz) * side;
  if (into > 0) {
    vx -= road.rx * side * into;
    vz -= road.rz * side * into;
    const along = Math.hypot(vx, vz);
    if (along > 1e-6) {
      // Keep the sign convention: speed is negative when reversing.
      const fwd = s.speed >= 0 ? 1 : -1;
      s.velAngle = Math.atan2(vx * fwd, vz * fwd);
      s.speed = along * fwd;
    } else {
      s.speed = 0;
    }
  }

  // If the nose points into the wall, swing it toward running along the wall, so
  // holding throttle scrapes you off it rather than pinning you there.
  const nx = Math.sin(s.heading);
  const nz = Math.cos(s.heading);
  if ((nx * road.rx + nz * road.rz) * side > 0) {
    const ax = nx - road.rx * side * (nx * road.rx + nz * road.rz) * side;
    const az = nz - road.rz * side * (nx * road.rx + nz * road.rz) * side;
    const alongHeading = Math.atan2(ax, az);
    const diff = Math.atan2(Math.sin(alongHeading - s.heading), Math.cos(alongHeading - s.heading));
    s.heading += diff * (1 - Math.exp(-cfg.wallAlign * dt));
  }
  return true;
}
