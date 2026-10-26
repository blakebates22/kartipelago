// Loop-the-loops (src/game/loops.ts): the curve is smooth and closes where the Blender
// kit says (its probe points); a kart driven onto one is carried right round it,
// upside down at the top, and handed back to normal driving at the exit with its speed;
// it can back out before the commit point but never stalls after it; steering moves it
// across the road but never off it; a kart that comes in the wrong way rides it
// backwards; and on Loop Lab the AI laps through it, checkpoints and all.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import {
  buildLoop,
  createLoopSystem,
  loopEntities,
  loopFrame,
  loopHeight,
  loopPitch,
  parseLoop,
  parseRide,
  type LoopPath,
} from "../src/game/loops";
import { trackById } from "../src/game/tracks";
import { WORLDS } from "../src/game/worlds";
import { createKartState, stepKart, type KartConfig, type KartState } from "../src/vehicles/kart";
import { loadTrackPackage, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const cfg: KartConfig = { ...tuning.vehicle };
const dt = 1 / 120;
const reader =
  (id: string): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`../public/tracks/${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

const LOOP = buildLoop(
  parseLoop({
    x: 10,
    y: 2,
    z: -5,
    heading: 0.7,
    radius: 22,
    ramp: 26,
    offset: 18,
    width: 14,
    minSpeed: 14,
    commit: 18,
    boostMult: 1.45,
    boostSec: 2.2,
    gravity: 8,
  }),
);

/** A kart a little way before the loop's entry, lined up (sideways offset `across`). */
function approach(p: LoopPath, back = 6, across = 0, speed = 24) {
  const k = createKartState(
    p.x - p.fwd.x * back + p.right.x * across,
    p.z - p.fwd.z * back + p.right.z * across,
    p.heading,
    p.y,
  );
  k.speed = speed;
  return k;
}

/** Drive one kart with the loop system until it's back on normal ground (or time's up). */
function drive(
  p: LoopPath,
  k: KartState,
  input: (t: number) => InputState,
  seconds = 15,
  onStep?: (t: number) => void,
) {
  const sys = createLoopSystem([p], 1);
  const log = {
    entered: false,
    exited: false,
    minNy: 1,
    maxY: -Infinity,
    minSpeed: Infinity,
    t: 0,
  };
  for (let t = 0; t < seconds; t += dt) {
    const want = input(t);
    const before = { x: k.x, y: k.y, z: k.z };
    stepKart(k, sys.input(0, k, want), cfg, dt);
    const ev = sys.step(0, k, before, want.steer, cfg, dt);
    if (ev.entered) log.entered = true;
    if (sys.riding(0)) {
      log.minNy = Math.min(log.minNy, k.ny);
      log.maxY = Math.max(log.maxY, k.y);
      log.minSpeed = Math.min(log.minSpeed, k.speed);
    }
    onStep?.(t);
    if (ev.exited) {
      log.exited = true;
      log.t = t;
      return { ...log, sys };
    }
  }
  return { ...log, sys };
}

const full = { ...NEUTRAL, throttle: 1 };

describe("loop geometry", () => {
  it("turns the road through a full circle, smoothly, and comes back level", () => {
    expect(loopPitch(LOOP, 0)).toBe(0);
    expect(loopPitch(LOOP, LOOP.length)).toBeCloseTo(2 * Math.PI, 9);
    // The pitch never jumps and never turns back.
    let prev = 0;
    for (let s = 0; s <= LOOP.length; s += 0.25) {
      const v = loopPitch(LOOP, s);
      expect(v).toBeGreaterThanOrEqual(prev - 1e-9);
      expect(v - prev).toBeLessThan(0.25 / 22 + 1e-6);
      prev = v;
    }
    expect(LOOP.exit.y).toBeCloseTo(LOOP.y, 6);
    // The exit is SHIFT to the right of the entry line, and ahead of it.
    const dx = LOOP.exit.x - LOOP.x;
    const dz = LOOP.exit.z - LOOP.z;
    expect(dx * LOOP.right.x + dz * LOOP.right.z).toBeCloseTo(18, 6);
    expect(dx * LOOP.fwd.x + dz * LOOP.fwd.z).toBeGreaterThan(10);
    expect(loopHeight(LOOP)).toBeGreaterThan(42);
  });

  it("has a continuous, orthonormal frame: tangent along the road, normal up at the ends and down at the top", () => {
    let prev = loopFrame(LOOP, -1);
    for (let s = -1; s <= LOOP.length + 1; s += 0.2) {
      const f = loopFrame(LOOP, s);
      expect(Math.hypot(f.tx, f.ty, f.tz)).toBeCloseTo(1, 6);
      expect(Math.hypot(f.nx, f.ny, f.nz)).toBeCloseTo(1, 6);
      expect(f.tx * f.nx + f.ty * f.ny + f.tz * f.nz).toBeCloseTo(0, 6);
      expect(f.bx * f.tx + f.by * f.ty + f.bz * f.tz).toBeCloseTo(0, 6);
      // Neighbouring frames barely differ: no kinks, no flips.
      const turn = 1 - (f.nx * prev.nx + f.ny * prev.ny + f.nz * prev.nz);
      expect(turn).toBeLessThan(1e-3);
      expect(Math.hypot(f.px - prev.px, f.py - prev.py, f.pz - prev.pz)).toBeLessThan(0.21);
      prev = f;
    }
    expect(loopFrame(LOOP, 0).ny).toBeCloseTo(1, 6);
    expect(loopFrame(LOOP, LOOP.length / 2).ny).toBeLessThan(-0.99);
    expect(loopFrame(LOOP, LOOP.length).ny).toBeCloseTo(1, 6);
  });

  it("matches the Blender kit's curve (Loop Lab's probe points)", async () => {
    const meta = JSON.parse(
      new TextDecoder().decode(
        await readFile(new URL("../public/tracks/loop_lab/track.json", import.meta.url)),
      ),
    ) as { entities: Record<string, unknown>[] };
    const raw = meta.entities.filter((e) => e.type === "loop");
    expect(raw).toHaveLength(1);
    const p = buildLoop(loopEntities(raw)[0]!);
    const probe = raw[0]!.probe as number[][];
    expect(probe.length).toBeGreaterThanOrEqual(5);
    for (const [s, x, y, z] of probe) {
      const f = loopFrame(p, s!);
      expect(Math.hypot(f.px - x!, f.py - y!, f.pz - z!)).toBeLessThan(0.02);
    }
  });
});

describe("riding a loop", () => {
  it("carries a kart driven straight in right round, upside down at the top, and out at speed", () => {
    const k = approach(LOOP);
    const r = drive(LOOP, k, () => full);
    expect(r.entered).toBe(true);
    expect(r.exited).toBe(true);
    expect(r.minNy).toBeLessThan(-0.99);
    expect(r.maxY - LOOP.y).toBeGreaterThan(42);
    // Out at the exit, on the ground, facing the way the road goes, still fast.
    const dx = k.x - LOOP.exit.x;
    const dz = k.z - LOOP.exit.z;
    expect(Math.abs(dx * LOOP.right.x + dz * LOOP.right.z)).toBeLessThan(6.5);
    expect(k.y).toBeCloseTo(LOOP.y, 6);
    expect(k.ny).toBe(1);
    expect(
      Math.abs(Math.atan2(Math.sin(k.heading - LOOP.heading), Math.cos(k.heading - LOOP.heading))),
    ).toBeLessThan(0.05);
    expect(k.speed).toBeGreaterThan(cfg.topSpeed);
    expect(r.sys.riding(0)).toBe(false);
    // Normal driving carries on from there.
    const z0 = k.z;
    for (let i = 0; i < 60; i++) stepKart(k, full, cfg, dt);
    expect(Math.abs(k.z - z0) + Math.abs(k.x - LOOP.exit.x)).toBeGreaterThan(5);
  });

  it("never stalls once committed: a slow entry is carried round by the assist", () => {
    const k = approach(LOOP, 1, 0, 4);
    const r = drive(LOOP, k, (t) => (t < 0.5 ? full : NEUTRAL), 30);
    expect(r.exited).toBe(true);
    expect(r.minNy).toBeLessThan(-0.99);
    // Past the commit point the speed is held up at the minimum (the gravity step can
    // dip a hair under before the assist catches it).
    expect(k.speed).toBeGreaterThan(0);
  });

  it("lets you back out before the commit point", () => {
    const k = approach(LOOP, 1, 0, 6);
    let reversing = false;
    const r = drive(LOOP, k, (t) => {
      if (t > 0.4) reversing = true;
      return reversing ? { ...NEUTRAL, brake: 1 } : NEUTRAL;
    });
    expect(r.entered).toBe(true);
    expect(r.exited).toBe(true);
    // Out of the entry, backwards, facing forwards.
    const along = (k.x - LOOP.x) * LOOP.fwd.x + (k.z - LOOP.z) * LOOP.fwd.z;
    expect(along).toBeLessThanOrEqual(0.01);
    expect(k.speed).toBeLessThan(0);
    // It only got a little way up the curve.
    expect(r.minNy).toBeGreaterThan(0.9);
  });

  it("steers across the road but never off it, and lines back up when let go", () => {
    const k2 = approach(LOOP);
    const sys2 = createLoopSystem([LOOP], 1);
    let widest = 0;
    let movedRight = false;
    for (let t = 0; t < 12; t += dt) {
      const want = { ...full, steer: t < 2.5 ? 1 : 0 };
      const before = { x: k2.x, y: k2.y, z: k2.z };
      stepKart(k2, sys2.input(0, k2, want), cfg, dt);
      const ev = sys2.step(0, k2, before, want.steer, cfg, dt);
      if (sys2.riding(0)) {
        widest = Math.max(widest, Math.abs(sys2.rides[0]!.d));
        if (sys2.rides[0]!.d > 2) movedRight = true;
      }
      if (ev.exited) break;
    }
    expect(movedRight).toBe(true);
    expect(widest).toBeLessThanOrEqual(LOOP.width / 2 - 1.1 + 1e-9);
    expect(Math.abs(sys2.rides[0]!.rel)).toBeLessThan(0.1);
  });

  it("ignores a kart that comes at it badly lined up, slowly reversing, or from the side", () => {
    const sideways = approach(LOOP);
    sideways.heading = LOOP.heading + 1.5;
    expect(drive(LOOP, sideways, () => full, 0.5).entered).toBe(false);
    const wide = approach(LOOP, 6, LOOP.width);
    expect(drive(LOOP, wide, () => full, 0.5).entered).toBe(false);
  });

  it("carries a kart spinning out as it reaches the loop round it, by where it's going", () => {
    // (Blake: a rival hit just as it entered spun out and went straight through.)
    const k = approach(LOOP, 4);
    k.heading = LOOP.heading + 2.5;
    k.spinTime = 1.2;
    const r = drive(LOOP, k, () => NEUTRAL);
    expect(r.entered).toBe(true);
    expect(r.exited).toBe(true);
    expect(r.minNy).toBeLessThan(-0.99);
  });

  it("rides a wrong-way kart round backwards, from the exit to the entry", () => {
    const k = createKartState(
      LOOP.exit.x + LOOP.fwd.x * 6,
      LOOP.exit.z + LOOP.fwd.z * 6,
      LOOP.heading + Math.PI,
      LOOP.exit.y,
    );
    k.speed = 24;
    const r = drive(LOOP, k, () => full);
    expect(r.entered).toBe(true);
    expect(r.exited).toBe(true);
    expect(r.minNy).toBeLessThan(-0.99);
    expect(Math.hypot(k.x - LOOP.x, k.z - LOOP.z)).toBeLessThan(10);
  });

  it("keeps each kart's ride separate, and karts side by side don't overlap", () => {
    const a = approach(LOOP, 6, -1);
    const b = approach(LOOP, 6, 1);
    const sys = createLoopSystem([LOOP], 2);
    let closest = Infinity;
    for (let t = 0; t < 4; t += dt) {
      for (const [i, k] of [a, b].entries()) {
        const before = { x: k.x, y: k.y, z: k.z };
        stepKart(k, sys.input(i, k, full), cfg, dt);
        sys.step(i, k, before, 0, cfg, dt);
      }
      sys.contacts([a, b]);
      if (sys.riding(0) && sys.riding(1))
        closest = Math.min(closest, Math.abs(sys.rides[0]!.d - sys.rides[1]!.d));
    }
    expect(closest).toBeGreaterThan(1.8);
    sys.reset(0);
    expect(sys.riding(0)).toBe(false);
  });

  it("gives race logic a point on the straight from entry to exit", () => {
    const sys = createLoopSystem([LOOP], 1);
    const k = approach(LOOP);
    for (let t = 0; t < 3; t += dt) {
      const before = { x: k.x, y: k.y, z: k.z };
      stepKart(k, sys.input(0, k, full), cfg, dt);
      sys.step(0, k, before, 0, cfg, dt);
      if (sys.riding(0)) {
        const p = sys.racePos(0, k);
        expect(p.y).toBeCloseTo(LOOP.y, 6);
        const along = (p.x - LOOP.x) * LOOP.fwd.x + (p.z - LOOP.z) * LOOP.fwd.z;
        expect(along).toBeGreaterThanOrEqual(-0.01);
      }
    }
  });
});

describe("Loop Lab", () => {
  it("is in the Test World", () => {
    expect(WORLDS.find((w) => w.id === "test_world")!.tracks).toContain("loop_lab");
    expect(trackById("loop_lab")).toBeDefined();
  });

  it("the AI laps it three times, through the loop every lap", async () => {
    const p = await loadTrackPackage(reader("loop_lab"), { visual: false });
    expect(p.warnings).toEqual([]);
    const r = await aiLap(p, { laps: 3, surfaces: true, lapSeconds: 60 });
    expect(r.race.racers[0]!.lapTimes).toHaveLength(3);
    expect(r.respawns).toBe(0);
    expect(r.loopsRidden).toBe(3);
    expect(r.inverted).toBeGreaterThan(100);
    expect(r.worstAbove).toBeLessThan(2);
  }, 60000);
});

describe("rides (a road of any shape: the spiral up Snowy Summit's great tree)", () => {
  // Two turns of a 26 m spiral climbing 15 m a turn, entered heading +x (kart heading
  // π/2), turning left; then 20 m on straight.
  const pts: number[][] = [];
  const R = 26;
  const turns = 2;
  const len = 2 * Math.PI * R * turns;
  for (let s = 0; s <= len; s += 2) {
    const a = s / R;
    pts.push([R * Math.sin(a), 3 + (15 * a) / (2 * Math.PI), R - R * Math.cos(a), 0]);
  }
  for (let s = 2; s <= 20; s += 2) pts.push([s, 3 + 15 * turns, 0, 0]);
  const RIDE = parseRide({
    id: "spiral",
    points: pts,
    width: 13,
    minSpeed: 28,
    commit: 0,
    boostMult: 1.35,
    boostSec: 14,
    gravity: 0,
  })!;

  it("is built from its points: entry, exit and headings", () => {
    expect(RIDE.length).toBeGreaterThan(len);
    expect(RIDE.heading).toBeCloseTo(Math.PI / 2, 1);
    expect(RIDE.exitHeading).toBeCloseTo(Math.PI / 2, 2);
    expect(RIDE.exit.y).toBeCloseTo(3 + 15 * turns, 3);
    const f = loopFrame(RIDE, 40);
    expect(Math.hypot(f.nx, f.ny, f.nz)).toBeCloseTo(1, 6);
    expect(f.ny).toBeGreaterThan(0.95);
  });

  it("carries a kart up both turns at full zipper speed and hands it back at the top", () => {
    const k = approach(RIDE, 6, 0, 18);
    const r = drive(RIDE, k, () => full, 30);
    expect(r.entered).toBe(true);
    expect(r.exited).toBe(true);
    expect(k.y).toBeCloseTo(3 + 15 * turns, 0);
    expect(k.speed).toBeGreaterThan(27);
    // About 330 m at ~28 m/s: twelve seconds or so, not the twenty-odd it takes on foot.
    expect(r.t).toBeLessThan(14);
    expect(r.minSpeed).toBeGreaterThan(17);
  });
});
