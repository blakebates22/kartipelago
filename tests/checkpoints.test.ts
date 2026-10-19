// Checkpoint progression: the acceptance scenarios (A-N) for DKR-style checkpoints.
// Karts are moved along a real course (Riverbend Palms) in small steps, on and off the
// road, flying, reversing and respawning, the way the race steps them.
import { readFile } from "node:fs/promises";
import { beforeAll, describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { crossGate, type CheckpointGate } from "../src/race/checkpoints";
import {
  createRace,
  respawnSpot,
  standings,
  stepRacer,
  teleported,
  tickRace,
  type Race,
} from "../src/race/race";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack, type Track } from "../src/world/track";
import { loadTrackPackage, parseCheckpoints, type PackageReader } from "../src/world/trackPackage";
import { aiLap } from "./aiLap";

const cfg = { ...tuning.race, laps: 3 };
const dt = 1 / 120;
const reader =
  (id: string, dir = "../public/tracks/"): PackageReader =>
  async (file) => {
    const b = await readFile(new URL(`${dir}${id}/${file}`, import.meta.url));
    return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
  };

let track: Track;
let pkgGates: CheckpointGate[];
beforeAll(async () => {
  const p = await loadTrackPackage(reader("riverbend_palms"), { visual: false });
  pkgGates = p.trackData.gates!;
  track = buildTrack(p.trackData, tuning.track.sampleSpacing);
});

/** A point `off` metres right of the route, `up` above it, at distance d round the lap. */
function at(d: number, off = 0, up = 0) {
  const L = track.length;
  const dd = ((d % L) + L) % L;
  const ss = track.samples;
  let i = 0;
  while (i + 1 < ss.length && ss[i + 1]!.dist <= dd) i++;
  const a = ss[i]!;
  const b = ss[(i + 1) % ss.length]!;
  const span = (i + 1 < ss.length ? b.dist : L) - a.dist;
  const f = span > 0 ? (dd - a.dist) / span : 0;
  const h = Math.hypot(a.forward.x, a.forward.z);
  const x = a.pos.x + (b.pos.x - a.pos.x) * f;
  const y = a.pos.y + (b.pos.y - a.pos.y) * f;
  const z = a.pos.z + (b.pos.z - a.pos.z) * f;
  // Right of the direction of travel is (-fz, fx).
  return { x: x - (a.forward.z / h) * off, y: y + up, z: z + (a.forward.x / h) * off };
}

function started(n = 1): Race {
  const race = createRace(track, cfg, n);
  while (race.phase === "countdown") {
    tickRace(race, dt);
    for (let i = 0; i < n; i++) stepRacer(race, i, kartAt(at(-6)), true, 0, cfg, dt);
  }
  return race;
}

function kartAt(p: { x: number; y: number; z: number }) {
  const k = createKartState(p.x, p.z, 0, p.y);
  k.y = p.y;
  return k;
}

/**
 * Drive racer i from distance d0 to d1 (backwards if d1 < d0), `step` metres at a time,
 * at the offset and height the functions give. Returns the kart's last position.
 */
function drive(
  race: Race,
  d0: number,
  d1: number,
  off: (d: number) => number = () => 0,
  up: (d: number) => number = () => 0,
  i = 0,
  step = 1.5,
) {
  const n = Math.max(1, Math.ceil(Math.abs(d1 - d0) / step));
  let p = at(d0, off(d0), up(d0));
  for (let k = 0; k <= n; k++) {
    const d = d0 + ((d1 - d0) * k) / n;
    p = at(d, off(d), up(d));
    tickRace(race, dt);
    stepRacer(race, i, kartAt(p), true, 0, cfg, dt);
  }
  return p;
}

const gateDist = (race: Race, idx: number) => {
  const g = race.gates[idx]!;
  let best = 0;
  let bd = Infinity;
  for (const s of track.samples) {
    const d = (s.pos.x - g.x) ** 2 + (s.pos.z - g.z) ** 2;
    if (d < bd) {
      bd = d;
      best = s.dist;
    }
  }
  return best;
};

describe("checkpoint progression (acceptance)", () => {
  it("uses the course's own checkpoints, with a shortcut gate", () => {
    const race = createRace(track, cfg);
    expect(race.course.length).toBeGreaterThanOrEqual(8);
    expect(race.course.length).toBeLessThan(20); // a few wide gates, not hundreds
    expect(pkgGates.some((g) => g.route !== "main")).toBe(true);
    for (const g of race.gates) expect(g.left + g.right).toBeGreaterThan(30); // wider than the road
  });

  it("A: a normal lap registers every checkpoint and completes the lap", () => {
    const race = started();
    drive(race, -6, track.length + 5);
    const r = race.racers[0]!;
    expect(r.passed).toBe(race.course.length);
    expect(r.lapTimes).toHaveLength(1);
    expect(r.lap).toBe(2);
  });

  it("B: driving on the grass between checkpoints keeps progress", () => {
    const race = started();
    // 30 m off the road between gates, back near it at each gate.
    const gd = race.gates.map((_, k) => gateDist(race, k));
    const off = (d: number) => {
      const near = Math.min(
        ...gd.map((g) => Math.min(Math.abs(d - g), Math.abs(d - g - track.length))),
      );
      return 4 + 26 * Math.min(1, Math.max(0, (near - 8) / 20)); // eases out onto the grass
    };
    drive(race, -6, track.length + 5, off);
    expect(race.racers[0]!.lapTimes).toHaveLength(1);
  });

  it("C: a very wide line through every checkpoint still counts", () => {
    const race = started();
    drive(race, -6, track.length + 5, () => 20); // 13 m beyond the road's edge
    expect(race.racers[0]!.lapTimes).toHaveLength(1);
  });

  it("D: flying through a checkpoint counts, flying right over it doesn't", () => {
    const race = started();
    const g2 = gateDist(race, 2);
    drive(race, -6, g2 - 20);
    drive(
      race,
      g2 - 20,
      g2 + 20,
      () => 0,
      () => 4,
    ); // 4 m up: through the gate
    expect(race.racers[0]!.last).toBe(2);
    const g3 = gateDist(race, 3);
    drive(race, g2 + 20, g3 - 20);
    drive(
      race,
      g3 - 20,
      g3 + 20,
      () => 0,
      () => 14,
    ); // 14 m up: over it
    expect(race.racers[0]!.last).toBe(2);
    expect(race.racers[0]!.lastEvent?.kind).toBe("accepted");
  });

  it("E: skipping a checkpoint and crossing the line gives no lap", () => {
    const race = started();
    const g4 = gateDist(race, 4);
    // Go far round gate 4 (outside it), then carry on round to the line.
    drive(race, -6, track.length + 5, (d) => (Math.abs(d - g4) < 15 ? 80 : 0));
    const r = race.racers[0]!;
    expect(r.lapTimes).toHaveLength(0);
    expect(r.next).toBe(4); // still waiting for it
    expect(r.lastEvent?.kind).toBe("rejected");
  });

  it("F: reversing over the line and back gives no extra lap", () => {
    const race = started();
    drive(race, -6, track.length + 5);
    expect(race.racers[0]!.lapTimes).toHaveLength(1);
    drive(race, track.length + 5, track.length - 10); // back over the line
    drive(race, track.length - 10, track.length + 10); // and forward again
    const r = race.racers[0]!;
    expect(r.lapTimes).toHaveLength(1);
    expect(r.completedLaps).toBe(1);
    expect(r.lastEvent?.kind).toBe("accepted");
  });

  it("G: driving backwards, then turning round, recovers progress", () => {
    const race = started();
    const g3 = gateDist(race, 3);
    drive(race, -6, g3 + 10);
    expect(race.racers[0]!.last).toBe(3);
    drive(race, g3 + 10, g3 - 30); // the wrong way, back through gate 3
    expect(race.racers[0]!.next).toBe(3);
    expect(race.racers[0]!.lastEvent?.kind).toBe("reversed");
    drive(race, g3 - 30, track.length + 5); // turn round and carry on
    expect(race.racers[0]!.lapTimes).toHaveLength(1);
  });

  it("H: wandering far from the road keeps the checkpoints you've passed", () => {
    const race = started(2);
    const g3 = gateDist(race, 3);
    const g4 = gateDist(race, 4);
    drive(race, -6, g3 + 10);
    const mid = (g3 + g4) / 2;
    const far = drive(race, g3 + 10, mid, (d) => Math.min(150, (d - g3 - 10) * 4)); // way off
    const r = race.racers[0]!;
    expect(r.passed).toBe(3);
    // Racer 1 sits just behind gate 3 on the road: the wanderer still ranks ahead.
    drive(
      race,
      -6,
      g3 - 5,
      () => 0,
      () => 0,
      1,
    );
    expect(standings(race, [far, at(g3 - 5)])).toEqual([0, 1]);
    drive(race, mid, g4 + 5); // back to the road and on through gate 4
    expect(race.racers[0]!.last).toBe(4);
  });

  it("I: a wider line ranks by real progress, not distance from the centre line", () => {
    const race = started(2);
    const g2 = gateDist(race, 2);
    const g3 = gateDist(race, 3);
    drive(
      race,
      -6,
      g2 + 30,
      () => 0,
      () => 0,
      0,
    ); // on the road
    const wide = drive(
      race,
      -6,
      g2 + 45,
      () => 22,
      () => 0,
      1,
    ); // wide, but further on
    expect(standings(race, [at(g2 + 30), wide])).toEqual([1, 0]);
    expect(g3).toBeGreaterThan(g2 + 45);
  });

  it("J: crossing at boost speed (big steps) never misses a gate", () => {
    const race = started();
    drive(
      race,
      -6,
      track.length + 5,
      () => 0,
      () => 0,
      0,
      7.5,
    ); // 7.5 m per step
    expect(race.racers[0]!.lapTimes).toHaveLength(1);
  });

  it("K: a gate on a bridge ignores the road underneath it", () => {
    const g: CheckpointGate = {
      ...pkgGates[0]!,
      x: 0,
      y: 8,
      z: 0,
      fx: 0,
      fz: 1,
      heading: 0,
      left: 20,
      right: 20,
      height: 6,
      below: 3,
    };
    const p = (y: number, z: number) => ({ x: 0, y, z });
    expect(crossGate(g, p(0, -1), p(0, 1))).toBeUndefined(); // the road below
    expect(crossGate(g, p(8, -1), p(8, 1))).toBe("forward"); // the bridge
  });

  it("K: on the layered Bridge Test, every gate is clear of the other level", async () => {
    // The frozen reference copy (the live one is a work in progress).
    const b = await loadTrackPackage(reader("bridge_test", "./fixtures/"), { visual: false });
    const t = buildTrack(b.trackData, tuning.track.sampleSpacing);
    const race = createRace(t, cfg);
    for (const g of race.gates)
      for (const s of t.samples) {
        const ahead = (s.pos.x - g.x) * g.fx + (s.pos.z - g.z) * g.fz;
        const across = (s.pos.x - g.x) * -g.fz + (s.pos.z - g.z) * g.fx;
        const inBox = Math.abs(ahead) < 0.5 && across >= -g.left && across <= g.right;
        if (inBox && Math.abs(s.pos.y - g.y) > 1) {
          const up = s.pos.y - g.y;
          expect(
            up > g.height || up < -g.below,
            `gate ${g.id} vs road at ${s.dist.toFixed(0)} m`,
          ).toBe(true);
        }
      }
    const r = await aiLap(b, { laps: 1 });
    expect(r.race.racers[0]!.lapTimes).toHaveLength(1);
  }, 60000);

  it("L: a respawn keeps your checkpoints but can't skip any", () => {
    const race = started();
    const g3 = gateDist(race, 3);
    const g5 = gateDist(race, 5);
    drive(race, -6, g3 + 10);
    // Somehow far ahead, past gates 4 and 5... then put back (a respawn).
    const spot = respawnSpot(race, 0);
    const ahead = kartAt(at(g5 + 20));
    teleported(race, 0, ahead);
    const k = createKartState(spot.x, spot.z, spot.heading, spot.y);
    tickRace(race, dt);
    stepRacer(race, 0, k, true, 0, cfg, dt); // the jump back is never swept
    const r = race.racers[0]!;
    expect(r.passed).toBe(3);
    expect(r.next).toBe(4);
    // The spot is just past gate 3, on the road.
    expect(Math.hypot(spot.x - race.gates[3]!.x, spot.z - race.gates[3]!.z)).toBeLessThan(25);
  });

  it("M: three laps finish the race with sensible lap times", () => {
    const race = started();
    for (let lap = 0; lap < 3; lap++)
      drive(race, lap * track.length - (lap ? 0 : 6), (lap + 1) * track.length + 5);
    const r = race.racers[0]!;
    expect(r.finished).toBe(true);
    expect(r.lapTimes).toHaveLength(3);
    expect(r.totalTime).toBeCloseTo(
      r.lapTimes.reduce((a, b) => a + b, 0),
      3,
    );
    expect(race.finishOrder).toEqual([0]);
  });

  it("N: a restart resets all progress", () => {
    const race = started();
    drive(race, -6, 300);
    const fresh = createRace(track, cfg);
    const r = fresh.racers[0]!;
    expect([r.passed, r.best, r.completedLaps, r.next, r.last, r.lapTimes.length]).toEqual([
      0, 0, 0, 1, 0, 0,
    ]);
  });

  it("doesn't count a gate twice for wobbling on it", () => {
    const race = started();
    const g1 = gateDist(race, 1);
    drive(race, -6, g1 - 2);
    for (let k = 0; k < 20; k++) drive(race, g1 + (k % 2 ? -0.5 : 0.5), g1 + (k % 2 ? 0.5 : -0.5));
    expect(race.racers[0]!.passed).toBe(1);
  });

  it("takes the shortcut gate as the checkpoint it stands for", () => {
    const race = started();
    const alt = race.course.find((c) => c.gates.length > 1)!;
    const g = alt.gates.find((x) => x.route !== "main")!;
    drive(race, -6, gateDist(race, alt.index - 1) + 15);
    expect(race.racers[0]!.next).toBe(alt.index);
    // Straight through the shortcut gate (not the main one).
    for (const d of [-3, -1.5, 0, 1.5, 3]) {
      tickRace(race, dt);
      stepRacer(
        race,
        0,
        kartAt({ x: g.x + g.fx * d, y: g.y, z: g.z + g.fz * d }),
        true,
        0,
        cfg,
        dt,
      );
    }
    expect(race.racers[0]!.last).toBe(alt.index);
    expect(race.racers[0]!.activeRoute).toBe(g.route);
  });

  it("AI racers use the same progression, with the race's own physics", async () => {
    const p = await loadTrackPackage(reader("riverbend_palms"), { visual: false });
    const r = await aiLap(p, { laps: 1, surfaces: true });
    expect(r.race.racers[0]!.lapTimes).toHaveLength(1);
    expect(r.race.racers[0]!.passed).toBe(r.race.course.length);
  }, 60000);

  it("reads checkpoints.json, warning about gates that can't count", () => {
    const warnings: string[] = [];
    const gates = parseCheckpoints(
      {
        schemaVersion: 1,
        checkpoints: [
          { id: "cp00", index: 0, position: [0, 0, 0], heading: 0, width: 30, height: 6 },
          { id: "cp01", index: 1, position: [0, 0, 50], heading: 0, width: 30, height: 6 },
          {
            id: "cp07_x",
            index: 7,
            route: "x",
            position: [9, 0, 9],
            heading: 0,
            width: 10,
            height: 6,
          },
        ],
      },
      warnings,
    );
    expect(gates.map((g) => g.id)).toEqual(["cp00", "cp01"]);
    expect(gates[0]!.left).toBe(15);
    expect(warnings.join(" ")).toContain("cp07_x");
  });
});
