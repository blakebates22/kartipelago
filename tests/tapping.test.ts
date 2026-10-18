import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { createKartState, stepKart, type KartConfig, type KartState } from "../src/vehicles/kart";

const cfg: KartConfig = { ...tuning.vehicle };
const dt = 1 / 120;

function hold(s: KartState, seconds: number, input: Partial<InputState>) {
  for (let t = 0; t < seconds; t += dt) stepKart(s, { ...NEUTRAL, ...input }, cfg, dt);
  return s;
}

/** Tap the throttle at `hz` taps per second, down for `duty` of each cycle. */
function tap(
  s: KartState,
  seconds: number,
  hz: number,
  duty = 0.6,
  extra: Partial<InputState> = {},
) {
  const period = 1 / hz;
  for (let t = 0; t < seconds; t += dt) {
    const down = t % period < period * duty;
    stepKart(s, { ...NEUTRAL, ...extra, throttle: down ? 1 : 0 }, cfg, dt);
  }
  return s;
}

/** Up to normal top speed by holding the throttle. */
const cruising = () => hold(createKartState(), 3, { throttle: 1 });

describe("throttle tapping", () => {
  it("holding the throttle gives normal top speed and no charge", () => {
    const s = cruising();
    expect(s.speed).toBeCloseTo(cfg.topSpeed);
    expect(s.tapCharge).toBe(0);
  });

  it("tapping at a moderate rhythm builds up to about 10% more top speed", () => {
    const s = tap(cruising(), 3, 4);
    expect(s.tapCharge).toBeCloseTo(1);
    expect(s.speed).toBeGreaterThan(cfg.topSpeed * (1 + cfg.tapBonus) * 0.97);
    expect(s.speed).toBeLessThanOrEqual(cfg.topSpeed * (1 + cfg.tapBonus) + 1e-9);
  });

  it("doesn't reward mashing too fast or tapping too slowly", () => {
    expect(tap(cruising(), 3, 12).tapCharge).toBe(0);
    expect(tap(cruising(), 3, 1.5, 0.8).tapCharge).toBe(0);
  });

  it("bleeds the extra speed off gradually after you stop tapping", () => {
    const s = tap(cruising(), 3, 4);
    const fast = s.speed;
    hold(s, 0.5, { throttle: 1 });
    expect(s.speed).toBeGreaterThan(cfg.topSpeed + (fast - cfg.topSpeed) * 0.4);
    hold(s, 3, { throttle: 1 });
    expect(s.speed).toBeCloseTo(cfg.topSpeed);
  });

  it("stacks with the drift speed bonus", () => {
    const drift = (s: KartState) => hold(s, dt, { throttle: 1, steer: 1, drift: true });
    const held = hold(drift(cruising()), 3, { throttle: 1, drift: true });
    const tapped = tap(drift(cruising()), 3, 4, 0.6, { drift: true });
    expect(held.driftDir).toBe(1);
    expect(tapped.driftDir).toBe(1);
    expect(tapped.speed).toBeGreaterThan(held.speed * 1.07);
  });
});
