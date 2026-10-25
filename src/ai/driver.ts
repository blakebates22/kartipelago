/**
 * An AI driver. Each step it looks at its kart, the racing line and (when it's given
 * one) the race around it, and produces an InputState (throttle, brake, steer, drift,
 * item), exactly what a player's controller would. The kart model treats it the same
 * as the player's input: there's no faked cornering, no extra grip and no teleporting.
 *
 * Two layers:
 * - The plan (a few times a second, delayed by the rival's reaction time): where on the
 *   road to be. Its own line (the racing line, moved a little by its line bias), or off
 *   it to pass a racer ahead, defend from one behind, keep clear of a trap, or take a
 *   zipper pad. Mistakes come in here too, now and then: a wide line, a lift, a missed
 *   drift.
 * - The controls (every step): steer for a point ahead on that path (pure pursuit, the
 *   lookahead growing with speed), drift the corners whose shape rewards a drift,
 *   lift or brake when the speed is too much for what's coming, tap the throttle on the
 *   straights, let it go over zippers to enhance them and press again in the rainbow,
 *   and get unstuck (reverse out, turn round) when something's gone wrong.
 *
 * How well it does each of those is its skill (src/ai/skill.ts). Items are chosen in
 * src/ai/items.ts and fired by the session.
 */
import type { InputState } from "../core/input";
import { driftCurvature, driftSteerFor, type KartConfig, type KartState } from "../vehicles/kart";
import { ZIP } from "../vehicles/zipper";
import type { RacingLine } from "./racingLine";
import { TIERS, type AiSkill } from "./skill";

export interface AiConfig {
  /** Rivals' top speed relative to their character's (a whole-field trim). */
  speedMult: number;
  /** 1 = rivals drift, 0 = they never do. */
  drift: number;
  /** Steering aim point: this far ahead, plus more at speed. Metres, seconds. */
  lookAhead: number;
  lookAheadPerSpeed: number;
  /** Start a drift when a corner ahead is tighter than this radius, metres. */
  driftEnterRadius: number;
  /** End a drift when the line ahead is straighter than this radius, metres. */
  driftExitRadius: number;
  /** How far ahead to look for corners to drift, metres. */
  driftScan: number;
  /**
   * The start (race.ts): each rival first presses the throttle this many reference
   * frames before GO, give or take up to startSpreadFrames (fixed per rival, so starts
   * repeat). Around 1-14 frames is a strong start, 15-29 weak, 0 an ordinary one: a
   * skill knob, not a guaranteed boost.
   */
  startAimFrames: number;
  startSpreadFrames: number;
  /** How often the plan is redone, seconds. */
  planEvery?: number;
}

/** What a rival can see of the race round it (all optional: on its own it just drives). */
export interface AiWorld {
  /** The other racers (not this one). */
  others: {
    x: number;
    y: number;
    z: number;
    speed: number;
    heading: number;
    /** Shielded (best not rammed). */
    shield?: boolean;
  }[];
  /** Zipper pads and boost strips: centres on the road (y: its height, for telling a
   * pad on a road above or below apart). */
  pads?: { x: number; y?: number; z: number }[];
  /** Traps on the road (oil, mines, bubbles). */
  traps?: { x: number; z: number }[];
}

export type AiState =
  "grid" | "racing" | "overtake" | "follow" | "defend" | "dodge" | "pad" | "recover" | "turnaround";

export interface Driver {
  line: RacingLine;
  /** Nearest line point last step. */
  index: number;
  /** Drift button held last step (a drift needs a fresh press). */
  driftHeld: boolean;
  /** Reference frames before GO that this driver first presses the throttle. */
  startLead: number;
  /** The last drift's direction and when it ended (race clock): a drift the other way
   * straight after (an S-bend) would be flung wide by the new slide building, so the
   * second half is steered. */
  lastDrift: { dir: number; at: number };
  skill: AiSkill;
  seed: number;
  /** Where it's driving, metres off the line (+ = to the line's right), and where the
   * plan wants it. */
  offset: number;
  wantOffset: number;
  state: AiState;
  /** Seconds to the next plan; the plan's choice waits out the reaction time. */
  planIn: number;
  pending: { offset: number; state: AiState; at: number } | null;
  /** Seconds it's been stuck (barely moving with the throttle down), and the reverse
   * manoeuvre left. */
  stuck: number;
  /** Progress watch: where along the line it was, and how long ago (no progress in a
   * few seconds, even while moving, is stuck too: grinding along a wall, say). */
  watch: { t: number; index: number };
  /** The long watch: hardly any progress in many seconds (lost off the road behind a
   * wall, say, where backing out doesn't help) and it asks to be put back on the road. */
  lost: { t: number; index: number };
  /** Set when lost: the race puts it back at its last checkpoint and clears this. */
  wantsRespawn: boolean;
  reversing: number;
  reverseSteer: number;
  /** A mistake under way: what, and for how long. */
  mistake: { kind: "wide" | "lift" | "nodrift" | "early" | null; left: number; dir: number };
  /** The corner (line index) it has decided about drifting, and the decision. */
  corner: { at: number; drift: boolean };
  /** Throttle tapping: on/off timer, and whether it's tapping this straight. */
  tap: { on: boolean; t: number; straight: number; active: boolean };
  /** This boost is being done properly (lift at the pad, press in the rainbow). */
  boostTechnique: boolean;
  /** Time on the race clock (for the plan's reaction delay). */
  clock: number;
  /** The item planner's state (src/ai/items.ts). */
  itemThink: number;
  itemHeld: number;
  /** What it was doing last step, for the debug view. */
  debug: { tx: number; tz: number; note: string };
}

/** Small deterministic pseudo-random number in [-1, 1) from a seed. */
export function noise(seed: number) {
  const v = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return (v - Math.floor(v)) * 2 - 1;
}
/** ...and in [0, 1). */
const chance = (seed: number) => (noise(seed) + 1) / 2;

/** The skill tests and single-kart laps use when none is given: a clean, flat-out
 * driver with the old rivals' habits (it drifts everything, never taps or enhances). */
export const STEADY: AiSkill = {
  ...TIERS.strong,
  precision: 1,
  drift: 1,
  tapping: 0,
  boosting: 0,
  mistakes: 0,
  aggression: 0.5,
  lineBias: 0,
  start: 0.5,
  pace: 1,
  vision: 1,
};

export function createDriver(
  line: RacingLine,
  seed: number,
  cfg: AiConfig,
  skill: AiSkill = STEADY,
): Driver {
  // Start timing: better starters land in the strong window more often.
  const spread = cfg.startSpreadFrames * (1.3 - skill.start);
  return {
    line,
    index: 0,
    driftHeld: false,
    startLead: cfg.startAimFrames + noise(seed) * spread,
    lastDrift: { dir: 0, at: -Infinity },
    skill,
    seed,
    offset: skill.lineBias * 1.5,
    wantOffset: skill.lineBias * 1.5,
    state: "grid",
    planIn: chance(seed * 3.1) * 0.2,
    pending: null,
    stuck: 0,
    watch: { t: 0, index: 0 },
    lost: { t: 0, index: 0 },
    wantsRespawn: false,
    reversing: 0,
    reverseSteer: 0,
    mistake: { kind: null, left: 0, dir: 0 },
    corner: { at: -1, drift: true },
    tap: { on: true, t: 0, straight: 0, active: false },
    boostTechnique: false,
    clock: 0,
    itemThink: chance(seed * 7.7) * 0.5,
    itemHeld: 0,
    debug: { tx: 0, tz: 0, note: "" },
  };
}

/** Lost: under this many metres of progress along the line in this many seconds. */
const LOST_SEC = 8;
const LOST_METRES = 25;

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const mod = (i: number, n: number) => ((i % n) + n) % n;

/** The nearest line point (searching near the last one first, at about the kart's height). */
export function nearestIndex(d: Driver, x: number, y: number, z: number): number {
  const { line } = d;
  const dist = (i: number) => {
    const j = mod(i, line.n);
    // Height counts too (three times over), so a road right over another isn't mixed up.
    return (line.x[j]! - x) ** 2 + (line.z[j]! - z) ** 2 + ((line.y[j]! - y) * 3) ** 2;
  };
  // A kart moves a few line points a step at most, so a jump further along (or back) is
  // only taken if it's much nearer: where two parts of the road lie side by side (a
  // hairpin's legs, an S), a kart knocked toward the other part keeps its place on its
  // own, instead of suddenly finding itself "backwards" and turning round.
  const jump = (k: number) => (Math.max(0, Math.abs(k) - 4) * line.spacing * 0.8) ** 2;
  let best = d.index;
  let bestD = dist(best);
  let bestCost = bestD;
  for (let k = -30; k <= 30; k++) {
    const v = dist(d.index + k);
    if (v + jump(k) < bestCost) {
      bestCost = v + jump(k);
      bestD = v;
      best = d.index + k;
    }
  }
  if (bestD > 40 * 40) {
    for (let i = 0; i < line.n; i++) {
      const v = dist(i);
      if (v < bestD) {
        bestD = v;
        best = i;
      }
    }
  }
  d.index = mod(best, line.n);
  return d.index;
}

/** The corner ahead with the largest curvature (signed), between two distances ahead. */
function sharpestAhead(line: RacingLine, from: number, near: number, far: number) {
  let best = 0;
  let at = from;
  const a = Math.round(near / line.spacing);
  const b = Math.round(far / line.spacing);
  for (let k = a; k <= b; k++) {
    const j = (from + k) % line.n;
    const c = line.curvature[j]!;
    if (Math.abs(c) > Math.abs(best)) {
      best = c;
      at = j;
    }
  }
  return { curv: best, at };
}

/** Where a point is relative to the line near index i: metres along (+ = ahead) and across. */
export function lineFrame(line: RacingLine, i: number, x: number, z: number) {
  const dx = x - line.x[i]!;
  const dz = z - line.z[i]!;
  const h = line.heading[i]!;
  return {
    along: dx * Math.sin(h) + dz * Math.cos(h),
    across: dx * line.rx[i]! + dz * line.rz[i]!,
  };
}

export interface RaceMoment {
  /** True while the race is still counting down. */
  countdown: boolean;
  /** Race clock; negative before GO. */
  clock: number;
  /** The frame rate the start windows are counted in (race.ts: startRefHz). */
  startRefHz: number;
}

/** Lateral room on the road at a line point, for an offset. */
function room(line: RacingLine, j: number, off: number) {
  return clamp(off, line.roomLeft[j]!, line.roomRight[j]!);
}

/**
 * The plan: where on the road to be, from the racers, traps and pads round it.
 * Returns the offset from the line wanted, and what it's doing.
 */
function plan(
  d: Driver,
  kart: KartState,
  i: number,
  world: AiWorld | undefined,
): { offset: number; state: AiState } {
  const { line, skill } = d;
  const base = skill.lineBias * 1.5;
  if (!world) return { offset: base, state: "racing" };
  const n = line.n;
  const ahead = Math.round(30 / line.spacing);
  // Racers near: along the line (+ ahead) and across it.
  let block: { along: number; across: number; speed: number } | null = null;
  let behind: { along: number; across: number; speed: number } | null = null;
  for (const o of world.others) {
    if (Math.abs(o.y - kart.y) > 4) continue;
    const f = lineFrame(line, i, o.x, o.z);
    if (
      f.along > 0.5 &&
      f.along < 8 + 18 * skill.aggression &&
      Math.abs(f.across - d.offset) < 3.2
    ) {
      if (!block || f.along < block.along) block = { ...f, speed: o.speed };
    } else if (f.along < -0.5 && f.along > -12 && Math.abs(f.across - d.offset) < 6) {
      if (!behind || f.along > behind.along) behind = { ...f, speed: o.speed };
    }
  }
  // Traps ahead on our path: steer round them.
  for (const t of world.traps ?? []) {
    const f = lineFrame(line, i, t.x, t.z);
    if (f.along > 2 && f.along < 28 && Math.abs(f.across - d.offset) < 2.6) {
      const j = mod(i + Math.round(f.along / line.spacing), n);
      const left = f.across - line.roomLeft[j]!;
      const right = line.roomRight[j]! - f.across;
      return { offset: room(line, j, f.across + (right > left ? 3.4 : -3.4)), state: "dodge" };
    }
  }
  // A racer ahead in the way: pull out to pass on the side with more room (a keener
  // racer pulls out earlier and closer), or tuck in behind on a different line.
  if (block && kart.speed + 0.5 >= block.speed) {
    const j = mod(i + Math.round(block.along / line.spacing), n);
    const left = block.across - line.roomLeft[j]!;
    const right = line.roomRight[j]! - block.across;
    const gap = 3.3;
    if (Math.max(left, right) > gap + 0.5) {
      const side = right >= left ? 1 : -1;
      return { offset: room(line, j, block.across + side * gap), state: "overtake" };
    }
    return {
      offset: room(line, j, block.across + (block.across > 0 ? -1.6 : 1.6)),
      state: "follow",
    };
  }
  // Defending: a racer close behind, coming up to pass: now and then, cover the line
  // it's taking (gently; no weaving).
  if (
    behind &&
    behind.speed > kart.speed - 0.5 &&
    chance(d.seed * 13 + Math.floor(d.clock / 3)) < skill.aggression * 0.6
  ) {
    const j = mod(i + 2, n);
    const toward = clamp(behind.across - d.offset, -2, 2);
    return { offset: room(line, j, d.offset + toward), state: "defend" };
  }
  // A zipper pad ahead: line up with it (a booster goes for every one).
  if (world.pads && chance(d.seed * 5 + Math.floor(d.clock / 6)) < 0.25 + 0.75 * skill.boosting) {
    for (const p of world.pads) {
      if (p.y !== undefined && Math.abs(p.y - kart.y) > 3) continue;
      const f = lineFrame(line, i, p.x, p.z);
      if (f.along > 4 && f.along < 45 && Math.abs(f.across) < 9) {
        const j = mod(i + Math.round(f.along / line.spacing), n);
        // Only a pad on this road (one beside it across a wall isn't).
        if (f.across < line.roomLeft[j]! - 1 || f.across > line.roomRight[j]! + 1) continue;
        return { offset: room(line, j, f.across), state: "pad" };
      }
    }
  }
  // Clear road: its own line (and in a corner, a cleaner racer hugs the inside a touch).
  void ahead;
  return { offset: base, state: "racing" };
}

/** Mistakes: now and then (skill.mistakes a minute), one goes wrong for a moment. */
function maybeMistake(d: Driver, dt: number, line: RacingLine, i: number) {
  if (d.mistake.left > 0) {
    d.mistake.left -= dt;
    if (d.mistake.left <= 0) d.mistake.kind = null;
    return;
  }
  const rate = d.skill.mistakes / 60;
  if (rate <= 0) return;
  // A fixed-per-driver pseudo-random draw each tenth of a second.
  const tick = Math.floor(d.clock * 10);
  if (chance(d.seed * 31.7 + tick * 1.37) > rate / 10) return;
  const r = chance(d.seed * 17 + tick * 0.73);
  const c = line.curvature[mod(i + Math.round(15 / line.spacing), line.n)]!;
  if (r < 0.35) d.mistake = { kind: "wide", left: 1.1, dir: c > 0 ? 1 : -1 };
  else if (r < 0.55) d.mistake = { kind: "lift", left: 0.35, dir: 0 };
  else if (r < 0.8) d.mistake = { kind: "nodrift", left: 2.5, dir: 0 };
  else d.mistake = { kind: "early", left: 1.5, dir: 0 };
}

export function driveAi(
  d: Driver,
  kart: KartState,
  kartCfg: KartConfig,
  cfg: AiConfig,
  moment: RaceMoment,
  /** Steer for this point instead of the racing line, without drifting (lining up a
   * loop-the-loop's entry: src/game/loops.ts). */
  aim?: { x: number; z: number },
  world?: AiWorld,
  dt = 1 / 120,
): InputState {
  const input: InputState = { throttle: 0, brake: 0, steer: 0, drift: false, item: false };
  const { skill } = d;
  d.clock = moment.clock;
  if (moment.countdown) {
    // Pressed once, then held through GO (a press at or after GO is an ordinary start).
    d.state = "grid";
    input.throttle = moment.clock >= -d.startLead / moment.startRefHz ? 1 : 0;
    return input;
  }
  input.throttle = 1;
  const { line } = d;
  const i = nearestIndex(d, kart.x, kart.y, kart.z);
  const speed = Math.max(1, Math.abs(kart.speed));

  // ---- Getting unstuck: barely moving with the throttle down, or facing backwards.
  if (d.reversing > 0) {
    d.reversing -= dt;
    d.state = "recover";
    input.throttle = 0;
    input.brake = 1;
    input.steer = d.reverseSteer;
    d.driftHeld = false;
    return input;
  }
  const backwards = Math.abs(wrap(kart.heading - line.heading[i]!)) > 2.0;
  if (Math.abs(kart.speed) < 1.5 && moment.clock > 1.5 && kart.grounded) d.stuck += dt;
  else d.stuck = Math.max(0, d.stuck - dt * 2);
  d.watch.t += dt;
  if (d.watch.t > 2.5) {
    let moved = (i - d.watch.index) * line.spacing;
    if (moved < -line.n * line.spacing * 0.5) moved += line.n * line.spacing;
    if (moved < 6 && moment.clock > 3 && !aim) d.stuck = 2;
    d.watch = { t: 0, index: i };
  }
  d.lost.t += dt;
  if (aim || moment.clock < 3) d.lost = { t: 0, index: i };
  else if (d.lost.t > LOST_SEC) {
    let moved = (i - d.lost.index) * line.spacing;
    if (moved < -line.n * line.spacing * 0.5) moved += line.n * line.spacing;
    if (moved < LOST_METRES) d.wantsRespawn = true;
    d.lost = { t: 0, index: i };
  }
  if (d.stuck > 1.0) {
    d.stuck = 0;
    d.reversing = 0.9;
    // Back out turning the nose toward the road ahead.
    const want = wrap(
      Math.atan2(line.x[(i + 8) % line.n]! - kart.x, line.z[(i + 8) % line.n]! - kart.z) -
        kart.heading,
    );
    d.reverseSteer = want > 0 ? 1 : -1;
    d.state = "recover";
    input.throttle = 0;
    input.brake = 1;
    input.steer = d.reverseSteer;
    return input;
  }

  // ---- The plan (a few times a second), arriving after the rival's reaction time.
  d.planIn -= dt;
  if (d.planIn <= 0 && !aim) {
    d.planIn = cfg.planEvery ?? 0.2;
    const p = plan(d, kart, i, world);
    // (A newer plan replaces a waiting one but doesn't restart its wait.)
    if (d.pending) d.pending = { ...p, at: d.pending.at };
    else if (p.state !== d.state || Math.abs(p.offset - d.wantOffset) > 0.5)
      d.pending = {
        ...p,
        at: moment.clock + skill.reaction * (0.6 + 0.8 * chance(d.seed + moment.clock)),
      };
  }
  if (d.pending && moment.clock >= d.pending.at) {
    d.wantOffset = d.pending.offset;
    d.state = d.pending.state;
    d.pending = null;
  }
  maybeMistake(d, dt, line, i);
  let want = d.wantOffset;
  if (d.mistake.kind === "wide") want += -d.mistake.dir * 3;
  // Ease across the road (quicker when dodging or passing), staying on it.
  const rate = d.state === "dodge" ? 7 : d.state === "overtake" ? 4.5 : 2.5;
  d.offset += clamp(want - d.offset, -rate * dt, rate * dt);

  // ---- Steering: pure pursuit for a point ahead on the path.
  // Off the road (thrown wide, knocked off): head back to it by the shortest way, for a
  // point just ahead on the line, instead of one far up the road beyond the obstacle.
  const here = lineFrame(line, i, kart.x, kart.z);
  const offRoad = here.across > line.roomRight[i]! + 4 || here.across < line.roomLeft[i]! - 4;
  // (On a narrow road it looks less far ahead: a far point cuts the corners into the walls.)
  const narrowLook = Math.min(1, Math.max(0.55, (line.width[i]! - 4) / 12));
  const look = offRoad
    ? 6
    : (cfg.lookAhead + cfg.lookAheadPerSpeed * speed) * skill.vision * narrowLook;
  const j = (i + Math.round(look / line.spacing)) % line.n;
  const off = offRoad ? 0 : room(line, j, d.offset);
  const tx = aim ? aim.x : line.x[j]! + line.rx[j]! * off;
  const tz = aim ? aim.z : line.z[j]! + line.rz[j]! * off;
  d.debug.tx = tx;
  d.debug.tz = tz;
  let toward = wrap(Math.atan2(tx - kart.x, tz - kart.z) - kart.velAngle);
  if (backwards && !aim) {
    // Facing the wrong way: turn round (the plain pursuit would too, but decisively).
    d.state = "turnaround";
    toward = clamp(toward * 3, -Math.PI / 2, Math.PI / 2);
  }
  // A less precise driver wanders a little about its aim (a slow, smooth wobble).
  const wobble =
    (1 - skill.precision) *
    0.22 *
    (Math.sin(moment.clock * 0.9 + d.seed) + 0.6 * Math.sin(moment.clock * 2.3 + d.seed * 1.7));
  toward += wobble;
  const dist = aim ? Math.max(4, Math.hypot(tx - kart.x, tz - kart.z)) : look;
  const wantRate = (2 * speed * Math.sin(toward)) / dist; // heading change per second (+ = left)

  // ---- Speed: lift (or brake) when it's carrying more speed than the road ahead
  // allows without scrubbing (mostly when boosted), and the throttle technique.
  const corner = sharpestAhead(line, i, 4, cfg.driftScan);
  const brakeLook = sharpestAhead(line, i, 2, 10 + speed * 1.2);
  const vmax =
    brakeLook.curv === 0
      ? Infinity
      : Math.sqrt((kartCfg.turnScrubFree * 1.05) / Math.abs(brakeLook.curv));
  let throttle = 1;
  let brake = 0;
  // (Only above normal top speed: at it, a kart turns tighter than any road here.)
  const boosted = kart.speed > kartCfg.topSpeed * 1.05;
  if (boosted && kart.speed > vmax + 2 && kart.driftDir === 0 && kart.grounded) throttle = 0;
  if (boosted && kart.speed > vmax + 5 && kart.driftDir === 0 && kart.grounded) brake = 1;
  // A narrow road (a passage, a gap between walls) is no place to drift: there it slows
  // for a kink it can't steer round at speed instead.
  const narrow = line.width[brakeLook.at]! < 13;
  if (narrow && kart.speed > vmax + 2 && kart.driftDir === 0 && kart.grounded) throttle = 0;
  if (narrow && kart.speed > vmax + 5 && kart.driftDir === 0 && kart.grounded) brake = 1;
  if (d.mistake.kind === "lift") throttle = 0;
  // Knocked off its line (a spin, a wall, a respawn's turn): pointing well away from where
  // it's steering for at speed, it lifts, and brakes if it's far off, to turn in time
  // (else a narrow road takes it straight off the edge before it comes round).
  const lineErr = Math.abs(wrap(kart.heading - line.heading[j]!));
  if (!aim && kart.grounded && kart.driftDir === 0 && (lineErr > 0.8 || offRoad)) {
    if (Math.abs(toward) > 0.6 && speed > 9) throttle = 0;
    if (Math.abs(toward) > 1.0 && speed > 12) brake = 1;
  }

  // Zippers and blue boosts: lift at the pad to enhance it, stay off the throttle while
  // it pushes, press again in the rainbow window.
  if (kart.zipPhase === ZIP.ACTIVE && kart.zipEnhanced && d.boostTechnique) throttle = 0;
  else if (kart.zipPhase === ZIP.ENDING) throttle = 1;
  if (world?.pads && kart.zipPhase !== ZIP.ACTIVE) {
    for (const p of world.pads) {
      if (p.y !== undefined && Math.abs(p.y - kart.y) > 3) continue;
      const f = lineFrame(line, i, p.x, p.z);
      if (f.along > -1 && f.along < speed * 0.12 + 1.5 && Math.abs(f.across - d.offset) < 4) {
        d.boostTechnique = chance(d.seed * 3 + Math.floor(p.x * 7 + p.z)) < skill.boosting;
        if (d.boostTechnique) throttle = 0;
      }
    }
  }

  // Throttle tapping (it builds the tap charge, which raises top speed and stacks with a
  // drift's): a tapper keeps it going whenever it's at speed on the ground, drifting or
  // not; how much of the time is its tapping skill (a few seconds at a go).
  const tapWindow = Math.floor(moment.clock / 3);
  const tapping = chance(d.seed * 11 + tapWindow * 1.31) < skill.tapping;
  if (
    tapping &&
    kart.zipPhase === ZIP.NORMAL &&
    kart.grounded &&
    throttle > 0 &&
    kart.speed > kartCfg.topSpeed * 0.7
  ) {
    d.tap.active = true;
    d.tap.t += dt;
    // Held ~0.17 s, lifted ~0.08 s: inside the tap rhythm (a little looser the less
    // practised the tapper).
    const holdFor = 0.17 + (1 - skill.tapping) * 0.05;
    const liftFor = 0.08;
    if (d.tap.on && d.tap.t > holdFor) {
      d.tap.on = false;
      d.tap.t = 0;
    } else if (!d.tap.on && d.tap.t > liftFor) {
      d.tap.on = true;
      d.tap.t = 0;
    }
    if (!d.tap.on) throttle = 0;
  } else {
    d.tap.active = false;
    d.tap.on = true;
    d.tap.t = 0;
  }
  input.throttle = throttle;
  input.brake = brake;

  if (backwards && !aim) {
    // Turning round: brake while there's speed (braking steers twice as hard), so it
    // pivots on the spot instead of looping wide into whatever knocked it round.
    if (kart.speed > 6 && kart.grounded) {
      input.throttle = 0;
      input.brake = 1;
    }
    d.driftHeld = input.drift = false;
    return steerFor(input, wantRate, speed, kartCfg);
  }

  if (aim) {
    // Lining up: no drift; plain steering onto the point.
    d.driftHeld = input.drift = false;
    return steerFor(input, wantRate, speed, kartCfg);
  }

  // ---- Drifting: the corners that reward it (a drift is faster: driftSpeedMult).
  const radius = corner.curv === 0 ? Infinity : 1 / Math.abs(corner.curv);
  const cornerDir = corner.curv < 0 ? 1 : -1; // drift direction: +1 right, -1 left
  // The tightest arc a drift can carve (offset model): corners tighter than that are
  // taken with ordinary steering, which bites harder.
  const tightest = kartCfg.driftModel >= 1 ? kartCfg.driftRadiusTight : 0;
  // ...and the widest it can hold without countersteering into a spin-out: gentler
  // corners than that are taken with ordinary steering too.
  const counterMax = kartCfg.spinThreshold * 0.9;
  const widestCurv = kartCfg.driftModel >= 1 ? driftCurvature(-counterMax, kartCfg) : -1;
  const widest = widestCurv > 1e-6 ? 1 / widestCurv : Infinity;

  if (kart.driftDir !== 0) d.lastDrift = { dir: kart.driftDir, at: moment.clock };
  if (kart.driftDir !== 0) {
    // Keep drifting while the corner continues the same way and is still tight (an
    // early exit, now and then, from a less sure drifter).
    const now = sharpestAhead(line, i, 0, cfg.driftScan * 0.5).curv;
    const nowRadius = now === 0 ? Infinity : 1 / Math.abs(now);
    const sameWay = (now < 0 ? 1 : -1) === kart.driftDir;
    const exitRadius =
      cfg.driftExitRadius * (0.8 + 0.6 * skill.drift) * (d.mistake.kind === "early" ? 0.55 : 1);
    // (and out of it if it's been thrown off the road)
    input.drift = sameWay && nowRadius < exitRadius && nowRadius > tightest * 1.05 && !offRoad;
    if (input.drift) {
      if (kartCfg.driftModel >= 1) {
        // Offset model: the stick sets the body's curvature, and the path is the body
        // plus an offset that is still building (on entry it carries the kart wide). So
        // ask the body for the turn the line needs minus what the offset is adding,
        // staying short of the spin-out zone on countersteer.
        const target = (kart.driftDir * kartCfg.driftOffsetDeg * Math.PI) / 180;
        const offsetRate = (target - kart.driftOffset) * kartCfg.driftOffsetRate;
        const curvature = (-kart.driftDir * (wantRate - offsetRate)) / speed;
        const wantSteer = driftSteerFor(curvature, kartCfg);
        if (wantSteer >= -counterMax) {
          input.steer = clamp(wantSteer, -1, 1) * kart.driftDir;
          d.driftHeld = true;
          d.debug.note = "drift";
          return input;
        }
        // The line straightens out more than the drift can follow: let go and steer.
        input.drift = false;
        return steerFor(input, wantRate, speed, kartCfg);
      }
      // Legacy model: pick the stick position whose drift turn rate matches what the
      // line needs, inverting the kart's tight / neutral / counter mapping.
      const turn = -kart.driftDir * wantRate;
      const into =
        turn >= kartCfg.driftTurnNeutral
          ? (turn - kartCfg.driftTurnNeutral) / (kartCfg.driftTurnTight - kartCfg.driftTurnNeutral)
          : -(kartCfg.driftTurnNeutral - turn) /
            (kartCfg.driftTurnNeutral - kartCfg.driftTurnCounter);
      input.steer = clamp(into, -1, 1) * kart.driftDir;
      d.driftHeld = true;
      return input;
    }
  }

  // Whether to drift this corner: decided once per corner, by drift skill.
  // (A practised drifter drifts the sweepers too: the drift's speed bonus pays there.)
  const enter = cfg.driftEnterRadius * (0.8 + 0.6 * skill.drift);
  const goodCorner = radius < Math.min(enter, widest) && radius >= tightest * 1.25;
  if (goodCorner && Math.abs(corner.at - d.corner.at) > Math.round(25 / line.spacing)) {
    d.corner = {
      at: corner.at,
      drift: chance(d.seed * 7.3 + corner.at * 0.37 + Math.floor(moment.clock / 40)) < skill.drift,
    };
  }
  const startDrift =
    cfg.drift > 0 &&
    d.corner.drift &&
    d.mistake.kind !== "nodrift" &&
    kart.driftDir === 0 &&
    // (not the other way straight after a drift: the new slide would carry it wide)
    (cornerDir === d.lastDrift.dir || moment.clock - d.lastDrift.at > 0.9) &&
    !d.driftHeld &&
    kart.grounded &&
    kart.speed > kartCfg.driftMinSpeed + 3 &&
    goodCorner &&
    // Only from its line, pointing the right way, and where the road has room for the
    // slide (not a narrow passage: a drift there carries it into the wall or off the edge).
    !offRoad &&
    Math.abs(here.across - d.offset) < 3.5 &&
    lineErr < 0.6 &&
    line.width[corner.at]! >= 13;
  if (startDrift) {
    input.drift = true;
    input.steer = cornerDir;
    d.driftHeld = true;
    return input;
  }

  d.driftHeld = false;
  d.debug.note = "";
  return steerFor(input, wantRate, speed, kartCfg);
}

/** Normal steering: the stick position for the wanted turn rate at this speed. */
function steerFor(input: InputState, wantRate: number, speed: number, kartCfg: KartConfig) {
  const atSpeed = Math.min(1, speed / kartCfg.topSpeed);
  const rolling = Math.min(1, speed / kartCfg.turnFullSpeed);
  let rate = (kartCfg.turnRate + (kartCfg.turnRateAtTop - kartCfg.turnRate) * atSpeed) * rolling;
  // Braking steers harder (the braking steering coefficient: see the sharp turn).
  if (kartCfg.sharpTurn && input.brake > 0)
    rate *= 1 + (kartCfg.steerCoefBrake / kartCfg.steerCoefNormal - 1) * Math.min(1, input.brake);
  input.steer = clamp(-wantRate / Math.max(0.1, rate), -1, 1);
  return input;
}
