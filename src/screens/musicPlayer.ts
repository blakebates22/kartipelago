/**
 * MUSIC_PLAYER: listen to the soundtrack. Lists every composed piece, and the planned
 * ones as "not composed yet". Play / pause, previous / next, loop, and music volume.
 *
 * It borrows the music channel: whatever was playing before comes back on the way out.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { CATALOG } from "../audio/songs";
import { PAL } from "../ui/textures";
import { hints } from "./common";

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

export function musicPlayer(game: Game): Screen {
  const music = game.audio.music;
  const before = music.playingId;
  let focus = Math.max(
    0,
    CATALOG.findIndex((c) => c.id === before),
  );
  let playing: string | undefined;
  let paused: { id: string; at: number } | undefined;
  let preparing: string | undefined;
  let loop = true;
  let clicked: (() => void) | undefined;
  const rows = CATALOG.length + 2; // songs, LOOP, VOLUME

  const status = () =>
    preparing ? "PREPARING..." : paused ? "PAUSED" : playing ? "PLAYING" : "STOPPED";

  async function playSong(i: number) {
    const c = CATALOG[i]!;
    if (!c.available) return game.sounds.error();
    focus = i;
    paused = undefined;
    preparing = c.id;
    playing = c.id;
    await music.play(c.id, {
      fade: 0.3,
      restart: true,
      loop,
      layers: { tiko: 1, brakka: 1, zephyr: 0.6, pebble: 0.6 },
      onEnd: () => {
        if (playing === c.id && !loop) next(1);
      },
    });
    if (preparing === c.id) preparing = undefined;
  }
  function next(d: number) {
    for (let k = 1; k <= CATALOG.length; k++) {
      const i = (focus + d * k + CATALOG.length * 4) % CATALOG.length;
      if (CATALOG[i]!.available) return void playSong(i);
    }
  }
  function toggle() {
    const c = CATALOG[focus]!;
    if (!c.available) return game.sounds.error();
    if (playing === c.id && !paused) {
      paused = { id: c.id, at: music.position() };
      music.stop(0.1);
    } else if (paused && paused.id === c.id) {
      const p = paused;
      paused = undefined;
      void music.seek(p.id, p.at, loop);
    } else void playSong(focus);
  }

  return {
    id: "MUSIC_PLAYER",
    enter() {
      game.ui.interactive = true;
      if (before) playing = before;
    },
    exit() {
      if (music.playingId !== before || paused) {
        if (before) void music.play(before, { fade: 0.6, restart: true });
        else music.stop();
      }
    },
    frame(_dt, actions) {
      if (clicked) {
        const c = clicked;
        clicked = undefined;
        c();
      }
      for (const a of actions) {
        if (a === "back") {
          game.sounds.back();
          return game.screens.pop();
        }
        if (a === "up" || a === "down") {
          focus = (focus + (a === "up" ? -1 : 1) + rows) % rows;
          game.sounds.move();
        } else if (focus === CATALOG.length) {
          if (a === "confirm" || a === "left" || a === "right") {
            loop = !loop;
            game.sounds.tick();
          }
        } else if (focus === CATALOG.length + 1) {
          if (a === "left" || a === "right") {
            const au = game.settings.audio;
            au.music =
              Math.round(Math.max(0, Math.min(1, au.music + (a === "left" ? -0.1 : 0.1))) * 10) /
              10;
            game.applySettings();
            game.sounds.tick();
          }
        } else if (a === "left") next(-1);
        else if (a === "right") next(1);
        else if (a === "confirm") toggle();
      }
    },
    draw(ui) {
      ui.dim(0.45);
      const w = 288;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = 10;
      ui.panel(x, y, w, 210, "wood", "gold");
      ui.text("♪ MUSIC PLAYER ♪", ui.W / 2, y + 9, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      // Now playing.
      const now = CATALOG.find((c) => c.id === (paused?.id ?? playing));
      ui.panel(x + 10, y + 28, w - 20, 30, "#1d120a", "dark");
      ui.text(now ? now.title.toUpperCase() : "NOTHING PLAYING", x + 18, y + 34, {
        color: PAL.cream,
        outline: PAL.shadow,
      });
      ui.text(status(), x + w - 18, y + 34, {
        color: paused ? PAL.coral : PAL.leaf,
        outline: PAL.shadow,
        align: "right",
      });
      const len = music.length();
      const pos = paused ? paused.at : music.position();
      ui.rect(x + 18, y + 47, w - 80, 3, PAL.shadow);
      if (len > 0) ui.rect(x + 18, y + 47, (w - 80) * Math.min(1, pos / len), 3, PAL.gold);
      ui.text(len > 0 ? `${fmt(pos)}/${fmt(len)}` : "-:--", x + w - 18, y + 45, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "right",
      });
      // The list.
      CATALOG.forEach((c, i) => {
        const ry = y + 64 + i * 11;
        const on = focus === i;
        if (on) ui.rect(x + 10, ry - 2, w - 20, 11, "#1d120a", 0.5);
        const mark = c.id === (paused?.id ?? playing) ? "♪" : " ";
        ui.text(`${mark} ${c.title.toUpperCase()}`, x + 16, ry, {
          color: !c.available ? "#9a8a78" : on ? PAL.gold : PAL.cream,
          outline: PAL.shadow,
        });
        ui.text(c.available ? c.role.toUpperCase() : "NOT COMPOSED YET", x + w - 16, ry, {
          color: c.available ? "#d9c3a0" : "#8a7a68",
          outline: PAL.shadow,
          align: "right",
        });
        if (ui.hover(x + 10, ry - 2, w - 20, 11)) {
          if (game.menuInput.pointer.moved) focus = i;
          if (game.menuInput.pointer.clicked) clicked = () => ((focus = i), toggle());
        }
      });
      // Loop and volume.
      const cy = y + 64 + CATALOG.length * 11 + 4;
      const onLoop = focus === CATALOG.length;
      const onVol = focus === CATALOG.length + 1;
      if (onLoop) ui.rect(x + 10, cy - 2, 120, 11, "#1d120a", 0.5);
      ui.text(`LOOP: ${loop ? "ON" : "OFF"}`, x + 16, cy, {
        color: onLoop ? PAL.gold : PAL.cream,
        outline: PAL.shadow,
      });
      if (ui.hover(x + 10, cy - 2, 120, 11) && game.menuInput.pointer.clicked)
        clicked = () => ((loop = !loop), game.sounds.tick());
      ui.text("VOLUME", x + 140, cy, { color: onVol ? PAL.gold : PAL.cream, outline: PAL.shadow });
      const v = ui.slider(x + 186, cy - 1, 80, game.settings.audio.music, onVol);
      if (v !== undefined)
        clicked = () => {
          game.settings.audio.music = Math.round(v * 20) / 20;
          game.applySettings();
        };
      if (!game.settings.audio.musicOn)
        ui.text("MUSIC IS OFF IN AUDIO OPTIONS", ui.W / 2, y + 196, {
          color: PAL.coral,
          outline: PAL.shadow,
          align: "center",
        });
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "PLAY/PAUSE"],
        ["◀▶", "PREV/NEXT"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
