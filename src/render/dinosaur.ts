/**
 * The friendly long-neck who strolls along the river at Riverbend Palms: an original
 * cartoon sauropod. Its tail, body, neck and head are one smooth skin, lofted round a
 * spine curve and re-bent every frame (the neck sways, the head bobs and turns, the
 * tail swishes), coloured with a cream belly and darker spots along the back. Chunky
 * lathed legs with toenails, big friendly eyes and rosy cheeks.
 *
 * Built in code, about 6k triangles. Purely visual: where it walks, and what it bumps,
 * is game/hazards.ts.
 */
import * as THREE from "three";

export interface DinoView {
  readonly root: THREE.Group;
  /** Place and animate it: walk phase in metres walked, 0..1 walk strength, head turn. */
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    walked: number,
    walking: number,
    look: number,
    t: number,
  ): void;
  dispose(): void;
}

/** The spine at rest: [z, y, half-width, half-height], tail tip to nose (it faces +z). */
const SPINE: [number, number, number, number][] = [
  [-12.6, 1.9, 0, 0],
  [-11.2, 2.3, 0.28, 0.26],
  [-9.0, 3.0, 0.55, 0.52],
  [-6.6, 3.8, 0.95, 0.92],
  [-4.2, 4.5, 1.6, 1.55],
  [-2.0, 4.9, 2.25, 2.05],
  [0.2, 5.05, 2.45, 2.2],
  [2.3, 5.0, 2.1, 1.95],
  [3.9, 5.6, 1.3, 1.3],
  [4.9, 6.9, 0.95, 0.95],
  [5.5, 8.4, 0.76, 0.76],
  [5.9, 9.9, 0.66, 0.66],
  [6.2, 11.1, 0.62, 0.62],
  [6.6, 11.9, 0.78, 0.76],
  [7.4, 12.15, 0.92, 0.8],
  [8.2, 12.0, 0.78, 0.6],
  [8.8, 11.85, 0.48, 0.42],
  [9.05, 11.8, 0, 0],
];
/** Which spine points belong to the tail, the neck and the head. */
const TAIL = 4;
const NECK = 8;
const HEAD = 14;

const RINGS = 110;
const SIDES = 22;

export function createDinoView(parent: THREE.Object3D, scale = 1): DinoView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const mat = (color: string, opts: THREE.MeshLambertMaterialParameters = {}) => {
    const m = new THREE.MeshLambertMaterial({ color, ...opts });
    mats.push(m);
    return m;
  };
  const SKIN = new THREE.Color("#69c46c");
  const BACK = new THREE.Color("#3f9a52");
  const BELLY = new THREE.Color("#f6e8b4");
  const skinMat = mat("#ffffff", { vertexColors: true });
  const legMat = mat("#69c46c");
  const cream = mat("#f6e8b4");
  const white = mat("#ffffff");
  const black = mat("#1d1a18");
  const cheek = mat("#f59a8a");

  const root = new THREE.Group();
  root.name = "dinosaur";
  const body = new THREE.Group();
  root.add(body);

  // ------------------------------------------------------------- the skin
  const n = SPINE.length;
  const pos = new Float32Array((RINGS + 1) * SIDES * 3);
  const col = new Float32Array((RINGS + 1) * SIDES * 3);
  const idx: number[] = [];
  for (let i = 0; i < RINGS; i++)
    for (let k = 0; k < SIDES; k++) {
      const a = i * SIDES + k;
      const b = i * SIDES + ((k + 1) % SIDES);
      idx.push(a, b, a + SIDES, b, b + SIDES, a + SIDES);
    }
  const skinGeo = new THREE.BufferGeometry();
  skinGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  skinGeo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  skinGeo.setIndex(idx);
  geos.push(skinGeo);
  const skin = new THREE.Mesh(skinGeo, skinMat);
  skin.castShadow = true;
  skin.frustumCulled = false;
  body.add(skin);

  const ctrl = SPINE.map(([z, y]) => new THREE.Vector3(0, y, z));
  const curve = new THREE.CatmullRomCurve3(ctrl, false, "catmullrom", 0.5);
  const p = new THREE.Vector3();
  const tan = new THREE.Vector3();
  const side = new THREE.Vector3();
  const up = new THREE.Vector3();
  const X = new THREE.Vector3(1, 0, 0);
  const c = new THREE.Color();
  const smooth = (e: number) => e * e * (3 - 2 * e);
  /** Half-width and half-height at u (0..1 along the spine's control points). */
  const radii = (u: number): [number, number] => {
    const f = u * (n - 1);
    const i = Math.min(n - 2, Math.floor(f));
    const e = smooth(f - i);
    const a = SPINE[i]!;
    const b = SPINE[i + 1]!;
    return [a[2] + (b[2] - a[2]) * e, a[3] + (b[3] - a[3]) * e];
  };
  // Spots: a fixed scatter of soft dark patches along the back (u, angle, size).
  const spots: [number, number, number][] = [
    [0.27, 0.0, 0.035],
    [0.31, 0.5, 0.025],
    [0.33, -0.45, 0.028],
    [0.37, 0.15, 0.03],
    [0.4, -0.6, 0.022],
    [0.41, 0.65, 0.024],
    [0.2, 0.2, 0.025],
    [0.15, -0.2, 0.02],
    [0.5, 0.0, 0.02],
    [0.56, 0.3, 0.015],
  ];
  // Colours depend only on where a vertex sits on the skin, so they're painted once.
  for (let i = 0; i <= RINGS; i++) {
    const u = i / RINGS;
    for (let k = 0; k < SIDES; k++) {
      const a = (k / SIDES) * Math.PI * 2; // 0 = right side, pi/2 = top
      const down = -Math.sin(a);
      c.copy(SKIN).lerp(BELLY, smooth(Math.min(1, Math.max(0, (down - 0.2) / 0.5))));
      const ang = Math.atan2(Math.sin(a), Math.cos(a)) - Math.PI / 2; // 0 on the spine
      let spot = 0;
      for (const [su, sa, sz] of spots) {
        const d = Math.hypot((u - su) / (sz * 1.5), (ang - sa) / (sz * 13));
        spot = Math.max(spot, 1 - smooth(Math.min(1, Math.max(0, (d - 0.6) / 0.4))));
      }
      c.lerp(BACK, spot);
      const o = (i * SIDES + k) * 3;
      col[o] = c.r;
      col[o + 1] = c.g;
      col[o + 2] = c.b;
    }
  }

  // The head's frame, re-placed each frame: eyes, cheeks and nostrils ride on it.
  const head = new THREE.Group();
  head.name = "dinosaur head";
  body.add(head);
  const ball = new THREE.SphereGeometry(1, 20, 14);
  geos.push(ball);
  const add = (
    g: THREE.BufferGeometry,
    m: THREE.Material,
    at: [number, number, number],
    s: [number, number, number],
    to: THREE.Object3D,
  ) => {
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set(...at);
    mesh.scale.set(...s);
    mesh.castShadow = true;
    to.add(mesh);
    return mesh;
  };
  // In the head frame: x to its right, y up, z forward along the snout.
  for (const sd of [-1, 1]) {
    add(ball, white, [sd * 0.6, 0.38, 0.05], [0.34, 0.4, 0.34], head);
    add(ball, black, [sd * 0.78, 0.42, 0.18], [0.17, 0.23, 0.17], head);
    add(ball, white, [sd * 0.88, 0.52, 0.24], [0.06, 0.07, 0.06], head);
    add(ball, cheek, [sd * 0.62, -0.18, 0.55], [0.2, 0.13, 0.16], head);
    add(ball, black, [sd * 0.17, 0.02, 1.45], [0.06, 0.05, 0.05], head);
  }

  // ------------------------------------------------------------- the legs
  const prof: THREE.Vector2[] = [
    [0.0, -4.15],
    [0.86, -4.13],
    [1.0, -3.95],
    [0.98, -3.7],
    [0.8, -3.35],
    [0.7, -2.6],
    [0.72, -1.6],
    [0.86, -0.6],
    [0.95, 0.2],
    [0.6, 0.8],
    [0.0, 0.9],
  ].map(([r, y]) => new THREE.Vector2(r!, y!));
  const legGeo = new THREE.LatheGeometry(prof, 20);
  geos.push(legGeo);
  const legs: THREE.Group[] = [];
  for (const [x, z, s] of [
    [1.45, 1.9, 1.0],
    [-1.45, 1.9, 1.0],
    [1.55, -2.3, 1.12],
    [-1.55, -2.3, 1.12],
  ] as const) {
    const hip = new THREE.Group();
    hip.position.set(x, 4.15, z);
    body.add(hip);
    add(legGeo, legMat, [0, 0, 0], [s, 1, s], hip);
    for (const tx of [-0.42, 0, 0.42])
      add(ball, cream, [tx * s, -3.95, (0.82 - Math.abs(tx) * 0.35) * s], [0.2, 0.17, 0.16], hip);
    legs.push(hip);
  }

  // A soft round shadow on the ground.
  const shadowGeo = new THREE.CircleGeometry(1, 32);
  geos.push(shadowGeo);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.3,
    depthWrite: false,
  });
  mats.push(shadowMat);
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(3.6, 7.5, 1);
  shadow.position.z = -1;
  shadow.renderOrder = 1;
  root.add(shadow);
  root.scale.setScalar(scale);
  parent.add(root);

  const basis = new THREE.Matrix4();
  /** Bend the spine (sway, bob, swish), re-loft the skin and place the head. */
  function bend(t: number, ph: number, walking: number, look: number) {
    SPINE.forEach(([z, y], i) => {
      const v = ctrl[i]!;
      v.set(0, y, z);
      if (i >= NECK) {
        const k = (i - NECK) / (n - 1 - NECK); // 0 at the shoulders, 1 at the nose
        v.x = (Math.sin(t * 0.7 + k * 1.6) * 0.35 + look * 2.2) * k * k;
        v.y += Math.sin(t * 1.3) * 0.25 * k * k + Math.sin(ph * 2) * 0.08 * walking * k;
      } else if (i <= TAIL) {
        const k = (TAIL - i) / TAIL; // 0 at the hips, 1 at the tip
        v.x = Math.sin(t * 1.6 - k * 2.2 + ph * 0.5) * 1.1 * k * k;
        v.y += Math.sin(t * 1.1 + 1) * 0.15 * k;
      }
    });
    curve.updateArcLengths();
    for (let i = 0; i <= RINGS; i++) {
      const u = i / RINGS;
      curve.getPoint(u, p);
      curve.getTangent(u, tan);
      up.crossVectors(tan, X).normalize();
      side.crossVectors(up, tan).normalize();
      const [rx, ry] = radii(u);
      for (let k = 0; k < SIDES; k++) {
        const a = (k / SIDES) * Math.PI * 2;
        const ca = Math.cos(a) * rx;
        const sa = Math.sin(a) * ry;
        const o = (i * SIDES + k) * 3;
        pos[o] = p.x + side.x * ca + up.x * sa;
        pos[o + 1] = p.y + side.y * ca + up.y * sa;
        pos[o + 2] = p.z + side.z * ca + up.z * sa;
      }
    }
    skinGeo.attributes.position!.needsUpdate = true;
    skinGeo.computeVertexNormals();
    // The head sits at the widest point of the skull, facing along the snout.
    const u = HEAD / (n - 1);
    curve.getPoint(u, p);
    curve.getTangent(u, tan);
    up.crossVectors(tan, X).normalize();
    side.crossVectors(up, tan).normalize();
    basis.makeBasis(side, up, tan);
    head.position.copy(p);
    head.quaternion.setFromRotationMatrix(basis);
  }
  bend(0, 0, 0, 0);

  return {
    root,
    update(x, y, z, heading, walked, walking, look, t) {
      root.position.set(x, y, z);
      root.rotation.y = heading;
      shadow.position.y = 0.06 / scale;
      const ph = walked * 0.9;
      legs.forEach((leg, i) => {
        const off = i === 0 || i === 3 ? 0 : Math.PI;
        leg.rotation.x = Math.sin(ph + off) * 0.34 * walking;
      });
      body.position.y = Math.abs(Math.sin(ph)) * 0.16 * walking;
      body.rotation.z = Math.sin(ph) * 0.025 * walking;
      bend(t, ph, walking, look);
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
