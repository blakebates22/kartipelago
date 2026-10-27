/**
 * The mini-games (Blake, Oct 26: two battle royales like the old kart racers' and two of
 * our own; for now they unlock nothing). Four karts in an arena (tools/blender/
 * prehistoric/arena_region.py), the rivals driven by the games' own simple minds (seek a
 * target, fire at whoever's in front), the rules here as plain logic (no rendering: the
 * screen, src/screens/minigames.ts, draws them):
 *
 *   balloons  BALLOON BRAWL: three balloons each; a hit from any item pops one; with none
 *             left you're out. The last kart with balloons wins (or the most when the
 *             clock runs out).
 *   eggs      EGG SCRAMBLE: eggs roll out of the middle; drive over one to pick it up,
 *             take it home to your nest; drive into a rival's nest to steal one. Hit
 *             while carrying, you drop it. Three in your nest wins.
 *   crown     CROWN HILL: hold the crown's ring on top of the hill: the one holding it
 *             scores while they stay in it (shove them out to take it). First to 30
 *             seconds wins.
 *   stars     STAR FALL: stars fall out of the sky (their shadows first); drive through
 *             one where it lands to catch it (gold ones are worth three). A hit knocks one
 *             out of you. First to 15 wins.
 */
import type { DeviceReading } from "../core/input";

export type MiniGameId = "balloons" | "eggs" | "crown" | "stars";

export interface MiniGameInfo {
  id: MiniGameId;
  name: string;
  arena: string;
  /** Battle royale (like the old kart racers' battles) or one of our own. */
  kind: "battle" | "own";
  blurb: string;
  /** Seconds on the clock. */
  seconds: number;
}

export const MINIGAMES: MiniGameInfo[] = [
  {
    id: "balloons",
    name: "Balloon Brawl",
    arena: "arena_bowl",
    kind: "battle",
    blurb: "THREE BALLOONS EACH. EVERY HIT POPS ONE. LAST KART FLYING WINS.",
    seconds: 180,
  },
  {
    id: "eggs",
    name: "Egg Scramble",
    arena: "arena_nest",
    kind: "battle",
    blurb: "GRAB AN EGG, TAKE IT HOME, STEAL FROM THE OTHERS' NESTS. THREE IN YOUR NEST WINS.",
    seconds: 180,
  },
  {
    id: "crown",
    name: "Crown Hill",
    arena: "arena_crown",
    kind: "own",
    blurb:
      "HOLD THE CROWN'S RING ON THE HILL. SHOVE THE HOLDER OUT TO TAKE IT. FIRST TO 30 SECONDS.",
    seconds: 150,
  },
  {
    id: "stars",
    name: "Star Fall",
    arena: "arena_stars",
    kind: "own",
    blurb: "CATCH THE FALLING STARS WHERE THEY LAND. GOLD ONES ARE WORTH THREE. FIRST TO 15.",
    seconds: 120,
  },
];

export const minigameById = (id: string) => MINIGAMES.find((m) => m.id === id);

export interface Kart {
  x: number;
  y: number;
  z: number;
  heading: number;
  speed: number;
}

export interface Arena {
  spawns: { x: number; z: number; heading: number }[];
  radius: number;
  nests: { x: number; z: number; y: number; color: string }[];
  eggSpawn?: { x: number; z: number; y: number; r: number };
  crown?: { x: number; z: number; y: number; r: number };
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** An arena's things from its package's entities. */
export function parseArena(entities: unknown[]): Arena {
  const a: Arena = { spawns: [], radius: 60, nests: [] };
  for (const e of entities) {
    if (!e || typeof e !== "object") continue;
    const o = e as Record<string, unknown>;
    if (o.type === "arena_spawn")
      a.spawns[num(o.index, a.spawns.length)] = {
        x: num(o.x, 0),
        z: num(o.z, 0),
        heading: num(o.heading, 0),
      };
    else if (o.type === "arena") a.radius = num(o.radius, 60);
    else if (o.type === "nest")
      a.nests[num(o.index, a.nests.length)] = {
        x: num(o.x, 0),
        z: num(o.z, 0),
        y: num(o.y, 0),
        color: String(o.color ?? "red"),
      };
    else if (o.type === "egg_spawn")
      a.eggSpawn = { x: num(o.x, 0), z: num(o.z, 0), y: num(o.y, 0), r: num(o.r, 8) };
    else if (o.type === "crown_zone")
      a.crown = { x: num(o.x, 0), z: num(o.z, 0), y: num(o.y, 0), r: num(o.r, 10) };
  }
  a.spawns = a.spawns.filter(Boolean);
  a.nests = a.nests.filter(Boolean);
  return a;
}

// ---------------------------------------------------------------- the rules

export interface Egg {
  x: number;
  z: number;
  /** Who's carrying it (-1: on the ground), or in whose nest (`nest`). */
  carrier: number;
  nest: number;
}

export interface Star {
  x: number;
  z: number;
  /** Seconds until it lands (> 0: falling, its shadow showing), then how long it stays. */
  fall: number;
  life: number;
  gold: boolean;
}

export interface MiniGame {
  readonly info: MiniGameInfo;
  readonly arena: Arena;
  /** Each kart's score: balloons left, eggs in its nest, crown seconds, stars. */
  readonly score: number[];
  /** Out of the game (Balloon Brawl). */
  readonly out: boolean[];
  readonly eggs: Egg[];
  readonly stars: Star[];
  /** Who holds the crown's ring now (-1: nobody). */
  readonly holder: number;
  /** Seconds left. */
  readonly clock: number;
  /** The winner once it's over (index), or undefined. */
  readonly winner: number | undefined;
  /** What just happened, for sound and the screen ("pop", "egg", "steal", "drop",
   * "star", "nest"...), with whose it was. */
  readonly news: { what: string; who: number }[];
  step(karts: Kart[], dt: number): void;
  /** A kart was hit by an item (not blocked by a shield). */
  hit(i: number): void;
  /** Where a rival should drive now. */
  target(i: number, karts: Kart[]): { x: number; z: number };
  /** Standings: kart indices, best first. */
  standings(): number[];
}

/** A small, repeatable random sequence. */
function rng(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return ((s >>> 0) % 100000) / 100000;
  };
}

export const RULES = {
  lives: 3,
  hitImmuneSec: 2,
  eggsToWin: 3,
  eggPick: 3.5,
  nestRadius: 7,
  maxEggs: 7,
  eggEvery: 4,
  crownToWin: 30,
  starsToWin: 15,
  starEvery: 1.6,
  starFall: 2.2,
  starLife: 9,
  starPick: 3.5,
};

export function createMiniGame(
  info: MiniGameInfo,
  arena: Arena,
  karts: number,
  seed = 1,
): MiniGame {
  const rand = rng(seed);
  const score = new Array<number>(karts).fill(info.id === "balloons" ? RULES.lives : 0);
  const out = new Array<boolean>(karts).fill(false);
  const immune = new Array<number>(karts).fill(0);
  const eggs: Egg[] = [];
  const stars: Star[] = [];
  let clock = info.seconds;
  let winner: number | undefined;
  let holder = -1;
  const crownT = new Array<number>(karts).fill(0);
  const since = new Array<number>(karts).fill(0);
  let eggIn = 0;
  let starIn = 0;
  const news: { what: string; who: number }[] = [];
  const say = (what: string, who: number) => news.push({ what, who });

  const nestOf = (i: number) => arena.nests[i % Math.max(1, arena.nests.length)];
  const inNest = (i: number) => eggs.filter((e) => e.nest === i).length;
  const randomSpot = (r: number) => {
    const a = rand() * Math.PI * 2;
    const d = r * Math.sqrt(rand());
    return { x: Math.sin(a) * d, z: Math.cos(a) * d };
  };

  const best = () => {
    const order = score.map((_, i) => i).sort((a, b) => score[b]! - score[a]! || a - b);
    return order;
  };

  const game: MiniGame = {
    info,
    arena,
    score,
    out,
    eggs,
    stars,
    get holder() {
      return holder;
    },
    get clock() {
      return clock;
    },
    get winner() {
      return winner;
    },
    news,
    standings: best,
    step(ks, dt) {
      news.length = 0;
      if (winner !== undefined) return;
      clock -= dt;
      for (let i = 0; i < karts; i++) immune[i] = Math.max(0, immune[i]! - dt);
      if (info.id === "balloons") {
        const left = out.map((o, i) => (o ? -1 : i)).filter((i) => i >= 0);
        if (left.length <= 1) winner = left[0] ?? best()[0];
      } else if (info.id === "eggs") {
        // New eggs out of the middle now and then.
        eggIn -= dt;
        const s = arena.eggSpawn ?? { x: 0, z: 0, y: 0, r: 8 };
        if (eggIn <= 0 && eggs.length < RULES.maxEggs) {
          const p = randomSpot(s.r);
          eggs.push({ x: s.x + p.x, z: s.z + p.z, carrier: -1, nest: -1 });
          eggIn = RULES.eggEvery;
        }
        for (let i = 0; i < karts; i++) {
          const k = ks[i]!;
          const carrying = eggs.find((e) => e.carrier === i);
          const home = nestOf(i);
          if (carrying) {
            carrying.x = k.x;
            carrying.z = k.z;
            if (home && Math.hypot(k.x - home.x, k.z - home.z) < RULES.nestRadius) {
              carrying.carrier = -1;
              carrying.nest = i;
              const a = inNest(i) * 2.1;
              carrying.x = home.x + Math.sin(a) * 2;
              carrying.z = home.z + Math.cos(a) * 2;
              say("nest", i);
            }
            continue;
          }
          // Pick one up off the ground, or steal one from a rival's nest.
          const free = eggs.find(
            (e) => e.carrier < 0 && e.nest < 0 && Math.hypot(e.x - k.x, e.z - k.z) < RULES.eggPick,
          );
          if (free) {
            free.carrier = i;
            say("egg", i);
            continue;
          }
          for (let j = 0; j < karts; j++) {
            const n = nestOf(j);
            if (j === i || !n || Math.hypot(k.x - n.x, k.z - n.z) > RULES.nestRadius * 0.7)
              continue;
            const e = eggs.find((e) => e.nest === j);
            if (e) {
              e.nest = -1;
              e.carrier = i;
              say("steal", i);
              break;
            }
          }
        }
        for (let i = 0; i < karts; i++) score[i] = inNest(i);
        const w = score.findIndex((v) => v >= RULES.eggsToWin);
        if (w >= 0) winner = w;
      } else if (info.id === "crown") {
        const c = arena.crown ?? { x: 0, z: 0, y: 0, r: 10 };
        const inside = ks
          .map((k, i) => (Math.hypot(k.x - c.x, k.z - c.z) < c.r ? i : -1))
          .filter((i) => i >= 0);
        // The king of the hill: whoever holds the ring keeps it while they're in it (shove
        // them out to take it); with them gone, whoever's been in it longest.
        for (let i = 0; i < karts; i++) since[i] = inside.includes(i) ? since[i]! + dt : 0;
        if (!inside.includes(holder))
          holder = inside.length ? inside.reduce((a, b) => (since[b]! > since[a]! ? b : a)) : -1;
        if (holder >= 0) {
          crownT[holder]! += dt;
          score[holder] = Math.floor(crownT[holder]!);
          if (crownT[holder]! >= RULES.crownToWin) winner = holder;
        }
      } else if (info.id === "stars") {
        starIn -= dt;
        if (starIn <= 0) {
          const p = randomSpot(arena.radius - 8);
          stars.push({
            x: p.x,
            z: p.z,
            fall: RULES.starFall,
            life: RULES.starLife,
            gold: rand() < 0.15,
          });
          starIn = RULES.starEvery;
        }
        for (let s = stars.length - 1; s >= 0; s--) {
          const st = stars[s]!;
          if (st.fall > 0) {
            st.fall -= dt;
            continue;
          }
          st.life -= dt;
          const by = ks.findIndex(
            (k, i) => !out[i] && Math.hypot(k.x - st.x, k.z - st.z) < RULES.starPick,
          );
          if (by >= 0) {
            score[by]! += st.gold ? 3 : 1;
            say("star", by);
            stars.splice(s, 1);
          } else if (st.life <= 0) stars.splice(s, 1);
        }
        const w = score.findIndex((v) => v >= RULES.starsToWin);
        if (w >= 0) winner = w;
      }
      if (winner === undefined && clock <= 0) winner = best()[0];
      if (winner !== undefined) say("over", winner);
    },
    hit(i) {
      if (winner !== undefined || immune[i]! > 0) return;
      immune[i] = RULES.hitImmuneSec;
      if (info.id === "balloons") {
        if (out[i]) return;
        score[i] = Math.max(0, score[i]! - 1);
        say("pop", i);
        if (score[i] === 0) {
          out[i] = true;
          say("out", i);
        }
      } else if (info.id === "eggs") {
        const e = eggs.find((e) => e.carrier === i);
        if (e) {
          e.carrier = -1;
          e.x += (rand() - 0.5) * 6;
          e.z += (rand() - 0.5) * 6;
          say("drop", i);
        }
      } else if (info.id === "stars") {
        if (score[i]! > 0) {
          score[i]! -= 1;
          say("knock", i);
        }
      }
    },
    target(i, ks) {
      const k = ks[i]!;
      const near = <T extends { x: number; z: number }>(list: T[]) =>
        list.reduce<T | undefined>(
          (a, b) =>
            !a || Math.hypot(b.x - k.x, b.z - k.z) < Math.hypot(a.x - k.x, a.z - k.z) ? b : a,
          undefined,
        );
      if (info.id === "eggs") {
        if (eggs.some((e) => e.carrier === i)) return nestOf(i) ?? { x: 0, z: 0 };
        const free = near(eggs.filter((e) => e.carrier < 0 && e.nest < 0));
        if (free) return free;
        // Raid the fullest rival nest.
        let bestJ = -1;
        for (let j = 0; j < karts; j++)
          if (j !== i && (bestJ < 0 || inNest(j) > inNest(bestJ))) bestJ = j;
        if (bestJ >= 0 && inNest(bestJ) > 0) return nestOf(bestJ)!;
        return arena.eggSpawn ?? { x: 0, z: 0 };
      }
      if (info.id === "crown") {
        const c = arena.crown ?? { x: 0, z: 0, y: 0, r: 10 };
        // In the ring: circle it (a moving target's harder to shove out).
        // Someone else holds it: go and shove them out.
        if (holder >= 0 && holder !== i) return ks[holder]!;
        if (Math.hypot(k.x - c.x, k.z - c.z) < c.r) {
          const a = Math.atan2(k.x - c.x, k.z - c.z) + 0.9;
          return { x: c.x + Math.sin(a) * c.r * 0.5, z: c.z + Math.cos(a) * c.r * 0.5 };
        }
        return c;
      }
      if (info.id === "stars") {
        const landed = stars.filter((s) => s.fall < 1.2);
        const best = landed.reduce<Star | undefined>((a, s) => {
          const v = (s.gold ? 3 : 1) / (8 + Math.hypot(s.x - k.x, s.z - k.z));
          const va = a ? (a.gold ? 3 : 1) / (8 + Math.hypot(a.x - k.x, a.z - k.z)) : -1;
          return v > va ? s : a;
        }, undefined);
        return best ?? { x: 0, z: 0 };
      }
      // Balloon Brawl: the nearest kart still in.
      const rivals = ks.map((o, j) => ({ ...o, j })).filter((o) => o.j !== i && !out[o.j]);
      return near(rivals) ?? { x: 0, z: 0 };
    },
  };
  return game;
}

// ---------------------------------------------------------------- the rivals' minds

export interface Mind {
  stuck: number;
  reverse: number;
}

export const newMind = (): Mind => ({ stuck: 0, reverse: 0 });

/** Steer for (tx, tz): full throttle, easing off for a sharp turn; backing out when stuck
 * against something. Positive steer lowers the heading (src/vehicles/kart.ts). */
export function seek(m: Mind, k: Kart, tx: number, tz: number, dt: number): DeviceReading {
  const want = Math.atan2(tx - k.x, tz - k.z);
  const err = Math.atan2(Math.sin(want - k.heading), Math.cos(want - k.heading));
  if (m.reverse > 0) {
    m.reverse -= dt;
    return { throttle: 0, brake: 1, steer: err > 0 ? 1 : -1, drift: false, item: false };
  }
  m.stuck = Math.abs(k.speed) < 1.5 ? m.stuck + dt : 0;
  if (m.stuck > 1.4) {
    m.stuck = 0;
    m.reverse = 1.0;
  }
  const steer = Math.max(-1, Math.min(1, -err * 2.2));
  const d = Math.hypot(tx - k.x, tz - k.z);
  const throttle = Math.abs(err) > 1.6 ? 0.45 : d < 6 ? 0.6 : 1;
  return { throttle, brake: 0, steer, drift: false, item: false };
}

/** Fire now? A rival in front and in range (or anything to drop or use on yourself). */
export function shouldFire(
  i: number,
  k: Kart,
  karts: Kart[],
  color: string | null,
  out: boolean[],
): boolean {
  if (!color) return false;
  if (color === "blue" || color === "yellow") return Math.random() < 0.02;
  if (color === "green")
    return karts.some((o, j) => j !== i && !out[j] && Math.hypot(o.x - k.x, o.z - k.z) < 14);
  return karts.some((o, j) => {
    if (j === i || out[j]) return false;
    const d = Math.hypot(o.x - k.x, o.z - k.z);
    const a = Math.atan2(o.x - k.x, o.z - k.z);
    const err = Math.abs(Math.atan2(Math.sin(a - k.heading), Math.cos(a - k.heading)));
    return d < 45 && err < 0.4;
  });
}
