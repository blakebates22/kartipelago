import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { flatGround } from "../src/physics/ground";
import {
  addBananas,
  bananaMult,
  effectiveBananas,
  loseBananas,
  removeBananas,
} from "../src/vehicles/bananas";
import { createKartState, stepKart, type KartConfig, type KartState } from "../src/vehicles/kart";
import { ZIP, startZipper } from "../src/vehicles/zipper";
import {
  canCollect,
  collectBananas,
  createBananaField,
  dropBananas,
  stepBananaField,
} from "../src/world/bananas";

/**
 * Repeatable banana measurements on flat ground with the base kart. Run with
 * BANANA_REPORT=1 (and --disableConsoleIntercept) to print the comparison table.
 */
const cfg: KartConfig = { ...tuning.vehicle };
const field = tuning.bananas;
const dt = 1 / 120;
const COUNTS = [0, 1, 5, 9, 10, 11, 12];

function kartWith(bananas: number, speed = 0) {
  const s = createKartState();
  s.bananas = bananas;
  s.speed = speed;
  return s;
}

type Plan = (t: number, s: KartState) => Partial<InputState>;
/** Step for `seconds`, calling `each` after every step with the time since the start. */
function drive(s: KartState, seconds: number, plan: Plan, each?: (t: number) => void) {
  let dist = 0;
  const steps = Math.round(seconds / dt);
  for (let i = 1; i <= steps; i++) {
    const x0 = s.x;
    const z0 = s.z;
    stepKart(s, { ...NEUTRAL, ...plan(i * dt, s) }, cfg, dt);
    dist += Math.hypot(s.x - x0, s.z - z0);
    each?.(i * dt);
  }
  return dist;
}
const full: Plan = () => ({ throttle: 1 });
const atRainbow: Plan = (_t, s) => ({
  throttle: s.zipPhase === ZIP.ACTIVE ? 0 : 1,
});

function stableMax(bananas: number) {
  const s = kartWith(bananas);
  drive(s, 15, full);
  return s.speed;
}

function measure(bananas: number) {
  // From rest.
  const s = kartWith(bananas);
  let to20 = Infinity;
  const at: Record<number, number> = {};
  const dist10 = drive(s, 10, full, (t) => {
    if (s.speed >= 20 && to20 === Infinity) to20 = t;
    for (const mark of [1, 3, 5]) if (Math.abs(t - mark) < dt / 2) at[mark] = s.speed;
  });
  const max = stableMax(bananas);

  // An identical enhanced zipper from cruising speed, pressing again at the rainbow.
  const z = kartWith(bananas, max);
  startZipper(z, 0, cfg);
  let zipPeak = 0;
  const zipAt: Record<number, number> = {};
  const zipDist = drive(z, 6, atRainbow, (t) => {
    zipPeak = Math.max(zipPeak, z.speed);
    for (const mark of [1, 2, 4, 6]) if (Math.abs(t - mark) < dt / 2) zipAt[mark] = z.speed;
  });

  // An identical 3 s drift from cruising speed, throttle held.
  const d = kartWith(bananas, max);
  let minSpeed = Infinity;
  let turned = 0;
  let last = d.velAngle;
  const driftDist = drive(
    d,
    3,
    (t) => ({ throttle: 1, drift: true, steer: t < 0.05 ? 1 : 0.6 }),
    () => {
      minSpeed = Math.min(minSpeed, d.speed);
      turned += Math.abs(Math.atan2(Math.sin(d.velAngle - last), Math.cos(d.velAngle - last)));
      last = d.velAngle;
    },
  );
  return {
    bananas,
    effective: effectiveBananas(bananas, cfg),
    mult: bananaMult(bananas, cfg),
    accel1: at[1]!,
    to20,
    v3: at[3]!,
    v5: at[5]!,
    max,
    dist10,
    zipPeak,
    zip1: zipAt[1]!,
    zip2: zipAt[2]!,
    zip4: zipAt[4]!,
    zip6: zipAt[6]!,
    zipDist,
    driftEntry: max,
    driftMin: minSpeed,
    driftEnd: d.speed,
    driftRadius: driftDist / turned,
    drifted: d.driftDir !== 0,
  };
}

const rows = COUNTS.map(measure);
const row = (n: number) => rows.find((r) => r.bananas === n)!;

function lossCase(from: number) {
  const s = kartWith(from, stableMax(from));
  const before = s.speed;
  const lost = loseBananas(s, "weapon", field);
  const justAfter = s.speed; // nothing has stepped yet
  drive(s, 0.25, full);
  const shortlyAfter = s.speed;
  drive(s, 4, full);
  return { from, lost, left: s.bananas, before, justAfter, shortlyAfter, settled: s.speed };
}
const losses = [1, 2, 5, 10, 11, 12].map(lossCase);

const env = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env;
if (env?.BANANA_REPORT) {
  const f = (n: number, d = 1) => n.toFixed(d).padStart(7);
  console.log(
    [
      `base top speed ${cfg.topSpeed} m/s, accel ${cfg.accel} m/s². speeds m/s, distances m`,
      "held eff   mult  v@1s  t→20   v3s   v5s   max  d10s | zipPk  z1s   z2s   z4s   z6s  zd6s | drIn drMin drEnd  drR",
      ...rows.map(
        (r) =>
          `${String(r.bananas).padStart(4)}${String(r.effective).padStart(4)}` +
          f(r.mult, 3) +
          f(r.accel1) +
          f(r.to20, 2) +
          f(r.v3) +
          f(r.v5) +
          f(r.max) +
          f(r.dist10, 0) +
          " |" +
          f(r.zipPeak) +
          f(r.zip1) +
          f(r.zip2) +
          f(r.zip4) +
          f(r.zip6) +
          f(r.zipDist, 0) +
          " |" +
          f(r.driftEntry) +
          f(r.driftMin) +
          f(r.driftEnd) +
          f(r.driftRadius),
      ),
      "",
      "lose 2 (weapon): from -> left, speed before / just after / +0.25 s / +4 s",
      ...losses.map(
        (l) =>
          `${String(l.from).padStart(4)} -> ${String(l.left).padStart(2)}` +
          f(l.before) +
          f(l.justAfter) +
          f(l.shortlyAfter) +
          f(l.settled),
      ),
    ].join("\n"),
  );
}

describe("banana speed", () => {
  it("multiplier: 1.0 with none, 1.125 at five, 1.25 at ten, capped beyond", () => {
    expect(bananaMult(0, cfg)).toBe(1);
    expect(bananaMult(5, cfg)).toBeCloseTo(1.125, 10);
    expect(bananaMult(10, cfg)).toBeCloseTo(1.25, 10);
    expect(bananaMult(12, cfg)).toBeCloseTo(1.25, 10);
    expect(effectiveBananas(12, cfg)).toBe(10);
  });

  it("each effective banana makes the kart faster, up to ten", () => {
    for (let k = 1; k <= 4; k++) {
      const a = rows[k - 1]!;
      const b = rows[k]!;
      expect(b.max).toBeGreaterThan(a.max);
      expect(b.dist10).toBeGreaterThan(a.dist10);
      expect(b.to20).toBeLessThan(a.to20);
    }
  });

  it("gives ten bananas a clear but not huge edge", () => {
    const gain = row(10).max / row(0).max;
    expect(gain).toBeGreaterThan(1.1);
    expect(gain).toBeLessThan(1.25);
  });

  it("gives nothing extra beyond ten", () => {
    for (const n of [11, 12]) {
      expect(row(n).max).toBeCloseTo(row(10).max, 6);
      expect(row(n).dist10).toBeCloseTo(row(10).dist10, 6);
    }
  });

  it("raises speed by accelerating to it, not by multiplying the current speed", () => {
    const s = kartWith(0);
    drive(s, 15, full);
    const cruising = s.speed;
    addBananas(s, 10);
    expect(s.speed).toBe(cruising);
    drive(s, 1 / 120, full);
    expect(s.speed - cruising).toBeLessThanOrEqual(cfg.accel * 1.25 * dt + 1e-9);
  });
});

describe("bananas and zippers", () => {
  it("leave the zipper's push alone: same peak with or without bananas", () => {
    expect(row(10).zipPeak).toBeCloseTo(row(0).zipPeak, 6);
    expect(row(10).zip1).toBeCloseTo(row(0).zip1, 6);
  });

  it("help after the boost, once normal driving takes over", () => {
    expect(row(10).zip4).toBeGreaterThan(row(0).zip4 + 1);
    expect(row(10).zip6).toBeGreaterThan(row(0).zip6 + 2);
    expect(row(10).zipDist).toBeGreaterThan(row(0).zipDist);
  });

  it("collecting a banana mid-boost doesn't reset the boost timer", () => {
    const s = kartWith(0, cfg.topSpeed);
    startZipper(s, 0, cfg);
    drive(s, 0.5, () => ({}));
    const left = s.zipTime;
    addBananas(s, 5);
    drive(s, 0.1, () => ({}));
    expect(s.zipTime).toBeCloseTo(left - 0.1, 6);
    expect(s.zipEnhanced).toBe(true);
  });
});

describe("bananas and drifting", () => {
  it("leave the drift line alone: same arc at any banana count", () => {
    for (const r of rows) {
      expect(r.drifted).toBe(true);
      expect(r.driftRadius).toBeCloseTo(row(0).driftRadius, 0);
    }
  });

  it("keep drift speed the same way at any count (no banana drift penalty)", () => {
    for (const r of rows) expect(r.driftMin / r.driftEntry).toBeGreaterThan(0.97);
  });
});

describe("losing bananas", () => {
  it("drops up to two for a weapon hit, never going below zero", () => {
    expect(losses.map((l) => [l.from, l.left])).toEqual([
      [1, 0],
      [2, 0],
      [5, 3],
      [10, 8],
      [11, 9],
      [12, 10],
    ]);
    const s = kartWith(0);
    expect(removeBananas(s, 5)).toBe(0);
    expect(s.bananas).toBe(0);
    expect(loseBananas(s, "spin", field)).toBe(0);
  });

  it("never snaps the current speed; it eases down to the new top speed", () => {
    for (const l of losses) {
      expect(l.justAfter).toBe(l.before);
      expect(l.before - l.shortlyAfter).toBeLessThanOrEqual(cfg.drag * 0.25 + 1e-6);
      expect(l.settled).toBeCloseTo(stableMax(l.left), 3);
    }
  });

  it("a reserve above ten keeps the full bonus", () => {
    const l = losses.find((x) => x.from === 12)!;
    expect(l.settled).toBeCloseTo(row(10).max, 6);
  });
});

describe("banana pickups", () => {
  const make = () => createBananaField(undefined, [], () => flatGround);

  it("are collected once, then respawn later", () => {
    const f = make();
    f.bananas.push({
      x: 0,
      y: 0,
      z: 0,
      vx: 0,
      vy: 0,
      vz: 0,
      settled: true,
      active: true,
      placed: true,
      age: 0,
      respawnIn: 0,
    });
    const kart = kartWith(0);
    expect(collectBananas(f, 0, kart, field)).toHaveLength(1);
    expect(collectBananas(f, 0, kart, field)).toHaveLength(0);
    expect(kart.bananas).toBe(1);
    for (let t = 0; t < field.respawnSec + 0.1; t += dt) stepBananaField(f, field, dt);
    expect(collectBananas(f, 0, kart, field)).toHaveLength(1);
    expect(kart.bananas).toBe(2);
  });

  it("are out of reach beyond the pickup radius", () => {
    const f = make();
    f.bananas.push({
      x: field.pickupRadius + 0.5,
      y: 0,
      z: 0,
      vx: 0,
      vy: 0,
      vz: 0,
      settled: true,
      active: true,
      placed: true,
      age: 0,
      respawnIn: 0,
    });
    expect(collectBananas(f, 0, kartWith(0), field)).toHaveLength(0);
  });

  it("dropped bananas fly out and up, land, settle, and only then can be collected", () => {
    const f = make();
    const kart = kartWith(0, 10);
    const dropped = dropBananas(f, kart, 2, field);
    expect(dropped).toHaveLength(2);
    expect(dropped.every((b) => b.vy > 0)).toBe(true);
    // Thrown in opposite directions, out to the sides.
    expect(Math.sign(dropped[0]!.vx)).not.toBe(Math.sign(dropped[1]!.vx));
    let peak = 0;
    let t = 0;
    while (!dropped.every((b) => b.settled) && t < 5) {
      stepBananaField(f, field, dt);
      peak = Math.max(peak, dropped[0]!.y);
      // The kart sitting right where they were dropped can't grab them mid-air.
      for (const b of dropped)
        if (!b.settled) expect(canCollect(b, { x: b.x, y: b.y, z: b.z }, field)).toBe(false);
      t += dt;
    }
    expect(peak).toBeGreaterThan(0.5);
    expect(t).toBeLessThan(3);
    const b = dropped[0]!;
    expect(b.y).toBe(0);
    expect(Math.hypot(b.x, b.z)).toBeGreaterThan(1);
    const there = kartWith(0);
    there.x = b.x;
    there.z = b.z;
    expect(collectBananas(f, 0, there, field)).toHaveLength(1);
    // Dropped bananas don't come back.
    expect(f.bananas).toHaveLength(1);
  });
});
