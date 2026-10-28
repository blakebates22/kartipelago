/**
 * TIDEWYRM, the Tropic Isles' dragon: the trickster. Greedy, sly, charming.
 *
 * A serpent: a long eel's body slung low on four short webbed legs, weaving as he rests,
 * and a neck that rises in a cobra's S to a broad flat head with a wide, sly grin, long
 * drooping whiskers and lazy half-lidded eyes. No great wings: webbed fins, and a fin
 * down his back to the paddle of his tail. Teal and deep-sea blue, a glowing pale line
 * down his belly and glowing spots along his flanks, and gold: rings on his horns, a
 * band on his tail. He breathes a jet of water.
 */
import * as THREE from "three";
import { Parts, type V3 } from "../parts";
import { buildEyes } from "../face";
import { noise, scales, smoothstep } from "../hide";
import type { DragonDesign, HeadKit, HeadParts } from "../types";
import { tube } from "../../racers/kit/shapes";
import {
  ball,
  brow,
  fan,
  hornPaint,
  hornPair,
  mesh,
  sectionAt,
  shade,
  skull,
  surfaceX,
  surfaceY,
  teeth,
} from "./common";

type Sec = { at: V3; rx: number; ry: number; sq?: number; flat?: number };

const TEAL = "#1f8f8c";
const DEEP = "#0e3a4c";
const PALE = "#bff7e8";
const GOLD = "#f2c040";
const FIN = "#2fb0a6";

function head(kit: HeadKit): HeadParts {
  const head = new THREE.Group();
  head.name = "tidewyrm head";
  // Broad and flat, like a catfish's.
  const S: Sec[] = [
    { at: [0, 0.2, -1.3], rx: 1.75, ry: 1.45, sq: 2.2, flat: 0.3 },
    { at: [0, 0.35, 0.5], rx: 2.15, ry: 1.45, sq: 2.4, flat: 0.4 },
    { at: [0, 0.3, 2.4], rx: 2.0, ry: 1.2, sq: 2.5, flat: 0.45 },
    { at: [0, 0.05, 4.4], rx: 1.65, ry: 0.95, sq: 2.6, flat: 0.45 },
    { at: [0, -0.1, 6.2], rx: 1.4, ry: 0.8, sq: 2.6, flat: 0.4 },
    { at: [0, -0.15, 7.2], rx: 1.0, ry: 0.6, sq: 2.4, flat: 0.35 },
    { at: [0, -0.18, 7.6], rx: 0.45, ry: 0.3, sq: 2, flat: 0.3 },
  ];
  const p = new Parts();
  const lip = (z: number) => surfaceY(S, 0.85, z) + 0.12;
  p.add(
    skull(S, 22, 4),
    (q, n) => {
      const c = shade(DEEP, TEAL, PALE, 0, 0.55)(q, n);
      // The grin: a dark line curling up at the corners of the mouth.
      const yl = lip(q.z) + Math.max(0, 1.9 - q.z) * 0.32;
      if (Math.abs(q.x) > 1.0 && q.z < 2.4 && q.z > -0.4 && Math.abs(q.y - yl) < 0.1)
        c.set("#06202a");
      // Glowing freckles on the cheeks.
      if (n.y < 0.4 && n.y > -0.3 && noise(q.z * 3.1, q.y * 3.1) > 0.8) c.set(PALE);
      return c;
    },
    { rep: [7, 5] },
  );
  // Nostrils on top of the snout.
  p.both(ball(8, 6), "#05181e", { p: [0.45, 0.62, 6.9], s: [0.16, 0.1, 0.2], r: [0.5, 0.3, 0] });
  head.add(
    new THREE.Mesh(
      new THREE.SphereGeometry(1, 12, 8).scale(1.4, 0.2, 2.8).translate(0, -0.3, 4.0),
      kit.heat,
    ),
  );
  teeth(p, {
    z0: 3.0,
    z1: 7.0,
    count: 6,
    x: (z) => sectionAt(S, z).rx * 0.8,
    y: (z) => surfaceY(S, 0.8, z) + 0.06,
    len: (k) => (k > 0.8 ? 0.6 : 0.3),
    r: 0.12,
    down: true,
    color: "#f4fff8",
  });
  // Little swept horns, each wearing two gold rings.
  const hb: V3 = [0.95, 1.15, -0.4];
  const ht: V3 = [1.5, 2.6, -3.0];
  hornPair(p, hb, ht, 0.34, hornPaint(hb, ht, DEEP, "#7ad8c8"), [0, 0.5, 0.3], 10);
  for (const k of [0.3, 0.55])
    for (const sd of [1, -1]) {
      const at = new THREE.Vector3(...hb).lerp(new THREE.Vector3(...ht), k);
      p.add(new THREE.TorusGeometry(0.34 * (1 - k * 0.55), 0.09, 6, 14), GOLD, {
        p: [at.x * sd, at.y + k * 0.25, at.z],
        r: [1.2, 0, 0.3 * sd],
      });
    }
  head.add(mesh(p, kit.skin));
  // Gill frills behind the cheeks.
  for (const sd of [1, -1]) {
    const bases: V3[] = [];
    const tips: V3[] = [];
    for (let i = 0; i < 5; i++) {
      const a = -0.7 + i * 0.35;
      bases.push([1.75 * sd, 0.2 + a * 0.6, -0.6]);
      tips.push([(2.6 + Math.cos(a) * 0.6) * sd, 0.2 + a * 2.0, -2.6 - Math.cos(a) * 0.4]);
    }
    const f = fan(bases, tips, {
      spineR: 0.07,
      spine: DEEP,
      color: (_i, along) => new THREE.Color(FIN).lerp(new THREE.Color(PALE), along * along),
      dip: 0.3,
      rows: 3,
    });
    head.add(mesh(f.spines, kit.skin), new THREE.Mesh(f.membrane, kit.fin));
  }
  // Whiskers: two long ones from the upper lip, two short ones on the chin.
  const sway: HeadParts["sway"] = [];
  const whisker = (to: THREE.Object3D, at: V3, pts: V3[], r: number, phase: number) => {
    const g = new THREE.Group();
    g.position.set(...at);
    const w = new Parts().add(
      tube(pts, [r * 1.5, r * 1.1, r * 0.75, r * 0.3], [TEAL, FIN, "#7ad8c8", PALE], { sides: 8 }),
      null,
    );
    g.add(mesh(w, kit.skin));
    to.add(g);
    sway.push({ obj: g, amount: 0.12, phase });
  };
  for (const sd of [1, -1])
    whisker(
      head,
      [1.25 * sd, -0.15, 6.5],
      [
        [0, 0, 0],
        [0.9 * sd, -0.4, 0.8],
        [1.7 * sd, -1.4, 1.1],
        [2.2 * sd, -2.9, 0.8],
      ],
      0.14,
      sd,
    );

  // The jaw: wide, a sly turned-up line at the corners.
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.32, -0.3);
  head.add(jaw);
  const J: Sec[] = [
    { at: [0, 0.0, -0.9], rx: 1.7, ry: 0.65, sq: 2.3, flat: -0.7 },
    { at: [0, -0.06, 1.2], rx: 1.9, ry: 0.78, sq: 2.4, flat: -0.8 },
    { at: [0, -0.08, 4.0], rx: 1.55, ry: 0.66, sq: 2.5, flat: -0.8 },
    { at: [0, -0.04, 6.4], rx: 1.32, ry: 0.55, sq: 2.5, flat: -0.78 },
    { at: [0, 0.0, 7.5], rx: 0.95, ry: 0.42, sq: 2.3, flat: -0.72 },
    { at: [0, 0.02, 7.9], rx: 0.35, ry: 0.2, sq: 2, flat: -0.6 },
  ];
  const j = new Parts();
  j.add(skull(J, 20, 4), shade(TEAL, TEAL, PALE, 0, 0.5), { rep: [6, 4] });
  j.add(ball(10, 6), "#c85a7a", { p: [0, 0.12, 4.0], s: [1.0, 0.16, 2.8] });
  teeth(j, {
    z0: 3.2,
    z1: 7.0,
    count: 5,
    x: (z) => sectionAt(J, z).rx * 0.78,
    y: (z) => surfaceY(J, 0.78, z, true) - 0.05,
    len: () => 0.3,
    r: 0.11,
    down: false,
    color: "#f4fff8",
  });
  jaw.add(mesh(j, kit.skin));
  for (const sd of [1, -1])
    whisker(
      jaw,
      [0.6 * sd, -0.55, 6.6],
      [
        [0, 0, 0],
        [0.2 * sd, -0.6, 0.2],
        [0.3 * sd, -1.3, 0.0],
        [0.3 * sd, -1.8, -0.3],
      ],
      0.1,
      2 + sd,
    );

  // Lazy, sly eyes: green-gold with a goat's bar pupil, lids low, a squint.
  const ey = 1.05;
  const ez = 2.4;
  const eyes = buildEyes(
    head,
    {
      at: [surfaceX(S, ey, ez) - 0.18, ey, ez],
      size: [0.64, 0.56, 0.56],
      yaw: 0.42,
      pitch: -0.05,
      sclera: "#f2ffe8",
      iris: "#c8e83a",
      irisRim: "#3a8a2a",
      irisSize: 0.8,
      pupil: "bar",
      pupilSize: 0.26,
      lid: TEAL,
      liner: DEEP,
      rest: 0.4,
      lower: 0.28,
      slant: 0.12,
    },
    { eye: kit.eye, iris: kit.iris, skin: kit.skin },
  );
  if (kit.iris instanceof THREE.MeshLambertMaterial) kit.iris.emissive.set("#7ab82a");
  const by = 1.55;
  const bz = 2.4;
  const brows = [1, -1].map((side) =>
    brow(
      head,
      [surfaceX(S, by, bz) - 0.15, by, bz],
      side,
      (b, mirror) =>
        b.add(ball(10, 6), DEEP, { s: [0.7, 0.18, 1.1], r: [0.05, 0.3, -0.2], mirror }),
      kit.skin,
    ),
  );
  return {
    head,
    jaw,
    jawOpen: 0.5,
    eyes,
    brows,
    mouth: [0, -0.45, 7.7],
    nose: [0.45, 0.62, 7.0],
    sway,
    heat: kit.heat,
  };
}

/** The tail's paddle, and a gold band round the tail (greedy). */
function paddle(kit: HeadKit) {
  const g = new THREE.Group();
  const bases: V3[] = [];
  const tips: V3[] = [];
  for (let i = 0; i < 7; i++) {
    const th = -1.3 + (2.6 * i) / 6;
    const L = 4.6 - Math.abs(th) * 1.4;
    bases.push([0, Math.sin(th) * 0.2, 0]);
    tips.push([0, Math.sin(th) * L, Math.cos(th) * L * 0.9 + 0.8]);
  }
  const f = fan(bases, tips, {
    spineR: 0.09,
    spine: DEEP,
    color: (_i, along) => new THREE.Color(FIN).lerp(new THREE.Color(PALE), along * along),
    dip: 0.22,
    rows: 4,
  });
  g.add(mesh(f.spines, kit.skin), new THREE.Mesh(f.membrane, kit.fin));
  const ring = new Parts().add(new THREE.TorusGeometry(0.62, 0.16, 8, 18), GOLD, {
    p: [0, 0, -2.2],
  });
  g.add(mesh(ring, kit.skin));
  return g;
}

export const TIDEWYRM: DragonDesign = {
  id: "tidewyrm",
  spine: [
    [-46, 2.2, 0.25, 0.4],
    [-41, 2.4, 0.55, 0.75],
    [-36, 2.6, 0.9, 1.1],
    [-31, 2.9, 1.3, 1.5],
    [-26, 3.3, 1.7, 1.9],
    [-21, 3.8, 2.1, 2.3],
    [-16, 4.3, 2.45, 2.6],
    [-11.5, 4.8, 2.7, 2.8, 2, 0.25], // hips
    [-7, 5.1, 2.9, 3.0, 2, 0.25],
    [-2.5, 5.4, 3.0, 3.1, 2, 0.25],
    [2, 5.9, 3.0, 3.1, 2, 0.2],
    [6, 6.8, 2.8, 2.9, 2, 0.15], // shoulders
    [8.6, 8.8, 2.4, 2.5],
    [9.6, 11.6, 2.1, 2.2],
    [9.4, 14.4, 1.9, 2.0],
    [9.6, 17.0, 1.75, 1.8],
    [10.8, 19.0, 1.6, 1.65],
    [12.6, 19.8, 1.35, 1.4],
  ],
  hip: 7,
  shoulder: 11,
  neck: 6,
  headScale: 1.15,
  headTilt: 0.1,
  neckInto: 1.2,
  rings: 140,
  sides: 20,
  cells: 18,
  bump: 0.018,
  glow: "#9af8e0",
  hide: (h) => {
    const sc = scales(h.cu, h.cv * 1.3, 18);
    const c = new THREE.Color(TEAL).lerp(new THREE.Color(DEEP), smoothstep(0.0, 0.8, h.up));
    c.multiplyScalar(0.95 + 0.08 * sc.r);
    // Darker mottling down the back.
    if (h.up > 0.2 && noise(h.s * 0.6, h.u * 30) > 0.62) c.multiplyScalar(0.75);
    let glow = 0;
    // A glowing line down the belly.
    const belly = Math.min(h.u, 1 - h.u);
    if (belly < 0.09) {
      c.lerp(new THREE.Color(PALE), smoothstep(0.09, 0.05, belly));
      glow = smoothstep(0.06, 0.02, belly) * 0.8;
    }
    // Rows of glowing spots along the flanks.
    for (const u0 of [0.2, 0.8]) {
      const ds = (((h.s / 2.4) % 1) + 1) % 1;
      const d = Math.hypot((ds - 0.5) * 2.4, (h.u - u0) * 16);
      if (d < 0.32 && h.s > 3) {
        c.set(PALE);
        glow = Math.max(glow, 1 - d / 0.32);
      }
    }
    return { color: c, height: 0.4 + 0.5 * sc.h, glow };
  },
  legs: {
    hind: {
      hip: [2.4, 3.6, -10.5],
      foot: [3.8, -10],
      upper: 2.4,
      lower: 2.2,
      meta: [0, 1.1, -0.6],
      radii: [2.0, 1.4, 0.9, 0.6, 0.55],
      knee: 1,
      toes: 4,
      toeLen: 1.3,
      toeR: 0.42,
      claw: 0.6,
      color: [TEAL, DEEP],
      clawColor: "#e8f8f0",
    },
    fore: {
      hip: [2.4, 5.0, 4.4],
      foot: [3.8, 5.5],
      upper: 2.6,
      lower: 2.4,
      meta: [0, 1.1, -0.3],
      radii: [2.0, 1.3, 0.85, 0.6, 0.55],
      knee: -1,
      toes: 4,
      toeLen: 1.3,
      toeR: 0.42,
      claw: 0.6,
      color: [TEAL, DEEP],
      clawColor: "#e8f8f0",
    },
  },
  wings: {
    root: [2.2, 7.6, 5.0],
    flank: [2.7, 5.8, 0.5],
    humerus: 2.5,
    forearm: 3.0,
    fingers: [9, 9.5, 9, 8, 6.5],
    fan: [0.1, -1.5],
    boneR: 0.22,
    scallop: 0.4,
    sag: 0.6,
    membrane: FIN,
    edge: PALE,
    vein: "#127070",
    bone: "#1a8a84",
    thumb: 0.4,
    opacity: 0.94,
    rest: 0.4,
  },
  spikes: [],
  sails: [
    {
      from: 0.03,
      to: 0.68,
      height: (k) => 0.4 + 1.9 * Math.sin(Math.PI * Math.min(1, k * 1.15)) ** 0.6,
      rays: 22,
      color: FIN,
      edge: PALE,
      opacity: 0.92,
    },
    {
      from: 0.02,
      to: 0.24,
      height: (k) => 0.3 + 1.6 * Math.sin(Math.PI * k) ** 0.7,
      rays: 8,
      color: FIN,
      edge: PALE,
      around: Math.PI,
      opacity: 0.92,
    },
  ],
  buildHead: head,
  tailTip: paddle,
  tailDroop: 0,
  tailDrape: 2.2,
  breath: "water",
  horn: GOLD,
  manner: {
    sway: 0.4,
    tail: 1.4,
    breathe: 0.6,
    blink: 4.2,
    talk: 0.6,
    nod: 1.0,
    brow: 0.1,
    talkBrow: 0.4,
    smoke: 0,
    aura: 0,
    undulate: 0.7,
    tilt: 0.22,
    speed: 0.95,
    squint: 0.25,
    quirk: 0.35,
  },
};
