/**
 * LUMEN: a dragon hatchling who lived disguised in a hooded robe, and the golden dragon
 * he grows into.
 *
 * The hatchling: a big round head on a short neck, huge kind eyes (round pupils, the
 * only dragon here without a predator's slit), little budding horns, soft ear-fins, a
 * chubby golden body, stubby wings and a short tail ending in a tuft of light.
 *
 * Grown: slender and tall, the same face matured (the same eyes and ear-fins), long
 * swept gold horns, a soft golden crest down his neck, great wings with glowing veins,
 * sun-markings that glow along his back, and the tuft of light grown into a flame. He
 * breathes golden light, and a glow drifts round him.
 */
import * as THREE from "three";
import { Parts, type V3 } from "../parts";
import { buildEyes } from "../face";
import { bands, scales, smoothstep } from "../hide";
import type { DragonDesign, HeadKit, HeadParts } from "../types";
import {
  ball,
  brow,
  fan,
  hornPaint,
  hornPair,
  mesh,
  mix,
  sectionAt,
  shade,
  skull,
  surfaceX,
  surfaceY,
  teeth,
} from "./common";

type Sec = { at: V3; rx: number; ry: number; sq?: number; flat?: number };

const GOLDEN = "#f2d68a";
const WARM = "#e6b04c";
const CREAM = "#fff3d4";
const GLOW = "#ffd870";
const EYE = "#2a9ac8";

function head(kit: HeadKit, grown: boolean): HeadParts {
  const head = new THREE.Group();
  head.name = grown ? "lumen grown head" : "lumen head";
  // The hatchling's skull is round with a short snout; grown, the snout lengthens.
  const L = grown ? 1.45 : 1;
  const S: Sec[] = [
    { at: [0, 0.5, -1.4], rx: 2.3, ry: 2.4, sq: 2.0, flat: 0.25 },
    { at: [0, 0.9, 0.4], rx: 2.6, ry: 2.5, sq: 2.0, flat: 0.35 },
    { at: [0, 0.6, 2.2], rx: 2.2, ry: 2.0, sq: 2.1, flat: 0.45 },
    { at: [0, 0.0, 2.2 + 1.6 * L], rx: 1.5, ry: 1.35, sq: 2.2, flat: 0.45 },
    { at: [0, -0.25, 2.2 + 2.8 * L], rx: 1.15, ry: 1.0, sq: 2.2, flat: 0.4 },
    { at: [0, -0.3, 2.2 + 3.4 * L], rx: 0.55, ry: 0.5, sq: 2, flat: 0.35 },
  ];
  const tip = 2.2 + 3.4 * L;
  const p = new Parts();
  p.add(
    skull(S, 24, 4),
    (q, n) => {
      const c = shade(WARM, GOLDEN, CREAM, 0, 0.6)(q, n);
      // A sun-mark on the brow.
      if (Math.hypot(q.x, q.z - 1.3) < 0.55 && n.y > 0.6) c.set(grown ? "#fff8e0" : "#ffe9a8");
      return c;
    },
    { rep: [6, 5] },
  );
  p.both(ball(8, 6), "#8a5a20", {
    p: [0.4, 0.15, tip - 0.35],
    s: [0.12, 0.09, 0.16],
    r: [0.4, 0.4, 0],
  });
  head.add(
    new THREE.Mesh(
      new THREE.SphereGeometry(1, 12, 8).scale(1.2, 0.25, 1.4 * L + 0.6).translate(0, -0.6, 3.4),
      kit.heat,
    ),
  );
  teeth(p, {
    z0: tip - 1.6,
    z1: tip - 0.6,
    count: grown ? 3 : 1,
    x: (z) => sectionAt(S, z).rx * 0.62,
    y: (z) => surfaceY(S, 0.62, z) + 0.06,
    len: () => (grown ? 0.42 : 0.3),
    r: 0.12,
    down: true,
    color: "#ffffff",
  });
  // Horns: little buds, or long swept gold ones (and the buds still there below them).
  if (grown) {
    const hb: V3 = [1.1, 2.4, -0.3];
    const ht: V3 = [2.0, 4.4, -5.4];
    hornPair(p, hb, ht, 0.5, hornPaint(hb, ht, "#fff4d8", "#e8b040"), [0, 1.0, 0.8], 12);
    const sb: V3 = [1.6, 1.4, -0.6];
    const st: V3 = [2.6, 1.9, -3.2];
    hornPair(p, sb, st, 0.28, hornPaint(sb, st, "#fff4d8", "#e8b040"), [0, 0.4, 0.3], 8);
  } else {
    const hb: V3 = [1.0, 2.5, -0.1];
    const ht: V3 = [1.4, 3.5, -1.0];
    hornPair(p, hb, ht, 0.4, hornPaint(hb, ht, "#fff4d8", "#f0c050"), [0, 0.2, 0.2], 10);
  }
  head.add(mesh(p, kit.skin));
  // Soft ear-fins.
  for (const sd of [1, -1]) {
    const bases: V3[] = [];
    const tips: V3[] = [];
    const n = 4;
    for (let i = 0; i < n; i++) {
      const a = -0.5 + i * 0.4;
      bases.push([2.1 * sd, 0.9 + a * 0.9, -0.8]);
      const len = (grown ? 3.2 : 2.4) - Math.abs(a) * 0.8;
      tips.push([(2.1 + 1.0 * len * 0.6) * sd, 0.9 + a * 2.2 + 0.5, -0.8 - len]);
    }
    const f = fan(bases, tips, {
      spineR: 0.08,
      spine: WARM,
      color: (_i, along) => new THREE.Color(CREAM).lerp(new THREE.Color(GLOW), along),
      dip: 0.32,
      rows: 3,
    });
    head.add(mesh(f.spines, kit.skin), new THREE.Mesh(f.membrane, kit.fin));
  }

  const jaw = new THREE.Group();
  jaw.position.set(0, -0.55, 0.2);
  head.add(jaw);
  const J: Sec[] = [
    { at: [0, 0.0, -0.9], rx: 1.8, ry: 0.7, sq: 2.1, flat: -0.7 },
    { at: [0, -0.06, 1.0], rx: 1.85, ry: 0.85, sq: 2.1, flat: -0.8 },
    { at: [0, -0.06, 1.8 + 1.4 * L], rx: 1.25, ry: 0.65, sq: 2.1, flat: -0.8 },
    { at: [0, 0.0, 1.8 + 2.7 * L], rx: 0.85, ry: 0.5, sq: 2.1, flat: -0.75 },
    { at: [0, 0.02, 1.8 + 3.1 * L], rx: 0.35, ry: 0.22, sq: 2, flat: -0.6 },
  ];
  const j = new Parts();
  j.add(skull(J, 20, 4), shade(GOLDEN, GOLDEN, CREAM, 0, 0.5), { rep: [5, 4] });
  j.add(ball(10, 6), "#e87a8a", { p: [0, 0.12, 2.6], s: [0.9, 0.16, 1.6 * L] });
  jaw.add(mesh(j, kit.skin));

  // Big, kind eyes: round pupils, wide open, lots of shine.
  const ey = grown ? 1.15 : 1.15;
  const ez = grown ? 2.4 : 2.5;
  const size: V3 = grown ? [0.74, 0.7, 0.66] : [0.9, 0.9, 0.8];
  const eyes = buildEyes(
    head,
    {
      at: [surfaceX(S, ey, ez) - (grown ? 0.26 : 0.48), ey, ez],
      size,
      yaw: grown ? 0.3 : 0.24,
      pitch: -0.02,
      sclera: "#ffffff",
      iris: "#5ac8e8",
      irisRim: "#145a8a",
      irisSize: grown ? 0.76 : 0.8,
      pupil: "round",
      pupilSize: 0.5,
      lid: GOLDEN,
      liner: "#8a5a20",
      rest: grown ? 0.14 : 0.04,
      lower: 0,
      slant: grown ? 0 : -0.1,
    },
    { eye: kit.eye, iris: kit.iris, skin: kit.skin },
  );
  if (kit.iris instanceof THREE.MeshLambertMaterial) {
    kit.iris.emissive.set(EYE);
    kit.iris.emissiveIntensity = 0.35;
  }
  const by = grown ? 1.95 : 2.15;
  const bz = grown ? 2.4 : 2.5;
  const brows = [1, -1].map((side) =>
    brow(
      head,
      [surfaceX(S, by, bz) - 0.3, by, bz],
      side,
      (b, mirror) => b.add(ball(10, 6), WARM, { s: [0.75, 0.18, 0.9], r: [0, 0.3, 0.15], mirror }),
      kit.skin,
    ),
  );
  return {
    head,
    jaw,
    jawOpen: 0.5,
    eyes,
    brows,
    mouth: [0, -0.6, tip + 0.2],
    nose: [0.4, 0.15, tip],
    sway: [],
    heat: kit.heat,
  };
}

/** A tuft of light at the tail's end (it glows: the irises' glowing material). */
const tuft = (big: number) => (kit: HeadKit) => {
  const g = new THREE.Group();
  const p = new Parts();
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2;
    const r = i === 0 ? 0 : 0.5 * big;
    p.add(ball(10, 8), (q) => mix(GLOW, "#fffbe8", (q.z + 1) / 2), {
      p: [Math.cos(a) * r, Math.sin(a) * r, 0.9 * big + (i === 0 ? 0.6 * big : 0)],
      s: [0.6 * big, 0.6 * big, 1.3 * big],
    });
  }
  g.add(new THREE.Mesh(p.build(), kit.iris));
  return g;
};

const hide = (grown: boolean) => (h: Parameters<DragonDesign["hide"]>[0]) => {
  const sc = scales(h.cu, h.cv, 18);
  const c = new THREE.Color(GOLDEN).lerp(new THREE.Color(WARM), smoothstep(0.2, 0.95, h.up));
  c.multiplyScalar(0.96 + 0.06 * sc.r);
  let height = 0.35 + 0.5 * sc.h;
  let glow = 0;
  // Sun-marks down the back: little glowing diamonds (grown, they're bigger).
  const ph = (((h.s / (grown ? 3.0 : 2.4)) % 1) + 1) % 1;
  const d = Math.abs(ph - 0.5) * (grown ? 3.0 : 2.4) + Math.abs(h.u - 0.5) * (grown ? 10 : 14);
  if (h.up > 0.6 && d < (grown ? 0.9 : 0.6)) {
    c.set("#fff3c0");
    glow = grown ? 0.9 : 0.6;
  }
  const belly = smoothstep(-0.45, -0.75, h.up);
  if (belly > 0) {
    const b = bands(h.s, grown ? 1.0 : 0.8);
    c.lerp(new THREE.Color(CREAM).multiplyScalar(0.92 + 0.08 * b), belly);
    height = height * (1 - belly) + (0.3 + 0.5 * b) * belly;
  }
  return { color: c, height, glow };
};

const MANNER = {
  sway: 0.5,
  tail: 1.2,
  breathe: 0.8,
  blink: 3.0,
  talk: 0.55,
  nod: 1.2,
  brow: 0.35,
  talkBrow: 0.4,
  smoke: 0,
  aura: 0.6,
  undulate: 0,
  tilt: 0.14,
  speed: 1.1,
  squint: 0,
  quirk: 0,
};

export const LUMEN: DragonDesign = {
  id: "lumen",
  spine: [
    [-22, 3.0, 0.4, 0.4],
    [-19, 3.6, 0.8, 0.8],
    [-16, 4.6, 1.3, 1.3],
    [-13, 5.8, 1.9, 1.9],
    [-10.5, 7.0, 2.6, 2.6],
    [-8, 8.0, 3.4, 3.4],
    [-5.5, 8.8, 4.2, 4.2, 2, 0.15], // hips
    [-2.5, 9.4, 4.7, 4.8, 2, 0.15],
    [1.0, 10.2, 4.8, 5.0, 2, 0.1],
    [4.0, 11.6, 4.2, 4.4], // shoulders
    [6.0, 13.6, 3.4, 3.5],
    [7.0, 15.4, 3.0, 3.0],
    [8.0, 16.6, 2.6, 2.6],
  ],
  hip: 6,
  shoulder: 9,
  neck: 3,
  headScale: 1.55,
  headTilt: 0.05,
  neckInto: 1.4,
  rings: 100,
  sides: 22,
  cells: 16,
  bump: 0.018,
  glow: "#ffd870",
  hide: hide(false),
  legs: {
    hind: {
      hip: [3.4, 7.6, -5.2],
      foot: [4.2, -4.0],
      upper: 4.0,
      lower: 3.6,
      meta: [0, 1.8, -1.0],
      radii: [3.2, 2.4, 1.6, 1.15, 1.05],
      knee: 1,
      toes: 3,
      toeLen: 1.5,
      toeR: 0.75,
      claw: 0.6,
      color: [GOLDEN, WARM],
      clawColor: "#fff4d8",
    },
    fore: {
      hip: [3.3, 9.6, 3.8],
      foot: [4.0, 6.4],
      upper: 4.6,
      lower: 4.2,
      meta: [0, 1.4, -0.3],
      radii: [3.0, 2.2, 1.5, 1.1, 1.0],
      knee: -1,
      toes: 3,
      toeLen: 1.5,
      toeR: 0.72,
      claw: 0.6,
      color: [GOLDEN, WARM],
      clawColor: "#fff4d8",
    },
  },
  wings: {
    root: [2.4, 15.0, 4.0],
    flank: [3.2, 11.5, -2.5],
    humerus: 3.5,
    forearm: 4.5,
    fingers: [7, 6.4, 5.2],
    fan: [-0.1, -1.3],
    boneR: 0.4,
    scallop: 0.3,
    sag: 1.0,
    membrane: "#f8e8b8",
    edge: "#ffd060",
    vein: "#e8b850",
    bone: WARM,
    thumb: 0.6,
    glow: "#ffc850",
    rest: 0.15,
  },
  spikes: [
    {
      from: 0.15,
      to: 0.9,
      count: 10,
      size: [0.6, 1.2, 0.6],
      shape: "nub",
      color: CREAM,
      tip: "#ffd870",
      lean: 0.3,
      width: 1,
    },
  ],
  buildHead: (kit) => head(kit, false),
  tailTip: tuft(1.2),
  tailDroop: 0,
  tailDrape: 0.8,
  breath: "light",
  horn: "#fff4d8",
  manner: MANNER,
};

export const LUMEN_GROWN: DragonDesign = {
  id: "lumen_grown",
  spine: [
    [-38, 5.0, 0.3, 0.3],
    [-33.5, 5.2, 0.6, 0.6],
    [-29, 5.8, 0.95, 0.95],
    [-24.5, 6.6, 1.35, 1.35],
    [-20, 7.6, 1.8, 1.8],
    [-15.5, 8.6, 2.25, 2.25],
    [-11.5, 9.6, 2.75, 2.75],
    [-7.5, 10.4, 3.2, 3.3, 2, 0.1], // hips
    [-3.8, 11.0, 3.45, 3.6, 2, 0.1],
    [0, 11.8, 3.55, 3.9],
    [3.5, 13.0, 3.45, 3.95],
    [6.2, 14.6, 3.0, 3.4], // shoulders
    [8.0, 17.2, 2.4, 2.5],
    [9.0, 19.9, 2.0, 2.1],
    [9.6, 22.4, 1.8, 1.85],
    [10.6, 24.4, 1.65, 1.7],
    [12.0, 25.6, 1.5, 1.55],
    [13.6, 26.2, 1.25, 1.3],
  ],
  hip: 7,
  shoulder: 11,
  neck: 6,
  headScale: 1.0,
  headTilt: 0.08,
  neckInto: 1.3,
  rings: 124,
  sides: 22,
  cells: 20,
  bump: 0.02,
  glow: "#ffd870",
  hide: hide(true),
  legs: {
    hind: {
      hip: [2.8, 9.6, -7.4],
      foot: [3.4, -6.4],
      upper: 5.8,
      lower: 5.2,
      meta: [0, 2.9, -1.7],
      radii: [3.0, 2.1, 1.25, 0.82, 0.72],
      knee: 1,
      toes: 3,
      toeLen: 1.7,
      toeR: 0.6,
      claw: 1.0,
      color: [GOLDEN, WARM],
      clawColor: "#fff4d8",
    },
    fore: {
      hip: [2.8, 12.4, 5.2],
      foot: [3.2, 8.2],
      upper: 5.8,
      lower: 5.6,
      meta: [0, 2.0, -0.5],
      radii: [2.9, 2.0, 1.2, 0.8, 0.7],
      knee: -1,
      toes: 3,
      toeLen: 1.6,
      toeR: 0.58,
      claw: 1.0,
      color: [GOLDEN, WARM],
      clawColor: "#fff4d8",
    },
  },
  wings: {
    root: [2.0, 17.2, 5.2],
    flank: [2.9, 13, -4],
    humerus: 7,
    forearm: 10,
    fingers: [16, 14.5, 12.5, 10],
    fan: [-0.08, -1.3],
    boneR: 0.42,
    scallop: 0.22,
    sag: 0.8,
    membrane: "#ffe6a0",
    edge: "#fff8e0",
    vein: "#e8a838",
    bone: "#d89a30",
    thumb: 1.0,
    glow: "#ffc850",
    opacity: 0.92,
    rest: 0,
  },
  spikes: [
    {
      from: 0.15,
      to: 0.62,
      count: 12,
      size: [0.6, 1.4, 0.9],
      shape: "spike",
      color: CREAM,
      tip: "#f0c050",
      lean: 0.6,
      width: 0.8,
    },
  ],
  sails: [
    {
      from: 0.64,
      to: 0.97,
      height: (k) => 0.5 + 2.2 * Math.sin(Math.PI * Math.min(1, k * 1.1)) ** 0.7,
      rays: 10,
      color: CREAM,
      edge: GLOW,
    },
  ],
  buildHead: (kit) => head(kit, true),
  tailTip: tuft(1.8),
  tailDroop: 0,
  tailDrape: 0.6,
  breath: "light",
  horn: "#fff4d8",
  manner: { ...MANNER, aura: 0.9, sway: 0.3, nod: 0.9, brow: 0.2, tilt: 0.08, speed: 0.95 },
};
