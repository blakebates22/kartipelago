/**
 * The friendly long-neck who strolls along the river at Riverbend Palms: an original
 * design (round body, cream belly, darker back spots, a long neck that sways, a
 * swishing tail and a big-eyed smiley head). Built in code from smooth-shaded spheres
 * and capsules (rounded joints, so the neck and tail bend without seams), about 12k
 * triangles. Purely visual: where it walks, and what it bumps, is game/hazards.ts.
 *
 * v1 (Riverbend v1) was a 600-triangle, flat-shaded version of the same shapes.
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
    const m = new THREE.MeshLambertMaterial({ color });
    mats.push(m);
    return m;
  };
  const root = new THREE.Group();
  root.name = "dinosaur";
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
  const ball = new THREE.SphereGeometry(1, 22, 14);
  const bead = new THREE.SphereGeometry(1, 10, 7);
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
  const legGeo = new THREE.CapsuleGeometry(0.62, 2.4, 6, 14);
  const footGeo = new THREE.SphereGeometry(1, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2);
  for (const [x, z] of [
    [1.4, 2.0],
    [-1.4, 2.0],
    [1.5, -2.0],
    [-1.5, -2.0],
  ] as const) {
    const hip = new THREE.Group();
    hip.position.set(x, 3.6, z);
    body.add(hip);
    add(legGeo, skin, [0, -1.6, 0], [1, 1, 1], hip);
    add(footGeo, skin, [0, -3.45, 0.1], [0.85, 0.45, 0.95], hip);
    // Three little toenails.
    for (const tx of [-0.38, 0, 0.38])
      add(bead, belly, [tx, -3.3, 0.85 - Math.abs(tx) * 0.3], [0.2, 0.16, 0.16], hip);
    legs.push(hip);
  }
  // The neck: a chain of segments, each swaying a little more than the last.
  const neck: THREE.Group[] = [];
  let parentSeg: THREE.Object3D = body;
  let start = new THREE.Vector3(0, 5.2, 3.0);
  for (let k = 0; k < 5; k++) {
    const g = new THREE.Group();
    g.position.copy(start);
    g.rotation.x = k === 0 ? 0.75 : -0.12;
    parentSeg.add(g);
    neck.push(g);
    parentSeg = g;
    start = new THREE.Vector3(0, 1.55, 0);
  }
  // The head, at the top of the neck.
  const head = new THREE.Group();
  head.name = "dinosaur head";
  head.position.set(0, 1.6, 0);
  head.rotation.x = -0.9;
  parentSeg.add(head);
  add(ball, skin, [0, 0.4, 0.5], [0.95, 0.85, 1.35], head);
  add(ball, belly, [0, 0.05, 0.85], [0.75, 0.45, 1.0], head);
  for (const side of [-1, 1]) {
    add(ball, white, [side * 0.62, 0.75, 0.75], [0.36, 0.42, 0.3], head);
    add(ball, black, [side * 0.72, 0.8, 0.9], [0.16, 0.22, 0.14], head);
    // A sparkle in each eye, a rosy cheek and a nostril.
    add(bead, white, [side * 0.8, 0.88, 0.98], [0.05, 0.06, 0.04], head);
    add(ball, cheek, [side * 0.7, 0.2, 1.1], [0.18, 0.12, 0.12], head);
    add(bead, black, [side * 0.22, 0.45, 1.84], [0.06, 0.05, 0.05], head);
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
    tail.push(g);
    parentSeg = g;
    start = new THREE.Vector3(0, 1.75, 0);
  }
  // The neck and tail are each one smooth tube, re-bent every frame through the
  // joints of their (invisible) chains, so there are no seams as they sway.
  const tailTip = new THREE.Object3D();
  tailTip.position.set(0, 1.75, 0);
  tail[tail.length - 1]!.add(tailTip);
  const tubes = [
    createTube(skin, [body, ...neck, head], (t) => 0.95 - 0.42 * t, 0.6),
    createTube(skin, [body, ...tail, tailTip], (t) => 1.25 * (1 - t) + 0.12, 0.45),
  ];
  for (const tube of tubes) {
    geos.push(tube.mesh.geometry);
    body.add(tube.mesh);
  }
  add(bead, skin, [0, 0, 0], [0.13, 0.13, 0.13], tailTip);
  root.updateMatrixWorld(true);
  for (const tube of tubes) tube.bend(body);

  // A soft round shadow on the ground.
  const shadowGeo = new THREE.CircleGeometry(4.2, 32);
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
      root.updateMatrixWorld(true);
      for (const tube of tubes) tube.bend(body);
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

/**
 * A smooth tube through a chain of joints: `chain[0]` is the frame the tube lives in
 * (the body), the rest are the joints in order. `inset` is how far back into the body
 * (along the first joint's direction) the tube starts, so it grows out of it.
 */
function createTube(
  mat: THREE.Material,
  chain: THREE.Object3D[],
  radius: (t: number) => number,
  inset: number,
) {
  const RINGS = 28;
  const SIDES = 16;
  const pos = new Float32Array((RINGS + 1) * SIDES * 3);
  const idx: number[] = [];
  for (let i = 0; i < RINGS; i++)
    for (let k = 0; k < SIDES; k++) {
      const a = i * SIDES + k;
      const b = i * SIDES + ((k + 1) % SIDES);
      idx.push(a, a + SIDES, b, b, a + SIDES, b + SIDES);
    }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setIndex(idx);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = true;
  mesh.frustumCulled = false;
  const inv = new THREE.Matrix4();
  const pts = chain.slice(1).map(() => new THREE.Vector3());
  const first = new THREE.Vector3();
  const curve = new THREE.CatmullRomCurve3([first, ...pts], false, "centripetal");
  const p = new THREE.Vector3();
  const tan = new THREE.Vector3();
  const side = new THREE.Vector3();
  const up = new THREE.Vector3();
  const across = new THREE.Vector3(1, 0, 0);
  return {
    mesh,
    /** Re-bend through the joints (world matrices must be up to date). */
    bend(frame: THREE.Object3D) {
      inv.copy(frame.matrixWorld).invert();
      chain
        .slice(1)
        .forEach((j, i) => pts[i]!.setFromMatrixPosition(j.matrixWorld).applyMatrix4(inv));
      first.copy(pts[0]!).addScaledVector(tan.subVectors(pts[0]!, pts[1]!).normalize(), inset);
      curve.updateArcLengths();
      for (let i = 0; i <= RINGS; i++) {
        const t = i / RINGS;
        curve.getPointAt(t, p);
        curve.getTangentAt(t, tan);
        // The chains bend in the body's y-z plane, so its x axis is never along them.
        up.crossVectors(tan, across).normalize();
        side.crossVectors(up, tan).normalize();
        const r = radius(t);
        for (let k = 0; k < SIDES; k++) {
          const a = (k / SIDES) * Math.PI * 2;
          const o = (i * SIDES + k) * 3;
          pos[o] = p.x + (side.x * Math.cos(a) + up.x * Math.sin(a)) * r;
          pos[o + 1] = p.y + (side.y * Math.cos(a) + up.y * Math.sin(a)) * r;
          pos[o + 2] = p.z + (side.z * Math.cos(a) + up.z * Math.sin(a)) * r;
        }
      }
      geo.attributes.position!.needsUpdate = true;
      geo.computeVertexNormals();
    },
  };
}
