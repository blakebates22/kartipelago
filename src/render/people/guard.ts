/**
 * The smugglers' guards: the underground's doormen, who look like they'd sell their own
 * tails. Shifty, comic and not to be trusted.
 *
 * A stocky bonehead (a thick bony dome of a skull ringed with knobs, for butting) with a
 * pot belly and round shoulders, slouching. One eye under a patch (or both squinting),
 * a heavy brow cocked, a crooked grin with a gold tooth and a gap. A bandana over the
 * dome, knotted behind, a patched vest open over the belly, a wide belt, and the ring of
 * keys at the hip (the tunnel's key: he holds it out when the deal's done). Dressed for
 * his kingdom: the valley's leather and red bandana, the snow's fur trim and bobble hat,
 * the desert's head wrap and sash, the islands' flowered vest and shell necklace. The
 * seed picks his skin, his colours, the patch and the gold tooth.
 *
 * The Dragon Kingdom's own guards (folk "dragon") are another thing altogether (Blake,
 * valley polish 14, note 13: "these should be different than the smuggler npcs. they are
 * dragon guards"): soldiers, standing straight, in a steel helm with a crimson crest, a
 * breastplate over a crimson tabard with the dragon's gold mark, pauldrons, and a spear.
 * No patch, no gold tooth, no keys.
 */
import * as THREE from "three";
import { Build, ellipsoid, gem, loft, tube, cone, type V3 } from "../racers/kit/shapes";
import { seeded, skinMaterial } from "../racers/kit/paint";
import { buildEyes } from "../racers/kit/rig";
import { buildTail, mesh, mottle, shade, skeleton, type PersonRig } from "./rig";
import { cutFront, keyRingGeometry, patch, tassel } from "./parts";
import type { Folk } from "../villager";

const SKINS: Record<string, string[]> = {
  valley: ["#8a8a5a", "#9a7048", "#6f8a6a"],
  snow: ["#7f93a8", "#8a8298", "#6f8580"],
  desert: ["#b08050", "#a06a48", "#9a8a5a"],
  beach: ["#4f9a8a", "#a8786a", "#7a9a4a"],
  dragon: ["#7a6a8a", "#6a7a6a"],
  road: ["#8a8a6a", "#8a7058"],
};

interface Dress {
  vest: string;
  vestDark: string;
  patches: string[];
  head: string;
  dots: string;
  belt: string;
  /** What's on his head (a helm: a dragon guard, a soldier). */
  hat: "bandana" | "beanie" | "wrap" | "helm";
  fur?: string;
  flowers?: string[];
  sash?: string;
  shells?: boolean;
}

const DRESS: Record<Folk, Dress[]> = {
  valley: [
    {
      vest: "#6a4428",
      vestDark: "#4a2e1a",
      patches: ["#8a6a3a", "#3f6a2a", "#a8502a"],
      head: "#c8302a",
      dots: "#f4e8d0",
      belt: "#3a2618",
      hat: "bandana",
    },
    {
      vest: "#4a5a2a",
      vestDark: "#30401a",
      patches: ["#7a4a2a", "#a88a4a", "#5a3a2a"],
      head: "#2a5aa8",
      dots: "#f4e8d0",
      belt: "#3a2618",
      hat: "bandana",
    },
  ],
  snow: [
    {
      vest: "#5a3a5a",
      vestDark: "#3a2440",
      patches: ["#2a5a8a", "#8a2a2a"],
      head: "#d83a3a",
      dots: "#ffffff",
      belt: "#2a2028",
      hat: "beanie",
    },
    {
      vest: "#2a4a6a",
      vestDark: "#1a3048",
      patches: ["#6a2a2a", "#3a6a4a"],
      head: "#3a8a5a",
      dots: "#ffe060",
      belt: "#2a2028",
      hat: "beanie",
    },
  ],
  desert: [
    {
      vest: "#b8884a",
      vestDark: "#8a6030",
      patches: ["#7a3a2a", "#2a6a7a"],
      head: "#e8d8b0",
      dots: "#c8402a",
      belt: "#5a3a20",
      hat: "wrap",
      sash: "#c8402a",
    },
    {
      vest: "#8a4a6a",
      vestDark: "#603048",
      patches: ["#c8a040", "#2a5a6a"],
      head: "#2a8a9a",
      dots: "#f0c040",
      belt: "#5a3a20",
      hat: "wrap",
      sash: "#f0c040",
    },
  ],
  beach: [
    {
      vest: "#ff7a4a",
      vestDark: "#c85a30",
      patches: ["#2fb0e0", "#ffe040"],
      head: "#2fb0e0",
      dots: "#ffffff",
      belt: "#6a4a2a",
      hat: "bandana",
      flowers: ["#ffffff", "#ffe040"],
      shells: true,
    },
    {
      vest: "#3fb8a0",
      vestDark: "#2a8a78",
      patches: ["#ff4f8a", "#ffe040"],
      head: "#ff4f8a",
      dots: "#ffe040",
      belt: "#6a4a2a",
      hat: "bandana",
      flowers: ["#ff4f8a", "#ffffff"],
      shells: true,
    },
  ],
  dragon: [
    {
      // (vest: the steel; head: the crimson of the crest and tabard; dots: the gold mark.)
      vest: "#8a8e9a",
      vestDark: "#4e525e",
      patches: [],
      head: "#9a1e1e",
      dots: "#e0b840",
      belt: "#2a1e18",
      hat: "helm",
    },
  ],
  road: [
    {
      vest: "#6a5a3a",
      vestDark: "#4a3e28",
      patches: ["#3a5a7a", "#8a3a2a"],
      head: "#8a6a2a",
      dots: "#f4e8d0",
      belt: "#3a2618",
      hat: "bandana",
    },
  ],
};

export function guardLook(folk: Folk, seed: number) {
  // (Each trait from its own draw, so neighbouring seeds differ.)
  const pick = (k: number) => seeded(seed * 7919 + k * 104729)();
  const skins = SKINS[folk] ?? SKINS.valley!;
  const dresses = DRESS[folk] ?? DRESS.valley;
  const soldier = folk === "dragon";
  return {
    skin: skins[Math.floor(pick(1) * skins.length)]!,
    dress: dresses[seed % dresses.length]!,
    /** The eye under a patch: 1 left, -1 right, 0 none (both squint). */
    patch: soldier ? 0 : ([1, -1, 0][(seed + Math.floor(pick(2) * 2)) % 3]! as 1 | -1 | 0),
    gold: pick(3) < 0.5 ? 1 : -1,
    belly: soldier ? 0.9 : 0.88 + pick(4) * 0.28,
    scar: !soldier && pick(5) < 0.5,
    /** A dragon guard: a soldier, not a smuggler. */
    soldier,
  };
}

export function buildGuard(folk: Folk, seed: number): PersonRig {
  const L = guardLook(folk, seed);
  const d = L.dress;
  const C = {
    skin: L.skin,
    skinDark: shade(L.skin, 0.72),
    belly: shade(L.skin, 1.5),
    dome: shade(L.skin, 1.18),
    knob: shade(L.skin, 0.62),
    mouth: "#5a1e22",
    tongue: "#d8607a",
    tooth: "#fff4dc",
    gold: "#f0c030",
    claw: "#3a3028",
    patch: "#1a1614",
  };
  const skin = new THREE.Color(C.skin);
  const skinDark = new THREE.Color(C.skinDark);
  const belly = new THREE.Color(C.belly);
  const B = L.belly;
  const rig = skeleton({
    name: L.soldier ? "Dragon Guard" : "Smugglers' Guard",
    stance: {
      hipY: 0.52,
      stride: 0.36,
      lift: 0.1,
      stoop: L.soldier ? 0.02 : 0.14,
      handRest: [0.31, -0.02, 0.12],
      ...(L.soldier ? { handRestL: [0.3, 0.06, 0.2] as V3 } : {}),
      mouth: [0, 0.07, 0.3],
      breath: 1.3,
      sway: 1.3,
      blinkEvery: 2.6,
      restJaw: 0.24,
      restLids: L.soldier ? 0.2 : 0.46,
      restBrow: L.soldier ? -0.2 : -0.35,
      glance: L.soldier ? 4 : 1.3,
      response: 1.15,
      lookReach: 1.1,
    },
    neckAt: [0, 0.5, 0.08],
    headAt: [0, 0.09, 0.05],
    arms: {
      shoulder: [0.25, 0.42, 0.06],
      upper: 0.22,
      fore: 0.21,
      radius: [0.09, 0.075, 0.068],
      upperColor: C.skin,
      foreColor: (t) => (t > 0.72 ? d.belt : C.skin),
      hand: C.skin,
      handSize: 0.08,
      claws: C.claw,
      hint: [0.75, -0.3, -0.6],
    },
    legs: {
      hip: [0.15, -0.02, 0.0],
      thigh: 0.25,
      shin: 0.22,
      radius: [0.12, 0.09, 0.075],
      thighColor: C.skin,
      shinColor: C.skin,
      foot: { len: 0.26, width: 0.17, color: C.skin, claw: C.claw },
      ankleH: 0.075,
    },
  });

  // ------------------------------------------------------------ body
  const torsoSecs = (k: number) =>
    [
      { at: [0, -0.07, 0.02], rx: 0.17 * k, ry: 0.15 * k },
      { at: [0, 0.05, 0.05], rx: 0.27 * k * B, ry: 0.27 * k * B },
      { at: [0, 0.19, 0.05], rx: 0.28 * k * B, ry: 0.27 * k * B },
      { at: [0, 0.33, 0.04], rx: 0.27 * k, ry: 0.22 * k },
      { at: [0, 0.45, 0.04], rx: 0.22 * k, ry: 0.17 * k },
      { at: [0, 0.54, 0.07], rx: 0.13 * k, ry: 0.12 * k },
    ] as { at: V3; rx: number; ry: number }[];
  const body = new Build();
  body.addColored(
    loft(torsoSecs(1), {
      sides: 14,
      steps: 2,
      up: [0, 0, 1],
      capStart: true,
      paint: (t, a) =>
        Math.abs(a - Math.PI / 2) < 0.8
          ? Math.sin(t * 40) > 0.7
            ? shade(C.belly, 0.9)
            : belly
          : skin.clone().lerp(skinDark, mottle(t * 4, a, seed) * 0.5),
    }),
  );
  if (L.soldier) armour(body, torsoSecs, d, B);
  // The vest: open down the front, patched and stitched.
  const fur = d.fur;
  const vestPaint = (t: number, a: number) => {
    if (d.flowers) {
      // Big island flowers on it.
      const f = Math.sin(t * 23 + a * 5) * Math.sin(a * 7 - t * 9);
      if (f > 0.72) return d.flowers[0]!;
      if (f > 0.6) return d.flowers[1]!;
    }
    return Math.sin(t * 60) > 0.92 ? d.vestDark : d.vest;
  };
  const vestGeo = loft(
    torsoSecs(1.06)
      .slice(1)
      .map((s, i) => ({
        ...s,
        at: [s.at[0], s.at[1], s.at[2] - 0.005] as V3,
        rx: s.rx + (i === 4 ? 0.02 : 0),
      })),
    { sides: 16, steps: 2, up: [0, 0, 1], paint: vestPaint },
  );
  if (!L.soldier)
    body.addColored(cutFront(vestGeo, (y) => 0.34 + Math.max(0, 0.3 - y) * 1.3, -0.2, 0.7));
  // Lapels: the vest's front edges (fur, in the snow).
  for (const s of L.soldier ? [] : [1, -1]) {
    const edge: V3[] = [];
    for (const y of [0.0, 0.12, 0.24, 0.36, 0.47]) {
      const a = 0.34 + Math.max(0, 0.3 - y) * 1.3;
      const rx = 0.28 * 1.06 * (y < 0.25 ? B : 1) - (y > 0.4 ? 0.06 : 0);
      const rz = 0.27 * 1.06 * (y < 0.25 ? B : 0.85) - (y > 0.4 ? 0.07 : 0);
      edge.push([s * Math.sin(a) * rx, y + 0.02, 0.05 + Math.cos(a) * rz]);
    }
    body.addColored(tube(edge, fur ? 0.045 : 0.016, fur ?? d.vestDark, { sides: 7, steps: 3 }));
    if (fur)
      // Thick fur along the edge (and round the collar), in soft overlapping tufts.
      for (let i = 0; i < edge.length - 1; i++)
        for (let k = 0; k < 3; k++) {
          const a = edge[i]!;
          const b = edge[i + 1]!;
          const f = k / 3;
          body.add(ellipsoid(8, 6), k % 2 ? fur : shade(fur, 0.93), {
            p: [
              (a[0] + (b[0] - a[0]) * f) * 1.03,
              a[1] + (b[1] - a[1]) * f,
              (a[2] + (b[2] - a[2]) * f) * 1.01,
            ],
            s: [0.055, 0.05, 0.045],
          });
        }
  }
  // Patches on the vest (back and sides), stitched on crooked.
  const r = seeded(seed + 101);
  const patchAt = (a: number, y: number, w: number, h: number, k: number) => {
    const rx = 0.28 * 1.07 * (y < 0.25 ? B : 1);
    const rz = 0.27 * 1.07 * (y < 0.25 ? B : 0.85);
    const p: V3 = [Math.sin(a) * rx, y, 0.05 + Math.cos(a) * rz];
    patch(
      body,
      p,
      [Math.sin(a), 0, Math.cos(a)],
      w,
      h,
      d.patches[k % d.patches.length]!,
      "#e8dcc0",
      (r() - 0.5) * 0.6,
    );
  };
  if (!L.soldier) {
    patchAt(1.4 + r() * 0.3, 0.14, 0.09, 0.08, 0);
    patchAt(-1.6 - r() * 0.3, 0.3, 0.08, 0.1, 1);
    patchAt(Math.PI - 0.3, 0.22, 0.12, 0.1, 2);
  }
  // The belt under the belly, a big buckle.
  body.addColored(
    loft(
      Array.from({ length: 13 }, (_, i) => {
        const a = (i / 12) * Math.PI * 2;
        return {
          at: [Math.sin(a) * 0.275 * B, 0.0, 0.05 + Math.cos(a) * 0.27 * B] as V3,
          rx: 0.016,
          ry: 0.045,
        };
      }),
      { sides: 6, steps: 2, paint: () => d.belt },
    ),
  );
  body.add(new THREE.BoxGeometry(0.1, 0.08, 0.025), C.gold, { p: [0, 0.0, 0.05 + 0.275 * B] });
  body.add(new THREE.BoxGeometry(0.06, 0.045, 0.03), d.belt, { p: [0, 0.0, 0.05 + 0.276 * B] });
  if (d.sash)
    body.addColored(
      loft(
        Array.from({ length: 13 }, (_, i) => {
          const a = (i / 12) * Math.PI * 2;
          return {
            at: [Math.sin(a) * 0.282 * B, 0.07, 0.05 + Math.cos(a) * 0.276 * B] as V3,
            rx: 0.02,
            ry: 0.035,
          };
        }),
        { sides: 6, steps: 2, paint: () => d.sash! },
      ),
    );
  if (d.shells)
    for (let k = 0; k < 9; k++) {
      const a = ((k - 4) / 9) * Math.PI * 1.1;
      body.add(cone(0.022, 0.04, 6), k % 2 ? "#fff0e0" : "#f0b8a0", {
        p: [Math.sin(a) * 0.15, 0.47 - Math.cos(a) * 0.04, 0.09 + Math.cos(a) * 0.13],
        r: [Math.PI + 0.3, 0, 0],
      });
    }
  if (d.hat === "beanie") {
    // A knitted scarf, its end hanging.
    body.addColored(
      loft(
        Array.from({ length: 13 }, (_, i) => {
          const a = (i / 12) * Math.PI * 2;
          return {
            at: [Math.sin(a) * 0.15, 0.51, 0.08 + Math.cos(a) * 0.13] as V3,
            rx: 0.05,
            ry: 0.05,
          };
        }),
        { sides: 8, steps: 2, paint: (t) => (Math.floor(t * 12) % 2 ? d.head : d.dots) },
      ),
    );
    body.add(new THREE.BoxGeometry(0.08, 0.2, 0.03), d.head, {
      p: [0.08, 0.38, 0.22],
      r: [0.25, 0, 0.15],
    });
  }
  rig.torso.add(mesh(body));

  if (L.soldier) spear(rig, d);
  // The key ring at his right hip (a smuggler's: not a soldier's).
  const keys = new THREE.Group();
  const kr = new THREE.Mesh(keyRingGeometry({ iron: "#6a6a74", gold: C.gold }), skinMaterial());
  kr.scale.setScalar(1.7);
  keys.add(kr);
  keys.userData.inHand = { at: [0, -0.03, 0.05], rot: [0, 0, 0] };
  keys.userData.dangle = true;
  if (!L.soldier) rig.root.add(keys);
  if (!L.soldier)
    rig.props.key = { obj: keys, restAt: [-0.27 * B, 0.0, 0.12], restRot: [0, -0.6, 0.15] };

  // Tail.
  rig.tail = buildTail(
    rig.hips,
    [0, 0.02, -0.18],
    [
      [0.13, 0.24, 0.08],
      [0.08, 0.22, 0.03],
      [0.03, 0.12, 0.008],
    ],
    [0.6, -0.3, -0.2],
    (_k, t, a) => (a < -1.0 ? belly : skin.clone().lerp(skinDark, mottle(t * 3, a, seed) * 0.5)),
  );

  // Wrist bands with studs.
  for (const arm of rig.arms)
    arm.fore.add(
      mesh(
        (() => {
          const b = new Build().add(new THREE.CylinderGeometry(0.074, 0.074, 0.06, 10), d.belt, {
            p: [0, 0, 0.16],
            r: [Math.PI / 2, 0, 0],
          });
          for (let k = 0; k < 5; k++) {
            const a = (k / 5) * Math.PI * 2;
            b.add(gem(0), "#c8c8d0", {
              p: [Math.cos(a) * 0.075, Math.sin(a) * 0.075, 0.16],
              s: 0.012,
            });
          }
          return b;
        })(),
      ),
    );

  // Neck: short and thick.
  rig.neck.add(
    mesh(
      new Build().addColored(
        loft(
          [
            { at: [0, -0.06, -0.01], rx: 0.14, ry: 0.13 },
            { at: [0, 0.04, 0.0], rx: 0.13, ry: 0.12 },
            { at: [0, 0.12, 0.02], rx: 0.12, ry: 0.12 },
          ],
          {
            sides: 10,
            steps: 2,
            up: [0, 0, 1],
            paint: (_t, a) => (Math.abs(a - Math.PI / 2) < 0.7 ? belly : skin),
          },
        ),
      ),
    ),
  );

  buildHead(rig, C, L, d, seed);
  return rig;
}

function buildHead(
  rig: PersonRig,
  C: Record<
    | "skin"
    | "skinDark"
    | "belly"
    | "dome"
    | "knob"
    | "mouth"
    | "tongue"
    | "tooth"
    | "gold"
    | "claw"
    | "patch",
    string
  >,
  L: ReturnType<typeof guardLook>,
  d: Dress,
  seed: number,
) {
  const head = rig.head;
  head.scale.setScalar(1.1);
  const skin = new THREE.Color(C.skin);
  const skinDark = new THREE.Color(C.skinDark!);
  const belly = new THREE.Color(C.belly);

  // The skull: a short heavy face under the dome, a blunt snout.
  const sk = new Build().addColored(
    loft(
      [
        { at: [0, 0.15, -0.15], rx: 0.1, ry: 0.1 },
        { at: [0, 0.165, -0.1], rx: 0.19, ry: 0.18 },
        { at: [0, 0.165, 0.0], rx: 0.205, ry: 0.19 },
        { at: [0, 0.14, 0.09], rx: 0.18, ry: 0.15, flat: 0.3 },
        { at: [0, 0.115, 0.18], rx: 0.15, ry: 0.115, flat: 0.35 },
        { at: [0, 0.105, 0.24], rx: 0.12, ry: 0.09, flat: 0.3 },
        { at: [0, 0.105, 0.275], rx: 0.07, ry: 0.06 },
        { at: [0, 0.105, 0.29], rx: 0.03, ry: 0.025 },
      ],
      {
        sides: 16,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) =>
          a < -0.9 && t > 0.4 ? belly : skin.clone().lerp(skinDark, mottle(t * 5, a, seed) * 0.4),
      },
    ),
  );
  // The dome: thick and bony, ringed with knobs; knobs on the snout too.
  sk.add(ellipsoid(16, 10), C.dome!, { p: [0, 0.29, -0.03], s: [0.2, 0.16, 0.2] });
  for (let k = 0; k < 9; k++) {
    const a = ((k - 4) / 8) * Math.PI * 1.2 + Math.PI;
    sk.add(gem(1), C.knob!, {
      p: [Math.sin(a) * 0.2, 0.22, -0.03 + Math.cos(a) * 0.19],
      s: [0.028, 0.03, 0.028],
    });
  }
  for (const s of [1, -1]) {
    sk.add(gem(1), C.knob!, { p: [s * 0.06, 0.19, 0.24], s: [0.018, 0.02, 0.018] });
    // Nostrils.
    sk.add(ellipsoid(6, 4), C.skinDark!, { p: [s * 0.035, 0.15, 0.275], s: [0.016, 0.012, 0.012] });
  }
  // The crooked grin: one corner hitched up, a row of teeth, one gold, one missing.
  const g = L.gold;
  sk.addColored(
    tube(
      [
        [-g * 0.17, 0.085, 0.09],
        [-g * 0.13, 0.072, 0.18],
        [-g * 0.06, 0.07, 0.25],
        [0, 0.072, 0.27],
        [g * 0.07, 0.078, 0.245],
        [g * 0.13, 0.095, 0.18],
        [g * 0.16, 0.13, 0.11],
      ],
      [0.011, 0.012, 0.012, 0.012, 0.012, 0.012, 0.01],
      C.mouth!,
      { sides: 5, steps: 2 },
    ),
  );
  // Teeth hanging under the lip: a gap, and a gold one.
  for (let k = -3; k <= 3; k++) {
    if (k === -1 * g && !L.soldier) continue;
    const x = k * 0.03;
    const z = 0.272 - k * k * 0.004;
    const gold = k === 2 * g && !L.soldier;
    sk.add(
      new THREE.BoxGeometry(gold ? 0.028 : 0.024, gold ? 0.036 : 0.03, 0.014),
      gold ? C.gold : C.tooth,
      {
        p: [x, 0.058 + (k * g > 0 ? k * g * 0.004 : 0), z],
        r: [0.1, Math.atan2(x, 0.25), (k % 2) * 0.12],
      },
    );
  }
  sk.add(ellipsoid(10, 6), C.mouth!, { p: [0, 0.075, 0.15], s: [0.12, 0.03, 0.12] });
  if (L.scar)
    sk.addColored(
      tube(
        [
          [L.patch === 0 ? 0.08 : -L.patch * 0.07, 0.31, 0.12],
          [L.patch === 0 ? 0.12 : -L.patch * 0.11, 0.22, 0.16],
          [L.patch === 0 ? 0.15 : -L.patch * 0.14, 0.14, 0.15],
        ],
        0.008,
        shade(C.skin, 1.35),
        { sides: 4 },
      ),
    );

  // On his head: a bandana knotted behind, a bobble hat, a head wrap, or a soldier's helm.
  if (d.hat === "helm") helm(sk, d);
  else if (d.hat === "beanie") {
    sk.add(
      new THREE.SphereGeometry(1, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.55),
      (p) => (Math.floor((p.y + 0.2) * 8) % 2 ? d.head : shade(d.head, 0.8)),
      { p: [0, 0.27, -0.03], s: [0.225, 0.2, 0.225] },
    );
    sk.addColored(
      loft(
        Array.from({ length: 17 }, (_, i) => {
          const a = (i / 16) * Math.PI * 2;
          return {
            at: [
              Math.sin(a) * 0.215,
              0.29 + (Math.cos(a) > 0 ? 0.02 : -0.01),
              -0.03 + Math.cos(a) * 0.215,
            ] as V3,
            rx: 0.03,
            ry: 0.035,
          };
        }),
        { sides: 6, steps: 2, paint: () => d.dots },
      ),
    );
    sk.add(gem(1), d.dots, { p: [0, 0.5, -0.04], s: 0.06 });
  } else {
    const wrap = d.hat === "wrap";
    sk.add(
      new THREE.SphereGeometry(1, 16, 9, 0, Math.PI * 2, 0, Math.PI * (wrap ? 0.6 : 0.5)),
      (p) => {
        if (wrap)
          return Math.abs(Math.sin(p.y * 40 + p.x * 8)) < 0.15 ? shade(d.head, 0.85) : d.head;
        // Polka dots.
        const u = Math.atan2(p.x, p.z) * 4;
        const v = p.y * 9;
        return Math.hypot(u - Math.round(u), v - Math.round(v)) < 0.22 ? d.dots : d.head;
      },
      { p: [0, wrap ? 0.25 : 0.27, -0.03], s: [0.215, wrap ? 0.22 : 0.185, 0.215] },
    );
    // The knot behind, two tails hanging.
    sk.add(ellipsoid(8, 6), d.head, { p: [0, 0.3, -0.24], s: [0.05, 0.045, 0.04] });
    for (const s of [1, -1])
      sk.addColored(
        loft(
          [
            { at: [s * 0.02, 0.29, -0.25], rx: 0.04, ry: 0.012 },
            { at: [s * 0.06, 0.2, -0.27], rx: 0.045, ry: 0.012 },
            { at: [s * 0.08, 0.12, -0.25], rx: 0.035, ry: 0.01 },
          ],
          { sides: 6, steps: 2, up: [0, 0, 1], capStart: true, capEnd: true, paint: () => d.head },
        ),
      );
    if (wrap) tassel(sk, [0.12, 0.33, -0.18], 0.06, d.dots);
  }
  head.add(mesh(sk));

  // The jaw: a heavy underbite, one tooth poking up.
  const jaw = new THREE.Group();
  jaw.position.set(0, 0.07, 0.03);
  head.add(jaw);
  const jb = new Build()
    .addColored(
      loft(
        [
          { at: [0, -0.015, -0.03], rx: 0.17, ry: 0.06, sq: 2.4 },
          { at: [0, -0.03, 0.08], rx: 0.155, ry: 0.055, flat: -0.4 },
          { at: [0, -0.03, 0.18], rx: 0.13, ry: 0.048, flat: -0.5, sq: 2.6 },
          { at: [0, -0.02, 0.25], rx: 0.08, ry: 0.035 },
        ],
        {
          sides: 12,
          steps: 2,
          capStart: true,
          capEnd: true,
          paint: (_t, a) => (a > 0.4 && a < 2.7 ? C.mouth! : a < -1 ? C.belly! : C.skin),
        },
      ),
    )
    .add(ellipsoid(8, 5), C.tongue!, { p: [0, -0.008, 0.12], s: [0.085, 0.022, 0.095] })
    .add(cone(0.016, 0.045, 5), C.tooth!, { p: [g * 0.075, 0.01, 0.22] });
  // A stubbly chin.
  for (let k = 0; k < 7; k++)
    jb.add(ellipsoid(5, 3), C.skinDark!, {
      p: [Math.sin(k * 2.1) * 0.08, -0.06, 0.16 + Math.cos(k * 1.7) * 0.05],
      s: [0.008, 0.005, 0.008],
    });
  jaw.add(mesh(jb));

  // Small, close-set, shifty eyes under a heavy brow; one under a patch.
  const eyes = buildEyes(head, {
    at: [0.085, 0.215, 0.165],
    size: [0.05, 0.055, 0.045],
    yaw: 0.25,
    pitch: -0.08,
    iris: "#3a5a1a",
    irisRing: "#c8a030",
    irisScale: 0.95,
    lid: shade(C.skin, 0.9),
    inward: -0.3,
    lidTilt: 0.42,
    cheek: 0.4,
    gaze: [0.22, -0.05],
    brow: {
      color: shade(C.skin, 0.55),
      at: [0.09, 0.275, 0.2],
      size: [0.07, 0.024, 0.035],
      tilt: 0.35,
    },
  });
  // One brow cocked up (suspicious), the other down. (A soldier's both level and stern.)
  const cock = L.soldier ? 0 : L.patch === 0 ? 1 : -L.patch;
  eyes.brows.forEach((b, i) => {
    const side = i === 0 ? 1 : -1;
    if (side === cock) {
      b.position.y += 0.025;
      b.rotation.z -= side * 0.6;
    }
  });
  if (L.patch !== 0) {
    const s = L.patch;
    const pb = new Build()
      .add(ellipsoid(12, 8), C.patch!, {
        p: [s * 0.095, 0.215, 0.205],
        s: [0.06, 0.062, 0.025],
        r: [0, s * 0.3, 0],
      })
      .addColored(
        tube(
          [
            [s * 0.05, 0.25, 0.215],
            [-s * 0.08, 0.31, 0.17],
            [-s * 0.19, 0.3, 0.02],
            [-s * 0.19, 0.24, -0.12],
          ],
          0.008,
          C.patch!,
          { sides: 4, steps: 2 },
        ),
      )
      .addColored(
        tube(
          [
            [s * 0.15, 0.2, 0.16],
            [s * 0.205, 0.2, 0.04],
            [s * 0.19, 0.24, -0.12],
          ],
          0.008,
          C.patch!,
          { sides: 4, steps: 2 },
        ),
      );
    head.add(mesh(pb));
    // (The eye under it is shut.)
    for (const e of eyes.eyes) if (e.side === s) e.group.visible = false;
    eyes.brows.forEach((b, i) => {
      if ((i === 0 ? 1 : -1) === s) b.position.y += 0.012;
    });
  }
  rig.face = { ...eyes, jaw, jawOpen: 0.42 };
}

/** A dragon guard's armour: a steel breastplate (banded) over a crimson tabard with the
 * dragon's gold mark on it, a gorget at the neck and a pauldron on each shoulder. */
function armour(
  body: Build,
  torsoSecs: (k: number) => { at: V3; rx: number; ry: number }[],
  d: Dress,
  B: number,
) {
  const steel = d.vest;
  const dark = d.vestDark;
  body.addColored(
    loft(
      torsoSecs(1.07)
        .slice(1, 5)
        .map((s) => ({ ...s, at: [s.at[0], s.at[1], s.at[2] - 0.004] as V3 })),
      {
        sides: 16,
        steps: 2,
        up: [0, 0, 1],
        capStart: true,
        // (Lames: steel bands, a dark line between each.)
        paint: (t) => (Math.sin(t * 34) > 0.86 ? dark : steel),
      },
    ),
  );
  // The tabard: crimson, hanging front and back from under the breastplate to the thighs.
  for (const z of [1, -1]) {
    body.add(new THREE.BoxGeometry(0.26, 0.3, 0.02), d.head, {
      p: [0, -0.1, 0.05 + z * (0.272 * B + 0.012)],
      r: [z * 0.12, 0, 0],
    });
    body.add(new THREE.BoxGeometry(0.27, 0.025, 0.024), d.dots, {
      p: [0, -0.245, 0.05 + z * (0.272 * B + 0.03)],
      r: [z * 0.12, 0, 0],
    });
  }
  // The dragon's gold mark on the chest: a diamond, wings either side.
  body.add(gem(1), d.dots, { p: [0, 0.27, 0.05 + 0.28], s: [0.05, 0.065, 0.02] });
  for (const s of [1, -1])
    body.add(cone(0.03, 0.09, 3), d.dots, {
      p: [s * 0.07, 0.29, 0.05 + 0.27],
      r: [0, 0, s * 1.2],
      s: [1, 1, 0.3],
    });
  // Gorget and pauldrons.
  body.addColored(
    loft(
      [
        { at: [0, 0.44, 0.05], rx: 0.2, ry: 0.16 },
        { at: [0, 0.52, 0.06], rx: 0.15, ry: 0.13 },
      ],
      { sides: 14, steps: 2, up: [0, 0, 1], paint: () => steel },
    ),
  );
  for (const s of [1, -1]) {
    body.add(new THREE.SphereGeometry(1, 12, 8, 0, Math.PI * 2, 0, Math.PI * 0.55), steel, {
      p: [s * 0.25, 0.43, 0.05],
      s: [0.13, 0.1, 0.13],
      r: [0, 0, -s * 0.35],
    });
    body.add(new THREE.TorusGeometry(1, 0.12, 5, 14), dark, {
      p: [s * 0.27, 0.4, 0.05],
      s: [0.12, 0.12, 0.12],
      r: [Math.PI / 2, 0, -s * 0.35],
    });
  }
}

/** A dragon guard's spear: always in his left hand, upright, its butt on the ground; a
 * steel head and a crimson pennant under it. */
function spear(rig: PersonRig, d: Dress) {
  const b = new Build()
    .add(new THREE.CylinderGeometry(0.022, 0.026, 1.9, 7), "#5a3a22", { p: [0, 0.45, 0] })
    .add(new THREE.CylinderGeometry(0.03, 0.03, 0.06, 7), d.dots, { p: [0, 1.38, 0] })
    .add(cone(0.045, 0.24, 4), d.vest, { p: [0, 1.52, 0] })
    .add(new THREE.BoxGeometry(0.012, 0.16, 0.22), d.head, { p: [0, 1.28, -0.12] });
  const obj = new THREE.Group();
  obj.add(mesh(b));
  obj.userData.alwaysHeld = { hand: 0, at: [0.0, 0, 0.03], rot: [0, 0, 0] };
  obj.userData.foot = 0.5;
  rig.root.add(obj);
  rig.props.spear = { obj, restAt: [0.3, 0.1, 0.25], restRot: [0, 0, 0] };
}

/** A dragon guard's helm: a steel dome over the bony one, a brow band, a crimson crest of
 * spines from front to back, and a neck guard. */
function helm(sk: Build, d: Dress) {
  sk.add(new THREE.SphereGeometry(1, 16, 9, 0, Math.PI * 2, 0, Math.PI * 0.55), d.vest, {
    p: [0, 0.265, -0.03],
    s: [0.23, 0.2, 0.23],
  });
  sk.addColored(
    loft(
      Array.from({ length: 17 }, (_, i) => {
        const a = (i / 16) * Math.PI * 2;
        return {
          at: [Math.sin(a) * 0.228, 0.275, -0.03 + Math.cos(a) * 0.228] as V3,
          rx: 0.02,
          ry: 0.03,
        };
      }),
      { sides: 6, steps: 2, paint: () => d.dots },
    ),
  );
  // (The crest: thin spines standing up off the helm, front to back, tallest in the middle.)
  for (let k = 0; k < 7; k++) {
    const t = k / 6;
    const a = 0.85 - t * 1.9;
    const h = 0.22 - Math.abs(t - 0.4) * 0.16;
    const rr = 0.2 + h * 0.42;
    sk.add(cone(0.06, h, 4), d.head, {
      p: [0, 0.265 + Math.cos(a) * rr, -0.03 + Math.sin(a) * rr],
      r: [a, 0, 0],
      s: [0.3, 1, 1.3],
    });
  }
  // The neck guard behind.
  sk.add(
    new THREE.SphereGeometry(
      1,
      12,
      6,
      Math.PI * 1.1,
      Math.PI * 0.8,
      Math.PI * 0.45,
      Math.PI * 0.25,
    ),
    d.vestDark,
    {
      p: [0, 0.265, -0.03],
      s: [0.25, 0.24, 0.25],
    },
  );
}
