import { describe, expect, it } from "vitest";
import { mergeReadings, NEUTRAL, rampKeySteer, shapeStick } from "../src/core/input";

const cfg = {
  stickDeadzone: 0.15,
  stickCurve: 1,
  keySteerRate: 5,
  keySteerReturn: 10,
  driftKeyRate: 3,
  driftKeyReturn: 6,
  driftKeyReverse: 14,
};

describe("shapeStick", () => {
  it("ignores small movements inside the deadzone", () => {
    expect(shapeStick(0.1, 0.15, 1)).toBe(0);
    expect(shapeStick(-0.15, 0.15, 1)).toBe(0);
  });

  it("still reaches full lock at the edge", () => {
    expect(shapeStick(1, 0.15, 1)).toBeCloseTo(1);
    expect(shapeStick(-1, 0.15, 2)).toBeCloseTo(-1);
  });

  it("starts from zero just outside the deadzone instead of jumping", () => {
    expect(shapeStick(0.16, 0.15, 1)).toBeLessThan(0.02);
  });
});

describe("rampKeySteer", () => {
  it("ramps toward full lock rather than snapping", () => {
    const after = rampKeySteer(0, 1, 0.1, cfg);
    expect(after).toBeCloseTo(0.5);
    expect(rampKeySteer(after, 1, 0.1, cfg)).toBe(1);
  });

  it("recentres faster than it turns in", () => {
    expect(rampKeySteer(1, 0, 0.05, cfg)).toBeCloseTo(0.5);
  });

  it("swings through centre at the return rate when switching direction", () => {
    expect(rampKeySteer(0.5, -1, 0.05, cfg)).toBeCloseTo(0);
  });
});

describe("rampKeySteer while drifting", () => {
  it("builds more slowly, so a short tap is a small nudge", () => {
    expect(rampKeySteer(0, 1, 0.1, cfg, true)).toBeCloseTo(0.3);
    expect(rampKeySteer(0, 1, 0.1, cfg, false)).toBeCloseTo(0.5);
  });

  it("eases back to centre at its own rate when released", () => {
    expect(rampKeySteer(0.6, 0, 0.05, cfg, true)).toBeCloseTo(0.3);
  });

  it("swings through centre quickly when you switch direction", () => {
    expect(rampKeySteer(0.7, -1, 0.05, cfg, true)).toBeCloseTo(0);
  });
});

describe("mergeReadings", () => {
  it("takes the stronger steering input and ORs buttons", () => {
    const keys = { ...NEUTRAL, steer: 0.3, drift: true };
    const pad = { ...NEUTRAL, steer: -0.8, throttle: 0.6 };
    expect(mergeReadings(keys, pad)).toEqual({ throttle: 0.6, brake: 0, steer: -0.8, drift: true });
  });
});
