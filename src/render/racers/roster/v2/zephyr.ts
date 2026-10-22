/**
 * Zephyr v2: the hotshot ace. A leather flying helmet with the goggles pushed up on it,
 * the crest a long, sharp blade with a pale leading edge slicing back out of the
 * helmet, and a long needle beak. The personality is all in the face: half-lidded side
 * glance, one brow cocked high and a lopsided smirk.
 * Kart: the Sky Jet, deep red with gold, a needle nose, delta wings for sidepods, a tall
 * tail fin and twin burners.
 */
import * as THREE from "three";
import { buildEyes, type RiderRig } from "../../kit/rig";
import { Build, card, cyl, ellipsoid, loft, tube } from "../../kit/shapes";
import { skinMaterial } from "../../kit/paint";
import { goggles } from "../../kit/props";
import { sleekKart } from "../../kit/sleek";
import { ZEPHYR } from "../zephyr";
import type { RacerBuild } from "../types";
import { clearHead } from "./common";

type P = typeof ZEPHYR.palettes.main;

const LEATHER = "#7a4a26";
const LEATHER_DARK = "#5a3418";
const BRASS = "#e8b440";

function head(rig: RiderRig, c: P) {
  clearHead(rig);
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.2, 0.03);
  head.rotation.x = -0.06;
  head.scale.setScalar(1.32);
  const beak = new THREE.Color(c.beak);
  const beakTip = new THREE.Color(c.beakTip);

  // A compact cranium and a long, sharp beak.
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.15], rx: 0.08, ry: 0.09 },
        { at: [0, 0.11, -0.1], rx: 0.155, ry: 0.155 },
        { at: [0, 0.11, -0.0], rx: 0.18, ry: 0.17 },
        { at: [0, 0.085, 0.09], rx: 0.15, ry: 0.13, flat: 0.3 },
        { at: [0, 0.05, 0.17], rx: 0.095, ry: 0.08, flat: 0.5 },
        { at: [0, 0.035, 0.32], rx: 0.06, ry: 0.05, flat: 0.5 },
        { at: [0, 0.02, 0.48], rx: 0.026, ry: 0.022, flat: 0.4 },
        { at: [0, 0.01, 0.56], rx: 0.005, ry: 0.005 },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) =>
          t > 0.45
            ? beak.clone().lerp(beakTip, Math.max(0, (t - 0.72) * 3.5))
            : a < -1.0 && t > 0.3
              ? c.cream
              : c.skin,
      },
    ),
  );
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.0, 0.18], s: [0.08, 0.03, 0.18] });
  for (const s of [1, -1])
    skull.add(ellipsoid(5, 4), c.beakTip, { p: [s * 0.033, 0.065, 0.32], s: [0.012, 0.008, 0.02] });
  // The smirk: the beak line curls up on the left side only.
  skull.addColored(
    tube(
      [
        [0.04, 0.012, 0.3],
        [0.075, 0.012, 0.18],
        [0.12, 0.03, 0.1],
        [0.13, 0.065, 0.075],
      ],
      [0.011, 0.013, 0.013, 0.009],
      "#5a1a10",
      { sides: 5 },
    ),
  );
  skull.addColored(
    tube(
      [
        [-0.04, 0.012, 0.3],
        [-0.075, 0.01, 0.18],
        [-0.12, 0.005, 0.1],
      ],
      [0.011, 0.012, 0.009],
      "#5a1a10",
      { sides: 5 },
    ),
  );

  // The flying helmet: a leather cap over the back of the cranium, a stitched ridge,
  // ear flaps and a chin strap.
  skull.addColored(
    loft(
      [
        { at: [0, 0.11, -0.17], rx: 0.09, ry: 0.1, color: LEATHER },
        { at: [0, 0.13, -0.11], rx: 0.17, ry: 0.17, color: LEATHER },
        { at: [0, 0.14, -0.02], rx: 0.192, ry: 0.18, color: LEATHER },
        { at: [0, 0.15, 0.05], rx: 0.18, ry: 0.16, color: LEATHER, flat: 0.55 },
        { at: [0, 0.17, 0.08], rx: 0.15, ry: 0.11, color: LEATHER_DARK, flat: 0.7 },
      ],
      { sides: 14, steps: 2, capStart: true },
    ),
  );
  skull.addColored(
    tube(
      [
        [0, 0.33, 0.06],
        [0, 0.32, -0.04],
        [0, 0.27, -0.12],
      ],
      0.012,
      LEATHER_DARK,
      { sides: 5 },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(ellipsoid(10, 6), LEATHER, { p: [s * 0.17, 0.06, -0.04], s: [0.04, 0.09, 0.075], r: [0.2, 0, 0] });
    skull.add(cyl(0.022, 0.022, 0.012, 8), BRASS, { p: [s * 0.21, 0.04, -0.04], r: [0, 0, Math.PI / 2] });
  }
  skull.addColored(
    tube(
      [
        [0.2, 0.02, -0.03],
        [0.14, -0.09, 0.02],
        [0, -0.12, 0.04],
        [-0.14, -0.09, 0.02],
        [-0.2, 0.02, -0.03],
      ],
      0.013,
      LEATHER_DARK,
      { sides: 5 },
    ),
  );
  // Goggles pushed up on the helmet: brass frames, sky-blue lenses.
  skull.addColored(goggles({ frame: BRASS, lens: c.gogLens, glint: "#ffffff" }, 0.08, 0.058), {
    p: [0, 0.29, 0.1],
    r: [-0.75, 0, 0],
  });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The crest: a long, sharp blade out of the back of the helmet, a pale leading edge.
  const crest = new THREE.Group();
  crest.position.set(0, 0.22, -0.1);
  head.add(crest);
  const ctop = new THREE.Color(c.crest);
  const ctip = new THREE.Color(c.crestTip);
  crest.add(
    new THREE.Mesh(
      new Build()
        .add(
          card(
            [
              [0.08, -0.08],
              [0.04, 0.06],
              [-0.3, 0.2],
              [-0.8, 0.3],
              [-0.5, 0.1],
              [-0.12, -0.06],
            ],
            0.06,
          ),
          (p) => {
            const k = ctop.clone().lerp(ctip, Math.min(1, Math.max(0, -p.x * 1.6)));
            // The pale leading (top) edge.
            const edge = 0.06 + (-p.x) * 0.3;
            if (p.y > edge - 0.035 && p.x < 0.0) k.lerp(new THREE.Color(c.cream), 0.75);
            return k;
          },
          { r: [0, -Math.PI / 2, 0] },
        )
        .build(),
      mat,
    ),
  );

  const jaw = new THREE.Group();
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, 0.0, -0.02], rx: 0.11, ry: 0.05 },
              { at: [0, -0.02, 0.12], rx: 0.085, ry: 0.04, flat: -0.4 },
              { at: [0, -0.015, 0.32], rx: 0.05, ry: 0.028, flat: -0.4 },
              { at: [0, -0.005, 0.46], rx: 0.015, ry: 0.01 },
            ],
            {
              sides: 10,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (_t, a) => (a > 0.5 && a < 2.6 ? c.mouth : c.beak),
            },
          ),
        )
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.006, 0.14], s: [0.05, 0.018, 0.1] })
        .build(),
      mat,
    ),
  );

  // A cool, half-lidded side glance; one brow cocked.
  const eyes = buildEyes(head, {
    at: [0.098, 0.145, 0.07],
    size: [0.076, 0.088, 0.066],
    yaw: 0.42,
    iris: "#3a2210",
    irisRing: "#e0902a",
    lid: c.skin,
    inward: 0,
    gaze: [0.22, 0.02],
    lidTilt: 0.12,
    brow: { color: LEATHER_DARK, at: [0.1, 0.228, 0.095], size: [0.06, 0.02, 0.026], tilt: 0.25 },
  });
  // The cocked brow: the right one high and arched, its eye a little wider.
  const right = eyes.eyes.find((e) => e.side === -1)!;
  const rb = eyes.brows[1]!;
  rb.position.y += 0.035;
  rb.rotation.z = 0.35;
  (right.lid.parent as THREE.Object3D).rotation.z = -0.1;
  right.group.scale.setScalar(1.06);

  rig.face = { ...eyes, jaw, jawOpen: 0.4 };
  rig.wiggles.push({ obj: crest, kind: "crest", side: 0, amount: 0.8 });
  Object.assign(rig.personality, { restJaw: 0.04, restBrow: 0.0, restLids: 0.2 });
}

function rider(c: P): RiderRig {
  const rig = ZEPHYR.rider(c);
  head(rig, c);
  return rig;
}

export const ZEPHYR_V2: RacerBuild<P> = {
  palettes: ZEPHYR.palettes,
  rider,
  kart: (c) =>
    sleekKart({
      main: c.red,
      dark: c.redDark,
      stripe: c.gold,
      nose: c.red,
      trim: c.sand,
      metal: "#3a3436",
      seat: c.seat,
      glass: "#9ad8f6",
      tyre: c.tyre,
      rim: c.gold,
      cap: c.orange,
      tyreLine: c.gold,
      front: "needle",
      pods: "delta",
      rear: "jet",
      spokes: 5,
      emblem: { kind: "wing", disc: c.sand, ink: c.red, rim: c.gold },
    }),
};
