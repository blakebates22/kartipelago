/**
 * The sharp turn (drift + brake + steer into the drift), on the real tuning.json kart,
 * on flat ground. Every case enters at the same speed (top speed, 22 m/s), so the arcs
 * and turn rates compare like for like. The numbers are printed as a table (run with
 * --disableConsoleIntercept to see it). See docs/sharp-turn.md.
 */
import { describe, expect, it } from "vitest";
import type { InputState } from "../src/core/input";
import { tuning } from "../src/core/tuning";
import {
  createKartState,
  stepKart,
  wrapAngle,
  type KartConfig,
  type KartState,
} from "../src/vehicles/kart";

const base = tuning.vehicle as KartConfig;
const DEG = 180 / Math.PI;

type Phase = { sec: number; input: Partial<InputState> };

/** Run phases of held input at `hz`; measure the last phase (arc radius, path turn rate, speed). */
function run(phases: Phase[], cfg: KartConfig = base, hz = 120) {
  const dt = 1 / hz;
  const s = createKartState(0, 0, 0);
  s.speed = cfg.topSpeed;
  let measure = { dist: 0, turn: 0, sec: 0, speedIn: 0, maxRoll: 0, maxSharp: 0 };
  const trace: KartState[] = [];
  for (let k = 0; k < phases.length; k++) {
    const ph = phases[k]!;
    const last = k === phases.length - 1;
    if (last) measure = { dist: 0, turn: 0, sec: 0, speedIn: s.speed, maxRoll: 0, maxSharp: 0 };
    const input: InputState = {
      throttle: 1,
      brake: 0,
      steer: 0,
      drift: false,
      item: false,
      ...ph.input,
    };
    for (let i = 0; i < Math.round(ph.sec * hz); i++) {
      const x = s.x;
      const z = s.z;
      const path = s.velAngle;
      stepKart(s, input, cfg, dt);
      for (const v of [s.x, s.z, s.heading, s.speed, s.sharpRoll])
        expect(Number.isFinite(v)).toBe(true);
      if (last) {
        measure.dist += Math.hypot(s.x - x, s.z - z);
        measure.turn += Math.abs(wrapAngle(s.velAngle - path));
        measure.sec += dt;
        measure.maxRoll = Math.max(measure.maxRoll, Math.abs(s.sharpRoll));
        measure.maxSharp = Math.max(measure.maxSharp, s.sharp);
      }
      trace.push({ ...s });
    }
  }
  return {
    s,
    trace,
    radius: measure.dist / Math.max(1e-6, measure.turn),
    yaw: (measure.turn / measure.sec) * DEG,
    speedIn: measure.speedIn,
    speedOut: s.speed,
    maxRollDeg: measure.maxRoll * DEG,
    maxSharp: measure.maxSharp,
  };
}

// Full right, as a drift starts: press drift with the stick over, hold half a second so
// the slide settles, then the case's input for the measured stretch.
const R = 1;
const enterDrift: Phase[] = [{ sec: 0.6, input: { drift: true, steer: R } }];
const MEASURE = 0.4;

const cases = {
  "1 steer": run([
    { sec: 0.6, input: { steer: R } },
    { sec: MEASURE, input: { steer: R } },
  ]),
  "2 brake + steer": run([
    { sec: 0.6, input: { steer: R } },
    { sec: MEASURE, input: { throttle: 0, brake: 1, steer: R } },
  ]),
  "3 drift": run([...enterDrift, { sec: MEASURE, input: { drift: true, steer: R } }]),
  "4 drift + brake (sharp)": run([
    ...enterDrift,
    { sec: MEASURE, input: { drift: true, brake: 1, steer: R } },
  ]),
  "5 sharp, half stick": run([
    ...enterDrift,
    { sec: MEASURE, input: { drift: true, brake: 1, steer: 0.5 } },
  ]),
  "6 drift + brake, countersteer": run([
    ...enterDrift,
    { sec: MEASURE, input: { drift: true, brake: 1, steer: -R } },
  ]),
  "7 sharp, then brake let go": run([
    ...enterDrift,
    { sec: 0.3, input: { drift: true, brake: 1, steer: R } },
    { sec: MEASURE, input: { drift: true, steer: R } },
  ]),
  "8 sharp held 3 s": run([...enterDrift, { sec: 3, input: { drift: true, brake: 1, steer: R } }]),
};

describe("the sharp turn (drift + brake + steer)", () => {
  it("prints the eight cases", () => {
    const rows = Object.entries(cases).map(([name, c]) => ({
      case: name,
      "entry m/s": +c.speedIn.toFixed(1),
      "exit m/s": +c.speedOut.toFixed(1),
      "arc m": +c.radius.toFixed(1),
      "turn °/s": +c.yaw.toFixed(0),
      "roll °": +c.maxRollDeg.toFixed(1),
    }));
    console.table(rows);
  });

  it("turns much tighter than a plain drift, but costs speed", () => {
    const drift = cases["3 drift"];
    const sharp = cases["4 drift + brake (sharp)"];
    expect(sharp.radius).toBeLessThan(drift.radius * 0.6);
    expect(sharp.yaw).toBeGreaterThan(drift.yaw * 1.4);
    expect(sharp.speedOut).toBeLessThan(drift.speedOut - 3);
    // Never tighter than the floor, so it can't pivot on the spot.
    expect(sharp.radius).toBeGreaterThan(base.sharpMinRadius * 0.9);
  });

  it("braking without a drift steers harder than steering alone", () => {
    expect(cases["2 brake + steer"].yaw).toBeGreaterThan(cases["1 steer"].yaw * 1.2);
  });

  it("half stick gives a sharp turn between a drift and a full one", () => {
    const half = cases["5 sharp, half stick"];
    expect(half.radius).toBeLessThan(cases["3 drift"].radius);
    expect(half.radius).toBeGreaterThan(cases["4 drift + brake (sharp)"].radius);
  });

  it("rolls onto the outside wheels, up to sharpLeanDeg and no further", () => {
    const sharp = cases["4 drift + brake (sharp)"];
    expect(sharp.maxRollDeg).toBeGreaterThan(base.sharpLeanDeg * 0.9);
    expect(sharp.maxRollDeg).toBeLessThanOrEqual(base.sharpLeanDeg + 1e-6);
    // Turning right rolls onto the left wheels: negative in three.js's sense.
    expect(Math.min(...sharp.trace.map((t) => t.sharpRoll))).toBeLessThan(0);
    expect(Math.max(...sharp.trace.map((t) => t.sharpRoll))).toBeLessThanOrEqual(0);
    // A plain drift doesn't roll.
    expect(cases["3 drift"].maxRollDeg).toBe(0);
  });

  it("countersteering with the brake is no sharp turn, and no spin in the moment", () => {
    const c = cases["6 drift + brake, countersteer"];
    expect(c.maxSharp).toBe(0);
    expect(c.maxRollDeg).toBe(0);
    expect(c.trace.every((t) => t.spinTime === 0)).toBe(true);
  });

  it("letting go of the brake eases the turn and the roll away; the drift carries on", () => {
    const c = cases["7 sharp, then brake let go"];
    expect(c.s.driftDir).toBe(1);
    expect(c.s.sharp).toBeLessThan(0.1);
    // The roll follows the hold down, so it trails a little behind it.
    expect(Math.abs(c.s.sharpRoll) * DEG).toBeLessThan(5);
  });

  it("held on, it carves a tight drift on two wheels at its holding speed, as long as you like", () => {
    const c = cases["8 sharp held 3 s"];
    const hold = base.topSpeed * base.sharpHoldSpeed;
    expect(c.s.driftDir).toBe(1);
    expect(Math.abs(c.s.speed - hold)).toBeLessThan(0.3);
    expect(c.s.sharp).toBeGreaterThan(0.95);
    expect(Math.abs(c.s.sharpRoll) * DEG).toBeGreaterThan(base.sharpLeanDeg * 0.95);
    expect(c.radius).toBeLessThan(cases["3 drift"].radius / 2.5);
    expect(c.trace.every((t) => t.spinTime === 0)).toBe(true);
  });

  it("lifting off the throttle in it still slows you (it holds speed, it doesn't add it)", () => {
    const c = run([
      ...enterDrift,
      { sec: 2, input: { drift: true, brake: 1, steer: R, throttle: 0 } },
    ]);
    expect(c.s.speed).toBeLessThan(base.topSpeed * base.sharpHoldSpeed - 5);
  });

  it("is the same at any physics rate", () => {
    const phases: Phase[] = [
      ...enterDrift,
      { sec: 0.5, input: { drift: true, brake: 1, steer: R } },
    ];
    const at = [60, 120, 240].map((hz) => run(phases, base, hz).s);
    for (const s of at.slice(1)) {
      expect(Math.abs(wrapAngle(s.heading - at[0]!.heading)) * DEG).toBeLessThan(2);
      expect(Math.abs(s.speed - at[0]!.speed)).toBeLessThan(0.3);
      expect(Math.hypot(s.x - at[0]!.x, s.z - at[0]!.z)).toBeLessThan(0.3);
      expect(Math.abs(s.sharpRoll - at[0]!.sharpRoll) * DEG).toBeLessThan(1.5);
    }
  });

  it("does nothing in the air, and can be switched off", () => {
    const off = run([...enterDrift, { sec: MEASURE, input: { drift: true, brake: 1, steer: R } }], {
      ...base,
      sharpTurn: false,
    });
    expect(off.maxSharp).toBe(0);
    expect(off.maxRollDeg).toBe(0);
    const s = createKartState();
    s.speed = 20;
    s.driftDir = 1;
    s.grounded = false;
    const input: InputState = { throttle: 1, brake: 1, steer: 1, drift: true, item: false };
    for (let i = 0; i < 60; i++) {
      s.grounded = false;
      stepKart(s, input, base, 1 / 120);
    }
    expect(s.sharp).toBe(0);
    expect(s.sharpRoll).toBe(0);
  });
});
