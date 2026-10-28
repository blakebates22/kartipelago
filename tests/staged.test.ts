// Staged scenes (src/adventure/staged.ts): each stages a real scene, in a region that
// exists, with a shot for every line, and only names actors it has; and every scene
// the story plays in the 3D world has its staging (the opening is a storybook, the
// credits roll).
import { describe, expect, it } from "vitest";
import { STAGED } from "../src/adventure/staged";
import { SCENES, sceneById } from "../src/adventure/scenes";
import { OPENING } from "../src/adventure/data";
import { regionById } from "../src/overworld/regions";

describe("staged scenes", () => {
  it.each(STAGED.map((s) => [s.scene, s] as const))("%s", (_id, s) => {
    const sc = sceneById(s.scene);
    expect(sc).toBeDefined();
    expect(regionById(s.region)).toBeDefined();
    expect(s.beats.length).toBe(sc!.beats.length);
    for (const b of s.beats) {
      expect(b.cam).toBeDefined();
      for (const m of b.moves ?? []) expect(s.actors[m.actor], m.actor).toBeDefined();
      for (const a of [b.fx?.fire, b.fx?.rear, ...(b.fx?.show ?? []), ...(b.fx?.hide ?? [])])
        if (a) expect(s.actors[a], a).toBeDefined();
    }
  });

  it("stage every scene but the opening's storybook", () => {
    const staged = new Set(STAGED.map((s) => s.scene));
    for (const id of Object.keys(SCENES)) if (id !== OPENING) expect(staged, id).toContain(id);
  });
});
