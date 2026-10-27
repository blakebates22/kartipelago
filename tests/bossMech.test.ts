// The boss races' mechanics (src/game/bossMech.ts): Cinderjaw's heat (the fire sweeps
// burn on their beat, the vents cool, a full gauge overheats you) and his alternative,
// the crumbling road behind the leader.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import {
  createBossMech,
  parseBossMech,
  sweepPhase,
  HEAT,
  type MechKart,
} from "../src/game/bossMech";

const sweep = {
  type: "fire_sweep",
  x: 0,
  y: 0,
  z: 0,
  heading: 0,
  width: 16,
  depth: 4,
  period: 5,
  offset: 0,
  warn: 1.4,
  burn: 1.3,
};
const kart = (z: number): MechKart => ({
  x: 0,
  y: 0,
  z,
  speed: 20,
  heading: 0,
  spinTime: 0,
  spinDir: 0,
});

describe("Cinderjaw's heat", () => {
  it("a sweep warns, then burns, on its beat", () => {
    const [s] = parseBossMech([sweep]).sweeps;
    expect(sweepPhase(s!, 1).phase).toBe("off");
    expect(sweepPhase(s!, 3.0).phase).toBe("warn");
    expect(sweepPhase(s!, 4.2).phase).toBe("burn");
    expect(sweepPhase(s!, 6).phase).toBe("off");
  });

  it("driving through it burning heats you; vents cool you; a full gauge spins you", () => {
    const m = createBossMech({
      cfg: parseBossMech([sweep, { type: "crust_vent", x: 0, y: 0, z: 30, r: 3 }]),
    });
    const k = kart(-5);
    // Through it while it's off: nothing.
    m.step(k, 1, 1 / 60, 0, 0, 500);
    k.z = 0;
    m.step(k, 1, 1 / 60, 0, 0, 500);
    expect(m.heat).toBe(0);
    // Through it burning: heat, once per pass.
    k.z = -5;
    m.step(k, 4.2, 1 / 60, 0, 0, 500);
    k.z = 0;
    expect(m.step(k, 4.2, 1 / 60, 0, 0, 500).burnt).toBe(true);
    m.step(k, 4.25, 1 / 60, 0, 0, 500);
    expect(m.heat).toBeCloseTo(HEAT.sweep, 0);
    // The vent takes it away.
    k.z = 30;
    expect(m.step(k, 4.3, 1 / 60, 0, 0, 500).vented).toBe(true);
    expect(m.heat).toBe(0);
    // Three passes through the fire overheat you.
    let over = false;
    for (let p = 0; p < 3; p++) {
      const t = 4.2 + 5 * (p + 1);
      k.z = -5;
      m.step(k, t, 1 / 60, 0, 0, 500);
      k.z = 0;
      over ||= Boolean(m.step(k, t, 1 / 60, 0, 0, 500).overheated);
    }
    expect(over).toBe(true);
    expect(k.spinTime).toBeGreaterThan(0);
    expect(k.speed).toBeLessThan(20);
  });
});

describe("the crumbling road (the alternative)", () => {
  it("drops you in when you're behind the front in a crumbling stretch", () => {
    const cfg = parseBossMech(
      [{ type: "crumble", variant: "alt", from: 100, to: 300, gap: 40 }],
      "alt",
    );
    const m = createBossMech({ cfg });
    const k = kart(0);
    // The leader at 250: the front's at 210. You at 150: behind it, in the stretch.
    expect(m.step(k, 10, 1 / 60, 150, 250, 1000).dropAt).toBeGreaterThan(210);
    // You at 230 (ahead of the front): fine.
    const m2 = createBossMech({ cfg });
    expect(m2.step(k, 10, 1 / 60, 230, 250, 1000).dropAt).toBeUndefined();
    // Not in the main variant.
    expect(
      parseBossMech([{ type: "crumble", variant: "alt", from: 1, to: 2 }]).crumbles,
    ).toHaveLength(0);
  });

  it("Cinderjaw's Caldera has both", async () => {
    const bytes = await readFile(
      new URL("../public/tracks/boss_prehistoric/track.json", import.meta.url),
    );
    const meta = JSON.parse(new TextDecoder().decode(bytes)) as { entities: unknown[] };
    const main = parseBossMech(meta.entities);
    expect(main.sweeps.length).toBeGreaterThanOrEqual(4);
    expect(main.vents.length).toBeGreaterThanOrEqual(4);
    expect(parseBossMech(meta.entities, "alt").crumbles.length).toBeGreaterThanOrEqual(2);
  });
});

describe("the other bosses' mechanics", () => {
  const road = (s: number) => ({ x: 0, y: 0, z: s, heading: 0, width: 14 });
  const step = (
    m: ReturnType<typeof createBossMech>,
    k: MechKart,
    t: number,
    lap: number,
    more = {},
  ) => m.step(k, t, 1 / 60, lap, lap, 1000, more);

  it("Rimefang's ice wall stops you in its lane while it's up, not in the other", () => {
    const wall = {
      type: "ice_wall",
      x: 0,
      y: 0,
      z: 50,
      heading: 0,
      width: 6,
      across: 3.5,
      period: 4,
      offset: 0,
      warn: 1,
      up: 2,
    };
    const m = createBossMech({ cfg: parseBossMech([wall]), roadAt: road });
    const inLane: MechKart = { ...kart(50), x: 3.5 };
    expect(step(m, inLane, 3.0, 50).bumped).toBe(true);
    expect(inLane.speed).toBeLessThanOrEqual(0);
    const other: MechKart = { ...kart(50), x: -3.5 };
    expect(step(m, other, 3.0, 50).bumped).toBeUndefined();
    const early: MechKart = { ...kart(50), x: 3.5 };
    expect(step(m, early, 1.0, 50).bumped).toBeUndefined();
  });

  it("the avalanche (and the King's fire) catches you if you dawdle", () => {
    const m = createBossMech({
      cfg: parseBossMech([{ type: "avalanche", from: 100, to: 900, gap: 30, speed: 25 }]),
      roadAt: road,
    });
    const k = kart(120);
    let buried = false;
    for (let i = 0; i < 60 * 3; i++) buried ||= Boolean(step(m, k, i / 60, 120 + i * 0.05).buried);
    expect(buried).toBe(true);
    // Flat out ahead of it: never.
    const m2 = createBossMech({
      cfg: parseBossMech([{ type: "firewall", from: 100, to: 900, gap: 30, speed: 25 }]),
      roadAt: road,
    });
    let caught = false;
    for (let i = 0; i < 60 * 10; i++)
      caught ||= Boolean(step(m2, kart(0), i / 60, 120 + i * 0.5).buried);
    expect(caught).toBe(false);
  });

  it("the thin lake gives way under a kart that lingers, not one that keeps going", () => {
    const lake = { type: "thin_lake", variant: "alt", x: 0, y: 0, z: 0, r: 40 };
    const m = createBossMech({ cfg: parseBossMech([lake], "alt"), roadAt: road });
    const slow: MechKart = { ...kart(0), speed: 2 };
    let fell = false;
    for (let i = 0; i < 60 * 3; i++) fell ||= Boolean(step(m, slow, i / 60, 0).splashed);
    expect(fell).toBe(true);
    const m2 = createBossMech({ cfg: parseBossMech([lake], "alt"), roadAt: road });
    let fell2 = false;
    for (let i = 0; i < 60 * 3; i++)
      fell2 ||= Boolean(step(m2, { ...kart(0), speed: 22 }, i / 60, 0).splashed);
    expect(fell2).toBe(false);
  });

  it("Scorchwind's gust shoves you sideways, except behind a pillar", () => {
    const gust = {
      type: "gust",
      x: 0,
      y: 0,
      z: 0,
      r: 40,
      dx: 1,
      dz: 0,
      period: 5,
      offset: 0,
      warn: 1,
      on: 2.5,
      strength: 8,
    };
    const m = createBossMech({ cfg: parseBossMech([gust]), roadAt: road });
    const k = kart(0);
    for (let i = 0; i < 60; i++) step(m, k, 3.5 + i / 60, 0);
    expect(k.x).toBeGreaterThan(2);
    const m2 = createBossMech({
      cfg: parseBossMech([gust, { type: "shelter", x: -4, z: 10, r: 5 }]),
      roadAt: road,
    });
    const k2 = kart(10);
    for (let i = 0; i < 60; i++) step(m2, k2, 3.5 + i / 60, 0);
    expect(k2.x).toBeLessThan(0.5);
  });

  it("Tidewyrm: the sandbar floods at high tide (you swim); his humps breach in turn", () => {
    const tide = { type: "tide", period: 20, low: -1, high: 1 };
    const m = createBossMech({
      cfg: parseBossMech([
        tide,
        { type: "sandbar", x: 0, y: 0, z: 0, r: 8 },
        { type: "coil", from: 200, to: 260, period: 8, offset: 0 },
      ]),
      roadAt: road,
    });
    // High tide at t = 5 (a quarter of the way round): on the sandbar, you swim, slowly,
    // and you're not put back.
    const k = kart(0);
    const ev = step(m, k, 5, 0);
    expect(ev.splashed).toBe(true);
    expect(ev.dropAt).toBeUndefined();
    expect(k.speed).toBeLessThanOrEqual(9);
    expect(m.gauge()?.label).toMatch(/FLOODED/);
    // Low tide at t = 15: dry, and the gauge says so.
    const k2 = kart(0);
    expect(step(m, k2, 15, 0).splashed).toBeUndefined();
    expect(k2.speed).toBe(20);
    expect(m.gauge()?.label).toMatch(/OPEN/);
    // The coils are road now: never into the sea.
    for (let t = 0; t < 8; t += 0.5)
      expect(step(m, { ...kart(220), x: 30 }, t, 220).dropAt).toBeUndefined();
    // The first hump (207.5 m, the left half): up from t = 8 - 2.2 = 5.8; just risen it
    // throws you on, fully up it knocks you back.
    const left = { ...kart(207.5), x: -3.5 };
    expect(step(m, { ...left }, 5.9, 207.5).boosted).toBe(true);
    const hit = { ...left };
    expect(step(m, hit, 7.2, 207.5).bumped).toBe(true);
    expect(hit.speed).toBeLessThan(20);
  });

  it("a whirlpool swings you round; the King's fireball is sent back with the item button", () => {
    const m = createBossMech({
      cfg: parseBossMech(
        [{ type: "whirlpool", variant: "alt", x: 0, y: 0, z: 0, r: 10, spin: 1.5 }],
        "alt",
      ),
      roadAt: road,
    });
    const k = { ...kart(5) };
    const h0 = k.heading;
    for (let i = 0; i < 30; i++) step(m, k, i / 60, 0);
    expect(k.heading).not.toBe(h0);
    const f = createBossMech({
      cfg: parseBossMech([{ type: "fireball", variant: "alt", period: 2, speed: 30 }], "alt"),
      roadAt: road,
    });
    const you = kart(0);
    let reflected = false;
    let hit = false;
    for (let i = 0; i < 60 * 8 && !hit; i++) {
      const ev = step(f, you, i / 60, 0, { boss: { x: 0, y: 0, z: 60 }, item: true });
      reflected ||= Boolean(ev.reflected);
      hit ||= Boolean(ev.bossHit);
    }
    expect(reflected).toBe(true);
    expect(hit).toBe(true);
  });
});
