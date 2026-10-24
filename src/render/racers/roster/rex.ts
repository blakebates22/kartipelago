/**
 * The T-Rex: powerful, confident, a little boastful (Blake's concept sheet, our own
 * build).
 *
 * Silhouette: a huge head with a huge toothy grin, a wreath of jungle leaves round it
 * with gold goggles on top; a stocky body, a leaf lei, a thick tail.
 * Orange-red skin with darker red mottling, a cream belly and jaw.
 * Gear: a red neckerchief, a bone pendant, leather straps and bracers.
 * Kart: the Bone Crusher (the sleek family, dark): a dinosaur-skull front with glowing
 * eye sockets, bone spikes down the spine, red banners, leaves lashed on with rope,
 * glowing twin exhausts, black tyres veined with lava orange, a fang emblem.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, card, cone, cyl, ellipsoid, horn, loft, tube } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { goggles, leaf, strap } from "../kit/props";
import { sleekKart } from "../kit/sleek";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#e2551e",
  skinDark: "#b23314",
  spot: "#a82a14",
  belly: "#f6dcae",
  claw: "#2a2020",
  mouth: "#7c1e28",
  tongue: "#e8607a",
  tooth: "#fff8ea",
  leaf: "#3f9a34",
  leafRib: "#8fd05a",
  scarf: "#d8302a",
  bone: "#f1e4c4",
  boneDark: "#c9b48a",
  leather: "#6a3e22",
  leatherDark: "#43281a",
  gold: "#e8b030",
  lens: "#3ad0e0",
  // The kart.
  char: "#2c2422",
  charLight: "#4a3a32",
  wood: "#7a4a26",
  rope: "#c9a060",
  banner: "#c8302a",
  lava: "#ff7a1a",
  seat: "#3a2620",
  tyre: "#221c1c",
};

/** The alternate look (a repeated rival): a deep green rex. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#4a9a3a",
  skinDark: "#2e6e24",
  spot: "#2a5a20",
  scarf: "#e8a020",
  banner: "#2a6ac8",
  lava: "#3ad0ff",
};

type P = typeof MAIN;

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return sleekKart({
    main: c.char,
    dark: c.charLight,
    stripe: c.banner,
    nose: c.bone,
    trim: c.boneDark,
    metal: c.wood,
    seat: c.seat,
    glass: "#ffb060",
    tyre: c.tyre,
    rim: c.lava,
    cap: c.char,
    tyreLine: c.lava,
    width: 1.06,
    front: "blade",
    pods: "intake",
    rear: "ducktail",
    spokes: 5,
    emblem: { kind: "fang", disc: c.bone, ink: c.banner, rim: c.char },
    extras(b, detail) {
      // The skull on the nose: a broad bone snout, its eye sockets glowing, a jaw of
      // fangs hanging over the front wing.
      b.addColored(
        loft(
          [
            { at: [0, 0.52, 0.7], rx: 0.34, ry: 0.16, sq: 2.6 },
            { at: [0, 0.5, 0.95], rx: 0.3, ry: 0.14, sq: 2.6, flat: 0.3 },
            { at: [0, 0.44, 1.2], rx: 0.24, ry: 0.11, sq: 2.6, flat: 0.4 },
            { at: [0, 0.4, 1.38], rx: 0.16, ry: 0.08, sq: 2.4 },
          ],
          {
            sides: 10,
            steps: 1,
            capStart: true,
            capEnd: true,
            paint: (t) => (t > 0.85 ? c.boneDark : c.bone),
          },
        ),
      );
      for (const s of [1, -1]) {
        b.add(ellipsoid(6, 4), c.boneDark, { p: [s * 0.17, 0.67, 0.84], s: [0.13, 0.05, 0.1] });
        b.add(ellipsoid(6, 4), c.char, { p: [s * 0.17, 0.62, 0.9], s: [0.1, 0.07, 0.07] });
        b.add(ellipsoid(5, 3), c.lava, { p: [s * 0.17, 0.62, 0.94], s: [0.06, 0.045, 0.04] });
      }
      if (detail === 1) return;
      // The fangs, top and bottom, along the skull's jaw line.
      for (let k = 0; k < 4; k++) {
        const x = -0.21 + k * 0.14;
        b.addColored(
          horn(
            [x, 0.36, 1.2 - Math.abs(x) * 0.6],
            [x * 1.05, 0.22, 1.27 - Math.abs(x) * 0.6],
            0.03,
            c.bone,
            [0, 0, 0.02],
            5,
          ),
        );
      }
      // Bone spikes down the spine behind the seat, and a pair at the shoulders.
      for (let k = 0; k < 3; k++)
        b.addColored(
          horn(
            [0, 0.6 - k * 0.02, -0.78 - k * 0.14],
            [0, 0.95 - k * 0.04, -0.95 - k * 0.14],
            0.06 - k * 0.006,
            c.bone,
            [0, 0, -0.04],
            5,
          ),
        );
      for (const s of [1, -1]) {
        b.addColored(
          horn([s * 0.44, 0.62, -0.2], [s * 0.6, 0.95, -0.4], 0.05, c.bone, [0, 0, -0.04], 4),
        );
        // A red banner on each side, a white leaf on it.
        b.add(
          card(
            [
              [0, 0],
              [0.32, 0],
              [0.32, 0.24],
              [0.16, 0.32],
              [0, 0.24],
            ],
            0.015,
          ),
          c.banner,
          {
            p: [s * 0.52, 0.42, -0.1],
            r: [0, (s * Math.PI) / 2, 0],
          },
        );
        b.addColored(leaf(0.16, 0.05, "#fff4e0", "#ffffff"), {
          p: [s * 0.535, 0.48, -0.26],
          r: [0, (s * Math.PI) / 2, 0],
        });
        // Jungle leaves lashed on at the back, with rope.
        for (let k = 0; k < 1; k++)
          b.addColored(leaf(0.4, 0.12, c.leaf, c.leafRib), {
            p: [s * (0.3 + k * 0.06), 0.66, -1.05 - k * 0.05],
            r: [-1.9 + k * 0.2, s * 0.2, s * (0.4 + k * 0.3)],
          });
        b.add(new THREE.TorusGeometry(0.11, 0.015, 3, 8), c.rope, {
          p: [s * 0.4, 0.55, -0.6],
          r: [0, Math.PI / 2, 0],
        });
        // The exhausts: twin glowing pipes kicked up at the back.
        b.add(cyl(0.06, 0.07, 0.36, 8), c.charLight, {
          p: [s * 0.22, 0.6, -1.24],
          r: [Math.PI / 2 - 0.35, 0, 0],
        });
        b.add(cyl(0.045, 0.045, 0.03, 8), c.lava, {
          p: [s * 0.22, 0.66, -1.41],
          r: [Math.PI / 2 - 0.35, 0, 0],
        });
      }
    },
  });
}

// ------------------------------------------------------------------ the rex

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "rex";
  const torso = new THREE.Group();
  root.add(torso);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);
  const spot = new THREE.Color(c.spot);
  // Mottled: darker spots scattered over the back and sides.
  const mottle = (x: number, y: number) =>
    Math.sin(x * 37 + y * 11) * Math.sin(y * 29 - x * 13) > 0.55;
  const skinPaint = (t: number, a: number) =>
    Math.abs(a - Math.PI / 2) < 0.8 ? belly : mottle(t * 5, a) ? spot : skin;

  // A stocky, deep-chested body, cream down the front.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.01], rx: 0.21, ry: 0.18 },
        { at: [0, 0.12, 0.0], rx: 0.25, ry: 0.22 },
        { at: [0, 0.28, 0.02], rx: 0.24, ry: 0.21 },
        { at: [0, 0.42, 0.04], rx: 0.18, ry: 0.16 },
        { at: [0, 0.5, 0.06], rx: 0.13, ry: 0.13 },
      ],
      { sides: 10, steps: 2, up: [0, 0, 1], capStart: true, paint: skinPaint },
    ),
  );
  // The lei: leaves all round the neck, a red neckerchief under it, a bone pendant.
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2;
    body.addColored(leaf(0.15, 0.05, c.leaf, c.leafRib), {
      p: [Math.sin(a) * 0.15, 0.47, 0.05 + Math.cos(a) * 0.14],
      r: [Math.PI / 2 + 0.9 * Math.cos(a), a, 0],
    });
  }
  body.add(new THREE.TorusGeometry(0.13, 0.035, 4, 10), c.scarf, {
    p: [0, 0.45, 0.05],
    r: [Math.PI / 2 + 0.2, 0, 0],
  });
  body.add(cone(0.07, 0.12, 3), c.scarf, {
    p: [0, 0.36, 0.22],
    r: [Math.PI - 0.3, 0, 0],
    s: [1, 1, 0.3],
  });
  // The pendant: a little bone skull.
  body.add(ellipsoid(8, 6), c.bone, { p: [0, 0.31, 0.25], s: [0.05, 0.045, 0.03] });
  for (const s of [1, -1])
    body.add(ellipsoid(5, 4), c.leatherDark, {
      p: [s * 0.018, 0.32, 0.275],
      s: [0.012, 0.012, 0.006],
    });
  // Crossed straps and a belt.
  for (const s of [1, -1])
    body.addColored(
      strap(
        [
          [s * 0.18, 0.42, 0.12],
          [0, 0.24, 0.235],
          [-s * 0.2, 0.06, 0.2],
        ],
        0.022,
        0.01,
        c.leather,
      ),
    );
  body.add(new THREE.TorusGeometry(0.22, 0.025, 3, 10), c.leather, {
    p: [0, 0.04, 0.0],
    r: [Math.PI / 2, 0, 0],
    s: [1, 0.85, 1],
  });
  body.add(box(0.07, 0.06, 0.03, 0.01), c.gold, { p: [0, 0.04, 0.2] });
  torso.add(new THREE.Mesh(body.build(), mat));

  const neck = new THREE.Group();
  neck.position.set(0, 0.46, 0.06);
  neck.rotation.x = 0.15;
  torso.add(neck);
  neck.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.05, 0], rx: 0.14, ry: 0.14 },
              { at: [0, 0.06, 0.02], rx: 0.13, ry: 0.13 },
              { at: [0, 0.14, 0.03], rx: 0.13, ry: 0.13 },
            ],
            { sides: 8, steps: 2, up: [0, 0, 1], paint: skinPaint },
          ),
        )
        .build(),
      mat,
    ),
  );
  const head = new THREE.Group();
  neck.add(head);

  // Short (but not too short) arms, leather bracers, dark claws.
  const { arms, hands } = buildArms(torso, {
    shoulder: [0.19, 0.38, 0.12],
    upper: 0.19,
    fore: 0.18,
    radius: [0.07, 0.058, 0.05],
    color: c.skin,
    hand: c.skin,
    handSize: 0.07,
    claws: c.claw,
    hint: [0.9, -0.4, -0.2],
  });
  for (const arm of arms)
    arm.fore.add(
      new THREE.Mesh(
        new Build()
          .add(cyl(0.058, 0.055, 0.07, 8), c.leather, { p: [0, 0, 0.12], r: [Math.PI / 2, 0, 0] })
          .build(),
        mat,
      ),
    );

  // A thick tail over the back of the kart.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.15, 0.25, 0.11],
    [0.11, 0.24, 0.06],
    [0.06, 0.22, 0.015],
  ];
  const lift = [0.5, -0.28, 0.15];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.08, -0.16);
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
                { at: [0, 0, -len - r1 * 0.6], rx: r1 * 0.6, ry: r1 * 0.6 },
              ],
              {
                sides: 7,
                capStart: true,
                capEnd: true,
                paint: (t, a) => (a < -1.0 ? belly : mottle(t * 4 + k, a) ? spot : skin),
              },
            ),
          )
          .build(),
        mat,
      ),
    );
    tail.push(j);
    parent = j;
  });

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.22, 0.02], s: [0.25, 0.28, 0.22] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.82, 0.22], s: [0.24, 0.22, 0.38] })
      .add(ellipsoid(5, 3), c.leaf, { p: [0, 1.02, 0.12], s: [0.24, 0.07, 0.24] })
      .add(
        tube(
          [
            [0, 0.06, -0.14],
            [0, 0.06, -0.5],
            [0, 0.04, -0.82],
          ],
          [0.14, 0.09, 0.02],
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
    cheer: [new THREE.Vector3(0.38, 0.66, 0.18), new THREE.Vector3(-0.38, 0.66, 0.18)],
    personality: {
      lean: 1.15,
      headTurn: 1.0,
      curiosity: 0.3,
      glanceEvery: 3.2,
      blinkEvery: 3.4,
      blinkTime: 0.12,
      bob: 0.025,
      bobHz: 1.8,
      steerHands: 1.1,
      boostKick: 1.0,
      boostFace: 1.0,
      grumble: 0.7,
      response: 1,
      restJaw: 0.22,
      restBrow: -0.05,
      restLids: 0.12,
      victory: "cheer",
    },
  };
  buildHead(rig, c);
  return rig;
}

function buildHead(rig: RiderRig, c: P) {
  const mat = skinMaterial();
  const head = rig.head;
  head.position.set(0, 0.16, 0.06);
  head.rotation.x = 0.02;
  head.scale.setScalar(1.4);
  const belly = new THREE.Color(c.belly);
  const skin = new THREE.Color(c.skin);

  // The skull: big and boxy, a deep muzzle, a heavy brow.
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.14, -0.2], rx: 0.1, ry: 0.1, sq: 2.4 },
        { at: [0, 0.15, -0.13], rx: 0.2, ry: 0.19, sq: 2.6 },
        { at: [0, 0.15, -0.02], rx: 0.23, ry: 0.21, sq: 2.8 },
        { at: [0, 0.12, 0.1], rx: 0.21, ry: 0.17, sq: 2.8, flat: 0.3 },
        { at: [0, 0.09, 0.22], rx: 0.18, ry: 0.13, sq: 2.8, flat: 0.4 },
        { at: [0, 0.07, 0.33], rx: 0.15, ry: 0.1, sq: 2.6, flat: 0.4 },
        { at: [0, 0.065, 0.4], rx: 0.11, ry: 0.075, sq: 2.4 },
        { at: [0, 0.06, 0.43], rx: 0.05, ry: 0.04 },
      ],
      {
        sides: 12,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (a < -0.8 && t > 0.4 ? belly : skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(ellipsoid(6, 4), c.skinDark, {
      p: [s * 0.055, 0.12, 0.415],
      s: [0.02, 0.012, 0.015],
    });
    // The big grin, curling up at the back, a row of upper teeth.
    skull.addColored(
      tube(
        [
          [s * 0.07, 0.015, 0.41],
          [s * 0.13, 0.01, 0.3],
          [s * 0.17, 0.02, 0.17],
          [s * 0.19, 0.07, 0.07],
        ],
        [0.009, 0.01, 0.01, 0.007],
        c.mouth,
        { sides: 5 },
      ),
    );
    for (let k = 0; k < 5; k++)
      skull.add(cone(0.019, 0.055, 4), c.tooth, {
        p: [s * (0.07 + k * 0.022), 0.0, 0.4 - k * 0.065],
        r: [Math.PI, 0, 0],
      });
    // The heavy brow over each eye.
    skull.add(ellipsoid(8, 5), c.skinDark, {
      p: [s * 0.13, 0.3, 0.12],
      s: [0.08, 0.03, 0.06],
      r: [0, 0, s * 0.3],
    });
  }
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.0, 0.26], s: [0.14, 0.03, 0.17] });
  head.add(new THREE.Mesh(skull.build(), mat));

  // The wreath: leaves round the crown, gold goggles riding on top.
  const crown = new THREE.Group();
  crown.position.set(0, 0.3, -0.04);
  head.add(crown);
  const wb = new Build();
  for (let k = 0; k < 7; k++) {
    const a = (k / 7) * Math.PI * 2;
    wb.addColored(leaf(0.16 + (k % 3) * 0.03, 0.055, k % 4 === 1 ? "#c8302a" : c.leaf, c.leafRib), {
      p: [Math.sin(a) * 0.17, 0, Math.cos(a) * 0.16],
      r: [-0.5 - 0.5 * Math.cos(a), a, 0],
    });
  }
  wb.addColored(goggles({ frame: c.gold, lens: c.lens, glint: "#e8ffff" }, 0.085, 0.058), {
    p: [0, 0.03, 0.12],
    r: [-1.0, 0, 0],
  });
  wb.add(new THREE.TorusGeometry(0.18, 0.018, 3, 12), c.leather, {
    p: [0, -0.01, 0.0],
    r: [Math.PI / 2 + 0.25, 0, 0],
  });
  crown.add(new THREE.Mesh(wb.build(), mat));

  // The lower jaw with its teeth, and a big tongue.
  const jaw = new THREE.Group();
  jaw.position.set(0, 0.0, 0.04);
  head.add(jaw);
  const jb = new Build()
    .addColored(
      loft(
        [
          { at: [0, -0.02, -0.02], rx: 0.19, ry: 0.07, sq: 2.6 },
          { at: [0, -0.05, 0.12], rx: 0.16, ry: 0.06, flat: -0.4, sq: 2.6 },
          { at: [0, -0.05, 0.26], rx: 0.13, ry: 0.05, flat: -0.5, sq: 2.4 },
          { at: [0, -0.04, 0.36], rx: 0.08, ry: 0.035 },
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
    .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.02, 0.17], s: [0.09, 0.025, 0.12] });
  for (const s of [1, -1])
    for (let i = 0; i < 4; i++)
      jb.add(cone(0.016, 0.045, 4), c.tooth, {
        p: [s * (0.06 + i * 0.024), -0.015, 0.33 - i * 0.075],
      });
  jaw.add(new THREE.Mesh(jb.build(), mat));

  // Smaller, confident eyes under the brow.
  const eyes = buildEyes(head, {
    at: [0.135, 0.235, 0.17],
    size: [0.068, 0.08, 0.058],
    yaw: 0.42,
    pitch: -0.05,
    iris: "#6a3a10",
    irisRing: "#e8a02a",
    irisScale: 1.05,
    lid: c.skin,
    inward: 0.12,
    lidTilt: 0.35,
    cheek: 0.25,
    brow: { color: c.skinDark, at: [0.135, 0.315, 0.19], size: [0.065, 0.02, 0.03], tilt: 0.3 },
  });

  rig.face = { ...eyes, jaw, jawOpen: 0.5 };
  rig.wiggles.push({ obj: crown, kind: "sway", side: 0, amount: 0.5 });
}

export const REX: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
