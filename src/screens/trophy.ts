/**
 * Trophy Race screens (the cup itself is game/trophy.ts):
 *
 * - TROPHY_STANDINGS, over the finished race: where you came and your time, then the
 *   cup table, everyone's points for this race ticking onto their totals. CONTINUE goes
 *   on to the next track (no retries), or to the podium after the last.
 * - TROPHY_PODIUM: the ceremony. The top three on a stone podium at dawn, confetti, your
 *   trophy (gold, silver or bronze) if you made it, the final table beside it.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import type { RaceResult } from "../game/session";
import {
  cupOver,
  cupStandings,
  nextTrack,
  pointsFor,
  scoreRace,
  yourCupPlace,
} from "../game/trophy";
import { trackById, type TrackEntry } from "../game/tracks";
import { formatTime } from "../race/race";
import type { RacerId } from "../render/racers/designs";
import type { UiLayer } from "../ui/layer";
import { INK, INK_SOFT, trophy, type Metal } from "../ui/mapArt";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { selectBackdrop } from "../ui/selectArt";
import { PAL } from "../ui/textures";
import { hints } from "./common";
import { loadingScreen } from "./loading";
import { titleScreen } from "./title";
import { tracksMenu } from "./tracks";
import { adventureCupDone } from "./adventure";
import { overworldLoading } from "./overworld";

const ordinal = (n: number) =>
  `${n}${["TH", "ST", "ND", "RD"][n % 10 < 4 && Math.floor(n / 10) !== 1 ? n % 10 : 0]}`;

/** An inked paper card with a soft shadow. */
function card(ui: UiLayer, x: number, y: number, w: number, h: number) {
  ui.rect(x + 3, y + 3, w, h, "#00000044");
  ui.rect(x - 1, y - 1, w + 2, h + 2, INK);
  ui.rect(x, y, w, h, "#f4e8cc");
  ui.rect(x, y, w, 1, "#fff8e4");
}

/** A racer's little pixel head, for the tables. */
function head(
  pp: PixelPortraits | undefined,
  ui: UiLayer,
  look: string,
  x: number,
  y: number,
  s = 16,
) {
  if (!pp) return;
  const img = pp.draw(
    look as RacerId,
    { w: 20, h: 20, view: "head", yaw: 0.35, levels: 7 },
    undefined,
    0,
  );
  ui.image(img, x, y, s, s, false);
}

/** After each race of a cup: your result, the points, the table. */
export function trophyStandings(game: Game, result: RaceResult, entry: TrackEntry): Screen {
  const cup = game.trophy!;
  const before = new Map(cup.racers.map((r) => [r.slot, r.points]));
  const won = scoreRace(
    cup,
    result.order.map((o) => ({ slot: o.slot, name: o.name, look: o.racer })),
  );
  const raceNo = cup.raced;
  const last = cupOver(cup);
  let t = 0;
  let pp: PixelPortraits | undefined;
  // A championship toured in the overworld: back to the region between races (you drive
  // to the next one's gateway).
  const tour = game.overworld?.adventure ? game.overworld : undefined;
  const go = () => {
    game.sounds.confirm();
    if (last) return game.screens.go(trophyPodium(game));
    if (tour) return game.screens.go(overworldLoading(game, tour.region, tour.at, true));
    const next = trackById(nextTrack(cup)!);
    if (!next) return game.screens.go(trophyPodium(game));
    game.selection.trackId = next.id;
    game.selection.mode = "race";
    game.screens.go(loadingScreen(game));
  };
  return {
    id: "TROPHY_STANDINGS",
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
      // Keys don't act for a moment, so a held throttle can't skip the table.
      if (t > 0.8 && actions.includes("confirm")) return go();
    },
    draw(ui) {
      ui.dim(0.35);
      const w = 300;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = 8;
      card(ui, x, y, w, 210);
      ui.text(`${cup.worldName.toUpperCase()} TROPHY`, x + w / 2, y + 6, {
        color: "#8a2a1a",
        align: "center",
      });
      ui.text(
        `RACE ${raceNo} OF ${cup.tracks.length} · ${entry.name.toUpperCase()}`,
        x + w / 2,
        y + 16,
        {
          color: INK_SOFT,
          align: "center",
        },
      );
      const pos = result.position ?? 1;
      ui.text(`${ordinal(pos)}!`, x + 14, y + 28, {
        scale: 3,
        color: pos === 1 ? PAL.gold : pos <= 3 ? PAL.leaf : PAL.coral,
        outline: INK,
      });
      ui.text(`TIME ${formatTime(result.totalTime)}`, x + w - 14, y + 30, {
        color: INK,
        align: "right",
      });
      ui.text(`+${pointsFor(pos)} POINTS`, x + w - 14, y + 42, {
        color: "#8a2a1a",
        align: "right",
      });
      // The table: points tick up from before this race to now over a second.
      const k = Math.min(1, Math.max(0, (t - 0.4) / 1));
      const rows = cupStandings(cup);
      const ty = y + 60;
      ui.rect(x + 10, ty - 3, w - 20, 1, "#b08a5a");
      rows.forEach((r, i) => {
        const ry = ty + i * 15;
        const you = r.slot === 0;
        if (you) ui.rect(x + 10, ry - 2, w - 20, 14, "#ffd84a", 0.55);
        ui.text(`${i + 1}`, x + 18, ry + 2, { color: INK, align: "center" });
        head(pp, ui, r.look, x + 28, ry - 2, 14);
        ui.text(r.name.toUpperCase(), x + 48, ry + 2, { color: you ? "#8a2a1a" : INK });
        const gained = won.get(r.slot) ?? 0;
        ui.text(`+${gained}`, x + w - 70, ry + 2, { color: INK_SOFT, align: "right" });
        const shown = Math.round((before.get(r.slot) ?? 0) + gained * k);
        ui.text(`${shown}`, x + w - 18, ry + 2, { scale: 1, color: INK, align: "right" });
      });
      const label = last ? "TO THE PODIUM" : tour ? "ON TO THE NEXT RACE" : "NEXT RACE";
      const r = ui.button(x + w / 2 - 60, y + 186, 120, 18, label, { focused: true });
      if (r.clicked && t > 0.5) go();
      hints(ui, [["ENTER", last ? "PODIUM" : "NEXT RACE"]]);
    },
  };
}

/** The end of a cup: the top three on the podium, your trophy, the final table. */
export function trophyPodium(game: Game): Screen {
  const cup = game.trophy!;
  const final = cupStandings(cup);
  const place = yourCupPlace(cup) ?? 8;
  const metal: Metal | null =
    place === 1 ? "gold" : place === 2 ? "silver" : place === 3 ? "bronze" : null;
  let t = 0;
  let pp: PixelPortraits | undefined;
  const confetti = Array.from({ length: 70 }, (_, i) => ({
    x: Math.sin(i * 91.7) * 0.5 + 0.5,
    v: 20 + ((i * 37) % 30),
    c: ["#ff6a4a", "#ffd84a", "#5ab4ff", "#6ade5a", "#e86ae0"][i % 5]!,
    ph: (i * 0.137) % 1,
  }));
  const leave = (to: () => Screen) => {
    game.sounds.confirm();
    game.trophy = undefined;
    game.screens.go(to());
  };
  const options: [string, () => void][] = game.adventure?.run
    ? [
        ["CONTINUE", () => (game.sounds.confirm(), adventureCupDone(game, place))],
        ["MAIN MENU", () => leave(() => titleScreen(game, true))],
      ]
    : [
        ["TRACKS MENU", () => leave(() => tracksMenu(game))],
        ["MAIN MENU", () => leave(() => titleScreen(game, true))],
      ];
  let focus = 0;
  return {
    id: "TROPHY_PODIUM",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
      void game.audio.music.play("fanfare", {
        fade: 0.2,
        restart: true,
        loop: false,
        onEnd: () => void game.audio.music.play("map", { fade: 1.5 }),
      });
    },
    exit() {
      pp?.dispose();
      pp = undefined;
    },
    frame(dt, actions) {
      t += dt;
      if (t < 1) return;
      for (const a of actions) {
        if (a === "left" || a === "up") focus = 0;
        else if (a === "right" || a === "down") focus = 1;
        else if (a === "confirm") return options[focus]![1]();
      }
    },
    draw(ui) {
      const calm = game.settings.general.reduceMotion;
      selectBackdrop(ui.g, ui.W, ui.H, "dawn", t, calm);
      ui.text(`${cup.worldName.toUpperCase()} TROPHY`, ui.W / 2, 8, {
        scale: 2,
        color: PAL.gold,
        outline: INK,
        align: "center",
      });
      // The podium: 2nd, 1st, 3rd, with the racers on top in their kart.
      const px0 = Math.round(ui.W * 0.32);
      const steps: [number, number, number][] = [
        [1, px0 - 62, 40],
        [0, px0, 56],
        [2, px0 + 62, 28],
      ];
      for (const [i, cx, h] of steps) {
        const r = final[i];
        if (!r) continue;
        const top = 196 - h;
        ui.rect(cx - 28, top, 56, h, "#8a7e6c");
        ui.rect(cx - 28, top, 56, 3, "#b8ad94");
        ui.rect(cx - 28, top, 2, h, "#a89c82");
        ui.text(`${i + 1}`, cx, top + 8, {
          scale: 2,
          color: ["#f2c64a", "#d4dae4", "#d8904a"][i],
          outline: INK,
          align: "center",
        });
        if (pp) {
          const img = pp.draw(
            r.look as RacerId,
            { w: 48, h: 40, view: "kart", yaw: 0.5 + Math.sin(t * 1.2 + i) * 0.25, levels: 8 },
            undefined,
            1 / 60,
            i + 1,
          );
          const hop = calm || i ? 0 : Math.round(Math.abs(Math.sin(t * 4)) * 3);
          ui.image(img, cx - 36, top - 58 - hop, 72, 60, false);
        }
        ui.text(r.name.toUpperCase(), cx, 200, {
          color: r.slot === 0 ? PAL.gold : PAL.cream,
          outline: INK,
          align: "center",
        });
        ui.text(`${r.points} PTS`, cx, 210, { color: PAL.cream, outline: INK, align: "center" });
      }
      // Your trophy, or where you finished.
      const rx = Math.round(ui.W * 0.62);
      const rw = ui.W - rx - 12;
      card(ui, rx, 30, rw, 176);
      if (metal) {
        trophy(ui.g, rx + rw / 2 - 18, 40, 3, Math.sin(t * 3), metal);
        ui.text(`YOU WIN ${metal.toUpperCase()}!`, rx + rw / 2, 92, {
          color: "#8a2a1a",
          align: "center",
        });
      } else
        ui.text(`YOU FINISHED ${ordinal(place)}`, rx + rw / 2, 60, {
          color: "#8a2a1a",
          align: "center",
        });
      final.forEach((r, i) => {
        const ry = 106 + i * 11;
        const you = r.slot === 0;
        if (you) ui.rect(rx + 4, ry - 2, rw - 8, 10, "#ffd84a", 0.55);
        ui.text(`${i + 1} ${r.name.toUpperCase()}`, rx + 8, ry, { color: you ? "#8a2a1a" : INK });
        ui.text(`${r.points}`, rx + rw - 8, ry, { color: INK, align: "right" });
      });
      // Confetti.
      if (!calm)
        for (const c of confetti) {
          const y = ((t * c.v + c.ph * ui.H) % (ui.H + 10)) - 10;
          ui.rect(c.x * ui.W + Math.sin(t * 3 + c.ph * 9) * 4, y, 2, 2, c.c);
        }
      options.forEach(([label, act], i) => {
        const b = ui.button(rx + (i ? rw / 2 + 2 : 4), 212, rw / 2 - 6, 16, label, {
          focused: focus === i,
        });
        if (b.clicked && t > 0.5) act();
      });
      hints(ui, [
        ["◀▶", "CHOOSE"],
        ["ENTER", "SELECT"],
      ]);
    },
  };
}
