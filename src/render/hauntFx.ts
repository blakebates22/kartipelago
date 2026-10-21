/**
 * Dry Gulch Ghost Town's haunting, drawn in code (original designs, a few dozen
 * triangles each): see-through ghosts (a shape at a window, a sheet-like spirit, a
 * ghostly miner, a giant miner's shadow), the ghost rider and his horse, ore carts, a
 * tumbleweed, the saloon's swinging doors and drifting green wisps. Purely visual: when
 * and where is game/haunt.ts.
 */
import * as THREE from "three";
import type { GhostLook, WispsConfig } from "../game/haunt";
import { wispAt } from "../game/haunt";

const disposeAll = (o: THREE.Object3D) =>
  o.traverse((m) => {
    if (m instanceof THREE.Mesh || m instanceof THREE.LineSegments || m instanceof THREE.Points) {
      m.geometry.dispose();
      (Array.isArray(m.material) ? m.material : [m.material]).forEach((x) => x.dispose());
    }
  });

/** The pale green, see-through glow every ghost is made of. */
function ghostly(color = 0xaaffd8) {
  return new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
}

function box(w: number, h: number, d: number, mat: THREE.Material, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  return m;
}

export interface GhostView {
  set(x: number, y: number, z: number, heading: number, alpha: number, t: number): void;
  dispose(): void;
}

/** A ghost of the given look, standing on (x, y, z), facing `heading`. */
export function createGhostView(parent: THREE.Object3D, look: GhostLook, scale = 1): GhostView {
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  root.scale.setScalar(scale);
  const mats: { m: THREE.MeshBasicMaterial; k: number }[] = [];
  const glow = (k = 1, color?: number) => {
    const m = ghostly(color);
    mats.push({ m, k });
    return m;
  };
  if (look === "float") {
    // A sheet-like spirit: a rounded hood flaring to a ragged hem, two hollow eyes,
    // little arms held out.
    const prof = [
      [0.0, 2.1],
      [0.28, 2.04],
      [0.46, 1.84],
      [0.52, 1.5],
      [0.56, 1.0],
      [0.66, 0.5],
      [0.8, 0.12],
    ].map(([x, y]) => new THREE.Vector2(x, y));
    const g = new THREE.LatheGeometry(prof, 14);
    const pos = g.attributes.position!;
    for (let i = 0; i < pos.count; i++)
      if (pos.getY(i) < 0.2) {
        const a = Math.atan2(pos.getZ(i), pos.getX(i));
        pos.setY(i, pos.getY(i) + 0.14 * Math.sin(a * 7));
      }
    body.add(new THREE.Mesh(g, glow(0.6)));
    for (const s of [-1, 1]) {
      const arm = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.7, 5), glow(0.5));
      arm.position.set(s * 0.6, 1.25, 0.15);
      arm.rotation.z = s * 1.9;
      body.add(arm);
    }
    const eyes = new THREE.MeshBasicMaterial({ color: 0x041810, transparent: true, opacity: 0 });
    mats.push({ m: eyes, k: 0.9 });
    for (const s of [-1, 1]) {
      const e = new THREE.Mesh(new THREE.SphereGeometry(0.08, 6, 4), eyes);
      e.scale.set(1, 1.6, 0.5);
      e.position.set(s * 0.16, 1.6, 0.49);
      body.add(e);
    }
  } else if (look === "window") {
    // A figure standing at the window: shoulders, a head, a broad-brimmed hat.
    const m = glow(0.7);
    const s = new THREE.Shape();
    s.moveTo(-0.62, 0);
    s.lineTo(0.62, 0);
    s.quadraticCurveTo(0.66, 0.7, 0.2, 0.86);
    s.lineTo(0.12, 0.98);
    s.lineTo(-0.12, 0.98);
    s.lineTo(-0.2, 0.86);
    s.quadraticCurveTo(-0.66, 0.7, -0.62, 0);
    body.add(new THREE.Mesh(new THREE.ShapeGeometry(s), m));
    const head = new THREE.Mesh(new THREE.CircleGeometry(0.22, 12), m);
    head.position.set(0, 1.18, 0);
    body.add(head);
    body.add(box(0.95, 0.07, 0.01, m, 0, 1.36, 0));
    body.add(box(0.42, 0.26, 0.01, m, 0, 1.5, 0));
  } else if (look === "miner") {
    // A miner who never came out: legs, a coat, a helmet with its lamp still lit, a
    // pickaxe over one shoulder.
    const m = glow(0.5);
    for (const s of [-1, 1]) body.add(box(0.22, 0.85, 0.26, m, s * 0.15, 0.43, 0));
    body.add(box(0.62, 0.8, 0.36, m, 0, 1.25, 0));
    for (const s of [-1, 1]) {
      const arm = box(0.16, 0.7, 0.18, m, s * 0.42, 1.25, 0);
      arm.rotation.z = s * 0.15;
      body.add(arm);
    }
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 6), m);
    head.position.set(0, 1.85, 0);
    body.add(head);
    const helm = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.3, 0.12, 10), m);
    helm.position.set(0, 2.02, 0);
    body.add(helm);
    const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.07, 6, 4), glow(1.2, 0xfff0b0));
    lamp.position.set(0, 2.02, 0.28);
    body.add(lamp);
    const pick = new THREE.Group();
    pick.add(box(0.06, 1.2, 0.06, m));
    pick.add(box(0.7, 0.08, 0.08, m, 0, 0.6, 0));
    pick.position.set(0.35, 1.7, -0.1);
    pick.rotation.z = -0.9;
    body.add(pick);
  } else {
    // The shadow: a huge dark miner on the wall, pick raised, a halo of green round it.
    const dark = new THREE.MeshBasicMaterial({
      color: 0x040208,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    mats.push({ m: dark, k: 0.8 });
    const halo = glow(0.35, 0x44ffa0);
    const rim = new THREE.Mesh(new THREE.CircleGeometry(2.4, 24), halo);
    rim.position.set(0, 1.8, -0.05);
    rim.scale.set(0.9, 1.15, 1);
    body.add(rim);
    const s = new THREE.Shape();
    s.moveTo(-0.5, 0);
    s.lineTo(-0.15, 0);
    s.lineTo(0, 0.7);
    s.lineTo(0.15, 0);
    s.lineTo(0.5, 0);
    s.lineTo(0.42, 1.6);
    s.lineTo(0.95, 2.5);
    s.lineTo(0.8, 2.6);
    s.lineTo(0.3, 1.95);
    s.lineTo(0.18, 2.1);
    s.lineTo(-0.18, 2.1);
    s.lineTo(-0.5, 1.55);
    s.lineTo(-0.5, 0);
    body.add(new THREE.Mesh(new THREE.ShapeGeometry(s), dark));
    const head = new THREE.Mesh(new THREE.CircleGeometry(0.26, 12), dark);
    head.position.set(0, 2.32, 0);
    body.add(head);
    body.add(box(0.75, 0.12, 0.01, dark, 0, 2.52, 0));
    const pick = new THREE.Group();
    pick.add(box(0.08, 1.4, 0.01, dark, 0, 0.7, 0));
    pick.add(box(1.1, 0.14, 0.01, dark, 0, 1.4, 0));
    pick.position.set(0.88, 2.5, 0);
    pick.rotation.z = -0.5;
    body.add(pick);
  }
  root.visible = false;
  parent.add(root);
  return {
    set(x, y, z, heading, alpha, t) {
      root.visible = alpha > 0.01;
      if (!root.visible) return;
      root.position.set(x, y, z);
      root.rotation.y = heading;
      for (const { m, k } of mats)
        m.opacity = Math.min(1, alpha * k * (0.85 + 0.15 * Math.sin(t * 7.3)));
      if (look === "float") {
        body.rotation.z = 0.08 * Math.sin(t * 1.3);
        body.scale.y = 1 + 0.05 * Math.sin(t * 2.1);
      } else if (look === "miner") {
        body.rotation.y = 0.15 * Math.sin(t * 0.7);
      } else if (look === "shadow") {
        body.scale.setScalar(0.92 + 0.08 * alpha);
      }
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}

export interface RiderView {
  set(x: number, y: number, z: number, heading: number, alpha: number, t: number): void;
  dispose(): void;
}

/** The ghost rider: a horse at full gallop (legs swinging, head nodding, tail
 * streaming) and the cowboy on it, hat and all, every bit of them glowing pale green. */
export function createRiderView(parent: THREE.Object3D): RiderView {
  const root = new THREE.Group();
  const m = ghostly();
  const horse = new THREE.Group();
  root.add(horse);
  horse.add(box(0.9, 0.95, 2.3, m, 0, 1.75, 0));
  const neck = box(0.5, 1.1, 0.6, m, 0, 2.35, 1.1);
  neck.rotation.x = 0.6;
  horse.add(neck);
  const head = box(0.4, 0.42, 0.95, m, 0, 2.85, 1.65);
  head.rotation.x = 0.35;
  horse.add(head);
  const tail = box(0.18, 0.18, 1.1, m, 0, 1.95, -1.55);
  tail.rotation.x = -0.6;
  horse.add(tail);
  const legs: THREE.Group[] = [];
  for (const [x, z] of [
    [-0.3, 0.85],
    [0.3, 0.85],
    [-0.3, -0.85],
    [0.3, -0.85],
  ] as const) {
    const leg = new THREE.Group();
    leg.position.set(x, 1.4, z);
    leg.add(box(0.2, 1.4, 0.22, m, 0, -0.7, 0));
    horse.add(leg);
    legs.push(leg);
  }
  const rider = new THREE.Group();
  rider.position.set(0, 2.25, 0.1);
  rider.add(box(0.55, 0.85, 0.35, m, 0, 0.55, 0));
  const rh = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 6), m);
  rh.position.set(0, 1.15, 0.05);
  rider.add(rh);
  const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.05, 12), m);
  brim.position.set(0, 1.32, 0.05);
  rider.add(brim);
  const crown = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.25, 0.3, 10), m);
  crown.position.set(0, 1.48, 0.05);
  rider.add(crown);
  for (const s of [-1, 1]) {
    const arm = box(0.14, 0.6, 0.14, m, s * 0.35, 0.55, 0.25);
    arm.rotation.x = -0.9;
    rider.add(arm);
    const leg = box(0.16, 0.7, 0.16, m, s * 0.42, 0.0, 0.1);
    leg.rotation.z = s * 0.4;
    rider.add(leg);
  }
  horse.add(rider);
  root.scale.setScalar(1.6);
  root.visible = false;
  parent.add(root);
  return {
    set(x, y, z, heading, alpha, t) {
      root.visible = alpha > 0.01;
      if (!root.visible) return;
      root.position.set(x, y, z);
      root.rotation.y = heading;
      m.opacity = 0.7 * alpha * (0.85 + 0.15 * Math.sin(t * 9));
      const g = t * 9.5;
      legs.forEach((l, k) => {
        l.rotation.x = 0.8 * Math.sin(g + (k < 2 ? 0 : Math.PI) + (k % 2) * 0.5);
      });
      horse.position.y = 0.18 * Math.abs(Math.sin(g));
      horse.rotation.x = 0.06 * Math.sin(g);
      tail.rotation.x = -0.6 + 0.2 * Math.sin(g * 0.5);
      rider.position.y = 2.25 + 0.08 * Math.sin(g + 0.8);
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}

export interface CartView {
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    run: number,
    shown: boolean,
    glow: number,
    t: number,
  ): void;
  dispose(): void;
}

/** An ore cart on its little iron wheels, heaped with ore; `glow` lights the ore and a
 * spectral sheen round the cart (the runaway's warning). */
export function createCartView(parent: THREE.Object3D): CartView {
  const root = new THREE.Group();
  const iron = new THREE.MeshLambertMaterial({ color: 0x4a3a34, flatShading: true });
  const dark = new THREE.MeshLambertMaterial({ color: 0x1e1a1c, flatShading: true });
  const hull = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 0.95, 1.0, 4, 1), iron);
  hull.rotation.y = Math.PI / 4;
  hull.scale.set(1.0, 1.0, 0.7);
  hull.position.y = 0.95;
  root.add(hull);
  const wheels: THREE.Mesh[] = [];
  for (const [x, z] of [
    [-0.55, 0.62],
    [0.55, 0.62],
    [-0.55, -0.62],
    [0.55, -0.62],
  ] as const) {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.12, 8), dark);
    w.rotation.x = Math.PI / 2;
    w.position.set(z, 0.28, x);
    root.add(w);
    wheels.push(w);
  }
  const oreMat = new THREE.MeshBasicMaterial({ color: 0x2a6a4a });
  const ore = new THREE.Mesh(new THREE.SphereGeometry(0.8, 8, 5), oreMat);
  ore.scale.set(1.2, 0.4, 0.8);
  ore.position.y = 1.4;
  root.add(ore);
  const aura = ghostly(0x44ffa0);
  const sheen = new THREE.Mesh(new THREE.SphereGeometry(1.6, 12, 8), aura);
  sheen.scale.set(1.3, 0.9, 1.0);
  sheen.position.y = 1.0;
  root.add(sheen);
  const base = new THREE.Color(0x2a6a4a);
  const hot = new THREE.Color(0x9affd0);
  root.visible = false;
  parent.add(root);
  return {
    update(x, y, z, heading, run, shown, glow, t) {
      root.visible = shown;
      if (!shown) return;
      root.position.set(x, y, z);
      // Along its heading (the cart's long side is local X).
      root.rotation.y = heading - Math.PI / 2;
      for (const w of wheels) w.rotation.y = -run / 0.28;
      root.rotation.z = 0.03 * Math.sin(t * 23) * Math.min(1, glow + 0.2);
      oreMat.color.copy(base).lerp(hot, glow * (0.7 + 0.3 * Math.sin(t * 11)));
      aura.opacity = 0.22 * glow;
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}

export interface TumbleweedView {
  update(x: number, y: number, z: number, heading: number, run: number, shown: boolean): void;
  dispose(): void;
}

/** A tumbleweed: a loose ball of thin dry twigs, rolling. */
export function createTumbleweedView(parent: THREE.Object3D, r: number): TumbleweedView {
  const root = new THREE.Group();
  const ball = new THREE.Group();
  root.add(ball);
  const mat = new THREE.LineBasicMaterial({ color: 0x8a6a4a });
  const ico = new THREE.IcosahedronGeometry(r, 1);
  ball.add(new THREE.LineSegments(new THREE.EdgesGeometry(ico), mat));
  ico.dispose();
  const twigs: number[] = [];
  for (let k = 0; k < 24; k++) {
    const a = k * 2.39996;
    const b = Math.acos(1 - (2 * (k + 0.5)) / 24);
    const p = new THREE.Vector3(Math.sin(b) * Math.cos(a), Math.cos(b), Math.sin(b) * Math.sin(a));
    const q = new THREE.Vector3(
      Math.sin(b + 1.9) * Math.cos(a + 2.4),
      Math.cos(b + 1.9),
      Math.sin(b + 1.9) * Math.sin(a + 2.4),
    );
    twigs.push(p.x * r, p.y * r, p.z * r, q.x * r * 0.8, q.y * r * 0.8, q.z * r * 0.8);
  }
  const tg = new THREE.BufferGeometry();
  tg.setAttribute("position", new THREE.Float32BufferAttribute(twigs, 3));
  ball.add(new THREE.LineSegments(tg, mat));
  root.visible = false;
  parent.add(root);
  return {
    update(x, y, z, heading, run, shown) {
      root.visible = shown;
      if (!shown) return;
      root.position.set(x, y + r + Math.abs(Math.sin(run * 0.45)) * r * 1.4, z);
      root.rotation.y = heading;
      ball.rotation.x = run / r;
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}

export interface DoorView {
  update(angle: number): void;
  dispose(): void;
}

/** The saloon's swinging doors: two slatted half-height leaves on spring hinges. */
export function createDoorView(
  parent: THREE.Object3D,
  x: number,
  y: number,
  z: number,
  heading: number,
  width: number,
): DoorView {
  const root = new THREE.Group();
  root.position.set(x, y, z);
  root.rotation.y = heading;
  const mat = new THREE.MeshLambertMaterial({ color: 0x6a4428, flatShading: true });
  const leaves: THREE.Group[] = [];
  for (const s of [-1, 1]) {
    const hinge = new THREE.Group();
    hinge.position.set(s * width * 0.5, 0, 0);
    const leaf = new THREE.Mesh(new THREE.BoxGeometry(width * 0.48, 1.35, 0.06), mat);
    leaf.position.set(-s * width * 0.25, 1.35, 0);
    hinge.add(leaf);
    root.add(hinge);
    leaves.push(hinge);
  }
  parent.add(root);
  return {
    update(angle) {
      leaves[0]!.rotation.y = angle;
      leaves[1]!.rotation.y = -angle;
    },
    dispose() {
      root.removeFromParent();
      disposeAll(root);
    },
  };
}

export interface WispsView {
  update(t: number): void;
  dispose(): void;
}

/** A drift of little green lights (each wandering on its own path, brightening and
 * dimming). */
export function createWispsView(parent: THREE.Object3D, w: WispsConfig): WispsView {
  const n = w.count;
  const pos = new Float32Array(n * 3);
  const col = new Float32Array(n * 3);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.BufferAttribute(col, 3));
  // A soft round glow for each.
  const cv = document.createElement("canvas");
  cv.width = cv.height = 32;
  const cg = cv.getContext("2d")!;
  const grad = cg.createRadialGradient(16, 16, 0, 16, 16, 16);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.3, "rgba(255,255,255,0.6)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  cg.fillStyle = grad;
  cg.fillRect(0, 0, 32, 32);
  const tex = new THREE.CanvasTexture(cv);
  const m = new THREE.PointsMaterial({
    size: 1.4,
    map: tex,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const pts = new THREE.Points(g, m);
  pts.frustumCulled = false;
  parent.add(pts);
  return {
    update(t) {
      for (let k = 0; k < n; k++) {
        const p = wispAt(w, k, t);
        pos[k * 3] = p.x;
        pos[k * 3 + 1] = p.y;
        pos[k * 3 + 2] = p.z;
        col[k * 3] = 0.35 * p.glow;
        col[k * 3 + 1] = 1.0 * p.glow;
        col[k * 3 + 2] = 0.6 * p.glow;
      }
      g.attributes.position!.needsUpdate = true;
      g.attributes.color!.needsUpdate = true;
    },
    dispose() {
      pts.removeFromParent();
      g.dispose();
      m.dispose();
      tex.dispose();
    },
  };
}
