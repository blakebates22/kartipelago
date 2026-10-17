import { describe, expect, it } from "vitest";
import { NEUTRAL } from "../src/core/input";
import { createKartState, slipAngle, stepKart, type KartConfig } from "../src/vehicles/kart";

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
};
const dt = 1 / 120;

function run(seconds: number, input: Partial<typeof NEUTRAL>, s = createKartState()) {
  const held = { ...NEUTRAL, ...input };
  for (let t = 0; t < seconds; t += dt) stepKart(s, held, cfg, dt);
  return s;
}

describe("stepKart", () => {
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
