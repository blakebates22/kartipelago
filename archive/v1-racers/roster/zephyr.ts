/**
 * Zephyr the pteranodon: the Sky Scout (design A).
 *
 * Silhouette: the most aerodynamic of the four: a long pointed beak forward, a swept-back
 * orange-red crest behind, and orange wings folded at the sides that spread in the air
 * and flap to celebrate. Golden-yellow face and neck, pale cream underside, big eyes.
 * Gear: brown aviator goggles up on the forehead and a red-orange scarf.
 * Kart: an aviation-inspired racer (still a kart): a pointed deep-red nose with a wing
 * emblem on the hood, burnt-orange fenders, cream panels, rivets, and a rounded engine
 * with twin exhausts at the back.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, card, cone, cyl, ellipsoid, loft, taper } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { emblemMesh, goggles } from "../kit/props";
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

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return {
    wheel: { tyre: c.tyre, rim: c.orange, cap: c.gold, ring: c.gold, sides: 10 },
    steering: c.charcoal,
    shell(b, detail) {
      b.add(box(0.96, 0.14, 2.2, 0.05), c.charcoal, { p: [0, 0.28, -0.05] });
      // A sleek tub that narrows into a pointed nose; an orange stripe down each side.
      b.addColored(
        loft(
          [
            { at: [0, 0.5, -1.0], rx: 0.42, ry: 0.15 },
            { at: [0, 0.51, -0.72], rx: 0.52, ry: 0.2 },
            { at: [0, 0.5, -0.2], rx: 0.53, ry: 0.2 },
            { at: [0, 0.48, 0.4], rx: 0.46, ry: 0.19 },
            { at: [0, 0.44, 0.9], rx: 0.33, ry: 0.16 },
            { at: [0, 0.4, 1.25], rx: 0.17, ry: 0.1 },
            { at: [0, 0.37, 1.42], rx: 0.04, ry: 0.035 },
          ],
          {
            sides: 12,
            steps: 2,
            capStart: true,
            capEnd: true,
            paint: (t, a) => {
              if (Math.abs(a) < 0.22 || Math.abs(Math.abs(a) - Math.PI) < 0.22) return c.orange;
              if (a > 0.9 && a < 2.25 && t > 0.62) return c.sand; // the hood
              return a > 0 ? c.red : c.redDark;
            },
          },
        ),
      );
      // Cream intake lip under the nose, gold trim round the cockpit.
      b.add(taper(box(0.5, 0.1, 0.4, 0.04), 0.5, 0.8), c.sand, { p: [0, 0.3, 1.16] });
      b.add(new THREE.TorusGeometry(0.34, 0.045, 4, 14), c.gold, {
        p: [0, 0.69, -0.26],
        r: [Math.PI / 2, 0, 0],
        s: [1, 1.2, 1],
      });
      // A little dashboard dial.
      b.add(cyl(0.06, 0.06, 0.03, 10), c.sand, { p: [0.18, 0.73, 0.14], r: [1.1, 0, 0] });
      b.add(box(0.5, 0.1, 0.42, 0.04), c.seat, { p: [0, 0.48, -0.3] });
      b.add(box(0.5, 0.26, 0.1, 0.04), c.seat, { p: [0, 0.66, -0.56], r: [-0.15, 0, 0] });
      for (const s of [1, -1]) {
        // Swept fenders, and rivets down the sides.
        b.add(taper(box(0.44, 0.22, 0.76, 0.1), 0.85, 0.6, 0.06), c.orange, {
          p: [s * 0.76, 0.74, 0.88],
        });
        b.add(taper(box(0.5, 0.28, 0.84, 0.11), 0.92, 0.8, 0.04), c.red, {
          p: [s * 0.8, 0.72, -0.78],
        });
        for (let k = 0; k < 5; k++)
          b.add(cyl(0.018, 0.018, 0.02, 5), c.gold, {
            p: [s * 0.545, 0.56, -0.5 + k * 0.22],
            r: [0, 0, Math.PI / 2],
          });
        b.add(box(0.2, 0.16, 0.8, 0.05), c.charcoal, { p: [s * 0.6, 0.36, 0.05] });
      }
      // The rounded engine behind the seat, with twin exhausts and gold bands.
      b.add(ellipsoid(12, 8), c.charcoal, { p: [0, 0.68, -0.92], s: [0.3, 0.2, 0.26] });
      b.add(cyl(0.2, 0.2, 0.05, 12), c.gold, {
        p: [0, 0.68, -0.92],
        r: [Math.PI / 2, 0, 0],
        s: [1.45, 1, 1],
      });
      for (const s of [1, -1]) {
        b.add(cyl(0.08, 0.1, 0.42, 9), c.charcoal, {
          p: [s * 0.2, 0.46, -1.16],
          r: [Math.PI / 2, 0, 0],
        });
        b.add(cyl(0.1, 0.1, 0.05, 9), c.gold, {
          p: [s * 0.2, 0.46, -1.37],
          r: [Math.PI / 2, 0, 0],
        });
      }
      if (detail === 0)
        b.add(cyl(0.07, 0.07, 0.04, 9), "#141012", { p: [0, 0.42, -1.33], r: [Math.PI / 2, 0, 0] });
    },
    decorate(body) {
      // The wing emblem on the cream hood.
      const e = emblemMesh("wing", { disc: c.sand, ink: c.red, rim: c.gold }, 0.3);
      e.position.set(0, 0.565, 1.02);
      e.rotation.x = -1.22;
      body.add(e);
    },
  };
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

  const head = new THREE.Group();
  head.position.set(0, 0.2, 0.03);
  head.rotation.x = -0.08;
  head.scale.setScalar(1.3);
  neck.add(head);
  const beak = new THREE.Color(c.beak);
  const beakTip = new THREE.Color(c.beakTip);
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.15], rx: 0.08, ry: 0.09 },
        { at: [0, 0.11, -0.1], rx: 0.15, ry: 0.15 },
        { at: [0, 0.11, -0.01], rx: 0.18, ry: 0.17 },
        { at: [0, 0.09, 0.08], rx: 0.15, ry: 0.14, flat: 0.3 },
        { at: [0, 0.05, 0.16], rx: 0.1, ry: 0.085, flat: 0.5 },
        { at: [0, 0.035, 0.3], rx: 0.065, ry: 0.055, flat: 0.5 },
        { at: [0, 0.02, 0.44], rx: 0.03, ry: 0.025, flat: 0.4 },
        { at: [0, 0.01, 0.5], rx: 0.006, ry: 0.006 },
      ],
      {
        sides: 12,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) =>
          t > 0.45
            ? beak.clone().lerp(beakTip, Math.max(0, (t - 0.75) * 4))
            : a < -1.0 && t > 0.3
              ? c.cream
              : c.skin,
      },
    ),
  );
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.0, 0.18], s: [0.08, 0.03, 0.18] });
  for (const s of [1, -1])
    skull.add(ellipsoid(5, 4), c.beakTip, { p: [s * 0.035, 0.07, 0.3], s: [0.012, 0.008, 0.02] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The crest: a long blade swept back from the top of the head.
  const crest = new THREE.Group();
  crest.position.set(0, 0.2, -0.06);
  head.add(crest);
  const ctop = new THREE.Color(c.crest);
  const ctip = new THREE.Color(c.crestTip);
  crest.add(
    new THREE.Mesh(
      new Build()
        .add(
          card(
            [
              [0.12, -0.06],
              [0.02, 0.1],
              [-0.26, 0.22],
              [-0.62, 0.27],
              [-0.4, 0.1],
              [-0.14, -0.03],
            ],
            0.07,
          ),
          (p) => ctop.clone().lerp(ctip, Math.min(1, Math.max(0, -p.x * 2))),
          { r: [0, -Math.PI / 2, 0] },
        )
        .build(),
      mat,
    ),
  );

  // Aviator goggles up on the forehead, on a band round the head.
  const gog = new Build()
    .addColored(goggles({ frame: c.gogFrame, lens: c.gogLens, glint: "#ffffff" }, 0.075, 0.052), {
      p: [0, 0.255, 0.1],
      r: [-0.55, 0, 0],
    })
    .add(new THREE.TorusGeometry(0.17, 0.018, 4, 14), c.gogFrame, {
      p: [0, 0.2, -0.01],
      r: [Math.PI / 2 + 0.55, 0, 0],
      s: [1.05, 1.1, 1],
    });
  head.add(new THREE.Mesh(gog.build(), mat));

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
              { at: [0, -0.015, 0.3], rx: 0.055, ry: 0.03, flat: -0.4 },
              { at: [0, -0.005, 0.42], rx: 0.02, ry: 0.012 },
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

  const eyes = buildEyes(head, {
    at: [0.1, 0.14, 0.06],
    size: [0.078, 0.09, 0.068],
    yaw: 0.45,
    iris: c.eye,
    lid: c.skin,
    inward: 0.2,
    brow: { color: c.skinDark, at: [0.1, 0.225, 0.08], size: [0.05, 0.014, 0.02], tilt: -0.2 },
  });

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

  return {
    root,
    torso,
    neck,
    head,
    face: { ...eyes, jaw, jawOpen: 0.4 },
    arms,
    hands,
    tail: [],
    wings,
    wiggles: [
      { obj: crest, kind: "crest", side: 0, amount: 0.8 },
      { obj: tails, kind: "flutter", side: 1, amount: 1.2 },
    ],
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
      restJaw: 0.3,
      restBrow: 0.3,
      restLids: 0,
      victory: "flap",
    },
  };
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
