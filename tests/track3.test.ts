import { describe, expect, it } from "vitest";
import meadow from "../assets/data/track3.json";
import tuning from "../assets/data/tuning.json";
import roster from "../assets/data/characters.json";
import { NEUTRAL, type InputState } from "../src/core/input";
import { createDriver, driveAi } from "../src/ai/driver";
import { buildRacingLine } from "../src/ai/racingLine";
import { bumpKarts } from "../src/physics/bump";
import { createTrackGround } from "../src/physics/ground";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepSolids } from "../src/physics/walls";
import { gridSlot } from "../src/race/grid";
import { canDrive, createRace, stepRacer, tickRace } from "../src/race/race";
import { applyCharacter, type Character } from "../src/vehicles/character";
import { createKartState, stepKart, type KartState } from "../src/vehicles/kart";
import { startZipper } from "../src/vehicles/zipper";
import { collectBananas, createBananaField, stepBananaField } from "../src/world/bananas";
import {
  boundarySolids,
  buildTunnel,
  insideBox,
  placeTrees,
  tunnelSolids,
  type SolidBox,
} from "../src/world/solids";
import { buildTrack, type TrackData } from "../src/world/track";
import { buildZippers, enteredZipper } from "../src/world/zippers";

// Meadow Run: an open track. Wide road, no walls; tunnel rock, trees and the map
// boundary are the only things to hit.
const dt = 1 / 120;
const data = meadow as TrackData;
const track = buildTrack(data, tuning.track.sampleSpacing);
const tunnels = (data.tunnels ?? []).map((t) => buildTunnel(track, t));
const fixed = [
  ...tunnels.flatMap(tunnelSolids),
  ...boundarySolids(track, tuning.scenery.boundaryMargin),
];
const trees = placeTrees(track, tuning.scenery, fixed);
const solids = [...fixed, ...trees];
const pads = buildZippers(track, data.zippers ?? [], tuning.track);
const line = buildRacingLine(track, {
  margin: data.aiLineMargin ?? tuning.ai.lineMargin,
  span: tuning.ai.lineSpan,
  iterations: tuning.ai.lineIterations,
});
const walls = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
const find = (id: string) => roster.characters.find((c) => c.id === id) as Character;

function drive(s: KartState, seconds: number, input: Partial<InputState>) {
  let hits = 0;
  for (let t = 0; t < seconds; t += dt) {
    stepImpacts(s, tuning.collision, dt);
    stepKart(s, { ...NEUTRAL, ...input }, tuning.vehicle, dt);
    if (stepSolids(s, solids, walls, dt)) hits++;
  }
  return hits;
}

/** A full race of AI karts, as in the game loop on an open track. */
function aiRace(ids: string[]) {
  const race = createRace(track, tuning.race, ids.length);
  const field = createBananaField(track, data.bananas ?? [], () => createTrackGround(track), false);
  const grounds = ids.map(() => createTrackGround(track));
  const drivers = ids.map((_, i) => createDriver(line, i + 1, tuning.ai));
  const karts = ids.map((_, i) => {
    const g = gridSlot(track, i);
    return createKartState(g.x, g.z, g.heading, g.y);
  });
  const stats = { hits: 0, offRoad: 0, steps: 0, respawns: 0 };
  for (let t = 0; t < 200 && race.finishOrder.length < ids.length; t += dt) {
    tickRace(race, dt);
    const moment = {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startRefHz: tuning.race.startRefHz,
    };
    ids.forEach((id, i) => {
      const k = karts[i]!;
      const cfg = applyCharacter(tuning.vehicle, find(id), tuning.stats);
      const want = driveAi(drivers[i]!, k, cfg, tuning.ai, moment);
      stepImpacts(k, tuning.collision, dt);
      stepKart(k, canDrive(race) ? want : NEUTRAL, cfg, dt);
      if (enteredZipper(k, pads)) startZipper(k, want.throttle, cfg);
      if (stepSolids(k, solids, walls, dt)) stats.hits++;
      stepVertical(k, grounds[i]!, tuning.physics, dt);
      collectBananas(field, i, k, tuning.bananas);
      const onRoad = grounds[i]!.at(k.x, k.z).onRoad;
      if (!onRoad) stats.offRoad++;
      if (stepRacer(race, i, k, onRoad, want.throttle, tuning.race, dt).respawn) stats.respawns++;
      stats.steps++;
    });
    bumpKarts(karts, tuning.physics.kartBump);
    stepBananaField(field, tuning.bananas, dt);
  }
  return { race, stats };
}

describe("Meadow Run", () => {
  it("is a flat, wide, open lap of about 800-900 m", () => {
    expect(data.open).toBe(true);
    expect(track.length).toBeGreaterThan(800);
    expect(track.length).toBeLessThan(900);
    for (const s of track.samples) {
      expect(s.pos.y).toBeCloseTo(0, 6);
      expect(s.width).toBeGreaterThanOrEqual(28);
    }
  });

  it("keeps separate parts of the course well apart (grass between them)", () => {
    const n = track.samples.length;
    for (let i = 0; i < n; i += 3) {
      for (let j = i + 3; j < n; j += 3) {
        const a = track.samples[i]!;
        const b = track.samples[j]!;
        const along = Math.min(b.dist - a.dist, track.length - (b.dist - a.dist));
        if (along < 150) continue;
        expect(Math.hypot(a.pos.x - b.pos.x, a.pos.z - b.pos.z)).toBeGreaterThan(60);
      }
    }
  });

  it("runs its tunnel along a straight, with the road clear between the rock", () => {
    for (const spot of data.tunnels ?? []) {
      const t = buildTunnel(track, spot);
      const [left, right] = tunnelSolids(t) as [SolidBox, SolidBox];
      for (const s of track.samples) {
        if (s.dist < spot.from || s.dist > spot.to) continue;
        const fx = Math.sin(t.heading);
        const fz = Math.cos(t.heading);
        const across = (s.pos.x - t.x) * fz - (s.pos.z - t.z) * fx;
        expect(Math.abs(across)).toBeLessThan(0.5);
        for (const side of [-1, 1]) {
          const ex = s.pos.x + fz * side * (s.width / 2 - 0.1);
          const ez = s.pos.z - fx * side * (s.width / 2 - 0.1);
          expect(insideBox(left, ex, ez)).toBe(false);
          expect(insideBox(right, ex, ez)).toBe(false);
        }
      }
    }
  });

  it("keeps trees off the road and the whole course inside the boundary", () => {
    const ground = createTrackGround(track);
    expect(trees.length).toBeGreaterThan(80);
    for (const t of trees) expect(ground.at(t.x, t.z).onRoad).toBe(false);
    const edges = fixed.filter((s) => s.look === "boundary");
    for (const s of track.samples)
      for (const e of edges) expect(insideBox(e, s.pos.x, s.pos.z, 5)).toBe(false);
  });

  it("lets you drive off the road onto the grass, with no respawn", () => {
    const race = createRace(track, tuning.race, 1);
    expect(race.open).toBe(true);
    const g = track.samples[60]!;
    const s = createKartState(g.pos.x + 40, g.pos.z, 0);
    const ground = createTrackGround(track);
    expect(ground.at(s.x, s.z).onRoad).toBe(false);
    race.phase = "racing";
    for (let t = 0; t < 2; t += dt)
      expect(stepRacer(race, 0, s, false, 0, tuning.race, dt).respawn).toBeUndefined();
  });

  it("stops you at the map boundary", () => {
    const north = fixed.find((s) => s.look === "boundary" && s.heading !== 0) as SolidBox;
    const s = createKartState(north.x, north.z - 30, 0); // heading +Z, toward it
    const top = north.z > track.samples[0]!.pos.z;
    if (!top) s.heading = s.velAngle = Math.PI;
    s.speed = 25;
    const hits = drive(s, 3, { throttle: 1 });
    expect(hits).toBeGreaterThan(0);
    expect(Math.abs(s.z - north.z)).toBeGreaterThan(north.halfWidth);
  });

  it("blocks you at the side of a tunnel instead of letting you into it", () => {
    const t = tunnels[0]!;
    const rock = tunnelSolids(t)[0]!;
    // Start out on the grass beside the rock, driving straight at its side.
    const ox = Math.sin(rock.heading + Math.PI / 2);
    const oz = Math.cos(rock.heading + Math.PI / 2);
    const side = (rock.x - t.x) * ox + (rock.z - t.z) * oz > 0 ? 1 : -1;
    const start = rock.halfWidth + 20;
    const s = createKartState(
      rock.x + ox * side * start,
      rock.z + oz * side * start,
      Math.atan2(-ox * side, -oz * side),
    );
    s.speed = 25;
    const hits = drive(s, 2, { throttle: 1 });
    expect(hits).toBeGreaterThan(0);
    // Still outside the rock, on the grass side: not pushed through into the tunnel.
    const across = (s.x - rock.x) * ox + (s.z - rock.z) * oz;
    expect(across * side).toBeGreaterThan(rock.halfWidth);
  });

  it("lets an AI Speedster race three laps, staying on the road and clear of obstacles", () => {
    const { race, stats } = aiRace(["speedster"]);
    const r = race.racers[0]!;
    expect(r.finished).toBe(true);
    for (const lap of r.lapTimes.slice(1)) {
      expect(lap).toBeGreaterThan(24);
      expect(lap).toBeLessThan(34);
    }
    expect(stats.respawns).toBe(0);
    expect(stats.hits / stats.steps).toBeLessThan(0.005);
    expect(stats.offRoad / stats.steps).toBeLessThan(0.03);
  });

  it("finishes a full field of eight", () => {
    const { race, stats } = aiRace(Array<string>(8).fill(roster.default));
    expect(race.finishOrder).toHaveLength(8);
    expect(stats.respawns).toBe(0);
  });
});
