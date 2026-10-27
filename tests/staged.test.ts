// Staged scenes (src/adventure/staged.ts): each stages a real scene, in a region that
// exists, with a shot for every line, and only names actors it has.
import { describe, expect, it } from "vitest";
import { STAGED } from "../src/adventure/staged";
import { sceneById } from "../src/adventure/scenes";
import { regionById } from "../src/overworld/regions";

describe("staged scenes", () => {
  it.each(STAGED.map((s) => [s.scene, s] as const))("%s", (_id, s) => {
    const sc = sceneById(s.scene);
    expect(sc).toBeDefined();
    expect(regionById(s.region)).toBeDefined();
    expect(s.beats.length).toBe(sc!.beats.length);
    for (const b of s.beats) {
      for (const m of b.moves ?? []) expect(s.actors[m.actor], m.actor).toBeDefined();
      for (const a of [b.fx?.fire, b.fx?.rear]) if (a) expect(s.actors[a], a).toBeDefined();
    }
  });
});
