/**
 * RACING, PAUSED, CONFIRM and RESULTS.
 *
 * Racing drives the session (game/session.ts) one fixed step at a time and draws the
 * pixel HUD. Pausing pushes the pause menu on top; while anything is on top, the race
 * isn't stepped, so physics, the race clock, items, bananas and the AI all stop
 * together. (Results are the exception: the race keeps running behind them so the AI
 * can finish and your kart takes its lap of honour.)
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { submitResult, type NewRecords } from "../app/records";
import type { HudState, RaceResult, Session } from "../game/session";
import type { TrackEntry } from "../game/tracks";
import { formatTime } from "../race/race";
import { tuning } from "../core/tuning";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { BALLOON_HUES, ICON, itemIcon } from "../ui/itemIcons";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { VMenu, hints } from "./common";
import { optionsScreen } from "./options";
import { trackSelect } from "./trackSelect";
import { titleScreen } from "./title";

const ordinal = (n: number) =>
  `${n}${["TH", "ST", "ND", "RD"][n % 10 < 4 && Math.floor(n / 10) !== 1 ? n % 10 : 0]}`;

/** Wait this long after crossing the line before the results come up, seconds. */
const RESULTS_AFTER = 2.4;

export function raceScreen(game: Game, session: Session, entry: TrackEntry): Screen {
  let showingResults = false;
  let lastCount = -1;
  let lastLap = 1;
  let banner: { text: string; until: number } | undefined;
  let clock = 0;
  const practice = entry.modes.includes("practice");

  const startMusic = () => void game.audio.music.play(entry.music, { fade: 1.2, restart: true });

  const screen: Screen = {
    id: "RACING",
    enter() {
      game.session = session;
      game.ui.interactive = false;
      startMusic();
    },
    resume() {
      game.ui.interactive = false;
      game.audio.music.duck(false);
    },
    exit() {
      session.dispose();
      if (game.session === session) game.session = undefined;
      game.audio.music.duck(false);
    },
    step(dt, top) {
      if (top || showingResults) session.update(dt);
    },
    frame(dt, actions, top) {
      clock += dt;
      if (!top) return;
      if (actions.some((a) => a === "pause" || a === "back")) {
        game.screens.push(pauseMenu(game, session, entry, restart));
        return;
      }
      const h = session.hud();
      // A knock as GET READY comes up, the GO sound the moment the karts are let go,
      // lap chimes.
      if (h.phase === "countdown") {
        if (lastCount !== 1) game.sounds.count();
        lastCount = 1;
      } else if (lastCount > 0) {
        lastCount = 0;
        game.sounds.go();
      }
      if (h.phase === "racing" && h.lap !== lastLap && !h.finished) {
        // Songs that grow with the race (Celestial Dragon Festival's) bring in their
        // layers: "rise" for the middle laps, "finale" (which carries it) for the last.
        game.audio.music.layer("rise", h.lap >= 2 && h.lap < h.laps ? 1 : 0, 2.5);
        game.audio.music.layer("finale", h.lap >= h.laps ? 1 : 0, 2.5);
        if (h.lap === h.laps) {
          game.sounds.finalLap();
          banner = { text: "FINAL LAP!", until: clock + 1.6 };
        } else {
          game.sounds.lap();
          banner = { text: `LAP ${h.lap}`, until: clock + 1.2 };
        }
      }
      lastLap = h.lap;
      const since = session.finishedFor();
      if (since !== undefined && !showingResults) {
        if (!banner || banner.text !== "FINISH!") {
          banner = { text: "FINISH!", until: clock + RESULTS_AFTER };
          void game.audio.music.play("fanfare", {
            fade: 0.2,
            restart: true,
            loop: false,
            onEnd: () => void game.audio.music.play("map", { fade: 1.5 }),
          });
        }
        if (since > RESULTS_AFTER) {
          const result = session.result()!;
          const mode = entry.modes.includes(game.selection.mode) ? game.selection.mode : "race";
          const rec = submitResult(
            entry.id,
            mode === "timeTrial" ? "timeTrial" : "race",
            result.totalTime,
            result.bestLap,
          );
          showingResults = true;
          game.screens.push(
            resultsScreen(game, result, rec, entry, restart, () => (showingResults = false)),
          );
        }
      }
    },
    render3d(alpha, frameSeconds) {
      session.render(alpha, frameSeconds);
      game.stage.render();
      return true;
    },
    draw(ui) {
      drawHud(
        ui,
        session,
        entry,
        practice,
        banner && clock < banner.until ? banner.text : undefined,
        clock,
      );
    },
  };

  function restart() {
    session.restart();
    showingResults = false;
    lastCount = -1;
    lastLap = 1;
    banner = undefined;
    startMusic();
  }
  return screen;
}

// The pickups are dinosaur eggs (the code calls them bananas).
const EGG = [
  "...####...",
  "..#wwww#..",
  ".#wwwggw#.",
  ".#wggwww#.",
  "#wwwwwgg#.",
  "#wggwwwww#",
  "#wwwwggww#",
  ".#wwwwww#.",
  "..######..",
];
const EGG_COLORS: Record<string, string> = {
  "#": "#3a2a18",
  w: "#f6ecd2",
  g: "#3f9e6e",
};

/** The last item shown in each race's item box, and when it changed (for the pop). */
const shownItem = new WeakMap<Session, { key: string; at: number }>();

/**
 * The item box: a frame in the balloon's colour with its pixel icon at 2x, a pip for each
 * level and the ammo count when there's more than one shot. It's only there while you
 * hold something; a new or upgraded item pops in (a quick grow and a white flash).
 */
function itemBox(
  ui: UiLayer,
  session: Session,
  held: HudState["held"],
  x: number,
  y: number,
  t: number,
) {
  const S = 48;
  const key = held ? `${held.color}${held.level}` : "";
  let seen = shownItem.get(session);
  if (!seen || seen.key !== key) {
    seen = { key, at: held ? t : -1 };
    shownItem.set(session, seen);
  }
  // Nothing held: no box at all (it pops in with the first item).
  if (!held) return;
  const pop = seen.at >= 0 ? Math.max(0, 1 - (t - seen.at) / 0.25) : 0;
  const hue = BALLOON_HUES[held.color];
  ui.rect(x - 2, y - 2, S + 4, S + 4, PAL.shadow);
  ui.rect(x, y, S, S, pop > 0.5 ? "#ffffff" : hue.light);
  ui.rect(x + 2, y + 2, S - 4, S - 4, hue.dark);
  ui.rect(x + 3, y + 3, S - 6, S - 6, "#14121e");
  const size = Math.round(ICON * (2 + pop * 0.8));
  ui.image(
    itemIcon(held.color, held.level),
    x + (S - size) / 2,
    y + (S - size) / 2 - 1,
    size,
    size,
    false,
  );
  // Level pips along the bottom.
  for (let i = 0; i < 3; i++)
    ui.rect(x + 6 + i * 6, y + S - 7, 4, 3, i < held.level ? hue.light : "#3a3a4a");
  if (held.ammo > 1)
    ui.text(`×${held.ammo}`, x + S - 4, y + S - 11, {
      color: PAL.cream,
      outline: PAL.shadow,
      align: "right",
    });
}

/** A dinosaur egg, in pixels. */
function banana(ui: UiLayer, x: number, y: number) {
  EGG.forEach((row, j) => {
    for (let i = 0; i < row.length; i++) {
      const c = EGG_COLORS[row[i]!];
      if (c) ui.rect(x + i, y + j, 1, 1, c);
    }
  });
}

function drawHud(
  ui: UiLayer,
  session: Session,
  entry: TrackEntry,
  practice: boolean,
  banner: string | undefined,
  t: number,
) {
  const h = session.hud();
  const W = ui.W;
  const big = { outline: PAL.shadow };
  // Top left: position (or the mode).
  if (practice && h.park) {
    ui.text("DRIFT PARK", 8, 8, { color: PAL.gold, ...big });
    ui.text(h.park.loop.toUpperCase(), 8, 18, { color: PAL.cream, ...big });
    ui.text(`STREAK ${h.park.streak.toFixed(2)} LAPS`, 8, 30, { color: PAL.cream, ...big });
    ui.text(`BEST ${h.park.best.toFixed(2)}`, 8, 40, { color: PAL.gold, ...big });
    ui.text(`[ ] LOOP · F FLIP (TURNING ${h.park.turning.toUpperCase()})`, 8, 52, {
      color: PAL.cream,
      ...big,
    });
  } else if (h.position !== undefined) {
    const pos = ordinal(h.position);
    const w = ui.text(pos, 8, 6, {
      scale: 3,
      color: h.position === 1 ? PAL.gold : PAL.cream,
      ...big,
    });
    ui.text(`/${h.racers}`, 12 + w, 18, { color: PAL.cream, ...big });
  } else if (!practice) ui.text("TIME TRIAL", 8, 8, { color: PAL.gold, ...big });

  // Top right: lap and times.
  if (h.phase !== "practice") {
    const lap = `LAP ${Math.max(1, h.lap)}/${h.laps}`;
    ui.text(lap, W - 8, 6, { scale: 2, color: PAL.cream, align: "right", ...big });
    ui.text(formatTime(h.totalTime), W - 8, 24, { color: PAL.gold, align: "right", ...big });
    ui.text(`LAP ${formatTime(h.lapTime)}`, W - 8, 34, {
      color: PAL.cream,
      align: "right",
      ...big,
    });
    if (h.bestLap !== undefined)
      ui.text(`BEST ${formatTime(h.bestLap)}`, W - 8, 44, {
        color: "#cfe9a8",
        align: "right",
        ...big,
      });
  }

  // Bottom left: the item box (the held balloon's pixel icon) and the eggs (bananas, in
  // the code) beside it.
  if (!practice || h.bananas > 0) {
    banana(ui, 9, ui.H - 22);
    ui.text(`×${h.bananas}`, 24, ui.H - 21, { scale: 2, color: PAL.gold, ...big });
  }
  itemBox(ui, session, h.held, 8, ui.H - 80, t);

  // Centre: countdown, GO!, banners, toasts.
  if (h.phase === "countdown") {
    // GET READY...: the letters pop in one after another, each in its own colour. Nothing here hints at the moment to press: that's the skill.
    const shown = tuning.race.readySec - h.countdown;
    popWord(ui, "GET READY...", W / 2, 74, shown, 3);
  } else if (h.phase === "racing" && h.sinceGo < tuning.race.goShowSec) {
    // GO!: slams in big, settles, wobbles.
    const k = h.sinceGo;
    const scale = k < 0.06 ? 8 : 7;
    const wob = Math.round(Math.sin(k * 30) * (k < 0.3 ? 2 : 0));
    ui.text("GO!", W / 2 + wob, 62 - (scale - 7) * 3, {
      scale,
      color: Math.floor(k * 12) % 2 ? PAL.gold : PAL.leaf,
      align: "center",
      ...big,
    });
    if (h.startTier === "strong")
      ui.text("STRONG START!", W / 2, 118, {
        scale: 2,
        color: Math.floor(k * 16) % 2 ? PAL.white : PAL.gold,
        align: "center",
        ...big,
      });
    else if (h.startTier === "weak")
      ui.text("GOOD START", W / 2, 118, { color: PAL.cream, align: "center", ...big });
  } else if (banner) {
    const wob = Math.round(Math.sin(t * 10) * 1);
    ui.text(banner, W / 2, 70 + wob, {
      scale: 3,
      color: banner === "FINISH!" ? PAL.gold : PAL.cream,
      align: "center",
      ...big,
    });
  }
  if (h.toast) {
    const w = ui.textWidth(h.toast) + 14;
    ui.panel(W / 2 - w / 2, ui.H - 58, w, 16, "#1d120a", "dark");
    ui.text(h.toast.toUpperCase(), W / 2, ui.H - 53, { align: "center", color: PAL.cream });
  }
  void entry;
}

/**
 * A word whose letters drop in one after another (every 0.05 s), each overshooting to a
 * bigger size before settling, in the accent colours: the countdown's GET READY.
 */
function popWord(ui: UiLayer, word: string, cx: number, y: number, t: number, scale: number) {
  const colors = [PAL.coral, PAL.gold, PAL.leaf, PAL.turquoise, PAL.sky, PAL.violet];
  const total = [...word].reduce((a, ch) => a + ui.textWidth(ch) * scale + scale, -scale);
  let x = cx - total / 2;
  [...word].forEach((ch, i) => {
    const w = ui.textWidth(ch) * scale;
    const k = t - i * 0.05;
    if (ch !== " " && k > 0) {
      const s = k < 0.08 ? scale + 1 : scale;
      const dy = k < 0.08 ? -Math.round((0.08 - k) * 60) : 0;
      ui.text(ch, x + w / 2, y + dy - (s - scale) * 3, {
        scale: s,
        color: colors[i % colors.length]!,
        align: "center",
        outline: PAL.shadow,
      });
    }
    x += w + scale;
  });
}

// ---------------------------------------------------------------- pause

function pauseMenu(game: Game, session: Session, entry: TrackEntry, restart: () => void): Screen {
  const leave = (what: string, go: () => void) => () =>
    game.screens.push(confirmDialog(game, `LEAVE THIS RACE AND GO TO ${what}?`, go));
  const menu: VMenu = new VMenu(
    game,
    [
      { label: "RESUME", action: () => resume() },
      {
        label: entry.modes.includes("practice") ? "RESTART" : "RESTART RACE",
        action: () => {
          restart();
          resume(false);
        },
      },
      { label: "OPTIONS", action: () => game.screens.push(optionsScreen(game)) },
      {
        label: "TRACK SELECT",
        action: leave("TRACK SELECT", () => game.screens.go(trackSelect(game))),
      },
      {
        label: "MAIN MENU",
        action: leave("THE MAIN MENU", () => game.screens.go(titleScreen(game, true))),
      },
    ],
    () => resume(),
  );
  function resume(sound = true) {
    if (sound) game.sounds.unpause();
    game.screens.pop();
  }
  return {
    id: "PAUSED",
    enter() {
      game.ui.interactive = true;
      game.audio.music.duck(true);
      game.sounds.pause();
    },
    resume() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      if (actions.includes("pause")) return resume();
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.45);
      const w = 132;
      const x = ui.W / 2 - w / 2;
      ui.panel(x, 34, w, 170, "wood", "gold");
      ui.text("PAUSED", ui.W / 2, 44, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text(session.trackName.toUpperCase(), ui.W / 2, 62, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      menu.draw(ui, x + 14, 76, w - 28, 18, 6);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "SELECT"],
        ["ESC", "RESUME"],
      ]);
    },
  };
}

/** A yes/no question over whatever's below. */
export function confirmDialog(game: Game, question: string, yes: () => void): Screen {
  const menu = new VMenu(
    game,
    [
      { label: "NO", action: () => game.screens.pop() },
      { label: "YES", action: () => yes() },
    ],
    () => game.screens.pop(),
  );
  let clicked = -1;
  return {
    id: "CONFIRM",
    frame(_dt, actions) {
      if (clicked >= 0) {
        const it = menu.items[clicked]!;
        clicked = -1;
        game.sounds.confirm();
        return it.action();
      }
      // Left/right work too.
      menu.handle(actions.map((a) => (a === "left" ? "up" : a === "right" ? "down" : a)));
    },
    draw(ui) {
      ui.dim(0.35);
      ui.panel(ui.W / 2 - 120, 80, 240, 80, "parchment", "ink");
      const words = question.split(" ");
      const lines: string[] = [];
      for (const w of words) {
        const l = lines.length ? `${lines[lines.length - 1]} ${w}` : w;
        if (lines.length && ui.textWidth(l) <= 220) lines[lines.length - 1] = l;
        else lines.push(w);
      }
      lines.forEach((l, i) =>
        ui.text(l, ui.W / 2, 92 + i * 10, { align: "center", color: PAL.ink }),
      );
      // Two buttons side by side (the menu is a column, so draw them by hand).
      menu.items.forEach((it, i) => {
        const bx = ui.W / 2 - 84 + i * 92;
        const r = ui.button(bx, 132, 76, 18, it.label, { focused: menu.focus === i });
        if (r.hover && game.menuInput.pointer.moved) menu.focus = i;
        if (r.clicked) clicked = i;
      });
    },
  };
}

// ---------------------------------------------------------------- results

function resultsScreen(
  game: Game,
  result: RaceResult,
  rec: NewRecords,
  entry: TrackEntry,
  restart: () => void,
  closed: () => void,
): Screen {
  let t = 0;
  const menu = new VMenu(game, [
    {
      label: "RETRY",
      action: () => {
        closed();
        game.screens.pop();
        restart();
      },
    },
    { label: "TRACK SELECT", action: () => game.screens.go(trackSelect(game)) },
    { label: "MAIN MENU", action: () => game.screens.go(titleScreen(game, true)) },
  ]);
  const solo = result.position === undefined;
  let clicked = -1;
  const best = Math.min(...result.lapTimes);
  let pp: PixelPortraits | undefined;
  return {
    id: "RESULTS",
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
    },
    exit() {
      pp?.dispose();
      pp = undefined;
    },
    frame(dt, actions) {
      t += dt;
      if (clicked >= 0) {
        const it = menu.items[clicked]!;
        clicked = -1;
        game.sounds.confirm();
        return it.action();
      }
      // Keys don't act for a moment, so a held throttle can't skip the results.
      if (t > 0.6)
        menu.handle(actions.map((a) => (a === "left" ? "up" : a === "right" ? "down" : a)));
    },
    draw(ui) {
      ui.dim(0.3);
      const w = 300;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = 14;
      ui.panel(x, y, w, 192, "parchment", "ink");
      // Your racer, celebrating (or not), beside where you came.
      const won = solo || (result.position ?? 9) <= 3;
      if (pp) {
        const img = pp.draw(
          game.selection.racer,
          { w: 48, h: 48, view: "head", yaw: 0.35 + Math.sin(t * 1.6) * 0.2, levels: 8 },
          undefined,
          1 / 60,
          won ? 1 : 6,
        );
        ui.rect(x + 12, y + 10, 52, 52, PAL.ink);
        ui.rect(x + 14, y + 12, 48, 48, won ? "#f6d77a" : "#c9b48a");
        ui.image(img, x + 14, y + 12, 48, 48, false);
      }
      const cx = x + 64 + (w - 64) / 2;
      if (solo)
        ui.text("TIME TRIAL", cx, y + 14, {
          scale: 2,
          color: PAL.coral,
          outline: PAL.ink,
          align: "center",
        });
      else {
        const pop = Math.max(0, 1 - t * 4);
        ui.text(`${ordinal(result.position!)}!`, cx, y + 10 - Math.round(pop * 4), {
          scale: 4,
          color: result.position === 1 ? PAL.gold : result.position! <= 3 ? PAL.leaf : PAL.coral,
          outline: PAL.ink,
          align: "center",
        });
      }
      ui.text(entry.name.toUpperCase(), cx, y + 46, { color: PAL.inkSoft, align: "center" });
      // Your time, big, and the laps underneath.
      ui.rect(x + 12, y + 68, w - 24, 1, "#b08a5a");
      ui.text("TIME", x + w / 2, y + 74, { color: PAL.inkSoft, align: "center" });
      ui.text(formatTime(result.totalTime), x + w / 2, y + 84, {
        scale: 3,
        color: PAL.ink,
        align: "center",
      });
      if (rec.race && t % 0.8 < 0.55)
        ui.text("NEW RECORD!", x + w / 2, y + 108, { color: PAL.coral, align: "center" });
      const laps = result.lapTimes.map(
        (lt, i) => `${i + 1} ${formatTime(lt)}${lt === best ? "★" : ""}`,
      );
      const lapRow = laps.join("   ");
      ui.text(lapRow, x + w / 2, y + 120, { color: PAL.ink, align: "center" });
      const lapLine = rec.lap
        ? "NEW LAP RECORD!"
        : rec.previousLap !== undefined
          ? `BEST LAP ${formatTime(result.bestLap)} · RECORD ${formatTime(rec.previousLap)}`
          : `BEST LAP ${formatTime(result.bestLap)}`;
      ui.text(lapLine, x + w / 2, y + 134, {
        color: rec.lap ? PAL.coral : PAL.inkSoft,
        align: "center",
      });
      ui.rect(x + 12, y + 148, w - 24, 1, "#b08a5a");
      menu.items.forEach((it, i) => {
        const bx = x + 10 + i * 96;
        const r = ui.button(bx, y + 160, 88, 18, it.label, { focused: menu.focus === i });
        if (r.hover && game.menuInput.pointer.moved) menu.focus = i;
        if (r.clicked && t > 0.3) clicked = i;
      });
      hints(ui, [
        ["◀▶", "CHOOSE"],
        ["ENTER", "SELECT"],
      ]);
    },
  };
}
