import { describe, expect, it } from "vitest";
import trackData from "../assets/data/track.json";
import { acrossRoad, buildTrack, type TrackData } from "../src/world/track";

const data = trackData as TrackData;
const track = buildTrack(data, 2);

describe("track.json", () => {
  it("has at least 3 points with finite values and sensible widths", () => {
    expect(data.points.length).toBeGreaterThanOrEqual(3);
    for (const p of data.points) {
      for (const v of Object.values(p)) expect(Number.isFinite(v)).toBe(true);
      expect(p.width ?? data.defaultWidth).toBeGreaterThan(4);
    }
  });
});

describe("buildTrack", () => {
  it("samples evenly all the way round, closing the loop", () => {
    const gaps = track.samples.map((s, i) => {
      const next = track.samples[(i + 1) % track.samples.length]!;
      return s.pos.distanceTo(next.pos);
    });
    for (const g of gaps) expect(g).toBeGreaterThan(1.4);
    for (const g of gaps) expect(g).toBeLessThan(2.5);
  });

  it("puts right at right angles to travel, and level when unbanked", () => {
    const flat = buildTrack({ ...data, points: data.points.map((p) => ({ ...p, bank: 0 })) }, 2);
    for (const s of flat.samples) {
      expect(Math.abs(s.right.dot(s.forward))).toBeLessThan(0.05);
      expect(Math.abs(s.right.y)).toBeLessThan(1e-9);
    }
  });

  it("places the right edge to the driver's right", () => {
    // Driving along +Z (the first leg), the driver's right is -X.
    const first = track.samples[0]!;
    expect(acrossRoad(first, 1).x).toBeLessThan(first.pos.x);
  });

  it("starts on the first point, facing the second", () => {
    expect(track.start.x).toBeCloseTo(data.points[0]!.x);
    expect(track.start.z).toBeCloseTo(data.points[0]!.z);
    expect(Math.abs(track.start.heading)).toBeLessThan(0.2); // first leg runs along +Z
  });

  it("never dips below the ground", () => {
    for (const s of track.samples) expect(s.pos.y).toBeGreaterThanOrEqual(0);
  });

  it("uses per-point widths", () => {
    const narrow = data.points.findIndex((p) => p.width !== undefined);
    const near = track.samples.reduce((best, s) =>
      Math.hypot(s.pos.x - data.points[narrow]!.x, s.pos.z - data.points[narrow]!.z) <
      Math.hypot(best.pos.x - data.points[narrow]!.x, best.pos.z - data.points[narrow]!.z)
        ? s
        : best,
    );
    expect(near.width).toBeCloseTo(data.points[narrow]!.width!, 0);
  });

  it("banks the road when asked", () => {
    const banked = buildTrack({ ...data, points: data.points.map((p) => ({ ...p, bank: 10 })) }, 2);
    const s = banked.samples[0]!;
    expect(acrossRoad(s, 1).y).toBeLessThan(acrossRoad(s, -1).y);
  });
});
