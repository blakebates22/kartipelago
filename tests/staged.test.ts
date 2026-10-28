// Staged scenes (src/adventure/staged.ts): each stages a real scene, in a region that
// exists, with a shot for every line, and only names actors it has; and every scene
// the story plays in the 3D world has its staging (the opening is a storybook, the
// credits roll).
import { describe, expect, it } from "vitest";
import { CUES, STAGED } from "../src/adventure/staged";
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
      // Poses are for dragons, gestures for those on foot; music is one of the score's cues.
      for (const a of Object.keys(b.fx?.pose ?? {})) expect(s.actors[a]?.kind, a).toBe("dragon");
      for (const a of Object.keys(b.fx?.gesture ?? {}))
        expect(["elder", "guard", "villager"], a).toContain(s.actors[a]?.kind);
      if (b.fx?.music) expect(CUES as readonly string[]).toContain(b.fx.music);
    }
    if (s.music) expect(CUES as readonly string[]).toContain(s.music);
  });

  it("stage every scene but the opening's storybook", () => {
    const staged = new Set(STAGED.map((s) => s.scene));
    for (const id of Object.keys(SCENES)) if (id !== OPENING) expect(staged, id).toContain(id);
  });
});
