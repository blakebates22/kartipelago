/**
 * The townsfolk (Blake, Oct 26; rebuilt to the racers' finish): the dinosaur folk who
 * live in each kingdom, in its colours and clothes. Eight kinds, each its own shape:
 *
 *   parasaur  tall and gentle, a broad duck-bill, a long tube of a crest swept back
 *   iggy      tall and sturdy, a long deep snout, thumb spikes
 *   pachy     round and cheerful, a bony dome ringed with knobs
 *   compy     the villages' children: small, quick, a big head and big eyes
 *   ovi       slim and feathered: a beak, a rounded crest, a fan of tail feathers
 *   ankylo    low and wide on four legs, an armoured back of knobs, a club on its tail
 *   trike     on four legs: a frill, three horns, a beak
 *   sauro     a small long-neck on four legs
 *
 * The kingdom dresses them: the valley's leaf collars and shell beads, the snow's
 * striped scarves, bobble hats and earmuffs, the desert's straw hats and ponchos, the
 * islands' leis and sun hats, the Dragon Kingdom's hooded tunics, and the roads'
 * travellers' packs. The seed picks the kind, the skin, the colours and the variant.
 */
import * as THREE from "three";
import { Build, cone, ellipsoid, gem, loft, tube, type V3 } from "../racers/kit/shapes";
import { buildEyes, type EyeStyle } from "../racers/kit/rig";
import { backpack, bedroll, leaf, feather } from "../racers/kit/props";
import { seeded } from "../racers/kit/paint";
import {
  buildTail,
  mesh,
  mix,
  mottle,
  shade,
  skeleton,
  type ArmSpec,
  type LegSpec,
  type PersonRig,
  type Stance,
} from "./rig";
import { flower, sleeve, woven } from "./parts";

export type Species =
  "ankylo" | "parasaur" | "trike" | "pachy" | "compy" | "iggy" | "ovi" | "sauro";
export const SPECIES: readonly Species[] = [
  "ankylo",
  "parasaur",
  "trike",
  "pachy",
  "compy",
  "iggy",
  "ovi",
  "sauro",
];
export type Folk = "valley" | "snow" | "desert" | "beach" | "dragon" | "road";

/** Four-legged kinds (the rest walk on two). */
export const FOURS = new Set<Species>(["ankylo", "trike", "sauro"]);

/** How big each kind is (the view's scale), how fast it walks, and how wide it stands. */
export const SIZE: Record<Species, { scale: number; speed: number; radius: number }> = {
  ankylo: { scale: 1.15, speed: 0.9, radius: 1.3 },
  parasaur: { scale: 1.12, speed: 1.3, radius: 0.8 },
  trike: { scale: 1.15, speed: 0.95, radius: 1.4 },
  pachy: { scale: 1.05, speed: 1.2, radius: 0.75 },
  compy: { scale: 1.0, speed: 2.0, radius: 0.45 },
  iggy: { scale: 1.18, speed: 1.15, radius: 0.8 },
  ovi: { scale: 1.0, speed: 1.6, radius: 0.6 },
  sauro: { scale: 1.1, speed: 0.85, radius: 1.3 },
};

/** Skin colours each kingdom's folk come in (picked by the seed). */
const SKINS: Record<Folk, string[]> = {
  valley: ["#6fae4a", "#9a7b4f", "#c98a3a", "#4f8f7a", "#b5a046"],
  snow: ["#8aa6c9", "#b7b1d8", "#6f8f9e", "#c9c2b0", "#7d9b8a"],
  desert: ["#d09a5b", "#b8743e", "#d8b878", "#a86a4a", "#c99a6a"],
  beach: ["#3fb8a0", "#ff9a6a", "#6fc06a", "#e0b040", "#5aa0e0"],
  dragon: ["#7a6aa0", "#5f8a6a", "#9a5a5a", "#6a7a9a", "#a08a5a"],
  road: ["#8a9a6a", "#a08060", "#7a8aa0", "#b0906a", "#6a8a7a"],
};
/** Clothes colours (main, trim) per folk. */
const CLOTH: Record<Folk, [string, string][]> = {
  valley: [
    ["#3f7a2a", "#f0e0b0"],
    ["#7a4a2a", "#e0d0a0"],
  ],
  snow: [
    ["#d83a3a", "#ffffff"],
    ["#2f6fd0", "#ffe060"],
    ["#3a9a5a", "#ffffff"],
  ],
  desert: [
    ["#c8402a", "#f0c040"],
    ["#2a8a9a", "#f0e0c0"],
    ["#8a3a8a", "#f0c040"],
  ],
  beach: [
    ["#ff4f8a", "#ffe040"],
    ["#ffffff", "#2fb0e0"],
    ["#ff8a20", "#ffffff"],
  ],
  dragon: [
    ["#5a3a8a", "#d8b040"],
    ["#8a2a2a", "#d8b040"],
    ["#2a5a8a", "#e0e0e0"],
  ],
  road: [
    ["#8a6a3a", "#e0d0a0"],
    ["#4a6a8a", "#e0d0a0"],
  ],
};
const IRIS = ["#6a3a10", "#2a6a3a", "#2a4a8a", "#7a2a6a", "#8a6a10"];

/** A villager's look, all picked by its seed. */
export function villagerLook(folk: Folk, seed: number, kind?: Species) {
  const species = kind ?? SPECIES[seed % SPECIES.length]!;
  const skins = SKINS[folk];
  const cloths = CLOTH[folk];
  return {
    species,
    skin: skins[Math.floor(seed / 8) % skins.length]!,
    cloth: cloths[Math.floor(seed / 3) % cloths.length]!,
    variant: seed % 2,
    iris: IRIS[Math.floor(seed / 5) % IRIS.length]!,
  };
}

// ---------------------------------------------------------------- heads

export interface Skull {
  /** Cranium radius, centre height (head space), snout length (from the cranium's
   * centre), and the snout tip's half-width and half-height. */
  R: number;
  cy: number;
  L: number;
  w: number;
  h: number;
}

export interface Pal {
  skin: THREE.Color;
  dark: THREE.Color;
  belly: THREE.Color;
  accent: string;
  mouth: string;
  tongue: string;
  claw: string;
  iris: string;
}

/** The skull (round cranium, a snout), its mouth, nostrils and smile; and the jaw. */
export function skullAndJaw(
  head: THREE.Object3D,
  s: Skull,
  p: Pal,
  o: { tip?: string; seed: number },
) {
  const { R, cy, L, w, h } = s;
  const my = cy - 0.25 * R - h * 0.55; // the mouth line
  const tip = o.tip ? new THREE.Color(o.tip) : undefined;
  const sk = new Build().addColored(
    loft(
      [
        { at: [0, cy, -0.85 * R], rx: 0.42 * R, ry: 0.42 * R },
        { at: [0, cy, -0.6 * R], rx: 0.88 * R, ry: 0.86 * R },
        { at: [0, cy, -0.08 * R], rx: R, ry: 0.96 * R },
        { at: [0, cy - 0.05 * R, 0.38 * R], rx: 0.9 * R, ry: 0.8 * R, flat: 0.2 },
        {
          at: [0, cy - 0.18 * R, 0.38 * R + (L - 0.38 * R) * 0.5],
          rx: (0.9 * R + w) / 2,
          ry: (0.8 * R + h) / 2,
          flat: 0.3,
        },
        { at: [0, cy - 0.25 * R, L], rx: w, ry: h, flat: 0.25 },
        { at: [0, cy - 0.25 * R, L + 0.45 * h], rx: 0.45 * w, ry: 0.45 * h },
      ],
      {
        sides: 14,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => {
          if (tip && t > 0.78 && a < 0.5) return tip;
          if (a < -0.9 && t > 0.42) return p.belly;
          return p.skin.clone().lerp(p.dark, mottle(t * 5, a, o.seed) * 0.35);
        },
      },
    ),
  );
  for (const sd of [1, -1]) {
    sk.add(ellipsoid(6, 4), shade(p.dark, 0.85), {
      p: [sd * w * 0.45, cy - 0.25 * R + h * 0.55, L + 0.25 * h],
      s: [0.014, 0.009, 0.011],
    });
    sk.addColored(
      tube(
        [
          [sd * w * 0.75, my + 0.004, L + 0.1 * h],
          [sd * (w + 0.9 * R) * 0.5, my + 0.002, (L + 0.38 * R) * 0.5],
          [sd * 0.86 * R, my + 0.02, 0.2 * R],
          [sd * 0.88 * R, my + 0.05, 0.02],
        ],
        [0.006, 0.007, 0.007, 0.005],
        p.mouth,
        { sides: 5 },
      ),
    );
  }
  sk.add(ellipsoid(10, 6), p.mouth, {
    p: [0, my + 0.005, (L + 0.1 * R) * 0.5],
    s: [Math.min(w, 0.8 * R) * 0.9, 0.025, (L - 0.1 * R) * 0.5],
  });
  head.add(mesh(sk));
  const jaw = new THREE.Group();
  jaw.position.set(0, my, 0.1 * R);
  head.add(jaw);
  const jl = L - 0.1 * R - 0.025;
  jaw.add(
    mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, -0.012, -0.05], rx: 0.82 * R, ry: 0.42 * h + 0.012, sq: 2.4 },
              {
                at: [0, -0.024, jl * 0.5],
                rx: (0.82 * R + w) * 0.5,
                ry: 0.4 * h + 0.01,
                flat: -0.4,
              },
              { at: [0, -0.02, jl], rx: 0.8 * w, ry: 0.35 * h + 0.008, flat: -0.5 },
              { at: [0, -0.012, jl + 0.2 * h], rx: 0.45 * w, ry: 0.22 * h + 0.005 },
            ],
            {
              sides: 12,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (t, a) =>
                a > 0.5 && a < 2.6
                  ? p.mouth
                  : tip && t > 0.75
                    ? tip
                    : a < -0.7 && a > -2.4
                      ? p.belly
                      : p.skin,
            },
          ),
        )
        .add(ellipsoid(8, 5), p.tongue, {
          p: [0, -0.008, jl * 0.5],
          s: [Math.min(w, 0.6 * R) * 0.8, 0.016, jl * 0.38],
        }),
    ),
  );
  return { jaw, mouth: [0, my, L + 0.05] as V3 };
}

export function eyesFor(
  head: THREE.Object3D,
  s: Skull,
  p: Pal,
  big = 1,
  extra: Partial<EyeStyle> = {},
) {
  const R = s.R;
  return buildEyes(head, {
    at: [0.48 * R, s.cy + 0.24 * R, 0.64 * R],
    size: [0.35 * R * big, 0.41 * R * big, 0.29 * R * big],
    yaw: 0.32,
    pitch: -0.05,
    iris: p.iris,
    irisRing: mix(p.iris, "#ffffff", 0.32),
    irisScale: 1.12,
    lid: shade(p.skin, 0.94),
    inward: 0.2,
    lidTilt: 0.04,
    cheek: 0.24,
    brow: {
      color: shade(p.skin, 0.42),
      at: [0.5 * R, s.cy + 0.66 * R * Math.max(1, big * 0.95), 0.72 * R],
      size: [0.3 * R, 0.085 * R, 0.12 * R],
      tilt: -0.1,
    },
    ...extra,
  });
}

// ---------------------------------------------------------------- the kinds

interface Kind {
  stance: Partial<Stance>;
  torsoAt?: V3;
  neckAt: V3;
  headAt: V3;
  headScale: number;
  arms?: (p: Pal, sleeves: { upper: string | null; fore: string | null }) => ArmSpec;
  legs: (p: Pal) => LegSpec;
  frontLegs?: (p: Pal) => LegSpec;
  skull: Skull;
  /** The body's sections (torso space; up the body for bipeds, along it for quads). */
  body: { at: V3; rx: number; ry: number }[];
  /** The neck's loft (neck space, from its base to under the head). */
  neck: { at: V3; r: number }[];
  tail: { at: V3; segs: [number, number, number][]; lift: number[] };
  /** Anchors for the clothes. */
  collar: { on: "torso" | "neck"; at: V3; r: number; tilt: number; upright?: boolean };
  crown: V3;
  belt?: { y: number; rx: number; rz: number; z: number };
  back: V3;
  /** Eyes bigger (1 = normal). */
  eyes: number;
  /** No hats (a crest in the way). */
  noHat?: boolean;
  /** The skull's lighter tip colour (a bill, a beak). */
  tip?: (p: Pal) => string;
  extras?: (rig: PersonRig, p: Pal, head: Build, body: Build, seed: number) => void;
}

const bipedLegs =
  (hip: number, thigh: number, shin: number, r: number, foot: number) =>
  (p: Pal): LegSpec => ({
    hip: [hip, -0.02, 0],
    thigh,
    shin,
    radius: [r, r * 0.74, r * 0.62],
    thighColor: p.skin,
    shinColor: p.skin,
    foot: { len: foot, width: foot * 0.66, color: p.skin, claw: p.claw },
    ankleH: r * 0.62,
  });
const bipedArms =
  (sh: V3, upper: number, fore: number, r: number, hand: number) =>
  (p: Pal, sl: { upper: string | null; fore: string | null }): ArmSpec => ({
    shoulder: sh,
    upper,
    fore,
    radius: [r, r * 0.85, r * 0.75],
    upperColor: sl.upper ? sleeve(sl.upper, p.skin, 0.9) : p.skin,
    foreColor: sl.fore ? sleeve(sl.fore, p.skin, 0.55, shade(sl.fore, 0.8)) : p.skin,
    hand: `#${p.skin.getHexString()}`,
    handSize: hand,
    claws: p.claw,
    hint: [0.7, -0.4, -0.6],
  });
const bipedBody = (w: number, d: number, k = 1): Kind["body"] => [
  { at: [0, -0.06 * k, 0.0], rx: 0.15 * w, ry: 0.13 * d },
  { at: [0, 0.06 * k, 0.02], rx: 0.22 * w, ry: 0.2 * d },
  { at: [0, 0.2 * k, 0.03], rx: 0.23 * w, ry: 0.2 * d },
  { at: [0, 0.33 * k, 0.03], rx: 0.2 * w, ry: 0.17 * d },
  { at: [0, 0.43 * k, 0.05], rx: 0.14 * w, ry: 0.13 * d },
  { at: [0, 0.49 * k, 0.07], rx: 0.09 * w, ry: 0.09 * d },
];
const bipedTail = (r: number, len: number, lift = 0.3): Kind["tail"] => ({
  at: [0, 0.02, -0.15],
  segs: [
    [r, len, r * 0.65],
    [r * 0.65, len * 0.9, r * 0.32],
    [r * 0.32, len * 0.6, r * 0.08],
  ],
  lift: [lift, -0.15, -0.1],
});
const quadLegs =
  (x: number, z: number, thigh: number, shin: number, r: number, front: boolean) =>
  (p: Pal): LegSpec => ({
    hip: [x, -0.04, z],
    thigh,
    shin,
    radius: [r, r * 0.82, r * 0.75],
    thighColor: p.skin,
    shinColor: p.skin,
    foot: { len: r * 2.1, width: r * 1.9, color: p.skin, claw: p.claw, toes: true },
    ankleH: r * 0.6,
    hint: front ? [0.05, 0, -1] : [0.05, 0, 1],
  });

const KINDS: Record<Species, Kind> = {
  parasaur: {
    stance: { hipY: 0.62, stride: 0.42, stoop: 0.12, handRest: [0.27, -0.02, 0.1] },
    neckAt: [0, 0.47, 0.07],
    headAt: [0, 0.09, 0.05],
    headScale: 1,
    arms: bipedArms([0.18, 0.38, 0.06], 0.2, 0.19, 0.058, 0.06),
    legs: bipedLegs(0.13, 0.31, 0.28, 0.1, 0.24),
    skull: { R: 0.18, cy: 0.17, L: 0.37, w: 0.12, h: 0.045 },
    body: bipedBody(0.95, 0.95, 1.05),
    neck: [
      { at: [0, -0.06, -0.01], r: 0.13 },
      { at: [0, 0.04, 0.01], r: 0.115 },
      { at: [0, 0.12, 0.04], r: 0.11 },
    ],
    tail: bipedTail(0.11, 0.28, 0.25),
    collar: { on: "torso", at: [0, 0.48, 0.07], r: 0.12, tilt: 0.25 },
    crown: [0, 0.35, 0.02],
    belt: { y: 0.04, rx: 0.215, rz: 0.2, z: 0.02 },
    back: [0, 0.28, -0.2],
    eyes: 1,
    tip: () => "#e8d49a",
    noHat: true,
    extras(rig, p, head) {
      // The crest: a long tube swept back off the top of the head.
      const acc = new THREE.Color(p.accent);
      head.addColored(
        tube(
          [
            [0, 0.27, -0.02],
            [0, 0.36, -0.14],
            [0, 0.41, -0.3],
            [0, 0.4, -0.45],
            [0, 0.35, -0.55],
          ],
          [0.06, 0.065, 0.055, 0.045, 0.025],
          p.accent,
          {
            sides: 9,
            steps: 3,
            paint: (t, a) =>
              a > 0.6 && a < 2.5
                ? acc.clone().lerp(new THREE.Color("#fff6d8"), 0.25)
                : t > 0.85
                  ? shade(acc, 0.8)
                  : acc,
          },
        ),
      );
      void rig;
    },
  },
  iggy: {
    stance: { hipY: 0.66, stride: 0.44, stoop: 0.16, handRest: [0.3, -0.02, 0.12] },
    neckAt: [0, 0.51, 0.08],
    headAt: [0, 0.09, 0.05],
    headScale: 1,
    arms: bipedArms([0.21, 0.41, 0.06], 0.22, 0.21, 0.072, 0.072),
    legs: bipedLegs(0.15, 0.32, 0.3, 0.12, 0.27),
    skull: { R: 0.18, cy: 0.17, L: 0.38, w: 0.085, h: 0.085 },
    body: bipedBody(1.1, 1.1, 1.1),
    neck: [
      { at: [0, -0.06, -0.01], r: 0.15 },
      { at: [0, 0.04, 0.01], r: 0.135 },
      { at: [0, 0.12, 0.04], r: 0.125 },
    ],
    tail: bipedTail(0.13, 0.32, 0.25),
    collar: { on: "torso", at: [0, 0.53, 0.08], r: 0.14, tilt: 0.25 },
    crown: [0, 0.35, 0.0],
    belt: { y: 0.05, rx: 0.25, rz: 0.23, z: 0.02 },
    back: [0, 0.3, -0.23],
    eyes: 1,
    extras(rig, p, head) {
      // A bump on the nose, and the thumb spikes.
      head.add(ellipsoid(8, 6), shade(p.skin, 0.9), { p: [0, 0.18, 0.47], s: [0.05, 0.03, 0.06] });
      for (const arm of rig.arms)
        arm.hand.add(
          mesh(
            new Build().add(cone(0.022, 0.09, 6), "#f4ead0", {
              p: [-arm.side * 0.05, 0.04, 0.03],
              r: [-0.6, 0, arm.side * 0.9],
            }),
          ),
        );
    },
  },
  pachy: {
    stance: { hipY: 0.52, stride: 0.36, stoop: 0.1, handRest: [0.28, -0.02, 0.1] },
    neckAt: [0, 0.46, 0.07],
    headAt: [0, 0.1, 0.05],
    headScale: 1.05,
    arms: bipedArms([0.21, 0.38, 0.06], 0.19, 0.18, 0.068, 0.066),
    legs: bipedLegs(0.14, 0.25, 0.22, 0.11, 0.23),
    skull: { R: 0.19, cy: 0.16, L: 0.27, w: 0.1, h: 0.075 },
    body: bipedBody(1.15, 1.15, 0.98),
    neck: [
      { at: [0, -0.06, -0.01], r: 0.12 },
      { at: [0, 0.05, 0.01], r: 0.11 },
      { at: [0, 0.12, 0.03], r: 0.105 },
    ],
    tail: bipedTail(0.12, 0.26, 0.3),
    collar: { on: "torso", at: [0, 0.47, 0.07], r: 0.135, tilt: 0.2 },
    crown: [0, 0.39, -0.03],
    belt: { y: 0.05, rx: 0.255, rz: 0.235, z: 0.02 },
    back: [0, 0.28, -0.22],
    eyes: 1.05,
    extras(_rig, p, head) {
      head.add(ellipsoid(16, 10), shade(p.skin, 1.22), {
        p: [0, 0.28, -0.03],
        s: [0.19, 0.15, 0.19],
      });
      for (let k = 0; k < 9; k++) {
        const a = ((k - 4) / 8) * Math.PI * 1.25 + Math.PI;
        head.add(gem(1), shade(p.skin, 0.7), {
          p: [Math.sin(a) * 0.19, 0.21, -0.03 + Math.cos(a) * 0.18],
          s: [0.025, 0.028, 0.025],
        });
      }
    },
  },
  compy: {
    stance: {
      hipY: 0.34,
      stride: 0.24,
      lift: 0.09,
      stoop: 0.05,
      handRest: [0.2, -0.0, 0.1],
      breath: 1.4,
      sway: 1.5,
      blinkEvery: 2.6,
      curious: 0.8,
      response: 1.4,
      glance: 2.2,
    },
    neckAt: [0, 0.33, 0.06],
    headAt: [0, 0.08, 0.04],
    headScale: 1.12,
    arms: bipedArms([0.14, 0.26, 0.05], 0.13, 0.12, 0.045, 0.048),
    legs: bipedLegs(0.09, 0.17, 0.15, 0.07, 0.17),
    skull: { R: 0.19, cy: 0.17, L: 0.24, w: 0.075, h: 0.06 },
    body: bipedBody(0.72, 0.75, 0.68),
    neck: [
      { at: [0, -0.04, -0.01], r: 0.075 },
      { at: [0, 0.04, 0.01], r: 0.07 },
      { at: [0, 0.1, 0.03], r: 0.07 },
    ],
    tail: bipedTail(0.08, 0.24, 0.35),
    collar: { on: "torso", at: [0, 0.33, 0.06], r: 0.09, tilt: 0.2 },
    crown: [0, 0.36, 0.0],
    belt: { y: 0.03, rx: 0.17, rz: 0.15, z: 0.02 },
    back: [0, 0.2, -0.14],
    eyes: 1.3,
    extras(_rig, p, head) {
      // A little crest of three scales on top.
      for (let k = 0; k < 3; k++)
        head.add(ellipsoid(8, 6), p.accent, {
          p: [0, 0.35 - k * 0.02, -0.02 - k * 0.07],
          s: [0.02, 0.05 - k * 0.01, 0.035],
          r: [-0.4 - k * 0.2, 0, 0],
        });
    },
  },
  ovi: {
    stance: {
      hipY: 0.52,
      stride: 0.38,
      lift: 0.1,
      stoop: 0.18,
      handRest: [0.24, 0.0, 0.12],
      curious: 0.6,
    },
    neckAt: [0, 0.44, 0.07],
    headAt: [0, 0.12, 0.07],
    headScale: 0.98,
    arms: bipedArms([0.16, 0.35, 0.05], 0.18, 0.17, 0.05, 0.055),
    legs: bipedLegs(0.11, 0.27, 0.25, 0.085, 0.22),
    skull: { R: 0.17, cy: 0.16, L: 0.24, w: 0.06, h: 0.06 },
    body: bipedBody(0.88, 0.92, 0.95),
    neck: [
      { at: [0, -0.06, -0.01], r: 0.11 },
      { at: [0, 0.05, 0.03], r: 0.09 },
      { at: [0, 0.14, 0.06], r: 0.085 },
    ],
    tail: bipedTail(0.1, 0.24, 0.35),
    collar: { on: "torso", at: [0, 0.44, 0.07], r: 0.11, tilt: 0.25 },
    crown: [0, 0.33, 0.02],
    belt: { y: 0.04, rx: 0.2, rz: 0.19, z: 0.02 },
    back: [0, 0.27, -0.19],
    eyes: 1.1,
    tip: () => "#f0a030",
    extras(rig, p, head, body) {
      // The casque: a rounded crest on top; a tuft behind.
      head.add(ellipsoid(12, 8), p.accent, { p: [0, 0.32, 0.03], s: [0.025, 0.1, 0.11] });
      for (let k = -1; k <= 1; k++)
        head.addColored(feather(0.14, 0.03, p.accent, shade(p.accent, 1.3)), {
          p: [k * 0.03, 0.24, -0.12],
          r: [-1.0, k * 0.4, 0],
        });
      // Feathers along the arms (little wings), and a fan on the tail.
      for (const arm of rig.arms) {
        const b = new Build();
        for (let k = 0; k < 4; k++)
          b.addColored(feather(0.16 - k * 0.015, 0.035, shade(p.skin, 0.85), p.accent, "#2a2a2a"), {
            p: [arm.side * 0.04, -0.02, 0.04 + k * 0.045],
            r: [Math.PI / 2 + 0.8, 0, arm.side * (Math.PI / 2 + 0.3)],
          });
        arm.fore.add(mesh(b));
      }
      const tip = rig.tail[rig.tail.length - 1]!;
      const tb = new Build();
      for (let k = -2; k <= 2; k++)
        tb.addColored(feather(0.28, 0.06, shade(p.skin, 0.8), p.accent, "#2a2a2a"), {
          p: [0, 0, -0.06],
          r: [-Math.PI / 2 + 0.25 + k * 0.28, Math.PI / 2, 0],
        });
      tip.add(mesh(tb));
      void body;
    },
  },
  ankylo: {
    stance: { quad: true, hipY: 0.42, stride: 0.34, lift: 0.08, sway: 0.6 },
    neckAt: [0, 0.12, 0.62],
    headAt: [0, 0.0, 0.14],
    headScale: 1,
    legs: quadLegs(0.27, 0, 0.21, 0.19, 0.1, false),
    frontLegs: quadLegs(0.26, 0.5, 0.2, 0.18, 0.095, true),
    skull: { R: 0.16, cy: 0.06, L: 0.2, w: 0.1, h: 0.07 },
    body: [
      { at: [0, 0.05, -0.42], rx: 0.22, ry: 0.18 },
      { at: [0, 0.1, -0.22], rx: 0.42, ry: 0.3 },
      { at: [0, 0.12, 0.12], rx: 0.46, ry: 0.32 },
      { at: [0, 0.1, 0.42], rx: 0.38, ry: 0.27 },
      { at: [0, 0.08, 0.6], rx: 0.22, ry: 0.18 },
    ],
    neck: [
      { at: [0, 0, -0.06], r: 0.15 },
      { at: [0, 0.0, 0.06], r: 0.13 },
      { at: [0, 0.0, 0.14], r: 0.12 },
    ],
    tail: {
      at: [0, 0.08, -0.42],
      segs: [
        [0.12, 0.26, 0.08],
        [0.08, 0.26, 0.05],
        [0.05, 0.22, 0.04],
      ],
      lift: [-0.15, 0.05, 0.05],
    },
    collar: { on: "neck", at: [0, 0.0, 0.0], r: 0.16, tilt: -1.3 },
    crown: [0, 0.22, 0.02],
    back: [0, 0.36, 0.05],
    eyes: 1.1,
    extras(rig, p, head, body) {
      // The armour: rows of knobs down the back and sides.
      for (let row = -2; row <= 2; row++)
        for (let k = 0; k < 5; k++) {
          const z = -0.32 + k * 0.2;
          const a = row * 0.42;
          const rx = 0.44 - Math.abs(z - 0.08) * 0.25;
          body.add(cone(0.06 - Math.abs(row) * 0.008, 0.11, 6), shade(p.skin, 0.66), {
            p: [Math.sin(a) * rx, 0.12 + Math.cos(a) * 0.3 * (1 - Math.abs(z - 0.08) * 0.4), z],
            r: [0, 0, -a],
          });
        }
      // Plates on the head, horns at its back corners.
      head.add(ellipsoid(10, 6), shade(p.skin, 0.75), {
        p: [0, 0.17, -0.02],
        s: [0.13, 0.04, 0.12],
      });
      for (const s of [1, -1])
        head.add(cone(0.03, 0.08, 6), "#f0e4c8", {
          p: [s * 0.14, 0.12, -0.1],
          r: [0, 0, -s * 1.2],
        });
      // The club on the tail.
      const tip = rig.tail[rig.tail.length - 1]!;
      tip.add(
        mesh(
          new Build()
            .add(ellipsoid(10, 8), shade(p.skin, 0.7), { p: [0, 0, -0.24], s: [0.13, 0.08, 0.1] })
            .add(gem(1), shade(p.skin, 0.6), { p: [0.1, 0, -0.24], s: 0.045 })
            .add(gem(1), shade(p.skin, 0.6), { p: [-0.1, 0, -0.24], s: 0.045 }),
        ),
      );
    },
  },
  trike: {
    stance: { quad: true, hipY: 0.48, stride: 0.38, lift: 0.08, sway: 0.6 },
    neckAt: [0, 0.16, 0.6],
    headAt: [0, 0.0, 0.12],
    headScale: 1,
    legs: quadLegs(0.25, 0, 0.25, 0.22, 0.105, false),
    frontLegs: quadLegs(0.24, 0.48, 0.24, 0.21, 0.1, true),
    skull: { R: 0.2, cy: 0.04, L: 0.3, w: 0.08, h: 0.09 },
    body: [
      { at: [0, 0.06, -0.4], rx: 0.22, ry: 0.2 },
      { at: [0, 0.12, -0.2], rx: 0.38, ry: 0.34 },
      { at: [0, 0.14, 0.12], rx: 0.41, ry: 0.36 },
      { at: [0, 0.13, 0.42], rx: 0.34, ry: 0.3 },
      { at: [0, 0.13, 0.6], rx: 0.2, ry: 0.2 },
    ],
    neck: [
      { at: [0, 0, -0.06], r: 0.16 },
      { at: [0, 0.0, 0.05], r: 0.15 },
      { at: [0, 0.0, 0.12], r: 0.14 },
    ],
    tail: {
      at: [0, 0.1, -0.4],
      segs: [
        [0.13, 0.26, 0.08],
        [0.08, 0.26, 0.04],
        [0.04, 0.18, 0.01],
      ],
      lift: [-0.2, 0.05, 0.05],
    },
    collar: { on: "neck", at: [0, 0.0, 0.0], r: 0.17, tilt: -1.3 },
    crown: [0, 0.27, 0.04],
    back: [0, 0.5, 0.05],
    eyes: 1.05,
    tip: () => "#c8b080",
    extras(_rig, p, head) {
      // The frill: a broad scalloped shield behind the head, knobs round its edge.
      const fr = new THREE.Color(p.accent);
      head.add(
        new THREE.CylinderGeometry(0.36, 0.3, 0.035, 18),
        (q) => {
          const r = Math.hypot(q.x, q.z);
          return r > 0.27 ? shade(fr, 0.8) : fr.clone().lerp(p.skin, 0.25);
        },
        { p: [0, 0.22, -0.16], r: [1.15, 0, 0] },
      );
      for (let k = 0; k < 11; k++) {
        const b = ((k - 5) / 10) * Math.PI * 1.2;
        const rr = 0.35;
        head.add(gem(1), "#f4ead0", {
          p: [
            Math.sin(b) * rr,
            0.22 + Math.cos(b) * rr * Math.sin(1.15),
            -0.16 - Math.cos(b) * rr * Math.cos(1.15),
          ],
          s: 0.03,
        });
      }
      // Three horns: two over the eyes, one on the nose.
      for (const s of [1, -1])
        head.addColored(
          tube(
            [
              [s * 0.1, 0.2, 0.08],
              [s * 0.12, 0.33, 0.2],
              [s * 0.12, 0.38, 0.34],
            ],
            [0.035, 0.022, 0.004],
            "#f4ead0",
            { sides: 7, steps: 2 },
          ),
        );
      head.add(cone(0.03, 0.09, 7), "#f4ead0", { p: [0, 0.07, 0.31], r: [0.5, 0, 0] });
    },
  },
  sauro: {
    stance: { quad: true, hipY: 0.5, stride: 0.36, lift: 0.07, sway: 0.5, lookReach: 1.2 },
    neckAt: [0, 0.22, 0.48],
    headAt: [0, 0.72, 0.3],
    headScale: 1,
    legs: quadLegs(0.21, 0, 0.25, 0.23, 0.095, false),
    frontLegs: quadLegs(0.2, 0.4, 0.25, 0.23, 0.09, true),
    skull: { R: 0.13, cy: 0.06, L: 0.18, w: 0.07, h: 0.055 },
    body: [
      { at: [0, 0.08, -0.38], rx: 0.2, ry: 0.2 },
      { at: [0, 0.15, -0.18], rx: 0.34, ry: 0.32 },
      { at: [0, 0.17, 0.1], rx: 0.36, ry: 0.33 },
      { at: [0, 0.17, 0.36], rx: 0.28, ry: 0.27 },
      { at: [0, 0.2, 0.5], rx: 0.17, ry: 0.17 },
    ],
    neck: [
      { at: [0, -0.06, -0.1], r: 0.19 },
      { at: [0, 0.12, 0.06], r: 0.14 },
      { at: [0, 0.38, 0.12], r: 0.105 },
      { at: [0, 0.6, 0.2], r: 0.088 },
      { at: [0, 0.72, 0.29], r: 0.08 },
    ],
    tail: {
      at: [0, 0.12, -0.38],
      segs: [
        [0.13, 0.32, 0.08],
        [0.08, 0.32, 0.04],
        [0.04, 0.3, 0.008],
      ],
      lift: [-0.25, 0.08, 0.08],
    },
    collar: { on: "neck", at: [0, 0.2, 0.1], r: 0.14, tilt: 0.3, upright: true },
    crown: [0, 0.2, 0.0],
    back: [0, 0.52, 0.0],
    eyes: 1.15,
  },
};

// ---------------------------------------------------------------- clothes

function dress(
  rig: PersonRig,
  k: Kind,
  folk: Folk,
  cloth: [string, string],
  v: number,
  quad: boolean,
  builds: { torso: Build; neck: Build; head: Build },
  seed: number,
) {
  const [main, trim] = cloth;
  const col = k.collar;
  const cb = col.on === "torso" ? builds.torso : builds.neck;
  // (A collar round a neck that runs forward stands up; round one that rises, it lies flat.)
  const qc = quad && !col.upright;
  const hb = builds.head;
  const S = k.skull;
  // A ring round the neck (scarves, collars, leis), tilted to sit on the shoulders.
  const ring = (r: number, th: number, paint: (t: number) => string, dy = 0) => {
    cb.addColored(
      loft(
        Array.from({ length: 15 }, (_, i) => {
          const a = (i / 14) * Math.PI * 2;
          const at: V3 = qc
            ? [Math.sin(a) * r, col.at[1] + Math.cos(a) * r, col.at[2] + dy]
            : [
                Math.sin(a) * r,
                col.at[1] + dy - Math.cos(a) * r * 0.25,
                col.at[2] + Math.cos(a) * r,
              ];
          return { at, rx: th, ry: th * 1.05 };
        }),
        { sides: 7, steps: 2, paint: (t) => paint(t) },
      ),
    );
  };
  const around = (n: number, r: number, f: (p: V3, a: number, i: number) => void, dy = 0) => {
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      let p: V3 = [
        Math.sin(a) * r,
        col.at[1] + dy - Math.cos(a) * r * 0.25,
        col.at[2] + Math.cos(a) * r,
      ];
      if (qc) {
        // (Round a neck that runs forward: the ring stands up.)
        p = [Math.sin(a) * r, col.at[1] + Math.cos(a) * r, col.at[2] + dy];
      }
      f(p, a, i);
    }
  };
  // A hat on the crown.
  const crown = k.crown;
  const R = S.R;
  if (folk === "valley") {
    // A ruff of leaves round the neck, two layers, bright against the skin.
    for (const layer of [0, 1])
      around(
        9,
        col.r * (1.0 + layer * 0.08),
        (p, a, i) => {
          const out: V3 = qc
            ? [Math.sin(a), Math.cos(a), 0.35]
            : [Math.sin(a) * 0.9, -0.75, Math.cos(a) * 0.9];
          const q = new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 1, 0),
            new THREE.Vector3(...out).normalize(),
          );
          const e = new THREE.Euler().setFromQuaternion(q);
          const c = layer
            ? mix(main, "#8ad048", 0.55)
            : i % 2
              ? "#5aa83a"
              : mix(main, "#7ac040", 0.4);
          cb.addColored(leaf(0.2 - layer * 0.04, 0.07, c, "#d8f0a0"), {
            p: [p[0], p[1] + layer * 0.02, p[2]],
            r: [e.x, e.y, e.z],
          });
        },
        layer ? 0.01 : 0,
      );
    if (v === 1)
      around(
        12,
        col.r * 0.92,
        (p, _a, i) =>
          cb.add(ellipsoid(6, 4), i % 3 ? "#fff4e8" : "#f0b8a0", {
            p: [p[0], p[1] - (qc ? 0 : 0.06), p[2]],
            s: 0.022,
          }),
        qc ? 0.05 : -0.04,
      );
    else
      flower(
        hb,
        [R * 0.75, crown[1] - 0.05, -0.02],
        [1, 0.4, 0.2],
        0.03,
        trim === "#f0e0b0" ? "#ffffff" : "#ffd040",
      );
  } else if (folk === "snow") {
    ring(col.r * 1.02, quad ? 0.06 : 0.05, (t) => (Math.floor(t * 14) % 2 ? main : trim));
    // The scarf's end hanging.
    if (!quad)
      cb.addColored(
        loft(
          [
            {
              at: [col.r * 0.55, col.at[1] - 0.02, col.at[2] + col.r * 0.85],
              rx: 0.045,
              ry: 0.016,
            },
            { at: [col.r * 0.65, col.at[1] - 0.12, col.at[2] + col.r * 1.1], rx: 0.045, ry: 0.016 },
            { at: [col.r * 0.7, col.at[1] - 0.22, col.at[2] + col.r * 1.15], rx: 0.045, ry: 0.016 },
          ],
          {
            sides: 6,
            steps: 2,
            up: [0, 0, 1],
            capStart: true,
            capEnd: true,
            paint: (t) => (Math.floor(t * 6) % 2 ? main : trim),
          },
        ),
      );
    if (v === 0) {
      hb.add(
        new THREE.SphereGeometry(1, 14, 8, 0, Math.PI * 2, 0, Math.PI * 0.5),
        (p) => (Math.floor(p.y * 6 + 6) % 2 ? main : shade(main, 0.82)),
        {
          p: [crown[0], crown[1] - R * 0.35, crown[2]],
          s: [R * 0.95, R * 0.75, R * 0.95],
        },
      );
      hb.add(new THREE.TorusGeometry(R * 0.93, R * 0.14, 6, 16), trim, {
        p: [crown[0], crown[1] - R * 0.33, crown[2]],
        r: [Math.PI / 2, 0, 0],
      });
      hb.add(gem(1), trim, { p: [crown[0], crown[1] + R * 0.45, crown[2]], s: R * 0.3 });
    } else {
      for (const s of [1, -1])
        hb.add(gem(1), trim, {
          p: [s * R * 0.95, S.cy + R * 0.1, -R * 0.15],
          s: [R * 0.22, R * 0.3, R * 0.3],
        });
      hb.addColored(
        tube(
          [
            [R * 0.9, S.cy + R * 0.3, -R * 0.15],
            [0, crown[1] + R * 0.05, -R * 0.15],
            [-R * 0.9, S.cy + R * 0.3, -R * 0.15],
          ],
          R * 0.06,
          main,
          { sides: 5, steps: 3 },
        ),
      );
    }
  } else if (folk === "desert") {
    // A straw hat: a wide brim, a woven crown, a band in the folk's colour.
    const straw = (p: THREE.Vector3) =>
      Math.sin(Math.atan2(p.x, p.z) * 24 + p.y * 40) > 0.3 ? "#e8c870" : "#d8b058";
    if (!k.noHat) {
      hb.add(new THREE.CylinderGeometry(R * 1.75, R * 1.85, 0.02, 20), straw, {
        p: [crown[0], crown[1] - R * 0.15, crown[2]],
      });
      hb.add(new THREE.CylinderGeometry(R * 0.6, R * 0.85, R * 0.6, 14), straw, {
        p: [crown[0], crown[1] + R * 0.15, crown[2]],
      });
      hb.add(new THREE.CylinderGeometry(R * 0.87, R * 0.87, R * 0.16, 14), main, {
        p: [crown[0], crown[1] - R * 0.05, crown[2]],
      });
    } else flower(hb, [R * 0.75, crown[1] - 0.05, -0.02], [1, 0.4, 0.2], 0.04, trim);
    if (v === 1) {
      const pon = woven(main, [trim, shade(main, 0.6), trim], 0.22);
      if (!quad)
        builds.torso.addColored(
          loft(
            [
              { at: [0, col.at[1] + 0.02, col.at[2]], rx: col.r * 1.05, ry: col.r * 1.0 },
              { at: [0, col.at[1] - 0.08, col.at[2] - 0.01], rx: col.r * 2.0, ry: col.r * 1.7 },
              { at: [0, col.at[1] - 0.2, col.at[2] - 0.02], rx: col.r * 2.3, ry: col.r * 1.95 },
              { at: [0, col.at[1] - 0.24, col.at[2] - 0.02], rx: col.r * 2.32, ry: col.r * 1.97 },
            ],
            { sides: 16, steps: 2, up: [0, 0, 1], paint: (t, a) => pon(1 - t, a) },
          ),
        );
      else saddle(builds.torso, k, pon);
    }
  } else if (folk === "beach") {
    // A lei.
    around(10, col.r * 1.02, (p, a, i) => {
      const n: V3 = qc
        ? [Math.sin(a), Math.cos(a), 0.3]
        : [Math.sin(a) * 0.7, 0.6, Math.cos(a) * 0.7];
      flower(cb, p, n, 0.03, [main, trim, "#ffffff"][i % 3]!, "#e89a20");
    });
    if (v === 1 && !k.noHat) {
      hb.add(new THREE.CylinderGeometry(R * 1.7, R * 1.95, 0.02, 20), main, {
        p: [crown[0], crown[1] - R * 0.18, crown[2]],
        r: [0.12, 0, 0],
      });
      hb.add(new THREE.SphereGeometry(1, 14, 7, 0, Math.PI * 2, 0, Math.PI * 0.5), main, {
        p: [crown[0], crown[1] - R * 0.2, crown[2]],
        s: [R * 0.8, R * 0.6, R * 0.8],
      });
      hb.add(new THREE.TorusGeometry(R * 0.8, R * 0.08, 5, 16), trim, {
        p: [crown[0], crown[1] - R * 0.12, crown[2]],
        r: [Math.PI / 2, 0, 0],
      });
    } else flower(hb, [R * 0.75, crown[1] - 0.04, -0.02], [1, 0.4, 0.2], 0.04, main);
  } else if (folk === "dragon") {
    if (!quad) {
      // A hooded tunic: the tunic over the body, a belt, the hood down behind the neck.
      const secs = k.body.slice(1, 5).map((s, i) => ({
        at: [s.at[0], s.at[1] - (i === 0 ? 0.1 : 0), s.at[2]] as V3,
        rx: s.rx * 1.07 + (i === 0 ? 0.03 : 0),
        ry: s.ry * 1.07 + (i === 0 ? 0.03 : 0),
      }));
      builds.torso.addColored(
        loft(secs, {
          sides: 14,
          steps: 2,
          up: [0, 0, 1],
          capEnd: true,
          paint: (t, a) => (t < 0.08 ? trim : Math.abs(a - Math.PI / 2) < 0.12 ? trim : main),
        }),
      );
      const b = k.belt!;
      builds.torso.add(new THREE.TorusGeometry(1, 0.06, 5, 16), trim, {
        p: [0, b.y + 0.04, b.z],
        s: [b.rx * 1.12, b.rz * 1.12, 0.35],
        r: [Math.PI / 2, 0, 0],
      });
      builds.torso.addColored(
        loft(
          [
            { at: [0, col.at[1] - 0.02, col.at[2] - col.r * 0.9], rx: col.r * 1.2, ry: 0.05 },
            { at: [0, col.at[1] - 0.08, col.at[2] - col.r * 1.35], rx: col.r * 1.1, ry: 0.06 },
            { at: [0, col.at[1] - 0.16, col.at[2] - col.r * 1.45], rx: col.r * 0.6, ry: 0.04 },
          ],
          {
            sides: 10,
            steps: 2,
            capStart: true,
            capEnd: true,
            paint: (t) => (t < 0.15 ? trim : main),
          },
        ),
      );
    } else saddle(builds.torso, k, () => main, trim);
    if (v === 1 && !k.noHat) {
      hb.add(cone(R * 0.7, R * 1.1, 12), main, {
        p: [crown[0], crown[1] + R * 0.25, crown[2] - R * 0.1],
        r: [-0.25, 0, 0],
      });
      hb.add(new THREE.TorusGeometry(R * 0.68, R * 0.08, 5, 14), trim, {
        p: [crown[0], crown[1] - R * 0.25, crown[2] - R * 0.02],
        r: [Math.PI / 2 - 0.25, 0, 0],
      });
    }
  } else {
    // On the road: a traveller's pack and a bedroll.
    const bk = k.back;
    const pk = new Build().addColored(
      backpack(0.3, 0.32, 0.16, { bag: main, flap: shade(main, 0.75), buckle: "#d8b040" }),
    );
    builds.torso.addColored(pk.build(), {
      p: quad ? [bk[0], bk[1] + 0.08, bk[2]] : [bk[0], bk[1], bk[2] - 0.04],
      r: quad ? [-Math.PI / 2, 0, 0] : [0, Math.PI, 0],
    });
    builds.torso.addColored(bedroll(0.36, 0.06, { roll: trim, strap: "#6a4426" }), {
      p: quad ? [bk[0], bk[1] + 0.2, bk[2] - 0.15] : [bk[0], bk[1] + 0.2, bk[2] - 0.06],
    });
    if (!quad)
      for (const s of [1, -1])
        builds.torso.addColored(
          tube(
            [
              [s * 0.1, col.at[1] - 0.02, col.at[2] - 0.08],
              [s * 0.15, col.at[1] - 0.1, col.at[2] + 0.1],
              [s * 0.15, col.at[1] - 0.25, col.at[2] + 0.12],
            ],
            0.014,
            "#6a4426",
            { sides: 4 },
          ),
        );
  }

  // Something to wear on the body, by kingdom (two-legged folk).
  if (!quad && k.belt) {
    const bt = k.belt;
    const at = (a: number, r = 1, dy = 0): V3 => [
      Math.sin(a) * bt.rx * r,
      bt.y + dy,
      bt.z + Math.cos(a) * bt.rz * r,
    ];
    const band = (color: string, th = 0.022, dy = 0, r = 1.04) =>
      builds.torso.addColored(
        loft(
          Array.from({ length: 17 }, (_, i) => ({
            at: at((i / 16) * Math.PI * 2, r, dy),
            rx: th,
            ry: th * 1.4,
          })),
          { sides: 6, steps: 2, paint: () => color },
        ),
      );
    if (folk === "valley") {
      // A skirt of big leaves round the hips, on a vine.
      band("#4a7a2a", 0.018);
      for (let i = 0; i < 14; i++) {
        const a = (i / 14) * Math.PI * 2;
        const out = new THREE.Vector3(Math.sin(a) * 0.35, -1, Math.cos(a) * 0.35).normalize();
        const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), out);
        const e = new THREE.Euler().setFromQuaternion(q);
        builds.torso.addColored(
          leaf(0.17, 0.065, i % 2 ? "#4f9a34" : mix(main, "#6aaa3a", 0.5), "#c8ec90"),
          { p: at(a, 1.06, 0.0), r: [e.x, e.y, e.z] },
        );
      }
    } else if (folk === "beach") {
      // A grass skirt on a bright waistband.
      band(main, 0.022);
      for (let i = 0; i < 22; i++) {
        const a = (i / 22) * Math.PI * 2;
        const p0 = at(a, 1.05);
        builds.torso.addColored(
          tube(
            [
              p0,
              [p0[0] * 1.12, p0[1] - 0.12, p0[2] * 1.1],
              [p0[0] * 1.18, p0[1] - 0.24, p0[2] * 1.15],
            ],
            [0.016, 0.012, 0.003],
            i % 3 ? "#d8b860" : "#c09040",
            { sides: 4, steps: 2 },
          ),
        );
      }
    } else if (folk === "snow") {
      // A knitted jumper, striped, its hem rolled.
      const secs = k.body.slice(1, 5).map((b, i) => ({
        at: [b.at[0], b.at[1] - (i === 0 ? 0.07 : 0), b.at[2]] as V3,
        rx: b.rx * 1.06 + (i === 0 ? 0.02 : 0),
        ry: b.ry * 1.06 + (i === 0 ? 0.02 : 0),
      }));
      builds.torso.addColored(
        loft(secs, {
          sides: 14,
          steps: 5,
          up: [0, 0, 1],
          capEnd: true,
          paint: (t, a) =>
            t < 0.1 || (t > 0.42 && t < 0.52)
              ? trim
              : Math.abs(((a * 4) / Math.PI) % 1) < 0.5 && t > 0.2 && t < 0.4
                ? shade(main, 0.85)
                : main,
        }),
      );
    } else if (folk === "desert" && v === 0) {
      // A sash, knotted at the side, its ends hanging.
      band(main, 0.02, 0.03, 1.03);
      const side = at(1.2, 1.08, 0.03);
      builds.torso.add(ellipsoid(8, 6), trim, { p: side, s: [0.04, 0.035, 0.04] });
      builds.torso.addColored(
        tube(
          [
            side,
            [side[0] * 1.05, side[1] - 0.12, side[2] * 1.05],
            [side[0] * 1.1, side[1] - 0.22, side[2]],
          ],
          0.022,
          main,
          {
            sides: 5,
            steps: 2,
          },
        ),
      );
    } else if (folk === "road") {
      // A belt with a pouch.
      band("#6a4426", 0.02);
      builds.torso.add(new THREE.BoxGeometry(0.09, 0.08, 0.05), shade(main, 0.8), {
        p: at(-1.1, 1.08, -0.03),
        r: [0, -1.1, 0],
      });
    }
  }
  void rig;
  void seed;
}

/** A saddle blanket over a four-legged one's back. */
function saddle(
  b: Build,
  k: Kind,
  paint: (t: number, a: number) => THREE.Color | string,
  edge?: string,
) {
  const top = k.back;
  b.addColored(
    loft(
      [
        { at: [0, top[1] - 0.06, top[2] - 0.26], rx: 0.36, ry: 0.06 },
        { at: [0, top[1], top[2]], rx: 0.4, ry: 0.07 },
        { at: [0, top[1] - 0.06, top[2] + 0.26], rx: 0.36, ry: 0.06 },
      ],
      {
        sides: 10,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (edge && Math.abs(Math.cos(a)) > 0.92 ? edge : paint(t, a)),
      },
    ),
  );
}

// ---------------------------------------------------------------- the builder

export function buildFolk(folk: Folk, seed: number, kind?: Species): PersonRig {
  const look = villagerLook(folk, seed, kind);
  const k = KINDS[look.species];
  const quad = FOURS.has(look.species);
  const skin = new THREE.Color(look.skin);
  const r = seeded(seed * 13 + 5);
  const p: Pal = {
    skin,
    dark: new THREE.Color(shade(look.skin, 0.68)),
    belly: new THREE.Color(mix(shade(look.skin, 1.55), "#fff0d0", 0.25)),
    accent: mix(look.cloth[0], shade(look.skin, 0.6), 0.35 + r() * 0.2),
    mouth: "#6a2430",
    tongue: "#e07088",
    claw: "#3a3028",
    iris: look.iris,
  };
  // (The dragon folk's tunics have sleeves.)
  const sleeves =
    (folk === "dragon" || folk === "snow") && !quad
      ? { upper: look.cloth[0], fore: look.cloth[0] }
      : { upper: null, fore: null };
  const rig = skeleton({
    name: `Villager ${look.species}`,
    stance: { ...k.stance, glance: k.stance.glance ?? 3 + r() * 2 },
    torsoAt: k.torsoAt,
    neckAt: k.neckAt,
    headAt: k.headAt,
    arms: k.arms?.(p, sleeves),
    legs: k.legs(p),
    frontLegs: k.frontLegs?.(p),
  });
  // The body.
  const torso = new Build().addColored(
    loft(
      k.body.map((s) => ({ at: s.at, rx: s.rx, ry: s.ry })),
      {
        sides: 14,
        steps: 2,
        up: quad ? [0, 1, 0] : [0, 0, 1],
        capStart: true,
        capEnd: true,
        paint: (t, a) => {
          const front = quad ? a < -0.7 : Math.abs(a - Math.PI / 2) < 0.8;
          if (front) return Math.sin(t * 40) > 0.75 ? shade(p.belly, 0.92) : p.belly;
          // Darker spots along the back.
          const back = quad ? a > 0.6 && a < 2.5 : Math.abs(a + Math.PI / 2) < 1;
          if (back && mottle(t * 9, a * 2, seed) > 0.72) return p.dark;
          return skin.clone().lerp(p.dark, mottle(t * 4, a, seed) * 0.3);
        },
      },
    ),
  );
  const neckB = new Build().addColored(
    loft(
      k.neck.map((n) => ({ at: n.at, rx: n.r, ry: n.r })),
      {
        sides: 11,
        steps: 2,
        up: quad ? [0, 1, 0] : [0, 0, 1],
        paint: (_t, a) => ((quad ? a < -0.8 : Math.abs(a - Math.PI / 2) < 0.7) ? p.belly : skin),
      },
    ),
  );
  // The head.
  rig.head.scale.setScalar(k.headScale);
  const headB = new Build();
  const { jaw, mouth } = skullAndJaw(rig.head, k.skull, p, { tip: k.tip?.(p), seed });
  const eyes = eyesFor(rig.head, k.skull, p, k.eyes);
  rig.face = { ...eyes, jaw, jawOpen: 0.38 };
  rig.stance.mouth = mouth;
  // The tail.
  rig.tail = buildTail(rig.hips, k.tail.at, k.tail.segs, k.tail.lift, (_seg, t, a) =>
    a < -1.0 ? p.belly : skin.clone().lerp(p.dark, mottle(t * 3, a, seed) * 0.35),
  );
  k.extras?.(rig, p, headB, torso, seed);
  dress(rig, k, folk, look.cloth, look.variant, quad, { torso, neck: neckB, head: headB }, seed);
  rig.torso.add(mesh(torso));
  rig.neck.add(mesh(neckB));
  if (!headB.empty) rig.head.add(mesh(headB));
  return rig;
}
