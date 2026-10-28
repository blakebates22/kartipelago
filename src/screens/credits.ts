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
  ["", "gap"],
  ["STORY AND ART", "head"],
  ["SIENNA BATES", "text"],
  ["", "gap"],
  ["WITH", "head"],
  ["THE KARTIPELAGO CONTRIBUTORS", "text"],
  ["", "gap"],
  ["RACERS", "head"],
  ["TIKO · BRAKKA · PEBBLE · ZEPHYR", "text"],
  ["REX · BRACHIO · STEGO · RAPTOR", "text"],
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

/**
 * The credits rolled over the whole screen in Adventure: at the real ending, and at the
 * fake one (Blake, Oct 27: the King stunned, the credits start to roll... and break off,
 * the screen shaking and going red as he wakes). ENTER or ESC skips them.
 */
export function rollingCredits(game: Game, o: { fake: boolean; then: () => void }): Screen {
  let t = 0;
  let done = false;
  /** When the fake credits break off. */
  const BREAK = 9;
  const finish = () => {
    if (done) return;
    done = true;
    o.then();
  };
  return {
    id: "CREDITS",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      void game.audio.music.play("fanfare", { fade: 0.5 });
    },
    frame(dt, actions) {
      t += dt;
      if (actions.some((a) => a === "back" || a === "confirm") && t > 0.5) {
        game.sounds.back();
        return finish();
      }
      if (o.fake && t > BREAK && t - dt <= BREAK) {
        game.audio.music.stop(0.1);
        game.sounds.gong(1);
      }
      if (o.fake ? t > BREAK + 3.5 : t > LINES.length * 1.0 + 16) finish();
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#0c0a08");
      const broke = o.fake && t > BREAK;
      const k = broke ? Math.min(1, (t - BREAK) / 1.5) : 0;
      const shake = broke ? (1 - k * 0.5) * 6 : 0;
      const sx = Math.sin(t * 47) * shake;
      const sy = Math.cos(t * 39) * shake;
      // Rolls up from the bottom (stops dead when it breaks).
      const at = broke ? BREAK : t;
      const speed = game.settings.general.reduceMotion ? 0 : 16;
      let y = ui.H + 10 - at * speed;
      for (const [text, kind] of LINES) {
        if (y > -12 && y < ui.H + 12) {
          if (kind === "head")
            ui.text(text, ui.W / 2 + sx, y + sy, { color: PAL.gold, align: "center" });
          else if (kind === "text")
            ui.text(text, ui.W / 2 + sx, y + sy, { color: PAL.cream, align: "center" });
        }
        y += 14;
      }
      if (o.fake && !broke)
        ui.text("THE END", ui.W / 2, 20, { scale: 2, color: PAL.gold, align: "center" });
      if (broke) {
        ui.rect(0, 0, ui.W, ui.H, "#8a0a00", 0.25 + 0.45 * k);
        if (t > BREAK + 1.2)
          ui.text("...", ui.W / 2, ui.H / 2 - 6, { scale: 3, color: PAL.cream, align: "center" });
      }
      hints(ui, [["ENTER", "SKIP"]]);
    },
  };
}
