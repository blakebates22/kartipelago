/**
 * The pterosaur that circles over Cascade Caverns: an original cartoon flyer with a long
 * beak, a swept crest and broad leathery wings. Each wing is two panels (arm and hand)
 * that fold at the wrist, so a wingbeat whips: the arm leads and the hand follows. It
 * flaps for a while, then spreads its wings and glides, banking into its turns.
 *
 * Built in code, under 1k triangles. Purely visual: where it flies is game/hazards.ts.
 */
import * as THREE from "three";

export interface PterosaurView {
  readonly root: THREE.Group;
  /**
   * Place and animate it: position, heading (radians, 0 = +z), bank (radians, + rolls
   * right), how hard it's flapping (0 glide .. 1 full beat) and the time.
   */
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    bank: number,
    flap: number,
    t: number,
  ): void;
  dispose(): void;
}

const BODY = "#a8582e";
const BELLY = "#e9c48a";
const WING = "#c9874a";
const EDGE = "#6b3420";
const CREST = "#d8452b";

export function createPterosaurView(parent: THREE.Object3D, scale = 1): PterosaurView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const mat = (color: string, opts: THREE.MeshLambertMaterialParameters = {}) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
    mats.push(m);
    return m;
  };
  const geo = <G extends THREE.BufferGeometry>(g: G) => (geos.push(g), g);
  const body = mat(BODY);
  const belly = mat(BELLY);
  const wingMat = mat("#ffffff", { vertexColors: true, side: THREE.DoubleSide });
  const crest = mat(CREST);
  const white = mat("#ffffff");
  const black = mat("#1d1a18");

  const root = new THREE.Group();
  root.name = "pterosaur";
  root.scale.setScalar(scale);
  const frame = new THREE.Group(); // banks and pitches inside the heading
  root.add(frame);

  // The body: a spindle along +z, a paler belly, a stubby tail.
  const torso = new THREE.Mesh(geo(new THREE.SphereGeometry(0.5, 10, 7)), body);
  torso.scale.set(0.95, 0.8, 2.1);
  const under = new THREE.Mesh(geo(new THREE.SphereGeometry(0.46, 10, 6)), belly);
  under.scale.set(0.85, 0.65, 1.9);
  under.position.set(0, -0.12, 0.05);
  const tail = new THREE.Mesh(geo(new THREE.ConeGeometry(0.16, 1.3, 5)), body);
  tail.rotation.x = -Math.PI / 2;
  tail.position.set(0, 0.05, -1.5);
  frame.add(torso, under, tail);

  // The neck and head: a long beak forward, the crest swept back.
  const head = new THREE.Group();
  head.position.set(0, 0.35, 1.05);
  frame.add(head);
  const neck = new THREE.Mesh(geo(new THREE.CylinderGeometry(0.2, 0.28, 0.8, 6)), body);
  neck.rotation.x = Math.PI / 2 - 0.5;
  neck.position.set(0, -0.15, -0.15);
  const skull = new THREE.Mesh(geo(new THREE.SphereGeometry(0.34, 8, 6)), body);
  skull.scale.set(0.9, 0.85, 1.25);
  skull.position.set(0, 0.12, 0.2);
  const beak = new THREE.Mesh(geo(new THREE.ConeGeometry(0.2, 1.7, 6)), belly);
  beak.rotation.x = Math.PI / 2;
  beak.position.set(0, 0.02, 1.15);
  const comb = new THREE.Mesh(geo(new THREE.ConeGeometry(0.17, 1.5, 4)), crest);
  comb.rotation.x = -Math.PI / 2 - 0.35;
  comb.scale.set(0.45, 1, 1.6);
  comb.position.set(0, 0.42, -0.45);
  head.add(neck, skull, beak, comb);
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(geo(new THREE.SphereGeometry(0.11, 6, 5)), white);
    eye.position.set(s * 0.27, 0.22, 0.38);
    const pupil = new THREE.Mesh(geo(new THREE.SphereGeometry(0.06, 5, 4)), black);
    pupil.position.set(s * 0.33, 0.23, 0.44);
    head.add(eye, pupil);
  }

  // The wings: arm (shoulder to wrist) and hand (wrist to tip), each a membrane with a
  // bony leading edge. +x is the left wing; the right is mirrored.
  const membrane = (pts: [number, number, number][], edgeFrom: number) => {
    // A fan of triangles from the first point; vertex colours darken toward the trailing edge.
    const pos: number[] = [];
    const col: number[] = [];
    const a = new THREE.Color(WING);
    const b = new THREE.Color(EDGE);
    const c = new THREE.Color();
    for (let i = 1; i < pts.length - 1; i++)
      for (const k of [0, i, i + 1]) {
        const p = pts[k]!;
        pos.push(...p);
        c.copy(a).lerp(b, k >= edgeFrom ? 0.55 : 0);
        col.push(c.r, c.g, c.b);
      }
    const g = geo(new THREE.BufferGeometry());
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    g.computeVertexNormals();
    return new THREE.Mesh(g, wingMat);
  };
  const bone = (len: number, r: number) => {
    const m = new THREE.Mesh(geo(new THREE.CylinderGeometry(r * 0.7, r, len, 5)), body);
    m.rotation.z = -Math.PI / 2;
    m.position.x = len / 2;
    return m;
  };
  const wings: { arm: THREE.Group; hand: THREE.Group; side: number }[] = [];
  for (const side of [1, -1]) {
    const arm = new THREE.Group();
    arm.position.set(side * 0.38, 0.2, 0.35);
    arm.scale.x = side;
    const armSkin = membrane(
      [
        [0, 0, 0],
        [1.9, 0, 0.15],
        [1.9, 0, -1.2],
        [1.0, 0, -1.9],
        [0, 0, -1.8],
      ],
      2,
    );
    arm.add(armSkin, bone(1.9, 0.12));
    const hand = new THREE.Group();
    hand.position.set(1.9, 0, 0.1);
    const handSkin = membrane(
      [
        [0, 0, 0],
        [1.6, 0, -0.25],
        [3.0, 0, -1.0],
        [1.9, 0, -1.45],
        [0.8, 0, -1.4],
        [0, 0, -1.25],
      ],
      2,
    );
    const finger = bone(3.05, 0.09);
    finger.rotation.y = 0.28;
    hand.add(handSkin, finger);
    // A little three-clawed thumb at the wrist.
    const thumb = new THREE.Mesh(geo(new THREE.ConeGeometry(0.06, 0.3, 4)), black);
    thumb.position.set(0.05, 0.05, 0.2);
    thumb.rotation.x = Math.PI / 2;
    hand.add(thumb);
    arm.add(hand);
    frame.add(arm);
    wings.push({ arm, hand, side });
  }
  // Feet tucked back under the tail.
  for (const s of [-1, 1]) {
    const foot = new THREE.Mesh(geo(new THREE.ConeGeometry(0.09, 0.6, 4)), black);
    foot.rotation.x = -Math.PI / 2;
    foot.position.set(s * 0.25, -0.3, -1.0);
    frame.add(foot);
  }
  root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) o.castShadow = true;
  });
  parent.add(root);

  return {
    root,
    update(x, y, z, heading, bank, flap, t) {
      root.position.set(x, y, z);
      root.rotation.set(0, heading, 0);
      frame.rotation.set(0, 0, 0);
      // Climb a touch on the downstroke, nose down a touch in a glide.
      const beat = t * 5.2;
      const down = Math.sin(beat);
      frame.position.y = -down * 0.25 * flap;
      frame.rotation.x = -0.08 * (1 - flap) + 0.05 * down * flap;
      frame.rotation.z = bank;
      for (const w of wings) {
        // The arm sweeps through about 70 degrees; the hand follows a quarter-beat behind.
        const glide = 0.08 + 0.03 * Math.sin(t * 0.9);
        const armUp = glide * (1 - flap) + flap * (0.15 + 0.6 * Math.sin(beat));
        const handUp = 0.06 * (1 - flap) + flap * 0.45 * Math.sin(beat - 1.1);
        w.arm.rotation.z = armUp * w.side;
        w.hand.rotation.z = handUp;
        w.arm.rotation.y = -0.12 * flap * Math.cos(beat) * w.side;
      }
      head.rotation.y = 0.25 * Math.sin(t * 0.7);
      head.rotation.x = 0.1 * Math.sin(t * 1.3);
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
