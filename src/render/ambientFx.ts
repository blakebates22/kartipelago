/**
 * The air of each area of an overworld region (overworld/air.ts AmbientSpec): its
 * course's particles drifting round the camera (Bonebog's fireflies in the swamp, Ember's
 * ash and embers on the volcano's slopes, the snow, the ice motes, the desert's dust),
 * each at the strength its area holds where you are, so they fade in and out with the
 * light as you drive from one area into the next. The same particles as the courses
 * (game/hazards.ts), from the same pools. Purely visual.
 */
import * as THREE from "three";
import type { AmbientKind, AmbientSpec } from "../overworld/air";
import { windAt } from "../game/desert";
import { createParticles, type ParticlePool } from "./particles";

const POOLS: Record<AmbientKind, Parameters<typeof createParticles>[1]> = {
  fireflies: { max: 500, size: 0.45, gravity: 0.8, additive: true },
  ashfall: { max: 700, size: 0.3, gravity: 0, opacity: 0.9 },
  snowfall: { max: 900, size: 0.22, gravity: 0, opacity: 0.95 },
  sparkles: { max: 600, size: 0.28, gravity: 0, additive: true },
  dustwind: { max: 700, size: 1.5, gravity: -0.5, opacity: 0.5 },
};

const pickOf = <T>(xs: readonly T[]) => xs[Math.floor(Math.random() * xs.length)]!;

export interface AmbientFx {
  /** Emit each area's particles at `weight` of their strength (and step them). */
  update(
    dt: number,
    t: number,
    listener: { x: number; y: number; z: number },
    areas: readonly { specs: readonly AmbientSpec[]; weight: number }[],
    groundAt?: (x: number, z: number, y: number) => number,
  ): void;
  dispose(): void;
}

export function createAmbientFx(root: THREE.Object3D): AmbientFx {
  const group = new THREE.Group();
  group.name = "area-ambient";
  root.add(group);
  const pools = new Map<AmbientKind, ParticlePool>();
  const acc = new Map<AmbientSpec, number>();
  const pool = (k: AmbientKind) => {
    let p = pools.get(k);
    if (!p) {
      p = createParticles(group, POOLS[k]);
      pools.set(k, p);
    }
    return p;
  };
  const r1 = () => Math.random() - 0.5;

  function emit(
    s: AmbientSpec,
    p: ParticlePool,
    t: number,
    L: { x: number; y: number; z: number },
    groundAt?: (x: number, z: number, y: number) => number,
  ) {
    const r = s.radius;
    const x = L.x + r1() * 2 * r;
    const z = L.z + r1() * 2 * r;
    const col = (d: readonly number[]) => (s.colors ? pickOf(s.colors) : pickOf(d));
    switch (s.kind) {
      case "fireflies":
        p.emit(
          x,
          L.y + 0.5 + Math.random() * 9,
          z,
          r1() * 1.2,
          -0.4 + Math.random() * 0.3,
          r1() * 1.2,
          2.5 + Math.random() * 2.5,
          col([0xeaff7a, 0xeaff7a, 0xfff2a0]),
        );
        break;
      case "ashfall": {
        const ember = Math.random() < 0.35;
        p.emit(
          x,
          L.y + (ember ? -2 + Math.random() * 6 : 4 + Math.random() * 16),
          z,
          r1() * 1.6,
          ember ? 1 + Math.random() * 1.5 : -1.5 - Math.random(),
          r1() * 1.6,
          ember ? 2.5 : 7,
          ember ? pickOf([0xff8a20, 0xffc040]) : col([0x7a6e6a, 0x9a8e88]),
        );
        break;
      }
      case "snowfall":
        p.emit(
          x,
          L.y + 6 + Math.random() * 18,
          z,
          0.8 + Math.sin(t * 0.3) * 0.6 + r1() * 0.6,
          -2.2 - Math.random() * 1.2,
          0.3 + r1() * 0.6,
          8,
          col([0xffffff, 0xffffff, 0xffffff, 0xdfe6ff]),
        );
        break;
      case "sparkles":
        p.emit(
          x,
          L.y - 2 + Math.random() * 14,
          z,
          r1() * 0.6,
          -0.3 + Math.random() * 0.5,
          r1() * 0.6,
          3 + Math.random() * 3,
          col([0xbff6ff, 0x7ae8ff, 0xd6b8ff, 0xffffff]),
        );
        break;
      case "dustwind": {
        const y = groundAt ? groundAt(x, z, L.y + 30) : L.y - 1;
        if (!Number.isFinite(y) || y > L.y + 20) break;
        const w = windAt(t);
        for (let k = 0; k < 3; k++)
          p.emit(
            x + k * 0.8,
            y + 0.2 + Math.random() * 0.8,
            z + r1(),
            w.x * (0.8 + Math.random() * 0.4),
            0.2 + Math.random() * 0.4,
            w.z * (0.8 + Math.random() * 0.4),
            2.2 + Math.random() * 1.6,
            col([0xe0a878]),
          );
        break;
      }
    }
  }

  return {
    update(dt, t, listener, areas, groundAt) {
      for (const { specs, weight } of areas)
        for (const s of specs) {
          if (weight <= 0.01) {
            acc.set(s, 0);
            continue;
          }
          const p = pool(s.kind);
          let a = Math.min(3, (acc.get(s) ?? 0) + dt * s.rate * weight);
          for (; a >= 1; a -= 1) emit(s, p, t, listener, groundAt);
          acc.set(s, a);
        }
      for (const p of pools.values()) p.step(dt);
    },
    dispose() {
      for (const p of pools.values()) p.dispose();
      pools.clear();
      group.removeFromParent();
    },
  };
}
