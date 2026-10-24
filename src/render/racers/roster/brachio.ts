/**
 * The brachiosaurus: friendly, gentle, steady but playful (Blake's concept sheet, our
 * own build).
 *
 * Silhouette: the long neck, rising tall over the kart, a small head on top with a
 * headdress of leaves (red, orange, green) and a leather flying cap with goggles.
 * Teal skin with lighter teal spots, a cream throat and belly.
 * Gear: leather straps with a gold sun medallion, a little bedroll.
 * Kart: the Bamboo Cruiser (the sleek family): cream and teal-spotted, a bamboo frame
 * lashed round it, leaf fins and island flowers, gold headlamps, flower hubs.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, cone, cyl, ellipsoid, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { bedroll, goggles, leaf, strap } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#2aa8b0",
  skinDark: "#1a7c86",
  spot: "#6ad8d0",
  belly: "#f4e4bc",
  mouth: "#8a2a36",
  tongue: "#f0788a",
  toe: "#2a2228",
  leafA: "#3f9a34",
  leafB: "#e8502a",
  leafC: "#f7a21e",
  leafRib: "#c8f08a",
  leather: "#7a4a28",
  leatherDark: "#55321c",
  gold: "#f2b830",
  lens: "#3ad0e0",
  roll: "#d8b47a",
  // The kart.
  cream: "#f2e2b8",
  bamboo: "#c89a4a",
  bambooDark: "#8a6a30",
  flower: "#f26a2a",
  flowerMid: "#ffd23a",
  seat: "#4a3426",
  tyre: "#252226",
  hub: "#1a9aa0",
};

/** The alternate look (a repeated rival): a lavender long-neck. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#9a7ad8",
  skinDark: "#6e54a8",
  spot: "#c8b0f0",
  hub: "#d8902a",
  flower: "#e83a8a",
};

type P = typeof MAIN;

/** A length of bamboo: a cane with darker rings at its nodes. */
function bamboo(
  b: Build,
  a: [number, number, number],
  z: [number, number, number],
  r: number,
  c: P,
) {
  const n = 5;
  const pts: [number, number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    pts.push([a[0] + (z[0] - a[0]) * t, a[1] + (z[1] - a[1]) * t, a[2] + (z[2] - a[2]) * t]);
  }
  b.addColored(
    tube(
      pts,
      r,
      pts.map((_, i) => (i % 2 ? c.bamboo : c.bambooDark)),
      { sides: 5 },
    ),
  );
}

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  const spot = new THREE.Color(c.skin);
  return sleekKart({
    main: c.cream,
    dark: c.skin,
    stripe: c.skin,
    nose: c.cream,
    trim: c.bamboo,
    metal: c.bambooDark,
    seat: c.seat,
    glass: "#fff0a0",
    tyre: c.tyre,
    rim: c.hub,
    cap: c.flowerMid,
    tyreLine: c.flowerMid,
    width: 1.0,
    front: "twin",
    pods: "round",
    rear: "wing",
    spokes: 5,
    emblem: { kind: "flower", disc: c.cream, ink: c.flower, rim: c.hub },
    extras(b, detail) {
      void spot;
      // Leaf fins off the back, and flowers tucked in.
      const leaves = [c.leafA, c.leafB, c.leafC, c.leafA];
      for (const s of [1, -1])
        for (let k = 0; k < (detail === 1 ? 2 : 3); k++)
          b.addColored(leaf(0.38 + k * 0.04, 0.1, leaves[k]!, c.leafRib), {
            p: [s * (0.3 + k * 0.08), 0.68, -0.98],
            r: [-1.4 + k * 0.12, s * 0.2, s * (0.3 + k * 0.3)],
          });
      if (detail === 1) return;
      for (const s of [1, -1]) {
        // The bamboo frame: rails along the sides and up round the cockpit.
        bamboo(b, [s * 0.46, 0.4, 0.95], [s * 0.52, 0.6, 0.2], 0.035, c);
        bamboo(b, [s * 0.52, 0.6, 0.2], [s * 0.48, 0.74, -0.5], 0.035, c);
        bamboo(b, [s * 0.48, 0.74, -0.5], [s * 0.36, 0.55, -1.1], 0.035, c);
        b.add(new THREE.TorusGeometry(0.045, 0.012, 4, 8), c.leatherDark, {
          p: [s * 0.52, 0.6, 0.2],
          r: [0, Math.PI / 2, 0],
        });
        // Gold headlamps on the nose.
        b.add(cyl(0.07, 0.075, 0.05, 10), c.gold, {
          p: [s * 0.25, 0.5, 1.08],
          r: [Math.PI / 2, 0, 0],
        });
        b.add(cyl(0.05, 0.05, 0.02, 10), "#fff6c8", {
          p: [s * 0.25, 0.5, 1.11],
          r: [Math.PI / 2, 0, 0],
        });
        // Island flowers on the sidepods.
        flower(b, [s * 0.56, 0.6, 0.0], c);
        // Leaves along the top of the pods.
        b.addColored(leaf(0.3, 0.09, c.leafA, c.leafRib), {
          p: [s * 0.52, 0.6, -0.05],
          r: [-1.3, 0, s * 0.7],
        });
      }
      // The roll bar: bamboo, lashed.
      bamboo(b, [0.3, 0.5, -0.66], [0.25, 1.0, -0.7], 0.04, c);
      bamboo(b, [-0.3, 0.5, -0.66], [-0.25, 1.0, -0.7], 0.04, c);
      bamboo(b, [0.27, 1.0, -0.7], [-0.27, 1.0, -0.7], 0.04, c);
    },
  });
}

function flower(b: Build, at: [number, number, number], c: P) {
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2;
    b.add(ellipsoid(5, 3), c.flower, {
      p: [at[0], at[1] + Math.cos(a) * 0.06, at[2] + Math.sin(a) * 0.06],
      s: [0.015, 0.05, 0.05],
    });
  }
  b.add(ellipsoid(6, 4), c.flowerMid, {
    p: [at[0] + Math.sign(at[0]) * 0.01, at[1], at[2]],
    s: [0.02, 0.025, 0.025],
  });
}

// ------------------------------------------------------------------ the long-neck

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "brachio";
  const torso = new THREE.Group();
  root.add(torso);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);
  const spot = new THREE.Color(c.spot);
  const spots = (t: number, a: number) => Math.sin(t * 31 + a * 5) * Math.sin(a * 7 - t * 17) > 0.5;
  const skinPaint = (t: number, a: number) =>
    Math.abs(a - Math.PI / 2) < 0.75 ? belly : spots(t, a) ? spot : skin;

  // A round, comfortable body.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.02], rx: 0.22, ry: 0.19 },
        { at: [0, 0.12, -0.01], rx: 0.25, ry: 0.22 },
        { at: [0, 0.27, 0.0], rx: 0.22, ry: 0.19 },
        { at: [0, 0.38, 0.02], rx: 0.15, ry: 0.13 },
      ],
      { sides: 12, steps: 2, up: [0, 0, 1], capStart: true, paint: skinPaint },
    ),
  );
  // Straps over the shoulders to a gold sun medallion on the chest.
  for (const s of [1, -1])
    body.addColored(
      strap(
        [
          [s * 0.14, 0.36, -0.1],
          [s * 0.16, 0.35, 0.1],
          [s * 0.04, 0.22, 0.215],
        ],
        0.02,
        0.008,
        c.leather,
      ),
    );
  body.add(cyl(0.055, 0.055, 0.02, 12), c.gold, { p: [0, 0.21, 0.225], r: [Math.PI / 2, 0, 0] });
  body.add(cyl(0.03, 0.03, 0.025, 10), "#c88a1a", { p: [0, 0.21, 0.232], r: [Math.PI / 2, 0, 0] });
  // A bedroll and a leaf bundle on the back.
  body.addColored(bedroll(0.32, 0.06, { roll: c.roll, strap: c.leatherDark }), {
    p: [0, 0.32, -0.22],
  });
  for (const [k, col] of [c.leafA, c.leafB].entries())
    body.addColored(leaf(0.2, 0.06, col, c.leafRib), {
      p: [0.08 - k * 0.08, 0.36, -0.24],
      r: [-0.4, 0, 0.5 - k * 0.5],
    });
  torso.add(new THREE.Mesh(body.build(), mat));

  // The neck: long, rising and curving gently forward, two joints so it sways.
  const neck = new THREE.Group();
  neck.position.set(0, 0.34, 0.03);
  neck.rotation.x = 0.1;
  torso.add(neck);
  neck.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.05, 0], rx: 0.16, ry: 0.15 },
              { at: [0, 0.12, 0.02], rx: 0.13, ry: 0.125 },
              { at: [0, 0.3, 0.05], rx: 0.11, ry: 0.105 },
              { at: [0, 0.48, 0.08], rx: 0.095, ry: 0.095 },
              { at: [0, 0.6, 0.1], rx: 0.09, ry: 0.09 },
            ],
            {
              sides: 10,
              steps: 2,
              up: [0, 0, 1],
              paint: (t, a) =>
                Math.abs(a - Math.PI / 2) < 0.7 ? belly : spots(t * 2, a) ? spot : skin,
            },
          ),
        )
        .build(),
      mat,
    ),
  );
  const head = new THREE.Group();
  neck.add(head);

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.18, 0.3, 0.08],
    upper: 0.2,
    fore: 0.19,
    radius: [0.065, 0.055, 0.048],
    color: c.skin,
    hand: c.skin,
    handSize: 0.068,
    claws: c.toe,
    hint: [0.85, -0.5, -0.2],
  });

  // The tail, with a little leaf tuft at the tip.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.14, 0.25, 0.1],
    [0.1, 0.23, 0.055],
    [0.055, 0.2, 0.015],
  ];
  const lift = [0.55, -0.3, 0.15];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.08, -0.16);
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
          sides: 9,
          capStart: true,
          capEnd: true,
          paint: (t, a) => (a < -1.0 ? belly : spots(t + k, a) ? spot : skin),
        },
      ),
    );
    if (k === 2)
      for (const [f, col] of [c.leafB, c.leafC].entries())
        tb.addColored(leaf(0.16, 0.05, col, c.leafRib), {
          p: [0, 0, -len],
          r: [-Math.PI / 2 - 0.3, 0, -0.6 + f * 0.6],
        });
    j.add(new THREE.Mesh(tb.build(), mat));
    tail.push(j);
    parent = j;
  });

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.2, 0], s: [0.25, 0.26, 0.22] })
      .add(cyl(0.08, 0.12, 0.62, 6), c.skin, { p: [0, 0.68, 0.08], r: [0.12, 0, 0] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 1.12, 0.2], s: [0.15, 0.13, 0.22] })
      .add(cone(0.16, 0.25, 5), c.leafB, { p: [0, 1.28, 0.1], r: [-0.6, 0, 0] })
      .add(
        tube(
          [
            [0, 0.06, -0.14],
            [0, 0.06, -0.5],
            [0, 0.04, -0.82],
          ],
          [0.13, 0.08, 0.02],
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
    wiggles: [],
    low,
    cheer: [new THREE.Vector3(0.4, 0.6, 0.16), new THREE.Vector3(-0.4, 0.6, 0.16)],
    personality: {
      lean: 1.0,
      headTurn: 1.2,
      curiosity: 1,
      glanceEvery: 3,
      blinkEvery: 3.2,
      blinkTime: 0.16,
      bob: 0.03,
      bobHz: 1.6,
      steerHands: 1.0,
      boostKick: 0.9,
      boostFace: 0.9,
      grumble: 0.1,
      response: 0.85,
      restJaw: 0.12,
      restBrow: 0.25,
      restLids: 0.16,
      victory: "wave",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.6, 0.1);
  head.rotation.x = 0.1;
  head.scale.setScalar(1.3);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);

  // A small rounded head with a gentle, smiling muzzle (a domed brow, like the real one).
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.13], rx: 0.06, ry: 0.06 },
        { at: [0, 0.12, -0.08], rx: 0.13, ry: 0.13 },
        { at: [0, 0.13, 0.0], rx: 0.15, ry: 0.15 },
        { at: [0, 0.1, 0.09], rx: 0.13, ry: 0.11, flat: 0.25 },
        { at: [0, 0.07, 0.17], rx: 0.115, ry: 0.08, flat: 0.35 },
        { at: [0, 0.065, 0.24], rx: 0.095, ry: 0.06, flat: 0.3 },
        { at: [0, 0.065, 0.27], rx: 0.05, ry: 0.035 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (a < -0.8 && t > 0.4 ? belly : skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(ellipsoid(6, 4), c.skinDark, {
      p: [s * 0.035, 0.11, 0.255],
      s: [0.014, 0.01, 0.012],
    });
    skull.addColored(
      tube(
        [
          [s * 0.04, 0.015, 0.26],
          [s * 0.08, 0.012, 0.2],
          [s * 0.11, 0.03, 0.12],
          [s * 0.115, 0.06, 0.08],
        ],
        [0.007, 0.008, 0.008, 0.006],
        c.mouth,
        { sides: 5 },
      ),
    );
  }
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.01, 0.16], s: [0.08, 0.022, 0.1] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The headdress: a leather flying cap, goggles on its brim, leaves fanning up and back.
  const dress = new THREE.Group();
  dress.position.set(0, 0.2, -0.02);
  head.add(dress);
  const db = new Build();
  db.add(ellipsoid(10, 6), c.leather, { p: [0, 0.0, 0.0], s: [0.16, 0.08, 0.16] });
  db.addColored(goggles({ frame: c.gold, lens: c.lens, glint: "#e8ffff" }, 0.07, 0.048), {
    p: [0, 0.075, 0.08],
    r: [-1.3, 0, 0],
  });
  const cols = [c.leafB, c.leafA, c.leafC, c.leafA, c.leafB, c.leafC, c.leafA];
  for (let i = 1; i < 6; i++) {
    const x = (i - 3) * 0.04;
    db.addColored(leaf(0.24 - Math.abs(i - 3) * 0.02, 0.055, cols[i]!, c.leafRib), {
      p: [x, 0.04, -0.06],
      r: [-0.7, 0, -(i - 3) * 0.3],
    });
  }
  dress.add(new THREE.Mesh(db.build(), mat));

  const jaw = new THREE.Group();
  jaw.position.set(0, 0.0, 0.02);
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.015, -0.02], rx: 0.11, ry: 0.04 },
              { at: [0, -0.03, 0.1], rx: 0.1, ry: 0.035, flat: -0.4 },
              { at: [0, -0.025, 0.2], rx: 0.075, ry: 0.025 },
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
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.01, 0.1], s: [0.055, 0.016, 0.07] })
        .build(),
      mat,
    ),
  );

  // Big, kind eyes.
  const eyes = buildEyes(head, {
    at: [0.08, 0.16, 0.09],
    size: [0.065, 0.08, 0.058],
    yaw: 0.3,
    pitch: -0.05,
    iris: "#6a3a14",
    irisRing: "#d88a2a",
    irisScale: 1.1,
    lid: c.skin,
    inward: 0.18,
    lidTilt: -0.05,
    cheek: 0.15,
    brow: { color: c.skinDark, at: [0.08, 0.24, 0.11], size: [0.05, 0.016, 0.026], tilt: -0.15 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.35 };
  rig.wiggles.push({ obj: dress, kind: "crest", side: 0, amount: 0.8 });
}

export const BRACHIO: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
