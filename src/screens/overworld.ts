/**
 * The overworld (src/overworld/regions.ts): drive a region freely, and drive into a
 * course's gateway to race it. Adventure runs its story through the regions (the
 * approved story, Blake, Oct 27: claude/kartipelago-story.md): their gateways open the
 * story's races, each kingdom's smugglers' cave its underground games and the tunnel on,
 * and the race the story wants next starts where you are, after its scene.
 *
 * - OVERWORLD_LOADING: builds the region's session (free roam: no countdown, laps,
 *   clock or rivals) and drops you at its spawn, or back out of the mark you went in by.
 * - OVERWORLD: free roam. Each gateway is an arch with its course's name over it; drive
 *   in and its card opens. After the race you come back out of the same arch.
 * - GATEWAY: the course's card (standard or ruined, your best times), or the story's.
 *
 * Leaving it clears game.overworld, so races go back to their usual menus.
 */
import type { Folk } from "../render/villager";
import * as THREE from "three";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { loadRecords } from "../app/records";
import {
  inGateway,
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
import { reviewScreen } from "../review/reviewScreen";
import { worldById, worldOfTrack } from "../game/worlds";
import { minigameById } from "../game/minigames";
import { wrap } from "../ui/font";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { loadingScreen } from "./loading";
import { titleScreen } from "./title";
import { confirmDialog, drawHud } from "./race";
import { optionsScreen } from "./options";
import { minigameLoading } from "./minigames";
import {
  adventureOf,
  crewMenu,
  devMenu,
  freeRoam,
  goHome,
  hereIn,
  launch,
  persist,
  portrait,
  portraitSlot,
  sceneScreen,
  youOf,
} from "./adventure";
import { CAST } from "../adventure/scenes";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import {
  DRAGON,
  RAGE,
  STORY_ORDER,
  kingdomById,
  sceneOf,
  nameOf,
  type Kingdom,
  type KingdomId,
} from "../adventure/data";
import { Racer as RacerView } from "../render/racers/racer";
import type { RacerId } from "../render/racers/designs";
import {
  BEFORE_KING,
  HEART,
  UNDERGROUND,
  challengeScene,
  coursesOf,
  crewOf,
  dragonPhase,
  dueScene,
  gamesFinished,
  kingdomPhase,
  newStoneScene,
  objective,
  regionLook,
  shardCourse,
  shardsOf,
  storyKingdom,
  winsOf,
} from "../adventure/progress";
import { gateSolid } from "../overworld/gates";
import { createChestView, createObstacleView } from "../overworld/yardView";
import { createVillagers, parseHomes, type Villagers } from "../overworld/villagers";
import { exitSpot, frontSpot, roadSpot } from "../overworld/exits";
import { challengeStaged, stageAt } from "../adventure/staged";
import type { VillagerView } from "../render/villager";
import { createGuardView } from "../render/people";
import {
  createBannerView,
  createPactStoneView,
  type PropView,
  type StoneState,
} from "../render/storyProps";
import { createGatewayArch, type ArchTheme } from "../render/gatewayArch";
import { instaWin } from "../debug/devFlags";
import {
  airAt,
  airOf,
  airWeights,
  areaAmbient,
  courseAmbient,
  mixAir,
  type AmbientSpec,
  type Air,
  type AirSpot,
} from "../overworld/air";
import { createAmbientFx } from "../render/ambientFx";
import { packageBase } from "../game/session";
import { parseLook, type TrackLook } from "../world/trackPackage";

/** Where the overworld is: the region, and the mark you went into (you come back out of
 * it; `<id>:front`: in front of it, facing it; `@x,z,heading`: just there). */
export interface OverworldState {
  region: string;
  at?: string;
  /** Adventure mode: the story runs through the region. */
  adventure?: boolean;
  /** Dev free roam: drive the regions as they are after the Rage. */
  ruined?: boolean;
}

/** Dev builds: a region warped to as standard or ruined stays so (whatever the story
 * says) until warped again (the warp list: devWarp). */
const devState = new Map<string, boolean>();

/** Is the region ruined now (Adventure: by the story; else the free roam's choice)? */
export function regionRuined(game: Game, regionId: string, adventure: boolean): boolean {
  const r = regionById(regionId);
  if (!r?.ruinPackageId) return false;
  const dev = import.meta.env.DEV ? devState.get(r.id) : undefined;
  if (dev !== undefined) return dev;
  if (adventure && r.kingdom) return regionLook(adventureOf(game).save, r.kingdom) === "ruined";
  return Boolean(game.overworld?.ruined);
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
  const joined = (story ? crewOf(story) : k ? [k.champion.look] : []).filter(
    (r) => r !== game.selection.racer,
  );
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const made: RacerView[] = [];
  const park = (look: RacerId, x: number, z: number, heading: number, alt = false) => {
    const r = new RacerView(look, { seed: made.length * 13 + 3, alt });
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
  if (waiting && region.challenge && k) {
    const c = region.challenge;
    const rx = Math.cos(c.heading);
    const rz = -Math.sin(c.heading);
    park(k.champion.look, c.x + rx * 9, c.z + rz * 9, c.heading, k.champion.look === youOf(game));
  }
  return {
    dispose() {
      for (const r of made) r.dispose(session.root);
    },
  };
}

/** Dev free roam: secrets found, for this visit. */
const devSecrets = new Set<string>();

/** A region's secret (dev free roam only, for now: Adventure has no tools to open them
 * any more): its yard's obstacle (open in the ruined region), the chest inside. */
function regionSecret(game: Game, session: Session, region: Region) {
  const sc = region.secret;
  if (!sc || game.overworld?.adventure) return undefined;
  const open = Boolean(game.overworld?.ruined);
  const found = () => devSecrets.has(region.id);
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const view = createObstacleView(session.root, sc.obstacle, sc.gate, groundAt);
  view.shown = !open;
  if (!open) session.solids.push(gateSolid({ gate: sc.gate }, groundAt(sc.gate.x, sc.gate.z)));
  const chest = createChestView(session.root, sc.spot, sc.gate.heading, groundAt);
  chest.open = found();
  let banner: { text: string; t: number } | undefined;
  return {
    step(x: number, z: number, dt: number) {
      if (banner && (banner.t -= dt) <= 0) banner = undefined;
      if (open && !found() && Math.hypot(x - sc.spot.x, z - sc.spot.z) < 3.5) {
        devSecrets.add(region.id);
        chest.open = true;
        game.sounds.keyFound();
        const of = REGIONS.filter((r) => r.secret).length;
        banner = { text: `A SECRET CHEST! (${devSecrets.size} OF ${of} FOUND)`, t: 4 };
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

// ---------------------------------------------------------------- the smugglers' caves

/** What the smugglers' cave is now (Adventure): shut (with what the guards say), the
 * underground games (only for the kingdom's champion, or a racer who's them), or the
 * tunnel on. */
interface CaveNow {
  k: Kingdom;
  mode: "shut" | "games" | "tunnel";
  /** What the guards say at the gate. */
  say: string;
  /** Said in a little scene of its own as you come up (Blake, Oct 29: "when I run into
   * the sketchy guards before I have rex unlocked, i want it to be a proper cutscene"):
   * the camera on the guards, each line in the text box with the guard's face. Which
   * guard says it (0 or 1), and what. */
  talk?: [number, string][];
}

function caveOf(game: Game, region: Region): CaveNow | undefined {
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (!k || !region.cave || !game.overworld?.adventure) return undefined;
  const s = adventureOf(game).save;
  const ph = kingdomPhase(s, k);
  const champ = k.champion.name.toUpperCase();
  const dragon = k.boss.name.toUpperCase();
  const isChamp = game.selection.racer === k.champion.look || youOf(game) === k.champion.look;
  if (freeRoam())
    return {
      k,
      mode: ph === "underground" || ph === "duel" || ph === "games" ? "games" : "tunnel",
      say: "",
    };
  switch (ph) {
    case "underground":
      return isChamp
        ? { k, mode: "games", say: `"${champ}! COME ON IN."` }
        : {
            k,
            mode: "shut",
            // (Blake, Oct 28: the smugglers say it, not a menu hint.)
            say: `"NEVER SEEN YOU BEFORE. WE OPEN UP FOR ${champ}'S CREW, AND ONLY WITH ${champ} AT THE WHEEL."`,
            talk: [
              [0, "WHOA, WHOA. HOLD IT RIGHT THERE. NEVER SEEN YOU BEFORE."],
              [1, `THIS CAVE OPENS FOR ${champ}'S CREW. AND ONLY WITH ${champ} AT THE WHEEL.`],
              [0, `NO ${champ}, NO GAMES. GO ON, BEAT IT.`],
            ],
          };
    case "escaped":
    case "restored":
      return {
        k,
        mode: "tunnel",
        say: `"THE TUNNEL'S YOURS. ON TO THE ${nameOf(k.next).toUpperCase()}."`,
      };
    case "waiting":
    case "shards":
    case "boss":
      return {
        k,
        mode: "shut",
        say: `${dragon}'S GUARDS HOLD THE TUNNEL NOW. BEAT ${dragon} FIRST.`,
      };
    default:
      return { k, mode: "shut", say: `SKETCHY GUARDS: "NEVER HEARD OF YOU. GET LOST."` };
  }
}

/** The cave's mark: its mouth inside the yard, facing out through the gate. */
function caveMark(region: Region) {
  const c = region.cave!;
  return {
    id: "cave",
    radius: 4,
    x: c.spot.x,
    z: c.spot.z,
    heading: Math.atan2(c.gate.x - c.spot.x, c.gate.z - c.spot.z),
  };
}

/** The cave in the scene: two sketchy guards at the yard's gate (solid while it's shut:
 * they stand across it), a dark mouth inside, and what the guards say as you come up. */
function regionCave(game: Game, session: Session, region: Region) {
  const now = caveOf(game, region);
  if (!now) return undefined;
  const c = region.cave!;
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const out = c.gate.heading;
  const rx = Math.cos(out);
  const rz = -Math.sin(out);
  const shut = now.mode === "shut";
  const folk = ({ valley: "valley", snow: "snow", desert: "desert", beach: "beach" } as const)[
    now.k.id as "valley"
  ];
  // Shut: the guards stand across the gate; open: either side of it. Out in front of the
  // gate, clear of its walls and posts (Blake, valley polish 14, note 4: "both smugglers
  // guard are in the wall"): the first spot out from the gate with room to stand.
  const off = shut ? 1.6 : 3.8;
  const fx = Math.sin(out);
  const fz = Math.cos(out);
  const guards: { v: VillagerView; x: number; z: number }[] = [-1, 1].map((sd, i) => {
    let x = c.gate.x + rx * sd * off + fx * 1.2;
    let z = c.gate.z + rz * sd * off + fz * 1.2;
    search: for (const f of [1.2, 2.2, 3.2, 4.4])
      for (const o of shut ? [off, off - 0.4] : [off, off - 0.7, off - 1.4]) {
        const tx = c.gate.x + rx * sd * o + fx * f;
        const tz = c.gate.z + rz * sd * o + fz * f;
        if (session.standFits(tx, tz, PROBE_Y, 0.55)) {
          x = tx;
          z = tz;
          break search;
        }
      }
    return { v: createGuardView(session.root, folk, 7 + i * 11), x, z };
  });
  if (shut) session.solids.push(gateSolid({ gate: c.gate }, groundAt(c.gate.x, c.gate.z)));
  // The cave's mouth: a dark arch of rock round the mark.
  const group = new THREE.Group();
  const rock = new THREE.MeshLambertMaterial({ color: 0x4a4238, flatShading: true });
  const dark = new THREE.MeshBasicMaterial({ color: 0x080604 });
  const geos: THREE.BufferGeometry[] = [];
  const m = caveMark(region);
  const gy = groundAt(m.x, m.z);
  group.position.set(m.x - Math.sin(m.heading) * 2, gy, m.z - Math.cos(m.heading) * 2);
  group.rotation.y = m.heading;
  for (const sd of [-1, 1]) {
    const g = new THREE.IcosahedronGeometry(2.2, 0);
    geos.push(g);
    const b = new THREE.Mesh(g, rock);
    b.scale.set(0.9, 1.8, 1);
    b.position.set(sd * 2.6, 2.2, 0);
    group.add(b);
  }
  const lg = new THREE.IcosahedronGeometry(2.6, 0);
  const hole = new THREE.PlaneGeometry(4, 4.4);
  geos.push(lg, hole);
  const lintel = new THREE.Mesh(lg, rock);
  lintel.scale.set(1.6, 0.6, 1);
  lintel.position.set(0, 4.8, 0);
  const mouth = new THREE.Mesh(hole, dark);
  mouth.position.set(0, 2.2, -0.4);
  group.add(lintel, mouth);
  session.root.add(group);
  let near = false;
  let banner = 0;
  let wants = false;
  return {
    step(x: number, z: number, dt: number, t: number) {
      for (const [i, g] of guards.entries())
        g.v.update(g.x, groundAt(g.x, g.z), g.z, out + Math.PI + (i ? -0.2 : 0.2), 0, t);
      banner = Math.max(0, banner - dt);
      const now2 = Math.hypot(x - c.gate.x, z - c.gate.z) < c.gate.width + 5;
      if (now2 && !near && now.talk) wants = true;
      else if (now2 && !near && now.say) banner = 4;
      near = now2;
    },
    /** A scene to play now (the guards turning you away), once each time you come up. */
    talk() {
      if (!wants || !now.talk) return undefined;
      wants = false;
      return {
        lines: now.talk,
        gate: c.gate,
        folk,
        seeds: [7, 18],
        guards: guards.map((g) => ({ x: g.x, z: g.z })),
      };
    },
    draw(ui: UiLayer) {
      if (banner > 0)
        wrap(`${now.k.cave}: ${now.say}`, ui.W - 60)
          .slice(0, 3)
          .forEach((l, i) =>
            ui.text(l, ui.W / 2, ui.H / 2 - 40 + i * 10, {
              color: PAL.cream,
              outline: PAL.shadow,
              align: "center",
            }),
          );
    },
    dispose() {
      for (const g of guards) g.v.dispose();
      session.root.remove(group);
      rock.dispose();
      dark.dispose();
      for (const g of geos) g.dispose();
    },
  };
}

/** The guards at the smugglers' cave turning you away, as a little scene (Blake, Oct 29:
 * "a proper cutscene", not a line of white text): the world held still, letterboxed, the
 * camera low beside you on the two guards across the gate, each line in the text box
 * with the guard's own face; ENTER for the next, ESC to skip. */
function caveTalk(
  game: Game,
  session: Session,
  t: {
    lines: [number, string][];
    gate: { x: number; z: number; heading: number };
    folk: Folk;
    seeds: number[];
    guards: { x: number; z: number }[];
  },
): Screen {
  let i = 0;
  let tt = 0;
  let pp: PixelPortraits | undefined;
  const you = session.entrants[0]!;
  const cam = new THREE.Vector3();
  const look = new THREE.Vector3();
  const done = () => {
    pp?.dispose();
    game.screens.pop();
  };
  return {
    id: "CAVE_TALK",
    seeThrough: true,
    enter() {
      game.ui.interactive = false;
      pp = createPixelPortraits(game.stage.renderer);
    },
    frame(dt, actions) {
      tt += dt;
      for (const a of actions) {
        if (a === "back") return done();
        if (a === "confirm") {
          const line = t.lines[i]![1];
          if (Math.floor(tt * 50) < line.length) {
            tt = 99;
            continue;
          }
          i++;
          tt = 0;
          if (i >= t.lines.length) return done();
          game.sounds.move();
        }
      }
    },
    render3d(alpha, frameSeconds) {
      session.render(alpha, frameSeconds);
      // Low beside you, the guards across the gate filling the shot, the speaker a little
      // nearer the middle.
      const s = you.state;
      const gy = you.ground.at(t.gate.x, t.gate.z, PROBE_Y).height;
      const who = t.guards[t.lines[Math.min(i, t.lines.length - 1)]![0]] ?? t.gate;
      const dx = t.gate.x - s.x;
      const dz = t.gate.z - s.z;
      const d = Math.hypot(dx, dz) || 1;
      const ux = dx / d;
      const uz = dz / d;
      // (In front of the gate on your side, a touch off centre, at a guard's eye height.)
      cam.set(t.gate.x - ux * 5.2 + uz * 0.9, gy + 1.5, t.gate.z - uz * 5.2 - ux * 0.9);
      look.set(who.x * 0.75 + t.gate.x * 0.25, gy + 0.7, who.z * 0.75 + t.gate.z * 0.25);
      const c = game.stage.camera;
      c.position.copy(cam);
      c.lookAt(look);
      c.updateMatrixWorld();
      game.stage.render();
      return true;
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, 22, "#000000");
      ui.rect(0, ui.H - 22, ui.W, 22, "#000000");
      const [g, text] = t.lines[Math.min(i, t.lines.length - 1)]!;
      const bx = 10;
      const bh = 54;
      const by = ui.H - bh - 26;
      const bw = ui.W - 20;
      ui.panel(bx, by, bw, bh, "parchment", "ink");
      const slot = portraitSlot(bx, by, bh);
      portrait(ui, pp, CAST.guard!, undefined, slot.x, slot.y, ui.time, slot.size, {
        folk: t.folk,
        seed: t.seeds[g] ?? 7,
      });
      ui.text("SKETCHY GUARD", slot.tx, by + 6, { color: "#8a2a1a" });
      wrap(text.slice(0, Math.floor(tt * 50)), bw - (slot.tx - bx) - 10)
        .slice(0, 3)
        .forEach((l, j) => ui.text(l, slot.tx, by + 18 + j * 10, { color: "#2a1a10" }));
    },
  };
}

/** The cave's card: the underground games (the welcome the first time, then the
 * mini-game), or the smugglers' tunnel on. */
function caveCard(game: Game, region: Region): Screen {
  const now = caveOf(game, region)!;
  const k = now.k;
  const s = adventureOf(game).save;
  const back = () => game.screens.pop();
  const play = () => {
    const info = minigameById(k.minigame)!;
    const finish = (won: boolean) => {
      gamesFinished(s, k.id, won);
      s.where = { region: region.id, at: "cave" };
      persist(game);
      // Won: the key, the stone, and through the tunnel (goHome plays them); lost: back
      // out of the cave to try again.
      if (won) goHome(game);
      else game.screens.go(overworldLoading(game, region.id, "cave", true));
    };
    if (instaWin()) return finish(true);
    game.screens.go(minigameLoading(game, info, { finish, title: k.cave }));
  };
  const games = () => {
    game.sounds.confirm();
    if (!s.seen.includes(UNDERGROUND(k.id)))
      return game.screens.go(sceneScreen(game, UNDERGROUND(k.id), play));
    play();
  };
  const tunnel = () => {
    game.sounds.confirm();
    game.overworld = { region: k.tunnel, at: "start", adventure: true };
    game.screens.go(overworldLoading(game, k.tunnel, "start", true));
  };
  const items =
    now.mode === "games"
      ? [{ label: "PLAY!", action: games }]
      : now.mode === "tunnel"
        ? [{ label: "THROUGH THE TUNNEL", action: tunnel }]
        : [];
  // (Dev free roam: both, whatever the story says.)
  if (freeRoam() && now.mode === "games") items.push({ label: "THE TUNNEL (DEV)", action: tunnel });
  const menu = new VMenu(game, [...items, { label: "NOT YET", action: back }], back);
  const info = minigameById(k.minigame);
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
      const w = 270;
      const h = 110;
      const x = Math.round(ui.W / 2 - w / 2);
      const y = Math.round(ui.H / 2 - h / 2) - 8;
      ui.panel(x, y, w, h, "parchment", "ink");
      ui.text(k.cave, ui.W / 2, y + 8, {
        scale: 2,
        color: PAL.coral,
        outline: PAL.ink,
        align: "center",
      });
      const lines =
        now.mode === "games"
          ? [
              `THE UNDERGROUND GAMES: ${(info?.name ?? "").toUpperCase()}.`,
              "WIN IT FOR THE SMUGGLERS' KEY.",
            ]
          : [`THE SMUGGLERS' TUNNEL: ON TO THE ${nameOf(k.next).toUpperCase()}.`];
      lines.forEach((l, i) =>
        ui.text(l, ui.W / 2, y + 30 + i * 10, { color: PAL.ink, align: "center" }),
      );
      menu.draw(ui, x + 60, y + h - 46, w - 120, 14, 4);
    },
  };
}

/** A conquered kingdom (Adventure): its dragon's banners round the square, and guards. */
function regionDressing(game: Game, session: Session, region: Region) {
  if (!game.overworld?.adventure || !region.kingdom || region.kingdom === "dragon")
    return undefined;
  if (regionLook(adventureOf(game).save, region.kingdom) !== "conquered") return undefined;
  const color = (
    { valley: "#8a1a10", snow: "#3a5a8a", desert: "#8a6a2a", beach: "#1a5a5a" } as Record<
      string,
      string
    >
  )[region.kingdom]!;
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, PROBE_Y).height;
  const sp = region.spawn;
  const fx = Math.sin(sp.heading);
  const fz = Math.cos(sp.heading);
  const P = (f: number, r: number) => [sp.x + fx * f + fz * r, sp.z + fz * f - fx * r] as const;
  const banners: { v: PropView; x: number; z: number; h: number }[] = [
    [16, -9],
    [16, 9],
    [-8, -11],
    [-8, 11],
  ].map(([f, r]) => {
    const [x, z] = P(f!, r!);
    return { v: createBannerView(session.root, color), x, z, h: sp.heading + Math.PI / 2 };
  });
  const guards = [
    [20, -4],
    [20, 4],
  ].map(([f, r], i) => {
    const [x, z] = P(f!, r!);
    // (The dragon's own guards: Dragon Kingdom folk, as in The Hundredth Summer.)
    return { v: createGuardView(session.root, "dragon", 31 + i * 9), x, z };
  });
  return {
    step(t: number) {
      for (const b of banners) b.v.update(b.x, groundAt(b.x, b.z), b.z, b.h, t);
      for (const g of guards) g.v.update(g.x, groundAt(g.x, g.z), g.z, sp.heading + Math.PI, 0, t);
    },
    dispose() {
      for (const b of banners) b.v.dispose();
      for (const g of guards) g.v.dispose();
    },
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

/** A track's look.json (its sky, sky dome, sun, light and fog), once per visit. */
const looks = new Map<string, Promise<TrackLook>>();
function lookOf(id: string): Promise<TrackLook> {
  let p = looks.get(id);
  if (!p) {
    p = fetch(`${packageBase(id)}look.json`)
      .then((r) => (r.ok ? r.json() : {}))
      .then((j) => parseLook(j))
      .catch(() => ({}));
    looks.set(id, p);
  }
  return p;
}

/** A course's camera-round particles (its track.json's), once per visit. */
const airs = new Map<string, Promise<AmbientSpec[]>>();
function ambientOf(id: string): Promise<AmbientSpec[]> {
  let p = airs.get(id);
  if (!p) {
    p = fetch(`${packageBase(id)}track.json`)
      .then((r) => (r.ok ? r.json() : {}))
      .then((j: { entities?: unknown[] }) => courseAmbient(j.entities ?? []))
      .catch(() => []);
    airs.set(id, p);
  }
  return p;
}

/**
 * Each area of the region in its own course's air (Blake, Oct 28: the levels' own
 * lighting and sky): every gateway's course (ruined: its ruin) lends its look.json to
 * the ground round it, the square has the region's own, and between them the two nearest
 * blend as you drive (overworld/air.ts). A square with no painted sky borrows the
 * nearest course's. What drifts in each course's air (Bonebog's fireflies, Ember's ash)
 * drifts in its area too, fading with the same blend (note 38), with the region's own
 * extras for an area (its `area_ambient`s: Riverbend's pollen, the Cascade's spray).
 */
function regionAir(game: Game, session: Session, region: Region, ruined: boolean) {
  const courses = region.gateways.filter((g) => !g.boss && !g.king && trackById(g.track));
  if (!courses.length) return undefined;
  const pkg = (ruined && region.ruinPackageId) || region.packageId;
  let spots: (AirSpot & { air: Air })[] | undefined;
  let alive = true;
  const fx = createAmbientFx(session.root);
  const land = session.makeGround();
  const extras = areaAmbient(session.entities);
  const idOf = (g: Gateway) => {
    const t = trackById(g.track)!;
    return (ruined && t.ruin && trackById(t.ruin) ? t.ruin : g.track) as string;
  };
  void Promise.all([
    lookOf(pkg),
    Promise.all(courses.map((g) => lookOf(idOf(g)))),
    Promise.all(courses.map((g) => ambientOf(idOf(g)))),
  ]).then(([own, theirs, ambient]) => {
    if (!alive) return;
    const base = airOf(own);
    const list: AirSpot[] = [
      { x: region.spawn.x, z: region.spawn.z, look: own, ambient: extras.hub ?? [] },
      ...courses.map((g, i) => ({
        x: g.x,
        z: g.z,
        look: theirs[i]!,
        ambient: [...ambient[i]!, ...(extras[g.id] ?? [])],
      })),
    ];
    // (A square with no sky of its own: the nearest course's.)
    if (!list[0]!.look.skyDome) {
      const near = list
        .slice(1)
        .filter((q) => q.look.skyDome)
        .sort(
          (p, q) =>
            Math.hypot(p.x - region.spawn.x, p.z - region.spawn.z) -
            Math.hypot(q.x - region.spawn.x, q.z - region.spawn.z),
        )[0];
      if (near) list[0] = { ...list[0]!, look: { ...own, skyDome: near.look.skyDome } };
    }
    spots = list.map((q) => ({ ...q, air: airOf(q.look, base) }));
  });
  let clock = 0;
  return {
    step(x: number, z: number, dt: number) {
      if (!spots) return;
      const { a, b, t } = airAt(spots, x, z);
      const A = spots[a]!;
      const B = spots[b]!;
      game.stage.setAir(mixAir(A.air, B.air, t));
      const sky = (q: AirSpot) =>
        q.look.skyDome ? { spec: q.look.skyDome, sun: q.look.sun?.direction } : undefined;
      const under = sky(A);
      const over = sky(B);
      game.stage.setSkies(under ?? over, under && over ? { ...over, t } : undefined);
      // What drifts in the air, round the camera.
      clock += dt;
      const w = airWeights(spots, x, z);
      const cam = game.stage.camera.position;
      fx.update(
        Math.min(0.1, dt),
        clock,
        cam,
        spots.map((q, i) => ({ specs: q.ambient ?? [], weight: w[i]! })),
        (px, pz, py) => land.at(px, pz, py).height,
      );
    },
    dispose() {
      alive = false;
      fx.dispose();
      game.stage.setSkies(undefined);
      game.stage.setAir(undefined);
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

// ---------------------------------------------------------------- the story's races

/**
 * The race the story wants next, here (Adventure), if any: its scene staged where you
 * are or where it happens, then the race at once. The champion's challenge as you come
 * out of the fourth course's gateway; the race for the lands after the King's Games; a
 * new Pact Stone's forced race; the King's last.
 */
function raceTrigger(
  game: Game,
  region: Region,
  at: string | undefined,
): { scene: string; go: () => void } | undefined {
  const s = adventureOf(game).save;
  const unseen = (id: string) => !s.seen.includes(id);
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (k) {
    const ph = kingdomPhase(s, k);
    if (ph === "duel" && region.challenge && unseen(challengeScene(k.id))) {
      const mark = at ? region.gateways.find((g) => g.id === at) : undefined;
      const spot = mark ? exitSpot(mark, () => true) : region.challenge;
      stageAt(challengeStaged(k.id, region.id, spot));
      return {
        scene: challengeScene(k.id),
        go: () => {
          game.overworld = { region: region.id, at: "challenge", adventure: true };
          launch(game, { kind: "duel", kingdom: k.id }, region.packageId);
        },
      };
    }
    const lair = region.gateways.find((g) => g.boss);
    if (ph === "boss" && lair && unseen(newStoneScene(k.id)))
      return {
        scene: newStoneScene(k.id),
        go: () => {
          game.overworld = { region: region.id, at: lair.id, adventure: true };
          launch(game, { kind: "boss", kingdom: k.id }, k.boss.track);
        },
      };
  }
  if (region.kingdom === "dragon") {
    const dp = dragonPhase(s);
    const citadel = region.gateways.find((g) => g.king);
    const king = (final: boolean) => () => {
      game.overworld = { region: region.id, at: citadel?.id, adventure: true };
      launch(game, { kind: "king", final }, DRAGON.king.track);
    };
    if (dp === "king" && unseen(BEFORE_KING)) return { scene: BEFORE_KING, go: king(false) };
    if (dp === "final" && unseen(HEART)) return { scene: HEART, go: king(true) };
  }
  return undefined;
}

export function overworldLoading(
  game: Game,
  regionId: string,
  at?: string,
  adventure = game.overworld?.adventure ?? false,
  /** Dev builds: this state whatever the story says (the warp list). */
  devRuined?: boolean,
): Screen {
  const full = regionById(regionId)!;
  const story = adventure && Boolean(full.kingdom || full.journey);
  const save = story ? adventureOf(game).save : undefined;
  if (import.meta.env.DEV && devRuined !== undefined) devState.set(full.id, devRuined);
  const ruined = regionRuined(game, full.id, story);
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
      if (save && story) {
        // Adventure: the file remembers where you are.
        save.where = { region: region.id, ...(at ? { at } : {}) };
        persist(game);
        // The story's next scene first (it may put you somewhere else: its `where`).
        const due = dueScene(save, hereIn(save));
        if (due) {
          alive = false;
          return game.screens.go(
            sceneScreen(game, due, () => {
              const w = save.where ?? { region: regionId };
              game.screens.go(overworldLoading(game, w.region, w.at, true));
            }),
          );
        }
        // Then the race the story wants next, if it's here.
        const trig = raceTrigger(game, region, at);
        if (trig) {
          alive = false;
          return game.screens.go(sceneScreen(game, trig.scene, trig.go));
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

/** The gateways, in the session's scene (render/gatewayArch.ts: Blake, Oct 28, grand and
 * natural: a cave mouth of the world's rock, a rugged sign, torches); the passages and
 * the champion's spot the same. */
function buildGateways(
  session: Session,
  region: Region,
  extra: { x: number; z: number; heading: number; label: string; world: string }[] = [],
) {
  const you = session.entrants[0]!;
  const marks = [
    ...region.gateways.map((g) => ({
      ...g,
      label: g.label ?? trackById(g.track)?.name ?? g.track,
      world: worldOfTrack(g.track)?.id ?? region.worldId,
      lair: Boolean(g.boss || g.king),
    })),
    ...(region.passages ?? []).map((p) => ({
      ...p,
      label: `TO ${(regionById(p.to)?.name ?? p.to).toUpperCase()}`,
      world: regionById(p.to)?.worldId ?? region.worldId,
      lair: false,
    })),
    ...extra.map((e) => ({ ...e, lair: false })),
  ];
  const themes = ["prehistoric", "frostveil", "desert", "beach", "dragon"];
  const arches = marks.map((g, i) => {
    const y = you.ground.at(g.x, g.z, PROBE_Y).height;
    const own = themes.includes(region.worldId) ? region.worldId : "prehistoric";
    const arch = createGatewayArch(session.root, {
      label: g.label,
      // (The valley's volcano's gateway in its own basalt, no moss on it.)
      theme: (g.lair
        ? "lair"
        : own === "prehistoric" &&
            /ember|lava|volcan|crater/i.test(`${g.label} ${"track" in g ? g.track : ""}`)
          ? "ember"
          : own) as ArchTheme,
      glow: g.lair ? "#ff4a20" : (worldById(g.world)?.color ?? "#e0a040"),
      seed: i * 31 + Math.round(Math.abs(g.x) + Math.abs(g.z)),
    });
    arch.group.position.set(g.x, y, g.z);
    arch.group.rotation.y = g.heading;
    return arch;
  });
  return {
    update: (t: number) => arches.forEach((a) => a.update(t)),
    dispose: () => arches.forEach((a) => a.dispose()),
  };
}

/** The region as it's being driven now (its state after or before the attack): for the
 * debug tools and the playtest bot. */
export let drivenRegion: Region | undefined;

export function overworldScreen(game: Game, session: Session, region: Region, at?: string): Screen {
  const entry = entryOf(region);
  let clock = 0;
  let gateways: ReturnType<typeof buildGateways> | undefined;
  let blockers: ReturnType<typeof regionBlockers> | undefined;
  let map: ReturnType<typeof regionMap> | undefined;
  let crew: ReturnType<typeof regionCrew> | undefined;
  let secret: ReturnType<typeof regionSecret> | undefined;
  let cave: ReturnType<typeof regionCave> | undefined;
  let dressing: ReturnType<typeof regionDressing> | undefined;
  let pactStone: ReturnType<typeof regionPactStone> | undefined;
  let air: ReturnType<typeof regionAir> | undefined;
  let villagers: Villagers | undefined;
  /** The gateway (or passage) you're standing in (its card doesn't open again until you
   * leave it). */
  let inside: { x: number; z: number; radius: number } | undefined;
  const story = Boolean(game.overworld?.adventure);
  // Adventure, after the four courses: the champion waits beside the ring's start line.
  const champ = story ? challengeOf(game, region) : undefined;
  const challenge =
    champ && region.challenge ? { id: "challenge", radius: 6, ...region.challenge } : undefined;
  // The smugglers' cave, inside its yard.
  const caveNow = story ? caveOf(game, region) : undefined;
  const caveAt = caveNow ? caveMark(region) : undefined;
  const marks = [
    ...region.gateways,
    ...(region.passages ?? []),
    ...(challenge ? [challenge] : []),
    ...(caveAt ? [caveAt] : []),
  ];

  // F2 (dev builds): the level review tool, as in the races.
  const onKey = (e: KeyboardEvent) => {
    if (!import.meta.env.DEV || e.code !== "F2" || e.repeat || game.screens.top !== screen) return;
    e.preventDefault();
    openRegionReview(game, session, region);
  };
  const screen: Screen = {
    id: "OVERWORLD",
    enter() {
      window.addEventListener("keydown", onKey);
      game.session = session;
      game.ui.interactive = false;
      drivenRegion = region;
      gateways = buildGateways(session, region, [
        ...(challenge
          ? [{ ...challenge, label: `${champ!.name}'S CHALLENGE`, world: region.worldId }]
          : []),
      ]);
      blockers = regionBlockers(game, session, region);
      crew = regionCrew(game, session, region);
      secret = regionSecret(game, session, region);
      cave = regionCave(game, session, region);
      dressing = regionDressing(game, session, region);
      pactStone = regionPactStone(game, session, region);
      air = regionAir(game, session, region, regionRuined(game, region.id, story));
      // The folk who live here, walking about round their homes.
      const land = session.makeGround();
      villagers = createVillagers({
        root: session.root,
        homes: parseHomes(session.entities),
        solids: session.solids,
        ground: (x, z, y) => {
          const g = land.at(x, z, y);
          const bad = g.surface && /water|lava|wall|mud/.test(g.surface);
          // No land under you (a well's mouth, a hole): not somewhere to stand.
          return { height: g.height, ok: !bad && g.ny > 0.8 && g.height > -500 };
        },
        fits: (x, z, y, r) => session.standFits(x, z, y, r),
      });
      if (import.meta.env.DEV)
        (window as unknown as { kpVillagers?: Villagers }).kpVillagers = villagers;
      map = regionMap(session, region, [
        ...(challenge ? [challenge] : []),
        ...(caveAt ? [caveAt] : []),
      ]);
      // Back out of the mark you went in by (a gateway: onto the road, facing along it), in
      // front of a mark (`<id>:front`), just where you were (`@x,z,heading`: a change of
      // driver), or at the region's spawn.
      const you = session.entrants[0]!;
      const fits = (x: number, z: number) => session.kartFits(x, z, PROBE_Y);
      const front = at?.endsWith(":front") ?? false;
      const markId = front ? at!.slice(0, -":front".length) : at;
      const from = marks.find((g) => g.id === markId);
      if (at?.startsWith("@")) {
        const [x, z, h] = at.slice(1).split(",").map(Number) as [number, number, number];
        session.placeYou(x, z, h, PROBE_Y);
      } else if (from && front) {
        const p = frontSpot(from, fits);
        session.placeYou(p.x, p.z, p.heading, PROBE_Y);
      } else if (from) {
        const out = exitSpot(from, fits);
        const gate = region.gateways.some((g) => g.id === from.id);
        const road = gate && session.track ? roadSpot(session.track.samples, out, fits) : undefined;
        const p = road ?? out;
        session.placeYou(p.x, p.z, p.heading, PROBE_Y);
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
      window.removeEventListener("keydown", onKey);
      gateways?.dispose();
      blockers?.dispose();
      crew?.dispose();
      secret?.dispose();
      cave?.dispose();
      dressing?.dispose();
      pactStone?.dispose();
      air?.dispose();
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
      cave?.step(session.entrants[0]!.state.x, session.entrants[0]!.state.z, top ? dt : 0, clock);
      dressing?.step(clock);
      pactStone?.step(clock);
      gateways?.update(clock);
      if (!top) return;
      if (actions.some((a) => a === "pause" || a === "back")) {
        game.screens.push(overworldPause(game, region, session));
        return;
      }
      const s = session.entrants[0]!.state;
      const talk = cave?.talk();
      if (talk) {
        s.speed = 0;
        game.screens.push(caveTalk(game, session, talk));
        return;
      }
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
        const cv = caveAt && inGateway(caveAt, s.x, s.z) ? caveAt : undefined;
        if (p && !g && passageOpen(game, p)) {
          inside = p;
          game.sounds.confirm();
          return throughPassage(game, p);
        }
        if (g || p || ch || cv) {
          inside = g ?? p ?? ch ?? cv;
          s.speed = 0;
          game.sounds.confirm();
          game.screens.push(
            g
              ? gatewayCard(game, region, g)
              : p
                ? passageCard(game, p)
                : ch
                  ? challengeCard(game, region)
                  : caveCard(game, region),
          );
        }
      }
    },
    render3d(alpha, frameSeconds) {
      session.render(alpha, frameSeconds);
      const s = session.entrants[0]!.state;
      air?.step(s.x, s.z, frameSeconds);
      game.stage.render();
      return true;
    },
    draw(ui) {
      drawHud(ui, session, entry, true, undefined, clock);
      // (No region plaque and no minimap any more: Blake, Oct 28, they bothered him. The
      // region's name shows as you arrive; a proper journal menu, what you've done and
      // what's next, comes later.)
      const goal = story ? storyGoal(game, region) : undefined;
      if (goal) ui.text(goal, 8, 8, { color: PAL.cream, outline: PAL.shadow });
      blockers?.draw(ui);
      secret?.draw(ui);
      cave?.draw(ui);
      void map;
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
  // (The mark you came out of counts as the one you're in, so its card doesn't reopen.)
  inside = marks.find((g) => g.id === (at?.endsWith(":front") ? undefined : at));
  return screen;
}

/** Adventure: what the story asks of this region's gateways now. `go` is undefined
 * when this gateway has nothing to race yet. */
interface StoryOffer {
  /** The course the card shows. */
  track: string;
  note: string;
  go?: () => void;
}

/** One of a kingdom's four standard courses at its gateway (the festival, the
 * gladiator games, the King's Games: win all four, in any order): race it, or race it
 * again once won. */
function courseOffer(
  game: Game,
  region: Region,
  g: Gateway,
  id: KingdomId,
  title: string,
): StoryOffer {
  const s = adventureOf(game).save;
  const n = winsOf(s, id);
  const won = Boolean(s.wins[g.track]);
  return {
    track: g.track,
    note: won
      ? `${title} · WON (${n}/4) · RACE IT AGAIN`
      : `${title} · WIN HERE (${n}/4 WON, ANY ORDER)`,
    go: () => {
      game.overworld = { region: region.id, at: g.id, adventure: true };
      launch(game, { kind: "race", kingdom: id, track: g.track }, g.track);
    },
  };
}

/** A light shard's race on the gateway's ruined course: every shard piece, and 1st. */
function shardOffer(game: Game, region: Region, g: Gateway, id: KingdomId): StoryOffer | undefined {
  const s = adventureOf(game).save;
  const course = coursesOf(id).find((c) => c.track === g.track);
  if (!course) return undefined;
  const cc = shardCourse(course, (t) => Boolean(trackById(t)));
  const won = Boolean(s.shards[course.track]);
  return {
    track: cc.track,
    note: won
      ? `ITS LIGHT SHARD IS YOURS (${shardsOf(s, id)}/4) · RACE IT AGAIN`
      : "A LIGHT SHARD: GET EVERY SHARD PIECE AND FINISH 1ST",
    go: () => {
      game.overworld = { region: region.id, at: g.id, adventure: true };
      launch(game, { kind: "shards", kingdom: id, course: course.track, ...cc }, cc.track);
    },
  };
}

/** The Dragon Kingdom's gateways, by where the story is. */
function dragonOffer(game: Game, region: Region, g: Gateway): StoryOffer | undefined {
  const s = adventureOf(game).save;
  const p = dragonPhase(s);
  const king = DRAGON.king.name.toUpperCase();
  if (g.king) {
    const race = (final: boolean, note: string) => ({
      track: g.track,
      note,
      go: () => {
        game.overworld = { region: region.id, at: g.id, adventure: true };
        launch(game, { kind: "king", final }, DRAGON.king.track);
      },
    });
    if (p === "king") return race(false, `RACE ${king} FOR THE LANDS!`);
    if (p === "final") return race(true, `RACE ${king}, UNDER THE NEW PACT!`);
    if (p === "done") return race(true, `${king} IS BEATEN · RACE HIM AGAIN`);
    if (p === "shards")
      return { track: g.track, note: `BRING THE LAST FOUR SHARDS (${shardsOf(s, "dragon")}/4)` };
    return { track: g.track, note: `${king} WAITS IN HIS CITADEL. WIN HIS GAMES FIRST` };
  }
  if (!DRAGON.courses.some((c) => c.track === g.track)) return undefined;
  if (p === "locked" || p === "waiting") return { track: g.track, note: "NOT YET" };
  if (p === "games" || p === "king")
    return courseOffer(game, region, g, "dragon", "THE KING'S GAMES");
  if (p === "shards" || p === "final") return shardOffer(game, region, g, "dragon");
  return courseOffer(game, region, g, "dragon", "THE KINGDOMS ARE RESTORED");
}

function storyOffer(game: Game, region: Region, g: Gateway): StoryOffer | undefined {
  if (region.kingdom === "dragon") return dragonOffer(game, region, g);
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  const course = k?.courses.find((c) => c.track === g.track);
  if (!k || (!course && !g.boss)) return undefined;
  const s = adventureOf(game).save;
  const ph = kingdomPhase(s, k);
  const name = k.boss.name.toUpperCase();
  if (g.boss) {
    if (ph === "boss")
      return {
        track: g.track,
        note: `RACE ${name}!`,
        go: () => {
          game.overworld = { region: region.id, at: g.id, adventure: true };
          launch(game, { kind: "boss", kingdom: k.id }, k.boss.track);
        },
      };
    return {
      track: g.track,
      note: `${name}'S LAIR · BRING FOUR LIGHT SHARDS (${shardsOf(s, k.id)}/4)`,
    };
  }
  switch (ph) {
    case "locked":
    case "waiting":
      return { track: g.track, note: "NOT YET" };
    case "games":
      return courseOffer(game, region, g, k.id, k.id === "valley" ? "THE FESTIVAL" : "THE GAMES");
    case "duel":
      return {
        track: g.track,
        note: `${k.champion.name.toUpperCase()} IS WAITING BY THE START LINE ON THE RING`,
      };
    case "shards":
    case "boss":
      return shardOffer(game, region, g, k.id);
    default:
      return courseOffer(game, region, g, k.id, k.id === "valley" ? "THE FESTIVAL" : "THE GAMES");
  }
}

/** Adventure: where the story wants you next in this region (the map marks it): the
 * champion's challenge, the cave, the lair or the Citadel, the next course that moves
 * the story on, or the way on in a journey. */
export function storyTarget(
  game: Game,
  region: Region,
): { id: string; x: number; z: number; radius: number; heading: number } | undefined {
  if (!game.overworld?.adventure) return undefined;
  const s = adventureOf(game).save;
  if (region.challenge && challengeOf(game, region))
    return { id: "challenge", radius: 6, ...region.challenge };
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (k && region.cave) {
    const ph = kingdomPhase(s, k);
    if (ph === "underground" || ph === "escaped" || ph === "restored") return caveMark(region);
  }
  for (const g of region.gateways) {
    const o = storyOffer(game, region, g);
    if (o?.go && !/AGAIN/.test(o.note)) return g;
  }
  // A journey: the way on towards where the story is.
  if (region.journey) {
    const here = storyPlace(region, STORY_ORDER);
    const there = STORY_ORDER.indexOf(storyKingdom(s));
    return (region.passages ?? []).find((p) => (there > here ? p.id === "end" : p.id === "start"));
  }
  return undefined;
}

/** Adventure: the champion who'll race you 1 on 1 here now (their challenge is due). */
function challengeOf(game: Game, region: Region) {
  const k = region.kingdom ? kingdomById(region.kingdom) : undefined;
  if (!k || !region.challenge || kingdomPhase(adventureOf(game).save, k) !== "duel")
    return undefined;
  const cousin = k.champion.look === youOf(game);
  return { name: `${k.champion.name.toUpperCase()}${cousin ? "'S COUSIN" : ""}`, kingdom: k.id };
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

/** On through a passage: the region (or the journey) beyond loads. A journey's way back
 * into a kingdom whose own end of it isn't there (it's the ruin's: the gorge, the pass,
 * the road, the causeway the Rage broke open) comes out of the smugglers' tunnel instead,
 * at the cave. */
function throughPassage(game: Game, p: Passage) {
  const story = game.overworld?.adventure ?? false;
  const to = regionById(p.to);
  const there = to?.passages?.find((q) => q.id === p.toPassage);
  const at = there?.ruinOnly && to?.cave && !regionRuined(game, p.to, story) ? "cave" : p.toPassage;
  game.overworld = { region: p.to, at, adventure: story, ruined: game.overworld?.ruined };
  game.screens.go(overworldLoading(game, p.to, at, story));
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

/**
 * The level review tool (dev builds), on the region you're driving: the same tool as
 * the races' (F2, or REVIEW REGION in the pause menu), its notes filed under the
 * region's package (the ruined one when it's ruined).
 */
function openRegionReview(game: Game, session: Session, region: Region) {
  const story = Boolean(game.overworld?.adventure);
  const ruined = regionRuined(game, region.id, story);
  const pkg = (ruined && region.ruinPackageId) || region.packageId;
  const base = trackById(pkg) ?? trackById(region.packageId);
  const entry = {
    ...(base ?? ({} as TrackEntry)),
    id: pkg,
    name: ruined ? `${region.name} (ruined)` : region.name,
  } as TrackEntry;
  game.screens.push(reviewScreen(game, session, entry));
}

/**
 * The kingdom's Pact Stone (Blake, Oct 28: it's in the story, so it's in the world), as
 * the story has it: old; glowing from the hundredth summer; cracked once it's been found
 * cracked; broken after the Rage (and in the ruined region). Solid.
 */
function regionPactStone(game: Game, session: Session, region: Region) {
  const at = region.pactStone;
  if (!at) return undefined;
  const story = Boolean(game.overworld?.adventure);
  const k = region.kingdom;
  let state: StoneState = "old";
  if (regionRuined(game, region.id, story)) state = "broken";
  else if (story && k) {
    const seen = adventureOf(game).save.seen;
    if (RAGE.some((r) => seen.includes(r))) state = "broken";
    else if (seen.includes(sceneOf(k as KingdomId, "stone"))) state = "cracked";
    else if (seen.includes(sceneOf(k as KingdomId, "hundredth"))) state = "glowing";
  }
  const you = session.entrants[0]!;
  const y = you.ground.at(at.x, at.z, PROBE_Y).height;
  const view = createPactStoneView(session.root, state);
  view.update(at.x, y, at.z, at.heading, 0);
  session.solids.push({
    kind: "circle",
    look: "creature",
    x: at.x,
    z: at.z,
    radius: 1.6,
    height: y + 6,
  });
  return {
    step(t: number) {
      view.update(at.x, y, at.z, at.heading, t);
    },
    dispose: () => view.dispose(),
  };
}

function overworldPause(game: Game, region: Region, session: Session): Screen {
  const leave = () => {
    game.overworld = undefined;
    game.screens.go(titleScreen(game, true));
  };
  const story = Boolean(game.overworld?.adventure);
  const here = () => {
    const s = session.entrants[0]!.state;
    return `@${s.x.toFixed(2)},${s.z.toFixed(2)},${s.heading.toFixed(3)}`;
  };
  const menu = new VMenu(
    game,
    [
      { label: "RESUME", action: () => resume() },
      // Adventure: who drives (your racer and the crew who've joined you).
      ...(story
        ? [
            {
              label: "YOUR CREW",
              action: () =>
                game.screens.push(
                  crewMenu(game, () =>
                    game.screens.go(overworldLoading(game, region.id, here(), true)),
                  ),
                ),
            },
          ]
        : []),
      // Dev free roam: the region before or after the Rage.
      ...(!story && region.ruinPackageId
        ? [
            {
              label: game.overworld?.ruined ? "SHOW IT STANDARD" : "SHOW IT RUINED",
              action: () => {
                const ruined = !game.overworld?.ruined;
                game.overworld = { region: region.id, ruined };
                devState.delete(region.id);
                game.screens.go(overworldLoading(game, region.id, undefined, false));
              },
            },
          ]
        : []),
      // Dev builds: the level review tool, on this region.
      ...(import.meta.env.DEV
        ? [
            {
              label: "REVIEW REGION",
              action: () => {
                game.screens.pop();
                openRegionReview(game, session, region);
              },
            },
          ]
        : []),
      // Dev builds: every testing tool on one page.
      ...(import.meta.env.DEV
        ? [
            {
              label: "DEV TOOLS",
              action: () => {
                const back = () => {
                  game.overworld = { region: region.id, adventure: story };
                  game.screens.go(overworldLoading(game, region.id, here(), story));
                };
                game.screens.go(devMenu(game, { back }));
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
