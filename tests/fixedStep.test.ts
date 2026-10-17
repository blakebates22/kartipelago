import { describe, expect, it } from "vitest";
import { createFixedStep } from "../src/core/fixedStep";

describe("createFixedStep", () => {
  it("runs one step per step-length of elapsed time", () => {
    const clock = createFixedStep(100, 10);
    expect(clock.advance(0.035)).toBe(3);
    expect(clock.tick).toBe(3);
    expect(clock.alpha).toBeCloseTo(0.5);
  });

  it("carries leftover time into the next frame", () => {
    const clock = createFixedStep(100, 10);
    expect(clock.advance(0.006)).toBe(0);
    expect(clock.advance(0.006)).toBe(1);
  });

  it("caps steps and drops the backlog after a long pause", () => {
    const clock = createFixedStep(100, 5);
    expect(clock.advance(10)).toBe(5);
    expect(clock.alpha).toBe(0);
  });

  it("ignores negative time", () => {
    const clock = createFixedStep(60, 5);
    expect(clock.advance(-1)).toBe(0);
  });

  it("rejects a non-positive rate", () => {
    expect(() => createFixedStep(0, 5)).toThrow();
  });
});
