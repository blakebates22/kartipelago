/**
 * The woolly mammoths who wander the frozen lake at Snowy Summit Pass: an original,
 * friendly cartoon mammoth. A big shaggy russet body with a fringe of long fur hanging
 * round it, a domed head, a long swinging trunk, great curling ivory tusks, little
 * flapping ears, kind eyes, four stout furry legs and a tufted tail.
 *
 * Built in code from simple shapes (about 4k triangles), with the same interface as the
 * long-neck (render/dinosaur.ts), so game/hazards.ts walks it round its path the same
 * way. Purely visual.
 */
import * as THREE from "three";
import type { DinoView } from "./dinosaur";

export function createMammothView(parent: THREE.Object3D, scale = 1): DinoView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const mat = (color: string, opts: THREE.MeshLambertMaterialParameters = {}) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
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

  const ball = geo(new THREE.IcosahedronGeometry(1, 2));
  const lowBall = geo(new THREE.IcosahedronGeometry(1, 1));
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
  add(ball, FUR, [0, 4.5, -0.3], [2.4, 2.3, 3.6], body); // the barrel
  add(ball, FUR, [0, 5.3, 1.6], [2.3, 2.3, 2.2], body); // the shoulder hump
  add(lowBall, SNOW, [0.2, 7.1, 0.9], [1.5, 0.45, 2.0], body); // snow on its back
  // The fringe: long locks of fur hanging all round the belly.
  const lock = geo(new THREE.ConeGeometry(0.55, 2.6, 5));
  for (let i = 0; i < 22; i++) {
    const a = (i / 22) * Math.PI * 2;
    const x = Math.cos(a) * 2.25;
    const z = Math.sin(a) * 3.3 - 0.2;
    add(lock, i % 2 ? DARK : FUR, [x, 2.9 + 0.3 * Math.sin(i * 1.7), z], [1, 1, 1], body, [
      Math.PI + Math.sin(a) * 0.25,
      0,
      -Math.cos(a) * 0.25,
    ]);
  }

  // ------------------------------------------------------------- the head
  const head = new THREE.Group();
  head.position.set(0, 5.6, 3.4);
  body.add(head);
  add(ball, FUR, [0, 0.2, 0.6], [1.7, 1.8, 1.6], head);
  add(ball, DARK, [0, 1.6, 0.3], [1.15, 1.1, 1.1], head); // the domed crown
  add(lowBall, SNOW, [0, 2.55, 0.2], [0.8, 0.25, 0.8], head);
  const ears: THREE.Mesh[] = [];
  for (const sd of [-1, 1]) {
    ears.push(add(ball, SKIN, [sd * 1.55, 0.4, 0.2], [0.25, 0.75, 0.6], head));
    add(ball, WHITE, [sd * 0.85, 0.65, 1.75], [0.3, 0.32, 0.25], head);
    add(ball, BLACK, [sd * 0.92, 0.7, 1.92], [0.15, 0.19, 0.12], head);
    add(ball, WHITE, [sd * 0.98, 0.8, 1.98], [0.05, 0.06, 0.04], head);
  }
  // The tusks: long ivory curves sweeping down, out, forward and up.
  for (const sd of [-1, 1]) {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(sd * 0.8, -0.6, 1.5),
      new THREE.Vector3(sd * 1.3, -2.1, 3.0),
      new THREE.Vector3(sd * 1.6, -2.0, 4.8),
      new THREE.Vector3(sd * 1.1, -0.6, 5.9),
      new THREE.Vector3(sd * 0.4, 0.6, 5.8),
    ]);
    const tusk = geo(new THREE.TubeGeometry(curve, 16, 0.32, 6, false));
    // Taper it towards the tip.
    const p = tusk.attributes.position!;
    const v = new THREE.Vector3();
    const c = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) {
      const u = Math.floor(i / 7) / 16;
      curve.getPoint(u, c);
      v.fromBufferAttribute(p, i)
        .sub(c)
        .multiplyScalar(1.15 - u * 0.85)
        .add(c);
      p.setXYZ(i, v.x, v.y, v.z);
    }
    tusk.computeVertexNormals();
    const m = new THREE.Mesh(tusk, IVORY);
    m.castShadow = true;
    head.add(m);
  }
  // The trunk: a chain of segments, each hung from the one before, so it can swing and
  // curl.
  const trunk: THREE.Group[] = [];
  const seg = geo(new THREE.CylinderGeometry(0.42, 0.5, 1.0, 7));
  let hang: THREE.Object3D = head;
  for (let i = 0; i < 7; i++) {
    const g = new THREE.Group();
    g.position.set(0, i ? -0.85 : -0.4, i ? 0 : 1.9);
    hang.add(g);
    const r = 1 - i * 0.09;
    add(seg, i % 2 ? SKIN : FUR, [0, -0.45, 0], [r, 1, r], g);
    trunk.push(g);
    hang = g;
  }

  // ------------------------------------------------------------- legs and tail
  const legGeo = geo(new THREE.CylinderGeometry(0.75, 0.85, 3.6, 8));
  const cuff = geo(new THREE.ConeGeometry(1.05, 1.4, 8, 1, true));
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
    add(lowBall, LIGHT, [0, -3.55, 0.35], [0.85, 0.3, 0.85], hip);
    for (const tx of [-0.45, 0, 0.45])
      add(ball, IVORY, [tx, -3.5, 0.95 - Math.abs(tx) * 0.3], [0.2, 0.16, 0.14], hip);
    legs.push(hip);
  }
  const tail = new THREE.Group();
  tail.position.set(0, 5.0, -3.9);
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
