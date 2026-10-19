/**
 * Race rules for every kart in a race: "Get ready!" then "GO!" with a start boost for
 * good timing, laps, lap times, finishing order, race positions, and respawning.
 *
 * Progress round the course is checkpoint progression (checkpoints.ts): invisible 3D
 * gates crossed in order, wherever you drive between them. Gate 0 is the start/finish
 * line. The road surface plays no part in it: leaving the road, flying and cutting
 * corners never cost progress. Only walled tracks (not open ones) still put a kart that
 * sits grounded off the road for a moment back at its last checkpoint: that's being
 * stuck outside the walls, not a progress rule.
 *
 * Racer 0 is the player.
 */
import type { KartState } from "../vehicles/kart";
import type { Track } from "../world/track";
import {
  DEFAULT_GATES,
  checkpointsFromRoute,
  gateAt,
  groupGates,
  newProgression,
  planeDist,
  rankValue,
  stepProgression,
  type Checkpoint,
  type CheckpointGate,
  type GateOptions,
  type Progression,
  type RouteSample,
  type Spot,
} from "./checkpoints";

export type { Spot } from "./checkpoints";

export interface RaceConfig {
  laps: number;
  /** How long "Get ready!" shows before GO, seconds. */
  readySec: number;
  /** Where the perfect start moment sits between "Get ready!" (0) and GO (1). */
  startTargetFrac: number;
  /** A press this close to the perfect moment (either side) is a perfect start, s. */
  perfectWindowSec: number;
  /** A press up to this much earlier than the perfect window is a good start, s. */
  earlyWindowSec: number;
  /** How long "GO!" stays up, seconds. */
  goShowSec: number;
  startPerfectMult: number;
  startPerfectSec: number;
  startGoodMult: number;
  startGoodSec: number;
  /** Seconds grounded off the road before you're put back on it. */
  respawnAfterSec: number;
}

/** A checkpoint's main gate (see checkpoints.ts). */
export type Gate = CheckpointGate;

export type Phase = "countdown" | "racing";

export type StartTier = "perfect" | "good" | "early" | "late" | "none";

export interface StartResult {
  tier: StartTier;
  /** Seconds from the perfect moment to the press: negative = early. */
  offset?: number;
}

/** One kart's progress through the race. */
export interface Racer extends Progression {
  /** Current lap, 1-based. */
  lap: number;
  lapStart: number;
  lapTimes: number[];
  bestLap?: number;
  totalTime?: number;
  finished: boolean;
  offRoadFor: number;
  /** Kart position at the end of the previous step, for crossing tests. */
  px: number;
  py: number;
  pz: number;
  /** Clock time of the latest throttle press during "Get ready!". */
  pressAt?: number;
  /** Throttle state last step; undefined before the first step. */
  throttleWas?: boolean;
  /** How the start went, once GO has happened. */
  start?: StartResult;
}

export interface Race {
  /** Open track: leaving the road never respawns you. */
  open: boolean;
  /** The checkpoints, in order (each with one or more gates). */
  course: Checkpoint[];
  /** Each checkpoint's main gate, by index. */
  gates: Gate[];
  /** Track samples on the last 80 m before the line (x, z, metres before it): only for
   * ranking the starting grid, which can sit on the curve leading onto the line. */
  approach: { x: number; z: number; before: number }[];
  phase: Phase;
  /** Seconds since GO; negative during the countdown. */
  clock: number;
  /** True only on the step where GO happens. */
  goThisStep: boolean;
  racers: Racer[];
  /** Racer indices in the order they finished. */
  finishOrder: number[];
}

export interface RaceEvents {
  /** Put the kart back here (walled tracks: stuck off the road). */
  respawn?: Spot;
  /** Start boost to apply right now, at GO. */
  boost?: { mult: number; seconds: number };
  /** A checkpoint was validated, a lap completed, or a checkpoint lost by reversing. */
  checkpoint?: Gate;
  lap?: number;
  reversed?: Gate;
}

/** The track's route as checkpoint-placement samples (game coordinates). */
export function routeSamples(track: Track): RouteSample[] {
  return track.samples.map((p) => ({
    x: p.pos.x,
    y: p.pos.y,
    z: p.pos.z,
    fx: p.forward.x,
    fz: p.forward.z,
    width: p.width,
    dist: p.dist,
  }));
}

/** Gate sizes for a track: generous on open tracks, closer to the road between walls. */
export function gateOptions(track: Track): GateOptions {
  const d = track.data;
  return {
    ...DEFAULT_GATES,
    margin: d.gateMargin ?? (d.open ? DEFAULT_GATES.margin : 6),
    height: d.gateHeight ?? DEFAULT_GATES.height,
  };
}

/**
 * The track's checkpoints: Blender's gates (track.data.gates) if it has them, else the
 * ones listed in its data (track.data.checkpoints, by distance along the lap), else
 * placed automatically from the route.
 */
export function makeCourse(track: Track): Checkpoint[] {
  const d = track.data;
  if (d.gates?.length) return groupGates(d.gates);
  const s = routeSamples(track);
  const o = gateOptions(track);
  if (d.checkpoints?.length)
    return d.checkpoints.map((c, i) => {
      const g = gateAt(s, track.length, c.at, i, {
        ...o,
        ...(c.height !== undefined && { height: c.height }),
      });
      if (c.left !== undefined) g.left = c.left;
      if (c.right !== undefined) g.right = c.right;
      return { index: i, gates: [g] };
    });
  return checkpointsFromRoute(s, track.length, o);
}

/** Each checkpoint's main gate (kept for older callers and tests). */
export const makeGates = (track: Track): Gate[] => makeCourse(track).map((c) => c.gates[0]!);

function newRacer(course: Checkpoint[]): Racer {
  const start = course[0]!.gates[0]!;
  return {
    ...newProgression(course),
    lap: 1,
    lapStart: 0,
    lapTimes: [],
    finished: false,
    offRoadFor: 0,
    px: start.x,
    py: start.y,
    pz: start.z,
  };
}

export function createRace(
  track: Track,
  cfg: RaceConfig,
  racers = 1,
  course = makeCourse(track),
): Race {
  return {
    open: Boolean(track.data.open),
    course,
    gates: course.map((c) => c.gates[0]!),
    approach: track.samples
      .filter((p) => track.length - p.dist < 80)
      .map((p) => ({ x: p.pos.x, z: p.pos.z, before: track.length - p.dist })),
    phase: "countdown",
    clock: -cfg.readySec,
    goThisStep: false,
    racers: Array.from({ length: racers }, () => newRacer(course)),
    finishOrder: [],
  };
}

/** Where racer i goes if they need putting back: just past their last checkpoint. */
export const respawnSpot = (race: Race, i: number): Spot => race.racers[i]!.lastGate.respawn;

/** Tell the race a kart was moved (respawned): the jump isn't swept for crossings. */
export function teleported(race: Race, i: number, kart: { x: number; y: number; z: number }) {
  const r = race.racers[i]!;
  r.px = kart.x;
  r.py = kart.y;
  r.pz = kart.z;
}

/** Clock time (negative, before GO) of the perfect start moment. */
export const startTarget = (cfg: RaceConfig) => -cfg.readySec * (1 - cfg.startTargetFrac);

/**
 * Judge a start. The press must still be held at GO. Holding the throttle from before
 * "Get ready!" never counts as a press, so mashing it early earns nothing.
 */
export function judgeStart(
  pressAt: number | undefined,
  heldAtGo: boolean,
  cfg: RaceConfig,
): StartResult {
  if (pressAt === undefined || !heldAtGo) return { tier: "none" };
  const offset = pressAt - startTarget(cfg);
  if (Math.abs(offset) <= cfg.perfectWindowSec) return { tier: "perfect", offset };
  if (offset < 0 && offset >= -(cfg.perfectWindowSec + cfg.earlyWindowSec)) {
    return { tier: "good", offset };
  }
  return { tier: offset < 0 ? "early" : "late", offset };
}

export const canDrive = (race: Race) => race.phase !== "countdown";

/** Advance the shared race clock. Call once per step, before stepRacer. */
export function tickRace(race: Race, dt: number) {
  race.clock += dt;
  race.goThisStep = false;
  if (race.phase === "countdown" && race.clock >= 0) {
    race.phase = "racing";
    race.goThisStep = true;
  }
}

/** Advance one racer by a step, after its kart has moved. */
export function stepRacer(
  race: Race,
  index: number,
  kart: KartState,
  onRoad: boolean,
  throttle: number,
  cfg: RaceConfig,
  dt: number,
): RaceEvents {
  const r = race.racers[index]!;
  const events: RaceEvents = {};
  const pressed = throttle > 0.5;

  if (race.phase === "countdown" || race.goThisStep) {
    // A press is the moment the throttle goes down. One already held when the race
    // (re)starts doesn't count: on the first step we only note its state.
    if (race.phase === "countdown" && r.throttleWas === false && pressed) {
      r.pressAt = race.clock;
    }
    r.throttleWas = pressed;
    if (race.goThisStep) {
      r.start = judgeStart(r.pressAt, pressed, cfg);
      if (r.start.tier === "perfect") {
        events.boost = { mult: cfg.startPerfectMult, seconds: cfg.startPerfectSec };
      } else if (r.start.tier === "good") {
        events.boost = { mult: cfg.startGoodMult, seconds: cfg.startGoodSec };
      }
    }
    r.px = kart.x;
    r.py = kart.y;
    r.pz = kart.z;
    return events;
  }

  if (!r.finished) {
    const step = stepProgression(race.course, r, { x: r.px, y: r.py, z: r.pz }, kart);
    if (step.passed) events.checkpoint = step.passed;
    if (step.reversed) events.reversed = step.reversed;
    if (step.lap) {
      const time = race.clock - r.lapStart;
      r.lapTimes.push(time);
      r.bestLap = Math.min(r.bestLap ?? Infinity, time);
      r.lapStart = race.clock;
      events.lap = step.lap;
      if (step.lap >= cfg.laps) {
        r.finished = true;
        r.totalTime = race.clock;
        race.finishOrder.push(index);
      } else {
        r.lap = step.lap + 1;
      }
    }
  }
  r.px = kart.x;
  r.py = kart.y;
  r.pz = kart.z;

  // Walled tracks only: grounded outside the walls for a moment means stuck.
  r.offRoadFor = !onRoad && !race.open && kart.grounded ? r.offRoadFor + dt : 0;
  if (r.offRoadFor > cfg.respawnAfterSec) {
    r.offRoadFor = 0;
    events.respawn = respawnSpot(race, index);
  }
  return events;
}

/**
 * How far round the race a racer is: checkpoints validated, plus how far from the last
 * one towards the next (between the two gate planes; negative behind the start line,
 * on the grid). Never from the nearest road: being off it changes nothing.
 */
export function progress(race: Race, index: number, x: number, z: number, y = 0): number {
  const r = race.racers[index]!;
  if (
    r.passed === 0 &&
    r.best === 0 &&
    race.approach.length &&
    planeDist(r.lastGate, { x, y, z }) < 0
  ) {
    // On the grid, behind the line: rank by distance along the road to the line.
    let best = race.approach[0]!;
    let bestD = Infinity;
    for (const p of race.approach) {
      const dd = (p.x - x) ** 2 + (p.z - z) ** 2;
      if (dd < bestD) {
        bestD = dd;
        best = p;
      }
    }
    return -Math.min(0.999, best.before / 100);
  }
  return rankValue(race.course, r, { x, y, z });
}

/**
 * Racer indices from first place to last. Finished racers keep their finishing order;
 * the rest rank by progress, ties by racer index.
 */
export function standings(race: Race, positions: { x: number; y?: number; z: number }[]): number[] {
  const done = race.finishOrder;
  const value = race.racers.map((_, i) =>
    progress(race, i, positions[i]!.x, positions[i]!.z, positions[i]!.y ?? 0),
  );
  const rest = race.racers
    .map((_, i) => i)
    .filter((i) => !race.racers[i]!.finished)
    .sort((a, b) => value[b]! - value[a]! || a - b);
  return [...done, ...rest];
}

/** A racer's current lap time, or their last lap's once finished. */
export function lapClock(race: Race, index: number): number {
  const r = race.racers[index]!;
  if (race.phase === "countdown") return 0;
  return r.finished ? (r.lapTimes.at(-1) ?? 0) : race.clock - r.lapStart;
}

/** 83.456 → "1:23.45" */
export function formatTime(seconds: number): string {
  const s = Math.max(0, seconds);
  const m = Math.floor(s / 60);
  const rest = s - m * 60;
  return `${m}:${rest.toFixed(2).padStart(5, "0")}`;
}
