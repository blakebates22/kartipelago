/**
 * Kart-to-kart contact: karts are circles on the ground plane. Overlapping karts are
 * pushed apart equally, and the part of their velocities moving into each other is
 * shared out (equal masses), so a kart that rams another slows and pushes it along.
 */
import type { KartState } from "../vehicles/kart";

/** Karts further apart vertically than this (one mid-jump) don't touch. */
const VERTICAL_CLEAR = 1.5;

/** Separate every overlapping pair. Returns how many pairs touched. */
export function bumpKarts(karts: KartState[], radius: number): number {
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
      const push = (min - dist) / 2;
      a.x -= nx * push;
      a.z -= nz * push;
      b.x += nx * push;
      b.z += nz * push;

      const avx = Math.sin(a.velAngle) * a.speed;
      const avz = Math.cos(a.velAngle) * a.speed;
      const bvx = Math.sin(b.velAngle) * b.speed;
      const bvz = Math.cos(b.velAngle) * b.speed;
      const closing = (avx - bvx) * nx + (avz - bvz) * nz;
      if (closing <= 0) continue; // already separating
      const share = closing / 2;
      setVelocity(a, avx - nx * share, avz - nz * share);
      setVelocity(b, bvx + nx * share, bvz + nz * share);
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
