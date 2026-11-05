// The detailed folk posed about the Rookery's buildings and the Rusty Anchor Fish Fry
// (Blake, Nov 4: "we need to bring up the fidelity of the npcs in the buildings").
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { FOLK_POSES, folkPoseCue, parseFolkPoses } from "../src/game/folkPoses";

const meta = JSON.parse(
  readFileSync(new URL("../public/tracks/journey_cause/track.json", import.meta.url), "utf8"),
) as { entities: ({ type: string } & Record<string, unknown>)[] };

describe("posed folk", () => {
  it("reads its list, keeping only poses it knows", () => {
    const p = parseFolkPoses({
      list: [
        [1, 2, 3, 0.5, "wave", 7],
        [0, 0, 0, 0, "juggle", 2],
        [1, 2],
      ],
    });
    expect(p).toHaveLength(2);
    expect(p[0]).toMatchObject({ x: 1, y: 2, z: 3, heading: 0.5, pose: "wave", seed: 7 });
    expect(p[1]!.pose).toBe("watch");
  });

  it("keeps busy at their thing, glances at you as you come by, and carries on", () => {
    const [a] = parseFolkPoses({ list: [[0, 0, 0, 0, "eat", 4, 1, 1, 1]] });
    expect(a!.target).toEqual({ x: 1, y: 1, z: 1 });
    const st = { seen: false, glance: 0 };
    const you = { x: 9, y: 9, z: 9 } as never;
    const at = { set: (x: number, y: number, z: number) => ({ x, y, z }) } as never;
    // (far off: eating, looking at the plate)
    let q = folkPoseCue(a!, st, 0, 0.1, false, you, at);
    expect(q.gesture).toBe("eat");
    expect(q.look).toEqual({ x: 1, y: 1, z: 1 });
    // (you come by: a glance at you, then back to the plate though you're still there)
    q = folkPoseCue(a!, st, 0.1, 0.1, true, you, at);
    expect(q.look).toBe(you);
    for (let t = 0; t < 3; t += 0.1) q = folkPoseCue(a!, st, t, 0.1, true, you, at);
    expect(q.look).toEqual({ x: 1, y: 1, z: 1 });
    expect(q.gesture).toBe("eat");
  });

  it("gestures now and then, each on their own clock", () => {
    const [a] = parseFolkPoses({ list: [[0, 0, 0, 0, "wave", 3]] });
    const st = { seen: false, glance: 0 };
    const cues = Array.from({ length: 80 }, (_, i) =>
      folkPoseCue(a!, st, i * 0.25, 0.25, false, null, null),
    );
    expect(cues.some((q) => q.gesture === "wave")).toBe(true);
    expect(cues.some((q) => !q.gesture)).toBe(true);
    // (chatters talk by turns)
    const [ch] = parseFolkPoses({ list: [[0, 0, 0, 0, "chat", 5]] });
    const talk = Array.from(
      { length: 40 },
      (_, i) => folkPoseCue(ch!, st, i * 0.5, 0.5, false, null, null).talk,
    );
    expect(talk.some(Boolean)).toBe(true);
    expect(talk.some((x) => !x)).toBe(true);
  });

  it("stands the Edge's slum and diner full of them, all in poses the game knows", () => {
    const e = meta.entities.filter((x) => x.type === "folk_poses");
    expect(e).toHaveLength(1);
    expect(e[0]!.folk).toBe("sump");
    const list = parseFolkPoses(e[0]!);
    expect(list.length).toBeGreaterThan(60);
    for (const r of e[0]!.list as unknown[][]) expect(FOLK_POSES).toContain(r[4]);
    // (busy at things, not staring: cooks, diners, chatters, rail-leaners)
    for (const pose of ["cook", "eat", "chat", "lean"])
      expect(list.filter((p) => p.pose === pose).length).toBeGreaterThan(3);
    expect(list.filter((p) => p.pose === "watch").length).toBe(0);
  });
});
