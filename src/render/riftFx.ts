/**
 * Aurora Rift's living pieces, drawn in code (original, a few dozen triangles each):
 * the falling icicles and the glowing ring that warns where they'll land, the cracked
 * patches of lake ice (their cracks spreading, then open slush with floating plates),
 * and the crystals that flare as you pass. Purely visual: what they do is game/rift.ts
 * and game/hazards.ts.
 */
import * as THREE from "three";
import type { IcicleConfig, IciclePhase, ThinIce } from "../game/rift";

const disposeAll = (o: THREE.Object3D) =>
  o.traverse((m) => {
    if (m instanceof THREE.Mesh) {
      m.geometry.dispose();
      (Array.isArray(m.material) ? m.material : [m.material]).forEach((x) => x.dispose());
    }
  });

export interface IcicleView {
  update(phase: IciclePhase, u: number, tip: number, t: number): void;
  dispose(): void;
}

/** A great icicle (a cluster of three, the middle one longest) and its warning ring. */
export function createIcicleView(parent: THREE.Object3D, c: IcicleConfig): IcicleView {
  const root = new THREE.Group();
  const rock = c.look === "rock";
  const meteor = c.look === "meteor";
  const ice = new THREE.MeshLambertMaterial(
    rock
      ? { color: 0x2a2224, emissive: 0xff4a10, emissiveIntensity: 0.25, flatShading: true }
      : meteor
        ? { color: 0x3a2a2a, emissive: 0xff7a2a, emissiveIntensity: 1.1, flatShading: true }
        : {
            color: 0xbfe8ff,
            emissive: 0x2a7ad8,
            emissiveIntensity: 0.6,
            transparent: true,
            opacity: 0.88,
            flatShading: true,
          },
  );
  const shard = (len: number, r: number, x: number, z: number) => {
    // Point down: the cone's tip at the group's origin, its base `len` above.
    const g = new THREE.ConeGeometry(r, len, 6).rotateX(Math.PI).translate(0, len / 2, 0);
    const m = new THREE.Mesh(g, ice);
    m.position.set(x, len * 0.12, z);
    root.add(m);
  };
  let trail: THREE.Mesh | undefined;
  if (rock || meteor) {
    // A jagged boulder (a burning one, with a tail of fire behind it, for a meteor).
    const g = new THREE.DodecahedronGeometry(meteor ? 1.6 : 2.0, 0);
    const pos = g.getAttribute("position") as THREE.BufferAttribute;
    for (let i = 0; i < pos.count; i++)
      pos.setXYZ(i, pos.getX(i) * 1.15, pos.getY(i) * 0.85 + 1.4, pos.getZ(i));
    root.add(new THREE.Mesh(g, ice));
    if (meteor) {
      trail = new THREE.Mesh(
        new THREE.ConeGeometry(1.6, 1, 8, 1, true).translate(0, 0.5, 0),
        new THREE.MeshBasicMaterial({
          color: 0xff8a3a,
          transparent: true,
          opacity: 0.6,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
      trail.position.y = 1.4;
      root.add(trail);
    }
  } else {
    shard(7, 1.1, 0, 0);
    shard(4.5, 0.7, 0.9, 0.4);
    shard(3.5, 0.6, -0.8, -0.5);
  }
  root.position.set(c.x, c.top, c.z);
  parent.add(root);
  // The warning: a ring on the road where it will land.
  const ringMat = new THREE.MeshBasicMaterial({
    color: rock || meteor ? 0xff7a2a : 0x7af0ff,
    transparent: true,
    opacity: 0,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
  });
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(c.r * 0.7, c.r, 28).rotateX(-Math.PI / 2),
    ringMat,
  );
  ring.position.set(c.x, c.y + 0.12, c.z);
  ring.renderOrder = 3;
  if (!c.decor) parent.add(ring);
  return {
    update(phase, u, tip, t) {
      // A meteor is only seen once it's falling (it comes out of the sky); a rock
      // hangs from the roof like an icicle, working loose.
      root.visible = phase !== "shattered" && (!meteor || phase === "falling");
      const grow = phase === "hanging" && !rock && !meteor ? 0.3 + 0.7 * u : 1;
      root.scale.setScalar(grow);
      const shake = phase === "warning" ? 0.12 + 0.25 * u : 0;
      root.position.set(c.x + Math.sin(t * 47) * shake, tip, c.z + Math.cos(t * 39) * shake);
      if (trail) trail.scale.set(1, 6 + 30 * (phase === "falling" ? 1 - u : 0), 1);
      ringMat.opacity =
        phase === "warning"
          ? 0.25 + 0.45 * u + 0.2 * Math.sin(t * 18)
          : phase === "falling"
            ? 0.8
            : 0;
    },
    dispose() {
      root.removeFromParent();
      ring.removeFromParent();
      disposeAll(root);
      ring.geometry.dispose();
      ringMat.dispose();
    },
  };
}

/** Crack lines, drawn once: a starburst of jagged lines from the middle, and rings. */
function crackTexture(seed: number) {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d")!;
  let s = seed * 9301 + 49297;
  const r = () => (s = (s * 9301 + 49297) % 233280) / 233280;
  g.strokeStyle = "#f4fbff";
  g.lineWidth = 2;
  for (let k = 0; k < 9; k++) {
    let a = (k / 9) * Math.PI * 2 + r() * 0.5;
    let x = 64;
    let y = 64;
    g.beginPath();
    g.moveTo(x, y);
    for (let j = 0; j < 6; j++) {
      a += (r() - 0.5) * 0.9;
      x += Math.cos(a) * (8 + r() * 6);
      y += Math.sin(a) * (8 + r() * 6);
      g.lineTo(x, y);
    }
    g.stroke();
  }
  g.lineWidth = 1.5;
  for (const rad of [22, 40]) {
    g.beginPath();
    for (let k = 0; k <= 24; k++) {
      const a = (k / 24) * Math.PI * 2;
      const rr = rad + (r() - 0.5) * 6;
      if (k === 0) g.moveTo(64 + Math.cos(a) * rr, 64 + Math.sin(a) * rr);
      else g.lineTo(64 + Math.cos(a) * rr, 64 + Math.sin(a) * rr);
    }
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export interface ThinIceView {
  update(p: ThinIce, t: number): void;
  dispose(): void;
}

/** A cracked patch: cracks spreading as the stage goes up; broken, dark slush and plates. */
export function createThinIceView(parent: THREE.Object3D, p: ThinIce, seed: number): ThinIceView {
  const root = new THREE.Group();
  root.position.set(p.x, p.y + 0.08, p.z);
  const tex = crackTexture(seed);
  const crackMat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    opacity: 0.2,
    depthWrite: false,
  });
  const cracks = new THREE.Mesh(new THREE.CircleGeometry(p.r, 32).rotateX(-Math.PI / 2), crackMat);
  cracks.renderOrder = 3;
  root.add(cracks);
  const waterMat = new THREE.MeshLambertMaterial({
    color: 0x0a2a4a,
    emissive: 0x0a4a7a,
    emissiveIntensity: 0.5,
    transparent: true,
    opacity: 0.85,
    depthWrite: false,
  });
  const water = new THREE.Mesh(
    new THREE.CircleGeometry(p.r * 0.9, 24).rotateX(-Math.PI / 2),
    waterMat,
  );
  water.position.y = 0.02;
  water.renderOrder = 4;
  water.visible = false;
  root.add(water);
  const plateMat = new THREE.MeshLambertMaterial({ color: 0xcfeaff, flatShading: true });
  const plates: THREE.Mesh[] = [];
  for (let k = 0; k < 6; k++) {
    const a = k * 2.4;
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(1.4 + (k % 3) * 0.5, 0.25, 1.1 + (k % 2) * 0.6),
      plateMat,
    );
    m.position.set(Math.cos(a) * p.r * 0.5, 0.1, Math.sin(a) * p.r * 0.5);
    m.rotation.y = a;
    m.visible = false;
    root.add(m);
    plates.push(m);
  }
  parent.add(root);
  return {
    update(q, t) {
      const open = q.broken > 0;
      crackMat.opacity = open ? 0 : [0.18, 0.5, 0.85, 1][Math.min(3, q.stage)]!;
      cracks.scale.setScalar(0.55 + 0.15 * Math.min(3, q.stage));
      water.visible = open;
      plates.forEach((m, k) => {
        m.visible = open;
        m.position.y = 0.1 + 0.08 * Math.sin(t * 2 + k);
        m.rotation.z = 0.08 * Math.sin(t * 1.6 + k * 2);
      });
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
      tex.dispose();
    },
  };
}

export interface ShimmerView {
  /** level: 0 at rest .. 1 flaring. */
  update(level: number, t: number): void;
  dispose(): void;
}

/** A small crystal cluster that flares bright when you pass. */
export function createShimmerView(
  parent: THREE.Object3D,
  x: number,
  y: number,
  z: number,
  size: number,
  color: string,
  phase: number,
): ShimmerView {
  const root = new THREE.Group();
  root.position.set(x, y, z);
  const base = new THREE.Color(color);
  const mat = new THREE.MeshLambertMaterial({
    color: base.clone().multiplyScalar(0.7),
    emissive: base,
    emissiveIntensity: 0.4,
    flatShading: true,
  });
  for (const [h, r, dx, dz, lean] of [
    [2.4, 0.38, 0, 0, 0.05],
    [1.6, 0.28, 0.45, 0.2, 0.35],
    [1.3, 0.24, -0.4, -0.15, -0.3],
  ] as const) {
    const g = new THREE.ConeGeometry(r * size, h * size, 6).translate(0, (h * size) / 2, 0);
    const m = new THREE.Mesh(g, mat);
    m.position.set(dx * size, 0, dz * size);
    m.rotation.z = lean;
    root.add(m);
  }
  parent.add(root);
  return {
    update(level, t) {
      mat.emissiveIntensity = 0.35 + 0.12 * Math.sin(t * 2.1 + phase) + 2.2 * level;
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}
