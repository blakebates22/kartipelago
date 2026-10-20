/**
 * LOADING: a wooden sign, a rolling tyre and a racing tip while the track loads and
 * the race is built. Then straight into the race (and its countdown).
 * LOAD_ERROR: if the track couldn't load, say why and go back to Track Select.
 *
 * The load is tied to the screen manager's token: if you've left by the time it
 * finishes, the half-built race is thrown away.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { trackById } from "../game/tracks";
import { landscape, rollingTyre } from "../ui/backdrops";
import { wrap } from "../ui/font";
import { PAL } from "../ui/textures";
import { raceScreen } from "./race";
import { trackSelect } from "./trackSelect";

const TIPS = [
  "HOLD DRIFT INTO A CORNER, THEN STEER TO TIGHTEN OR WIDEN YOUR ARC.",
  "LET GO OF THE THROTTLE AS A ZIPPER FIRES, THEN PRESS IT AGAIN AT THE RAINBOW.",
  "PRESS THE THROTTLE JUST BEFORE GO FOR A PERFECT START.",
  "DINO EGGS MAKE YOUR KART FASTER. GETTING HIT MAKES YOU DROP SOME.",
  "BALLOON ITEMS FIRE WHEN YOU LET GO OF THE ITEM BUTTON.",
  "PRESS ESC OR START TO PAUSE AT ANY TIME.",
];

const MIN_SHOW = 0.9;

export function loadingScreen(game: Game): Screen {
  let t = 0;
  let ready: Awaited<ReturnType<Game["createSession"]>> | undefined;
  let failed: string | undefined;
  let alive = true;
  const entry = trackById(game.selection.trackId) ?? trackById("drift_loop")!;
  const tip = TIPS[Math.floor(Math.random() * TIPS.length)]!;

  return {
    id: "LOADING",
    seeThrough: false,
    enter() {
      game.ui.interactive = false;
      game.audio.music.stop(0.6);
      game.audio.music.prepare(entry.music);
      const token = game.screens.token;
      game
        .createSession({
          scene: entry.load.scene,
          trackData: entry.load.trackData,
          packageId: entry.load.packageId,
          rivals: game.selection.mode === "race",
          racer: game.selection.racer,
        })
        .then((s) => {
          if (!alive || token !== game.screens.token) return s.dispose();
          ready = s;
        })
        .catch((err: Error) => {
          console.error(err);
          if (alive) failed = err.message;
        });
    },
    exit() {
      alive = false;
    },
    frame(dt) {
      t += dt;
      if (failed !== undefined) {
        const msg = failed;
        failed = undefined;
        return game.screens.go(loadError(game, entry.name, msg));
      }
      if (ready && t >= MIN_SHOW) {
        const s = ready;
        ready = undefined;
        alive = false; // the race owns the session now
        game.screens.go(raceScreen(game, s, entry));
      }
    },
    draw(ui) {
      landscape(ui.g, ui.W, ui.H, t, game.settings.general.reduceMotion);
      ui.dim(0.25);
      const w = 200;
      const x = ui.W / 2 - w / 2;
      ui.panel(x, 64, w, 74, "wood", "gold");
      ui.text("LOADING", ui.W / 2, 74, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text(entry.name.toUpperCase(), ui.W / 2, 94, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      const tx = x + 20 + ((t * 70) % (w - 40));
      rollingTyre(ui.g, Math.round(tx), 118, t);
      ui.panel(ui.W / 2 - 140, 162, 280, 40, "parchment", "ink");
      ui.text("TIP", ui.W / 2, 168, { color: PAL.coral, align: "center" });
      wrap(tip, 260).forEach((l, i) =>
        ui.text(l, ui.W / 2, 179 + i * 9, { color: PAL.ink, align: "center" }),
      );
    },
  };
}

export function loadError(game: Game, name: string, message: string): Screen {
  let clicked = false;
  const back = () => game.screens.go(trackSelect(game));
  return {
    id: "LOAD_ERROR",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      game.sounds.error();
    },
    frame(_dt, actions) {
      if (clicked || actions.some((a) => a === "back" || a === "confirm")) back();
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#2b1b14");
      ui.panel(ui.W / 2 - 140, 60, 280, 110, "parchment", "ink");
      ui.text("UH OH!", ui.W / 2, 70, {
        scale: 2,
        color: PAL.coral,
        outline: PAL.ink,
        align: "center",
      });
      ui.text(`${name.toUpperCase()} WOULDN'T LOAD.`, ui.W / 2, 92, {
        color: PAL.ink,
        align: "center",
      });
      wrap(message.toUpperCase(), 250)
        .slice(0, 4)
        .forEach((l, i) =>
          ui.text(l, ui.W / 2, 106 + i * 9, { color: PAL.inkSoft, align: "center" }),
        );
      const r = ui.button(ui.W / 2 - 60, 146, 120, 18, "TRACK SELECT", { focused: true });
      if (r.clicked) clicked = true;
    },
  };
}
