/**
 * The story's own things in the 3D world (the staged scenes, src/adventure/staged.ts;
 * the overworld): Lumen in his robe (Blake, Oct 27: a robed, hooded figure, his wings
 * hidden under it), the Pact Stones (old, cracked, new and glowing, broken), the dragons'
 * banners over a conquered kingdom. Flat-shaded low-poly, like everything else.
 */
import * as THREE from "three";

export interface PropView {
  readonly root: THREE.Group;
  /** Place it (`t` seconds, for the glow and the robe's sway). */
  update(x: number, y: number, z: number, heading: number, t: number, walk?: number): void;
  dispose(): void;
}

function kit(parent: THREE.Object3D, name: string) {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const root = new THREE.Group();
  root.name = name;
  parent.add(root);
  const mat = (color: string, glow = 0) => {
    const m = new THREE.MeshLambertMaterial({
      color,
      flatShading: true,
      ...(glow ? { emissive: new THREE.Color(color), emissiveIntensity: glow } : {}),
    });
    mats.push(m);
    return m;
  };
  const mesh = (g: THREE.BufferGeometry, m: THREE.Material) => {
    geos.push(g);
    return new THREE.Mesh(g, m);
  };
  const dispose = () => {
    parent.remove(root);
    for (const m of mats) {
      (m as THREE.SpriteMaterial).map?.dispose();
      m.dispose();
    }
    for (const g of geos) g.dispose();
  };
  return { root, mat, mesh, mats, dispose };
}

/** A soft glow sprite (a radial gradient), for the stones' light. */
function glowSprite(color: string, size: number) {
  const cv = document.createElement("canvas");
  cv.width = cv.height = 64;
  const g = cv.getContext("2d")!;
  const grad = g.createRadialGradient(32, 32, 2, 32, 32, 32);
  grad.addColorStop(0, color);
  grad.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  const m = new THREE.SpriteMaterial({
    map: new THREE.CanvasTexture(cv),
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const s = new THREE.Sprite(m);
  s.scale.setScalar(size);
  return { sprite: s, material: m };
}

/** Lumen in his robe: a long hooded cloak, a dark face with two gold eyes, the hump of
 * folded wings under it. About as tall as a villager. */
export function createRobedView(parent: THREE.Object3D): PropView {
  const k = kit(parent, "Lumen (robed)");
  const cloth = k.mat("#8a6a48");
  const trim = k.mat("#e0c890");
  const shade = k.mat("#120c08");
  const eye = k.mat("#ffd860", 1.6);
  const body = new THREE.Group();
  k.root.add(body);
  // The robe: a cone, flaring to the ground.
  const robe = k.mesh(new THREE.ConeGeometry(0.62, 1.7, 8, 1, true), cloth);
  robe.position.y = 0.85;
  const hem = k.mesh(new THREE.TorusGeometry(0.6, 0.05, 4, 10), trim);
  hem.rotation.x = Math.PI / 2;
  hem.position.y = 0.06;
  // Folded wings under it: a hump on the back.
  const hump = k.mesh(new THREE.IcosahedronGeometry(0.42, 0), cloth);
  hump.scale.set(1.2, 0.9, 0.7);
  hump.position.set(0, 1.25, -0.24);
  // The hood, its dark opening and the eyes in it.
  const hood = k.mesh(new THREE.IcosahedronGeometry(0.36, 1), cloth);
  hood.scale.set(1, 1.15, 1.05);
  hood.position.set(0, 1.86, 0.02);
  const face = k.mesh(new THREE.IcosahedronGeometry(0.24, 1), shade);
  face.scale.set(1, 1.05, 0.6);
  face.position.set(0, 1.8, 0.2);
  const eyes = [-1, 1].map((sd) => {
    const e = k.mesh(new THREE.IcosahedronGeometry(0.045, 0), eye);
    e.position.set(sd * 0.08, 1.84, 0.33);
    return e;
  });
  // Sleeves, hands hidden in them.
  const sleeves = [-1, 1].map((sd) => {
    const s = k.mesh(new THREE.CylinderGeometry(0.12, 0.17, 0.62, 6), cloth);
    s.position.set(sd * 0.36, 1.28, 0.14);
    s.rotation.set(-0.7, 0, sd * 0.25);
    return s;
  });
  body.add(robe, hem, hump, hood, face, ...eyes, ...sleeves);
  const shadow = k.mesh(
    new THREE.CircleGeometry(0.6, 12),
    new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.25, depthWrite: false }),
  );
  k.mats.push(shadow.material as THREE.Material);
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = 0.04;
  k.root.add(shadow);
  return {
    root: k.root,
    update(x, y, z, heading, t, walk = 0) {
      k.root.position.set(x, y, z);
      k.root.rotation.y = heading;
      body.rotation.z = Math.sin(t * 1.3) * 0.02 + Math.sin(t * 7) * 0.04 * walk;
      body.position.y = Math.abs(Math.sin(t * 7)) * 0.05 * walk;
    },
    dispose: k.dispose,
  };
}

export type StoneState = "old" | "cracked" | "new" | "broken";

/** A Pact Stone: a tall carved slab on a plinth. Old (faint glyphs), cracked (a hot crack
 * down it), new (glowing gold with Lumen's light), broken (in pieces round its plinth).
 * `big`: the Heart Stone. */
export function createPactStoneView(
  parent: THREE.Object3D,
  state: StoneState,
  big = false,
): PropView {
  const k = kit(parent, `Pact Stone (${state})`);
  const fresh = state === "new";
  const rock = k.mat(fresh ? "#e8dcb8" : "#7a7468");
  const dark = k.mat("#4a463e");
  const glyph = k.mat(
    fresh ? "#ffe08a" : state === "cracked" ? "#7a7468" : "#a8a090",
    fresh ? 1.2 : 0,
  );
  const crack = k.mat("#ff7a30", 1.4);
  const inner = new THREE.Group();
  inner.scale.setScalar(big ? 2.2 : 1);
  k.root.add(inner);
  const plinth = k.mesh(new THREE.BoxGeometry(2.4, 0.5, 1.4), dark);
  plinth.position.y = 0.25;
  inner.add(plinth);
  const glyphs = (into: THREE.Object3D, h: number) => {
    for (let r = 0; r < 4; r++)
      for (let c = 0; c < 2; c++) {
        const g = k.mesh(new THREE.BoxGeometry(0.42, 0.08, 0.04), glyph);
        g.position.set(-0.28 + c * 0.56, 0.9 + r * (h / 5), 0.31);
        into.add(g);
      }
  };
  if (state === "broken") {
    // Three chunks: the stump on the plinth, two fallen beside it.
    const stump = k.mesh(new THREE.BoxGeometry(1.5, 1.2, 0.6), rock);
    stump.position.set(0, 1.1, 0);
    stump.rotation.z = 0.08;
    const a = k.mesh(new THREE.BoxGeometry(1.5, 1.3, 0.6), rock);
    a.position.set(-1.6, 0.4, 0.6);
    a.rotation.set(1.3, 0.4, 0.3);
    const b = k.mesh(new THREE.BoxGeometry(1.2, 1.0, 0.6), rock);
    b.position.set(1.5, 0.35, -0.4);
    b.rotation.set(-1.2, -0.6, 0.2);
    inner.add(stump, a, b);
  } else {
    const slab = k.mesh(new THREE.BoxGeometry(1.5, 3.4, 0.6), rock);
    slab.position.y = 2.2;
    const cap = k.mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.6, 8, 1, false, 0, Math.PI), rock);
    cap.rotation.set(Math.PI / 2, 0, Math.PI / 2);
    cap.position.y = 3.9;
    inner.add(slab, cap);
    glyphs(inner, 3.2);
    if (state === "cracked") {
      // A jagged crack down the face, glowing hot.
      let y = 3.8;
      let x = 0.1;
      for (let s = 0; s < 6; s++) {
        const len = 0.55;
        const g = k.mesh(new THREE.BoxGeometry(0.07, len, 0.05), crack);
        const nx = x + (s % 2 ? 0.18 : -0.2);
        g.position.set((x + nx) / 2, y - len / 2, 0.32);
        g.rotation.z = Math.atan2(nx - x, len);
        inner.add(g);
        x = nx;
        y -= len;
      }
    }
  }
  const glow =
    fresh || state === "cracked"
      ? glowSprite(fresh ? "rgba(255,226,140,0.9)" : "rgba(255,120,40,0.5)", fresh ? 7 : 3)
      : undefined;
  if (glow) {
    glow.sprite.position.y = 2.4;
    inner.add(glow.sprite);
    k.mats.push(glow.material);
  }
  return {
    root: k.root,
    update(x, y, z, heading, t) {
      k.root.position.set(x, y, z);
      k.root.rotation.y = heading;
      if (glow) glow.sprite.material.opacity = 0.75 + 0.25 * Math.sin(t * 2.2);
    },
    dispose: k.dispose,
  };
}

/** A dragon's banner on a tall pole (a conquered kingdom): a dark cloth with a pale claw
 * mark, in the dragon's colour. */
export function createBannerView(parent: THREE.Object3D, color: string): PropView {
  const k = kit(parent, "Dragon Banner");
  const pole = k.mesh(new THREE.CylinderGeometry(0.12, 0.16, 9, 6), k.mat("#3a2a1a"));
  pole.position.y = 4.5;
  const cv = document.createElement("canvas");
  cv.width = 64;
  cv.height = 128;
  const g = cv.getContext("2d")!;
  g.fillStyle = color;
  g.fillRect(0, 0, 64, 128);
  g.fillStyle = "rgba(0,0,0,0.35)";
  g.fillRect(0, 0, 64, 10);
  g.strokeStyle = "#f4e8cc";
  g.lineWidth = 6;
  for (const dx of [-12, 0, 12]) {
    g.beginPath();
    g.moveTo(32 + dx - 6, 34);
    g.lineTo(32 + dx + 6, 84);
    g.stroke();
  }
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  const cloth = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide });
  k.mats.push(cloth);
  const flag = k.mesh(new THREE.PlaneGeometry(1.8, 3.6, 1, 4), cloth);
  flag.position.set(0.95, 6.6, 0);
  const bar = k.mesh(new THREE.BoxGeometry(2.1, 0.12, 0.12), k.mat("#3a2a1a"));
  bar.position.set(0.95, 8.45, 0);
  k.root.add(pole, flag, bar);
  return {
    root: k.root,
    update(x, y, z, heading, t) {
      k.root.position.set(x, y, z);
      k.root.rotation.y = heading;
      flag.rotation.y = Math.sin(t * 1.7 + x) * 0.25;
    },
    dispose: k.dispose,
  };
}
