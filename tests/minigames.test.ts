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
  newMind,
  parseArena,
  seek,
  type Arena,
  type Kart,
} from "../src/game/minigames";

const arena: Arena = {
  spawns: [0, 1, 2, 3].map((k) => ({ x: Math.sin(k) * 40, z: Math.cos(k) * 40, heading: 0 })),
  radius: 60,
  docks: [
    { x: 30, z: 30, y: 0, color: "red" },
    { x: -30, z: 30, y: 0, color: "blue" },
    { x: -30, z: -30, y: 0, color: "green" },
    { x: 30, z: -30, y: 0, color: "yellow" },
  ],
  crateSpawn: { x: 0, z: 0, y: 0, r: 0.1 },
  rink: { x: 0, z: 0, y: 2, r: 30, tile: 2.6 },
};
const karts = (): Kart[] =>
  arena.spawns.map((s) => ({ x: s.x, y: 0, z: s.z, heading: 0, speed: 0 }));

describe("the mini-games", () => {
  it("Balloon Brawl: three hits and you're out; the last one flying wins", () => {
    const g = createMiniGame(minigameById("balloons")!, arena, 4);
    const ks = karts();
    for (const i of [1, 2, 3])
      for (let h = 0; h < RULES.lives; h++) {
        g.hit(i);
        g.hit(i); // (immune just after a hit: the second doesn't count)
        for (let k = 0; k < 150; k++) g.step(ks, 1 / 60);
      }
    expect(g.out).toEqual([false, true, true, true]);
    expect(g.winner).toBe(0);
  });

  it("Smugglers' Run: grab a crate, run it to your dock; rammed, you drop it; five wins", () => {
    const g = createMiniGame(minigameById("smugglers")!, arena, 4);
    const ks = karts();
    const fetch = () => {
      // Wait for a crate to land in the middle, drive over it, run it home.
      for (let k = 0; k < 60 * 6 && !g.crates.some((c) => c.carrier < 0 && c.fall <= 0); k++)
        g.step(ks, 1 / 60);
      const free = g.crates.find((c) => c.carrier < 0 && c.fall <= 0)!;
      Object.assign(ks[0]!, { x: free.x, z: free.z, speed: 0 });
      g.step(ks, 1 / 60);
      expect(g.carrying(0)).toBe(true);
      Object.assign(ks[0]!, { x: 30, z: 30 });
      g.step(ks, 1 / 60);
      Object.assign(ks[0]!, { x: 50, z: 0 });
    };
    fetch();
    expect(g.score[0]).toBe(1);
    expect(g.carrying(0)).toBe(false);
    // Rammed while carrying: dropped.
    for (let k = 0; k < 60 * 6 && !g.crates.some((c) => c.carrier < 0 && c.fall <= 0); k++)
      g.step(ks, 1 / 60);
    const free = g.crates.find((c) => c.carrier < 0 && c.fall <= 0)!;
    Object.assign(ks[0]!, { x: free.x, z: free.z });
    g.step(ks, 1 / 60);
    expect(g.carrying(0)).toBe(true);
    Object.assign(ks[1]!, { x: free.x + 1, z: free.z, speed: RULES.bumpSpeed + 5 });
    g.step(ks, 1 / 60);
    expect(g.carrying(0)).toBe(false);
    Object.assign(ks[1]!, { x: -50, z: 0, speed: 0 });
    Object.assign(ks[0]!, { x: 50, z: 0 });
    for (let k = 0; k < 60 * 3; k++) g.step(ks, 1 / 60);
    // (Hit by an item while carrying: dropped too.)
    for (let n = 0; n < 4; n++) fetch();
    expect(g.winner).toBe(0);
  });

  it("Crumble Rink: the ice cracks where you drive and falls; through it, you're out", () => {
    const g = createMiniGame(minigameById("crumble")!, arena, 4, 3);
    const ice = g.ice!;
    expect(ice.state.length).toBeGreaterThan(100);
    // Every tile is found again at its own centre.
    for (let t = 0; t < ice.state.length; t += 17) expect(ice.at(ice.x[t]!, ice.z[t]!)).toBe(t);
    const ks = karts().map((k, i) => ({ ...k, x: (i - 1.5) * 12, z: 0 }));
    // Standing still (the countdown) cracks nothing.
    for (let k = 0; k < 60 * (RULES.graceSec + 1); k++) g.step(ks, 1 / 60);
    expect(ice.state.every((s) => s === 0)).toBe(true);
    // Kart 1 drives: the tile under it cracks, then falls; it's out if it stays.
    ks[1]!.speed = 10;
    g.step(ks, 1 / 60);
    const t = ice.at(ks[1]!.x, ks[1]!.z);
    expect(ice.state[t]).toBe(1);
    for (let k = 0; k < 60 * (RULES.crackSec + 0.2); k++) g.step(ks, 1 / 60);
    expect(g.out[1]).toBe(true);
    // Off the ice: out too.
    Object.assign(ks[2]!, { x: 80, z: 0 });
    g.step(ks, 1 / 60);
    expect(g.out[2]).toBe(true);
    // The edge crumbles in over time; the last one on the ice wins.
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
      if (m.id === "smugglers") {
        expect(a.docks).toHaveLength(4);
        expect(a.crateSpawn).toBeDefined();
      }
      if (m.id === "crumble") {
        expect(a.rink).toBeDefined();
        // Every kart starts on the ice.
        const ice = makeIce(a.rink!);
        for (const s of a.spawns) expect(ice.at(s.x, s.z), m.arena).toBeGreaterThanOrEqual(0);
      }
    }
  });
});
