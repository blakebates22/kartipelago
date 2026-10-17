import { describe, expect, it } from "vitest";
import trackData from "../assets/data/track.json";
import tuning from "../assets/data/tuning.json";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack, type TrackData } from "../src/world/track";
import {
  createRace,
  crossed,
  formatTime,
  judgeStart,
  makeGates,
  standings,
  startTarget,
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
  const kart = createKartState(x, z);
  return stepRacer(race, i, kart, onRoad, throttle, cfg, dt);
}

/** Teleport racer 0 through a list of gate indices, a little past each. */
function passGates(race: Race, order: number[], i = 0) {
  for (const gi of order) {
    const g = race.gates[gi]!;
    for (const d of [-1, 1]) {
      tickRace(race, dt);
      stepRacer(race, i, createKartState(g.x + g.fx * d, g.z + g.fz * d), true, 0, cfg, dt);
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
  it("are spaced around the whole track, starting at the start line", () => {
    const gates = makeGates(track, cfg.checkpointSpacing);
    expect(gates.length).toBeGreaterThanOrEqual(8);
    expect(gates[0]!.x).toBeCloseTo(track.start.x);
    expect(gates[0]!.z).toBeCloseTo(track.start.z);
  });

  it("count only forward crossings inside the road", () => {
    const g = { x: 0, y: 0, z: 0, fx: 0, fz: 1, heading: 0, halfWidth: 10 };
    expect(crossed(g, 0, -1, 0, 1)).toBe(true);
    expect(crossed(g, 0, 1, 0, -1)).toBe(false); // backwards
    expect(crossed(g, 20, -1, 20, 1)).toBe(false); // outside the road
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

  it("respawns a kart at its last checkpoint after sitting off the road", () => {
    const race = started();
    passGates(race, [1, 2, 3]);
    let spawn;
    for (let t = 0; t < cfg.respawnAfterSec + 0.1 && !spawn; t += dt) {
      spawn = step(race, 999, 999, 0, false).respawn;
    }
    expect(spawn).toBe(race.gates[3]);
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

/** Run a start for racer 0 with a throttle press at `pressAt` (clock time). */
function startWith(pressAt: number | undefined, holdFromStart = false) {
  const race = createRace(track, cfg);
  let boost;
  while (race.phase === "countdown") {
    const down = holdFromStart || (pressAt !== undefined && race.clock + dt >= pressAt);
    boost ??= step(race, 0, 0, down ? 1 : 0).boost;
  }
  return { racer: race.racers[0]!, boost };
}

describe("start boost", () => {
  const target = startTarget(cfg);

  it("sits halfway between Get ready and GO", () => {
    expect(target).toBeCloseTo(-cfg.readySec / 2);
  });

  it("gives the strong boost for a press in the perfect window", () => {
    const { racer, boost } = startWith(target + 0.02);
    expect(racer.start?.tier).toBe("perfect");
    expect(boost?.mult).toBe(cfg.startPerfectMult);
  });

  it("gives the weaker boost for a press a bit too early", () => {
    const { racer, boost } = startWith(target - cfg.perfectWindowSec - 0.1);
    expect(racer.start?.tier).toBe("good");
    expect(boost?.mult).toBe(cfg.startGoodMult);
  });

  it("gives nothing for pressing way too early or late", () => {
    expect(startWith(target - 0.9).boost).toBeUndefined();
    expect(startWith(target + 0.3).racer.start?.tier).toBe("late");
  });

  it("gives nothing for holding the throttle down from the very start", () => {
    const { racer, boost } = startWith(undefined, true);
    expect(racer.start?.tier).toBe("none");
    expect(boost).toBeUndefined();
  });

  it("needs the press still held at GO", () => {
    expect(judgeStart(target, false, cfg).tier).toBe("none");
  });
});

describe("formatTime", () => {
  it("shows minutes, seconds and hundredths", () => {
    expect(formatTime(83.456)).toBe("1:23.46");
    expect(formatTime(5.1)).toBe("0:05.10");
  });
});
