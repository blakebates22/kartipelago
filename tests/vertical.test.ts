import { describe, expect, it } from "vitest";
import trackData from "../assets/data/track.json";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { createTrackGround, flatGround, type GroundQuery } from "../src/physics/ground";
import { stepVertical } from "../src/physics/vertical";
import { createKartState, stepKart, wrapAngle, type KartState } from "../src/vehicles/kart";
import { buildTrack, type Track, type TrackData } from "../src/world/track";

const dt = 1 / 120;
const kartCfg = tuning.vehicle;
const phys = tuning.physics;
const track = buildTrack(trackData as TrackData, tuning.track.sampleSpacing);

/** Simple autopilot: steer toward a point a little way ahead on the centre line. */
function steerAlong(track: Track, s: KartState) {
  let best = 0;
  let bestD = Infinity;
  track.samples.forEach((p, i) => {
    const d = (p.pos.x - s.x) ** 2 + (p.pos.z - s.z) ** 2;
    if (d < bestD) {
      bestD = d;
      best = i;
    }
  });
  const aim = track.samples[(best + 6) % track.samples.length]!.pos;
  const want = Math.atan2(aim.x - s.x, aim.z - s.z);
  return Math.max(-1, Math.min(1, -wrapAngle(want - s.heading) * 3));
}

function drive(
  s: KartState,
  ground: GroundQuery,
  seconds: number,
  input: Partial<InputState>,
  cfg = kartCfg,
  follow?: Track,
) {
  const log: { airborne: boolean; y: number; speed: number; onRoad: boolean }[] = [];
  for (let t = 0; t < seconds; t += dt) {
    const steer = follow ? steerAlong(follow, s) : (input.steer ?? 0);
    stepKart(s, { ...NEUTRAL, ...input, steer }, cfg, dt);
    stepVertical(s, ground, phys, dt);
    log.push({ airborne: !s.grounded, y: s.y, speed: s.speed, onRoad: ground.at(s.x, s.z).onRoad });
  }
  return log;
}

describe("ground following", () => {
  it("stays grounded at height 0 on flat ground", () => {
    const s = createKartState();
    const log = drive(s, flatGround, 3, { throttle: 1 });
    expect(log.every((l) => !l.airborne && l.y === 0)).toBe(true);
  });

  it("follows the track surface round a whole lap without leaving the road", () => {
    const ground = createTrackGround(track);
    const s = createKartState(track.start.x, track.start.z, track.start.heading);
    const log = drive(s, ground, 50, { throttle: 1 }, kartCfg, track);
    expect(log.every((l) => l.onRoad)).toBe(true);
    // Slopes change speed: slower up hills, faster down them.
    const speeds = log.slice(400).map((l) => l.speed);
    expect(Math.max(...speeds) - Math.min(...speeds)).toBeGreaterThan(2);
  });
});

describe("the opening-straight jump", () => {
  const ground = createTrackGround(track);
  const s = createKartState(track.start.x, track.start.z, track.start.heading);
  const log = drive(s, ground, 6, { throttle: 1 }, kartCfg, track);
  const air = log.filter((l) => l.airborne);

  it("launches at full speed", () => {
    expect(air.length * dt).toBeGreaterThan(0.4);
  });

  it("keeps all its speed through the air and on landing", () => {
    const takeoff = log.findIndex((l) => l.airborne);
    const landing = takeoff + log.slice(takeoff).findIndex((l) => !l.airborne);
    expect(landing).toBeGreaterThan(takeoff);
    expect(log[landing]!.speed).toBeGreaterThanOrEqual(log[takeoff - 1]!.speed - 1e-9);
  });

  it("barely leaves the ground at low speed", () => {
    const slow = createKartState(track.start.x, track.start.z, track.start.heading);
    const cfg = { ...kartCfg, topSpeed: 14 };
    const slowLog = drive(slow, createTrackGround(track), 6, { throttle: 1 }, cfg, track);
    expect(slowLog.filter((l) => l.airborne).length * dt).toBeLessThan(0.15);
  });
});

describe("in the air", () => {
  it("steers only a little", () => {
    const ground: GroundQuery = flatGround;
    const a = createKartState();
    a.speed = 20;
    a.grounded = false;
    a.y = 50;
    const b = createKartState();
    b.speed = 20;
    drive(a, ground, 0.5, { steer: 1 });
    drive(b, ground, 0.5, { steer: 1, throttle: 1 });
    expect(Math.abs(a.heading)).toBeLessThan(Math.abs(b.heading) * 0.25);
    expect(Math.abs(a.heading)).toBeGreaterThan(0);
  });

  it("can't start a drift", () => {
    const a = createKartState();
    a.speed = 20;
    a.grounded = false;
    a.y = 50;
    drive(a, flatGround, 0.1, { steer: 1, drift: true });
    expect(a.driftDir).toBe(0);
  });
});
