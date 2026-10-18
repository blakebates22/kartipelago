/**
 * The four original racers, built from rounded painted shapes on a simple rig.
 *
 * Every character shares the same rig layout, so one animator drives them all:
 *   root (on the kart seat)
 *     torso (pivot at the hips): body, arms, back details
 *       head (pivot at the neck): face, eyes, mouths, ears and other head shapes
 * Hands are built separately and ride on the steering wheel, so they never come off
 * it; the arms reach from the shoulders to wherever the hands are.
 *
 * Each racer has its own head shape, face and silhouette from behind (where you see
 * them most): Moss's fan of gills, Bramble's armour plates and curled tail, Poppy's
 * feathery antennae and folded wings, Otto's big round back and the orange on his head.
 */
import * as THREE from "three";
import { PALETTE, type RacerId } from "./designs";
import { Parts, ball, capsule, cone, halfBall, ring, tube } from "./geo";
import { paintedMaterial, plainMaterial } from "./paint";

export interface Personality {
  /** Idle bob: height (m) and speed (Hz). */
  bob: number;
  bobHz: number;
  /** How much they lean into turns (1 = normal). */
  lean: number;
  /** Seconds between blinks, roughly. */
  blinkEvery: number;
  /** Face while boosting: "open" (excited) or "grin" (determined). */
  boostFace: "open" | "grin";
  /** How often they glance at a nearby racer, seconds (roughly). */
  glanceEvery: number;
}

export interface CharacterRig {
  root: THREE.Group;
  torso: THREE.Group;
  head: THREE.Group;
  /** Both eyes; blinking squashes this vertically. */
  eyes: THREE.Group;
  mouths: { smile: THREE.Mesh; open: THREE.Mesh; grin: THREE.Mesh };
  brows: THREE.Mesh | null;
  shoulders: [THREE.Vector3, THREE.Vector3];
  arms: [THREE.Mesh, THREE.Mesh];
  /** Both hands, in steering-wheel space (added to the steering wheel). */
  hands: THREE.Mesh;
  /** Parts with their own little motions (gills, antennae, tail, wings, scarf...). */
  wiggles: { obj: THREE.Object3D; kind: string; side: number }[];
  /** A cheap one-mesh version for far away. */
  low: THREE.Mesh;
  personality: Personality;
}

type V3 = [number, number, number];
const C = (hex: string) => new THREE.Color(hex);
const shade = (hex: string, k: number) => C(hex).multiplyScalar(k);
const tint = (hex: string, k: number) => C(hex).lerp(C("#ffffff"), k);

/** A wide smile: the lower half of a thin ring. */
const smileGeo = (r: number, t: number) =>
  new THREE.TorusGeometry(r, t, 4, 10, Math.PI).rotateZ(Math.PI);

function face(
  head: THREE.Group,
  opts: {
    eyeAt: V3;
    eyeSize: V3;
    pupil: number;
    mouthAt: V3;
    mouthWidth: number;
    tilt?: number;
    lids?: string;
  },
) {
  const plain = plainMaterial();
  // Eyes: big white, dark pupils looking slightly inward, a bright highlight each.
  const eyes = new THREE.Group();
  eyes.position.set(0, opts.eyeAt[1], opts.eyeAt[2]);
  const e = new Parts();
  for (const side of [-1, 1]) {
    const x = side * opts.eyeAt[0];
    const [sx, sy, sz] = opts.eyeSize;
    e.add(ball(12), PALETTE.white, {
      p: [x, 0, 0],
      s: [sx, sy, sz],
      r: [0, side * 0.3, (opts.tilt ?? 0) * side],
    });
    e.add(ball(10), PALETTE.ink, {
      p: [x - side * sx * 0.12, -sy * 0.05, sz * 0.72],
      s: [sx * opts.pupil, sy * opts.pupil * 1.1, sz * 0.4],
    });
    e.add(ball(6), PALETTE.white, {
      p: [x - side * sx * 0.05 + sx * 0.18, sy * 0.28, sz * 0.98],
      s: [sx * 0.2, sy * 0.2, sz * 0.12],
    });
  }
  eyes.add(new THREE.Mesh(e.build(), plain));
  head.add(eyes);
  if (opts.lids) {
    // Heavy, relaxed eyelids (static); blinking still closes the eyes underneath.
    const l = new Parts();
    for (const side of [-1, 1])
      l.add(halfBall(10), opts.lids, {
        p: [side * opts.eyeAt[0], opts.eyeAt[1] - opts.eyeSize[1] * 0.05, opts.eyeAt[2] + 0.005],
        s: [opts.eyeSize[0] * 1.12, opts.eyeSize[1] * 1.1, opts.eyeSize[2] * 1.12],
        r: [-0.25, side * 0.3, 0],
      });
    head.add(new THREE.Mesh(l.build(), paintedMaterial()));
  }

  const [mx, my, mz] = opts.mouthAt;
  const w = opts.mouthWidth;
  const smile = new THREE.Mesh(new Parts().add(smileGeo(w, w * 0.14), PALETTE.ink).build(), plain);
  smile.position.set(mx, my, mz);
  const open = new THREE.Mesh(
    new Parts()
      .add(ball(10), "#5a1f2e", { s: [w * 0.75, w * 0.6, w * 0.25] })
      .add(ball(8), PALETTE.rose, {
        p: [0, -w * 0.25, w * 0.08],
        s: [w * 0.45, w * 0.25, w * 0.15],
      })
      .build(),
    plain,
  );
  open.position.set(mx, my - w * 0.2, mz);
  const grin = new THREE.Mesh(
    new Parts()
      .add(smileGeo(w * 1.15, w * 0.12), PALETTE.ink, { s: [1, 0.55, 1] })
      .add(ball(8), PALETTE.white, { p: [0, -w * 0.3, -w * 0.02], s: [w * 0.8, w * 0.18, w * 0.1] })
      .build(),
    plain,
  );
  grin.position.set(mx, my, mz);
  open.visible = grin.visible = false;
  head.add(smile, open, grin);
  return { eyes, mouths: { smile, open, grin } };
}

/** Arms: a tube along +Z of length 1, stretched each frame from shoulder to hand. */
function arm(color: string, r: number) {
  // A rounded capsule spanning z = 0..1 (its caps stretch a little with the arm).
  const g = new Parts().add(new THREE.CapsuleGeometry(1, 2, 3, 8), color, {
    r: [Math.PI / 2, 0, 0],
    s: [r, 0.25, r],
    p: [0, 0, 0.5],
  });
  const mesh = new THREE.Mesh(g.build(), paintedMaterial());
  return mesh;
}

function hands(color: string, size: number, grips: [THREE.Vector3, THREE.Vector3], claws?: string) {
  const p = new Parts();
  for (const g of grips) {
    p.add(ball(10), color, { p: [g.x, g.y, g.z - 0.02], s: [size, size * 0.9, size * 1.05] });
    // A thumb over the rim.
    p.add(ball(6), color, { p: [g.x * 0.85, g.y + size * 0.6, g.z + 0.02], s: size * 0.45 });
    if (claws)
      for (const k of [-1, 0, 1])
        p.add(cone(5), claws, {
          p: [g.x + k * size * 0.4, g.y - size * 0.7, g.z + size * 0.4],
          r: [Math.PI * 0.85, 0, 0],
          s: [size * 0.16, size * 0.4, size * 0.16],
        });
  }
  return new THREE.Mesh(p.build(), paintedMaterial());
}

interface Built {
  torso: Parts;
  head: Parts;
  extras: { parent: "torso" | "head"; geo: Parts; at: V3; kind: string; side: number }[];
  low: Parts;
  neck: V3;
  shoulders: [THREE.Vector3, THREE.Vector3];
  armColor: string;
  armRadius: number;
  handColor: string;
  handSize: number;
  claws?: string;
  face: Parameters<typeof face>[1];
  brows?: { color: string; at: V3; angle: number; size: V3 };
  personality: Personality;
}

// ---------------------------------------------------------------- Moss, axolotl
function moss(): Built {
  const skin = PALETTE.turquoise;
  const belly = tint(PALETTE.turquoise, 0.4);
  const gill = PALETTE.coral;
  const torso = new Parts()
    .add(ball(12), skin, { p: [0, 0.3, 0], s: [0.3, 0.36, 0.26] })
    .add(ball(10), belly, { p: [0, 0.26, 0.09], s: [0.22, 0.27, 0.19] });
  const head = new Parts()
    .add(ball(14), skin, { p: [0, 0.2, 0.06], s: [0.52, 0.36, 0.42] })
    .add(ball(14), belly, { p: [0, 0.07, 0.08], s: [0.4, 0.15, 0.33] })
    .add(ball(8), PALETTE.rose, { p: [0.33, 0.1, 0.3], s: [0.08, 0.05, 0.03] })
    .add(ball(8), PALETTE.rose, { p: [-0.33, 0.1, 0.3], s: [0.08, 0.05, 0.03] });
  // Three feathery gills a side, fanning up and back: the silhouette from behind.
  const extras: Built["extras"] = [];
  for (const side of [-1, 1]) {
    const g = new Parts();
    [0.65, 0.15, -0.35].forEach((tilt, k) => {
      const len = 0.46 - k * 0.05;
      const rz = -side * (0.9 + tilt * 0.6);
      const dir = new THREE.Vector3(0, 1, 0).applyEuler(new THREE.Euler(-0.5, 0, rz));
      const at = (f: number): V3 => [dir.x * len * f, dir.y * len * f, dir.z * len * f];
      g.add(capsule(0.055, len, 6), gill, { p: at(0.55), r: [-0.5, 0, rz] });
      // Feathery fronds along each stalk, alternating sides.
      for (let f = 0; f < 4; f++)
        g.add(ball(6), f % 2 ? PALETTE.rose : gill, {
          p: at(0.35 + f * 0.2),
          s: [0.1 - f * 0.01, 0.055, 0.075],
          r: [0, (f % 2 ? 0.4 : -0.4) * side, rz],
        });
    });
    extras.push({ parent: "head", geo: g, at: [side * 0.42, 0.26, -0.04], kind: "gill", side });
  }
  // A tail fin rising behind the seat.
  extras.push({
    parent: "torso",
    geo: new Parts()
      .add(ball(10), shade(PALETTE.turquoise, 0.85), {
        p: [0, 0.2, 0],
        s: [0.04, 0.3, 0.18],
        r: [-0.5, 0, 0],
      })
      .add(ball(8), gill, { p: [0, 0.4, -0.12], s: [0.03, 0.12, 0.1], r: [-0.5, 0, 0] }),
    at: [0, 0.1, -0.32],
    kind: "tail",
    side: 0,
  });
  const low = new Parts()
    .add(ball(6), skin, { p: [0, 0.3, 0], s: [0.3, 0.36, 0.26] })
    .add(ball(6), skin, { p: [0, 0.8, 0.08], s: [0.52, 0.36, 0.42] })
    .add(ball(5), gill, { p: [0.5, 0.95, 0], s: [0.2, 0.14, 0.06] })
    .add(ball(5), gill, { p: [-0.5, 0.95, 0], s: [0.2, 0.14, 0.06] });
  return {
    torso,
    head,
    extras,
    low,
    neck: [0, 0.6, 0.02],
    shoulders: [new THREE.Vector3(0.27, 0.48, 0.06), new THREE.Vector3(-0.27, 0.48, 0.06)],
    armColor: skin,
    armRadius: 0.065,
    handColor: skin,
    handSize: 0.08,
    face: {
      eyeAt: [0.21, 0.29, 0.405],
      eyeSize: [0.13, 0.14, 0.08],
      pupil: 0.62,
      mouthAt: [0, 0.12, 0.48],
      mouthWidth: 0.16,
    },
    personality: {
      bob: 0.035,
      bobHz: 2.2,
      lean: 1.15,
      blinkEvery: 3,
      boostFace: "open",
      glanceEvery: 5,
    },
  };
}

// ------------------------------------------------------------- Bramble, pangolin
function bramble(): Built {
  const scale = PALETTE.rust;
  const scaleDark = shade(PALETTE.rust, 0.78);
  const cream = PALETTE.cream;
  const torso = new Parts()
    .add(ball(12), scale, { p: [0, 0.3, 0], s: [0.33, 0.34, 0.3] })
    .add(ball(10), cream, { p: [0, 0.26, 0.12], s: [0.24, 0.27, 0.2] });
  // Overlapping armour plates over the back and shoulders, in staggered rows.
  for (let row = 0; row < 3; row++) {
    const y = 0.5 - row * 0.15;
    const count = 5 - (row === 0 ? 1 : 0);
    for (let k = 0; k < count; k++) {
      const a = Math.PI + ((k - (count - 1) / 2) * 0.55 + (row % 2) * 0.27);
      const rr = 0.31 + row * 0.02;
      torso.add(ball(8), (k + row) % 2 ? scale : scaleDark, {
        p: [Math.sin(a) * rr, y, Math.cos(a) * rr * 0.95],
        r: [-0.35, a, 0],
        s: [0.13, 0.1, 0.06],
      });
    }
  }
  const head = new Parts()
    .add(ball(14), scale, { p: [0, 0.2, 0], s: [0.37, 0.34, 0.36] })
    .add(ball(12), cream, { p: [0, 0.16, 0.16], s: [0.29, 0.25, 0.26] })
    // A long, tapering pangolin snout with a little pink nose.
    .add(ball(12), cream, { p: [0, 0.12, 0.4], s: [0.15, 0.13, 0.3] })
    .add(ball(10), cream, { p: [0, 0.11, 0.62], s: [0.09, 0.08, 0.16] })
    .add(ball(8), "#c9677a", { p: [0, 0.13, 0.77], s: [0.05, 0.04, 0.03] });
  // Crown of plates on the head.
  // A hood of big overlapping plates from the brow back over the crown and neck.
  for (let k = 0; k < 6; k++) {
    // Laid on the head's surface, from just above the brow round to the back of the neck.
    const t = 0.55 - k * 0.42;
    head.add(ball(8), k % 2 ? scale : scaleDark, {
      p: [0, 0.2 + 0.35 * Math.cos(t), 0.37 * Math.sin(t)],
      r: [t, 0, 0],
      s: [0.24 - Math.abs(k - 2) * 0.02, 0.06, 0.17],
    });
  }
  for (const side of [-1, 1])
    head.add(ball(8), scaleDark, {
      p: [side * 0.22, 0.42, 0.02],
      r: [-0.3, side * 0.6, side * 0.5],
      s: [0.14, 0.05, 0.13],
    });
  // Little round ears.
  for (const side of [-1, 1])
    head
      .add(ball(8), scale, {
        p: [side * 0.34, 0.27, -0.03],
        s: [0.055, 0.065, 0.035],
        r: [0, side * 0.4, 0],
      })
      .add(ball(6), PALETTE.rose, {
        p: [side * 0.35, 0.27, -0.01],
        s: [0.028, 0.035, 0.015],
        r: [0, side * 0.4, 0],
      });
  // A thick armoured tail curling up behind the seat.
  const tail = new Parts();
  const links: [V3, number][] = [
    [[0, 0.02, -0.16], 0.17],
    [[0, 0.2, -0.36], 0.15],
    [[0, 0.44, -0.46], 0.13],
    [[0, 0.68, -0.42], 0.11],
    [[0, 0.84, -0.28], 0.085],
  ];
  links.forEach(([p, r], k) =>
    tail.add(ball(8), k % 2 ? scale : shade(PALETTE.rust, 0.6), { p, s: [r * 1.1, r * 0.9, r] }),
  );
  const extras: Built["extras"] = [
    { parent: "torso", geo: tail, at: [0, 0.05, -0.28], kind: "tail", side: 0 },
  ];
  const low = new Parts()
    .add(ball(6), scale, { p: [0, 0.3, 0], s: [0.34, 0.34, 0.31] })
    .add(ball(6), scale, { p: [0, 0.8, 0.04], s: [0.37, 0.34, 0.36] })
    .add(ball(5), cream, { p: [0, 0.73, 0.42], s: [0.16, 0.14, 0.26] })
    .add(ball(5), scale, { p: [0, 0.65, -0.55], s: [0.14, 0.24, 0.14] });
  return {
    torso,
    head,
    extras,
    low,
    neck: [0, 0.6, 0],
    shoulders: [new THREE.Vector3(0.29, 0.47, 0.06), new THREE.Vector3(-0.29, 0.47, 0.06)],
    armColor: scale,
    armRadius: 0.075,
    handColor: tint(PALETTE.rust, 0.25).getStyle(),
    handSize: 0.085,
    claws: cream,
    face: {
      // One eye a touch bigger: a slightly clumsy, earnest look.
      eyeAt: [0.15, 0.29, 0.32],
      eyeSize: [0.085, 0.095, 0.06],
      pupil: 0.66,
      mouthAt: [0, 0.03, 0.6],
      mouthWidth: 0.09,
      tilt: 0.1,
    },
    brows: {
      color: PALETTE.chestnut,
      at: [0.15, 0.41, 0.33],
      angle: 0.35,
      size: [0.09, 0.025, 0.03],
    },
    personality: {
      bob: 0.02,
      bobHz: 1.6,
      lean: 1,
      blinkEvery: 2.4,
      boostFace: "grin",
      glanceEvery: 3.5,
    },
  };
}

// ----------------------------------------------------------------- Poppy, moth
function poppy(): Built {
  const fur = PALETTE.lavender;
  const furLight = tint(PALETTE.lavender, 0.45);
  const wing = PALETTE.violet;
  const torso = new Parts()
    .add(ball(12), fur, { p: [0, 0.27, 0], s: [0.24, 0.29, 0.22] })
    .add(ball(10), furLight, { p: [0, 0.26, 0.08], s: [0.17, 0.22, 0.16] });
  // Fluffy collar.
  for (let k = 0; k < 12; k++) {
    const a = (k / 12) * Math.PI * 2;
    torso.add(ball(6), PALETTE.cream, {
      p: [Math.sin(a) * 0.2, 0.52, Math.cos(a) * 0.18],
      s: 0.07,
    });
  }
  // Short scarf wrapped round the neck.
  torso.add(ring(0.17, 0.05, 12), PALETTE.rose, { p: [0, 0.57, 0], r: [Math.PI / 2, 0, 0] });
  const head = new Parts()
    .add(ball(14), fur, { p: [0, 0.22, 0], s: [0.38, 0.36, 0.35] })
    .add(ball(12), furLight, { p: [0, 0.16, 0.13], s: [0.3, 0.26, 0.24] })
    .add(ball(6), PALETTE.rose, { p: [0.2, 0.08, 0.3], s: [0.06, 0.04, 0.03] })
    .add(ball(6), PALETTE.rose, { p: [-0.2, 0.08, 0.3], s: [0.06, 0.04, 0.03] });
  const extras: Built["extras"] = [];
  // Feathery antennae: a curved stalk and a broad feather fan each.
  for (const side of [-1, 1]) {
    const a = new Parts()
      .add(capsule(0.02, 0.22, 5), PALETTE.ink, { p: [0, 0.12, 0], r: [0.2, 0, -side * 0.3] })
      .add(ball(10), wing, {
        p: [side * 0.1, 0.36, 0.06],
        s: [0.08, 0.18, 0.025],
        r: [0.25, 0, -side * 0.45],
      });
    for (let f = 0; f < 4; f++)
      a.add(ball(5), furLight, {
        p: [side * (0.05 + f * 0.035), 0.26 + f * 0.06, 0.06],
        s: [0.09, 0.016, 0.016],
        r: [0, 0, -side * (0.2 + f * 0.15)],
      });
    extras.push({ parent: "head", geo: a, at: [side * 0.13, 0.5, 0.04], kind: "antenna", side });
  }
  // Folded wings standing up behind her back, with cream spots and a rose eye-spot.
  for (const side of [-1, 1]) {
    const w = new Parts()
      .add(ball(12), wing, { p: [0, 0.34, 0], s: [0.035, 0.4, 0.26] })
      .add(ball(10), PALETTE.rose, { p: [-side * 0.02, 0.42, -0.02], s: [0.03, 0.09, 0.07] })
      .add(ball(8), PALETTE.cream, { p: [-side * 0.025, 0.42, -0.02], s: [0.025, 0.045, 0.035] })
      .add(ball(8), PALETTE.cream, { p: [-side * 0.02, 0.16, 0.06], s: [0.026, 0.05, 0.05] })
      .add(ball(8), PALETTE.cream, { p: [-side * 0.02, 0.62, -0.08], s: [0.026, 0.04, 0.04] });
    extras.push({ parent: "torso", geo: w, at: [side * 0.13, 0.3, -0.2], kind: "wing", side });
  }
  // The scarf's tail flutters out behind.
  extras.push({
    parent: "torso",
    geo: new Parts()
      .add(ball(8), PALETTE.rose, { p: [0, -0.06, -0.12], s: [0.07, 0.03, 0.14], r: [0.4, 0, 0] })
      .add(ball(8), shade(PALETTE.rose, 0.85), {
        p: [0.05, -0.12, -0.26],
        s: [0.06, 0.025, 0.1],
        r: [0.6, 0, 0.3],
      }),
    at: [0.06, 0.58, -0.16],
    kind: "scarf",
    side: 0,
  });
  const low = new Parts()
    .add(ball(6), fur, { p: [0, 0.27, 0], s: [0.24, 0.29, 0.22] })
    .add(ball(6), fur, { p: [0, 0.82, 0], s: [0.38, 0.36, 0.35] })
    .add(ball(5), wing, { p: [0.14, 0.62, -0.2], s: [0.04, 0.4, 0.26] })
    .add(ball(5), wing, { p: [-0.14, 0.62, -0.2], s: [0.04, 0.4, 0.26] })
    .add(ball(5), wing, { p: [0.22, 1.42, 0.08], s: [0.08, 0.18, 0.03] })
    .add(ball(5), wing, { p: [-0.22, 1.42, 0.08], s: [0.08, 0.18, 0.03] });
  return {
    torso,
    head,
    extras,
    low,
    neck: [0, 0.6, 0],
    shoulders: [new THREE.Vector3(0.21, 0.45, 0.05), new THREE.Vector3(-0.21, 0.45, 0.05)],
    armColor: fur,
    armRadius: 0.05,
    handColor: furLight.getStyle(),
    handSize: 0.065,
    face: {
      // Huge, sparkly eyes.
      eyeAt: [0.16, 0.22, 0.3],
      eyeSize: [0.14, 0.16, 0.08],
      pupil: 0.72,
      mouthAt: [0, 0.04, 0.345],
      mouthWidth: 0.07,
    },
    personality: {
      bob: 0.03,
      bobHz: 2.8,
      lean: 1.25,
      blinkEvery: 2.2,
      boostFace: "open",
      glanceEvery: 4,
    },
  };
}

// --------------------------------------------------------------- Otto, capybara
function otto(): Built {
  const fur = PALETTE.caramel;
  const furDark = shade(PALETTE.caramel, 0.75);
  const furLight = tint(PALETTE.caramel, 0.3);
  const torso = new Parts()
    .add(ball(14), fur, { p: [0, 0.32, -0.02], s: [0.42, 0.4, 0.36] })
    .add(ball(10), furLight, { p: [0, 0.27, 0.13], s: [0.3, 0.3, 0.23] });
  const head = new Parts()
    // A big, boxy, gently rounded head with a blunt snout.
    .add(ball(14), fur, { p: [0, 0.24, 0.02], s: [0.44, 0.37, 0.46] })
    .add(ball(12), furDark, { p: [0, 0.13, 0.36], s: [0.33, 0.24, 0.25] })
    .add(ball(10), fur, { p: [0, 0.22, 0.34], s: [0.3, 0.2, 0.24] })
    .add(ball(8), PALETTE.ink, { p: [0.08, 0.22, 0.58], s: [0.035, 0.022, 0.02] })
    .add(ball(8), PALETTE.ink, { p: [-0.08, 0.22, 0.58], s: [0.035, 0.022, 0.02] });
  for (const side of [-1, 1])
    head.add(ball(8), furDark, {
      p: [side * 0.26, 0.55, -0.1],
      s: [0.075, 0.065, 0.045],
      r: [0, side * 0.3, 0],
    });
  // Something orange, resting on his head, as one does.
  const orange = new Parts()
    .add(ball(12), PALETTE.orange, { p: [0, 0.12, 0], s: [0.14, 0.125, 0.14] })
    .add(tube(1, 1, 5), PALETTE.chestnut, { p: [0, 0.27, 0], s: [0.015, 0.05, 0.015] })
    .add(ball(8), PALETTE.leaf, { p: [0.06, 0.28, 0], s: [0.07, 0.015, 0.035], r: [0, 0, 0.4] });
  const extras: Built["extras"] = [
    { parent: "head", geo: orange, at: [0, 0.56, -0.02], kind: "orange", side: 0 },
  ];
  const low = new Parts()
    .add(ball(6), fur, { p: [0, 0.32, -0.02], s: [0.42, 0.4, 0.36] })
    .add(ball(6), fur, { p: [0, 0.86, 0.02], s: [0.44, 0.37, 0.46] })
    .add(ball(5), PALETTE.orange, { p: [0, 1.3, 0], s: 0.14 });
  return {
    torso,
    head,
    extras,
    low,
    neck: [0, 0.62, 0.02],
    shoulders: [new THREE.Vector3(0.36, 0.5, 0.06), new THREE.Vector3(-0.36, 0.5, 0.06)],
    armColor: fur,
    armRadius: 0.085,
    handColor: furDark.getStyle(),
    handSize: 0.09,
    face: {
      // Small, sleepy, contented eyes under heavy lids.
      eyeAt: [0.23, 0.33, 0.38],
      eyeSize: [0.065, 0.065, 0.05],
      pupil: 0.7,
      mouthAt: [0, 0.03, 0.59],
      mouthWidth: 0.08,
      lids: shade(PALETTE.caramel, 0.9).getStyle(),
    },
    personality: {
      bob: 0.015,
      bobHz: 0.9,
      lean: 0.7,
      blinkEvery: 4.5,
      boostFace: "grin",
      glanceEvery: 7,
    },
  };
}

const BUILDERS: Record<RacerId, () => Built> = { moss, bramble, poppy, otto };

export function buildCharacter(id: RacerId, grips: [THREE.Vector3, THREE.Vector3]): CharacterRig {
  const b = BUILDERS[id]();
  const mat = paintedMaterial();
  const root = new THREE.Group();
  const torso = new THREE.Group();
  root.add(torso);
  torso.add(new THREE.Mesh(b.torso.build(), mat));
  const head = new THREE.Group();
  head.position.set(...b.neck);
  torso.add(head);
  head.add(new THREE.Mesh(b.head.build(), mat));
  const { eyes, mouths } = face(head, b.face);
  let brows: THREE.Mesh | null = null;
  if (b.brows) {
    const br = new Parts();
    for (const side of [-1, 1])
      br.add(capsule(0.5, 1, 5), b.brows.color, {
        p: [side * b.brows.at[0], b.brows.at[1], b.brows.at[2]],
        r: [0, 0, Math.PI / 2 - side * b.brows.angle],
        s: b.brows.size,
      });
    brows = new THREE.Mesh(br.build(), plainMaterial());
    head.add(brows);
  }
  const wiggles: CharacterRig["wiggles"] = [];
  for (const x of b.extras) {
    const m = new THREE.Mesh(x.geo.build(), mat);
    m.position.set(...x.at);
    (x.parent === "head" ? head : torso).add(m);
    wiggles.push({ obj: m, kind: x.kind, side: x.side });
  }
  const arms: [THREE.Mesh, THREE.Mesh] = [
    arm(b.armColor, b.armRadius),
    arm(b.armColor, b.armRadius),
  ];
  arms.forEach((a, i) => {
    a.position.copy(b.shoulders[i]!);
    torso.add(a);
  });
  return {
    root,
    torso,
    head,
    eyes,
    mouths,
    brows,
    shoulders: b.shoulders,
    arms,
    hands: hands(b.handColor, b.handSize, grips, b.claws),
    wiggles,
    low: new THREE.Mesh(b.low.build(), mat),
    personality: b.personality,
  };
}
