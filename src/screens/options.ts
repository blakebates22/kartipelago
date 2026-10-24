/**
 * OPTIONS and its pages: AUDIO_SETTINGS, VIDEO_SETTINGS, CONTROLS and GENERAL_SETTINGS.
 *
 * Every change applies at once and is saved in this browser. Options open over the
 * title screen or over a paused race, and Back returns to whichever it came from.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import type { MenuAction } from "../app/menuInput";
import { DEFAULT_SETTINGS, type Resolution } from "../app/settings";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { musicPlayer } from "./musicPlayer";
import { confirmDialog } from "./race";

export function optionsScreen(game: Game): Screen {
  const menu = new VMenu(
    game,
    [
      { label: "AUDIO", action: () => game.screens.push(audioSettings(game)) },
      { label: "VIDEO", action: () => game.screens.push(videoSettings(game)) },
      { label: "CONTROLS", action: () => game.screens.push(controlsScreen(game)) },
      { label: "GENERAL", action: () => game.screens.push(generalSettings(game)) },
      { label: "BACK", action: () => game.screens.pop() },
    ],
    () => game.screens.pop(),
  );
  return {
    id: "OPTIONS",
    enter() {
      game.ui.interactive = true;
    },
    resume() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.4);
      const w = 140;
      const x = ui.W / 2 - w / 2;
      ui.panel(x, 30, w, 170, "stone", "stone");
      ui.text("OPTIONS", ui.W / 2, 40, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      menu.draw(ui, x + 16, 62, w - 32, 20, 5);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "OPEN"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

/** One row of a settings page. */
type Row =
  | { kind: "slider"; label: string; get: () => number; set: (v: number) => void }
  | {
      kind: "choice";
      label: string;
      options: string[];
      get: () => number;
      set: (i: number) => void;
    }
  | { kind: "button"; label: string; value?: () => string; press: () => void };

/** A page of rows: ▲▼ to move, ◀▶ to change, Enter on buttons. */
function settingsPage(
  game: Game,
  id: Screen["id"],
  title: string,
  rows: Row[],
  footer?: string,
): Screen {
  let focus = 0;
  let clicked: { row: number; dx?: number; value?: number } | undefined;
  const changed = () => {
    game.applySettings();
    game.sounds.tick();
  };
  const adjust = (r: Row, d: number) => {
    if (r.kind === "slider") {
      r.set(Math.round(Math.max(0, Math.min(1, r.get() + d * 0.1)) * 10) / 10);
      changed();
    } else if (r.kind === "choice") {
      r.set((r.get() + d + r.options.length) % r.options.length);
      changed();
    }
  };
  const press = (r: Row) => {
    if (r.kind === "button") {
      game.sounds.confirm();
      r.press();
    } else adjust(r, 1);
  };
  return {
    id,
    enter() {
      game.ui.interactive = true;
    },
    resume() {
      game.ui.interactive = true;
    },
    frame(_dt, actions: MenuAction[]) {
      if (clicked) {
        const c = clicked;
        clicked = undefined;
        const r = rows[c.row]!;
        focus = c.row;
        if (c.value !== undefined && r.kind === "slider") {
          r.set(Math.round(c.value * 20) / 20);
          changed();
        } else if (c.dx) adjust(r, c.dx);
        else press(r);
      }
      for (const a of actions) {
        const r = rows[focus]!;
        if (a === "up" || a === "down") {
          focus = (focus + (a === "up" ? -1 : 1) + rows.length) % rows.length;
          game.sounds.move();
        } else if (a === "left") adjust(r, -1);
        else if (a === "right") adjust(r, 1);
        else if (a === "confirm") press(r);
        else if (a === "back") {
          game.sounds.back();
          game.screens.pop();
          return;
        }
      }
    },
    draw(ui: UiLayer) {
      ui.dim(0.45);
      const w = 280;
      const x = Math.round(ui.W / 2 - w / 2);
      const h = 44 + rows.length * 18 + (footer ? 14 : 0);
      const y = Math.round(Math.max(8, ui.H / 2 - h / 2 - 6));
      ui.panel(x, y, w, h, "stone", "stone");
      ui.text(title, ui.W / 2, y + 10, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      rows.forEach((r, i) => {
        const ry = y + 34 + i * 18;
        const on = i === focus;
        if (on) ui.rect(x + 8, ry - 4, w - 16, 16, "#1d120a", 0.45);
        ui.text(r.label, x + 16, ry, { color: on ? PAL.gold : PAL.cream, outline: PAL.shadow });
        const cx = x + 150;
        const cw = 112;
        if (r.kind === "slider") {
          const v = ui.slider(cx, ry - 1, cw - 28, r.get(), on);
          ui.text(`${Math.round(r.get() * 100)}`, cx + cw, ry, {
            color: PAL.cream,
            outline: PAL.shadow,
            align: "right",
          });
          if (v !== undefined) clicked = { row: i, value: v };
        } else if (r.kind === "choice") {
          const d = ui.arrows(cx, ry, cw, r.options[r.get()]!, on);
          if (d) clicked = { row: i, dx: d };
        } else if (r.value) {
          ui.text(r.value(), cx + cw / 2, ry, {
            color: on ? PAL.gold : PAL.cream,
            outline: PAL.shadow,
            align: "center",
          });
        }
        if (ui.hover(x + 8, ry - 4, w - 16, 16)) {
          if (game.menuInput.pointer.moved && focus !== i) {
            focus = i;
            game.sounds.move();
          }
          if (
            game.menuInput.pointer.clicked &&
            !clicked &&
            (r.kind === "button" || ui.hover(x + 8, ry - 4, 130, 16))
          )
            clicked = { row: i };
        }
      });
      if (footer)
        ui.text(footer, ui.W / 2, y + h - 14, {
          color: "#d6d1c2",
          outline: PAL.shadow,
          align: "center",
        });
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["◀▶", "CHANGE"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

const onOff = ["OFF", "ON"];

export function audioSettings(game: Game): Screen {
  const a = () => game.settings.audio;
  return settingsPage(game, "AUDIO_SETTINGS", "AUDIO", [
    { kind: "slider", label: "MASTER", get: () => a().master, set: (v) => (a().master = v) },
    { kind: "slider", label: "MUSIC", get: () => a().music, set: (v) => (a().music = v) },
    { kind: "slider", label: "SOUND EFFECTS", get: () => a().sfx, set: (v) => (a().sfx = v) },
    { kind: "slider", label: "RACER VOICES", get: () => a().voice, set: (v) => (a().voice = v) },
    {
      kind: "choice",
      label: "PLAY MUSIC",
      options: onOff,
      get: () => (a().musicOn ? 1 : 0),
      set: (i) => (a().musicOn = i === 1),
    },
    {
      kind: "choice",
      label: "OUTPUT",
      options: ["STEREO", "MONO"],
      get: () => (a().mono ? 1 : 0),
      set: (i) => (a().mono = i === 1),
    },
    {
      kind: "button",
      label: "MUSIC PLAYER",
      value: () => "▶",
      press: () => game.screens.push(musicPlayer(game)),
    },
  ]);
}

const RESOLUTIONS: Resolution[] = [240, 360, 480, 0];

export function videoSettings(game: Game): Screen {
  const v = () => game.settings.video;
  return settingsPage(
    game,
    "VIDEO_SETTINGS",
    "VIDEO",
    [
      {
        kind: "choice",
        label: "TEXTURES",
        options: ["SOFT (N64)", "SHARP"],
        get: () => (v().filtering === "soft" ? 0 : 1),
        set: (i) => (v().filtering = i === 0 ? "soft" : "sharp"),
      },
      {
        kind: "choice",
        label: "RESOLUTION",
        options: ["240 LINES", "360 LINES", "480 LINES", "FULL"],
        get: () => Math.max(0, RESOLUTIONS.indexOf(v().resolution)),
        set: (i) => (v().resolution = RESOLUTIONS[i]!),
      },
      {
        kind: "choice",
        label: "SCREEN SHAPE",
        options: ["FILL WINDOW", "4:3"],
        get: () => (v().aspect === "fill" ? 0 : 1),
        set: (i) => (v().aspect = i === 0 ? "fill" : "4:3"),
      },
      {
        kind: "choice",
        label: "SCANLINES",
        options: onOff,
        get: () => (v().scanlines ? 1 : 0),
        set: (i) => (v().scanlines = i === 1),
      },
      {
        kind: "button",
        label: "FULLSCREEN",
        value: () => (document.fullscreenElement ? "ON" : "OFF"),
        press: () => {
          if (document.fullscreenElement) void document.exitFullscreen();
          else void document.documentElement.requestFullscreen?.().catch(() => game.sounds.error());
        },
      },
    ],
    "V IN A RACE SWITCHES SOFT 360 / SHARP FULL",
  );
}

export function generalSettings(game: Game): Screen {
  const g = () => game.settings.general;
  return settingsPage(
    game,
    "GENERAL_SETTINGS",
    "GENERAL",
    [
      {
        kind: "choice",
        label: "REDUCE MOTION",
        options: onOff,
        get: () => (g().reduceMotion ? 1 : 0),
        set: (i) => (g().reduceMotion = i === 1),
      },
      {
        kind: "choice",
        label: "TIME TRIAL GHOST",
        options: ["PERSONAL BEST", "OFF"],
        get: () => (g().ghost === "off" ? 1 : 0),
        set: (i) => {
          g().ghost = i === 1 ? "off" : "best";
          game.session?.setGhost(g().ghost);
        },
      },
      {
        kind: "button",
        label: "RESET SETTINGS",
        value: () => "...",
        press: () =>
          game.screens.push(
            confirmDialog(
              game,
              "PUT EVERY SETTING BACK TO ITS DEFAULT? (YOUR RECORDS ARE KEPT.)",
              () => {
                const last = game.settings.last;
                Object.assign(game.settings, structuredClone(DEFAULT_SETTINGS), { last });
                game.applySettings();
                game.screens.pop();
              },
            ),
          ),
      },
    ],
    "RECORDS AND SETTINGS ARE SAVED IN THIS BROWSER",
  );
}

/** What every control does, on keyboard and on a gamepad. */
export const BINDINGS: [string, string, string][] = [
  ["ACCELERATE", "W / ▲", "A / RT"],
  ["BRAKE, REVERSE", "S / ▼", "X / LT"],
  ["STEER", "A D / ◀ ▶", "STICK / D-PAD"],
  ["DRIFT", "SPACE / SHIFT", "RB / LB"],
  ["USE ITEM (RELEASE)", "E / F", "B / Y"],
  ["PAUSE", "ESC / P", "START"],
  ["MENUS", "ARROWS ENTER ESC", "D-PAD A B"],
];

export function controlsScreen(game: Game): Screen {
  return {
    id: "CONTROLS",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      if (actions.some((a) => a === "back" || a === "confirm") || game.menuInput.pointer.clicked) {
        game.sounds.back();
        game.screens.pop();
      }
    },
    draw(ui) {
      ui.dim(0.45);
      const w = 300;
      const x = Math.round(ui.W / 2 - w / 2);
      ui.panel(x, 22, w, 186, "stone", "stone");
      ui.text("CONTROLS", ui.W / 2, 32, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      const cols = [x + 12, x + 124, x + 214];
      ui.text("", cols[0]!, 54);
      ui.text("KEYBOARD", cols[1]!, 54, { color: PAL.sky, outline: PAL.shadow });
      ui.text("GAMEPAD", cols[2]!, 54, { color: PAL.sky, outline: PAL.shadow });
      BINDINGS.forEach(([what, key, pad], i) => {
        const y = 68 + i * 14;
        ui.text(what, cols[0]!, y, { color: PAL.gold, outline: PAL.shadow });
        ui.text(key, cols[1]!, y, { color: PAL.cream, outline: PAL.shadow });
        ui.text(pad, cols[2]!, y, { color: PAL.cream, outline: PAL.shadow });
      });
      ui.text("KEYS CAN'T BE CHANGED YET.", ui.W / 2, 172, {
        color: "#d6d1c2",
        outline: PAL.shadow,
        align: "center",
      });
      ui.text("ANY GAMEPAD THE BROWSER SEES WORKS.", ui.W / 2, 182, {
        color: "#d6d1c2",
        outline: PAL.shadow,
        align: "center",
      });
      hints(ui, [["ESC", "BACK"]]);
    },
  };
}
