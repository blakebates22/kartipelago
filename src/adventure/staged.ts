/**
 * Staged scenes (Blake, Oct 26: in-game cutscenes): a story scene played out in the 3D
 * world itself, in an overworld region, instead of over a still picture. The cast stand
 * on their marks (racers in their karts, villagers, the dragon), the camera moves and
 * cuts with each line, and the big moments have their effects (a dragon over the sun,
 * fire, the screen shaking). The lines are the scene's own (scenes.ts); a staged scene
 * says only where everyone is and what the camera does for each.
 *
 * Positions are game coordinates (x, z; heading 0 faces +z); heights come from the
 * ground. Cameras: `from` and `to` (where it moves, over the line), looking from `look`
 * to `lookTo`; heights are over the ground at that spot.
 */
import type { RacerId } from "../render/racers/designs";
import type { Folk, Species } from "../render/villager";
import { REGIONS } from "../overworld/regions";
import { KINGDOMS } from "./data";

export type V2 = [number, number];
export type V3 = [number, number, number];

export type ActorSpec =
  | { kind: "racer"; look: RacerId | "you"; at: V2; heading: number }
  | { kind: "villager"; folk: Folk; seed: number; species?: Species; at: V2; heading: number }
  | {
      kind: "dragon";
      at: V2;
      heading: number;
      y?: number;
      scale?: number;
      look?: "ember" | "frost" | "sand" | "sea" | "king";
    };

export interface Shot {
  from: V3;
  to?: V3;
  look: V3;
  lookTo?: V3;
}

export interface StagedBeat {
  cam: Shot;
  /** Actors moving to a mark over the line (seconds; `y` metres up for a flyer). */
  moves?: { actor: string; to: V2; y?: number; dur: number; heading?: number }[];
  /** Effects: the dragon's fire from its jaws (`fire`: the actor), a white flash, the
   * screen shaking, the dragon rearing up. */
  fx?: { fire?: string; flash?: boolean; shake?: number; rear?: string; darken?: boolean };
}

export interface StagedScene {
  /** The scene in scenes.ts it stages (its lines). */
  scene: string;
  /** The overworld region it's played in, as it is then. */
  region: string;
  ruined: boolean;
  actors: Record<string, ActorSpec>;
  /** One per line of the scene (a missing one keeps the last shot). */
  beats: StagedBeat[];
  music?: string;
}

// Dinosaur Valley's camp: the square round the fire at (0, -4), the huts round it, the way
// out east. Heights over the ground.
const FIRE: V2 = [0, -4];

export const STAGED: StagedScene[] = [
  {
    scene: "intro",
    region: "dinosaur_valley",
    ruined: false,
    music: "riverbend",
    actors: {
      elder: {
        kind: "villager",
        folk: "valley",
        seed: 5,
        species: "iggy",
        at: [0, -13],
        heading: 0,
      },
      rex: { kind: "racer", look: "rex", at: [-8, 3], heading: 2.4 },
      chosen: {
        kind: "villager",
        folk: "dragon",
        seed: 6,
        species: "ovi",
        at: [8, 2],
        heading: -2.4,
      },
      you: { kind: "racer", look: "you", at: [-10, -6], heading: 1.3 },
      v1: { kind: "villager", folk: "valley", seed: 9, at: [5, -12], heading: -0.4 },
      v2: { kind: "villager", folk: "valley", seed: 12, at: [-5, -12], heading: 0.4 },
      v3: { kind: "villager", folk: "valley", seed: 21, at: [12, -6], heading: -1.6 },
    },
    beats: [
      // "A hidden valley...": high over the valley, sweeping down to the camp.
      { cam: { from: [140, 90, 120], to: [40, 30, 34], look: [0, 0, -4], lookTo: [0, 2, -4] } },
      // The elder announces the championship.
      { cam: { from: [3, 3.2, -4], to: [2, 2.8, -6], look: [0, 2.6, -13], lookTo: [0, 2.8, -13] } },
      // Rex.
      { cam: { from: [-3, 2.4, -2], to: [-4, 2.2, -1], look: [-8, 1.2, 3] } },
      // Aurin.
      { cam: { from: [3, 2.4, -3], to: [4, 2.2, -2], look: [8, 1.6, 2] } },
      // The elder, quietly, to you.
      {
        cam: { from: [-6, 2.6, -9], to: [-4, 2.4, -10], look: [0, 2.6, -13] },
        moves: [{ actor: "elder", to: [-3, -11], dur: 2.5, heading: -1.0 }],
      },
    ],
  },
  {
    scene: "valley_catastrophe",
    region: "dinosaur_valley",
    ruined: false,
    actors: {
      rex: { kind: "racer", look: "rex", at: [6, 0], heading: -2.2 },
      you: { kind: "racer", look: "you", at: [-4, -2], heading: 1.6 },
      elder: {
        kind: "villager",
        folk: "valley",
        seed: 5,
        species: "iggy",
        at: [0, -13],
        heading: 0,
      },
      v1: { kind: "villager", folk: "valley", seed: 9, at: [5, -12], heading: -0.4 },
      v2: { kind: "villager", folk: "valley", seed: 12, at: [-5, -12], heading: 0.4 },
      v3: { kind: "villager", folk: "valley", seed: 21, at: [12, -8], heading: -1.6 },
      cinderjaw: { kind: "dragon", at: [-160, 120], heading: 2.4, y: 70, scale: 2.2 },
    },
    beats: [
      // Rex: beaten fair and square.
      { cam: { from: [1, 2.4, -3], to: [2, 2.2, -2.5], look: [6, 1.4, 0] } },
      // Rex joins.
      { cam: { from: [-8, 6, -14], to: [-10, 7, -16], look: [2, 1, -2] } },
      // Shadows cross the sun: Cinderjaw over the valley.
      {
        cam: { from: [0, 3, -4], look: [-40, 40, 40], lookTo: [40, 50, -10] },
        moves: [{ actor: "cinderjaw", to: [60, -30], y: 45, dur: 4.5 }],
        fx: { darken: true },
      },
      // Cinderjaw lands on the camp's edge.
      {
        cam: { from: [4, 1.2, -2], to: [2, 1.0, -1], look: [0, 10, 24], lookTo: [0, 9, 24] },
        moves: [{ actor: "cinderjaw", to: [0, 26], y: 0, dur: 2.5, heading: Math.PI }],
        fx: { rear: "cinderjaw", shake: 0.6, darken: true },
      },
      // Fire falls on the valley.
      {
        cam: { from: [-24, 14, -28], to: [-30, 18, -34], look: [0, 4, 6] },
        fx: { fire: "cinderjaw", flash: true, shake: 1.2, darken: true },
      },
      // The elder: the Chosen One is gone.
      {
        cam: { from: [2, 2.6, -6], to: [1.5, 2.6, -7], look: [0, 2.6, -13] },
        fx: { darken: true },
      },
      {
        cam: { from: [-3, 2.6, -6], to: [-2, 2.6, -7], look: [0, 2.6, -13] },
        fx: { darken: true },
      },
      { cam: { from: [0, 4, -2], to: [0, 5, 0], look: [0, 2.4, -13] }, fx: { darken: true } },
    ],
  },
];

/**
 * The other kingdoms' arrivals and attacks, staged at their squares the same way: you
 * pull in, the champion and the townsfolk waiting; then later, the champion joins you,
 * the dragon flies over and lands at the square's edge, breathes fire. `at`: the
 * square (the region's spawn), facing out of it.
 */
function square(
  region: string,
  folk: Folk,
  champ: RacerId,
  at: { x: number; z: number; heading: number },
  arrive: string,
  attack: string,
  look: "ember" | "frost" | "sand" | "sea" | "king",
  dragonAt = 34,
): StagedScene[] {
  const fx = Math.sin(at.heading);
  const fz = Math.cos(at.heading);
  // (Forward along the way out, right across it.)
  const P = (f: number, r: number): V2 => [at.x + fx * f + fz * r, at.z + fz * f - fx * r];
  const P3 = (f: number, up: number, r: number): V3 => {
    const [x, z] = P(f, r);
    return [x, up, z];
  };
  const face = (from: V2, to: V2) => Math.atan2(to[0] - from[0], to[1] - from[1]);
  const you = P(0, 0);
  const ch = P(9, 3);
  const vill = (seed: number, f: number, r: number) => ({
    kind: "villager" as const,
    folk,
    seed,
    at: P(f, r),
    heading: face(P(f, r), you),
  });
  return [
    {
      scene: arrive,
      region,
      ruined: false,
      actors: {
        you: { kind: "racer", look: "you", at: P(-14, 0), heading: at.heading },
        champ: { kind: "racer", look: champ, at: ch, heading: face(ch, you) },
        v1: vill(3, 6, -6),
        v2: vill(14, 10, -2),
        v3: vill(27, 4, 8),
        v4: vill(40, 12, 7),
      },
      beats: [
        {
          cam: { from: P3(-30, 18, -10), to: P3(-8, 6, -6), look: P3(6, 1, 0) },
          moves: [{ actor: "you", to: you, dur: 3.5, heading: at.heading }],
        },
        { cam: { from: P3(3, 2.4, 0), to: P3(4, 2.2, 1), look: P3(9, 1.4, 3) } },
      ],
    },
    {
      scene: attack,
      region,
      ruined: false,
      actors: {
        you: { kind: "racer", look: "you", at: you, heading: at.heading },
        champ: { kind: "racer", look: champ, at: ch, heading: face(ch, you) },
        v1: vill(3, 6, -6),
        v2: vill(14, 10, -2),
        v3: vill(27, 4, 8),
        dragon: {
          kind: "dragon",
          at: P(140, -120),
          heading: at.heading + Math.PI,
          y: 70,
          scale: 2.2,
          look,
        },
      },
      beats: [
        { cam: { from: P3(4, 2.4, -1), to: P3(5, 2.2, 0), look: P3(9, 1.4, 3) } },
        { cam: { from: P3(-8, 6, -10), to: P3(-10, 7, -12), look: P3(5, 1, 0) } },
        {
          cam: { from: P3(0, 3, 0), look: P3(60, 40, -40), lookTo: P3(30, 30, 20) },
          moves: [
            { actor: "dragon", to: P(dragonAt, 0), y: 0, dur: 5, heading: at.heading + Math.PI },
          ],
          fx: { darken: true, shake: 0.4 },
        },
        {
          cam: { from: P3(4, 1.2, -2), to: P3(6, 1.0, -1), look: P3(dragonAt, 10, 0) },
          fx: { rear: "dragon", fire: "dragon", flash: true, shake: 1.0, darken: true },
        },
        {
          cam: { from: P3(2, 2.4, -2), to: P3(3, 2.2, -1), look: P3(9, 1.4, 3) },
          fx: { darken: true },
        },
      ],
    },
  ];
}

STAGED.push(
  ...square(
    "snow_kingdom",
    "snow",
    "brachio",
    { x: 0, z: 250, heading: Math.PI },
    "snow_arrive",
    "snow_catastrophe",
    "frost",
  ),
  ...square(
    "desert_world",
    "desert",
    "stego",
    { x: -270, z: 0, heading: Math.PI / 2 },
    "desert_arrive",
    "desert_catastrophe",
    "sand",
  ),
  ...square(
    "tropic_isles",
    "beach",
    "raptor",
    { x: 0, z: -248, heading: 0 },
    "beach_arrive",
    "beach_catastrophe",
    "sea",
  ),
);

// Each dragon's challenge at its lair (the ruined region's boss gateway): it waits before
// the lair's mouth; you pull up, it rears up and roars its line.
const DRAGON_LOOK: Record<string, "ember" | "frost" | "sand" | "sea"> = {
  valley: "ember",
  snow: "frost",
  desert: "sand",
  beach: "sea",
};
for (const k of KINGDOMS) {
  const r = REGIONS.find((x) => x.kingdom === k.id);
  const lair = r?.gateways.find((g) => g.boss);
  if (!r || !lair) continue;
  const fx = Math.sin(lair.heading);
  const fz = Math.cos(lair.heading);
  const P = (f: number, side: number): V2 => [
    lair.x + fx * f + fz * side,
    lair.z + fz * f - fx * side,
  ];
  const P3 = (f: number, up: number, side: number): V3 => {
    const [x, z] = P(f, side);
    return [x, up, z];
  };
  STAGED.push({
    scene: k.scenes.boss,
    region: r.id,
    ruined: true,
    actors: {
      dragon: {
        kind: "dragon",
        at: P(2, 0),
        heading: lair.heading,
        scale: 1.6,
        look: DRAGON_LOOK[k.id] ?? "ember",
      },
      you: { kind: "racer", look: "you", at: P(26, 0), heading: lair.heading + Math.PI },
    },
    beats: [
      {
        cam: { from: P3(52, 6, 12), to: P3(44, 5, 9), look: P3(0, 8, 0) },
        fx: { rear: "dragon", shake: 0.5, darken: true },
      },
    ],
  });
}

export const stagedById = (scene: string) => STAGED.find((s) => s.scene === scene);
export const CAMP_FIRE = FIRE;
