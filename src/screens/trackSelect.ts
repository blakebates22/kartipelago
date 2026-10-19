/**
 * TRACK_SELECT: a big framed picture of the highlighted track on a parchment map, its
 * name in chunky letters, a row of tiles for every track, the race type, and Start.
 *
 * Rows: tracks (◀ ▶), race type (◀ ▶), and the Start / Back buttons. Up and down move
 * between rows; Enter on the tracks row jumps straight to Start.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { loadRecords } from "../app/records";
import { saveSettings } from "../app/settings";
import { MODE_LABELS, trackById, type TrackEntry } from "../game/tracks";
import { currentWorld, tracksOf } from "../game/worlds";
import { formatTime } from "../race/race";
import { tuning } from "../core/tuning";
import { wrap } from "../ui/font";
import { ACCENTS, PAL } from "../ui/textures";
import { hints, titleSign } from "./common";
import { worldSelect } from "./worldSelect";
import { loadingScreen } from "./loading";

const images = new Map<string, HTMLImageElement>();
/** Track pictures, loaded once and kept (they're small). */
export function preview(src: string): HTMLImageElement | undefined {
  let img = images.get(src);
  if (!img) {
    img = new Image();
    img.src = `${import.meta.env.BASE_URL}${src}`;
    images.set(src, img);
  }
  return img.complete && img.naturalWidth > 0 ? img : undefined;
}

export function trackSelect(game: Game): Screen {
  const world = currentWorld(game.selection);
  game.selection.worldId = world.id;
  const TRACKS = tracksOf(world);
  let index = Math.max(
    0,
    TRACKS.findIndex((t) => t.id === game.settings.last.track),
  );
  let row = 0; // 0 tracks, 1 mode, 2 buttons
  let button = 0; // 0 start, 1 back
  let t = 0;
  /** Slide animation between tracks: -1..1 */
  let slide = 0;
  let clicked: (() => void) | undefined;
  const records = loadRecords();
  for (const tr of TRACKS) preview(tr.preview);

  const track = (): TrackEntry => TRACKS[index]!;
  const modeOf = (tr: TrackEntry) =>
    tr.modes.includes(game.selection.mode) ? game.selection.mode : tr.modes[0]!;
  const moveTrack = (d: number) => {
    index = (index + d + TRACKS.length) % TRACKS.length;
    slide = game.settings.general.reduceMotion ? 0 : d;
    game.audio.music.prepare(track().music); // ready by the time the race starts
    game.sounds.move();
  };
  const cycleMode = (d: number) => {
    const tr = track();
    const modes = tr.modes;
    const i = modes.indexOf(modeOf(tr));
    if (modes.length < 2) return game.sounds.error();
    game.selection.mode = modes[(i + d + modes.length) % modes.length]!;
    game.sounds.move();
  };
  const start = () => {
    const tr = track();
    game.selection.trackId = tr.id;
    game.selection.mode = modeOf(tr);
    game.settings.last.track = tr.id;
    if (game.selection.mode !== "practice") game.settings.last.mode = game.selection.mode;
    saveSettings(game.settings);
    game.sounds.start();
    game.screens.go(loadingScreen(game));
  };
  const back = () => {
    game.sounds.back();
    game.screens.go(worldSelect(game));
  };

  return {
    id: "TRACK_SELECT",
    seeThrough: false,
    enter() {
      void game.audio.music.play("map", { fade: 1 });
      game.audio.music.prepare(track().music);
    },
    frame(dt, actions) {
      t += dt;
      slide *= Math.exp(-12 * dt);
      if (clicked) {
        const c = clicked;
        clicked = undefined;
        return c();
      }
      for (const a of actions) {
        if (a === "back") return back();
        if (a === "up" && row > 0) {
          row = row === 2 && track().modes.length < 2 ? 0 : row - 1;
          game.sounds.move();
        } else if (a === "down" && row < 2) {
          row = row === 0 && track().modes.length < 2 ? 2 : row + 1;
          game.sounds.move();
        } else if (a === "left" || a === "right") {
          const d = a === "left" ? -1 : 1;
          if (row === 0) moveTrack(d);
          else if (row === 1) cycleMode(d);
          else if (button !== (d < 0 ? 0 : 1)) {
            button = d < 0 ? 0 : 1;
            game.sounds.move();
          }
        } else if (a === "confirm") {
          if (row === 2 && button === 1) return back();
          return start();
        }
      }
    },
    draw(ui) {
      // A parchment map, edge to edge.
      ui.panel(-4, -4, ui.W + 8, ui.H + 8, "parchment", "ink");
      ui.g.globalAlpha = 0.18;
      for (let y = 30; y < ui.H; y += 22)
        for (let x = (y / 22) % 2 ? 10 : 0; x < ui.W; x += 20) ui.rect(x, y, 6, 1, PAL.inkSoft);
      ui.g.globalAlpha = 1;
      titleSign(ui, world.name.toUpperCase(), 4);
      const tr = track();
      const sx = ui.safeX;
      // The big picture.
      const pw = 176;
      const ph = 99;
      const px = sx + 8 + Math.round(slide * 24);
      const py = 32;
      ui.panel(px - 4, py - 4, pw + 8, ph + 8, "wood", "gold");
      const img = preview(tr.preview);
      if (img) ui.image(img, px, py, pw, ph);
      else {
        ui.rect(px, py, pw, ph, ACCENTS[index % ACCENTS.length]!);
        ui.text("NO PICTURE YET", px + pw / 2, py + ph / 2 - 3, {
          align: "center",
          color: PAL.cream,
          outline: PAL.shadow,
        });
      }
      if (tr.prototype) {
        ui.rect(px, py + ph - 12, 58, 12, PAL.coral, 0.92);
        ui.text("PROTOTYPE", px + 4, py + ph - 10, { color: PAL.cream, outline: PAL.shadow });
      }
      if (ui.hover(px, py, pw, ph) && game.menuInput.pointer.clicked) clicked = start;
      // Name and details, to the right.
      const ix = px + pw + 12;
      const iw = sx + 312 - ix;
      const rec = records[tr.id];
      const recLines: string[] = [];
      if (rec?.best.race) recLines.push(`BEST RACE ${formatTime(rec.best.race)}`);
      if (rec?.best.timeTrial) recLines.push(`BEST TRIAL ${formatTime(rec.best.timeTrial)}`);
      if (rec?.bestLap) recLines.push(`BEST LAP  ${formatTime(rec.bestLap)}`);
      const recTop = py + 92 - recLines.length * 9;
      recLines.forEach((l, i) => ui.text(l, ix, recTop + i * 9, { color: PAL.inkSoft }));
      // Long names wrap onto a second line; the description fills what's left.
      const nameLines = wrap(tr.name.toUpperCase(), Math.floor(iw / 2)).slice(0, 2);
      nameLines.forEach((line, i) =>
        ui.text(line, ix, py + i * 16, { scale: 2, color: PAL.coral, outline: PAL.ink }),
      );
      const dy = py + 6 + nameLines.length * 16;
      const room = Math.max(1, Math.floor((recTop - 3 - dy) / 9) + 1);
      const desc = wrap(tr.description.toUpperCase(), iw);
      desc.slice(0, room).forEach((line, i) =>
        ui.text(i === room - 1 && desc.length > room ? `${line}...` : line, ix, dy + i * 9, {
          color: PAL.ink,
        }),
      );
      // Tiles for every track.
      const ty = 142;
      const tw = 46;
      const tiles = TRACKS.length;
      const tx0 = Math.round(ui.W / 2 - (tiles * (tw + 4) - 4) / 2);
      TRACKS.forEach((o, i) => {
        const x = tx0 + i * (tw + 4);
        const sel = i === index;
        ui.panel(x, ty, tw, 30, "wood", sel ? "gold" : "dark");
        const im = preview(o.preview);
        if (im) ui.image(im, x + 3, ty + 3, tw - 6, 24);
        else ui.rect(x + 3, ty + 3, tw - 6, 24, ACCENTS[i % ACCENTS.length]!);
        if (sel && row === 0)
          ui.text("▲", x + tw / 2 - 2, ty + 32 + Math.round(Math.sin(t * 6)), {
            color: PAL.coral,
            outline: PAL.ink,
          });
        if (ui.hover(x, ty, tw, 30) && game.menuInput.pointer.clicked) {
          clicked = () => {
            if (i !== index) moveTrack(i - index);
            row = 0;
          };
        }
      });
      // Race type.
      const my = 184;
      const mode = modeOf(tr);
      const label = MODE_LABELS[mode];
      const sub =
        mode === "practice" ? label.sub : label.sub.replace("3 LAPS", `${tuning.race.laps} LAPS`);
      ui.panel(ui.W / 2 - 90, my - 4, 180, 22, "wood", row === 1 ? "gold" : "dark");
      const d = ui.arrows(ui.W / 2 - 82, my + 3, 164, `${label.name} · ${sub}`, row === 1);
      if (d) {
        row = 1;
        cycleMode(d);
      }
      // Buttons.
      const by = 206;
      const s = ui.button(ui.W / 2 - 92, by, 100, 18, "START RACE", {
        focused: row === 2 && button === 0,
      });
      const b = ui.button(ui.W / 2 + 16, by, 76, 18, "BACK", {
        focused: row === 2 && button === 1,
      });
      if (s.hover && game.menuInput.pointer.moved) [row, button] = [2, 0];
      if (b.hover && game.menuInput.pointer.moved) [row, button] = [2, 1];
      if (s.clicked) clicked = start;
      if (b.clicked) clicked = back;
      hints(ui, [
        ["◀▶", "TRACK"],
        ["▲▼", "ROW"],
        ["ENTER", "START"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

export { trackById };
