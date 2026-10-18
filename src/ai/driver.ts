/**
 * An AI driver. Each step it looks at its kart and the racing line and produces an
 * InputState (throttle, brake, steer, drift), exactly what a player's controller would.
 * The kart model treats it the same as the player's input.
 */
import type { InputState } from "../core/input";
import { driftSteerFor, type KartConfig, type KartState } from "../vehicles/kart";
import type { RacingLine } from "./racingLine";

export interface AiConfig {
  /** Rivals' top speed relative to their character's (difficulty). */
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
  /** Rivals press the throttle within ± this many seconds of the perfect start. */
  startSpread: number;
}

export interface Driver {
  line: RacingLine;
  /** Nearest line point last step. */
  index: number;
  /** Drift button held last step (a drift needs a fresh press). */
  driftHeld: boolean;
  /** Seconds from the perfect start moment that this driver presses the throttle. */
  startOffset: number;
}

/** Small deterministic pseudo-random number in [-1, 1) from an integer seed. */
function noise(seed: number) {
  const v = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return (v - Math.floor(v)) * 2 - 1;
}

export function createDriver(line: RacingLine, seed: number, cfg: AiConfig): Driver {
  return { line, index: 0, driftHeld: false, startOffset: noise(seed) * cfg.startSpread };
}

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

function nearest(d: Driver, x: number, z: number): number {
  const { line } = d;
  const dist = (i: number) => {
    const j = ((i % line.n) + line.n) % line.n;
    return (line.x[j]! - x) ** 2 + (line.z[j]! - z) ** 2;
  };
  let best = d.index;
  let bestD = dist(best);
  for (let k = -30; k <= 30; k++) {
    const v = dist(d.index + k);
    if (v < bestD) {
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
  d.index = ((best % line.n) + line.n) % line.n;
  return d.index;
}

/** The corner ahead with the largest curvature (signed), between two distances ahead. */
function sharpestAhead(line: RacingLine, from: number, near: number, far: number) {
  let best = 0;
  const a = Math.round(near / line.spacing);
  const b = Math.round(far / line.spacing);
  for (let k = a; k <= b; k++) {
    const c = line.curvature[(from + k) % line.n]!;
    if (Math.abs(c) > Math.abs(best)) best = c;
  }
  return best;
}

export interface RaceMoment {
  /** True while the race is still counting down. */
  countdown: boolean;
  /** Race clock; negative before GO. */
  clock: number;
  /** Clock time of the perfect start moment. */
  startTarget: number;
}

export function driveAi(
  d: Driver,
  kart: KartState,
  kartCfg: KartConfig,
  cfg: AiConfig,
  moment: RaceMoment,
): InputState {
  const input: InputState = { throttle: 0, brake: 0, steer: 0, drift: false, item: false };
  if (moment.countdown) {
    input.throttle = moment.clock >= moment.startTarget + d.startOffset ? 1 : 0;
    return input;
  }
  input.throttle = 1;
  const { line } = d;
  const i = nearest(d, kart.x, kart.z);
  const speed = Math.max(1, Math.abs(kart.speed));

  // Pure pursuit: the turn rate that arcs the travel direction onto a point ahead.
  const look = cfg.lookAhead + cfg.lookAheadPerSpeed * speed;
  const j = (i + Math.round(look / line.spacing)) % line.n;
  const aim = wrap(Math.atan2(line.x[j]! - kart.x, line.z[j]! - kart.z) - kart.velAngle);
  const wantRate = (2 * speed * Math.sin(aim)) / look; // heading change per second (+ = left)

  const corner = sharpestAhead(line, i, 4, cfg.driftScan);
  const radius = corner === 0 ? Infinity : 1 / Math.abs(corner);
  const cornerDir = corner < 0 ? 1 : -1; // drift direction: +1 right, -1 left

  if (kart.driftDir !== 0) {
    // Keep drifting while the corner continues the same way and is still tight.
    const now = sharpestAhead(line, i, 0, cfg.driftScan * 0.5);
    const nowRadius = now === 0 ? Infinity : 1 / Math.abs(now);
    const sameWay = (now < 0 ? 1 : -1) === kart.driftDir;
    input.drift = sameWay && nowRadius < cfg.driftExitRadius;
    if (input.drift) {
      if (kartCfg.driftModel >= 1) {
        // Offset model: the stick sets the body's curvature, and the path is the body
        // plus an offset that is still building (on entry it carries the kart wide). So
        // ask the body for the turn the line needs minus what the offset is adding,
        // staying short of the spin-out zone on countersteer.
        const target = (kart.driftDir * kartCfg.driftOffsetDeg * Math.PI) / 180;
        const offsetRate = (target - kart.driftOffset) * kartCfg.driftOffsetRate;
        const curvature = (-kart.driftDir * (wantRate - offsetRate)) / speed;
        const into = Math.max(-kartCfg.spinThreshold * 0.9, driftSteerFor(curvature, kartCfg));
        input.steer = clamp(into, -1, 1) * kart.driftDir;
        d.driftHeld = true;
        return input;
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

  const startDrift =
    cfg.drift > 0 &&
    kart.driftDir === 0 &&
    !d.driftHeld &&
    kart.grounded &&
    kart.speed > kartCfg.driftMinSpeed + 3 &&
    radius < cfg.driftEnterRadius;
  if (startDrift) {
    input.drift = true;
    input.steer = cornerDir;
    d.driftHeld = true;
    return input;
  }

  // Normal steering: stick position for the wanted turn rate at this speed.
  const atSpeed = Math.min(1, speed / kartCfg.topSpeed);
  const rolling = Math.min(1, speed / kartCfg.turnFullSpeed);
  const rate = (kartCfg.turnRate + (kartCfg.turnRateAtTop - kartCfg.turnRate) * atSpeed) * rolling;
  input.steer = clamp(-wantRate / Math.max(0.1, rate), -1, 1);
  d.driftHeld = false;
  return input;
}
