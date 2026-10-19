/**
 * The friendly long-neck who strolls along the river at Riverbend Palms: an original,
 * low-poly, flat-shaded design (round body, cream belly, darker back spots, a long
 * neck that sways, a swishing tail and a big-eyed smiley head). Built in code, about
 * 600 triangles. Purely visual: where it walks, and what it bumps, is game/hazards.ts.
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

export function createDinoView(parent: THREE.Object3D, scale = 1): DinoView {
  const mats: THREE.Material[] = [];
  const mat = (color: string) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true });
    mats.push(m);
    return m;
  };
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const skin = mat("#5fbf6a");
  const back = mat("#3f9a55");
  const belly = mat("#f2e6b0");
  const white = mat("#ffffff");
  const black = mat("#1d1a18");
  const cheek = mat("#f59a8a");
  const geos: THREE.BufferGeometry[] = [];
  const add = (
    g: THREE.BufferGeometry,
    m: THREE.Material,
    p: [number, number, number],
    s: [number, number, number] = [1, 1, 1],
    to: THREE.Object3D = body,
  ) => {
    geos.push(g);
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set(...p);
    mesh.scale.set(...s);
    mesh.castShadow = true;
    to.add(mesh);
    return mesh;
  };
  const ball = new THREE.SphereGeometry(1, 9, 6);
  // Body and belly (the dino faces +z).
  add(ball, skin, [0, 4.2, 0], [2.4, 2.1, 3.6]);
  add(ball, belly, [0, 3.5, 0.3], [2.0, 1.4, 3.0]);
  for (const [x, y, z, r] of [
    [0, 6.1, 0.6, 0.7],
    [0.9, 5.7, -1.2, 0.55],
    [-0.8, 5.8, -0.4, 0.5],
    [0.3, 5.6, 2.0, 0.45],
  ] as const)
    add(ball, back, [x, y, z], [r, r * 0.45, r]);
  // Legs: pivots at the hips so they can swing.
  const legs: THREE.Group[] = [];
  const legGeo = new THREE.CylinderGeometry(0.55, 0.65, 3.4, 6);
  const footGeo = new THREE.CylinderGeometry(0.75, 0.8, 0.5, 6);
  for (const [x, z] of [
    [1.4, 2.0],
    [-1.4, 2.0],
    [1.5, -2.0],
    [-1.5, -2.0],
  ] as const) {
    const hip = new THREE.Group();
    hip.position.set(x, 3.6, z);
    body.add(hip);
    add(legGeo, skin, [0, -1.7, 0], [1, 1, 1], hip);
    add(footGeo, belly, [0, -3.35, 0.1], [1, 1, 1], hip);
    legs.push(hip);
  }
  // The neck: a chain of segments, each swaying a little more than the last.
  const neck: THREE.Group[] = [];
  let parentSeg: THREE.Object3D = body;
  const segGeo = new THREE.CylinderGeometry(0.62, 0.8, 1.7, 7);
  let start = new THREE.Vector3(0, 5.2, 3.0);
  for (let k = 0; k < 5; k++) {
    const g = new THREE.Group();
    g.position.copy(start);
    g.rotation.x = k === 0 ? 0.75 : -0.12;
    parentSeg.add(g);
    add(segGeo, skin, [0, 0.8, 0], [1 - k * 0.08, 1, 1 - k * 0.08], g);
    neck.push(g);
    parentSeg = g;
    start = new THREE.Vector3(0, 1.55, 0);
  }
  // The head, at the top of the neck.
  const head = new THREE.Group();
  head.position.set(0, 1.6, 0);
  head.rotation.x = -0.9;
  parentSeg.add(head);
  add(ball, skin, [0, 0.4, 0.5], [0.95, 0.85, 1.35], head);
  add(ball, belly, [0, 0.05, 0.85], [0.75, 0.45, 1.0], head);
  for (const side of [-1, 1]) {
    add(ball, white, [side * 0.62, 0.75, 0.75], [0.36, 0.42, 0.3], head);
    add(ball, black, [side * 0.72, 0.8, 0.9], [0.16, 0.22, 0.14], head);
    add(ball, cheek, [side * 0.7, 0.2, 1.1], [0.18, 0.12, 0.12], head);
  }
  // The tail: tapering segments that swish.
  const tail: THREE.Group[] = [];
  parentSeg = body;
  start = new THREE.Vector3(0, 4.2, -3.2);
  for (let k = 0; k < 5; k++) {
    const g = new THREE.Group();
    g.position.copy(start);
    g.rotation.x = k === 0 ? -1.75 : 0.12;
    parentSeg.add(g);
    const r = 1.1 - k * 0.2;
    add(
      new THREE.CylinderGeometry(Math.max(0.12, r - 0.2), r, 1.8, 6),
      skin,
      [0, 0.9, 0],
      [1, 1, 1],
      g,
    );
    tail.push(g);
    parentSeg = g;
    start = new THREE.Vector3(0, 1.75, 0);
  }
  // A soft round shadow on the ground.
  const shadowGeo = new THREE.CircleGeometry(4.2, 16);
  geos.push(shadowGeo);
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.32,
    depthWrite: false,
  });
  mats.push(shadowMat);
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(0.8, 1.3, 1);
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
      const ph = walked * 0.9;
      legs.forEach((leg, i) => {
        const off = i === 0 || i === 3 ? 0 : Math.PI;
        leg.rotation.x = Math.sin(ph + off) * 0.38 * walking;
      });
      body.position.y = Math.abs(Math.sin(ph)) * 0.18 * walking;
      body.rotation.z = Math.sin(ph) * 0.03 * walking;
      neck.forEach((g, k) => {
        g.rotation.z = Math.sin(t * 0.7 + k * 0.4) * 0.05 + look * 0.09;
      });
      head.rotation.y = look * 0.4;
      head.rotation.x = -0.9 + Math.sin(t * 1.3) * 0.08;
      tail.forEach((g, k) => {
        g.rotation.z = Math.sin(t * 1.6 - k * 0.6 + ph * 0.5) * (0.12 + 0.05 * k);
      });
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
