/**
 * Tiko v2: the mascot, made a hero. A big round cranium and a short, broad duck-bill
 * muzzle with a confident grin; tall front-set eyes with amber irises under a determined
 * lid and bold brows; and the crest, longer and bolder, a swoosh of gold into flame
 * orange with two dark bands, readable from anywhere.
 * Kart: the Jungle GT, teal and ivory with an orange stripe, a blade front wing and a
 * raised rear wing.
 */
import * as THREE from "three";
import { buildEyes, type RiderRig } from "../../kit/rig";
import { Build, ellipsoid, loft, tube } from "../../kit/shapes";
import { skinMaterial } from "../../kit/paint";
import { leaf } from "../../kit/props";
import { sleekKart } from "../../kit/sleek";
import { TIKO } from "../tiko";
import type { RacerBuild } from "../types";
import { clearHead } from "./common";

type P = typeof TIKO.palettes.main;

const IRIS = "#2f8a3e";
const IRIS_RING = "#7fd35a";

function head(rig: RiderRig, c: P) {
  clearHead(rig);
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.3, 0.06);
  head.rotation.x = -0.1;
  head.scale.setScalar(1.45);

  // The skull: a big round cranium, a short brow, and a broad, flat duck-bill muzzle.
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.13, -0.19], rx: 0.07, ry: 0.07 },
        { at: [0, 0.14, -0.15], rx: 0.17, ry: 0.17 },
        { at: [0, 0.14, -0.05], rx: 0.22, ry: 0.22 },
        { at: [0, 0.13, 0.05], rx: 0.21, ry: 0.2 },
        { at: [0, 0.07, 0.15], rx: 0.17, ry: 0.115, flat: 0.3 },
        { at: [0, 0.04, 0.23], rx: 0.155, ry: 0.08, flat: 0.45, sq: 2.6 },
        { at: [0, 0.045, 0.285], rx: 0.145, ry: 0.066, flat: 0.4, sq: 2.8 },
        { at: [0, 0.05, 0.315], rx: 0.1, ry: 0.042, sq: 2.6 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (a < -0.8 && t > 0.5 ? belly : skin),
      },
    ),
  );
  // Nostrils high on the bill.
  for (const s of [1, -1])
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.05, 0.09, 0.29], s: [0.02, 0.011, 0.016] });
  // The grin: a dark line along each side of the bill, curling up at the corners.
  for (const s of [1, -1])
    skull.addColored(
      tube(
        [
          [s * 0.1, 0.012, 0.29],
          [s * 0.14, 0.008, 0.22],
          [s * 0.165, 0.015, 0.15],
          [s * 0.165, 0.05, 0.1],
        ],
        [0.008, 0.009, 0.009, 0.006],
        c.mouth,
        { sides: 5 },
      ),
    );
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.0, 0.18], s: [0.13, 0.03, 0.14] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The crest: a bold swoosh off the top of the head, thick in the middle, a sharp
  // tip, gold into flame orange, with two dark bands and a light top edge.
  const crest = new THREE.Group();
  crest.position.set(0, 0.25, 0.0);
  head.add(crest);
  const gold = new THREE.Color(c.crestBase);
  const tip = new THREE.Color(c.crestTip);
  const band = new THREE.Color("#a8341a");
  crest.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.07, 0.1], rx: 0.06, ry: 0.06 },
              { at: [0, 0.02, 0.02], rx: 0.1, ry: 0.1 },
              { at: [0, 0.14, -0.1], rx: 0.125, ry: 0.13 },
              { at: [0, 0.26, -0.26], rx: 0.13, ry: 0.13 },
              { at: [0, 0.33, -0.45], rx: 0.115, ry: 0.11 },
              { at: [0, 0.35, -0.64], rx: 0.085, ry: 0.08 },
              { at: [0, 0.33, -0.8], rx: 0.04, ry: 0.045 },
              { at: [0, 0.3, -0.9], rx: 0.008, ry: 0.008 },
            ],
            {
              sides: 12,
              steps: 3,
              capStart: true,
              capEnd: true,
              paint: (t, a) => {
                const k = gold.clone().lerp(tip, Math.min(1, Math.max(0, (t - 0.15) * 1.4)));
                if ((t > 0.46 && t < 0.52) || (t > 0.62 && t < 0.68)) k.copy(band);
                if (a > 1.0 && a < 2.1) k.lerp(new THREE.Color("#ffffff"), 0.18);
                return k;
              },
            },
          ),
        )
        .build(),
      mat,
    ),
  );

  // The lower bill.
  const jaw = new THREE.Group();
  jaw.position.set(0, 0.0, 0.02);
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.02, -0.02], rx: 0.15, ry: 0.06 },
              { at: [0, -0.035, 0.1], rx: 0.15, ry: 0.05, flat: -0.4 },
              { at: [0, -0.03, 0.2], rx: 0.14, ry: 0.04, flat: -0.5, sq: 2.6 },
              { at: [0, -0.02, 0.27], rx: 0.1, ry: 0.025, sq: 2.6 },
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
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.012, 0.14], s: [0.075, 0.02, 0.09] })
        .build(),
      mat,
    ),
  );

  // Tall eyes set to the front (they look ahead, together), amber irises, a determined
  // lid and bold brows.
  const eyes = buildEyes(head, {
    at: [0.072, 0.18, 0.135],
    size: [0.08, 0.118, 0.07],
    yaw: 0.16,
    pitch: -0.04,
    iris: IRIS,
    irisRing: IRIS_RING,
    irisScale: 0.95,
    lid: c.skin,
    inward: 0.05,
    lidTilt: 0.32,
    cheek: 0.2,
    brow: { color: "#155f68", at: [0.08, 0.272, 0.165], size: [0.07, 0.022, 0.032], tilt: 0.34 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.4 };
  rig.wiggles.push({ obj: crest, kind: "crest", side: 0, amount: 1 });
  Object.assign(rig.personality, { restJaw: 0.08, restBrow: 0.05, restLids: 0.14 });
}

function rider(c: P): RiderRig {
  const rig = TIKO.rider(c);
  head(rig, c);
  return rig;
}

export const TIKO_V2: RacerBuild<P> = {
  palettes: TIKO.palettes,
  rider,
  kart: (c) =>
    sleekKart({
      main: c.kart,
      dark: c.kartDark,
      stripe: c.trim,
      nose: c.ivory,
      trim: c.ivory,
      metal: "#3b3436",
      seat: c.seat,
      glass: "#9fe4f0",
      tyre: c.tyre,
      rim: c.gold,
      cap: c.trim,
      tyreLine: c.trim,
      front: "blade",
      pods: "intake",
      rear: "wing",
      emblem: { kind: "palm", disc: c.ivory, ink: c.emblem, rim: c.trim },
      extras(b, detail) {
        if (detail === 1) return;
        // A pair of leaves tucked behind the rear wing's endplates.
        for (const s of [1, -1])
          b.addColored(leaf(0.4, 0.12, c.leaf, c.leafRib), { p: [s * 0.62, 0.98, -1.3], r: [-1.9, s * 0.25, s * 0.35] });
      },
    }),
};
