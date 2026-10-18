import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { createTrackGround } from "../src/physics/ground";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepWalls } from "../src/physics/walls";
import { createKartState, stepKart, type KartState } from "../src/vehicles/kart";
import { buildTrack, type TrackData } from "../src/world/track";

const dt = 1 / 120;
const walls = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

// A long straight along +Z, 20 m wide: walls at x = ±10.
const straight: TrackData = {
  name: "straight",
  defaultWidth: 20,
  points: [
    { x: 0, z: -400 },
    { x: 0, z: 0 },
    { x: 0, z: 400 },
    { x: 400, z: 400 },
    { x: 400, z: -400 },
  ],
};
const track = buildTrack(straight, 2);

function drive(s: KartState, seconds: number, input: Partial<InputState>) {
  const ground = createTrackGround(track);
  let hits = 0;
  for (let t = 0; t < seconds; t += dt) {
    stepImpacts(s, tuning.collision, dt);
    stepKart(s, { ...NEUTRAL, ...input }, tuning.vehicle, dt);
    if (stepWalls(s, ground, walls, dt)) hits++;
    stepVertical(s, ground, tuning.physics, dt);
  }
  return hits;
}

/** A kart at speed heading `deg` degrees off straight ahead, toward the left wall. */
function aimed(deg: number) {
  const s = createKartState(0, 0, (deg * Math.PI) / 180);
  s.speed = 20;
  return s;
}

describe("walls", () => {
  it("keep the kart on the road", () => {
    const s = aimed(30);
    drive(s, 2, { throttle: 1 });
    expect(Math.abs(s.x)).toBeLessThanOrEqual(10 - walls.kartRadius + 1e-6);
  });

  it("let a glancing hit slide along with most of its speed", () => {
    const s = aimed(8);
    s.x = 9;
    const hits = drive(s, 0.2, {});
    expect(hits).toBeGreaterThan(0);
    expect(s.speed).toBeGreaterThan(18);
  });

  it("nearly stop a head-on hit", () => {
    const s = aimed(85);
    s.x = 8.5;
    drive(s, 0.1, {});
    expect(Math.abs(s.speed)).toBeLessThan(4);
  });

  it("don't pin you: holding throttle with the nose in the wall scrapes you off it", () => {
    const s = aimed(60);
    s.x = 8.5;
    drive(s, 2, { throttle: 1 });
    expect(s.speed).toBeGreaterThan(15);
  });

  it("still apply on the outside of a bend, between road segments", () => {
    // Regression: points far out on the outside of a corner used to fall in gaps
    // between segments and count as off the road, with no walls.
    const bend = buildTrack(
      {
        name: "bend",
        defaultWidth: 22,
        points: Array.from({ length: 24 }, (_, i) => ({
          x: 40 * Math.sin((i / 24) * Math.PI * 2),
          z: 40 * Math.cos((i / 24) * Math.PI * 2),
        })),
      },
      2,
    );
    const ground = createTrackGround(bend);
    for (let a = 0; a < Math.PI * 2; a += 0.01) {
      // 10 m outside the centre line (radius 50 on a 40 m loop), still on the road.
      const q = ground.at(50 * Math.sin(a), 50 * Math.cos(a));
      expect(q.road).toBeDefined();
    }
  });

  it("are cleared by a kart flying high enough", () => {
    const s = aimed(60);
    s.x = 9;
    s.y = 5;
    s.grounded = false;
    s.vy = 0;
    const ground = createTrackGround(track);
    stepKart(s, NEUTRAL, tuning.vehicle, dt);
    expect(stepWalls(s, ground, walls, dt)).toBeNull();
  });
});
