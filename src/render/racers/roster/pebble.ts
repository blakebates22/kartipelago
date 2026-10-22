/**
 * Pebble the ankylosaurus: the Shoreline Roller (design D), an ankylosaur you can't
 * mistake.
 *
 * Silhouette: the armoured dome with rows of ivory spikes, long flank spikes pointing out
 * sideways, a spiked collar, and a tail with spikes down both sides and a big two-lobed
 * club over the back of the kart.
 * Face: a wide, flat, triangular head armoured with plates, big horns swept back from the
 * corners of the skull and smaller ones at the cheeks; heavy bony brows over half-lidded,
 * easy-going eyes and a content smile. Slate-blue skin, cream muzzle and belly.
 * Kart: the Shore Cruiser (the sleek family): round and smooth, sky blue and cream with a
 * cyan line, twin winglets, bubble pods, fins at the back and a spiral emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, cone, ellipsoid, gem, horn, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#7891c2",
  skinDark: "#56709e",
  cream: "#f2e4c4",
  plate: "#90a4cc",
  plateDark: "#6b81ab",
  spike: "#f2ead4",
  spikeBase: "#cfc4a6",
  eye: "#1a1418",
  mouth: "#8a2a3a",
  tongue: "#ec7a8c",
  glove: "#2c3346",
  brow: "#3a4766",
  // The kart.
  blue: "#5f9ee0",
  blueDark: "#3f74b8",
  cream2: "#f5ecd6",
  sand: "#dcc79a",
  wood: "#b9895a",
  slate: "#3c4a5e",
  cyan: "#35d0d8",
  seat: "#2f3b52",
  tyre: "#262a33",
};

/** The alternate look: Pebble as a sandy canyon cruiser. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#b07a4a",
  skinDark: "#8a5a32",
  plate: "#c4925a",
  plateDark: "#8f6236",
  blue: "#d9773a",
  blueDark: "#b0552a",
  cyan: "#f2b33a",
};

type P = typeof MAIN;

/** A spike on the armour, from `base` pointing along `dir`, on a plate. */

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
    main: c.blue,
    dark: c.blueDark,
    stripe: c.cyan,
    nose: c.cream2,
    trim: c.cream2,
    metal: "#3c4452",
    seat: c.seat,
    glass: "#c8f4ff",
    tyre: c.tyre,
    rim: c.cream2,
    cap: c.cyan,
    tyreLine: c.cyan,
    front: "twin",
    pods: "round",
    rear: "fins",
    spokes: 7,
    emblem: { kind: "spiral", disc: c.cream2, ink: "#2bb0c0", rim: c.blue },
  });
}

// ------------------------------------------------------------------ Pebble

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "pebble";
  const torso = new THREE.Group();
  root.add(torso);

  // A round, compact body with a cream belly.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, 0.0, -0.02], rx: 0.25, ry: 0.18 },
        { at: [0, 0.12, -0.02], rx: 0.29, ry: 0.26 },
        { at: [0, 0.28, -0.02], rx: 0.27, ry: 0.24 },
        { at: [0, 0.4, 0.0], rx: 0.2, ry: 0.18 },
        { at: [0, 0.47, 0.02], rx: 0.12, ry: 0.12 },
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
  // The armoured back: a dome of plates, with rows of ivory spikes.
  body.add(gem(2), (p) => (p.y > 0.55 ? c.plate : c.plateDark), {
    p: [0, 0.27, -0.08],
    s: [0.33, 0.33, 0.28],
  });
  const rows: [number, number, number][] = [
    // [height on the dome (0 low .. 1 top), spikes in the row, spike size]
    [0.24, 7, 0.13],
    [0.45, 6, 0.16],
    [0.8, 4, 0.15],
  ];
  rows.forEach(([hgt, n, size], ri) => {
    for (let k = 0; k < n; k++) {
      // Spread over the back half (and round the sides), facing outward.
      const span = hgt > 0.9 ? 0.6 : 2.6 - hgt * 1.2;
      const a = Math.PI + (n === 1 ? 0 : (k / (n - 1) - 0.5) * span) + (ri % 2 ? 0.12 : 0);
      const el = (hgt * Math.PI) / 2.3;
      const dir = new THREE.Vector3(
        Math.sin(a) * Math.cos(el),
        Math.sin(el),
        Math.cos(a) * Math.cos(el),
      );
      const base = new THREE.Vector3(0, 0.27, -0.08).add(
        dir.clone().multiply(new THREE.Vector3(0.33, 0.33, 0.28)),
      );
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      const e = new THREE.Euler().setFromQuaternion(q);
      body.add(cone(size * 0.55, size * 1.5, 6), (p) => (p.y < -0.25 ? c.spikeBase : c.spike), {
        p: [base.x, base.y, base.z],
        r: [e.x, e.y, e.z],
      });
      // A plate under each spike.
      body.add(gem(0), c.plateDark, {
        p: [base.x * 0.97, base.y, base.z * 0.97],
        r: [e.x, e.y, e.z],
        s: [size * 0.95, size * 0.3, size * 0.95],
      });
    }
  });
  torso.add(new THREE.Mesh(body.build(), mat));

  // The head: built by buildHead() below, once the rig exists.
  const head = new THREE.Group();
  torso.add(head);

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.23, 0.37, 0.1],
    upper: 0.2,
    fore: 0.19,
    radius: [0.072, 0.062, 0.055],
    color: c.skin,
    hand: c.glove,
    handSize: 0.07,
    hint: [0.85, -0.5, -0.2],
  });

  // The thick tail and its rounded club, resting out over the back of the kart.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.14, 0.2, 0.11],
    [0.11, 0.17, 0.085],
    [0.085, 0.13, 0.07],
  ];
  const lift = [0.5, -0.32, -0.12];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.09, -0.2);
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
        { sides: 9, capStart: true, capEnd: true, paint: (_t, a) => (a < -1.0 ? c.cream : c.skin) },
      ),
    );
    // Small plates down the top of the tail.
    tb.add(gem(0), c.plateDark, {
      p: [0, r0 * 0.85, -len * 0.5],
      s: [r0 * 0.7, r0 * 0.3, len * 0.35],
    });
    if (k === 2) {
      // The club: a heavy rounded knob with ivory bumps.
      tb.add(ellipsoid(10, 7), c.plate, { p: [0, 0, -len - 0.08], s: [0.17, 0.12, 0.13] });
      for (const s of [1, -1])
        tb.add(ellipsoid(6, 4), c.spike, { p: [s * 0.15, 0, -len - 0.08], s: [0.05, 0.06, 0.06] });
      tb.add(ellipsoid(6, 4), c.spike, { p: [0, 0.1, -len - 0.08], s: [0.05, 0.04, 0.05] });
    }
    j.add(new THREE.Mesh(tb.build(), mat));
    tail.push(j);
    parent = j;
  });

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(7, 5), c.plate, { p: [0, 0.22, -0.06], s: [0.34, 0.34, 0.3] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.58, 0.2], s: [0.27, 0.21, 0.32] })
      .add(cone(0.06, 0.12, 4), c.spike, { p: [0.25, 0.4, -0.2] })
      .add(cone(0.06, 0.12, 4), c.spike, { p: [-0.25, 0.4, -0.2] })
      .add(cone(0.06, 0.12, 4), c.spike, { p: [0, 0.55, -0.25] })
      .add(ellipsoid(5, 4), c.plate, { p: [0, 0.32, -0.85], s: [0.17, 0.12, 0.14] })
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
    tail,
    wings: [],
    wiggles: [],
    low,
    cheer: [new THREE.Vector3(0.36, 0.6, 0.18), new THREE.Vector3(-0.38, 0.62, 0.2)],
    personality: {
      lean: 1.0,
      headTurn: 0.6,
      curiosity: 0.3,
      glanceEvery: 6,
      blinkEvery: 4.5,
      blinkTime: 0.28,
      bob: 0.018,
      bobHz: 1.1,
      steerHands: 0.7,
      boostKick: 1.7,
      boostFace: 1.2,
      grumble: 0.1,
      response: 0.75,
      restJaw: 0.05,
      restBrow: 0.1,
      restLids: 0.42,
      victory: "wave",
    },
  };
  armour(rig, c);
  buildHead(rig, c);
  return rig;
}

/** A spike on the armour, from `base` pointing along `dir`, on a plate. */
function spike(b: Build, c: P, base: THREE.Vector3, dir: THREE.Vector3, len: number) {
  const q = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    dir.clone().normalize(),
  );
  const e = new THREE.Euler().setFromQuaternion(q);
  const mid = base.clone().addScaledVector(dir.clone().normalize(), len * 0.5);
  b.add(cone(len * 0.3, len, 7), (p) => (p.y < -len * 0.2 ? c.spikeBase : c.spike), {
    p: [mid.x, mid.y, mid.z],
    r: [e.x, e.y, e.z],
  });
  b.add(gem(0), c.plateDark, {
    p: [base.x, base.y, base.z],
    r: [e.x, e.y, e.z],
    s: [len * 0.42, len * 0.14, len * 0.42],
  });
}

function armour(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const b = new Build();
  const centre = new THREE.Vector3(0, 0.27, -0.08);
  // Flank spikes: long, out sideways and a little back, behind the arms.
  const flank: [number, number, number, number][] = [
    // [height, z, length, sweep back]
    [0.34, -0.1, 0.26, 0.2],
    [0.28, -0.26, 0.3, 0.4],
    [0.2, -0.38, 0.22, 0.65],
  ];
  for (const s of [1, -1])
    for (const [y, z, len, back] of flank) {
      const base = new THREE.Vector3(s * 0.31, y, z);
      spike(b, c, base, new THREE.Vector3(s, 0.15, -back), len);
    }
  // A collar of short spikes across the shoulders, behind the head.
  for (const s of [1, -1])
    for (const [x, len] of [
      [0.12, 0.12],
      [0.22, 0.14],
    ] as const)
      spike(b, c, new THREE.Vector3(s * x, 0.5, -0.12), new THREE.Vector3(s * 0.5, 1, -0.35), len);
  // Studs over the top of the dome, between the spike rows.
  for (let k = 0; k < 9; k++) {
    const a = Math.PI + (k / 8 - 0.5) * 2.2;
    const el = 0.55 + (k % 2) * 0.25;
    const dir = new THREE.Vector3(
      Math.sin(a) * Math.cos(el),
      Math.sin(el),
      Math.cos(a) * Math.cos(el),
    );
    const p = centre.clone().add(dir.clone().multiply(new THREE.Vector3(0.335, 0.335, 0.285)));
    b.add(gem(0), c.spike, { p: [p.x, p.y, p.z], s: 0.032 });
  }
  rig.torso.add(new THREE.Mesh(b.build(), mat));

  // The tail: spikes down both sides, and a big two-lobed club.
  rig.tail.forEach((j, k) => {
    const len = [0.2, 0.17, 0.13][k]!;
    const r0 = [0.14, 0.11, 0.085][k]!;
    const tb = new Build();
    for (const s of [1, -1])
      tb.add(cone(0.03, 0.11 - k * 0.015, 5), c.spike, {
        p: [s * (r0 + 0.02), 0.02, -len * 0.5],
        r: [0, 0, -s * (Math.PI / 2 - 0.15)],
      });
    if (k === 2) {
      for (const s of [1, -1]) {
        tb.add(gem(1), (p) => (p.y > 0.3 ? c.plate : c.plateDark), {
          p: [s * 0.1, 0, -len - 0.06],
          s: [0.14, 0.12, 0.15],
        });
        tb.add(cone(0.04, 0.09, 5), c.spike, {
          p: [s * 0.25, 0, -len - 0.06],
          r: [0, 0, (-s * Math.PI) / 2],
        });
        tb.add(cone(0.035, 0.07, 5), c.spike, {
          p: [s * 0.1, 0.13, -len - 0.06],
          r: [0, 0, -s * 0.2],
        });
      }
    }
    j.add(new THREE.Mesh(tb.build(), mat));
  });
}

function buildHead(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.42, 0.13);
  head.rotation.x = -0.05;
  head.scale.setScalar(1.3);
  const cream = new THREE.Color(c.cream);
  const skin = new THREE.Color(c.skin);

  // Wide, flat and triangular from above, into a small beak.
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.15], rx: 0.14, ry: 0.08, sq: 2.6 },
        { at: [0, 0.11, -0.09], rx: 0.24, ry: 0.13, sq: 2.8 },
        { at: [0, 0.11, 0.0], rx: 0.255, ry: 0.14, sq: 3 },
        { at: [0, 0.09, 0.1], rx: 0.21, ry: 0.12, sq: 2.8, flat: 0.3 },
        { at: [0, 0.07, 0.18], rx: 0.15, ry: 0.09, sq: 2.6, flat: 0.35 },
        { at: [0, 0.06, 0.24], rx: 0.1, ry: 0.065, sq: 2.4, flat: 0.3 },
        { at: [0, 0.055, 0.27], rx: 0.04, ry: 0.03 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => ((t > 0.6 && a < 0.2) || t > 0.85 ? cream : skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    // The horns: big ones swept back from the skull's top corners, smaller ones down
    // and out at the cheeks.
    skull.addColored(
      horn([s * 0.2, 0.17, -0.08], [s * 0.38, 0.22, -0.26], 0.055, c.spike, [0, 0.03, 0.02], 7),
    );
    skull.addColored(
      horn([s * 0.22, 0.05, -0.03], [s * 0.36, -0.06, -0.1], 0.045, c.spike, [0, 0.01, 0.02], 7),
    );
    skull.add(gem(1), c.spikeBase, { p: [s * 0.2, 0.17, -0.08], s: [0.06, 0.04, 0.06] });
    skull.add(ellipsoid(6, 4), c.skinDark, {
      p: [s * 0.045, 0.09, 0.255],
      s: [0.018, 0.012, 0.012],
    });
    // A content smile, curling up at the corners.
    skull.addColored(
      tube(
        [
          [s * 0.06, 0.012, 0.25],
          [s * 0.13, 0.01, 0.17],
          [s * 0.19, 0.03, 0.07],
          [s * 0.2, 0.06, 0.03],
        ],
        [0.008, 0.009, 0.009, 0.006],
        c.mouth,
        { sides: 5 },
      ),
    );
  }
  // Armour plates across the top of the head.
  const plates: [number, number, number][] = [
    [0, 0.25, -0.03],
    [0.1, 0.23, -0.07],
    [-0.1, 0.23, -0.07],
    [0.06, 0.23, 0.06],
    [-0.06, 0.23, 0.06],
    [0, 0.235, -0.12],
  ];
  for (const [x, y, z] of plates)
    skull.add(gem(0), (p) => (p.y > 0 ? c.plate : c.plateDark), {
      p: [x, y, z],
      s: [0.06, 0.025, 0.055],
    });
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.01, 0.13], s: [0.13, 0.035, 0.12] });
  head.add(new THREE.Mesh(skull.build(), mat));

  const jaw = new THREE.Group();
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, 0.0, -0.03], rx: 0.19, ry: 0.05, sq: 2.6 },
              { at: [0, -0.02, 0.1], rx: 0.17, ry: 0.05, flat: -0.4, sq: 2.6 },
              { at: [0, -0.02, 0.2], rx: 0.11, ry: 0.04, flat: -0.4 },
              { at: [0, -0.01, 0.245], rx: 0.03, ry: 0.015 },
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
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.006, 0.11], s: [0.08, 0.02, 0.08] })
        .build(),
      mat,
    ),
  );

  // Easy-going, half-lidded eyes with bony scutes for brows.
  const eyes = buildEyes(head, {
    at: [0.105, 0.165, 0.15],
    size: [0.085, 0.092, 0.07],
    yaw: 0.3,
    iris: "#22446e",
    irisRing: "#8fd0f0",
    irisScale: 0.82,
    lid: c.skin,
    inward: 0.15,
    lidTilt: -0.08,
    cheek: 0.35,
    brow: { color: c.plate, at: [0.11, 0.25, 0.155], size: [0.08, 0.026, 0.045], tilt: 0.05 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.36 };
}

export const PEBBLE: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
