/**
 * Race rules: "Get ready!" then "GO!" with a start boost for good timing, checkpoints
 * that must be passed in order, laps, lap times, a finish, and respawning at the last
 * checkpoint if you end up off the track.
 *
 * Checkpoints are gates spaced evenly along the track, derived from its samples. Gate 0
 * is the start/finish line. A gate counts when the kart crosses its line going forward
 * while inside the road's width, so skipping a section of track doesn't count.
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
  halfWidth: number;
}

export type Phase = "countdown" | "racing" | "finished";

export type StartTier = "perfect" | "good" | "early" | "late" | "none";

export interface StartResult {
  tier: StartTier;
  /** Seconds from the perfect moment to the press: negative = early. */
  offset?: number;
}

export interface Race {
  gates: Gate[];
  phase: Phase;
  /** Seconds since GO; negative during the countdown. */
  clock: number;
  /** Current lap, 1-based. */
  lap: number;
  /** Index of the next gate to pass. */
  next: number;
  /** Last gate passed: where a respawn puts you. */
  last: number;
  lapStart: number;
  lapTimes: number[];
  bestLap?: number;
  totalTime?: number;
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

export interface RaceEvents {
  respawn?: Gate;
  /** Start boost to apply right now, at GO. */
  boost?: { mult: number; seconds: number };
}

/** Extra width either side of the road that still counts as passing a gate. */
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
      halfWidth: s.width / 2,
    });
  }
  return gates;
}

export function createRace(track: Track, cfg: RaceConfig): Race {
  const gates = makeGates(track, cfg.checkpointSpacing);
  return {
    gates,
    phase: "countdown",
    clock: -cfg.readySec,
    lap: 1,
    next: 1,
    last: 0,
    lapStart: 0,
    lapTimes: [],
    offRoadFor: 0,
    px: gates[0]!.x,
    pz: gates[0]!.z,
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
  return before < 0 && after >= 0 && Math.abs(across) <= g.halfWidth + GATE_MARGIN;
}

export const canDrive = (race: Race) => race.phase !== "countdown";

/** Advance the race by one fixed step, after the kart has moved. */
export function stepRace(
  race: Race,
  kart: KartState,
  onRoad: boolean,
  throttle: number,
  cfg: RaceConfig,
  dt: number,
): RaceEvents {
  const events: RaceEvents = {};
  const pressed = throttle > 0.5;
  race.clock += dt;

  if (race.phase === "countdown") {
    // A press is the moment the throttle goes down. One already held when the race
    // (re)starts doesn't count: on the first step we only note its state.
    if (race.throttleWas === false && pressed) race.pressAt = race.clock;
    race.throttleWas = pressed;
    if (race.clock >= 0) {
      race.phase = "racing";
      race.start = judgeStart(race.pressAt, pressed, cfg);
      if (race.start.tier === "perfect") {
        events.boost = { mult: cfg.startPerfectMult, seconds: cfg.startPerfectSec };
      } else if (race.start.tier === "good") {
        events.boost = { mult: cfg.startGoodMult, seconds: cfg.startGoodSec };
      }
    }
    race.px = kart.x;
    race.pz = kart.z;
    return events;
  }

  if (race.phase === "racing") {
    const gate = race.gates[race.next]!;
    if (crossed(gate, race.px, race.pz, kart.x, kart.z)) {
      race.last = race.next;
      if (race.next === 0) {
        const time = race.clock - race.lapStart;
        race.lapTimes.push(time);
        race.bestLap = Math.min(race.bestLap ?? Infinity, time);
        race.lapStart = race.clock;
        if (race.lap >= cfg.laps) {
          race.phase = "finished";
          race.totalTime = race.clock;
        } else {
          race.lap++;
        }
      }
      race.next = (race.next + 1) % race.gates.length;
    }
  }
  race.px = kart.x;
  race.pz = kart.z;

  race.offRoadFor = !onRoad && kart.grounded ? race.offRoadFor + dt : 0;
  if (race.offRoadFor > cfg.respawnAfterSec) {
    race.offRoadFor = 0;
    events.respawn = race.gates[race.last];
  }
  return events;
}

/** Current lap's running time, or 0 before the start. */
export const lapClock = (race: Race) =>
  race.phase === "racing" ? race.clock - race.lapStart : (race.lapTimes.at(-1) ?? 0);

/** 83.456 → "1:23.45" */
export function formatTime(seconds: number): string {
  const s = Math.max(0, seconds);
  const m = Math.floor(s / 60);
  const rest = s - m * 60;
  return `${m}:${rest.toFixed(2).padStart(5, "0")}`;
}
