/**
 * MODE_SELECT: two big wooden signs, TRACKS and ADVENTURE, over the island.
 * ADVENTURE_COMING_SOON: a treasure-map teaser with a Back button. Adventure itself
 * isn't built yet; nothing here pretends it is.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { landscape, treasureMap } from "../ui/backdrops";
import { PAL } from "../ui/textures";
import { hints, titleSign } from "./common";
import { characterSelect } from "./characterSelect";
import { trackSelect } from "./trackSelect";

export function modeSelect(game: Game): Screen {
  let focus = 0;
  let t = 0;
  let clicked = -1;
  const pick = (i: number) => {
    game.sounds.confirm();
    if (i === 0) game.screens.go(trackSelect(game));
    else game.screens.go(comingSoon(game));
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
          if (focus !== 0) game.sounds.move();
          focus = 0;
        } else if (a === "right" || a === "down") {
          if (focus !== 1) game.sounds.move();
          focus = 1;
        } else if (a === "confirm") return pick(focus);
        else if (a === "back") {
          game.sounds.back();
          return game.screens.go(characterSelect(game));
        }
      }
    },
    draw(ui) {
      landscape(ui.g, ui.W, ui.H, t, game.settings.general.reduceMotion);
      titleSign(ui, "CHOOSE A MODE");
      const signs = [
        { label: "TRACKS", sub: "RACE ANY COURSE", color: PAL.gold },
        { label: "ADVENTURE", sub: "COMING SOON", color: "#cfe9a8" },
      ];
      const w = 128;
      const gap = 16;
      signs.forEach((s, i) => {
        const x = ui.W / 2 - w - gap / 2 + i * (w + gap);
        const sway = game.settings.general.reduceMotion
          ? 0
          : Math.round(Math.sin(t * 2 + i) * (i === focus ? 2 : 0.6));
        const y = 74 + sway;
        // Posts in the ground.
        ui.rect(x + 22, y + 60, 6, 80, "#5a3318");
        ui.rect(x + w - 28, y + 60, 6, 80, "#5a3318");
        const r = ui.button(x, y, w, 64, s.label, {
          focused: i === focus,
          scale: 2,
          color: i === focus ? s.color : PAL.cream,
          sub: s.sub,
        });
        if (r.hover && game.menuInput.pointer.moved && focus !== i) {
          focus = i;
          game.sounds.move();
        }
        if (r.clicked) clicked = i;
      });
      hints(ui, [
        ["◀▶", "CHOOSE"],
        ["ENTER", "SELECT"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

export function comingSoon(game: Game): Screen {
  let t = 0;
  let clicked = false;
  const back = () => {
    game.sounds.back();
    game.screens.go(modeSelect(game));
  };
  return {
    id: "ADVENTURE_COMING_SOON",
    seeThrough: false,
    frame(dt, actions) {
      t += dt;
      if (clicked || actions.some((a) => a === "back" || a === "confirm")) back();
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#2f6f9a");
      const w = 300;
      const h = 196;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = 18;
      ui.panel(x, y, w, h, "parchment", "ink");
      treasureMap(ui.g, x + 8, y + 26, w - 16, 118, t);
      ui.text("ADVENTURE", ui.W / 2, y + 8, {
        scale: 2,
        color: PAL.coral,
        outline: PAL.ink,
        align: "center",
      });
      ui.text("COMING SOON!", ui.W / 2, y + 148, { scale: 2, color: PAL.ink, align: "center" });
      ui.text("AN ISLAND TO EXPLORE, RACES TO WIN AND SECRETS", ui.W / 2, y + 168, {
        color: PAL.inkSoft,
        align: "center",
      });
      ui.text("TO FIND. FOR NOW, HEAD TO TRACKS MODE!", ui.W / 2, y + 177, {
        color: PAL.inkSoft,
        align: "center",
      });
      const r = ui.button(ui.W / 2 - 40, ui.H - 26, 80, 18, "BACK", { focused: true });
      if (r.clicked) clicked = true;
    },
  };
}
