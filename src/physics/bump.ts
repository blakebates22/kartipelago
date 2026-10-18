/**
 * Kart-to-kart contact: karts are circles on the ground plane. Overlapping karts are
 * pushed apart, and the part of their velocities moving into each other is shared out
 * by mass (equal by default), so a kart that rams another slows and pushes it along. A
 * heavier kart (e.g. one with a shield up) moves less and shoves the other more.
 */
import type { KartState } from "../vehicles/kart";

/** Karts further apart vertically than this (one mid-jump) don't touch. */
const VERTICAL_CLEAR = 1.5;

/** Separate every overlapping pair. Returns how many pairs touched. */
export function bumpKarts(karts: KartState[], radius: number, masses?: number[]): number {
  let touches = 0;
  for (let i = 0; i < karts.length; i++) {
    for (let j = i + 1; j < karts.length; j++) {
      const a = karts[i]!;
      const b = karts[j]!;
      if (Math.abs(a.y - b.y) > VERTICAL_CLEAR) continue;
      const dx = b.x - a.x;
      const dz = b.z - a.z;
      const dist = Math.hypot(dx, dz);
      const min = radius * 2;
      if (dist >= min || dist < 1e-6) continue;
      touches++;
      const nx = dx / dist;
      const nz = dz / dist;
      const ma = masses?.[i] ?? 1;
      const mb = masses?.[j] ?? 1;
      // Share of the separation and of the closing speed each takes: the lighter moves more.
      const sa = mb / (ma + mb);
      const sb = ma / (ma + mb);
      const overlap = min - dist;
      a.x -= nx * overlap * sa;
      a.z -= nz * overlap * sa;
      b.x += nx * overlap * sb;
      b.z += nz * overlap * sb;

      const avx = Math.sin(a.velAngle) * a.speed;
      const avz = Math.cos(a.velAngle) * a.speed;
      const bvx = Math.sin(b.velAngle) * b.speed;
      const bvz = Math.cos(b.velAngle) * b.speed;
      const closing = (avx - bvx) * nx + (avz - bvz) * nz;
      if (closing <= 0) continue; // already separating
      setVelocity(a, avx - nx * closing * sa, avz - nz * closing * sa);
      setVelocity(b, bvx + nx * closing * sb, bvz + nz * closing * sb);
    }
  }
  return touches;
}

function setVelocity(k: KartState, vx: number, vz: number) {
  const v = Math.hypot(vx, vz);
  if (v < 1e-6) {
    k.speed = 0;
    return;
  }
  const fwd = k.speed >= 0 ? 1 : -1;
  k.velAngle = Math.atan2(vx * fwd, vz * fwd);
  k.speed = v * fwd;
}
