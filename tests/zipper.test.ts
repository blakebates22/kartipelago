import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { createTrackGround } from "../src/physics/ground";
import { stepImpacts, stepWalls } from "../src/physics/walls";
import { createKartState, stepKart, type KartConfig, type KartState } from "../src/vehicles/kart";
import { ZIP, startZipper } from "../src/vehicles/zipper";
import { buildTrack } from "../src/world/track";
import { buildZippers, enteredZipper } from "../src/world/zippers";

/**
 * Repeatable zipper measurements. Every scenario starts identically: on a long flat
 * straight, at normal top speed, touching a zipper at t = 0. Only the inputs differ.
 * Run with ZIP_REPORT=1 to print the comparison table.
 */
const cfg: KartConfig = { ...tuning.vehicle };
const top = cfg.topSpeed;
const dt = 1 / 120;
const walls = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
const track = buildTrack(
  {
    name: "straight",
    defaultWidth: 20,
    points: [
      { x: 0, z: -2000 },
      { x: 0, z: 0 },
      { x: 0, z: 2000 },
      { x: 600, z: 2000 },
      { x: 600, z: -2000 },
    ],
  },
  2,
);
const ground = createTrackGround(track);

type Plan = (t: number, s: KartState) => Partial<InputState>;
interface Scenario {
  name: string;
  zipper: boolean;
  /** Throttle at the moment of contact. */
  contactThrottle: number;
  plan: Plan;
  walls?: boolean;
  start?: (s: KartState) => void;
  event?: (t: number, s: KartState) => void;
}

const released =
  (pressAt: number): Plan =>
  (t) => ({ throttle: t >= pressAt ? 1 : 0 });
const atRainbow: Plan = (_t, s) => ({
  throttle:
    s.zipPhase === ZIP.ENDING || s.zipPhase === ZIP.RECOVERY || s.zipPhase === ZIP.NORMAL ? 1 : 0,
});
const drift =
  (from: number): Plan =>
  (t, s) => ({ ...atRainbow(t, s), drift: t >= from, steer: t >= from ? 0.6 : 0 });

const SCENARIOS: Scenario[] = [
  { name: "1 no zipper", zipper: false, contactThrottle: 1, plan: () => ({ throttle: 1 }) },
  { name: "2 hold throttle", zipper: true, contactThrottle: 1, plan: () => ({ throttle: 1 }) },
  { name: "3 stay released", zipper: true, contactThrottle: 0, plan: () => ({ throttle: 0 }) },
  { name: "4 press 0.25s", zipper: true, contactThrottle: 0, plan: released(0.25) },
  { name: "5 press 0.5s", zipper: true, contactThrottle: 0, plan: released(0.5) },
  { name: "6 press 1.0s", zipper: true, contactThrottle: 0, plan: released(1.0) },
  { name: "7 press at rainbow", zipper: true, contactThrottle: 0, plan: atRainbow },
  { name: "8 drift at once", zipper: true, contactThrottle: 0, plan: drift(0) },
  { name: "9 drift at 1.0s", zipper: true, contactThrottle: 0, plan: drift(1.0) },
  {
    name: "10a brake 0.3s",
    zipper: true,
    contactThrottle: 0,
    plan: (t, s) => (t >= 0.5 && t < 0.8 ? { brake: 1 } : atRainbow(t, s)),
  },
  {
    name: "10b wall crash",
    zipper: true,
    contactThrottle: 0,
    plan: atRainbow,
    walls: true,
    start: (s) => (s.x = -5),
    // Knocked 35 degrees toward the wall half a second in.
    event: (t, s) => {
      if (Math.abs(t - 0.5) < dt / 2) {
        s.heading += 0.6;
        s.velAngle += 0.6;
      }
    },
  },
];

interface Result {
  peak: number;
  timeToPeak: number;
  at: number[]; // speed at 0.5, 1, 1.5, 2 s
  dist: number[]; // distance at 1, 2, 3 s
  enhancedSec: number; // time spent above the ordinary zipper's target speed
  cornerExit: number;
}

/** Drive one scenario. With `corner`, take a 90 degree bend once 70 m past the pad. */
function run(sc: Scenario, corner: boolean): Result & { s: KartState } {
  const s = createKartState(0, -150, 0);
  s.speed = top;
  sc.start?.(s);
  if (sc.zipper) startZipper(s, sc.contactThrottle, cfg);
  const r: Result = { peak: 0, timeToPeak: 0, at: [], dist: [], enhancedSec: 0, cornerExit: 0 };
  let dist = 0;
  let turned = 0;
  let cornerDone = false;
  for (let i = 0; i <= 5 * 120; i++) {
    const t = i * dt;
    for (const [k, mark] of [0.5, 1, 1.5, 2].entries())
      if (i === Math.round(mark * 120)) r.at[k] = s.speed;
    for (const [k, mark] of [1, 2, 3].entries()) if (i === Math.round(mark * 120)) r.dist[k] = dist;
    if (s.speed > r.peak + 1e-9) {
      r.peak = s.speed;
      r.timeToPeak = t;
    }
    if (s.speed > top * cfg.zipOrdinaryMult + 0.5) r.enhancedSec += dt;

    sc.event?.(t, s);
    const input = { ...NEUTRAL, ...sc.plan(t, s) };
    const inCorner = corner && !cornerDone && dist >= 70;
    if (inCorner) {
      // A right-hand bend: full lock (into the drift, if drifting).
      input.steer = s.driftDir !== 0 ? s.driftDir : 1;
    }
    const before = s.velAngle;
    const z0 = s.z;
    const x0 = s.x;
    if (sc.walls) stepImpacts(s, tuning.collision, dt);
    stepKart(s, input, cfg, dt);
    if (sc.walls) stepWalls(s, ground, walls, dt);
    dist += Math.hypot(s.x - x0, s.z - z0);
    if (inCorner) {
      turned += Math.abs(s.velAngle - before);
      if (turned >= Math.PI / 2) {
        cornerDone = true;
        r.cornerExit = s.speed;
      }
    }
  }
  return { ...r, s };
}

const results = SCENARIOS.map((sc) => {
  const straight = run(sc, false);
  const bend = run(sc, true);
  return { name: sc.name, ...straight, cornerExit: bend.cornerExit };
});
const byName = (prefix: string) => results.find((r) => r.name.startsWith(prefix))!;

if (
  (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env.ZIP_REPORT
) {
  const f = (n: number, d = 1) => n.toFixed(d).padStart(6);
  const lines = [
    `top speed ${top} m/s. speeds in m/s, distance in m`,
    "scenario             peak  t@pk  v0.5  v1.0  v1.5  v2.0    d1    d2    d3  enhS  bendX",
    ...results.map(
      (r) =>
        r.name.padEnd(18) +
        f(r.peak) +
        f(r.timeToPeak, 2) +
        r.at.map((v) => f(v)).join("") +
        r.dist.map((v) => f(v, 0)).join("") +
        f(r.enhancedSec, 2) +
        f(r.cornerExit),
    ),
  ];
  console.log(lines.join("\n"));
}

describe("zippers", () => {
  it("ordinary boost (throttle held) reaches about the ordinary multiple", () => {
    expect(byName("2 ").peak / top).toBeCloseTo(cfg.zipOrdinaryMult, 1);
  });

  it("enhanced boost (released) reaches about the enhanced multiple, quickly but not instantly", () => {
    const r = byName("3 ");
    expect(r.peak / top).toBeGreaterThan(cfg.zipEnhancedMult - 0.1);
    expect(r.timeToPeak).toBeGreaterThan(0.2);
    expect(r.timeToPeak).toBeLessThan(1.2);
  });

  it("pressing early costs more the earlier it is, without a big slowdown", () => {
    const d = (p: string) => byName(p).dist[2]!;
    expect(d("4 ")).toBeLessThan(d("5 "));
    expect(d("5 ")).toBeLessThan(d("6 "));
    expect(d("4 ")).toBeGreaterThan(d("2 "));
    // Even the earliest press still goes faster than a held-throttle zipper at 0.5 s.
    expect(byName("4 ").at[0]!).toBeGreaterThan(byName("2 ").at[0]!);
  });

  it("pressing at the rainbow is the best way out", () => {
    const best = byName("7 ").dist[2]!;
    for (const p of ["2 ", "3 ", "4 ", "5 ", "6 "])
      expect(best).toBeGreaterThan(byName(p).dist[2]!);
  });

  it("drifting late keeps more speed than drifting at once", () => {
    expect(byName("9 ").dist[2]!).toBeGreaterThan(byName("8 ").dist[2]!);
  });

  it("braking and a serious crash both cut the boost", () => {
    expect(byName("10a").dist[2]!).toBeLessThan(byName("7 ").dist[2]!);
    expect(byName("10b").dist[2]!).toBeLessThan(byName("10a").dist[2]!);
  });

  it("a zipper always beats no zipper", () => {
    for (const r of results.slice(1)) expect(r.dist[2]!).toBeGreaterThan(byName("1 ").dist[2]!);
  });

  it("the pad fires once on entry, not again while you're still on it", () => {
    const pads = buildZippers(track, [{ at: 600 }], tuning.track);
    const pad = pads[0]!;
    const kart = { x: pad.x, z: pad.z, zipOnPad: false };
    expect(enteredZipper(kart, pads)).toBe(true);
    expect(enteredZipper(kart, pads)).toBe(false);
    kart.x += 50;
    expect(enteredZipper(kart, pads)).toBe(false);
    kart.x = pad.x;
    expect(enteredZipper(kart, pads)).toBe(true);
  });
});
