/** CREDITS: who made this, on a slowly scrolling parchment. */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { PAL } from "../ui/textures";
import { hints } from "./common";

const LINES: [string, "head" | "text" | "gap"][] = [
  ["KARTIPELAGO", "head"],
  ["AN ORIGINAL ISLAND KART RACER", "text"],
  ["", "gap"],
  ["CREATED BY", "head"],
  ["BLAKE BATES", "text"],
  ["AND THE KARTIPELAGO CONTRIBUTORS", "text"],
  ["", "gap"],
  ["RACERS", "head"],
  ["MOSS · BRAMBLE · POPPY · OTTO", "text"],
  ["", "gap"],
  ["MUSIC AND SOUND", "head"],
  ["ORIGINAL, PLAYED BY A TINY SYNTH BAND", "text"],
  ["", "gap"],
  ["BUILT WITH", "head"],
  ["THREE.JS · VITE · TYPESCRIPT · BLENDER", "text"],
  ["", "gap"],
  ["INSPIRED BY", "head"],
  ["THE PLAYFUL KART RACERS OF THE LATE 1990S", "text"],
  ["", "gap"],
  ["CODE, ART AND MUSIC: MIT LICENCE", "text"],
  ["", "gap"],
  ["THANKS FOR PLAYING!", "head"],
];

export function creditsScreen(game: Game): Screen {
  let t = 0;
  let close = false;
  return {
    id: "CREDITS",
    enter() {
      game.ui.interactive = true;
    },
    frame(dt, actions) {
      t += dt;
      if (close || actions.some((a) => a === "back" || a === "confirm")) {
        game.sounds.back();
        game.screens.pop();
      }
    },
    draw(ui) {
      ui.dim(0.45);
      const w = 260;
      const x = Math.round(ui.W / 2 - w / 2);
      ui.panel(x, 16, w, 196, "parchment", "ink");
      const g = ui.g;
      g.save();
      g.beginPath();
      g.rect(x + 6, 22, w - 12, 184);
      g.clip();
      // Starts at the top, rests a moment, then rolls up and round again.
      const total = LINES.length * 11 + 190;
      const scroll = game.settings.general.reduceMotion ? 0 : (Math.max(0, t - 2.5) * 12) % total;
      let y = 30 - scroll;
      if (y < 30 - LINES.length * 11) y += total;
      for (const [text, kind] of LINES) {
        if (kind === "head") ui.text(text, ui.W / 2, y, { color: PAL.coral, align: "center" });
        else if (kind === "text") ui.text(text, ui.W / 2, y, { color: PAL.ink, align: "center" });
        y += 11;
      }
      g.restore();
      if (game.menuInput.pointer.clicked) close = true;
      hints(ui, [["ESC", "BACK"]]);
    },
  };
}
