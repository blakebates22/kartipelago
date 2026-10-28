/**
 * CINDERJAW, the dragon of Dinosaur Valley: the brute. All fire, no patience.
 *
 * Heavy and hunched, a deep chest and humped shoulders, a short neck as thick as a tree,
 * a broad square head carried low: a jutting underbite with two tusks, a shelf of a brow
 * over small glowing eyes, short bull horns and a stubby nose horn. Scarred, cracked
 * plates with embers glowing in the cracks, a row of blunt plates down the back, short
 * heavy wings and a tail that ends in a spiked club. Smoke curls from his nostrils.
 */
import * as THREE from "three";
import { Parts, clawGeo, type V3 } from "../parts";
import { buildEyes } from "../face";
import { bands, noise, plates, smoothstep } from "../hide";
import type { DragonDesign, HeadKit, HeadParts } from "../types";
import {
  ball,
  brow,
  hornPaint,
  hornPair,
  mesh,
  mix,
  sectionAt,
  skull,
  surfaceX,
  surfaceY,
  teeth,
} from "./common";

type Sec = { at: V3; rx: number; ry: number; sq?: number; flat?: number };

const SIDE = "#6e2618";
const BACK = "#34130e";
const BELLY = "#c8743c";
const LIP = "#8a3a22";
const HORN = "#e6d6b4";
const HORN_TIP = "#3a2418";
const SCAR = "#b8846a";

function head(kit: HeadKit): HeadParts {
  const head = new THREE.Group();
  head.name = "cinderjaw head";
  // The skull and the upper jaw: broad, boxy, flat underneath (the mouth's line), with
  // a stop between the brow and a broad bulldog muzzle.
  const S: Sec[] = [
    { at: [0, 0.4, -1.6], rx: 2.2, ry: 2.2, sq: 2.2, flat: 0.3 },
    { at: [0, 0.7, 0.3], rx: 2.75, ry: 2.3, sq: 2.5, flat: 0.45 },
    { at: [0, 0.55, 2.4], rx: 2.5, ry: 2.0, sq: 2.7, flat: 0.55 },
    { at: [0, 0.15, 4.3], rx: 2.05, ry: 1.55, sq: 2.9, flat: 0.5 },
    { at: [0, 0.0, 6.2], rx: 1.95, ry: 1.45, sq: 3.0, flat: 0.45 },
    { at: [0, -0.05, 7.4], rx: 1.7, ry: 1.25, sq: 2.8, flat: 0.4 },
    { at: [0, -0.1, 8.0], rx: 0.95, ry: 0.75, sq: 2.3, flat: 0.4 },
  ];
  const p = new Parts();
  const skin = (q: THREE.Vector3, n: THREE.Vector3) => {
    const c = new THREE.Color(SIDE);
    c.lerp(new THREE.Color(BACK), smoothstep(0.2, 0.85, n.y));
    // The lip line, lighter.
    c.lerp(new THREE.Color(LIP), smoothstep(-0.2, -0.75, n.y));
    // A paler, scarred muzzle.
    c.lerp(new THREE.Color("#a8502c"), smoothstep(4.0, 6.5, q.z) * smoothstep(0.9, 0.2, n.y) * 0.6);
    // A scar across the left brow and down the cheek; a nick on the right.
    const scar =
      Math.abs(q.y - 1.5 + (q.z - 2.0) * 0.7) < 0.14 && q.x > 0.6 && q.z > 1.0 && q.z < 4.6;
    const nick = Math.abs(q.z - 1.1 - (q.y + 0.2) * 0.4) < 0.12 && q.x < -1.6 && q.y < 0.8;
    if (scar || nick) c.lerp(new THREE.Color(SCAR), 0.85);
    return c;
  };
  p.add(skull(S, 24, 4), skin, { rep: [7, 5] });
  // Heavy jowls flaring at the back of the jaw.
  p.both(ball(12, 9), (_q, nn) => mix(SIDE, BACK, nn.y * 0.8), {
    p: [2.3, -0.2, 0.2],
    s: [0.95, 1.3, 1.8],
    r: [0.2, 0.25, 0],
    rep: [3, 3],
  });
  // The roof of the mouth (it glows when he breathes): hidden till the jaw drops.
  const roof = new THREE.Mesh(
    new THREE.SphereGeometry(1, 12, 8).scale(1.55, 0.3, 3.2).translate(0, -0.55, 4.2),
    kit.heat,
  );
  head.add(roof);
  // Upper teeth: stubby and thick, hanging from the lip, with a pair of fangs.
  teeth(p, {
    z0: 2.9,
    z1: 7.3,
    count: 6,
    x: (z) => sectionAt(S, z).rx * 0.8,
    y: (z) => surfaceY(S, 0.8, z) + 0.12,
    len: (k) => (k > 0.6 && k < 0.8 ? 1.15 : 0.55),
    r: 0.27,
    down: true,
    color: HORN,
  });
  // The nose: a broad pad, flared nostrils, a stubby horn and a smaller one behind.
  p.both(ball(10, 8), "#1e0a06", {
    p: [0.55, 0.62, 7.82],
    s: [0.34, 0.2, 0.28],
    r: [0.4, 0.45, 0],
  });
  p.both(ball(10, 8), SIDE, { p: [0.72, 0.5, 7.45], s: [0.6, 0.5, 0.6], rep: [2, 2] });
  p.add(
    new THREE.ConeGeometry(0.62, 1.9, 10).translate(0, 0.95, 0),
    hornPaint([0, 0, 0], [0, 1.9, 0], HORN, HORN_TIP),
    { p: [0, 1.25, 6.2], r: [0.45, 0, 0] },
  );
  p.add(
    new THREE.ConeGeometry(0.4, 0.9, 10).translate(0, 0.45, 0),
    hornPaint([0, 0, 0], [0, 0.9, 0], HORN, HORN_TIP),
    { p: [0, 1.55, 4.7], r: [0.3, 0, 0] },
  );
  // Short bull horns: out to the sides, then forward and up.
  const hb: V3 = [1.9, 2.3, -0.3];
  const ht: V3 = [4.7, 3.5, 2.0];
  hornPair(p, hb, ht, 0.9, hornPaint(hb, ht, HORN, HORN_TIP), [0.4, -0.9, -0.8], 12);
  // Cheek spikes, swept back.
  const cb: V3 = [2.5, 0.0, -0.4];
  const ct: V3 = [3.7, -0.5, -2.7];
  hornPair(p, cb, ct, 0.45, hornPaint(cb, ct, HORN, HORN_TIP), [0.2, 0, 0], 8);
  // A ridge of knobs down the back of the skull.
  for (let k = 0; k < 3; k++)
    p.add(ball(10, 7), BACK, { p: [0, 2.85 - k * 0.2, 0.6 - k * 1.1], s: [0.5, 0.45, 0.6] });
  head.add(mesh(p, kit.skin));

  // The jaw: massive, jutting past the upper (an underbite), two tusks.
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.6, 0);
  head.add(jaw);
  const j = new Parts();
  const J: Sec[] = [
    { at: [0, 0.0, -1.2], rx: 2.0, ry: 1.0, sq: 2.4, flat: -0.7 },
    { at: [0, -0.05, 1.0], rx: 2.25, ry: 1.35, sq: 2.7, flat: -0.82 },
    { at: [0, -0.05, 3.8], rx: 2.05, ry: 1.3, sq: 2.8, flat: -0.82 },
    { at: [0, 0.0, 6.5], rx: 1.95, ry: 1.15, sq: 2.9, flat: -0.82 },
    { at: [0, 0.1, 8.2], rx: 1.7, ry: 1.0, sq: 2.7, flat: -0.8 },
    { at: [0, 0.2, 8.7], rx: 0.9, ry: 0.6, sq: 2.2, flat: -0.7 },
  ];
  j.add(
    skull(J, 22, 4),
    (_q, n) => {
      const c = new THREE.Color(SIDE).lerp(new THREE.Color(BELLY), smoothstep(-0.2, -0.8, n.y));
      return c.lerp(new THREE.Color("#5a1a14"), smoothstep(0.5, 0.9, n.y));
    },
    { rep: [6, 5] },
  );
  // The tongue on the floor of the mouth.
  j.add(ball(12, 8), "#8a2e2e", { p: [0, 0.2, 4.0], s: [1.25, 0.28, 3.0] });
  teeth(j, {
    z0: 2.8,
    z1: 6.8,
    count: 5,
    x: (z) => sectionAt(J, z).rx * 0.78,
    y: (z) => surfaceY(J, 0.78, z, true) - 0.1,
    len: () => 0.5,
    r: 0.25,
    down: false,
    color: HORN,
  });
  // Tusks, up outside the upper lip.
  const tb: V3 = [1.45, 0.0, 7.5];
  const tt: V3 = [1.95, 2.5, 7.75];
  hornPair(j, tb, tt, 0.3, hornPaint(tb, tt, HORN, "#c8b890"), [0.15, 0, -0.3], 10);
  // Jowl spikes beneath.
  j.both(clawGeo(0.32, 1.2), HORN_TIP, { p: [1.3, -1.1, 1.6], r: [-2.2, 0, 0.3] });
  jaw.add(mesh(j, kit.skin));

  // Small deep-set eyes, glowing under a heavy lid.
  const ey = 1.45;
  const ez = 3.0;
  const eyes = buildEyes(
    head,
    {
      at: [surfaceX(S, ey, ez) - 0.3, ey, ez],
      size: [0.62, 0.54, 0.56],
      yaw: 0.4,
      pitch: 0.05,
      sclera: "#f2c040",
      iris: "#ff8a10",
      irisRim: "#c02a08",
      irisSize: 0.8,
      pupil: "round",
      pupilSize: 0.36,
      lid: SIDE,
      liner: "#1a0806",
      rest: 0.3,
      lower: 0.25,
      slant: 0.4,
    },
    { eye: kit.eye, iris: kit.iris, skin: kit.skin },
  );
  if (kit.iris instanceof THREE.MeshLambertMaterial) kit.iris.emissive.set("#ff7a10");
  // The brow: a shelf over each eye.
  const by = 2.1;
  const bz = 2.95;
  const brows = [1, -1].map((side) =>
    brow(
      head,
      [surfaceX(S, by, bz) - 0.45, by, bz],
      side,
      (b, mirror) =>
        b.add(ball(12, 9), (_q, n) => mix(SIDE, BACK, n.y), {
          s: [1.0, 0.5, 1.55],
          r: [0.18, 0.3, -0.3],
          mirror,
          rep: [3, 3],
        }),
      kit.skin,
    ),
  );
  return {
    head,
    jaw,
    jawOpen: 0.6,
    eyes,
    brows,
    mouth: [0, -0.7, 8.6],
    nose: [0.55, 0.7, 8.0],
    sway: [],
    heat: kit.heat,
  };
}

/** The club: a heavy spiked ball on the tail's end. */
function club(kit: HeadKit) {
  const g = new THREE.Group();
  const p = new Parts();
  p.add(
    ball(18, 14),
    (q, n) =>
      mix(SIDE, BACK, n.y * 0.7 + 0.2).lerp(
        new THREE.Color("#d05a20"),
        noise(q.x * 3, q.z * 3) > 0.72 ? 0.6 : 0,
      ),
    {
      p: [0, 0, 2.0],
      s: [2.6, 2.2, 3.2],
      rep: [4, 4],
    },
  );
  for (const [a, b, len] of [
    [0, 1, 1.8],
    [1.2, 0.6, 1.5],
    [-1.2, 0.6, 1.5],
    [0.9, -0.5, 1.3],
    [-0.9, -0.5, 1.3],
    [0, 0, 1.6],
  ] as const) {
    const dir = new THREE.Vector3(a, b, b === 0 && a === 0 ? 1 : 0.15).normalize();
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    const e = new THREE.Euler().setFromQuaternion(q);
    p.add(clawGeo(0.65, len * 1.3), hornPaint([0, 0, 0], [0, len, 0], HORN, HORN_TIP), {
      p: [dir.x * 2.3, dir.y * 1.95, 2.0 + dir.z * 2.9],
      r: [e.x, e.y, e.z],
    });
  }
  g.add(mesh(p, kit.skin));
  return g;
}

export const CINDERJAW: DragonDesign = {
  id: "cinderjaw",
  // Tail tip to the back of the skull: [z, y, half-width, half-height, squareness, keel].
  spine: [
    [-30, 3.2, 1.0, 1.0],
    [-27, 3.8, 1.3, 1.3],
    [-24, 4.6, 1.7, 1.7],
    [-21, 5.5, 2.2, 2.15],
    [-18, 6.4, 2.8, 2.7],
    [-15, 7.3, 3.45, 3.35],
    [-12, 8.0, 4.1, 3.95],
    [-8.8, 8.6, 4.7, 4.5, 2.2, 0.15], // hips
    [-5.0, 8.9, 5.2, 5.0, 2.2, 0.2],
    [-1.0, 9.6, 5.7, 5.5, 2.25, 0.2],
    [3.0, 11.0, 6.1, 6.1, 2.3, 0.15],
    [6.2, 12.6, 5.5, 5.6, 2.2, 0.1], // shoulders
    [8.8, 13.9, 4.3, 4.3],
    [10.8, 14.7, 3.6, 3.6],
    [12.6, 15.3, 3.0, 3.0],
    [14.2, 15.8, 2.2, 2.2],
  ],
  hip: 7,
  shoulder: 11,
  neck: 4,
  headScale: 1.2,
  headTilt: 0.12,
  neckInto: 1.6,
  rings: 116,
  sides: 24,
  cells: 18,
  bump: 0.06,
  glow: "#ff6a1a",
  hide: (h) => {
    const pl = plates(h.cu, h.cv * 0.9, 18);
    const up = h.up;
    const belly = smoothstep(-0.45, -0.75, up);
    const c = new THREE.Color(SIDE).lerp(new THREE.Color(BACK), smoothstep(0.1, 0.8, up));
    // Each plate a shade different.
    c.multiplyScalar(0.85 + 0.3 * pl.r);
    let height = 0.25 + 0.75 * pl.h;
    // Embers in the cracks, brightest down the flanks and chest, flickering in patches.
    const patch = noise(h.s * 0.18, h.u * 9);
    let glow = (1 - smoothstep(0, 0.55, pl.h)) * smoothstep(0.35, 0.75, patch) * (1 - belly);
    glow *= smoothstep(-0.6, 0.1, up) * (1 - smoothstep(0.75, 1, up) * 0.6);
    // The tail tip and the neck's top cooler.
    glow *= smoothstep(0, h.hip * 0.6, h.s);
    // Belly plates: broad bands, a burnt orange.
    if (belly > 0) {
      const b = bands(h.s, 1.5);
      const bc = new THREE.Color(BELLY).multiplyScalar(0.8 + 0.2 * b);
      c.lerp(bc, belly);
      height = height * (1 - belly) + (0.3 + 0.6 * b) * belly;
    }
    // Old scars raked across the flanks.
    for (const [s0, u0, sl] of [
      [0.42, 0.2, 0.9],
      [0.5, 0.28, -0.7],
      [0.58, 0.72, 0.8],
    ] as const) {
      const ds = h.s / h.length - s0;
      const du = h.u - u0 - ds * sl * 2.2;
      if (Math.abs(ds) < 0.05 && Math.abs(du) < 0.006) {
        c.lerp(new THREE.Color(SCAR), 0.8);
        height = 0.15;
        glow = 0;
      }
    }
    return { color: c, height, glow };
  },
  legs: {
    hind: {
      hip: [3.9, 7.6, -8.6],
      foot: [5.0, -7.2],
      upper: 4.4,
      lower: 3.8,
      meta: [0, 2.0, -1.3],
      radii: [3.6, 2.9, 1.9, 1.2, 1.05],
      knee: 1,
      toes: 3,
      toeLen: 1.9,
      toeR: 0.9,
      claw: 1.3,
      color: [SIDE, BACK],
      clawColor: HORN,
    },
    fore: {
      hip: [4.1, 9.6, 5.6],
      foot: [5.6, 9.0],
      upper: 4.8,
      lower: 4.6,
      meta: [0, 1.6, -0.5],
      radii: [4.0, 3.2, 2.3, 1.6, 1.35],
      knee: -1,
      toes: 3,
      toeLen: 1.9,
      toeR: 1.0,
      claw: 1.35,
      color: [SIDE, BACK],
      clawColor: HORN,
    },
  },
  wings: {
    root: [2.6, 17.0, 4.5],
    flank: [3.4, 13.0, -4.5],
    humerus: 5.5,
    forearm: 6,
    fingers: [8.5, 7.4, 6],
    fan: [-0.15, -1.3],
    boneR: 0.6,
    scallop: 0.34,
    sag: 1.2,
    membrane: "#4c1a12",
    edge: "#b04018",
    vein: "#24100c",
    bone: BACK,
    thumb: 1.3,
    rest: 0.0,
  },
  spikes: [
    {
      from: 0.15,
      to: 0.88,
      count: 13,
      size: [1.8, 3.2, 2.0],
      shape: "plate",
      color: BACK,
      tip: "#7a3418",
      lean: 0.55,
      width: 0.9,
    },
  ],
  buildHead: head,
  tailTip: club,
  tailDroop: 0,
  tailDrape: 0.6,
  breath: "fire",
  horn: HORN,
  manner: {
    sway: 0.7,
    tail: 1,
    breathe: 1.2,
    blink: 3.6,
    talk: 0.8,
    nod: 1.4,
    brow: -0.7,
    talkBrow: -0.3,
    smoke: 0.7,
    aura: 0,
    undulate: 0,
    tilt: 0,
    speed: 1.15,
    squint: 0.15,
    quirk: 0,
  },
};
