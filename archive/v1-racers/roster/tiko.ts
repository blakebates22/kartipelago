/**
 * Tiko the parasaurolophus: the Tropical Explorer (design F), our mascot.
 *
 * Silhouette: the big backward-curving crest (gold into orange), readable from behind
 * and from the race camera; a slender neck and a long tail over the back of the kart.
 * Turquoise skin with a lighter belly and small orange accents down the neck and back.
 * Gear: an orange neckerchief, a brown backpack with a bedroll and tucked-in leaves.
 * Kart: a rounded tropical explorer, turquoise and ivory with orange trim, a palm emblem
 * on the nose, wooden side slats, leaves at the back and explorer gear behind the seat.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, cone, cyl, ellipsoid, gem, loft, taper, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { backpack, bedroll, emblemMesh, leaf, strap } from "../kit/props";
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

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return {
    wheel: { tyre: c.tyre, rim: c.trim, cap: c.gold, ring: c.gold, sides: 10 },
    steering: "#3b2f2a",
    shell(b, detail) {
      // Floor tray.
      b.add(box(0.98, 0.14, 2.2, 0.05), c.kartDark, { p: [0, 0.28, -0.05] });
      // The rounded tub: turquoise on top, darker below, an orange band behind the nose.
      b.addColored(
        loft(
          [
            { at: [0, 0.5, -1.02], rx: 0.42, ry: 0.13 },
            { at: [0, 0.51, -0.78], rx: 0.52, ry: 0.19 },
            { at: [0, 0.5, -0.3], rx: 0.55, ry: 0.2 },
            { at: [0, 0.5, 0.3], rx: 0.5, ry: 0.21 },
            { at: [0, 0.48, 0.8], rx: 0.42, ry: 0.19 },
            { at: [0, 0.47, 0.98], rx: 0.36, ry: 0.15 },
          ],
          {
            sides: 12,
            steps: 2,
            capStart: true,
            capEnd: true,
            paint: (t, a) => {
              const z = -1.02 + t * 2.0;
              if (z > 0.5 && z < 0.66 && a > -0.6) return c.trim;
              return a > 0.1 ? c.kart : c.kartDark;
            },
          },
        ),
      );
      // The ivory nose panel, flat at the front for the emblem, an orange frame on top
      // and a dark bumper below.
      b.add(taper(box(0.76, 0.36, 0.48, 0.13), 0.9, 0.86), c.ivory, { p: [0, 0.47, 1.1] });
      b.add(box(0.66, 0.06, 0.44, 0.03), c.trim, { p: [0, 0.64, 1.07] });
      b.add(box(0.8, 0.1, 0.14, 0.04), "#3a2d28", { p: [0, 0.29, 1.32] });
      // Cockpit rim.
      b.add(new THREE.TorusGeometry(0.34, 0.055, 5, 14), c.trim, {
        p: [0, 0.69, -0.28],
        r: [Math.PI / 2, 0, 0],
        s: [1, 1.2, 1],
      });
      // Seat: a padded cushion with a low back (the backpack rides above it).
      b.add(box(0.5, 0.1, 0.42, 0.04), c.seat, { p: [0, 0.48, -0.3] });
      b.add(box(0.48, 0.2, 0.1, 0.04), c.seat, { p: [0, 0.64, -0.56], r: [-0.15, 0, 0] });
      for (const s of [1, -1]) {
        // Rounded fenders: turquoise, with an orange stripe at the front and wooden
        // slats on the back ones.
        b.add(taper(box(0.46, 0.26, 0.74, 0.12), 0.9, 0.72, 0.05), c.kart, {
          p: [s * 0.76, 0.74, 0.88],
        });
        b.add(box(0.52, 0.3, 0.82, 0.13), c.kart, { p: [s * 0.8, 0.72, -0.78] });
        for (const k of [-0.07, 0.05])
          b.add(box(0.04, 0.06, 0.7, 0.012), c.wood, { p: [s * 1.065, 0.72 + k, -0.78] });
        // Wooden slats down the side of the tub.
        for (const k of [0, 1])
          b.add(box(0.05, 0.07, 0.6, 0.015), c.wood, { p: [s * 0.56, 0.46 + k * 0.11, -0.02] });
        b.add(box(0.2, 0.16, 0.8, 0.05), c.kartDark, { p: [s * 0.6, 0.36, 0.05] });
      }
      // Explorer gear on the back fenders: a strapped canvas bundle and a canteen.
      b.add(cyl(0.11, 0.11, 0.36, 8), "#d9c39a", { p: [0.8, 0.98, -0.82], r: [Math.PI / 2, 0, 0] });
      for (const z of [-0.94, -0.7])
        b.add(cyl(0.115, 0.115, 0.04, 8), c.strap, { p: [0.8, 0.98, z], r: [Math.PI / 2, 0, 0] });
      b.add(cyl(0.11, 0.12, 0.22, 8), "#5f8a4a", { p: [-0.8, 0.98, -0.8] });
      b.add(cyl(0.04, 0.05, 0.06, 6), "#3b2f2a", { p: [-0.8, 1.12, -0.8] });
      b.add(box(0.03, 0.2, 0.22, 0.01), c.strap, { p: [-0.8, 0.98, -0.8], s: [8.2, 1, 1] });
      // Exhaust.
      b.add(cyl(0.08, 0.1, 0.3, 8), "#4a3c36", { p: [0, 0.42, -1.18], r: [Math.PI / 2, 0, 0] });
      b.add(cyl(0.1, 0.1, 0.05, 8), c.trim, { p: [0, 0.42, -1.31], r: [Math.PI / 2, 0, 0] });
      if (detail === 0) {
        // Big tropical leaves sprouting from behind the back fenders and the nose.
        for (const s of [1, -1]) {
          b.addColored(leaf(0.55, 0.16, c.leaf, c.leafRib), {
            p: [s * 0.86, 0.78, -1.12],
            r: [-1.2, s * 0.3, s * 0.5],
          });
          b.addColored(leaf(0.42, 0.13, c.leaf, c.leafRib), {
            p: [s * 0.62, 0.74, -1.12],
            r: [-1.5, s * 0.2, s * 0.15],
          });
        }
      }
    },
    decorate(body) {
      // The palm emblem on the ivory nose.
      const e = emblemMesh("palm", { disc: c.ivory, ink: c.emblem, rim: c.trim }, 0.3);
      e.position.set(0, 0.47, 1.345);
      body.add(e);
    },
  };
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

  // The head: a round cranium with big eyes, an elongated rounded snout.
  const head = new THREE.Group();
  head.position.set(0, 0.32, 0.05);
  head.rotation.x = -0.12;
  // Oversized, like every mascot of the era.
  head.scale.setScalar(1.4);
  neck.add(head);
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.17], rx: 0.08, ry: 0.08 },
        { at: [0, 0.11, -0.13], rx: 0.15, ry: 0.15 },
        { at: [0, 0.11, -0.04], rx: 0.2, ry: 0.19 },
        { at: [0, 0.1, 0.06], rx: 0.2, ry: 0.18 },
        { at: [0, 0.06, 0.15], rx: 0.155, ry: 0.13, flat: 0.35 },
        { at: [0, 0.03, 0.25], rx: 0.135, ry: 0.1, flat: 0.5 },
        { at: [0, 0.025, 0.33], rx: 0.125, ry: 0.088, flat: 0.5 },
        { at: [0, 0.03, 0.38], rx: 0.09, ry: 0.065, flat: 0.4 },
        { at: [0, 0.035, 0.405], rx: 0.03, ry: 0.025 },
      ],
      {
        sides: 12,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (a < -0.9 && t > 0.45 ? c.belly : c.skin),
      },
    ),
  );
  // Nostrils.
  for (const s of [1, -1])
    skull.add(ellipsoid(6, 4), c.skinDark, {
      p: [s * 0.045, 0.085, 0.37],
      s: [0.018, 0.012, 0.014],
    });
  // The mouth's inside, seen when the jaw drops.
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, -0.01, 0.18], s: [0.11, 0.035, 0.17] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The crest: thick, curving back and up, gold into orange with soft bands.
  const crest = new THREE.Group();
  crest.position.set(0, 0.24, -0.04);
  head.add(crest);
  const gold = new THREE.Color(c.crestBase);
  const tip = new THREE.Color(c.crestTip);
  crest.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.06, 0.05], rx: 0.075, ry: 0.075 },
              { at: [0, 0.04, -0.02], rx: 0.09, ry: 0.1 },
              { at: [0, 0.17, -0.1], rx: 0.095, ry: 0.11 },
              { at: [0, 0.3, -0.21], rx: 0.094, ry: 0.105 },
              { at: [0, 0.39, -0.36], rx: 0.085, ry: 0.095 },
              { at: [0, 0.41, -0.5], rx: 0.07, ry: 0.078 },
              { at: [0, 0.37, -0.6], rx: 0.035, ry: 0.04 },
            ],
            {
              sides: 10,
              steps: 3,
              capStart: true,
              capEnd: true,
              paint: (t, a) => {
                const k = gold.clone().lerp(tip, Math.min(1, t * 1.15));
                // Soft bands across the crest, and a lighter top edge.
                if (Math.sin(t * 34) > 0.55) k.multiplyScalar(0.9);
                if (a > 0.9 && a < 2.2) k.lerp(new THREE.Color("#ffffff"), 0.12);
                return k;
              },
            },
          ),
        )
        .build(),
      mat,
    ),
  );

  // Lower jaw (pale underneath), with a tongue.
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.01, 0.0);
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.02, 0.0], rx: 0.13, ry: 0.06 },
              { at: [0, -0.04, 0.12], rx: 0.12, ry: 0.05, flat: -0.4 },
              { at: [0, -0.04, 0.25], rx: 0.11, ry: 0.045, flat: -0.5 },
              { at: [0, -0.03, 0.33], rx: 0.08, ry: 0.035, flat: -0.4 },
              { at: [0, -0.025, 0.36], rx: 0.02, ry: 0.015 },
            ],
            {
              sides: 10,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (_t, a) => (a > 0.5 && a < 2.6 ? c.mouth : a < -0.3 ? c.belly : c.skin),
            },
          ),
        )
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.012, 0.16], s: [0.07, 0.022, 0.1] })
        .build(),
      mat,
    ),
  );

  // Big friendly eyes, high on the cranium, and small brows.
  const eyes = buildEyes(head, {
    at: [0.1, 0.165, 0.085],
    size: [0.085, 0.104, 0.075],
    yaw: 0.32,
    pitch: -0.05,
    iris: c.eye,
    lid: c.skin,
    inward: 0.35,
    brow: { color: c.skinDark, at: [0.1, 0.245, 0.1], size: [0.05, 0.014, 0.025], tilt: -0.2 },
  });

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

  return {
    root,
    torso,
    neck,
    head,
    face: { ...eyes, jaw, jawOpen: 0.42 },
    arms,
    hands,
    tail,
    wings: [],
    wiggles: [
      { obj: crest, kind: "crest", side: 0, amount: 1 },
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
      restJaw: 0.32,
      restBrow: 0.2,
      restLids: 0,
      victory: "cheer",
    },
  };
}

export const TIKO: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
