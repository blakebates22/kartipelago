/**
 * KING PYRRHAX, the Dragon King: ancient, massive, regal. He lost the First Race young,
 * and remembers.
 *
 * The biggest of them: a vast deep chest held high, a thick raised neck, a broad heavy
 * head crowned with a ring of many horns, and a long beard of spines that sways under his
 * jaw. Deep-set eyes of white gold. Old scars, one across his brow. Great heavy wings
 * that drape like a cloak, their edges ragged with age. Deep crimson and black, with gold
 * plates down his belly and gold on every horn and spine. His fire burns white-gold.
 */
import * as THREE from "three";
import { Parts, clawGeo, type V3 } from "../parts";
import { buildEyes } from "../face";
import { bands, hash, scales, smoothstep } from "../hide";
import type { DragonDesign, HeadKit, HeadParts } from "../types";
import { horn } from "../../racers/kit/shapes";
import {
  ball,
  brow,
  hornPaint,
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

const CRIMSON = "#7a1420";
const BLACK = "#1c0a0e";
const GOLD = "#d8a838";
const BONE = "#2a1618";
const SCAR = "#c08878";

function head(kit: HeadKit): HeadParts {
  const head = new THREE.Group();
  head.name = "king head";
  const S: Sec[] = [
    { at: [0, 0.4, -1.6], rx: 2.5, ry: 2.5, sq: 2.2, flat: 0.3 },
    { at: [0, 0.8, 0.5], rx: 2.9, ry: 2.5, sq: 2.4, flat: 0.45 },
    { at: [0, 0.65, 2.7], rx: 2.6, ry: 2.1, sq: 2.5, flat: 0.5 },
    { at: [0, 0.2, 4.9], rx: 1.95, ry: 1.6, sq: 2.5, flat: 0.45 },
    { at: [0, -0.05, 7.0], rx: 1.65, ry: 1.35, sq: 2.5, flat: 0.4 },
    { at: [0, -0.15, 8.3], rx: 1.35, ry: 1.1, sq: 2.4, flat: 0.35 },
    { at: [0, -0.2, 8.9], rx: 0.6, ry: 0.5, sq: 2.1, flat: 0.3 },
  ];
  const ey = 1.5;
  const ez = 3.1;
  const p = new Parts();
  p.add(
    skull(S, 24, 4),
    (q, n) => {
      const c = shade(BLACK, CRIMSON, "#a83a2a", 0, 0.6)(q, n);
      // The old scar: across the right brow, through the eye, down the cheek.
      const sc = Math.abs(q.z - ez + (q.y - ey) * 0.35);
      if (q.x < -1.2 && sc < 0.14 && q.y > -0.6 && q.y < 2.6) c.set(SCAR);
      // Gold edging along the snout's ridge.
      if (Math.abs(q.x) < 0.12 && n.y > 0.85 && q.z > 4.5) c.lerp(new THREE.Color(GOLD), 0.6);
      return c;
    },
    { rep: [8, 6] },
  );
  // A row of gold-tipped knobs down the snout.
  for (let k = 0; k < 3; k++)
    p.add(
      new THREE.ConeGeometry(0.22 - k * 0.03, 0.6 - k * 0.1, 8).translate(0, 0.3, 0),
      (q) => mix(BONE, GOLD, (q.y / 0.55) ** 2),
      { p: [0, surfaceY(S, 0, 7.6 - k * 1.2, true) - 0.05, 7.6 - k * 1.2], r: [0.35, 0, 0] },
    );
  p.both(ball(8, 6), "#0a0406", { p: [0.55, 0.7, 8.55], s: [0.3, 0.16, 0.26], r: [0.4, 0.45, 0] });
  head.add(
    new THREE.Mesh(
      new THREE.SphereGeometry(1, 12, 8).scale(1.6, 0.3, 3.4).translate(0, -0.55, 4.6),
      kit.heat,
    ),
  );
  teeth(p, {
    z0: 3.0,
    z1: 8.1,
    count: 8,
    x: (z) => sectionAt(S, z).rx * 0.8,
    y: (z) => surfaceY(S, 0.8, z) + 0.1,
    len: (k) => (k > 0.6 && k < 0.75 ? 1.2 : 0.55),
    r: 0.2,
    down: true,
    color: "#efe4c8",
  });
  // The crown: a ring of horns round the back of the skull, the middle ones longest.
  const N = 9;
  for (let i = 0; i < N; i++) {
    const th = -1.95 + (3.9 * i) / (N - 1);
    const L = 6.2 - Math.abs(th) * 1.4;
    const base: V3 = [Math.sin(th) * 2.2, 1.0 + Math.cos(th) * 1.9, -0.5 - Math.abs(th) * 0.2];
    const d = new THREE.Vector3(Math.sin(th) * 0.55, Math.cos(th) * 0.75 + 0.25, -0.85).normalize();
    const tip: V3 = [base[0] + d.x * L, base[1] + d.y * L, base[2] + d.z * L];
    p.add(
      horn(base, tip, 0.42 + (L / 6) * 0.2, "#ffffff", [0, L * 0.12, L * 0.1], 9),
      hornPaint(base, tip, BONE, GOLD),
    );
  }
  // Heavy cheek plates.
  p.both(ball(12, 8), shade(BLACK, CRIMSON, CRIMSON), {
    p: [2.55, 0.0, 0.5],
    s: [0.8, 1.3, 1.9],
    r: [0.2, 0.2, 0],
  });
  head.add(mesh(p, kit.skin));

  // The jaw, and the beard of spines under it (each one sways).
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.6, -0.1);
  head.add(jaw);
  const J: Sec[] = [
    { at: [0, 0.0, -1.1], rx: 2.2, ry: 0.95, sq: 2.3, flat: -0.7 },
    { at: [0, -0.06, 1.2], rx: 2.35, ry: 1.2, sq: 2.5, flat: -0.82 },
    { at: [0, -0.08, 4.4], rx: 1.8, ry: 1.0, sq: 2.5, flat: -0.82 },
    { at: [0, -0.04, 7.0], rx: 1.5, ry: 0.85, sq: 2.5, flat: -0.8 },
    { at: [0, 0.02, 8.4], rx: 1.15, ry: 0.65, sq: 2.3, flat: -0.75 },
    { at: [0, 0.05, 8.9], rx: 0.45, ry: 0.3, sq: 2, flat: -0.65 },
  ];
  const j = new Parts();
  j.add(skull(J, 22, 4), shade(CRIMSON, CRIMSON, "#b0603a", 0, 0.5), { rep: [7, 5] });
  j.add(ball(10, 6), "#7a2a2a", { p: [0, 0.18, 4.4], s: [1.3, 0.22, 3.2] });
  teeth(j, {
    z0: 3.0,
    z1: 7.8,
    count: 7,
    x: (z) => sectionAt(J, z).rx * 0.78,
    y: (z) => surfaceY(J, 0.78, z, true) - 0.08,
    len: () => 0.5,
    r: 0.18,
    down: false,
    color: "#efe4c8",
  });
  jaw.add(mesh(j, kit.skin));
  const sway: HeadParts["sway"] = [];
  for (let i = 0; i < 9; i++) {
    const k = i / 8;
    const x = (k - 0.5) * 2.6;
    const z = 1.0 + (1 - Math.abs(k - 0.5) * 2) * 4.2;
    const L = 3.2 + (1 - Math.abs(k - 0.5) * 2) * 2.8 + hash(i, 3) * 0.6;
    const g = new THREE.Group();
    g.position.set(x, -0.8, z);
    g.rotation.set(0.5 + k * 0.1, 0, x * 0.12);
    const sp = new Parts().add(clawGeo(0.22, L), (q) => mix(BONE, GOLD, q.y / L), {
      r: [Math.PI, 0, 0],
    });
    g.add(mesh(sp, kit.skin));
    jaw.add(g);
    sway.push({ obj: g, amount: 0.05, phase: i * 0.7 });
  }

  // Deep-set eyes of white gold, under heavy black brows.
  const eyes = buildEyes(
    head,
    {
      at: [surfaceX(S, ey, ez) - 0.28, ey, ez],
      size: [0.64, 0.54, 0.56],
      yaw: 0.4,
      pitch: 0.05,
      sclera: "#f8e0a0",
      iris: "#fffbe0",
      irisRim: "#e8a020",
      irisSize: 0.8,
      pupil: "slit",
      pupilSize: 0.16,
      lid: CRIMSON,
      liner: "#0a0406",
      rest: 0.34,
      lower: 0.18,
      slant: 0.28,
    },
    { eye: kit.eye, iris: kit.iris, skin: kit.skin },
  );
  if (kit.iris instanceof THREE.MeshLambertMaterial) {
    kit.iris.emissive.set("#ffd870");
    kit.iris.emissiveIntensity = 0.6;
  }
  const by = 2.2;
  const bz = 3.05;
  const brows = [1, -1].map((side) =>
    brow(
      head,
      [surfaceX(S, by, bz) - 0.42, by, bz],
      side,
      (b, mirror) =>
        b.add(ball(12, 8), shade(BLACK, BLACK, CRIMSON), {
          s: [1.0, 0.45, 1.7],
          r: [0.18, 0.28, -0.3],
          mirror,
        }),
      kit.skin,
    ),
  );
  return {
    head,
    jaw,
    jawOpen: 0.55,
    eyes,
    brows,
    mouth: [0, -0.8, 9.0],
    nose: [0.55, 0.75, 8.7],
    sway,
    heat: kit.heat,
  };
}

/** The tail's end: a heavy spade with gold edges. */
function spade(kit: HeadKit) {
  const g = new THREE.Group();
  const p = new Parts();
  p.add(
    new THREE.OctahedronGeometry(1, 1),
    (q) => mix(BLACK, GOLD, Math.abs(q.x) > 0.55 ? 0.9 : 0),
    {
      p: [0, 0, 2.2],
      s: [2.0, 0.35, 2.8],
    },
  );
  g.add(mesh(p, kit.skin));
  return g;
}

export const KING: DragonDesign = {
  id: "king",
  spine: [
    [-44, 3.0, 0.5, 0.5],
    [-39, 3.6, 0.95, 0.95],
    [-34, 4.6, 1.5, 1.5],
    [-29, 5.8, 2.1, 2.1],
    [-24, 7.2, 2.8, 2.8],
    [-19, 8.6, 3.6, 3.5],
    [-14, 10.0, 4.5, 4.4],
    [-9.5, 11.0, 5.4, 5.3, 2.1, 0.15], // hips
    [-5, 11.6, 6.0, 5.9, 2.1, 0.18],
    [-0.5, 12.6, 6.4, 6.4, 2.15, 0.15],
    [4, 14.2, 6.5, 6.8, 2.2, 0.1],
    [7.8, 16.4, 5.8, 6.0], // shoulders
    [10.0, 19.4, 4.6, 4.7],
    [11.4, 22.2, 3.9, 4.0],
    [12.4, 24.8, 3.4, 3.5],
    [13.6, 27.0, 3.0, 3.1],
    [15.4, 28.4, 2.4, 2.5],
  ],
  hip: 7,
  shoulder: 11,
  neck: 5,
  headScale: 1.3,
  headTilt: 0.18,
  neckInto: 1.6,
  rings: 124,
  sides: 24,
  cells: 20,
  bump: 0.05,
  hide: (h) => {
    const sc = scales(h.cu, h.cv, 20);
    const c = new THREE.Color(CRIMSON).lerp(new THREE.Color(BLACK), smoothstep(0.0, 0.75, h.up));
    c.multiplyScalar(0.9 + 0.15 * sc.r);
    let height = 0.3 + 0.7 * sc.h;
    // Gold edging on the scales over the shoulders, like mail.
    const shoulders = Math.exp(-(((h.s - h.shoulder) / 6) ** 2));
    if (sc.h < 0.25 && shoulders > 0.35 && h.up > -0.3)
      c.lerp(new THREE.Color(GOLD), 0.7 * shoulders);
    // Old scars.
    for (const [s0, u0, sl] of [
      [0.48, 0.25, 1.1],
      [0.55, 0.7, -0.9],
      [0.6, 0.32, 0.6],
    ] as const) {
      const ds = h.s / h.length - s0;
      const du = h.u - u0 - ds * sl * 2.2;
      if (Math.abs(ds) < 0.045 && Math.abs(du) < 0.006) {
        c.set(SCAR);
        height = 0.15;
      }
    }
    // Gold plates down the belly.
    const belly = smoothstep(-0.45, -0.75, h.up);
    if (belly > 0) {
      const b = bands(h.s, 1.6);
      c.lerp(new THREE.Color(GOLD).multiplyScalar(0.8 + 0.2 * b), belly);
      height = height * (1 - belly) + (0.3 + 0.6 * b) * belly;
    }
    return { color: c, height, glow: 0 };
  },
  legs: {
    hind: {
      hip: [4.6, 10.0, -9.4],
      foot: [6.0, -8.4],
      upper: 6.2,
      lower: 5.4,
      meta: [0, 2.8, -1.6],
      radii: [4.6, 3.6, 2.3, 1.5, 1.3],
      knee: 1,
      toes: 4,
      toeLen: 2.4,
      toeR: 1.0,
      claw: 1.8,
      color: [CRIMSON, BLACK],
      clawColor: GOLD,
    },
    fore: {
      hip: [4.8, 13.4, 7.2],
      foot: [6.2, 11.4],
      upper: 6.6,
      lower: 6.4,
      meta: [0, 2.0, -0.6],
      radii: [4.4, 3.4, 2.3, 1.55, 1.35],
      knee: -1,
      toes: 4,
      toeLen: 2.4,
      toeR: 1.0,
      claw: 1.8,
      color: [CRIMSON, BLACK],
      clawColor: GOLD,
    },
  },
  wings: {
    root: [3.0, 20.6, 6.5],
    flank: [4.6, 15.5, -6],
    humerus: 8,
    forearm: 11,
    fingers: [19, 17, 15, 12],
    fan: [-0.1, -1.4],
    boneR: 0.75,
    scallop: 0.38,
    sag: 1.6,
    membrane: "#6a0e16",
    edge: GOLD,
    vein: "#1a0608",
    bone: BLACK,
    thumb: 1.8,
    rest: 0.08,
    paint: (c, panel, sr, a) => {
      // Ragged with age: darker tears near the edge.
      if (panel >= 0 && sr > 0.7 && hash(Math.floor(a * 6) + panel * 7, Math.floor(sr * 5)) > 0.75)
        return new THREE.Color("#2a0408");
      return c;
    },
  },
  spikes: [
    {
      from: 0.12,
      to: 0.93,
      count: 18,
      size: [1.6, 3.6, 2.4],
      shape: "spike",
      color: BONE,
      tip: GOLD,
      lean: 0.6,
      width: 0.6,
    },
  ],
  buildHead: head,
  tailTip: spade,
  tailDroop: 0,
  tailDrape: 0.8,
  breath: "kingfire",
  horn: GOLD,
  manner: {
    sway: 0.35,
    tail: 0.7,
    breathe: 1.1,
    blink: 6,
    talk: 0.55,
    nod: 0.7,
    brow: -0.35,
    talkBrow: -0.3,
    smoke: 0.25,
    aura: 0,
    undulate: 0,
    tilt: 0,
    speed: 0.75,
    squint: 0.1,
    quirk: 0,
  },
};
