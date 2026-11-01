/**
 * The woolly mammoths who wander the frozen lake at Snowy Summit Pass: an original,
 * friendly cartoon mammoth. A big shaggy russet body with a fringe of long fur hanging
 * round it, a domed head, a long swinging trunk, great curling ivory tusks, little
 * flapping ears, kind eyes, four stout furry legs and a tufted tail.
 *
 * Built in code from simple shapes (about 20k triangles), with the same interface as the
 * long-neck (render/dinosaur.ts), so game/hazards.ts walks it round its path the same
 * way. Purely visual. (Blake's Snowy Summit review asked for better mammoths: the back
 * now slopes from a high shoulder hump to low hips, the fur hangs in two layered
 * fringes in three shades with shaggy legs, the head has a brow, a forelock and a lip,
 * and the trunk is longer, tapering to a two-fingered tip. Smooth-shaded and rounder
 * since review-snow_region 9 note 18: "smooth out these mammoths and make them less
 * polygonal".)
 */
import * as THREE from "three";
import type { DinoView } from "./dinosaur";

export function createMammothView(parent: THREE.Object3D, scale = 1): DinoView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const mat = (color: string, opts: THREE.MeshLambertMaterialParameters = {}) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: false, ...opts });
    mats.push(m);
    return m;
  };
  const geo = <T extends THREE.BufferGeometry>(g: T) => {
    geos.push(g);
    return g;
  };
  const FUR = mat("#8a5232");
  const DARK = mat("#5e3420");
  const LIGHT = mat("#a8683e");
  const IVORY = mat("#f2e6c8");
  const SKIN = mat("#6a4030");
  const WHITE = mat("#ffffff");
  const BLACK = mat("#1d1a18");
  const SNOW = mat("#f6faff");

  const root = new THREE.Group();
  root.name = "mammoth";
  const body = new THREE.Group();
  root.add(body);

  const ball = geo(new THREE.IcosahedronGeometry(1, 4));
  const lowBall = geo(new THREE.IcosahedronGeometry(1, 3));
  const add = (
    g: THREE.BufferGeometry,
    m: THREE.Material,
    at: [number, number, number],
    s: [number, number, number],
    to: THREE.Object3D,
    rot?: [number, number, number],
  ) => {
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set(...at);
    mesh.scale.set(...s);
    if (rot) mesh.rotation.set(...rot);
    mesh.castShadow = true;
    to.add(mesh);
    return mesh;
  };

  // ------------------------------------------------------------- the body (faces +z)
  add(ball, FUR, [0, 4.3, -0.4], [2.35, 2.2, 3.5], body); // the barrel
  add(ball, FUR, [0, 5.5, 1.5], [2.3, 2.5, 2.2], body); // the high shoulder hump
  add(ball, FUR, [0, 4.0, -2.4], [2.15, 2.0, 1.9], body); // the low hips
  add(ball, DARK, [0, 6.9, 1.2], [1.1, 0.7, 1.4], body); // the hump's dark crest
  add(lowBall, SNOW, [0.2, 7.3, 1.1], [1.3, 0.4, 1.6], body); // snow on its back
  add(lowBall, SNOW, [-0.3, 5.9, -1.8], [1.0, 0.3, 1.1], body);
  // The fur: shaggy skirts, not separate locks (review-snow_region 10 note 2: "the fur
  // that is draping down looks horrible"): a long one round the belly hanging to the
  // knees, a cape over the shoulders on top of it, each a single smooth sheet with a
  // ragged hem of pointed tufts.
  const SHAG = mat("#7a4528", { side: THREE.DoubleSide });
  const CAPE = mat("#5e3420", { side: THREE.DoubleSide });
  const LEGFUR = mat("#8a5232", { side: THREE.DoubleSide });
  /** A skirt of fur round an ellipse (rx across, rz along, centred cz), from yTop down to
   * the hem at yBot, flaring out by `flare`, its hem cut in `teeth` tufts `jag` deep. */
  const skirt = (
    rx: number,
    rz: number,
    cz: number,
    yTop: number,
    yBot: number,
    teeth: number,
    jag: number,
    flare: number,
    seed: number,
  ) => {
    const n = teeth * 2;
    const rows = [0, 0.35, 0.7, 1];
    const pos: number[] = [];
    const idx: number[] = [];
    for (const [r, t] of rows.entries()) {
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        const h = Math.sin(i * 12.9898 + seed * 78.233) * 43758.5453;
        const rand = h - Math.floor(h);
        const out = 1 + flare * t * t + (r > 0 ? 0.05 * (rand - 0.5) : 0);
        let y = yTop + (yBot - yTop) * t;
        if (r === rows.length - 1) y -= i % 2 ? 0 : jag * (0.6 + 0.8 * rand);
        else if (r === rows.length - 2) y -= i % 2 ? 0 : jag * 0.15;
        pos.push(Math.cos(a) * rx * out, y, cz + Math.sin(a) * rz * out);
      }
    }
    for (let r = 0; r < rows.length - 1; r++)
      for (let i = 0; i < n; i++) {
        const a0 = r * n + i;
        const a1 = r * n + ((i + 1) % n);
        const b0 = a0 + n;
        const b1 = a1 + n;
        idx.push(a0, b0, a1, a1, b0, b1);
      }
    const g = geo(new THREE.BufferGeometry());
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    return g;
  };
  const sheet = (g: THREE.BufferGeometry, m: THREE.Material, to: THREE.Object3D) => {
    const mesh = new THREE.Mesh(g, m);
    mesh.castShadow = true;
    to.add(mesh);
    return mesh;
  };
  sheet(skirt(2.2, 3.4, -0.5, 4.0, 2.2, 22, 0.55, 0.12, 1), SHAG, body); // round the belly
  sheet(skirt(2.25, 2.25, 1.4, 6.2, 3.7, 16, 0.45, 0.18, 2), CAPE, body); // the shoulder cape
  sheet(skirt(1.95, 1.6, -2.4, 4.8, 3.0, 14, 0.4, 0.12, 3), SHAG, body); // over the hips
  // ------------------------------------------------------------- the head
  const head = new THREE.Group();
  head.position.set(0, 5.6, 3.4);
  body.add(head);
  add(ball, FUR, [0, 0.2, 0.6], [1.7, 1.8, 1.6], head);
  add(ball, DARK, [0, 1.75, 0.2], [1.2, 1.25, 1.15], head); // the tall domed crown
  add(ball, DARK, [0, 1.2, 1.38], [1.15, 0.24, 0.45], head); // the brow
  add(lowBall, SNOW, [0, 2.85, 0.1], [0.8, 0.25, 0.8], head);
  for (let i = 0; i < 5; i++)
    add(ball, DARK, [(i - 2) * 0.3, 1.55 - Math.abs(i - 2) * 0.08, 1.45], [0.26, 0.38, 0.2], head, [
      0.5,
      0,
      (i - 2) * 0.15,
    ]); // forelock
  add(ball, SKIN, [0, -0.9, 1.35], [0.55, 0.3, 0.45], head); // the lower lip
  const ears: THREE.Mesh[] = [];
  for (const sd of [-1, 1]) {
    ears.push(add(ball, SKIN, [sd * 1.55, 0.4, 0.2], [0.25, 0.75, 0.6], head));
    add(ball, WHITE, [sd * 0.85, 0.6, 1.7], [0.26, 0.28, 0.22], head);
    add(ball, BLACK, [sd * 0.92, 0.64, 1.86], [0.14, 0.17, 0.11], head);
    add(ball, WHITE, [sd * 0.97, 0.72, 1.93], [0.05, 0.06, 0.04], head);
  }
  // The tusks: long ivory curves sweeping down, out, forward and up, tapering to a point
  // (review-snow_region 10 note 2, "the tusks are all glitched out": the taper used to
  // pick the wrong ring for each vertex, crumpling them).
  const TUBE = 32;
  const RADIAL = 12;
  for (const sd of [-1, 1]) {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(sd * 0.75, -0.5, 1.3),
      new THREE.Vector3(sd * 1.2, -1.9, 2.8),
      new THREE.Vector3(sd * 1.65, -2.0, 4.4),
      new THREE.Vector3(sd * 1.55, -0.9, 5.6),
      new THREE.Vector3(sd * 1.05, 0.4, 5.9),
    ]);
    const tusk = geo(new THREE.TubeGeometry(curve, TUBE, 0.34, RADIAL, false));
    const p = tusk.attributes.position!;
    const v = new THREE.Vector3();
    const c = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) {
      const u = Math.floor(i / (RADIAL + 1)) / TUBE;
      curve.getPointAt(u, c);
      v.fromBufferAttribute(p, i)
        .sub(c)
        .multiplyScalar(1.1 - 0.95 * u * u)
        .add(c);
      p.setXYZ(i, v.x, v.y, v.z);
    }
    tusk.computeVertexNormals();
    const m = new THREE.Mesh(tusk, IVORY);
    m.castShadow = true;
    head.add(m);
    // (a ring of skin where it leaves the head, and a rounded tip)
    add(ball, SKIN, [sd * 0.75, -0.5, 1.3], [0.42, 0.42, 0.42], head);
    curve.getPointAt(1, c);
    add(ball, IVORY, [c.x, c.y, c.z], [0.05, 0.05, 0.05], head);
  }
  // The trunk: a chain of segments, each hung from the one before, so it can swing and
  // curl.
  const trunk: THREE.Group[] = [];
  const seg = geo(new THREE.CylinderGeometry(0.42, 0.5, 1.0, 16));
  let hang: THREE.Object3D = head;
  for (let i = 0; i < 8; i++) {
    const g = new THREE.Group();
    g.position.set(0, i ? -0.72 : -0.4, i ? 0 : 1.9);
    hang.add(g);
    const r = 1 - i * 0.085;
    add(seg, i % 3 === 2 ? DARK : SKIN, [0, -0.45, 0], [r, 1, r], g);
    trunk.push(g);
    hang = g;
  }
  // The tip: two little fingers.
  add(ball, SKIN, [0.14, -1.0, 0.05], [0.16, 0.24, 0.16], hang);
  add(ball, SKIN, [-0.12, -0.95, -0.08], [0.12, 0.2, 0.12], hang);

  // ------------------------------------------------------------- legs and tail
  const legGeo = geo(new THREE.CylinderGeometry(0.75, 0.85, 3.6, 16));
  const cuff = geo(new THREE.ConeGeometry(1.05, 1.4, 16, 1, true));
  const legs: THREE.Group[] = [];
  for (const [x, z] of [
    [1.25, 1.7],
    [-1.25, 1.7],
    [1.25, -2.0],
    [-1.25, -2.0],
  ] as const) {
    const hip = new THREE.Group();
    hip.position.set(x, 3.6, z);
    body.add(hip);
    add(legGeo, FUR, [0, -1.8, 0], [1, 1, 1], hip);
    add(cuff, DARK, [0, -2.7, 0], [1, 1, 1], hip);
    // Shaggy fur down the leg: a little skirt of it to the ankle.
    sheet(skirt(0.98, 0.98, 0, -0.4, -2.5, 9, 0.35, 0.15, x * 3 + z), LEGFUR, hip);
    add(lowBall, LIGHT, [0, -3.55, 0.35], [0.85, 0.3, 0.85], hip);
    for (const tx of [-0.45, 0, 0.45])
      add(ball, IVORY, [tx, -3.5, 0.95 - Math.abs(tx) * 0.3], [0.2, 0.16, 0.14], hip);
    legs.push(hip);
  }
  const tail = new THREE.Group();
  tail.position.set(0, 5.0, -4.3);
  body.add(tail);
  add(seg, SKIN, [0, -0.6, -0.1], [0.3, 1.3, 0.3], tail, [0.3, 0, 0]);
  add(ball, DARK, [0, -1.4, -0.4], [0.35, 0.55, 0.35], tail);

  // A soft round shadow on the ground.
  const shadowGeo = geo(new THREE.CircleGeometry(1, 28));
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.28,
    depthWrite: false,
  });
  mats.push(shadowMat);
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(3.4, 5.6, 1);
  shadow.renderOrder = 1;
  root.add(shadow);
  root.scale.setScalar(scale);
  parent.add(root);

  return {
    root,
    update(x, y, z, heading, walked, walking, look, t) {
      root.position.set(x, y, z);
      root.rotation.y = heading;
      shadow.position.y = 0.06 / scale;
      const ph = walked * 0.75;
      legs.forEach((leg, i) => {
        const off = i === 0 || i === 3 ? 0 : Math.PI;
        leg.rotation.x = Math.sin(ph + off) * 0.3 * walking;
      });
      body.position.y = Math.abs(Math.sin(ph)) * 0.14 * walking;
      body.rotation.z = Math.sin(ph) * 0.03 * walking;
      // The head nods with the walk and turns towards a nearby kart.
      head.rotation.y = look * 0.5;
      head.rotation.x = Math.sin(ph * 2) * 0.04 * walking + Math.sin(t * 0.6) * 0.03;
      // The trunk swings and curls, the ears flap, the tail swishes.
      trunk.forEach((g, i) => {
        const k = i / (trunk.length - 1);
        g.rotation.x =
          0.12 + 0.1 * k + 0.16 * Math.sin(t * 1.3 - i * 0.5) * (0.3 + k) + (i > 4 ? 0.25 : 0);
        g.rotation.z = 0.08 * Math.sin(t * 0.9 - i * 0.6 + ph * 0.5) * (0.3 + k);
      });
      ears.forEach((e, i) => {
        e.rotation.y = (i ? -1 : 1) * (0.25 + 0.2 * Math.sin(t * 2.1 + i));
      });
      tail.rotation.z = Math.sin(t * 2.4) * 0.35;
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
