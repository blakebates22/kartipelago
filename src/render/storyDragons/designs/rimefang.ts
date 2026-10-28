/**
 * RIMEFANG, the Snow Kingdom's dragon: the lawyer. Cold, precise, never breaks a rule.
 *
 * Lean and tall and very upright: a slim deep chest on long thin legs, a long elegant neck
 * rising straight up, a narrow angular head held high with half-lidded, judging eyes.
 * Swept-back horns of ice crystal, a frill of crystals at the jaw, a row of translucent
 * shards down the spine and an icy spearhead on the tail. Long, thin, crisp-edged wings
 * like frosted glass. Pale ice and steel blue, with fine navy pinstripes down his back.
 */
import * as THREE from "three";
import { Parts, type V3 } from "../parts";
import { buildEyes } from "../face";
import { bands, scales, smoothstep } from "../hide";
import type { DragonDesign, HeadKit, HeadParts } from "../types";
import { horn } from "../../racers/kit/shapes";
import {
  ball,
  brow,
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

const PALE = "#d6e6f4";
const STEEL = "#6f8fb6";
const NAVY = "#2c3e66";
const WHITE = "#f4f9ff";

/** A shard of ice: a faceted horn. */
const shard = (p: Parts, base: V3, tip: V3, r: number, bend: V3 = [0, 0, 0]) =>
  p.both(horn(base, tip, r, "#ffffff", bend, 5), (q) => {
    const L = Math.hypot(tip[0] - base[0], tip[1] - base[1], tip[2] - base[2]);
    const d = Math.hypot(q.x - base[0], q.y - base[1], q.z - base[2]);
    return mix("#8ac8f0", "#f4fcff", d / L);
  });

function head(kit: HeadKit): HeadParts {
  const head = new THREE.Group();
  head.name = "rimefang head";
  // A narrow, long, angular skull: a pinched (diamond-ish) section down a pointed snout.
  const S: Sec[] = [
    { at: [0, 0.2, -1.2], rx: 1.35, ry: 1.45, sq: 2.0, flat: 0.25 },
    { at: [0, 0.45, 0.6], rx: 1.6, ry: 1.5, sq: 2.2, flat: 0.4 },
    { at: [0, 0.38, 2.4], rx: 1.45, ry: 1.25, sq: 2.1, flat: 0.5 },
    { at: [0, 0.02, 4.4], rx: 1.05, ry: 0.95, sq: 1.85, flat: 0.45 },
    { at: [0, -0.25, 6.2], rx: 0.8, ry: 0.72, sq: 1.85, flat: 0.4 },
    { at: [0, -0.36, 7.3], rx: 0.55, ry: 0.5, sq: 1.9, flat: 0.35 },
    { at: [0, -0.42, 7.85], rx: 0.18, ry: 0.18, sq: 2, flat: 0.3 },
  ];
  const p = new Parts();
  p.add(skull(S, 22, 4), shade(STEEL, PALE, WHITE, 0, 0.55), { rep: [7, 5] });
  // Sharp ridges from the nostrils back over the eyes to the horns.
  for (const side of [1, -1])
    p.add(
      skull(
        [
          { at: [0.55 * side, 0.55, 6.6], rx: 0.08, ry: 0.06 },
          { at: [0.85 * side, 0.95, 4.4], rx: 0.16, ry: 0.13 },
          { at: [1.12 * side, 1.38, 2.6], rx: 0.22, ry: 0.18 },
          { at: [1.0 * side, 1.62, 0.6], rx: 0.2, ry: 0.16 },
          { at: [0.8 * side, 1.5, -0.6], rx: 0.08, ry: 0.06 },
        ],
        8,
        3,
        { start: true, end: true },
      ),
      STEEL,
    );
  // Cheekbones, high and sharp.
  p.both(ball(12, 8), shade(STEEL, PALE, WHITE), {
    p: [1.32, -0.05, 0.9],
    s: [0.45, 0.6, 1.4],
    r: [0.1, 0.2, 0.3],
  });
  // Nostrils: neat slits.
  p.both(ball(8, 6), NAVY, { p: [0.3, -0.05, 7.25], s: [0.1, 0.07, 0.28], r: [0, 0.4, 0] });
  // The mouth's roof.
  head.add(
    new THREE.Mesh(
      new THREE.SphereGeometry(1, 12, 8).scale(0.85, 0.2, 2.8).translate(0, -0.35, 4.2),
      kit.heat,
    ),
  );
  // Fine, even, needle teeth.
  teeth(p, {
    z0: 2.6,
    z1: 7.1,
    count: 8,
    x: (z) => sectionAt(S, z).rx * 0.78,
    y: (z) => surfaceY(S, 0.78, z) + 0.06,
    len: (k) => (k > 0.55 && k < 0.7 ? 0.62 : 0.34),
    r: 0.1,
    down: true,
    color: WHITE,
  });
  head.add(mesh(p, kit.skin));
  // Crystal horns: two long ones swept straight back, two shorter below them, and a
  // frill of shards at the jaw's corners.
  const g = new Parts();
  shard(g, [0.85, 1.45, -0.4], [1.7, 3.0, -6.6], 0.5, [0.1, 0.9, 0]);
  shard(g, [1.15, 0.75, -0.6], [2.1, 1.15, -4.4], 0.32, [0.1, 0.4, 0]);
  shard(g, [0.55, 1.7, 0.4], [0.75, 2.5, -2.4], 0.2, [0, 0.4, 0]);
  for (let k = 0; k < 3; k++)
    shard(
      g,
      [1.1, -0.55 - k * 0.2, 0.0 - k * 0.15],
      [1.9 + k * 0.1, -0.7 - k * 0.6, -1.9 + k * 0.3],
      0.17,
    );
  head.add(mesh(g, kit.glass));

  // The jaw: narrow and long.
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.42, -0.2);
  head.add(jaw);
  const J: Sec[] = [
    { at: [0, 0.0, -0.8], rx: 1.2, ry: 0.6, sq: 2.0, flat: -0.7 },
    { at: [0, -0.08, 1.2], rx: 1.25, ry: 0.72, sq: 2.1, flat: -0.8 },
    { at: [0, -0.1, 4.0], rx: 0.92, ry: 0.58, sq: 2.0, flat: -0.8 },
    { at: [0, -0.05, 6.4], rx: 0.68, ry: 0.44, sq: 1.9, flat: -0.75 },
    { at: [0, 0.0, 7.5], rx: 0.4, ry: 0.3, sq: 1.9, flat: -0.7 },
    { at: [0, 0.02, 7.85], rx: 0.12, ry: 0.1, sq: 2, flat: -0.6 },
  ];
  const j = new Parts();
  j.add(skull(J, 20, 4), shade("#5a6a8a", PALE, WHITE, 0, 0.5), { rep: [6, 4] });
  j.add(ball(10, 6), "#6a4a6a", { p: [0, 0.12, 4.0], s: [0.65, 0.16, 2.8] });
  teeth(j, {
    z0: 2.6,
    z1: 6.9,
    count: 7,
    x: (z) => sectionAt(J, z).rx * 0.75,
    y: (z) => surfaceY(J, 0.75, z, true) - 0.05,
    len: () => 0.3,
    r: 0.09,
    down: false,
    color: WHITE,
  });
  jaw.add(mesh(j, kit.skin));
  // A dignified shard of a beard under the chin.
  const cb = new Parts();
  cb.add(horn([0, -0.55, 5.6], [0, -2.0, 4.4], 0.18, "#ffffff", [0, 0, 0.2], 5), (q) =>
    mix("#8ac8f0", "#f4fcff", (-q.y - 0.55) / 1.4),
  );
  jaw.add(mesh(cb, kit.glass));

  // Calm, half-lidded eyes: ice-blue, thin slits. Judging you.
  const ey = 1.0;
  const ez = 2.6;
  const eyes = buildEyes(
    head,
    {
      at: [surfaceX(S, ey, ez) - 0.2, ey, ez],
      size: [0.58, 0.48, 0.52],
      yaw: 0.36,
      pitch: 0.02,
      sclera: "#eef8ff",
      iris: "#8ad8ff",
      irisRim: "#2a6ab8",
      irisSize: 0.74,
      pupil: "slit",
      pupilSize: 0.14,
      lid: PALE,
      liner: NAVY,
      rest: 0.44,
      lower: 0.12,
      slant: 0.04,
    },
    { eye: kit.eye, iris: kit.iris, skin: kit.skin },
  );
  if (kit.iris instanceof THREE.MeshLambertMaterial) {
    kit.iris.emissive.set("#3a9ad8");
    kit.iris.emissiveIntensity = 0.35;
  }
  // Thin, straight brows: one raised a touch (sceptical).
  const by = 1.5;
  const bz = 2.6;
  const brows = [1, -1].map((side) =>
    brow(
      head,
      [surfaceX(S, by, bz) - 0.18, by, bz],
      side,
      (b, mirror) =>
        b.add(ball(10, 6), STEEL, { s: [0.62, 0.15, 1.05], r: [0.05, 0.25, -0.12], mirror }),
      kit.skin,
    ),
  );
  return {
    head,
    jaw,
    jawOpen: 0.5,
    eyes,
    brows,
    mouth: [0, -0.55, 7.9],
    nose: [0.3, -0.05, 7.4],
    sway: [],
    heat: kit.heat,
  };
}

/** The tail's icy spearhead. */
function blade(kit: HeadKit) {
  const g = new THREE.Group();
  const p = new Parts();
  p.add(new THREE.OctahedronGeometry(1, 0), (q) => mix("#9ad4f8", "#f4fcff", (q.z + 1) / 2), {
    p: [0, 0, 1.9],
    s: [0.9, 0.28, 2.4],
  });
  for (const s of [1, -1])
    p.add(new THREE.OctahedronGeometry(1, 0), "#cfeeff", {
      p: [0.7 * s, 0, 0.5],
      s: [0.6, 0.18, 1.1],
      r: [0, 0.6 * s, 0],
    });
  g.add(mesh(p, kit.glass));
  return g;
}

export const RIMEFANG: DragonDesign = {
  id: "rimefang",
  spine: [
    [-34, 4.0, 0.35, 0.35],
    [-30, 5.0, 0.6, 0.6],
    [-26, 6.2, 0.9, 0.9],
    [-22, 7.4, 1.25, 1.25],
    [-18, 8.6, 1.65, 1.65],
    [-14, 9.7, 2.1, 2.1],
    [-10.5, 10.6, 2.6, 2.6],
    [-7, 11.3, 3.0, 3.1, 2, 0.1], // hips
    [-3.5, 12.0, 3.15, 3.35, 2, 0.1],
    [0, 13.0, 3.3, 3.75, 2, 0.05],
    [3.2, 14.4, 3.3, 3.95],
    [5.8, 16.0, 2.95, 3.35], // shoulders
    [7.4, 18.5, 2.35, 2.45],
    [8.4, 21.1, 1.95, 2.05],
    [9.0, 23.7, 1.72, 1.78],
    [9.6, 26.1, 1.58, 1.62],
    [10.7, 28.0, 1.45, 1.48],
    [12.2, 29.0, 1.2, 1.25],
  ],
  hip: 7,
  shoulder: 11,
  neck: 6,
  headScale: 1.05,
  headTilt: 0.05,
  neckInto: 1.2,
  rings: 124,
  sides: 22,
  cells: 22,
  bump: 0.03,
  glow: "#bfe8ff",
  hide: (h) => {
    const sc = scales(h.cu, h.cv * 1.1, 22);
    const c = new THREE.Color(PALE).lerp(new THREE.Color(STEEL), smoothstep(0.15, 0.85, h.up));
    c.multiplyScalar(0.95 + 0.08 * sc.r);
    let height = 0.3 + 0.7 * sc.h;
    // Pinstripes down the back and flanks.
    const pin = (((h.u * 22) % 1) + 1) % 1;
    if (h.up > -0.1 && Math.abs(pin - 0.5) < 0.05) c.lerp(new THREE.Color(NAVY), 0.75);
    // A pale belly of fine plates.
    const belly = smoothstep(-0.45, -0.75, h.up);
    if (belly > 0) {
      const b = bands(h.s, 0.95);
      c.lerp(new THREE.Color(WHITE).multiplyScalar(0.9 + 0.1 * b), belly);
      height = height * (1 - belly) + (0.3 + 0.6 * b) * belly;
    }
    // Frost on the tips of the scales (a faint shine).
    const glow = sc.h > 0.85 && sc.r > 0.7 ? 0.25 : 0;
    return { color: c, height, glow };
  },
  legs: {
    hind: {
      hip: [2.6, 10.4, -7],
      foot: [3.2, -6.0],
      upper: 6,
      lower: 5.5,
      meta: [0, 3.2, -1.8],
      radii: [2.6, 1.9, 1.1, 0.72, 0.62],
      knee: 1,
      toes: 3,
      toeLen: 1.7,
      toeR: 0.55,
      claw: 1.2,
      color: [PALE, STEEL],
      clawColor: "#cfeeff",
    },
    fore: {
      hip: [2.6, 13.6, 5.0],
      foot: [3.0, 7.8],
      upper: 6.2,
      lower: 6.0,
      meta: [0, 2.2, -0.6],
      radii: [2.6, 1.8, 1.05, 0.7, 0.62],
      knee: -1,
      toes: 3,
      toeLen: 1.6,
      toeR: 0.52,
      claw: 1.15,
      color: [PALE, STEEL],
      clawColor: "#cfeeff",
    },
  },
  wings: {
    root: [1.8, 18.6, 4.8],
    flank: [2.6, 14.5, -4],
    humerus: 6.5,
    forearm: 9,
    fingers: [15, 13, 11, 8.5],
    fan: [-0.08, -1.25],
    boneR: 0.38,
    scallop: 0.12,
    sag: 0.35,
    membrane: "#c4d8ee",
    edge: "#ffffff",
    vein: "#7f9cc4",
    bone: STEEL,
    thumb: 1.0,
    opacity: 0.8,
    glow: "#6aa8e0",
    rest: 0,
  },
  spikes: [
    {
      from: 0.12,
      to: 0.93,
      count: 20,
      size: [0.9, 2.3, 1.4],
      shape: "crystal",
      color: "#9ad4f8",
      tip: "#f4fcff",
      lean: 0.55,
      width: 0.8,
      glass: true,
    },
  ],
  buildHead: head,
  tailTip: blade,
  tailDroop: 0,
  tailDrape: -0.3,
  breath: "frost",
  horn: "#cfeeff",
  manner: {
    sway: 0.2,
    tail: 0.45,
    breathe: 0.6,
    blink: 5.5,
    talk: 0.45,
    nod: 0.5,
    brow: 0.15,
    talkBrow: 0.35,
    smoke: 0,
    aura: 0,
    undulate: 0,
    tilt: 0.07,
    speed: 0.85,
    squint: 0.1,
    quirk: 0.18,
  },
};
