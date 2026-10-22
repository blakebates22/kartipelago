/**
 * Celestial Dragon Festival: the festival that grows lap by lap (track.json entity
 * "festival", written by tools/blender/prehistoric/cdf_town.py).
 *
 *   festival  {
 *     "length": lap length (m),
 *     "sites": [[x, y, z], ...]          where the city's rockets go up from
 *     "pieces": [{ "id", "stages": [2, 3], "at": lap distance, "cue": "gong" | "roar" | ...,
 *                  "bursts": [{ "t": seconds, "x", "y", "z", "pattern", "size",
 *                               "colors": [...], "from": [x, y, z], "yaw", "tilt" }] }]
 *     "lanterns": [[x, y, z, r], ...]    where sky lanterns are let go
 *     "observatory": [x, y, z, r]        the great golden rings (centre, size)
 *   }
 *
 * The festival has three stages, one per lap: the Opening Celebration (lap 1), the
 * Ceremony Intensifies (the middle laps) and the Grand Finale (the last lap, and after
 * the line). Each stage sets how often the city's rockets go up, how big and how varied
 * they are, how many lanterns rise, how bright the observatory and the flash of light on
 * the kingdom are. Inside the last lap everything keeps building to the finish.
 *
 * Over that, set pieces: choreographed displays keyed to places on the lap (where you
 * are, not the clock, so whoever's driving sees them as they reach the landmark): the
 * dragon drawn in gold over the observatory as you cross the Star Bridge on the last lap,
 * rings round the observatory's rings, golden rain over the palace, the salute rippling
 * along the skyline, the constellation, the grand finale over the finish.
 *
 * Purely visual (and sound): nothing here touches a kart, and the city's own rockets
 * follow the race clock and a fixed seed, so every race and every time trial sees the
 * same show. Pure (no three.js); game/festivalLife.ts draws it.
 */

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);
const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

export interface V3 {
  x: number;
  y: number;
  z: number;
}

export type Stage = 1 | 2 | 3;

export const PATTERNS = [
  "peony",
  "chrysanthemum",
  "willow",
  "glitter",
  "palm",
  "ring",
  "star",
  "dragon",
  "constellation",
  "comet",
] as const;
export type Pattern = (typeof PATTERNS)[number];

export interface ShowBurst {
  /** Seconds after the piece starts that it bursts (its rocket goes up before). */
  t: number;
  x: number;
  y: number;
  z: number;
  pattern: Pattern;
  /** Radius, metres. */
  size: number;
  colors: string[];
  /** Where its rocket goes up from (none: it just bursts). */
  from?: V3;
  /** Which way a flat pattern (ring, dragon, constellation) faces, radians about Y. */
  yaw: number;
  /** How far a ring leans out of upright, radians. */
  tilt: number;
}

export interface SetPiece {
  id: string;
  stages: Stage[];
  at: number;
  cue?: string;
  bursts: ShowBurst[];
}

export interface FestivalConfig {
  length: number;
  sites: V3[];
  pieces: SetPiece[];
  lanterns: (V3 & { r: number })[];
  observatory?: V3 & { r: number };
}

const v3 = (a: unknown): V3 | undefined =>
  Array.isArray(a) && a.length >= 3
    ? { x: num(a[0], 0), y: num(a[1], 0), z: num(a[2], 0) }
    : undefined;

function parsePattern(v: unknown): Pattern {
  return (PATTERNS as readonly string[]).includes(String(v)) ? (v as Pattern) : "peony";
}

export function parseFestival(e: Record<string, unknown>): FestivalConfig {
  const sites: V3[] = [];
  if (Array.isArray(e.sites))
    for (const s of e.sites) {
      const p = v3(s);
      if (p) sites.push(p);
    }
  const pieces: SetPiece[] = [];
  if (Array.isArray(e.pieces))
    for (const p of e.pieces) {
      if (!isObj(p)) continue;
      const stages = (Array.isArray(p.stages) ? p.stages : [3])
        .map((s) => Math.round(num(s, 3)))
        .filter((s): s is Stage => s === 1 || s === 2 || s === 3);
      const bursts: ShowBurst[] = [];
      if (Array.isArray(p.bursts))
        for (const b of p.bursts) {
          if (!isObj(b)) continue;
          bursts.push({
            t: Math.max(0, num(b.t, 0)),
            x: num(b.x, 0),
            y: num(b.y, 100),
            z: num(b.z, 0),
            pattern: parsePattern(b.pattern),
            size: Math.max(2, num(b.size, 30)),
            colors:
              Array.isArray(b.colors) && b.colors.length
                ? b.colors.map((c) => String(c))
                : ["#ffd060"],
            from: v3(b.from),
            yaw: num(b.yaw, 0),
            tilt: num(b.tilt, 0),
          });
        }
      bursts.sort((a, b) => a.t - b.t);
      pieces.push({
        id: String(p.id ?? `piece${pieces.length}`),
        stages: stages.length ? stages : [3],
        at: num(p.at, 0),
        cue: typeof p.cue === "string" ? p.cue : undefined,
        bursts,
      });
    }
  const lanterns: FestivalConfig["lanterns"] = [];
  if (Array.isArray(e.lanterns))
    for (const l of e.lanterns) {
      const p = v3(l);
      if (p && Array.isArray(l)) lanterns.push({ ...p, r: Math.max(5, num(l[3], 60)) });
    }
  const ob = Array.isArray(e.observatory) ? e.observatory : undefined;
  const obs = v3(ob);
  return {
    length: Math.max(1, num(e.length, 1)),
    sites,
    pieces,
    lanterns,
    observatory: obs && ob ? { ...obs, r: Math.max(5, num(ob[3], 30)) } : undefined,
  };
}

/** The stage for the racer's lap: the first lap opens, the last lap (and after the line)
 * is the grand finale, everything between intensifies. */
export function festivalStage(lap: number, laps: number, finished = false): Stage {
  if (finished || lap >= laps) return 3;
  if (lap <= 1) return 1;
  return 2;
}

/**
 * How festive it is (0..1): the stage's level, and inside the last lap rising all the
 * way to the line (u: how far round the lap, 0..1).
 */
export function festivalLevel(stage: Stage, u: number): number {
  const k = Math.max(0, Math.min(1, u));
  if (stage === 1) return 0.22 + 0.06 * k;
  if (stage === 2) return 0.5 + 0.1 * k;
  return 0.72 + 0.28 * k * k;
}

/** What each stage launches from the city between the set pieces. */
export interface AmbientStyle {
  /** Rockets a second. */
  rate: number;
  /** Burst radius, metres (min, max). */
  size: [number, number];
  patterns: Pattern[];
  colors: string[][];
  /** Chance a launch is a volley of several at once. */
  volley: number;
}

const RED_GOLD = ["#ff3a3a", "#ffd050", "#ffe8a0"];
const BLUE_GOLD = ["#5aa0ff", "#ffd050", "#e0f0ff"];
const PINK = ["#ff5ac8", "#ffb0e8", "#ffffff"];
const GOLD = ["#ffd060", "#ffb030", "#fff0b0"];
const GREEN = ["#4aff9a", "#ffd050", "#ffffff"];
const VIOLET = ["#b07aff", "#5ac8ff", "#ffffff"];
const RAINBOW = ["#ff3a3a", "#ffa030", "#ffe050", "#4aff9a", "#5aa0ff", "#b07aff"];

export const AMBIENT: Record<Stage, AmbientStyle> = {
  1: {
    rate: 1.4,
    size: [18, 30],
    patterns: ["peony", "peony", "chrysanthemum", "glitter"],
    colors: [RED_GOLD, BLUE_GOLD, GOLD],
    volley: 0.15,
  },
  2: {
    rate: 3.2,
    size: [22, 42],
    patterns: ["peony", "chrysanthemum", "willow", "glitter", "palm", "ring", "star"],
    colors: [RED_GOLD, BLUE_GOLD, GOLD, PINK, GREEN, VIOLET],
    volley: 0.3,
  },
  3: {
    rate: 4.6,
    size: [28, 56],
    patterns: ["peony", "chrysanthemum", "willow", "willow", "glitter", "palm", "ring", "star"],
    colors: [RED_GOLD, BLUE_GOLD, GOLD, PINK, GREEN, VIOLET, RAINBOW],
    volley: 0.45,
  },
};

/** Lanterns rising at each level (of the course's pool). */
export function lanternCount(level: number, pool: number): number {
  return Math.round(pool * Math.max(0.15, Math.min(1, level)));
}

/** A number in [0, 1) from integers (a fixed hash: the same show every race). */
export function hash01(a: number, b = 0): number {
  let h = Math.imul(a | 0, 0x27d4eb2d) ^ Math.imul((b | 0) + 0x165667b1, 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d);
  h = Math.imul(h ^ (h >>> 12), 0x297a2d39);
  h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}

/** The city's own launches are decided ten times a second. */
export const TICK = 0.1;

export interface AmbientLaunch {
  site: number;
  /** Burst point above (and a little off) its site. */
  x: number;
  y: number;
  z: number;
  pattern: Pattern;
  size: number;
  colors: string[];
  /** Seconds after the tick it bursts at (the rocket's flight). */
  fuse: number;
}

/**
 * The city's launches for one tick of the race clock (none most ticks), for a stage and
 * level. Deterministic: the same tick, stage and level always give the same launches.
 */
export function ambientAt(
  cfg: FestivalConfig,
  tick: number,
  stage: Stage,
  level: number,
): AmbientLaunch[] {
  const n = cfg.sites.length;
  if (!n) return [];
  const style = AMBIENT[stage];
  const rate = style.rate * (stage === 3 ? 0.3 + 1.2 * level : 1);
  if (hash01(tick, 1) >= rate * TICK) return [];
  const count = hash01(tick, 2) < style.volley ? 2 + Math.floor(hash01(tick, 3) * 3) : 1;
  const out: AmbientLaunch[] = [];
  const base = Math.floor(hash01(tick, 4) * n);
  const pattern = style.patterns[Math.floor(hash01(tick, 5) * style.patterns.length)]!;
  const colors = style.colors[Math.floor(hash01(tick, 6) * style.colors.length)]!;
  for (let k = 0; k < count; k++) {
    const site = (base + k * 7) % n;
    const s = cfg.sites[site]!;
    const h = 90 + hash01(tick, 10 + k) * 110 + (stage === 3 ? 30 * level : 0);
    const size = style.size[0] + (style.size[1] - style.size[0]) * hash01(tick, 20 + k);
    out.push({
      site,
      x: s.x + (hash01(tick, 30 + k) - 0.5) * 40,
      y: s.y + h,
      z: s.z + (hash01(tick, 40 + k) - 0.5) * 40,
      pattern,
      size,
      colors,
      fuse: 1.6 + hash01(tick, 50 + k) * 0.9 + k * 0.12,
    });
  }
  return out;
}

/**
 * The set pieces that start as the racer goes from lap distance s0 to s1 (within one
 * frame; across the line it wraps) on this stage.
 */
export function piecesDue(cfg: FestivalConfig, s0: number, s1: number, stage: Stage): SetPiece[] {
  const L = cfg.length;
  let a = ((s0 % L) + L) % L;
  let b = ((s1 % L) + L) % L;
  // Backwards (reversing, a respawn) or a jump of more than a few hundred metres: no.
  let d = b - a;
  if (d < -L / 2) d += L;
  if (d <= 0 || d > 150) return [];
  if (b < a) b += L;
  return cfg.pieces.filter((p) => {
    if (!p.stages.includes(stage)) return false;
    const at = p.at < a ? p.at + L : p.at;
    return at > a && at <= b;
  });
}

// ---------------------------------------------------------------- shapes

/**
 * The shape of a pattern: unit-ish offsets (x, y, z) per star, and a weight per star
 * (1: a bright star, less: a fainter one, e.g. a constellation's lines). Flat patterns
 * (ring, dragon, constellation) lie in the X-Y plane; the caller turns them.
 */
export function patternPoints(
  pattern: Pattern,
  count: number,
  seed: number,
): { p: number[]; w: number[] } {
  const p: number[] = [];
  const w: number[] = [];
  const add = (x: number, y: number, z: number, k = 1) => {
    p.push(x, y, z);
    w.push(k);
  };
  const r = (i: number) => hash01(seed, i);
  switch (pattern) {
    case "ring": {
      for (let i = 0; i < count; i++) {
        const a = (i / count) * Math.PI * 2;
        add(Math.cos(a), Math.sin(a), 0);
      }
      break;
    }
    case "star": {
      // An eight-pointed star: stars along eight rays.
      const per = Math.max(3, Math.floor(count / 8));
      for (let k = 0; k < 8; k++) {
        const a = (k / 8) * Math.PI * 2 + r(1) * 0.4;
        const up = (r(k + 2) - 0.5) * 0.6;
        for (let i = 1; i <= per; i++) {
          const f = i / per;
          add(Math.cos(a) * f, up * f, Math.sin(a) * f, 1 - 0.4 * f);
        }
      }
      break;
    }
    case "palm": {
      // Thick fronds curving out and down.
      const arms = 7;
      const per = Math.max(4, Math.floor(count / arms));
      for (let k = 0; k < arms; k++) {
        const a = (k / arms) * Math.PI * 2 + r(3) * 0.5;
        for (let i = 1; i <= per; i++) {
          const f = i / per;
          add(Math.cos(a) * f, 0.5 * f - 0.15 * f * f, Math.sin(a) * f);
        }
      }
      break;
    }
    case "dragon":
      dragonShape(count, add);
      break;
    case "constellation":
      constellation(add);
      break;
    default: {
      // A sphere of stars (Fibonacci), a little ragged.
      const n = Math.max(8, count);
      const golden = Math.PI * (3 - Math.sqrt(5));
      for (let i = 0; i < n; i++) {
        const y = 1 - (2 * (i + 0.5)) / n;
        const rad = Math.sqrt(1 - y * y);
        const a = i * golden + r(9) * 6.28;
        const j = 0.9 + 0.2 * r(100 + i);
        add(Math.cos(a) * rad * j, y * j, Math.sin(a) * rad * j);
      }
    }
  }
  return { p, w };
}

/** The dragon's spine, u 0 (tail) .. 1 (head): (x, y) in about [-1, 1] x [-0.4, 0.5]. */
export function dragonSpine(u: number): [number, number] {
  const x = (u - 0.5) * 2;
  const y = 0.26 * Math.sin(u * Math.PI * 2.4 + 0.4) * (0.45 + 0.55 * u) + 0.12 * u;
  return [x, y];
}

function dragonShape(count: number, add: (x: number, y: number, z: number, k?: number) => void) {
  // Body: two outlines either side of the spine, thick in the middle, tapering to the tail.
  const body = Math.max(40, Math.floor(count * 0.55));
  for (let i = 0; i < body; i++) {
    const u = i / (body - 1);
    const [x, y] = dragonSpine(u);
    const [x2, y2] = dragonSpine(Math.min(1, u + 0.01));
    const tx = x2 - x;
    const ty = y2 - y;
    const tl = Math.hypot(tx, ty) || 1;
    const nx = -ty / tl;
    const ny = tx / tl;
    const half = 0.012 + 0.07 * Math.sin(Math.PI * Math.pow(u, 0.7)) * (u < 0.92 ? 1 : 0.6);
    const side = i % 2 ? 1 : -1;
    add(x + nx * half * side, y + ny * half * side, 0);
  }
  // Spikes along the back.
  for (let u = 0.12; u < 0.9; u += 0.07) {
    const [x, y] = dragonSpine(u);
    add(x, y + 0.11, 0, 0.8);
  }
  // Four legs with claws.
  for (const u of [0.3, 0.42, 0.66, 0.78]) {
    const [x, y] = dragonSpine(u);
    for (let k = 1; k <= 4; k++) add(x + k * 0.012, y - 0.05 - k * 0.025, 0, 0.9);
    add(x + 0.07, y - 0.15, 0, 0.9);
  }
  // The head: a round skull, a long snout, two swept horns, whiskers, an eye.
  const [hx, hy] = dragonSpine(1);
  for (let k = 0; k < 14; k++) {
    const a = (k / 14) * Math.PI * 2;
    add(hx + 0.07 * Math.cos(a), hy + 0.06 * Math.sin(a), 0);
  }
  for (let k = 1; k <= 6; k++) {
    add(hx + 0.07 + k * 0.02, hy + 0.025 - k * 0.003, 0);
    add(hx + 0.07 + k * 0.02, hy - 0.03 - k * 0.002, 0);
  }
  for (let k = 1; k <= 6; k++) {
    add(hx - 0.02 - k * 0.025, hy + 0.06 + k * 0.022, 0, 0.9);
    add(hx - 0.05 - k * 0.025, hy + 0.04 + k * 0.016, 0, 0.9);
  }
  for (let k = 1; k <= 7; k++) {
    const f = k / 7;
    add(hx + 0.18 + f * 0.12, hy - 0.04 - Math.sin(f * 3) * 0.06, 0, 0.7);
    add(hx + 0.18 + f * 0.1, hy + 0.0 + Math.sin(f * 3) * 0.05, 0, 0.7);
  }
  add(hx + 0.03, hy + 0.025, 0, 1);
  // A pearl ahead of the jaws.
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2;
    add(hx + 0.42 + 0.04 * Math.cos(a), hy + 0.02 + 0.04 * Math.sin(a), 0, 1);
  }
}

/** Stars along the dragon's spine joined by faint dotted lines. */
function constellation(add: (x: number, y: number, z: number, k?: number) => void) {
  const nodes: [number, number][] = [];
  for (let k = 0; k <= 11; k++) nodes.push(dragonSpine(k / 11));
  const [hx, hy] = dragonSpine(1);
  nodes.push([hx + 0.16, hy + 0.12], [hx + 0.2, hy - 0.06]);
  for (const [x, y] of nodes) add(x, y, 0, 1);
  const link = (a: [number, number], b: [number, number]) => {
    for (let k = 1; k < 5; k++) {
      const f = k / 5;
      add(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, 0, 0.35);
    }
  };
  for (let k = 0; k < 11; k++) link(nodes[k]!, nodes[k + 1]!);
  link(nodes[11]!, nodes[12]!);
  link(nodes[11]!, nodes[13]!);
  // Legs.
  for (const k of [3, 4, 7, 8]) {
    const [x, y] = nodes[k]!;
    const foot: [number, number] = [x + 0.05, y - 0.22];
    add(foot[0], foot[1], 0, 0.9);
    link(nodes[k]!, foot);
  }
}

/** Turn a flat pattern point (x, y in its plane) to face `yaw` and lean by `tilt`. */
export function orient(
  x: number,
  y: number,
  z: number,
  yaw: number,
  tilt: number,
): [number, number, number] {
  // Lean about the plane's X axis, then turn about Y.
  const ct = Math.cos(tilt);
  const st = Math.sin(tilt);
  const y1 = y * ct - z * st;
  const z1 = y * st + z * ct;
  const cy = Math.cos(yaw);
  const sy = Math.sin(yaw);
  return [x * cy + z1 * sy, y1, -x * sy + z1 * cy];
}

/** How long a pattern's stars live (seconds) and how strongly they droop. */
export function patternLife(pattern: Pattern): { life: number; droop: number; kind: number } {
  switch (pattern) {
    case "willow":
      return { life: 4.2, droop: 1, kind: 1 };
    case "glitter":
      return { life: 2.6, droop: 0.35, kind: 2 };
    case "dragon":
      return { life: 6, droop: 0.04, kind: 3 };
    case "constellation":
      return { life: 7.5, droop: 0, kind: 6 };
    case "ring":
      return { life: 2.6, droop: 0.15, kind: 3 };
    case "palm":
      return { life: 2.6, droop: 0.6, kind: 0 };
    default:
      return { life: 2.2, droop: 0.3, kind: 0 };
  }
}

/** Stars per burst for a pattern and size (bigger bursts, more stars). */
export function patternCount(pattern: Pattern, size: number): number {
  if (pattern === "dragon") return 640;
  if (pattern === "constellation") return 0;
  if (pattern === "ring") return Math.round(40 + size * 1.4);
  return Math.round(50 + size * 2.2);
}
