/**
 * Brakka v2: the bruiser. A blocky skull under a heavy bony brow, deep-set eyes in a
 * permanent scowl, a hooked beak with a tough set to it, two long brow horns thrust
 * forward and a stout nose horn; and the frill, big and graphic: a sunburst of rust and
 * orange rays inside a dark rim, ringed with ivory spikes, two cream eye-spots on the
 * front. From the race camera the frill is the whole silhouette.
 * Kart: the Rock Rally, broad and low, sandstone and burnt orange, horn splitters at
 * the front, a ducktail and fat twin pipes at the back.
 */
import * as THREE from "three";
import { buildEyes, type RiderRig } from "../../kit/rig";
import { Build, card, cone, ellipsoid, horn, loft, tube } from "../../kit/shapes";
import { skinMaterial } from "../../kit/paint";
import { sleekKart } from "../../kit/sleek";
import { BRAKKA } from "../brakka";
import type { RacerBuild } from "../types";
import { clearHead } from "./common";

type P = typeof BRAKKA.palettes.main;

const RIM = "#5a2414";
const RAY_A = "#c94a1c";
const RAY_B = "#ef8a2a";

function head(rig: RiderRig, c: P) {
  clearHead(rig);
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
      horn([s * 0.12, 0.27, 0.06], [s * 0.22, 0.36, 0.56], 0.065, c.horn, [s * 0.04, 0.12, -0.08], 8),
    );
  skull.addColored(horn([0, 0.13, 0.22], [0, 0.25, 0.32], 0.05, c.horn, [0, 0.03, -0.03], 7));
  for (const s of [1, -1])
    skull.add(cone(0.07, 0.04, 8), c.hornBase, { p: [s * 0.12, 0.27, 0.06], r: [-0.6, 0, s * 0.2] });
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
    fb.add(cone(0.035, 0.07, 5), c.hornBase, { p: [0, 0.06 + k * 0.09, -0.04], r: [-Math.PI / 2, 0, 0] });
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
  Object.assign(rig.personality, { restJaw: 0.06, restBrow: -0.2, restLids: 0.2 });
}

function rider(c: P): RiderRig {
  const rig = BRAKKA.rider(c);
  head(rig, c);
  return rig;
}

export const BRAKKA_V2: RacerBuild<P> = {
  palettes: BRAKKA.palettes,
  rider,
  kart: (c) =>
    sleekKart({
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
    }),
};
