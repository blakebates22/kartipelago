/**
 * TRACK_SELECT, the Tracks menu (the "Ledger"): one screen on an ancient map. Bookmarks
 * for the worlds along the top; on the left a list: the world's tracks, then Trophy
 * Race; on the right the chosen one's picture, name and details.
 *
 * ◀ ▶ change world, ▲ ▼ move down the list, Enter picks. A track asks how to race it
 * (Race or Time Trial) in a small note; Trophy Race starts a cup (game/trophy.ts): all of
 * the world's tracks in a row. Esc goes back to the mode select. Mouse: click a bookmark,
 * a row (again to pick it), or a choice in the note.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { loadRecords } from "../app/records";
import { saveSettings } from "../app/settings";
import { startCup } from "../game/trophy";
import { MODE_LABELS, trackById, type TrackEntry, type TrackMode } from "../game/tracks";
import {
  VISIBLE_WORLDS,
  WORLDS as ALL_WORLDS,
  currentWorld,
  trackTilesOf,
  tracksOf,
  type WorldEntry,
} from "../game/worlds";
import { formatTime } from "../race/race";
import { textWidth, wrap } from "../ui/font";
import type { UiLayer } from "../ui/layer";
import { INK, INK_SOFT, island, parchment, trophy, type IslandStyle } from "../ui/mapArt";
import { PAL } from "../ui/textures";
import { hints } from "./common";
import { loadingScreen } from "./loading";
import { modeSelect } from "./modeSelect";

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

type Entry = { kind: "trophy" } | { kind: "track"; track: TrackEntry };

/** The worlds along the top; dev builds add the Testing tab (prototypes, old versions,
 * ruins, bosses), which players never see. */
const WORLDS: WorldEntry[] = import.meta.env.DEV
  ? [...VISIBLE_WORLDS, ...ALL_WORLDS.filter((w) => w.testing)]
  : VISIBLE_WORLDS;

/** A best time not set yet. */
const NO_TIME = "-:--.--";

const STYLE: Record<string, IslandStyle> = {
  prehistoric: "prehistoric",
  frostveil: "frostveil",
  desert: "desert",
  dragon: "dragon",
  beach: "beach",
};
const styleOf = (w: WorldEntry): IslandStyle => STYLE[w.id] ?? "prehistoric";

const entriesOf = (w: WorldEntry): Entry[] => [
  ...trackTilesOf(w).map((track) => ({ kind: "track" as const, track })),
  ...(w.testing ? [] : [{ kind: "trophy" as const }]),
];

export function tracksMenu(game: Game): Screen {
  // Leaving a cup (or coming back after one) ends it.
  game.trophy = undefined;
  const testingAt = WORLDS.findIndex((w) => w.testing && w.id === game.selection.worldId);
  let wi = testingAt >= 0 ? testingAt : Math.max(0, WORLDS.indexOf(currentWorld(game.selection)));
  let ei = Math.max(
    0,
    trackTilesOf(WORLDS[wi]!).findIndex((t) => t.id === game.settings.last.track),
  );
  let t = 0;
  /** The "how to race it" note: open, and which line is chosen. */
  let asking: { title: string; options: { label: string; run: () => void }[]; i: number } | null =
    null;
  let clicked: (() => void) | undefined;
  const records = loadRecords();
  for (const w of WORLDS) for (const tr of trackTilesOf(w)) if (tr.preview) preview(tr.preview);

  const world = () => WORLDS[wi]!;
  const entries = () => entriesOf(world());
  const entry = () => entries()[ei] ?? entries()[0]!;

  const setWorld = (i: number) => {
    const n = (i + WORLDS.length) % WORLDS.length;
    if (n === wi) return;
    wi = n;
    ei = Math.min(ei, entries().length - 1);
    game.selection.worldId = world().id;
    game.sounds.move();
  };
  const setEntry = (i: number) => {
    const n = (i + entries().length) % entries().length;
    if (n === ei) return;
    ei = n;
    game.sounds.move();
  };
  const choose = () => {
    const e = entry();
    if (e.kind === "trophy") return startTrophy();
    if (e.track.comingSoon) return game.sounds.error();
    const track = e.track;
    const modes = track.modes.filter((m) => m !== "practice");
    if (modes.length < 2) return pickMode(track, modes[0] ?? track.modes[0]!);
    game.sounds.confirm();
    asking = {
      title: "HOW WILL YOU RACE?",
      options: modes.map((m) => ({
        label: `${MODE_LABELS[m].name} · ${MODE_LABELS[m].sub}`,
        run: () => pickMode(track, m),
      })),
      i: Math.max(0, modes.indexOf(game.settings.last.mode)),
    };
  };
  /** Dev builds: a course with a ruined version (the treasure map challenge's, see
   * TrackEntry.ruin) asks which one to drive. */
  const pickMode = (track: TrackEntry, mode: TrackMode) => {
    const ruin = import.meta.env.DEV && track.ruin ? trackById(track.ruin) : undefined;
    if (!ruin) return start(track, mode);
    game.sounds.confirm();
    asking = {
      title: "WHICH VERSION? (DEV)",
      options: [
        { label: "STANDARD · THE FULL LAP", run: () => start(track, mode) },
        { label: "RUINED · TREASURE MAP", run: () => start(ruin, mode, track) },
      ],
      i: 0,
    };
  };
  const go = (track: TrackEntry, mode: TrackMode) => {
    game.selection.worldId = world().id;
    game.selection.trackId = track.id;
    game.selection.mode = mode;
    game.sounds.start();
    game.screens.go(loadingScreen(game));
  };
  /** `listed`: the menu's own entry, when starting another version of it. */
  const start = (track: TrackEntry, mode: TrackMode, listed = track) => {
    asking = null;
    game.settings.last.track = listed.id;
    if (mode !== "practice") game.settings.last.mode = mode;
    saveSettings(game.settings);
    go(track, mode);
  };
  const startTrophy = () => {
    const w = world();
    const tracks = tracksOf(w).filter((tr) => !tr.comingSoon && tr.modes.includes("race"));
    if (!tracks.length) return game.sounds.error();
    game.trophy = startCup(
      w.id,
      w.name,
      tracks.map((tr) => tr.id),
    );
    go(tracks[0]!, "race");
  };
  const back = () => {
    if (asking) {
      asking = null;
      return game.sounds.back();
    }
    game.sounds.back();
    game.screens.go(modeSelect(game));
  };

  // ---------------------------------------------------------------- drawing

  /** An inked note card: paper with a dark line round it and a soft shadow. */
  function note(ui: UiLayer, x: number, y: number, w: number, h: number, fill = "#f4e8cc") {
    ui.rect(x + 2, y + 2, w, h, "#00000033");
    ui.rect(x - 1, y - 1, w + 2, h + 2, INK);
    ui.rect(x, y, w, h, fill);
    ui.rect(x, y, w, 1, "#fff8e4");
  }

  /** A numbered route stop: an inked disc, gold when chosen. */
  function stopMark(ui: UiLayer, x: number, y: number, n: number, on: boolean, locked = false) {
    const r = on ? 7 : 6;
    for (let yy = -r; yy <= r; yy++) {
      const half = Math.round(Math.sqrt(r * r - yy * yy));
      ui.rect(x - half, y + yy, half * 2 + 1, 1, INK);
      if (Math.abs(yy) < r)
        ui.rect(
          x - half + 1,
          y + yy,
          half * 2 - 1,
          1,
          locked ? "#b8a88a" : on ? "#ffd84a" : "#f4e8cc",
        );
    }
    ui.text(String(n), x + 1, y - 3, { color: INK, align: "center" });
  }

  /**
   * Trophy Race's picture: the world's courses side by side behind a podium, gold cup
   * on the top step, silver and bronze either side, confetti falling.
   */
  function trophyPicture(ui: UiLayer, x: number, y: number, w: number, h: number) {
    const tracks = tracksOf(world()).filter((tr) => tr.preview && !tr.comingSoon);
    const n = Math.max(1, tracks.length);
    const sw = w / n;
    ui.rect(x, y, w, h, "#3a2a50");
    tracks.forEach((tr, i) => {
      const img = preview(tr.preview!);
      const x0 = Math.round(x + i * sw);
      const x1 = Math.round(x + (i + 1) * sw);
      // A slice from the middle of each course's picture.
      if (img) {
        const iw = img.naturalWidth;
        const ih = img.naturalHeight;
        const cw = Math.min(iw, (ih * (x1 - x0)) / h);
        ui.g.drawImage(img, (iw - cw) / 2, 0, cw, ih, x0, y, x1 - x0, h);
      }
      if (i > 0) ui.rect(x0, y, 1, h, INK);
    });
    ui.rect(x, y, w, h, "#20142e", 0.45);
    // The podium: 2nd, 1st, 3rd.
    const s = Math.max(1, Math.floor(h / 34));
    const bw = 18 * s;
    const cx = x + w / 2;
    const base = y + h - 3 * s;
    const steps: [number, number, string, string][] = [
      [cx - bw * 1.5, 9 * s, "#c9ced8", "2"],
      [cx - bw * 0.5, 14 * s, "#f2c64a", "1"],
      [cx + bw * 0.5, 6 * s, "#d8904a", "3"],
    ];
    for (const [sx, sh, c, label] of steps) {
      ui.rect(sx - 1, base - sh - 1, bw + 2, sh + 2, INK);
      ui.rect(sx, base - sh, bw, sh, c);
      ui.rect(sx, base - sh, bw, s, "#ffffff", 0.5);
      ui.text(label, sx + bw / 2, base - sh + 2 * s, { color: INK, align: "center" });
    }
    const shine = Math.sin(t * 3);
    trophy(ui.g, cx - 6 * s, base - 14 * s - 16 * s, s, shine, "gold");
    trophy(ui.g, cx - bw - 6 * s, base - 9 * s - 16 * s, s, shine, "silver");
    trophy(ui.g, cx + bw - 6 * s, base - 6 * s - 16 * s, s, shine, "bronze");
    // Confetti.
    const colors = ["#ffd84a", "#ff6b8a", "#6bd6ff", "#9fe870", "#ffffff"];
    for (let i = 0; i < 26; i++) {
      const fx = x + ((i * 53 + 17) % w);
      const fy = y + ((i * 31 + Math.floor(t * 18) * (1 + (i % 3))) % Math.max(1, h - 10));
      ui.rect(fx, fy, s, s * 2, colors[i % colors.length]!);
    }
  }

  /** A track picture in an inked frame (Trophy Race: the podium). */
  function picture(ui: UiLayer, e: Entry, x: number, y: number, w: number, h: number) {
    ui.rect(x - 2, y - 2, w + 4, h + 4, INK);
    if (e.kind === "trophy") {
      trophyPicture(ui, x, y, w, h);
      return;
    }
    const img = e.track.preview && !e.track.comingSoon ? preview(e.track.preview) : undefined;
    if (img) ui.image(img, x, y, w, h);
    else {
      ui.rect(x, y, w, h, "#d8c49a");
      ui.text("?", x + w / 2, y + h / 2 - 7, { scale: 2, color: INK_SOFT, align: "center" });
    }
  }

  const nameOf = (e: Entry) =>
    e.kind === "trophy"
      ? "TROPHY RACE"
      : e.track.comingSoon
        ? "COMING SOON"
        : e.track.name.toUpperCase();

  /** The words for an entry: its description and best times, or the trophy rules. */
  function details(e: Entry): { body: string; lines: string[] } {
    if (e.kind === "trophy") {
      const n = tracksOf(world()).filter((tr) => !tr.comingSoon).length;
      return {
        body: `Race all ${n} of the ${world().name} tracks in a row against the same seven rivals. Most points wins the trophy.`,
        lines: [`${n} RACES · 8 RACERS`, "POINTS 10 8 6 5 4 3 2 1"],
      };
    }
    if (e.track.comingSoon) return { body: "Still being built. Coming soon!", lines: [] };
    const rec = records[e.track.id];
    // Time Trials only (src/app/records.ts): a race against the rivals is never a record.
    const lines = [
      `BEST TRIAL ${rec?.best.timeTrial ? formatTime(rec.best.timeTrial) : NO_TIME}`,
      `BEST LAP ${rec?.bestLap ? formatTime(rec.bestLap) : NO_TIME}`,
    ];
    return { body: e.track.description, lines };
  }

  /**
   * The world picker: one wooden board per world across the top (Blake's pick of the
   * layouts tried). Each board is as wide as its name needs, the spare width shared out.
   * Returns where the track list goes.
   */
  function header(ui: UiLayer): { x: number; y: number; w: number } {
    const n = WORLDS.length;
    const img = (w: WorldEntry) => island(styleOf(w), 9);
    const imgW = (w: WorldEntry) => (w.testing ? 0 : img(w).width);
    const margin = WORLDS.some((w) => w.testing) ? 6 : 12;
    // (Dev builds' Testing tab: a short label, so six boards fit.)
    const title = (w: WorldEntry) => (w.testing ? "DEV" : w.name.toUpperCase());
    const lineW = (w: WorldEntry) => Math.max(...title(w).split(" ").map(textWidth));
    const need = WORLDS.map((w) => imgW(w) + 7 + lineW(w));
    const spare = Math.max(0, ui.W - 2 * margin - (n - 1) * 4 - need.reduce((a, b) => a + b, 0));
    let x = margin;
    WORLDS.forEach((w, i) => {
      const on = i === wi;
      const tw = Math.floor(need[i]! + spare / n);
      const h = on ? 30 : 24;
      // Wooden boards like the other menus' signs: the chosen one in a gold frame with a
      // stripe of its world's colour, the rest darker.
      ui.panel(x, 6, tw, h, "wood", on ? "gold" : "dark");
      ui.rect(x + 3, 6 + h - 5, tw - 6, 2, on ? w.color : "#6a4a2a");
      if (!on) ui.rect(x + 2, 8, tw - 4, h - 4, "#1a1008", 0.25);
      const im = img(w);
      if (!w.testing)
        ui.image(im, x + 3, 6 + h / 2 - im.height / 2 - 1, im.width, im.height, false);
      const label = wrap(title(w), Math.max(lineW(w), tw - imgW(w) - 8));
      label.slice(0, 2).forEach((l, j) =>
        ui.text(l, x + imgW(w) + 4, 6 + (label.length > 1 ? 4 : 9) + j * 9, {
          color: on ? PAL.gold : PAL.cream,
          outline: PAL.shadow,
        }),
      );
      if (game.menuInput.pointer.clicked && ui.hover(x, 6, tw, h)) clicked = () => setWorld(i);
      x += tw + 4;
    });
    return { x: 14, y: 46, w: Math.round(ui.W * 0.4) };
  }

  function draw(ui: UiLayer) {
    ui.image(parchment(ui.W, ui.H, { compass: false, ships: false }), 0, 0, ui.W, ui.H, false);
    const L = header(ui);
    // The list: the tracks, then Trophy Race.
    const lx = L.x;
    const ly = L.y;
    const lw = L.w;
    note(ui, lx, ly, lw, 170);
    // A long list (dev builds' Testing tab): one line each, scrolling with the choice.
    const all = entries();
    const many = all.length > 5;
    const rows = many ? 12 : all.length;
    const first = many ? Math.max(0, Math.min(all.length - rows, ei - Math.floor(rows / 2))) : 0;
    if (many)
      all.slice(first, first + rows).forEach((e, k) => {
        const i = first + k;
        const on = i === ei;
        const y = ly + 5 + k * 13.5;
        if (on) ui.rect(lx + 2, y - 2, lw - 4, 12, "#ffd84a", 0.55);
        ui.text(`${i + 1} ${nameOf(e)}`, lx + 8, y + 1, { color: on ? "#8a2a1a" : INK });
        if (game.menuInput.pointer.clicked && ui.hover(lx, y - 2, lw, 13))
          clicked = () => (i === ei ? choose() : setEntry(i));
      });
    else
      all.forEach((e, i) => {
        const on = i === ei;
        const y = ly + 6 + i * 32;
        if (on) ui.rect(lx + 2, y - 2, lw - 4, 28, "#ffd84a", 0.55);
        if (e.kind === "trophy") trophy(ui.g, lx + 8, y + 5, 1, on ? Math.sin(t * 3) : 0);
        else stopMark(ui, lx + 14, y + 12, i + 1, on, e.track.comingSoon);
        ui.text(nameOf(e), lx + 30, y + 4, { color: on ? "#8a2a1a" : INK });
        const trial = e.kind === "track" ? records[e.track.id]?.best.timeTrial : undefined;
        const sub =
          e.kind === "trophy"
            ? `${tracksOf(world()).filter((tr) => !tr.comingSoon).length} RACES · MOST POINTS`
            : e.track.comingSoon
              ? ""
              : `BEST TRIAL ${trial ? formatTime(trial) : NO_TIME}`;
        ui.text(sub, lx + 30, y + 14, { color: INK_SOFT });
        if (i < entries().length - 1)
          for (let k = lx + 6; k < lx + lw - 6; k += 3) ui.rect(k, y + 29, 1, 1, INK_SOFT);
        if (game.menuInput.pointer.clicked && ui.hover(lx, y - 2, lw, 30))
          clicked = () => (i === ei ? choose() : setEntry(i));
      });
    // The chosen one, large.
    const e = entry();
    const px = lx + lw + 14;
    const pw = ui.W - px - 14;
    const ph = Math.round(pw * 0.44);
    picture(ui, e, px, ly + 2, pw, ph);
    const top = ly - 46;
    ui.text(nameOf(e), px, 56 + top + ph, { scale: 2, color: "#8a2a1a" });
    const d = details(e);
    const body = wrap(d.body.toUpperCase(), pw).slice(0, 3);
    body.forEach((l, i) => ui.text(l, px, 74 + top + ph + i * 9, { color: INK }));
    d.lines.forEach((l, i) =>
      ui.text(l, px, 74 + top + ph + body.length * 9 + 4 + i * 9, {
        color: i === 0 && e.kind === "trophy" ? "#8a2a1a" : INK_SOFT,
      }),
    );
    if (asking) drawAsking(ui);
  }

  function drawAsking(ui: UiLayer) {
    if (!asking) return;
    ui.dim(0.35);
    const w = 150;
    const h = 34 + asking.options.length * 16;
    const x = Math.round(ui.W / 2 - w / 2);
    const y = Math.round(ui.H / 2 - h / 2);
    note(ui, x, y, w, h);
    ui.text(nameOf(entry()), x + w / 2, y + 6, { color: "#8a2a1a", align: "center" });
    ui.text(asking.title, x + w / 2, y + 16, { color: INK_SOFT, align: "center" });
    asking.options.forEach((o, i) => {
      const yy = y + 30 + i * 16;
      const on = i === asking!.i;
      if (on) ui.rect(x + 8, yy - 3, w - 16, 14, "#ffd84a", 0.6);
      ui.text(`${on ? "▶ " : ""}${o.label}`, x + w / 2, yy, { color: INK, align: "center" });
      if (game.menuInput.pointer.clicked && ui.hover(x + 8, yy - 3, w - 16, 14)) clicked = o.run;
    });
  }

  return {
    id: "TRACK_SELECT",
    seeThrough: false,
    enter() {
      void game.audio.music.play("map", { fade: 1 });
    },
    frame(dt, actions) {
      t += dt;
      if (clicked) {
        const c = clicked;
        clicked = undefined;
        return c();
      }
      for (const a of actions) {
        if (a === "back") return back();
        if (asking) {
          if (a === "up" || a === "down") {
            const n = asking.options.length;
            asking.i = (asking.i + (a === "up" ? -1 : 1) + n) % n;
            game.sounds.move();
          } else if (a === "confirm") return asking.options[asking.i]!.run();
          continue;
        }
        if (a === "left") setWorld(wi - 1);
        else if (a === "right") setWorld(wi + 1);
        else if (a === "up") setEntry(ei - 1);
        else if (a === "down") setEntry(ei + 1);
        else if (a === "confirm") choose();
      }
    },
    draw(ui) {
      draw(ui);
      hints(ui, [
        ["◀▶", "WORLD"],
        ["▲▼", "TRACK"],
        ["ENTER", "SELECT"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
