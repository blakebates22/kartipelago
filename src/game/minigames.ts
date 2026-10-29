/**
 * The mini-games (Blake, Oct 26: two battle royales like the old kart racers' and two of
 * our own; Oct 27: keep Balloon Brawl's and Star Fall's rules, replace the other two with
 * Smugglers' Run and Crumble Rink). Four karts in an arena (tools/blender/prehistoric/
 * arena_region.py), the rivals driven by the games' own simple minds (seek a target, fire
 * at whoever's in front), the rules here as plain logic (no rendering: the screen,
 * src/screens/minigames.ts, draws them):
 *
 *   balloons   BALLOON BRAWL: three balloons each; a hit from any item pops one; with none
 *              left you're out. The last kart with balloons wins (or the most when the
 *              clock runs out).
 *   smugglers  SMUGGLERS' RUN: crates drop round the cove. Drive over one to grab it and
 *              take it to your crew's dock; a crate's heavy (you're slower carrying it).
 *              Ram a carrier, or hit them with an item, and they drop it. Five delivered
 *              wins.
 *   crumble    CRUMBLE RINK: the floor is ice tiles over a crevasse. A tile cracks when a
 *              kart drives over it; drive onto a cracked tile and it breaks and falls a
 *              moment later (keep going and you're across). The edge crumbles in every
 *              few seconds. Fall and you're out; the last kart on the ice wins.
 *   stars      STAR FALL: stars fall out of the sky (their shadows first); drive through
 *              one where it lands to catch it (gold ones are worth three). A hit knocks one
 *              out of you. First to 15 wins.
 */
import type { DeviceReading } from "../core/input";

export type MiniGameId = "balloons" | "smugglers" | "crumble" | "stars";

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
    id: "smugglers",
    name: "Smugglers' Run",
    arena: "arena_docks",
    kind: "own",
    blurb:
      "GRAB A FALLING CRATE AND RUN IT TO YOUR DOCK. RAM A CARRIER TO MAKE THEM DROP IT. FIVE WINS.",
    seconds: 180,
  },
  {
    id: "crumble",
    name: "Crumble Rink",
    arena: "arena_rink",
    kind: "battle",
    blurb:
      "THIN ICE: IT CRACKS WHERE YOU DRIVE, AND CRACKED ICE BREAKS UNDER THE NEXT KART. LAST ON THE ICE WINS.",
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
  /** Each crew's dock (Smugglers' Run), in the karts' order. */
  docks: { x: number; z: number; y: number; color: string }[];
  /** Where crates drop (Smugglers' Run). */
  crateSpawn?: { x: number; z: number; y: number; r: number };
  /** The ice (Crumble Rink): its centre, height, radius and tile size. */
  rink?: { x: number; z: number; y: number; r: number; tile: number };
  /** The upper level (the two-storey arenas): a ring deck round the middle, its centre
   * line's radius, its width and its height. */
  deck?: { r: number; w: number; y: number };
  /** The ramps between the levels: the foot (x, z) and the top (tx, tz). */
  ramps: { x: number; z: number; tx: number; tz: number }[];
}

/** On the upper level? (Over the deck's ring and up at its height.) */
export function onDeck(arena: Arena, p: { x: number; z: number; y?: number }): boolean {
  const d = arena.deck;
  if (!d) return false;
  const r = Math.hypot(p.x, p.z);
  return Math.abs(r - d.r) < d.w / 2 + 0.5 && (p.y ?? -Infinity) > d.y - 1.6;
}

/** Under the deck's ring (its footprint), whatever the height. */
export function overDeck(arena: Arena, x: number, z: number): boolean {
  const d = arena.deck;
  return Boolean(d) && Math.abs(Math.hypot(x, z) - d!.r) < d!.w / 2 - 0.5;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** An arena's things from its package's entities. */
export function parseArena(entities: unknown[]): Arena {
  const a: Arena = { spawns: [], radius: 60, docks: [], ramps: [] };
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
    else if (o.type === "dock")
      a.docks[num(o.index, a.docks.length)] = {
        x: num(o.x, 0),
        z: num(o.z, 0),
        y: num(o.y, 0),
        color: String(o.color ?? "red"),
      };
    else if (o.type === "crate_spawn")
      a.crateSpawn = { x: num(o.x, 0), z: num(o.z, 0), y: num(o.y, 0), r: num(o.r, 30) };
    else if (o.type === "deck") a.deck = { r: num(o.r, 30), w: num(o.w, 16), y: num(o.y, 6) };
    else if (o.type === "ramp")
      a.ramps[num(o.index, a.ramps.length)] = {
        x: num(o.x, 0),
        z: num(o.z, 0),
        tx: num(o.tx, 0),
        tz: num(o.tz, 0),
      };
    else if (o.type === "rink")
      a.rink = {
        x: num(o.x, 0),
        z: num(o.z, 0),
        y: num(o.y, 0),
        r: num(o.r, 40),
        tile: num(o.tile, 2.6),
      };
  }
  a.spawns = a.spawns.filter(Boolean);
  a.docks = a.docks.filter(Boolean);
  a.ramps = a.ramps.filter(Boolean);
  return a;
}

// ---------------------------------------------------------------- the rules

export interface Crate {
  x: number;
  z: number;
  /** Seconds until it lands (> 0: falling, its shadow showing). */
  fall: number;
  /** Who's carrying it (-1: on the ground). */
  carrier: number;
  /** Up on the deck (it fell there, or was dropped there). */
  high?: boolean;
}

export interface Star {
  x: number;
  z: number;
  /** Seconds until it lands (> 0: falling, its shadow showing), then how long it stays. */
  fall: number;
  life: number;
  gold: boolean;
  /** Up on the deck (it fell on it). */
  high?: boolean;
}

/** Crumble Rink's ice: hexagonal tiles (pointy-top), each solid, cracking or gone. */
export interface Ice {
  readonly x: Float32Array;
  readonly z: Float32Array;
  /** 0 solid; 1 cracked (driven over once); 3 breaking (driven onto again, or the edge
   * crumbling: it falls when its timer runs out); 2 gone. */
  readonly state: Uint8Array;
  /** Seconds since it cracked (cracked), left to fall (breaking), since it fell (gone). */
  readonly timer: Float32Array;
  /** Its distance from the middle, in tiles (the edge crumbles in by these). */
  readonly ring: Uint8Array;
  readonly size: number;
  readonly y: number;
  /** The tile under a point (-1: none). */
  at(x: number, z: number): number;
}

export function makeIce(rink: NonNullable<Arena["rink"]>): Ice {
  const size = rink.tile;
  const w = Math.sqrt(3) * size;
  const xs: number[] = [];
  const zs: number[] = [];
  const rings: number[] = [];
  const index = new Map<string, number>();
  const n = Math.ceil(rink.r / (1.5 * size)) + 2;
  for (let r = -n; r <= n; r++)
    for (let q = -n; q <= n; q++) {
      const x = w * (q + r / 2);
      const z = 1.5 * size * r;
      if (Math.hypot(x, z) > rink.r - size * 0.5) continue;
      index.set(`${q},${r}`, xs.length);
      xs.push(rink.x + x);
      zs.push(rink.z + z);
      rings.push(Math.max(Math.abs(q), Math.abs(r), Math.abs(q + r)));
    }
  const ice: Ice = {
    x: Float32Array.from(xs),
    z: Float32Array.from(zs),
    state: new Uint8Array(xs.length),
    timer: new Float32Array(xs.length),
    ring: Uint8Array.from(rings),
    size,
    y: rink.y,
    at(px, pz) {
      // Pixel to axial, then cube rounding.
      const lx = px - rink.x;
      const lz = pz - rink.z;
      const fr = lz / (1.5 * size);
      const fq = lx / w - fr / 2;
      const fs = -fq - fr;
      let q = Math.round(fq);
      let r = Math.round(fr);
      const s = Math.round(fs);
      const dq = Math.abs(q - fq);
      const dr = Math.abs(r - fr);
      const ds = Math.abs(s - fs);
      if (dq > dr && dq > ds) q = -r - s;
      else if (dr > ds) r = -q - s;
      return index.get(`${q},${r}`) ?? -1;
    },
  };
  return ice;
}

export interface MiniGame {
  readonly info: MiniGameInfo;
  readonly arena: Arena;
  /** Each kart's score: balloons left, crates delivered, seconds on the ice, stars. */
  readonly score: number[];
  /** Out of the game (Balloon Brawl, Crumble Rink). */
  readonly out: boolean[];
  readonly crates: Crate[];
  readonly stars: Star[];
  /** Crumble Rink's ice (undefined in the other games). */
  readonly ice: Ice | undefined;
  /** Seconds left. */
  readonly clock: number;
  /** The winner once it's over (index), or undefined. */
  readonly winner: number | undefined;
  /** What just happened, for sound and the screen ("pop", "grab", "dock", "drop", "bump",
   * "crack", "fall", "star"...), with whose it was. */
  readonly news: { what: string; who: number }[];
  step(karts: Kart[], dt: number): void;
  /** A kart was hit by an item (not blocked by a shield). */
  hit(i: number): void;
  /** Is this kart carrying a crate (Smugglers' Run: it's slower)? */
  carrying(i: number): boolean;
  /** Where a rival should drive now. */
  target(i: number, karts: Kart[]): { x: number; z: number; high?: boolean };
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
  // Smugglers' Run.
  cratesToWin: 5,
  maxCrates: 5,
  crateEvery: 2.6,
  crateFall: 2.0,
  cratePick: 3.6,
  dockRadius: 7,
  /** A carrier's top speed (of their own). */
  carrySpeed: 0.72,
  /** Ram a carrier: this close, this fast. */
  bumpDist: 3.4,
  bumpSpeed: 7,
  /** After dropping one, how long before you can grab again. */
  dropCooldown: 1.2,
  // Crumble Rink: thin ice. The first kart over a tile cracks it; driving onto a cracked
  // tile breaks it (it falls a moment later: keep going and you're across).
  /** Seconds from a tile breaking to its fall. */
  breakSec: 0.5,
  /** A kart cracks the tile under it only when moving at least this fast (standing on
   * the start doesn't). */
  crackSpeed: 3,
  /** The first seconds nothing cracks (the countdown). */
  graceSec: 4,
  /** The edge crumbles in a ring every this many seconds. */
  edgeEvery: 10,
  // Star Fall.
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
  const cooldown = new Array<number>(karts).fill(0);
  const crates: Crate[] = [];
  const stars: Star[] = [];
  const ice = info.id === "crumble" && arena.rink ? makeIce(arena.rink) : undefined;
  let clock = info.seconds;
  let played = 0;
  let winner: number | undefined;
  let crateIn = 0;
  let starIn = 0;
  let edgeIn = RULES.edgeEvery;
  let edgeRing = ice ? Math.max(...ice.ring) : 0;
  /** The tile each kart was on last step (Crumble Rink: a tile breaks as you drive onto
   * it, not while you're on it). */
  const onTile = new Array<number>(karts).fill(-1);
  /** Seconds each kart lasted on the ice (Crumble Rink's tie-break). */
  const lasted = new Array<number>(karts).fill(0);
  const goals: ({ x: number; z: number; t: number } | undefined)[] = new Array(karts);
  const news: { what: string; who: number }[] = [];
  const say = (what: string, who: number) => news.push({ what, who });
  /** The karts as last stepped (where a dropped crate lands, which level). */
  let lastKarts: Kart[] = [];
  /** Is kart k at the level of something there (high: on the deck)? */
  const sameLevel = (k: Kart, high: boolean | undefined) =>
    !arena.deck || onDeck(arena, k) === Boolean(high);

  const dockOf = (i: number) => arena.docks[i % Math.max(1, arena.docks.length)];
  const randomSpot = (r: number) => {
    const a = rand() * Math.PI * 2;
    const d = r * Math.sqrt(rand());
    return { x: Math.sin(a) * d, z: Math.cos(a) * d };
  };
  const best = () =>
    score
      .map((_, i) => i)
      .sort(
        (a, b) =>
          Number(out[a]) - Number(out[b]) ||
          score[b]! - score[a]! ||
          lasted[b]! - lasted[a]! ||
          a - b,
      );
  const drop = (i: number) => {
    const c = crates.find((c) => c.carrier === i);
    if (!c) return false;
    c.carrier = -1;
    c.x += (rand() - 0.5) * 5;
    c.z += (rand() - 0.5) * 5;
    c.high = Boolean(lastKarts[i]) && onDeck(arena, lastKarts[i]!) && overDeck(arena, c.x, c.z);
    cooldown[i] = RULES.dropCooldown;
    return true;
  };
  const solidAround = (x: number, z: number, r: number) => {
    if (!ice) return 0;
    let n = 0;
    for (let t = 0; t < ice.state.length; t++)
      if (ice.state[t] === 0 && Math.hypot(ice.x[t]! - x, ice.z[t]! - z) < r) n++;
    return n;
  };

  const game: MiniGame = {
    info,
    arena,
    score,
    out,
    crates,
    stars,
    ice,
    get clock() {
      return clock;
    },
    get winner() {
      return winner;
    },
    news,
    standings: best,
    carrying: (i) => crates.some((c) => c.carrier === i),
    step(ks, dt) {
      news.length = 0;
      lastKarts = ks;
      if (winner !== undefined) return;
      clock -= dt;
      played += dt;
      for (let i = 0; i < karts; i++) {
        immune[i] = Math.max(0, immune[i]! - dt);
        cooldown[i] = Math.max(0, cooldown[i]! - dt);
      }
      if (info.id === "balloons") {
        const left = out.map((o, i) => (o ? -1 : i)).filter((i) => i >= 0);
        if (left.length <= 1) winner = left[0] ?? best()[0];
      } else if (info.id === "smugglers") {
        // New crates out of the sky now and then (their shadows first).
        crateIn -= dt;
        const s = arena.crateSpawn ?? { x: 0, z: 0, y: 0, r: 30 };
        if (crateIn <= 0 && crates.length < RULES.maxCrates) {
          const p = randomSpot(s.r);
          crates.push({ x: s.x + p.x, z: s.z + p.z, fall: RULES.crateFall, carrier: -1 });
          crateIn = RULES.crateEvery;
        }
        for (const c of crates) if (c.fall > 0) c.fall -= dt;
        for (let i = 0; i < karts; i++) {
          const k = ks[i]!;
          const held = crates.find((c) => c.carrier === i);
          if (held) {
            held.x = k.x;
            held.z = k.z;
            const home = dockOf(i);
            if (home && Math.hypot(k.x - home.x, k.z - home.z) < RULES.dockRadius) {
              crates.splice(crates.indexOf(held), 1);
              score[i]! += 1;
              say("dock", i);
            }
            continue;
          }
          if (cooldown[i]! > 0) continue;
          const free = crates.find(
            (c) =>
              c.carrier < 0 &&
              c.fall <= 0 &&
              Math.hypot(c.x - k.x, c.z - k.z) < RULES.cratePick &&
              sameLevel(k, c.high),
          );
          if (free) {
            free.carrier = i;
            say("grab", i);
          }
        }
        // Rammed: a kart driving into a carrier knocks the crate loose.
        for (let i = 0; i < karts; i++) {
          if (!game.carrying(i) || immune[i]! > 0) continue;
          const k = ks[i]!;
          const by = ks.findIndex(
            (o, j) =>
              j !== i &&
              Math.abs(o.speed) > RULES.bumpSpeed &&
              Math.hypot(o.x - k.x, o.z - k.z) < RULES.bumpDist,
          );
          if (by >= 0 && drop(i)) {
            immune[i] = RULES.hitImmuneSec;
            say("bump", by);
            say("drop", i);
          }
        }
        const w = score.findIndex((v) => v >= RULES.cratesToWin);
        if (w >= 0) winner = w;
      } else if (info.id === "crumble" && ice) {
        if (played > RULES.graceSec) {
          // Where karts drive, the ice cracks; onto cracked ice, it breaks.
          for (let i = 0; i < karts; i++) {
            if (out[i]) continue;
            const k = ks[i]!;
            const t = ice.at(k.x, k.z);
            const entered = t !== onTile[i];
            onTile[i] = t;
            if (t < 0 || Math.abs(k.speed) <= RULES.crackSpeed) continue;
            if (ice.state[t] === 0) {
              ice.state[t] = 1;
              ice.timer[t] = 0;
              say("crack", i);
            } else if (ice.state[t] === 1 && entered) {
              ice.state[t] = 3;
              ice.timer[t] = RULES.breakSec;
              say("break", i);
            }
          }
          // And the edge crumbles in, a ring at a time.
          edgeIn -= dt;
          if (edgeIn <= 0 && edgeRing > 2) {
            edgeIn = RULES.edgeEvery;
            for (let t = 0; t < ice.state.length; t++)
              if (ice.ring[t]! >= edgeRing && (ice.state[t] === 0 || ice.state[t] === 1)) {
                ice.state[t] = 3;
                ice.timer[t] = RULES.breakSec + 0.6 + rand() * 1.6;
              }
            edgeRing -= 1;
            say("edge", -1);
          }
        }
        for (let t = 0; t < ice.state.length; t++) {
          if (ice.state[t] === 3) {
            ice.timer[t]! -= dt;
            if (ice.timer[t]! <= 0) {
              ice.state[t] = 2;
              ice.timer[t] = 0;
            }
          } else ice.timer[t]! += dt;
        }
        // Over a hole, or off the ice: you fall.
        for (let i = 0; i < karts; i++) {
          if (out[i]) continue;
          const k = ks[i]!;
          const t = ice.at(k.x, k.z);
          if (t < 0 || ice.state[t] === 2) {
            out[i] = true;
            say("fall", i);
          } else {
            lasted[i] = played;
            score[i] = Math.floor(played);
          }
        }
        const left = out.map((o, i) => (o ? -1 : i)).filter((i) => i >= 0);
        if (left.length <= 1) winner = left[0] ?? best()[0];
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
            // (One falling over the deck's ring lands on the deck.)
            high: overDeck(arena, p.x, p.z),
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
            (k, i) =>
              !out[i] &&
              Math.hypot(k.x - st.x, k.z - st.z) < RULES.starPick &&
              sameLevel(k, st.high),
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
      if (winner === undefined && clock <= 0) {
        // (Crumble Rink, out of time: whoever's on the most ice round them.)
        if (ice) {
          const alive = out.map((o, i) => (o ? -1 : i)).filter((i) => i >= 0);
          winner = alive.reduce(
            (a, b) =>
              solidAround(ks[b]!.x, ks[b]!.z, 10) > solidAround(ks[a]!.x, ks[a]!.z, 10) ? b : a,
            alive[0] ?? best()[0]!,
          );
        } else winner = best()[0];
      }
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
      } else if (info.id === "smugglers") {
        if (drop(i)) say("drop", i);
      } else if (info.id === "stars") {
        if (score[i]! > 0) {
          score[i]! -= 1;
          say("knock", i);
        }
      }
    },
    target(i, ks) {
      const k = ks[i]!;
      const dist = (p: { x: number; z: number }) => Math.hypot(p.x - k.x, p.z - k.z);
      const near = <T extends { x: number; z: number }>(list: T[]) =>
        list.reduce<T | undefined>((a, b) => (!a || dist(b) < dist(a) ? b : a), undefined);
      if (info.id === "smugglers") {
        if (game.carrying(i)) return dockOf(i) ?? { x: 0, z: 0 };
        const free = near(crates.filter((c) => c.carrier < 0 && c.fall < 0.8));
        // A loose crate near enough, or else go and ram whoever's carrying one.
        const carrier = near(
          ks
            .filter((_, j) => j !== i && game.carrying(j))
            .map((o) => ({ x: o.x, z: o.z, high: onDeck(arena, o) })),
        );
        if (free && (!carrier || dist(free) < dist(carrier) * 1.5)) return free;
        if (carrier) return carrier;
        return arena.crateSpawn ?? { x: 0, z: 0 };
      }
      if (info.id === "crumble" && ice) {
        // A spot on solid ice with plenty of solid ice round it, not too far; picked
        // afresh now and then, or when the ice under the goal goes.
        const g = goals[i];
        const t = g ? ice.at(g.x, g.z) : -1;
        if (g && g.t > played && t >= 0 && ice.state[t] === 0 && dist(g) > 5) return g;
        let bestT = -1;
        let bestV = -Infinity;
        for (let n = 0; n < 24; n++) {
          const c = Math.floor(rand() * ice.state.length);
          if (ice.state[c] !== 0) continue;
          const p = { x: ice.x[c]!, z: ice.z[c]! };
          const d = dist(p);
          if (d < 6 || d > 40) continue;
          // (How much cracked ice lies on the way: crossing it breaks it.)
          let bad = 0;
          for (let f = 0.15; f < 1; f += 0.15) {
            const u = ice.at(k.x + (p.x - k.x) * f, k.z + (p.z - k.z) * f);
            if (u < 0 || ice.state[u] !== 0) bad += u >= 0 && ice.state[u] === 1 ? 1 : 4;
          }
          const v = solidAround(p.x, p.z, 9) - d * 0.15 - ice.ring[c]! * 0.6 - bad * 6;
          if (v > bestV) {
            bestV = v;
            bestT = c;
          }
        }
        if (bestT >= 0) {
          goals[i] = { x: ice.x[bestT]!, z: ice.z[bestT]!, t: played + 2.5 };
          return goals[i]!;
        }
        return arena.rink ?? { x: 0, z: 0 };
      }
      if (info.id === "stars") {
        const landed = stars.filter((s) => s.fall < 1.2);
        const pick = landed.reduce<Star | undefined>((a, s) => {
          const v = (s.gold ? 3 : 1) / (8 + dist(s));
          const va = a ? (a.gold ? 3 : 1) / (8 + dist(a)) : -1;
          return v > va ? s : a;
        }, undefined);
        return pick ?? { x: 0, z: 0 };
      }
      // Balloon Brawl: the nearest kart still in (on the same level counts for more).
      const rivals = ks
        .map((o, j) => ({ ...o, j, high: onDeck(arena, o) }))
        .filter((o) => o.j !== i && !out[o.j]);
      const mine = onDeck(arena, k);
      return (
        rivals.reduce<(typeof rivals)[number] | undefined>(
          (a, b) =>
            !a || dist(b) * (b.high === mine ? 1 : 1.8) < dist(a) * (a.high === mine ? 1 : 1.8)
              ? b
              : a,
          undefined,
        ) ?? { x: 0, z: 0 }
      );
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

// ---------------------------------------------------------------- finding the way

/** Where to drive for a target, by the levels (the two-storey arenas): up a ramp to reach
 * one on the deck (to its foot first, then up it), round the ring on the deck itself,
 * straight off the deck's edge for one below. */
export function waypoint(
  arena: Arena,
  k: Kart,
  tg: { x: number; z: number; high?: boolean },
): { x: number; z: number } {
  const d = arena.deck;
  if (!d || !arena.ramps.length) return tg;
  const up = onDeck(arena, k);
  const want = Boolean(tg.high);
  if (up && want) {
    // Round the ring: never more than a bend ahead, so the line stays on the deck.
    const ak = Math.atan2(k.x, k.z);
    const at = Math.atan2(tg.x, tg.z);
    const da = Math.atan2(Math.sin(at - ak), Math.cos(at - ak));
    if (Math.abs(da) * d.r < 10) return tg;
    const a = ak + Math.sign(da) * Math.min(Math.abs(da), 0.45);
    return { x: Math.sin(a) * d.r, z: Math.cos(a) * d.r };
  }
  if (up === want) return tg;
  if (!up && want) {
    // Climb: the ramp with the shortest way, foot then top then on.
    let best = arena.ramps[0]!;
    let bv = Infinity;
    for (const r of arena.ramps) {
      const v = Math.hypot(r.x - k.x, r.z - k.z) + Math.hypot(r.tx - tg.x, r.tz - tg.z);
      if (v < bv) {
        bv = v;
        best = r;
      }
    }
    const ux = best.tx - best.x;
    const uz = best.tz - best.z;
    const len = Math.hypot(ux, uz) || 1;
    // On it already (between its foot and top, inside its width): straight on up.
    const t = ((k.x - best.x) * ux + (k.z - best.z) * uz) / (len * len);
    const side = Math.abs(((k.x - best.x) * uz - (k.z - best.z) * ux) / len);
    if (t > -0.15 && t < 1.2 && side < 5)
      return { x: best.tx + (ux / len) * 6, z: best.tz + (uz / len) * 6 };
    // Else to a spot out before its foot, to come at it straight.
    return { x: best.x - (ux / len) * 7, z: best.z - (uz / len) * 7 };
  }
  return tg;
}

/** Steer round what's in the way: try the line to (tx, tz), then lines turned a little
 * either side, further and further, and take the first clear for a few metres. */
export function clearLine(
  k: Kart,
  tx: number,
  tz: number,
  fits: (x: number, z: number, y: number) => boolean,
): { x: number; z: number } {
  const want = Math.atan2(tx - k.x, tz - k.z);
  const dist = Math.hypot(tx - k.x, tz - k.z);
  for (const off of [0, 0.35, -0.35, 0.7, -0.7, 1.05, -1.05, 1.4, -1.4]) {
    const a = want + off;
    let ok = true;
    for (const r of [2.5, 5, 8]) {
      if (r > dist + 2) break;
      if (!fits(k.x + Math.sin(a) * r, k.z + Math.cos(a) * r, k.y + 1.2)) {
        ok = false;
        break;
      }
    }
    if (ok)
      return off === 0
        ? { x: tx, z: tz }
        : { x: k.x + Math.sin(a) * 10, z: k.z + Math.cos(a) * 10 };
  }
  return { x: tx, z: tz };
}

/** Crumble Rink's rivals (Blake, Oct 29: "the cpus just flew off the edge almost
 * instantly ... we want this one to be hard, but not ridiculously hard"): never faster
 * than they can stop on ice, slowing to arrive; looking ahead along where they're
 * sliding, and if that's off the ice or onto a hole, braking and turning for the
 * safest way (solid ice the whole way); away from the edge as it crumbles in. */
export function iceDrive(
  m: Mind,
  k: Kart,
  game: MiniGame,
  tg: { x: number; z: number },
  dt: number,
): DeviceReading {
  const ice = game.ice!;
  const here = ice.at(k.x, k.z);
  // (Cracked ice breaks under the next kart onto it: as bad as a hole, except the tile
  // it's on now.)
  const solid = (x: number, z: number) => {
    const t = ice.at(x, z);
    return t >= 0 && (ice.state[t] === 0 || t === here);
  };
  const safe = (a: number, reach: number) => {
    for (let r = 2; r <= reach; r += 1.5)
      if (!solid(k.x + Math.sin(a) * r, k.z + Math.cos(a) * r)) return false;
    return true;
  };
  const v = Math.abs(k.speed);
  // How far it'll slide: look that far ahead (and a little more).
  const reach = 4 + v * 0.7;
  let aimA = Math.atan2(tg.x - k.x, tg.z - k.z);
  if (!safe(aimA, Math.min(reach, Math.hypot(tg.x - k.x, tg.z - k.z) + 2))) {
    let found = false;
    for (const off of [0.4, -0.4, 0.8, -0.8, 1.2, -1.2, 1.7, -1.7, 2.3, -2.3, Math.PI]) {
      if (safe(aimA + off, reach)) {
        aimA += off;
        found = true;
        break;
      }
    }
    const mid = game.arena.rink ?? { x: 0, z: 0 };
    if (!found) aimA = Math.atan2(mid.x - k.x, mid.z - k.z); // (toward the middle)
  }
  const err = Math.atan2(Math.sin(aimA - k.heading), Math.cos(aimA - k.heading));
  const ahead = safe(k.heading, reach);
  const dist = Math.hypot(tg.x - k.x, tg.z - k.z);
  // Speed: slow to arrive, slow to turn, and never fast on ice.
  const vmax = Math.min(14, 3 + dist * 0.6) * (Math.abs(err) > 0.8 ? 0.5 : 1);
  m.stuck = v < 1 ? m.stuck + dt : 0;
  const steer = Math.max(-1, Math.min(1, -err * 2.4));
  if (!ahead && v > 3) return { throttle: 0, brake: 1, steer, drift: false, item: false };
  return {
    throttle: v < vmax ? (Math.abs(err) > 1.4 ? 0.4 : 0.85) : 0,
    brake: v > vmax + 2 ? 0.6 : 0,
    steer,
    drift: false,
    item: false,
  };
}
