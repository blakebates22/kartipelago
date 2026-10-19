// Course hazards: lava's burning bounce, deep water, respawn zones and the dinosaur.
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { createHazards, type HazardConfig, type Spot } from "../src/game/hazards";
import type { GroundQuery } from "../src/physics/ground";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack, type TrackData } from "../src/world/track";

const data: TrackData = {
  name: "ring",
  defaultWidth: 14,
  points: Array.from({ length: 24 }, (_, i) => ({
    x: 100 * Math.cos((i / 24) * Math.PI * 2),
    z: 100 * Math.sin((i / 24) * Math.PI * 2),
  })),
};
const track = buildTrack(data, 2);
const flat: GroundQuery = {
  at: () => ({ height: 0, nx: 0, ny: 1, nz: 0, onRoad: true }),
} as unknown as GroundQuery;
const cfg = tuning.hazards as HazardConfig;
const gate: Spot = { x: 100, y: 0, z: 0, heading: 0 };

function world(
  entities: unknown[] = [],
  routes: {
    id: string;
    closed: boolean;
    points: { x: number; y: number; z: number; width: number; bank: number }[];
  }[] = [],
) {
  return createHazards({
    root: undefined as never,
    track,
    entities,
    routes,
    makeGround: () => flat,
    cfg,
    karts: 1,
    quiet: true,
    headless: true,
  });
}

describe("lava", () => {
  it("bounces you up and back towards the road, slower, then you're briefly immune", () => {
    const h = world();
    const k = createKartState(130, 0, 0, 0);
    k.grounded = true;
    k.speed = 20;
    k.velAngle = Math.PI / 2; // heading +x, away from the ring's road at x = 100
    const ev = h.stepKart(0, k, "lava", gate, 1 / 120);
    expect(ev.burnt).toBe(true);
    expect(k.vy).toBe(cfg.lavaBounce);
    expect(k.grounded).toBe(false);
    expect(k.speed).toBeLessThan(20);
    // The push points back towards the road (-x).
    expect(Math.sin(k.velAngle) * k.speed).toBeLessThan(20 * cfg.lavaKeep);
    // Landing on lava again straight away does nothing: immune.
    k.grounded = true;
    expect(h.stepKart(0, k, "lava", gate, 1 / 120).burnt).toBeUndefined();
  });

  it("puts you back at the checkpoint, held for the penalty, after too many burns", () => {
    const h = world();
    const k = createKartState(130, 0, 0, 0);
    let respawned: Spot | undefined;
    for (let t = 0; t < 6 && !respawned; t += 1 / 120) {
      k.grounded = true;
      const ev = h.stepKart(0, k, "lava", gate, 1 / 120);
      h.step([k], 1 / 120);
      respawned = ev.respawned;
    }
    expect(respawned).toEqual(gate);
    expect(k.x).toBe(gate.x);
    // Held still for the penalty, never left in a loop of burns.
    for (let t = 0; t < cfg.lavaPenaltySec * 0.9; t += 1 / 120) {
      k.x += 1;
      h.stepKart(0, k, "road", gate, 1 / 120);
      expect(k.x).toBe(gate.x);
    }
  });
});

describe("water and respawn zones", () => {
  it("fishes you out of deep water after a moment, past a jump's gap if a zone says", () => {
    const at = track.samples[40]!.dist;
    const h = world([{ type: "respawn", from: 0, to: 60, at }]);
    const k = createKartState(100, 0, 0, 0);
    let ev = h.stepKart(0, k, "road", gate, 1 / 120);
    k.grounded = true;
    ev = h.stepKart(0, k, "deep_water", gate, 1 / 120);
    expect(ev.splashed).toBe("deep");
    let out: Spot | undefined;
    for (let t = 0; t < 3 && !out; t += 1 / 120) {
      k.grounded = true;
      out = h.stepKart(0, k, "deep_water", gate, 1 / 120).respawned;
    }
    expect(out).toBeDefined();
    expect(out!.x).toBeCloseTo(track.samples[40]!.pos.x, 0);
    expect(h.handles("deep_water")).toBe(true);
    expect(h.handles("water")).toBe(false);
  });
});

describe("dinosaur", () => {
  const path = Array.from({ length: 20 }, (_, i) => ({
    x: 30 * Math.cos((i / 20) * Math.PI * 2),
    y: 0,
    z: 30 * Math.sin((i / 20) * Math.PI * 2),
    width: 4,
    bank: 0,
  }));
  it("walks its path smoothly, and stops for karts close by", () => {
    const h = world(
      [{ type: "dinosaur", route: "Dino Path", speed: 3 }],
      [{ id: "Dino Path", closed: true, points: path }],
    );
    const far = createKartState(500, 500, 0, 0);
    const d = h.dinos[0]!;
    let last = { x: d.x, z: d.z };
    for (let k = 0; k < 600; k++) {
      h.step([far], 1 / 120);
      // No teleporting: never more than a step's walk at a time.
      expect(Math.hypot(d.x - last.x, d.z - last.z)).toBeLessThan(0.1);
      last = { x: d.x, z: d.z };
    }
    expect(Math.hypot(d.x - 30, d.z)).toBeGreaterThan(5); // it went somewhere
    const near = createKartState(d.x + 6, d.z, 0, 0);
    for (let k = 0; k < 240; k++) h.step([near], 1 / 120);
    const at = { x: d.x, z: d.z };
    for (let k = 0; k < 240; k++) h.step([near], 1 / 120);
    expect(Math.hypot(d.x - at.x, d.z - at.z)).toBeLessThan(0.3); // waiting
    expect(h.solids.length).toBe(2);
  });
});
