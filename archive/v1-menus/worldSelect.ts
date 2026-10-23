/**
 * WORLD_SELECT: the worlds as wooden boards over the island, each with a mosaic of its
 * tracks' pictures, its name, a line about it and how many tracks it has. The
 * highlighted board lifts and glows; picking one gives it a little hop and a flash,
 * then the track select opens on that world's courses.
 *
 * ◀ ▶ choose, Enter picks, Esc goes back to the mode select. Mouse: hover to highlight,
 * click to pick, or the Back button.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { VISIBLE_WORLDS as WORLDS, currentWorld, tracksOf, type WorldEntry } from "../game/worlds";
import { landscape } from "../ui/backdrops";
import { wrap } from "../ui/font";
import { ACCENTS, PAL, focusRing } from "../ui/textures";
import { hints, titleSign } from "./common";
import { modeSelect } from "./modeSelect";
import { preview, trackSelect } from "./trackSelect";

/** How long the pick animation plays before the track select opens, s. */
const PICK_SEC = 0.42;

export function worldSelect(game: Game): Screen {
  let focus = Math.max(0, WORLDS.indexOf(currentWorld(game.selection)));
  let t = 0;
  let picked = -1;
  let pickT = 0;
  let clicked: (() => void) | undefined;
  /** Eased card offsets for the lift animation. */
  const lift = WORLDS.map(() => 0);
  for (const w of WORLDS) for (const tr of tracksOf(w)) preview(tr.preview);
  const calm = () => game.settings.general.reduceMotion;

  const moveTo = (i: number) => {
    if (picked >= 0 || i === focus) return;
    focus = (i + WORLDS.length) % WORLDS.length;
    game.sounds.move();
  };
  const pick = (i: number) => {
    if (picked >= 0) return;
    focus = i;
    picked = i;
    pickT = 0;
    game.selection.worldId = WORLDS[i]!.id;
    game.sounds.confirm();
    if (calm()) pickT = PICK_SEC;
  };
  const back = () => {
    if (picked >= 0) return;
    game.sounds.back();
    game.screens.go(modeSelect(game));
  };

  return {
    id: "WORLD_SELECT",
    seeThrough: false,
    enter() {
      void game.audio.music.play("map", { fade: 1 });
    },
    frame(dt, actions) {
      t += dt;
      for (let i = 0; i < lift.length; i++) {
        const goal = i === focus ? 1 : 0;
        lift[i]! += (goal - lift[i]!) * (1 - Math.exp(-14 * dt));
      }
      if (picked >= 0) {
        pickT += dt;
        if (pickT >= PICK_SEC) {
          picked = -2; // only once
          game.screens.go(trackSelect(game));
        }
        return;
      }
      if (picked === -2) return;
      if (clicked) {
        const c = clicked;
        clicked = undefined;
        return c();
      }
      for (const a of actions) {
        if (a === "left" || a === "up") moveTo(focus - 1);
        else if (a === "right" || a === "down") moveTo(focus + 1);
        else if (a === "confirm") return pick(focus);
        else if (a === "back") return back();
      }
    },
    draw(ui) {
      landscape(ui.g, ui.W, ui.H, t, calm());
      titleSign(ui, "CHOOSE A WORLD");
      const n = WORLDS.length;
      // Cards shrink to fit however many worlds there are.
      const gap = n > 2 ? 8 : 14;
      const cw = Math.min(140, Math.floor((ui.W - 16 - (n - 1) * gap) / n));
      const ch = 140;
      const total = n * cw + (n - 1) * gap;
      const x0 = Math.round(ui.W / 2 - total / 2);
      const y0 = 40;
      WORLDS.forEach((w, i) => {
        const sel = i === focus;
        const hop =
          picked === i || picked === -2 ? Math.sin(Math.min(1, pickT / PICK_SEC) * Math.PI) * 8 : 0;
        const bob = calm() || !sel ? 0 : Math.sin(t * 3) * 1.2;
        const x = x0 + i * (cw + gap);
        const y = Math.round(y0 + 6 - lift[i]! * 6 + bob - hop);
        // Posts in the ground, like the mode signs.
        ui.rect(x + 26, y + ch - 4, 6, 60, "#5a3318");
        ui.rect(x + cw - 32, y + ch - 4, 6, 60, "#5a3318");
        drawCard(game, ui, w, x, y, cw, ch, sel, t);
        if (sel) focusRing(ui.g, x, y, cw, ch, t);
        if (picked === i && !calm()) {
          // The flash as it's picked.
          const f = 1 - Math.min(1, pickT / PICK_SEC);
          ui.rect(x, y, cw, ch, "#fffbe0", 0.55 * f);
        }
        if (picked < 0 && ui.hover(x, y, cw, ch)) {
          if (game.menuInput.pointer.moved && focus !== i) moveTo(i);
          if (game.menuInput.pointer.clicked) clicked = () => pick(i);
        }
      });
      // The highlighted world's description, on a parchment strip.
      const w = WORLDS[focus]!;
      const dy = 196;
      ui.panel(ui.W / 2 - 150, dy - 4, 300, 26, "parchment", "ink");
      wrap(w.description.toUpperCase(), 288)
        .slice(0, 2)
        .forEach((line, k) =>
          ui.text(line, ui.W / 2, dy + 2 + k * 9, { color: PAL.ink, align: "center" }),
        );
      const b = ui.button(ui.safeX + 4, 6, 44, 16, "BACK");
      if (b.clicked) clicked = back;
      hints(ui, [
        ["◀▶", "WORLD"],
        ["ENTER", "SELECT"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

function drawCard(
  game: Game,
  ui: Game["ui"],
  w: WorldEntry,
  x: number,
  y: number,
  cw: number,
  ch: number,
  sel: boolean,
  t: number,
) {
  ui.panel(x, y, cw, ch, "wood", sel ? "gold" : "dark");
  // A banner in the world's colour.
  ui.rect(x + 5, y + 5, cw - 10, 22, w.color);
  ui.rect(x + 5, y + 26, cw - 10, 1, PAL.shadow);
  // A long name on a narrow card wraps onto the tagline's line instead.
  const name = wrap(w.name.toUpperCase(), cw - 12);
  if (name.length > 1)
    name.slice(0, 2).forEach((line, k) =>
      ui.text(line, x + cw / 2, y + 8 + k * 9, {
        color: sel ? PAL.cream : "#fff4d6",
        outline: PAL.shadow,
        align: "center",
      }),
    );
  else {
    ui.text(w.name.toUpperCase(), x + cw / 2, y + 9, {
      color: sel ? PAL.cream : "#fff4d6",
      outline: PAL.shadow,
      align: "center",
    });
    ui.text(w.tagline.toUpperCase(), x + cw / 2, y + 18, {
      color: PAL.ink,
      align: "center",
    });
  }
  // The thumbnail: a 2×2 mosaic of the world's track pictures.
  const tracks = tracksOf(w);
  const mx = x + 8;
  const my = y + 32;
  const mw = cw - 16;
  const mh = 74;
  ui.rect(mx - 1, my - 1, mw + 2, mh + 2, PAL.shadow);
  const tw = Math.floor((mw - 2) / 2);
  const th = Math.floor((mh - 2) / 2);
  for (let k = 0; k < 4; k++) {
    const tr = tracks[k];
    const tx = mx + (k % 2) * (tw + 2);
    const ty = my + Math.floor(k / 2) * (th + 2);
    const img = tr && preview(tr.preview);
    if (img) ui.image(img, tx, ty, tw, th);
    else if (k < tracks.length + (w.comingSoon?.length ?? 0)) {
      // A planned track: a dark, locked square.
      ui.rect(tx, ty, tw, th, "#1d2238");
      ui.text("?", tx + tw / 2 - 2, ty + th / 2 - 3, { color: PAL.gold, outline: PAL.shadow });
    } else ui.rect(tx, ty, tw, th, ACCENTS[k % ACCENTS.length]!);
  }
  if (!sel) ui.rect(mx, my, mw, mh, "#1d120a", 0.35);
  // A shine sweeping across the highlighted one.
  if (sel && !game.settings.general.reduceMotion) {
    const sx = mx + (((t * 60) % (mw + 60)) - 30);
    ui.g.save();
    ui.g.beginPath();
    ui.g.rect(mx, my, mw, mh);
    ui.g.clip();
    ui.g.globalAlpha = 0.22;
    ui.g.fillStyle = "#ffffff";
    for (let k = 0; k < mh; k++) ui.g.fillRect(Math.round(sx - k * 0.4), my + k, 6, 1);
    ui.g.restore();
  }
  // Track count and the track names.
  const soon = w.comingSoon?.length ?? 0;
  const count = `${tracks.length} TRACK${tracks.length === 1 ? "" : "S"}${soon ? ` +${soon} SOON` : ""}`;
  ui.text(count, x + cw / 2, my + mh + 6, {
    color: sel ? PAL.gold : PAL.cream,
    outline: PAL.shadow,
    align: "center",
  });
  if (w.testing)
    ui.text("WORK IN PROGRESS", x + cw / 2, my + mh + 17, {
      color: "#e8d5b0",
      align: "center",
      shadow: PAL.shadow,
    });
  else
    ui.text("3 LAPS · 8 RACERS", x + cw / 2, my + mh + 17, {
      color: "#e8d5b0",
      align: "center",
      shadow: PAL.shadow,
    });
  if (sel)
    ui.text("▼", x + cw / 2 - 2, y + ch + 2 + Math.round(Math.sin(t * 6)), {
      color: PAL.gold,
      outline: PAL.shadow,
    });
}
