/**
 * The stegosaurus: sturdy, dependable, laid-back but courageous (Blake's concept sheet,
 * our own build).
 *
 * Silhouette: the plates, big and graphic, two staggered rows of orange-and-teal plates
 * up the back and neck; a small head with a leaf-and-flower wreath; a spiked tail.
 * Green skin with lighter mottling, a cream belly.
 * Gear: a red bandana with a white leaf, a leather harness with a pouch.
 * Kart: the Plate Tank (the sleek family, broad): dark and gold, plate panels standing
 * along its spine, bone spikes round the nose and tail, leaves and flowers, a wide
 * stance, a leaf emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, card, cone, ellipsoid, horn, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { leaf, strap } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#5aa83a",
  skinDark: "#3a7a26",
  mottle: "#b8d040",
  belly: "#f0e0b0",
  plateA: "#f26a1a",
  plateB: "#1aa0a0",
  plateEdge: "#c83a1a",
  mouth: "#7a2a30",
  tongue: "#f0788a",
  bone: "#f1e4c4",
  boneDark: "#c9b48a",
  leaf: "#3f9a34",
  leafRib: "#a8e070",
  flower: "#f04a6a",
  bandana: "#e2383a",
  leather: "#6e4426",
  buckle: "#d8b04a",
  // The kart.
  dark: "#2c2a26",
  darkLight: "#4a443c",
  gold: "#e2a82a",
  teal: "#1a8a8a",
  seat: "#3a2a22",
  tyre: "#232022",
};

/** The alternate look (a repeated rival): a blue stego with gold plates. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#3a7ac8",
  skinDark: "#265a98",
  mottle: "#7ab0f0",
  plateA: "#f2c02a",
  plateB: "#e2382a",
  bandana: "#f0a020",
};

type P = typeof MAIN;

/**
 * A stegosaurus plate: a rounded diamond card in orange with a teal chevron set into
 * it (a smaller card, standing a little proud on both faces), a darker edge.
 */
function plate(h: number, w: number, c: P) {
  const shape = (hh: number, ww: number, y0: number) => {
    const pts: [number, number][] = [];
    const n = 6;
    for (let i = 0; i <= n; i++) {
      const t = i / n;
      pts.push([Math.sin(t * Math.PI) * ww * (1 - t * 0.3), y0 + t * hh]);
    }
    for (let i = n - 1; i > 0; i--) {
      const t = i / n;
      pts.push([-Math.sin(t * Math.PI) * ww * (1 - t * 0.3), y0 + t * hh]);
    }
    return pts;
  };
  return new Build()
    .add(card(shape(h, w, 0)), c.plateA)
    .add(card(shape(h * 0.55, w * 0.55, h * 0.22), 0.04), c.plateB)
    .build();
}

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
    main: c.dark,
    dark: c.darkLight,
    stripe: c.gold,
    nose: c.gold,
    trim: c.teal,
    metal: c.gold,
    seat: c.seat,
    glass: "#ffd27a",
    tyre: c.tyre,
    rim: c.teal,
    cap: c.gold,
    tyreLine: c.gold,
    width: 1.1,
    front: "horns",
    pods: "round",
    rear: "fins",
    spokes: 5,
    emblem: { kind: "leaf", disc: c.gold, ink: c.leaf, rim: c.teal },
    extras(b, detail) {
      // Plate panels standing along the spine behind the seat, staggered.
      const n = detail === 1 ? 3 : 4;
      for (let k = 0; k < n; k++) {
        const s = k % 2 ? 1 : -1;
        b.addColored(plate(0.34 - k * 0.03, 0.13, c), {
          p: [s * 0.08, 0.62, -0.7 - k * 0.14],
          r: [0, Math.PI / 2, s * 0.15],
        });
      }
      if (detail === 1) return;
      for (const s of [1, -1]) {
        // Plates on the sidepods too, and bone spikes round the nose and tail.
        for (let k = 0; k < 2; k++)
          b.addColored(plate(0.26, 0.1, c), {
            p: [s * 0.55, 0.56, 0.3 - k * 0.45],
            r: [0, Math.PI / 2, s * 0.35],
          });
        for (let k = 0; k < 2; k++)
          b.addColored(
            horn(
              [s * (0.2 + k * 0.14), 0.4, 1.05 - k * 0.1],
              [s * (0.32 + k * 0.2), 0.36, 1.35 - k * 0.1],
              0.05,
              c.bone,
              [0, 0.04, 0],
              6,
            ),
          );
        b.addColored(
          horn([s * 0.3, 0.6, -1.15], [s * 0.55, 0.85, -1.38], 0.055, c.bone, [0, 0, -0.04], 6),
        );
        b.addColored(
          horn([s * 0.2, 0.6, -1.18], [s * 0.3, 0.8, -1.42], 0.045, c.bone, [0, 0, -0.04], 6),
        );
        // Leaves and a flower tucked in by the pods.
        for (let k = 0; k < 2; k++)
          b.addColored(leaf(0.26, 0.08, c.leaf, c.leafRib), {
            p: [s * 0.5, 0.58, 0.55 - k * 0.42],
            r: [-1.2, 0, s * (0.9 + k * 0.1)],
          });
        b.add(ellipsoid(6, 4), c.flower, { p: [s * 0.58, 0.62, 0.0], s: [0.04, 0.04, 0.04] });
        // The reinforced suspension: gold coils by the front wheels.
        for (let k = 0; k < 3; k++)
          b.add(new THREE.TorusGeometry(0.055, 0.014, 3, 7), c.gold, {
            p: [s * 0.6, 0.35 + k * 0.045, 0.82],
            r: [Math.PI / 2, 0, 0],
          });
      }
    },
  });
}

// ------------------------------------------------------------------ the stego

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "stego";
  const torso = new THREE.Group();
  root.add(torso);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);
  const mottle = new THREE.Color(c.mottle);
  const spots = (t: number, a: number) =>
    Math.sin(t * 23 + a * 6) * Math.sin(a * 9 - t * 13) > 0.45;
  const skinPaint = (t: number, a: number) =>
    Math.abs(a - Math.PI / 2) < 0.8 ? belly : spots(t, a) ? mottle : skin;

  // A broad, sturdy body, hunched a little.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.02], rx: 0.24, ry: 0.2 },
        { at: [0, 0.12, -0.02], rx: 0.28, ry: 0.24 },
        { at: [0, 0.27, 0.0], rx: 0.25, ry: 0.21 },
        { at: [0, 0.38, 0.04], rx: 0.17, ry: 0.15 },
      ],
      { sides: 12, steps: 2, up: [0, 0, 1], capStart: true, paint: skinPaint },
    ),
  );
  // The bandana, its point down the chest, a white leaf on it.
  body.add(new THREE.TorusGeometry(0.13, 0.035, 5, 12), c.bandana, {
    p: [0, 0.36, 0.05],
    r: [Math.PI / 2 + 0.2, 0, 0],
  });
  body.add(cone(0.085, 0.15, 3), c.bandana, {
    p: [0, 0.27, 0.22],
    r: [Math.PI - 0.35, 0, 0],
    s: [1, 1, 0.3],
  });
  body.addColored(leaf(0.06, 0.02, "#fff4e0", "#ffffff"), {
    p: [0, 0.24, 0.245],
    r: [-0.35, 0, Math.PI],
  });
  // The harness and a pouch.
  body.addColored(
    strap(
      [
        [0.2, 0.34, 0.06],
        [0.02, 0.18, 0.25],
        [-0.22, 0.04, 0.16],
      ],
      0.022,
      0.01,
      c.leather,
    ),
  );
  body.add(box(0.1, 0.09, 0.05, 0.015), c.leather, { p: [-0.24, 0.06, 0.02], r: [0, 0.6, 0] });
  body.add(box(0.03, 0.025, 0.02, 0.005), c.buckle, { p: [-0.255, 0.08, 0.05], r: [0, 0.6, 0] });
  torso.add(new THREE.Mesh(body.build(), mat));

  // The plates: two staggered rows up the back, biggest over the shoulders.
  const plates = new THREE.Group();
  torso.add(plates);
  const pb = new Build();
  for (let k = 0; k < 6; k++) {
    const s = k % 2 ? 1 : -1;
    const h = 0.4 + 0.22 * Math.sin(((k + 1) / 7) * Math.PI);
    pb.addColored(plate(h, 0.2, c), {
      p: [s * 0.06, 0.02 + k * 0.07, -0.2 + k * 0.02],
      r: [-0.45 + k * 0.1, Math.PI / 2 + s * 0.6, 0],
    });
  }
  plates.add(new THREE.Mesh(pb.build(), mat));

  // A short, thick neck.
  const neck = new THREE.Group();
  neck.position.set(0, 0.34, 0.05);
  neck.rotation.x = 0.35;
  torso.add(neck);
  const nb = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, 0], rx: 0.14, ry: 0.13 },
        { at: [0, 0.08, 0.02], rx: 0.11, ry: 0.105 },
        { at: [0, 0.16, 0.03], rx: 0.1, ry: 0.1 },
      ],
      { sides: 10, steps: 2, up: [0, 0, 1], paint: skinPaint },
    ),
  );
  for (let k = 0; k < 1; k++)
    nb.addColored(plate(0.14, 0.07, c), {
      p: [0, 0.04 + k * 0.07, -0.09],
      r: [-0.6, Math.PI / 2, 0],
    });
  neck.add(new THREE.Mesh(nb.build(), mat));
  const head = new THREE.Group();
  neck.add(head);

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.2, 0.3, 0.1],
    upper: 0.2,
    fore: 0.19,
    radius: [0.075, 0.065, 0.055],
    color: c.skin,
    hand: c.skin,
    handSize: 0.072,
    claws: c.bone,
    hint: [0.9, -0.4, -0.2],
  });

  // The tail: thick, ending in four bone spikes (the thagomizer) with a leaf wrap.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.15, 0.24, 0.11],
    [0.11, 0.22, 0.07],
    [0.07, 0.2, 0.04],
  ];
  const lift = [0.5, -0.25, 0.2];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.08, -0.17);
    else j.position.set(0, 0, -segs[k - 1]![1]);
    j.rotation.x = lift[k]!;
    parent.add(j);
    const tb = new Build().addColored(
      loft(
        [
          { at: [0, 0, r0 * 0.5], rx: r0 * 0.7, ry: r0 * 0.7 },
          { at: [0, 0, 0], rx: r0, ry: r0 },
          { at: [0, 0, -len], rx: r1, ry: r1 },
          { at: [0, 0, -len - r1 * 0.6], rx: r1 * 0.6, ry: r1 * 0.6 },
        ],
        {
          sides: 7,
          capStart: true,
          capEnd: true,
          paint: (t, a) => (a < -1.0 ? belly : spots(t + k, a) ? mottle : skin),
        },
      ),
    );
    if (k < 2)
      tb.addColored(plate(0.1, 0.05, c), {
        p: [0, r0 * 0.8, -len * 0.5],
        r: [-1.2, Math.PI / 2, 0],
      });
    if (k === 2) {
      for (const s of [1, -1])
        for (const d of [0.05, 0.17])
          tb.addColored(
            horn(
              [s * 0.03, 0.02, -len + d],
              [s * 0.16, 0.12, -len + d - 0.04],
              0.028,
              c.bone,
              [0, 0, 0],
              5,
            ),
          );
      tb.add(new THREE.TorusGeometry(0.06, 0.02, 4, 10), c.leather, { p: [0, 0, -len + 0.22] });
      tb.addColored(leaf(0.1, 0.035, c.leaf, c.leafRib), {
        p: [0, 0.05, -len + 0.22],
        r: [-0.4, 0, 0.4],
      });
    }
    j.add(new THREE.Mesh(tb.build(), mat));
    tail.push(j);
    parent = j;
  });

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.2, 0], s: [0.27, 0.27, 0.23] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.62, 0.2], s: [0.15, 0.13, 0.22] })
      .add(cone(0.18, 0.42, 4), c.plateA, { p: [0, 0.52, -0.16], r: [-0.3, 0, 0], s: [0.3, 1, 1] })
      .add(
        tube(
          [
            [0, 0.06, -0.14],
            [0, 0.06, -0.5],
            [0, 0.04, -0.8],
          ],
          [0.14, 0.09, 0.03],
          c.skin,
          { sides: 5 },
        ),
        c.skin,
      )
      .build(),
    mat,
  );

  const rig: RiderRig = {
    root,
    torso,
    neck,
    head,
    face: { eyes: [], brows: [], jaw: null, jawOpen: 0, lidOpen: -1.6, lidClosed: 1.45 },
    arms,
    hands,
    tail,
    wings: [],
    wiggles: [{ obj: plates, kind: "bounce", side: 0, amount: 0.4 }],
    low,
    cheer: [new THREE.Vector3(0.4, 0.6, 0.18), new THREE.Vector3(-0.4, 0.6, 0.18)],
    personality: {
      lean: 0.95,
      headTurn: 0.8,
      curiosity: 0.4,
      glanceEvery: 4.5,
      blinkEvery: 3.8,
      blinkTime: 0.18,
      bob: 0.02,
      bobHz: 1.4,
      steerHands: 0.9,
      boostKick: 0.85,
      boostFace: 0.8,
      grumble: 0.2,
      response: 0.8,
      restJaw: 0.1,
      restBrow: 0.1,
      restLids: 0.3,
      victory: "nod",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.16, 0.05);
  head.rotation.x = -0.15;
  head.scale.setScalar(1.4);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);

  // A small, long head with a beaky, smiling snout.
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.14], rx: 0.07, ry: 0.07 },
        { at: [0, 0.12, -0.08], rx: 0.14, ry: 0.13 },
        { at: [0, 0.12, 0.02], rx: 0.16, ry: 0.14 },
        { at: [0, 0.1, 0.11], rx: 0.13, ry: 0.11, flat: 0.25 },
        { at: [0, 0.07, 0.2], rx: 0.1, ry: 0.08, flat: 0.35 },
        { at: [0, 0.055, 0.27], rx: 0.07, ry: 0.06, flat: 0.3 },
        { at: [0, 0.04, 0.31], rx: 0.03, ry: 0.03 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (t > 0.85 ? "#e0b840" : a < -0.8 && t > 0.4 ? belly : skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.03, 0.09, 0.28], s: [0.012, 0.009, 0.01] });
    skull.addColored(
      tube(
        [
          [s * 0.03, 0.012, 0.29],
          [s * 0.07, 0.01, 0.22],
          [s * 0.1, 0.03, 0.14],
          [s * 0.11, 0.06, 0.1],
        ],
        [0.007, 0.008, 0.008, 0.006],
        c.mouth,
        { sides: 5 },
      ),
    );
  }
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.01, 0.18], s: [0.07, 0.02, 0.1] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The wreath: leaves and pink flowers round the head.
  const crown = new THREE.Group();
  crown.position.set(0, 0.2, -0.02);
  head.add(crown);
  const wb = new Build();
  for (let k = 0; k < 7; k++) {
    const a = (k / 7) * Math.PI * 2;
    wb.addColored(leaf(0.12, 0.045, c.leaf, c.leafRib), {
      p: [Math.sin(a) * 0.13, 0, Math.cos(a) * 0.12],
      r: [-0.7 - 0.4 * Math.cos(a), a, 0],
    });
  }
  for (const [x, z] of [
    [0.09, 0.08],
    [-0.1, 0.05],
    [0.0, -0.1],
  ] as [number, number][])
    wb.add(ellipsoid(6, 4), c.flower, { p: [x, 0.02, z], s: [0.035, 0.03, 0.035] });
  crown.add(new THREE.Mesh(wb.build(), mat));

  const jaw = new THREE.Group();
  jaw.position.set(0, 0.0, 0.02);
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.015, -0.02], rx: 0.12, ry: 0.045 },
              { at: [0, -0.03, 0.1], rx: 0.09, ry: 0.035, flat: -0.4 },
              { at: [0, -0.025, 0.22], rx: 0.05, ry: 0.025 },
            ],
            {
              sides: 12,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (_t, a) => (a > 0.5 && a < 2.6 ? c.mouth : c.belly),
            },
          ),
        )
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.01, 0.1], s: [0.05, 0.016, 0.07] })
        .build(),
      mat,
    ),
  );

  // Calm, half-lidded eyes (laid-back), brows up a little.
  const eyes = buildEyes(head, {
    at: [0.085, 0.16, 0.1],
    size: [0.062, 0.075, 0.055],
    yaw: 0.32,
    pitch: -0.05,
    iris: "#6a3a14",
    irisRing: "#d8a03a",
    irisScale: 1.05,
    lid: c.skin,
    inward: 0.15,
    lidTilt: -0.1,
    cheek: 0.2,
    brow: { color: c.skinDark, at: [0.085, 0.235, 0.12], size: [0.05, 0.016, 0.026], tilt: -0.1 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.35 };
  rig.wiggles.push({ obj: crown, kind: "sway", side: 0, amount: 0.5 });
}

export const STEGO: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
