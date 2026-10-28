/**
 * Elder Mossback: the valley's elder, keeper of the Pact's stories and of the Founders'
 * Horn. Kind, old, warm, and carrying a secret.
 *
 * An old armoured dinosaur (a shell of stone-grey plates over his back and shoulders,
 * a soft round beak of a face) gone slow and stooped with the years. Moss and lichen
 * grow on his plates (his name), with a fern frond and a few tiny flowers. Bushy white
 * brows, white whiskers on his cheeks and a white beard on his chin, little round
 * spectacles on his beak. A woven stole round his neck in the valley's red and cream,
 * fringed; a rope belt, and the Founders' Horn on its cord at his right hip. A gnarled
 * walking staff, a carved charm hanging from its crook.
 */
import * as THREE from "three";
import { Build, ellipsoid, gem, loft, tube, type V3 } from "../racers/kit/shapes";
import { skinMaterial } from "../racers/kit/paint";
import { buildEyes } from "../racers/kit/rig";
import { buildTail, mesh, mix, mottle, shade, skeleton, type PersonRig } from "./rig";
import {
  facing,
  flower,
  hornGeometry,
  moss,
  spectacles,
  staffGeometry,
  tassel,
  woven,
} from "./parts";

const C = {
  skin: "#93a274",
  skinDark: "#6f7f58",
  belly: "#e9dfbf",
  beak: "#d9c592",
  beakDark: "#a8925e",
  shell: "#77705a",
  shellDark: "#565040",
  shellRim: "#9a9070",
  lichen: "#cfd88a",
  white: "#f4f0e6",
  whiteShade: "#cfc8b8",
  mouth: "#6a2a2a",
  tongue: "#d8707a",
  iris: "#5a3a1a",
  irisRing: "#a8743a",
  stole: "#a8402a",
  stoleBands: ["#efe0b4", "#2f7a74", "#efe0b4", "#e0a030"],
  rope: "#b89660",
  ropeDark: "#8a6a3a",
  gold: "#d8a840",
  wood: "#7a5634",
  woodDark: "#4e3420",
  claw: "#d8ceb0",
};

export function buildMossback(): PersonRig {
  const rig = skeleton({
    name: "Elder Mossback",
    stance: {
      hipY: 0.5,
      stride: 0.3,
      lift: 0.07,
      stoop: 0.32,
      handRest: [0.27, 0.04, 0.12],
      handRestL: [0.3, 0.12, 0.3],
      mouth: [0, 0.075, 0.34],
      breath: 1.2,
      sway: 0.7,
      blinkEvery: 4.2,
      restJaw: 0.05,
      restLids: 0.24,
      restBrow: 0.15,
      response: 0.7,
      lookReach: 0.9,
    },
    neckAt: [0, 0.5, 0.06],
    headAt: [0, 0.1, 0.06],
    arms: {
      shoulder: [0.25, 0.42, 0.05],
      upper: 0.21,
      fore: 0.2,
      radius: [0.075, 0.062, 0.054],
      upperColor: C.skin,
      foreColor: (t) => (t > 0.78 ? C.rope : C.skin),
      hand: C.skin,
      handSize: 0.068,
      claws: C.claw,
      hint: [0.7, -0.4, -0.6],
    },
    legs: {
      hip: [0.15, -0.02, 0],
      thigh: 0.235,
      shin: 0.205,
      radius: [0.12, 0.085, 0.072],
      thighColor: C.skin,
      shinColor: C.skin,
      foot: { len: 0.24, width: 0.17, color: C.skin, claw: C.claw },
      ankleH: 0.075,
    },
  });
  rig.root.name = "Elder Mossback";
  const skin = new THREE.Color(C.skin);
  const skinDark = new THREE.Color(C.skinDark);
  const belly = new THREE.Color(C.belly);

  // ------------------------------------------------------------ body
  const body = new Build();
  // A round old body, soft in the middle, cream down the front.
  body.addColored(
    loft(
      [
        { at: [0, -0.07, 0.0], rx: 0.17, ry: 0.15 },
        { at: [0, 0.04, 0.02], rx: 0.26, ry: 0.24 },
        { at: [0, 0.18, 0.03], rx: 0.29, ry: 0.27 },
        { at: [0, 0.32, 0.02], rx: 0.27, ry: 0.24 },
        { at: [0, 0.44, 0.03], rx: 0.2, ry: 0.18 },
        { at: [0, 0.53, 0.05], rx: 0.12, ry: 0.12 },
      ],
      {
        sides: 14,
        steps: 2,
        up: [0, 0, 1],
        capStart: true,
        paint: (t, a) => {
          const front = Math.abs(a - Math.PI / 2) < 0.75;
          if (front) {
            // Belly scales: soft bands across.
            return Math.sin(t * 42) > 0.75 ? mix(C.belly, C.beakDark, 0.25) : belly;
          }
          return skin.clone().lerp(skinDark, mottle(t * 4, a) * 0.5);
        },
      },
    ),
  );
  // The shell: a dome of plates over the back, rimmed, with knobbly scutes.
  const shellC: V3 = [0, 0.29, -0.06];
  const shellS: V3 = [0.3, 0.32, 0.24];
  body.add(ellipsoid(16, 12), C.shellDark, { p: shellC, s: shellS });
  // Scutes: raised plates in rows over the dome.
  const dir = new THREE.Vector3();
  for (let row = 0; row < 4; row++)
    for (let col = -3; col <= 3; col++) {
      const v = -0.3 + row * 0.36;
      const h = (col * 0.38 + (row % 2 ? 0.19 : 0)) / Math.max(0.55, Math.cos(v));
      if (Math.abs(h) > 1.3 || (row === 3 && Math.abs(col) > 1)) continue;
      dir.set(Math.sin(h) * Math.cos(v), Math.sin(v), -Math.cos(h) * Math.cos(v));
      const p: V3 = [
        shellC[0] + dir.x * shellS[0] * 0.97,
        shellC[1] + dir.y * shellS[1] * 0.97,
        shellC[2] + dir.z * shellS[2] * 0.97,
      ];
      const n = new THREE.Vector3(
        dir.x / shellS[0],
        dir.y / shellS[1],
        dir.z / shellS[2],
      ).normalize();
      const s = 0.098 - row * 0.01;
      body.add(
        ellipsoid(8, 5),
        (pp) =>
          new THREE.Color(pp.z > 0.2 ? C.shellRim : C.shell).lerp(
            new THREE.Color(C.shellDark),
            mottle(row * 3 + col, pp.x * 4, 5) * 0.3,
          ),
        { p, r: facing([n.x, n.y, n.z]), s: [s * 0.92, s * 0.85, s * 0.32] },
      );
    }
  // Moss on the shell's top and over the shoulders; lichen lower down.
  const mossAt = (h: number, v: number, rad: number, seed: number, more = {}) => {
    dir.set(Math.sin(h) * Math.cos(v), Math.sin(v), -Math.cos(h) * Math.cos(v));
    const n = new THREE.Vector3(
      dir.x / shellS[0],
      dir.y / shellS[1],
      dir.z / shellS[2],
    ).normalize();
    moss(
      body,
      [
        shellC[0] + dir.x * shellS[0] * 1.02,
        shellC[1] + dir.y * shellS[1] * 1.02,
        shellC[2] + dir.z * shellS[2] * 1.02,
      ],
      [n.x, n.y, n.z],
      rad,
      seed,
      more,
    );
  };
  mossAt(0, 0.95, 0.17, 11, { fronds: 3, flowers: 2 });
  mossAt(0.55, 0.65, 0.13, 12, { flowers: 1 });
  mossAt(-0.5, 0.7, 0.13, 13, { fronds: 1 });
  mossAt(0.15, 0.55, 0.1, 17);
  mossAt(-0.2, 0.35, 0.08, 14);
  mossAt(0.9, 0.2, 0.07, 15);
  mossAt(-1.0, 0.45, 0.075, 16, { flowers: 1 });
  for (const [h, v, r] of [
    [0.6, -0.15, 0.03],
    [-0.4, -0.3, 0.025],
    [1.1, -0.35, 0.028],
    [-1.05, -0.05, 0.022],
  ] as V3[]) {
    dir.set(Math.sin(h) * Math.cos(v), Math.sin(v), -Math.cos(h) * Math.cos(v));
    const n = new THREE.Vector3(
      dir.x / shellS[0],
      dir.y / shellS[1],
      dir.z / shellS[2],
    ).normalize();
    body.add(new THREE.CircleGeometry(r, 9), C.lichen, {
      p: [
        shellC[0] + dir.x * shellS[0] * 1.012,
        shellC[1] + dir.y * shellS[1] * 1.012,
        shellC[2] + dir.z * shellS[2] * 1.012,
      ],
      r: facing([n.x, n.y, n.z]),
    });
  }
  // Shoulder plates, mossy on top.
  for (const s of [1, -1]) {
    body.add(ellipsoid(12, 8), C.shell, {
      p: [s * 0.25, 0.47, 0.0],
      s: [0.12, 0.075, 0.13],
      r: [0, 0, -s * 0.35],
    });
    body.add(gem(1), C.shellDark, { p: [s * 0.28, 0.53, 0.0], s: [0.04, 0.03, 0.04] });
    moss(body, [s * 0.24, 0.535, -0.02], [s * 0.35, 1, -0.1], 0.07, 20 + s, { lump: 0.024 });
  }

  // The stole: a woven collar round the neck, its two ends hanging down the front, fringed.
  const stolePaint = woven(C.stole, C.stoleBands, 0.2);
  body.addColored(
    loft(
      Array.from({ length: 13 }, (_, i) => {
        const a = (i / 12) * Math.PI * 2;
        return {
          at: [Math.sin(a) * 0.17, 0.5 - Math.cos(a) * 0.015, 0.04 + Math.cos(a) * 0.15] as V3,
          rx: 0.055,
          ry: 0.06,
          color: C.stole,
        };
      }),
      {
        sides: 8,
        steps: 2,
        paint: (t) => (Math.abs(((t * 6) % 1) - 0.5) < 0.12 ? C.stoleBands[0]! : C.stole),
      },
    ),
  );
  for (const s of [1, -1]) {
    const pts: V3[] = [
      [s * 0.1, 0.49, 0.17],
      [s * 0.11, 0.4, 0.23],
      [s * 0.115, 0.3, 0.27],
      [s * 0.12, 0.2, 0.29],
      [s * 0.12, 0.12, 0.28],
    ];
    body.addColored(
      loft(
        pts.map((p, i) => ({ at: p, rx: 0.07 + i * 0.004, ry: 0.016 })),
        {
          sides: 8,
          steps: 2,
          up: [0, 0, 1],
          capStart: true,
          capEnd: true,
          paint: (t, a) => stolePaint(t * 0.9, a),
        },
      ),
    );
    for (let k = 0; k < 4; k++)
      tassel(
        body,
        [s * 0.12 + (k - 1.5) * 0.034, 0.105, 0.285],
        0.07,
        k % 2 ? C.stoleBands[0]! : C.stole,
      );
  }
  // The rope belt, knotted at the right hip; the horn's cord tied to it.
  body.addColored(
    loft(
      Array.from({ length: 13 }, (_, i) => {
        const a = (i / 12) * Math.PI * 2;
        return {
          at: [Math.sin(a) * 0.272, 0.06, 0.025 + Math.cos(a) * 0.255] as V3,
          rx: 0.022,
          ry: 0.022,
        };
      }),
      { sides: 6, steps: 2, paint: (t) => (Math.sin(t * 130) > 0 ? C.rope : C.ropeDark) },
    ),
  );
  body.add(ellipsoid(8, 6), C.rope, { p: [-0.25, 0.06, 0.12], s: [0.04, 0.035, 0.04] });
  body.addColored(
    tube(
      [
        [-0.26, 0.04, 0.12],
        [-0.29, -0.02, 0.09],
        [-0.3, -0.04, 0.04],
      ],
      0.007,
      C.ropeDark,
      { sides: 4 },
    ),
  );
  rig.torso.add(mesh(body));

  // A short, thick tail with a ridge of plates, moss at its root.
  rig.tail = buildTail(
    rig.hips,
    [0, 0.02, -0.18],
    [
      [0.13, 0.2, 0.09],
      [0.09, 0.18, 0.04],
      [0.04, 0.12, 0.01],
    ],
    [0.55, -0.25, -0.2],
    (_k, t, a) => (a < -1.0 ? belly : skin.clone().lerp(skinDark, mottle(t * 3, a) * 0.5)),
  );
  rig.tail.forEach((j, k) => {
    const b = new Build();
    for (let i = 0; i < 2; i++)
      b.add(gem(1), C.shellDark, {
        p: [0, [0.12, 0.085, 0.04][k]! * 0.85, -0.05 - i * 0.08],
        s: [0.03 - k * 0.006, 0.03 - k * 0.006, 0.035],
      });
    if (k === 0) moss(b, [0, 0.12, 0.02], [0, 1, -0.2], 0.05, 31, { lump: 0.022 });
    j.add(mesh(b));
  });

  // Arms: wrist wraps.
  for (const arm of rig.arms)
    arm.fore.add(
      mesh(
        new Build().add(new THREE.CylinderGeometry(0.058, 0.058, 0.035, 9), C.rope, {
          p: [0, 0, 0.14],
          r: [Math.PI / 2, 0, 0],
        }),
      ),
    );

  // Neck: thick and wrinkled.
  rig.neck.add(
    mesh(
      new Build().addColored(
        loft(
          [
            { at: [0, -0.06, -0.01], rx: 0.13, ry: 0.13 },
            { at: [0, 0.04, 0.0], rx: 0.115, ry: 0.115 },
            { at: [0, 0.13, 0.03], rx: 0.11, ry: 0.11 },
          ],
          {
            sides: 10,
            steps: 2,
            up: [0, 0, 1],
            paint: (t, a) =>
              Math.abs(a - Math.PI / 2) < 0.7
                ? Math.sin(t * 30) > 0.5
                  ? shade(C.belly, 0.88)
                  : belly
                : skin,
          },
        ),
      ),
    ),
  );

  buildHead(rig);

  // ------------------------------------------------------------ the staff and the horn
  const staff = new THREE.Group();
  staff.add(
    new THREE.Mesh(
      staffGeometry(0.6, 0.7, { wood: C.wood, dark: C.woodDark, charm: C.gold, cord: "#6a4426" }),
      skinMaterial(),
    ),
  );
  staff.userData.alwaysHeld = { hand: 0, at: [0.0, 0, 0.04], rot: [0.06, 0, -0.05] };
  staff.userData.foot = 0.6;
  rig.root.add(staff);
  rig.props.staff = { obj: staff, restAt: [0.3, 0.1, 0.3], restRot: [0, 0, 0] };
  const hornRest: { at: V3; rot: V3 } = { at: [-0.3, 0.02, -0.12], rot: [0.75, 0.2, 0.15] };
  for (const part of ["a", "b"] as const) {
    const h = new THREE.Group();
    h.add(new THREE.Mesh(hornGeometry(part), skinMaterial()));
    h.userData.inHand =
      part === "a"
        ? { at: [0.0, 0.0, 0.03], rot: [-1.2, 0, 0.2] }
        : { at: [0.0, -0.02, -0.12], rot: [-1.0, 0, -0.2] };
    rig.root.add(h);
    rig.props[part === "a" ? "hornA" : "hornB"] = {
      obj: h,
      restAt: hornRest.at,
      restRot: hornRest.rot,
    };
  }
  return rig;
}

function buildHead(rig: PersonRig) {
  const head = rig.head;
  head.scale.setScalar(1.12);
  const skin = new THREE.Color(C.skin);
  const skinDark = new THREE.Color(C.skinDark);
  const beak = new THREE.Color(C.beak);
  const belly = new THREE.Color(C.belly);

  // The skull: a round dome, a short soft snout ending in a beak at the mouth.
  const beakDark = new THREE.Color(C.beakDark);
  const sk = new Build().addColored(
    loft(
      [
        { at: [0, 0.17, -0.16], rx: 0.1, ry: 0.1 },
        { at: [0, 0.18, -0.11], rx: 0.2, ry: 0.19 },
        { at: [0, 0.18, -0.01], rx: 0.225, ry: 0.2 },
        { at: [0, 0.165, 0.08], rx: 0.205, ry: 0.17, flat: 0.2 },
        { at: [0, 0.14, 0.16], rx: 0.165, ry: 0.13, flat: 0.3 },
        { at: [0, 0.125, 0.225], rx: 0.13, ry: 0.105, flat: 0.3 },
        { at: [0, 0.12, 0.262], rx: 0.09, ry: 0.078 },
        { at: [0, 0.12, 0.28], rx: 0.04, ry: 0.035 },
      ],
      {
        sides: 16,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => {
          // The beak: the snout's lower front, pale horn, darker at its edge.
          if (t > 0.72 && a < 0.35) return beak.clone().lerp(beakDark, a < -0.9 ? 0.35 : 0);
          if (a < -0.9 && t > 0.4) return belly;
          return skin.clone().lerp(skinDark, mottle(t * 5, a, 4) * 0.45);
        },
      },
    ),
  );
  for (const s of [1, -1]) {
    // Nostrils on top of the snout.
    sk.add(ellipsoid(6, 4), C.skinDark, { p: [s * 0.035, 0.185, 0.255], s: [0.016, 0.01, 0.013] });
    // The gentle smile: along the beak's edge, curling up under the cheek.
    sk.addColored(
      tube(
        [
          [s * 0.05, 0.088, 0.268],
          [s * 0.11, 0.084, 0.21],
          [s * 0.155, 0.09, 0.13],
          [s * 0.175, 0.112, 0.075],
        ],
        [0.007, 0.008, 0.008, 0.006],
        C.mouth,
        { sides: 5 },
      ),
    );
    // Wrinkles at the eye's corner.
    for (const k of [0, 1])
      sk.addColored(
        tube(
          [
            [s * 0.17, 0.25 - k * 0.025, 0.1],
            [s * 0.195, 0.245 - k * 0.035, 0.07],
            [s * 0.205, 0.235 - k * 0.045, 0.04],
          ],
          0.005,
          C.skinDark,
          { sides: 4 },
        ),
      );
    // Whiskers: soft white tufts down his cheeks (they meet the beard).
    for (const [y, z, len, r] of [
      [0.16, 0.07, 0.14, 0.045],
      [0.12, 0.03, 0.12, 0.042],
    ] as [number, number, number, number][]) {
      sk.addColored(
        loft(
          [
            { at: [s * 0.17, y + 0.02, z], rx: r * 0.6, ry: r * 0.6 },
            { at: [s * 0.195, y - len * 0.2, z - 0.01], rx: r, ry: r * 0.9 },
            { at: [s * 0.205, y - len * 0.6, z - 0.02], rx: r * 0.8, ry: r * 0.7 },
            { at: [s * 0.19, y - len, z - 0.04], rx: r * 0.12, ry: r * 0.12 },
          ],
          {
            sides: 9,
            steps: 3,
            capStart: true,
            capEnd: true,
            up: [0, 0, 1],
            paint: (t, a) => (t > 0.75 || Math.abs(a) > 2.4 ? C.whiteShade : C.white),
          },
        ),
      );
    }
  }
  sk.add(ellipsoid(10, 6), C.mouth, { p: [0, 0.09, 0.16], s: [0.13, 0.03, 0.12] });
  // Moss on his crown, a sprig and a flower.
  moss(sk, [0, 0.355, -0.06], [0, 1, -0.25], 0.075, 41, { lump: 0.026, fronds: 1 });
  flower(sk, [0.05, 0.36, -0.02], [0.3, 1, 0.3], 0.018, "#fff6e8");
  // Little round spectacles perched on his beak.
  spectacles(sk, {
    at: [0.1, 0.25, 0.2],
    r: 0.064,
    yaw: 0.28,
    bridgeY: 0.245,
    ear: [0.205, 0.26, -0.02],
    rim: C.gold,
  });
  head.add(mesh(sk));

  // The lower beak (the jaw), with his white beard.
  const jaw = new THREE.Group();
  jaw.position.set(0, 0.085, 0.03);
  head.add(jaw);
  const jb = new Build()
    .addColored(
      loft(
        [
          { at: [0, -0.015, -0.03], rx: 0.17, ry: 0.055, sq: 2.4 },
          { at: [0, -0.03, 0.08], rx: 0.15, ry: 0.05, flat: -0.4 },
          { at: [0, -0.03, 0.17], rx: 0.115, ry: 0.042, flat: -0.5 },
          { at: [0, -0.02, 0.235], rx: 0.065, ry: 0.03 },
        ],
        {
          sides: 12,
          steps: 2,
          capStart: true,
          capEnd: true,
          paint: (t, a) => (a > 0.5 && a < 2.6 ? C.mouth : t > 0.75 ? C.beak : C.belly),
        },
      ),
    )
    .add(ellipsoid(8, 5), C.tongue, { p: [0, -0.012, 0.13], s: [0.08, 0.02, 0.09] });
  // The beard: soft white lobes under the chin, the middle one longest.
  for (const [x, len, r] of [
    [0, 0.15, 0.06],
    [0.06, 0.11, 0.048],
    [-0.06, 0.11, 0.048],
    [0.11, 0.07, 0.04],
    [-0.11, 0.07, 0.04],
  ] as V3[]) {
    const z = 0.16 - Math.abs(x) * 0.5;
    jb.addColored(
      loft(
        [
          { at: [x, -0.02, z], rx: r * 0.9, ry: r * 0.7 },
          { at: [x * 1.05, -0.04 - len * 0.35, z + 0.012], rx: r, ry: r * 0.8 },
          { at: [x * 1.12, -0.04 - len * 0.75, z - 0.005], rx: r * 0.6, ry: r * 0.5 },
          { at: [x * 1.15, -0.04 - len, z - 0.03], rx: r * 0.12, ry: r * 0.12 },
        ],
        {
          sides: 9,
          steps: 3,
          capStart: true,
          capEnd: true,
          up: [0, 0, 1],
          paint: (t) => (t > 0.7 ? C.whiteShade : C.white),
        },
      ),
    );
  }
  jaw.add(mesh(jb));

  // Kind, heavy-lidded eyes; big bushy white brows drooping at their ends.
  const eyes = buildEyes(head, {
    at: [0.1, 0.25, 0.125],
    size: [0.058, 0.068, 0.05],
    yaw: 0.3,
    pitch: -0.06,
    iris: C.iris,
    irisRing: C.irisRing,
    irisScale: 1.08,
    lid: shade(C.skin, 0.95),
    inward: 0.2,
    lidTilt: -0.18,
    cheek: 0.3,
    brow: { color: C.white, at: [0.105, 0.33, 0.155], size: [0.08, 0.028, 0.045], tilt: -0.32 },
  });
  // Brow tufts: a second, wispier lump on each brow's outer end.
  eyes.brows.forEach((br, i) => {
    const s = i === 0 ? 1 : -1;
    br.add(
      new THREE.Mesh(
        new Build()
          .add(ellipsoid(8, 5), C.white, {
            p: [s * 0.075, -0.018, -0.012],
            s: [0.055, 0.028, 0.04],
            r: [0, 0, -s * 0.4],
          })
          .add(ellipsoid(8, 5), C.whiteShade, {
            p: [s * 0.11, -0.04, -0.02],
            s: [0.03, 0.02, 0.025],
            r: [0, 0, -s * 0.6],
          })
          .build(),
        skinMaterial(),
      ),
    );
  });
  rig.face = { ...eyes, jaw, jawOpen: 0.36 };
}
