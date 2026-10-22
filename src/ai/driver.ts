/**
 * An AI driver. Each step it looks at its kart and the racing line and produces an
 * InputState (throttle, brake, steer, drift), exactly what a player's controller would.
 * The kart model treats it the same as the player's input.
 */
import type { InputState } from "../core/input";
import { driftCurvature, driftSteerFor, type KartConfig, type KartState } from "../vehicles/kart";
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
  /**
   * The start (race.ts): each rival first presses the throttle this many reference
   * frames before GO, give or take up to startSpreadFrames (fixed per rival, so starts
   * repeat). Around 1-14 frames is a strong start, 15-29 weak, 0 an ordinary one: a
   * skill knob, not a guaranteed boost.
   */
  startAimFrames: number;
  startSpreadFrames: number;
}

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
}

/** Small deterministic pseudo-random number in [-1, 1) from an integer seed. */
function noise(seed: number) {
  const v = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return (v - Math.floor(v)) * 2 - 1;
}

export function createDriver(line: RacingLine, seed: number, cfg: AiConfig): Driver {
  return {
    line,
    index: 0,
    driftHeld: false,
    startLead: cfg.startAimFrames + noise(seed) * cfg.startSpreadFrames,
    lastDrift: { dir: 0, at: -Infinity },
  };
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
  /** The frame rate the start windows are counted in (race.ts: startRefHz). */
  startRefHz: number;
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
): InputState {
  const input: InputState = { throttle: 0, brake: 0, steer: 0, drift: false, item: false };
  if (moment.countdown) {
    // Pressed once, then held through GO (a press at or after GO is an ordinary start).
    input.throttle = moment.clock >= -d.startLead / moment.startRefHz ? 1 : 0;
    return input;
  }
  input.throttle = 1;
  const { line } = d;
  const i = nearest(d, kart.x, kart.z);
  const speed = Math.max(1, Math.abs(kart.speed));

  // Pure pursuit: the turn rate that arcs the travel direction onto a point ahead.
  const look = cfg.lookAhead + cfg.lookAheadPerSpeed * speed;
  const j = (i + Math.round(look / line.spacing)) % line.n;
  const tx = aim ? aim.x : line.x[j]!;
  const tz = aim ? aim.z : line.z[j]!;
  const toward = wrap(Math.atan2(tx - kart.x, tz - kart.z) - kart.velAngle);
  const dist = aim ? Math.max(4, Math.hypot(tx - kart.x, tz - kart.z)) : look;
  const wantRate = (2 * speed * Math.sin(toward)) / dist; // heading change per second (+ = left)
  if (aim) {
    // Lining up: no drift; plain steering onto the point.
    d.driftHeld = input.drift = false;
    return steerFor(input, wantRate, speed, kartCfg);
  }

  const corner = sharpestAhead(line, i, 4, cfg.driftScan);
  const radius = corner === 0 ? Infinity : 1 / Math.abs(corner);
  const cornerDir = corner < 0 ? 1 : -1; // drift direction: +1 right, -1 left
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
    // Keep drifting while the corner continues the same way and is still tight.
    const now = sharpestAhead(line, i, 0, cfg.driftScan * 0.5);
    const nowRadius = now === 0 ? Infinity : 1 / Math.abs(now);
    const sameWay = (now < 0 ? 1 : -1) === kart.driftDir;
    input.drift = sameWay && nowRadius < cfg.driftExitRadius && nowRadius > tightest * 1.05;
    if (input.drift) {
      if (kartCfg.driftModel >= 1) {
        // Offset model: the stick sets the body's curvature, and the path is the body
        // plus an offset that is still building (on entry it carries the kart wide). So
        // ask the body for the turn the line needs minus what the offset is adding,
        // staying short of the spin-out zone on countersteer.
        const target = (kart.driftDir * kartCfg.driftOffsetDeg * Math.PI) / 180;
        const offsetRate = (target - kart.driftOffset) * kartCfg.driftOffsetRate;
        const curvature = (-kart.driftDir * (wantRate - offsetRate)) / speed;
        const want = driftSteerFor(curvature, kartCfg);
        if (want >= -counterMax) {
          input.steer = clamp(want, -1, 1) * kart.driftDir;
          d.driftHeld = true;
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

  const startDrift =
    cfg.drift > 0 &&
    kart.driftDir === 0 &&
    // (not the other way straight after a drift: the new slide would carry it wide)
    (cornerDir === d.lastDrift.dir || moment.clock - d.lastDrift.at > 0.9) &&
    !d.driftHeld &&
    kart.grounded &&
    kart.speed > kartCfg.driftMinSpeed + 3 &&
    radius < Math.min(cfg.driftEnterRadius, widest) &&
    radius >= tightest * 1.1;
  if (startDrift) {
    input.drift = true;
    input.steer = cornerDir;
    d.driftHeld = true;
    return input;
  }

  d.driftHeld = false;
  return steerFor(input, wantRate, speed, kartCfg);
}

/** Normal steering: the stick position for the wanted turn rate at this speed. */
function steerFor(input: InputState, wantRate: number, speed: number, kartCfg: KartConfig) {
  const atSpeed = Math.min(1, speed / kartCfg.topSpeed);
  const rolling = Math.min(1, speed / kartCfg.turnFullSpeed);
  const rate = (kartCfg.turnRate + (kartCfg.turnRateAtTop - kartCfg.turnRate) * atSpeed) * rolling;
  input.steer = clamp(-wantRate / Math.max(0.1, rate), -1, 1);
  return input;
}
