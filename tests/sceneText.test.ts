// Every line of every scene fits its text box (Blake, Oct 28: lines were being cut off):
// three lines in a staged scene's box, four in a picture scene's, on a 16:9 screen, with
// the speaker's portrait inside the box.
import { describe, expect, it } from "vitest";
import { SCENES } from "../src/adventure/scenes";
import { portraitSlot } from "../src/screens/adventure";
import { wrap } from "../src/ui/font";
import { UI_H } from "../src/ui/layer";

describe("the scenes' lines", () => {
  it("fit their text boxes", () => {
    const W = Math.round((UI_H * 16) / 9);
    const bx = 10;
    const bw = W - 20;
    const long: string[] = [];
    for (const sc of Object.values(SCENES)) {
      const staged = !sc.backdrop.storybook;
      const bh = staged ? 54 : 64;
      for (const b of sc.beats) {
        const tx = b.who ? portraitSlot(bx, 100, bh).tx : bx + 10;
        const lines = wrap(b.text, bw - (tx - bx) - 10).length;
        if (lines > (staged ? 3 : 4)) long.push(`${sc.id}: ${b.text}`);
      }
    }
    expect(long).toEqual([]);
  });
});
