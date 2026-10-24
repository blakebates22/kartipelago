/**
 * CHARACTER_SELECT ("Select Racer"): a pixel-art roster, like an arcade fighting game.
 * A big turning portrait of the highlighted racer and their kart on the left, with their
 * name and title; a grid of head tiles on the right (and locked slots for racers still to
 * come) with a blinking cursor in the racer's colour; their bio and motto below.
 *
 * Every sprite is the real 3D model rendered small and turned into pixel art each frame
 * (ui/pixelPortraits.ts), so the sprites always match the racers on the track.
 *
 * Left and right cycle the racers (or click a tile; click it again to pick). The
 * highlighted racer hops; picked, they boost and then celebrate, and it's on to the mode
 * select. Looks don't change driving, so there are no stat bars here. The music is "Pick
 * Your Racer": the same piece throughout, with the highlighted racer's instruments faded
 * up (no restart).
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { saveSettings } from "../app/settings";
import { RACER_STEMS } from "../audio/songs";
import { DESIGNS, RACER_IDS, type RacerId } from "../render/racers/designs";
import type { UiLayer } from "../ui/layer";
import { wrap } from "../ui/font";
import { PAL } from "../ui/textures";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { mysteryEgg, selectBackdrop, type SelectBackdrop } from "../ui/selectArt";
import { hints } from "./common";
import { modeSelect } from "./modeSelect";
import { titleScreen } from "./title";

/** Roster slots still to come (the locked tiles). */
const LOCKED = 0;
/** Racers per row of the grid. */
const COLS = 4;

function shade(hex: string, k: number) {
  const n = parseInt(hex.slice(1), 16);
  const f = (v: number) => Math.max(0, Math.min(255, Math.round(v * k)));
  return `rgb(${f((n >> 16) & 255)},${f((n >> 8) & 255)},${f(n & 255)})`;
}

/** A chunky pixel frame: dark outline, a bright edge, a darker inner edge. */
function frame(
  ui: UiLayer,
  x: number,
  y: number,
  w: number,
  h: number,
  color: string,
  fill?: string,
) {
  ui.rect(x - 2, y - 2, w + 4, h + 4, PAL.shadow);
  ui.rect(x, y, w, h, color);
  ui.rect(x + 2, y + 2, w - 4, h - 4, shade(color, 0.55));
  ui.rect(x + 3, y + 3, w - 6, h - 6, fill ?? "#12162e");
}

export function characterSelect(game: Game): Screen {
  // The backdrop: a jungle at dawn (?selectbg=ruins|vista shows the other options).
  const bgParam =
    typeof location !== "undefined" ? new URLSearchParams(location.search).get("selectbg") : null;
  const backdrop: SelectBackdrop = bgParam === "ruins" || bgParam === "vista" ? bgParam : "dawn";
  let index = Math.max(0, RACER_IDS.indexOf(game.settings.last.racer));
  let pp: PixelPortraits | undefined;
  let t = 0;
  let hop = 0;
  let picked = -1;
  let clicked: "left" | "right" | "confirm" | number | undefined;
  const id = () => RACER_IDS[index]!;
  const N = RACER_IDS.length;

  function highlight(d: number) {
    if (picked >= 0 || d === 0) return;
    const before = id();
    index = (index + d + N) % N;
    game.audio.music.layer(before, 0, 0.5);
    game.audio.music.layer(id(), 1, 0.5);
    game.sounds.racer(id());
    hop = 0.3;
  }

  function choose() {
    if (picked >= 0) return;
    picked = 0;
    game.sounds.racerPicked(id());
    game.selection.racer = id();
    game.settings.last.racer = id();
    saveSettings(game.settings);
  }

  /** The pose for a racer this frame: the highlighted one hops, then cheers when picked. */
  const pose = (r: RacerId) => {
    const on = r === id();
    return {
      grounded: !(on && hop > 0 && hop < 0.24),
      steer: Math.sin(t * (on ? 1.4 : 0.6) + r.length) * (on ? 0.3 : 0.12),
      boostPhase: on && picked >= 0 && picked < 0.6 ? 1 : 0,
      boostEnhanced: on && picked >= 0 && picked < 0.6,
      speed: on && picked >= 0 && picked < 0.6 ? 6 : 0,
    };
  };
  const result = (r: RacerId) => (r === id() && picked > 0.6 ? 1 : null);

  // ---------------------------------------------------------------- the backgrounds

  function banner(ui: UiLayer, text: string, y: number, color: string) {
    const w = ui.textWidth(text) * 2 + 20;
    const x = Math.round(ui.W / 2 - w / 2);
    ui.rect(x - 2, y - 2, w + 4, 22, PAL.shadow);
    ui.rect(x, y, w, 18, color);
    ui.rect(x, y + 14, w, 4, shade(color, 0.6));
    ui.text(text, ui.W / 2, y + 3, {
      scale: 2,
      color: PAL.cream,
      outline: PAL.shadow,
      align: "center",
    });
  }

  function bioBox(ui: UiLayer, x: number, y: number, w: number, h: number) {
    const d = DESIGNS[id()];
    frame(ui, x, y, w, h, d.color, "#0e1226");
    const bio = wrap(d.bio, w - 16);
    bio.forEach((l, i) => ui.text(l, x + 8, y + 7 + i * 9, { color: PAL.cream }));
    ui.text(`"${d.quote}"`, x + 8, y + h - 13, { color: PAL.gold });
  }

  // ---------------------------------------------------------------- the roster

  function drawRoster(ui: UiLayer) {
    const d = DESIGNS[id()];
    selectBackdrop(ui.g, ui.W, ui.H, backdrop, t, game.settings.general.reduceMotion);
    banner(ui, "SELECT RACER", 6, "#c8322a");
    // The big portrait, turning.
    const px = 14;
    const py = 34;
    const pw = 150;
    const ph = 132;
    frame(ui, px, py, pw, ph, d.color, shade(d.color, 0.22));
    // A floor ring under the kart.
    ui.rect(px + 20, py + 104, pw - 40, 6, shade(d.color, 0.4));
    const big = pp!.draw(
      id(),
      {
        w: 72,
        h: 60,
        view: "kart",
        yaw: game.settings.general.reduceMotion ? 0.6 + t * 0.15 : t * 0.9,
        levels: 8,
      },
      pose(id()),
      1 / 60,
      result(id()),
    );
    const lift = hop > 0 ? Math.round(Math.sin((hop / 0.3) * Math.PI) * 6) : 0;
    ui.image(big, px + 3, py + 2 - lift, 144, 120, false);
    ui.text(d.name.toUpperCase(), px + pw / 2, py + ph + 8, {
      scale: 2,
      color: d.color,
      outline: PAL.shadow,
      align: "center",
    });
    ui.text(d.title.toUpperCase(), px + pw / 2, py + ph + 26, {
      color: PAL.cream,
      outline: PAL.shadow,
      align: "center",
    });
    // The grid: the racers, then the locked slots.
    const cols = COLS;
    const tile = 46;
    const gap = 8;
    const gx = Math.round(Math.max(px + pw + 18, ui.W - 14 - cols * tile - (cols - 1) * gap));
    const gy = 36;
    const slots = N + LOCKED;
    for (let k = 0; k < slots; k++) {
      const x = gx + (k % cols) * (tile + gap);
      const y = gy + Math.floor(k / cols) * (tile + gap + 10);
      if (k < N) {
        const r = RACER_IDS[k]!;
        const dd = DESIGNS[r];
        const on = k === index;
        frame(
          ui,
          x,
          y,
          tile,
          tile,
          on ? dd.color : "#3a4068",
          on ? shade(dd.color, 0.3) : "#1c2142",
        );
        // 1:1 pixels at 40x40: big enough for the eyes to read.
        const img = pp!.draw(
          r,
          {
            w: 40,
            h: 40,
            view: "head",
            yaw: on ? Math.sin(t * 1.5) * 0.4 : 0.35,
            levels: 8,
            dim: on ? 0 : 0.45,
          },
          pose(r),
          1 / 60,
          result(r),
        );
        ui.image(img, x + 3, y + 3, tile - 6, tile - 6, false);
        ui.text(dd.name.toUpperCase(), x + tile / 2, y + tile + 3, {
          color: on ? dd.color : "#8a90b8",
          outline: PAL.shadow,
          align: "center",
        });
        if (on) {
          // The cursor: a blinking frame and a "1P" tag.
          const blink = Math.floor(t * 4) % 2 === 0;
          const c = blink ? PAL.cream : dd.color;
          ui.rect(x - 4, y - 4, tile + 8, 2, c);
          ui.rect(x - 4, y + tile + 2, tile + 8, 2, c);
          ui.rect(x - 4, y - 4, 2, tile + 8, c);
          ui.rect(x + tile + 2, y - 4, 2, tile + 8, c);
          ui.rect(x - 6, y - 12, 16, 9, PAL.coral);
          ui.text("1P", x + 2, y - 11, { color: PAL.cream, align: "center" });
        }
        if (game.menuInput.pointer.clicked && ui.hover(x, y, tile, tile)) clicked = k;
      } else {
        // Still to hatch: a mystery egg (not one of our racers in shadow).
        frame(ui, x, y, tile, tile, "#2a2e4a", "#151830");
        mysteryEgg(
          ui.g,
          x + tile / 2,
          y + tile / 2 + 1,
          30,
          t,
          k,
          game.settings.general.reduceMotion,
        );
        ui.text("???", x + tile / 2, y + tile + 3, { color: "#4a5078", align: "center" });
      }
    }
    bioBox(ui, gx - 4, gy + 2 * (tile + gap + 10) + 2, ui.W - gx - 10, 56);
  }

  return {
    id: "CHARACTER_SELECT",
    seeThrough: false,
    enter() {
      pp = createPixelPortraits(game.stage.renderer);
      const layers = Object.fromEntries(RACER_STEMS.map((s) => [s, s === id() ? 1 : 0]));
      void game.audio.music.play("select", { fade: 0.8, layers });
      game.audio.music.prepare("map");
    },
    exit() {
      pp?.dispose();
      pp = undefined;
    },
    frame(dt, actions) {
      t += dt;
      hop = Math.max(0, hop - dt);
      const act: (string | number)[] = [...actions];
      if (clicked !== undefined) act.push(clicked);
      clicked = undefined;
      for (const a of act) {
        if (typeof a === "number") {
          if (a === index) choose();
          else highlight(a - index);
        } else if (a === "left") highlight(-1);
        else if (a === "right") highlight(1);
        // Up and down move between the rows of the grid (wrapping top to bottom).
        else if (a === "up" || a === "down") {
          const rows = Math.ceil(N / COLS);
          const row = Math.floor(index / COLS);
          let to = ((row + (a === "down" ? 1 : -1) + rows) % rows) * COLS + (index % COLS);
          if (to >= N) to = N - 1;
          highlight(to - index);
        } else if (a === "confirm") choose();
        else if (a === "back" && picked < 0) {
          game.sounds.back();
          game.screens.go(titleScreen(game, true));
        }
      }
      if (picked >= 0) {
        picked += dt;
        if (picked > 1.4) game.screens.go(modeSelect(game));
      }
    },
    draw(ui) {
      if (!pp) return;
      drawRoster(ui);
      if (picked >= 0)
        ui.text(`${DESIGNS[id()].name.toUpperCase()}!`, ui.W / 2, 100, {
          scale: 3,
          color: PAL.gold,
          outline: PAL.shadow,
          align: "center",
        });
      hints(ui, [
        ["◀▶▲▼", "CHOOSE"],
        ["ENTER", "CONFIRM"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
