import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import {
  createKartState,
  driftCurvature,
  driftSteerFor,
  stepKart,
  wrapAngle,
  type KartConfig,
  type KartState,
} from "../src/vehicles/kart";

// The offset drift model (driftModel 1), with the shipped tuning.
const cfg: KartConfig = { ...tuning.vehicle, driftModel: 1 };
const dt = 1 / 120;
const DEG = 180 / Math.PI;

function run(s: KartState, seconds: number, input: Partial<InputState>, c = cfg) {
  const held = { ...NEUTRAL, ...input };
  for (let t = 0; t < seconds; t += dt) stepKart(s, held, c, dt);
  return s;
}

/** Up to speed, then start a right drift. */
function drifting(c = cfg) {
  const s = run(createKartState(), 2, { throttle: 1 }, c);
  return run(s, dt, { throttle: 1, steer: 1, drift: true }, c);
}

/** Measured radius of the path over a stretch of steady input. */
function arcRadius(s: KartState, seconds: number, input: Partial<InputState>, c = cfg) {
  const h0 = s.velAngle;
  let dist = 0;
  let px = s.x;
  let pz = s.z;
  let turned = 0;
  let prev = h0;
  for (let t = 0; t < seconds; t += dt) {
    stepKart(s, { ...NEUTRAL, ...input }, c, dt);
    dist += Math.hypot(s.x - px, s.z - pz);
    px = s.x;
    pz = s.z;
    turned += wrapAngle(s.velAngle - prev);
    prev = s.velAngle;
  }
  return dist / Math.abs(turned);
}

describe("offset drift: steering shape", () => {
  it("turns inward hands-off, tightens to a limit, and widens on countersteer", () => {
    const classic = { ...cfg, driftCounterOut: false };
    expect(1 / driftCurvature(0, cfg)).toBeCloseTo(cfg.driftRadiusNeutral);
    expect(1 / driftCurvature(1, cfg)).toBeCloseTo(cfg.driftRadiusTight);
    expect(1 / driftCurvature(-1, classic)).toBeCloseTo(cfg.driftRadiusCounter);
    expect(driftCurvature(1, cfg)).toBeGreaterThan(driftCurvature(0.5, cfg));
  });

  it("countersteers out of the drift: full countersteer bends the other way", () => {
    expect(cfg.driftCounterOut).toBe(true);
    expect(1 / driftCurvature(-1, cfg)).toBeCloseTo(-cfg.driftRadiusCounterOut);
    // Somewhere in the middle of the countersteer the path runs straight.
    expect(driftCurvature(-0.3, cfg)).toBeGreaterThan(0);
    expect(driftCurvature(-0.8, cfg)).toBeLessThan(0);
  });

  it("gives most of the extra turn early, less as you push further in", () => {
    const k = (u: number) => driftCurvature(u, cfg);
    expect(k(0.5) - k(0)).toBeGreaterThan(k(1) - k(0.5));
  });

  it("has an exact inverse, so the AI can ask for a curvature", () => {
    for (const u of [-1, -0.6, -0.2, 0, 0.3, 0.7, 1]) {
      expect(driftSteerFor(driftCurvature(u, cfg), cfg)).toBeCloseTo(u, 6);
    }
  });
});

describe("offset drift: trajectory", () => {
  it("carves the same arc at different speeds for the same steer", () => {
    const slow = { ...cfg, topSpeed: 18 };
    const fast = { ...cfg, topSpeed: 32 };
    const rSlow = arcRadius(
      run(drifting(slow), 1, { throttle: 1, drift: true }, slow),
      1,
      { throttle: 1, drift: true },
      slow,
    );
    const rFast = arcRadius(
      run(drifting(fast), 1, { throttle: 1, drift: true }, fast),
      1,
      { throttle: 1, drift: true },
      fast,
    );
    expect(Math.abs(rSlow - rFast) / rFast).toBeLessThan(0.05);
    expect(rFast).toBeCloseTo(cfg.driftRadiusNeutral, -1);
  });

  it("drift right, countersteer: a wider arc than hands-off, and the nose stays in", () => {
    const neutral = arcRadius(run(drifting(), 1, { throttle: 1, drift: true }), 1, {
      throttle: 1,
      drift: true,
    });
    const s = run(drifting(), 1, { throttle: 1, drift: true, steer: -1 });
    const counter = arcRadius(s, 1, { throttle: 1, drift: true, steer: -0.55 });
    expect(counter).toBeGreaterThan(neutral * 1.5);
    // Path still points outward of the nose: the offset doesn't follow the stick.
    expect(s.driftOffset * DEG).toBeGreaterThan(cfg.driftOffsetDeg * 0.9);
  });

  it("drift left, countersteer right: the kart really goes right, still angled left", () => {
    // Up to speed, start a LEFT drift, settle it, then hold full right.
    const s = run(createKartState(), 2, { throttle: 1 });
    run(s, dt, { throttle: 1, steer: -1, drift: true });
    run(s, 0.8, { throttle: 1, drift: true });
    expect(s.driftDir).toBe(-1);
    const path0 = s.velAngle;
    run(s, 0.6, { throttle: 1, drift: true, steer: 1 });
    // Positive steer lowers the angle: the path has swung right...
    expect(wrapAngle(s.velAngle - path0)).toBeLessThan(-0.1);
    // ...while the body is still angled into the left drift, and the drift goes on.
    expect(s.driftDir).toBe(-1);
    expect(s.driftOffset * DEG).toBeLessThan(-cfg.driftOffsetDeg * 0.8);
  });

  it("with the switch off, full countersteer only widens the arc (the original feel)", () => {
    const classic = { ...cfg, driftCounterOut: false };
    const s = run(createKartState(), 2, { throttle: 1 }, classic);
    run(s, dt, { throttle: 1, steer: -1, drift: true }, classic);
    run(s, 0.8, { throttle: 1, drift: true }, classic);
    const path0 = s.velAngle;
    run(s, 0.6, { throttle: 1, drift: true, steer: 1 }, classic);
    expect(wrapAngle(s.velAngle - path0)).toBeGreaterThan(0); // still turning left
  });

  it("builds the offset over about half a second on entry", () => {
    const s = drifting();
    run(s, 0.5, { throttle: 1, drift: true });
    const frac = s.driftOffset / ((cfg.driftOffsetDeg * Math.PI) / 180);
    expect(frac).toBeGreaterThan(0.8);
    expect(frac).toBeLessThan(0.95);
  });

  it("eases the offset away after release with no overshoot, then grips again", () => {
    const s = run(drifting(), 1.5, { throttle: 1, drift: true, steer: 0.5 });
    let last = s.driftOffset;
    let t = 0;
    for (; t < 0.5; t += dt) {
      stepKart(s, { ...NEUTRAL, throttle: 1 }, cfg, dt);
      expect(s.driftOffset).toBeLessThanOrEqual(last + 1e-12);
      expect(s.driftOffset).toBeGreaterThanOrEqual(0);
      last = s.driftOffset;
    }
    expect(last * DEG).toBeLessThan(cfg.driftOffsetDeg * 0.2);
    run(s, 2, { throttle: 1 });
    expect(s.recovering).toBe(false);
  });
});

describe("offset drift: braking", () => {
  it("tightens the arc instead of cancelling the drift", () => {
    const loose = arcRadius(run(drifting(), 1, { throttle: 1, drift: true }), 0.3, {
      throttle: 1,
      drift: true,
    });
    const s = run(drifting(), 1, { throttle: 1, drift: true });
    const braking = arcRadius(s, 0.3, { throttle: 1, drift: true, brake: 1 });
    expect(s.driftDir).toBe(1);
    expect(braking).toBeLessThan(loose * 0.85);
  });

  it("slows the kart only gently, so a dab of brake keeps the drift alive", () => {
    const s = run(drifting(), 1, { throttle: 1, drift: true });
    const before = s.speed;
    run(s, 0.25, { drift: true, brake: 1 });
    expect(s.driftDir).toBe(1);
    expect(s.speed).toBeGreaterThan(before - cfg.brake * 0.25 * 0.5);
  });
});

describe("offset drift: countersteer spin-out", () => {
  it("spins out after sustained hard countersteer", () => {
    const s = drifting();
    const before = s.speed;
    run(s, cfg.spinOutAfterSec + 0.2, { throttle: 1, drift: true, steer: -1 });
    expect(s.driftDir).toBe(0);
    expect(s.spinTime).toBeGreaterThan(0);
    expect(s.speed).toBeLessThan(before * 0.75);
  });

  it("never spins out if you ease off now and then", () => {
    const s = drifting();
    for (let i = 0; i < 6; i++) {
      run(s, cfg.spinOutAfterSec * 0.8, { throttle: 1, drift: true, steer: -1 });
      run(s, 0.1, { throttle: 1, drift: true, steer: 0 });
    }
    expect(s.driftDir).toBe(1);
    expect(s.spinTime).toBe(0);
  });

  it("can be turned off", () => {
    const off = { ...cfg, spinOutAfterSec: 0 };
    const s = run(drifting(off), 4, { throttle: 1, drift: true, steer: -1 }, off);
    expect(s.driftDir).toBe(1);
  });
});
