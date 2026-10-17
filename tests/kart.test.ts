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
  driftGrip: 4,
  driftTurnTight: 2.6,
  driftTurnLoose: 0.8,
  driftMinSpeed: 8,
  driftStartSteer: 0.3,
  driftStartWindow: 0.25,
  driftSpeedMult: 1.15,
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

  it("locks direction: full countersteer still turns the drift's way", () => {
    const s = drifting();
    expect(s.driftDir).toBe(1);
    const before = s.heading;
    run(0.5, { throttle: 1, steer: -1, drift: true }, s);
    expect(s.driftDir).toBe(1);
    expect(s.heading).toBeLessThan(before); // still turning right
  });

  it("countersteer widens the arc, steering in tightens it", () => {
    const tight = run(1, { throttle: 1, steer: 1, drift: true }, drifting());
    const loose = run(1, { throttle: 1, steer: -1, drift: true }, drifting());
    const turned = (s: KartState) => Math.abs(s.velAngle);
    expect(turned(tight)).toBeGreaterThan(turned(loose) * 2);
  });

  it("slides: much more slip than a normal grippy turn", () => {
    const normal = run(1, { throttle: 1, steer: 1 }, run(2, { throttle: 1 }));
    const drift = run(1, { throttle: 1, steer: 1, drift: true }, drifting());
    expect(Math.abs(slipAngle(drift))).toBeGreaterThan(Math.abs(slipAngle(normal)) * 3);
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
