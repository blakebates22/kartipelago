/**
 * Zipper pads on a track. Each track's JSON lists them by distance along the lap and
 * offset across the road; here they become rectangles on the road surface. A pad fires
 * only on the step a kart enters it, so overlapping a pad can't re-trigger it.
 */
import type { Track } from "./track";

export interface ZipperSpot {
  /** Distance along the lap from the start line, metres. */
  at: number;
  /** Offset across the road, metres; positive is toward the right edge. */
  across?: number;
  /** Branching courses: `at` is along this whole-lap route (TrackMeta.lapRoutes). */
  route?: string;
}

export interface ZipperPad {
  x: number;
  y: number;
  z: number;
  /** Direction of travel along the track at the pad. */
  heading: number;
  halfLength: number;
  halfWidth: number;
}

export interface PadSize {
  zipperLength: number;
  zipperWidth: number;
}

export function buildZippers(track: Track, spots: ZipperSpot[], size: PadSize): ZipperPad[] {
  const n = track.samples.length;
  return spots.map((spot) => {
    const s = track.samples[Math.round((spot.at / track.length) * n) % n]!;
    const rh = Math.hypot(s.right.x, s.right.z);
    const across = spot.across ?? 0;
    return {
      x: s.pos.x + (s.right.x / rh) * across,
      y: s.pos.y + s.right.y * (across / rh),
      z: s.pos.z + (s.right.z / rh) * across,
      heading: Math.atan2(s.forward.x, s.forward.z),
      halfLength: size.zipperLength / 2,
      halfWidth: size.zipperWidth / 2,
    };
  });
}

export function onZipper(x: number, z: number, pad: ZipperPad): boolean {
  const dx = x - pad.x;
  const dz = z - pad.z;
  const along = dx * Math.sin(pad.heading) + dz * Math.cos(pad.heading);
  const across = dx * Math.cos(pad.heading) - dz * Math.sin(pad.heading);
  return Math.abs(along) <= pad.halfLength && Math.abs(across) <= pad.halfWidth;
}

/** True on the step a kart enters any pad (and updates its "on a pad" memory). */
export function enteredZipper(
  kart: { x: number; y?: number; z: number; zipOnPad: boolean },
  pads: ZipperPad[],
): boolean {
  // Within a few metres of the pad's height too: on stacked roads a pad on the lower
  // road mustn't fire for a kart on the bridge above it.
  const on = pads.some(
    (p) => onZipper(kart.x, kart.z, p) && (kart.y === undefined || Math.abs(kart.y - p.y) < 4),
  );
  const entered = on && !kart.zipOnPad;
  kart.zipOnPad = on;
  return entered;
}
