/**
 * Race rules for every kart in a race: "Get ready!" then "GO!" with a start boost for
 * good timing, checkpoints passed in order, laps, lap times, finishing order, race
 * positions, and respawning at the last checkpoint if a kart ends up off the track.
 *
 * Checkpoints are gates spaced evenly along the track, derived from its samples. Gate 0
 * is the start/finish line. A gate counts when the kart crosses its line going forward
 * while inside the road's width, so skipping a section of track doesn't count.
 *
 * Racer 0 is the player.
 */
import type { KartState } from "../vehicles/kart";
import type { Track } from "../world/track";

export interface RaceConfig {
  laps: number;
  /** Rough distance between checkpoints, metres. */
  checkpointSpacing: number;
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

export interface Gate {
  x: number;
  y: number;
  z: number;
  /** Unit forward (direction of travel) on the ground plane. */
  fx: number;
  fz: number;
  heading: number;
  /** Half the road width plus the margin that still counts as passing. */
  halfWidth: number;
}

export type Phase = "countdown" | "racing";

export type StartTier = "perfect" | "good" | "early" | "late" | "none";

export interface StartResult {
  tier: StartTier;
  /** Seconds from the perfect moment to the press: negative = early. */
  offset?: number;
}

/** One kart's progress through the race. */
export interface Racer {
  /** Current lap, 1-based. */
  lap: number;
  /** Index of the next gate to pass. */
  next: number;
  /** Last gate passed: where a respawn puts you. */
  last: number;
  /** Gates passed in total since the start (for positions). */
  passed: number;
  lapStart: number;
  lapTimes: number[];
  bestLap?: number;
  totalTime?: number;
  finished: boolean;
  offRoadFor: number;
  /** Kart position at the end of the previous step, for crossing tests. */
  px: number;
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
  gates: Gate[];
  /** Track samples near the end of the lap (x, z, metres before the line), for ranking the grid. */
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
  respawn?: Gate;
  /** Start boost to apply right now, at GO. */
  boost?: { mult: number; seconds: number };
}

/** Extra width either side of the road that still counts as passing a gate (default). */
const GATE_MARGIN = 2;

export function makeGates(track: Track, spacing: number): Gate[] {
  const n = Math.max(3, Math.round(track.length / spacing));
  const gates: Gate[] = [];
  for (let g = 0; g < n; g++) {
    const s = track.samples[Math.floor((g * track.samples.length) / n)]!;
    const flat = Math.hypot(s.forward.x, s.forward.z);
    const fx = s.forward.x / flat;
    const fz = s.forward.z / flat;
    gates.push({
      x: s.pos.x,
      y: s.pos.y,
      z: s.pos.z,
      fx,
      fz,
      heading: Math.atan2(fx, fz),
      halfWidth: s.width / 2 + (track.data.gateMargin ?? GATE_MARGIN),
    });
  }
  return gates;
}

function newRacer(start: Gate): Racer {
  return {
    lap: 1,
    next: 1,
    last: 0,
    passed: 0,
    lapStart: 0,
    lapTimes: [],
    finished: false,
    offRoadFor: 0,
    px: start.x,
    pz: start.z,
  };
}

export function createRace(track: Track, cfg: RaceConfig, racers = 1): Race {
  const gates = makeGates(track, cfg.checkpointSpacing);
  // The last stretch of road before the start line, where the grid sits.
  const approach = track.samples
    .filter((p) => track.length - p.dist < 80)
    .map((p) => ({ x: p.pos.x, z: p.pos.z, before: track.length - p.dist }));
  return {
    open: Boolean(track.data.open),
    gates,
    approach,
    phase: "countdown",
    clock: -cfg.readySec,
    goThisStep: false,
    racers: Array.from({ length: racers }, () => newRacer(gates[0]!)),
    finishOrder: [],
  };
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

/** Has the kart moved from behind this gate's line to on/after it, within its width? */
export function crossed(g: Gate, px: number, pz: number, x: number, z: number): boolean {
  const before = (px - g.x) * g.fx + (pz - g.z) * g.fz;
  const after = (x - g.x) * g.fx + (z - g.z) * g.fz;
  // Right is (-fz, fx); how far across the road the crossing happened.
  const across = (x - g.x) * -g.fz + (z - g.z) * g.fx;
  return before < 0 && after >= 0 && Math.abs(across) <= g.halfWidth;
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
    r.pz = kart.z;
    return events;
  }

  if (!r.finished) {
    const gate = race.gates[r.next]!;
    if (crossed(gate, r.px, r.pz, kart.x, kart.z)) {
      r.last = r.next;
      r.passed++;
      if (r.next === 0) {
        const time = race.clock - r.lapStart;
        r.lapTimes.push(time);
        r.bestLap = Math.min(r.bestLap ?? Infinity, time);
        r.lapStart = race.clock;
        if (r.lap >= cfg.laps) {
          r.finished = true;
          r.totalTime = race.clock;
          race.finishOrder.push(index);
        } else {
          r.lap++;
        }
      }
      r.next = (r.next + 1) % race.gates.length;
    }
  }
  r.px = kart.x;
  r.pz = kart.z;

  r.offRoadFor = !onRoad && !race.open && kart.grounded ? r.offRoadFor + dt : 0;
  if (r.offRoadFor > cfg.respawnAfterSec) {
    r.offRoadFor = 0;
    events.respawn = race.gates[r.last];
  }
  return events;
}

/** How far round the race a racer is, in gates (fractions between gates). */
export function progress(race: Race, index: number, x: number, z: number): number {
  const r = race.racers[index]!;
  const a = race.gates[r.last]!;
  const b = race.gates[r.next]!;
  const gap = Math.hypot(b.x - a.x, b.z - a.z) || 1;
  const along = ((x - a.x) * (b.x - a.x) + (z - a.z) * (b.z - a.z)) / (gap * gap);
  if (r.passed === 0 && along < 0 && race.approach.length > 0) {
    // Still behind the start line (on the grid): rank by distance along the road to the
    // line, which stays right when the grid sits on the curve leading onto it.
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
  return r.passed + Math.min(0.999, Math.max(0, along));
}

/** Racer indices from first place to last. Finished racers keep their finishing order. */
export function standings(race: Race, positions: { x: number; z: number }[]): number[] {
  const done = race.finishOrder;
  const rest = race.racers
    .map((_, i) => i)
    .filter((i) => !race.racers[i]!.finished)
    .sort(
      (a, b) =>
        progress(race, b, positions[b]!.x, positions[b]!.z) -
        progress(race, a, positions[a]!.x, positions[a]!.z),
    );
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
