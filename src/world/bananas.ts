/**
 * Bananas lying on the track, to drive through and collect.
 *
 * Placed bananas come from the track's JSON (rows along the lap) and come back
 * `respawnSec` after being collected. Dropped bananas are thrown out of a kart that
 * loses some: they fly outward and up, fall under gravity, slide to a stop on the road,
 * and only then become ordinary pickups (so the kart that dropped them can't scoop them
 * straight back up mid-air). Once collected, a dropped banana is gone for good.
 *
 * Everything here is plain data stepped on the fixed physics step.
 */
import type { GroundQuery } from "../physics/ground";
import { addBananas } from "../vehicles/bananas";
import type { Track } from "./track";

export interface BananaSpot {
  /** Distance along the lap from the start line, metres. */
  at: number;
  /** Offset across the road, metres; positive is toward the right edge. */
  across?: number;
  /** A row of this many along the track (default 1)... */
  count?: number;
  /** ...this many metres apart (default 4). */
  gap?: number;
}

export interface Banana {
  x: number;
  /** Height of the ground under it (the mesh floats restHeight above). */
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  /** Lying still on the ground and collectible (after any drop delay). */
  settled: boolean;
  /** On the track right now (false once collected, until a placed one respawns). */
  active: boolean;
  /** Placed by the track (respawns) or dropped by a kart (doesn't). */
  placed: boolean;
  /** Seconds since dropped, or since it last (re)appeared. */
  age: number;
  /** Seconds until a collected placed banana comes back. */
  respawnIn: number;
  /** Ground lookup while falling (dropped bananas only). */
  ground?: GroundQuery;
}

export interface BananaFieldConfig {
  pickupRadius: number;
  pickupHeight: number;
  respawnSec: number;
  dropSpeed: number;
  dropUp: number;
  dropCarry: number;
  dropGravity: number;
  dropAirDrag: number;
  dropFriction: number;
  dropBounce: number;
  dropSettleSpeed: number;
  dropPickupDelay: number;
}

export interface BananaField {
  bananas: Banana[];
  /** A fresh ground lookup, for each dropped banana while it falls. */
  makeGround: () => GroundQuery;
}

/** Where a banana was collected, and by which kart (for effects and sound). */
export interface BananaPickup {
  kart: number;
  x: number;
  y: number;
  z: number;
}

/** Kept this far inside the road edge when sliding. */
const EDGE_MARGIN = 0.6;

export function createBananaField(
  track: Track | undefined,
  spots: BananaSpot[],
  makeGround: () => GroundQuery,
): BananaField {
  const bananas: Banana[] = [];
  if (track) {
    const n = track.samples.length;
    for (const spot of spots) {
      for (let k = 0; k < (spot.count ?? 1); k++) {
        const at = spot.at + k * (spot.gap ?? 4);
        const s = track.samples[((Math.round((at / track.length) * n) % n) + n) % n]!;
        const rh = Math.hypot(s.right.x, s.right.z);
        const across = spot.across ?? 0;
        bananas.push({
          ...still(),
          x: s.pos.x + (s.right.x / rh) * across,
          y: s.pos.y + s.right.y * (across / rh),
          z: s.pos.z + (s.right.z / rh) * across,
          placed: true,
        });
      }
    }
  }
  return { bananas, makeGround };
}

const still = () => ({
  x: 0,
  y: 0,
  z: 0,
  vx: 0,
  vy: 0,
  vz: 0,
  settled: true,
  active: true,
  placed: false,
  age: 0,
  respawnIn: 0,
});

/** Put every placed banana back and clear dropped ones (a restart). */
export function resetBananaField(field: BananaField) {
  field.bananas = field.bananas.filter((b) => b.placed);
  for (const b of field.bananas) Object.assign(b, { active: true, age: 0, respawnIn: 0 });
}

/**
 * Throw `count` bananas out of a kart: spread evenly around it, outward and up, plus a
 * share of the kart's own velocity. Deterministic (no randomness).
 */
export function dropBananas(
  field: BananaField,
  kart: { x: number; y: number; z: number; heading: number; velAngle: number; speed: number },
  count: number,
  cfg: BananaFieldConfig,
): Banana[] {
  const out: Banana[] = [];
  const carryX = Math.sin(kart.velAngle) * kart.speed * cfg.dropCarry;
  const carryZ = Math.cos(kart.velAngle) * kart.speed * cfg.dropCarry;
  for (let k = 0; k < count; k++) {
    // Start out to the sides (not straight ahead), evenly spaced round the kart.
    const a = kart.heading + Math.PI / 2 + (2 * Math.PI * k) / count;
    const b: Banana = {
      ...still(),
      x: kart.x,
      y: kart.y + 0.5,
      z: kart.z,
      vx: Math.sin(a) * cfg.dropSpeed + carryX,
      vy: cfg.dropUp,
      vz: Math.cos(a) * cfg.dropSpeed + carryZ,
      settled: false,
      ground: field.makeGround(),
    };
    field.bananas.push(b);
    out.push(b);
  }
  return out;
}

/** Fly, fall, slide and settle dropped bananas; count down respawns. */
export function stepBananaField(field: BananaField, cfg: BananaFieldConfig, dt: number) {
  for (const b of field.bananas) {
    b.age += dt;
    if (!b.active) {
      if (b.placed && (b.respawnIn -= dt) <= 0) {
        b.active = true;
        b.age = 0;
      }
      continue;
    }
    if (b.settled || !b.ground) continue;

    // Air: gravity, and horizontal momentum fades.
    b.vy -= cfg.dropGravity * dt;
    const keep = Math.exp(-cfg.dropAirDrag * dt);
    b.vx *= keep;
    b.vz *= keep;
    b.x += b.vx * dt;
    b.y += b.vy * dt;
    b.z += b.vz * dt;

    const surface = b.ground.at(b.x, b.z);
    // Stay on the road: push back inside the edge and bounce off it.
    const road = surface.road;
    if (road) {
      const out = Math.abs(road.across) - (road.halfWidth - EDGE_MARGIN);
      if (out > 0) {
        const side = Math.sign(road.across);
        b.x -= road.rx * side * out;
        b.z -= road.rz * side * out;
        const into = (b.vx * road.rx + b.vz * road.rz) * side;
        if (into > 0) {
          b.vx -= road.rx * side * into * 1.5;
          b.vz -= road.rz * side * into * 1.5;
        }
      }
    }
    const floor = b.ground.at(b.x, b.z).height;
    if (b.y <= floor) {
      b.y = floor;
      // A small bounce, then sliding friction until it stops.
      b.vy = b.vy < -2 ? -b.vy * cfg.dropBounce : 0;
      const h = Math.hypot(b.vx, b.vz);
      const slowed = Math.max(0, h - cfg.dropFriction * dt);
      if (h > 0) {
        b.vx *= slowed / h;
        b.vz *= slowed / h;
      }
      if (b.vy === 0 && slowed <= cfg.dropSettleSpeed) {
        b.vx = b.vz = 0;
        b.settled = true;
        b.ground = undefined;
      }
    }
  }
}

/** Whether a kart at this spot is close enough to take this banana. */
export function canCollect(
  b: Banana,
  kart: { x: number; y: number; z: number },
  cfg: BananaFieldConfig,
): boolean {
  if (!b.active || !b.settled) return false;
  if (!b.placed && b.age < cfg.dropPickupDelay) return false;
  const dx = kart.x - b.x;
  const dz = kart.z - b.z;
  return dx * dx + dz * dz <= cfg.pickupRadius ** 2 && Math.abs(kart.y - b.y) <= cfg.pickupHeight;
}

/**
 * Collect every banana this kart is touching. Each is taken once: placed ones go away
 * until they respawn, dropped ones are removed. Returns the pickups.
 */
export function collectBananas(
  field: BananaField,
  kartIndex: number,
  kart: { x: number; y: number; z: number; bananas: number },
  cfg: BananaFieldConfig,
): BananaPickup[] {
  const got: BananaPickup[] = [];
  for (const b of field.bananas) {
    if (!canCollect(b, kart, cfg)) continue;
    b.active = false;
    b.respawnIn = cfg.respawnSec;
    addBananas(kart, 1);
    got.push({ kart: kartIndex, x: b.x, y: b.y, z: b.z });
  }
  if (got.length) field.bananas = field.bananas.filter((b) => b.active || b.placed);
  return got;
}
