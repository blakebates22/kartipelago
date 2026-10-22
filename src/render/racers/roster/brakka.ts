/**
 * Brakka the triceratops: the Rocky Roader (design D), the bruiser.
 *
 * Silhouette: the frill, big and graphic: a sunburst of rust and orange rays inside a
 * dark rim, ringed with ivory spikes, two cream eye-spots on the front. From the race
 * camera it's the whole silhouette. A compact, muscular body sitting low.
 * Face: a blocky skull under a heavy bony brow, deep-set eyes in a permanent scowl, a
 * hooked beak with a tough set to it, two long brow horns thrust forward and a stout
 * nose horn. Warm golden-brown skin, cream muzzle and belly.
 * Gear: utility straps and a small rugged pack.
 * Kart: the Rock Rally (the sleek family): broad and low, sandstone and burnt orange,
 * horn splitters at the front, a ducktail and fat twin pipes, a footprint emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, card, cone, cyl, ellipsoid, horn, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { backpack, strap } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#d38a3a",
  skinDark: "#a9652a",
  cream: "#f3e1b6",
  horn: "#f3ead2",
  hornBase: "#d8c9a4",
  rock1: "#9a948b",
  rock2: "#b8a990",
  rock3: "#8a7862",
  rockLight: "#d6caae",
  eye: "#2a1a10",
  brow: "#5a3518",
  mouth: "#8f2a30",
  tongue: "#e8707c",
  glove: "#3a2b24",
  strap: "#5e3c22",
  buckle: "#c9a24a",
  pack: "#8a6a44",
  packDark: "#6a4e30",
  // The kart.
  sand: "#e6d2a2",
  sandDark: "#c7ae7c",
  wood: "#8a5a34",
  woodDark: "#5f3c22",
  stone: "#625d58",
  stoneLight: "#87817a",
  orange: "#e07a2e",
  green: "#5d9e3a",
  greenLight: "#9ccf62",
  seat: "#4a3426",
  tyre: "#2b2626",
  ink: "#3a2a20",
};

/** The alternate look: Brakka in classic explorer red. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#d9533a",
  skinDark: "#a83a2a",
  rock1: "#e8a030",
  rock2: "#f2c050",
  rock3: "#c97a2a",
  rockLight: "#ffd86a",
  sand: "#f2d7a8",
  stone: "#9c3a2e",
  stoneLight: "#c4553e",
  orange: "#f2b33a",
};

type P = typeof MAIN;

const RIM = "#5a2414";
const RAY_A = "#c94a1c";
const RAY_B = "#ef8a2a";

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
    main: c.sand,
    dark: c.stone,
    stripe: c.orange,
    nose: c.orange,
    trim: c.stone,
    metal: "#4a4440",
    seat: c.seat,
    glass: "#f2c27a",
    tyre: c.tyre,
    rim: c.orange,
    cap: c.sand,
    tyreLine: c.orange,
    width: 1.08,
    front: "horns",
    pods: "intake",
    rear: "ducktail",
    spokes: 6,
    emblem: { kind: "footprint", disc: c.sand, ink: c.ink, rim: c.orange },
  });
}

// ------------------------------------------------------------------ Brakka

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "brakka";
  const torso = new THREE.Group();
  root.add(torso);

  // A compact, muscular body: broad shoulders, cream belly.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.01], rx: 0.22, ry: 0.19 },
        { at: [0, 0.12, 0.0], rx: 0.26, ry: 0.22 },
        { at: [0, 0.3, 0.01], rx: 0.28, ry: 0.21 },
        { at: [0, 0.43, 0.02], rx: 0.24, ry: 0.17 },
        { at: [0, 0.52, 0.03], rx: 0.16, ry: 0.14 },
      ],
      {
        sides: 12,
        steps: 2,
        up: [0, 0, 1],
        capStart: true,
        paint: (_t, a) => (Math.abs(a - Math.PI / 2) < 0.8 ? c.cream : c.skin),
      },
    ),
  );
  // Utility straps crossing the chest, and a little pack on the back.
  for (const s of [1, -1])
    body.addColored(
      strap(
        [
          [s * 0.2, 0.45, 0.13],
          [0, 0.27, 0.235],
          [-s * 0.21, 0.08, 0.2],
        ],
        0.024,
        0.01,
        c.strap,
      ),
    );
  body.add(box(0.06, 0.05, 0.03, 0.01), c.buckle, { p: [0, 0.27, 0.24] });
  body.addColored(backpack(0.26, 0.22, 0.12, { bag: c.pack, flap: c.packDark, buckle: c.buckle }), {
    p: [0, 0.3, -0.24],
  });
  torso.add(new THREE.Mesh(body.build(), mat));

  // The head: built by buildHead() below, once the rig exists.
  const head = new THREE.Group();
  torso.add(head);

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.21, 0.41, 0.08],
    upper: 0.21,
    fore: 0.19,
    radius: [0.075, 0.065, 0.055],
    color: c.skin,
    hand: c.glove,
    handSize: 0.075,
    hint: [0.9, -0.4, -0.2],
  });

  // A short, thick tail behind the seat.
  const tailJ = new THREE.Group();
  tailJ.position.set(0, 0.06, -0.16);
  tailJ.rotation.x = 0.35;
  torso.add(tailJ);
  tailJ.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          tube(
            [
              [0, 0, 0.04],
              [0, 0, -0.18],
              [0, -0.02, -0.34],
            ],
            [0.13, 0.09, 0.03],
            c.skin,
            { sides: 8 },
          ),
        )
        .build(),
      mat,
    ),
  );

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.2, 0], s: [0.26, 0.26, 0.21] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.6, 0.12], s: [0.27, 0.23, 0.32] })
      .add(cyl(0.5, 0.56, 0.06, 7), RAY_B, { p: [0, 0.84, -0.08], r: [1.15, 0, 0] })
      .add(cone(0.06, 0.3, 4), c.horn, { p: [0.15, 0.85, 0.35], r: [1.0, 0, 0] })
      .add(cone(0.06, 0.3, 4), c.horn, { p: [-0.15, 0.85, 0.35], r: [1.0, 0, 0] })
      .build(),
    mat,
  );

  const rig: RiderRig = {
    root,
    torso,
    neck: null,
    head,
    face: { eyes: [], brows: [], jaw: null, jawOpen: 0, lidOpen: -1.6, lidClosed: 1.45 },
    arms,
    hands,
    tail: [tailJ],
    wings: [],
    wiggles: [],
    low,
    cheer: [new THREE.Vector3(0.36, 0.66, 0.16), new THREE.Vector3(-0.36, 0.66, 0.16)],
    personality: {
      lean: 1.2,
      headTurn: 0.9,
      curiosity: 0.2,
      glanceEvery: 5,
      blinkEvery: 3.6,
      blinkTime: 0.12,
      bob: 0.02,
      bobHz: 1.6,
      steerHands: 1.0,
      boostKick: 0.9,
      boostFace: 0.55,
      grumble: 1,
      response: 1,
      restJaw: 0.06,
      restBrow: -0.2,
      restLids: 0.2,
      victory: "nod",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.5, 0.07);
  head.rotation.x = -0.1;
  head.scale.setScalar(1.36);
  const cream = new THREE.Color(c.cream);
  const skin = new THREE.Color(c.skin);

  // A blocky skull, deep at the cheeks, into a hooked beak.
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.12, -0.17], rx: 0.12, ry: 0.11, sq: 2.6 },
        { at: [0, 0.13, -0.1], rx: 0.2, ry: 0.18, sq: 2.8 },
        { at: [0, 0.12, 0.0], rx: 0.225, ry: 0.2, sq: 3 },
        { at: [0, 0.1, 0.1], rx: 0.2, ry: 0.18, sq: 3, flat: 0.25 },
        { at: [0, 0.07, 0.19], rx: 0.15, ry: 0.14, sq: 2.6, flat: 0.3 },
        { at: [0, 0.04, 0.26], rx: 0.1, ry: 0.11, sq: 2.2, flat: 0.2 },
        { at: [0, -0.01, 0.31], rx: 0.055, ry: 0.07 },
        { at: [0, -0.06, 0.33], rx: 0.015, ry: 0.02 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (t > 0.74 ? cream : t > 0.5 && a < -0.2 ? cream : skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.045, 0.1, 0.255], s: [0.02, 0.013, 0.014] });
    // The heavy brow ridge: a bony shelf over each eye, sloping down toward the nose.
    skull.addColored(
      loft(
        [
          { at: [s * 0.2, 0.25, 0.1], rx: 0.03, ry: 0.025, color: c.skinDark },
          { at: [s * 0.15, 0.27, 0.17], rx: 0.05, ry: 0.035, color: c.skinDark },
          { at: [s * 0.06, 0.235, 0.225], rx: 0.04, ry: 0.03, color: c.skinDark },
          { at: [s * 0.0, 0.21, 0.24], rx: 0.02, ry: 0.02, color: c.skinDark },
        ],
        { sides: 8, steps: 2, capStart: true, capEnd: true, up: [0, 0, 1] },
      ),
    );
    // A tough set to the mouth: a dark line, turned down at the back.
    skull.addColored(
      tube(
        [
          [s * 0.07, -0.025, 0.28],
          [s * 0.12, -0.005, 0.2],
          [s * 0.165, 0.0, 0.1],
          [s * 0.175, -0.025, 0.04],
        ],
        [0.008, 0.01, 0.01, 0.007],
        c.mouth,
        { sides: 5 },
      ),
    );
  }
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, -0.01, 0.15], s: [0.13, 0.04, 0.14] });
  // Three horns: two long brow horns thrust forward and out, a stout nose horn.
  for (const s of [1, -1])
    skull.addColored(
      horn(
        [s * 0.12, 0.27, 0.06],
        [s * 0.22, 0.36, 0.56],
        0.065,
        c.horn,
        [s * 0.04, 0.12, -0.08],
        8,
      ),
    );
  skull.addColored(horn([0, 0.13, 0.22], [0, 0.25, 0.32], 0.05, c.horn, [0, 0.03, -0.03], 7));
  for (const s of [1, -1])
    skull.add(cone(0.07, 0.04, 8), c.hornBase, {
      p: [s * 0.12, 0.27, 0.06],
      r: [-0.6, 0, s * 0.2],
    });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The frill: a sunburst shield behind the head, ringed with spikes.
  const frill = new THREE.Group();
  frill.position.set(0, 0.2, -0.12);
  frill.rotation.x = -0.4;
  head.add(frill);
  const N = 11;
  const R = 0.5;
  const a0 = 0.02;
  const a1 = Math.PI - 0.02;
  const outline: [number, number][] = [];
  for (let i = 0; i <= N * 2; i++) {
    const a = a0 + (a1 - a0) * (i / (N * 2));
    const r = i % 2 ? R * 0.92 : R;
    outline.push([Math.cos(a) * r * 1.1, Math.sin(a) * r * 0.9 - 0.06]);
  }
  outline.push([-0.22, -0.14], [0.22, -0.14]);
  const fb = new Build();
  // The rim (dark), then the rays inside it, a touch in front and behind.
  fb.add(card(outline, 0.045), RIM);
  const inner = outline.map(([x, y]) => [x * 0.84, (y + 0.06) * 0.84 - 0.06] as [number, number]);
  const rays = (p: THREE.Vector3) => {
    const a = Math.atan2(p.y + 0.06, p.x);
    return Math.floor(a / (Math.PI / 9)) % 2 ? RAY_A : RAY_B;
  };
  fb.add(card(inner, 0.06), rays);
  // Two cream eye-spots on the front, a crest of studs up the middle of the back.
  for (const s of [1, -1]) {
    fb.add(ellipsoid(10, 6), c.cream, { p: [s * 0.22, 0.2, 0.032], s: [0.075, 0.06, 0.012] });
    fb.add(ellipsoid(8, 5), RIM, { p: [s * 0.22, 0.2, 0.04], s: [0.035, 0.028, 0.008] });
  }
  for (let k = 0; k < 4; k++)
    fb.add(cone(0.035, 0.07, 5), c.hornBase, {
      p: [0, 0.06 + k * 0.09, -0.04],
      r: [-Math.PI / 2, 0, 0],
    });
  // Ivory spikes round the edge, longest at the top.
  for (let i = 0; i <= N; i++) {
    const a = a0 + (a1 - a0) * (i / N);
    const len = 0.09 + 0.07 * Math.sin(a);
    fb.add(cone(0.04, len, 5), (p) => (p.y < 0 ? c.hornBase : c.horn), {
      p: [Math.cos(a) * (R * 1.1 + len * 0.35), Math.sin(a) * (R * 0.9 + len * 0.35) - 0.06, 0],
      r: [0, 0, a - Math.PI / 2],
    });
  }
  frill.add(new THREE.Mesh(fb.build(), mat));

  // The lower beak.
  const jaw = new THREE.Group();
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.01, -0.02], rx: 0.17, ry: 0.06, sq: 2.6 },
              { at: [0, -0.04, 0.12], rx: 0.14, ry: 0.06, flat: -0.4, sq: 2.6 },
              { at: [0, -0.05, 0.22], rx: 0.09, ry: 0.05, flat: -0.4 },
              { at: [0, -0.05, 0.28], rx: 0.03, ry: 0.02 },
            ],
            {
              sides: 10,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (_t, a) => (a > 0.5 && a < 2.6 ? c.mouth : c.cream),
            },
          ),
        )
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.02, 0.12], s: [0.075, 0.022, 0.08] })
        .build(),
      mat,
    ),
  );

  // Deep-set, narrowed eyes in a scowl, under the brow ridge.
  const eyes = buildEyes(head, {
    at: [0.105, 0.175, 0.19],
    size: [0.078, 0.088, 0.065],
    yaw: 0.3,
    iris: "#4a2a12",
    irisRing: "#c98a2a",
    lid: c.skinDark,
    inward: 0.1,
    lidTilt: 0.5,
    brow: { color: c.brow, at: [0.105, 0.258, 0.215], size: [0.075, 0.024, 0.032], tilt: 0.42 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.42 };
  rig.wiggles.push({ obj: frill, kind: "crest", side: 0, amount: 0.5 });
}

export const BRAKKA: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
