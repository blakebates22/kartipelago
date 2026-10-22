import { describe, expect, it } from "vitest";
import trackData from "../assets/data/track.json";
import tuning from "../assets/data/tuning.json";
import roster from "../assets/data/characters.json";
import { NEUTRAL } from "../src/core/input";
import { createDriver, driveAi } from "../src/ai/driver";
import { buildRacingLine } from "../src/ai/racingLine";
import { bumpKarts } from "../src/physics/bump";
import { createTrackGround } from "../src/physics/ground";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepWalls } from "../src/physics/walls";
import { gridSlot } from "../src/race/grid";
import { canDrive, createRace, standings, stepRacer, tickRace } from "../src/race/race";
import { applyCharacter, type Character } from "../src/vehicles/character";
import { createKartState, stepKart, type KartState } from "../src/vehicles/kart";
import { startZipper } from "../src/vehicles/zipper";
import { collectBananas, createBananaField, stepBananaField } from "../src/world/bananas";
import { buildZippers, enteredZipper } from "../src/world/zippers";
import { buildTrack, type TrackData } from "../src/world/track";

const dt = 1 / 120;
const track = buildTrack(trackData as TrackData, tuning.track.sampleSpacing);
const pads = buildZippers(track, (trackData as TrackData).zippers ?? [], tuning.track);
const bananaSpots = (trackData as TrackData).bananas ?? [];
const ai = tuning.ai;
const line = buildRacingLine(track, {
  margin: ai.lineMargin,
  span: ai.lineSpan,
  iterations: ai.lineIterations,
});
const find = (id: string) => roster.characters.find((c) => c.id === id) as Character;

describe("racing line", () => {
  it("stays on the road, inside the margin", () => {
    for (let i = 0; i < line.n; i++) {
      const s = track.samples[i]!;
      const off = Math.hypot(line.x[i]! - s.pos.x, line.z[i]! - s.pos.z);
      expect(off).toBeLessThanOrEqual(s.width / 2 - ai.lineMargin + 0.01);
    }
  });

  it("is smoother than the centre line overall (it cuts corners)", () => {
    // Total bending: the sum of squared curvature. A racing line straightens the lap.
    const bending = (c: ArrayLike<number>) => Array.from(c, (k) => k * k).reduce((a, b) => a + b);
    const centre = buildRacingLine(track, { margin: 1000, span: ai.lineSpan, iterations: 0 });
    expect(bending(line.curvature)).toBeLessThan(bending(centre.curvature));
  });
});

/** Run a full race with every entrant driven by the AI. */
function aiRace(ids: string[], seconds = 200) {
  const race = createRace(track, tuning.race, ids.length);
  const karts: KartState[] = [];
  const grounds = ids.map(() => createTrackGround(track));
  const drivers = ids.map((_, i) => createDriver(line, i + 1, ai));
  ids.forEach((_, i) => {
    const g = gridSlot(track, i);
    karts.push(createKartState(g.x, g.z, g.heading, g.y));
  });
  const stats = { wallSteps: 0, driftSteps: 0, steps: 0, respawns: 0 };
  const field = createBananaField(track, bananaSpots, () => createTrackGround(track));
  for (let t = 0; t < seconds && race.finishOrder.length < ids.length; t += dt) {
    tickRace(race, dt);
    const moment = {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startRefHz: tuning.race.startRefHz,
    };
    ids.forEach((id, i) => {
      const k = karts[i]!;
      const cfg = applyCharacter(tuning.vehicle, find(id), tuning.stats);
      const want = driveAi(drivers[i]!, k, cfg, ai, moment);
      stepImpacts(k, tuning.collision, dt);
      stepKart(k, canDrive(race) ? want : NEUTRAL, cfg, dt);
      if (enteredZipper(k, pads)) startZipper(k, want.throttle, cfg);
      collectBananas(field, 0, k, tuning.bananas);
      if (
        stepWalls(
          k,
          grounds[i]!,
          { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight },
          dt,
        )
      )
        stats.wallSteps++;
      stepVertical(k, grounds[i]!, tuning.physics, dt);
      const ev = stepRacer(
        race,
        i,
        k,
        grounds[i]!.at(k.x, k.z).onRoad,
        want.throttle,
        tuning.race,
        dt,
      );
      if (ev.respawn) stats.respawns++;
      if (k.driftDir) stats.driftSteps++;
      stats.steps++;
    });
    bumpKarts(karts, tuning.physics.kartBump);
    stepBananaField(field, tuning.bananas, dt);
  }
  return { race, karts, stats };
}

describe("AI driver", () => {
  const solo = aiRace(["speedster"]);

  it("finishes three laps on its own", () => {
    expect(solo.race.racers[0]!.finished).toBe(true);
  });

  it("drifts for a good share of the lap and rarely touches a wall", () => {
    expect(solo.stats.driftSteps / solo.stats.steps).toBeGreaterThan(0.15);
    expect(solo.stats.wallSteps / solo.stats.steps).toBeLessThan(0.02);
    expect(solo.stats.respawns).toBe(0);
  });

  it("laps faster than driving the centre line with no drifting", () => {
    // About 30 s per lap is what the plain centre-line autopilot manages.
    expect(Math.max(...solo.race.racers[0]!.lapTimes.slice(1))).toBeLessThan(29);
  });
});

describe("a full eight-kart race", () => {
  const ids = [
    "speedster",
    "nimble",
    "heavy",
    "allrounder",
    "speedster",
    "nimble",
    "heavy",
    "allrounder",
  ];
  const full = aiRace(ids, 260);

  it("gets every kart to the finish", () => {
    expect(full.race.finishOrder).toHaveLength(8);
    expect(full.stats.respawns).toBe(0);
  });

  it("ranks the finishers in finishing order", () => {
    expect(standings(full.race, full.karts)).toEqual(full.race.finishOrder);
  });
});

describe("grid", () => {
  it("puts every slot on the road, behind the line, apart from each other", () => {
    const ground = createTrackGround(track);
    const slots = Array.from({ length: 8 }, (_, i) => gridSlot(track, i));
    for (const s of slots) expect(ground.at(s.x, s.z).onRoad).toBe(true);
    for (let i = 0; i < 8; i++) {
      for (let j = i + 1; j < 8; j++) {
        expect(Math.hypot(slots[i]!.x - slots[j]!.x, slots[i]!.z - slots[j]!.z)).toBeGreaterThan(3);
      }
    }
  });
});

describe("bumping", () => {
  it("pushes overlapping karts apart and shares their closing speed", () => {
    const a = createKartState(0, 0, 0);
    const b = createKartState(0, 1, 0);
    a.speed = 20;
    b.speed = 10;
    expect(bumpKarts([a, b], tuning.physics.kartBump)).toBe(1);
    expect(b.z - a.z).toBeCloseTo(tuning.physics.kartBump * 2);
    expect(a.speed).toBeCloseTo(15);
    expect(b.speed).toBeCloseTo(15);
  });

  it("ignores a kart flying overhead", () => {
    const a = createKartState(0, 0, 0);
    const b = createKartState(0, 1, 0, 4);
    expect(bumpKarts([a, b], tuning.physics.kartBump)).toBe(0);
  });
});

describe("AI at the start", () => {
  /** Each rival's start, with the race's rules, from its own throttle in the countdown. */
  function rivalStarts(n: number) {
    const race = createRace(track, tuning.race, n);
    const drivers = Array.from({ length: n }, (_, i) => createDriver(line, i + 1, ai));
    const karts = Array.from({ length: n }, (_, i) => {
      const g = gridSlot(track, i);
      return createKartState(g.x, g.z, g.heading, g.y);
    });
    const moved = new Set<number>();
    const startPos = karts.map((k) => ({ x: k.x, z: k.z }));
    while (race.clock < 0.1) {
      tickRace(race, dt);
      const moment = {
        countdown: race.phase === "countdown",
        clock: race.clock,
        startRefHz: tuning.race.startRefHz,
      };
      drivers.forEach((d, i) => {
        const k = karts[i]!;
        const want = driveAi(d, k, tuning.vehicle, ai, moment);
        if (race.phase === "countdown") expect(want.steer).toBe(0);
        stepKart(k, canDrive(race) ? want : NEUTRAL, tuning.vehicle, dt);
        if (
          race.phase === "countdown" &&
          Math.hypot(k.x - startPos[i]!.x, k.z - startPos[i]!.z) > 1e-6
        )
          moved.add(i);
        stepRacer(race, i, k, true, want.throttle, tuning.race, dt);
      });
    }
    return { tiers: race.racers.map((r) => r.start?.tier), moved };
  }

  it("10. no rival moves before GO", () => {
    expect(rivalStarts(8).moved.size).toBe(0);
  });

  it("plays by the same windows: a mix of strong, weak and ordinary starts, not all strong", () => {
    const { tiers } = rivalStarts(16);
    expect(tiers.filter((t) => t === "strong").length).toBeGreaterThan(0);
    expect(tiers.filter((t) => t !== "strong").length).toBeGreaterThan(0);
    expect(tiers.every((t) => t !== "early" && t !== "released")).toBe(true);
  });
});
