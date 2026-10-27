/**
 * MODE_SELECT: two wooden signboards, TRACKS and ADVENTURE, on a stone terrace looking
 * out over the island, the sea and the Dragon Kingdom (art in ui/modeArt.ts).
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import {
  PLINTH,
  TRIKE_FEET,
  TRIKE_FROM_RIGHT,
  modeBoard,
  modeVista,
  terraceDino,
  titlePlank,
} from "../ui/modeArt";
import { triceratops } from "../ui/modeRuins";
import { PAL } from "../ui/textures";
import { hints } from "./common";
import { characterSelect } from "./characterSelect";
import { adventureFiles } from "./adventure";
import { titleScreen } from "./title";

export function modeSelect(game: Game): Screen {
  let focus = 0;
  let t = 0;
  let clicked = -1;
  const pick = (i: number) => {
    game.sounds.confirm();
    // Tracks: pick a racer, then a course. Adventure: pick a file (each has its racer).
    // (The mini-games are in the Tracks menu's DEV tab for now: Blake, Oct 27.)
    if (i === 0) game.screens.go(characterSelect(game));
    else game.screens.go(adventureFiles(game));
  };
  return {
    id: "MODE_SELECT",
    seeThrough: false,
    enter() {
      void game.audio.music.play("map", { fade: 1 });
    },
    frame(dt, actions) {
      t += dt;
      if (clicked >= 0) {
        const c = clicked;
        clicked = -1;
        return pick(c);
      }
      for (const a of actions) {
        if (a === "left" || a === "up") {
          if (focus > 0) game.sounds.move();
          focus = Math.max(0, focus - 1);
        } else if (a === "right" || a === "down") {
          if (focus < 1) game.sounds.move();
          focus = Math.min(1, focus + 1);
        } else if (a === "confirm") return pick(focus);
        else if (a === "back") {
          game.sounds.back();
          return game.screens.go(titleScreen(game, true));
        }
      }
    },
    draw(ui) {
      const calm = game.settings.general.reduceMotion;
      modeVista(ui.g, ui.W, ui.H, t, calm);
      // The dino stands on the left ledge when there's room beside the boards.
      if (ui.W / 2 - 128 - 15 > 64) {
        terraceDino(ui.g, 38, PLINTH - 22, t, calm);
        // And a triceratops grazing on the ruins on the other side.
        triceratops(ui.g, ui.W - TRIKE_FROM_RIGHT, TRIKE_FEET, t, calm);
      }
      titlePlank(ui.g, ui.W, "CHOOSE A MODE", t, calm);
      const signs = [
        { label: "TRACKS", sub: "ANY COURSE", icon: "flag" as const },
        { label: "ADVENTURE", sub: "THE STORY", icon: "map" as const },
      ];
      const gap = 10;
      const n = signs.length;
      const w = Math.min(128, Math.floor((ui.W - 24 - (n - 1) * gap) / n));
      const h = 80;
      signs.forEach((s, i) => {
        const x = Math.round(ui.W / 2 - (n * w + (n - 1) * gap) / 2 + i * (w + gap));
        const sway = calm ? 0 : Math.round(Math.sin(t * 2 + i) * (i === focus ? 1.5 : 0.4));
        const y = 96 + sway;
        modeBoard(ui.g, x, y, w, h, { ...s, focused: i === focus }, t, calm);
        const over = ui.hover(x, y, w, h);
        if (over && game.menuInput.pointer.moved && focus !== i) {
          focus = i;
          game.sounds.move();
        }
        if (over && game.menuInput.pointer.clicked) clicked = i;
        if (i === focus) {
          // A gold arrow pointing at the chosen board, bobbing.
          const bob = calm ? 0 : Math.round(Math.sin(t * 6) * 1.5);
          ui.text("▼", x + w / 2, y - 18 + bob, {
            scale: 2,
            color: PAL.gold,
            outline: PAL.shadow,
            align: "center",
          });
        }
      });
      hints(ui, [
        ["◀▶", "CHOOSE"],
        ["ENTER", "SELECT"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
