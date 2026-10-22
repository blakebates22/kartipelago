/**
 * Impact Depths: the world under the desert. track.json entities for the air and the
 * life of a course that goes down through many worlds:
 *
 *   atmosphere  { "type": "atmosphere", "zones": { name: Zone, ... },
 *                 "keys": [[x, y, z, "zoneA", "zoneB", t], ...] }
 *               The air of each world (fog colour and distance, how much sun reaches
 *               it, the ambient light's colours and strength, and its sound), and keys
 *               all along the lap (and any shortcut) saying which worlds are either side
 *               and how far between them (t: 0 = all A .. 1 = all B). Wherever the
 *               camera is, the nearest keys say what the air is like: going down, the
 *               desert's haze gives way to the crater's dust, a crystal cavern's blue
 *               dark, a jungle's green gloom, the red of the lava.
 *   triceratops { "type": "triceratops", "x", "y", "z", "heading", "scale": 1,
 *                 "roam": 6, "seed": 1 }
 *               A three-horned grazer, wandering slowly round its own patch, stopping
 *               to graze (head down), now and then lifting its head to bellow. Solid.
 *   raptors     { "type": "raptors", "ax", "ay", "az", "bx", "by", "bz", "period": 9,
 *                 "offset": 0, "travel": 2.2, "warn": 1.4, "count": 3 }
 *               A pack of raptors darting across the road from A to B on a beat of the
 *               race clock (see game/movers.ts's crossings), chirping in the ferns for
 *               `warn` seconds first. Solid while crossing: a knock and a slowdown.
 *   meteors     { "type": "meteors", "x", "y", "z", "rate": 0.35, "intro": true }
 *               Shooting stars over the desert (rate: per second), and with `intro` one
 *               great fireball at the start of every race, streaking over the line and
 *               down into the crater at (x, y, z), a flash and a boom where it lands.
 *               Purely visual.
 *   plume       { "type": "plume", "x", "y", "z", "height": 150, "radius": 16,
 *                 "rate": 7, "color": "#4a3e44", "glow": "#ff7a4a" }
 *               A column of smoke rising and spreading (the asteroid's), lit from below.
 *   core        { "type": "core", "x", "y", "z", "size": 11 }
 *               The Heart of the Earth: a great layered crystal, gold at its heart and
 *               magenta outside, pulsing, rings of light turning round it, motes rising,
 *               its light washing the chamber.
 *   motes       { "type": "motes", "x", "y", "z", "radius", "rate", "color", "rise",
 *                 "size", "blink" }
 *               Little lights drifting in the air near (x, y, z): dust in a sunbeam,
 *               crystal glints, fireflies, embers.
 *   glow        { "type": "glow", "x", "y", "z", "color": "#ff6a2a" }
 *               A coloured light (lava, crystal, fungus): the few nearest the camera
 *               light the road, the walls and the karts.
 *
 * Everything here is pure (no three.js); render/depthsFx.ts draws it.
 */

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);
const str = (v: unknown, d: string) => (typeof v === "string" ? v : d);
const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

// ---------------------------------------------------------------- the atmosphere

export type SoundKind =
  | "wind"
  | "resonance"
  | "chime"
  | "jungle"
  | "drip"
  | "rumble"
  | "hum"
  | "festival"
  | "falls"
  | "garden"
  | "harbour"
  | "quarry"
  | "blizzard"
  | "bells"
  /** No bed of noise at all: only the odd drum, gong or plucked phrase of a celebration
   * (Celestial Dragon Festival, where the fireworks and the music carry it). */
  | "celebration";
export const SOUND_KINDS: SoundKind[] = [
  "wind",
  "resonance",
  "chime",
  "jungle",
  "drip",
  "rumble",
  "hum",
  "festival",
  "falls",
  "garden",
  "harbour",
  "quarry",
  "blizzard",
  "bells",
  "celebration",
];

export interface Zone {
  fog: [number, number, number];
  near: number;
  far: number;
  /** The sun's strength here (it hardly reaches the deep caves). */
  sun: number;
  sky: [number, number, number];
  ground: [number, number, number];
  hemi: number;
  sound: SoundKind;
}

export interface AtmosphereKey {
  x: number;
  y: number;
  z: number;
  a: string;
  b: string;
  t: number;
}

export interface AtmosphereConfig {
  zones: Record<string, Zone>;
  keys: AtmosphereKey[];
}

/** "#rrggbb" to [r, g, b] (0..1). */
export function hexColor(h: string): [number, number, number] {
  const m = /^#?([0-9a-f]{6})$/i.exec(h.trim());
  if (!m) return [1, 1, 1];
  const n = parseInt(m[1]!, 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

export function parseAtmosphere(e: Record<string, unknown>): AtmosphereConfig {
  const zones: Record<string, Zone> = {};
  if (isObj(e.zones))
    for (const [name, z] of Object.entries(e.zones)) {
      if (!isObj(z)) continue;
      const sound = str(z.sound, "wind") as SoundKind;
      zones[name] = {
        fog: hexColor(str(z.fog, "#c8c8c8")),
        near: Math.max(1, num(z.near, 300)),
        far: Math.max(2, num(z.far, 2000)),
        sun: Math.max(0, num(z.sun, 2)),
        sky: hexColor(str(z.sky, "#ffffff")),
        ground: hexColor(str(z.ground, "#808080")),
        hemi: Math.max(0, num(z.hemi, 1)),
        sound: SOUND_KINDS.includes(sound) ? sound : "wind",
      };
    }
  const keys: AtmosphereKey[] = [];
  if (Array.isArray(e.keys))
    for (const k of e.keys) {
      if (!Array.isArray(k) || k.length < 6) continue;
      const a = str(k[3], "");
      const b = str(k[4], a);
      if (!zones[a] || !zones[b]) continue;
      keys.push({
        x: num(k[0], 0),
        y: num(k[1], 0),
        z: num(k[2], 0),
        a,
        b,
        t: Math.min(1, Math.max(0, num(k[5], 0))),
      });
    }
  return { zones, keys };
}

export interface Air {
  fog: [number, number, number];
  near: number;
  far: number;
  sun: number;
  sky: [number, number, number];
  ground: [number, number, number];
  hemi: number;
  /** How loud each world's sound is here (0..1, summing to 1). */
  sound: Record<SoundKind, number>;
}

const mix3 = (
  a: [number, number, number],
  b: [number, number, number],
  t: number,
): [number, number, number] => [
  a[0] + (b[0] - a[0]) * t,
  a[1] + (b[1] - a[1]) * t,
  a[2] + (b[2] - a[2]) * t,
];

/** The air at (x, y, z): a blend of the worlds the nearest keys name (the two nearest,
 * weighted by how near each is). Undefined with no keys. */
export function airAt(cfg: AtmosphereConfig, x: number, y: number, z: number): Air | undefined {
  let best = -1;
  let second = -1;
  let d1 = Infinity;
  let d2 = Infinity;
  cfg.keys.forEach((k, i) => {
    // Height counts for more: a cave's road and the desert above it are different air.
    const d = (k.x - x) ** 2 + ((k.y - y) * 3) ** 2 + (k.z - z) ** 2;
    if (d < d1) {
      d2 = d1;
      second = best;
      d1 = d;
      best = i;
    } else if (d < d2) {
      d2 = d;
      second = i;
    }
  });
  if (best < 0) return undefined;
  const one = (k: AtmosphereKey): Air => {
    const A = cfg.zones[k.a]!;
    const B = cfg.zones[k.b]!;
    const t = k.t;
    const sound = Object.fromEntries(SOUND_KINDS.map((s) => [s, 0])) as Record<SoundKind, number>;
    sound[A.sound] += 1 - t;
    sound[B.sound] += t;
    return {
      fog: mix3(A.fog, B.fog, t),
      near: A.near + (B.near - A.near) * t,
      far: A.far + (B.far - A.far) * t,
      sun: A.sun + (B.sun - A.sun) * t,
      sky: mix3(A.sky, B.sky, t),
      ground: mix3(A.ground, B.ground, t),
      hemi: A.hemi + (B.hemi - A.hemi) * t,
      sound,
    };
  };
  const a = one(cfg.keys[best]!);
  if (second < 0) return a;
  const b = one(cfg.keys[second]!);
  const wa = 1 / (Math.sqrt(d1) + 1);
  const wb = 1 / (Math.sqrt(d2) + 1);
  const t = wb / (wa + wb);
  const sound = Object.fromEntries(
    SOUND_KINDS.map((s) => [s, a.sound[s] + (b.sound[s] - a.sound[s]) * t]),
  ) as Record<SoundKind, number>;
  return {
    fog: mix3(a.fog, b.fog, t),
    near: a.near + (b.near - a.near) * t,
    far: a.far + (b.far - a.far) * t,
    sun: a.sun + (b.sun - a.sun) * t,
    sky: mix3(a.sky, b.sky, t),
    ground: mix3(a.ground, b.ground, t),
    hemi: a.hemi + (b.hemi - a.hemi) * t,
    sound,
  };
}

// ---------------------------------------------------------------- triceratops

export interface TriceratopsConfig {
  x: number;
  y: number;
  z: number;
  heading: number;
  scale: number;
  roam: number;
  seed: number;
}

export function parseTriceratops(e: Record<string, unknown>): TriceratopsConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    scale: Math.max(0.2, num(e.scale, 1)),
    roam: Math.max(0, num(e.roam, 6)),
    seed: num(e.seed, 1),
  };
}

export interface GrazerPose {
  x: number;
  z: number;
  heading: number;
  /** Walking (0..1: blends the legs' swing in). */
  walk: number;
  /** Head down to graze (0..1). */
  graze: number;
  /** Head up, bellowing (0..1). */
  bellow: number;
}

/**
 * Where a grazer is at time t: it ambles round a lazy figure of its own patch (radius
 * `roam`), pausing to graze; every so often it stops, lifts its head and bellows. Pure.
 */
export function grazerAt(c: TriceratopsConfig, t: number): GrazerPose {
  const cycle = 22 + (c.seed % 5) * 3;
  const u = (((t + c.seed * 7.3) % cycle) + cycle) % cycle;
  // Walk for the first 40% of the cycle, then stand and graze, then bellow briefly.
  const walking = u < cycle * 0.4;
  const along = walking ? u / (cycle * 0.4) : 1;
  const lap = Math.floor((t + c.seed * 7.3) / cycle);
  const a0 = lap * 1.9 + c.seed;
  const a = a0 + along * 1.6;
  const r = c.roam;
  const x = c.x + r * Math.cos(a) * 0.8;
  const z = c.z + r * Math.sin(a * 1.3) * 0.55;
  // Facing along its way (the derivative of the path).
  const dx = -r * Math.sin(a) * 0.8;
  const dz = r * 1.3 * Math.cos(a * 1.3) * 0.55;
  const heading = Math.atan2(dx, dz);
  const graze = walking
    ? 0
    : Math.min(1, (u - cycle * 0.4) / 1.5) *
      (u > cycle * 0.85 ? Math.max(0, 1 - (u - cycle * 0.85) / 0.8) : 1);
  const bellow =
    u > cycle * 0.88 && u < cycle * 0.97
      ? Math.sin(((u - cycle * 0.88) / (cycle * 0.09)) * Math.PI)
      : 0;
  const walk = walking ? Math.min(1, u / 1.0, (cycle * 0.4 - u) / 1.0) : 0;
  return { x, z, heading, walk: Math.max(0, walk), graze, bellow };
}

// ---------------------------------------------------------------- meteors

export interface MeteorsConfig {
  x: number;
  y: number;
  z: number;
  rate: number;
  intro: boolean;
}

export function parseMeteors(e: Record<string, unknown>): MeteorsConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    rate: Math.max(0, num(e.rate, 0.3)),
    intro: e.intro === true,
  };
}

/** The intro fireball: when it's in the air (race clock), and where it starts. */
export const INTRO = { start: -2.6, travel: 3.2 };

/** Where the intro fireball is at race time `clock` (0..1 along its path), or null. */
export function introAt(clock: number): number | null {
  const u = (clock - INTRO.start) / INTRO.travel;
  return u >= 0 && u <= 1 ? u : null;
}

// ---------------------------------------------------------------- the core, motes, plumes, glows

export interface CoreConfig {
  x: number;
  y: number;
  z: number;
  size: number;
}

export function parseCore(e: Record<string, unknown>): CoreConfig {
  return { x: num(e.x, 0), y: num(e.y, 0), z: num(e.z, 0), size: Math.max(1, num(e.size, 10)) };
}

/** The core's pulse at time t (0..1): a heartbeat, two quick swells then a rest. */
export function corePulse(t: number): number {
  const u = ((t % 1.6) + 1.6) % 1.6;
  const beat = (c: number) => Math.exp(-(((u - c) / 0.12) ** 2));
  return Math.min(1, beat(0.2) + 0.7 * beat(0.55));
}

export interface MotesConfig {
  x: number;
  y: number;
  z: number;
  radius: number;
  rate: number;
  color: string;
  rise: number;
  size: number;
  blink: boolean;
}

export function parseMotes(e: Record<string, unknown>): MotesConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    radius: Math.max(1, num(e.radius, 30)),
    rate: Math.max(0, num(e.rate, 8)),
    color: str(e.color, "#ffffff"),
    rise: num(e.rise, 0.2),
    size: Math.max(0.05, num(e.size, 0.25)),
    blink: e.blink === true,
  };
}

export interface PlumeConfig {
  x: number;
  y: number;
  z: number;
  height: number;
  radius: number;
  rate: number;
  color: string;
  glow: string;
}

export function parsePlume(e: Record<string, unknown>): PlumeConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    height: Math.max(5, num(e.height, 120)),
    radius: Math.max(1, num(e.radius, 12)),
    rate: Math.max(0, num(e.rate, 6)),
    color: str(e.color, "#4a4448"),
    glow: str(e.glow, "#ff7a4a"),
  };
}

export interface GlowConfig {
  x: number;
  y: number;
  z: number;
  color: string;
}

export function parseGlow(e: Record<string, unknown>): GlowConfig {
  return { x: num(e.x, 0), y: num(e.y, 0), z: num(e.z, 0), color: str(e.color, "#ff8040") };
}
