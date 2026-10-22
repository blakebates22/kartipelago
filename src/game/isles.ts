/**
 * Dragon Isles: the great dragon's flight, the villagers and the little things that
 * move (track.json entities, written by tools/blender/prehistoric/isles_town.py).
 *
 *   isles_dragon    The great jade dragon. `keys`: [lap distance, x, y, z] — where the
 *                   dragon should be when the player is that far round the lap. It flies
 *                   a smooth loop through the keys, never backwards, faster when it has
 *                   ground to make up and gliding slowly when it is ahead, so it meets
 *                   the race at its set moments (over the falls as you reach the bridge,
 *                   straight overhead on the long bridge, low over the harbour) whatever
 *                   the pace. It is scenery: it never touches a kart.
 *   villagers       `list`: [x, y, z, faceX, faceZ, role, variant] per villager. Roles:
 *                   cheer, wave, merchant, dancer, musician, fisher, gardener, guard, bow.
 *   waterwheel      A mill wheel turning (x, y, z, heading of its axle, radius, speed).
 *   little_dragons  A few small dragons circling (x, y, z, radius, count, speed, seed).
 *
 * Everything here is pure (no three.js); render/islesFx.ts draws it and game/islesLife.ts
 * runs it.
 */

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);
const str = (v: unknown, d: string) => (typeof v === "string" ? v : d);

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

// ---------------------------------------------------------------- the great dragon

export interface DragonKey extends Vec3 {
  /** Lap distance (m) at which the dragon should be here. */
  s: number;
}

export interface IslesDragonConfig {
  keys: DragonKey[];
  /** The lap's length (m). */
  length: number;
  size: number;
  /** Its colours (Snow Dragon Pass's is ice blue); jade and gold if not given. */
  colors?: { body: string; belly: string };
  /** The grand finale's flight (Celestial Dragon Festival's last lap), if it has one:
   * the same lap, other keys. */
  finale?: IslesDragonConfig;
}

export function parseIslesDragon(e: Record<string, unknown>): IslesDragonConfig | undefined {
  const keys = parseKeys(e.keys);
  if (keys.length < 4) return undefined;
  const col =
    typeof e.colors === "object" && e.colors !== null && !Array.isArray(e.colors)
      ? (e.colors as Record<string, unknown>)
      : undefined;
  const base: IslesDragonConfig = {
    keys,
    length: Math.max(1, num(e.length, 1000)),
    size: Math.max(0.1, num(e.size, 1)),
    ...(col && { colors: { body: str(col.body, "#34b888"), belly: str(col.belly, "#ffe39a") } }),
  };
  const fin = parseKeys(e.finale);
  if (fin.length >= 4) base.finale = { ...base, keys: fin };
  return base;
}

function parseKeys(src: unknown): DragonKey[] {
  const keys: DragonKey[] = [];
  if (Array.isArray(src))
    for (const k of src) {
      if (!Array.isArray(k) || k.length < 4) continue;
      keys.push({ s: num(k[0], 0), x: num(k[1], 0), y: num(k[2], 0), z: num(k[3], 0) });
    }
  keys.sort((a, b) => a.s - b.s);
  return keys;
}

/** A point on the closed Catmull-Rom loop through the keys: u in key units (key i at
 * u = i), wrapping. */
export function loopPoint(keys: Vec3[], u: number): Vec3 {
  const n = keys.length;
  const w = ((u % n) + n) % n;
  const i = Math.floor(w);
  const t = w - i;
  const p0 = keys[(i - 1 + n) % n]!;
  const p1 = keys[i]!;
  const p2 = keys[(i + 1) % n]!;
  const p3 = keys[(i + 2) % n]!;
  const cr = (a: number, b: number, c: number, d: number) =>
    0.5 *
    (2 * b +
      (-a + c) * t +
      (2 * a - 5 * b + 4 * c - d) * t * t +
      (-a + 3 * b - 3 * c + d) * t * t * t);
  return {
    x: cr(p0.x, p1.x, p2.x, p3.x),
    y: cr(p0.y, p1.y, p2.y, p3.y),
    z: cr(p0.z, p1.z, p2.z, p3.z),
  };
}

/** Where on the loop (key units) the dragon should be when the player is `s` metres
 * round the lap. */
export function dragonTarget(c: IslesDragonConfig, s: number): number {
  const n = c.keys.length;
  const w = ((s % c.length) + c.length) % c.length;
  for (let i = 0; i < n; i++) {
    const a = c.keys[i]!;
    const b = c.keys[(i + 1) % n]!;
    const sb = i + 1 < n ? b.s : b.s + c.length;
    if (w >= a.s && w < sb) return i + (w - a.s) / Math.max(1e-6, sb - a.s);
  }
  // Before the first key (it isn't at 0): between the last and the first.
  const a = c.keys[n - 1]!;
  const b = c.keys[0]!;
  const sa = a.s - c.length;
  return n - 1 + (w - sa) / Math.max(1e-6, b.s - sa);
}

/** Metres of loop per key unit near u (for turning speeds into steps along the loop). */
export function loopScale(keys: Vec3[], u: number): number {
  const a = loopPoint(keys, u - 0.02);
  const b = loopPoint(keys, u + 0.02);
  return Math.max(1, Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z) / 0.04);
}

export interface DragonFlight {
  /** Position on the loop, key units, unwrapped (only ever grows). */
  u: number;
  /** Current speed, m/s. */
  speed: number;
}

export const DRAGON_MIN_SPEED = 9;
export const DRAGON_MAX_SPEED = 72;

/**
 * Advance the dragon toward where the lap says it should be: it hurries when behind,
 * glides slowly when ahead (never backwards), and its speed changes smoothly.
 */
export function stepDragon(c: IslesDragonConfig, f: DragonFlight, s: number, dt: number) {
  const n = c.keys.length;
  // How far behind the target the dragon is, round the loop (key units, 0..n). Within
  // the last few keys of the loop it's really just ahead.
  const behind = (((dragonTarget(c, s) - f.u) % n) + n) % n;
  const target = behind > n - 3 ? f.u - (n - behind) : f.u + behind;
  const scale = loopScale(c.keys, f.u);
  const gap = (target - f.u) * scale;
  const want =
    gap > 0
      ? Math.min(DRAGON_MAX_SPEED, DRAGON_MIN_SPEED + 18 + gap * 0.5)
      : Math.max(DRAGON_MIN_SPEED, 20 + gap * 0.25);
  f.speed += (want - f.speed) * (1 - Math.exp(-1.2 * dt));
  f.u += (f.speed * dt) / scale;
}

/** Put the dragon straight where the lap says it should be (a race restart, tools). */
export function placeDragon(c: IslesDragonConfig, f: DragonFlight, s: number) {
  f.u = dragonTarget(c, s);
  f.speed = 24;
}

/** The dragon's head: the loop point plus a slow sway (it never flies a ruler line). */
export function dragonHead(c: IslesDragonConfig, u: number, t: number): Vec3 {
  const p = loopPoint(c.keys, u);
  const q = loopPoint(c.keys, u + 0.02);
  const fx = q.x - p.x;
  const fz = q.z - p.z;
  const l = Math.hypot(fx, fz) || 1;
  const sway = 7 * Math.sin(t * 0.55) + 3 * Math.sin(t * 1.3 + 1);
  return {
    x: p.x + (-fz / l) * sway,
    y: p.y + 5 * Math.sin(t * 0.8) + 2 * Math.sin(t * 1.9 + 0.5),
    z: p.z + (fx / l) * sway,
  };
}

/** How strongly the kingdom reacts to the dragon passing close (0..1): villagers bow
 * together, the festival hushes. `d` is the horizontal distance from the dragon. */
export function awe(d: number, height: number): number {
  const reach = 150;
  if (height > 140) return 0;
  const k = Math.max(0, Math.min(1, (reach - d) / 80));
  return k * k * (3 - 2 * k) * Math.max(0, Math.min(1, (140 - height) / 60));
}

// ---------------------------------------------------------------- the villagers

export const ROLES = [
  "cheer",
  "wave",
  "merchant",
  "dancer",
  "musician",
  "fisher",
  "gardener",
  "guard",
  "bow",
  "worker",
  "hauler",
  "huddle",
  "queue",
  "monk",
  "worship",
] as const;
export type Role = (typeof ROLES)[number];

export interface Villager extends Vec3 {
  /** Which way they face (unit, horizontal). */
  fx: number;
  fz: number;
  role: Role;
  variant: number;
}

export function parseVillagers(e: Record<string, unknown>): Villager[] {
  const out: Villager[] = [];
  if (!Array.isArray(e.list)) return out;
  for (const v of e.list) {
    if (!Array.isArray(v) || v.length < 7) continue;
    const role = str(v[5], "cheer") as Role;
    const fx = num(v[3], 0);
    const fz = num(v[4], 1);
    const l = Math.hypot(fx, fz) || 1;
    out.push({
      x: num(v[0], 0),
      y: num(v[1], 0),
      z: num(v[2], 0),
      fx: fx / l,
      fz: fz / l,
      role: ROLES.includes(role) ? role : "cheer",
      variant: Math.max(0, Math.round(num(v[6], 0))),
    });
  }
  return out;
}

/** A villager's pose at time t: hop (m), body lean forward (rad), arm raises (0..1,
 * 1 = straight up), turn about their own axis (rad). `bow` (0..1) is the dragon's awe:
 * everyone but the guards stops and bows low together. Guards never move. */
export interface Pose {
  hop: number;
  lean: number;
  armL: number;
  armR: number;
  turn: number;
  /** How far they've walked along their facing (haulers pacing to and fro), m. */
  step: number;
}

export function villagerPose(v: Villager, k: number, t: number, bow: number): Pose {
  const ph = k * 0.73 + v.variant * 1.9;
  let p: Pose = { hop: 0, lean: 0, armL: 0, armR: 0, turn: 0, step: 0 };
  switch (v.role) {
    case "guard":
      return p;
    case "cheer": {
      const b = Math.max(0, Math.sin(t * 7 + ph));
      p = {
        hop: 0.25 * b,
        lean: -0.05,
        armL: 0.6 + 0.4 * b,
        armR: 0.6 + 0.4 * Math.sin(t * 7 + ph + 1),
        turn: 0,
        step: 0,
      };
      break;
    }
    case "wave":
      p = {
        hop: 0,
        lean: 0,
        armL: 0.1,
        armR: 0.75 + 0.25 * Math.sin(t * 6 + ph),
        turn: 0.15 * Math.sin(t * 6 + ph),
        step: 0,
      };
      break;
    case "merchant":
      p = {
        hop: 0,
        lean: 0.05 * Math.sin(t * 1.2 + ph),
        armL: 0.15,
        armR: 0.35 + 0.25 * Math.max(0, Math.sin(t * 2.4 + ph)),
        turn: 0.4 * Math.sin(t * 0.5 + ph),
        step: 0,
      };
      break;
    case "dancer": {
      const b = Math.sin(t * 4.4 + ph);
      p = {
        hop: 0.2 * Math.abs(b),
        lean: 0.1 * b,
        armL: 0.5 + 0.4 * b,
        armR: 0.5 - 0.4 * b,
        turn: t * 1.6 + ph,
        step: 0,
      };
      break;
    }
    case "musician":
      p = {
        hop: 0,
        lean: 0.08,
        armL: 0.35 + 0.3 * Math.abs(Math.sin(t * 8 + ph)),
        armR: 0.35 + 0.3 * Math.abs(Math.cos(t * 8 + ph)),
        turn: 0,
        step: 0,
      };
      break;
    case "fisher":
      p = {
        hop: 0,
        lean: 0.06 + 0.03 * Math.sin(t * 0.7 + ph),
        armL: 0.3,
        armR: 0.45,
        turn: 0,
        step: 0,
      };
      break;
    case "gardener": {
      const b = 0.5 + 0.5 * Math.sin(t * 0.8 + ph);
      p = { hop: 0, lean: 0.9 * b * b, armL: 0.1, armR: 0.1 + 0.1 * b, turn: 0, step: 0 };
      break;
    }
    case "worker": {
      // Hewing stone: a slow, heavy swing, bent over the block; now and then a pause.
      const sw = Math.max(0, Math.sin(t * 1.6 + ph));
      const rest = Math.sin(t * 0.13 + ph) > 0.7 ? 0 : 1;
      p = {
        hop: 0,
        lean: 0.35 + 0.15 * sw * rest,
        armL: 0.2 + 0.7 * sw * rest,
        armR: 0.2 + 0.7 * sw * rest,
        turn: 0,
        step: 0,
      };
      break;
    }
    case "hauler": {
      // Leaning into a load, pacing slowly to and fro along a short track.
      const w = Math.sin(t * 0.32 + ph);
      p = {
        hop: 0.05 * Math.abs(Math.sin(t * 3.2 + ph)),
        lean: 0.45,
        armL: 0.35,
        armR: 0.35,
        turn: w < 0 ? Math.PI : 0,
        step: (4.0 * Math.asin(Math.max(-1, Math.min(1, w)))) / (Math.PI / 2),
      };
      break;
    }
    case "huddle": {
      // Crouched by a fire, arms in, rocking a little against the cold.
      p = {
        hop: -0.45,
        lean: 0.55 + 0.06 * Math.sin(t * 1.1 + ph),
        armL: 0.05,
        armR: 0.05,
        turn: 0.06 * Math.sin(t * 0.7 + ph),
        step: 0,
      };
      break;
    }
    case "queue": {
      // Waiting in line: hunched, shifting from foot to foot, now and then a shuffle
      // forward and back.
      const sh = Math.sin(t * 0.21 + ph);
      p = {
        hop: 0.03 * Math.abs(Math.sin(t * 1.4 + ph)),
        lean: 0.22,
        armL: 0.05,
        armR: 0.05,
        turn: 0.08 * Math.sin(t * 0.9 + ph),
        step: sh > 0.9 ? (sh - 0.9) * 4 : 0,
      };
      break;
    }
    case "monk": {
      // Thin, hooded and silent: head bowed, perfectly still but for a slow breath.
      p = {
        hop: 0,
        lean: 0.18 + 0.02 * Math.sin(t * 0.5 + ph),
        armL: 0.08,
        armR: 0.08,
        turn: 0,
        step: 0,
      };
      break;
    }
    case "worship": {
      // Kneeling before the altar, all together (not phased by villager): arms raised
      // to the sky, then down in a deep bow, over and over.
      const w = 0.5 + 0.5 * Math.sin(t * 1.1);
      p = {
        hop: -0.45,
        lean: 0.15 + 0.85 * (1 - w),
        armL: 0.9 * w,
        armR: 0.9 * w,
        turn: 0,
        step: 0,
      };
      break;
    }
    case "bow": {
      // Bowing politely now and then as the race goes by.
      const b = Math.max(0, Math.sin(t * 0.9 + ph * 0.3) - 0.3) / 0.7;
      p = { hop: 0, lean: 0.75 * b, armL: 0, armR: 0, turn: 0, step: 0 };
      break;
    }
  }
  if (bow > 0) {
    // In step with everyone else: the bow itself isn't phased by villager.
    const deep = 0.9 * bow;
    p.hop *= 1 - bow;
    p.armL *= 1 - bow;
    p.armR *= 1 - bow;
    p.turn *= 1 - bow;
    p.lean = p.lean * (1 - bow) + deep;
  }
  return p;
}

// ---------------------------------------------------------------- mill wheels and little dragons

export interface WaterwheelConfig extends Vec3 {
  heading: number;
  radius: number;
  speed: number;
}

export function parseWaterwheel(e: Record<string, unknown>): WaterwheelConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    radius: Math.max(0.5, num(e.radius, 3)),
    speed: num(e.speed, 0.8),
  };
}

export interface LittleDragonsConfig extends Vec3 {
  radius: number;
  count: number;
  speed: number;
  seed: number;
}

export function parseLittleDragons(e: Record<string, unknown>): LittleDragonsConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 40),
    z: num(e.z, 0),
    radius: Math.max(5, num(e.radius, 30)),
    count: Math.max(1, Math.min(6, Math.round(num(e.count, 2)))),
    speed: num(e.speed, 0.3),
    seed: num(e.seed, 1),
  };
}

/** Little dragon k's head at time t: looping and weaving round the centre. */
export function littleDragonAt(c: LittleDragonsConfig, k: number, t: number): Vec3 {
  const ph = c.seed * 1.7 + (k * Math.PI * 2) / c.count;
  const a = ph + c.speed * t;
  const r = c.radius * (0.8 + 0.2 * Math.sin(a * 2.3 + k));
  return {
    x: c.x + Math.cos(a) * r,
    y: c.y + 6 * Math.sin(a * 1.7 + ph) + 3 * Math.sin(t * 0.9 + k),
    z: c.z + Math.sin(a) * r * (0.85 + 0.15 * Math.cos(ph)),
  };
}

// ---------------------------------------------------------------- quarry cranes

export interface CraneConfig extends Vec3 {
  /** Which way the jib points (game yaw; its tip is at x + sin·reach, z − cos·reach). */
  heading: number;
  reach: number;
  /** Longest the rope pays out (the block's lowest), m. */
  drop: number;
  swing: number;
  period: number;
}

export function parseCrane(e: Record<string, unknown>): CraneConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    reach: Math.max(1, num(e.reach, 10)),
    drop: Math.max(2.5, num(e.drop, 10)),
    swing: num(e.swing, 0.5),
    period: Math.max(2, num(e.period, 10)),
  };
}

/** The crane's load at time t: where the rope hangs from, and the block's centre. */
export function craneLoad(c: CraneConfig, t: number) {
  const tip = {
    x: c.x + Math.sin(c.heading) * c.reach,
    y: c.y,
    z: c.z - Math.cos(c.heading) * c.reach,
  };
  const k = 0.5 - 0.5 * Math.cos((t / c.period) * Math.PI * 2);
  const rope = 2 + (c.drop - 2) * k;
  const sway = c.swing * Math.sin(t * 1.7 + c.x * 0.1);
  return {
    tip,
    rope,
    block: {
      x: tip.x + Math.cos(c.heading) * sway,
      y: tip.y - rope - 0.8,
      z: tip.z + Math.sin(c.heading) * sway,
    },
  };
}

// ---------------------------------------------------------------- lap distance

/** The nearest track sample to (x, z), searching near the last answer first (a cheap
 * walk), else everywhere. Returns its index. */
export function nearestSample(
  samples: { pos: { x: number; z: number } }[],
  x: number,
  z: number,
  hint: number,
): number {
  const n = samples.length;
  if (!n) return 0;
  const d2 = (i: number) => {
    const p = samples[((i % n) + n) % n]!.pos;
    return (p.x - x) ** 2 + (p.z - z) ** 2;
  };
  let best = ((hint % n) + n) % n;
  let bd = d2(best);
  for (let k = -40; k <= 40; k++) {
    const d = d2(hint + k);
    if (d < bd) {
      bd = d;
      best = (((hint + k) % n) + n) % n;
    }
  }
  if (bd < 30 * 30) return best;
  for (let i = 0; i < n; i += 2) {
    const d = d2(i);
    if (d < bd) {
      bd = d;
      best = i;
    }
  }
  return best;
}
