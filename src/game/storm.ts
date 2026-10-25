/**
 * A thunderstorm over a course (Emberdeep Hold): now and then a fork of lightning cracks
 * down from the clouds somewhere round the horizon, the whole scene flashes white-blue
 * (a double flicker), and a moment later the thunder rolls in. Purely visual and audible:
 * nothing here touches a kart, so it can be random.
 *
 * From the track.json entity:
 *
 *   { "type": "storm", "period": 9, "spread": 5, "distance": 900, "color": "#cfe0ff" }
 *
 * `period` is the average gap between strikes, give or take `spread` seconds; `distance`
 * how far off (metres) the bolts come down.
 */
import * as THREE from "three";

export interface StormConfig {
  period: number;
  spread: number;
  distance: number;
  color: string;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export function parseStorm(e: Record<string, unknown>): StormConfig {
  const period = Math.max(2, num(e.period, 9));
  return {
    period,
    spread: Math.max(0, Math.min(period - 1, num(e.spread, 5))),
    distance: Math.max(200, num(e.distance, 900)),
    color: typeof e.color === "string" ? e.color : "#cfe0ff",
  };
}

/** The flash's brightness `t` seconds into a strike: two quick flickers, then a fade. */
export function flashAt(t: number): number {
  if (t < 0) return 0;
  if (t < 0.07) return 1;
  if (t < 0.13) return 0.15;
  if (t < 0.2) return 0.85;
  return Math.max(0, 0.85 * Math.exp(-(t - 0.2) * 6));
}

/** A jagged bolt from (0, top, 0) down to (0, 0, 0) with a branch or two, as segments. */
function boltPath(top: number, rand: () => number): [THREE.Vector3, THREE.Vector3][] {
  const segs: [THREE.Vector3, THREE.Vector3][] = [];
  const walk = (from: THREE.Vector3, h: number, n: number, sway: number, branch: boolean) => {
    let p = from.clone();
    for (let i = 0; i < n; i++) {
      const q = new THREE.Vector3(
        p.x + (rand() - 0.5) * sway,
        p.y - h / n,
        p.z + (rand() - 0.5) * sway * 0.4,
      );
      segs.push([p, q]);
      if (branch && i > 2 && i < n - 3 && rand() < 0.18)
        walk(q, h * (0.2 + rand() * 0.2), 5, sway * 0.8, false);
      p = q;
    }
  };
  walk(new THREE.Vector3(0, top, 0), top, 14, top * 0.14, true);
  return segs;
}

export function createStormView(group: THREE.Group, cfg: StormConfig) {
  const light = new THREE.HemisphereLight(new THREE.Color(cfg.color), 0x404060, 0);
  group.add(light);
  const mat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(cfg.color),
    transparent: true,
    opacity: 0,
    fog: false,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
  });
  let bolt: THREE.Mesh | undefined;
  let next = cfg.period * (0.3 + Math.random() * 0.5);
  let since = Infinity;
  let thunder = Infinity;

  const strike = (lx: number, lz: number) => {
    if (bolt) {
      group.remove(bolt);
      bolt.geometry.dispose();
    }
    const top = 420 + Math.random() * 180;
    const w = 3.5;
    const pos: number[] = [];
    for (const [a, b] of boltPath(top, Math.random)) {
      // A flat ribbon facing the course (it's always far off).
      pos.push(a.x - w, a.y, a.z, a.x + w, a.y, a.z, b.x + w, b.y, b.z);
      pos.push(a.x - w, a.y, a.z, b.x + w, b.y, b.z, b.x - w, b.y, b.z);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    bolt = new THREE.Mesh(g, mat);
    const az = Math.random() * Math.PI * 2;
    const d = cfg.distance * (0.75 + Math.random() * 0.5);
    bolt.position.set(lx + Math.cos(az) * d, -20, lz + Math.sin(az) * d);
    bolt.lookAt(lx, -20, lz);
    group.add(bolt);
    since = 0;
    thunder = 0.6 + Math.random() * 1.4;
  };

  return {
    /** Step the storm; `rumble` plays the thunder. */
    update(dt: number, listener: { x: number; z: number }, rumble?: (loud: number) => void) {
      next -= dt;
      if (next <= 0) {
        strike(listener.x, listener.z);
        next = cfg.period + (Math.random() * 2 - 1) * cfg.spread;
      }
      since += dt;
      const f = flashAt(since);
      light.intensity = 2.6 * f;
      mat.opacity = Math.min(1, f * 1.2);
      if (bolt) bolt.visible = f > 0.01;
      if (thunder !== Infinity) {
        thunder -= dt;
        if (thunder <= 0) {
          thunder = Infinity;
          rumble?.(0.7);
        }
      }
    },
  };
}
