/**
 * Loop-the-loops: a road that climbs, goes right over the top upside down and comes
 * back down, offset sideways so the exit clears the entry.
 *
 * A loop is a track.json entity:
 *
 *   { "type": "loop", "id": "rift_loop", "x", "y", "z", "heading",
 *     "radius": 22, "ramp": 26, "offset": 18, "width": 14,
 *     "minSpeed": 14, "commit": 18, "boostMult": 1.45, "boostSec": 2.2, "gravity": 8 }
 *
 * (x, y, z) is where the loop starts on the road (game coordinates, the road surface)
 * and `heading` the direction of travel there (kart convention: forward is
 * (sin h, 0, cos h)). The exit is `offset` metres to the driver's right of the entry
 * line, a little way ahead, facing the same way. The Blender kit (course_kit.py,
 * `loop_path`) builds the same curve for the visible road; track.json carries a few of
 * its points ("probe") and tests/loops.test.ts checks the two agree.
 *
 * The shape: the road's pitch angle φ turns through 360° along its length. Its rate of
 * turn (curvature) eases in over `ramp` metres, holds at 1/radius through the circular
 * part and eases out again, so there is no sudden kink at either end (a clothoid
 * entry, like a real coaster's). The sideways shift is a smootherstep along the length,
 * so the road is straight (no sideways slope) where it meets the ordinary road.
 *
 * Driving it: crossing either end's gate onto the loop, driving forwards and roughly
 * lined up, hands the kart to a special loop mode (like the mode-change triggers of
 * classic kart racers). In it the kart is attached to the road surface: it moves along
 * the curve by its speed, with gravity along the road slowing it on the way up and
 * speeding it on the way down, and steering moves it across the road between the
 * edges. Past `commit` metres an assist won't let it drop below `minSpeed`, so it
 * always makes it over; before that you can still back out. The normal kart model
 * still runs every step for throttle, brakes, boosts and zippers (with the steering
 * taken over here), and normal driving resumes at either end with the kart's speed,
 * position and heading carried across exactly.
 *
 * Rides use the same machinery on a road of any shape (a "ride" entity: its centre line
 * as points). The spiral up inside Snowy Summit's great tree is one: it takes the kart up
 * both turns at full zipper speed, steering only across the road, like a coaster:
 *
 *   { "type": "ride", "id": "tree_spiral", "points": [[x, y, z, bank?], ...] (the road's
 *     centre, entry to exit, every metre or two; bank in degrees, + = its right side
 *     lower, as the Blender kit banks roads), "width": 13, "minSpeed": 28, "outSpeed": 22, "commit": 0,
 *     "boostMult": 1.35, "boostSec": 12, "gravity": 0 }
 *
 * On a ride the kart's race position is where it really is (the road is the race line).
 *
 * Everything here is pure (no three.js): the session, the AI test and the renderer
 * share it.
 */
import type { InputState } from "../core/input";
import { applyBoost, type KartConfig, type KartState } from "../vehicles/kart";

export interface LoopDef {
  id: string;
  x: number;
  y: number;
  z: number;
  heading: number;
  /** Radius of the circular part (the top), m. */
  radius: number;
  /** Length of the easing curve at each end, m. */
  ramp: number;
  /** Sideways shift from entry to exit, m (+ = to the driver's right). */
  offset: number;
  width: number;
  /** The assist keeps the kart at least this fast once committed, m/s. */
  minSpeed: number;
  /** Metres in after which the assist takes over (before it, you can back out). */
  commit: number;
  /** The entry booster (a boost, as from a pad): top-speed multiplier and seconds; 0 = none. */
  boostMult: number;
  boostSec: number;
  /** Gravity along the road, m/s² (gentler than in the air: it's arcade). */
  gravity: number;
}

export interface LoopPath extends LoopDef {
  /** Arc length, m. */
  length: number;
  /** Curvature of the circular part (1/radius). */
  k0: number;
  /** Forward (a) and up (b) distance of the centre line from the entry, every `ds`. */
  a: Float64Array;
  b: Float64Array;
  ds: number;
  /** The exit point (road surface). */
  exit: { x: number; y: number; z: number };
  /** Entry axes: forward and the driver's right (horizontal). */
  fwd: { x: number; z: number };
  right: { x: number; z: number };
  /** The direction of travel out of the exit, and its axes (a loop's are its entry's). */
  exitHeading: number;
  exitFwd: { x: number; z: number };
  exitRight: { x: number; z: number };
  /** A ride's least speed as it comes out (it eases down to it), m/s. */
  outSpeed?: number;
  /** A ride: its centre line (and the distance along it at each point). */
  path?: { x: Float64Array; y: Float64Array; z: Float64Array; s: Float64Array; bank: Float64Array };
}

/** Where the road is at a distance along it, and which way it faces. */
export interface LoopFrame {
  /** Centre line, on the road surface. */
  px: number;
  py: number;
  pz: number;
  /** Tangent (direction of the road, entry to exit). */
  tx: number;
  ty: number;
  tz: number;
  /** Surface normal (the road's "up": toward the loop's centre). */
  nx: number;
  ny: number;
  nz: number;
  /** Across the road (the right of a kart driving entry to exit). */
  bx: number;
  by: number;
  bz: number;
}

const SAMPLES = 1024;
const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

/** A loop from a track.json entity (defaults for anything missing). */
export function parseLoop(e: Record<string, unknown>): LoopDef {
  return {
    id: typeof e.id === "string" ? e.id : "loop",
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    heading: num(e.heading, 0),
    radius: clamp(num(e.radius, 20), 4, 200),
    ramp: clamp(num(e.ramp, 24), 0, 200),
    offset: num(e.offset, 16),
    width: clamp(num(e.width, 14), 4, 60),
    minSpeed: clamp(num(e.minSpeed, 14), 0, 100),
    commit: Math.max(0, num(e.commit, 18)),
    boostMult: Math.max(0, num(e.boostMult, 0)),
    boostSec: Math.max(0, num(e.boostSec, 0)),
    gravity: Math.max(0, num(e.gravity, 8)),
  };
}

/** The pitch angle at distance s along a loop of length L (radians, 0 .. 2π). */
export function loopPitch(p: { k0: number; ramp: number; length: number }, s: number): number {
  const { k0, ramp: r, length: L } = p;
  if (s <= 0) return 0;
  if (s >= L) return 2 * Math.PI;
  if (r > 0 && s < r) return (k0 * s * s) / (2 * r);
  if (r > 0 && s > L - r) return 2 * Math.PI - (k0 * (L - s) * (L - s)) / (2 * r);
  return k0 * (r / 2) + k0 * (s - r);
}

/** Sideways shift share along the loop (smootherstep: flat at both ends). */
const shift = (u: number) => {
  const t = clamp(u, 0, 1);
  return t * t * t * (t * (t * 6 - 15) + 10);
};
const shiftRate = (u: number) => {
  const t = clamp(u, 0, 1);
  return 30 * t * t * (1 - t) * (1 - t);
};

export function buildLoop(def: LoopDef): LoopPath {
  const k0 = 1 / def.radius;
  const length = 2 * Math.PI * def.radius + def.ramp;
  const ds = length / SAMPLES;
  const a = new Float64Array(SAMPLES + 1);
  const b = new Float64Array(SAMPLES + 1);
  const shape = { k0, ramp: def.ramp, length };
  for (let i = 0; i < SAMPLES; i++) {
    const phi = loopPitch(shape, (i + 0.5) * ds);
    a[i + 1] = a[i]! + Math.cos(phi) * ds;
    b[i + 1] = b[i]! + Math.sin(phi) * ds;
  }
  const fwd = { x: Math.sin(def.heading), z: Math.cos(def.heading) };
  const right = { x: -Math.cos(def.heading), z: Math.sin(def.heading) };
  const ea = a[SAMPLES]!;
  const eb = b[SAMPLES]!;
  return {
    ...def,
    length,
    k0,
    a,
    b,
    ds,
    fwd,
    right,
    exitHeading: def.heading,
    exitFwd: fwd,
    exitRight: right,
    exit: {
      x: def.x + fwd.x * ea + right.x * def.offset,
      y: def.y + eb,
      z: def.z + fwd.z * ea + right.z * def.offset,
    },
  };
}

/** A ride from a track.json "ride" entity: a road of any shape, given by its centre line. */
export function parseRide(e: Record<string, unknown>): LoopPath | undefined {
  const raw = Array.isArray(e.points) ? (e.points as unknown[]) : [];
  const pts = raw.filter(
    (q): q is number[] => Array.isArray(q) && q.length >= 3 && q.every((v) => Number.isFinite(v)),
  );
  if (pts.length < 3) return undefined;
  const n = pts.length;
  const path = {
    x: new Float64Array(n),
    y: new Float64Array(n),
    z: new Float64Array(n),
    s: new Float64Array(n),
    bank: new Float64Array(n),
  };
  for (let i = 0; i < n; i++) {
    const [x, y, z] = pts[i]!;
    path.x[i] = x!;
    path.y[i] = y!;
    path.z[i] = z!;
    path.bank[i] = ((pts[i]![3] ?? 0) * Math.PI) / 180;
    if (i)
      path.s[i] =
        path.s[i - 1]! + Math.hypot(x! - path.x[i - 1]!, y! - path.y[i - 1]!, z! - path.z[i - 1]!);
  }
  const heading = Math.atan2(path.x[1]! - path.x[0]!, path.z[1]! - path.z[0]!);
  const exitHeading = Math.atan2(path.x[n - 1]! - path.x[n - 2]!, path.z[n - 1]! - path.z[n - 2]!);
  const axes = (h: number) => ({
    fwd: { x: Math.sin(h), z: Math.cos(h) },
    right: { x: -Math.cos(h), z: Math.sin(h) },
  });
  const a = axes(heading);
  const b = axes(exitHeading);
  return {
    id: typeof e.id === "string" ? e.id : "ride",
    x: path.x[0]!,
    y: path.y[0]!,
    z: path.z[0]!,
    heading,
    radius: 0,
    ramp: 0,
    offset: 0,
    width: clamp(num(e.width, 14), 4, 60),
    minSpeed: clamp(num(e.minSpeed, 24), 0, 100),
    commit: Math.max(0, num(e.commit, 0)),
    boostMult: Math.max(0, num(e.boostMult, 0)),
    boostSec: Math.max(0, num(e.boostSec, 0)),
    gravity: Math.max(0, num(e.gravity, 0)),
    outSpeed: clamp(num(e.outSpeed, num(e.minSpeed, 24)), 0, 100),
    length: path.s[n - 1]!,
    k0: 0,
    a: new Float64Array(0),
    b: new Float64Array(0),
    ds: 1,
    fwd: a.fwd,
    right: a.right,
    exitHeading,
    exitFwd: b.fwd,
    exitRight: b.right,
    exit: { x: path.x[n - 1]!, y: path.y[n - 1]!, z: path.z[n - 1]! },
    path,
  };
}

/** A ride's frame at distance s along its centre line (0 < s < length). */
function rideFrame(p: LoopPath, s: number, f: LoopFrame): LoopFrame {
  const P = p.path!;
  const n = P.s.length;
  let lo = 0;
  let hi = n - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (P.s[mid]! <= s) lo = mid;
    else hi = mid;
  }
  const t = (s - P.s[lo]!) / Math.max(1e-9, P.s[hi]! - P.s[lo]!);
  f.px = P.x[lo]! + (P.x[hi]! - P.x[lo]!) * t;
  f.py = P.y[lo]! + (P.y[hi]! - P.y[lo]!) * t;
  f.pz = P.z[lo]! + (P.z[hi]! - P.z[lo]!) * t;
  // Tangent: across the neighbouring points (smooth from one to the next).
  const a = Math.max(0, lo - 1);
  const b = Math.min(n - 1, hi + 1);
  let tx = P.x[b]! - P.x[a]!;
  let ty = P.y[b]! - P.y[a]!;
  let tz = P.z[b]! - P.z[a]!;
  const tl = Math.hypot(tx, ty, tz) || 1;
  tx /= tl;
  ty /= tl;
  tz /= tl;
  // Up: the world's up, square to the road.
  let nx = -ty * tx;
  let ny = 1 - ty * ty;
  let nz = -ty * tz;
  const nl = Math.hypot(nx, ny, nz) || 1;
  nx /= nl;
  ny /= nl;
  nz /= nl;
  let bx = ty * nz - tz * ny;
  let by = tz * nx - tx * nz;
  let bz = tx * ny - ty * nx;
  // The road's bank: turn the across and up axes about the tangent (right side lower).
  const th = P.bank[lo]! + (P.bank[hi]! - P.bank[lo]!) * t;
  if (th !== 0) {
    const c = Math.cos(th);
    const sn = Math.sin(th);
    const nb = [nx * c + bx * sn, ny * c + by * sn, nz * c + bz * sn];
    [bx, by, bz] = [bx * c - nx * sn, by * c - ny * sn, bz * c - nz * sn];
    [nx, ny, nz] = nb as [number, number, number];
  }
  f.tx = tx;
  f.ty = ty;
  f.tz = tz;
  f.nx = nx;
  f.ny = ny;
  f.nz = nz;
  f.bx = bx;
  f.by = by;
  f.bz = bz;
  return f;
}

/** The road's frame at distance s (beyond either end it carries on straight). */
export function loopFrame(p: LoopPath, s: number, out?: LoopFrame): LoopFrame {
  const f = out ?? ({} as LoopFrame);
  const start = s <= 0;
  const fwd = start ? p.fwd : p.exitFwd;
  const right = start ? p.right : p.exitRight;
  if (s > 0 && s < p.length && p.path) return rideFrame(p, s, f);
  if (s <= 0 || s >= p.length) {
    const o = s <= 0 ? { x: p.x, y: p.y, z: p.z } : p.exit;
    const along = s <= 0 ? s : s - p.length;
    f.px = o.x + fwd.x * along;
    f.py = o.y;
    f.pz = o.z + fwd.z * along;
    f.tx = fwd.x;
    f.ty = 0;
    f.tz = fwd.z;
    f.nx = 0;
    f.ny = 1;
    f.nz = 0;
    f.bx = right.x;
    f.by = 0;
    f.bz = right.z;
    return f;
  }
  const { fwd: lf, right: lr } = p;
  const at = s / p.ds;
  const i = Math.min(SAMPLES - 1, Math.floor(at));
  const t = at - i;
  const la = p.a[i]! + (p.a[i + 1]! - p.a[i]!) * t;
  const lb = p.b[i]! + (p.b[i + 1]! - p.b[i]!) * t;
  const u = s / p.length;
  const lc = p.offset * shift(u);
  const phi = loopPitch(p, s);
  const ca = Math.cos(phi);
  const sb = Math.sin(phi);
  const cc = (p.offset * shiftRate(u)) / p.length;
  f.px = p.x + lf.x * la + lr.x * lc;
  f.py = p.y + lb;
  f.pz = p.z + lf.z * la + lr.z * lc;
  // Tangent: forward·cos φ + up·sin φ + right·(shift rate).
  let tx = lf.x * ca + lr.x * cc;
  let ty = sb;
  let tz = lf.z * ca + lr.z * cc;
  const tl = Math.hypot(tx, ty, tz);
  tx /= tl;
  ty /= tl;
  tz /= tl;
  // Normal = right × tangent (up at the entry, down at the top), then across = T × N.
  let nx = 0 * tz - lr.z * ty;
  let ny = lr.z * tx - lr.x * tz;
  let nz = lr.x * ty - 0 * tx;
  const nl = Math.hypot(nx, ny, nz);
  nx /= nl;
  ny /= nl;
  nz /= nl;
  f.tx = tx;
  f.ty = ty;
  f.tz = tz;
  f.nx = nx;
  f.ny = ny;
  f.nz = nz;
  f.bx = ty * nz - tz * ny;
  f.by = tz * nx - tx * nz;
  f.bz = tx * ny - ty * nx;
  return f;
}

/** How high the loop's road goes above its entry, m. */
export const loopHeight = (p: LoopPath) => Math.max(...p.b);

// ---- Riding ---------------------------------------------------------------------------

/** One kart's loop state. */
export interface LoopRide {
  /** Index of the loop being ridden; -1 = normal driving. */
  loop: number;
  /** Distance along the loop (entry 0 .. exit length). */
  s: number;
  /** Across the road from the centre line, m (+ = the entry-to-exit right). */
  d: number;
  /** Kart's yaw relative to the road, radians (+ = turned left of the direction of travel). */
  rel: number;
  /** +1 riding entry to exit; -1 riding it backwards (came in at the exit, the wrong way). */
  dir: number;
  /** Metres driven into the loop (for the commit point). */
  travelled: number;
  time: number;
  /** Last step's s, d, rel: for drawing between steps. */
  ps: number;
  pd: number;
  prel: number;
  /** After leaving a loop: which one and which way (for the camera's hand-back). */
  last: number;
  lastDir: number;
}

export function newRide(): LoopRide {
  return {
    loop: -1,
    s: 0,
    d: 0,
    rel: 0,
    dir: 1,
    travelled: 0,
    time: 0,
    ps: 0,
    pd: 0,
    prel: 0,
    last: -1,
    lastDir: 1,
  };
}

/** Steering in the loop: yaw rate at full lock, rad/s; centring when let go, per second. */
const STEER_RATE = 1.7;
const CENTRE = 2.5;
/** Most the kart can angle across the road, radians. */
const MAX_REL = 0.42;
/** Kept this far inside the road edges, m. */
const EDGE = 1.1;
/** The assist's acceleration up to the minimum speed, m/s². */
const ASSIST = 45;
/** Safety net: a ride this long ends at the far end. */
const MAX_RIDE = 25;
/** A ride eases down to its outSpeed over this many metres before its exit. */
const OUT_EASE = 45;
/** Capture: how far from the line across, above or below, and how far off line. */
const CATCH_SIDE = 1.5;
const CATCH_HEIGHT = 2.5;
const CATCH_ANGLE = 1.15;

export interface LoopSystem {
  paths: LoopPath[];
  rides: LoopRide[];
  /** Is kart i on a loop? */
  riding(i: number): boolean;
  /**
   * Before stepKart: while riding, the kart model gets the throttle and brake only (the
   * loop does the steering) and is kept on the ground without drifting.
   */
  input(i: number, k: KartState, want: InputState): InputState;
  /**
   * After the kart has moved: ride the loop (riding), or check whether it just drove
   * onto one (from `before`). Returns what happened.
   */
  step(
    i: number,
    k: KartState,
    before: { x: number; y: number; z: number },
    steer: number,
    cfg: KartConfig,
    dt: number,
  ): { entered?: LoopPath; exited?: LoopPath };
  /** Where race logic should think a riding kart is: the matching point on the road
   * straight from entry to exit, so gates and places never see the loop's tangle. */
  racePos(i: number, k: KartState): { x: number; y: number; z: number };
  /** AI on the approach: a point on the entry line to aim at, so it arrives straight. */
  aim(i: number, k: KartState): { x: number; z: number } | undefined;
  /** AI steering while riding: hold the middle of the road. */
  aiSteer(i: number): number;
  /** Karts on the same loop bump along and across the road. Returns pairs touching. */
  contacts(karts: KartState[]): number;
  /** Respawned or restarted: back to normal driving. */
  reset(i: number): void;
  /** Pose for drawing kart i between steps (alpha 0..1); undefined when not riding. */
  pose(i: number, alpha: number): LoopPose | undefined;
  /** The loop camera's rail point for kart i (undefined when it isn't needed). */
  rail(i: number, k: KartState, alpha: number, cam: RailConfig): RailView | undefined;
}

export interface LoopPose {
  /** Road surface under the kart. */
  x: number;
  y: number;
  z: number;
  /** Kart forward and up (unit). */
  fx: number;
  fy: number;
  fz: number;
  ux: number;
  uy: number;
  uz: number;
}

export interface RailConfig {
  /** Camera distance behind along the road, height above it, aim height, look ahead. */
  distance: number;
  height: number;
  lookHeight: number;
  lookAhead: number;
  /** Keep giving the rail along the exit straight (while the camera blends back out). */
  keep?: boolean;
}

export interface RailView {
  /** Still on the loop (riding, or the camera hasn't left it yet): blend it in. */
  hold: boolean;
  px: number;
  py: number;
  pz: number;
  lx: number;
  ly: number;
  lz: number;
  ux: number;
  uy: number;
  uz: number;
}

export function loopEntities(entities: unknown[]): LoopDef[] {
  return entities
    .filter(
      (e): e is Record<string, unknown> =>
        typeof e === "object" && e !== null && (e as { type?: unknown }).type === "loop",
    )
    .map(parseLoop);
}

/** Loops for a track's entities, for `karts` karts; undefined when it has none. */
export function createLoops(entities: unknown[], karts: number): LoopSystem | undefined {
  const paths = [...loopEntities(entities).map(buildLoop), ...rideEntities(entities)];
  if (!paths.length) return undefined;
  return createLoopSystem(paths, karts);
}

export function rideEntities(entities: unknown[]): LoopPath[] {
  return entities
    .filter(
      (e): e is Record<string, unknown> =>
        typeof e === "object" && e !== null && (e as { type?: unknown }).type === "ride",
    )
    .map(parseRide)
    .filter((p): p is LoopPath => p !== undefined);
}

export function createLoopSystem(paths: LoopPath[], karts: number): LoopSystem {
  const rides = Array.from({ length: karts }, newRide);
  const fr = {} as LoopFrame;

  /** Put the kart where its ride says (position, heading, surface normal). */
  function place(r: LoopRide, k: KartState) {
    const p = paths[r.loop]!;
    loopFrame(p, r.s, fr);
    k.x = fr.px + fr.bx * r.d;
    k.y = fr.py + fr.by * r.d;
    k.z = fr.pz + fr.bz * r.d;
    // Kart forward: the direction of travel, turned by rel (left = away from the right).
    const c = Math.cos(r.rel);
    const sn = Math.sin(r.rel);
    const fx = r.dir * (fr.tx * c - fr.bx * sn);
    const fz = r.dir * (fr.tz * c - fr.bz * sn);
    // Heading only means something while the road isn't near vertical.
    if (Math.hypot(fx, fz) > 0.25) {
      k.heading = Math.atan2(fx, fz);
      k.velAngle = k.heading;
    }
    k.nx = fr.nx;
    k.ny = fr.ny;
    k.nz = fr.nz;
    k.grounded = true;
    k.vy = 0;
    k.slope = 0;
  }

  /** Hand back to normal driving at the end the kart has gone past. */
  function leave(i: number, k: KartState) {
    const r = rides[i]!;
    const p = paths[r.loop]!;
    loopFrame(p, r.s, fr);
    k.x = fr.px + fr.bx * r.d;
    k.y = fr.py;
    k.z = fr.pz + fr.bz * r.d;
    // Past either end the road is straight along the entry heading.
    const base = r.dir > 0 ? p.exitHeading : p.heading + Math.PI;
    k.heading = wrap(base + r.rel);
    k.velAngle = k.heading;
    k.nx = 0;
    k.ny = 1;
    k.nz = 0;
    k.grounded = true;
    k.vy = 0;
    k.slope = 0;
    r.last = r.loop;
    r.lastDir = r.dir;
    r.loop = -1;
    return p;
  }

  function capture(i: number, k: KartState, before: { x: number; y: number; z: number }) {
    if (k.speed <= 0) return undefined;
    // Lined up by where it's going, not where it's facing: a kart spinning out (hit as
    // it reaches the loop, Blake) still travels into it, and is carried round.
    const mx = k.x - before.x;
    const mz = k.z - before.z;
    const travel = Math.hypot(mx, mz) > 1e-4 ? Math.atan2(mx, mz) : k.heading;
    for (let li = 0; li < paths.length; li++) {
      const p = paths[li]!;
      for (const dir of [1, -1]) {
        const g = dir > 0 ? { x: p.x, y: p.y, z: p.z } : p.exit;
        // Gate normal points into the loop.
        const gf = dir > 0 ? p.fwd : p.exitFwd;
        const gr = dir > 0 ? p.right : p.exitRight;
        const nx = gf.x * dir;
        const nz = gf.z * dir;
        const pd = (before.x - g.x) * nx + (before.z - g.z) * nz;
        const qd = (k.x - g.x) * nx + (k.z - g.z) * nz;
        if (!(pd < 0 && qd >= 0)) continue;
        const t = pd / (pd - qd);
        const ax = before.x + (k.x - before.x) * t;
        const ay = before.y + (k.y - before.y) * t;
        const az = before.z + (k.z - before.z) * t;
        const lat = (ax - g.x) * gr.x + (az - g.z) * gr.z;
        if (Math.abs(lat) > p.width / 2 + CATCH_SIDE) continue;
        if (Math.abs(ay - g.y) > CATCH_HEIGHT) continue;
        const rel = wrap(travel - (dir > 0 ? p.heading : p.exitHeading + Math.PI));
        if (Math.abs(rel) > CATCH_ANGLE) continue;
        k.spinTime = 0; // (the loop straightens it out)
        const r = rides[i]!;
        r.loop = li;
        r.dir = dir;
        r.s = dir > 0 ? qd : p.length - qd;
        r.d = clamp(lat, -(p.width / 2 - EDGE), p.width / 2 - EDGE);
        r.rel = clamp(rel, -MAX_REL, MAX_REL);
        r.travelled = qd;
        r.time = 0;
        r.ps = r.s;
        r.pd = r.d;
        r.prel = r.rel;
        return p;
      }
    }
    return undefined;
  }

  const sys: LoopSystem = {
    paths,
    rides,
    riding: (i) => rides[i]!.loop >= 0,
    input(i, k, want) {
      if (rides[i]!.loop < 0) return want;
      k.grounded = true;
      k.slope = 0;
      if (k.driftDir !== 0 || k.recovering) {
        k.driftDir = 0;
        k.recovering = false;
        k.driftOffset = 0;
      }
      k.spinTime = 0;
      return { ...want, steer: 0, drift: false };
    },
    step(i, k, before, steer, cfg, dt) {
      const r = rides[i]!;
      if (r.loop < 0) {
        const p = capture(i, k, before);
        if (!p) return {};
        if (p.boostMult > 0 && p.boostSec > 0) applyBoost(k, cfg, p.boostMult, p.boostSec);
        place(r, k);
        return { entered: p };
      }
      const p = paths[r.loop]!;
      r.ps = r.s;
      r.pd = r.d;
      r.prel = r.rel;
      loopFrame(p, r.s, fr);
      // Gravity along the road: slower going up, faster coming down.
      k.speed -= p.gravity * fr.ty * r.dir * dt;
      // Past the commit point the loop won't let you stall: it carries you round.
      // (A ride eases off to outSpeed over its last OUT_EASE metres, so you come out
      // under control.)
      const left = r.dir > 0 ? p.length - r.s : r.s;
      const least =
        p.outSpeed !== undefined && left < OUT_EASE
          ? p.outSpeed + (p.minSpeed - p.outSpeed) * (left / OUT_EASE)
          : p.minSpeed;
      if (r.travelled > p.commit && k.speed < least)
        k.speed = Math.min(least, k.speed + ASSIST * dt);
      // Steering turns the kart across the road; let go and it lines back up.
      r.rel -= clamp(steer, -1, 1) * STEER_RATE * dt;
      if (Math.abs(steer) < 0.1) r.rel *= Math.exp(-CENTRE * dt);
      r.rel = clamp(r.rel, -MAX_REL, MAX_REL);
      const along = Math.cos(r.rel) * k.speed * dt;
      r.s += r.dir * along;
      r.travelled += along;
      r.d -= r.dir * Math.sin(r.rel) * k.speed * dt;
      const lim = p.width / 2 - EDGE;
      if (Math.abs(r.d) > lim) {
        // At the edge: held on the road, and the kart straightens up along it.
        r.d = Math.sign(r.d) * lim;
        r.rel *= Math.exp(-8 * dt);
      }
      r.time += dt;
      if (r.time > MAX_RIDE) r.s = r.dir > 0 ? p.length : 0;
      if (r.s >= p.length || r.s <= 0) return { exited: leave(i, k) };
      place(r, k);
      return {};
    },
    racePos(i, k) {
      const r = rides[i]!;
      if (r.loop < 0) return { x: k.x, y: k.y, z: k.z };
      const p = paths[r.loop]!;
      if (p.path) return { x: k.x, y: k.y, z: k.z };
      const u = clamp(r.s / p.length, 0, 1);
      return {
        x: p.x + (p.exit.x - p.x) * u + p.right.x * r.d,
        y: p.y + (p.exit.y - p.y) * u,
        z: p.z + (p.exit.z - p.z) * u + p.right.z * r.d,
      };
    },
    aim(i, k) {
      if (rides[i]!.loop >= 0) return undefined;
      for (const p of paths) {
        const rx = k.x - p.x;
        const rz = k.z - p.z;
        const along = rx * p.fwd.x + rz * p.fwd.z;
        const lat = rx * p.right.x + rz * p.right.z;
        if (along < -55 || along > 0 || Math.abs(lat) > p.width * 1.5) continue;
        if (Math.abs(k.y - p.y) > 6) continue;
        if (Math.abs(wrap(k.heading - p.heading)) > 1.4) continue;
        const ahead = Math.min(-along, 14) + 6;
        return { x: p.x + p.fwd.x * (along + ahead), z: p.z + p.fwd.z * (along + ahead) };
      }
      return undefined;
    },
    aiSteer(i) {
      const r = rides[i]!;
      if (r.loop < 0) return 0;
      // Travel-right offset; aim to turn back toward the middle, gently.
      const off = r.d * r.dir;
      const want = clamp(0.08 * off, -0.25, 0.25);
      return clamp((r.rel - want) * 3, -1, 1);
    },
    contacts(karts) {
      let touches = 0;
      for (let i = 0; i < karts.length; i++) {
        const a = rides[i]!;
        if (a.loop < 0) continue;
        for (let j = i + 1; j < karts.length; j++) {
          const b = rides[j]!;
          if (b.loop !== a.loop) continue;
          const ds = b.s - a.s;
          const dd = b.d - a.d;
          if (Math.abs(ds) > 2.2 || Math.abs(dd) > 1.9) continue;
          touches++;
          const push = (1.9 - Math.abs(dd)) / 2;
          const side = dd === 0 ? (i < j ? 1 : -1) : Math.sign(dd);
          a.d -= side * push;
          b.d += side * push;
          // Closing up along the road: the two share their speed.
          const ka = karts[i]!;
          const kb = karts[j]!;
          const rear = ds * a.dir > 0 ? ka : kb;
          const front = rear === ka ? kb : ka;
          if (rear.speed > front.speed) {
            const v = (rear.speed + front.speed) / 2;
            rear.speed = v;
            front.speed = v;
          }
        }
      }
      return touches;
    },
    reset(i) {
      const r = rides[i]!;
      r.loop = -1;
      r.last = -1;
    },
    pose(i, alpha) {
      const r = rides[i]!;
      if (r.loop < 0) return undefined;
      const p = paths[r.loop]!;
      const s = r.ps + (r.s - r.ps) * alpha;
      const d = r.pd + (r.d - r.pd) * alpha;
      const rel = r.prel + (r.rel - r.prel) * alpha;
      loopFrame(p, s, fr);
      const c = Math.cos(rel);
      const sn = Math.sin(rel);
      return {
        x: fr.px + fr.bx * d,
        y: fr.py + fr.by * d,
        z: fr.pz + fr.bz * d,
        fx: r.dir * (fr.tx * c - fr.bx * sn),
        fy: r.dir * (fr.ty * c - fr.by * sn),
        fz: r.dir * (fr.tz * c - fr.bz * sn),
        ux: fr.nx,
        uy: fr.ny,
        uz: fr.nz,
      };
    },
    rail(i, k, alpha, cam) {
      const r = rides[i]!;
      let li = r.loop;
      let s: number;
      let d: number;
      let dir: number;
      let hold = true;
      if (li >= 0) {
        s = r.ps + (r.s - r.ps) * alpha;
        d = r.pd + (r.d - r.pd) * alpha;
        dir = r.dir;
      } else {
        // Just left a loop: keep the rail until the camera is off it too.
        li = r.last;
        if (li < 0) return undefined;
        const p = paths[li]!;
        dir = r.lastDir;
        const g = dir > 0 ? p.exit : { x: p.x, y: p.y, z: p.z };
        const gf = dir > 0 ? p.exitFwd : p.fwd;
        const gr = dir > 0 ? p.exitRight : p.right;
        const along = ((k.x - g.x) * gf.x + (k.z - g.z) * gf.z) * dir;
        const lat = (k.x - g.x) * gr.x + (k.z - g.z) * gr.z;
        hold = along <= cam.distance + 2;
        if (along < -1 || Math.abs(lat) > p.width || (!hold && (!cam.keep || along > 80))) {
          r.last = -1;
          return undefined;
        }
        s = dir > 0 ? p.length + along : -along;
        d = lat;
      }
      const p = paths[li]!;
      // The camera rides the road a little way behind, so it's always inside the loop.
      loopFrame(p, s - dir * cam.distance, fr);
      const px = fr.px + fr.bx * d * 0.6 + fr.nx * cam.height;
      const py = fr.py + fr.by * d * 0.6 + fr.ny * cam.height;
      const pz = fr.pz + fr.bz * d * 0.6 + fr.nz * cam.height;
      const cn = { x: fr.nx, y: fr.ny, z: fr.nz };
      loopFrame(p, s + dir * cam.lookAhead, fr);
      const lx = fr.px + fr.bx * d + fr.nx * cam.lookHeight;
      const ly = fr.py + fr.by * d + fr.ny * cam.lookHeight;
      const lz = fr.pz + fr.bz * d + fr.nz * cam.lookHeight;
      // Up: between the camera's road normal and the kart's, so the roll is smooth.
      loopFrame(p, s, fr);
      const ux = cn.x + fr.nx;
      const uy = cn.y + fr.ny;
      const uz = cn.z + fr.nz;
      const ul = Math.hypot(ux, uy, uz) || 1;
      return { hold, px, py, pz, lx, ly, lz, ux: ux / ul, uy: uy / ul, uz: uz / ul };
    },
  };
  return sys;
}
