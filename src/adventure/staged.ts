/**
 * Staged scenes (Blake, Oct 26: in-game cutscenes): a story scene played out in the 3D
 * world itself, in an overworld region, instead of over a still picture. The cast stand
 * on their marks (racers in their karts, villagers, Lumen in his robe, the dragons, the
 * Pact Stones), the camera moves and cuts with each line, and the big moments have their
 * effects. The lines are the scene's own (scenes.ts); a staged scene says only where
 * everyone is and what the camera does for each.
 *
 * Every line gets a shot of whoever's speaking (stage(): over the shoulder, from the
 * side of the one they're talking to), unless the scene says otherwise; captions get the
 * scene's wide shot.
 *
 * Positions are game coordinates (x, z; heading 0 faces +z); heights come from the
 * ground. Cameras: `from` and `to` (where it moves, over the line), looking from `look`
 * to `lookTo`; heights are over the ground at that spot.
 */
import type { RacerId } from "../render/racers/designs";
import type { Folk, Species } from "../render/villager";
import type { DragonLook } from "../render/dragon";
import { DRAGON_HEAD, DRAGON_SIZE } from "../render/storyDragons/headAt";
import type { StoneState } from "../render/storyProps";
import { REGIONS, regionById, regionOfKingdom } from "../overworld/regions";

/** Where a region's square is (its spawn): the scenes there are staged round it. */
const squareOf = (id: string) => {
  const s = regionById(id)?.spawn;
  return s ? { x: s.x, z: s.z, heading: s.heading } : { x: 0, z: 0, heading: 0 };
};
import { KINGDOMS, RAGE, sceneOf, type KingdomId } from "./data";
import { CHAMP_OF, DRAGON_OF, sceneById } from "./scenes";

export type V2 = [number, number];
export type V3 = [number, number, number];

export type ActorSpec = (
  | { kind: "racer"; look: RacerId | "you" }
  | { kind: "villager"; folk: Folk; seed: number; species?: Species }
  /** Elder Mossback (the Founders' Horn at his hip; in two pieces, once he's broken it). */
  | { kind: "elder"; horn?: "broken" }
  /** A smugglers' guard (the kingdom's folk dress them). */
  | { kind: "guard"; folk: Folk; seed: number }
  | { kind: "dragon"; y?: number; scale?: number; look?: DragonLook }
  /** Lumen in his robe. */
  | { kind: "robed" }
  /** A Pact Stone (`big`: the Heart Stone). */
  | { kind: "stone"; state: StoneState; big?: boolean }
) & {
  at: V2;
  heading: number;
  /** Not there until a beat shows it (fx.show). */
  hidden?: boolean;
};

export interface Shot {
  from: V3;
  to?: V3;
  look: V3;
  lookTo?: V3;
  /** The camera's height is over the ground where it looks (the subject's), not under it
   * (close on someone standing lower or higher than the camera's spot). */
  rel?: boolean;
}

/** What a dragon is doing on a line (render/storyDragon.ts poses). */
export type StoryPose =
  | "idle"
  | "rear"
  | "breathe"
  | "fly"
  | "land"
  | "roar"
  | "bow"
  | "stunned"
  | "claw"
  | "walk"
  | "turn";
/** What a character on foot (Mossback, a guard, townsfolk) is doing on a line. */
export type Gesture =
  | "wave"
  | "point"
  | "cheer"
  | "nod"
  | "shake"
  | "shrug"
  | "bow"
  | "cower"
  | "think"
  | "raiseStaff"
  | "blowHorn"
  | "breakHorn"
  | "holdOut"
  | "touchHorn"
  | "dance"
  | "kneel";

export interface StagedBeat {
  cam: Shot;
  /** Actors moving to a mark over the line (seconds; `y` metres up for a flyer). */
  /** Moves: straight to `to`, or along `via` first (a road's bends), at an even speed;
   * facing the way it goes, then `heading` at the end. */
  moves?: {
    actor: string;
    to: V2;
    via?: V2[];
    /** Come along the main road instead, from ahead of "you" (the cutscene finds it). */
    road?: boolean;
    y?: number;
    dur: number;
    heading?: number;
  }[];
  fx?: {
    /** The dragon's fire from its jaws (the actor). */
    fire?: string;
    flash?: boolean;
    shake?: number;
    /** A dragon rearing up. */
    rear?: string;
    darken?: boolean;
    /** A golden light washing over everything (Lumen's). */
    light?: boolean;
    night?: boolean;
    /** Black: the blackout. */
    black?: boolean;
    /** Actors appearing and disappearing (Lumen's robe off; the stone breaking). */
    show?: string[];
    hide?: string[];
    /** The Founders' Horn. */
    horn?: boolean;
    /** The music changes (a song id: "dread" when a dragon comes). */
    music?: string;
    /** Dragons' poses on this line (actor -> pose). */
    pose?: Record<string, StoryPose>;
    /** Characters' gestures on this line (actor -> gesture). */
    gesture?: Record<string, Gesture>;
  };
}

export interface StagedScene {
  /** The scene in scenes.ts it stages (its lines). */
  scene: string;
  /** The overworld region it's played in, as it is then. */
  region: string;
  ruined: boolean;
  actors: Record<string, ActorSpec>;
  /** One per line of the scene. */
  beats: StagedBeat[];
  music?: string;
}

// ---------------------------------------------------------------- staging helpers

/** Spots round a place, by how far forward (along `heading`) and right of it. */
export function frame(at: { x: number; z: number; heading: number }) {
  const fx = Math.sin(at.heading);
  const fz = Math.cos(at.heading);
  const P = (f: number, r: number): V2 => [at.x + fx * f + fz * r, at.z + fz * f - fx * r];
  const P3 = (f: number, up: number, r: number): V3 => {
    const [x, z] = P(f, r);
    return [x, up, z];
  };
  return { P, P3 };
}
export const face = (from: V2, to: V2) => Math.atan2(to[0] - from[0], to[1] - from[1]);

/** Where the townsfolk's faces are, by kind (m; render/people/folk.ts). */
const FACE: Record<string, number> = {
  ankylo: 0.75,
  trike: 0.85,
  sauro: 1.65,
  compy: 1.0,
  pachy: 1.35,
  ovi: 1.25,
  parasaur: 1.5,
  iggy: 1.65,
};

/** Over the shoulder onto `a` (standing at `at`), from the side of `toward`. */
function closeUp(a: ActorSpec, at: V2, toward: V2, y = 0): Shot {
  let dx = toward[0] - at[0];
  let dz = toward[1] - at[1];
  const l = Math.hypot(dx, dz) || 1;
  dx /= l;
  dz /= l;
  const rx = dz;
  const rz = -dx;
  if (a.kind === "dragon") {
    // (Each dragon's head: how far up and forward of its feet, render/storyDragons.)
    const s = a.scale ?? 1.6;
    const [hu, hf] = DRAGON_HEAD[a.look ?? "ember"];
    const hx = at[0] + Math.sin(a.heading) * hf * s;
    const hz = at[1] + Math.cos(a.heading) * hf * s;
    return {
      from: [
        at[0] + dx * 44 * s + rx * 10 * s,
        y + (hu - 5) * s,
        at[1] + dz * 44 * s + rz * 10 * s,
      ],
      to: [at[0] + dx * 41 * s + rx * 9 * s, y + (hu - 5) * s, at[1] + dz * 41 * s + rz * 9 * s],
      look: [hx, y + (hu - 2) * s, hz],
    };
  }
  if (a.kind === "stone") {
    const s = a.big ? 2.2 : 1;
    return {
      from: [at[0] + dx * 7 * s + rx * 2 * s, 2.6 * s, at[1] + dz * 7 * s + rz * 2 * s],
      to: [at[0] + dx * 6 * s + rx * 1.5 * s, 2.4 * s, at[1] + dz * 6 * s + rz * 1.5 * s],
      look: [at[0], 2.2 * s, at[1]],
    };
  }
  if (a.kind === "racer")
    // (In their karts: the camera low in front, the rider's face in the top half of
    // the picture, above the line's text box.)
    return {
      from: [at[0] + dx * 3.0 + rx * 1.1, 1.85, at[1] + dz * 3.0 + rz * 1.1],
      to: [at[0] + dx * 2.75 + rx * 0.95, 1.8, at[1] + dz * 2.75 + rz * 0.95],
      look: [at[0], 1.0, at[1]],
    };
  // People on foot: close on their faces (render/people: the Elder's is 1.47 m up, a
  // guard's 1.45, Lumen's 1.07; the townsfolk's by kind, a four-legged one's ahead of
  // it), the camera about at eye level, the face in the top half of the picture.
  const face =
    a.kind === "elder"
      ? 1.45
      : a.kind === "guard"
        ? 1.45
        : a.kind === "robed"
          ? 1.08
          : (FACE[a.kind === "villager" ? (a.species ?? "") : ""] ?? 1.4);
  const ahead =
    a.kind === "villager" && a.species && ["ankylo", "trike", "sauro"].includes(a.species)
      ? 0.9
      : 0.2;
  const fx = at[0] + Math.sin(a.heading) * ahead;
  const fz = at[1] + Math.cos(a.heading) * ahead;
  const up = a.kind === "robed" ? 0.02 : 0.14;
  return {
    from: [fx + dx * 1.4 + rx * 0.5, face + up, fz + dz * 1.4 + rz * 0.5],
    to: [fx + dx * 1.22 + rx * 0.42, face + up - 0.03, fz + dz * 1.22 + rz * 0.42],
    look: [fx, face - 0.2, fz],
    rel: true,
  };
}

interface StageOpts {
  /** The shot for captions (and anyone not on stage). */
  wide: Shot;
  /** A line's own staging (its shot, moves, effects), by line number. */
  per?: Record<number, Partial<StagedBeat>>;
  /** Effects on every line (night falling, the darkness of a conquered kingdom). */
  all?: StagedBeat["fx"];
  music?: string;
}

/** Who a line's speaker is on stage (the cast keys are the actors' names; Lumen once
 * he's out of his robe, the guards, the crowd). */
const actorOf = (actors: Record<string, ActorSpec>, who: string, shown: Set<string>) => {
  for (const k of [who, who === "lumen_dragon" ? "lumen" : "", `${who}1`])
    if (k && actors[k] && shown.has(k)) return k;
  return undefined;
};

/** A scene staged: a shot of each speaker (their latest spot), the wide shot for the
 * captions, and each line's own staging where it has one. */
export function stage(
  scene: string,
  region: string,
  ruined: boolean,
  actors: Record<string, ActorSpec>,
  o: StageOpts,
): StagedScene {
  const sc = sceneById(scene);
  const pos = new Map(Object.entries(actors).map(([k, a]) => [k, a.at] as [string, V2]));
  const ys = new Map(
    Object.entries(actors).map(([k, a]) => [k, a.kind === "dragon" ? (a.y ?? 0) : 0]),
  );
  const heads = new Map(Object.entries(actors).map(([k, a]) => [k, a.heading]));
  const shown = new Set(Object.keys(actors).filter((k) => !actors[k]!.hidden));
  const beats = (sc?.beats ?? []).map((b, i): StagedBeat => {
    const p = o.per?.[i] ?? {};
    for (const m of p.moves ?? []) {
      const was = pos.get(m.actor)!;
      heads.set(m.actor, m.heading ?? face(was, m.to));
      pos.set(m.actor, m.to);
      if (m.y !== undefined) ys.set(m.actor, m.y);
    }
    for (const k of p.fx?.show ?? []) shown.add(k);
    for (const k of p.fx?.hide ?? []) shown.delete(k);
    const who = b.who ? actorOf(actors, b.who, shown) : undefined;
    let cam = p.cam;
    if (!cam && who) {
      const at = pos.get(who)!;
      // (In front of them, the way they face; you, towards the nearest of the others.)
      const h = heads.get(who)!;
      let toward: V2 = [at[0] + Math.sin(h) * 10, at[1] + Math.cos(h) * 10];
      if (who === "you") {
        let best = Infinity;
        for (const [k, q] of pos)
          if (k !== "you" && shown.has(k) && actors[k]!.kind !== "stone") {
            const d = Math.hypot(q[0] - at[0], q[1] - at[1]);
            if (d < best) {
              best = d;
              toward = q;
            }
          }
      }
      cam = closeUp({ ...actors[who]!, heading: heads.get(who)! }, at, toward, ys.get(who) ?? 0);
    }
    // A champion joining your crew: their theme (unless the line sets its own music).
    const joins =
      b.crew && CHAMP_THEME[b.crew] && !p.fx?.music ? { music: CHAMP_THEME[b.crew] } : {};
    return { cam: cam ?? o.wide, moves: p.moves, fx: { ...o.all, ...joins, ...p.fx } };
  });
  return { scene, region, ruined, actors, beats, music: o.music };
}

const ELDER = { kind: "elder" } as const;
const vill = (folk: Folk, seed: number, at: V2, to: V2): ActorSpec => ({
  kind: "villager",
  folk,
  seed,
  at,
  heading: face(at, to),
});
const guard = (folk: Folk, seed: number, at: V2, heading: number): ActorSpec => ({
  kind: "guard",
  folk,
  seed,
  at,
  heading,
});
/** One of the dragons' own guards: Dragon Kingdom folk. */
const sentry = (seed: number, at: V2, heading: number): ActorSpec => ({
  kind: "villager",
  folk: "dragon",
  seed,
  species: "pachy",
  at,
  heading,
});
const DLOOK: Record<string, DragonLook> = {
  cinderjaw: "ember",
  rimefang: "frost",
  scorchwind: "sand",
  tidewyrm: "sea",
  king: "king",
};

export const STAGED: StagedScene[] = [];
const add = (...s: (StagedScene | undefined)[]) => {
  for (const x of s) if (x) STAGED.push(x);
};

// ---------------------------------------------------------------- music

/** The cutscene score's cues (audio/songs.ts): each scene starts on one, and a line can
 * change it (fx.music). */
export const CUES = [
  "festival",
  "lumen",
  "smugglers",
  "conquered",
  "rimefang",
  "scorchwind",
  "tidewyrm",
  "king",
  "suspense",
  "court",
  "shatter",
  "false_victory",
  "rage",
  "sorrow",
  "hope",
  "new_stone",
  "yield",
  "confession",
  "finale",
  "home",
  "dread",
  "rex",
  "brachio",
  "stego",
  "raptor",
] as const;
export type Cue = (typeof CUES)[number];
/** Each champion's theme (their challenge, and joining your crew). */
const CHAMP_THEME: Record<string, Cue> = {
  rex: "rex",
  brachio: "brachio",
  stego: "stego",
  raptor: "raptor",
};
/** Each dragon's own theme (Cinderjaw's is the dread). */
const THEME: Record<string, Cue> = {
  cinderjaw: "dread",
  rimefang: "rimefang",
  scorchwind: "scorchwind",
  tidewyrm: "tidewyrm",
  king: "king",
};

// ---------------------------------------------------------------- Act I: the valley's camp

/** Dinosaur Valley's camp: the square round the fire at (0, -4), the huts round it, the
 * way out east. The Elder by his hut to the south; the valley's Pact Stone by the fire. */
const CAMP = { x: -6, z: -4, heading: Math.PI / 2 };
const STONE_V: V2 = [-12, -14];
const campFolk = (ruined: boolean): Record<string, ActorSpec> =>
  ruined
    ? {}
    : {
        v1: vill("valley", 9, [5, -12], [0, -4]),
        v2: vill("valley", 12, [-5, -12], [0, -4]),
        v3: vill("valley", 21, [12, -6], [0, -4]),
      };
const VALLEY = "dinosaur_valley";
/** Where Cinderjaw lands in the camp (The Hundredth Summer): its flat ground, east. */
const CINDER_LANDS: V2 = [28, -8];
/** His guards' runs out across the valley as he takes it: from his feet, to. */
const GUARD_RUNS: [V2, V2][] = [
  [
    [16, -14],
    [-30, -30],
  ],
  [
    [17, -6],
    [-34, 4],
  ],
  [
    [18, -18],
    [-12, -42],
  ],
  [
    [18, 0],
    [-6, 22],
  ],
  [
    [15, -10],
    [-44, -14],
  ],
  [
    [20, -22],
    [24, -42],
  ],
  [
    [16, -2],
    [-26, -6],
  ],
  [
    [19, -12],
    [-22, -20],
  ],
];
const cheer = (...who: string[]) =>
  Object.fromEntries(who.map((w) => [w, "cheer"])) as Record<string, Gesture>;
const cower = (...who: string[]) =>
  Object.fromEntries(who.map((w) => [w, "cower"])) as Record<string, Gesture>;

add(
  stage(
    sceneOf("valley", "festival"),
    VALLEY,
    false,
    {
      elder: { ...ELDER, at: [0, -13], heading: 0 },
      lumen: { kind: "robed", at: [8, 2], heading: -2.4 },
      you: { kind: "racer", look: "you", at: [-10, -6], heading: 1.3 },
      ...campFolk(false),
      v4: vill("valley", 31, [-8, 6], [0, -4]),
    },
    {
      music: "festival",
      wide: { from: [140, 90, 120], to: [40, 30, 34], look: [0, 0, -4], lookTo: [0, 2, -4] },
      per: {
        0: { fx: { gesture: cheer("v1", "v2", "v3", "v4") } },
        1: { fx: { gesture: { elder: "wave" } } },
        2: { fx: { gesture: { elder: "point" } } },
        3: { fx: { gesture: { lumen: "wave" } } },
        4: { fx: { gesture: { elder: "raiseStaff" } } },
        5: { fx: { music: "lumen" } },
        6: { fx: { gesture: { elder: "shake" } } },
        // The Founders' Horn at his hip (the story turns on it); the festival goes on
        // behind him.
        7: {
          // (From his right, where the horn hangs, framed above the text box.)
          cam: { from: [-1.2, 1.25, -11.2], to: [-1.05, 1.2, -11.4], look: [-0.2, 0.7, -12.9] },
          fx: { gesture: { elder: "touchHorn" } },
          moves: [
            { actor: "v1", to: [11, -20], dur: 6 },
            { actor: "v2", to: [-12, -19], dur: 6 },
          ],
        },
        8: {
          cam: {
            from: [6.2, 1.25, 5.8],
            to: [6.4, 1.25, 6.1],
            look: [8.6, 1.0, 3.2],
            lookTo: [9.8, 1.0, 4.8],
          },
          moves: [
            { actor: "lumen", to: [10, 5], dur: 3, heading: 0.6 },
            { actor: "v3", to: [18, -12], dur: 6 },
          ],
          fx: { gesture: { v4: "cheer" } },
        },
      },
    },
  ),
  stage(
    sceneOf("valley", "prize"),
    VALLEY,
    false,
    {
      rex: { kind: "racer", look: "rex", at: [6, 0], heading: -2.2 },
      you: { kind: "racer", look: "you", at: [-4, -2], heading: 1.6 },
      elder: { ...ELDER, at: [0, -13], heading: 0 },
      ...campFolk(false),
    },
    {
      music: "festival",
      wide: { from: [-8, 6, -14], to: [-10, 7, -16], look: [2, 1, -2] },
      per: {
        2: { fx: { gesture: cheer("v1", "v2", "v3") } },
        // The whole camp celebrates: Mossback cheering, the folk dancing.
        3: {
          cam: { from: [-6, 2.6, -2], to: [-6.5, 2.8, -1.5], look: [1, 1.4, -11] },
          fx: { gesture: { elder: "cheer", v1: "dance", v2: "dance", v3: "dance" } },
        },
      },
    },
  ),
  stage(
    sceneOf("valley", "hundredth"),
    VALLEY,
    false,
    {
      rex: { kind: "racer", look: "rex", at: [6, 0], heading: -2.2 },
      you: { kind: "racer", look: "you", at: [-4, -2], heading: 1.6 },
      elder: { ...ELDER, at: [0, -13], heading: 0 },
      ...campFolk(false),
      cinderjaw: {
        kind: "dragon",
        at: [-160, 120],
        heading: 2.4,
        y: 70,
        scale: DRAGON_SIZE.cinderjaw,
        look: "ember",
      },
      // His guards (Dragon Kingdom folk), there once he's landed.
      ...Object.fromEntries(
        GUARD_RUNS.map(([from], i) => [
          `g${i + 1}`,
          { kind: "guard", folk: "dragon", seed: 40 + i * 7, at: from, heading: 0, hidden: true },
        ]),
      ),
    },
    {
      music: "festival",
      wide: { from: [-24, 14, -28], to: [-30, 18, -34], look: [0, 4, 6] },
      all: { night: true },
      per: {
        0: { fx: { gesture: { elder: "think" } } },
        1: { fx: { gesture: { elder: "think" }, music: "suspense" } },
        2: { fx: { gesture: { elder: "kneel" } } },
        // (Blake, Oct 28: we saw only his belly, his feet floating, never his face. He
        // lands now on the camp's own flat ground, east of it, facing the camp, and the
        // shots are from the camp, low, his face toward us.)
        // His shadow over the camp: seen side-on, crossing the sky.
        3: {
          cam: { from: [-10, 3, -40], look: [-60, 40, 60], lookTo: [40, 40, -16] },
          moves: [{ actor: "cinderjaw", to: [60, -30], y: 45, dur: 4.5 }],
          fx: {
            darken: true,
            music: "dread",
            pose: { cinderjaw: "fly" },
            gesture: cower("v1", "v2", "v3", "elder"),
          },
        },
        // He comes down behind you, east of the camp.
        4: {
          cam: {
            from: [-6, 3.5, 6],
            to: [-5, 3.5, 5],
            look: [22, 14, -8],
            lookTo: [14, 10, -8],
          },
          moves: [{ actor: "cinderjaw", to: CINDER_LANDS, y: 0, dur: 3, heading: -Math.PI / 2 }],
          fx: { pose: { cinderjaw: "land" }, shake: 0.35 },
        },
        // Rearing up to name himself: from the camp, his face toward us.
        5: {
          cam: { from: [-8, 3, 8], to: [-7, 3.2, 7], look: [13, 11, -8] },
          fx: { pose: { cinderjaw: "idle" } },
        },
        // His head down over the racers.
        6: {
          cam: { from: [-2, 4, 4], to: [-1, 4.3, 3.4], look: [13, 14, -8] },
          fx: { pose: { cinderjaw: "idle" } },
        },
        7: {
          cam: { from: [-14, 9, -12], to: [-15, 9.4, -13], look: [12, 7, -8] },
          fx: {
            pose: { cinderjaw: "breathe" },
            fire: "cinderjaw",
            shake: 0.6,
            gesture: cower("v1", "v2", "v3"),
          },
        },
        // His guards fan out from his feet across the valley.
        8: {
          cam: { from: [-22, 10, -36], to: [-24, 10.5, -38], look: [0, 1, -8] },
          fx: {
            darken: true,
            music: "conquered",
            show: GUARD_RUNS.map((_, i) => `g${i + 1}`),
            gesture: cower("v1", "v2", "v3", "elder"),
          },
          moves: GUARD_RUNS.map(([, to], i) => ({ actor: `g${i + 1}`, to, dur: 7 })),
        },
      },
    },
  ),
  stage(
    sceneOf("valley", "way_out"),
    VALLEY,
    false,
    {
      elder: { ...ELDER, at: [-3, -11], heading: -0.6 },
      you: { kind: "racer", look: "you", at: [-8, -6], heading: 2.6 },
      rex: { kind: "racer", look: "rex", at: [-1, -5], heading: -2.6 },
    },
    {
      music: "conquered",
      wide: { from: [-20, 9, -20], to: [-22, 10, -22], look: [-4, 1, -7] },
      all: { night: true },
      per: {
        0: { fx: { gesture: { elder: "shake" } } },
        1: { fx: { gesture: { elder: "raiseStaff" }, music: "hope" } },
        2: { fx: { gesture: { elder: "point" } } },
        4: { fx: { gesture: { elder: "think" }, music: "suspense" } },
        5: { fx: { gesture: { elder: "point" } } },
        6: { fx: { gesture: { elder: "nod" } } },
      },
    },
  ),
  stage(
    sceneOf("valley", "stone"),
    VALLEY,
    false,
    {
      stone: { kind: "stone", state: "cracked", at: STONE_V, heading: 0.6 },
      cinderjaw: {
        kind: "dragon",
        at: [-30, 14],
        heading: face([-30, 14], STONE_V),
        scale: 1.4,
        look: "ember",
      },
    },
    {
      music: "suspense",
      wide: { from: [-4, 3, -4], to: [-6, 2.6, -7], look: [-12, 2.4, -14] },
      all: { night: true },
      per: {
        1: { fx: { pose: { cinderjaw: "rear" } } },
        2: { fx: { pose: { cinderjaw: "turn" } } },
      },
    },
  ),
  // Act IV: woken in the cage among the ruins; Rex, then the Elder and the first shard,
  // which won't let him hold it (Lumen's voice says why).
  stage(
    sceneOf("valley", "rescue"),
    VALLEY,
    true,
    {
      you: { kind: "racer", look: "you", at: [-4, -2], heading: 1.6 },
      rex: { kind: "racer", look: "rex", at: [6, 4], heading: -2.2 },
      elder: { ...ELDER, at: [4, -12], heading: -0.4 },
    },
    {
      music: "sorrow",
      wide: { from: [-24, 14, -28], to: [-30, 18, -34], look: [0, 4, 6] },
      per: {
        0: {
          cam: { from: [-1, 1.4, 0], to: [-1.5, 1.3, 0.5], look: [-4, 0.8, -2] },
          fx: { darken: true },
        },
        2: { moves: [{ actor: "rex", to: [2, 0], dur: 2.5, heading: -2.4 }] },
        3: {
          moves: [{ actor: "elder", to: [1, -6], dur: 3, heading: -0.6 }],
          fx: { gesture: { elder: "holdOut" }, light: true },
        },
        4: {
          cam: { from: [-1.5, 1.6, -3.4], to: [-1.2, 1.5, -3.8], look: [1, 1.1, -6] },
          fx: { gesture: { elder: "cower" }, flash: true, light: true },
        },
        5: {
          cam: { from: [-1.5, 1.6, -3.4], to: [-1.0, 1.4, -4.2], look: [1, 1.0, -6] },
          fx: { light: true, music: "lumen" },
        },
        6: { fx: { gesture: { elder: "think" } } },
        7: { fx: { gesture: { elder: "raiseStaff" }, music: "hope" } },
        8: { fx: { gesture: { elder: "point" } } },
      },
    },
  ),
);

// ---------------------------------------------------------------- the caves

/** A kingdom's smugglers' cave: the yard's gate (the guards either side), and its mouth
 * inside. `outside`: in front of the gate, facing it; `inside`: by the mouth. */
function caveFrame(kingdom: KingdomId) {
  const r = regionOfKingdom(kingdom);
  const c = r?.cave;
  if (!r || !c) return undefined;
  const dx0 = c.spot.x - c.gate.x;
  const dz0 = c.spot.z - c.gate.z;
  const l = Math.hypot(dx0, dz0) || 1;
  // Facing in, through the gate to the mouth.
  const inward = Math.atan2(dx0 / l, dz0 / l);
  const gate = frame({ x: c.gate.x, z: c.gate.z, heading: inward });
  const mouth = frame({ x: c.spot.x, z: c.spot.z, heading: inward });
  return { r, c, inward, gate, mouth };
}
const FOLK: Record<string, Folk> = {
  valley: "valley",
  snow: "snow",
  desert: "desert",
  beach: "beach",
};

for (const k of KINGDOMS) {
  const cf = caveFrame(k.id);
  if (!cf) continue;
  const { gate, mouth, inward, r } = cf;
  const champ = CHAMP_OF[k.id]!;
  const folk = FOLK[k.id]!;
  // The key's handed over on the line that names it (the valley's second).
  const keyLine = k.id === "valley" ? 1 : 0;
  add(
    stage(
      sceneOf(k.id, "underground"),
      r.id,
      false,
      {
        you: { kind: "racer", look: "you", at: gate.P(-9, 2), heading: inward },
        [champ]: { kind: "racer", look: champ, at: gate.P(-8, -2.5), heading: inward },
        guard: guard(folk, 7, gate.P(0.5, 3.6), inward + Math.PI),
        guard2: guard(folk, 18, gate.P(0.5, -3.6), inward + Math.PI),
      },
      {
        music: "smugglers",
        wide: { from: gate.P3(-24, 9, 8), to: gate.P3(-20, 7, 6), look: gate.P3(2, 1.5, 0) },
        all: { night: true },
        per: {
          1: { fx: { gesture: { guard: "point" } } },
          3: { fx: { gesture: { guard: "shrug", guard2: "nod" } } },
        },
      },
    ),
    stage(
      sceneOf(k.id, "key"),
      r.id,
      false,
      {
        you: { kind: "racer", look: "you", at: mouth.P(-6, 1.5), heading: inward },
        [champ]: { kind: "racer", look: champ, at: mouth.P(-6.5, -2.5), heading: inward },
        guard: guard(folk, 7, mouth.P(-1, 0), inward + Math.PI),
        elder: { ...ELDER, at: mouth.P(-4, 4.5), heading: inward - 0.8 },
        ...(champ === "rex"
          ? {}
          : {
              rex: {
                kind: "racer",
                look: "rex",
                at: mouth.P(-10, 4),
                heading: inward,
              } as ActorSpec,
            }),
      },
      {
        music: "smugglers",
        wide: { from: mouth.P3(-16, 6, 6), to: mouth.P3(-14, 5, 5), look: mouth.P3(0, 1, 0) },
        all: { night: true },
        per: {
          [keyLine]: { fx: { gesture: { guard: "holdOut" } } },
          ...(k.id === "valley"
            ? {
                2: { fx: { gesture: { elder: "think" }, music: "lumen" } },
                3: { fx: { gesture: { elder: "nod" } } },
              }
            : k.id === "snow"
              ? { 2: { fx: { gesture: { guard: "shrug" } } } }
              : k.id === "beach"
                ? { 1: { fx: { gesture: { elder: "nod" }, music: "hope" } } }
                : {}),
        },
      },
    ),
  );
}

// ---------------------------------------------------------------- Act II: the squares

/** The other kingdoms' squares (the region's spawn, facing out of it). */
const SQUARES: Record<
  string,
  { region: string; folk: Folk; at: { x: number; z: number; heading: number } }
> = {
  snow: { region: "snow_kingdom", folk: "snow", at: squareOf("snow_kingdom") },
  desert: { region: "desert_world", folk: "desert", at: squareOf("desert_world") },
  beach: { region: "tropic_isles", folk: "beach", at: squareOf("tropic_isles") },
};

for (const k of ["snow", "desert", "beach"] as const) {
  const q = SQUARES[k]!;
  const { P, P3 } = frame(q.at);
  const d = DRAGON_OF[k]!;
  const champ = CHAMP_OF[k]!;
  const you = P(0, 0);
  const folkAround = (n = 4): Record<string, ActorSpec> =>
    Object.fromEntries(
      [
        [6, -7],
        [11, -2],
        [5, 8],
        [12, 7],
        [3, -10],
        [9, 11],
      ]
        .slice(0, n)
        .map(([f, r], i) => [`v${i}`, vill(q.folk, 3 + i * 11, P(f!, r!), you)]),
    );
  const folkKeys = (n: number) => Array.from({ length: n }, (_, i) => `v${i}`);
  const dragonAt = P(34, 0);
  const dragon = (more: Partial<ActorSpec> = {}): ActorSpec =>
    ({
      kind: "dragon",
      at: dragonAt,
      heading: q.at.heading + Math.PI,
      scale: 1.6,
      look: DLOOK[d],
      ...more,
    }) as ActorSpec;
  const wide: Shot = { from: P3(-30, 18, -10), to: P3(-8, 6, -6), look: P3(6, 1, 0) };
  // Your crew comes out of the tunnel with you: Rex, and the Elder.
  const crew: Record<string, ActorSpec> = {
    rex: { kind: "racer", look: "rex", at: P(-20, -3.5), heading: q.at.heading },
    elder: { ...ELDER, at: P(-21, 3.5), heading: q.at.heading },
  };
  const caught = sceneById(sceneOf(k, "caught"))!.beats.length;
  const prize = sceneById(sceneOf(k, "prize"))!.beats;
  // The dragon's lines in the caught scene, after its landing: how it holds itself.
  const CAUGHT_POSE: Record<string, StoryPose[]> = {
    snow: ["idle", "rear", "idle", "idle"],
    desert: ["rear", "roar", "idle"],
    beach: ["idle", "idle"],
  };
  const caughtPer: Record<number, Partial<StagedBeat>> = {
    0: {
      moves: [
        { actor: "you", to: you, dur: 3.5, heading: q.at.heading },
        { actor: "rex", to: P(-4, -3.5), dur: 3.8, heading: q.at.heading },
        { actor: "elder", to: P(-6, 3.5), dur: 4.2, heading: q.at.heading },
      ],
    },
    1: {
      cam: { from: P3(0, 3, 0), look: P3(60, 40, -40), lookTo: P3(34, 10, 0) },
      moves: [{ actor: d, to: dragonAt, y: 0, dur: 5, heading: q.at.heading + Math.PI }],
      fx: {
        darken: true,
        shake: 0.4,
        music: THEME[d],
        pose: { [d]: "land" },
        gesture: { elder: "cower", ...cower(...folkKeys(4)) },
      },
    },
    [caught - 1]: {
      cam: { from: P3(8.5, 2.2, 5.5), to: P3(9, 2.1, 6), look: P3(13, 1.5, 8) },
      fx: { music: "lumen" },
    },
  };
  CAUGHT_POSE[k]!.forEach((p, i) => {
    const at = 2 + i;
    if (at < caught - 1) caughtPer[at] = { fx: { pose: { [d]: p } } };
  });
  // The crew joining, and the crowd's cheer.
  const join = prize.findIndex((b) => b.crew);
  const prizePer: Record<number, Partial<StagedBeat>> = {
    0: { fx: { music: THEME[d] } },
    [join]: { fx: { music: "hope", gesture: cheer(...folkKeys(6), "crowd1") } },
  };
  if (k === "desert") prizePer[2] = { fx: { pose: { [d]: "rear" }, gesture: cheer("crowd1") } };
  if (k === "beach") {
    prizePer[2] = { fx: { gesture: { crowd1: "point", ...cheer(...folkKeys(6)) } } };
    prizePer[3] = { fx: { pose: { [d]: "turn" } } };
  }
  add(
    stage(
      sceneOf(k, "caught"),
      q.region,
      false,
      {
        you: { kind: "racer", look: "you", at: P(-14, 0), heading: q.at.heading },
        ...crew,
        sentry: sentry(7, P(4, -5), q.at.heading + Math.PI),
        sentry2: sentry(18, P(4, 5), q.at.heading + Math.PI),
        ...folkAround(4),
        [d]: { ...dragon(), at: P(140, -120), y: 70, scale: 2 } as ActorSpec,
        lumen: { kind: "robed", at: P(13, 8), heading: face(P(13, 8), you) },
      },
      { wide, music: "conquered", per: caughtPer },
    ),
    stage(
      sceneOf(k, "stands"),
      q.region,
      false,
      {
        [d]: dragon({ at: P(30, -8) }),
        sentry: sentry(7, P(16, -6), face(P(16, -6), P(30, -8))),
        you: { kind: "racer", look: "you", at: P(-6, 0), heading: q.at.heading },
      },
      {
        music: "suspense",
        wide: { from: P3(-20, 12, 10), to: P3(-16, 10, 8), look: P3(28, 8, -8) },
        per:
          k === "snow"
            ? {
                1: { fx: { pose: { [d]: "turn" } } },
                3: { fx: { pose: { [d]: "rear" } } },
                4: { fx: { gesture: { sentry: "bow" } } },
              }
            : { 1: { fx: { pose: { [d]: k === "desert" ? "roar" : "turn" } } } },
      },
    ),
    stage(
      sceneOf(k, "prize"),
      q.region,
      false,
      {
        you: { kind: "racer", look: "you", at: you, heading: q.at.heading },
        [champ]: { kind: "racer", look: champ, at: P(9, 3), heading: face(P(9, 3), you) },
        rex: { kind: "racer", look: "rex", at: P(-4, -3.5), heading: q.at.heading },
        elder: { ...ELDER, at: P(-6, 3.5), heading: q.at.heading },
        [d]: dragon(),
        ...folkAround(6),
        crowd1: vill(q.folk, 51, P(14, -9), you),
      },
      { wide, per: prizePer },
    ),
    stage(
      sceneOf(k, "stone"),
      q.region,
      false,
      {
        stone: { kind: "stone", state: "cracked", at: P(18, -14), heading: q.at.heading + Math.PI },
        [d]: dragon({ at: P(40, -4), heading: face(P(40, -4), P(18, -14)), scale: 1.4 }),
      },
      {
        music: "suspense",
        wide: { from: P3(8, 3, -8), to: P3(10, 2.6, -10), look: P3(18, 2.4, -14) },
        all: { night: true },
        per: { 1: { fx: { pose: { [d]: "turn" } } }, 2: { fx: { pose: { [d]: "rear" } } } },
      },
    ),
  );
}

// ---------------------------------------------------------------- the champion's challenge

/**
 * A champion's challenge (Blake, Oct 27): you've just come out of a gateway (`at`,
 * facing the way out); the champion drives up and pulls in beside you, says their
 * piece, and the race starts at once. Out of the valley, the kingdom's dragon is there
 * too, sending its champion out. `at` is wherever you are, so the overworld stages it
 * there (stageAt); the list has one at each region's challenge spot for the scene list.
 */
export function challengeStaged(
  kingdom: KingdomId,
  region: string,
  at: { x: number; z: number; heading: number },
): StagedScene {
  const { P, P3 } = frame(at);
  const you = P(0, 0);
  const stop = P(7, 3.5);
  // (They come up the main road to you, from ahead: Blake, Oct 28, not out of the cliff.
  // The cutscene finds the road; out of sight until then.)
  const start = P(30, 5);
  const champ = CHAMP_OF[kingdom]!;
  const d = kingdom === "valley" ? undefined : DRAGON_OF[kingdom];
  const actors: Record<string, ActorSpec> = {
    you: { kind: "racer", look: "you", at: you, heading: at.heading },
    [champ]: { kind: "racer", look: champ, at: start, heading: face(start, stop), hidden: true },
  };
  if (d)
    actors[d] = {
      kind: "dragon",
      at: P(46, -12),
      heading: face(P(46, -12), you),
      scale: 1.4,
      look: DLOOK[d],
    };
  const sc = sceneById(sceneOf(kingdom, "challenge"));
  const first = Math.max(0, sc?.beats.findIndex((b) => b.who === champ) ?? 0);
  const per: Record<number, Partial<StagedBeat>> = {};
  if (d) per[0] = { fx: { pose: { [d]: "rear" } } };
  // The champion's lines over your shoulder, so you're in the shot with them (Blake,
  // Oct 28: a close-up of the champion alone loses you); their arrival from behind you.
  sc?.beats.forEach((b, k) => {
    if (b.who === champ)
      per[k] = {
        ...per[k],
        cam: { from: P3(-3, 2.6, -4.5), to: P3(-2.6, 2.6, -4.2), look: P3(5, 1.0, 2) },
      };
  });
  per[first] = {
    ...per[first],
    moves: [{ actor: champ, to: stop, road: true, dur: 4.5, heading: face(stop, you) }],
    fx: { ...per[first]?.fx, show: [champ], music: CHAMP_THEME[champ] },
    cam: { from: P3(-4, 2.6, -6), to: P3(-3.4, 2.6, -5.6), look: P3(16, 1.2, 4) },
  };
  return stage(sceneOf(kingdom, "challenge"), region, false, actors, {
    wide: { from: P3(-12, 8, -10), to: P3(-14, 10, -12), look: P3(3, 0.5, 1.5) },
    music: d ? THEME[d] : (CHAMP_THEME[champ] ?? "festival"),
    per,
  });
}

for (const k of KINGDOMS) {
  const r = REGIONS.find((x) => x.kingdom === k.id);
  if (r?.challenge) add(challengeStaged(k.id, r.id, r.challenge));
}

// ---------------------------------------------------------------- Act IV: the lairs

/** How each dragon answers the new stone, and how it takes its loss. */
const STONE_POSE: Record<string, StoryPose> = {
  cinderjaw: "rear",
  rimefang: "bow",
  scorchwind: "roar",
  tidewyrm: "turn",
};
const YIELD_POSE: Record<string, StoryPose> = {
  cinderjaw: "roar",
  rimefang: "bow",
  scorchwind: "rear",
  tidewyrm: "turn",
};

for (const k of KINGDOMS) {
  const r = REGIONS.find((x) => x.kingdom === k.id);
  const lair = r?.gateways.find((g) => g.boss);
  if (!r || !lair) continue;
  const { P, P3 } = frame(lair);
  const d = DRAGON_OF[k.id]!;
  const stoneAt = P(16, -12);
  const dragon: ActorSpec = {
    kind: "dragon",
    at: P(3, 0),
    heading: lair.heading,
    scale: 1.6,
    look: DLOOK[d],
  };
  const you: ActorSpec = {
    kind: "racer",
    look: "you",
    at: P(28, 2),
    heading: lair.heading + Math.PI,
  };
  const wide: Shot = { from: P3(48, 7, 14), to: P3(42, 6, 11), look: P3(6, 7, -2) };
  const rise: Shot = { from: P3(34, 2.4, 6), to: P3(33, 3, 5), look: P3(16, 6, -10) };
  const onStone: Shot = { from: P3(24, 2.6, -8), to: P3(23, 2.4, -9), look: P3(16, 2.4, -12) };
  // The valley's stone says its two laws line by line; the others, in one caption.
  const n = sceneById(sceneOf(k.id, "new_stone"))!.beats.length;
  const stonePer: Record<number, Partial<StagedBeat>> = n > 3
    ? {
        0: { cam: rise, fx: { light: true } },
        1: { fx: { show: ["stone"], light: true, flash: true } },
        2: { cam: onStone, fx: { light: true } },
        3: { cam: onStone, fx: { light: true } },
      }
    : { 0: { cam: rise, fx: { show: ["stone"], light: true, flash: true } } };
  stonePer[n - 1] = { fx: { pose: { [d]: STONE_POSE[d]! } } };
  add(
    stage(
      sceneOf(k.id, "new_stone"),
      r.id,
      true,
      {
        [d]: dragon,
        you,
        stone: {
          kind: "stone",
          state: "new",
          at: stoneAt,
          heading: lair.heading + 0.5,
          hidden: true,
        },
      },
      { wide, music: "new_stone", per: stonePer },
    ),
    stage(
      sceneOf(k.id, "yield"),
      r.id,
      true,
      {
        [d]: dragon,
        you,
        stone: { kind: "stone", state: "new", at: stoneAt, heading: lair.heading + 0.5 },
      },
      {
        wide,
        music: "yield",
        per: {
          0: { cam: onStone, fx: { light: true } },
          1: { fx: { pose: { [d]: YIELD_POSE[d]! } } },
          2: {
            cam: { from: P3(34, 3, 8), look: P3(4, 8, 0), lookTo: P3(-60, 50, 0) },
            moves: [{ actor: d, to: P(-220, 0), y: 90, dur: 5 }],
            fx: { pose: { [d]: "fly" } },
          },
          3: {
            cam: {
              from: P3(30, 30, 0),
              to: P3(40, 60, 0),
              look: P3(200, 30, 0),
              lookTo: P3(400, 20, 0),
            },
            fx: { light: true, music: "hope" },
          },
          4: {
            cam: {
              from: P3(30, 30, 0),
              to: P3(40, 60, 0),
              look: P3(200, 30, 0),
              lookTo: P3(400, 20, 0),
            },
            fx: { light: true },
          },
        },
      },
    ),
  );
}

// ---------------------------------------------------------------- the Dragon Kingdom

const DSQUARE = squareOf("dragon_kingdom");
/** The King's gateway (the citadel, where the Heart Stone stands). */
const CITADEL = (() => {
  const g = regionById("dragon_kingdom")?.gateways.find((g) => g.king);
  if (!g) return { x: 0, z: 0, heading: 0 };
  // (The court stands out in the open in front of the gate, in the King's deep courtyard
  // (dragon_layout.py's citadel pocket).)
  const OUT = 40;
  const SIDE = -9;
  const fx = Math.sin(g.heading);
  const fz = Math.cos(g.heading);
  return {
    x: g.x + fx * OUT + fz * SIDE,
    z: g.z + fz * OUT - fx * SIDE,
    heading: g.heading,
  };
})();
const DK = "dragon_kingdom";
const FOUR = ["cinderjaw", "rimefang", "scorchwind", "tidewyrm"];
{
  const { P, P3 } = frame(DSQUARE);
  const you = P(0, 0);
  const perch = (f: number, r: number): V2 => P(f, r);
  add(
    stage(
      "dragon_challenger",
      DK,
      false,
      {
        you: { kind: "racer", look: "you", at: P(-14, 0), heading: DSQUARE.heading },
        rex: { kind: "racer", look: "rex", at: P(-20, -3.5), heading: DSQUARE.heading },
        elder: { ...ELDER, at: P(-21, 3.5), heading: DSQUARE.heading },
        lumen: { kind: "robed", at: P(10, 6), heading: face(P(10, 6), you) },
        king: {
          kind: "dragon",
          at: P(140, 70),
          heading: DSQUARE.heading + Math.PI,
          y: 70,
          scale: 1.8,
          look: "king",
        },
        cinderjaw: { kind: "dragon", at: P(200, -200), heading: 0, y: 90, scale: 1, look: "ember" },
        rimefang: { kind: "dragon", at: P(220, 200), heading: 0, y: 90, scale: 1, look: "frost" },
        scorchwind: { kind: "dragon", at: P(-200, 220), heading: 0, y: 90, scale: 1, look: "sand" },
        tidewyrm: { kind: "dragon", at: P(-220, -200), heading: 0, y: 90, scale: 1, look: "sea" },
      },
      {
        music: "suspense",
        wide: { from: P3(-30, 20, -12), to: P3(-10, 7, -6), look: P3(10, 2, 0) },
        per: {
          0: {
            moves: [
              { actor: "you", to: you, dur: 3.5, heading: DSQUARE.heading },
              { actor: "rex", to: P(-4, -3.5), dur: 3.8, heading: DSQUARE.heading },
              { actor: "elder", to: P(-6, 3.5), dur: 4.2, heading: DSQUARE.heading },
            ],
          },
          1: {
            cam: { from: P3(0, 3, 0), look: P3(80, 50, 40), lookTo: P3(36, 12, 0) },
            moves: [
              { actor: "king", to: P(36, 0), y: 0, dur: 5, heading: DSQUARE.heading + Math.PI },
            ],
            fx: { shake: 0.5, music: "king", pose: { king: "land" } },
          },
          2: { fx: { pose: { king: "roar" } } },
          3: { fx: { pose: { king: "idle" } } },
          5: { fx: { pose: { king: "turn" } } },
          6: {
            cam: { from: P3(-24, 70, 0), to: P3(-22, 74, 0), look: P3(56, 14, 0) },
            moves: [
              {
                actor: "cinderjaw",
                to: perch(52, -30),
                y: 14,
                dur: 5,
                heading: face(perch(52, -30), you),
              },
              {
                actor: "rimefang",
                to: perch(52, 30),
                y: 14,
                dur: 5.5,
                heading: face(perch(52, 30), you),
              },
              {
                actor: "scorchwind",
                to: perch(70, -16),
                y: 18,
                dur: 6,
                heading: face(perch(70, -16), you),
              },
              {
                actor: "tidewyrm",
                to: perch(70, 16),
                y: 18,
                dur: 6.5,
                heading: face(perch(70, 16), you),
              },
            ],
            fx: {
              pose: Object.fromEntries(FOUR.map((d) => [d, "fly"])) as Record<string, StoryPose>,
            },
          },
          7: {
            fx: {
              music: "lumen",
              pose: Object.fromEntries(FOUR.map((d) => [d, "idle"])) as Record<string, StoryPose>,
            },
          },
          8: { fx: { gesture: { elder: "point" } } },
        },
      },
    ),
  );
}
{
  const { P, P3 } = frame(CITADEL);
  const you = P(26, 0);
  const heart = P(12, -18);
  const court = (
    ruined: boolean,
    extra: Record<string, ActorSpec> = {},
  ): Record<string, ActorSpec> => ({
    you: { kind: "racer", look: "you", at: you, heading: CITADEL.heading + Math.PI },
    elder: { ...ELDER, at: P(24, 6), heading: face(P(24, 6), P(0, 0)) },
    rex: { kind: "racer", look: "rex", at: P(28, -5), heading: CITADEL.heading + Math.PI },
    king: { kind: "dragon", at: P(-14, 0), heading: CITADEL.heading, scale: 1.4, look: "king" },
    cinderjaw: {
      kind: "dragon",
      at: P(-4, -28),
      heading: face(P(-4, -28), you),
      scale: 0.9,
      look: "ember",
    },
    rimefang: {
      kind: "dragon",
      at: P(-4, 28),
      heading: face(P(-4, 28), you),
      scale: 0.9,
      look: "frost",
    },
    scorchwind: {
      kind: "dragon",
      at: P(-22, -30),
      heading: face(P(-22, -30), you),
      scale: 0.9,
      look: "sand",
    },
    tidewyrm: {
      kind: "dragon",
      at: P(-22, 30),
      heading: face(P(-22, 30), you),
      scale: 0.9,
      look: "sea",
    },
    heart: {
      kind: "stone",
      state: ruined ? "broken" : "old",
      big: true,
      at: heart,
      heading: CITADEL.heading + 0.6,
    },
    ...extra,
  });
  const wide: Shot = { from: P3(44, 14, 4), to: P3(40, 12, 3), look: P3(-2, 10, 0) };
  const onHeart: Shot = { from: P3(30, 10, -10), to: P3(28, 9, -11), look: P3(12, 3, -18) };
  // Lumen the hatchling, by the stone (a close-up of a dragon so small would be inside it).
  const onLumen: Shot = { from: P3(25, 2.6, -9), to: P3(24.5, 2.5, -9.6), look: P3(18, 2.2, -15) };
  const allPose = (p: StoryPose, who = FOUR) =>
    Object.fromEntries(who.map((d) => [d, p])) as Record<string, StoryPose>;
  add(
    stage("dragon_before_king", DK, false, court(false), {
      wide,
      music: "court",
      per: {
        0: { fx: { pose: { cinderjaw: "rear" } } },
        2: { fx: { pose: { scorchwind: "roar" } } },
        3: { fx: { pose: { tidewyrm: "bow" } } },
        4: { fx: { pose: { king: "roar", tidewyrm: "idle" }, music: "king" } },
      },
    }),
    stage(
      "dragon_return",
      DK,
      false,
      court(false, { lumen: { kind: "robed", at: P(21, -7), heading: face(P(21, -7), heart) } }),
      {
        wide,
        music: "court",
        per: {
          0: { fx: { pose: { king: "bow", ...allPose("rear") } } },
          1: { fx: { pose: { king: "idle" } } },
          2: {
            cam: onHeart,
            moves: [{ actor: "king", to: P(-6, -9), dur: 4, heading: face(P(-6, -9), heart) }],
            fx: { pose: { king: "walk" } },
          },
          3: {
            cam: onHeart,
            fx: { light: true, flash: true, pose: { king: "claw" }, music: "suspense" },
          },
        },
      },
    ),
    stage(
      "dragon_lumen",
      DK,
      false,
      court(false, {
        king: {
          kind: "dragon",
          at: P(-6, -9),
          heading: face(P(-6, -9), heart),
          scale: 1.4,
          look: "king",
        },
        lumen: { kind: "robed", at: P(21, -7), heading: face(P(21, -7), heart) },
        lumen_dragon: {
          kind: "dragon",
          at: P(18, -15),
          // (He speaks to the Elder; he turns to the stone to strike it.)
          heading: face(P(18, -15), P(24, 6)),
          scale: 0.32,
          look: "lumen",
          hidden: true,
        },
        broken: {
          kind: "stone",
          state: "broken",
          big: true,
          at: heart,
          heading: CITADEL.heading + 0.6,
          hidden: true,
        },
      }),
      {
        wide,
        music: "lumen",
        all: { light: true },
        per: {
          0: {
            moves: [{ actor: "lumen", to: P(18, -15), dur: 3, heading: face(P(18, -15), heart) }],
            fx: { pose: { king: "claw" } },
          },
          1: {
            cam: { from: P3(26, 3, -8), to: P3(25, 3.2, -9), look: P3(18, 2, -15) },
            fx: {
              hide: ["lumen"],
              show: ["lumen_dragon"],
              flash: true,
              light: true,
              pose: { lumen_dragon: "rear" },
            },
          },
          2: { fx: { gesture: { elder: "think" } } },
          3: { cam: onLumen, fx: { pose: { lumen_dragon: "idle" } } },
          4: { fx: { pose: { king: "rear" } } },
          5: { cam: onLumen },
          6: { cam: { from: P3(34, 5, -4), to: P3(33, 5, -5), look: P3(18, 3, -15) } },
          7: { cam: onLumen, fx: { music: "sorrow", gesture: { elder: "shake" } } },
          8: {
            cam: onHeart,
            moves: [
              { actor: "lumen_dragon", to: P(18, -15), dur: 0.6, heading: face(P(18, -15), heart) },
            ],
            fx: {
              flash: true,
              shake: 1.2,
              light: true,
              music: "shatter",
              pose: { lumen_dragon: "breathe" },
            },
          },
          9: {
            cam: wide,
            fx: {
              hide: ["heart"],
              show: ["broken"],
              flash: true,
              shake: 1.8,
              gesture: { elder: "cower" },
              pose: { king: "rear", ...allPose("rear") },
            },
          },
          10: {
            cam: { from: P3(70, 30, 30), to: P3(110, 60, 50), look: P3(0, 4, 0) },
            fx: { hide: ["lumen_dragon"], flash: true, shake: 1.2, darken: true },
          },
        },
      },
    ),
    stage("dragon_horn", DK, true, court(true), {
      wide,
      music: "dread",
      per: {
        0: {
          cam: { from: P3(30, 4, -14), to: P3(28, 3, -16), look: P3(12, 2, -18) },
          fx: { darken: true },
        },
        1: { fx: { pose: { king: "rear" }, night: true } },
        2: { fx: { pose: { king: "breathe" }, fire: "king", night: true } },
        3: { fx: { gesture: { elder: "raiseStaff" }, night: true } },
        4: {
          cam: wide,
          fx: {
            horn: true,
            flash: true,
            shake: 1.4,
            gesture: { elder: "blowHorn" },
            pose: { king: "stunned" },
          },
        },
        5: { fx: { pose: { king: "stunned" }, music: "false_victory" } },
        6: { fx: { pose: { king: "stunned" }, gesture: { elder: "cheer" } } },
      },
    }),
    stage("dragon_rage", DK, true, court(true), {
      wide,
      music: "dread",
      all: { night: true },
      per: {
        0: { fx: { black: true, pose: { king: "stunned" } } },
        1: { fx: { pose: { king: "rear" }, night: true } },
        2: { fx: { pose: { king: "idle" }, night: true } },
        3: { fx: { pose: { king: "roar" }, night: true } },
        4: {
          fx: {
            pose: { king: "breathe", ...allPose("fly") },
            fire: "king",
            shake: 1.2,
            night: true,
            music: "rage",
          },
          moves: FOUR.map((d, i) => ({
            actor: d,
            to: P(-200 + i * 60, (i % 2 ? 1 : -1) * 260),
            y: 120,
            dur: 6,
          })),
        },
      },
    }),
    stage(
      "rage_shards",
      DK,
      true,
      court(true, {
        king: {
          kind: "dragon",
          at: P(-120, 0),
          heading: CITADEL.heading,
          y: 80,
          scale: 1.4,
          look: "king",
        },
      }),
      {
        wide,
        music: "sorrow",
        per: {
          0: { cam: onHeart, fx: { light: true, night: true, pose: { king: "fly" } } },
          1: {
            cam: {
              from: P3(30, 4, -24),
              to: P3(60, 80, 0),
              look: P3(12, 6, -18),
              lookTo: P3(200, 120, 0),
            },
            fx: { light: true, flash: true, music: "hope" },
          },
          2: {
            cam: { from: P3(27, 1.6, 1), look: P3(26, 0.8, 0) },
            fx: { black: true, shake: 1.5, flash: true, music: "dread" },
          },
        },
      },
    ),
    stage("dragon_court", DK, true, court(true), {
      wide,
      music: "court",
      per: {
        1: {
          cam: {
            from: P3(30, 6, 0),
            to: P3(30, 7, -10),
            look: P3(0, 8, -30),
            lookTo: P3(0, 8, 30),
          },
        },
        3: { fx: { pose: { cinderjaw: "rear" } } },
        4: { fx: { pose: { king: "turn", cinderjaw: "idle" } } },
      },
    }),
    stage(
      "dragon_heart",
      DK,
      true,
      court(true, {
        heart: {
          kind: "stone",
          state: "broken",
          big: true,
          at: heart,
          heading: CITADEL.heading + 0.6,
        },
        whole: {
          kind: "stone",
          state: "new",
          big: true,
          at: heart,
          heading: CITADEL.heading + 0.6,
          hidden: true,
        },
      }),
      {
        wide,
        music: "new_stone",
        per: {
          0: { cam: onHeart, fx: { hide: ["heart"], show: ["whole"], light: true, flash: true } },
          // Lumen's voice, out of the light.
          1: { cam: onHeart, fx: { light: true, music: "lumen" } },
          2: { cam: onHeart, fx: { light: true } },
          3: { fx: { music: "confession", gesture: { elder: "think" } } },
          4: { fx: { gesture: { elder: "holdOut" } } },
          5: { fx: { gesture: { elder: "shake" } } },
          6: {
            cam: {
              from: P3(22.25, 2.35, 5.1),
              to: P3(22.3, 2.3, 5.12),
              look: P3(24, 0.8, 6),
              rel: true,
            },
            fx: { flash: true, shake: 0.6, gesture: { elder: "breakHorn" } },
          },
          7: { fx: { pose: { king: "bow" } } },
          8: { cam: onHeart, fx: { light: true, pose: { king: "idle" } } },
          9: { fx: { pose: { king: "rear" }, music: "king" } },
        },
      },
    ),
    stage(
      "dragon_lumen_returns",
      DK,
      false,
      court(false, {
        elder: { ...ELDER, horn: "broken", at: P(24, 6), heading: face(P(24, 6), P(0, 0)) },
        heart: {
          kind: "stone",
          state: "new",
          big: true,
          at: heart,
          heading: CITADEL.heading + 0.6,
        },
        lumen_dragon: {
          kind: "dragon",
          at: P(2, -26),
          heading: face(P(2, -26), you),
          scale: 0.9,
          look: "lumen_grown",
          hidden: true,
        },
      }),
      {
        wide,
        music: "finale",
        per: {
          0: { fx: { pose: { king: "bow" } } },
          1: { fx: { pose: { king: "bow" } } },
          2: { cam: onHeart, fx: { light: true } },
          3: {
            cam: onHeart,
            fx: {
              show: ["lumen_dragon"],
              light: true,
              flash: true,
              pose: { lumen_dragon: "land" },
            },
          },
          4: {
            cam: { from: P3(34, 21, -6), to: P3(33, 22, -7), look: P3(12.5, 22, -14.7) },
            fx: { pose: { lumen_dragon: "idle" } },
          },
          5: { fx: { gesture: { elder: "cheer" } } },
          6: { cam: { from: P3(34, 21, -6), to: P3(33, 22, -7), look: P3(12.5, 22, -14.7) } },
          7: { fx: { pose: { king: "bow" } } },
          8: { cam: { from: P3(34, 21, -6), to: P3(33, 22, -7), look: P3(12.5, 22, -14.7) } },
          9: {
            cam: wide,
            fx: {
              light: true,
              pose: allPose("bow", ["rimefang", "scorchwind", "tidewyrm"]),
              gesture: { elder: "bow" },
            },
          },
          10: {
            cam: { from: P3(20, 13, -54), to: P3(19, 14, -53), look: P3(4.4, 14, -28) },
            fx: { pose: { cinderjaw: "roar" }, music: "dread" },
          },
          11: {
            cam: { from: P3(40, 6, -20), look: P3(2, 10, -30), lookTo: P3(-300, 120, -200) },
            moves: [{ actor: "cinderjaw", to: P(-600, -400), y: 160, dur: 7 }],
            fx: { pose: { cinderjaw: "fly" } },
          },
        },
      },
    ),
  );
}

// ---------------------------------------------------------------- the Rage, kingdom by kingdom

{
  const rage = (
    scene: string,
    region: string,
    at: { x: number; z: number; heading: number },
    d: string,
  ) => {
    const { P, P3 } = frame(at);
    return stage(
      scene,
      region,
      true,
      {
        [d]: {
          kind: "dragon",
          at: P(160, -120),
          heading: at.heading + Math.PI,
          y: 60,
          scale: 2,
          look: DLOOK[d],
        },
      },
      {
        wide: { from: P3(-10, 6, 0), look: P3(60, 30, -40), lookTo: P3(20, 20, 20) },
        music: "rage",
        per: {
          0: {
            moves: [{ actor: d, to: P(30, 10), y: 18, dur: 5, heading: at.heading + Math.PI }],
            fx: { fire: d, pose: { [d]: "breathe" }, darken: true, shake: 0.8 },
          },
        },
      },
    );
  };
  add(
    rage(RAGE[1], VALLEY, { x: 0, z: -4, heading: -Math.PI / 2 }, "cinderjaw"),
    rage(RAGE[2], SQUARES.snow!.region, SQUARES.snow!.at, "rimefang"),
    rage(RAGE[3], SQUARES.desert!.region, SQUARES.desert!.at, "scorchwind"),
    rage(RAGE[4], SQUARES.beach!.region, SQUARES.beach!.at, "tidewyrm"),
  );
}

// ---------------------------------------------------------------- the ending

{
  const { P, P3 } = frame(CAMP);
  const you = P(0, 0);
  const elder = P(8, 2);
  add(
    stage(
      "ending",
      VALLEY,
      false,
      {
        you: { kind: "racer", look: "you", at: you, heading: face(you, elder) },
        elder: { ...ELDER, horn: "broken", at: elder, heading: face(elder, you) },
        rex: { kind: "racer", look: "rex", at: P(-4, -6), heading: face(P(-4, -6), elder) },
        brachio: { kind: "racer", look: "brachio", at: P(-4, 6), heading: face(P(-4, 6), elder) },
        stego: { kind: "racer", look: "stego", at: P(-9, -3), heading: face(P(-9, -3), elder) },
        raptor: { kind: "racer", look: "raptor", at: P(-9, 4), heading: face(P(-9, 4), elder) },
        lumen_dragon: {
          kind: "dragon",
          at: P(30, 18),
          heading: face(P(30, 18), you),
          scale: 0.9,
          look: "lumen_grown",
        },
        v1: vill("valley", 9, P(12, -6), you),
        v2: vill("valley", 12, P(12, 7), you),
        king: {
          kind: "dragon",
          at: P(-200, 0),
          heading: CAMP.heading,
          y: 60,
          scale: 1.6,
          look: "king",
        },
      },
      {
        music: "home",
        wide: { from: P3(-40, 30, -30), to: P3(-20, 12, -14), look: P3(4, 0, 0) },
        per: {
          0: { fx: { gesture: cheer("v1", "v2") } },
          1: {
            cam: { from: P3(-4, 3, 0), look: P3(60, 40, 0), lookTo: P3(200, 60, 0) },
            moves: [{ actor: "king", to: P(400, 0), y: 90, dur: 7 }],
            fx: { pose: { king: "fly" }, gesture: cheer("v1", "v2") },
          },
          2: { fx: { gesture: { elder: "wave" } } },
          4: { fx: { pose: { lumen_dragon: "roar" } } },
        },
      },
    ),
  );
}

/** Stagings made where you are (the challenges): they stand in for the list's. */
const HERE = new Map<string, StagedScene>();
export const stageAt = (s: StagedScene) => HERE.set(s.scene, s);

export const stagedById = (scene: string) =>
  HERE.get(scene) ?? STAGED.find((s) => s.scene === scene);
