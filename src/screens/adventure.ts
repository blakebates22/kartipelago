/**
 * Adventure mode's screens (the story: src/adventure/; the approved story, Blake, Oct 27:
 * claude/kartipelago-story.md). Everything is driven in the overworld (screens/
 * overworld.ts); these are the screens around it:
 *
 * - ADVENTURE_FILES: the three save files. A new one plays the opening (The First Race),
 *   then you pick your racer for it (yours for the whole story); erase one from here.
 * - ADVENTURE_SCENE: a story scene: staged in the 3D world (screens/cutscene.ts), or over
 *   a picture (the opening's storybook); the credits, fake and real.
 * - ADVENTURE_RESULT: after an Adventure race: what it did for the story.
 * - YOUR_CREW: who drives (your racer, and the champions who've joined you).
 * - ADVENTURE_DEV (dev builds only): the testing tools; jump to any point in the story.
 */
import type { Folk } from "../render/villager";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { safeStorage } from "../app/settings";
import {
  END_CREDITS,
  FAKE_CREDITS,
  KINGDOMS,
  OPENING,
  kingdomById,
  nameOf,
  type KingdomId,
} from "../adventure/data";
import {
  bossFinished,
  coursesOf,
  driversOf,
  duelFinished,
  afterScene,
  dueScene,
  eraseAdventure,
  finalFinished,
  kingRaceFinished,
  loadAdventure,
  markSeen,
  newSave,
  objective,
  raceFinished,
  SLOTS,
  saveAdventure,
  shardRaceFinished,
  storyKingdom,
  type AdventureSave,
} from "../adventure/progress";
import type { AdventureRun } from "../adventure/run";
import { CAST, SCENES, beatsFor, sceneById, type Scene } from "../adventure/scenes";
import type { RaceResult } from "../game/session";
import { trackById, type TrackEntry } from "../game/tracks";
import { wrap } from "../ui/font";
import type { UiLayer } from "../ui/layer";
import { INK, INK_SOFT, parchment } from "../ui/mapArt";
import { createPixelPortraits, hasCastModel, type PixelPortraits } from "../ui/pixelPortraits";
import {
  PLATE_H,
  PLATE_RIBBONS,
  PLATE_W,
  createStoryPlates,
  type StoryPlates,
} from "../ui/storyPlates";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { loadingScreen } from "./loading";
import { modeSelect } from "./modeSelect";
import { characterSelect } from "./characterSelect";
import { preview } from "./tracks";
import { devWarp, overworldLoading } from "./overworld";
import { stagedSceneScreen } from "./cutscene";
import { rollingCredits } from "./credits";
import { stagedById } from "../adventure/staged";
import { sceneOrder } from "../adventure/script";
import { regionById, regionOfKingdom } from "../overworld/regions";
import { setAllUnlocked, unlockRacer } from "../app/unlocks";
import { infiniteBoost, instaWin, setInfiniteBoost, setInstaWin } from "../debug/devFlags";
import { clipSwitch } from "../debug/clipRecorder";
import { DESIGNS, type RacerId } from "../render/racers/designs";

const store = () => safeStorage();

/**
 * Dev builds: go anywhere (Blake). Every passage and cave is open whatever the story
 * says, so any part can be tried and retried; results still count. On unless the dev
 * menu turns it off.
 */
const FREE_KEY = "kartipelago.adventure.devFree";
export function freeRoam(): boolean {
  if (!import.meta.env.DEV) return false;
  try {
    return store()?.getItem(FREE_KEY) !== "off";
  } catch {
    return true;
  }
}
function setFreeRoam(on: boolean) {
  try {
    store()?.setItem(FREE_KEY, on ? "on" : "off");
  } catch {
    // (no storage: stays as it was)
  }
}

/** The Adventure state on the game: the open file (file 1 if none was opened yet). */
export function adventureOf(game: Game) {
  if (!game.adventure) game.adventure = { save: loadAdventure(store(), 0) ?? newSave(), slot: 0 };
  return game.adventure;
}
export const persist = (game: Game) => {
  const a = adventureOf(game);
  saveAdventure(a.save, store(), a.slot);
};

/** The file's own racer ("you" in every scene), whoever's driving. */
export const youOf = (game: Game): RacerId => {
  const r = game.adventure?.save.racer;
  return r && r in DESIGNS ? (r as RacerId) : game.selection.racer;
};

/** Open a save file: its story, and who's driving in it. */
export function openFile(game: Game, slot: number) {
  game.adventure = { save: loadAdventure(store(), slot) ?? newSave(), slot };
  const s = game.adventure.save;
  const r = s.driver && driversOf(s).includes(s.driver as RacerId) ? s.driver : s.racer;
  if (r && r in DESIGNS) game.selection.racer = r as RacerId;
  return game.adventure;
}

/** Start the open file with this racer (the character select's pick), then the story. */
export function startFile(game: Game, racer: RacerId) {
  const a = adventureOf(game);
  a.save.racer = racer;
  a.save.driver = racer;
  markSeen(a.save, OPENING);
  persist(game);
  goHome(game);
}

/** Is the file in this kingdom's region (a welcome waits until you've driven there)? */
export const hereIn = (s: AdventureSave) => (id: KingdomId) =>
  regionOfKingdom(id)?.id === s.where?.region;

/** The overworld region the story is in now: where you last were, else the region of
 * the kingdom the story's at. */
export function storyRegion(s: AdventureSave) {
  const w = s.where && regionById(s.where.region) ? s.where : undefined;
  if (w) return { region: w.region, at: w.at };
  const r = regionOfKingdom(storyKingdom(s));
  return r ? { region: r.id } : undefined;
}

/** On with the story: its next scene if one is due, then straight into the overworld
 * region you're progressing through. */
export function goHome(game: Game) {
  const s = adventureOf(game).save;
  const due = dueScene(s, hereIn(s));
  if (due) return game.screens.go(sceneScreen(game, due, () => goHome(game)));
  const at = storyRegion(s);
  if (at) return game.screens.go(overworldLoading(game, at.region, at.at, true));
  game.screens.go(modeSelect(game));
}

/** The file chooser: three files, each its racer and where its story stands. */
export function adventureFiles(game: Game, erasing = false): Screen {
  const files = Array.from({ length: SLOTS }, (_, i) => loadAdventure(store(), i));
  let armed = -1;
  const label = (i: number) => {
    const f = files[i];
    if (!f) return `FILE ${i + 1}: NEW ADVENTURE`;
    const who = f.racer && f.racer in DESIGNS ? DESIGNS[f.racer as RacerId].name : "NO RACER YET";
    return `FILE ${i + 1}: ${who.toUpperCase()}`;
  };
  const sub = (i: number) => {
    const f = files[i];
    if (erasing)
      return f ? (armed === i ? "ENTER AGAIN TO ERASE IT FOR GOOD" : "ERASE THIS FILE") : "EMPTY";
    return f && f.racer ? objective(f) : "START THE STORY";
  };
  const open = (i: number) => {
    if (erasing) {
      if (!files[i]) return game.sounds.error();
      if (armed !== i) {
        armed = i;
        return;
      }
      eraseAdventure(store(), i);
      if (game.adventure?.slot === i) game.adventure = undefined;
      return game.screens.go(adventureFiles(game, false));
    }
    const a = openFile(game, i);
    // A new file: the opening first (Blake, Oct 27: the file, then the opening, then your
    // racer).
    if (!a.save.racer)
      return game.screens.go(
        sceneScreen(
          game,
          OPENING,
          () => game.screens.go(characterSelect(game, { adventure: i })),
          false,
        ),
      );
    goHome(game);
  };
  const back = () =>
    erasing ? game.screens.go(adventureFiles(game, false)) : game.screens.go(modeSelect(game));
  const items = files.map((_, i) => ({ label: label(i), action: () => open(i) }));
  items.push({
    label: erasing ? "DONE ERASING" : "ERASE A FILE",
    action: () => game.screens.go(adventureFiles(game, !erasing)),
  });
  const menu = new VMenu(game, items, back);
  return {
    id: "ADVENTURE_FILES",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      void game.audio.music.play("map", { fade: 1 });
    },
    frame(_dt, actions) {
      const before = menu.focus;
      menu.handle(actions);
      if (menu.focus !== before) armed = -1;
    },
    draw(ui) {
      ui.image(parchment(ui.W, ui.H, { compass: true, ships: false }), 0, 0, ui.W, ui.H, false);
      ui.text(erasing ? "ERASE A FILE" : "ADVENTURE", ui.W / 2, 8, {
        scale: 2,
        color: PAL.coral,
        outline: INK,
        align: "center",
      });
      ui.text(erasing ? "CHOOSE THE FILE TO ERASE" : "CHOOSE A FILE", ui.W / 2, 26, {
        color: INK,
        align: "center",
      });
      const w = Math.min(300, ui.W - 40);
      const x = Math.round(ui.W / 2 - w / 2);
      menu.items.forEach((it, i) => (it.label = i < SLOTS ? label(i) : it.label));
      menu.draw(ui, x, 44, w, 22, 8);
      const note = menu.focus < SLOTS ? sub(menu.focus) : erasing ? "BACK TO THE FILES" : "";
      const lines = wrap(note, w - 10);
      lines.forEach((l, j) =>
        ui.text(l, ui.W / 2, 44 + (SLOTS + 1) * 30 + 6 + j * 9, { color: INK, align: "center" }),
      );
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", erasing ? "ERASE" : "OPEN"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

/** Start a race for the story. */
export function launch(game: Game, run: AdventureRun, track: string) {
  const a = adventureOf(game);
  a.run = run;
  game.trophy = undefined;
  game.selection.trackId = track;
  game.selection.mode = "race";
  game.sounds.start();
  game.screens.go(loadingScreen(game));
}

// ---------------------------------------------------------------- your crew

/** Who drives (Blake, Oct 27: only your own racer and the crew who've joined you; never
 * the other starters): pick one, and you're back where you were, driving them. */
export function crewMenu(game: Game, then: () => void): Screen {
  const a = adventureOf(game);
  const who = driversOf(a.save);
  let pp: PixelPortraits | undefined;
  const pick = (r: RacerId) => {
    a.save.driver = r;
    game.selection.racer = r;
    persist(game);
    game.sounds.confirm();
    then();
  };
  const menu = new VMenu(
    game,
    who.map((r) => ({
      label: `${DESIGNS[r].name.toUpperCase()}${r === game.selection.racer ? "  (DRIVING)" : ""}`,
      action: () => pick(r),
    })),
    () => game.screens.pop(),
  );
  menu.focus = Math.max(0, who.indexOf(game.selection.racer));
  return {
    id: "YOUR_CREW",
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
    },
    exit() {
      pp?.dispose();
      pp = undefined;
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.5);
      const w = 240;
      const h = 70 + who.length * 20;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = Math.round(ui.H / 2 - h / 2);
      ui.panel(x, y, w, h, "wood", "gold");
      ui.text("YOUR CREW", ui.W / 2, y + 8, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text("WHO DRIVES?", ui.W / 2, y + 26, { color: PAL.cream, align: "center" });
      const r = who[menu.focus];
      if (r && pp) {
        const img = pp.draw(
          r,
          { w: 48, h: 48, view: "head", yaw: 0.4, levels: 8 },
          undefined,
          1 / 60,
        );
        ui.image(img, x + 12, y + 40, 48, 48, false);
      }
      menu.draw(ui, x + 70, y + 40, w - 84, 16, 4);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "DRIVE"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

// ---------------------------------------------------------------- scenes

/** Play a story scene, then `then` (it marks the scene seen, sets where it leaves you,
 * and saves first). */
export function sceneScreen(game: Game, id: string, then: () => void, record = true): Screen {
  const a = adventureOf(game);
  const sc: Scene | undefined = sceneById(id);
  const finish = () => {
    // (Watched from the dev menu's list: the story doesn't count it as seen.)
    if (record) {
      markSeen(a.save, id);
      afterScene(a.save, id);
      persist(game);
    }
    then();
  };
  // The credits: the fake ending's (cut short by the King's rage) and the real ones.
  if (id === FAKE_CREDITS || id === END_CREDITS)
    return rollingCredits(game, { fake: id === FAKE_CREDITS, then: finish });
  const you = youOf(game);
  const beats = sc ? beatsFor(sc, you) : [];
  // Staged in the 3D world (src/adventure/staged.ts), where there's a staging for it.
  const staged = stagedById(id);
  if (staged && beats.length)
    return stagedSceneScreen(game, staged, sc?.title ?? id, beats, finish, you);
  let i = 0;
  let t = 0;
  let pp: PixelPortraits | undefined;
  let plates: StoryPlates | undefined;
  return {
    id: "ADVENTURE_SCENE",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
      if (sc?.backdrop.storybook) {
        plates = createStoryPlates(game.stage.renderer);
        void game.audio.music.play("map", { fade: 1 });
      }
      if (!beats.length) finish();
    },
    exit() {
      pp?.dispose();
      pp = undefined;
      plates?.dispose();
      plates = undefined;
    },
    frame(dt, actions) {
      const before = i;
      t += dt;
      for (const act of actions) {
        if (act === "back") {
          game.sounds.back();
          return finish();
        }
        if (act === "confirm") {
          const shown = Math.floor(t * 60);
          const full = (beats[i]?.text.length ?? 0) <= shown;
          if (!full) {
            t = 999;
            continue;
          }
          game.sounds.move();
          // (The last line stays up, whole, until whatever comes next takes over.)
          if (i + 1 >= beats.length) return finish();
          i++;
          t = 0;
        }
      }
      if (game.menuInput.pointer.clicked && t > 0.2) {
        if (i + 1 >= beats.length) return finish();
        i++;
        t = 0;
      }
      if (i !== before && beats[i]?.fx === "horn") game.sounds.gong(3);
    },
    draw(ui) {
      const beat = beats[Math.min(i, beats.length - 1)];
      ui.rect(0, 0, ui.W, ui.H, sc?.backdrop.color ?? "#222");
      if (sc?.backdrop.storybook)
        storybook(ui, plates, Math.min(i, beats.length - 1), t, game.settings.general.reduceMotion);
      const img = sc?.backdrop.track
        ? preview(trackById(sc.backdrop.track)?.preview ?? "")
        : undefined;
      if (img && !sc?.backdrop.storybook) {
        const k = Math.max(ui.W / img.width, ui.H / img.height) * 1.08;
        const drift = game.settings.general.reduceMotion ? 0 : Math.sin(ui.time * 0.2) * 6;
        ui.image(
          img,
          ui.W / 2 - (img.width * k) / 2 + drift,
          ui.H / 2 - (img.height * k) / 2,
          img.width * k,
          img.height * k,
        );
      }
      if ((beat?.fx === "flash" || beat?.fx === "horn") && t < 0.5)
        ui.rect(0, 0, ui.W, ui.H, "#fff2d0", 1 - t * 2);
      if (beat?.fx === "light")
        ui.rect(0, 0, ui.W, ui.H, "#fff8e0", 0.25 + 0.1 * Math.sin(ui.time * 3));
      if (beat?.fx === "dragons" && !sc?.backdrop.storybook) dragonsOver(ui, ui.time);
      ui.rect(0, 0, ui.W, 16, "#000000", 0.55);
      ui.text((sc?.title ?? id).toUpperCase(), ui.W / 2, 4, { color: PAL.gold, align: "center" });
      if (!beat) return;
      const bx = 10;
      const bh = 64;
      const by = ui.H - bh - 18;
      const bw = ui.W - 20;
      ui.panel(bx, by, bw, bh, "parchment", "ink");
      const who = beat.who ? CAST[beat.who] : undefined;
      let tx = bx + 10;
      if (who) {
        const slot = portraitSlot(bx, by, bh);
        portrait(
          ui,
          pp,
          who,
          beat.who === "you" ? you : who.look,
          slot.x,
          slot.y,
          ui.time,
          slot.size,
        );
        tx = slot.tx;
        ui.text((beat.who === "you" ? "YOU" : who.name).toUpperCase(), tx, by + 6, {
          color: "#8a2a1a",
        });
      }
      const shown = beat.text.slice(0, Math.floor(t * 60));
      wrap(shown, bw - (tx - bx) - 10)
        .slice(0, 4)
        .forEach((line, j) => ui.text(line, tx, by + (who ? 18 : 10) + j * 10, { color: INK }));
      ui.text(`${i + 1}/${beats.length}`, bx + bw - 8, by + bh - 10, {
        color: INK_SOFT,
        align: "right",
      });
      hints(ui, [
        ["ENTER", "NEXT"],
        ["ESC", "SKIP"],
      ]);
    },
  };
}

/**
 * The opening's storybook (The First Race): an old page with an inked, washed plate for
 * each line (ui/storyPlates.ts): the war, the oath before the race, its three rules (each
 * under its ribbon), the horn at the last turn, the finish, the dragons going home, the
 * stones.
 */
function storybook(
  ui: UiLayer,
  plates: StoryPlates | undefined,
  page: number,
  t: number,
  still: boolean,
) {
  ui.image(parchment(ui.W, ui.H, { compass: false, ships: false }), 0, 0, ui.W, ui.H, false);
  if (!plates) return;
  const g = ui.g;
  const x = Math.round(ui.W / 2 - PLATE_W / 2);
  const y = 21;
  const img = plates.draw(page, t, still);
  g.save();
  g.globalCompositeOperation = "multiply";
  g.imageSmoothingEnabled = true;
  g.drawImage(img, x, y, PLATE_W, PLATE_H);
  g.restore();
  const ribbon = PLATE_RIBBONS[page];
  if (ribbon) {
    // A red ribbon with forked ends over the plate's top edge.
    const tw = ui.textWidth(ribbon) + 20;
    const rx = Math.round(ui.W / 2 - tw / 2);
    const ry = y - 3;
    g.fillStyle = "#6a1a12";
    for (const [sx, dir] of [
      [rx - 10, 1],
      [rx + tw + 10, -1],
    ] as const) {
      g.beginPath();
      g.moveTo(sx, ry + 2);
      g.lineTo(sx + dir * 14, ry + 2);
      g.lineTo(sx + dir * 14, ry + 13);
      g.lineTo(sx, ry + 13);
      g.lineTo(sx + dir * 5, ry + 7.5);
      g.closePath();
      g.fill();
    }
    ui.rect(rx, ry, tw, 12, "#9a2a1c");
    ui.rect(rx, ry, tw, 1, "#c84a30");
    ui.rect(rx, ry + 11, tw, 1, "#5a140c");
    ui.text(ribbon, ui.W / 2, ry + 3, { color: "#f4e4c0", align: "center" });
  }
}

/** A speaker's portrait: a racer's own face, or a drawn head (the Elder, Lumen in his
 * hood, a sketchy guard, a crowd, a dragon). */
/** Speakers' portraits sit inside the text box (Blake, Oct 28), a little smaller; false
 * puts them back, bigger, standing up out of its top-left corner. */
export const PORTRAIT_IN_BOX = true;

/** Where a speaker's portrait goes for a text box at (bx, by), bh high, and where the
 * text starts after it. */
export function portraitSlot(bx: number, by: number, bh: number) {
  if (!PORTRAIT_IN_BOX) return { x: bx + 6, y: by - 22, size: 48, tx: bx + 64 };
  const size = Math.min(48, bh - 10);
  return { x: bx + 5, y: by + 5, size, tx: bx + size + 14 };
}

export function portrait(
  ui: UiLayer,
  pp: PixelPortraits | undefined,
  who: { color: string; shape?: string; name?: string },
  look: string | undefined,
  x: number,
  y: number,
  t: number,
  size = 48,
  guard?: { folk: Folk; seed: number },
) {
  ui.rect(x - 2, y - 2, size + 4, size + 4, INK);
  ui.rect(x, y, size, size, who.color);
  if (look && pp) {
    const img = pp.draw(
      look as never,
      {
        w: size,
        h: size,
        view: "head",
        yaw: 0.35 + Math.sin(t * 1.4) * 0.15,
        levels: 8,
        // (A champion's cousin: the alternate paint.)
        alt: who.name?.endsWith("'s Cousin") ?? false,
      },
      undefined,
      1 / 60,
    );
    ui.image(img, x, y, size, size, false);
    return;
  }
  // The rest of the cast: their own models too (Mossback, Lumen, the guards, the dragons).
  const key = Object.keys(CAST).find((k) => CAST[k] === who);
  if (key && pp && hasCastModel(key)) {
    ui.image(pp.cast(key, { w: size, h: size }, t, guard), x, y, size, size, false);
    return;
  }
  // The drawn ones (drawn at 48, scaled to fit).
  ui.g.save();
  ui.g.translate(x, y);
  ui.g.scale(size / 48, size / 48);
  drawnPortrait(ui, who, 0, 0, t);
  ui.g.restore();
}

/** A portrait drawn by hand, 48 x 48 at (x, y): a hood, a guard, a crowd, the Elder, a
 * dragon's head. */
function drawnPortrait(
  ui: UiLayer,
  who: { color: string; shape?: string; name?: string },
  x: number,
  y: number,
  t: number,
) {
  const g = ui.g;
  if (who.shape === "robed") {
    // A hood, its dark opening, two gold eyes.
    g.fillStyle = "#8a6a48";
    g.beginPath();
    g.moveTo(x + 6, y + 48);
    g.quadraticCurveTo(x + 8, y + 6, x + 24, y + 6);
    g.quadraticCurveTo(x + 40, y + 6, x + 42, y + 48);
    g.closePath();
    g.fill();
    g.fillStyle = "#120c08";
    g.beginPath();
    g.ellipse(x + 24, y + 26, 10, 12, 0, 0, Math.PI * 2);
    g.fill();
    const blink = Math.sin(t * 0.9) > 0.97 ? 1 : 3;
    ui.rect(x + 18, y + 24, 4, blink, "#ffd860");
    ui.rect(x + 26, y + 24, 4, blink, "#ffd860");
    ui.rect(x + 10, y + 44, 28, 3, "#c8b070");
    return;
  }
  if (who.shape === "guard") {
    // A shady character: a broad head, a squint, a scar.
    g.fillStyle = "#4a3a2a";
    g.beginPath();
    g.ellipse(x + 24, y + 28, 16, 15, 0, 0, Math.PI * 2);
    g.fill();
    ui.rect(x + 14, y + 22, 8, 2, "#ffffff");
    ui.rect(x + 28, y + 23, 6, 1, "#ffffff");
    ui.rect(x + 30, y + 16, 2, 12, "#8a2a1a");
    ui.rect(x + 16, y + 34, 16, 2, "#1a1010");
    ui.rect(x + 8, y + 8, 32, 6, "#2a2a2a");
    return;
  }
  if (who.shape === "crowd") {
    for (let k = 0; k < 5; k++) {
      const hx = x + 8 + (k % 3) * 16 + (k > 2 ? 8 : 0);
      const hy = y + 16 + (k > 2 ? 16 : 0) + Math.round(Math.sin(t * 6 + k) * 2);
      g.fillStyle = ["#6a8a3a", "#8a5a2a", "#3a6a8a", "#8a3a3a", "#6a6a2a"][k]!;
      g.beginPath();
      g.arc(hx, hy, 7, 0, Math.PI * 2);
      g.fill();
    }
    return;
  }
  if (who.shape === "elder") {
    // A dinosaur's head in profile, grey-green with a mossy crest.
    g.fillStyle = "#3a5a2a";
    g.beginPath();
    g.moveTo(x + 10, y + 46);
    g.lineTo(x + 12, y + 22);
    g.lineTo(x + 20, y + 12);
    g.lineTo(x + 36, y + 12);
    g.lineTo(x + 44, y + 20);
    g.lineTo(x + 44, y + 28);
    g.lineTo(x + 28, y + 30);
    g.lineTo(x + 26, y + 46);
    g.closePath();
    g.fill();
    ui.rect(x + 32, y + 17, 3, 3, "#ffffff");
    for (let k = 0; k < 4; k++) ui.rect(x + 14 + k * 5, y + 9 - (k % 2) * 2, 4, 4, "#7aa84a");
    return;
  }
  // A dragon: a horned head in silhouette with a glowing eye (Lumen's is pale gold).
  g.fillStyle = who.name === "Lumen" ? "#8a6a30" : "#1a1010";
  g.beginPath();
  g.moveTo(x + 8, y + 40);
  g.lineTo(x + 14, y + 16);
  g.lineTo(x + 10, y + 4);
  g.lineTo(x + 20, y + 12);
  g.lineTo(x + 30, y + 6);
  g.lineTo(x + 30, y + 16);
  g.lineTo(x + 44, y + 26);
  g.lineTo(x + 40, y + 34);
  g.lineTo(x + 26, y + 32);
  g.lineTo(x + 22, y + 44);
  g.closePath();
  g.fill();
  ui.rect(x + 24, y + 18, 4, 3, who.name === "Lumen" ? "#ffffff" : "#ffd84a");
}

/** Dragons crossing the sky (the opening's war). */
function dragonsOver(ui: UiLayer, t: number) {
  for (let k = 0; k < 3; k++) {
    const x = ((t * 60 + k * 140) % (ui.W + 80)) - 40;
    const y = 30 + k * 18 + Math.sin(t * 2 + k) * 4;
    const flap = Math.sin(t * 8 + k) * 6;
    const g = ui.g;
    g.fillStyle = "#1a0a0a";
    g.beginPath();
    g.moveTo(x - 14, y);
    g.lineTo(x, y - 8 - flap);
    g.lineTo(x + 4, y);
    g.lineTo(x + 18, y - 8 - flap);
    g.lineTo(x + 22, y + 2);
    g.lineTo(x, y + 4);
    g.closePath();
    g.fill();
  }
}

// ---------------------------------------------------------------- after a race

/** What a race did for the story (the save), from its result. */
export function applyResult(game: Game, run: AdventureRun, result: RaceResult) {
  const s = adventureOf(game).save;
  const cousin = run.kind === "duel" && kingdomById(run.kingdom)?.champion.look === youOf(game);
  const out =
    run.kind === "shards"
      ? shardRaceFinished(s, run.course, result.coins ?? { got: 0, total: 4 }, result.position)
      : run.kind === "duel"
        ? duelFinished(s, run.kingdom, result.position, cousin)
        : run.kind === "boss"
          ? bossFinished(s, run.kingdom, result.position)
          : run.kind === "king"
            ? run.final
              ? finalFinished(s, result.position)
              : kingRaceFinished(s, result.position)
            : raceFinished(s, run.kingdom, run.track, result.position);
  // The champion beaten 1 on 1 joins the crew: pickable everywhere from now on.
  if (run.kind === "duel" && s.duels[run.kingdom]) {
    const champ = kingdomById(run.kingdom)?.champion;
    if (champ) unlockRacer(champ.look);
  }
  persist(game);
  return out;
}

/** After an Adventure race. */
export function adventureResult(
  game: Game,
  result: RaceResult,
  entry: TrackEntry,
  retry: () => void,
): Screen {
  const a = adventureOf(game);
  const run = a.run!;
  const s = a.save;
  const out = applyResult(game, run, result);
  const home = () => {
    a.run = undefined;
    // From the overworld: back out of the mark you went in by (the story's scenes play
    // first when one's due).
    const o = game.overworld;
    if (o) s.where = { region: o.region, ...(o.at ? { at: o.at } : {}) };
    persist(game);
    goHome(game);
  };
  const menu = new VMenu(game, [
    { label: "CONTINUE", action: home },
    ...(out.progressed ? [] : [{ label: "RETRY", action: () => (game.screens.pop(), retry()) }]),
  ]);
  let t = 0;
  return {
    id: "ADVENTURE_RESULT",
    enter() {
      game.ui.interactive = true;
    },
    frame(dt, actions) {
      t += dt;
      if (t > 0.6)
        menu.handle(actions.map((x) => (x === "left" ? "up" : x === "right" ? "down" : x)));
    },
    draw(ui) {
      ui.dim(0.35);
      const w = 280;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = 30;
      ui.panel(x, y, w, 160, "parchment", "ink");
      const pos = result.position;
      ui.text(
        pos
          ? `${pos === 1 ? "1ST" : pos === 2 ? "2ND" : pos === 3 ? "3RD" : `${pos}TH`}!`
          : "FINISHED",
        ui.W / 2,
        y + 10,
        {
          scale: 3,
          color: pos === 1 ? PAL.gold : PAL.coral,
          outline: INK,
          align: "center",
        },
      );
      ui.text(entry.name.toUpperCase(), ui.W / 2, y + 38, { color: INK_SOFT, align: "center" });
      if (result.coins)
        ui.text(`SHARD PIECES ${result.coins.got}/${result.coins.total}`, ui.W / 2, y + 52, {
          color: result.coins.got >= result.coins.total ? "#2a6a2a" : "#8a2a1a",
          align: "center",
        });
      out.lines.forEach((l, i) =>
        ui.text(l, ui.W / 2, y + 70 + i * 12, {
          color: out.progressed ? "#2a6a2a" : INK,
          align: "center",
        }),
      );
      menu.draw(ui, x + 70, y + 112, w - 140, 16, 4);
    },
  };
}

/** A Trophy Race cup's podium from inside Adventure (there are no cups in Adventure):
 * just back home. */
export function adventureCupDone(game: Game, _place: number) {
  const a = adventureOf(game);
  a.run = undefined;
  game.trophy = undefined;
  goHome(game);
}

// ---------------------------------------------------------------- dev tools

/** Dev builds only: set the story to any point, without racing everything again. */
function storyJumps(game: Game, back: () => void): Screen {
  const a = adventureOf(game);
  const s = a.save;
  const winAll = (id: KingdomId) => coursesOf(id).forEach((c) => (s.wins[c.track] = true));
  const shardAll = (id: KingdomId) => coursesOf(id).forEach((c) => (s.shards[c.track] = true));
  const out = (id: KingdomId) => {
    winAll(id);
    s.duels[id] = true;
    s.games[id] = true;
  };
  const way = ["valley", "snow", "desert", "beach"] as const;
  type Item = { label: string; action: () => void };
  const jump = (label: string, region: string | undefined, f: () => void): Item => ({
    label,
    action: () => {
      const racer = s.racer ?? game.selection.racer;
      Object.assign(s, newSave(), { racer, driver: racer });
      game.selection.racer = racer as RacerId;
      f();
      // Every scene up to now as seen (so a jump doesn't replay them all).
      for (let d = dueScene(s); d; d = dueScene(s)) markSeen(s, d);
      for (const k of KINGDOMS) if (s.duels[k.id]) unlockRacer(k.champion.look);
      s.where = region ? { region } : undefined;
      persist(game);
      goHome(game);
    },
  });
  const items: Item[] = [
    jump("RESET: A NEW ADVENTURE", "dinosaur_valley", () => {}),
    jump("VALLEY: FESTIVAL WON (REX NEXT)", "dinosaur_valley", () => winAll("valley")),
    jump("VALLEY: REX JOINED (UNDERGROUND NEXT)", "dinosaur_valley", () => {
      winAll("valley");
      s.duels.valley = true;
    }),
    jump("SNOW KINGDOM: CAUGHT", "snow_kingdom", () => out("valley")),
    jump("SNOW KINGDOM: GAMES WON (BRACHIO NEXT)", "snow_kingdom", () => {
      out("valley");
      winAll("snow");
    }),
    jump("DESERT WORLD: CAUGHT", "desert_world", () => way.slice(0, 2).forEach(out)),
    jump("TROPIC ISLES: CAUGHT", "tropic_isles", () => way.slice(0, 3).forEach(out)),
    jump("DRAGON KINGDOM: THE KING'S GAMES", "dragon_kingdom", () => way.forEach(out)),
    jump("DRAGON KINGDOM: THE KING NEXT", "dragon_kingdom", () => {
      way.forEach(out);
      winAll("dragon");
    }),
    jump("AFTER THE RAGE: THE RUINED VALLEY", "dinosaur_valley", () => {
      way.forEach(out);
      winAll("dragon");
      s.kingRace = true;
    }),
    ...way.map((k, i) =>
      jump(
        `${nameOf(k).toUpperCase()} (RUINED): SHARDS DONE, DRAGON NEXT`,
        regionOfKingdom(k)?.id,
        () => {
          way.forEach(out);
          winAll("dragon");
          s.kingRace = true;
          way.slice(0, i).forEach((p) => (shardAll(p), (s.bosses[p] = true)));
          shardAll(k);
        },
      ),
    ),
    jump("DRAGON KINGDOM (RUINED): THE LAST SHARDS", "dragon_kingdom", () => {
      way.forEach(out);
      winAll("dragon");
      s.kingRace = true;
      way.forEach((p) => (shardAll(p), (s.bosses[p] = true)));
    }),
    jump("DRAGON KINGDOM: THE KING'S LAST RACE NEXT", "dragon_kingdom", () => {
      way.forEach(out);
      winAll("dragon");
      s.kingRace = true;
      way.forEach((p) => (shardAll(p), (s.bosses[p] = true)));
      shardAll("dragon");
    }),
    {
      label: "REPLAY THE LAST SCENE AGAIN",
      action: () => {
        s.seen.pop();
        persist(game);
        goHome(game);
      },
    },
  ];
  return devList(game, "JUMP IN THE STORY", "EACH JUMP REPLACES THE SAVE", items, back);
}

/** A dev menu page: a title, a note, a scrolling list. */
function devList(
  game: Game,
  title: string,
  note: string,
  items: { label: string; action: () => void }[],
  back: () => void,
): Screen {
  const menu = new VMenu(game, items, back);
  return {
    id: "ADVENTURE_DEV",
    seeThrough: false,
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#1d2a34");
      ui.text(title, ui.W / 2, 6, { color: PAL.gold, outline: INK, align: "center" });
      ui.text(note, ui.W / 2, 16, { color: PAL.cream, align: "center" });
      menu.draw(ui, ui.W / 2 - 130, 28, 260, 13, 3, 1, 12);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "GO"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

const clipLabel = () => (clipSwitch.on ? "RECORD CLIPS: ON · F4 SAVES" : "RECORD CLIPS: OFF");

/**
 * Dev builds: every testing tool on one short page (Blake, Oct 27: the menu ran off the
 * screen): the switches first, then the pages of jumps, scenes and warps. `back`: where
 * ESC goes (the overworld's pause menu it was opened from).
 */
export function devMenu(game: Game, opts: { back?: () => void } = {}): Screen {
  const back = opts.back ?? (() => goHome(game));
  const again = () => game.screens.go(devMenu(game, opts));
  const items: { label: string; action: () => void }[] = [
    {
      label: instaWin() ? "INSTA-WIN RACES: ON" : "INSTA-WIN RACES: OFF",
      action: () => {
        setInstaWin(!instaWin());
        items[0]!.label = instaWin() ? "INSTA-WIN RACES: ON" : "INSTA-WIN RACES: OFF";
      },
    },
    {
      label: freeRoam() ? "GO ANYWHERE: ON" : "GO ANYWHERE: OFF",
      action: () => {
        setFreeRoam(!freeRoam());
        items[1]!.label = freeRoam() ? "GO ANYWHERE: ON" : "GO ANYWHERE: OFF";
      },
    },
    {
      label: infiniteBoost() ? "INFINITE BOOST (HOLD E): ON" : "INFINITE BOOST (HOLD E): OFF",
      action: () => {
        setInfiniteBoost(!infiniteBoost());
        const it = items.find((i) => i.label.startsWith("INFINITE BOOST"));
        if (it)
          it.label = infiniteBoost()
            ? "INFINITE BOOST (HOLD E): ON"
            : "INFINITE BOOST (HOLD E): OFF";
      },
    },
    // The clip recorder (src/debug/clipRecorder.ts): while it's on, F4 saves the last
    // 20-40 s of play as a video with the kart's readings (reviews/<track>/clips/).
    ...(clipSwitch.available
      ? [
          {
            label: clipLabel(),
            action: () => {
              clipSwitch.set(!clipSwitch.on);
              const it = items.find((i) => i.label.startsWith("RECORD CLIPS"));
              if (it) it.label = clipLabel();
            },
          },
        ]
      : []),
    {
      // Free roam: any region, standard or ruined, or any journey between them.
      label: "WARP ANYWHERE (FREE ROAM) ...",
      action: () => {
        game.overworld = undefined;
        game.screens.push(devWarp(game));
      },
    },
    { label: "JUMP IN THE STORY ...", action: () => game.screens.go(storyJumps(game, again)) },
    { label: "WATCH ANY SCENE ...", action: () => game.screens.go(sceneList(game, 0, again)) },
    {
      label: "RACERS: UNLOCK ALL EIGHT",
      action: () => setAllUnlocked(true),
    },
    {
      label: "RACERS: BACK TO THE STARTING FOUR",
      action: () => setAllUnlocked(false),
    },
    { label: "BACK", action: back },
  ];
  return devList(
    game,
    "DEV TOOLS",
    "DEV BUILDS ONLY · INSTA-WIN: EVERY RACE WON AT GO",
    items,
    back,
  );
}

/** Dev builds: every scene in the story, to watch again and again (nothing is saved). */
function sceneList(game: Game, at = 0, back = () => game.screens.go(devMenu(game))): Screen {
  const all = sceneOrder();
  const title = (id: string) =>
    id === FAKE_CREDITS
      ? "The Fake Ending"
      : id === END_CREDITS
        ? "The Credits"
        : (SCENES[id]?.title ?? id);
  const menu = new VMenu(
    game,
    all.map((id, i) => ({
      label: id.toUpperCase().replace(/_/g, " "),
      action: () =>
        game.screens.go(
          sceneScreen(game, id, () => game.screens.go(sceneList(game, i, back)), false),
        ),
    })),
    back,
  );
  menu.focus = at;
  return {
    id: "ADVENTURE_SCENES",
    seeThrough: false,
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#1d2a34");
      ui.text("EVERY SCENE", ui.W / 2, 6, { color: PAL.gold, outline: INK, align: "center" });
      const id = all[menu.focus];
      if (id) ui.text(title(id).toUpperCase(), ui.W / 2, 16, { color: PAL.cream, align: "center" });
      menu.draw(ui, ui.W / 2 - 110, 28, 220, 13, 3, 1, 12);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "WATCH"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
