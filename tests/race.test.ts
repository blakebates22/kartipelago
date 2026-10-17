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
  startTarget,
  stepRace,
  type Race,
} from "../src/race/race";

const track = buildTrack(trackData as TrackData, tuning.track.sampleSpacing);
const cfg = { ...tuning.race, laps: 3 };
const dt = 1 / 120;

/** Teleport-drive the kart through a list of gate indices, a little past each. */
function passGates(race: Race, order: number[]) {
  const kart = createKartState();
  for (const gi of order) {
    const g = race.gates[gi]!;
    for (const d of [-1, 1]) {
      kart.x = g.x + g.fx * d;
      kart.z = g.z + g.fz * d;
      stepRace(race, kart, true, 0, cfg, dt);
    }
  }
  return kart;
}

function started() {
  const race = createRace(track, cfg);
  const kart = createKartState(race.gates[0]!.x, race.gates[0]!.z);
  for (let t = 0; t <= cfg.readySec + dt; t += dt) stepRace(race, kart, true, 0, cfg, dt);
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
  it("holds you at the line during the countdown, then goes", () => {
    const race = createRace(track, cfg);
    expect(race.phase).toBe("countdown");
    const s = started();
    expect(s.phase).toBe("racing");
  });

  it("counts a lap only when every checkpoint is passed in order", () => {
    const race = started();
    passGates(race, [1, 2, 0]); // skipped most of the track
    expect(race.lap).toBe(1);
    expect(race.lapTimes).toHaveLength(0);
  });

  it("completes laps, records times and finishes after the last lap", () => {
    const race = started();
    for (let lap = 0; lap < 3; lap++) passGates(race, lapOrder(race));
    expect(race.lapTimes).toHaveLength(3);
    expect(race.phase).toBe("finished");
    expect(race.bestLap).toBe(Math.min(...race.lapTimes));
    expect(race.totalTime).toBeGreaterThan(0);
  });

  it("respawns you at the last checkpoint after sitting off the road", () => {
    const race = started();
    const kart = passGates(race, [1, 2, 3]);
    let spawn;
    for (let t = 0; t < cfg.respawnAfterSec + 0.1 && !spawn; t += dt) {
      spawn = stepRace(race, kart, false, 0, cfg, dt).respawn;
    }
    expect(spawn).toBe(race.gates[3]);
  });

  it("doesn't respawn you for flying over the grass", () => {
    const race = started();
    const kart = createKartState();
    kart.grounded = false;
    let spawn;
    for (let t = 0; t < 3; t += dt) spawn ??= stepRace(race, kart, false, 0, cfg, dt).respawn;
    expect(spawn).toBeUndefined();
  });
});

/** Run a start with a throttle press at `pressAt` (clock time), held through GO. */
function startWith(pressAt: number | undefined, holdFromStart = false) {
  const race = createRace(track, cfg);
  const kart = createKartState();
  let boost;
  for (let i = 0; race.phase === "countdown"; i++) {
    const clockAfter = race.clock + dt;
    const down = holdFromStart || (pressAt !== undefined && clockAfter >= pressAt);
    boost ??= stepRace(race, kart, true, down ? 1 : 0, cfg, dt).boost;
  }
  return { race, boost };
}

describe("start boost", () => {
  const target = startTarget(cfg);

  it("sits halfway between Get ready and GO", () => {
    expect(target).toBeCloseTo(-cfg.readySec / 2);
  });

  it("gives the strong boost for a press in the perfect window", () => {
    const { race, boost } = startWith(target + 0.02);
    expect(race.start?.tier).toBe("perfect");
    expect(boost?.mult).toBe(cfg.startPerfectMult);
  });

  it("gives the weaker boost for a press a bit too early", () => {
    const { race, boost } = startWith(target - cfg.perfectWindowSec - 0.1);
    expect(race.start?.tier).toBe("good");
    expect(boost?.mult).toBe(cfg.startGoodMult);
  });

  it("gives nothing for pressing way too early or late", () => {
    expect(startWith(target - 0.9).boost).toBeUndefined();
    expect(startWith(target + 0.3).race.start?.tier).toBe("late");
  });

  it("gives nothing for holding the throttle down from the very start", () => {
    const { race, boost } = startWith(undefined, true);
    expect(race.start?.tier).toBe("none");
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
