/**
 * Walls along both road edges, and what hitting them does to the kart.
 *
 * Contact: when the kart pokes past a wall it is pushed back inside and the part of its
 * velocity going into the wall is removed. A glancing hit keeps almost all its speed and
 * slides along; a head-on hit loses nearly all of it. Karts high enough in the air
 * clear the wall entirely.
 *
 * Impacts: how hard a hit is depends on the speed going into the wall when contact
 * starts. It's judged once per contact (a clearly harder hit during the same contact
 * counts again), so scraping along a wall can't keep cancelling a drift.
 *
 * - Light (below `scrapeSpeed`): no rotation. A drift carries on along the wall.
 * - Moderate: a yaw kick turns the nose away from the wall and fades out. The drift
 *   survives unless the total rotation the kick will cause passes `driftBreakDeg`.
 * - Severe (above `crashSpeed`, or a kick big enough to break the drift): the drift is
 *   cancelled, the kick is damped, any zipper boost ends, and steering and grip drop,
 *   then return smoothly over `crashSec`.
 */
import type { KartState } from "../vehicles/kart";
import type { GroundQuery } from "./ground";
import type { Solid } from "../world/solids";
import { deepestWall, type CollisionMesh } from "../world/collisionMesh";

export interface WallConfig {
  /** Half the kart's width, metres: how close its centre can get to a wall. */
  kartRadius: number;
  /** Wall height above the road edge, metres. */
  wallHeight: number;
  /** How fast a wall turns a pinned nose to run along it, per second. Stops karts sticking. */
  wallAlign: number;
  /** Fastest that alignment may turn the kart, rad/s, so it's a swing and never a snap. */
  wallAlignMaxRate: number;
}

export interface ImpactConfig {
  /** Into-wall speed below which a hit is a light scrape, m/s. */
  scrapeSpeed: number;
  /** Into-wall speed at or above which a hit is a crash, m/s. */
  crashSpeed: number;
  /** Yaw kick per m/s of into-wall speed above scrapeSpeed, rad/s. */
  kickPerSpeed: number;
  /** Largest yaw kick, rad/s. */
  kickMax: number;
  /** How fast a yaw kick fades, per second. Total rotation ≈ kick / kickDamp. */
  kickDamp: number;
  /** A drift survives a hit whose kick would rotate the kart less than this, degrees. */
  driftBreakDeg: number;
  /** Time away from a wall before touching it again counts as a new contact, s. */
  contactReset: number;
  /** How long control is disrupted after a crash, s. */
  crashSec: number;
  /** Share of steering right after a crash, rising back to full. */
  crashSteer: number;
  /** Share of grip right after a crash, rising back to full. */
  crashGrip: number;
  /** Share of the yaw kick kept by a crash (the rest is absorbed). */
  crashSpinKeep: number;
}

export type ImpactTier = 0 | 1 | 2 | 3; // none, light, moderate, severe

export interface WallHit {
  /** Speed going into the wall this step, m/s. */
  into: number;
  /** The tier if this step was judged as an impact; 0 while just scraping along. */
  tier: ImpactTier;
}

/** Further outside the edge than this, the kart is off the track and walls ignore it. */
const OUTSIDE = 4;
/** During one contact, a hit must be this much harder (m/s) to be judged again. */
const HARDER = 1.5;
const DEG = Math.PI / 180;

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
const smoothstep = (t: number) => t * t * (3 - 2 * t);

/**
 * Advance yaw kicks and crash recovery. Call once per step, before stepKart. It turns
 * the body by any yaw kick and sets the steering and grip scales stepKart applies.
 */
export function stepImpacts(s: KartState, cfg: ImpactConfig, dt: number) {
  if (s.yawKick !== 0) {
    s.heading = wrap(s.heading + s.yawKick * dt);
    s.yawKick *= Math.exp(-cfg.kickDamp * dt);
    if (Math.abs(s.yawKick) < 0.01) s.yawKick = 0;
  }
  s.wallContactAge += dt;
  if (s.crashTime > 0) {
    s.crashTime = Math.max(0, s.crashTime - dt);
    const back = smoothstep(1 - s.crashTime / Math.max(1e-6, cfg.crashSec));
    s.controlScale = cfg.crashSteer + (1 - cfg.crashSteer) * back;
    s.gripScale = cfg.crashGrip + (1 - cfg.crashGrip) * back;
  } else {
    s.controlScale = 1;
    s.gripScale = 1;
  }
}

/** Call after stepKart moves the kart. Returns the hit, or null if not touching a wall. */
export function stepWalls(
  s: KartState,
  ground: GroundQuery,
  cfg: WallConfig & ImpactConfig,
  dt: number,
): WallHit | null {
  const road = ground.at(s.x, s.z).road;
  if (!road) return null;
  const limit = road.halfWidth - cfg.kartRadius;
  const out = Math.abs(road.across) - limit;
  if (out <= 0 || out > cfg.kartRadius + OUTSIDE) return null;

  const side = Math.sign(road.across); // +1 right wall, -1 left wall
  const edgeY = road.centreY + side * road.halfWidth * road.rise;
  if (s.y > edgeY + cfg.wallHeight) return null; // flying over it

  return hitWall(s, road.rx * side, road.rz * side, out, cfg, dt);
}

/**
 * The kart is `out` metres into a wall whose face points away from (wx, wz), a unit
 * horizontal direction from the kart into the wall. Push it out, take away the velocity
 * into the wall, and judge the impact. Shared by road-edge walls and solid obstacles.
 */
export function hitWall(
  s: KartState,
  wx: number,
  wz: number,
  out: number,
  cfg: WallConfig & ImpactConfig,
  dt: number,
): WallHit {
  const newContact = s.wallContactAge > cfg.contactReset;
  s.wallContactAge = 0;
  if (newContact) s.impactPeak = 0;

  // Back inside.
  s.x -= wx * out;
  s.z -= wz * out;

  // Remove velocity into the wall; keep the rest.
  const pathBefore = s.velAngle;
  let vx = Math.sin(s.velAngle) * s.speed;
  let vz = Math.cos(s.velAngle) * s.speed;
  const into = Math.max(0, vx * wx + vz * wz);
  if (into > 0) {
    vx -= wx * into;
    vz -= wz * into;
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
  // While drifting (or easing out of one), the path is the body plus the drift offset.
  // Put the wall's deflection into the offset, not the body: the path follows the wall
  // at once, and the body only turns as the offset eases back, so it never snaps.
  if (s.driftDir !== 0 || s.recovering) {
    s.driftOffset = wrap(s.driftOffset + wrap(s.velAngle - pathBefore));
  }

  // Which way turns the nose away from the wall (toward running along it).
  const nx = Math.sin(s.heading);
  const nz = Math.cos(s.heading);
  const intoNose = nx * wx + nz * wz;
  const ax = nx - wx * intoNose;
  const az = nz - wz * intoNose;
  const toAlong = wrap(Math.atan2(ax, az) - s.heading);
  const away = toAlong !== 0 ? Math.sign(toAlong) : 1;

  // Judge the impact once per contact, or again if this hit is clearly harder.
  let tier: ImpactTier = 0;
  if (into > 0 && into >= s.impactPeak + HARDER) {
    s.impactPeak = into;
    tier = into < cfg.scrapeSpeed ? 1 : into < cfg.crashSpeed ? 2 : 3;
    if (tier >= 2) {
      const kick = Math.min(cfg.kickMax, cfg.kickPerSpeed * (into - cfg.scrapeSpeed));
      if (kick > Math.abs(s.yawKick)) s.yawKick = away * kick;
      // Total rotation the kick will cause before it fades.
      const turn = Math.abs(s.yawKick) / Math.max(1e-6, cfg.kickDamp);
      if (tier === 3 || (s.driftDir !== 0 && turn > cfg.driftBreakDeg * DEG)) tier = 3;
    }
    if (tier === 3) {
      if (s.driftDir !== 0) {
        s.driftDir = 0;
        s.recovering = true;
      }
      s.yawKick *= cfg.crashSpinKeep;
      s.crashTime = cfg.crashSec;
      // A crash also ends any zipper boost, keeping only part of its benefit.
      s.zipCrashed = true;
    }
    s.lastImpactSpeed = into;
    s.lastImpactTier = tier;
  }

  // If the nose is pinned into the wall (not drifting), swing it to run along the wall,
  // so holding throttle scrapes you off rather than pinning you there.
  if (s.driftDir === 0 && intoNose > 0) {
    const turn = toAlong * (1 - Math.exp(-cfg.wallAlign * dt));
    const cap = cfg.wallAlignMaxRate * dt;
    s.heading = wrap(s.heading + Math.max(-cap, Math.min(cap, turn)));
  }
  return { into, tier };
}

/**
 * Collide with solid obstacles (tunnel rock, the map boundary, trees). The kart is a
 * circle of kartRadius; every touching solid pushes it out like a wall would, with the
 * same impact rules. Returns the hardest hit this step, or null.
 */
export function stepSolids(
  s: KartState,
  solids: Solid[],
  cfg: WallConfig & ImpactConfig,
  dt: number,
): WallHit | null {
  let worst: WallHit | null = null;
  const r = cfg.kartRadius;
  for (const b of solids) {
    if (s.y > b.height) continue; // flying over it
    let nx: number;
    let nz: number;
    let out: number;
    if (b.kind === "circle") {
      const dx = s.x - b.x;
      const dz = s.z - b.z;
      const d = Math.hypot(dx, dz);
      if (d >= b.radius + r) continue;
      nx = d > 1e-6 ? dx / d : 1;
      nz = d > 1e-6 ? dz / d : 0;
      out = b.radius + r - d;
    } else {
      const fx = Math.sin(b.heading);
      const fz = Math.cos(b.heading);
      const dx = s.x - b.x;
      const dz = s.z - b.z;
      const u = dx * fx + dz * fz; // along the box
      const v = dx * fz - dz * fx; // across it, along (fz, -fx)
      if (Math.abs(u) >= b.halfLength + r || Math.abs(v) >= b.halfWidth + r) continue;
      const du = u - Math.max(-b.halfLength, Math.min(b.halfLength, u));
      const dv = v - Math.max(-b.halfWidth, Math.min(b.halfWidth, v));
      let nu: number;
      let nv: number;
      if (du === 0 && dv === 0) {
        // Centre inside the box: out through the nearest face.
        const pu = b.halfLength - Math.abs(u) + r;
        const pv = b.halfWidth - Math.abs(v) + r;
        if (pu < pv) {
          nu = Math.sign(u) || 1;
          nv = 0;
          out = pu;
        } else {
          nu = 0;
          nv = Math.sign(v) || 1;
          out = pv;
        }
      } else {
        const d = Math.hypot(du, dv);
        if (d >= r) continue;
        nu = du / d;
        nv = dv / d;
        out = r - d;
      }
      nx = nu * fx + nv * fz;
      nz = nu * fz - nv * fx;
    }
    const hit = hitWall(s, -nx, -nz, out, cfg, dt);
    if (!worst || hit.into > worst.into) worst = hit;
  }
  return worst;
}

/**
 * Collide with the walls of an imported track's collision mesh (barriers, cliffs,
 * pillars, tunnel sides). Each overlap goes through the same hitWall as every other
 * wall, so impacts, drift handling and alignment behave exactly as on built-in tracks.
 */
export function stepMeshWalls(
  s: KartState,
  mesh: CollisionMesh,
  cfg: WallConfig & ImpactConfig,
  dt: number,
): WallHit | null {
  let worst: WallHit | null = null;
  // A few passes resolve corners where two walls meet.
  for (let i = 0; i < 3; i++) {
    const c = deepestWall(
      mesh,
      s.x,
      s.y,
      s.z,
      cfg.kartRadius,
      Math.sin(s.velAngle) * s.speed,
      Math.cos(s.velAngle) * s.speed,
    );
    if (!c || c.out < 1e-6) break;
    const hit = hitWall(s, c.wx, c.wz, c.out, cfg, dt);
    if (!worst || hit.into > worst.into) worst = hit;
  }
  return worst;
}
