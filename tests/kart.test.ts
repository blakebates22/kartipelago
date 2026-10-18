import { describe, expect, it } from "vitest";
import { NEUTRAL, type InputState } from "../src/core/input";
import {
  createKartState,
  slipAngle,
  stepKart,
  type KartConfig,
  type KartState,
} from "../src/vehicles/kart";

const cfg: KartConfig = {
  accel: 20,
  brake: 40,
  reverseAccel: 10,
  topSpeed: 20,
  reverseSpeed: 6,
  drag: 5,
  turnRate: 2.5,
  turnRateAtTop: 1.5,
  turnFullSpeed: 4,
  grip: 18,
  driftTurnTight: 1.2,
  driftTurnNeutral: 0.9,
  driftTurnCounter: -0.4,
  driftNoseTightDeg: 40,
  driftNoseCounterDeg: 12,
  driftNoseRate: 8,
  driftModel: 0,
  driftSteerSmooth: 0.06,
  driftRadiusNeutral: 33,
  driftRadiusTight: 20,
  driftRadiusCounter: 120,
  driftInCurve: 2,
  driftCounterCurve: 1.3,
  driftOffsetDeg: 40,
  driftOffsetRate: 4,
  driftOffsetReturnRate: 4,
  driftRecoverSteer: 1,
  driftBrakeTighten: 0.35,
  driftBrakeDecel: 0.35,
  spinThreshold: 0.6,
  spinOutAfterSec: 1.5,
  spinSec: 0.8,
  spinSpeedKeep: 0.5,
  spinSteer: 0.3,
  driftMinSpeed: 8,
  driftStartSteer: 0.3,
  driftStartWindow: 0.25,
  driftSpeedMult: 1.15,
  driftRecoverRate: 5,
  driftRecoverTurn: 0.25,
  padSpeedMult: 1.35,
  padBoostSec: 1.2,
  airSteer: 0.12,
  slopeSpeed: 12,
};
const dt = 1 / 120;

function run(seconds: number, input: Partial<InputState>, s = createKartState()) {
  const held = { ...NEUTRAL, ...input };
  for (let t = 0; t < seconds; t += dt) stepKart(s, held, cfg, dt);
  return s;
}

/** Up to top speed, then start a right drift. */
function drifting(): KartState {
  const s = run(2, { throttle: 1 });
  return run(0.1, { throttle: 1, steer: 1, drift: true }, s);
}

// These tests cover the legacy drift model (driftModel 0); the offset model has its own
// tests in drift.test.ts.
describe("driving", () => {
  it("accelerates to top speed and no further", () => {
    const s = run(3, { throttle: 1 });
    expect(s.speed).toBe(cfg.topSpeed);
    expect(s.z).toBeGreaterThan(0);
  });

  it("coasts to a stop with no input", () => {
    const s = run(6, {}, run(2, { throttle: 1 }));
    expect(s.speed).toBe(0);
  });

  it("brakes to a stop, then reverses", () => {
    const s = run(0.4, { brake: 1 }, run(2, { throttle: 1 }));
    expect(s.speed).toBeGreaterThanOrEqual(0);
    run(2, { brake: 1 }, s);
    expect(s.speed).toBe(-cfg.reverseSpeed);
  });

  it("can't turn on the spot", () => {
    const s = run(1, { steer: 1 });
    expect(s.heading).toBe(0);
  });

  it("steering right moves the kart to its right", () => {
    // Facing +Z with the camera behind, the driver's right is -X.
    const s = run(1, { throttle: 1, steer: 1 });
    expect(s.heading).toBeLessThan(0);
    expect(s.x).toBeLessThan(0);
  });

  it("flips steering when reversing", () => {
    const s = run(1, { brake: 1, steer: 1 });
    expect(s.speed).toBeLessThan(0);
    expect(s.heading).toBeGreaterThan(0);
  });

  it("is grippy: slip settles near zero once you straighten up", () => {
    const s = run(1, { throttle: 1, steer: 1 }, run(1, { throttle: 1 }));
    expect(Math.abs(slipAngle(s))).toBeLessThan(0.2);
    run(0.5, { throttle: 1 }, s);
    expect(Math.abs(slipAngle(s))).toBeLessThan(0.01);
  });
});

describe("drifting", () => {
  it("needs steering to start", () => {
    const s = run(0.5, { throttle: 1, drift: true }, run(2, { throttle: 1 }));
    expect(s.driftDir).toBe(0);
  });

  it("needs a fresh press, not a button held from long ago", () => {
    const s = run(1, { throttle: 1, drift: true }, run(2, { throttle: 1 }));
    run(0.2, { throttle: 1, drift: true, steer: 1 }, s);
    expect(s.driftDir).toBe(0);
  });

  it("can't start when slow", () => {
    const s = run(0.3, { throttle: 1, steer: 1, drift: true });
    expect(s.driftDir).toBe(0);
  });

  it("locks direction: countersteer doesn't flip it to a left drift", () => {
    const s = drifting();
    expect(s.driftDir).toBe(1);
    run(0.5, { throttle: 1, steer: -1, drift: true }, s);
    expect(s.driftDir).toBe(1);
  });

  it("drift right, countersteer left: the path bends left", () => {
    const s = drifting();
    const before = s.velAngle;
    run(1, { throttle: 1, steer: -1, drift: true }, s);
    // Heading/velAngle go up when turning left (see the convention in kart.ts).
    expect(s.velAngle).toBeGreaterThan(before);
  });

  it("...while the nose still points right of travel", () => {
    const s = run(1, { throttle: 1, steer: -1, drift: true }, drifting());
    const deg = (slipAngle(s) * 180) / Math.PI;
    expect(deg).toBeCloseTo(-cfg.driftNoseCounterDeg, 0);
  });

  it("steering into the drift curves harder and swings the nose deeper", () => {
    const tight = run(1, { throttle: 1, steer: 1, drift: true }, drifting());
    const neutral = run(1, { throttle: 1, steer: 0, drift: true }, drifting());
    expect(tight.velAngle).toBeLessThan(neutral.velAngle);
    expect(neutral.velAngle).toBeLessThan(0); // centred stick still curves right
    expect((slipAngle(tight) * 180) / Math.PI).toBeCloseTo(-cfg.driftNoseTightDeg, 0);
  });

  it("eases out of a drift instead of snapping, mostly keeping its line", () => {
    const s = run(1, { throttle: 1, steer: 1, drift: true }, drifting());
    const travel = s.velAngle;
    const slipBefore = Math.abs(slipAngle(s));
    run(dt, { throttle: 1 }, s);
    // One step after release: still most of the slide angle left (no snap)...
    expect(Math.abs(slipAngle(s))).toBeGreaterThan(slipBefore * 0.9);
    run(1.5, { throttle: 1 }, s);
    // ...then it's gone, and the path turned by only part of the old slide angle.
    expect(Math.abs(slipAngle(s))).toBeLessThan(0.02);
    expect(Math.abs(s.velAngle - travel)).toBeLessThan(slipBefore * 0.4);
  });

  it("goes back to grippy driving after easing out", () => {
    const s = run(1, { throttle: 1, steer: 1, drift: true }, drifting());
    run(2, { throttle: 1 }, s);
    expect(s.recovering).toBe(false);
  });

  it("is faster while drifting, then settles back after", () => {
    const s = run(2, { throttle: 1, steer: 0, drift: true }, drifting());
    expect(s.driftDir).toBe(1);
    expect(s.speed).toBeCloseTo(cfg.topSpeed * cfg.driftSpeedMult);
    run(dt, { throttle: 1 }, s);
    expect(s.driftDir).toBe(0);
    expect(s.speed).toBeGreaterThan(cfg.topSpeed);
    run(3, { throttle: 1 }, s);
    expect(s.speed).toBe(cfg.topSpeed);
  });

  it("gives nothing extra just for releasing", () => {
    const s = run(0.2, { throttle: 1, steer: 1, drift: true }, drifting());
    const before = s.speed;
    run(dt, { throttle: 1 }, s);
    expect(s.speed).toBeLessThanOrEqual(before + cfg.accel * dt);
  });

  it("braking cancels the drift", () => {
    const s = drifting();
    run(0.1, { brake: 1, drift: true }, s);
    expect(s.driftDir).toBe(0);
  });
});
