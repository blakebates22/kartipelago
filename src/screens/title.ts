/**
 * BOOT and TITLE.
 *
 * Boot is a moment's splash while the title demo loads (any key skips it). The title
 * shows the logo bouncing in over a live demo race on Dino Demo (the AI drives every
 * kart, the camera circles your racer), "PRESS START", and then the main menu: Play,
 * Options, Music and Credits.
 */
import type { Game } from "../app/game";
import type { MenuAction } from "../app/menuInput";
import type { Screen } from "../app/app";
import type { Session } from "../game/session";
import { trackById } from "../game/tracks";
import { landscape, logo } from "../ui/backdrops";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { characterSelect } from "./characterSelect";
import { optionsScreen } from "./options";
import { musicPlayer } from "./musicPlayer";
import { creditsScreen } from "./credits";

export function bootScreen(game: Game): Screen {
  let t = 0;
  return {
    id: "BOOT",
    enter() {
      // Start rendering the first two pieces of music while the splash shows.
      game.audio.music.prepare("title");
      game.audio.music.prepare("select");
    },
    frame(dt, actions) {
      t += dt;
      if (t > 1.4 || actions.length || game.menuInput.pointer.clicked)
        game.screens.go(titleScreen(game));
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#0b0710");
      const a = Math.min(1, t * 3) * Math.min(1, (1.4 - t) * 4 + 0.2);
      ui.g.globalAlpha = Math.max(0, a);
      ui.text("A KARTIPELAGO CONTRIBUTORS GAME", ui.W / 2, 104, {
        align: "center",
        color: PAL.cream,
      });
      ui.text("ORIGINAL · OPEN SOURCE · MIT", ui.W / 2, 120, { align: "center", color: PAL.gold });
      ui.g.globalAlpha = 1;
    },
  };
}

export function titleScreen(game: Game, startInMenu = false): Screen {
  let t = 0;
  let mode: "press" | "menu" = startInMenu ? "menu" : "press";
  let session: Session | undefined;
  let alive = true;
  const calm = () => game.settings.general.reduceMotion;
  const menu = new VMenu(
    game,
    [
      { label: "PLAY", action: () => game.screens.go(characterSelect(game)) },
      { label: "OPTIONS", action: () => game.screens.push(optionsScreen(game)) },
      { label: "MUSIC", action: () => game.screens.push(musicPlayer(game)) },
      { label: "CREDITS", action: () => game.screens.push(creditsScreen(game)) },
    ],
    () => (mode = "press"),
  );

  async function loadDemo() {
    const token = game.screens.token;
    const tries = ["dino_demo", "drift_loop"];
    for (const id of tries) {
      const entry = trackById(id)!;
      try {
        const s = await game.createSession({
          scene: entry.load.scene,
          packageId: entry.load.packageId,
          trackData: entry.load.trackData,
          rivals: true,
          racer: game.settings.last.racer,
          demo: true,
        });
        if (!alive || token !== game.screens.token) {
          s.dispose();
          return;
        }
        session = s;
        return;
      } catch (err) {
        console.warn("[title] demo track failed to load:", err);
      }
    }
  }

  return {
    id: "TITLE",
    enter() {
      game.ui.interactive = true;
      void game.audio.music.play("title", { fade: 1 });
      void loadDemo();
    },
    resume() {
      void game.audio.music.play("title", { fade: 0.6 });
    },
    exit() {
      alive = false;
      session?.dispose();
      session = undefined;
    },
    step(dt) {
      session?.update(dt);
    },
    render3d(alpha, frameSeconds) {
      if (!session) return false;
      session.render(alpha, frameSeconds);
      game.stage.render();
      return true;
    },
    frame(dt, actions: MenuAction[]) {
      t += dt;
      if (mode === "press") {
        if (
          actions.some((a) => a === "confirm" || a === "pause") ||
          game.menuInput.pointer.clicked
        ) {
          game.sounds.start();
          mode = "menu";
        }
      } else menu.handle(actions);
    },
    draw(ui: UiLayer) {
      if (!session) landscape(ui.g, ui.W, ui.H, t, calm());
      // A soft band behind the logo so it reads over any scene.
      ui.rect(0, 14, ui.W, 46, "#0b0710", 0.18);
      logo(ui.g, ui.W / 2, 22, t, 3, calm());
      ui.text("ISLAND KART RACING", ui.W / 2, 50, {
        align: "center",
        color: PAL.cream,
        outline: PAL.shadow,
      });
      if (mode === "press") {
        const on = calm() || Math.floor(t * 2.2) % 2 === 0;
        if (on && t > 0.9)
          ui.text("PRESS START", ui.W / 2, 176, {
            align: "center",
            scale: 2,
            color: PAL.gold,
            outline: PAL.shadow,
          });
        if (!game.audio.running && t > 0.9)
          ui.text("(PRESS ANY KEY OR CLICK FOR SOUND)", ui.W / 2, 198, {
            align: "center",
            color: PAL.cream,
            outline: PAL.shadow,
          });
      } else {
        menu.draw(ui, ui.W / 2 - 50, 110, 100, 20, 5);
        hints(ui, [
          ["▲▼", "CHOOSE"],
          ["ENTER", "SELECT"],
          ["ESC", "BACK"],
        ]);
      }
      if (mode === "press")
        ui.text("(C) 2026 KARTIPELAGO CONTRIBUTORS · MIT LICENCE", ui.W / 2, ui.H - 11, {
          align: "center",
          color: "#e8d5b0",
          shadow: PAL.shadow,
        });
    },
  };
}
