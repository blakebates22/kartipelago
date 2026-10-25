// The Tracks menu shows three lines of a course's description under its picture (see
// src/screens/tracks.ts): every course in the menus must fit them on a 16:9 screen.
import { describe, expect, it } from "vitest";
import { trackById } from "../src/game/tracks";
import { VISIBLE_WORLDS } from "../src/game/worlds";
import { wrap } from "../src/ui/font";
import { UI_H } from "../src/ui/layer";

describe("track descriptions", () => {
  it("fit the menu's three lines on a 16:9 screen", () => {
    const W = Math.round((UI_H * 16) / 9);
    const pw = W - (14 + Math.round(W * 0.4) + 14) - 14;
    const long: string[] = [];
    for (const w of VISIBLE_WORLDS)
      for (const id of w.tracks) {
        const t = trackById(id);
        if (t && wrap(t.description.toUpperCase(), pw).length > 3) long.push(id);
      }
    expect(long).toEqual([]);
  });
});
