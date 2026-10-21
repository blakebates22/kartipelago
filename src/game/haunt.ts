/**
 * Dry Gulch Ghost Town's haunting: what appears where and when. Everything here is pure
 * (where a thing is depends only on the clock, and for some on how near a kart is); the
 * drawing is render/hauntFx.ts and the wiring is game/hazards.ts. None of it touches a
 * kart except the runaway ore cart (a "minecart" crossing in game/movers.ts).
 *
 *   ghost       { "type": "ghost", "x", "y", "z", "heading", "look": "float", "period": 13,
 *               "offset": 0, "scale": 1, "drift": 0, "vanish": 0 }
 *               A see-through figure that appears for a few seconds of every period and
 *               fades away again. "window": a pale shape standing at a window; "float":
 *               a sheet-like spirit bobbing over the graves (drifting round `drift`
 *               metres); "miner": a ghostly miner at the edge of a tunnel, who fades out
 *               if a kart comes within `vanish` metres; "shadow": a huge dark miner's
 *               shadow thrown on a wall, ringed by green light.
 *   ghostrider  { "type": "ghostrider", "route": "Ghost Rider Path", "period": 38,
 *               "offset": 0, "travel": 14 }  A ghostly rider on a ghostly horse galloping
 *               along a far ridge (a path from route.json) once a period, rising out of
 *               the mist at one end and melting into it at the other.
 *   railcart    { "type": "railcart", "route": "Railway", "period": 34, "offset": 0,
 *               "travel": 13, "pause": 4 }  An empty ore cart rolling by itself along the
 *               mine railway (a path): out, a pause, back, a pause.
 *   tumbleweed  { "type": "tumbleweed", "ax", "ay", "az", "bx", "by", "bz", "period", "offset",
 *               "travel", "r" }  A tumbleweed bowling across the road from A to B now and
 *               then, bouncing. It rolls straight through karts: purely visual.
 *   door        { "type": "door", "x", "y", "z", "heading", "width": 2.4, "period": 9 }
 *               The saloon's swinging doors: every so often they swing open on their own
 *               and flap shut.
 *   wisps       { "type": "wisps", "x", "y", "z", "radius", "count" }  Little green lights
 *               drifting about a spot, each on its own wandering path.
 *   mist        { "type": "mist", "x", "y", "z", "radius", "rate" }  Green mist curling low
 *               over the ground (the graveyard, the mine, the ravine's fissures).
 *   whispers    { "type": "whispers", "x", "y", "z", "radius" }  Ghostly whispering when
 *               you're near.
 *   creak       { "type": "creak", "x", "y", "z", "radius" }  Old timber creaking under
 *               you (the trestles).
 *   ambience    { "type": "ambience", "wind": 0.55, "caves": [[x, y, z, r], ...] }  The
 *               night wind, which falls away underground (inside the caves' spheres),
 *               where a low rumble and the drip of the mine take over.
 */

export type GhostLook = "window" | "float" | "miner" | "shadow";

export interface GhostConfig {
  x: number;
  y: number;
  z: number;
  heading: number;
  look: GhostLook;
  period: number;
  offset: number;
  scale: number;
  drift: number;
  vanish: number;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);
const LOOKS: readonly GhostLook[] = ["window", "float", "miner", "shadow"];

/** How long each kind of ghost is seen for, of its period (seconds). */
export const GHOST_SHOWN: Record<GhostLook, number> = {
  window: 4.5,
  float: 7.0,
  miner: 6.0,
  shadow: 3.5,
};

export function parseGhost(e: Record<string, unknown>): GhostConfig {
  const look = (LOOKS as readonly string[]).includes(String(e.look))
    ? (e.look as GhostLook)
    : "float";
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    look,
    period: Math.max(GHOST_SHOWN[look] + 2, num(e.period, 13)),
    offset: num(e.offset, 0),
    scale: Math.max(0.2, num(e.scale, 1)),
    drift: Math.max(0, num(e.drift, 0)),
    vanish: Math.max(0, num(e.vanish, 0)),
  };
}

const smooth = (t: number) => {
  const u = Math.max(0, Math.min(1, t));
  return u * u * (3 - 2 * u);
};

/**
 * A ghost at time t, `near` metres from the nearest kart: how solid it looks (0 = gone,
 * 1 = as solid as a ghost gets) and where it has drifted to (offsets, game x, y, z).
 */
export function ghostAt(
  g: GhostConfig,
  t: number,
  near = Infinity,
): { alpha: number; dx: number; dy: number; dz: number } {
  const u = (((t - g.offset) % g.period) + g.period) % g.period;
  const shown = GHOST_SHOWN[g.look];
  // Fade in over the first quarter, out over the last third.
  let alpha =
    u < shown ? Math.min(smooth(u / (shown * 0.25)), smooth((shown - u) / (shown * 0.33))) : 0;
  if (g.vanish > 0) alpha *= smooth((near - g.vanish * 0.45) / (g.vanish * 0.55));
  const bob = g.look === "float" ? 0.35 * Math.sin(t * 1.7 + g.offset) : 0;
  const a = (t * 0.35 + g.offset) % (Math.PI * 2);
  return {
    alpha,
    dx: g.drift * Math.cos(a),
    dy: bob + (g.look === "float" ? 0.6 * smooth(u / shown) : 0),
    dz: g.drift * Math.sin(a),
  };
}

// ---------------------------------------------------------------- paths

export interface PathPoint {
  x: number;
  y: number;
  z: number;
  d: number;
}

/** An open path from a route's points, with distances along it. */
export function openPath(points: { x: number; y: number; z: number }[]): {
  points: PathPoint[];
  length: number;
} {
  let d = 0;
  const out = points.map((p, k) => {
    if (k) d += Math.hypot(p.x - points[k - 1]!.x, p.z - points[k - 1]!.z);
    return { x: p.x, y: p.y, z: p.z, d };
  });
  return { points: out, length: d };
}

/** The point `d` metres along an open path (clamped to its ends), and its heading. */
export function pathPoint(
  path: { points: PathPoint[]; length: number },
  d: number,
): { x: number; y: number; z: number; heading: number } {
  const p = path.points;
  const dd = Math.max(0, Math.min(path.length, d));
  let i = 0;
  while (i < p.length - 2 && p[i + 1]!.d < dd) i++;
  const a = p[i]!;
  const b = p[Math.min(p.length - 1, i + 1)]!;
  const span = b.d - a.d;
  const f = span > 0 ? (dd - a.d) / span : 0;
  return {
    x: a.x + (b.x - a.x) * f,
    y: a.y + (b.y - a.y) * f,
    z: a.z + (b.z - a.z) * f,
    heading: Math.atan2(b.x - a.x, b.z - a.z),
  };
}

export interface RiderConfig {
  route: string;
  period: number;
  offset: number;
  travel: number;
}

export function parseRider(e: Record<string, unknown>): RiderConfig {
  const travel = Math.max(2, num(e.travel, 14));
  return {
    route: String(e.route ?? ""),
    period: Math.max(travel + 2, num(e.period, 38)),
    offset: num(e.offset, 0),
    travel,
  };
}

/** The ghost rider at time t: how far along the ride (0..1, or -1 when not riding) and
 * how solid (rising out of the mist, melting back into it). */
export function riderAt(r: RiderConfig, t: number): { u: number; alpha: number } {
  const k = (((t - r.offset) % r.period) + r.period) % r.period;
  if (k > r.travel) return { u: -1, alpha: 0 };
  const u = k / r.travel;
  return { u, alpha: Math.min(smooth(u / 0.15), smooth((1 - u) / 0.2)) };
}

export interface RailcartConfig {
  route: string;
  period: number;
  offset: number;
  travel: number;
  pause: number;
}

export function parseRailcart(e: Record<string, unknown>): RailcartConfig {
  const travel = Math.max(1, num(e.travel, 13));
  const pause = Math.max(0, num(e.pause, 4));
  return {
    route: String(e.route ?? ""),
    period: Math.max(2 * (travel + pause), num(e.period, 34)),
    offset: num(e.offset, 0),
    travel,
    pause,
  };
}

/** Where the rail cart is (0..1 along its path) and whether it's rolling: out, a pause
 * at the far end, back, and a rest until the period comes round. Eased at each end, the
 * way a cart on a slight grade gathers speed and slows. */
export function railcartAt(c: RailcartConfig, t: number): { u: number; moving: boolean } {
  const k = (((t - c.offset) % c.period) + c.period) % c.period;
  if (k < c.travel) return { u: smooth(k / c.travel), moving: true };
  if (k < c.travel + c.pause) return { u: 1, moving: false };
  if (k < 2 * c.travel + c.pause)
    return { u: 1 - smooth((k - c.travel - c.pause) / c.travel), moving: true };
  return { u: 0, moving: false };
}

// ---------------------------------------------------------------- doors

export interface DoorConfig {
  x: number;
  y: number;
  z: number;
  heading: number;
  width: number;
  period: number;
}

export function parseDoor(e: Record<string, unknown>): DoorConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    width: Math.max(0.6, num(e.width, 2.4)),
    period: Math.max(4, num(e.period, 9)),
  };
}

/** The swinging doors' angle at time t (radians; 0 shut): each period they're pushed
 * open from inside by nobody at all, and flap shut, swinging back and forth. */
export function doorSwing(d: DoorConfig, t: number): number {
  const k = ((t % d.period) + d.period) % d.period;
  if (k > 4) return 0;
  return 1.2 * Math.exp(-k * 1.1) * Math.sin(k * 5.0 + 0.3) * smooth(k / 0.3);
}

// ---------------------------------------------------------------- wisps and sounds

export interface WispsConfig {
  x: number;
  y: number;
  z: number;
  radius: number;
  count: number;
}

export function parseWisps(e: Record<string, unknown>): WispsConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    radius: Math.max(1, num(e.radius, 12)),
    count: Math.max(1, Math.min(40, Math.round(num(e.count, 8)))),
  };
}

/** Wisp k of a group at time t: each on its own looping, wandering path inside the
 * radius (no two the same), rising and sinking a little, glowing brighter and dimmer. */
export function wispAt(
  w: WispsConfig,
  k: number,
  t: number,
): { x: number; y: number; z: number; glow: number } {
  const s = k * 1.618 + 0.37;
  const a = t * (0.13 + 0.05 * Math.sin(s * 3.1)) + s * 4.0;
  const r = w.radius * (0.35 + 0.55 * (0.5 + 0.5 * Math.sin(t * 0.21 + s * 2.3)));
  return {
    x: w.x + Math.cos(a) * r + 1.5 * Math.sin(t * 0.9 + s * 7),
    y: w.y + 1.6 * Math.sin(t * 0.43 + s * 5.0) + 0.5 * Math.sin(t * 1.3 + s),
    z: w.z + Math.sin(a * 1.3) * r * 0.8 + 1.5 * Math.cos(t * 0.7 + s * 3),
    glow: 0.55 + 0.45 * Math.sin(t * (1.1 + 0.4 * Math.sin(s)) + s * 9.0),
  };
}

export interface SoundSpot {
  x: number;
  y: number;
  z: number;
  radius: number;
}

export function parseSpot(e: Record<string, unknown>, radius: number): SoundSpot {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    radius: Math.max(1, num(e.radius, radius)),
  };
}

export interface AmbienceConfig {
  wind: number;
  caves: SoundSpot[];
}

export function parseAmbience(e: Record<string, unknown>): AmbienceConfig {
  const caves: SoundSpot[] = [];
  if (Array.isArray(e.caves))
    for (const c of e.caves)
      if (Array.isArray(c) && c.length >= 4 && c.every((v) => typeof v === "number"))
        caves.push({ x: c[0]!, y: c[1]!, z: c[2]!, radius: Math.max(1, c[3]!) });
  return { wind: Math.max(0, Math.min(1, num(e.wind, 0.5))), caves };
}

/** How far underground a point is (0 out in the open .. 1 deep in the mine). */
export function underground(a: AmbienceConfig, x: number, y: number, z: number): number {
  let best = 0;
  for (const c of a.caves) {
    const d = Math.hypot(x - c.x, y - c.y, z - c.z);
    best = Math.max(best, smooth((c.radius - d) / (c.radius * 0.5)));
  }
  return best;
}
