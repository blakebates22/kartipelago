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
 *   cancelled, the kick is damped, and steering and grip drop, then return smoothly
 *   over `crashSec`.
 */
import type { KartState } from "../vehicles/kart";
import type { GroundQuery } from "./ground";

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

  const newContact = s.wallContactAge > cfg.contactReset;
  s.wallContactAge = 0;
  if (newContact) s.impactPeak = 0;

  // Back inside.
  s.x -= road.rx * side * out;
  s.z -= road.rz * side * out;

  // Remove velocity into the wall; keep the rest.
  const pathBefore = s.velAngle;
  let vx = Math.sin(s.velAngle) * s.speed;
  let vz = Math.cos(s.velAngle) * s.speed;
  const into = Math.max(0, (vx * road.rx + vz * road.rz) * side);
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
  // While drifting (or easing out of one), the path is the body plus the drift offset.
  // Put the wall's deflection into the offset, not the body: the path follows the wall
  // at once, and the body only turns as the offset eases back, so it never snaps.
  if (s.driftDir !== 0 || s.recovering) {
    s.driftOffset = wrap(s.driftOffset + wrap(s.velAngle - pathBefore));
  }

  // Which way turns the nose away from the wall (toward running along it).
  const nx = Math.sin(s.heading);
  const nz = Math.cos(s.heading);
  const intoNose = (nx * road.rx + nz * road.rz) * side;
  const ax = nx - road.rx * side * intoNose;
  const az = nz - road.rz * side * intoNose;
  const toAlong = wrap(Math.atan2(ax, az) - s.heading);
  const away = toAlong !== 0 ? Math.sign(toAlong) : side;

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
