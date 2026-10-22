/**
 * Zephyr the pteranodon: the Sky Scout (design A), the hotshot ace.
 *
 * Silhouette: the most aerodynamic of the four: a long needle beak forward, the crest a
 * long sharp blade with a pale leading edge, and orange wings folded at the sides that
 * spread in the air and flap to celebrate.
 * Face: a leather flying helmet with brass goggles pushed up on it; a half-lidded side
 * glance, one brow cocked high and a lopsided smirk. Golden-yellow face and neck, pale
 * cream underside. Gear: the helmet and a red-orange scarf.
 * Kart: the Sky Jet (the sleek family): deep red with gold, a needle nose, delta wings for
 * sidepods, a tall tail fin, twin burners and a wing emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, card, cone, cyl, ellipsoid, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { goggles } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#f5b52e",
  skinDark: "#d8901e",
  cream: "#f8e6bc",
  beak: "#f7cf5a",
  beakTip: "#e09a2a",
  crest: "#e2482a",
  crestTip: "#b8302a",
  wing: "#f58a2c",
  wingDark: "#c4502a",
  wingBone: "#c45a26",
  scarf: "#e04428",
  gogFrame: "#6a4426",
  gogLens: "#5cb6e6",
  eye: "#1e140e",
  mouth: "#9a3030",
  tongue: "#f07a80",
  glove: "#33261f",
  // The kart.
  red: "#b83226",
  redDark: "#8a2420",
  orange: "#e0672a",
  sand: "#efdcb2",
  gold: "#f5c040",
  charcoal: "#2e2a2c",
  seat: "#4a2a22",
  tyre: "#272325",
};

/** The alternate look: Zephyr as a blue wind racer. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#5d8fe0",
  skinDark: "#3f6cc0",
  crest: "#2f5fc8",
  crestTip: "#f2f6ff",
  wing: "#6aa4f0",
  wingDark: "#2f56a8",
  wingBone: "#3f6cc0",
  red: "#2f5fc8",
  redDark: "#22468f",
  orange: "#e04428",
};

type P = typeof MAIN;

const LEATHER = "#7a4a26";
const LEATHER_DARK = "#5a3418";
const BRASS = "#e8b440";

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
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
  });
}

// ------------------------------------------------------------------ Zephyr

function wingGeometry(c: P) {
  // The membrane, lying flat (XZ plane) and reaching out along +X: leading edge in front,
  // a long tip swept back, a scalloped trailing edge.
  const outline: [number, number][] = [
    [0, 0.06],
    [0.32, 0.07],
    [0.58, 0.02],
    [0.82, -0.2],
    [0.52, -0.16],
    [0.4, -0.24],
    [0.22, -0.2],
    [0.08, -0.26],
    [0, -0.18],
  ];
  const wing = new THREE.Color(c.wing);
  const dark = new THREE.Color(c.wingDark);
  const b = new Build().add(card(outline), (p) =>
    wing.clone().lerp(dark, Math.min(1, Math.max(0, -p.y * 3.2 + p.x * 0.4))),
  );
  // The leading-edge "arm" bone, darker.
  b.addColored(
    loft(
      [
        { at: [0, 0.06, 0], rx: 0.03, ry: 0.03, color: c.wingBone },
        { at: [0.32, 0.07, 0], rx: 0.025, ry: 0.025, color: c.wingBone },
        { at: [0.58, 0.02, 0], rx: 0.02, ry: 0.02, color: c.wingBone },
        { at: [0.8, -0.19, 0], rx: 0.008, ry: 0.008, color: c.wingBone },
      ],
      { sides: 5, capStart: true, capEnd: true, up: [0, 0, 1] },
    ),
  );
  return b.build().rotateX(-Math.PI / 2);
}

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "zephyr";
  const torso = new THREE.Group();
  root.add(torso);

  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.01], rx: 0.17, ry: 0.15 },
        { at: [0, 0.12, 0.0], rx: 0.2, ry: 0.17 },
        { at: [0, 0.27, 0.01], rx: 0.18, ry: 0.15 },
        { at: [0, 0.38, 0.02], rx: 0.12, ry: 0.11 },
        { at: [0, 0.44, 0.02], rx: 0.09, ry: 0.09 },
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
  torso.add(new THREE.Mesh(body.build(), mat));

  // The scarf: a band round the neck and two tails streaming back.
  const scarf = new THREE.Group();
  scarf.position.set(0, 0.42, 0.0);
  torso.add(scarf);
  scarf.add(
    new THREE.Mesh(
      new Build()
        .add(new THREE.TorusGeometry(0.1, 0.04, 5, 12), c.scarf, { r: [Math.PI / 2, 0, 0] })
        .add(ellipsoid(6, 4), c.scarf, { p: [0.04, 0.0, -0.1], s: [0.05, 0.045, 0.04] })
        .build(),
      mat,
    ),
  );
  const tails = new THREE.Group();
  tails.position.set(0.04, 0.0, -0.1);
  scarf.add(tails);
  tails.add(
    new THREE.Mesh(
      new Build()
        .add(
          card([
            [-0.035, 0],
            [0.035, 0],
            [0.03, -0.24],
            [0.0, -0.28],
            [-0.03, -0.24],
          ]),
          c.scarf,
          { r: [-1.3, 0, 0.2] },
        )
        .add(
          card([
            [-0.03, 0],
            [0.03, 0],
            [0.025, -0.2],
            [0.0, -0.23],
            [-0.025, -0.2],
          ]),
          c.scarf,
          { p: [0.04, 0, 0], r: [-1.1, 0, 0.5] },
        )
        .build(),
      mat,
    ),
  );

  // Neck: short and strong.
  const neck = new THREE.Group();
  neck.position.set(0, 0.38, 0.0);
  neck.rotation.x = 0.1;
  torso.add(neck);
  neck.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.02, 0], rx: 0.1, ry: 0.1 },
              { at: [0, 0.1, 0.01], rx: 0.085, ry: 0.085 },
              { at: [0, 0.2, 0.02], rx: 0.09, ry: 0.09 },
            ],
            {
              sides: 10,
              steps: 2,
              up: [0, 0, 1],
              paint: (_t, a) => (Math.abs(a - Math.PI / 2) < 0.7 ? c.cream : c.skin),
            },
          ),
        )
        .build(),
      mat,
    ),
  );

  // The head: built by buildHead() below, once the rig exists.
  const head = new THREE.Group();
  neck.add(head);

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.15, 0.34, 0.07],
    upper: 0.19,
    fore: 0.18,
    radius: [0.05, 0.042, 0.038],
    color: c.skin,
    hand: c.glove,
    handSize: 0.06,
    hint: [0.8, -0.5, -0.3],
  });

  // Wings: folded along the sides (tips back and up), spread out in the air.
  const wings: THREE.Object3D[] = [];
  const wingGeo = wingGeometry(c);
  for (const side of [1, -1]) {
    const w = new THREE.Group();
    w.position.set(side * 0.13, 0.36, -0.1);
    const m = new THREE.Mesh(side === 1 ? wingGeo : mirrored(wingGeo), mat);
    w.add(m);
    w.userData.fold = new THREE.Euler(0.15, side * 1.15, side * 0.62);
    w.userData.open = new THREE.Euler(-0.5, side * 0.15, side * 0.42);
    w.rotation.copy(w.userData.fold as THREE.Euler);
    torso.add(w);
    wings.push(w);
  }

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.18, 0], s: [0.18, 0.24, 0.16] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.82, 0.1], s: [0.2, 0.19, 0.22] })
      .add(cone(0.08, 0.5, 4), c.beak, { p: [0, 0.78, 0.45], r: [Math.PI / 2, 0, 0] })
      .add(cone(0.07, 0.5, 4), c.crest, { p: [0, 1.02, -0.3], r: [-1.3, 0, 0] })
      .add(box(0.7, 0.04, 0.3, 0), c.wing, { p: [0, 0.48, -0.25], r: [0.4, 0, 0] })
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
    tail: [],
    wings,
    wiggles: [{ obj: tails, kind: "flutter", side: 1, amount: 1.2 }],
    low,
    cheer: [new THREE.Vector3(0.38, 0.66, 0.12), new THREE.Vector3(-0.38, 0.66, 0.12)],
    personality: {
      lean: 1.3,
      headTurn: 1.25,
      curiosity: 0.6,
      glanceEvery: 3,
      blinkEvery: 3.2,
      blinkTime: 0.12,
      bob: 0.03,
      bobHz: 2.6,
      steerHands: 1.2,
      boostKick: 1.1,
      boostFace: 1,
      grumble: 0.3,
      response: 1.2,
      restJaw: 0.04,
      restBrow: 0.0,
      restLids: 0.2,
      victory: "flap",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
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
    skull.add(ellipsoid(10, 6), LEATHER, {
      p: [s * 0.17, 0.06, -0.04],
      s: [0.04, 0.09, 0.075],
      r: [0.2, 0, 0],
    });
    skull.add(cyl(0.022, 0.022, 0.012, 8), BRASS, {
      p: [s * 0.21, 0.04, -0.04],
      r: [0, 0, Math.PI / 2],
    });
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
              [-0.72, 0.29],
              [-0.5, 0.1],
              [-0.12, -0.06],
            ],
            0.06,
          ),
          (p) => {
            const k = ctop.clone().lerp(ctip, Math.min(1, Math.max(0, -p.x * 1.6)));
            // The pale leading (top) edge.
            const edge = 0.06 + -p.x * 0.3;
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
}

/** The same shape mirrored across X (the other wing), faces kept outward. */
function mirrored(geo: THREE.BufferGeometry) {
  return new Build().addColored(geo.clone(), { mirror: true }).build();
}

export const ZEPHYR: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
