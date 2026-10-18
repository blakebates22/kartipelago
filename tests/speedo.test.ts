import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import {
  DIAL_SWEEP_DEG,
  PEG_OVERSHOOT_DEG,
  boostChevrons,
  needleDeg,
  speedoScale,
  speedoValue,
} from "../src/render/speedo";

const hud = tuning.hud;
const base = tuning.vehicle;

describe("speedometer", () => {
  it("is a fixed scale of the true speed", () => {
    const k = speedoScale(hud, base);
    for (const v of [0, 1, 7.5, 22, 35.2]) expect(speedoValue(v, hud, base)).toBeCloseTo(v * k, 9);
  });

  it("reads 150 at the fastest boost, 62.5 at plain top speed", () => {
    const fastest = base.topSpeed * base.zipEnhancedMult;
    expect(speedoValue(fastest, hud, base)).toBeCloseTo(150, 9);
    expect(speedoValue(base.topSpeed, hud, base)).toBeCloseTo(62.5, 6);
  });

  it("reads reversing as a positive speed", () => {
    expect(speedoValue(-5, hud, base)).toBeCloseTo(speedoValue(5, hud, base), 9);
  });

  it("sweeps the needle from the lower left to the lower right, then pegs", () => {
    expect(needleDeg(0, 180)).toBe(-DIAL_SWEEP_DEG / 2);
    expect(needleDeg(90, 180)).toBeCloseTo(0, 9);
    expect(needleDeg(180, 180)).toBe(DIAL_SWEEP_DEG / 2);
    expect(needleDeg(500, 180)).toBe(DIAL_SWEEP_DEG / 2 + PEG_OVERSHOOT_DEG);
  });

  it("lights chevrons for the boost time left", () => {
    expect(boostChevrons(false, 1, 1)).toBe(0);
    expect(boostChevrons(true, 1, 1)).toBe(4);
    expect(boostChevrons(true, 0.5, 1)).toBe(2);
    expect(boostChevrons(true, 0.01, 1)).toBe(1);
    expect(boostChevrons(true, 0, 1)).toBe(0);
  });
});
