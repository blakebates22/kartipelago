import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { createTrackGround } from "../src/physics/ground";
import { stepImpacts, stepWalls } from "../src/physics/walls";
import {
  createKartState,
  stepKart,
  wrapAngle,
  type KartConfig,
  type KartState,
} from "../src/vehicles/kart";
import { buildTrack, type TrackData } from "../src/world/track";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle, driftModel: 1 };
const hitCfg = tuning.collision;
const walls = { ...tuning.physics, ...hitCfg, wallHeight: tuning.track.wallHeight };

// A long straight along +Z, 20 m wide: the left wall's inner face sits at x = +10 - radius.
const straight: TrackData = {
  name: "straight",
  defaultWidth: 20,
  points: [
    { x: 0, z: -400 },
    { x: 0, z: 0 },
    { x: 0, z: 400 },
    { x: 400, z: 400 },
    { x: 400, z: -400 },
  ],
};
const track = buildTrack(straight, 2);

interface Log {
  tiers: number[];
  maxHeadingStep: number;
}

function drive(s: KartState, seconds: number, input: Partial<InputState>, log?: Log) {
  const ground = createTrackGround(track);
  for (let t = 0; t < seconds; t += dt) {
    const before = s.heading;
    stepImpacts(s, hitCfg, dt);
    stepKart(s, { ...NEUTRAL, ...input }, cfg, dt);
    const hit = stepWalls(s, ground, walls, dt);
    if (log) {
      if (hit?.tier) log.tiers.push(hit.tier);
      log.maxHeadingStep = Math.max(log.maxHeadingStep, Math.abs(wrapAngle(s.heading - before)));
    }
  }
  return s;
}

/**
 * A kart drifting left at speed, its path angled `deg` toward the left wall (+X), with
 * the wall `gap` metres away.
 */
function driftingAt(deg: number, gap = 1) {
  const s = createKartState(10 - walls.kartRadius - gap, 0, 0);
  s.speed = 26;
  s.driftDir = -1;
  s.driftTime = 1;
  s.driftOffset = (-cfg.driftOffsetDeg * Math.PI) / 180;
  s.driftPressAge = 1;
  s.velAngle = (deg * Math.PI) / 180;
  s.heading = s.velAngle - s.driftOffset;
  return s;
}

const intoSpeed = (deg: number) => 26 * Math.sin((deg * Math.PI) / 180);

describe("wall impacts", () => {
  it("a light scrape keeps the drift and doesn't kick the kart", () => {
    const deg = 5; // about 2.3 m/s into the wall
    expect(intoSpeed(deg)).toBeLessThan(hitCfg.scrapeSpeed);
    const log = { tiers: [], maxHeadingStep: 0 };
    const s = drive(driftingAt(deg, 0.02), 0.6, { throttle: 1, drift: true }, log);
    expect(log.tiers).toContain(1);
    expect(s.driftDir).toBe(-1);
    expect(s.yawKick).toBe(0);
    expect(s.crashTime).toBe(0);
  });

  it("a moderate hit kicks the kart round but the drift survives", () => {
    const deg = 15; // about 6.7 m/s into the wall
    const log = { tiers: [], maxHeadingStep: 0 };
    const s = drive(driftingAt(deg), 0.15, { throttle: 1, drift: true }, log);
    expect(log.tiers).toContain(2);
    expect(log.tiers).not.toContain(3);
    expect(s.driftDir).toBe(-1);
    expect(s.crashTime).toBe(0);
  });

  it("a severe hit cancels the drift and disrupts control, which returns smoothly", () => {
    const deg = 40; // about 16.7 m/s into the wall
    expect(intoSpeed(deg)).toBeGreaterThan(hitCfg.crashSpeed);
    const log = { tiers: [], maxHeadingStep: 0 };
    const s = drive(driftingAt(deg), 0.12, { throttle: 1, drift: true }, log);
    expect(log.tiers).toContain(3);
    expect(s.driftDir).toBe(0);
    expect(s.crashTime).toBeGreaterThan(0);
    expect(s.controlScale).toBeLessThan(0.6);
    // Holding drift doesn't restart it until the disruption wears off.
    drive(s, hitCfg.crashSec * 0.5, { throttle: 1, drift: true, steer: -1 });
    expect(s.driftDir).toBe(0);
    let last = s.controlScale;
    for (let t = 0; t < hitCfg.crashSec; t += dt) {
      drive(s, dt, { throttle: 1 });
      expect(s.controlScale).toBeGreaterThanOrEqual(last - 1e-9); // only ever recovers
      last = s.controlScale;
    }
    expect(s.controlScale).toBe(1);
    expect(s.gripScale).toBe(1);
  });

  it("judges one contact once: sliding along a wall doesn't keep re-triggering", () => {
    const log = { tiers: [], maxHeadingStep: 0 };
    drive(driftingAt(15), 1.5, { throttle: 1, drift: true, steer: 1 }, log);
    expect(log.tiers.length).toBeLessThanOrEqual(2);
  });

  it("never snaps the heading: every step turns the kart only a little", () => {
    const log = { tiers: [], maxHeadingStep: 0 };
    drive(driftingAt(40), 1, { throttle: 1, drift: true }, log);
    // Under 3° per 1/120 s step, even in a crash.
    expect(log.maxHeadingStep).toBeLessThan((3 * Math.PI) / 180);
  });

  it("a head-on crash without drifting stops the kart and disrupts control", () => {
    const s = createKartState(10 - walls.kartRadius - 1, 0, Math.PI / 2);
    s.speed = 24;
    const log = { tiers: [], maxHeadingStep: 0 };
    drive(s, 0.15, { throttle: 1 }, log);
    expect(log.tiers).toContain(3);
    expect(Math.abs(s.speed)).toBeLessThan(6);
    expect(s.crashTime).toBeGreaterThan(0);
  });
});
