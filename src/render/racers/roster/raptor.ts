/**
 * The velociraptor: agile, fast, mischievous (Blake's concept sheet, our own build).
 *
 * Silhouette: a wild crest of feathers (red, orange, teal, gold) bursting up and back
 * off the head, with aviator goggles pushed up on it; a slim body leaning forward over
 * the wheel; feather tufts on the forearms and a long tail ending in a feather fan.
 * Face: a long snout with a toothy grin, big amber eyes, a cheeky lid.
 * Orange skin going gold on top, a cream belly and throat, dark claws.
 * Gear: a red bandana with a white chevron, a leather belt and buckle.
 * Kart: the Feather Dart (the sleek family): ivory and orange, a needle nose with three
 * claw splitters, feather fins down the sides and fanning off the back, gold frame
 * rails, orange springs, teal hubs, a claw emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, cone, ellipsoid, horn, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { feather, goggles, strap } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#f08a1c",
  skinTop: "#f6b430",
  skinDark: "#c2600e",
  belly: "#f6e2b8",
  claw: "#2e2422",
  red: "#e8402a",
  orange: "#f7931e",
  teal: "#1fb0b0",
  gold: "#f6c431",
  green: "#5aa83a",
  mouth: "#8c2430",
  tongue: "#f07080",
  tooth: "#fffaf0",
  bandana: "#e2383a",
  chevron: "#fff4e0",
  leather: "#6a4226",
  leatherDark: "#4a2c18",
  buckle: "#d8b04a",
  lens: "#3fd0d8",
  // The kart.
  ivory: "#f4e6c8",
  frame: "#d9a72e",
  spring: "#f07a1e",
  seat: "#3a2a22",
  tyre: "#252022",
  hub: "#1f9ea0",
};

/** The alternate look (a repeated rival): a blue-and-green raptor. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#3a8ee0",
  skinTop: "#5ec0f0",
  skinDark: "#2466b0",
  red: "#7a52e0",
  orange: "#3ac0e0",
  teal: "#f0c030",
  bandana: "#f0a020",
  spring: "#3ac0e0",
  hub: "#e0a020",
};

type P = typeof MAIN;

const FEATHER_COLS = (c: P) =>
  [
    [c.red, c.orange],
    [c.teal, "#0f7c86"],
    [c.orange, c.gold],
    [c.red, c.gold],
    [c.teal, c.green],
  ] as const;

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
    main: c.ivory,
    dark: c.orange,
    stripe: c.teal,
    nose: c.orange,
    trim: c.teal,
    metal: c.frame,
    seat: c.seat,
    glass: "#ffd27a",
    tyre: c.tyre,
    rim: c.hub,
    cap: c.gold,
    tyreLine: c.gold,
    width: 0.94,
    front: "needle",
    pods: "delta",
    rear: "fins",
    spokes: 6,
    emblem: { kind: "claw", disc: c.ivory, ink: c.red, rim: c.teal },
    extras(b, detail) {
      const cols = FEATHER_COLS(c);
      // Feather fins fanning up and back off the tail, and down each side.
      const fan = detail === 1 ? 2 : 4;
      for (const s of [1, -1])
        for (let k = 0; k < fan; k++) {
          const [a, t] = cols[k % cols.length]!;
          b.addColored(feather(0.42 + 0.05 * k, 0.07, a, t), {
            p: [s * (0.18 + k * 0.07), 0.64 + k * 0.02, -0.98],
            r: [-1.35 + k * 0.12, s * 0.15, s * (0.3 + k * 0.22)],
          });
        }
      if (detail === 1) return;
      // Three big claws hooking forward and down off the nose.
      for (const k of [-1, 0, 1])
        b.addColored(
          horn([k * 0.11, 0.36, 1.12], [k * 0.2, 0.2, 1.52], 0.06, c.ivory, [0, 0.1, 0.03], 6),
        );
      for (const s of [1, -1]) {
        // Feather fins rising off each sidepod, raked back.
        for (let k = 0; k < 3; k++) {
          const [a, t] = cols[(k + 2) % cols.length]!;
          b.addColored(feather(0.42 - k * 0.03, 0.075, a, t), {
            p: [s * 0.56, 0.6, 0.35 - k * 0.2],
            r: [-1.05, 0, s * 0.45],
          });
        }
        // Gold frame rails along each side, up round the cockpit.
        b.addColored(
          tube(
            [
              [s * 0.42, 0.42, 0.9],
              [s * 0.5, 0.62, 0.3],
              [s * 0.48, 0.78, -0.15],
              [s * 0.4, 0.66, -0.75],
              [s * 0.3, 0.5, -1.1],
            ],
            0.03,
            c.frame,
            { sides: 6 },
          ),
        );
        // Orange coil springs by the front wheels.
        for (let k = 0; k < 3; k++)
          b.add(new THREE.TorusGeometry(0.05, 0.013, 3, 7), c.spring, {
            p: [s * 0.58, 0.36 + k * 0.045, 0.82],
            r: [Math.PI / 2, 0, 0],
          });
      }
      // The roll hoop behind the seat.
      b.addColored(
        tube(
          [
            [0.3, 0.5, -0.62],
            [0.26, 0.98, -0.66],
            [0, 1.06, -0.68],
            [-0.26, 0.98, -0.66],
            [-0.3, 0.5, -0.62],
          ],
          0.035,
          c.frame,
          { sides: 6 },
        ),
      );
    },
  });
}

// ------------------------------------------------------------------ the raptor

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "raptor";
  const torso = new THREE.Group();
  root.add(torso);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);
  const top = new THREE.Color(c.skinTop);
  const skinPaint = (_t: number, a: number) =>
    Math.abs(a - Math.PI / 2) < 0.7 ? belly : a < -0.6 ? top : skin;

  // A slim body leaning forward, cream down the front, gold down the back.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.02], rx: 0.16, ry: 0.14 },
        { at: [0, 0.1, 0.0], rx: 0.18, ry: 0.16 },
        { at: [0, 0.24, 0.02], rx: 0.16, ry: 0.14 },
        { at: [0, 0.36, 0.05], rx: 0.11, ry: 0.11 },
        { at: [0, 0.42, 0.07], rx: 0.085, ry: 0.09 },
      ],
      { sides: 12, steps: 2, up: [0, 0, 1], capStart: true, paint: skinPaint },
    ),
  );
  // The bandana knotted round the neck, its point down the chest with a white chevron.
  body.add(new THREE.TorusGeometry(0.09, 0.03, 5, 12), c.bandana, {
    p: [0, 0.38, 0.06],
    r: [Math.PI / 2 + 0.2, 0, 0],
  });
  // A leather belt with a buckle, and a strap over one shoulder to a pouch.
  body.add(new THREE.TorusGeometry(0.17, 0.022, 4, 14), c.leather, {
    p: [0, 0.06, 0.0],
    r: [Math.PI / 2, 0, 0],
    s: [1, 0.92, 1],
  });
  body.add(box(0.06, 0.05, 0.03, 0.01), c.buckle, { p: [0, 0.06, 0.165] });
  body.addColored(
    strap(
      [
        [0.11, 0.36, 0.08],
        [0.0, 0.22, 0.165],
        [-0.15, 0.06, 0.1],
      ],
      0.018,
      0.008,
      c.leather,
    ),
  );
  body.add(box(0.09, 0.08, 0.05, 0.015), c.leatherDark, {
    p: [-0.17, 0.04, -0.04],
    r: [0, 0.5, 0],
  });
  torso.add(new THREE.Mesh(body.build(), mat));
  const scarf = new THREE.Mesh(
    new Build()
      .add(cone(0.075, 0.14, 3), c.bandana, { r: [Math.PI, 0, 0], s: [1, 1, 0.3] })
      .add(cone(0.03, 0.05, 3), c.chevron, {
        p: [0, 0.0, 0.012],
        r: [Math.PI, 0, 0],
        s: [1, 1, 0.2],
      })
      .build(),
    mat,
  );
  scarf.position.set(0, 0.31, 0.15);
  scarf.rotation.x = -0.3;
  torso.add(scarf);

  // The neck: short and forward.
  const neck = new THREE.Group();
  neck.position.set(0, 0.38, 0.05);
  neck.rotation.x = 0.28;
  torso.add(neck);
  neck.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.04, 0], rx: 0.085, ry: 0.085 },
              { at: [0, 0.08, 0.02], rx: 0.07, ry: 0.072 },
              { at: [0, 0.17, 0.03], rx: 0.075, ry: 0.075 },
            ],
            { sides: 10, steps: 2, up: [0, 0, 1], paint: skinPaint },
          ),
        )
        .build(),
      mat,
    ),
  );
  const head = new THREE.Group();
  neck.add(head);

  // Arms with dark claws, a tuft of feathers on each forearm.
  const { arms, hands } = buildArms(torso, {
    shoulder: [0.13, 0.32, 0.08],
    upper: 0.18,
    fore: 0.18,
    radius: [0.045, 0.038, 0.032],
    color: c.skin,
    hand: c.skin,
    handSize: 0.055,
    claws: c.claw,
    hint: [0.8, -0.5, -0.3],
  });
  const cols = FEATHER_COLS(c);
  for (const arm of arms) {
    const tuft = new Build();
    for (let k = 0; k < 3; k++) {
      const [a, t] = cols[(k + (arm.side > 0 ? 0 : 1)) % cols.length]!;
      tuft.addColored(feather(0.13 + k * 0.02, 0.025, a, t), {
        p: [arm.side * 0.025, 0.01, 0.05 + k * 0.035],
        r: [0.5 + k * 0.15, 0, -arm.side * (1.25 + k * 0.2)],
      });
    }
    // On the forearm (built along +Z from the elbow), sticking out and back.
    arm.fore.add(new THREE.Mesh(tuft.build(), mat));
  }

  // The tail: long and thin, over the back of the kart, a feather fan at the tip.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.095, 0.24, 0.07],
    [0.07, 0.22, 0.045],
    [0.045, 0.2, 0.02],
  ];
  const lift = [0.55, -0.28, 0.15];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.08, -0.13);
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
          sides: 8,
          capStart: true,
          capEnd: true,
          paint: (_t, a) => (a < -1.0 ? belly : a > 0.8 ? top : skin),
        },
      ),
    );
    if (k === 2)
      for (let f = 0; f < 4; f++) {
        const [a, t] = cols[f % cols.length]!;
        tb.addColored(feather(0.2, 0.045, a, t), {
          p: [0, 0, -len + 0.06],
          r: [-0.7, 0, -0.9 + f * 0.6],
        });
      }
    j.add(new THREE.Mesh(tb.build(), mat));
    tail.push(j);
    parent = j;
  });

  // Far away: body, head and snout, a crest blob, the tail.
  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.2, 0.02], s: [0.17, 0.24, 0.16] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.72, 0.22], s: [0.16, 0.14, 0.3] })
      .add(cone(0.2, 0.45, 5), c.red, { p: [0, 0.98, 0.05], r: [-0.9, 0, 0] })
      .add(
        tube(
          [
            [0, 0.06, -0.12],
            [0, 0.08, -0.5],
            [0, 0.06, -0.85],
          ],
          [0.09, 0.06, 0.02],
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
    wiggles: [{ obj: scarf, kind: "flutter", side: 0, amount: 0.7 }],
    low,
    cheer: [new THREE.Vector3(0.4, 0.62, 0.14), new THREE.Vector3(-0.4, 0.62, 0.14)],
    personality: {
      lean: 1.5,
      headTurn: 1.25,
      curiosity: 0.8,
      glanceEvery: 2.8,
      blinkEvery: 2.6,
      blinkTime: 0.1,
      bob: 0.035,
      bobHz: 2.6,
      steerHands: 1.35,
      boostKick: 1.2,
      boostFace: 1.1,
      grumble: 0.4,
      response: 1.3,
      restJaw: 0.16,
      restBrow: 0.15,
      restLids: 0.18,
      victory: "cheer",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.18, 0.05);
  head.rotation.x = 0.05;
  head.scale.setScalar(1.45);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);
  const top = new THREE.Color(c.skinTop);

  // The skull: a rounded cranium into a long, low snout.
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.12, -0.17], rx: 0.06, ry: 0.06 },
        { at: [0, 0.13, -0.12], rx: 0.15, ry: 0.15 },
        { at: [0, 0.13, -0.02], rx: 0.18, ry: 0.17 },
        { at: [0, 0.11, 0.08], rx: 0.155, ry: 0.13 },
        { at: [0, 0.07, 0.18], rx: 0.12, ry: 0.09, flat: 0.35 },
        { at: [0, 0.05, 0.28], rx: 0.1, ry: 0.07, flat: 0.45 },
        { at: [0, 0.045, 0.37], rx: 0.085, ry: 0.058, flat: 0.4 },
        { at: [0, 0.045, 0.43], rx: 0.05, ry: 0.04 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (a < -0.7 && t > 0.35 ? belly : a > 1.0 ? top : skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.04, 0.085, 0.42], s: [0.016, 0.01, 0.014] });
    // The grin: up at the back, a row of little teeth along it.
    skull.addColored(
      tube(
        [
          [s * 0.05, 0.012, 0.42],
          [s * 0.09, 0.008, 0.32],
          [s * 0.12, 0.012, 0.2],
          [s * 0.14, 0.05, 0.11],
        ],
        [0.007, 0.008, 0.008, 0.006],
        c.mouth,
        { sides: 5 },
      ),
    );
    for (let k = 0; k < 5; k++)
      skull.add(cone(0.012, 0.035, 4), c.tooth, {
        p: [s * (0.055 + k * 0.016), 0.0, 0.41 - k * 0.05],
        r: [Math.PI, 0, 0],
      });
  }
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.0, 0.26], s: [0.09, 0.025, 0.16] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The crest: a burst of feathers up and back off the top of the head.
  const crest = new THREE.Group();
  crest.position.set(0, 0.25, -0.04);
  head.add(crest);
  const cb = new Build();
  const cols = FEATHER_COLS(c);
  let k = 0;
  for (let row = 0; row < 3; row++)
    for (let i = -2; i <= 2; i++) {
      const [a, t] = cols[(k++ * 3 + row) % cols.length]!;
      const len = 0.32 + 0.08 * (2 - row) - Math.abs(i) * 0.025;
      cb.addColored(feather(len, 0.055, a, t), {
        p: [i * 0.04, -row * 0.03, 0.06 - row * 0.08],
        r: [-0.45 - row * 0.35, 0, -i * 0.3],
      });
    }
  crest.add(new THREE.Mesh(cb.build(), mat));
  // The goggles, pushed up on the forehead in front of the crest, their band round it.
  const gg = new Build().addColored(
    goggles({ frame: c.gold, lens: c.lens, glint: "#e8ffff" }, 0.08, 0.055),
    {
      p: [0, 0.31, 0.0],
      r: [-1.15, 0, 0],
    },
  );
  gg.add(new THREE.TorusGeometry(0.16, 0.018, 4, 16), c.leather, {
    p: [0, 0.27, -0.04],
    r: [Math.PI / 2 + 0.55, 0, 0],
  });
  head.add(new THREE.Mesh(gg.build(), mat));

  // The lower jaw, with its own teeth.
  const jaw = new THREE.Group();
  jaw.position.set(0, 0.0, 0.04);
  head.add(jaw);
  const jb = new Build()
    .addColored(
      loft(
        [
          { at: [0, -0.02, -0.02], rx: 0.13, ry: 0.05 },
          { at: [0, -0.035, 0.12], rx: 0.1, ry: 0.04, flat: -0.4 },
          { at: [0, -0.03, 0.26], rx: 0.08, ry: 0.032, flat: -0.5 },
          { at: [0, -0.02, 0.36], rx: 0.045, ry: 0.022 },
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
    .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.012, 0.18], s: [0.06, 0.018, 0.1] });
  for (const s of [1, -1])
    for (let i = 0; i < 4; i++)
      jb.add(cone(0.011, 0.03, 4), c.tooth, {
        p: [s * (0.045 + i * 0.016), -0.01, 0.33 - i * 0.055],
      });
  jaw.add(new THREE.Mesh(jb.build(), mat));

  // Big amber eyes, set to the sides a little, a cheeky lid and a sharp brow.
  const eyes = buildEyes(head, {
    at: [0.08, 0.17, 0.12],
    size: [0.072, 0.09, 0.062],
    yaw: 0.22,
    pitch: -0.05,
    iris: "#7a3a0c",
    irisRing: "#e0902a",
    irisScale: 1.15,
    lid: c.skin,
    inward: 0.12,
    lidTilt: 0.42,
    cheek: 0.15,
    brow: { color: c.skinDark, at: [0.09, 0.255, 0.13], size: [0.065, 0.018, 0.03], tilt: 0.45 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.45 };
  rig.wiggles.push({ obj: crest, kind: "crest", side: 0, amount: 1.1 });
}

export const RAPTOR: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
