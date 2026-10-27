// The mini-games' rules (src/game/minigames.ts): each can be won, the rivals' minds steer
// for their targets, and every arena's build has what its game needs.
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import {
  MINIGAMES,
  RULES,
  createMiniGame,
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
  nests: [
    { x: 30, z: 30, y: 0, color: "red" },
    { x: -30, z: 30, y: 0, color: "blue" },
    { x: -30, z: -30, y: 0, color: "green" },
    { x: 30, z: -30, y: 0, color: "yellow" },
  ],
  eggSpawn: { x: 0, z: 0, y: 0, r: 0.1 },
  crown: { x: 0, z: 0, y: 0, r: 10 },
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

  it("Egg Scramble: pick up, take home, steal; three in your nest wins", () => {
    const g = createMiniGame(minigameById("eggs")!, arena, 4);
    const ks = karts();
    const fetch = () => {
      // Wait for an egg in the middle, drive over it, take it home.
      for (let k = 0; k < 60 * 6 && !g.eggs.some((e) => e.carrier < 0 && e.nest < 0); k++)
        g.step(ks, 1 / 60);
      const free = g.eggs.find((e) => e.carrier < 0 && e.nest < 0)!;
      Object.assign(ks[0]!, { x: free.x, z: free.z });
      g.step(ks, 1 / 60);
      expect(g.eggs.some((e) => e.carrier === 0)).toBe(true);
      Object.assign(ks[0]!, { x: 30, z: 30 });
      g.step(ks, 1 / 60);
      Object.assign(ks[0]!, { x: 50, z: 0 });
    };
    fetch();
    expect(g.score[0]).toBe(1);
    // A rival steals it.
    Object.assign(ks[1]!, { x: 30, z: 30 });
    g.step(ks, 1 / 60);
    expect(g.score[0]).toBe(0);
    expect(g.eggs.some((e) => e.carrier === 1)).toBe(true);
    // Hit while carrying: dropped.
    g.hit(1);
    expect(g.eggs.some((e) => e.carrier === 1)).toBe(false);
    Object.assign(ks[1]!, { x: -50, z: 0 });
    for (let n = 0; n < 3; n++) fetch();
    expect(g.winner).toBe(0);
  });

  it("Crown Hill: the holder scores while they stay in the ring; out, and it passes on", () => {
    const g = createMiniGame(minigameById("crown")!, arena, 4);
    const ks = karts();
    Object.assign(ks[2]!, { x: 1, z: 1 });
    for (let k = 0; k < 60 * 5; k++) g.step(ks, 1 / 60);
    expect(g.score[2]).toBeGreaterThanOrEqual(4);
    // Another drives in: the holder keeps it.
    Object.assign(ks[3]!, { x: -1, z: 1 });
    for (let k = 0; k < 60 * 2; k++) g.step(ks, 1 / 60);
    expect(g.holder).toBe(2);
    // Shoved out: it passes to the one still in.
    Object.assign(ks[2]!, { x: 50, z: 50 });
    g.step(ks, 1 / 60);
    expect(g.holder).toBe(3);
    for (let k = 0; k < 60 * 40; k++) g.step(ks, 1 / 60);
    expect(g.winner).toBe(3);
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
      if (m.id === "eggs") {
        expect(a.nests).toHaveLength(4);
        expect(a.eggSpawn).toBeDefined();
      }
      if (m.id === "crown") expect(a.crown).toBeDefined();
    }
  });
});
