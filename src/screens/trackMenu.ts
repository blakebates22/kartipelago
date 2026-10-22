/**
 * The Tracks menu, reworked (prototypes): three layouts of the worlds and their tracks
 * on an ancient map, each with Trophy Race first in every world. Picked with
 * ?tracks=a|b|c while we choose; the default is still worldSelect.ts + trackSelect.ts.
 *
 *   a  "Atlas": the whole archipelago as one map, an island per world (your racer's
 *      head marks the one you're on). Enter sails in: that island fills the map, its
 *      tracks are stops on an inked route round it, the trophy sits at its heart, and
 *      a card beside it shows the chosen stop.
 *   b  "Ledger": bookmarks for the worlds along the top; a list (Trophy Race, then the
 *      tracks) on the left; the chosen one's picture and details on the right.
 *   c  "Postcards": one world at a time (▲ ▼ turn the page): its tracks as postcards
 *      pinned to the map, a trophy card first, the chosen one's details below.
 *
 * Picking a track asks how to race it (Race or Time Trial) in a small note, so the
 * screen itself stays clear. Trophy Race is a placeholder here (it's built next).
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { loadRecords } from "../app/records";
import { saveSettings } from "../app/settings";
import { MODE_LABELS, type TrackEntry, type TrackMode } from "../game/tracks";
import {
  VISIBLE_WORLDS as WORLDS,
  currentWorld,
  trackTilesOf,
  type WorldEntry,
} from "../game/worlds";
import { formatTime } from "../race/race";
import { wrap } from "../ui/font";
import type { UiLayer } from "../ui/layer";
import {
  INK,
  INK_SOFT,
  dashedRoute,
  island,
  parchment,
  routeStops,
  trophy,
  type IslandStyle,
} from "../ui/mapArt";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { PAL } from "../ui/textures";
import { hints } from "./common";
import { loadingScreen } from "./loading";
import { modeSelect } from "./modeSelect";
import { preview } from "./trackSelect";

export type TrackMenuVariant = "a" | "b" | "c";

type Entry = { kind: "trophy" } | { kind: "track"; track: TrackEntry };

const STYLE: Record<string, IslandStyle> = {
  prehistoric: "prehistoric",
  frostveil: "frostveil",
  desert: "desert",
  dragon: "dragon",
};
const styleOf = (w: WorldEntry): IslandStyle => STYLE[w.id] ?? "prehistoric";

const entriesOf = (w: WorldEntry): Entry[] => [
  { kind: "trophy" },
  ...trackTilesOf(w).map((track) => ({ kind: "track" as const, track })),
];

export function trackMenu(game: Game, variant: TrackMenuVariant): Screen {
  let wi = Math.max(0, WORLDS.indexOf(currentWorld(game.selection)));
  let ei =
    1 +
    Math.max(
      0,
      trackTilesOf(WORLDS[wi]!).findIndex((t) => t.id === game.settings.last.track),
    );
  /** Atlas only: looking at the whole map, or sailed in to one island. */
  let zoomed = variant !== "a";
  let zoomT = zoomed ? 1 : 0;
  let t = 0;
  /** The "how to race it" note: open, and which line is chosen. */
  let asking: { modes: TrackMode[]; i: number } | null = null;
  let toast: { text: string; until: number } | null = null;
  let clicked: (() => void) | undefined;
  let pp: PixelPortraits | undefined;
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
    if (e.kind === "trophy") {
      game.sounds.confirm();
      toast = { text: `${world().name.toUpperCase()} TROPHY: COMING NEXT!`, until: t + 1.6 };
      return;
    }
    if (e.track.comingSoon) return game.sounds.error();
    const modes = e.track.modes.filter((m) => m !== "practice");
    if (modes.length < 2) return start(modes[0] ?? e.track.modes[0]!);
    game.sounds.confirm();
    asking = { modes, i: Math.max(0, modes.indexOf(game.settings.last.mode)) };
  };
  const start = (mode: TrackMode) => {
    const e = entry();
    if (e.kind !== "track") return;
    game.selection.worldId = world().id;
    game.selection.trackId = e.track.id;
    game.selection.mode = mode;
    game.settings.last.track = e.track.id;
    if (mode !== "practice") game.settings.last.mode = mode;
    saveSettings(game.settings);
    game.sounds.start();
    game.screens.go(loadingScreen(game));
  };
  const back = () => {
    if (asking) {
      asking = null;
      return game.sounds.back();
    }
    if (variant === "a" && zoomed) {
      zoomed = false;
      return game.sounds.back();
    }
    game.sounds.back();
    game.screens.go(modeSelect(game));
  };

  // ---------------------------------------------------------------- shared drawing

  /** An inked title in a cartouche (a scroll with curled ends). */
  function cartouche(ui: UiLayer, text: string, cx: number, y: number, scale = 2) {
    const w = ui.textWidth(text) * scale + 24;
    const x = Math.round(cx - w / 2);
    const h = 7 * scale + 8;
    ui.rect(x - 1, y - 1, w + 2, h + 2, INK);
    ui.rect(x, y, w, h, "#f4e4bc");
    ui.rect(x, y + h - 2, w, 2, "#d8bf8a");
    for (const ex of [x - 6, x + w]) {
      ui.rect(ex, y + 2, 6, h - 4, INK);
      ui.rect(ex + 1, y + 3, 4, h - 6, "#e0c896");
    }
    ui.text(text, cx, y + 4, { scale, color: INK, align: "center" });
  }

  /** An inked note card: paper with a dark line round it and a soft shadow. */
  function note(ui: UiLayer, x: number, y: number, w: number, h: number, fill = "#f4e8cc") {
    ui.rect(x + 2, y + 2, w, h, "#00000033");
    ui.rect(x - 1, y - 1, w + 2, h + 2, INK);
    ui.rect(x, y, w, h, fill);
    ui.rect(x, y, w, 1, "#fff8e4");
  }

  /** A track picture in an inked frame (or a sketch for coming soon / trophy). */
  function picture(ui: UiLayer, e: Entry, x: number, y: number, w: number, h: number) {
    ui.rect(x - 2, y - 2, w + 4, h + 4, INK);
    if (e.kind === "trophy") {
      ui.rect(x, y, w, h, "#3a2a50");
      for (let i = 0; i < 14; i++)
        ui.rect(x + ((i * 37) % w), y + ((i * 23) % h), 1, 1, i % 2 ? "#ffd84a" : "#ffffff");
      const s = Math.max(1, Math.floor(h / 22));
      trophy(ui.g, x + w / 2 - 6 * s, y + h / 2 - 8 * s, s, Math.sin(t * 3));
      return;
    }
    const img = e.track.preview && !e.track.comingSoon ? preview(e.track.preview) : undefined;
    if (img) ui.image(img, x, y, w, h);
    else {
      ui.rect(x, y, w, h, "#d8c49a");
      ui.text("?", x + w / 2, y + h / 2 - 7, { scale: 2, color: INK_SOFT, align: "center" });
    }
  }

  /** A route stop with a readable number: an inked disc, gold when chosen. */
  function bigStop(ui: UiLayer, x: number, y: number, n: number, on: boolean, locked = false) {
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

  function nameOf(e: Entry) {
    return e.kind === "trophy" ? "TROPHY RACE" : e.track.name.toUpperCase();
  }

  /** The words for an entry: its description and best times, or the trophy rules. */
  function details(e: Entry): { body: string; lines: string[] } {
    if (e.kind === "trophy")
      return {
        body: `Race all of ${world().name}'s tracks in a row against the same seven rivals. Most points wins the trophy.`,
        lines: ["4 RACES · 8 RACERS", "POINTS 10 8 6 5 4 3 2 1"],
      };
    if (e.track.comingSoon) return { body: "Still being built. Coming soon!", lines: [] };
    const rec = records[e.track.id];
    const lines: string[] = [];
    if (rec?.best.race) lines.push(`BEST RACE ${formatTime(rec.best.race)}`);
    if (rec?.best.timeTrial) lines.push(`BEST TRIAL ${formatTime(rec.best.timeTrial)}`);
    if (rec?.bestLap) lines.push(`BEST LAP ${formatTime(rec.bestLap)}`);
    if (!lines.length) lines.push("NO RECORD YET");
    return { body: e.track.description, lines };
  }

  function detailText(ui: UiLayer, e: Entry, x: number, y: number, w: number, maxLines = 5) {
    const d = details(e);
    const body = wrap(d.body.toUpperCase(), w).slice(0, maxLines);
    body.forEach((l, i) => ui.text(l, x, y + i * 9, { color: INK }));
    d.lines.forEach((l, i) =>
      ui.text(l, x, y + body.length * 9 + 4 + i * 9, {
        color: i === 0 && e.kind === "trophy" ? "#8a2a1a" : INK_SOFT,
      }),
    );
  }

  /** Your racer's head, a little pixel portrait, bobbing over the map. */
  function racerMarker(ui: UiLayer, x: number, y: number) {
    if (!pp) return;
    const id = game.selection.racer;
    const img = pp.draw(id, { w: 20, h: 20, view: "head", yaw: 0.4, levels: 7 }, undefined, 1 / 60);
    const bob = game.settings.general.reduceMotion ? 0 : Math.round(Math.sin(t * 4) * 1.5);
    ui.rect(x - 1, y + 19 + bob, 22, 2, "#00000044");
    ui.image(img, x, y + bob, 20, 20, false);
  }

  // ---------------------------------------------------------------- a: the atlas

  function atlasSpots(ui: UiLayer): [number, number][] {
    const W = ui.W;
    return [
      [W * 0.27, 88],
      [W * 0.7, 80],
      [W * 0.3, 176],
      [W * 0.73, 170],
    ];
  }

  function drawAtlas(ui: UiLayer) {
    ui.image(parchment(ui.W, ui.H), 0, 0, ui.W, ui.H, false);
    const spots = atlasSpots(ui);
    if (zoomT < 0.5) {
      cartouche(ui, "THE GREAT ARCHIPELAGO", ui.W / 2, 8);
      // Voyages between the islands.
      dashedRoute(ui.g, [spots[0]!, spots[1]!, spots[3]!, spots[2]!, spots[0]!], INK_SOFT);
      WORLDS.forEach((w, i) => {
        const [x, y] = spots[i]!;
        const on = i === wi;
        const r = 38;
        const img = island(styleOf(w), r);
        const lift =
          on && !game.settings.general.reduceMotion ? Math.round(Math.sin(t * 3) * 1) : 0;
        ui.image(img, x - img.width / 2, y - img.height / 2 + lift, img.width, img.height, false);
        // Its name on a scroll below.
        const label = w.name.toUpperCase();
        const lw = ui.textWidth(label) + 10;
        ui.rect(x - lw / 2 - 1, y + 30, lw + 2, 12, INK);
        ui.rect(x - lw / 2, y + 31, lw, 10, on ? "#ffd84a" : "#f4e4bc");
        ui.text(label, x, y + 33, { color: INK, align: "center" });
        if (on) racerMarker(ui, x + 24, y - 32 + lift);
        if (game.menuInput.pointer.clicked && ui.hover(x - r, y - r, r * 2, r * 2 + 14))
          clicked = () => (i === wi ? sail() : setWorld(i));
      });
      const w = world();
      ui.text(
        `${w.tagline.toUpperCase()} · ${trackTilesOf(w).length} TRACKS · TROPHY RACE`,
        ui.W / 2,
        ui.H - 22,
        {
          color: INK,
          align: "center",
        },
      );
      return;
    }
    // Sailed in: this island fills the left of the map.
    const w = world();
    cartouche(ui, w.name.toUpperCase(), ui.W * 0.33, 6);
    const cx = ui.W * 0.33;
    const cy = 128;
    const r = 76;
    // Zoomed in: the same island as on the atlas, at twice the size.
    const img = island(styleOf(w), r / 2);
    ui.image(img, cx - img.width, cy - img.height, img.width * 2, img.height * 2, false);
    const tracks = trackTilesOf(w);
    const stops = routeStops(cx, cy, r * 1.25, tracks.length);
    dashedRoute(ui.g, stops);
    dashedRoute(ui.g, [stops[stops.length - 1]!, stops[0]!]);
    stops.forEach(([x, y], i) => {
      const on = ei === i + 1;
      bigStop(ui, x, y, i + 1, on, tracks[i]!.comingSoon);
      if (on) racerMarker(ui, x - 10, y - 30);
      if (game.menuInput.pointer.clicked && ui.hover(x - 7, y - 7, 14, 14))
        clicked = () => (ei === i + 1 ? choose() : setEntry(i + 1));
    });
    // The trophy at the island's heart.
    const on = ei === 0;
    const tx = cx - 6;
    const ty = cy + 8;
    if (on) {
      ui.rect(tx - 5, ty - 4, 24, 24, "#ffd84a", 0.35 + 0.15 * Math.sin(t * 4));
      racerMarker(ui, tx - 4, ty - 26);
    }
    trophy(ui.g, tx, ty, 1, Math.sin(t * 3));
    if (game.menuInput.pointer.clicked && ui.hover(tx - 4, ty - 4, 20, 22))
      clicked = () => (ei === 0 ? choose() : setEntry(0));
    // The card for the chosen stop.
    const x = Math.round(ui.W * 0.64);
    const cw = ui.W - x - 12;
    note(ui, x, 30, cw, 186);
    const e = entry();
    const ph = Math.round(cw * 0.56);
    picture(ui, e, x + 6, 36, cw - 12, ph);
    ui.text(nameOf(e), x + cw / 2, 42 + ph, { color: "#8a2a1a", align: "center" });
    detailText(ui, e, x + 6, 54 + ph, cw - 12, 6);
  }

  const sail = () => {
    zoomed = true;
    ei = 0;
    game.sounds.confirm();
  };

  // ---------------------------------------------------------------- b: the ledger

  function drawLedger(ui: UiLayer) {
    ui.image(parchment(ui.W, ui.H, { compass: false, ships: false }), 0, 0, ui.W, ui.H, false);
    // The bookmarks: one per world.
    const n = WORLDS.length;
    const tw = Math.floor((ui.W - 24 - (n - 1) * 4) / n);
    WORLDS.forEach((w, i) => {
      const on = i === wi;
      const x = 12 + i * (tw + 4);
      const h = on ? 30 : 24;
      ui.rect(x - 1, 6 - 1, tw + 2, h + 2, INK);
      ui.rect(x, 6, tw, h, on ? w.color : "#cdb07c");
      ui.rect(x, 6, tw, 2, "#ffffff55");
      // A notch at the bottom, like a ribbon.
      ui.rect(x + tw / 2 - 3, 6 + h - 3, 6, 3, on ? "#f0dcae" : "#e9d4a4");
      const img = island(styleOf(w), 9);
      ui.image(img, x + 3, 6 + h / 2 - img.height / 2 - 1, img.width, img.height, false);
      const label = wrap(w.name.toUpperCase(), tw - img.width - 8);
      label.slice(0, 2).forEach((l, j) =>
        ui.text(l, x + img.width + 4, 6 + (label.length > 1 ? 4 : 9) + j * 9, {
          color: on ? PAL.cream : INK,
          outline: on ? INK : undefined,
        }),
      );
      if (game.menuInput.pointer.clicked && ui.hover(x, 6, tw, h)) clicked = () => setWorld(i);
    });
    // The list.
    const lx = 14;
    const ly = 46;
    const lw = Math.round(ui.W * 0.4);
    note(ui, lx, ly, lw, 170);
    entries().forEach((e, i) => {
      const on = i === ei;
      const y = ly + 6 + i * 32;
      if (on) ui.rect(lx + 2, y - 2, lw - 4, 28, "#ffd84a", 0.55);
      if (e.kind === "trophy") trophy(ui.g, lx + 8, y + 5, 1, on ? Math.sin(t * 3) : 0);
      else bigStop(ui, lx + 14, y + 12, i, on, e.track.comingSoon);
      const name = e.kind === "track" && e.track.comingSoon ? "COMING SOON" : nameOf(e);
      ui.text(name, lx + 30, y + 4, { color: on ? "#8a2a1a" : INK });
      const sub =
        e.kind === "trophy"
          ? "4 RACES · MOST POINTS"
          : e.track.comingSoon
            ? ""
            : details(e).lines[0]!;
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
    const ph = Math.round(pw * 0.5);
    picture(ui, e, px, 48, pw, ph);
    ui.text(nameOf(e), px, 56 + ph, { scale: 2, color: "#8a2a1a" });
    detailText(ui, e, px, 74 + ph, pw, 3);
  }

  // ---------------------------------------------------------------- c: postcards

  function drawPostcards(ui: UiLayer) {
    ui.image(parchment(ui.W, ui.H), 0, 0, ui.W, ui.H, false);
    const w = world();
    // The world's island, faint in the background, and its name on a ribbon.
    const img = island(styleOf(w), 90);
    ui.g.globalAlpha = 0.35;
    ui.image(img, ui.W / 2 - img.width / 2, 120 - img.height / 2, img.width, img.height, false);
    ui.g.globalAlpha = 1;
    cartouche(ui, w.name.toUpperCase(), ui.W / 2, 6);
    const bob = game.settings.general.reduceMotion ? 0 : Math.round(Math.sin(t * 5) * 1.5);
    ui.text("▲", ui.W / 2, 30 - bob, { color: INK, align: "center" });
    // The cards.
    const list = entries();
    const n = list.length;
    const cw = Math.min(74, Math.floor((ui.W - 24 - (n - 1) * 8) / n));
    const ch = Math.round(cw * 0.95);
    const x0 = Math.round(ui.W / 2 - (n * cw + (n - 1) * 8) / 2);
    list.forEach((e, i) => {
      const on = i === ei;
      const x = x0 + i * (cw + 8);
      const tilt = [-2, 1, -1, 2, 0][i % 5]!;
      const y = 52 + tilt - (on ? 8 : 0);
      ui.rect(x + 3, y + 3, cw, ch, "#00000033");
      ui.rect(x - 1, y - 1, cw + 2, ch + 2, on ? "#8a2a1a" : INK);
      ui.rect(x, y, cw, ch, "#fbf3dc");
      const ph = Math.round(ch * 0.62);
      picture(ui, e, x + 4, y + 4, cw - 8, ph);
      const label = wrap(
        e.kind === "track" && e.track.comingSoon ? "COMING SOON" : nameOf(e),
        cw - 6,
      );
      label.slice(0, 2).forEach((l, j) =>
        ui.text(l, x + cw / 2, y + ph + 8 + j * 9, {
          color: on ? "#8a2a1a" : INK,
          align: "center",
        }),
      );
      // A red pin.
      ui.rect(x + cw / 2 - 2, y - 4, 4, 4, "#c8322a");
      ui.rect(x + cw / 2 - 1, y - 3, 1, 1, "#ff8a7a");
      if (game.menuInput.pointer.clicked && ui.hover(x, y, cw, ch))
        clicked = () => (i === ei ? choose() : setEntry(i));
    });
    ui.text("▼", ui.W / 2, 52 + ch + 6 + bob, { color: INK, align: "center" });
    // Details of the chosen card along the bottom.
    const e = entry();
    note(ui, 20, 52 + ch + 18, ui.W - 40, 46);
    detailText(ui, e, 28, 52 + ch + 24, ui.W - 56, 3);
  }

  // ---------------------------------------------------------------- the race-type note

  function drawAsking(ui: UiLayer) {
    if (!asking) return;
    ui.dim(0.35);
    const w = 150;
    const h = 34 + asking.modes.length * 16;
    const x = Math.round(ui.W / 2 - w / 2);
    const y = Math.round(ui.H / 2 - h / 2);
    note(ui, x, y, w, h);
    ui.text(nameOf(entry()), x + w / 2, y + 6, { color: "#8a2a1a", align: "center" });
    ui.text("HOW WILL YOU RACE?", x + w / 2, y + 16, { color: INK_SOFT, align: "center" });
    asking.modes.forEach((m, i) => {
      const yy = y + 30 + i * 16;
      const on = i === asking!.i;
      if (on) ui.rect(x + 8, yy - 3, w - 16, 14, "#ffd84a", 0.6);
      ui.text(`${on ? "▶ " : ""}${MODE_LABELS[m].name} · ${MODE_LABELS[m].sub}`, x + w / 2, yy, {
        color: INK,
        align: "center",
      });
      if (game.menuInput.pointer.clicked && ui.hover(x + 8, yy - 3, w - 16, 14))
        clicked = () => start(m);
    });
  }

  return {
    id: "WORLD_SELECT",
    seeThrough: false,
    enter() {
      pp = createPixelPortraits(game.stage.renderer);
      void game.audio.music.play("map", { fade: 1 });
    },
    exit() {
      pp?.dispose();
      pp = undefined;
    },
    frame(dt, actions) {
      t += dt;
      zoomT += ((zoomed ? 1 : 0) - zoomT) * (1 - Math.exp(-14 * dt));
      if (Math.abs(zoomT - (zoomed ? 1 : 0)) < 0.02) zoomT = zoomed ? 1 : 0;
      if (clicked) {
        const c = clicked;
        clicked = undefined;
        return c();
      }
      for (const a of actions) {
        if (a === "back") return back();
        if (asking) {
          if (a === "up" || a === "down") {
            asking.i =
              (asking.i + (a === "up" ? -1 : 1) + asking.modes.length) % asking.modes.length;
            game.sounds.move();
          } else if (a === "confirm") return start(asking.modes[asking.i]!);
          continue;
        }
        if (variant === "a" && !zoomed) {
          // Islands in a 2x2 grid.
          if (a === "left" || a === "right") setWorld(wi % 2 ? wi - 1 : wi + 1);
          else if (a === "up" || a === "down") setWorld((wi + 2) % 4);
          else if (a === "confirm") sail();
          continue;
        }
        if (variant === "b") {
          if (a === "left") setWorld(wi - 1);
          else if (a === "right") setWorld(wi + 1);
          else if (a === "up") setEntry(ei - 1);
          else if (a === "down") setEntry(ei + 1);
          else if (a === "confirm") choose();
          continue;
        }
        if (variant === "c") {
          if (a === "up") setWorld(wi - 1);
          else if (a === "down") setWorld(wi + 1);
          else if (a === "left") setEntry(ei - 1);
          else if (a === "right") setEntry(ei + 1);
          else if (a === "confirm") choose();
          continue;
        }
        // Atlas, sailed in: round the route (the trophy first).
        if (a === "left" || a === "up") setEntry(ei - 1);
        else if (a === "right" || a === "down") setEntry(ei + 1);
        else if (a === "confirm") choose();
      }
    },
    draw(ui) {
      if (variant === "a") drawAtlas(ui);
      else if (variant === "b") drawLedger(ui);
      else drawPostcards(ui);
      drawAsking(ui);
      if (toast && t < toast.until) {
        const w = ui.textWidth(toast.text) + 16;
        note(ui, ui.W / 2 - w / 2, ui.H / 2 - 9, w, 18, "#ffe8a0");
        ui.text(toast.text, ui.W / 2, ui.H / 2 - 4, { color: INK, align: "center" });
      }
      const nav =
        variant === "a" && !zoomed
          ? ([
              ["◀▶▲▼", "ISLAND"],
              ["ENTER", "SAIL IN"],
              ["ESC", "BACK"],
            ] as [string, string][])
          : variant === "b"
            ? ([
                ["◀▶", "WORLD"],
                ["▲▼", "TRACK"],
                ["ENTER", "SELECT"],
                ["ESC", "BACK"],
              ] as [string, string][])
            : variant === "c"
              ? ([
                  ["▲▼", "WORLD"],
                  ["◀▶", "TRACK"],
                  ["ENTER", "SELECT"],
                  ["ESC", "BACK"],
                ] as [string, string][])
              : ([
                  ["◀▶", "STOP"],
                  ["ENTER", "SELECT"],
                  ["ESC", "MAP"],
                ] as [string, string][]);
      hints(ui, nav);
    },
  };
}
