/**
 * Adventure mode's screens (the skeleton: every step of the story playable, everything
 * placeholder art and words; the rules are src/adventure/progress.ts, the story
 * src/adventure/data.ts and scenes.ts):
 *
 * - ADVENTURE_HUB: the world map. The five kingdoms on an old chart, the ones not reached
 *   yet in fog, the story's next step along the top, the tools you carry along the
 *   bottom. (It stands in for the drivable overworld to come.)
 * - ADVENTURE_KINGDOM: one kingdom's board: its championship, its four treasure map
 *   races, the map, its dragon, its return task, its mini-game slot.
 * - ADVENTURE_MAP: the map to the next kingdom, in four pieces.
 * - ADVENTURE_SCENE: a story scene: text boxes with a portrait over a picture.
 * - ADVENTURE_RESULT: after a single Adventure race: what it did for the story.
 * - ADVENTURE_DEV (dev builds only): jump to any point in the story.
 */
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { safeStorage } from "../app/settings";
import {
  DRAGON,
  KINGDOMS,
  STORY_ORDER,
  kingdomById,
  type Kingdom,
  type KingdomId,
} from "../adventure/data";
import {
  bossFinished,
  coinCourse,
  coinRaceFinished,
  completeReturn,
  cupFinished,
  dragonPhase,
  dueScene,
  eraseAdventure,
  kingFinished,
  kingdomPhase,
  loadAdventure,
  markSeen,
  newSave,
  objective,
  piecesOf,
  returnOpen,
  saveAdventure,
  toolsOf,
  championsOf,
  unlocked,
  type AdventureSave,
} from "../adventure/progress";
import type { AdventureRun } from "../adventure/run";
import { CAST, sceneById, type Scene } from "../adventure/scenes";
import type { RaceResult } from "../game/session";
import { trackById, type TrackEntry } from "../game/tracks";
import { startCup } from "../game/trophy";
import { worldById } from "../game/worlds";
import { wrap } from "../ui/font";
import type { UiLayer } from "../ui/layer";
import { INK, INK_SOFT, dashedRoute, island, parchment, type IslandStyle } from "../ui/mapArt";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { loadingScreen } from "./loading";
import { modeSelect } from "./modeSelect";
import { characterSelect } from "./characterSelect";
import { preview } from "./tracks";
import { STARTERS, setAllUnlocked, unlockRacer } from "../app/unlocks";
import { DESIGNS } from "../render/racers/designs";

const store = () => safeStorage();
const exists = (id: string) => Boolean(trackById(id));

/** The Adventure state on the game, loaded (or started) the first time it's needed. */
export function adventureOf(game: Game) {
  if (!game.adventure) game.adventure = { save: loadAdventure(store()) ?? newSave() };
  return game.adventure;
}
const persist = (game: Game) => saveAdventure(adventureOf(game).save, store());

const STYLE: Record<KingdomId, IslandStyle> = {
  valley: "prehistoric",
  snow: "frostveil",
  desert: "desert",
  beach: "beach",
  dragon: "dragon",
};
/** Where each kingdom sits on the chart (fractions of the screen). */
const SPOT: Record<KingdomId, [number, number]> = {
  valley: [0.14, 0.7],
  snow: [0.3, 0.36],
  desert: [0.5, 0.64],
  beach: [0.7, 0.74],
  dragon: [0.84, 0.36],
};
const nameOf = (id: KingdomId) => (id === "dragon" ? DRAGON.name : kingdomById(id)!.name);

function statusOf(s: AdventureSave, id: KingdomId): string {
  if (!unlocked(s, id)) return "NOT REACHED YET";
  if (id === "dragon") {
    const p = dragonPhase(s);
    return {
      locked: "",
      first: "FIND THE CHOSEN ONE",
      return: "IN RUINS: RETURN HOME FIRST",
      final: "THE LAST CHAMPIONSHIP",
      king: "THE DRAGON KING",
      done: "FREE!",
    }[p];
  }
  const k = kingdomById(id)!;
  const ph = kingdomPhase(s, k);
  if (returnOpen(s, k)) return `TASK: ${k.returnTask!.label}`;
  return {
    locked: "",
    championship: "THE CHAMPIONSHIP",
    coins: `THE MAP: ${piecesOf(s, k)}/4 PIECES`,
    boss: `RACE ${k.boss!.name.toUpperCase()}`,
    done: "FREE!",
  }[ph];
}

/** Start a race (or a cup's first race) for the story. */
function launch(
  game: Game,
  run: AdventureRun,
  track: string,
  cup?: { name: string; worldId: string; tracks: string[] },
) {
  const a = adventureOf(game);
  a.run = run;
  game.trophy = cup ? startCup(cup.worldId, cup.name, cup.tracks) : undefined;
  game.selection.trackId = track;
  game.selection.mode = "race";
  game.sounds.start();
  game.screens.go(loadingScreen(game));
}

// ---------------------------------------------------------------- the world map

export function adventureHub(game: Game): Screen {
  const a = adventureOf(game);
  a.run = undefined;
  game.trophy = undefined;
  const dev = import.meta.env.DEV;
  const spots: (KingdomId | "dev")[] = [...STORY_ORDER, ...(dev ? (["dev"] as const) : [])];
  let focus = Math.max(0, spots.indexOf(a.at ?? "valley"));
  let t = 0;
  let clicked = -1;
  const pick = (i: number) => {
    const id = spots[i]!;
    if (id === "dev") {
      game.sounds.confirm();
      return game.screens.go(devMenu(game));
    }
    if (!unlocked(a.save, id)) return game.sounds.error();
    game.sounds.confirm();
    a.at = id;
    game.screens.go(kingdomScreen(game, id));
  };
  return {
    id: "ADVENTURE_HUB",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      void game.audio.music.play("map", { fade: 1 });
      // The story's next turn plays first.
      const due = dueScene(a.save);
      if (due) game.screens.go(sceneScreen(game, due, () => game.screens.go(adventureHub(game))));
    },
    frame(dt, actions) {
      t += dt;
      if (clicked >= 0) {
        const c = clicked;
        clicked = -1;
        return pick(c);
      }
      for (const act of actions) {
        if (act === "left" || act === "up") {
          focus = (focus - 1 + spots.length) % spots.length;
          game.sounds.move();
        } else if (act === "right" || act === "down") {
          focus = (focus + 1) % spots.length;
          game.sounds.move();
        } else if (act === "confirm") return pick(focus);
        else if (act === "back") {
          game.sounds.back();
          return game.screens.go(modeSelect(game));
        }
      }
    },
    draw(ui) {
      ui.image(parchment(ui.W, ui.H, { compass: true, ships: true }), 0, 0, ui.W, ui.H, false);
      ui.text("ADVENTURE", ui.W / 2, 6, {
        scale: 2,
        color: PAL.coral,
        outline: INK,
        align: "center",
      });
      ui.text(objective(a.save), ui.W / 2, 24, { color: INK, align: "center" });
      const pos = (id: KingdomId): [number, number] => [
        Math.round(SPOT[id][0] * ui.W),
        Math.round(SPOT[id][1] * ui.H),
      ];
      // The route between the kingdoms reached so far.
      const reached = STORY_ORDER.filter((id) => unlocked(a.save, id));
      if (reached.length > 1) dashedRoute(ui.g, reached.map(pos));
      STORY_ORDER.forEach((id, i) => {
        const [x, y] = pos(id);
        const open = unlocked(a.save, id);
        const on = focus === i;
        const img = island(STYLE[id], on ? 22 : 19);
        // The kingdoms not reached yet: faint on the chart, a question mark over them.
        ui.g.globalAlpha = open ? 1 : 0.3;
        ui.image(
          img,
          x - img.width / 2,
          y -
            img.height / 2 +
            (on && !game.settings.general.reduceMotion ? Math.round(Math.sin(t * 4)) : 0),
          img.width,
          img.height,
          false,
        );
        ui.g.globalAlpha = 1;
        if (!open)
          ui.text("?", x, y - 6, { scale: 2, color: INK, outline: "#f4e8cc", align: "center" });
        if (ui.hover(x - 26, y - 24, 52, 48)) {
          if (game.menuInput.pointer.moved && focus !== i) {
            focus = i;
            game.sounds.move();
          }
          if (game.menuInput.pointer.clicked) clicked = i;
        }
        if (open || on)
          ui.text(open ? nameOf(id).toUpperCase() : "???", x, y + 24, {
            color: on ? "#8a2a1a" : INK,
            align: "center",
          });
      });
      // The chosen one's status, in a note.
      const sel = spots[focus]!;
      const note =
        sel === "dev"
          ? "DEV: JUMP ANYWHERE IN THE STORY"
          : `${nameOf(sel).toUpperCase()}: ${statusOf(a.save, sel)}`;
      ui.rect(0, ui.H - 40, ui.W, 14, "#f4e8cc", 0.85);
      ui.text(note, ui.W / 2, ui.H - 37, { color: "#8a2a1a", align: "center" });
      const tools = toolsOf(a.save).map((x) => x.name.toUpperCase());
      ui.text(`TOOLS: ${tools.length ? tools.join(" · ") : "NONE YET"}`, 8, ui.H - 24, {
        color: INK,
      });
      const champs = championsOf(a.save).map((c) => c.name.toUpperCase());
      if (champs.length) ui.text(`FRIENDS: ${champs.join(" · ")}`, 8, 36, { color: INK_SOFT });
      if (dev) {
        const on = sel === "dev";
        const r = ui.button(ui.W - 46, 6, 40, 14, "DEV", { focused: on });
        if (r.clicked) clicked = spots.length - 1;
      }
      hints(ui, [
        ["◀▶", "KINGDOM"],
        ["ENTER", "GO"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

// ---------------------------------------------------------------- a kingdom

function kingdomScreen(game: Game, id: KingdomId): Screen {
  const a = adventureOf(game);
  const s = a.save;
  const items: { label: string; sub?: string; disabled?: boolean; action: () => void }[] = [];
  const back = () => game.screens.go(adventureHub(game));
  const scene = (sid: string, then: () => void) => game.screens.go(sceneScreen(game, sid, then));
  const done = "★ ";
  if (id === "dragon") {
    const p = dragonPhase(s);
    const originals = DRAGON.courses.map((c) => c.track);
    items.push({
      label: `${s.cups.dragon ? done : ""}CHAMPIONSHIP: THE FIRST VISIT`,
      sub: "ITS FOUR COURSES, A TROPHY RACE",
      disabled: p !== "first",
      action: () =>
        launch(game, { kind: "cup", kingdom: "dragon" }, originals[0]!, {
          name: DRAGON.name,
          worldId: DRAGON.worldId,
          tracks: originals,
        }),
    });
    if (p === "return")
      items.push({
        label: "THE KINGDOM IS IN RUINS",
        sub: `RETURN TO THE FOUR KINGDOMS (${KINGDOMS.filter((k) => s.returns[k.id]).length}/4 TASKS)`,
        disabled: true,
        action: () => {},
      });
    const ruins = DRAGON.courses.map((c) => coinCourse(c, exists));
    items.push({
      label: `${s.finalCup ? done : ""}THE LAST CHAMPIONSHIP`,
      sub: ruins.some((r) => r.standIn)
        ? "ITS RUINED COURSES (STAND-INS FOR NOW)"
        : "ITS RUINED COURSES",
      disabled: p !== "final",
      action: () =>
        launch(game, { kind: "cup", kingdom: "dragon_final" }, ruins[0]!.track, {
          name: `${DRAGON.name} (Ruined)`,
          worldId: DRAGON.worldId,
          tracks: ruins.map((r) => r.track),
        }),
    });
    if (p === "done")
      items.push({
        label: "START A NEW ADVENTURE",
        sub: "THE STORY FROM THE START; YOUR CREW STAYS. PICK ANY OF THEM AS YOUR RACER.",
        action: () => {
          eraseAdventure(store());
          a.save = newSave();
          a.at = "valley";
          game.screens.go(characterSelect(game));
        },
      });
    items.push({
      label: `${s.kingWon ? done : ""}RACE THE DRAGON KING`,
      sub: s.kingLost ? `AS ${DRAGON.chosen.name.toUpperCase()}` : DRAGON.king.name.toUpperCase(),
      disabled: p !== "king" && p !== "done",
      action: () => launch(game, { kind: "king", chosen: s.kingLost }, DRAGON.king.track),
    });
  } else {
    const k = kingdomById(id)!;
    const ph = kingdomPhase(s, k);
    items.push({
      label: `${s.cups[id] ? done : ""}THE CHAMPIONSHIP`,
      sub: "A TROPHY RACE: WIN THE CUP",
      action: () => {
        const w = worldById(k.worldId)!;
        const tracks = k.courses.map((c) => c.track);
        launch(game, { kind: "cup", kingdom: id }, tracks[0]!, {
          name: k.name,
          worldId: w.id,
          tracks,
        });
      },
    });
    k.courses.forEach((c) => {
      const cc = coinCourse(c, exists);
      const name = trackById(c.track)?.name ?? c.track;
      items.push({
        label: `${s.pieces[c.track] ? done : ""}${name.toUpperCase()} (RUINED)`,
        sub: cc.standIn
          ? "4 SILVER COINS · STAND-IN: THE RUIN ISN'T BUILT YET"
          : "4 SILVER COINS AND 1ST PLACE",
        disabled: ph === "championship" || ph === "locked",
        action: () =>
          launch(game, { kind: "coins", kingdom: id, course: c.track, ...cc }, cc.track),
      });
    });
    items.push({
      label: `THE MAP (${piecesOf(s, k)}/4)`,
      sub: `TO THE ${nameOf(k.next!).toUpperCase()}`,
      disabled: ph === "championship",
      action: () => game.screens.go(mapScreen(game, k)),
    });
    items.push({
      label: `${s.bosses[id] ? done : ""}RACE ${k.boss!.name.toUpperCase()}`,
      sub:
        ph === "coins" || ph === "championship"
          ? "FINISH THE MAP FIRST"
          : "THE DRAGON OF THIS KINGDOM",
      disabled: ph === "coins" || ph === "championship",
      action: () =>
        scene(k.scenes.boss, () => launch(game, { kind: "boss", kingdom: id }, k.boss!.track)),
    });
    if (returnOpen(s, k) || s.returns[id])
      items.push({
        label: `${s.returns[id] ? done : ""}${k.returnTask!.label}`,
        sub: `PLACEHOLDER TASK WITH ${k.returnTask!.who.toUpperCase()}`,
        disabled: Boolean(s.returns[id]),
        action: () =>
          scene(k.returnTask!.scene, () => {
            completeReturn(s, id);
            persist(game);
            back();
          }),
      });
    items.push({ label: "MINI-GAME", sub: "A SLOT FOR LATER", disabled: true, action: () => {} });
  }
  // One line a row; the chosen row's explanation goes in the note on the right.
  const menu = new VMenu(
    game,
    items.map(({ sub: _sub, ...it }) => it),
    back,
  );
  return {
    id: "ADVENTURE_KINGDOM",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.image(parchment(ui.W, ui.H, { compass: false, ships: false }), 0, 0, ui.W, ui.H, false);
      const img = island(STYLE[id], 26);
      ui.image(img, ui.W - img.width - 6, 18, img.width, img.height, false);
      ui.text(nameOf(id).toUpperCase(), 14, 8, { scale: 2, color: PAL.coral, outline: INK });
      ui.text(statusOf(s, id), 14, 26, { color: INK });
      const lw = Math.min(230, ui.W - img.width - 40);
      menu.draw(ui, 22, 42, lw, 15, 4);
      const sub = items[menu.focus]?.sub;
      if (sub) {
        const nx = 22 + lw + 12;
        const nw = ui.W - nx - 10;
        const lines = wrap(sub, nw - 10);
        ui.rect(nx, 30 + img.height, nw, 12 + lines.length * 9, "#f4e8cc");
        ui.rect(nx, 30 + img.height, nw, 1, INK);
        lines.forEach((l, j) => ui.text(l, nx + 5, 36 + img.height + j * 9, { color: INK }));
      }
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "GO"],
        ["ESC", "WORLD MAP"],
      ]);
    },
  };
}

// ---------------------------------------------------------------- the map

function mapScreen(game: Game, k: Kingdom): Screen {
  const s = adventureOf(game).save;
  const back = () => game.screens.go(kingdomScreen(game, k.id));
  return {
    id: "ADVENTURE_MAP",
    seeThrough: false,
    frame(_dt, actions) {
      if (actions.some((x) => x === "back" || x === "confirm")) {
        game.sounds.back();
        back();
      }
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#2f4a5a");
      ui.text(`THE MAP TO THE ${nameOf(k.next!).toUpperCase()}`, ui.W / 2, 8, {
        color: PAL.gold,
        outline: INK,
        align: "center",
      });
      const w = 220;
      const h = 150;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = 26;
      const art = parchment(w, h, { compass: true, ships: false });
      k.courses.forEach((c, i) => {
        const qx = x + (i % 2) * (w / 2);
        const qy = y + Math.floor(i / 2) * (h / 2);
        const got = Boolean(s.pieces[c.track]);
        if (got) {
          ui.g.drawImage(
            art,
            (i % 2) * (w / 2),
            Math.floor(i / 2) * (h / 2),
            w / 2,
            h / 2,
            qx,
            qy,
            w / 2,
            h / 2,
          );
          if (i === 3 || piecesOf(s, k) === 4) {
            const isl = island(STYLE[k.next!], 16);
            if (i === 3)
              ui.image(
                isl,
                x + w / 2 - isl.width / 2,
                y + h / 2 - isl.height / 2,
                isl.width,
                isl.height,
                false,
              );
          }
        } else {
          ui.rect(qx + 2, qy + 2, w / 2 - 4, h / 2 - 4, "#1d2a34", 0.9);
          ui.text("?", qx + w / 4, qy + h / 4 - 7, { scale: 2, color: INK_SOFT, align: "center" });
        }
        ui.text((trackById(c.track)?.name ?? c.track).toUpperCase(), qx + w / 4, qy + h / 2 - 12, {
          color: got ? INK : "#8a9aa8",
          align: "center",
        });
      });
      ui.rect(x + w / 2, y, 1, h, INK);
      ui.rect(x, y + h / 2, w, 1, INK);
      ui.text(`${piecesOf(s, k)} OF 4 PIECES`, ui.W / 2, y + h + 8, {
        color: PAL.cream,
        outline: INK,
        align: "center",
      });
      hints(ui, [["ESC", "BACK"]]);
    },
  };
}

// ---------------------------------------------------------------- scenes

/** Play a story scene, then `then` (it marks the scene seen and saves first). */
export function sceneScreen(game: Game, id: string, then: () => void): Screen {
  const a = adventureOf(game);
  const sc: Scene | undefined = sceneById(id);
  let i = 0;
  let t = 0;
  let pp: PixelPortraits | undefined;
  const finish = () => {
    markSeen(a.save, id);
    persist(game);
    then();
  };
  // A new adventure as one of the crew who joined later: a "what if" story (placeholder).
  const crew = id === "intro" && !STARTERS.includes(game.selection.racer);
  const beats = [
    ...(crew
      ? [
          {
            who: "",
            text: `A WHAT-IF STORY: THIS TIME, ${DESIGNS[game.selection.racer].name.toUpperCase()} RACES FOR THE VALLEY.`,
          },
        ]
      : []),
    ...(sc?.beats ?? []),
  ];
  return {
    id: "ADVENTURE_SCENE",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
      if (!beats.length) finish();
    },
    exit() {
      pp?.dispose();
      pp = undefined;
    },
    frame(dt, actions) {
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
          i++;
          t = 0;
          if (i >= beats.length) return finish();
        }
      }
      if (game.menuInput.pointer.clicked && t > 0.2) {
        i++;
        t = 0;
        if (i >= beats.length) return finish();
      }
    },
    draw(ui) {
      const beat = beats[Math.min(i, beats.length - 1)];
      ui.rect(0, 0, ui.W, ui.H, sc?.backdrop.color ?? "#222");
      const img = sc?.backdrop.track
        ? preview(trackById(sc.backdrop.track)?.preview ?? "")
        : undefined;
      if (img) {
        // The picture, filling the screen, drifting slowly.
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
      if (beat?.fx === "flash" && t < 0.5) ui.rect(0, 0, ui.W, ui.H, "#fff2d0", 1 - t * 2);
      if (beat?.fx === "light")
        ui.rect(0, 0, ui.W, ui.H, "#fff8e0", 0.25 + 0.1 * Math.sin(ui.time * 3));
      if (beat?.fx === "dragons") dragonsOver(ui, ui.time);
      if (beat?.fx === "worldmap")
        ui.image(
          parchment(ui.W, ui.H, { compass: true, ships: true }),
          0,
          0,
          ui.W,
          ui.H * Math.min(1, t * 1.5),
          false,
        );
      ui.rect(0, 0, ui.W, 16, "#000000", 0.55);
      ui.text((sc?.title ?? id).toUpperCase(), ui.W / 2, 4, { color: PAL.gold, align: "center" });
      if (!beat) return;
      // The text box, with the speaker's portrait.
      const bx = 10;
      const bh = 64;
      const by = ui.H - bh - 18;
      const bw = ui.W - 20;
      ui.panel(bx, by, bw, bh, "parchment", "ink");
      const who = beat.who ? CAST[beat.who] : undefined;
      let tx = bx + 10;
      if (who) {
        portrait(
          ui,
          pp,
          who,
          beat.who === "you" ? game.selection.racer : who.look,
          bx + 6,
          by - 20,
          ui.time,
        );
        tx = bx + 64;
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

/** A speaker's portrait: a dinosaur's own face, or a placeholder dragon's head. */
function portrait(
  ui: UiLayer,
  pp: PixelPortraits | undefined,
  who: { color: string; shape?: string },
  look: string | undefined,
  x: number,
  y: number,
  t: number,
) {
  ui.rect(x - 2, y - 2, 52, 52, INK);
  ui.rect(x, y, 48, 48, who.color);
  if (look && pp) {
    const img = pp.draw(
      look as never,
      { w: 48, h: 48, view: "head", yaw: 0.35 + Math.sin(t * 1.4) * 0.15, levels: 8 },
      undefined,
      1 / 60,
    );
    ui.image(img, x, y, 48, 48, false);
    return;
  }
  const g = ui.g;
  if (who.shape === "elder" || who.shape === "chosen") {
    // A dinosaur's head in profile (placeholder): the Elder grey-green with a mossy crest,
    // the Chosen One dark with a pale gold scarf.
    const elder = who.shape === "elder";
    g.fillStyle = elder ? "#3a5a2a" : "#2a2a3a";
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
    ui.rect(x + 32, y + 17, 3, 3, elder ? "#ffffff" : "#ffd84a");
    if (elder)
      for (let k = 0; k < 4; k++) ui.rect(x + 14 + k * 5, y + 9 - (k % 2) * 2, 4, 4, "#7aa84a");
    else ui.rect(x + 10, y + 32, 18, 5, "#f2e6a8");
    return;
  }
  // A dragon (placeholder): a horned head in silhouette with a glowing eye.
  g.fillStyle = "#1a1010";
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
  ui.rect(x + 24, y + 18, 4, 3, "#ffd84a");
}

/** Dragons crossing the sky (the attack scenes). */
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

/** After a single Adventure race (a treasure map race, a dragon, the King). */
export function adventureResult(
  game: Game,
  result: RaceResult,
  entry: TrackEntry,
  retry: () => void,
): Screen {
  const a = adventureOf(game);
  const run = a.run!;
  const s = a.save;
  const out =
    run.kind === "coins"
      ? coinRaceFinished(s, run.course, result.coins ?? { got: 0, total: 4 }, result.position)
      : run.kind === "boss"
        ? bossFinished(s, run.kingdom, result.position)
        : run.kind === "king"
          ? kingFinished(s, run.chosen ? result.position : undefined)
          : { progressed: false, lines: [] };
  persist(game);
  // The King's first race is lost whatever happens: straight on to the story.
  const scripted = run.kind === "king" && !run.chosen;
  const home = () => {
    a.run = undefined;
    const kd = run.kind === "king" ? "dragon" : run.kingdom;
    a.at = kd === "dragon_final" ? "dragon" : kd;
    game.screens.go(adventureHub(game));
  };
  const menu = new VMenu(game, [
    { label: "CONTINUE", action: home },
    ...(scripted || (out.progressed && run.kind !== "coins")
      ? []
      : [{ label: "RETRY", action: () => (game.screens.pop(), retry()) }]),
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
        ui.text(`SILVER COINS ${result.coins.got}/${result.coins.total}`, ui.W / 2, y + 52, {
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

/** A championship cup is over (from the Trophy podium): count it and go back to the map. */
export function adventureCupDone(game: Game, place: number) {
  const a = adventureOf(game);
  const run = a.run;
  if (run?.kind === "cup") {
    cupFinished(a.save, run.kingdom, place);
    // The champion beaten in it joins the crew: pickable everywhere from now on.
    if (run.kingdom !== "dragon_final" && a.save.cups[run.kingdom]) {
      const champ = kingdomById(run.kingdom as KingdomId)?.champion;
      if (champ) unlockRacer(champ.look);
    }
    persist(game);
    a.at = run.kingdom === "dragon_final" ? "dragon" : run.kingdom;
  }
  a.run = undefined;
  game.trophy = undefined;
  game.screens.go(adventureHub(game));
}

// ---------------------------------------------------------------- dev tools

/** Dev builds only: set the story to any point, without racing everything again. */
function devMenu(game: Game): Screen {
  const a = adventureOf(game);
  const s = a.save;
  const save = () => persist(game);
  const seeAll = () => {
    // Mark every scene up to now as seen (so jumping doesn't replay them all).
    for (;;) {
      const d = dueScene(s);
      if (!d) break;
      markSeen(s, d);
    }
  };
  const free = (id: KingdomId) => {
    const k = kingdomById(id)!;
    s.cups[id] = true;
    for (const c of k.courses) s.pieces[c.track] = true;
    s.bosses[id] = true;
  };
  type Item = { label: string; action: () => void };
  const jump = (label: string, f: () => void): Item => ({
    label,
    action: () => {
      Object.assign(s, newSave());
      f();
      seeAll();
      for (const k of KINGDOMS) if (s.cups[k.id] && k.champion) unlockRacer(k.champion.look);
      save();
      game.screens.go(adventureHub(game));
    },
  });
  const items: Item[] = [
    jump("RESET: A NEW ADVENTURE", () => eraseAdventure(store())),
    jump("VALLEY: CHAMPIONSHIP WON", () => (s.cups.valley = true)),
    jump("VALLEY: MAP DONE (BOSS NEXT)", () => {
      s.cups.valley = true;
      for (const c of kingdomById("valley")!.courses) s.pieces[c.track] = true;
    }),
    jump("SNOW KINGDOM OPEN", () => free("valley")),
    jump("DESERT KINGDOM OPEN", () => ["valley", "snow"].forEach((k) => free(k as KingdomId))),
    jump("BEACH KINGDOM OPEN", () =>
      ["valley", "snow", "desert"].forEach((k) => free(k as KingdomId)),
    ),
    jump("DRAGON KINGDOM OPEN", () => KINGDOMS.forEach((k) => free(k.id))),
    jump("AFTER THE SACRIFICE (RETURN)", () => {
      KINGDOMS.forEach((k) => free(k.id));
      s.cups.dragon = true;
    }),
    jump("AFTER THE RESURRECTION", () => {
      KINGDOMS.forEach((k) => free(k.id));
      s.cups.dragon = true;
      KINGDOMS.forEach((k) => (s.returns[k.id] = true));
    }),
    jump("THE DRAGON KING (FIRST RACE)", () => {
      KINGDOMS.forEach((k) => free(k.id));
      s.cups.dragon = true;
      KINGDOMS.forEach((k) => (s.returns[k.id] = true));
      s.finalCup = true;
    }),
    jump("THE DRAGON KING (AS THE CHOSEN ONE)", () => {
      KINGDOMS.forEach((k) => free(k.id));
      s.cups.dragon = true;
      KINGDOMS.forEach((k) => (s.returns[k.id] = true));
      s.finalCup = true;
      s.kingLost = true;
    }),
    {
      label: "RACERS: UNLOCK ALL EIGHT",
      action: () => {
        setAllUnlocked(true);
        game.sounds.confirm();
      },
    },
    {
      label: "RACERS: BACK TO THE STARTING FOUR",
      action: () => {
        setAllUnlocked(false);
        game.sounds.confirm();
      },
    },
    {
      label: "REPLAY THE NEXT SCENE AGAIN",
      action: () => {
        s.seen.pop();
        save();
        game.screens.go(adventureHub(game));
      },
    },
  ];
  const menu = new VMenu(game, items, () => game.screens.go(adventureHub(game)));
  return {
    id: "ADVENTURE_DEV",
    seeThrough: false,
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#1d2a34");
      ui.text("ADVENTURE DEV MENU", ui.W / 2, 6, {
        color: PAL.gold,
        outline: INK,
        align: "center",
      });
      ui.text("DEV BUILDS ONLY · EACH JUMP REPLACES THE SAVE", ui.W / 2, 16, {
        color: PAL.cream,
        align: "center",
      });
      menu.draw(ui, ui.W / 2 - 110, 28, 220, 13, 3);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "JUMP"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
