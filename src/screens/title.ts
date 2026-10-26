/**
 * BOOT and TITLE.
 *
 * Boot is a moment's splash while the title demo loads (any key skips it). The title
 * shows the logo bouncing in over a montage of live demo races (Blake: the opening
 * should show the range of the game's courses, not a level you can't play): a few
 * seconds on each of a run of real courses from every world, the AI driving every kart
 * and the camera circling your racer, cut through black. Then "PRESS START" and the
 * main menu: Play, Options, Music and Credits. Party Beach stands in if none loads.
 */
import type { Game } from "../app/game";
import type { MenuAction } from "../app/menuInput";
import type { Screen } from "../app/app";
import type { Session } from "../game/session";
import { TITLE_MONTAGE, TITLE_TRACK, trackById } from "../game/tracks";
import { landscape, logo } from "../ui/backdrops";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { modeSelect } from "./modeSelect";
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

/** Seconds on each course, and the fade through black between them. */
const CLIP = 11;
const FADE = 0.5;

export function titleScreen(game: Game, startInMenu = false): Screen {
  let t = 0;
  let mode: "press" | "menu" = startInMenu ? "menu" : "press";
  let session: Session | undefined;
  /** Seconds since the demo race appeared (it fades in from black). */
  let shown = 0;
  /** No demo track would load: the painted landscape stands in. */
  let failed = false;
  let alive = true;
  /** The montage: which course is next, how long this one has shown, and whether any
   * has (from then on the logo and menu stay up while the next one loads). */
  let clip = 0;
  /** When this course appeared (wall-clock ms: a slow machine still cuts on time). */
  let clipAt = 0;
  const onClip = () => (performance.now() - clipAt) / 1000;
  let everShown = false;
  let loading = false;
  const calm = () => game.settings.general.reduceMotion;
  const menu = new VMenu(
    game,
    [
      { label: "PLAY", action: () => game.screens.go(modeSelect(game)) },
      { label: "OPTIONS", action: () => game.screens.push(optionsScreen(game)) },
      { label: "MUSIC", action: () => game.screens.push(musicPlayer(game)) },
      { label: "CREDITS", action: () => game.screens.push(creditsScreen(game)) },
    ],
    () => (mode = "press"),
  );

  async function loadDemo() {
    const token = game.screens.token;
    loading = true;
    // The montage's next course (any that won't load are skipped), then Party Beach and
    // the test tracks as the last resort.
    const montage = TITLE_MONTAGE.map((_, k) => TITLE_MONTAGE[(clip + k) % TITLE_MONTAGE.length]!)
      .map((id) => trackById(id))
      .filter((e): e is NonNullable<typeof e> => Boolean(e));
    const tries = [
      ...montage.slice(0, 3),
      TITLE_TRACK,
      trackById("dino_demo")!,
      trackById("drift_loop")!,
    ];
    for (const entry of tries) {
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
        // Into the race a little (the grid and the countdown are the same on every
        // course): a few seconds, different each time, run while the screen is black.
        const k = TITLE_MONTAGE.indexOf(entry.id);
        if (k >= 0) for (let i = 0, n = (8 + ((k * 5) % 12)) * 120; i < n; i++) s.update(1 / 120);
        session = s;
        clipAt = performance.now();
        everShown = true;
        loading = false;
        clip = k >= 0 ? (k + 1) % TITLE_MONTAGE.length : clip;
        return;
      } catch (err) {
        console.warn("[title] demo track failed to load:", err);
      }
    }
    loading = false;
    if (!everShown) failed = true;
  }

  /** Cut to the montage's next course (the current one has had its few seconds). */
  function nextClip() {
    session?.dispose();
    session = undefined;
    void loadDemo();
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
      if (everShown) shown += dt;
      if (session && onClip() >= CLIP && !loading) nextClip();
      // Nothing to press until there's something to see.
      if (!everShown && !failed) return;
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
      // Until the demo race is ready the screen stays black (no logo or menu over an
      // empty screen, and no painted landscape flashing up); then the race, the logo and
      // the menu all fade in together.
      if (!everShown && !failed) {
        ui.rect(0, 0, ui.W, ui.H, "#0b0710");
        return;
      }
      // Between courses: black (the logo and menu stay up).
      if (!session && !failed) ui.rect(0, 0, ui.W, ui.H, "#0b0710");
      else if (session && !failed) {
        const c = onClip();
        const a = Math.max(1 - c / FADE, (c - (CLIP - FADE)) / FADE, 0);
        if (a > 0) ui.rect(0, 0, ui.W, ui.H, "#0b0710", Math.min(1, a));
      }
      if (failed) landscape(ui.g, ui.W, ui.H, t, calm());
      // The logo's bounce-in starts when it can be seen.
      const lt = failed ? t : shown;
      // A soft band behind the logo so it reads over any scene.
      ui.rect(0, 14, ui.W, 46, "#0b0710", 0.18);
      logo(ui.g, ui.W / 2, 22, lt, 3, calm());
      ui.text("ISLAND KART RACING", ui.W / 2, 50, {
        align: "center",
        color: PAL.cream,
        outline: PAL.shadow,
      });
      if (mode === "press") {
        const on = calm() || Math.floor(lt * 2.2) % 2 === 0;
        if (on && lt > 0.9)
          ui.text("PRESS START", ui.W / 2, 176, {
            align: "center",
            scale: 2,
            color: PAL.gold,
            outline: PAL.shadow,
          });
        if (!game.audio.running && lt > 0.9)
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
      // Fading in from black the first time: the scene and the logo together.
      if (!failed && shown < 0.6) ui.rect(0, 0, ui.W, ui.H, "#0b0710", 1 - shown / 0.6);
    },
  };
}
