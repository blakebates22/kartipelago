import { describe, expect, it } from "vitest";
import trackData from "../assets/data/track.json";
import tuning from "../assets/data/tuning.json";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack, type TrackData } from "../src/world/track";
import { crossGate } from "../src/race/checkpoints";
import { createFixedStep } from "../src/core/fixedStep";
import { downAt } from "../src/core/input";
import {
  createRace,
  formatTime,
  judgeStart,
  makeGates,
  standings,
  stepRacer,
  tickRace,
  type Race,
} from "../src/race/race";

const track = buildTrack(trackData as TrackData, tuning.track.sampleSpacing);
const cfg = { ...tuning.race, laps: 3 };
const dt = 1 / 120;

/** One step for racer 0 with the kart at (x, z). */
function step(race: Race, x: number, z: number, throttle = 0, onRoad = true, i = 0) {
  tickRace(race, dt);
  const kart = createKartState(x, z, 0, 0);
  return stepRacer(race, i, kart, onRoad, throttle, cfg, dt);
}

/** Drive racer i through a list of gate indices: from 2 m before each to 2 m past it. */
function passGates(race: Race, order: number[], i = 0) {
  for (const gi of order) {
    const g = race.gates[gi]!;
    for (const d of [-2, 2]) {
      tickRace(race, dt);
      stepRacer(race, i, createKartState(g.x + g.fx * d, g.z + g.fz * d, 0, g.y), true, 0, cfg, dt);
    }
  }
}

function started(racers = 1) {
  const race = createRace(track, cfg, racers);
  while (race.phase === "countdown") step(race, race.gates[0]!.x, race.gates[0]!.z);
  return race;
}

const lapOrder = (race: Race) => [...race.gates.keys()].slice(1).concat(0);

describe("gates", () => {
  it("are placed round the whole track, starting at the start line", () => {
    const gates = makeGates(track);
    expect(gates.length).toBeGreaterThanOrEqual(5);
    expect(gates[0]!.x).toBeCloseTo(track.start.x);
    expect(gates[0]!.z).toBeCloseTo(track.start.z);
  });

  it("are finite 3D rectangles crossed forward or back", () => {
    const g = {
      ...makeGates(track)[0]!,
      x: 0,
      y: 0,
      z: 0,
      fx: 0,
      fz: 1,
      heading: 0,
      left: 10,
      right: 10,
      height: 6,
      below: 2,
    };
    const at = (x: number, y: number, z: number) => ({ x, y, z });
    expect(crossGate(g, at(0, 0, -1), at(0, 0, 1))).toBe("forward");
    expect(crossGate(g, at(0, 0, 1), at(0, 0, -2))).toBe("backward");
    expect(crossGate(g, at(0, 0, 1), at(0, 0, -0.5))).toBeUndefined(); // within the hysteresis
    expect(crossGate(g, at(20, 0, -1), at(20, 0, 1))).toBeUndefined(); // beside it
    expect(crossGate(g, at(0, 9, -1), at(0, 9, 1))).toBeUndefined(); // over it
    expect(crossGate(g, at(0, 5, -1), at(0, 5, 1))).toBe("forward"); // through it, flying
  });
});

describe("race", () => {
  it("holds everyone at the line during the countdown, then goes", () => {
    expect(createRace(track, cfg).phase).toBe("countdown");
    expect(started().phase).toBe("racing");
  });

  it("counts a lap only when every checkpoint is passed in order", () => {
    const race = started();
    passGates(race, [1, 2, 0]);
    expect(race.racers[0]!.lap).toBe(1);
    expect(race.racers[0]!.lapTimes).toHaveLength(0);
  });

  it("completes laps, records times and finishes after the last lap", () => {
    const race = started();
    for (let lap = 0; lap < 3; lap++) passGates(race, lapOrder(race));
    const r = race.racers[0]!;
    expect(r.lapTimes).toHaveLength(3);
    expect(r.finished).toBe(true);
    expect(r.bestLap).toBe(Math.min(...r.lapTimes));
    expect(race.finishOrder).toEqual([0]);
  });

  it("respawns a kart stuck off the road (walled tracks) just past its last checkpoint", () => {
    const race = started();
    passGates(race, [1, 2, 3]);
    let spawn;
    for (let t = 0; t < cfg.respawnAfterSec + 0.1 && !spawn; t += dt) {
      spawn = step(race, 999, 999, 0, false).respawn;
    }
    expect(spawn).toEqual(race.gates[3]!.respawn);
    expect(race.racers[0]!.passed).toBe(3); // progress kept
  });

  it("doesn't respawn a kart for flying over the grass", () => {
    const race = started();
    const kart = createKartState(999, 999);
    kart.grounded = false;
    let spawn;
    for (let t = 0; t < 3; t += dt) {
      tickRace(race, dt);
      spawn ??= stepRacer(race, 0, kart, false, 0, cfg, dt).respawn;
    }
    expect(spawn).toBeUndefined();
  });
});

describe("positions", () => {
  it("rank by laps and checkpoints, then by distance to the next one", () => {
    const race = started(3);
    passGates(race, [1, 2], 1); // racer 1 is two checkpoints in
    passGates(race, [1], 2); // racer 2 one
    const g1 = race.gates[1]!;
    const at = [
      { x: g1.x - g1.fx * 5, z: g1.z - g1.fz * 5 }, // racer 0 hasn't reached gate 1
      { x: race.gates[2]!.x, z: race.gates[2]!.z },
      { x: g1.x + g1.fx * 1, z: g1.z + g1.fz * 1 },
    ];
    expect(standings(race, at)).toEqual([1, 2, 0]);
  });

  it("rank the grid front to back before anyone crosses the line", () => {
    const race = createRace(track, cfg, 2);
    const g0 = race.gates[0]!;
    const front = { x: g0.x - g0.fx * 5, z: g0.z - g0.fz * 5 };
    const back = { x: g0.x - g0.fx * 20, z: g0.z - g0.fz * 20 };
    expect(standings(race, [back, front])).toEqual([1, 0]);
  });

  it("keep finishers in the order they finished", () => {
    const race = started(2);
    for (let lap = 0; lap < 3; lap++) passGates(race, lapOrder(race), 1);
    for (let lap = 0; lap < 3; lap++) passGates(race, lapOrder(race), 0);
    expect(race.finishOrder).toEqual([1, 0]);
    const far = { x: 0, z: 0 };
    expect(standings(race, [far, far])).toEqual([1, 0]);
  });
});

/**
 * Run a start for racer 0. `down(clock)` says whether the throttle is held at that race
 * clock time; `simDt` is the fixed step.
 */
function startWith(down: (clock: number) => boolean, simDt = dt) {
  const race = createRace(track, cfg);
  let boost;
  const g = race.gates[0]!;
  // Run on past GO a little, so presses after GO are seen too.
  while (race.clock < 0.2) {
    tickRace(race, simDt);
    const ev = stepRacer(
      race,
      0,
      createKartState(g.x, g.z, 0, 0),
      true,
      down(race.clock) ? 1 : 0,
      cfg,
      simDt,
    );
    boost ??= ev.boost;
  }
  return { racer: race.racers[0]!, boost, tier: race.racers[0]!.start?.tier };
}

/** Press `frames` reference frames (60 fps) before GO and hold on. */
const pressFrames = (frames: number) => (clock: number) => clock >= -frames / 60 - 1e-9;

describe("start boost (GET READY... GO!)", () => {
  it("counts its windows at a 60 fps reference", () => {
    expect(cfg.startRefHz).toBe(60);
    expect(cfg.startStrongFrames).toBe(14);
    expect(cfg.startWeakFrames).toBe(29);
  });

  it("1. holding from 40 frames before GO is too early: no boost", () => {
    const { tier, boost } = startWith(pressFrames(40));
    expect(tier).toBe("early");
    expect(boost).toBeUndefined();
  });

  it("2. pressing 20 frames before GO and holding: a weak boost", () => {
    const { tier, boost } = startWith(pressFrames(20));
    expect(tier).toBe("weak");
    expect(boost).toEqual({ tier: "weak", mult: cfg.startWeakMult, seconds: cfg.startWeakSec });
  });

  it("3. pressing 10 frames before GO and holding: a strong boost", () => {
    const { tier, boost } = startWith(pressFrames(10));
    expect(tier).toBe("strong");
    expect(boost).toEqual({
      tier: "strong",
      mult: cfg.startStrongMult,
      seconds: cfg.startStrongSec,
    });
  });

  it("4. pressing 2 frames before GO and holding: a strong boost", () => {
    expect(startWith(pressFrames(2)).tier).toBe("strong");
  });

  it("5. pressing at GO: an ordinary start", () => {
    const { tier, boost } = startWith((c) => c >= 0);
    expect(tier).toBe("none");
    expect(boost).toBeUndefined();
  });

  it("6. pressing after GO: an ordinary start", () => {
    expect(startWith((c) => c >= 0.1).boost).toBeUndefined();
  });

  it("7. letting go before GO loses it, and pressing again doesn't earn another try", () => {
    const tapped = startWith((c) => c >= -10 / 60 && c < -5 / 60);
    expect(tapped.tier).toBe("released");
    expect(tapped.boost).toBeUndefined();
    // Too early, let go, then a perfectly timed second press: still nothing.
    const again = startWith((c) => (c >= -50 / 60 && c < -40 / 60) || c >= -8 / 60);
    expect(again.tier).toBe("released");
    expect(again.boost).toBeUndefined();
  });

  it("gives nothing for holding the throttle down from before GET READY", () => {
    const { tier, boost } = startWith(() => true);
    expect(tier).toBe("none");
    expect(boost).toBeUndefined();
  });

  it("puts the window edges where the frames say (14 strong, 15 weak, 29 weak, 30 early)", () => {
    expect(judgeStart(-14 / 60, true, cfg).tier).toBe("strong");
    expect(judgeStart(-15 / 60, true, cfg).tier).toBe("weak");
    expect(judgeStart(-29 / 60, true, cfg).tier).toBe("weak");
    expect(judgeStart(-30 / 60, true, cfg).tier).toBe("early");
    expect(judgeStart(-1 / 60, true, cfg).tier).toBe("strong");
    expect(judgeStart(-0.004, true, cfg).tier).toBe("strong"); // inside the last frame
    expect(judgeStart(-5 / 60, false, cfg).tier).toBe("released");
  });

  it("is the same at a finer simulation step (the game's 120 Hz is half a frame)", () => {
    for (const frames of [2, 10, 13.5, 15.6, 20, 28.5, 31, 40])
      expect(
        new Set([1 / 120, 1 / 240].map((h) => startWith(pressFrames(frames), h).tier)).size,
        `${frames} frames`,
      ).toBe(1);
  });

  it("8. is the same at 30, 60, 120 and 144 fps rendering (presses timed to the step)", () => {
    // The real loop: frames of 1/fps, each running the fixed steps due, each step
    // standing for a moment a little before the frame (core/loop.ts). A key press at
    // wall time T only shows from the next frame on, and only to steps after T.
    const run = (fps: number, pressMs: number) => {
      const race = createRace(track, cfg);
      const clock = createFixedStep(120, 8);
      const g = race.gates[0]!;
      let now = 0;
      while (race.clock < 0.2) {
        now += 1000 / fps;
        const steps = clock.advance(1 / fps);
        for (let i = 0; i < steps; i++) {
          const at = now - (steps - 1 - i + clock.alpha) * clock.stepSeconds * 1000;
          const seen = pressMs <= now; // the browser delivered the event before this frame
          tickRace(race, clock.stepSeconds);
          const held = downAt(seen, pressMs, at);
          stepRacer(
            race,
            0,
            createKartState(g.x, g.z, 0, 0),
            true,
            held ? 1 : 0,
            cfg,
            clock.stepSeconds,
          );
        }
      }
      return race.racers[0]!.start?.tier;
    };
    // GO is at wall time readySec (the race clock starts at -readySec with the loop).
    const goMs = cfg.readySec * 1000;
    for (const before of [40, 20, 15.5, 13, 10, 2])
      for (const fps of [30, 60, 120, 144]) {
        const want = before >= 30 ? "early" : before > 14 ? "weak" : "strong";
        expect(run(fps, goMs - (before / 60) * 1000), `${before} frames at ${fps} fps`).toBe(want);
      }
  });
});

describe("formatTime", () => {
  it("shows minutes, seconds and hundredths", () => {
    expect(formatTime(83.456)).toBe("1:23.46");
    expect(formatTime(5.1)).toBe("0:05.10");
  });
});
