/**
 * SCORCHWIND, Desert World's dragon: the showman. Vain, theatrical.
 *
 * Lithe and long, with a proud swan's curve of a neck and a handsome head: arched,
 * expressive brows (one forever raised), eyes lined in kohl and turquoise, a crest, and a
 * great fan of a frill behind his head that he flares when he talks. A tall sail runs down
 * his back and his long sweeping tail ends in a painted fan. Sand and gold, with bold
 * maroon stripes and a row of diamonds down the spine. He breathes a whirling sandstorm.
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
  sectionAt,
  shade,
  skull,
  surfaceX,
  surfaceY,
  teeth,
} from "./common";

type Sec = { at: V3; rx: number; ry: number; sq?: number; flat?: number };

const SAND = "#dcae62";
const GOLD = "#f0c64c";
const MAROON = "#7a2416";
const CREAM = "#f6e4b4";
const TEAL = "#27b3a6";
const KOHL = "#2a1006";

/** Showy colours for a fan: gold to turquoise at the edge, maroon bands. */
const showy = (i: number, along: number) => {
  const c = new THREE.Color(GOLD).lerp(new THREE.Color("#e8902a"), along * 0.6);
  if (along > 0.82) c.lerp(new THREE.Color(TEAL), 0.9);
  else if (Math.abs(along - 0.55) < 0.08) c.lerp(new THREE.Color(MAROON), 0.85);
  void i;
  return c;
};

function head(kit: HeadKit): HeadParts {
  const head = new THREE.Group();
  head.name = "scorchwind head";
  const S: Sec[] = [
    { at: [0, 0.3, -1.3], rx: 1.6, ry: 1.6, sq: 2.1, flat: 0.3 },
    { at: [0, 0.6, 0.5], rx: 1.95, ry: 1.7, sq: 2.3, flat: 0.45 },
    { at: [0, 0.5, 2.3], rx: 1.75, ry: 1.45, sq: 2.3, flat: 0.5 },
    { at: [0, 0.15, 4.2], rx: 1.25, ry: 1.1, sq: 2.4, flat: 0.45 },
    { at: [0, -0.05, 5.9], rx: 1.05, ry: 0.92, sq: 2.4, flat: 0.4 },
    { at: [0, -0.1, 6.9], rx: 0.8, ry: 0.72, sq: 2.2, flat: 0.35 },
    { at: [0, -0.12, 7.3], rx: 0.35, ry: 0.32, sq: 2, flat: 0.3 },
  ];
  const ey = 1.12;
  const ez = 2.6;
  const ex = surfaceX(S, ey, ez) - 0.22;
  const p = new Parts();
  p.add(
    skull(S, 22, 4),
    (q, n) => {
      const c = shade(GOLD, SAND, CREAM, 0, 0.6)(q, n);
      // A turquoise flash sweeping back from each eye, and a maroon blaze down the nose.
      const d = Math.hypot(q.y - ey - (q.z - ez) * -0.25, (q.z - ez + 0.6) * 0.35);
      if (Math.abs(q.x) > 0.6 && d < 0.42 && q.z < ez + 0.4) c.lerp(new THREE.Color(TEAL), 0.85);
      if (Math.abs(q.x) < 0.32 && n.y > 0.5 && q.z > 1.5) c.lerp(new THREE.Color(MAROON), 0.8);
      return c;
    },
    { rep: [7, 5] },
  );
  // Nostrils with a showman's flare.
  p.both(ball(8, 6), KOHL, { p: [0.36, 0.42, 6.95], s: [0.16, 0.1, 0.24], r: [0.4, 0.5, 0] });
  // The mouth's roof.
  head.add(
    new THREE.Mesh(
      new THREE.SphereGeometry(1, 12, 8).scale(1.05, 0.22, 2.6).translate(0, -0.42, 4.0),
      kit.heat,
    ),
  );
  teeth(p, {
    z0: 2.7,
    z1: 6.7,
    count: 7,
    x: (z) => sectionAt(S, z).rx * 0.8,
    y: (z) => surfaceY(S, 0.8, z) + 0.06,
    len: (k) => (k > 0.6 && k < 0.75 ? 0.7 : 0.38),
    r: 0.13,
    down: true,
    color: "#fffaf0",
  });
  // Elegant swept horns, gold-tipped.
  const hb: V3 = [0.95, 1.75, -0.2];
  const ht: V3 = [1.7, 3.5, -2.9];
  hornPair(p, hb, ht, 0.36, hornPaint(hb, ht, "#5a2a14", GOLD), [0.1, 0.7, 0.7], 10);
  // The crest: a fin along the top of the skull.
  const cr = fan(
    [
      [0, 1.95, 3.6],
      [0, 2.2, 2.2],
      [0, 2.25, 0.8],
      [0, 2.1, -0.4],
    ],
    [
      [0, 2.7, 3.2],
      [0, 3.6, 1.6],
      [0, 3.9, 0.0],
      [0, 3.2, -1.5],
    ],
    { spineR: 0.09, spine: MAROON, color: showy, dip: 0.2, rows: 3 },
  );
  p.add(cr.spines.build(), null);
  head.add(new THREE.Mesh(cr.membrane, kit.fin));
  head.add(mesh(p, kit.skin));

  // The frill: a fan of spines round the back of the head, flared when he performs.
  const frill = new THREE.Group();
  frill.position.set(0, 0.4, -0.7);
  const N = 9;
  const bases: V3[] = [];
  const tips: V3[] = [];
  for (let i = 0; i < N; i++) {
    const th = -1.75 + (3.5 * i) / (N - 1);
    const L = 3.6 - Math.abs(th) * 0.55;
    const r0 = 1.45;
    bases.push([Math.sin(th) * r0, Math.cos(th) * r0, 0]);
    tips.push([Math.sin(th) * (r0 + L), Math.cos(th) * (r0 + L) - 0.2, -1.5]);
  }
  const fr = fan(bases, tips, {
    spineR: 0.12,
    spine: MAROON,
    color: (i, along) => {
      const c = showy(i, along);
      // Eye-spots on alternate panels.
      if (Math.floor(i) % 2 === 0 && Math.abs(along - 0.72) < 0.07) c.set(KOHL);
      return c;
    },
    dip: 0.3,
    rows: 5,
  });
  frill.add(mesh(fr.spines, kit.skin), new THREE.Mesh(fr.membrane, kit.fin));
  head.add(frill);

  // The jaw: a strong chin, a grin.
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.5, -0.1);
  head.add(jaw);
  const J: Sec[] = [
    { at: [0, 0.0, -0.9], rx: 1.45, ry: 0.75, sq: 2.2, flat: -0.7 },
    { at: [0, -0.08, 1.2], rx: 1.55, ry: 0.92, sq: 2.3, flat: -0.8 },
    { at: [0, -0.1, 3.8], rx: 1.15, ry: 0.78, sq: 2.3, flat: -0.8 },
    { at: [0, -0.05, 6.0], rx: 0.95, ry: 0.62, sq: 2.3, flat: -0.78 },
    { at: [0, 0.02, 7.0], rx: 0.65, ry: 0.5, sq: 2.2, flat: -0.7 },
    { at: [0, 0.05, 7.35], rx: 0.22, ry: 0.2, sq: 2, flat: -0.6 },
  ];
  const j = new Parts();
  j.add(skull(J, 20, 4), shade("#a8582a", SAND, CREAM, 0, 0.5), { rep: [6, 4] });
  j.add(ball(10, 6), "#9a3a3a", { p: [0, 0.14, 3.8], s: [0.8, 0.18, 2.6] });
  teeth(j, {
    z0: 2.7,
    z1: 6.5,
    count: 6,
    x: (z) => sectionAt(J, z).rx * 0.76,
    y: (z) => surfaceY(J, 0.76, z, true) - 0.06,
    len: () => 0.36,
    r: 0.12,
    down: false,
    color: "#fffaf0",
  });
  // A little goatee of spines: a showman's beard.
  for (const x of [-0.25, 0, 0.25])
    j.add(new THREE.ConeGeometry(0.11, 0.8, 6).translate(0, -0.4, 0), MAROON, {
      p: [x, -0.32, 6.2 - Math.abs(x)],
      r: [-0.5, 0, x],
    });
  jaw.add(mesh(j, kit.skin));

  // Gold eyes lined in kohl, lids half-lowered: smug.
  const eyes = buildEyes(
    head,
    {
      at: [ex, ey, ez],
      size: [0.62, 0.54, 0.54],
      yaw: 0.36,
      pitch: 0.02,
      sclera: "#fff6dc",
      iris: "#ffd23a",
      irisRim: "#b0600c",
      irisSize: 0.78,
      pupil: "slit",
      pupilSize: 0.22,
      lid: SAND,
      liner: KOHL,
      rest: 0.3,
      lower: 0.12,
      slant: -0.05,
    },
    { eye: kit.eye, iris: kit.iris, skin: kit.skin },
  );
  if (kit.iris instanceof THREE.MeshLambertMaterial) kit.iris.emissive.set("#ffb020");
  // Big arched brows that never sit still.
  const by = 1.85;
  const bz = 2.55;
  const brows = [1, -1].map((side) =>
    brow(
      head,
      [surfaceX(S, by, bz) - 0.2, by, bz],
      side,
      (b, mirror) => {
        b.add(
          skull(
            [
              { at: [-0.35, -0.1, 1.0], rx: 0.1, ry: 0.08 },
              { at: [0.0, 0.18, 0.2], rx: 0.2, ry: 0.15 },
              { at: [0.25, 0.1, -0.7], rx: 0.17, ry: 0.13 },
              { at: [0.35, -0.2, -1.4], rx: 0.06, ry: 0.05 },
            ],
            8,
            3,
            { start: true, end: true },
          ),
          MAROON,
          { mirror },
        );
      },
      kit.skin,
    ),
  );
  return {
    head,
    jaw,
    jawOpen: 0.55,
    eyes,
    brows,
    mouth: [0, -0.6, 7.4],
    nose: [0.36, 0.42, 7.1],
    sway: [],
    frill,
    heat: kit.heat,
  };
}

/** The tail's painted fan. */
function tailFan(kit: HeadKit) {
  const g = new THREE.Group();
  const bases: V3[] = [];
  const tips: V3[] = [];
  const N = 7;
  for (let i = 0; i < N; i++) {
    const th = -1.05 + (2.1 * i) / (N - 1);
    const L = 6.2 - Math.abs(th) * 1.6;
    bases.push([0, Math.sin(th) * 0.3, 0]);
    tips.push([0, Math.sin(th) * L, Math.cos(th) * L]);
  }
  const f = fan(bases, tips, {
    spineR: 0.16,
    spine: MAROON,
    color: (i, along) => {
      const c = showy(i, along);
      if (Math.abs(along - 0.7) < 0.1 && Math.floor(i) % 2 === 1) c.set(TEAL);
      return c;
    },
    dip: 0.28,
    rows: 5,
  });
  g.add(mesh(f.spines, kit.skin), new THREE.Mesh(f.membrane, kit.fin));
  return g;
}

export const SCORCHWIND: DragonDesign = {
  id: "scorchwind",
  spine: [
    [-40, 7.6, 0.3, 0.3],
    [-35.5, 5.8, 0.55, 0.55],
    [-30.5, 5.0, 0.85, 0.85],
    [-25.5, 5.3, 1.2, 1.2],
    [-20.5, 6.3, 1.6, 1.6],
    [-15.8, 7.5, 2.05, 2.05],
    [-11.6, 8.6, 2.6, 2.6],
    [-8, 9.4, 3.15, 3.2, 2, 0.1], // hips
    [-4, 9.7, 3.55, 3.6, 2, 0.12],
    [0, 10.2, 3.75, 3.9, 2, 0.12],
    [3.6, 11.1, 3.7, 4.0],
    [6.5, 12.6, 3.2, 3.5], // shoulders
    [8.3, 15.0, 2.5, 2.6],
    [8.8, 17.8, 2.05, 2.15],
    [8.7, 20.4, 1.8, 1.85],
    [9.5, 22.6, 1.65, 1.7],
    [11.1, 23.8, 1.5, 1.55],
    [12.7, 24.2, 1.25, 1.3],
  ],
  hip: 7,
  shoulder: 11,
  neck: 6,
  headScale: 1.1,
  headTilt: 0.12,
  neckInto: 1.2,
  rings: 124,
  sides: 22,
  cells: 20,
  bump: 0.035,
  hide: (h) => {
    const sc = scales(h.cu, h.cv, 20);
    const c = new THREE.Color(SAND).lerp(new THREE.Color(GOLD), smoothstep(0.2, 0.9, h.up));
    c.multiplyScalar(0.94 + 0.1 * sc.r);
    let height = 0.3 + 0.7 * sc.h;
    // Bold stripes over the back, tapering down the flanks (body and tail only).
    const rel = h.s / h.length;
    const onBody = h.s < h.shoulder + 2;
    const ph = (((h.s / 3.3) % 1) + 1) % 1;
    const width = 0.16 * smoothstep(-0.4, 0.6, h.up);
    if (onBody && h.up > -0.35 && Math.abs(ph - 0.5) < width) c.lerp(new THREE.Color(MAROON), 0.9);
    // A row of gold diamonds down the spine, outlined in maroon.
    const dph = (((h.s / 3.3 + 0.5) % 1) + 1) % 1;
    const dd = Math.abs(dph - 0.5) * 3.3 + Math.abs(h.u - 0.5) * 18;
    if (h.up > 0.85 && dd < 1.2) c.set(dd < 0.85 ? "#ffd860" : MAROON);
    // A pale belly.
    const belly = smoothstep(-0.45, -0.75, h.up);
    if (belly > 0) {
      const b = bands(h.s, 1.1);
      c.lerp(new THREE.Color(CREAM).multiplyScalar(0.88 + 0.12 * b), belly);
      height = height * (1 - belly) + (0.3 + 0.6 * b) * belly;
    }
    void rel;
    return { color: c, height, glow: 0 };
  },
  legs: {
    hind: {
      hip: [2.9, 8.6, -8],
      foot: [3.6, -7],
      upper: 5.2,
      lower: 4.6,
      meta: [0, 2.6, -1.6],
      radii: [3.0, 2.2, 1.3, 0.85, 0.75],
      knee: 1,
      toes: 3,
      toeLen: 1.7,
      toeR: 0.65,
      claw: 1.1,
      color: [SAND, "#b07a3a"],
      clawColor: "#3a1a0c",
    },
    fore: {
      hip: [2.9, 10.6, 5.6],
      foot: [3.4, 8.6],
      upper: 5.0,
      lower: 4.8,
      meta: [0, 1.9, -0.5],
      radii: [3.0, 2.1, 1.25, 0.82, 0.72],
      knee: -1,
      toes: 3,
      toeLen: 1.6,
      toeR: 0.62,
      claw: 1.05,
      color: [SAND, "#b07a3a"],
      clawColor: "#3a1a0c",
    },
  },
  wings: {
    root: [2.0, 15.2, 5.0],
    flank: [3.0, 11.5, -4.5],
    humerus: 6,
    forearm: 8,
    fingers: [13, 12, 10.5, 8],
    fan: [-0.1, -1.4],
    boneR: 0.45,
    scallop: 0.3,
    sag: 1.0,
    membrane: GOLD,
    edge: TEAL,
    vein: "#c88a2a",
    bone: MAROON,
    thumb: 1.0,
    rest: 0,
    paint: (c, panel, sr) => {
      // Maroon bands across the membrane.
      if (panel >= 0 && Math.abs(sr - 0.5) < 0.07)
        return c.clone().lerp(new THREE.Color(MAROON), 0.85);
      return c;
    },
  },
  spikes: [
    {
      from: 0.7,
      to: 0.95,
      count: 7,
      size: [1.0, 0.8, 0.6],
      shape: "spike",
      color: MAROON,
      tip: GOLD,
      lean: 0.7,
      width: 1,
    },
  ],
  sails: [
    {
      from: 0.3,
      to: 0.67,
      height: (k) => 0.5 + 5.6 * Math.sin(Math.PI * k) ** 0.9,
      rays: 9,
      color: GOLD,
      edge: TEAL,
      paint: (c, k, h) => {
        const ray = Math.abs(((k * 9) % 1) - 0.5) > 0.44;
        if (ray && h < 0.9) return c.clone().lerp(new THREE.Color(MAROON), 0.85);
        if (h > 0.4 && h < 0.7) return c.clone().lerp(new THREE.Color("#e8902a"), 0.6);
        return c;
      },
    },
  ],
  buildHead: head,
  tailTip: tailFan,
  tailDroop: 0,
  tailDrape: 1.2,
  breath: "sand",
  horn: GOLD,
  manner: {
    sway: 0.5,
    tail: 1.3,
    breathe: 0.8,
    blink: 3.2,
    talk: 0.7,
    nod: 1.6,
    brow: 0.25,
    talkBrow: 0.6,
    smoke: 0,
    aura: 0,
    undulate: 0,
    tilt: 0.12,
    speed: 1.1,
    squint: 0.05,
    quirk: 0.45,
  },
};
