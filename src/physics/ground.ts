/**
 * "What's under me?" The kart asks this every step instead of using a physics engine.
 * On a track, the answer comes from the nearest stretch of road between two samples; off
 * the road (or in the practice scene) it's the flat ground plane at height 0.
 */
import type { Track } from "../world/track";

export interface Surface {
  height: number;
  /** Unit surface normal. */
  nx: number;
  ny: number;
  nz: number;
  onRoad: boolean;
}

export interface GroundQuery {
  at(x: number, z: number): Surface;
}

const FLAT: Surface = { height: 0, nx: 0, ny: 1, nz: 0, onRoad: false };

export const flatGround: GroundQuery = { at: () => FLAT };

/** How far either side of the last nearest sample to look before a full search. */
const WINDOW = 40;

export function createTrackGround(track: Track): GroundQuery {
  const s = track.samples;
  const n = s.length;
  let hint = 0;

  const dist2 = (i: number, x: number, z: number) => {
    const p = s[((i % n) + n) % n]!.pos;
    return (p.x - x) ** 2 + (p.z - z) ** 2;
  };

  const nearest = (x: number, z: number) => {
    let best = hint;
    let bestD = dist2(hint, x, z);
    for (let k = -WINDOW; k <= WINDOW; k++) {
      const d = dist2(hint + k, x, z);
      if (d < bestD) {
        bestD = d;
        best = hint + k;
      }
    }
    // Lost track of the kart (reset, respawn, big jump): search everything.
    if (bestD > 30 * 30) {
      for (let i = 0; i < n; i++) {
        const d = dist2(i, x, z);
        if (d < bestD) {
          bestD = d;
          best = i;
        }
      }
    }
    hint = ((best % n) + n) % n;
    return hint;
  };

  /** Project onto the segment from sample i to i+1; null if outside it. */
  const onSegment = (i: number, x: number, z: number): Surface | null => {
    const a = s[i]!;
    const b = s[(i + 1) % n]!;
    const dx = b.pos.x - a.pos.x;
    const dz = b.pos.z - a.pos.z;
    const len2 = dx * dx + dz * dz;
    const t = ((x - a.pos.x) * dx + (z - a.pos.z) * dz) / len2;
    if (t < -0.01 || t > 1.01) return null;
    const lerp = (p: number, q: number) => p + (q - p) * t;
    const cx = lerp(a.pos.x, b.pos.x);
    const cy = lerp(a.pos.y, b.pos.y);
    const cz = lerp(a.pos.z, b.pos.z);
    const rx = lerp(a.right.x, b.right.x);
    const ry = lerp(a.right.y, b.right.y);
    const rz = lerp(a.right.z, b.right.z);
    const fx = lerp(a.forward.x, b.forward.x);
    const fy = lerp(a.forward.y, b.forward.y);
    const fz = lerp(a.forward.z, b.forward.z);
    const width = lerp(a.width, b.width);
    // How far across the road, measured horizontally; banking raises or lowers it.
    const rh = Math.hypot(rx, rz);
    const across = ((x - cx) * rx + (z - cz) * rz) / (rh * rh);
    if (Math.abs(across * rh) > width / 2) return { ...FLAT };
    // Normal = right × forward.
    let nx = ry * fz - rz * fy;
    let ny = rz * fx - rx * fz;
    let nz = rx * fy - ry * fx;
    const nl = Math.hypot(nx, ny, nz);
    nx /= nl;
    ny /= nl;
    nz /= nl;
    return { height: cy + across * ry, nx, ny, nz, onRoad: true };
  };

  return {
    at(x, z) {
      const i = nearest(x, z);
      return onSegment(i, x, z) ?? onSegment((i - 1 + n) % n, x, z) ?? { ...FLAT };
    },
  };
}
