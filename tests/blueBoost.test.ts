import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { activateBlue, blueSeconds } from "../src/items/boosts";
import type { ItemsConfig } from "../src/items/config";
import { createKartState, stepKart, type KartConfig, type KartState } from "../src/vehicles/kart";
import { ZIP, startZipper } from "../src/vehicles/zipper";

/**
 * Blue balloon calibration: every scenario starts identically (flat ground, cruising
 * at normal top speed, the balloon fired at t = 0) and only the inputs differ.
 * Run with BLUE_REPORT=1 and --disableConsoleIntercept to print the table.
 */
const cfg: KartConfig = { ...tuning.vehicle };
const items = tuning.items as ItemsConfig;
const dt = 1 / 120;
const top = cfg.topSpeed;
const SECONDS = 3;

type Plan = (t: number, s: KartState) => Partial<InputState>;
interface Scenario {
  name: string;
  /** Throttle at the moment the balloon fires. */
  atFire: number;
  plan: Plan;
  bananas?: number;
  /** Something before t = 0 (e.g. a zipper already running). */
  before?: (s: KartState) => void;
}

const resumeAt =
  (sec: number): Plan =>
  (t) => ({ throttle: t >= sec ? 1 : 0 });
const atRainbow: Plan = (_t, s) => ({ throttle: s.zipPhase === ZIP.ACTIVE ? 0 : 1 });
const drift =
  (from: (level: number) => number, level: number): Plan =>
  (t, s) => ({ ...atRainbow(t, s), drift: t >= from(level), steer: t >= from(level) ? 0.6 : 0 });

const scenarios = (level: number): Scenario[] => [
  { name: "1 hold throttle", atFire: 1, plan: () => ({ throttle: 1 }) },
  { name: "2 stay released", atFire: 0, plan: () => ({ throttle: 0 }) },
  { name: "3 resume 0.2s", atFire: 0, plan: resumeAt(0.2) },
  { name: "4 resume 0.4s", atFire: 0, plan: resumeAt(0.4) },
  { name: "5 resume 0.6s", atFire: 0, plan: resumeAt(0.6) },
  { name: "6 resume at rainbow", atFire: 0, plan: atRainbow },
  { name: "7 drift at once", atFire: 0, plan: drift(() => 0, level) },
  { name: "8 drift after push", atFire: 0, plan: drift((l) => blueSeconds(l, items), level) },
  { name: "9 rainbow, 10 bananas", atFire: 0, plan: atRainbow, bananas: 10 },
  {
    name: "10 during a zipper",
    atFire: 0,
    plan: atRainbow,
    // An enhanced zipper started 0.5 s earlier is still running when the balloon fires.
    before: (s) => {
      startZipper(s, 0, cfg);
      for (let t = 0; t < 0.5; t += dt) stepKart(s, NEUTRAL, cfg, dt);
    },
  },
];

interface Result {
  name: string;
  initial: number;
  peak: number;
  tPeak: number;
  v: number[]; // at 0.5, 1, 1.5, 2, 3 s
  d: number[]; // at 1, 2, 3 s
  timer: number; // how long the boost pushed, s
  trace: number[]; // speed every 0.05 s
}

const MARKS_V = [0.5, 1, 1.5, 2, 3];
const MARKS_D = [1, 2, 3];

function run(level: number | null, sc: Scenario): Result {
  const s = createKartState();
  s.speed = top;
  s.bananas = sc.bananas ?? 0;
  sc.before?.(s);
  const initial = s.speed;
  if (level !== null) activateBlue(s, level, sc.atFire, cfg, items);
  const r: Result = {
    name: sc.name,
    initial,
    peak: s.speed,
    tPeak: 0,
    v: [],
    d: [],
    timer: 0,
    trace: [],
  };
  let dist = 0;
  const steps = Math.round(SECONDS / dt);
  for (let i = 1; i <= steps; i++) {
    const t = i * dt;
    const pushing = s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING;
    const x0 = s.x;
    const z0 = s.z;
    stepKart(s, { ...NEUTRAL, ...sc.plan(t - dt, s) }, cfg, dt);
    if (pushing) r.timer += dt;
    dist += Math.hypot(s.x - x0, s.z - z0);
    if (s.speed > r.peak + 1e-9) {
      r.peak = s.speed;
      r.tPeak = t;
    }
    for (const [k, m] of MARKS_V.entries()) if (i === Math.round(m / dt)) r.v[k] = s.speed;
    for (const [k, m] of MARKS_D.entries()) if (i === Math.round(m / dt)) r.d[k] = dist;
    if (i % 6 === 0) r.trace.push(s.speed);
  }
  return r;
}

const baseline = run(null, { name: "no boost", atFire: 1, plan: () => ({ throttle: 1 }) });
const LEVELS = [1, 2, 3];
const table = LEVELS.map((level) => ({
  level,
  rows: scenarios(level).map((sc) => run(level, sc)),
}));
const get = (level: number, prefix: string) =>
  table.find((t) => t.level === level)!.rows.find((r) => r.name.startsWith(prefix))!;

const env = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env;
if (env?.BLUE_REPORT) {
  const f = (n: number, w = 6, d = 1) => n.toFixed(d).padStart(w);
  const lines = [`top speed ${top} m/s; no boost: d3 = ${baseline.d[2]!.toFixed(1)} m`];
  for (const { level, rows } of table) {
    lines.push(
      `\nBLUE ${level} (timer ${blueSeconds(level, items)} s)`,
      "scenario                init  peak  tPk  v0.5  v1.0  v1.5  v2.0  v3.0    d1    d2    d3 timer  gain",
    );
    for (const r of rows)
      lines.push(
        r.name.padEnd(22) +
          f(r.initial) +
          f(r.peak) +
          f(r.tPeak, 5, 2) +
          r.v.map((v) => f(v)).join("") +
          r.d.map((v) => f(v)).join("") +
          f(r.timer, 6, 2) +
          f(r.d[2]! - baseline.d[2]!),
      );
  }
  console.log(lines.join("\n"));
  if (env.BLUE_TRACES) console.log(JSON.stringify({ baseline: baseline.trace, table }));
}

describe("blue balloon boosts", () => {
  it("push for exactly their level's timer, from the moment they fire", () => {
    for (const level of LEVELS) {
      for (const prefix of ["1 ", "2 ", "6 "])
        expect(get(level, prefix).timer).toBeCloseTo(blueSeconds(level, items), 1);
    }
    expect(items.blue1Sec).toBeCloseTo(0.58, 2);
    expect(items.blue2Sec).toBeCloseTo(0.92, 2);
    expect(items.blue3Sec).toBeCloseTo(1.25, 2);
  });

  it("share one acceleration model: every level accelerates identically at first", () => {
    for (const prefix of ["1 ", "2 "]) {
      const a = get(1, prefix).trace.slice(0, 5);
      for (const level of [2, 3]) expect(get(level, prefix).trace.slice(0, 5)).toEqual(a);
    }
  });

  it("accelerate continuously, never jumping straight to the boosted speed", () => {
    for (const level of LEVELS) expect(get(level, "2 ").tPeak).toBeGreaterThan(0.3);
  });

  it("are worth more the longer the timer", () => {
    for (const prefix of ["1 ", "2 ", "6 "]) {
      expect(get(2, prefix).d[2]!).toBeGreaterThan(get(1, prefix).d[2]!);
      expect(get(3, prefix).d[2]!).toBeGreaterThan(get(2, prefix).d[2]!);
    }
  });

  it("reward releasing the throttle, and resuming at the rainbow most of all", () => {
    for (const level of LEVELS) {
      const best = get(level, "6 ").d[2]!;
      expect(get(level, "2 ").d[2]!).toBeGreaterThan(get(level, "1 ").d[2]!);
      for (const p of ["1 ", "2 ", "3 ", "4 ", "5 "])
        expect(best).toBeGreaterThanOrEqual(get(level, p).d[2]! - 1e-6);
    }
  });

  it("make waiting before drifting keep more of the boost than drifting at once", () => {
    for (const level of LEVELS)
      expect(get(level, "8 ").d[2]!).toBeGreaterThan(get(level, "7 ").d[2]!);
  });

  it("don't scale with bananas while pushing, but help afterwards", () => {
    for (const level of LEVELS) {
      expect(get(level, "9 ").peak).toBeCloseTo(get(level, "6 ").peak, 6);
      expect(get(level, "9 ").v[4]!).toBeGreaterThan(get(level, "6 ").v[4]!);
    }
  });

  it("replace an active zipper's timer instead of stacking", () => {
    for (const level of LEVELS) {
      const r = get(level, "10 ");
      expect(r.timer).toBeCloseTo(blueSeconds(level, items), 1);
      // One boost's worth of push: never faster than the single boost's ceiling.
      expect(r.peak).toBeLessThanOrEqual(top * cfg.zipEnhancedMult + 1e-6);
    }
  });

  it("can keep the longer timer instead, if boostOverlap is 1", () => {
    const s = createKartState();
    s.speed = top;
    const keep = { ...cfg, boostOverlap: 1 };
    startZipper(s, 0, keep);
    expect(activateBlue(s, 1, 0, keep, items)).toBe(false);
    expect(s.zipTotal).toBeCloseTo(cfg.zipEnhancedSec, 6);
    expect(activateBlue(s, 1, 0, cfg, items)).toBe(true);
    expect(s.zipTotal).toBeCloseTo(items.blue1Sec, 6);
  });

  it("end at a severe crash, like a zipper", () => {
    const s = createKartState();
    s.speed = top;
    activateBlue(s, 3, 0, cfg, items);
    for (let t = 0; t < 0.4; t += dt) stepKart(s, NEUTRAL, cfg, dt);
    s.zipCrashed = true;
    stepKart(s, NEUTRAL, cfg, dt);
    expect(s.zipPhase).toBe(ZIP.RECOVERY);
  });
});
