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

/** old; glowing (an old stone lit up: the hundredth summer); cracked; new (Lumen's light);
 * broken. */
export type StoneState = "old" | "glowing" | "cracked" | "new" | "broken";

/** A rounded-off box (bevelled on every edge), centred on the origin. */
function bevelBox(w: number, h: number, d: number, r: number) {
  const sh = new THREE.Shape();
  const x = w / 2 - r;
  const y = h / 2 - r;
  sh.moveTo(-x, -h / 2);
  sh.lineTo(x, -h / 2);
  sh.quadraticCurveTo(w / 2, -h / 2, w / 2, -y);
  sh.lineTo(w / 2, y);
  sh.quadraticCurveTo(w / 2, h / 2, x, h / 2);
  sh.lineTo(-x, h / 2);
  sh.quadraticCurveTo(-w / 2, h / 2, -w / 2, y);
  sh.lineTo(-w / 2, -y);
  sh.quadraticCurveTo(-w / 2, -h / 2, -x, -h / 2);
  const g = new THREE.ExtrudeGeometry(sh, {
    depth: d - r * 2,
    bevelEnabled: true,
    bevelSize: r,
    bevelThickness: r,
    bevelSegments: 2,
    curveSegments: 2,
  });
  g.translate(0, 0, -(d - r * 2) / 2);
  return g;
}

/** The standing stone's face: wide at the foot, narrowing to its shoulders, then a
 * pointed arch; `from`..`to` cuts a band of it (the broken stone's pieces). */
function stoneOutline(from = 0, to = 1) {
  const H = 4.4;
  const half = (y: number) => {
    // (Half-width at height y: the taper, then the arch.)
    if (y <= 3.2) return 0.86 - (y / 3.2) * 0.2;
    const k = (y - 3.2) / (H - 3.2);
    return 0.66 * Math.sqrt(Math.max(0, 1 - k * k * 0.96)) * (1 - k * 0.35);
  };
  const y0 = from * H;
  const y1 = to * H;
  const n = 14;
  const sh = new THREE.Shape();
  const ys = Array.from({ length: n + 1 }, (_, i) => y0 + ((y1 - y0) * i) / n);
  // (A jagged edge where it broke.)
  const jag = (y: number, i: number) => y + (i % 2 ? 0.12 : -0.1);
  sh.moveTo(-half(y0), y0);
  if (from > 0)
    for (let i = 1; i < 6; i++) sh.lineTo(-half(y0) + (i / 6) * 2 * half(y0), jag(y0, i));
  sh.lineTo(half(y0), y0);
  for (const y of ys.slice(1)) sh.lineTo(half(y), y);
  if (to < 1) for (let i = 5; i > 0; i--) sh.lineTo(-half(y1) + (i / 6) * 2 * half(y1), jag(y1, i));
  for (const y of ys.slice(0, -1).reverse()) sh.lineTo(-half(y), y);
  return sh;
}

function stoneSlab(from = 0, to = 1) {
  const g = new THREE.ExtrudeGeometry(stoneOutline(from, to), {
    depth: 0.5,
    bevelEnabled: true,
    bevelSize: 0.07,
    bevelThickness: 0.07,
    bevelSegments: 1,
    curveSegments: 4,
  });
  g.translate(0, 0, -0.25);
  // Weathered: every corner nudged a little (the same nudge for the same point).
  const p = g.getAttribute("position") as THREE.BufferAttribute;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i);
    const y = p.getY(i);
    const z = p.getZ(i);
    const n = Math.sin(x * 17.1 + y * 9.3) * Math.cos(y * 13.7 - z * 7.9);
    p.setXYZ(i, x + n * 0.035, y, z + n * 0.03);
  }
  g.computeVertexNormals();
  return g;
}

/** The Pact's sign, inlaid on every stone's face: a ring, a dragon's wing on its left
 * and a wheel on its right (both sides, one oath). Faces +z; `r` its radius. */
function pactSign(k: ReturnType<typeof kit>, m: THREE.Material, r: number) {
  const g = new THREE.Group();
  const ring = k.mesh(new THREE.TorusGeometry(r, r * 0.09, 4, 24), m);
  g.add(ring);
  // The wing: three fingers fanning up and out, a membrane between.
  const wing = new THREE.Shape();
  wing.moveTo(-r * 0.08, -r * 0.5);
  wing.lineTo(-r * 0.12, r * 0.62);
  wing.lineTo(-r * 0.34, r * 0.18);
  wing.lineTo(-r * 0.56, r * 0.4);
  wing.lineTo(-r * 0.6, -r * 0.02);
  wing.lineTo(-r * 0.78, r * 0.06);
  wing.lineTo(-r * 0.5, -r * 0.42);
  wing.lineTo(-r * 0.08, -r * 0.5);
  const w = k.mesh(new THREE.ExtrudeGeometry(wing, { depth: 0.04, bevelEnabled: false }), m);
  g.add(w);
  // The wheel: a rim, a hub and five spokes.
  const rim = k.mesh(new THREE.TorusGeometry(r * 0.36, r * 0.07, 4, 16), m);
  rim.position.x = r * 0.42;
  const hub = k.mesh(new THREE.CylinderGeometry(r * 0.09, r * 0.09, 0.05, 8), m);
  hub.rotation.x = Math.PI / 2;
  hub.position.x = r * 0.42;
  g.add(rim, hub);
  for (let s = 0; s < 5; s++) {
    const sp = k.mesh(new THREE.BoxGeometry(r * 0.05, r * 0.34, 0.04), m);
    const a = (s / 5) * Math.PI * 2;
    sp.position.set(r * 0.42 + Math.sin(a) * r * 0.17, Math.cos(a) * r * 0.17, 0);
    sp.rotation.z = -a;
    g.add(sp);
  }
  return g;
}

/** A Pact Stone: a weathered standing stone with a pointed-arch top on a stepped plinth,
 * the Pact's sign (a ring holding a dragon's wing and a wheel) inlaid near the top and
 * three rows of oath-runes under it. Old (grey, the inlay dull gold), cracked (a hot crack
 * down its face), new (pale and glowing with Lumen's light), broken (the stump on its
 * plinth, two pieces fallen beside it). `big`: the Heart Stone, which also carries a
 * crystal heart set in its arch and a deeper plinth. */
export function createPactStoneView(
  parent: THREE.Object3D,
  state: StoneState,
  big = false,
): PropView {
  const k = kit(parent, `Pact Stone (${state})`);
  const fresh = state === "new";
  const rock = k.mat(fresh ? "#e8dcb8" : "#8a8476");
  const rock2 = k.mat(fresh ? "#d4c69c" : "#6e695e");
  const dark = k.mat(fresh ? "#a89870" : "#56514a");
  const mossy = k.mat("#5a7a3a");
  const inlay = k.mat(
    fresh || state === "glowing" ? "#ffe08a" : state === "cracked" ? "#8a7a58" : "#c8a24a",
    fresh || state === "glowing" ? 1.3 : state === "cracked" ? 0 : 0.35,
  );
  const crack = k.mat("#ff7a30", 1.4);
  const inner = new THREE.Group();
  inner.scale.setScalar(big ? 2.2 : 1);
  k.root.add(inner);
  // The plinth: two steps (three for the Heart Stone).
  const steps: [number, number, number][] = big
    ? [
        [3.2, 0.32, 2.0],
        [2.6, 0.3, 1.6],
        [2.1, 0.26, 1.2],
      ]
    : [
        [2.6, 0.32, 1.5],
        [2.0, 0.28, 1.1],
      ];
  let top = 0;
  steps.forEach(([w, h, d], i) => {
    const s = k.mesh(bevelBox(w, h, d, 0.06), i % 2 ? rock2 : dark);
    s.position.y = top + h / 2;
    inner.add(s);
    top += h;
  });
  // Moss and fallen chips round the foot.
  for (let i = 0; i < 7; i++) {
    const a = i * 2.39;
    const m = k.mesh(
      new THREE.IcosahedronGeometry(0.16 + (i % 3) * 0.05, 0),
      i % 3 ? mossy : rock2,
    );
    m.scale.set(1.4, 0.45, 1.1);
    m.position.set(Math.cos(a) * (1.2 + (i % 2) * 0.2), 0.06, Math.sin(a) * 0.75);
    inner.add(m);
  }
  const face = (into: THREE.Object3D, y0: number) => {
    // The Pact's sign under the arch, the runes below it.
    const sign = pactSign(k, inlay, 0.36);
    sign.position.set(0, y0 + 3.15, 0.31);
    into.add(sign);
    for (let r = 0; r < 3; r++)
      for (let c = 0; c < 5; c++) {
        const tall = (r + c) % 3 === 0;
        const g = k.mesh(new THREE.BoxGeometry(0.07, tall ? 0.26 : 0.18, 0.04), inlay);
        g.position.set(-0.4 + c * 0.2, y0 + 2.2 - r * 0.42, 0.3);
        g.rotation.z = ((r * 5 + c) % 4) * 0.35 - 0.5;
        into.add(g);
        const bar = k.mesh(new THREE.BoxGeometry(0.12, 0.05, 0.04), inlay);
        bar.position.set(-0.36 + c * 0.2, y0 + 2.08 - r * 0.42, 0.3);
        into.add(bar);
      }
    // Two carved bands round it.
    for (const y of [1.0, 2.62]) {
      const b = k.mesh(new THREE.BoxGeometry(1.62 - y * 0.12, 0.06, 0.66), rock2);
      b.position.y = y0 + y;
      into.add(b);
    }
  };
  if (state === "broken") {
    const stump = k.mesh(stoneSlab(0, 0.36), rock);
    stump.position.y = top;
    const a = k.mesh(stoneSlab(0.36, 0.7), rock);
    a.position.set(-1.8, 0.3, 0.8);
    a.rotation.set(-Math.PI / 2 + 0.15, 0, 0.9);
    const b = k.mesh(stoneSlab(0.7, 1), rock2);
    b.position.set(1.6, 0.25, -0.6);
    b.rotation.set(-Math.PI / 2 - 0.1, 0, -2.4);
    inner.add(stump, a, b);
  } else {
    const slab = k.mesh(stoneSlab(), rock);
    slab.position.y = top;
    inner.add(slab);
    face(inner, top);
    if (big) {
      // The crystal heart, set in the arch.
      const heart = k.mesh(
        new THREE.OctahedronGeometry(0.34, 0),
        k.mat(fresh ? "#fff0b0" : "#e0a040", fresh ? 1.6 : 0.6),
      );
      heart.scale.set(0.8, 1.2, 0.5);
      heart.position.set(0, top + 3.95, 0.3);
      inner.add(heart);
    }
    if (state === "cracked") {
      // A jagged crack down the face, glowing hot.
      let y = top + 4.1;
      let x = 0.1;
      for (let s = 0; s < 7; s++) {
        const len = 0.52;
        const g = k.mesh(new THREE.BoxGeometry(0.07, len, 0.05), crack);
        const nx = x + (s % 2 ? 0.18 : -0.2);
        g.position.set((x + nx) / 2, y - len / 2, 0.33);
        g.rotation.z = Math.atan2(nx - x, len);
        inner.add(g);
        x = nx;
        y -= len;
      }
    }
  }
  const glow =
    fresh || state === "cracked" || state === "glowing"
      ? glowSprite(
          fresh || state === "glowing" ? "rgba(255,226,140,0.9)" : "rgba(255,120,40,0.5)",
          fresh || state === "glowing" ? 7 : 3,
        )
      : undefined;
  if (glow) {
    glow.sprite.position.y = 2.6;
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
