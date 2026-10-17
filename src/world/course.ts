/**
 * A drift practice course: pickups to collect and boost pads to hit. It exists to test
 * handling (can you drift onto the line you meant?), not as a real track. Layout lives in
 * assets/data/course.json; rules here are plain functions so they're testable.
 */
import { applyPadBoost, type KartConfig, type KartState } from "../vehicles/kart";

export interface Pad {
  x: number;
  z: number;
  /** Direction the pad pushes you, same convention as kart heading. */
  heading: number;
}

export interface CourseData {
  start: { x: number; z: number; heading: number };
  pickups: { x: number; z: number }[];
  pads: Pad[];
}

export interface CourseConfig {
  pickupRadius: number;
  pickupRespawnSec: number;
  padLength: number;
  padWidth: number;
}

export interface Pickup {
  x: number;
  z: number;
  /** Seconds until it reappears; 0 means it's there to collect. */
  respawnIn: number;
}

export interface Course {
  data: CourseData;
  pickups: Pickup[];
  collected: number;
}

export function createCourse(data: CourseData): Course {
  return {
    data,
    pickups: data.pickups.map((p) => ({ ...p, respawnIn: 0 })),
    collected: 0,
  };
}

export function resetCourse(course: Course) {
  for (const p of course.pickups) p.respawnIn = 0;
  course.collected = 0;
}

/** Is a point inside the pad's rectangle? */
export function onPad(x: number, z: number, pad: Pad, cfg: CourseConfig): boolean {
  const dx = x - pad.x;
  const dz = z - pad.z;
  const along = dx * Math.sin(pad.heading) + dz * Math.cos(pad.heading);
  const across = dx * Math.cos(pad.heading) - dz * Math.sin(pad.heading);
  return Math.abs(along) <= cfg.padLength / 2 && Math.abs(across) <= cfg.padWidth / 2;
}

/** Collect pickups and fire pads for this step. Returns how many were collected. */
export function stepCourse(
  course: Course,
  kart: KartState,
  cfg: CourseConfig,
  kartCfg: KartConfig,
  dt: number,
): number {
  let got = 0;
  const r2 = cfg.pickupRadius * cfg.pickupRadius;
  for (const p of course.pickups) {
    if (p.respawnIn > 0) {
      p.respawnIn = Math.max(0, p.respawnIn - dt);
      continue;
    }
    const dx = kart.x - p.x;
    const dz = kart.z - p.z;
    if (dx * dx + dz * dz <= r2) {
      p.respawnIn = cfg.pickupRespawnSec;
      got++;
    }
  }
  course.collected += got;

  for (const pad of course.data.pads) {
    if (onPad(kart.x, kart.z, pad, cfg)) applyPadBoost(kart, kartCfg);
  }
  return got;
}
