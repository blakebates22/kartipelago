import { describe, expect, it } from "vitest";
import { dampAngle, follow } from "../src/render/chaseCamera";

describe("chase camera smoothing", () => {
  it("is frame-rate independent", () => {
    let a = 0;
    for (let i = 0; i < 4; i++) a += (1 - a) * follow(5, 1 / 240);
    expect(a).toBeCloseTo(follow(5, 1 / 60));
  });

  it("swings the short way round across ±π", () => {
    const next = dampAngle(3, -3, 10, 1 / 60);
    expect(next).toBeGreaterThan(3); // heading up past π, not back down through 0
  });
});
