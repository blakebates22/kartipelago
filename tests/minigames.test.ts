// The mini-games' rules (src/game/minigames.ts): each can be won, the rivals' minds steer
// for their targets, and every arena's build has what its game needs.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import {
  MINIGAMES,
  RULES,
  createMiniGame,
  makeIce,
  minigameById,
  navPath,
  navSpot,
  navWaypoint,
  newMind,
  shouldFire,
  parseArena,
  seek,
  type Arena,
  type Kart,
} from "../src/game/minigames";

const arena: Arena = {
  spawns: [0, 1, 2, 3].map((k) => ({ x: Math.sin(k) * 40, z: Math.cos(k) * 40, heading: 0 })),
  radius: 60,
  rink: { x: 0, z: 0, y: 2, r: 30, tile: 2.6 },
  ramps: [],
};
const karts = (): Kart[] =>
  arena.spawns.map((s) => ({ x: s.x, y: 0, z: s.z, heading: 0, speed: 0 }));

describe("the mini-games", () => {
  it("Caldera Brawl: three hits and your health's gone, you're out; the last one running wins", () => {
    const g = createMiniGame(minigameById("brawl")!, arena, 4);
    const ks = karts();
    expect(g.score[0]).toBe(RULES.health);
    // (The lava takes less than a hit.)
    g.hit(0, RULES.hazardDamage);
    expect(g.score[0]).toBe(RULES.health - RULES.hazardDamage);
    for (const i of [1, 2, 3])
      for (let h = 0; h < 3; h++) {
        g.hit(i);
        g.hit(i); // (immune just after a hit: the second doesn't count)
        for (let k = 0; k < 150; k++) g.step(ks, 1 / 60);
      }
    expect(g.out).toEqual([false, true, true, true]);
    expect(g.winner).toBe(0);
  });

  it("Crumble Rink: thin ice cracks where you drive, breaks under the next kart; through it, you're out", () => {
    const g = createMiniGame(minigameById("crumble")!, arena, 4, 3);
    const ice = g.ice!;
    expect(ice.state.length).toBeGreaterThan(100);
    // Every tile is found again at its own centre.
    for (let t = 0; t < ice.state.length; t += 17) expect(ice.at(ice.x[t]!, ice.z[t]!)).toBe(t);
    const ks = karts().map((k, i) => ({ ...k, x: (i - 1.5) * 12, z: 0 }));
    // Standing still (the countdown) cracks nothing.
    for (let k = 0; k < 60 * (RULES.graceSec + 1); k++) g.step(ks, 1 / 60);
    expect(ice.state.every((s) => s === 0)).toBe(true);
    // Kart 1 drives over a tile: it cracks, and holds.
    ks[1]!.speed = 10;
    g.step(ks, 1 / 60);
    const t = ice.at(ks[1]!.x, ks[1]!.z);
    expect(ice.state[t]).toBe(1);
    for (let k = 0; k < 60 * 3; k++) g.step(ks, 1 / 60);
    expect(ice.state[t]).toBe(1);
    expect(g.out[1]).toBe(false);
    // Kart 2 drives onto it: it breaks, and if 2 stays there, it falls through.
    Object.assign(ks[2]!, { x: ks[1]!.x, z: ks[1]!.z, speed: 10 });
    Object.assign(ks[1]!, { x: 25, z: 5, speed: 0 });
    g.step(ks, 1 / 60);
    expect(ice.state[t]).toBe(3);
    for (let k = 0; k < 60 * (RULES.breakSec + 0.2); k++) g.step(ks, 1 / 60);
    expect(ice.state[t]).toBe(2);
    expect(g.out[2]).toBe(true);
    // Off the ice: out too.
    Object.assign(ks[1]!, { x: 80, z: 0 });
    g.step(ks, 1 / 60);
    expect(g.out[1]).toBe(true);
    // The last one on the ice wins.
    Object.assign(ks[3]!, { x: 200, z: 0 });
    g.step(ks, 1 / 60);
    expect(g.winner).toBe(0);
  });

  it("Star Fall: stars land and are caught; a hit knocks one out", () => {
    const g = createMiniGame(minigameById("stars")!, arena, 4, 7);
    const ks = karts();
    for (let k = 0; k < 60 * 40 && g.winner === undefined; k++) {
      // Kart 0 drives to whatever star's down.
      const t = g.target(0, ks);
      Object.assign(ks[0]!, { x: t.x, z: t.z });
      g.step(ks, 1 / 60);
    }
    expect(g.winner).toBe(0);
    const s = g.score[0]!;
    g.hit(0);
    expect(g.score[0]).toBe(s); // (over: nothing changes)
  });

  it("the rivals' minds steer for their target, and back out when stuck", () => {
    const m = newMind();
    const k: Kart = { x: 0, y: 0, z: 0, heading: 0, speed: 10 };
    // Target to the right (+x): heading must rise, so steer is negative.
    expect(seek(m, k, 10, 0, 1 / 60).steer).toBeLessThan(0);
    expect(seek(m, k, -10, 0, 1 / 60).steer).toBeGreaterThan(0);
    const stuck: Kart = { ...k, speed: 0 };
    let backing = false;
    for (let i = 0; i < 120; i++) backing ||= seek(m, stuck, 0, 50, 1 / 60).brake > 0;
    expect(backing).toBe(true);
  });

  it("every arena's build has spawns, and its game's things", async () => {
    for (const m of MINIGAMES) {
      const bytes = await readFile(
        new URL(`../public/tracks/${m.arena}/track.json`, import.meta.url),
      );
      const meta = JSON.parse(new TextDecoder().decode(bytes)) as { entities: unknown[] };
      const a = parseArena(meta.entities);
      expect(a.spawns.length, m.arena).toBeGreaterThanOrEqual(4);
      if (m.id === "crumble") {
        expect(a.rink).toBeDefined();
        // Every kart starts on the ice.
        const ice = makeIce(a.rink!);
        for (const s of a.spawns) expect(ice.at(s.x, s.z), m.arena).toBeGreaterThanOrEqual(0);
      }
    }
  });

  it("Caldera Keep: the rivals' map links every level (bailey, courtyard, walk, keep roof)", async () => {
    const bytes = await readFile(
      new URL("../public/tracks/arena_bowl/track.json", import.meta.url),
    );
    const a = parseArena(
      (JSON.parse(new TextDecoder().decode(bytes)) as { entities: unknown[] }).entities,
    );
    const nav = a.nav!;
    expect(nav.nodes.length).toBeGreaterThan(40);
    // Every spot reaches every other.
    for (let t = 1; t < nav.nodes.length; t++) expect(navPath(nav, 0, t).at(-1), String(t)).toBe(t);
    // From out in the bailey up onto the keep's roof: up a ramp onto the walk, over a bridge.
    const deck = a.deck!;
    const bailey = { x: 58, y: 2, z: 0, heading: 0, speed: 0 };
    const roof = { x: 0, y: deck.y, z: 0 };
    const path = navPath(nav, navSpot(nav, bailey), navSpot(nav, roof));
    const ys = path.map((n) => nav.nodes[n]!.y);
    expect(Math.min(...ys)).toBeLessThan(3);
    expect(Math.max(...ys)).toBeGreaterThan(deck.y - 1);
    const w = navWaypoint(nav, bailey, roof);
    expect(Math.hypot(w.x - roof.x, w.z - roof.z)).toBeGreaterThan(5); // (not straight at it)
  });

  it("the rivals wait a moment before they fire, and rest after", () => {
    const ks: Kart[] = [
      { x: 0, y: 0, z: 0, heading: 0, speed: 10 },
      { x: 0, y: 0, z: 20, heading: 0, speed: 10 },
    ];
    const m = newMind();
    expect(shouldFire(0, ks[0]!, ks, "red", [false, false], m, 10)).toBe(false);
    expect(shouldFire(0, ks[0]!, ks, "red", [false, false], m, 10.95)).toBe(true);
    expect(shouldFire(0, ks[0]!, ks, "red", [false, false], m, 11.5)).toBe(false);
    // Not through a floor.
    const up = [ks[0]!, { ...ks[1]!, y: 6 }];
    expect(shouldFire(0, ks[0]!, up, "red", [false, false])).toBe(false);
  });
});
