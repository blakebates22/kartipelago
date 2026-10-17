/**
 * Tracks are built from data: a closed loop of centre points, each with an optional
 * height, width and bank. A smooth spline runs through them, and everything else (road
 * mesh, walls, checkpoints, the start line) is derived from evenly spaced samples along
 * it. Layouts live in assets/data/track.json.
 */
import * as THREE from "three";

export interface TrackPoint {
  x: number;
  z: number;
  /** Height of the road surface, metres. Default 0. */
  y?: number;
  /** Road width, metres. Defaults to the track's defaultWidth. */
  width?: number;
  /** Bank angle in degrees; positive tilts the road down to the right. Default 0. */
  bank?: number;
}

export interface TrackData {
  name: string;
  defaultWidth: number;
  points: TrackPoint[];
}

export interface TrackSample {
  pos: THREE.Vector3;
  /** Unit direction of travel along the track. */
  forward: THREE.Vector3;
  /** Unit vector across the road toward the right edge (tilted by bank). */
  right: THREE.Vector3;
  width: number;
  /** Distance from the start line along the centre, metres. */
  dist: number;
}

export interface Track {
  data: TrackData;
  samples: TrackSample[];
  length: number;
  start: { x: number; z: number; heading: number };
}

const UP = new THREE.Vector3(0, 1, 0);

/** Interpolate a per-point value at curve parameter t (0..1 around the loop). */
function valueAt(points: TrackPoint[], t: number, get: (p: TrackPoint) => number): number {
  const f = t * points.length;
  const i = Math.floor(f) % points.length;
  const j = (i + 1) % points.length;
  const k = f - Math.floor(f);
  return get(points[i]!) * (1 - k) + get(points[j]!) * k;
}

export function buildTrack(data: TrackData, spacing: number): Track {
  if (data.points.length < 3) throw new Error("a track needs at least 3 points");
  const curve = new THREE.CatmullRomCurve3(
    data.points.map((p) => new THREE.Vector3(p.x, p.y ?? 0, p.z)),
    true,
    "centripetal",
  );
  const length = curve.getLength();
  const count = Math.max(8, Math.round(length / spacing));
  const samples: TrackSample[] = [];

  for (let i = 0; i < count; i++) {
    const u = i / count; // fraction of the way round by distance
    const t = curve.getUtoTmapping(u, 0); // curve parameter at that distance
    const pos = curve.getPoint(t);
    const forward = curve.getTangent(t).normalize();
    // Right is horizontal and perpendicular to travel, then tilted by the bank angle.
    const flat = new THREE.Vector3(forward.x, 0, forward.z).normalize();
    const right = new THREE.Vector3(-flat.z, 0, flat.x);
    const bank = valueAt(data.points, t, (p) => p.bank ?? 0);
    right.applyAxisAngle(flat, (bank * Math.PI) / 180);
    const width = valueAt(data.points, t, (p) => p.width ?? data.defaultWidth);
    // Banking lowers one edge; lift the road so that edge never sinks under the ground.
    pos.y = Math.max(pos.y, (Math.abs(right.y) * width) / 2);
    samples.push({ pos, forward, right, width, dist: u * length });
  }

  // Face down the road a few metres ahead rather than along the tangent at the start
  // point, which the spline leans toward the previous corner.
  const first = samples[0]!;
  const ahead = samples[Math.min(3, count - 1)]!;
  return {
    data,
    samples,
    length,
    start: {
      x: first.pos.x,
      z: first.pos.z,
      heading: Math.atan2(ahead.pos.x - first.pos.x, ahead.pos.z - first.pos.z),
    },
  };
}

/** World position of a point across the road: -1 = left edge, 1 = right edge. */
export function acrossRoad(s: TrackSample, side: number, lift = 0): THREE.Vector3 {
  return s.pos
    .clone()
    .addScaledVector(s.right, (side * s.width) / 2)
    .addScaledVector(UP, lift);
}
