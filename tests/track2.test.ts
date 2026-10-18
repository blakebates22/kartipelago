import { describe, expect, it } from "vitest";
import ribbon from "../assets/data/track2.json";
import tuning from "../assets/data/tuning.json";
import roster from "../assets/data/characters.json";
import { NEUTRAL } from "../src/core/input";
import { createDriver, driveAi } from "../src/ai/driver";
import { buildRacingLine } from "../src/ai/racingLine";
import { createTrackGround } from "../src/physics/ground";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepWalls } from "../src/physics/walls";
import { gridSlot } from "../src/race/grid";
import {
  canDrive,
  createRace,
  standings,
  startTarget,
  stepRacer,
  tickRace,
} from "../src/race/race";
import { applyCharacter, type Character } from "../src/vehicles/character";
import { createKartState, stepKart } from "../src/vehicles/kart";
import { startZipper } from "../src/vehicles/zipper";
import { collectBananas, createBananaField, stepBananaField } from "../src/world/bananas";
import { buildZippers, enteredZipper } from "../src/world/zippers";
import { acrossRoad, buildTrack, type TrackData } from "../src/world/track";

// Ribbon Ridge: the second track, built around long linked drifts and direction changes.
const dt = 1 / 120;
const track = buildTrack(ribbon as TrackData, tuning.track.sampleSpacing);
const pads = buildZippers(track, (ribbon as TrackData).zippers ?? [], tuning.track);
const bananaSpots = (ribbon as TrackData).bananas ?? [];
const line = buildRacingLine(track, {
  margin: tuning.ai.lineMargin,
  span: tuning.ai.lineSpan,
  iterations: tuning.ai.lineIterations,
});

describe("Ribbon Ridge", () => {
  it("is a lap of roughly 700-800 m that never dips under the ground", () => {
    expect(track.length).toBeGreaterThan(700);
    expect(track.length).toBeLessThan(800);
    for (const s of track.samples) {
      expect(acrossRoad(s, -1).y).toBeGreaterThanOrEqual(-1e-9);
      expect(acrossRoad(s, 1).y).toBeGreaterThanOrEqual(-1e-9);
    }
  });

  it("has corners sized for drifting: nothing tighter than a full-in drift", () => {
    const n = track.samples.length;
    for (let i = 0; i < n; i++) {
      const a = track.samples[(i - 3 + n) % n]!.pos;
      const b = track.samples[i]!.pos;
      const c = track.samples[(i + 3) % n]!.pos;
      const ab = Math.hypot(b.x - a.x, b.z - a.z);
      const bc = Math.hypot(c.x - b.x, c.z - b.z);
      const ca = Math.hypot(a.x - c.x, a.z - c.z);
      const cross = Math.abs((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x));
      if (cross > 1e-6) expect((ab * bc * ca) / (2 * cross)).toBeGreaterThan(20);
    }
  });

  it("puts every grid slot on the road", () => {
    const ground = createTrackGround(track);
    for (let i = 0; i < 8; i++) {
      const s = gridSlot(track, i);
      expect(ground.at(s.x, s.z).onRoad).toBe(true);
    }
  });

  it("ranks the grid front to back, with the player's back slot last", () => {
    const race = createRace(track, tuning.race, 8);
    const spots = Array.from({ length: 8 }, (_, i) => gridSlot(track, i));
    expect(standings(race, spots)).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
  });

  it("lets an AI Speedster race three clean laps of 25-30 s (less with bananas), mostly drifting", () => {
    const cfg = applyCharacter(
      tuning.vehicle,
      roster.characters.find((c) => c.id === "speedster") as Character,
      tuning.stats,
    );
    const ground = createTrackGround(track);
    const g = gridSlot(track, 0);
    const kart = createKartState(g.x, g.z, g.heading, g.y);
    const race = createRace(track, tuning.race, 1);
    const driver = createDriver(line, 1, tuning.ai);
    const stats = { wall: 0, drift: 0, air: 0, steps: 0, respawns: 0 };
    const field = createBananaField(track, bananaSpots, () => createTrackGround(track));
    for (let t = 0; t < 150 && !race.racers[0]!.finished; t += dt) {
      tickRace(race, dt);
      const moment = {
        countdown: race.phase === "countdown",
        clock: race.clock,
        startTarget: startTarget(tuning.race),
      };
      const want = driveAi(driver, kart, cfg, tuning.ai, moment);
      stepImpacts(kart, tuning.collision, dt);
      stepKart(kart, canDrive(race) ? want : NEUTRAL, cfg, dt);
      if (enteredZipper(kart, pads)) startZipper(kart, want.throttle, cfg);
      collectBananas(field, 0, kart, tuning.bananas);
      stepBananaField(field, tuning.bananas, dt);
      const walls = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
      if (stepWalls(kart, ground, walls, dt)) stats.wall++;
      stepVertical(kart, ground, tuning.physics, dt);
      const onRoad = ground.at(kart.x, kart.z).onRoad;
      if (stepRacer(race, 0, kart, onRoad, want.throttle, tuning.race, dt).respawn)
        stats.respawns++;
      if (kart.driftDir) stats.drift++;
      if (!kart.grounded) stats.air++;
      stats.steps++;
    }
    const r = race.racers[0]!;
    expect(r.finished).toBe(true);
    // 25-30 s at normal speed; holding ten bananas (it collects them) takes ~2 s off.
    for (const lap of r.lapTimes.slice(1)) {
      expect(lap).toBeGreaterThan(21);
      expect(lap).toBeLessThan(30);
    }
    expect(stats.respawns).toBe(0);
    expect(stats.wall / stats.steps).toBeLessThan(0.03);
    expect(stats.drift / stats.steps).toBeGreaterThan(0.4);
    // No jumps on this track: the kart should essentially never leave the road.
    expect(stats.air / stats.steps).toBeLessThan(0.01);
  });
});
