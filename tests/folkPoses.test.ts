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

  it("gestures now and then, each on their own clock, and watches you when you're near", () => {
    const [a] = parseFolkPoses({ list: [[0, 0, 0, 0, "wave", 3]] });
    const cues = Array.from({ length: 80 }, (_, i) => folkPoseCue(a!, i * 0.25, false, null));
    expect(cues.some((q) => q.gesture === "wave")).toBe(true);
    expect(cues.some((q) => !q.gesture)).toBe(true);
    const look = { x: 1, y: 2, z: 3 } as never;
    expect(folkPoseCue(a!, 0, true, look).look).toBe(look);
    expect(folkPoseCue(a!, 0, false, look).look).toBeNull();
  });

  it("stands the Edge's slum and diner full of them, all in poses the game knows", () => {
    const e = meta.entities.filter((x) => x.type === "folk_poses");
    expect(e).toHaveLength(1);
    expect(e[0]!.folk).toBe("sump");
    const list = parseFolkPoses(e[0]!);
    expect(list.length).toBeGreaterThan(60);
    for (const r of e[0]!.list as unknown[][]) expect(FOLK_POSES).toContain(r[4]);
    // (the diner: its cooks at work round the Rookery's middle)
    expect(list.filter((p) => p.pose === "work").length).toBeGreaterThan(5);
  });
});
