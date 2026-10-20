// The dragon (Ember Peak): its attacks follow the race clock exactly, are telegraphed,
// leave time to get through, only burn inside the zone where the flames are, and burn
// with the same bounce, immunity and three strikes as lava.
import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { dragonBurns, dragonPhase, inFireZone, parseDragon } from "../src/game/dragon";
import { createHazards, type HazardConfig, type Spot } from "../src/game/hazards";
import type { GroundQuery } from "../src/physics/ground";
import { createKartState } from "../src/vehicles/kart";
import { buildTrack } from "../src/world/track";

const entity = {
  type: "dragon",
  x: 60,
  y: 40,
  z: 0,
  heading: -Math.PI / 2,
  fire: { x: 0, y: 0, z: 0, heading: 0, length: 16, width: 22, height: 6 },
  period: 9,
  offset: 3,
  aim: 1.2,
  warn: 1.8,
  breathe: 2.0,
  cool: 1.0,
};
const d = parseDragon(entity);

describe("dragon schedule", () => {
  it("runs idle, aiming, warning, breathing, cooldown, every period, from the race clock", () => {
    const seen: string[] = [];
    for (let t = 3; t < 12; t += 0.05) {
      const p = dragonPhase(d, t).phase;
      if (seen.at(-1) !== p) seen.push(p);
    }
    expect(seen).toEqual(["idle", "aiming", "warning", "breathing", "cooldown"]);
    // The same clock always gives the same attack (time trials are reproducible).
    for (const t of [-2.4, 0, 7.31, 100.05, 1234.5]) {
      const a = dragonPhase(d, t);
      const b = dragonPhase(d, t + 9 * 7);
      expect(b.phase).toBe(a.phase);
      expect(b.t).toBeCloseTo(a.t, 6);
    }
  });

  it("always warns before it breathes fire, and rests between attacks", () => {
    expect(d.warn).toBeGreaterThanOrEqual(1.5);
    let last = dragonPhase(d, -0.01).phase as string;
    for (let t = 0; t < 40; t += 0.01) {
      const p = dragonPhase(d, t).phase;
      if (p === "breathing" && last !== "breathing") expect(last).toBe("warning");
      last = p;
    }
    // The road is clear most of the time.
    let burning = 0;
    for (let t = 0; t < 90; t += 0.01) if (dragonPhase(d, t).phase === "breathing") burning++;
    expect(burning / 9000).toBeLessThan(0.3);
  });

  it("only burns inside the zone, and only while breathing", () => {
    const breathing = 3 + 9 - 1.0 - 1.0; // a moment into the fire
    expect(dragonPhase(d, breathing).phase).toBe("breathing");
    expect(dragonBurns(d, breathing, 0, 0.5, 0)).toBe(true);
    expect(dragonBurns(d, breathing, 0, 0.5, 8.5)).toBe(false); // past its far end
    expect(dragonBurns(d, breathing, 11.5, 0.5, 0)).toBe(false); // past its side
    expect(dragonBurns(d, breathing, 0, 7.0, 0)).toBe(false); // over the flames
    expect(dragonBurns(d, breathing - 3, 0, 0.5, 0)).toBe(false); // still warning
    expect(inFireZone(d, 10.9, 0, 7.9)).toBe(true);
  });
});

describe("dragon fire", () => {
  const track = buildTrack(
    {
      name: "ring",
      defaultWidth: 14,
      points: Array.from({ length: 24 }, (_, i) => ({
        x: 100 * Math.cos((i / 24) * Math.PI * 2) - 100,
        z: 100 * Math.sin((i / 24) * Math.PI * 2),
      })),
    },
    2,
  );
  const flat = {
    at: () => ({ height: 0, nx: 0, ny: 1, nz: 0, onRoad: true }),
  } as unknown as GroundQuery;
  const cfg = tuning.hazards as HazardConfig;
  const gate: Spot = { x: 0, y: 0, z: -20, heading: 0 };

  it("burns like lava: the same bounce, then immunity, then three strikes and back", () => {
    let clock = 10; // breathing
    const h = createHazards({
      root: undefined as never,
      track,
      entities: [entity],
      routes: [],
      makeGround: () => flat,
      cfg,
      karts: 1,
      quiet: true,
      headless: true,
      clock: () => clock,
    });
    const k = createKartState(0, 0, 0, 0);
    k.grounded = true;
    k.speed = 20;
    const ev = h.stepKart(0, k, "road", gate, 1 / 120);
    expect(ev.burnt).toBe(true);
    expect(k.vy).toBe(cfg.lavaBounce);
    expect(k.speed).toBeLessThan(20);
    // Immune straight after, like lava.
    expect(h.stepKart(0, k, "road", gate, 1 / 120).burnt).toBeUndefined();
    // Out of the zone, or between breaths: nothing.
    clock = 5;
    for (let t = 0; t < 2; t += 1 / 120) h.step([k], 1 / 120);
    k.x = 0;
    k.y = 0;
    expect(h.stepKart(0, k, "road", gate, 1 / 120).burnt).toBeUndefined();
    // Stay in the fire: the third burn puts you back at the checkpoint.
    clock = 10;
    let respawned: Spot | undefined;
    for (let t = 0; t < 6 && !respawned; t += 1 / 120) {
      k.x = 0;
      k.y = 0;
      k.z = 0;
      const e = h.stepKart(0, k, "road", gate, 1 / 120);
      h.step([k], 1 / 120);
      respawned = e.respawned;
    }
    expect(respawned).toEqual(gate);
  });
});
