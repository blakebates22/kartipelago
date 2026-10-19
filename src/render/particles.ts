/**
 * Chunky little particles (splashes, spray, smoke puffs, sparks): a fixed pool of
 * points, each with its own colour, rising or falling under their own gravity and
 * fading out. One draw call per pool. Purely visual: nothing reads them back.
 */
import * as THREE from "three";

export interface ParticlePool {
  readonly points: THREE.Points;
  /** Start one particle. */
  emit(
    x: number,
    y: number,
    z: number,
    vx: number,
    vy: number,
    vz: number,
    life: number,
    color: THREE.ColorRepresentation,
  ): void;
  /** Start a ring-shaped burst of n particles (splashes). */
  burst(
    x: number,
    y: number,
    z: number,
    n: number,
    speed: number,
    up: number,
    life: number,
    color: THREE.ColorRepresentation,
  ): void;
  step(dt: number): void;
  dispose(): void;
}

function dotTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 16;
  const g = c.getContext("2d")!;
  g.fillStyle = "#fff";
  // A pixelly disc.
  for (let y = 0; y < 16; y++)
    for (let x = 0; x < 16; x++) if ((x - 7.5) ** 2 + (y - 7.5) ** 2 < 52) g.fillRect(x, y, 1, 1);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  return t;
}

export function createParticles(
  parent: THREE.Object3D,
  opts: {
    max?: number;
    size?: number;
    gravity?: number;
    opacity?: number;
    additive?: boolean;
  } = {},
): ParticlePool {
  const max = opts.max ?? 256;
  const gravity = opts.gravity ?? -12;
  const pos = new Float32Array(max * 3);
  const col = new Float32Array(max * 3);
  const vel = new Float32Array(max * 3);
  const life = new Float32Array(max);
  const total = new Float32Array(max);
  const base = new Float32Array(max * 3);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  const tex = typeof document !== "undefined" ? dotTexture() : null;
  const mat = new THREE.PointsMaterial({
    size: opts.size ?? 0.6,
    vertexColors: true,
    map: tex,
    transparent: true,
    opacity: opts.opacity ?? 0.9,
    alphaTest: 0.5,
    depthWrite: false,
    blending: opts.additive ? THREE.AdditiveBlending : THREE.NormalBlending,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.renderOrder = 2;
  parent.add(points);
  for (let i = 0; i < max; i++) pos[i * 3 + 1] = -1e4;
  let next = 0;
  const c = new THREE.Color();

  const pool: ParticlePool = {
    points,
    emit(x, y, z, vx, vy, vz, l, color) {
      const i = next;
      next = (next + 1) % max;
      pos[i * 3] = x;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = z;
      vel[i * 3] = vx;
      vel[i * 3 + 1] = vy;
      vel[i * 3 + 2] = vz;
      life[i] = l;
      total[i] = l;
      c.set(color);
      base[i * 3] = c.r;
      base[i * 3 + 1] = c.g;
      base[i * 3 + 2] = c.b;
    },
    burst(x, y, z, n, speed, up, l, color) {
      for (let k = 0; k < n; k++) {
        const a = (k / n) * Math.PI * 2 + Math.random() * 0.4;
        const s = speed * (0.6 + Math.random() * 0.6);
        pool.emit(
          x,
          y,
          z,
          Math.sin(a) * s,
          up * (0.7 + Math.random() * 0.6),
          Math.cos(a) * s,
          l * (0.7 + Math.random() * 0.5),
          color,
        );
      }
    },
    step(dt) {
      for (let i = 0; i < max; i++) {
        if (life[i]! <= 0) continue;
        life[i]! -= dt;
        if (life[i]! <= 0) {
          pos[i * 3 + 1] = -1e4;
          continue;
        }
        vel[i * 3 + 1]! += gravity * dt;
        pos[i * 3]! += vel[i * 3]! * dt;
        pos[i * 3 + 1]! += vel[i * 3 + 1]! * dt;
        pos[i * 3 + 2]! += vel[i * 3 + 2]! * dt;
        // Additive sparks fade by darkening; everything else keeps its colour to the end.
        const f = opts.additive ? Math.min(1, (life[i]! / total[i]!) * 2) : 1;
        col[i * 3] = base[i * 3]! * f;
        col[i * 3 + 1] = base[i * 3 + 1]! * f;
        col[i * 3 + 2] = base[i * 3 + 2]! * f;
      }
      geo.attributes.position!.needsUpdate = true;
      geo.attributes.color!.needsUpdate = true;
    },
    dispose() {
      points.removeFromParent();
      geo.dispose();
      mat.dispose();
      tex?.dispose();
    },
  };
  return pool;
}
