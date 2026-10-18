import { describe, expect, it } from "vitest";
import tuning from "../assets/data/tuning.json";
import { NEUTRAL } from "../src/core/input";
import type { ItemsConfig } from "../src/items/config";
import { racerItems, stepEffects, bumpMass, type Racer } from "../src/items/effects";
import { collectBalloon, emptyHeld, useAmmo } from "../src/items/inventory";
import {
  collectBalloons,
  createItemWorld,
  fireItem,
  itemReleased,
  stepItemWorld,
  type ItemEvent,
} from "../src/items/world";
import { bumpKarts } from "../src/physics/bump";
import { createTrackGround, flatGround } from "../src/physics/ground";
import driftLoop from "../assets/data/track.json";
import { buildTrack, type TrackData } from "../src/world/track";
import { createKartState, stepKart, type KartConfig } from "../src/vehicles/kart";
import { ZIP } from "../src/vehicles/zipper";

const items = tuning.items as ItemsConfig;
const cfg: KartConfig = { ...tuning.vehicle };
const loss = tuning.bananas;
const dt = 1 / 120;

/** Racers on flat open ground. "Ahead" is further along +Z. */
function setup(positions: [number, number][]) {
  const racers: Racer[] = positions.map(([x, z]) => ({
    kart: createKartState(x, z, 0),
    items: racerItems(),
    cfg,
  }));
  const world = createItemWorld(undefined, [], () => flatGround, [], false);
  const progress = (j: number) => racers[j]!.kart.z;
  return { racers, world, progress };
}

type Setup = ReturnType<typeof setup>;
/** Step the whole little world: karts (holding `input`), effects, items. */
function run(s: Setup, seconds: number, input = { ...NEUTRAL }) {
  const events: ItemEvent[] = [];
  for (let t = 0; t < seconds; t += dt) {
    for (const r of s.racers) stepKart(r.kart, r.items.bubbleTime > 0 ? NEUTRAL : input, r.cfg, dt);
    stepEffects(s.racers, items, dt);
    events.push(...stepItemWorld(s.world, s.racers, items, loss, dt, s.progress));
  }
  return events;
}
const give = (r: Racer, color: "red" | "blue" | "green" | "yellow" | "rainbow", level = 1) => {
  r.items.held = { color, level, ammo: color === "red" && level === 3 ? 10 : 1 };
};
const hits = (ev: ItemEvent[]) => ev.filter((e) => e.type === "hit");

describe("balloon inventory", () => {
  it("upgrades the same colour, caps at level 3, and refills there", () => {
    const h = emptyHeld();
    expect(collectBalloon(h, "red", items)).toBe("new");
    expect(h).toEqual({ color: "red", level: 1, ammo: 1 });
    expect(collectBalloon(h, "red", items)).toBe("upgrade");
    expect(h.level).toBe(2);
    collectBalloon(h, "red", items);
    expect(h).toEqual({ color: "red", level: 3, ammo: 10 });
    useAmmo(h);
    useAmmo(h);
    expect(h.ammo).toBe(8);
    expect(collectBalloon(h, "red", items)).toBe("refill");
    expect(h).toEqual({ color: "red", level: 3, ammo: 10 });
  });

  it("resets to level 1 when you switch colour or run out", () => {
    const h = emptyHeld();
    collectBalloon(h, "blue", items);
    collectBalloon(h, "blue", items);
    expect(h.level).toBe(2);
    collectBalloon(h, "green", items);
    expect(h).toEqual({ color: "green", level: 1, ammo: 1 });
    useAmmo(h);
    expect(h).toEqual({ color: null, level: 0, ammo: 0 });
    collectBalloon(h, "green", items);
    expect(h.level).toBe(1);
  });

  it("picks up balloons on the track, once, and they come back", () => {
    const s = setup([[0, 0]]);
    s.world.balloons.push({ x: 0, y: 0, z: 0, color: "blue", active: true, respawnIn: 0, age: 1 });
    expect(collectBalloons(s.world, s.racers, items, () => true)).toHaveLength(1);
    expect(collectBalloons(s.world, s.racers, items, () => true)).toHaveLength(0);
    run(s, items.balloonRespawnSec + 0.1);
    expect(s.world.balloons[0]!.active).toBe(true);
  });

  it("fires on the release of the item button, not the press", () => {
    const s = setup([[0, 0]]);
    const r = s.racers[0]!;
    expect(itemReleased(r, true)).toBe(false);
    expect(itemReleased(r, true)).toBe(false);
    expect(itemReleased(r, false)).toBe(true);
    expect(itemReleased(r, false)).toBe(false);
  });

  it("fires a blue balloon as an enhanced boost when the throttle is released", () => {
    const s = setup([[0, 0]]);
    const r = s.racers[0]!;
    r.kart.speed = cfg.topSpeed;
    give(r, "blue", 2);
    const ev = fireItem(s.world, s.racers, 0, 0, items, s.progress);
    expect(ev).toMatchObject({ type: "fire", color: "blue", level: 2, enhanced: true });
    expect(r.kart.zipPhase).toBe(ZIP.ACTIVE);
    expect(r.kart.zipTotal).toBeCloseTo(items.blue2Sec, 6);
    expect(r.items.held.color).toBe(null);
  });
});

describe("shields", () => {
  it("last 5 / 10 / 15 s by level and then drop", () => {
    for (const [level, sec] of [
      [1, items.shield1Sec],
      [2, items.shield2Sec],
      [3, items.shield3Sec],
    ] as const) {
      const s = setup([[0, 0]]);
      give(s.racers[0]!, "yellow", level);
      fireItem(s.world, s.racers, 0, 1, items, s.progress);
      expect(s.racers[0]!.items.shieldLevel).toBe(level);
      run(s, sec - 0.1);
      expect(s.racers[0]!.items.shieldTime).toBeGreaterThan(0);
      run(s, 0.2);
      expect(s.racers[0]!.items.shieldTime).toBe(0);
    }
    expect([items.shield1Sec, items.shield2Sec, items.shield3Sec]).toEqual([5, 10, 15]);
  });

  it("make a shielded kart push others aside without being pushed itself", () => {
    const a = createKartState(0, 0, 0);
    const b = createKartState(1, 0, 0);
    const shielded = racerItems();
    shielded.shieldTime = 5;
    bumpKarts([a, b], tuning.physics.kartBump, [bumpMass(shielded, items), 1]);
    expect(Math.abs(a.x)).toBeLessThan(Math.abs(b.x - 1));
  });
});

describe("missiles", () => {
  it("fly straight, hit the racer ahead, spin them and knock two bananas loose", () => {
    const s = setup([
      [0, 0],
      [0, 40],
    ]);
    const victim = s.racers[1]!.kart;
    victim.bananas = 5;
    victim.speed = 10;
    give(s.racers[0]!, "red", 1);
    fireItem(s.world, s.racers, 0, 1, items, s.progress);
    expect(s.world.missiles).toHaveLength(1);
    const ev = hits(run(s, 2));
    expect(ev).toEqual([{ type: "hit", racer: 1, kind: "missile", blocked: false, lost: 2 }]);
    expect(victim.bananas).toBe(3);
    expect(victim.spinTime).toBeGreaterThan(0);
  });

  it("carry the kart's own speed as well as their launch speed", () => {
    const s = setup([[0, 0]]);
    s.racers[0]!.kart.speed = 20;
    give(s.racers[0]!, "red", 1);
    fireItem(s.world, s.racers, 0, 1, items, s.progress);
    expect(s.world.missiles[0]!.speed).toBeCloseTo(items.missileSpeed + 20, 6);
  });

  it("are stopped by a shield", () => {
    const s = setup([
      [0, 0],
      [0, 30],
    ]);
    s.racers[1]!.items.shieldTime = 5;
    s.racers[1]!.kart.bananas = 5;
    give(s.racers[0]!, "red", 1);
    fireItem(s.world, s.racers, 0, 1, items, s.progress);
    expect(hits(run(s, 2))).toEqual([
      { type: "hit", racer: 1, kind: "missile", blocked: true, lost: 0 },
    ]);
    expect(s.racers[1]!.kart.bananas).toBe(5);
    expect(s.racers[1]!.kart.spinTime).toBe(0);
  });

  it("home in on a target off to the side that a straight missile misses", () => {
    const shoot = (level: number) => {
      const s = setup([
        [0, 0],
        [25, 50],
      ]);
      give(s.racers[0]!, "red", level);
      fireItem(s.world, s.racers, 0, 1, items, s.progress);
      return hits(run(s, 3));
    };
    expect(shoot(1)).toHaveLength(0);
    expect(shoot(2)).toHaveLength(1);
  });

  it("follow the road round a corner to reach a target out of sight", () => {
    const track = buildTrack(driftLoop as TrackData, tuning.track.sampleSpacing);
    const at = (d: number) => track.samples[Math.round((d / track.length) * track.samples.length)]!;
    const shoot = (level: number) => {
      const a = at(270);
      const b = at(350); // round the long right-hander
      const racers: Racer[] = [a, b].map((p) => ({
        kart: createKartState(p.pos.x, p.pos.z, Math.atan2(p.forward.x, p.forward.z), p.pos.y),
        items: racerItems(),
        cfg,
      }));
      const world = createItemWorld(track, [], () => createTrackGround(track), [], true);
      const progress = (j: number) => j; // racer 1 is ahead
      racers[0]!.items.held = { color: "red", level, ammo: 1 };
      fireItem(world, racers, 0, 1, items, progress);
      const ev: ItemEvent[] = [];
      let wall = false;
      for (let t = 0; t < 4; t += dt) {
        ev.push(...stepItemWorld(world, racers, items, loss, dt, progress));
        wall ||= world.blasts.some((b) => b.kind === "wall");
      }
      return { hit: hits(ev).length, wall };
    };
    expect(shoot(1)).toEqual({ hit: 0, wall: true });
    expect(shoot(2)).toMatchObject({ hit: 1 });
  });

  it("level 3 holds ten straight missiles", () => {
    const s = setup([[0, 0]]);
    give(s.racers[0]!, "red", 3);
    for (let k = 0; k < 10; k++) {
      expect(fireItem(s.world, s.racers, 0, 1, items, s.progress)).not.toBe(null);
    }
    expect(s.world.missiles).toHaveLength(10);
    expect(fireItem(s.world, s.racers, 0, 1, items, s.progress)).toBe(null);
  });
});

describe("green traps", () => {
  const dropAndDrive = (level: number) => {
    // Racer 1 drives through the spot behind racer 0 where the trap lands.
    const s = setup([
      [0, 0],
      [0, -30],
    ]);
    s.racers[1]!.kart.bananas = 5;
    s.racers[1]!.kart.speed = 20;
    give(s.racers[0]!, "green", level);
    fireItem(s.world, s.racers, 0, 1, items, s.progress);
    expect(s.world.traps).toHaveLength(1);
    expect(s.world.traps[0]!.z).toBeCloseTo(-items.trapBehind, 6);
    const ev: ItemEvent[] = [];
    for (let t = 0; t < 2; t += dt) {
      const k = s.racers[1]!.kart;
      stepKart(
        k,
        s.racers[1]!.items.bubbleTime > 0 ? NEUTRAL : { ...NEUTRAL, throttle: 1 },
        cfg,
        dt,
      );
      stepEffects(s.racers, items, dt);
      ev.push(...stepItemWorld(s.world, s.racers, items, loss, dt, s.progress));
    }
    return { s, ev: hits(ev) };
  };

  it("don't catch the racer who dropped them straight away", () => {
    const s = setup([[0, 0]]);
    give(s.racers[0]!, "green", 1);
    fireItem(s.world, s.racers, 0, 1, items, s.progress);
    s.racers[0]!.kart.z = -items.trapBehind; // sitting right on it
    expect(hits(run(s, 0.5))).toHaveLength(0);
  });

  it("oil spins a racer out without costing bananas", () => {
    const { s, ev } = dropAndDrive(1);
    expect(ev).toMatchObject([{ racer: 1, kind: "oil", lost: 0 }]);
    expect(s.racers[1]!.kart.bananas).toBe(5);
  });

  it("a mine blows a racer up and costs two bananas", () => {
    const { s, ev } = dropAndDrive(2);
    expect(ev).toMatchObject([{ racer: 1, kind: "mine", lost: 2 }]);
    expect(s.racers[1]!.kart.bananas).toBe(3);
  });

  it("a bubble holds a racer about two seconds, then lets go", () => {
    const s = setup([[0, 0]]);
    const k = s.racers[0]!.kart;
    k.speed = 20;
    s.world.traps.push({ kind: "bubble", x: 0, y: 0, z: 0, owner: 1, age: 5 });
    const throttle = { ...NEUTRAL, throttle: 1 };
    run(s, 0.6, throttle);
    expect(s.racers[0]!.items.bubbleTime).toBeGreaterThan(0);
    expect(k.speed).toBeLessThan(1);
    const z = k.z;
    run(s, items.bubbleSec - 0.8, throttle);
    expect(Math.abs(k.z - z)).toBeLessThan(0.5); // held in place
    run(s, 1, throttle);
    expect(s.racers[0]!.items.bubbleTime).toBe(0);
    expect(k.speed).toBeGreaterThan(5); // driving again
  });

  it("a shield blocks a trap", () => {
    const s = setup([[0, 0]]);
    s.racers[0]!.items.shieldTime = 5;
    s.world.traps.push({ kind: "mine", x: 0, y: 0, z: 0, owner: 1, age: 5 });
    expect(hits(run(s, 0.1))).toMatchObject([{ blocked: true }]);
    expect(s.world.traps).toHaveLength(0);
  });
});

describe("magnets", () => {
  it("pull you toward the racer ahead in range, smoothly", () => {
    const s = setup([
      [0, 0],
      [8, 40],
    ]);
    const me = s.racers[0]!.kart;
    me.speed = cfg.topSpeed;
    s.racers[1]!.kart.speed = cfg.topSpeed;
    give(s.racers[0]!, "rainbow", 1);
    expect(fireItem(s.world, s.racers, 0, 1, items, s.progress)).toMatchObject({ type: "fire" });
    const start = Math.hypot(8, 40);
    let last = { x: me.x, z: me.z };
    let maxStep = 0;
    for (let t = 0; t < 1.2; t += dt) {
      for (const r of s.racers) stepKart(r.kart, { ...NEUTRAL, throttle: 1 }, cfg, dt);
      stepEffects(s.racers, items, dt);
      maxStep = Math.max(maxStep, Math.hypot(me.x - last.x, me.z - last.z));
      last = { x: me.x, z: me.z };
    }
    const k1 = s.racers[1]!.kart;
    expect(Math.hypot(k1.x - me.x, k1.z - me.z)).toBeLessThan(start - 10);
    // Never more than the boosted speed allows in one step: no teleporting.
    expect(maxStep).toBeLessThan(cfg.topSpeed * items.magnetSpeedMult * dt + 1e-6);
  });

  it("need a target in range (scaled from original units), else keep the balloon", () => {
    const range = items.magnet1Range * items.magnetUnit;
    const s = setup([
      [0, 0],
      [0, range + 10],
    ]);
    give(s.racers[0]!, "rainbow", 1);
    expect(fireItem(s.world, s.racers, 0, 1, items, s.progress)).toEqual({
      type: "noTarget",
      racer: 0,
    });
    expect(s.racers[0]!.items.held.color).toBe("rainbow");
    give(s.racers[0]!, "rainbow", 2); // longer range reaches
    expect(fireItem(s.world, s.racers, 0, 1, items, s.progress)).toMatchObject({ type: "fire" });
  });

  it("level 3 drags the rival back toward you for about two seconds", () => {
    const s = setup([
      [0, 0],
      [0, 50],
    ]);
    const rival = s.racers[1]!.kart;
    rival.speed = cfg.topSpeed;
    give(s.racers[0]!, "rainbow", 3);
    fireItem(s.world, s.racers, 0, 1, items, s.progress);
    expect(s.racers[1]!.items.pullTime).toBeCloseTo(items.reverseMagnetSec, 6);
    const free = setup([[0, 50]]).racers[0]!.kart;
    free.speed = cfg.topSpeed;
    for (let t = 0; t < 1.5; t += dt) {
      stepKart(rival, { ...NEUTRAL, throttle: 1 }, cfg, dt);
      stepKart(free, { ...NEUTRAL, throttle: 1 }, cfg, dt);
      stepEffects(s.racers, items, dt);
    }
    expect(rival.z).toBeLessThan(free.z - 15);
  });
});
