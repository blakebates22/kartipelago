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
import type { StoneState } from "../render/storyProps";
import { REGIONS, regionOfKingdom } from "../overworld/regions";
import { KINGDOMS, RAGE, sceneOf, type KingdomId } from "./data";
import { CHAMP_OF, DRAGON_OF, sceneById } from "./scenes";

export type V2 = [number, number];
export type V3 = [number, number, number];

export type ActorSpec = (
  | { kind: "racer"; look: RacerId | "you" }
  | { kind: "villager"; folk: Folk; seed: number; species?: Species }
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
}

export interface StagedBeat {
  cam: Shot;
  /** Actors moving to a mark over the line (seconds; `y` metres up for a flyer). */
  moves?: { actor: string; to: V2; y?: number; dur: number; heading?: number }[];
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
    // (A dragon's head is 20 m up and 17 m forward of its feet at scale 1.)
    const s = a.scale ?? 1.6;
    const hx = at[0] + Math.sin(a.heading) * 17 * s;
    const hz = at[1] + Math.cos(a.heading) * 17 * s;
    return {
      from: [at[0] + dx * 44 * s + rx * 10 * s, y + 15 * s, at[1] + dz * 44 * s + rz * 10 * s],
      to: [at[0] + dx * 41 * s + rx * 9 * s, y + 15 * s, at[1] + dz * 41 * s + rz * 9 * s],
      look: [hx, y + 18 * s, hz],
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
  const tall = a.kind === "racer" ? 1.2 : 1.5;
  return {
    from: [at[0] + dx * 3.4 + rx * 1.3, 2.1, at[1] + dz * 3.4 + rz * 1.3],
    to: [at[0] + dx * 3.1 + rx * 1.1, 2.0, at[1] + dz * 3.1 + rz * 1.1],
    look: [at[0], tall, at[1]],
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
    return { cam: cam ?? o.wide, moves: p.moves, fx: { ...o.all, ...p.fx } };
  });
  return { scene, region, ruined, actors, beats, music: o.music };
}

const ELDER = { kind: "villager", folk: "valley", seed: 5, species: "iggy" } as const;
const vill = (folk: Folk, seed: number, at: V2, to: V2): ActorSpec => ({
  kind: "villager",
  folk,
  seed,
  at,
  heading: face(at, to),
});
const guard = (folk: Folk, seed: number, at: V2, heading: number): ActorSpec => ({
  kind: "villager",
  folk,
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
      music: "riverbend",
      wide: { from: [140, 90, 120], to: [40, 30, 34], look: [0, 0, -4], lookTo: [0, 2, -4] },
      per: {
        5: {
          cam: { from: [11, 1.9, 5], to: [11.5, 1.8, 5.5], look: [8, 1.6, 2] },
          moves: [{ actor: "lumen", to: [10, 5], dur: 3, heading: 0.6 }],
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
    { wide: { from: [-8, 6, -14], to: [-10, 7, -16], look: [2, 1, -2] } },
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
        scale: 2.2,
        look: "ember",
      },
    },
    {
      wide: { from: [-24, 14, -28], to: [-30, 18, -34], look: [0, 4, 6] },
      all: { night: true },
      per: {
        2: {
          cam: { from: [0, 3, -4], look: [-40, 40, 40], lookTo: [40, 50, -10] },
          moves: [{ actor: "cinderjaw", to: [60, -30], y: 45, dur: 4.5 }],
          fx: { darken: true, music: "dread" },
        },
        3: {
          cam: { from: [4, 1.2, -2], to: [2, 1.0, -1], look: [0, 10, 24], lookTo: [0, 9, 24] },
          moves: [{ actor: "cinderjaw", to: [0, 26], y: 0, dur: 2.5, heading: Math.PI }],
          fx: { rear: "cinderjaw", shake: 0.6, darken: true },
        },
        4: {
          cam: { from: [6, 3, 4], to: [5, 3.4, 6], look: [0, 12, 26] },
          fx: { darken: true },
        },
        5: {
          cam: { from: [-12, 4, 2], to: [-14, 5, 0], look: [0, 10, 26] },
          fx: { rear: "cinderjaw", shake: 1.0, darken: true },
        },
        6: { fx: { darken: true } },
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
      wide: { from: [-20, 9, -20], to: [-22, 10, -22], look: [-4, 1, -7] },
      all: { night: true },
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
      wide: { from: [-4, 3, -4], to: [-6, 2.6, -7], look: [-12, 2.4, -14] },
      all: { night: true },
      per: { 1: { fx: { rear: "cinderjaw" } } },
    },
  ),
  // Act IV: woken in the cage among the ruins; Rex, then the Elder and the first shard.
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
      wide: { from: [-24, 14, -28], to: [-30, 18, -34], look: [0, 4, 6] },
      per: {
        0: {
          cam: { from: [-1, 1.4, 0], to: [-1.5, 1.3, 0.5], look: [-4, 0.8, -2] },
          fx: { darken: true },
        },
        2: { moves: [{ actor: "rex", to: [2, 0], dur: 2.5, heading: -2.4 }] },
        3: { moves: [{ actor: "elder", to: [1, -6], dur: 3, heading: -0.6 }] },
        4: { fx: { light: true } },
        5: { fx: { light: true } },
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
        wide: { from: gate.P3(-24, 9, 8), to: gate.P3(-20, 7, 6), look: gate.P3(2, 1.5, 0) },
        all: { night: true },
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
        wide: { from: mouth.P3(-16, 6, 6), to: mouth.P3(-14, 5, 5), look: mouth.P3(0, 1, 0) },
        all: { night: true },
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
  snow: { region: "snow_kingdom", folk: "snow", at: { x: 0, z: 250, heading: Math.PI } },
  desert: { region: "desert_world", folk: "desert", at: { x: -270, z: 0, heading: Math.PI / 2 } },
  beach: { region: "tropic_isles", folk: "beach", at: { x: 0, z: -248, heading: 0 } },
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
  add(
    stage(
      sceneOf(k, "caught"),
      q.region,
      false,
      {
        you: { kind: "racer", look: "you", at: P(-14, 0), heading: q.at.heading },
        guard: guard(q.folk, 7, P(4, -5), q.at.heading + Math.PI),
        guard2: guard(q.folk, 18, P(4, 5), q.at.heading + Math.PI),
        ...folkAround(4),
        [d]: { ...dragon(), at: P(140, -120), y: 70, scale: 2 } as ActorSpec,
        lumen: { kind: "robed", at: P(13, 8), heading: face(P(13, 8), you) },
      },
      {
        wide,
        per: {
          0: { moves: [{ actor: "you", to: you, dur: 3.5, heading: q.at.heading }] },
          1: {
            cam: { from: P3(0, 3, 0), look: P3(60, 40, -40), lookTo: P3(34, 10, 0) },
            moves: [{ actor: d, to: dragonAt, y: 0, dur: 5, heading: q.at.heading + Math.PI }],
            fx: { darken: true, shake: 0.4, music: "dread" },
          },
          2: { fx: { rear: d } },
          3: { cam: { from: P3(8.5, 2.2, 5.5), to: P3(9, 2.1, 6), look: P3(13, 1.5, 8) } },
        },
      },
    ),
    stage(
      sceneOf(k, "stands"),
      q.region,
      false,
      {
        [d]: dragon({ at: P(30, -8) }),
        guard: guard(q.folk, 7, P(16, -6), face(P(16, -6), P(30, -8))),
        you: { kind: "racer", look: "you", at: P(-6, 0), heading: q.at.heading },
      },
      { wide: { from: P3(-20, 12, 10), to: P3(-16, 10, 8), look: P3(28, 8, -8) } },
    ),
    stage(
      sceneOf(k, "prize"),
      q.region,
      false,
      {
        you: { kind: "racer", look: "you", at: you, heading: q.at.heading },
        [champ]: { kind: "racer", look: champ, at: P(9, 3), heading: face(P(9, 3), you) },
        [d]: dragon(),
        ...folkAround(6),
        crowd1: vill(q.folk, 51, P(14, -9), you),
      },
      { wide },
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
        wide: { from: P3(8, 3, -8), to: P3(10, 2.6, -10), look: P3(18, 2.4, -14) },
        all: { night: true },
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
  const start = P(30, 5);
  const champ = CHAMP_OF[kingdom]!;
  const d = kingdom === "valley" ? undefined : DRAGON_OF[kingdom];
  const actors: Record<string, ActorSpec> = {
    you: { kind: "racer", look: "you", at: you, heading: at.heading },
    [champ]: { kind: "racer", look: champ, at: start, heading: face(start, stop) },
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
  if (d) per[0] = { fx: { rear: d } };
  per[first] = {
    ...per[first],
    moves: [{ actor: champ, to: stop, dur: 3, heading: face(stop, you) }],
    ...(first === 0
      ? { cam: { from: P3(-7, 3, -4), to: P3(-6, 3.2, -3), look: P3(20, 1.5, 4) } }
      : {}),
  };
  return stage(sceneOf(kingdom, "challenge"), region, false, actors, {
    wide: { from: P3(-12, 8, -10), to: P3(-14, 10, -12), look: P3(3, 0.5, 1.5) },
    per,
  });
}

for (const k of KINGDOMS) {
  const r = REGIONS.find((x) => x.kingdom === k.id);
  if (r?.challenge) add(challengeStaged(k.id, r.id, r.challenge));
}

// ---------------------------------------------------------------- Act IV: the lairs

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
      {
        wide,
        per: {
          0: {
            cam: { from: P3(34, 2.4, 6), to: P3(33, 3, 5), look: P3(16, 6, -10) },
            fx: { light: true },
          },
          1: { fx: { show: ["stone"], light: true, flash: true } },
          2: {
            cam: { from: P3(24, 2.6, -8), to: P3(23, 2.4, -9), look: P3(16, 2.4, -12) },
            fx: { light: true },
          },
          3: { fx: { rear: d } },
        },
      },
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
        per: {
          0: {
            cam: { from: P3(24, 2.6, -8), to: P3(23, 2.4, -9), look: P3(16, 2.4, -12) },
            fx: { light: true },
          },
          1: { fx: { rear: d } },
          2: {
            cam: { from: P3(34, 3, 8), look: P3(4, 8, 0), lookTo: P3(-60, 50, 0) },
            moves: [{ actor: d, to: P(-220, 0), y: 90, dur: 5 }],
          },
          3: {
            cam: {
              from: P3(30, 30, 0),
              to: P3(40, 60, 0),
              look: P3(200, 30, 0),
              lookTo: P3(400, 20, 0),
            },
            fx: { light: true },
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

const DSQUARE = { x: 0, z: 200, heading: Math.PI };
const CITADEL = { x: 9.53, z: -326.53, heading: 0.299 };
const DK = "dragon_kingdom";
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
        elder: { ...ELDER, at: P(-3, -4), heading: DSQUARE.heading },
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
        wide: { from: P3(-30, 20, -12), to: P3(-10, 7, -6), look: P3(10, 2, 0) },
        per: {
          0: { moves: [{ actor: "you", to: you, dur: 3.5, heading: DSQUARE.heading }] },
          1: {
            cam: { from: P3(0, 3, 0), look: P3(80, 50, 40), lookTo: P3(36, 12, 0) },
            moves: [
              { actor: "king", to: P(36, 0), y: 0, dur: 5, heading: DSQUARE.heading + Math.PI },
            ],
            fx: { shake: 0.5, music: "dread" },
          },
          2: { fx: { rear: "king" } },
          4: {
            cam: { from: P3(-6, 6, 0), look: P3(40, 20, 0), lookTo: P3(40, 16, 0) },
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
          },
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
      at: P(-6, -40),
      heading: face(P(-6, -40), you),
      scale: 0.9,
      look: "ember",
    },
    rimefang: {
      kind: "dragon",
      at: P(-6, 40),
      heading: face(P(-6, 40), you),
      scale: 0.9,
      look: "frost",
    },
    scorchwind: {
      kind: "dragon",
      at: P(-26, -44),
      heading: face(P(-26, -44), you),
      scale: 0.9,
      look: "sand",
    },
    tidewyrm: {
      kind: "dragon",
      at: P(-26, 44),
      heading: face(P(-26, 44), you),
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
  const wide: Shot = { from: P3(56, 8, 18), to: P3(48, 7, 14), look: P3(0, 9, 0) };
  const onHeart: Shot = { from: P3(30, 4, -24), to: P3(28, 3.6, -25), look: P3(12, 4, -18) };
  add(
    stage("dragon_before_king", DK, false, court(false), { wide }),
    stage(
      "dragon_return",
      DK,
      false,
      court(false, { lumen: { kind: "robed", at: P(21, -7), heading: face(P(21, -7), heart) } }),
      {
        wide,
        per: {
          2: {
            cam: onHeart,
            moves: [{ actor: "king", to: P(-6, -9), dur: 4, heading: face(P(-6, -9), heart) }],
          },
          3: { cam: onHeart, fx: { light: true, flash: true } },
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
          heading: face(P(18, -15), heart),
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
        all: { light: true },
        per: {
          0: {
            moves: [{ actor: "lumen", to: P(18, -15), dur: 3, heading: face(P(18, -15), heart) }],
          },
          1: {
            cam: { from: P3(26, 3, -8), to: P3(25, 3.2, -9), look: P3(18, 2, -15) },
            fx: { hide: ["lumen"], show: ["lumen_dragon"], flash: true, light: true },
          },
          3: { fx: { rear: "king" } },
          4: { cam: { from: P3(34, 5, -4), to: P3(33, 5, -5), look: P3(18, 3, -15) } },
          5: { cam: onHeart, fx: { flash: true, shake: 1.2, light: true } },
          6: { cam: wide, fx: { hide: ["heart"], show: ["broken"], flash: true, shake: 1.8 } },
          7: {
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
        1: { fx: { rear: "king", night: true } },
        2: { fx: { rear: "king", fire: "king", night: true } },
        3: { fx: { night: true } },
        4: { cam: wide, fx: { horn: true, flash: true, shake: 1.4 } },
      },
    }),
    stage("dragon_rage", DK, true, court(true), {
      wide,
      music: "dread",
      all: { night: true },
      per: {
        0: { fx: { black: true } },
        1: { fx: { rear: "king", night: true } },
        3: {
          fx: { rear: "king", fire: "king", shake: 1.2, night: true },
          moves: ["cinderjaw", "rimefang", "scorchwind", "tidewyrm"].map((d, i) => ({
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
        music: "dread",
        per: {
          0: { cam: onHeart, fx: { light: true, night: true } },
          1: {
            cam: {
              from: P3(30, 4, -24),
              to: P3(60, 80, 0),
              look: P3(12, 6, -18),
              lookTo: P3(200, 120, 0),
            },
            fx: { light: true, flash: true },
          },
          2: {
            cam: { from: P3(27, 1.6, 1), look: P3(26, 0.8, 0) },
            fx: { black: true, shake: 1.5, flash: true },
          },
        },
      },
    ),
    stage("dragon_court", DK, true, court(true), {
      wide,
      per: {
        1: {
          cam: {
            from: P3(30, 6, 0),
            to: P3(30, 7, -10),
            look: P3(0, 8, -30),
            lookTo: P3(0, 8, 30),
          },
        },
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
        per: {
          0: { cam: onHeart, fx: { hide: ["heart"], show: ["whole"], light: true, flash: true } },
          1: { cam: onHeart, fx: { light: true } },
          5: { fx: { flash: true, shake: 0.6 } },
          7: { cam: onHeart, fx: { light: true } },
          8: { fx: { rear: "king" } },
        },
      },
    ),
    stage(
      "dragon_lumen_returns",
      DK,
      false,
      court(false, {
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
          look: "lumen",
          hidden: true,
        },
      }),
      {
        wide,
        per: {
          2: { cam: onHeart, fx: { light: true } },
          3: { cam: onHeart, fx: { show: ["lumen_dragon"], light: true, flash: true } },
          7: { cam: wide, fx: { light: true } },
          8: { fx: { rear: "cinderjaw" } },
          9: {
            cam: { from: P3(40, 6, -20), look: P3(2, 10, -30), lookTo: P3(-300, 120, -200) },
            moves: [{ actor: "cinderjaw", to: P(-600, -400), y: 160, dur: 7 }],
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
        music: "dread",
        per: {
          0: {
            moves: [{ actor: d, to: P(30, 10), y: 18, dur: 5, heading: at.heading + Math.PI }],
            fx: { fire: d, darken: true, shake: 0.8 },
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
        elder: { ...ELDER, at: elder, heading: face(elder, you) },
        rex: { kind: "racer", look: "rex", at: P(-4, -6), heading: face(P(-4, -6), elder) },
        brachio: { kind: "racer", look: "brachio", at: P(-4, 6), heading: face(P(-4, 6), elder) },
        stego: { kind: "racer", look: "stego", at: P(-9, -3), heading: face(P(-9, -3), elder) },
        raptor: { kind: "racer", look: "raptor", at: P(-9, 4), heading: face(P(-9, 4), elder) },
        lumen_dragon: {
          kind: "dragon",
          at: P(30, 18),
          heading: face(P(30, 18), you),
          scale: 0.9,
          look: "lumen",
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
        music: "riverbend",
        wide: { from: P3(-40, 30, -30), to: P3(-20, 12, -14), look: P3(4, 0, 0) },
        per: {
          1: {
            cam: { from: P3(-4, 3, 0), look: P3(60, 40, 0), lookTo: P3(200, 60, 0) },
            moves: [{ actor: "king", to: P(400, 0), y: 90, dur: 7 }],
          },
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
