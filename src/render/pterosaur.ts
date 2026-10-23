/**
 * The pterosaur that circles over Cascade Caverns: an original cartoon flyer with a long
 * beak, a tall swept crest and broad leathery wings. Each wing is two panels (arm and
 * hand) that fold at the wrist, so a wingbeat whips: the arm leads and the hand follows.
 * It flaps for a while, then spreads its wings and glides, banking into its turns.
 *
 * v2 (Blake's Cascade review: "should look a little better"): a sleek tapering body on a
 * curved neck, a two-part beak, a blade of a crest, wings with a curved leading edge
 * (the long finger sweeping back to a sharp tip), a scalloped trailing edge joined to
 * the body down to the hip, banded upper sides and pale undersides, and little legs
 * trailing behind. Built in code, about 1.5k triangles. Purely visual: where it flies is
 * game/hazards.ts.
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

const BODY = "#9a4f2c";
const BELLY = "#ecd09a";
const BACK = "#6e3220";
const WING_LEAD = "#8a3a22";
const WING_MID = "#d27a3c";
const WING_BAND = "#f0b45a";
const WING_EDGE = "#4a2216";
const UNDER = "#e8c28c";
const UNDER_EDGE = "#a86a3e";
const CREST = "#d8452b";
const CREST_EDGE = "#7a2214";
const BEAK = "#e8cf8a";

type V3 = [number, number, number];

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
  const back = mat(BACK);
  const belly = mat(BELLY);
  // (A little glow of its own, so the undersides aren't lost in shadow against the sky.)
  const skin = mat("#ffffff", { vertexColors: true, emissive: "#3a2412" });
  const crest = mat("#ffffff", { vertexColors: true, side: THREE.DoubleSide });
  const beakMat = mat(BEAK);
  const white = mat("#ffffff");
  const black = mat("#1d1a18");

  const root = new THREE.Group();
  root.name = "pterosaur";
  root.scale.setScalar(scale);
  const frame = new THREE.Group(); // banks and pitches inside the heading
  root.add(frame);

  const mesh = (g: THREE.BufferGeometry, m: THREE.Material) => new THREE.Mesh(geo(g), m);
  /** A tapering tube along points (neck, bones, legs). */
  const tube = (pts: V3[], r0: number, r1: number, m: THREE.Material, seg = 6) => {
    const curve = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)));
    const g = new THREE.TubeGeometry(curve, Math.max(2, pts.length * 2), 1, seg, false);
    // Taper: scale each ring about the curve.
    const pos = g.attributes.position!;
    const rings = Math.max(2, pts.length * 2) + 1;
    const per = seg + 1;
    const p = new THREE.Vector3();
    for (let i = 0; i < rings; i++) {
      const c = curve.getPointAt(i / (rings - 1));
      const r = r0 + (r1 - r0) * (i / (rings - 1));
      for (let j = 0; j < per; j++) {
        const k = i * per + j;
        p.fromBufferAttribute(pos, k).sub(c).multiplyScalar(r).add(c);
        pos.setXYZ(k, p.x, p.y, p.z);
      }
    }
    g.computeVertexNormals();
    return mesh(g, m);
  };

  // The body: a sleek spindle along +z, darker along the back, a pale belly, a short
  // pointed tail.
  const torso = mesh(new THREE.SphereGeometry(0.5, 12, 8), body);
  torso.scale.set(0.82, 0.74, 2.0);
  const ridge = mesh(new THREE.SphereGeometry(0.42, 10, 6), back);
  ridge.scale.set(0.6, 0.55, 1.9);
  ridge.position.set(0, 0.16, -0.05);
  const under = mesh(new THREE.SphereGeometry(0.46, 10, 6), belly);
  under.scale.set(0.74, 0.6, 1.8);
  under.position.set(0, -0.12, 0.1);
  const tail = mesh(new THREE.ConeGeometry(0.17, 1.2, 5), body);
  tail.rotation.x = -Math.PI / 2;
  tail.position.set(0, 0.04, -1.45);
  frame.add(torso, ridge, under, tail);

  // The neck, curving up to the head.
  frame.add(
    tube(
      [
        [0, 0.05, 0.75],
        [0, 0.3, 1.25],
        [0, 0.55, 1.6],
      ],
      0.26,
      0.17,
      body,
    ),
  );
  const head = new THREE.Group();
  head.position.set(0, 0.6, 1.68);
  frame.add(head);
  const skull = mesh(new THREE.SphereGeometry(0.33, 10, 7), body);
  skull.scale.set(0.82, 0.86, 1.25);
  skull.position.set(0, 0.06, 0.08);
  // A two-part beak, the lower jaw a touch open.
  const upper = mesh(new THREE.ConeGeometry(0.19, 1.9, 6), beakMat);
  upper.rotation.x = Math.PI / 2;
  upper.scale.set(0.8, 1, 0.62);
  upper.position.set(0, 0.07, 1.2);
  const lower = mesh(new THREE.ConeGeometry(0.13, 1.55, 5), beakMat);
  lower.rotation.x = Math.PI / 2 + 0.1;
  lower.scale.set(0.75, 1, 0.5);
  lower.position.set(0, -0.1, 1.0);
  head.add(skull, upper, lower);
  // The crest: a tall blade sweeping back from the skull, red with a dark rim.
  {
    const out: V3[] = [
      [0, 0.18, 0.35],
      [0, 0.55, -0.2],
      [0, 1.15, -1.05],
      [0, 1.0, -1.45],
      [0, 0.62, -1.2],
      [0, 0.22, -0.55],
      [0, 0.1, -0.1],
    ];
    const pos: number[] = [];
    const col: number[] = [];
    const ca = new THREE.Color(CREST);
    const cb = new THREE.Color(CREST_EDGE);
    const mid: V3 = [0, 0.45, -0.45];
    for (let i = 0; i < out.length; i++) {
      const a = out[i]!;
      const b = out[(i + 1) % out.length]!;
      for (const [p, c] of [
        [mid, ca],
        [a, cb],
        [b, cb],
      ] as const) {
        pos.push(...p);
        col.push(c.r, c.g, c.b);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    g.computeVertexNormals();
    head.add(mesh(g, crest));
  }
  for (const s of [-1, 1]) {
    const eye = mesh(new THREE.SphereGeometry(0.105, 7, 5), white);
    eye.position.set(s * 0.24, 0.14, 0.3);
    const pupil = mesh(new THREE.SphereGeometry(0.06, 6, 4), black);
    pupil.position.set(s * 0.31, 0.15, 0.35);
    const glint = mesh(new THREE.SphereGeometry(0.022, 4, 3), white);
    glint.position.set(s * 0.35, 0.18, 0.37);
    head.add(eye, pupil, glint);
  }

  /**
   * A wing panel as a grid between a leading edge and a trailing edge (each a list of
   * points, the same count), `rows` across the chord. The upper side is banded and darkens
   * to the trailing edge; the underside is pale. Returns both sides as one mesh.
   */
  const panel = (lead: V3[], trail: V3[], rows: number, band0: number) => {
    const pos: number[] = [];
    const col: number[] = [];
    const cLead = new THREE.Color(WING_LEAD);
    const cMid = new THREE.Color(WING_MID);
    const cBand = new THREE.Color(WING_BAND);
    const cEdge = new THREE.Color(WING_EDGE);
    const uMid = new THREE.Color(UNDER);
    const uEdge = new THREE.Color(UNDER_EDGE);
    const grid: { p: THREE.Vector3; up: THREE.Color; dn: THREE.Color }[][] = [];
    for (let i = 0; i < lead.length; i++) {
      const row: { p: THREE.Vector3; up: THREE.Color; dn: THREE.Color }[] = [];
      const a = new THREE.Vector3(...lead[i]!);
      const b = new THREE.Vector3(...trail[i]!);
      for (let j = 0; j <= rows; j++) {
        const f = j / rows;
        const p = a.clone().lerp(b, f);
        // A gentle camber: the middle of the chord bellies up a little.
        p.y += 0.12 * Math.sin(Math.PI * f) * (1 - 0.5 * (i / (lead.length - 1)));
        const up = cLead.clone().lerp(cMid, Math.min(1, f * 1.8));
        // Bands across the span (every other column), and the dark trailing edge.
        if ((i + band0) % 3 === 1 && f > 0.2 && f < 0.9) up.lerp(cBand, 0.55);
        if (f > 0.85) up.lerp(cEdge, 0.7);
        const dn = uMid.clone().lerp(uEdge, f > 0.8 ? 0.7 : f * 0.3);
        row.push({ p, up, dn });
      }
      grid.push(row);
    }
    const tri = (a: (typeof grid)[0][0], b: typeof a, c: typeof a, under: boolean) => {
      const off = under ? -0.015 : 0.015;
      const vs = under ? [a, c, b] : [a, b, c];
      for (const v of vs) {
        pos.push(v.p.x, v.p.y + off, v.p.z);
        const k = under ? v.dn : v.up;
        col.push(k.r, k.g, k.b);
      }
    };
    for (let i = 0; i < grid.length - 1; i++)
      for (let j = 0; j < rows; j++) {
        const a = grid[i]![j]!;
        const b = grid[i + 1]![j]!;
        const c = grid[i + 1]![j + 1]!;
        const d = grid[i]![j + 1]!;
        for (const under of [false, true]) {
          tri(a, d, b, under);
          tri(b, d, c, under);
        }
      }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    g.computeVertexNormals();
    return mesh(g, skin);
  };

  const N = 6;
  const span = (f: (t: number) => V3) => Array.from({ length: N }, (_, i) => f(i / (N - 1)));
  const wings: { arm: THREE.Group; hand: THREE.Group; side: number }[] = [];
  for (const side of [1, -1]) {
    // +x is the left wing; the right is mirrored.
    const arm = new THREE.Group();
    arm.position.set(side * 0.34, 0.22, 0.42);
    arm.scale.x = side;
    const wrist: V3 = [2.0, 0.04, 0.22];
    // The arm panel: shoulder to wrist along the front, body flank to the hip behind.
    const armLead = span((t) => [
      wrist[0] * t,
      0.04 * t,
      0.06 + (wrist[2] - 0.06) * t + 0.12 * Math.sin(Math.PI * t),
    ]);
    const armTrail = span((t) => [
      0.05 + (wrist[0] - 0.05) * t,
      0,
      -1.9 + 0.5 * t - 0.12 * Math.sin(Math.PI * t),
    ]);
    arm.add(panel(armLead, armTrail, 3, 0));
    arm.add(tube(armLead.slice(0, N), 0.1, 0.075, body, 5));
    const hand = new THREE.Group();
    hand.position.set(...wrist);
    // The hand panel: the long finger sweeping back to a sharp tip in front, a scalloped
    // trailing edge behind, from the wrist out to the tip.
    const tip: V3 = [3.45, 0.06, -1.15];
    const handLead = span((t) => [
      tip[0] * t,
      tip[1] * t + 0.08 * Math.sin(Math.PI * t),
      tip[2] * t * t,
    ]);
    const handTrail = span((t) => [
      0.0 + tip[0] * t * 0.98,
      0,
      -1.4 + (tip[2] + 1.4) * t + 0.38 * Math.sin(Math.PI * t) + 0.05 * Math.sin(Math.PI * 3 * t),
    ]);
    handTrail[N - 1] = [...tip];
    hand.add(panel(handLead, handTrail, 3, 1));
    hand.add(tube(handLead, 0.075, 0.02, body, 5));
    // A three-clawed thumb at the wrist.
    for (let k = 0; k < 3; k++) {
      const claw = mesh(new THREE.ConeGeometry(0.04, 0.26, 4), black);
      claw.position.set(0.02 + k * 0.05, 0.04, 0.28 + k * 0.03);
      claw.rotation.x = Math.PI / 2 - 0.3;
      hand.add(claw);
    }
    arm.add(hand);
    frame.add(arm);
    wings.push({ arm, hand, side });
  }
  // Little legs trailing back under the tail, with clawed feet.
  for (const s of [-1, 1]) {
    frame.add(
      tube(
        [
          [s * 0.22, -0.22, -0.9],
          [s * 0.3, -0.3, -1.35],
          [s * 0.32, -0.32, -1.8],
        ],
        0.1,
        0.06,
        body,
        5,
      ),
    );
    const foot = mesh(new THREE.ConeGeometry(0.09, 0.4, 4), black);
    foot.rotation.x = -Math.PI / 2;
    foot.position.set(s * 0.32, -0.32, -2.0);
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
