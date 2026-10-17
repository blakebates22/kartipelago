import { describe, expect, it } from "vitest";
import courseData from "../assets/data/course.json";
import tuning from "../assets/data/tuning.json";
import { createCourse, onPad, stepCourse } from "../src/world/course";
import { createKartState } from "../src/vehicles/kart";

const cfg = tuning.course;
const kartCfg = tuning.vehicle;
const dt = 1 / 120;

describe("course.json", () => {
  it("has only finite coordinates", () => {
    const all = [courseData.start, ...courseData.pickups, ...courseData.pads];
    for (const p of all) {
      for (const v of Object.values(p)) expect(Number.isFinite(v)).toBe(true);
    }
  });
});

describe("boost pads", () => {
  const pad = { x: 10, z: 10, heading: Math.PI / 2 }; // pointing +X
  it("covers a rectangle aligned with its heading", () => {
    expect(onPad(10 + cfg.padLength / 2 - 0.1, 10, pad, cfg)).toBe(true);
    expect(onPad(10, 10 + cfg.padWidth / 2 - 0.1, pad, cfg)).toBe(true);
    expect(onPad(10, 10 + cfg.padWidth / 2 + 0.1, pad, cfg)).toBe(false);
  });

  it("boosts above top speed, which then bleeds back", () => {
    const course = createCourse({ start: { x: 0, z: 0, heading: 0 }, pickups: [], pads: [pad] });
    const kart = createKartState(10, 10);
    kart.speed = 10;
    stepCourse(course, kart, cfg, kartCfg, dt);
    expect(kart.speed).toBeCloseTo(kartCfg.topSpeed * kartCfg.padSpeedMult);
    expect(kart.boostTime).toBeGreaterThan(0);
  });
});

describe("pickups", () => {
  const data = { start: { x: 0, z: 0, heading: 0 }, pickups: [{ x: 0, z: 1 }], pads: [] };

  it("are collected once, then respawn", () => {
    const course = createCourse(data);
    const kart = createKartState();
    expect(stepCourse(course, kart, cfg, kartCfg, dt)).toBe(1);
    expect(stepCourse(course, kart, cfg, kartCfg, dt)).toBe(0);
    for (let t = 0; t < cfg.pickupRespawnSec + dt; t += dt)
      stepCourse(course, kart, cfg, kartCfg, dt);
    expect(course.collected).toBe(2);
  });

  it("are missed when you're too far away", () => {
    const course = createCourse(data);
    const kart = createKartState(cfg.pickupRadius + 0.1, 1);
    expect(stepCourse(course, kart, cfg, kartCfg, dt)).toBe(0);
  });
});
