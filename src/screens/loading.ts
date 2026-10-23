/**
 * LOADING: a title card for the race ahead while the track loads and the race is built.
 * The track's picture fills the screen (drifting slowly, in the game's chunky pixels);
 * the world on a wooden plaque, the track's name big, what kind of race it is; a racing
 * tip on a note; and along the bottom a dirt road where your own kart drives toward the
 * finish flag as the load goes. Then straight into the race (and its countdown).
 * LOAD_ERROR: if the track couldn't load, say why and go back to Track Select.
 *
 * The load is tied to the screen manager's token: if you've left by the time it
 * finishes, the half-built race is thrown away.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { tuning } from "../core/tuning";
import { trackById } from "../game/tracks";
import { worldOfTrack } from "../game/worlds";
import type { RacerId } from "../render/racers/designs";
import { wrap } from "../ui/font";
import { island, type IslandStyle } from "../ui/mapArt";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { PAL } from "../ui/textures";
import { raceScreen } from "./race";
import { preview, tracksMenu } from "./tracks";

const TIPS = [
  "HOLD DRIFT INTO A CORNER, THEN STEER TO TIGHTEN OR WIDEN YOUR ARC.",
  "LET GO OF THE THROTTLE AS A ZIPPER FIRES, THEN PRESS IT AGAIN AT THE RAINBOW.",
  "PRESS THE THROTTLE A SPLIT SECOND BEFORE GO, AND HOLD IT, FOR A STRONG START.",
  "DINO EGGS MAKE YOUR KART FASTER. GETTING HIT MAKES YOU DROP SOME.",
  "BALLOON ITEMS FIRE WHEN YOU LET GO OF THE ITEM BUTTON.",
  "PRESS ESC OR START TO PAUSE AT ANY TIME.",
];

const MIN_SHOW = 1.2;
/** Once loaded, the kart runs the rest of the road this fast (seconds). */
const FINISH_SEC = 0.35;

const ISLAND: Record<string, IslandStyle> = {
  prehistoric: "prehistoric",
  frostveil: "frostveil",
  desert: "desert",
  dragon: "dragon",
};

export function loadingScreen(game: Game): Screen {
  let t = 0;
  let ready: Awaited<ReturnType<Game["createSession"]>> | undefined;
  let failed: string | undefined;
  let alive = true;
  const entry = trackById(game.selection.trackId) ?? trackById("drift_loop")!;
  const tip = TIPS[Math.floor(Math.random() * TIPS.length)]!;
  const world = worldOfTrack(entry.id);
  let pp: PixelPortraits | undefined;
  /** How far along the road the kart is (0..1), and when the load finished. */
  let progress = 0;
  let doneAt = -1;

  return {
    id: "LOADING",
    seeThrough: false,
    enter() {
      game.ui.interactive = false;
      pp = createPixelPortraits(game.stage.renderer);
      game.audio.music.stop(0.6);
      game.audio.music.prepare(entry.music);
      game.sounds.preloadAnnouncer();
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
      pp?.dispose();
      pp = undefined;
    },
    frame(dt) {
      t += dt;
      // The kart eases toward 90% while loading, then dashes to the flag.
      if (ready && t >= MIN_SHOW && doneAt < 0) doneAt = t;
      progress =
        doneAt < 0
          ? 0.9 * (1 - Math.exp(-t * 1.1))
          : Math.min(1, progress + (dt / FINISH_SEC) * (1 - progress + 0.05) * 3);
      if (failed !== undefined) {
        const msg = failed;
        failed = undefined;
        return game.screens.go(loadError(game, entry.name, msg));
      }
      if (ready && doneAt >= 0 && t >= doneAt + FINISH_SEC) {
        const s = ready;
        ready = undefined;
        alive = false; // the race owns the session now
        game.screens.go(raceScreen(game, s, entry));
      }
    },
    draw(ui) {
      const { g, W, H } = ui;
      const calm = game.settings.general.reduceMotion;
      // The track's picture, cropped to fill the screen and drifting slowly sideways.
      g.fillStyle = "#1a1210";
      g.fillRect(0, 0, W, H);
      const img = preview(entry.preview);
      if (img) {
        const k = Math.max(W / img.naturalWidth, H / img.naturalHeight) * 1.12;
        const dw = img.naturalWidth * k;
        const dh = img.naturalHeight * k;
        const drift = calm ? 0.5 : 0.5 + Math.sin(t * 0.25) * 0.5;
        ui.image(img, -(dw - W) * drift, -(dh - H) / 2, dw, dh, false);
      }
      // Darker at the top and bottom, where the words are.
      for (let y = 0; y < 70; y++) ui.rect(0, y, W, 1, "#120a06", 0.55 * (1 - y / 70) + 0.1);
      for (let y = 0; y < 90; y++) ui.rect(0, H - 1 - y, W, 1, "#120a06", 0.7 * (1 - y / 90) + 0.1);

      // Top left: the world, on a wooden plaque with its island.
      if (world) {
        const isl = island(ISLAND[world.id] ?? "prehistoric", 9);
        const pw = Math.min(150, 12 + isl.width + ui.textWidth(world.name.toUpperCase()));
        ui.panel(8, 8, pw, 26, "wood", "gold");
        ui.rect(11, 29, pw - 6, 2, world.color);
        ui.image(isl, 11, 21 - isl.height / 2, isl.width, isl.height, false);
        ui.text(world.name.toUpperCase(), 14 + isl.width, 16, {
          color: PAL.cream,
          outline: PAL.shadow,
        });
      }
      // The track's name, big, and what kind of race.
      const name = entry.name.toUpperCase();
      const big = ui.textWidth(name) * 3 < W - 24 ? 3 : 2;
      const slam = calm ? 0 : Math.max(0, 1 - t / 0.25);
      ui.text(name, W / 2, 46 - Math.round(slam * 8), {
        scale: big,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      const mode = game.trophy
        ? `TROPHY RACE · RACE ${game.trophy.raced + 1} OF ${game.trophy.tracks.length}`
        : game.selection.mode === "timeTrial"
          ? `TIME TRIAL · ${tuning.race.laps} LAPS`
          : game.selection.mode === "practice"
            ? "PRACTICE"
            : `RACE · ${tuning.race.laps} LAPS · 8 RACERS`;
      ui.text(mode, W / 2, 48 + big * 9, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });

      // Bottom: a tip on a pinned note.
      const nw = Math.min(300, W - 40);
      const nx = Math.round(W / 2 - nw / 2);
      const lines = wrap(tip, nw - 20);
      const nh = 16 + lines.length * 9;
      const ny = H - 58 - nh;
      ui.rect(nx + 3, ny + 3, nw, nh, "#00000055");
      ui.panel(nx, ny, nw, nh, "parchment", "ink");
      ui.rect(nx + nw / 2 - 2, ny - 2, 4, 4, PAL.coral);
      ui.text("TIP", nx + 8, ny + 6, { color: PAL.coral });
      lines.forEach((l, i) => ui.text(l, nx + 28, ny + 6 + i * 9, { color: PAL.ink }));

      // The road: dirt with a dashed centre line, a chequered flag at the end, your kart
      // driving along it (dust behind) as the race loads.
      const ry = H - 30;
      const rx0 = 20;
      const rx1 = W - 34;
      ui.rect(0, ry - 1, W, 14, "#3a2414");
      ui.rect(0, ry, W, 12, "#8a6a42");
      ui.rect(0, ry, W, 1, "#a8865a");
      const scroll = calm ? 0 : Math.floor(t * 40) % 12;
      for (let x = -scroll; x < W; x += 12) ui.rect(x, ry + 6, 6, 1, "#c8a878");
      const kx = Math.round(rx0 + (rx1 - rx0) * progress);
      ui.rect(rx0, ry + 11, kx - rx0, 1, PAL.gold);
      // The flag.
      const wave = calm ? 0 : t * 6;
      ui.rect(rx1 + 12, ry - 30, 2, 36, "#3a2414");
      ui.rect(rx1 + 12, ry - 32, 2, 2, PAL.gold);
      for (let j = 0; j < 4; j++)
        for (let i = 0; i < 5; i++)
          ui.rect(
            rx1 + 14 + i * 4,
            ry - 30 + j * 4 + Math.round(Math.sin(wave + i * 0.9) * 1.2 * (i / 4)),
            4,
            4,
            (i + j) % 2 ? "#202020" : "#f4f4f4",
          );
      // Dust puffs.
      if (!calm)
        for (let i = 0; i < 4; i++) {
          const a = (t * 3 + i / 4) % 1;
          ui.rect(kx - 18 - a * 16, ry + 2 - a * 4, 3, 3, "#d8c098", 0.7 * (1 - a));
        }
      if (pp) {
        const kart = pp.draw(
          game.selection.racer as RacerId,
          { w: 48, h: 38, view: "kart", yaw: Math.PI / 2, levels: 8 },
          undefined,
          1 / 60,
        );
        const bump = calm ? 0 : Math.round(Math.abs(Math.sin(t * 14)));
        ui.image(kart, kx - 26, ry - 28 - bump, 48, 38, false);
      }
      ui.text(`${Math.round(progress * 100)}%`, W - 6, H - 12, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "right",
      });
    },
  };
}

export function loadError(game: Game, name: string, message: string): Screen {
  let clicked = false;
  const back = () => game.screens.go(tracksMenu(game));
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
