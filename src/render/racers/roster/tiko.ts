/**
 * Tiko the parasaurolophus: the Tropical Explorer (design F), our mascot, made a hero.
 *
 * Silhouette: the crest, a bold swoosh of gold into flame orange with two dark bands,
 * readable from anywhere; a slender neck and a long tail over the back of the kart.
 * Face: a big round cranium, a short broad duck-bill with a confident grin, tall
 * front-set green eyes under a determined lid and bold brows.
 * Turquoise skin with a lighter belly and small orange accents down the neck and back.
 * Gear: an orange neckerchief, a brown backpack with a bedroll and tucked-in leaves.
 * Kart: the Jungle GT (the sleek family): teal and ivory with an orange stripe, a blade
 * front wing, a raised rear wing with leaves behind its endplates, a palm emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, cone, cyl, ellipsoid, gem, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { backpack, bedroll, leaf, strap } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#33c3c9",
  skinDark: "#1f949e",
  belly: "#b6f0e4",
  crestBase: "#ffd43a",
  crestTip: "#f26419",
  accent: "#f5891f",
  kerchief: "#ea5a2a",
  eye: "#2b1a12",
  mouth: "#9a2b3a",
  tongue: "#f0788a",
  glove: "#3b2b26",
  pack: "#8c5a32",
  packDark: "#6b4224",
  buckle: "#e8c25a",
  roll: "#dcb67c",
  strap: "#5a3a22",
  leaf: "#3fae4a",
  leafRib: "#a4dd6a",
  // The kart.
  kart: "#2ab4c2",
  kartDark: "#1d8794",
  ivory: "#f6ead0",
  trim: "#f39a2b",
  gold: "#ffcf3f",
  wood: "#c48a52",
  woodDark: "#8e5d34",
  seat: "#5b3a2a",
  tyre: "#2a2226",
  emblem: "#3d9a3a",
};

/** The alternate look (a repeated rival): Tiko's sporty orange-and-teal take. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#4fb6e8",
  skinDark: "#2e86b8",
  belly: "#d2f0ff",
  kerchief: "#2f6fd1",
  kart: "#f39a2b",
  kartDark: "#c9711a",
  trim: "#2ab4c2",
  emblem: "#d9541f",
};

type P = typeof MAIN;

const IRIS = "#2f8a3e";
const IRIS_RING = "#7fd35a";

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
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
        b.addColored(leaf(0.4, 0.12, c.leaf, c.leafRib), {
          p: [s * 0.62, 0.98, -1.3],
          r: [-1.9, s * 0.25, s * 0.35],
        });
    },
  });
}

// ------------------------------------------------------------------ Tiko

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "tiko";
  const torso = new THREE.Group();
  root.add(torso);

  // A small, agile torso with a pale belly, and small orange spines down the back.
  const body = new Build();
  body.addColored(
    loft(
      [
        { at: [0, -0.04, -0.01], rx: 0.17, ry: 0.15 },
        { at: [0, 0.1, 0.0], rx: 0.2, ry: 0.18 },
        { at: [0, 0.24, 0.01], rx: 0.18, ry: 0.16 },
        { at: [0, 0.36, 0.02], rx: 0.13, ry: 0.12 },
        { at: [0, 0.42, 0.02], rx: 0.1, ry: 0.1 },
      ],
      {
        sides: 12,
        steps: 2,
        up: [0, 0, 1],
        capStart: true,
        paint: (_t, a) => (Math.abs(a - Math.PI / 2) < 0.75 ? c.belly : c.skin),
      },
    ),
  );
  // The neckerchief: a knotted band and a triangle hanging down the chest.
  body.add(new THREE.TorusGeometry(0.105, 0.035, 5, 12), c.kerchief, {
    p: [0, 0.4, 0.02],
    r: [Math.PI / 2 + 0.15, 0, 0],
  });
  body.add(gem(1), c.kerchief, { p: [0, 0.38, 0.13], s: [0.05, 0.045, 0.04] });
  // Backpack straps over the shoulders.
  for (const s of [1, -1])
    body.addColored(
      strap(
        [
          [s * 0.1, 0.06, 0.15],
          [s * 0.13, 0.25, 0.15],
          [s * 0.12, 0.38, 0.05],
          [s * 0.1, 0.36, -0.12],
        ],
        0.02,
        0.008,
        c.strap,
      ),
    );
  torso.add(new THREE.Mesh(body.build(), mat));

  // The kerchief's point flutters a little.
  const kerchief = new THREE.Mesh(
    new Build()
      .add(cone(0.07, 0.13, 3), c.kerchief, { r: [Math.PI, 0, 0], s: [1, 1, 0.35] })
      .build(),
    mat,
  );
  kerchief.position.set(0, 0.32, 0.15);
  kerchief.rotation.x = -0.25;
  torso.add(kerchief);

  // Backpack, bedroll and tucked-in leaves.
  const pack = new THREE.Group();
  pack.position.set(0, 0.3, -0.21);
  const packB = new Build()
    .addColored(backpack(0.26, 0.28, 0.13, { bag: c.pack, flap: c.packDark, buckle: c.buckle }))
    .addColored(bedroll(0.34, 0.06, { roll: c.roll, strap: c.strap }), { p: [0, 0.18, -0.02] })
    .addColored(leaf(0.22, 0.06, c.leaf, c.leafRib), { p: [0.1, 0.1, -0.04], r: [-0.3, 0.3, -0.5] })
    .addColored(leaf(0.18, 0.05, c.leaf, c.leafRib), {
      p: [0.12, 0.08, -0.02],
      r: [-0.2, 0.6, -1.0],
    });
  pack.add(new THREE.Mesh(packB.build(), mat));
  torso.add(pack);

  // Neck: slender, rising and leaning forward a little, with orange spines.
  const neck = new THREE.Group();
  neck.position.set(0, 0.38, 0.0);
  neck.rotation.x = 0.12;
  torso.add(neck);
  const neckB = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, 0], rx: 0.11, ry: 0.105 },
        { at: [0, 0.12, 0.02], rx: 0.088, ry: 0.088 },
        { at: [0, 0.26, 0.04], rx: 0.085, ry: 0.085 },
        { at: [0, 0.34, 0.04], rx: 0.09, ry: 0.09 },
      ],
      {
        sides: 10,
        steps: 2,
        up: [0, 0, 1],
        paint: (_t, a) => (Math.abs(a - Math.PI / 2) < 0.7 ? c.belly : c.skin),
      },
    ),
  );
  for (let k = 0; k < 4; k++)
    neckB.add(cone(0.032, 0.07, 4), c.accent, {
      p: [0, 0.04 + k * 0.08, -0.08],
      r: [-1.2, 0, 0],
      s: [0.6, 1, 1],
    });
  neck.add(new THREE.Mesh(neckB.build(), mat));
  // Spines down the back, between pack and neck.
  const spines = new Build();
  for (let k = 0; k < 2; k++)
    spines.add(cone(0.03, 0.06, 4), c.accent, {
      p: [0, 0.36 - k * 0.05, -0.1 - k * 0.02],
      r: [-1.5, 0, 0],
      s: [0.6, 1, 1],
    });
  torso.add(new THREE.Mesh(spines.build(), mat));

  // The head: built by buildHead() below, once the rig exists.
  const head = new THREE.Group();
  neck.add(head);

  // Arms and gloves.
  const { arms, hands } = buildArms(torso, {
    shoulder: [0.155, 0.33, 0.07],
    upper: 0.19,
    fore: 0.18,
    radius: [0.055, 0.045, 0.04],
    color: c.skin,
    hand: c.glove,
    handSize: 0.06,
    hint: [0.8, -0.5, -0.3],
  });

  // The tail: three joints trailing back over the kart, thinning to a point.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.12, 0.28, 0.095],
    [0.095, 0.28, 0.07],
    [0.07, 0.3, 0.025],
  ];
  // Out of the seat, up over the back deck, then gently down and up at the tip.
  const lift = [0.5, -0.38, 0.12];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.1, -0.14);
    else j.position.set(0, 0, -segs[k - 1]![1]);
    j.rotation.x = lift[k]!;
    parent.add(j);
    j.add(
      new THREE.Mesh(
        new Build()
          .addColored(
            loft(
              [
                { at: [0, 0, r0 * 0.5], rx: r0 * 0.7, ry: r0 * 0.7 },
                { at: [0, 0, 0], rx: r0, ry: r0 },
                { at: [0, 0, -len], rx: r1, ry: r1 },
                ...(k === 2
                  ? []
                  : [
                      {
                        at: [0, 0, -len - r1 * 0.6] as [number, number, number],
                        rx: r1 * 0.6,
                        ry: r1 * 0.6,
                      },
                    ]),
              ],
              {
                sides: 9,
                capStart: true,
                capEnd: true,
                paint: (_t, a) => (a < -1.0 ? c.belly : c.skin),
              },
            ),
          )
          .add(cone(0.026, 0.06, 4), c.accent, {
            p: [0, r0 * 0.85, -len * 0.4],
            r: [-1.3, 0, 0],
            s: [0.6, 1, 1],
          })
          .build(),
        mat,
      ),
    );
    tail.push(j);
    parent = j;
  });

  // Far away: one rough mesh (body, neck, head, crest, tail).
  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.18, 0], s: [0.19, 0.24, 0.17] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.82, 0.12], s: [0.19, 0.17, 0.27] })
      .add(cyl(0.08, 0.1, 0.4, 5), c.skin, { p: [0, 0.55, 0.04] })
      .add(
        tube(
          [
            [0, 0.98, 0.04],
            [0, 1.08, -0.15],
            [0, 1.15, -0.45],
          ],
          [0.08, 0.09, 0.05],
          c.crestTip,
          { sides: 5 },
        ),
        c.crestTip,
      )
      .add(box(0.24, 0.3, 0.14, 0.04), c.pack, { p: [0, 0.26, -0.2] })
      .add(
        tube(
          [
            [0, 0.03, -0.12],
            [0, 0.0, -0.45],
            [0, 0.0, -0.75],
          ],
          [0.11, 0.08, 0.03],
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
    wiggles: [
      { obj: kerchief, kind: "flutter", side: 0, amount: 0.6 },
      { obj: pack, kind: "bounce", side: 0, amount: 1 },
    ],
    low,
    cheer: [new THREE.Vector3(0.42, 0.64, 0.12), new THREE.Vector3(-0.42, 0.64, 0.12)],
    personality: {
      lean: 1.35,
      headTurn: 1.1,
      curiosity: 1,
      glanceEvery: 3.5,
      blinkEvery: 3,
      blinkTime: 0.14,
      bob: 0.03,
      bobHz: 2.3,
      steerHands: 1.25,
      boostKick: 1.1,
      boostFace: 1,
      grumble: 0.2,
      response: 1.15,
      restJaw: 0.08,
      restBrow: 0.05,
      restLids: 0.14,
      victory: "cheer",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
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
              { at: [0, 0.33, -0.43], rx: 0.115, ry: 0.11 },
              { at: [0, 0.35, -0.58], rx: 0.085, ry: 0.08 },
              { at: [0, 0.33, -0.7], rx: 0.04, ry: 0.045 },
              { at: [0, 0.3, -0.78], rx: 0.008, ry: 0.008 },
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
}

export const TIKO: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
