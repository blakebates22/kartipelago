import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import {
  createKartState,
  driftSteerFor,
  stepKart,
  type KartConfig,
  type KartState,
} from "../src/vehicles/kart";
import {
  buildDriftPark,
  createLocator,
  createStreak,
  loopLength,
  loopPoints,
  loopSizes,
  spinRadius,
  stepStreak,
  streakLaps,
  type ParkLoop,
} from "../src/world/driftPark";
import { collectBananas, createBananaField, stepBananaField } from "../src/world/bananas";
import { createTrackGround } from "../src/physics/ground";
import { buildZippers, enteredZipper } from "../src/world/zippers";
import { startZipper } from "../src/vehicles/zipper";

const cfg: KartConfig = { ...tuning.vehicle, driftModel: 1 };
const park = buildDriftPark(cfg, tuning.driftPark, tuning.track.sampleSpacing);
const dt = 1 / 120;
const env = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env;
const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

interface Run {
  /** Laps covered in the one drift. */
  laps: number;
  /** Furthest from the centre line while drifting, metres. */
  maxAcross: number;
  /** Left the road during the drift. */
  offRoad: boolean;
  spun: boolean;
  /** The drift ended before the laps were done. */
  dropped: boolean;
}

/**
 * A skilled driver: pure pursuit on the centre line, holding one drift for `laps` laps
 * (or `handsOff`: start the drift, then leave the stick centred). Driving direction
 * `dir`: 1 = the way the loop was laid out (turning left), -1 = the other way.
 */
function driveLoop(
  loop: ParkLoop,
  opts: { laps: number; handsOff?: boolean; dir?: 1 | -1; zippers?: boolean } = { laps: 3 },
): Run {
  const dir = opts.dir ?? 1;
  const t = loop.track;
  const n = t.samples.length;
  const s0 = t.samples[0]!;
  const heading = Math.atan2(s0.forward.x, s0.forward.z) + (dir < 0 ? Math.PI : 0);
  const k: KartState = createKartState(s0.pos.x, s0.pos.z, heading);
  const locate = createLocator(park);
  const pads = opts.zippers ? buildZippers(t, t.data.zippers ?? [], tuning.track) : [];
  // Loops laid out turning left; driven the other way they turn right.
  const turnSteer = dir > 0 ? -1 : 1;
  let index = 0;
  let drifted = 0;
  let maxAcross = 0;
  let offRoad = false;
  let spun = false;
  let started = false;
  const run = { laps: 0, maxAcross: 0, offRoad: false, spun: false, dropped: false };

  for (let time = 0; time < 120; time += dt) {
    // Nearest sample (local search), then the aim point ahead in the driving direction.
    let best = index;
    let bd = Infinity;
    for (let j = -20; j <= 20; j++) {
      const p = t.samples[(((index + j) % n) + n) % n]!.pos;
      const d = (p.x - k.x) ** 2 + (p.z - k.z) ** 2;
      if (d < bd) {
        bd = d;
        best = index + j;
      }
    }
    const moved = best - index;
    index = ((best % n) + n) % n;
    const speed = Math.max(1, Math.abs(k.speed));
    const look = 7 + 0.25 * speed;
    const aimS =
      t.samples[(((index + dir * Math.round(look / tuning.track.sampleSpacing)) % n) + n) % n]!;
    // Before the drift, line up on the inside (the drift's entry swings you wide).
    const inside = started ? 0 : -ENTRY_INSIDE; // the inside is to the loop's left
    const ax = aimS.pos.x + aimS.right.x * inside;
    const az = aimS.pos.z + aimS.right.z * inside;
    const aim = wrap(Math.atan2(ax - k.x, az - k.z) - k.velAngle);
    const wantRate = (2 * speed * Math.sin(aim)) / look;

    const input: InputState = { ...NEUTRAL, throttle: 1 };
    if (!started) {
      // Up to speed on the loop, then into the drift.
      const rate =
        (cfg.turnRate + (cfg.turnRateAtTop - cfg.turnRate) * Math.min(1, speed / cfg.topSpeed)) *
        Math.min(1, speed / cfg.turnFullSpeed);
      input.steer = Math.max(-1, Math.min(1, -wantRate / Math.max(0.1, rate)));
      // Start the drift just before a wide part of the loop.
      const lobeLen = t.length / loop.size.lobes;
      const at = (index / n) * t.length;
      const toWide = dir > 0 ? (lobeLen - (at % lobeLen)) % lobeLen : at % lobeLen;
      if (speed > cfg.topSpeed * 0.9 && time > 1 && toWide <= ENTRY_BEFORE) {
        input.drift = true;
        input.steer = turnSteer;
        started = true;
      }
    } else {
      input.drift = true;
      if (!opts.handsOff && k.driftDir !== 0) {
        const target = (k.driftDir * cfg.driftOffsetDeg * Math.PI) / 180;
        const offsetRate = (target - k.driftOffset) * cfg.driftOffsetRate;
        const curvature = (-k.driftDir * (wantRate - offsetRate)) / speed;
        // Countersteer past the spin-out point only in bursts: ease off before the
        // spin-out count runs out, which resets it.
        let into = driftSteerFor(curvature, cfg);
        if (k.counterTime > cfg.spinOutAfterSec * 0.75)
          into = Math.max(into, -cfg.spinThreshold * 0.95);
        input.steer = Math.max(-1, Math.min(1, into)) * k.driftDir;
        // Tighter than full lock: a dab of brake adds bite.
        const kTight = 1 / cfg.driftRadiusTight;
        if (curvature > kTight && k.driftTime > BRAKE_AFTER)
          input.brake = Math.min(BRAKE_MAX, (curvature / kTight - 1) / cfg.driftBrakeTighten);
      }
    }
    stepKart(k, input, cfg, dt);
    if (enteredZipper(k, pads)) startZipper(k, input.throttle, cfg);
    if (!started) continue;
    if (k.spinTime > 0) spun = true;
    if (k.driftDir === 0 && time > 2) {
      run.dropped = true;
      break;
    }
    if (k.driftTime > 0.6) {
      // Count distance once the drift has settled in.
      drifted += Math.abs(moved);
      const spot = locate.at(k.x, k.z);
      const across = spot && spot.loop === loop ? Math.abs(spot.across) : Infinity;
      maxAcross = Math.max(maxAcross, across);
      if (!spot || spot.loop !== loop || !spot.onRoad) offRoad = true;
    }
    if ((drifted * t.length) / n >= opts.laps * t.length) break;
  }
  return { ...run, laps: (drifted * t.length) / n / t.length, maxAcross, offRoad, spun };
}

/** The test driver's entry: this far inside, starting this many metres before a wide part. */
const ENTRY_INSIDE = Number(env?.ENTRY_INSIDE ?? 4);
const ENTRY_BEFORE = Number(env?.ENTRY_BEFORE ?? 8);
const BRAKE_MAX = Number(env?.BRAKE_MAX ?? 0.3);
const BRAKE_AFTER = Number(env?.BRAKE_AFTER ?? 0.4);

const plain = park.loops.filter((l) => l.variant === "plain");

describe("drift park geometry", () => {
  it("has four sizes, each plain, with bananas and with zippers", () => {
    expect(park.loops).toHaveLength(12);
    expect(new Set(park.loops.map((l) => l.size.id)).size).toBe(4);
    for (const v of ["plain", "bananas", "zipper"])
      expect(park.loops.filter((l) => l.variant === v)).toHaveLength(4);
  });

  it("sizes its loops from the drift radii, getting bigger", () => {
    const sizes = loopSizes(cfg);
    const spin = spinRadius(cfg);
    expect(spin).toBeGreaterThan(cfg.driftRadiusNeutral);
    expect(spin).toBeLessThan(cfg.driftRadiusCounter);
    for (const s of sizes) expect(s.rMin).toBeGreaterThan(cfg.driftRadiusTight);
    const lengths = sizes.map(loopLength);
    for (let i = 1; i < lengths.length; i++) expect(lengths[i]!).toBeGreaterThan(lengths[i - 1]!);
  });

  it("closes every loop on itself", () => {
    for (const s of loopSizes(cfg)) {
      const pts = loopPoints(s);
      const a = pts[0]!;
      const b = pts.at(-1)!;
      const step = loopLength(s) / pts.length;
      // The gap from the last point back to the first is one ordinary step.
      expect(Math.hypot(a.x - b.x, a.z - b.z)).toBeCloseTo(step, 0);
    }
  });

  it("keeps the loops apart", () => {
    for (const a of park.loops)
      for (const b of park.loops) {
        if (a === b) continue;
        const apart =
          a.box.maxX < b.box.minX ||
          b.box.maxX < a.box.minX ||
          a.box.maxZ < b.box.minZ ||
          b.box.maxZ < a.box.minZ;
        expect(apart, `${a.name} / ${b.name}`).toBe(true);
      }
  });
});

describe("drift park: holding one drift", () => {
  for (const loop of plain) {
    it(`${loop.size.name}: a skilled driver drifts three laps without letting go`, () => {
      for (const dir of [1, -1] as const) {
        const r = driveLoop(loop, { laps: 3, dir });
        expect(r.dropped, `dropped (dir ${dir})`).toBe(false);
        expect(r.spun, `spun (dir ${dir})`).toBe(false);
        expect(r.offRoad, `off road, max across ${r.maxAcross.toFixed(1)} (dir ${dir})`).toBe(
          false,
        );
        expect(r.laps).toBeGreaterThanOrEqual(3);
      }
    });
    it(`${loop.size.name}: just holding the stick still doesn't make it round`, () => {
      const r = driveLoop(loop, { laps: 1, handsOff: true });
      expect(r.offRoad).toBe(true);
    });
  }

  it("the zipper loops can be drifted through the zippers too", () => {
    for (const loop of park.loops.filter((l) => l.variant === "zipper")) {
      const r = driveLoop(loop, { laps: 2, zippers: true });
      expect(
        r.dropped || r.spun || r.offRoad,
        `${loop.name}: max across ${r.maxAcross.toFixed(1)}`,
      ).toBe(false);
    }
  });
});

describe("drift park: bananas", () => {
  it("brings banana-loop bananas back a few seconds after you take them", () => {
    const loop = park.loops.find((l) => l.variant === "bananas")!;
    const field = createBananaField(loop.track, loop.track.data.bananas ?? [], () =>
      createTrackGround(loop.track),
    );
    expect(field.bananas.length).toBeGreaterThan(8);
    const b = field.bananas[0]!;
    const kart = { x: b.x, y: b.y, z: b.z, bananas: 0 };
    expect(collectBananas(field, 0, kart, tuning.bananas)).toHaveLength(1);
    expect(b.active).toBe(false);
    for (let t = 0; t < tuning.driftPark.bananaRespawnSec + 0.1; t += dt)
      stepBananaField(field, tuning.bananas, dt);
    expect(b.active).toBe(true);
  });
});

describe("drift park: streaks", () => {
  it("counts laps in one unbroken drift, and resets when you let go or leave the road", () => {
    const loop = plain[1]!;
    const st = createStreak(park);
    const n = loop.track.samples.length;
    const spot = (i: number, onRoad = true) => ({ loop, sample: i % n, across: 0, onRoad });
    stepStreak(st, park, spot(0), false);
    let announced: number | undefined;
    for (let i = 1; i <= n + 5; i++) announced = stepStreak(st, park, spot(i), true) ?? announced;
    expect(announced).toBe(1);
    expect(streakLaps(st, park)).toBeGreaterThan(1);
    stepStreak(st, park, spot(n + 6, false), true);
    expect(streakLaps(st, park)).toBe(0);
    expect(st.best[loop.index]).toBeGreaterThan(1);
  });
});

if (env?.PARK_REPORT) {
  const spin = spinRadius(cfg);
  const lines = [`spin radius ${spin.toFixed(1)} m`];
  for (const loop of plain) {
    const s = loop.size;
    const fwd = driveLoop(loop, { laps: 3 });
    const back = driveLoop(loop, { laps: 3, dir: -1 });
    const still = driveLoop(loop, { laps: 1, handsOff: true });
    const zip = driveLoop(
      park.loops.find((l) => l.size === s && l.variant === "zipper")!,
      { laps: 2, zippers: true },
    );
    lines.push(
      `${s.name.padEnd(8)} lobes ${s.lobes} R ${s.rMin.toFixed(1)}-${s.rMax.toFixed(1)} len ${loopLength(s).toFixed(0)} m  ` +
        `fwd ${fwd.maxAcross.toFixed(1)}${fwd.spun ? " SPUN" : ""}${fwd.dropped ? " DROP" : ""}  ` +
        `back ${back.maxAcross.toFixed(1)}  still ${still.offRoad ? "off" : "ON"} ${still.laps.toFixed(2)}  ` +
        `zip ${zip.maxAcross.toFixed(1)}${zip.spun ? " SPUN" : ""}${zip.dropped ? " DROP" : ""}`,
    );
  }
  console.log(lines.join("\n"));
}
