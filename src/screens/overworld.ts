/**
 * The overworld (src/overworld/regions.ts): drive a region freely, and drive into a
 * course's gateway to race it.
 *
 * - OVERWORLD_LOADING: builds the region's session (free roam: no countdown, laps,
 *   clock or rivals) and drops you at its spawn, or back out of the gateway you raced.
 * - OVERWORLD: free roam. Each gateway is an arch with its course's name over it; drive
 *   in and its card opens. After the race you come back out of the same arch.
 * - GATEWAY: the course's card: standard or ruined, your best times, GO or back out.
 *
 * Step 1 of the overworld doc's build order (dev builds: ?overworld, or the Adventure
 * dev menu). Leaving it clears game.overworld, so races go back to their usual menus.
 */
import * as THREE from "three";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { loadRecords } from "../app/records";
import {
  inGateway,
  OBSTACLE_TEXT,
  REGIONS,
  regionAsIs,
  regionById,
  storyPlace,
  type Gateway,
  type Passage,
  type Region,
} from "../overworld/regions";
import type { Session } from "../game/session";
import { trackById, type TrackEntry } from "../game/tracks";
import { worldById, worldOfTrack } from "../game/worlds";
import { wrap } from "../ui/font";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { loadingScreen } from "./loading";
import { titleScreen } from "./title";
import { confirmDialog, drawHud } from "./race";
import { optionsScreen } from "./options";
import {
  adventureHub,
  devMenu,
  adventureOf,
  freeRoam,
  journeyBegun,
  kingdomScreen,
  launch,
  peekWorldMap,
  persist,
  sceneScreen,
} from "./adventure";
import { DRAGON, KINGDOMS, STORY_ORDER, kingdomById, type KingdomId } from "../adventure/data";
import { Racer as RacerView } from "../render/racers/racer";
import type { RacerId } from "../render/racers/designs";
import {
  championshipTracks,
  winsOf,
  championWon,
  championsOf,
  coinCourse,
  completeReturn,
  dragonPhase,
  dueScene,
  kingdomPhase,
  objective,
  piecesOf,
  returnOpen,
} from "../adventure/progress";
import {
  bellPosts,
  gateSolid,
  newPuzzleState,
  stepPuzzle,
  type Puzzle,
} from "../overworld/puzzles";
import { createChestView, createObstacleView, createPuzzleView } from "../overworld/puzzleView";
import { characterSelect } from "./characterSelect";
import { createVillagers, parseHomes, type Villagers } from "../overworld/villagers";
import { exitSpot } from "../overworld/exits";

/** Where the overworld is: the region, and the gateway you went into (you come back
 * out of it). */
export interface OverworldState {
  region: string;
  at?: string;
  /** Adventure mode: the story runs through the region (the gateways open its races). */
  adventure?: boolean;
  /** Dev free roam: drive the regions as they are after the attack (Adventure decides
   * that itself: once the kingdom's champion has joined you). */
  ruined?: boolean;
}

/** Dev builds: a region warped to as standard or ruined stays so (whatever the story
 * says) until warped again (the warp list: devWarp). */
const devState = new Map<string, boolean>();

/** Dev free roam (not an Adventure file): puzzles solved and keys found, for this visit. */
const devSolved = new Set<string>();
const devKeys = new Set<string>();

/** The region's puzzles while you drive it: their state, their things in the scene and
 * the gates' collision (src/overworld/puzzles.ts). */
function regionPuzzles(game: Game, session: Session, region: Region) {
  const story = game.overworld?.adventure ? adventureOf(game) : undefined;
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  const key = (p: Puzzle) => `${region.id}.${p.id}`;
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  let banner: { text: string; t: number } | undefined;
  let lastBeat = 0;
  const items = (region.puzzles ?? []).map((p) => {
    const st = newPuzzleState(
      p,
      story ? Boolean(story.save.puzzles[key(p)]) : devSolved.has(key(p)),
    );
    const solid = gateSolid(p, groundAt(p.gate.x, p.gate.z));
    if (!st.solved) session.solids.push(solid);
    // A bell's frame posts are solid.
    for (const b of bellPosts(p))
      session.solids.push({
        kind: "circle",
        look: "tree",
        x: b.x,
        z: b.z,
        radius: 0.5,
        height: groundAt(b.x, b.z) + 7,
      });
    return { p, st, solid, view: createPuzzleView(session.root, p, groundAt) };
  });
  // The kingdom's hidden key shows once its champion has joined you (the valley's: once
  // its championship is won); dev free roam always.
  const keyShown = () => !story || !k || championWon(story.save, k);
  const keyTaken = () =>
    story ? Boolean(region.kingdom && story.save.keys[region.kingdom]) : devKeys.has(region.id);
  const say = (text: string) => (banner = { text, t: 3.5 });
  return {
    step(x: number, z: number, dt: number, t: number) {
      if (banner && (banner.t -= dt) <= 0) banner = undefined;
      for (const it of items) {
        for (const e of stepPuzzle(it.p, it.st, x, z, dt)) {
          if (e.kind === "press") {
            if (it.p.look === "bell") game.sounds.bell(e.count);
            else if (it.p.look === "gong") game.sounds.gong(e.count);
            else game.sounds.stone(e.count);
            if (e.count === 1 && it.p.switches.length > 1) say(it.p.hint);
            lastBeat = Math.ceil(it.st.left);
          } else if (e.kind === "reset") {
            game.sounds.stonesReset();
            say(
              e.wrong
                ? `WRONG ONE! ${it.p.hint}`
                : `TOO SLOW! THE ${it.p.look === "stone" ? "STONES ROSE AGAIN" : `${it.p.look.toUpperCase()}S FELL SILENT`}`,
            );
          } else {
            game.sounds.solved();
            const i = session.solids.indexOf(it.solid);
            if (i >= 0) session.solids.splice(i, 1);
            if (story) {
              story.save.puzzles[key(it.p)] = true;
              persist(game);
            } else devSolved.add(key(it.p));
            say(
              it.p.prize && !keyShown()
                ? "THE GATE IS OPEN... BUT THE PLINTH INSIDE IS BARE, FOR NOW"
                : "THE GATE IS OPEN!",
            );
          }
        }
        // The drums, once a second while they run (faster near the end).
        if (it.st.left > 0) {
          const beat = Math.ceil(it.st.left * (it.st.left < 5 ? 2 : 1));
          if (beat !== lastBeat) {
            lastBeat = beat;
            game.sounds.drum(it.st.left < 5);
          }
        }
        // The prize: drive into it.
        const pr = it.p.prize;
        if (
          pr &&
          it.st.solved &&
          keyShown() &&
          !keyTaken() &&
          Math.hypot(x - pr.x, z - pr.z) < 3.5
        ) {
          game.sounds.keyFound();
          if (story && region.kingdom) {
            story.save.keys[region.kingdom] = true;
            persist(game);
          } else devKeys.add(region.id);
          say(`YOU FOUND ${region.name.toUpperCase()}'S HIDDEN KEY!`);
        }
        it.view.update(it.st, keyTaken(), keyShown(), t, dt);
      }
    },
    draw(ui: UiLayer) {
      const running = items.find((it) => it.st.left > 0);
      if (running) {
        const n = running.st.pressed.filter(Boolean).length;
        const text = `${running.p.label} ${n}/${running.p.switches.length}`;
        const w = ui.textWidth(text) + 20;
        ui.panel(ui.W / 2 - w / 2, 6, w, 30, "wood", "gold");
        ui.text(text, ui.W / 2, 10, { color: PAL.cream, outline: PAL.shadow, align: "center" });
        ui.text(running.st.left.toFixed(1), ui.W / 2, 21, {
          color: running.st.left < 5 ? PAL.coral : PAL.gold,
          outline: PAL.shadow,
          align: "center",
        });
      }
      if (banner)
        wrap(banner.text, ui.W - 60)
          .slice(0, 2)
          .forEach((l, i) =>
            ui.text(l, ui.W / 2, ui.H / 2 - 40 + i * 10, {
              color: PAL.gold,
              outline: PAL.shadow,
              align: "center",
            }),
          );
    },
    dispose() {
      for (const it of items) it.view.dispose();
    },
  };
}

/** The region's map, top right: its ring road, the gateways (gold; the dragon's lair
 * red), the ways on (white), the champion or the return task when they're waiting (green),
 * and you (blinking). Drawn once to a canvas; only you move. */
function regionMap(session: Session, region: Region, extra: { x: number; z: number }[]) {
  const S = 72;
  const R = 480; // (metres from the middle to the map's edge)
  const at = (x: number, z: number) =>
    [S / 2 + (x / R) * (S / 2), S / 2 + (z / R) * (S / 2)] as const;
  const cv = document.createElement("canvas");
  cv.width = S;
  cv.height = S;
  const g = cv.getContext("2d")!;
  g.fillStyle = "rgba(20, 30, 20, 0.75)";
  g.beginPath();
  g.arc(S / 2, S / 2, S / 2 - 1, 0, Math.PI * 2);
  g.fill();
  g.strokeStyle = "#d8c8a0";
  g.lineWidth = 2;
  g.beginPath();
  // (A journey: only its road, not the way round out of sight.)
  const road = region.journey?.road;
  const pts = (session.track?.samples ?? []).filter(
    (p) => !road || (p.dist >= road[0] && p.dist <= road[1]),
  );
  pts.forEach((p, i) => {
    const [u, v] = at(p.pos.x, p.pos.z);
    if (i === 0) g.moveTo(u, v);
    else g.lineTo(u, v);
  });
  if (!road) g.closePath();
  g.stroke();
  const dot = (x: number, z: number, color: string, r = 2) => {
    const [u, v] = at(x, z);
    g.fillStyle = color;
    g.fillRect(Math.round(u - r), Math.round(v - r), r * 2, r * 2);
  };
  for (const p of region.passages ?? []) dot(p.x, p.z, "#ffffff");
  for (const gw of region.gateways) dot(gw.x, gw.z, gw.boss || gw.king ? "#e04030" : "#f0c040");
  for (const e of extra) dot(e.x, e.z, "#60e070");
  return {
    draw(ui: UiLayer, t: number, target?: { x: number; z: number }) {
      const x0 = ui.W - S - 6;
      const y0 = 6;
      ui.image(cv, x0, y0, S, S, false);
      // Where the story wants you: a pulsing marker.
      if (target) {
        const [u, v] = at(target.x, target.z);
        const r = 3 + Math.round(1.5 + 1.5 * Math.sin(t * 5));
        const c = "#ffffff";
        ui.rect(x0 + Math.round(u) - r, y0 + Math.round(v) - r, r * 2, 1, c);
        ui.rect(x0 + Math.round(u) - r, y0 + Math.round(v) + r - 1, r * 2, 1, c);
        ui.rect(x0 + Math.round(u) - r, y0 + Math.round(v) - r, 1, r * 2, c);
        ui.rect(x0 + Math.round(u) + r - 1, y0 + Math.round(v) - r, 1, r * 2, c);
      }
      const s = session.entrants[0]!.state;
      if (Math.sin(t * 8) > -0.3) {
        const [u, v] = at(s.x, s.z);
        ui.rect(x0 + Math.round(u) - 2, y0 + Math.round(v) - 2, 4, 4, "#ff60c0");
      }
    },
  };
}

/** Your crew at the town square: the champions who've joined you, parked in a row by
 * where you arrive (dev free roam: the kingdom's own champion), and the champion who's
 * waiting to race you 1 on 1 parked by their challenge's arch. */
function regionCrew(game: Game, session: Session, region: Region) {
  const story = game.overworld?.adventure ? adventureOf(game).save : undefined;
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  const waiting = challengeOf(game, region);
  const joined = story
    ? championsOf(story).map((c) => c.look)
    : k?.champion
      ? [k.champion.look]
      : [];
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const made: RacerView[] = [];
  const park = (look: RacerId, x: number, z: number, heading: number) => {
    const r = new RacerView(look, { seed: made.length * 13 + 3 });
    const y = groundAt(x, z);
    r.root.position.set(x, y, z);
    r.root.rotation.y = heading;
    r.placeShadow(x, y, z, heading, 0);
    session.root.add(r.root, r.shadow);
    // (Parked karts are solid.)
    session.solids.push({ kind: "circle", look: "tree", x, z, radius: 1.4, height: y + 3 });
    made.push(r);
  };
  const sp = region.spawn;
  const fx = Math.sin(sp.heading);
  const fz = Math.cos(sp.heading);
  joined.forEach((look, i) => {
    const side = i % 2 ? 1 : -1;
    const across = side * (6 + 4 * Math.floor(i / 2));
    // In a row either side of the way out of the square, facing in to it.
    park(look, sp.x + fx * 10 + fz * across, sp.z + fz * 10 - fx * across, sp.heading + Math.PI);
  });
  if (waiting && region.challenge && k?.champion) {
    const c = region.challenge;
    const rx = Math.cos(c.heading);
    const rz = -Math.sin(c.heading);
    park(k.champion.look, c.x + rx * 9, c.z + rz * 9, c.heading);
  }
  return {
    dispose() {
      for (const r of made) r.dispose(session.root);
    },
  };
}

/** Dev free roam: secrets found, for this visit. */
const devSecrets = new Set<string>();

/** A region's secret: its yard's obstacle (a later kingdom's tool clears it; dev free
 * roam: open in the ruined region), and the treasure chest inside (drive into it). */
function regionSecret(game: Game, session: Session, region: Region) {
  const sc = region.secret;
  if (!sc) return undefined;
  const story = game.overworld?.adventure ? adventureOf(game) : undefined;
  const open = story ? Boolean(story.save.bosses[sc.tool]) : Boolean(game.overworld?.ruined);
  const found = () => (story ? Boolean(story.save.secrets[region.id]) : devSecrets.has(region.id));
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const view = createObstacleView(session.root, sc.obstacle, sc.gate, groundAt);
  view.shown = !open;
  if (!open) session.solids.push(gateSolid({ gate: sc.gate }, groundAt(sc.gate.x, sc.gate.z)));
  const chest = createChestView(session.root, sc.spot, sc.gate.heading, groundAt);
  chest.open = found();
  const tool = kingdomById(sc.tool)?.tool?.name.toUpperCase() ?? "ANOTHER KINGDOM'S TOOL";
  let near = false;
  let banner: { text: string; t: number } | undefined;
  return {
    step(x: number, z: number, dt: number) {
      if (banner && (banner.t -= dt) <= 0) banner = undefined;
      const now = !open && Math.hypot(x - sc.gate.x, z - sc.gate.z) < sc.gate.width + 4;
      if (now && !near)
        banner = { text: `${OBSTACLE_TEXT[sc.obstacle]}. THE ${tool} COULD CLEAR IT.`, t: 3.5 };
      near = now;
      if (open && !found() && Math.hypot(x - sc.spot.x, z - sc.spot.z) < 3.5) {
        if (story) {
          story.save.secrets[region.id] = true;
          persist(game);
        } else devSecrets.add(region.id);
        chest.open = true;
        game.sounds.keyFound();
        const n = story ? Object.keys(story.save.secrets).length : devSecrets.size;
        const of = REGIONS.filter((r) => r.secret).length;
        banner = { text: `A SECRET CHEST! (${n} OF ${of} FOUND)`, t: 4 };
      }
    },
    draw(ui: UiLayer) {
      if (banner)
        wrap(banner.text, ui.W - 60)
          .slice(0, 2)
          .forEach((l, i) =>
            ui.text(l, ui.W / 2, ui.H / 2 - 28 + i * 10, {
              color: PAL.gold,
              outline: PAL.shadow,
              align: "center",
            }),
          );
    },
    dispose() {
      view.dispose();
      chest.dispose();
    },
  };
}

/** Act V's return task's yard: its tool obstacle (solid, shown, until the kingdom's tool
 * is in the bag; dev free roam: in the ruined region) and what it says when you meet it. */
function regionReturnGate(game: Game, session: Session, region: Region) {
  const rt = region.returnTask;
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (!rt || !k) return undefined;
  const story = game.overworld?.adventure ? adventureOf(game) : undefined;
  const open = story ? Boolean(story.save.bosses[k.id]) : Boolean(game.overworld?.ruined);
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const view = createObstacleView(session.root, rt.obstacle, rt.gate, groundAt);
  view.shown = !open;
  if (!open) session.solids.push(gateSolid({ gate: rt.gate }, groundAt(rt.gate.x, rt.gate.z)));
  let near = false;
  let banner = 0;
  const tool = k.tool?.name.toUpperCase() ?? "A TOOL";
  return {
    step(x: number, z: number, dt: number) {
      banner = Math.max(0, banner - dt);
      const now = !open && Math.hypot(x - rt.gate.x, z - rt.gate.z) < rt.gate.width + 4;
      if (now && !near) banner = 3.5;
      near = now;
    },
    draw(ui: UiLayer) {
      if (banner > 0)
        wrap(`${OBSTACLE_TEXT[rt.obstacle]}. THE ${tool} COULD CLEAR IT ONE DAY.`, ui.W - 60)
          .slice(0, 2)
          .forEach((l, i) =>
            ui.text(l, ui.W / 2, ui.H / 2 - 40 + i * 10, {
              color: PAL.cream,
              outline: PAL.shadow,
              align: "center",
            }),
          );
    },
    dispose: () => view.dispose(),
  };
}

/** The passages' blockers (the fire in the Burnt Gorge, Rimefang's ice, Scorchwind's
 * drift): solid and shown until the dragon falls (dev free roam: never), and the first
 * time you come back after that they break open while you watch. */
function regionBlockers(game: Game, session: Session, region: Region) {
  const story = game.overworld?.adventure ? adventureOf(game) : undefined;
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  let banner: { text: string; t: number } | undefined;
  const items = (region.passages ?? []).flatMap((p) => {
    const b = p.blocker;
    if (!b || !p.opensAfter) return [];
    const open = !story || Boolean(story.save.bosses[p.opensAfter]);
    const seen = `opened:${region.id}.${p.id}`;
    const breaking = Boolean(story) && open && !story!.save.seen.includes(seen);
    if (open && !breaking) return [];
    const gate = { x: p.x, z: p.z, heading: p.heading, width: b.width };
    const view = createObstacleView(session.root, b.kind, gate, groundAt);
    const solid = gateSolid({ gate }, groundAt(p.x, p.z));
    if (!open) session.solids.push(solid);
    if (breaking) {
      story!.save.seen.push(seen);
      persist(game);
      banner = { text: `${p.label.split(" · ")[0]} IS OPEN!`, t: 4 };
      game.sounds.solved();
    }
    return [{ p, view, open, sink: 0, near: false }];
  });
  return {
    step(x: number, z: number, dt: number, t: number) {
      if (banner && (banner.t -= dt) <= 0) banner = undefined;
      for (const it of items) {
        it.view.flicker(t);
        if (it.open) {
          // Breaking open: a moment's pause, then it sinks away.
          it.sink = Math.min(1, it.sink + dt / 2.5);
          it.view.sunk = Math.max(0, it.sink * 1.4 - 0.4);
          continue;
        }
        const now = Math.hypot(x - it.p.x, z - it.p.z) < it.p.blocker!.width / 2 + 8;
        if (now && !it.near) banner = { text: it.p.locked ?? "NOT YET", t: 3.5 };
        it.near = now;
      }
    },
    /** Is this passage still shut behind its blocker? */
    shut: (id: string) => items.some((it) => it.p.id === id && !it.open),
    draw(ui: UiLayer) {
      if (banner)
        wrap(banner.text, ui.W - 60)
          .slice(0, 2)
          .forEach((l, i) =>
            ui.text(l, ui.W / 2, ui.H / 2 - 52 + i * 10, {
              color: PAL.gold,
              outline: PAL.shadow,
              align: "center",
            }),
          );
    },
    dispose() {
      for (const it of items) it.view.dispose();
    },
  };
}

/** Act V: the return task, waiting in its yard (once the Dragon Kingdom sends you home). */
function returnOf(game: Game, region: Region) {
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (!k?.returnTask || !region.returnTask || !game.overworld?.adventure) return undefined;
  return returnOpen(adventureOf(game).save, k) ? k : undefined;
}

/** The return task's card: the placeholder scene, then back out into the region. */
function returnCard(game: Game, region: Region): Screen {
  const k = returnOf(game, region)!;
  const go = () =>
    game.screens.go(
      sceneScreen(game, k.returnTask!.scene, () => {
        completeReturn(adventureOf(game).save, k.id);
        persist(game);
        game.screens.go(overworldLoading(game, region.id, "return", true));
      }),
    );
  const menu = new VMenu(
    game,
    [
      { label: "GO", action: go },
      { label: "NOT YET", action: () => game.screens.pop() },
    ],
    () => game.screens.pop(),
  );
  return {
    id: "GATEWAY",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.4);
      const w = 260;
      const h = 90;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = Math.round(ui.H / 2 - h / 2) - 8;
      ui.panel(x, y, w, h, "parchment", "ink");
      ui.text(k.returnTask!.label, ui.W / 2, y + 8, {
        scale: 2,
        color: PAL.coral,
        outline: PAL.ink,
        align: "center",
      });
      ui.text(`A PLACEHOLDER TASK WITH ${k.returnTask!.who.toUpperCase()}.`, ui.W / 2, y + 30, {
        color: PAL.ink,
        align: "center",
      });
      menu.draw(ui, x + 60, y + h - 38, w - 120, 14, 4);
    },
  };
}

/** Where to look down from for the ground (the floor search doesn't reach from far above). */
const PROBE_Y = 200;

const fmt = (s?: number) =>
  s === undefined ? "-:--.--" : `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, "0")}`;

/** The region as a menu entry (the HUD and loading screen want one). */
const entryOf = (r: Region): TrackEntry => ({
  id: r.id,
  name: r.name,
  description: "",
  preview: "",
  modes: ["practice"],
  music: r.music,
  load: { scene: "track", packageId: r.packageId },
});

export function overworldLoading(
  game: Game,
  regionId: string,
  at?: string,
  adventure = game.overworld?.adventure ?? false,
  /** Dev builds: this state whatever the story says (the warp list). */
  devRuined?: boolean,
): Screen {
  const full = regionById(regionId)!;
  // The region before or after its dragon's attack.
  const k = full.kingdom ? kingdomById(full.kingdom) : undefined;
  const story = adventure && Boolean(full.kingdom || full.journey);
  // (Adventure: once the kingdom's champion has joined you and the dragon struck; the
  // Dragon Kingdom after the sacrifice, at the end of its first championship.)
  const save = story ? adventureOf(game).save : undefined;
  const ruined =
    Boolean(full.ruinPackageId) &&
    (import.meta.env.DEV && (devRuined ?? devState.get(full.id)) !== undefined
      ? (devRuined ?? devState.get(full.id))!
      : save
        ? full.kingdom === "dragon"
          ? Boolean(save.cups.dragon)
          : Boolean(k && championWon(save, k))
        : Boolean(game.overworld?.ruined));
  if (import.meta.env.DEV && devRuined !== undefined) devState.set(full.id, devRuined);
  const region = regionAsIs(full, ruined);
  let ready: Session | undefined;
  let failed: string | undefined;
  let alive = true;
  let t = 0;
  return {
    id: "OVERWORLD_LOADING",
    seeThrough: false,
    enter() {
      game.ui.interactive = false;
      game.overworld = {
        region: region.id,
        at,
        adventure: story,
        ruined: story ? undefined : ruined,
      };
      // Adventure: the file remembers where you are.
      if (save && story) {
        save.where = { region: region.id, ...(at ? { at } : {}) };
        persist(game);
        // Driven into a kingdom the story's just reached: its welcome first.
        const due = dueScene(save);
        if (due) {
          alive = false;
          return game.screens.go(
            sceneScreen(game, due, () =>
              game.screens.go(overworldLoading(game, regionId, at, true)),
            ),
          );
        }
      }
      game.audio.music.stop(0.6);
      game.audio.music.prepare(region.music);
      const token = game.screens.token;
      game
        .createSession({
          scene: "track",
          packageId: (ruined && region.ruinPackageId) || region.packageId,
          rivals: false,
          racer: game.selection.racer,
          freeRoam: true,
        })
        .then((s) => {
          if (!alive || token !== game.screens.token) return s.dispose();
          ready = s;
        })
        .catch((err: Error) => {
          console.error(err);
          if (alive) failed = err.message;
        });
    },
    exit() {
      alive = false;
    },
    frame(dt) {
      t += dt;
      if (failed !== undefined) {
        game.overworld = undefined;
        return game.screens.go(titleScreen(game, true));
      }
      if (ready && t > 0.6) {
        const s = ready;
        ready = undefined;
        alive = false; // the overworld owns the session now
        game.screens.go(overworldScreen(game, s, region, at));
      }
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#1a1210");
      ui.text(region.name.toUpperCase(), ui.W / 2, ui.H / 2 - 12, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      const dots = ".".repeat(1 + (Math.floor(t * 3) % 3));
      ui.text(`ON THE WAY${dots}`, ui.W / 2, ui.H / 2 + 8, {
        color: PAL.cream,
        align: "center",
      });
    },
  };
}

/** The gateways' arches, in the session's scene: two posts and a lintel in the world's
 * colour, a glowing veil between them, and the course's name on a board above. */
function buildGateways(
  session: Session,
  region: Region,
  extra: { x: number; z: number; heading: number; label: string; world: string }[] = [],
) {
  const group = new THREE.Group();
  group.name = "Gateways";
  const you = session.entrants[0]!;
  const stone = new THREE.MeshLambertMaterial({ color: 0x8a7a66 });
  const made: THREE.Material[] = [stone];
  const geos: THREE.BufferGeometry[] = [];
  const marks = [
    ...region.gateways.map((g) => ({
      ...g,
      label: g.label ?? trackById(g.track)?.name ?? g.track,
      world: worldOfTrack(g.track)?.id ?? region.worldId,
    })),
    ...(region.passages ?? []).map((p) => ({
      ...p,
      label: `TO ${(regionById(p.to)?.name ?? p.to).toUpperCase()}`,
      world: regionById(p.to)?.worldId ?? region.worldId,
    })),
    ...extra,
  ];
  for (const g of marks) {
    const color = new THREE.Color(worldById(g.world)?.color ?? "#e0a040");
    const y = you.ground.at(g.x, g.z, PROBE_Y).height;
    const arch = new THREE.Group();
    arch.position.set(g.x, y, g.z);
    arch.rotation.y = g.heading;
    const post = new THREE.BoxGeometry(1.4, 9, 1.4);
    const lintel = new THREE.BoxGeometry(13, 1.6, 1.8);
    const veilG = new THREE.PlaneGeometry(10.6, 7.6);
    geos.push(post, lintel, veilG);
    const trim = new THREE.MeshLambertMaterial({ color });
    const veil = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    made.push(trim, veil);
    for (const sx of [-6, 6]) {
      const p = new THREE.Mesh(post, stone);
      p.position.set(sx, 4.5, 0);
      arch.add(p);
    }
    const l = new THREE.Mesh(lintel, trim);
    l.position.set(0, 9.4, 0);
    arch.add(l);
    const v = new THREE.Mesh(veilG, veil);
    v.position.set(0, 4.4, 0);
    arch.add(v);
    // The name board: a canvas texture.
    const cv = document.createElement("canvas");
    cv.width = 512;
    cv.height = 96;
    const cx = cv.getContext("2d")!;
    cx.fillStyle = "#3a2414";
    cx.fillRect(0, 0, 512, 96);
    cx.strokeStyle = "#e0b040";
    cx.lineWidth = 8;
    cx.strokeRect(4, 4, 504, 88);
    cx.fillStyle = "#f4e8cc";
    cx.font = "bold 44px monospace";
    cx.textAlign = "center";
    cx.textBaseline = "middle";
    cx.fillText(g.label.toUpperCase(), 256, 50, 480);
    const tex = new THREE.CanvasTexture(cv);
    tex.colorSpace = THREE.SRGBColorSpace;
    const boardM = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide });
    const boardG = new THREE.PlaneGeometry(12, 2.25);
    made.push(boardM);
    geos.push(boardG);
    const board = new THREE.Mesh(boardG, boardM);
    board.position.set(0, 11.6, 0);
    arch.add(board);
    group.add(arch);
  }
  session.root.add(group);
  return () => {
    session.root.remove(group);
    for (const m of made) {
      (m as THREE.MeshBasicMaterial).map?.dispose();
      m.dispose();
    }
    for (const g of geos) g.dispose();
  };
}

/** The region as it's being driven now (its state after or before the attack): for the
 * debug tools and the playtest bot. */
export let drivenRegion: Region | undefined;

export function overworldScreen(game: Game, session: Session, region: Region, at?: string): Screen {
  const entry = entryOf(region);
  let clock = 0;
  let removeGateways: (() => void) | undefined;
  let puzzles: ReturnType<typeof regionPuzzles> | undefined;
  let returnGate: ReturnType<typeof regionReturnGate> | undefined;
  let blockers: ReturnType<typeof regionBlockers> | undefined;
  let map: ReturnType<typeof regionMap> | undefined;
  let crew: ReturnType<typeof regionCrew> | undefined;
  let secret: ReturnType<typeof regionSecret> | undefined;
  let villagers: Villagers | undefined;
  /** The gateway (or passage) you're standing in (its card doesn't open again until you
   * leave it). */
  let inside: { x: number; z: number; radius: number } | undefined;
  // Adventure, after the championship: the champion waits beside the ring's start line.
  const champ = game.overworld?.adventure ? challengeOf(game, region) : undefined;
  const challenge =
    champ && region.challenge ? { id: "challenge", radius: 6, ...region.challenge } : undefined;
  // Act V: the return task, inside its yard (you come back out of the yard after it).
  const task = returnOf(game, region);
  const rt = region.returnTask;
  const taskSpot = rt
    ? { id: "return", radius: 4, x: rt.spot.x, z: rt.spot.z, heading: rt.gate.heading }
    : undefined;
  const taskMark = task ? taskSpot : undefined;
  const marks = [
    ...region.gateways,
    ...(region.passages ?? []),
    ...(challenge ? [challenge] : []),
    ...(taskMark ? [taskMark] : []),
  ];

  const screen: Screen = {
    id: "OVERWORLD",
    enter() {
      game.session = session;
      game.ui.interactive = false;
      drivenRegion = region;
      removeGateways = buildGateways(session, region, [
        ...(challenge
          ? [
              {
                ...challenge,
                label: `${challengeOf(game, region)!.name}'S CHALLENGE`,
                world: region.worldId,
              },
            ]
          : []),
        ...(taskMark && task
          ? [{ ...taskMark, label: task.returnTask!.label, world: region.worldId }]
          : []),
      ]);
      puzzles = regionPuzzles(game, session, region);
      returnGate = regionReturnGate(game, session, region);
      blockers = regionBlockers(game, session, region);
      crew = regionCrew(game, session, region);
      secret = regionSecret(game, session, region);
      // The folk who live here, walking about round their homes.
      const land = session.makeGround();
      villagers = createVillagers({
        root: session.root,
        homes: parseHomes(session.entities),
        solids: session.solids,
        ground: (x, z, y) => {
          const g = land.at(x, z, y);
          const bad = g.surface && /water|lava|wall|mud/.test(g.surface);
          return { height: g.height, ok: !bad && g.ny > 0.8 };
        },
      });
      if (import.meta.env.DEV)
        (window as unknown as { kpVillagers?: Villagers }).kpVillagers = villagers;
      map = regionMap(session, region, [
        ...(challenge ? [challenge] : []),
        ...(taskMark ? [taskMark] : []),
      ]);
      // Back out of the gateway you raced, or at the region's spawn.
      const from = [...marks, ...(taskSpot ? [taskSpot] : [])].find((g) => g.id === at);
      const you = session.entrants[0]!;
      if (from) {
        const out = exitSpot(from, (x, z) => session.kartFits(x, z, PROBE_Y));
        session.placeYou(out.x, out.z, out.heading, PROBE_Y);
      } else {
        const sp = region.spawn;
        session.placeYou(sp.x, sp.z, sp.heading, you.state.y + 20);
      }
      void game.audio.music.play(region.music, { fade: 1.2, restart: true });
    },
    resume() {
      game.ui.interactive = false;
      game.audio.music.duck(false);
    },
    exit() {
      removeGateways?.();
      puzzles?.dispose();
      returnGate?.dispose();
      blockers?.dispose();
      crew?.dispose();
      secret?.dispose();
      villagers?.dispose();
      session.dispose();
      if (game.session === session) game.session = undefined;
      game.audio.music.duck(false);
    },
    step(dt, top) {
      if (top) session.update(dt);
    },
    frame(dt, actions, top) {
      clock += dt;
      if (!top) return;
      if (actions.some((a) => a === "pause" || a === "back")) {
        game.screens.push(overworldPause(game, region));
        return;
      }
      const s = session.entrants[0]!.state;
      puzzles?.step(s.x, s.z, dt, clock);
      returnGate?.step(s.x, s.z, dt);
      blockers?.step(s.x, s.z, dt, clock);
      secret?.step(s.x, s.z, dt);
      villagers?.step(dt, clock, { x: s.x, z: s.z, speed: s.speed });
      if (inside && !inGateway(inside, s.x, s.z, 3)) inside = undefined;
      if (!inside) {
        const g = region.gateways.find((g) => inGateway(g, s.x, s.z));
        const p = (region.passages ?? []).find(
          (p) => inGateway(p, s.x, s.z) && !blockers?.shut(p.id),
        );
        const ch = challenge && inGateway(challenge, s.x, s.z) ? challenge : undefined;
        const tk = taskMark && inGateway(taskMark, s.x, s.z) ? taskMark : undefined;
        if (p && !g && passageOpen(game, p)) {
          inside = p;
          game.sounds.confirm();
          return throughPassage(game, p);
        }
        if (g || p || ch || tk) {
          inside = g ?? p ?? ch ?? tk;
          s.speed = 0;
          game.sounds.confirm();
          game.screens.push(
            g
              ? gatewayCard(game, region, g)
              : p
                ? passageCard(game, p)
                : ch
                  ? challengeCard(game, region)
                  : returnCard(game, region),
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
      drawHud(ui, session, entry, true, undefined, clock);
      const w = Math.min(170, ui.textWidth(region.name.toUpperCase()) + 16);
      ui.panel(6, 6, w, 18, "wood", "gold");
      ui.text(region.name.toUpperCase(), 6 + w / 2, 11, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      // Adventure: what to do next, under the plaque.
      const goal = game.overworld?.adventure ? storyGoal(game, region) : undefined;
      if (goal) ui.text(goal, 8, 28, { color: PAL.cream, outline: PAL.shadow });
      puzzles?.draw(ui);
      returnGate?.draw(ui);
      blockers?.draw(ui);
      secret?.draw(ui);
      map?.draw(ui, clock, storyTarget(game, region));
      // A villager you've stopped by: their name and what they say (placeholder lines:
      // the dialogue comes later).
      const v = villagers?.near();
      if (v) {
        const w = Math.min(ui.W - 40, 300);
        const lines = wrap(v.line, w - 16).slice(0, 2);
        const h = 20 + lines.length * 9;
        const x = Math.round(ui.W / 2 - w / 2);
        const y = ui.H - h - 30;
        ui.panel(x, y, w, h, "parchment", "ink");
        ui.text(v.name, x + 8, y + 5, { color: PAL.coral, outline: PAL.ink });
        lines.forEach((l, i) => ui.text(l, x + 8, y + 16 + i * 9, { color: PAL.ink }));
      }
    },
  };
  // (The arch you came out of counts as the one you're in, so its card doesn't reopen.)
  inside = [...marks, ...(taskSpot ? [taskSpot] : [])].find((g) => g.id === at);
  return screen;
}

/** Adventure: what the story asks of this region's gateways now. `go` is undefined
 * when this gateway has nothing to race yet (the championship is at another one). */
interface StoryOffer {
  /** The course the card shows. */
  track: string;
  note: string;
  go?: () => void;
}

/** One of a championship's courses at its gateway (Blake, Oct 26: win all four, in any
 * order; no Trophy Race cup): race it, or race it again once won. */
function courseOffer(
  game: Game,
  region: Region,
  g: Gateway,
  id: KingdomId | "dragon_final",
  title: string,
): StoryOffer | undefined {
  const s = adventureOf(game).save;
  const tracks = championshipTracks(id, (t) => Boolean(trackById(t)));
  if (!tracks.includes(g.track)) return undefined;
  const n = winsOf(s, id);
  const won = Boolean(s.wins[g.track]);
  return {
    track: g.track,
    note: won
      ? `${title} · WON (${n}/${tracks.length}) · RACE IT AGAIN`
      : `${title} · WIN HERE (${n}/${tracks.length} WON, ANY ORDER)`,
    go: () => {
      game.overworld = { region: region.id, at: g.id, adventure: true };
      launch(game, { kind: "race", kingdom: id, track: g.track }, g.track);
    },
  };
}

/** Adventure: the Dragon Kingdom's gateways, by where the story is (adventure.ts's
 * board for it does the same): the first visit's championship, the kingdom in ruins
 * while you go home, the last championship over its ruined courses, then the King. */
function dragonOffer(game: Game, region: Region, g: Gateway): StoryOffer | undefined {
  const s = adventureOf(game).save;
  const p = dragonPhase(s);
  const king = DRAGON.king.name.toUpperCase();
  if (g.king) {
    if (p !== "king" && p !== "done")
      return { track: g.track, note: `${king} WAITS IN HIS CITADEL. NOT YET` };
    return {
      track: g.track,
      note: p === "done" ? `${king} IS BEATEN · RACE HIM AGAIN` : `RACE ${king}!`,
      go: () => {
        game.overworld = { region: region.id, at: g.id, adventure: true };
        launch(game, { kind: "king", chosen: s.kingLost }, DRAGON.king.track);
      },
    };
  }
  if (!DRAGON.courses.some((c) => c.track === g.track)) return undefined;
  if (p === "locked") return { track: g.track, note: "NOT REACHED YET" };
  if (p === "first") return courseOffer(game, region, g, "dragon", "THE CHAMPIONSHIP");
  if (p === "return") {
    const left = KINGDOMS.filter((k) => !s.returns[k.id]).length;
    return {
      track: g.track,
      note: `THE KINGDOM LIES IN RUINS. GO HOME: ${left} TASK${left === 1 ? "" : "S"} LEFT IN THE FOUR KINGDOMS`,
    };
  }
  const ruins = DRAGON.courses.map((c) => coinCourse(c, (id) => Boolean(trackById(id))).track);
  const at = DRAGON.courses.findIndex((c) => c.track === g.track);
  if (p === "final")
    return courseOffer(
      game,
      region,
      { ...g, track: ruins[at]! },
      "dragon_final",
      "THE LAST CHAMPIONSHIP",
    );
  return {
    track: ruins[at]!,
    note: p === "king" ? `${king} WAITS IN HIS CITADEL` : "THE KINGDOMS ARE FREE · RACE IT AGAIN",
    go:
      p === "done"
        ? () => {
            game.overworld = { region: region.id, at: g.id, adventure: true };
            game.selection.trackId = ruins[at]!;
            game.selection.mode = "race";
            game.screens.go(loadingScreen(game));
          }
        : undefined,
  };
}

function storyOffer(game: Game, region: Region, g: Gateway): StoryOffer | undefined {
  if (region.kingdom === "dragon") return dragonOffer(game, region, g);
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  const course = k?.courses.find((c) => c.track === g.track);
  if (!k || (!course && !g.boss)) return undefined;
  const a = adventureOf(game);
  const s = a.save;
  const ph = kingdomPhase(s, k);
  const back = () => (game.overworld = { region: region.id, at: g.id, adventure: true });
  if (g.boss) {
    const name = k.boss!.name.toUpperCase();
    if (ph !== "boss" && ph !== "done")
      return { track: g.track, note: `${name}'S LAIR. FIND THE MAP FIRST (${piecesOf(s, k)}/4)` };
    return {
      track: g.track,
      note: ph === "done" ? `${name} IS BEATEN · RACE AGAIN` : `RACE ${name}!`,
      go: () => {
        back();
        game.screens.go(
          sceneScreen(game, k.scenes.boss, () =>
            launch(game, { kind: "boss", kingdom: k.id }, k.boss!.track),
          ),
        );
      },
    };
  }
  if (!course) return undefined;
  if (ph === "locked") return { track: g.track, note: "NOT REACHED YET" };
  if (ph === "duel")
    return {
      track: g.track,
      note: `${k.champion!.name.toUpperCase()} IS WAITING BY THE START LINE ON THE RING`,
    };
  if (ph === "championship") return courseOffer(game, region, g, k.id, "THE CHAMPIONSHIP");
  // After the championship: the ruined course and its map fragments.
  const cc = coinCourse(course, (id) => Boolean(trackById(id)));
  const found = Boolean(s.pieces[course.track]);
  return {
    track: cc.track,
    note: found
      ? "ITS MAP PIECE IS FOUND · RACE IT AGAIN"
      : "THE RUIN: GATHER ITS 4 MAP FRAGMENTS AND FINISH 1ST",
    go: () => {
      back();
      launch(game, { kind: "coins", kingdom: k.id, course: course.track, ...cc }, cc.track);
    },
  };
}

/** Adventure: where the story wants you next in this region (the map marks it, and the
 * playtest bot drives to it): the champion's challenge, the return task, the gateway with
 * the next race that moves the story on, or the way on or back towards the kingdom the
 * story's at. */
export function storyTarget(
  game: Game,
  region: Region,
): { id: string; x: number; z: number; radius: number; heading: number } | undefined {
  if (!game.overworld?.adventure) return undefined;
  const s = adventureOf(game).save;
  if (region.challenge && challengeOf(game, region))
    return { id: "challenge", radius: 6, ...region.challenge };
  if (returnOf(game, region) && region.returnTask)
    return {
      id: "return",
      radius: 4,
      ...region.returnTask.spot,
      heading: region.returnTask.gate.heading,
    };
  for (const g of region.gateways) {
    const o = storyOffer(game, region, g);
    if (o?.go && !/AGAIN/.test(o.note)) return g;
  }
  // The way on or back, towards the kingdom the story is at.
  const here = storyPlace(region, STORY_ORDER);
  const dp = dragonPhase(s);
  const pending = KINGDOMS.find((k) => kingdomPhase(s, k) !== "done");
  const goal: KingdomId = pending
    ? pending.id
    : dp === "return"
      ? (KINGDOMS.find((k) => !s.returns[k.id])?.id ?? "dragon")
      : "dragon";
  const there = STORY_ORDER.indexOf(goal);
  if (there === here) return undefined;
  const p = (region.passages ?? []).find((p) => {
    const to = regionById(p.to);
    const ti = to ? storyPlace(to, STORY_ORDER) : -1;
    const open = !p.opensAfter || Boolean(s.bosses[p.opensAfter]);
    return open && (there > here ? ti > here : ti < here);
  });
  return p;
}

/** Adventure: the champion who'll race you 1 on 1 here now (their challenge is due). */
function challengeOf(game: Game, region: Region) {
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  return k && region.challenge && kingdomPhase(adventureOf(game).save, k) === "duel"
    ? { name: k.champion!.name.toUpperCase(), kingdom: k.id }
    : undefined;
}
/** The champion's challenge: 1 on 1, once round the region's ring. */
function challengeCard(game: Game, region: Region): Screen {
  const ch = challengeOf(game, region)!;
  const go = () => {
    game.overworld = { region: region.id, at: "challenge", adventure: true };
    launch(game, { kind: "duel", kingdom: ch.kingdom }, region.packageId);
  };
  const menu = new VMenu(
    game,
    [
      { label: "RACE!", action: go },
      { label: "NOT YET", action: () => game.screens.pop() },
    ],
    () => game.screens.pop(),
  );
  return {
    id: "GATEWAY",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.4);
      const w = 260;
      const h = 100;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = Math.round(ui.H / 2 - h / 2) - 8;
      ui.panel(x, y, w, h, "parchment", "ink");
      ui.text(`${ch.name}'S CHALLENGE`, ui.W / 2, y + 8, {
        scale: 2,
        color: PAL.coral,
        outline: PAL.ink,
        align: "center",
      });
      ui.text(`1 ON 1, ONCE ROUND ${region.name.toUpperCase()}.`, ui.W / 2, y + 30, {
        color: PAL.ink,
        align: "center",
      });
      ui.text(`BEAT ${ch.name} AND THEY JOIN YOUR CREW.`, ui.W / 2, y + 40, {
        color: PAL.inkSoft,
        align: "center",
      });
      menu.draw(ui, x + 60, y + h - 40, w - 120, 14, 4);
    },
  };
}

/** Adventure: the region's goal, for the HUD. */
function storyGoal(game: Game, region: Region): string | undefined {
  if (!region.kingdom && !region.journey) return undefined;
  return objective(adventureOf(game).save);
}

/** A course's card at its gateway: standard or ruined, your best times, GO or back.
 * (Adventure: what the story asks there instead.) */
function gatewayCard(game: Game, region: Region, g: Gateway): Screen {
  const story = game.overworld?.adventure ? storyOffer(game, region, g) : undefined;
  const std = trackById(story?.track ?? g.track)!;
  const ruin = !story && std.ruin ? trackById(std.ruin) : undefined;
  const choices = ruin ? [std, ruin] : [std];
  let pick = 0;
  let clicked = -1;
  const go = () => {
    if (story) return story.go?.();
    const e = choices[pick]!;
    game.overworld = { region: region.id, at: g.id, ruined: game.overworld?.ruined };
    game.selection.trackId = e.id;
    game.selection.mode = "race";
    game.screens.go(loadingScreen(game));
  };
  const menu = new VMenu(
    game,
    [
      ...(story && !story.go ? [] : [{ label: "GO!", action: go }]),
      { label: "BACK OUT", action: () => game.screens.pop() },
    ],
    () => game.screens.pop(),
  );
  return {
    id: "GATEWAY",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      if (clicked >= 0) {
        const i = clicked;
        clicked = -1;
        if (i !== pick) {
          pick = i;
          game.sounds.move();
        }
      }
      for (const a of actions)
        if ((a === "left" || a === "right") && choices.length > 1) {
          pick = (pick + 1) % choices.length;
          game.sounds.move();
        }
      menu.handle(actions);
    },
    draw(ui: UiLayer) {
      ui.dim(0.4);
      const w = 240;
      const h = 168;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = Math.round(ui.H / 2 - h / 2) - 8;
      ui.panel(x, y, w, h, "parchment", "ink");
      const e = choices[pick]!;
      ui.text((g.label ?? std.name).toUpperCase(), ui.W / 2, y + 8, {
        scale: 2,
        color: PAL.coral,
        outline: PAL.ink,
        align: "center",
      });
      // Standard / ruined tabs (Adventure: the story's note instead).
      if (story) ui.text(story.note, ui.W / 2, y + 31, { color: "#8a2a1a", align: "center" });
      else
        choices.forEach((c, i) => {
          const tw = 90;
          const tx = ui.W / 2 + (i - (choices.length - 1) / 2) * (tw + 6) - tw / 2;
          const r = ui.button(tx, y + 28, tw, 14, c === std ? "STANDARD" : "RUINED", {
            focused: i === pick,
          });
          if (r.clicked) clicked = i;
        });
      const lines = wrap(e.description.toUpperCase(), w - 20).slice(0, 4);
      lines.forEach((l, i) => ui.text(l, x + 10, y + 50 + i * 9, { color: PAL.ink }));
      const rec = loadRecords()[e.id];
      ui.text(`BEST TRIAL ${fmt(rec?.best.timeTrial)}`, x + 10, y + 92, { color: PAL.inkSoft });
      ui.text(`BEST LAP   ${fmt(rec?.bestLap)}`, x + 10, y + 101, { color: PAL.inkSoft });
      menu.draw(ui, x + 50, y + 116, w - 100, 16, 4);
      hints(ui, [
        ...(choices.length > 1 ? ([["◀▶", "STANDARD / RUINED"]] as [string, string][]) : []),
        ["ENTER", "SELECT"],
        ["ESC", "BACK OUT"],
      ]);
    },
  };
}

/** Is the way on open (Adventure: once its dragon's beaten)? */
function passageOpen(game: Game, p: Passage) {
  const s = game.overworld?.adventure ? adventureOf(game).save : undefined;
  return !s || !p.opensAfter || freeRoam() || Boolean(s.bosses[p.opensAfter]);
}

/** On through a passage: the region (or the journey) beyond loads. */
function throughPassage(game: Game, p: Passage) {
  const story = game.overworld?.adventure;
  game.overworld = {
    region: p.to,
    at: p.toPassage,
    adventure: story,
    ruined: game.overworld?.ruined,
  };
  game.screens.go(overworldLoading(game, p.to, p.toPassage, story));
}

/** A passage's card: what's still in the way (an open passage is a loading zone: you go
 * straight on, Blake, Oct 26). */
function passageCard(game: Game, p: Passage): Screen {
  const open = passageOpen(game, p);
  const go = () => throughPassage(game, p);
  const menu = new VMenu(
    game,
    [
      ...(open ? [{ label: "ON YOU GO", action: go }] : []),
      { label: "BACK", action: () => game.screens.pop() },
    ],
    () => game.screens.pop(),
  );
  return {
    id: "GATEWAY",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.4);
      const w = 260;
      const h = 96;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = Math.round(ui.H / 2 - h / 2) - 8;
      ui.panel(x, y, w, h, "parchment", "ink");
      ui.text(p.label, ui.W / 2, y + 10, { color: PAL.coral, outline: PAL.ink, align: "center" });
      const why = open ? (regionById(p.to)?.name ?? p.to).toUpperCase() : (p.locked ?? "NOT YET");
      wrap(why, w - 20)
        .slice(0, 3)
        .forEach((l, i) =>
          ui.text(l, ui.W / 2, y + 26 + i * 9, { color: PAL.ink, align: "center" }),
        );
      menu.draw(ui, x + 60, y + h - 40, w - 120, 14, 4);
      hints(ui, [
        ["ENTER", "SELECT"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

function overworldPause(game: Game, region: Region): Screen {
  const leave = () => {
    game.overworld = undefined;
    game.screens.go(titleScreen(game, true));
  };
  const story = game.overworld?.adventure && region.kingdom ? region.kingdom : undefined;
  const menu = new VMenu(
    game,
    [
      { label: "RESUME", action: () => resume() },
      // Adventure: the kingdom's board (every step of its story, the ones the region
      // doesn't have yet: the map, the dragon, the task) and the world map.
      ...(game.overworld?.adventure
        ? [
            {
              // (Any of your crew can drive: Blake, Oct 26.)
              label: "CHANGE RACER",
              action: () => {
                game.overworld = undefined;
                game.screens.go(characterSelect(game, { swap: true }));
              },
            },
          ]
        : []),
      ...(story
        ? [
            {
              label: "KINGDOM BOARD",
              action: () => {
                game.overworld = undefined;
                game.screens.go(kingdomScreen(game, story));
              },
            },
          ]
        : []),
      // Dev free roam: the region before or after its dragon's attack.
      ...(!story && region.ruinPackageId
        ? [
            {
              label: game.overworld?.ruined ? "SHOW IT STANDARD" : "SHOW IT RUINED",
              action: () => {
                game.overworld = { region: region.id, ruined: !game.overworld?.ruined };
                game.screens.go(overworldLoading(game, region.id, undefined, false));
              },
            },
          ]
        : []),
      // Dev builds: every testing tool on one page (insta-win, go anywhere, warps, story
      // jumps, scenes; the world map in Adventure: no world map to hop from otherwise,
      // every world is reached by driving there).
      ...(import.meta.env.DEV
        ? [
            {
              label: "DEV TOOLS",
              action: () => {
                const adventure = Boolean(game.overworld?.adventure);
                const here = { ...game.overworld! };
                const back = () => {
                  game.overworld = here;
                  game.screens.go(overworldLoading(game, region.id, undefined, adventure));
                };
                const extra = adventure
                  ? [
                      {
                        label: "WORLD MAP",
                        action: () =>
                          journeyBegun(adventureOf(game).save)
                            ? game.screens.go(adventureHub(game))
                            : peekWorldMap(game),
                      },
                    ]
                  : [];
                game.screens.go(devMenu(game, { back, extra }));
              },
            },
          ]
        : []),
      { label: "OPTIONS", action: () => game.screens.push(optionsScreen(game)) },
      {
        label: "MAIN MENU",
        action: () =>
          game.screens.push(confirmDialog(game, "LEAVE THE OVERWORLD FOR THE MAIN MENU?", leave)),
      },
    ],
    () => resume(),
  );
  function resume() {
    game.sounds.unpause();
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
      const w = 140;
      const x = ui.W / 2 - w / 2;
      ui.panel(x, 50, w, 46 + menu.items.length * 24, "wood", "gold");
      ui.text("PAUSED", ui.W / 2, 60, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text(region.name.toUpperCase(), ui.W / 2, 78, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      menu.draw(ui, x + 14, 92, w - 28, 18, 6);
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "SELECT"],
        ["ESC", "RESUME"],
      ]);
    },
  };
}

/** Dev builds: every overworld region (◀▶: standard or ruined) and every journey between
 * them, to load straight away (Blake, Oct 26). In an Adventure file the story carries on
 * from wherever you land; a region warped to keeps its state until warped again. */
export function devWarp(game: Game): Screen {
  const places = REGIONS.filter((r) => r.kingdom || r.journey);
  let ruined = false;
  const adventure = game.overworld?.adventure ?? false;
  const menu = new VMenu(
    game,
    places.map((r) => ({
      label: r.journey ? `  ${r.name.toUpperCase()}` : r.name.toUpperCase(),
      action: () => {
        game.overworld = { region: r.id, adventure, ruined: ruined && !adventure };
        game.screens.go(
          overworldLoading(game, r.id, undefined, adventure, r.ruinPackageId ? ruined : undefined),
        );
      },
    })),
    () => game.screens.pop(),
  );
  return {
    id: "DEV_WARP",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      if (actions.includes("left") || actions.includes("right")) {
        ruined = !ruined;
        game.sounds.move();
      }
      menu.handle(actions.filter((a) => a !== "left" && a !== "right"));
    },
    draw(ui) {
      ui.dim(0.5);
      const w = 220;
      const x = Math.round(ui.W / 2 - w / 2);
      const h = 52 + places.length * 15;
      const y = Math.round(ui.H / 2 - h / 2);
      ui.panel(x, y, w, h, "wood", "gold");
      ui.text("WARP (DEV)", ui.W / 2, y + 8, {
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text(ruined ? "◀ RUINED ▶" : "◀ STANDARD ▶", ui.W / 2, y + 22, {
        color: ruined ? PAL.coral : PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      menu.draw(ui, x + 14, y + 36, w - 28, 13, 2);
      hints(ui, [
        ["◀▶", "STANDARD / RUINED"],
        ["ENTER", "GO"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
