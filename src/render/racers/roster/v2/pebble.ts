/**
 * Pebble v2: an ankylosaur you can't mistake. A wide, flat, triangular head armoured with
 * plates, two big horns swept back from the corners of the skull and two more down at
 * the cheeks; heavy bony brows over half-lidded, easy-going eyes and a content smile.
 * The body gets the ankylosaur's flank spikes (long, pointing out sideways), a spiked
 * collar, and a tail with spikes down both sides and a big two-lobed club.
 * Kart: the Shore Cruiser, round and smooth, sky blue and cream with a cyan line, twin
 * winglets, bubble pods and fins at the back.
 */
import * as THREE from "three";
import { buildEyes, type RiderRig } from "../../kit/rig";
import { Build, cone, ellipsoid, gem, horn, loft, tube } from "../../kit/shapes";
import { skinMaterial } from "../../kit/paint";
import { sleekKart } from "../../kit/sleek";
import { PEBBLE } from "../pebble";
import type { RacerBuild } from "../types";
import { clearHead } from "./common";

type P = typeof PEBBLE.palettes.main;

/** A spike on the armour, from `base` pointing along `dir`, on a plate. */
function spike(b: Build, c: P, base: THREE.Vector3, dir: THREE.Vector3, len: number) {
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
  const e = new THREE.Euler().setFromQuaternion(q);
  const mid = base.clone().addScaledVector(dir.clone().normalize(), len * 0.5);
  b.add(cone(len * 0.3, len, 7), (p) => (p.y < -len * 0.2 ? c.spikeBase : c.spike), {
    p: [mid.x, mid.y, mid.z],
    r: [e.x, e.y, e.z],
  });
  b.add(gem(1), c.plateDark, { p: [base.x, base.y, base.z], r: [e.x, e.y, e.z], s: [len * 0.42, len * 0.14, len * 0.42] });
}

function body(rig: RiderRig, c: P) {
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
    const dir = new THREE.Vector3(Math.sin(a) * Math.cos(el), Math.sin(el), Math.cos(a) * Math.cos(el));
    const p = centre.clone().add(dir.clone().multiply(new THREE.Vector3(0.335, 0.335, 0.285)));
    b.add(ellipsoid(6, 4), c.spike, { p: [p.x, p.y, p.z], s: 0.03 });
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
        tb.add(gem(2), (p) => (p.y > 0.3 ? c.plate : c.plateDark), { p: [s * 0.1, 0, -len - 0.11], s: [0.14, 0.12, 0.15] });
        tb.add(cone(0.04, 0.09, 5), c.spike, { p: [s * 0.25, 0, -len - 0.11], r: [0, 0, -s * Math.PI / 2] });
        tb.add(cone(0.035, 0.07, 5), c.spike, { p: [s * 0.1, 0.13, -len - 0.11], r: [0, 0, -s * 0.2] });
      }
    }
    j.add(new THREE.Mesh(tb.build(), mat));
  });
}

function head(rig: RiderRig, c: P) {
  clearHead(rig);
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
    skull.addColored(horn([s * 0.2, 0.17, -0.08], [s * 0.38, 0.22, -0.26], 0.055, c.spike, [0, 0.03, 0.02], 7));
    skull.addColored(horn([s * 0.22, 0.05, -0.03], [s * 0.36, -0.06, -0.1], 0.045, c.spike, [0, 0.01, 0.02], 7));
    skull.add(gem(1), c.spikeBase, { p: [s * 0.2, 0.17, -0.08], s: [0.06, 0.04, 0.06] });
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.045, 0.09, 0.255], s: [0.018, 0.012, 0.012] });
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
    skull.add(gem(1), (p) => (p.y > 0 ? c.plate : c.plateDark), { p: [x, y, z], s: [0.06, 0.025, 0.055] });
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
  Object.assign(rig.personality, { restJaw: 0.05, restBrow: 0.1, restLids: 0.42 });
}

function rider(c: P): RiderRig {
  const rig = PEBBLE.rider(c);
  body(rig, c);
  head(rig, c);
  return rig;
}

export const PEBBLE_V2: RacerBuild<P> = {
  palettes: PEBBLE.palettes,
  rider,
  kart: (c) =>
    sleekKart({
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
    }),
};
