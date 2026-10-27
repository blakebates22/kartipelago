/**
 * Checkpoint progression: how far round the course each racer has legally got.
 *
 * A course has an ordered sequence of checkpoints, 0 being the start/finish line. Each
 * checkpoint is one or more invisible **gates**: upright, finite rectangles in 3D, each
 * facing the way you're meant to cross it. A checkpoint with several gates (the main
 * road and a shortcut, say) is passed by crossing any one of them.
 *
 * Progress has nothing to do with the road surface. Leaving the asphalt, drifting over
 * the grass, flying through the air or cutting a corner never costs progress: only the
 * order you cross the gates in matters.
 *
 * - **Forward crossings** are found by sweeping the kart's movement this step (previous
 *   to current position, in 3D) against each gate's plane. That works at any speed, in
 *   the air, and on layered tracks, because each gate has a height as well as a width.
 * - **Crossing the next checkpoint** advances you. Crossing any other one forward is
 *   rejected (it's out of order), and says so for the debug overlay.
 * - **Laps** are awarded only for new progress: crossing the line again after reversing
 *   back over it never counts twice.
 * - **Going backwards** back through your last checkpoint (by more than a metre, so
 *   jittering on a gate doesn't count) takes that checkpoint back off you. Drive round
 *   and cross it again and you carry on as before.
 * - **Teleports** (respawns, being fished out of water) are never swept: they can't
 *   pass or un-pass a gate.
 *
 * Standing in the race is validated checkpoints, then how far you are from your last
 * gate towards the next one: measured across the planes of the road between them (each
 * route sample's, in order, walked from the last gate), never by looking for the
 * nearest bit of road, so being far from the road doesn't move you anywhere.
 *
 * All original code, built from how checkpoint racing works in late-90s kart racers.
 */

/** Where a respawn puts you: a point and the way to face. */
export interface Spot {
  x: number;
  y: number;
  z: number;
  heading: number;
}

export interface CheckpointGate {
  /** Stable id, e.g. "cp03" (or "cp03_shortcut" for an alternate gate). */
  id: string;
  /** Position in the sequence: 0 is the start/finish line. */
  index: number;
  /** "main", or the name of the alternate route the gate is on. */
  route: string;
  /** Bottom centre of the gate, on the road. */
  x: number;
  y: number;
  z: number;
  /** Unit forward (the crossing direction), horizontal. */
  fx: number;
  fz: number;
  heading: number;
  /** Extent to the left and right of the centre, metres. */
  left: number;
  right: number;
  /** Extent above and below the bottom centre, metres. */
  height: number;
  below: number;
  /** Where a respawn at this checkpoint puts you (default: just past the gate). */
  respawn: Spot;
}

export interface Checkpoint {
  index: number;
  /** gates[0] is the main-route gate. */
  gates: CheckpointGate[];
}

export type Crossing = "forward" | "backward" | undefined;

/** How far behind a gate you must go before reversing through it un-passes it, m. */
export const REVERSE_HYSTERESIS = 1;
/** A step longer than this is a teleport, not a drive: never swept, m. */
export const TELEPORT_STEP = 8;

interface V3 {
  x: number;
  y: number;
  z: number;
}

/** Signed distance of a point in front of the gate's plane, m. */
export const planeDist = (g: CheckpointGate, p: V3) => (p.x - g.x) * g.fx + (p.z - g.z) * g.fz;

/** Is a point on the gate plane inside the gate's rectangle? */
function inside(g: CheckpointGate, p: V3) {
  // Right is (-fz, fx) (heading 0 faces +z, right is -x).
  const across = (p.x - g.x) * -g.fz + (p.z - g.z) * g.fx;
  const up = p.y - g.y;
  return across >= -g.left && across <= g.right && up >= -g.below && up <= g.height;
}

/**
 * Did the movement p → q cross this gate? Forward crossings use the gate's plane;
 * backward ones a plane a metre behind it (so wobbling on the line doesn't un-pass it).
 */
export function crossGate(g: CheckpointGate, p: V3, q: V3): Crossing {
  const dp = planeDist(g, p);
  const dq = planeDist(g, q);
  if (dp < 0 && dq >= 0) {
    const t = dp / (dp - dq);
    const at = { x: p.x + (q.x - p.x) * t, y: p.y + (q.y - p.y) * t, z: p.z + (q.z - p.z) * t };
    return inside(g, at) ? "forward" : undefined;
  }
  const bp = dp + REVERSE_HYSTERESIS;
  const bq = dq + REVERSE_HYSTERESIS;
  if (bp >= 0 && bq < 0) {
    const t = bp / (bp - bq);
    const at = { x: p.x + (q.x - p.x) * t, y: p.y + (q.y - p.y) * t, z: p.z + (q.z - p.z) * t };
    // Check the rectangle at the real gate (a metre forward of the hysteresis plane).
    return inside(g, {
      x: at.x + g.fx * REVERSE_HYSTERESIS,
      y: at.y,
      z: at.z + g.fz * REVERSE_HYSTERESIS,
    })
      ? "backward"
      : undefined;
  }
  return undefined;
}

/** One racer's progression. */
export interface Progression {
  /** Laps completed. */
  completedLaps: number;
  /** The checkpoint you must cross next. */
  next: number;
  /** The checkpoint you passed last (where a respawn puts you). */
  last: number;
  /** The gate you actually crossed for `last` (main or alternate). */
  lastGate: CheckpointGate;
  /** Checkpoints validated since the start (goes down if you reverse back through one). */
  passed: number;
  /** The most ever validated: laps are only awarded for new progress. */
  best: number;
  /** The route of the last gate passed ("main", or a shortcut's name). */
  activeRoute: string;
  /** The latest crossing, for the debug overlay. */
  lastEvent?: { kind: "accepted" | "rejected" | "reversed" | "lap"; gate: string; why?: string };
}

export function newProgression(course: Checkpoint[]): Progression {
  const start = course[0]!.gates[0]!;
  return {
    completedLaps: 0,
    next: course.length > 1 ? 1 : 0,
    last: 0,
    lastGate: start,
    passed: 0,
    best: 0,
    activeRoute: "main",
  };
}

export interface StepResult {
  /** A checkpoint was validated this step. */
  passed?: CheckpointGate;
  /** A lap was completed this step (the count of laps now completed). */
  lap?: number;
  /** A checkpoint was taken back by reversing through it. */
  reversed?: CheckpointGate;
}

/** Advance a racer's progression for a movement from p to q (both after any teleport). */
export function stepProgression(course: Checkpoint[], r: Progression, p: V3, q: V3): StepResult {
  const out: StepResult = {};
  const n = course.length;
  if ((q.x - p.x) ** 2 + (q.y - p.y) ** 2 + (q.z - p.z) ** 2 > TELEPORT_STEP ** 2) return out;
  // Reversing back through the checkpoint you passed last.
  const back = course[r.last]!;
  for (const g of back.gates) {
    if (crossGate(g, p, q) === "backward") {
      r.passed--;
      r.next = r.last;
      r.last = (r.last - 1 + n) % n;
      r.lastGate = course[r.last]!.gates[0]!;
      r.activeRoute = "main";
      r.lastEvent = { kind: "reversed", gate: g.id, why: "drove back through it" };
      out.reversed = g;
      return out;
    }
  }
  // The next checkpoint, through any of its gates.
  for (const g of course[r.next]!.gates) {
    if (crossGate(g, p, q) === "forward") {
      r.passed++;
      r.last = r.next;
      r.lastGate = g;
      r.next = (r.next + 1) % n;
      r.activeRoute = g.route;
      out.passed = g;
      r.lastEvent = { kind: "accepted", gate: g.id };
      if (r.passed > r.best) {
        r.best = r.passed;
        if (r.last === 0 && r.passed % n === 0) {
          r.completedLaps = r.passed / n;
          out.lap = r.completedLaps;
          r.lastEvent = { kind: "lap", gate: g.id };
        }
      }
      return out;
    }
  }
  // Anything else crossed forward is out of order: note why it didn't count.
  for (const c of course) {
    if (c.index === r.next || c.index === r.last) continue;
    for (const g of c.gates)
      if (crossGate(g, p, q) === "forward") {
        const need = course[r.next]!.gates[0]!.id;
        r.lastEvent = { kind: "rejected", gate: g.id, why: `out of order: ${need} first` };
      }
  }
  return out;
}

/** A stretch's road between two checkpoints' main gates: the route's samples in order
 * (each a plane across the road, like a gate's), with metres from the first gate. */
interface Chain {
  x: number[];
  z: number[];
  fx: number[];
  fz: number[];
  d: number[];
  length: number;
}
const chains = new WeakMap<CheckpointGate, Chain>();

/**
 * Lay the route between each checkpoint's main gate and the next one's (`samples`: the
 * lap's route, in order, with dist), so segmentProgress can follow the road's bends.
 * On a long curved stretch the next gate's plane alone cuts back across the road
 * before it (a hairpin's far side is "past" it): a kart there counted as nearly at
 * the next gate, ahead of a rival really metres in front.
 */
export function layChains(course: Checkpoint[], samples: RouteSample[], lapLength: number) {
  const n = samples.length;
  if (n < 3 || course.length < 2) return;
  const nearest = (g: CheckpointGate) => {
    let best = 0;
    let bestD = Infinity;
    samples.forEach((p, i) => {
      const d = (p.x - g.x) ** 2 + (p.z - g.z) ** 2 + 4 * (p.y - g.y) ** 2;
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    });
    return best;
  };
  const at = course.map((c) => nearest(c.gates[0]!));
  course.forEach((c, k) => {
    const a = c.gates[0]!;
    const b = course[(k + 1) % course.length]!.gates[0]!;
    const ia = at[k]!;
    const ib = at[(k + 1) % course.length]!;
    const steps = (ib - ia + n) % n;
    // (Gates out of the route's order, or too close together: keep the plane fraction.)
    if (steps < 2 || steps > n / 2) return;
    const ch: Chain = { x: [a.x], z: [a.z], fx: [a.fx], fz: [a.fz], d: [0], length: 0 };
    let d = 0;
    let px = a.x;
    let pz = a.z;
    for (let j = 1; j <= steps; j++) {
      const p = samples[(ia + j) % n]!;
      const last = j === steps;
      const q = last ? { x: b.x, z: b.z, fx: b.fx, fz: b.fz } : p;
      const fl = Math.hypot(q.fx, q.fz) || 1;
      d += Math.hypot(q.x - px, q.z - pz);
      ch.x.push(q.x);
      ch.z.push(q.z);
      ch.fx.push(q.fx / fl);
      ch.fz.push(q.fz / fl);
      ch.d.push(d);
      px = q.x;
      pz = q.z;
    }
    ch.length = d;
    if (d > 0.5 && d < lapLength) chains.set(a, ch);
  });
}

/**
 * How far a racer is between their last gate and the next, 0..1. Along the road where
 * the stretch is laid (layChains): between which two of the road's planes the kart is
 * (the nearest such piece of road on a hairpin, where the far side is between two
 * planes as well), so a bend's far side never counts as past it or behind the start. Elsewhere (shortcuts, courses without a route): their distance in front of
 * the last gate's plane over the distance between the two planes. Negative (down to
 * -1) while behind the last gate (on the grid, or reversing).
 */
export function segmentProgress(course: Checkpoint[], r: Progression, at: V3): number {
  const a = r.lastGate;
  const b =
    course[r.next]!.gates.find((g) => g.route === r.activeRoute) ?? course[r.next]!.gates[0]!;
  const da = planeDist(a, at);
  const ch = b === course[r.next]!.gates[0] ? chains.get(a) : undefined;
  if (ch) {
    // Every piece of the stretch the kart is between the two planes of (in front of
    // the first, behind the second); on a hairpin there can be two, so the one whose
    // road is closest wins.
    let best = -1;
    let bestD = Infinity;
    let prev = da;
    for (let j = 1; j < ch.d.length; j++) {
      const dj = (at.x - ch.x[j]!) * ch.fx[j]! + (at.z - ch.z[j]!) * ch.fz[j]!;
      if (prev >= 0 && dj < 0) {
        const f = prev / Math.max(1e-6, prev - dj);
        const mx = ch.x[j - 1]! + (ch.x[j]! - ch.x[j - 1]!) * f;
        const mz = ch.z[j - 1]! + (ch.z[j]! - ch.z[j - 1]!) * f;
        const off = (at.x - mx) ** 2 + (at.z - mz) ** 2;
        if (off < bestD) {
          bestD = off;
          best = ch.d[j - 1]! + (ch.d[j]! - ch.d[j - 1]!) * f;
        }
      }
      prev = dj;
    }
    if (best >= 0) return Math.min(0.999, best / ch.length);
    if (da < 0) return Math.max(-0.999, da / 100);
    return 0.999;
  }
  if (da < 0) return Math.max(-0.999, da / 100);
  const db = planeDist(b, at);
  if (db >= 0) return 0.999;
  return Math.min(0.999, da / (da - db));
}

/** A racer's place-ranking value: validated checkpoints plus the fraction of the next. */
export const rankValue = (course: Checkpoint[], r: Progression, at: V3) =>
  r.passed + segmentProgress(course, r, at);

// ---------------------------------------------------------------- making checkpoints

export interface RouteSample {
  x: number;
  y: number;
  z: number;
  /** Unit forward (any length; it's normalised horizontally). */
  fx: number;
  fz: number;
  width: number;
  dist: number;
}

export interface GateOptions {
  /** Extra width either side of the road, m (capped where other road is near). */
  margin: number;
  /** Height above the road, and depth below it, m. */
  height: number;
  below: number;
  /** Fewest and most metres between checkpoints. */
  minGap: number;
  maxGap: number;
}

export const DEFAULT_GATES: GateOptions = {
  margin: 18,
  height: 8,
  below: 3,
  minGap: 45,
  maxGap: 130,
};

/** Signed curvature (1/m, + = turning left) at each sample, smoothed over ~±12 m. */
function curvature(s: RouteSample[]): number[] {
  const n = s.length;
  const head = s.map((p) => Math.atan2(p.fx, p.fz));
  const raw = s.map((_, i) => {
    let d = head[(i + 1) % n]! - head[(i - 1 + n) % n]!;
    d = ((((d + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;
    const a = s[(i - 1 + n) % n]!;
    const b = s[(i + 1) % n]!;
    return d / (Math.hypot(b.x - a.x, b.z - a.z) || 1);
  });
  const step = s.length > 1 ? Math.max(0.5, s[1]!.dist - s[0]!.dist) : 1;
  const w = Math.max(1, Math.round(12 / step));
  return raw.map((_, i) => {
    let sum = 0;
    for (let k = -w; k <= w; k++) sum += raw[(i + k + n) % n]!;
    return sum / (2 * w + 1);
  });
}

/**
 * Distances along the lap for checkpoints: the start line, the exit of every real turn,
 * and enough in between that no stretch is longer than maxGap. `avoid` lists stretches
 * (jump gaps) where no checkpoint may go.
 */
export function placeCheckpoints(
  s: RouteSample[],
  length: number,
  o: GateOptions = DEFAULT_GATES,
  avoid: [number, number][] = [],
): number[] {
  const k = curvature(s);
  const blocked = (d: number) => avoid.some(([a, b]) => d >= a - 8 && d <= b + 8);
  const exits: number[] = [];
  let inTurn = false;
  let turned = 0;
  for (let i = 0; i < s.length; i++) {
    const ak = Math.abs(k[i]!);
    if (ak > 1 / 70) {
      inTurn = true;
      turned += ak * (i ? s[i]!.dist - s[i - 1]!.dist : 0);
    } else if (inTurn && ak < 1 / 160) {
      // Out of a turn of at least ~35 degrees: a checkpoint just after its exit.
      if (turned > 0.6) exits.push(s[i]!.dist + 8);
      inTurn = false;
      turned = 0;
    }
  }
  const picks: number[] = [0];
  for (const d of exits.sort((a, b) => a - b)) {
    if (d >= length - o.minGap || blocked(d)) continue;
    if (d - picks.at(-1)! >= o.minGap) picks.push(d);
  }
  // Fill long stretches evenly.
  const out: number[] = [];
  const all = [...picks, length];
  for (let i = 0; i < all.length - 1; i++) {
    const a = all[i]!;
    const b = all[i + 1]!;
    out.push(a);
    const extra = Math.floor((b - a) / o.maxGap);
    for (let e = 1; e <= extra; e++) {
      let d = a + ((b - a) * e) / (extra + 1);
      // Nudge out of a blocked stretch, forward if there's room.
      for (const [x, y] of avoid)
        if (d >= x - 8 && d <= y + 8) d = y + 20 < b - 10 ? y + 20 : x - 20;
      out.push(d);
    }
  }
  return out;
}

/** The route sample at distance d (nearest). */
function sampleAt(s: RouteSample[], length: number, d: number) {
  const dd = ((d % length) + length) % length;
  let lo = 0;
  let hi = s.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (s[mid]!.dist <= dd) lo = mid;
    else hi = mid - 1;
  }
  return s[lo]!;
}

/**
 * A gate across the route at distance d: the road's width plus the margin each side,
 * but never reaching more than halfway to another part of the course at about the
 * same height (so it can't be crossed from the wrong road).
 */
export function gateAt(
  s: RouteSample[],
  length: number,
  d: number,
  index: number,
  o: GateOptions = DEFAULT_GATES,
  id = `cp${String(index).padStart(2, "0")}`,
  route = "main",
): CheckpointGate {
  const p = sampleAt(s, length, d);
  const h = Math.hypot(p.fx, p.fz) || 1;
  const fx = p.fx / h;
  const fz = p.fz / h;
  const half = p.width / 2;
  let left = half + o.margin;
  let right = half + o.margin;
  for (const q of s) {
    const along = Math.abs(q.dist - p.dist);
    if (Math.min(along, length - along) < 60) continue; // this same bit of road
    if (Math.abs(q.y - p.y) > o.height + o.below) continue; // another level
    const ahead = (q.x - p.x) * fx + (q.z - p.z) * fz;
    if (Math.abs(ahead) > q.width / 2 + 6) continue; // not near the gate's line
    const across = (q.x - p.x) * -fz + (q.z - p.z) * fx;
    const room = Math.max(half + 2, (Math.abs(across) - q.width / 2) * 0.5 + half * 0.5);
    if (across < 0) left = Math.min(left, room);
    else right = Math.min(right, room);
  }
  const ahead = sampleAt(s, length, d + 4);
  return {
    id,
    index,
    route,
    x: p.x,
    y: p.y,
    z: p.z,
    fx,
    fz,
    heading: Math.atan2(fx, fz),
    left,
    right,
    height: o.height,
    below: o.below,
    respawn: { x: ahead.x, y: ahead.y, z: ahead.z, heading: Math.atan2(fx, fz) },
  };
}

/** A whole course's checkpoints from its route. */
export function checkpointsFromRoute(
  s: RouteSample[],
  length: number,
  o: GateOptions = DEFAULT_GATES,
  avoid: [number, number][] = [],
): Checkpoint[] {
  return placeCheckpoints(s, length, o, avoid).map((d, i) => ({
    index: i,
    gates: [gateAt(s, length, d, i, o)],
  }));
}

/** Group a flat list of gates into checkpoints by index (main-route gate first). */
export function groupGates(gates: CheckpointGate[]): Checkpoint[] {
  const by = new Map<number, CheckpointGate[]>();
  for (const g of gates) by.set(g.index, [...(by.get(g.index) ?? []), g]);
  return [...by.keys()]
    .sort((a, b) => a - b)
    .map((index) => ({
      index,
      gates: by.get(index)!.sort((a, b) => (a.route === "main" ? -1 : b.route === "main" ? 1 : 0)),
    }));
}
