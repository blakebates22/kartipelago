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
  regionById,
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
  adventureOf,
  freeRoam,
  kingdomScreen,
  launch,
  sceneScreen,
} from "./adventure";
import { kingdomById } from "../adventure/data";
import { coinCourse, kingdomPhase, objective, piecesOf } from "../adventure/progress";

/** Where the overworld is: the region, and the gateway you went into (you come back
 * out of it). */
export interface OverworldState {
  region: string;
  at?: string;
  /** Adventure mode: the story runs through the region (the gateways open its races). */
  adventure?: boolean;
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
): Screen {
  const region = regionById(regionId)!;
  let ready: Session | undefined;
  let failed: string | undefined;
  let alive = true;
  let t = 0;
  return {
    id: "OVERWORLD_LOADING",
    seeThrough: false,
    enter() {
      game.ui.interactive = false;
      game.overworld = { region: region.id, at, adventure: adventure && Boolean(region.kingdom) };
      game.audio.music.stop(0.6);
      game.audio.music.prepare(region.music);
      const token = game.screens.token;
      game
        .createSession({
          scene: "track",
          packageId: region.packageId,
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

export function overworldScreen(game: Game, session: Session, region: Region, at?: string): Screen {
  const entry = entryOf(region);
  let clock = 0;
  let removeGateways: (() => void) | undefined;
  /** The gateway (or passage) you're standing in (its card doesn't open again until you
   * leave it). */
  let inside: { x: number; z: number; radius: number } | undefined;
  // Adventure, after the championship: the champion waits beside the ring's start line.
  const champ = game.overworld?.adventure ? challengeOf(game, region) : undefined;
  const challenge =
    champ && region.challenge ? { id: "challenge", radius: 6, ...region.challenge } : undefined;

  const screen: Screen = {
    id: "OVERWORLD",
    enter() {
      game.session = session;
      game.ui.interactive = false;
      removeGateways = buildGateways(
        session,
        region,
        challenge
          ? [
              {
                ...challenge,
                label: `${challengeOf(game, region)!.name}'S CHALLENGE`,
                world: region.worldId,
              },
            ]
          : [],
      );
      // Back out of the gateway you raced, or at the region's spawn.
      const from = [
        ...region.gateways,
        ...(region.passages ?? []),
        ...(challenge ? [challenge] : []),
      ].find((g) => g.id === at);
      const you = session.entrants[0]!;
      if (from) {
        const x = from.x + Math.sin(from.heading) * (from.radius + 6);
        const z = from.z + Math.cos(from.heading) * (from.radius + 6);
        session.placeYou(x, z, from.heading, PROBE_Y);
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
      if (inside && !inGateway(inside, s.x, s.z, 3)) inside = undefined;
      if (!inside) {
        const g = region.gateways.find((g) => inGateway(g, s.x, s.z));
        const p = (region.passages ?? []).find((p) => inGateway(p, s.x, s.z));
        const ch = challenge && inGateway(challenge, s.x, s.z) ? challenge : undefined;
        if (g || p || ch) {
          inside = g ?? p ?? ch;
          s.speed = 0;
          game.sounds.confirm();
          game.screens.push(
            g
              ? gatewayCard(game, region, g)
              : p
                ? passageCard(game, p)
                : challengeCard(game, region),
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
    },
  };
  // (The arch you came out of counts as the one you're in, so its card doesn't reopen.)
  inside = [...region.gateways, ...(region.passages ?? []), ...(challenge ? [challenge] : [])].find(
    (g) => g.id === at,
  );
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

function storyOffer(game: Game, region: Region, g: Gateway): StoryOffer | undefined {
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
  if (ph === "championship") {
    const cup = game.trophy && a.run?.kind === "cup" ? game.trophy : undefined;
    const raced = cup?.raced ?? 0;
    const next = k.courses[raced]!;
    const n = `RACE ${raced + 1} OF ${k.courses.length}`;
    if (next.track !== g.track)
      return {
        track: g.track,
        note: `THE CHAMPIONSHIP'S ${n} IS AT ${(trackById(next.track)?.name ?? next.track).toUpperCase()}`,
      };
    return {
      track: g.track,
      note: `THE CHAMPIONSHIP · ${n}`,
      go: () => {
        back();
        if (!cup) {
          const tracks = k.courses.map((c) => c.track);
          return launch(game, { kind: "cup", kingdom: k.id }, tracks[0]!, {
            name: k.name,
            worldId: worldById(k.worldId)!.id,
            tracks,
          });
        }
        game.selection.trackId = next.track;
        game.selection.mode = "race";
        game.screens.go(loadingScreen(game));
      },
    };
  }
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
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (!k) return undefined;
  const a = adventureOf(game);
  if (kingdomPhase(a.save, k) === "championship") {
    const raced = game.trophy && a.run?.kind === "cup" ? game.trophy.raced : 0;
    const next = trackById(k.courses[raced]!.track);
    return `THE CHAMPIONSHIP, RACE ${raced + 1} OF ${k.courses.length}: ${(next?.name ?? "").toUpperCase()}`;
  }
  return objective(a.save);
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
    game.overworld = { region: region.id, at: g.id };
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

/** A passage's card: on to the next region, or what's still in the way. */
function passageCard(game: Game, p: Passage): Screen {
  const story = game.overworld?.adventure;
  const s = story ? adventureOf(game).save : undefined;
  const open = !s || !p.opensAfter || freeRoam() || Boolean(s.bosses[p.opensAfter]);
  const go = () => {
    game.overworld = { region: p.to, at: p.toPassage, adventure: story };
    game.screens.go(overworldLoading(game, p.to, p.toPassage, story));
  };
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
      ...(story
        ? [
            {
              label: "KINGDOM BOARD",
              action: () => {
                game.overworld = undefined;
                game.screens.go(kingdomScreen(game, story));
              },
            },
            { label: "WORLD MAP", action: () => game.screens.go(adventureHub(game)) },
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
      ui.panel(x, 50, w, story ? 168 : 120, "wood", "gold");
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
