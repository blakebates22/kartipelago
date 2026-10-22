/**
 * One race (or practice) from start to finish: the track, the karts, the AI, items,
 * bananas and the race rules, plus their 3D views.
 *
 * This is the game that main.ts used to build at page load, now made into something
 * the frontend can create, pause, restart and throw away:
 *
 * - everything it adds to the 3D scene hangs off one group (`root`), and every HUD
 *   element off one DOM element, so `dispose()` removes and frees all of it;
 * - its key listeners share one AbortController;
 * - pausing is simply not calling `update()` (the race clock, physics, items and AI
 *   all advance there and nowhere else).
 *
 * Vehicle physics, drifting, zippers, bananas, items and the AI are used exactly as
 * before; nothing here changes how a kart drives.
 */
import * as THREE from "three";
import { tuning } from "../core/tuning";
import { NEUTRAL, type Input } from "../core/input";
import type { Stage } from "../render/stage";
import { createStartMeter } from "../debug/startMeter";
import courseData from "../../assets/data/course.json";
import roster from "../../assets/data/characters.json";
import { createCourseView } from "../render/courseView";
import { createTrackView } from "../render/trackView";
import { createCourse, resetCourse, stepCourse } from "../world/course";
import { buildTrack, type Track, type TrackData } from "../world/track";
import { buildZippers, enteredZipper } from "../world/zippers";
import { BOOST_SOURCE, ZIP, startZipper } from "../vehicles/zipper";
import {
  bumpMass,
  racerItems,
  shieldRam,
  stepEffects,
  type Racer,
  type RacerItems,
} from "../items/effects";
import { heldLabel, type BalloonColor } from "../items/inventory";
import {
  collectBalloons,
  createItemWorld,
  fireItem,
  itemReleased,
  resetItemWorld,
  stepItemWorld,
  type ItemEvent,
} from "../items/world";
import type { ItemsConfig } from "../items/config";
import { createItemView } from "../render/itemView";
import { Racer as RacerView, motionOf } from "../render/racers/racer";
import { DESIGNS, RACER_IDS, type RacerId } from "../render/racers/designs";
import { bananaMult, bananaScales, effectiveBananas, loseBananas } from "../vehicles/bananas";
import {
  collectBananas,
  createBananaField,
  dropBananas,
  resetBananaField,
  stepBananaField,
  type BananaPickup,
} from "../world/bananas";
import { createBananaView } from "../render/bananaView";
import type { Sfx } from "../audio/sfx";
import { createHazards, type HazardConfig } from "./hazards";
import { createLoops } from "./loops";
import { createCheckpointView, type CheckpointView } from "../render/checkpointView";
import { segmentProgress } from "../race/checkpoints";
import { createTrackGround, flatGround, type GroundQuery } from "../physics/ground";
import { stepVertical } from "../physics/vertical";
import { stepImpacts, stepMeshWalls, stepSolids, stepWalls } from "../physics/walls";
import { boundarySolids, buildTunnel, placeTrees, tunnelSolids } from "../world/solids";
import { createSceneryView } from "../render/sceneryView";
import { bumpKarts } from "../physics/bump";
import { buildRacingLine } from "../ai/racingLine";
import { createDriver, driveAi, type Driver } from "../ai/driver";
import {
  canDrive,
  createRace,
  lapClock,
  progress,
  respawnSpot,
  standings,
  stepRacer,
  teleported,
  tickRace,
} from "../race/race";
import type { Race } from "../race/race";
import { gridSlot } from "../race/grid";
import { createSpeedometer } from "../render/speedometer";
import type { LookMode } from "../render/trackMaterials";
import { createParkSigns } from "../render/parkSigns";
import { applySurface, createMeshGround } from "../world/collisionMesh";
import {
  disposeObject,
  loadTrackPackage,
  SURFACES,
  swapPackage,
  urlReader,
  type TrackPackage,
} from "../world/trackPackage";
import {
  buildDriftPark,
  createLocator,
  createParkGround,
  createStreak,
  distanceToRoad,
  loopStart,
  stepStreak,
  streakLaps,
} from "../world/driftPark";
import { boostChevrons, needleDeg, speedoValue } from "../render/speedo";
import { applyCharacter, type Character } from "../vehicles/character";
import {
  applyBoost,
  createKartState,
  slipAngle,
  stepKart,
  wrapAngle,
  type KartState,
} from "../vehicles/kart";
import type { createDebug } from "../debug";
import type { createBoostLab } from "../debug/boostLab";
import { createChaseCamera } from "../render/chaseCamera";

export type SessionScene = "track" | "practice" | "drift";

export interface SessionOptions {
  scene: SessionScene;
  /** A built-in track (scene "track"). */
  trackData?: TrackData;
  /** A Blender-exported track in public/tracks/<id>/ (scene "track"). */
  packageId?: string;
  /** Race against the AI (otherwise a solo time trial). */
  rivals: boolean;
  /** The player's racer (looks only). */
  racer: RacerId;
  /** The player's kart class (driving stats), by characters.json id. */
  character?: string;
  /** Title-screen demo: the player's kart is driven by the AI, no sound, orbiting camera. */
  demo?: boolean;
  /** Drift Park loop to start on (0-based). */
  parkLoop?: number;
  /** Texture look for imported tracks. */
  lookMode: LookMode;
  /**
   * If an imported track can't load: fall back to Drift Loop (the old URL behaviour),
   * instead of failing.
   */
  fallback?: boolean;
}

export interface SessionContext {
  stage: Stage;
  input: Input;
  sfx: Sfx;
  debug: ReturnType<typeof createDebug>;
  boostLab: ReturnType<typeof createBoostLab>;
  /** Where the session's HUD elements go. */
  hudParent: HTMLElement;
  /** Developer extras: stat keys (1-4), drift model (M), banana keys (K, L). */
  devKeys: boolean;
  /** Show the start-boost timing bar (?timing). */
  showTiming: boolean;
}

/** What the pixel HUD needs each frame. */
export interface HudState {
  phase: "countdown" | "racing" | "practice";
  /** Seconds until GO during the countdown (0 after). */
  countdown: number;
  /** Seconds since GO (for the "GO!" flash). */
  sinceGo: number;
  startTier?: string;
  position?: number;
  racers: number;
  lap: number;
  laps: number;
  lapTime: number;
  bestLap?: number;
  totalTime: number;
  finished: boolean;
  bananas: number;
  item: string;
  /** The held balloon, for the item box's icon (null when holding nothing). */
  held: { color: BalloonColor; level: number; ammo: number } | null;
  /** Drift Park: loop name, current drift streak (laps), best streak, direction. */
  park?: { loop: string; streak: number; best: number; turning: "left" | "right" };
  toast?: string;
}

/** The player's finished race. */
export interface RaceResult {
  position?: number;
  racers: number;
  totalTime: number;
  lapTimes: number[];
  bestLap: number;
  /** Everyone's finishing order (names and times), when racing the AI. */
  order: { name: string; racer: RacerId; time?: number; you: boolean }[];
}

interface Entrant {
  name: string;
  look: RacerId;
  character: Character;
  color: string;
  state: KartState;
  /** State at the previous step, for smooth rendering between steps. */
  prev: { x: number; y: number; z: number; heading: number; velAngle: number };
  /** What you see: kart, character, exhaust flame and shadow (visual only). */
  racer: RacerView;
  /** The racer's root: follows the kart's position and tilt. */
  mesh: THREE.Object3D;
  /** Held balloon and timed item effects. */
  items: RacerItems;
  /** Each kart keeps its own ground lookup (it remembers where on the track it was). */
  ground: GroundQuery;
  /** On a boost surface last step (imported tracks), so it fires once per visit. */
  onBoost?: boolean;
  driver?: Driver;
}

/** Exhaust colour by boost source: zipper, blue 1, blue 2, blue 3. */
const FLAME_COLORS = ["#ffb347", "#ff7b00", "#2f80ed", "#9b5de5"];
/** Meadow grass under the Drift Park. */
const PARK_GROUND = "#6fae4b";
const GROUND_SIZE = 1200;
const GROUND_TILE = 5; // metres per grid square
export const packageBase = (id: string) => `tracks/${encodeURIComponent(id)}/`;

const characters = roster.characters as Character[];
const findCharacter = (id: string) => characters.find((c) => c.id === id) ?? characters[0]!;

// Tiled lines on the ground give the eye something to judge speed and turning against.
function groundTexture() {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const g = canvas.getContext("2d")!;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, size, size);
  g.fillStyle = "#c4c4c4"; // multiplies groundColor, so lines are a darker shade of it
  g.fillRect(0, 0, size, 3);
  g.fillRect(0, 0, 3, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(GROUND_SIZE / GROUND_TILE, GROUND_SIZE / GROUND_TILE);
  tex.anisotropy = 8;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** Load what the session needs (imported tracks), then build it. */
export async function createSession(ctx: SessionContext, opts: SessionOptions) {
  let pkg: TrackPackage | undefined;
  let packageError: string | undefined;
  if (opts.scene === "track" && opts.packageId) {
    try {
      pkg = await loadTrackPackage(urlReader(packageBase(opts.packageId)), { mode: opts.lookMode });
    } catch (err) {
      if (!opts.fallback) throw err;
      packageError = `Couldn't load track "${opts.packageId}": ${(err as Error).message}`;
      console.error(err);
    }
  }
  for (const w of pkg?.warnings ?? []) console.warn(`[track] ${w}`);
  return buildSession(ctx, opts, pkg, packageError);
}

export type Session = ReturnType<typeof buildSession>;

function buildSession(
  ctx: SessionContext,
  opts: SessionOptions,
  pkg: TrackPackage | undefined,
  packageError: string | undefined,
) {
  const { stage, input, sfx, debug, boostLab } = ctx;
  const SCENE = opts.scene;
  const demo = Boolean(opts.demo);
  const abort = new AbortController();
  const listen = (fn: (e: KeyboardEvent) => void) =>
    window.addEventListener("keydown", fn, { signal: abort.signal });

  const trackData: TrackData = pkg ? pkg.trackData : (opts.trackData ?? ({} as TrackData));
  const root = new THREE.Group();
  root.name = "session";
  stage.scene.add(root);
  stage.setEnvironment(pkg?.look);
  const chase = createChaseCamera(stage.camera);
  const hudRoot = document.createElement("div");
  hudRoot.className = "session-hud";
  hudRoot.hidden = demo;
  ctx.hudParent.appendChild(hudRoot);

  const groundMat = new THREE.MeshStandardMaterial({
    color: tuning.world.groundColor,
    map: groundTexture(),
  });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(GROUND_SIZE, GROUND_SIZE), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  root.add(ground);
  // An imported track brings its own terrain.
  if (pkg) {
    ground.visible = false;
    root.add(pkg.visual);
  }

  const course = SCENE === "practice" ? createCourse(courseData) : undefined;
  const courseView = course ? createCourseView(root, course, tuning.course) : undefined;
  const track = SCENE === "track" ? buildTrack(trackData, tuning.track.sampleSpacing) : undefined;
  // The Drift Park: isolated loops sized from the drift's own radii (see world/driftPark.ts).
  const park =
    SCENE === "drift"
      ? buildDriftPark(tuning.vehicle, tuning.driftPark, tuning.track.sampleSpacing)
      : undefined;
  const parkPads = (park?.loops ?? []).map((l) =>
    buildZippers(l.track, l.track.data.zippers ?? [], tuning.track),
  );
  /** Branching courses: the other whole-lap routes, for pickups placed on their branches. */
  const altTracks = new Map(
    (pkg?.lapRoutes ?? []).map((r) => [r.id, buildTrack(r.trackData, tuning.track.sampleSpacing)]),
  );
  /** Split pickups by the route their `at` is measured along (main, or a lap route). */
  const byRoute = <T extends { route?: string }>(spots: T[] = []) => {
    const out: [Track, T[]][] = [];
    if (track) out.push([track, spots.filter((s) => !s.route || !altTracks.has(s.route))]);
    for (const [id, t] of altTracks) out.push([t, spots.filter((s) => s.route === id)]);
    return out;
  };
  const zippers = track
    ? byRoute(trackData.zippers).flatMap(([t, s]) => buildZippers(t, s, tuning.track))
    : parkPads.flat();
  let trackView = track
    ? createTrackView(root, track, tuning.track, zippers, { surface: !pkg })
    : undefined;
  const parkViews = (park?.loops ?? []).map((l, i) =>
    createTrackView(root, l.track, tuning.track, parkPads[i]),
  );
  if (park) createParkSigns(root, park);
  /** A fresh ground lookup (each kart and falling banana keeps its own). */
  const makeGround = (): GroundQuery =>
    pkg
      ? createMeshGround(pkg.collision)
      : track
        ? createTrackGround(track)
        : park
          ? createParkGround(park)
          : flatGround;
  // Open tracks: no road walls; tunnels, the map boundary and trees are what you can hit.
  const OPEN = Boolean(track && trackData.open) || Boolean(park);
  const tunnels = track && OPEN ? (trackData.tunnels ?? []).map((t) => buildTunnel(track, t)) : [];
  const solids = (() => {
    // Imported tracks: walls, rocks and trees are all in the collision mesh.
    if (pkg) return [];
    if (park) {
      // A boundary round the whole park, and trees between and inside the loops.
      const all = { samples: park.loops.flatMap((l) => l.track.samples) } as Track;
      const fixed = boundarySolids(all, tuning.scenery.boundaryMargin);
      const trees = park.loops.flatMap((l, i) =>
        placeTrees(l.track, { ...tuning.scenery, trees: 10, seed: tuning.scenery.seed + i }, fixed),
      );
      const kept = trees.filter(
        (t, i) =>
          distanceToRoad(park, t.x, t.z) >= tuning.scenery.treeClearance &&
          !trees.slice(0, i).some((o) => Math.hypot(o.x - t.x, o.z - t.z) < 7),
      );
      return [...fixed, ...kept];
    }
    if (!track || !OPEN) return [];
    const fixed = [
      ...tunnels.flatMap(tunnelSolids),
      ...boundarySolids(track, tuning.scenery.boundaryMargin),
    ];
    return [...fixed, ...placeTrees(track, tuning.scenery, fixed)];
  })();
  const sceneryView =
    OPEN && !pkg ? createSceneryView(root, solids, tunnels, tuning.scenery) : undefined;
  const bananaField = createBananaField(track, [], makeGround, !OPEN);
  for (const [t, s] of byRoute(trackData.bananas))
    bananaField.bananas.push(...createBananaField(t, s, makeGround, !OPEN).bananas);
  for (const l of park?.loops ?? [])
    bananaField.bananas.push(
      ...createBananaField(l.track, l.track.data.bananas ?? [], makeGround, false).bananas,
    );
  const bananaView = createBananaView(root, tuning.bananas);
  const itemsCfg = tuning.items as ItemsConfig;
  // Balloons and weapons: pickups, missiles and traps live in the item world.
  const itemWorld = createItemWorld(track, [], makeGround, solids, !OPEN);
  for (const [t, s] of byRoute(trackData.balloons))
    itemWorld.balloons.push(...createItemWorld(t, s, makeGround).balloons);
  const itemView = createItemView(root);
  /** Collected this step, for the render to show (effects run at frame rate). */
  const pickupsToShow: BananaPickup[] = [];
  const lineOf = (t: Track) =>
    buildRacingLine(t, {
      margin: trackData.aiLineMargin ?? tuning.ai.lineMargin,
      span: tuning.ai.lineSpan,
      iterations: tuning.ai.lineIterations,
    });
  let line = track ? lineOf(track) : undefined;
  /**
   * Branching courses: a racing line for every whole-lap route (the main one first).
   * Rivals are spread across them in turn, so every branch combination is raced, and
   * the same rival always takes the same branches (repeatable races and tests).
   */
  const lapLinesOf = (p: TrackPackage | undefined) =>
    line
      ? [
          line,
          ...(p?.lapRoutes ?? []).map((r) =>
            lineOf(buildTrack(r.trackData, tuning.track.sampleSpacing)),
          ),
        ]
      : [];
  let lapLines = lapLinesOf(pkg);
  const lineFor = (i: number) => lapLines[i % lapLines.length] ?? line!;

  // Rivals take the other racers' looks in turn; repeats get the alternate paint.
  const playerLook = opts.racer;
  const rivalLook = (i: number): { id: RacerId; alt: boolean } => {
    const others = RACER_IDS.filter((id) => id !== playerLook);
    return { id: others[(i - 1) % others.length]!, alt: i > others.length };
  };
  const makeRacer = (i: number): RacerView => {
    const look = i === 0 ? { id: playerLook, alt: false } : rivalLook(i);
    const r = new RacerView(look.id, { alt: look.alt, seed: i * 17 + 5 });
    root.add(r.root, r.shadow);
    return r;
  };

  const player = findCharacter(opts.character ?? roster.default);
  const rivals = track && opts.rivals ? roster.rivals : [];
  const entrants: Entrant[] = [
    { name: DESIGNS[playerLook].name, character: player, color: player.color },
    ...rivals.map((r, i) => ({
      // The first rivals are the other racers; their alternate-paint cousins keep their
      // roster names.
      name: i < RACER_IDS.length - 1 ? DESIGNS[rivalLook(i + 1).id].name : r.name,
      character: findCharacter(r.character),
      color: r.color,
    })),
  ].map((e, i) => {
    const racer = makeRacer(i);
    return {
      ...e,
      look: i === 0 ? playerLook : rivalLook(i).id,
      state: createKartState(),
      prev: { x: 0, y: 0, z: 0, heading: 0, velAngle: 0 },
      racer,
      mesh: racer.root,
      items: racerItems(),
      ground: makeGround(),
      driver:
        (i > 0 || demo) && line ? createDriver(i > 0 ? lineFor(i) : line, i, tuning.ai) : undefined,
    };
  });
  const you = entrants[0]!;
  // Loop-the-loops (src/game/loops.ts): each kart rides them in its own loop mode.
  const loops = pkg ? createLoops(pkg.meta.entities ?? [], entrants.length) : undefined;
  /** Where race logic sees each kart (on a loop: the straight from its entry to its exit). */
  const racePositions = () =>
    entrants.map((e, i) => (loops?.riding(i) ? loops.racePos(i, e.state) : e.state));
  // Blender tracks: lava, deep water, creatures and waterfalls from track.json.
  const hazards =
    pkg && track
      ? createHazards({
          root,
          track,
          entities: pkg.meta.entities ?? [],
          routes: pkg.route.routes,
          makeGround,
          sfx,
          cfg: tuning.hazards as HazardConfig,
          karts: entrants.length,
          quiet: demo,
          clock: () => race?.clock ?? 0,
          lap: () => {
            const r = race?.racers[0];
            return r ? { lap: r.lap, laps: tuning.race.laps, finished: r.finished } : undefined;
          },
        })
      : undefined;

  // Drift Park: which loop you start on ([ and ] step through them), which way round
  // (F flips), and your drift streak.
  let parkLoop = park ? Math.min(park.loops.length - 1, Math.max(0, opts.parkLoop ?? 0)) : 0;
  let parkReverse = false;
  const streak = park ? createStreak(park) : undefined;
  const streakLocator = park ? createLocator(park) : undefined;
  const parkBestKey = (i: number) =>
    `kartipelago.driftBest.${park!.loops[i]!.size.id}.${park!.loops[i]!.variant}`;
  if (park && streak)
    park.loops.forEach((_, i) => {
      try {
        streak.best[i] = Number(localStorage.getItem(parkBestKey(i))) || 0;
      } catch {
        // no storage: bests last for this visit only
      }
    });
  const saveParkBest = (i: number) => {
    try {
      localStorage.setItem(parkBestKey(i), String(streak!.best[i]));
    } catch {
      // not saved
    }
  };

  const snapPrev = (e: Entrant) => {
    const s = e.state;
    Object.assign(e.prev, { x: s.x, y: s.y, z: s.z, heading: s.heading, velAngle: s.velAngle });
  };
  /** Put every kart in its starting spot. The player starts at the front of the grid. */
  const placeKarts = () => {
    entrants.forEach((e, i) => {
      let spot = { x: courseData.start.x, y: 0, z: courseData.start.z, heading: 0 };
      if (track) spot = gridSlot(track, i);
      if (park) spot = loopStart(park.loops[parkLoop]!, parkReverse);
      Object.assign(e.state, createKartState(spot.x, spot.z, spot.heading, spot.y));
      e.state.y = e.ground.at(spot.x, spot.z, spot.y + 0.5).height;
      Object.assign(e.items, racerItems());
      loops?.reset(i);
      snapPrev(e);
      if (e.driver) {
        e.driver.driftHeld = false;
        e.driver.index = 0;
      }
      // After a finish the player's kart is driven by the AI; a restart hands it back.
      if (i === 0 && !demo) e.driver = undefined;
    });
  };

  const newRace = (): Race | undefined =>
    track ? createRace(track, tuning.race, entrants.length) : undefined;
  let race = newRace();
  placeKarts();
  /** The race position on the HUD, smoothed (see hud()). */
  let shownPlace = { shown: 1, pending: 1, since: 0 };
  /** Debug: the checkpoint gates drawn in the world (G toggles them). */
  let gateView: CheckpointView | undefined =
    race && ctx.devKeys && !demo ? createCheckpointView(root, race.course) : undefined;

  // HUD: the speedometer (unitless; see render/speedo.ts) and the debug timing bar.
  const startMeter = createStartMeter(hudRoot);
  const speedometer = createSpeedometer(hudRoot);
  let toast: { text: string; until: number } | undefined;
  const showToast = (text: string, seconds: number) => {
    toast = { text, until: performance.now() + seconds * 1000 };
  };

  let pathCurvature = 0;
  let youAccel = 0;
  /** Seconds since start, for water and lava animation. */
  let fxClock = 0;
  /** Camera angle for the demo's orbit. */
  let orbit = 0;
  let finishedAt: number | undefined;
  let lastPhase: number = ZIP.NORMAL;
  let lookMode = opts.lookMode;

  // Key events only request changes; they're applied on the fixed step, like all gameplay.
  let resetRequested = false;
  let pickRequested: Character | undefined;
  let bananaLossRequested = false;
  let bananaAddRequested = 0;
  if (!demo)
    listen((e) => {
      if (e.repeat) return;
      if (park && (e.code === "BracketLeft" || e.code === "BracketRight")) {
        const n = park.loops.length;
        parkLoop = (parkLoop + (e.code === "BracketRight" ? 1 : -1) + n) % n;
        resetRequested = true;
      }
      if (park && e.code === "KeyF") {
        parkReverse = !parkReverse;
        resetRequested = true;
      }
      if (!ctx.devKeys) return;
      if (debug.overlay.visible && e.code === "KeyL") bananaLossRequested = true;
      if (debug.overlay.visible && e.code === "KeyK") bananaAddRequested++;
      // M flips between the legacy and offset drift models, for side-by-side comparison.
      if (e.code === "KeyM") tuning.vehicle.driftModel = tuning.vehicle.driftModel >= 1 ? 0 : 1;
      // G shows the invisible checkpoint gates (debug).
      if (e.code === "KeyG" && gateView) gateView.visible = !gateView.visible;
      const n = /^Digit([1-9])$/.exec(e.code);
      if (n) pickRequested = characters[Number(n[1]) - 1];
    });

  const normalTop = (
    cfg: { topSpeed: number } & Parameters<typeof bananaScales>[1],
    k: KartState,
  ) => cfg.topSpeed * bananaScales(k.bananas, cfg).top;

  /** Sound and messages for item events. Hits are heard when they're near you. */
  function itemFeedback(ev: ItemEvent) {
    const vol = itemsCfg.volume;
    const me = you.state;
    const near = (j: number) => {
      const k = entrants[j]!.state;
      return j === 0 || Math.hypot(k.x - me.x, k.z - me.z) < 60;
    };
    if (ev.type === "hit") {
      const k = entrants[ev.racer]!.state;
      if (ev.lost) dropBananas(bananaField, k, ev.lost, tuning.bananas);
    }
    if (demo) return;
    if (ev.type === "pickup") {
      if (ev.racer === 0) sfx.balloon(vol, ev.result, you.items.held.level, ev.color);
    } else if (ev.type === "noTarget") {
      sfx.fizz(vol);
      showToast("No target in range", 1);
    } else if (ev.type === "fire") {
      if (ev.racer !== 0) return;
      if (ev.color === "blue") {
        sfx.blueBoost(vol, ev.level, itemsCfg.blue3ChargeSec);
        if (ev.enhanced) sfx.enhanced(vol);
      } else if (ev.color === "red") sfx.missile(vol);
      else if (ev.color === "green") sfx.drop(vol);
      else if (ev.color === "yellow") sfx.shield(vol);
      else sfx.magnet(vol);
    } else if (ev.type === "hit") {
      if (!near(ev.racer)) return;
      if (ev.blocked) sfx.shieldBlock(vol);
      else if (ev.kind === "oil") sfx.oil(vol);
      else if (ev.kind === "shield") sfx.shieldZap(vol);
      else if (ev.kind === "bubble") sfx.bubble(vol);
      else sfx.explosion(vol);
      if (ev.racer === 0 && ev.lost) sfx.bananaLost(tuning.bananas.volume);
    }
  }

  /** The player's boost cues: a blip as the rainbow window opens, a puff as the push ends. */
  function boostCues() {
    const phase = you.state.zipPhase;
    const vol = itemsCfg.volume;
    if (!demo) {
      if (phase === ZIP.ENDING && lastPhase !== ZIP.ENDING) sfx.rainbow(vol);
      const wasPushing = lastPhase === ZIP.ACTIVE || lastPhase === ZIP.ENDING;
      if (wasPushing && (phase === ZIP.RECOVERY || phase === ZIP.NORMAL)) sfx.boostEnd(vol);
    }
    lastPhase = phase;
  }

  /** Count collected bananas; the player hears each one, and a fanfare at the cap. */
  function gotBananas(i: number, n: number) {
    const s = entrants[i]!.state;
    const full = tuning.vehicle.bananaMaxEffective;
    const before = s.bananas;
    s.bananas += n;
    if (i !== 0 || demo) return;
    sfx.banana(tuning.bananas.volume);
    if (before < full && s.bananas >= full) {
      sfx.bananaMilestone(tuning.bananas.volume);
      showToast(`${full} eggs! Full speed bonus`, 1.6);
    }
  }

  function restart() {
    resetRequested = true;
  }

  function update(dt: number) {
    lastStepAt = performance.now();
    if (resetRequested) {
      resetRequested = false;
      race = newRace();
      placeKarts();
      shownPlace = { shown: 1, pending: 1, since: 0 };
      if (gateView && race) {
        const was = gateView.visible;
        gateView.dispose();
        gateView = createCheckpointView(root, race.course);
        gateView.visible = was;
      }
      resetBananaField(bananaField);
      resetItemWorld(itemWorld);
      if (course) resetCourse(course);
      finishedAt = undefined;
    }
    if (bananaAddRequested) {
      gotBananas(0, bananaAddRequested);
      bananaAddRequested = 0;
    }
    if (bananaLossRequested) {
      bananaLossRequested = false;
      const lost = loseBananas(you.state, "debug", tuning.bananas);
      dropBananas(bananaField, you.state, lost, tuning.bananas);
      if (lost) sfx.bananaLost(tuning.bananas.volume);
    }
    if (pickRequested) {
      you.character = pickRequested;
      you.color = pickRequested.color;
      pickRequested = undefined;
    }
    for (const e of entrants) snapPrev(e);
    const pathBefore = you.state.velAngle;
    const speedBefore = you.state.speed;
    const posBefore = { x: you.state.x, z: you.state.z };
    if (race) tickRace(race, dt);

    // Keyboard steering responds differently while you're drifting (finer taps).
    const held = demo ? NEUTRAL : input.sample(dt, you.state.driftDir !== 0);
    const moment = race && {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startRefHz: tuning.race.startRefHz,
    };
    const walls = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
    // Rebuilt each step so live tuning edits apply immediately.
    const racers: Racer[] = entrants.map((e, i) => {
      let cfg = applyCharacter(tuning.vehicle, e.character, tuning.stats);
      if (e.driver && (i > 0 || demo))
        cfg = { ...cfg, topSpeed: cfg.topSpeed * tuning.ai.speedMult };
      // Imported tracks: the surface under the wheels scales speed, acceleration and grip.
      if (pkg && e.state.grounded && !loops?.riding(i)) {
        const surface = e.ground.at(e.state.x, e.state.z, e.state.y).surface;
        cfg = applySurface(cfg, surface ? SURFACES[surface] : undefined);
      }
      return { kart: e.state, items: e.items, cfg };
    });
    const progressOf = (j: number) => {
      if (!race) return 0;
      const at = loops?.riding(j) ? loops.racePos(j, entrants[j]!.state) : entrants[j]!.state;
      return progress(race, j, at.x, at.z, at.y);
    };
    const events: ItemEvent[] = [];
    if (!demo && boostLab.equip(you.items.held)) sfx.balloon(itemsCfg.volume, "new");
    const canGo = !race || canDrive(race);

    entrants.forEach((e, i) => {
      const { cfg } = racers[i]!;
      const onLoop = loops?.riding(i) ?? false;
      let want =
        e.driver && moment
          ? driveAi(
              e.driver,
              onLoop ? { ...e.state, ...loops!.racePos(i, e.state) } : e.state,
              cfg,
              tuning.ai,
              moment,
              loops?.aim(i, e.state),
            )
          : held;
      // On a loop the AI holds the middle of the road.
      if (onLoop && e.driver) want = { ...want, steer: loops!.aiSteer(i) };
      if (i === 0 && !e.driver) {
        // The debug boost lab can script the throttle for a few seconds after a boost.
        const scripted = boostLab.throttle(e.state.zipPhase);
        if (scripted !== undefined) want = { ...want, throttle: scripted };
        // Items fire when the button is released, with the throttle as it is right then.
        if (itemReleased(racers[0]!, want.item) && canGo) {
          if (e.items.held.color === "blue") {
            boostLab.started(`Blue ${e.items.held.level}`, e.state.speed, normalTop(cfg, e.state));
            want = { ...want, throttle: boostLab.throttle(ZIP.ACTIVE) ?? want.throttle };
          }
          const ev = fireItem(itemWorld, racers, 0, want.throttle, itemsCfg, progressOf);
          if (ev) events.push(ev);
        }
      }
      // Trapped in a bubble: no control until it pops.
      if (e.items.bubbleTime > 0) want = { ...NEUTRAL };
      // During the countdown every kart sits on the line.
      stepImpacts(e.state, tuning.collision, dt);
      const before = { x: e.state.x, y: e.state.y, z: e.state.z };
      const drive = canGo ? want : NEUTRAL;
      stepKart(e.state, loops ? loops.input(i, e.state, drive) : drive, cfg, dt);
      // Riding a loop: it moves the kart along its road itself (no walls, no ground).
      if (onLoop) loops!.step(i, e.state, before, drive.steer, cfg, dt);
      else if (enteredZipper(e.state, zippers)) {
        let throttle = want.throttle;
        if (i === 0 && !e.driver) {
          boostLab.started("Zipper", e.state.speed, normalTop(cfg, e.state));
          throttle = boostLab.throttle(ZIP.ACTIVE) ?? throttle;
        }
        startZipper(e.state, throttle, cfg);
      }
      if (!onLoop) {
        if (!OPEN) stepWalls(e.state, e.ground, walls, dt);
        if (pkg) stepMeshWalls(e.state, pkg.collision, walls, dt);
        stepSolids(e.state, solids, walls, dt);
        if (hazards) stepSolids(e.state, hazards.solids, walls, dt);
        stepVertical(e.state, e.ground, tuning.physics, dt);
        // Driven onto a loop this step?
        if (loops?.step(i, e.state, before, drive.steer, cfg, dt).entered && i === 0 && !demo)
          sfx.loop(itemsCfg.volume);
      }
      if (pkg && !loops?.riding(i)) {
        // Boost surfaces fire a zipper boost when you drive onto them.
        const surface = e.ground.at(e.state.x, e.state.z, e.state.y).surface;
        const onBoost = Boolean(e.state.grounded && surface && SURFACES[surface]?.boost);
        if (onBoost && !e.onBoost) startZipper(e.state, want.throttle, cfg);
        e.onBoost = onBoost;
      }
      const held0 = e.state.bananas;
      const got = collectBananas(bananaField, i, e.state, tuning.bananas);
      if (got.length) {
        pickupsToShow.push(...got);
        e.state.bananas = held0;
        gotBananas(i, got.length);
      }
      if (course && i === 0) stepCourse(course, e.state, tuning.course, cfg, dt);
      if (!race) return;

      const riding = loops?.riding(i) ?? false;
      const onRoad = riding || e.ground.at(e.state.x, e.state.z, e.state.y).onRoad;
      const raceEvents = stepRacer(
        race,
        i,
        riding ? { ...e.state, ...loops!.racePos(i, e.state) } : e.state,
        onRoad,
        want.throttle,
        tuning.race,
        dt,
      );
      if (raceEvents.boost) {
        // The start boost: launched at a multiple of top speed, held for a while (the
        // strength the start boost has always had; only its timing is new).
        applyBoost(e.state, cfg, raceEvents.boost.mult, raceEvents.boost.seconds);
        if (i === 0 && !demo) sfx.startBoost(itemsCfg.volume, raceEvents.boost.tier === "strong");
      }
      // Lava, deep water, waterfalls (hazards.ts), then: fell off an imported track's
      // geometry, or onto another respawn surface: back to the last checkpoint (or where
      // a respawn zone says, past a jump's gap).
      const under =
        pkg && !riding ? e.ground.at(e.state.x, e.state.z, e.state.y).surface : undefined;
      const lastGate = respawnSpot(race, i);
      if (hazards && !riding) {
        const hz = hazards.stepKart(i, e.state, under, lastGate, dt);
        if (hz.burnt) e.racer.react("burn");
        if (hz.splashed === "deep") e.racer.react("splash");
        if (hz.struck) e.racer.react("burn");
        if (hz.respawned) {
          loops?.reset(i);
          snapPrev(e);
          teleported(race, i, e.state);
        }
      }
      const surfaceDef =
        pkg && e.state.grounded && !hazards?.handles(under) ? SURFACES[under ?? ""] : undefined;
      const fell =
        pkg && !riding && (e.state.y < pkg.killY || surfaceDef?.respawn)
          ? (hazards?.respawnSpot(e.state.x, e.state.y, e.state.z) ?? lastGate)
          : undefined;
      if (raceEvents.respawn || fell) {
        const g = (raceEvents.respawn ?? fell)!;
        const bananas = e.state.bananas; // a respawn keeps what you've collected
        Object.assign(e.state, createKartState(g.x, g.z, g.heading, g.y));
        e.state.bananas = bananas;
        loops?.reset(i);
        snapPrev(e);
        teleported(race, i, e.state); // a respawn never passes (or un-passes) a gate
      }
    });
    // Over the line: the AI takes the wheel for a lap of honour while the results show.
    if (race && race.racers[0]!.finished && finishedAt === undefined) {
      finishedAt = race.clock;
      if (line && !you.driver) {
        you.driver = createDriver(line, 0, tuning.ai);
        you.driver.index = 0;
      }
    }
    hazards?.step(
      entrants.map((e) => e.state),
      dt,
    );
    // Karts on loops bump each other along the loop's road instead.
    const free = entrants.filter((_, i) => !loops?.riding(i));
    bumpKarts(
      free.map((e) => e.state),
      tuning.physics.kartBump,
      free.map((e) => bumpMass(e.items, itemsCfg)),
      (a, b) => {
        // A shielded kart that touches an unshielded one spins it out (either way round).
        const ia = entrants.indexOf(free[a]!);
        const ib = entrants.indexOf(free[b]!);
        const hit = shieldRam(racers[ia]!, racers[ib]!, ia, ib, itemsCfg, tuning.bananas);
        if (hit)
          itemFeedback({
            type: "hit",
            racer: hit.victim,
            kind: "shield",
            blocked: false,
            lost: hit.lost,
          });
      },
    );
    loops?.contacts(entrants.map((e) => e.state));
    stepEffects(racers, itemsCfg, dt);
    if (park && streak && streakLocator) {
      // Drift streak: distance round the loop in one unbroken drift, on the road.
      const k = you.state;
      const before = streak.loop;
      const bestBefore = before >= 0 ? streak.best[before]! : 0;
      const laps = stepStreak(
        streak,
        park,
        streakLocator.at(k.x, k.z),
        k.driftDir !== 0 && k.spinTime <= 0,
      );
      if (laps)
        showToast(laps === 1 ? "A whole lap in one drift!" : `${laps} laps in one drift!`, 1.6);
      if (before >= 0 && streak.best[before]! > bestBefore && (laps || streak.held === 0))
        saveParkBest(before);
    }
    events.push(
      ...collectBalloons(itemWorld, racers, itemsCfg, (j) => j === 0 || itemsCfg.aiCollect),
      ...stepItemWorld(itemWorld, racers, itemsCfg, tuning.bananas, dt, progressOf),
    );
    for (const ev of events) itemFeedback(ev);
    stepBananaField(bananaField, tuning.bananas, dt);
    // Telemetry: how sharply the player's path is curving (1/m), for the debug overlay.
    const moved = Math.hypot(you.state.x - posBefore.x, you.state.z - posBefore.z);
    if (moved > 1e-3) pathCurvature = wrapAngle(you.state.velAngle - pathBefore) / moved;
    youAccel = (you.state.speed - speedBefore) / dt;
    if (!demo) boostLab.record(dt, you.state.speed, moved, you.state.zipPhase);
    boostCues();
  }

  // Visual tilt: sit flat on the surface when grounded; in the air, pitch with the arc
  // of the jump. Smoothed, so bumps and landings don't snap the mesh.
  const tilt = { up: new THREE.Vector3(), fwd: new THREE.Vector3(), right: new THREE.Vector3() };
  const tiltBasis = new THREE.Matrix4();
  const tiltTarget = new THREE.Quaternion();
  function renderKart(e: Entrant, alpha: number, frameSeconds: number) {
    const { state: s, prev: p, mesh } = e;
    const heading = p.heading + wrapAngle(s.heading - p.heading) * alpha;
    const pose = loops?.pose(entrants.indexOf(e), alpha);
    if (pose) {
      // On a loop: sat on the road wherever it faces, upside down at the top.
      const { up, fwd, right } = tilt;
      up.set(pose.ux, pose.uy, pose.uz);
      fwd.set(pose.fx, pose.fy, pose.fz);
      const lift = e.items.bubbleTime > 0 ? 0.8 : 0;
      mesh.position.set(pose.x + up.x * lift, pose.y + up.y * lift, pose.z + up.z * lift);
      right.crossVectors(up, fwd).normalize();
      fwd.crossVectors(right, up).normalize();
      tiltBasis.makeBasis(right, up, fwd);
      tiltTarget.setFromRotationMatrix(tiltBasis);
      mesh.quaternion.slerp(tiltTarget, 1 - Math.exp(-40 * frameSeconds));
      e.racer.shadow.visible = false;
      e.racer.animate(frameSeconds, motionOf(s), nearestRival(e));
      flames(e);
      return;
    }
    e.racer.shadow.visible = true;
    mesh.position.set(
      p.x + (s.x - p.x) * alpha,
      // The kart model's origin is where its wheels touch the ground, so it sits right on
      // the physics contact height (it once floated 0.4 m: the old placeholder box's
      // centre height).
      p.y +
        (s.y - p.y) * alpha +
        (e.items.bubbleTime > 0 ? 0.8 : 0) -
        (hazards?.sinkOf(entrants.indexOf(e)) ?? 0),
      p.z + (s.z - p.z) * alpha,
    );
    const { up, fwd, right } = tilt;
    fwd.set(Math.sin(heading), 0, Math.cos(heading));
    if (s.grounded) up.set(s.nx, s.ny, s.nz);
    else
      up.set(0, 1, 0)
        .addScaledVector(fwd, -s.vy / Math.max(8, Math.abs(s.speed)))
        .normalize();
    right.crossVectors(up, fwd).normalize();
    fwd.crossVectors(right, up).normalize();
    tiltBasis.makeBasis(right, up, fwd);
    tiltTarget.setFromRotationMatrix(tiltBasis);
    mesh.quaternion.slerp(tiltTarget, 1 - Math.exp(-14 * frameSeconds));

    // The blob shadow stays on the ground under the kart, smaller the higher it flies.
    const r = e.racer;
    const groundY = e.ground.at(mesh.position.x, mesh.position.z, mesh.position.y).height;
    r.placeShadow(mesh.position.x, groundY, mesh.position.z, heading, mesh.position.y - groundY);
    // Character and kart animation: a visual layer on top of the physics state.
    r.animate(frameSeconds, motionOf(s), nearestRival(e));
    flames(e);
  }

  function flames(e: Entrant) {
    const s = e.state;

    // Exhaust: the colour says which boost (zipper amber; blue balloons orange / blue /
    // purple by level), a green core says the enhanced boost took, rainbow says "press
    // the throttle now", and a small dim flame means the push has ended.
    const z = s.zipPhase;
    const color = FLAME_COLORS[s.zipSource] ?? FLAME_COLORS[0]!;
    const pushing = z === ZIP.ACTIVE || z === ZIP.ENDING;
    e.racer.flame.visible = z !== ZIP.NORMAL;
    e.racer.core.visible = pushing && s.zipEnhanced && z !== ZIP.ENDING;
    if (z === ZIP.ENDING) {
      e.racer.flameMat.color.setHSL((performance.now() / 250) % 1, 1, 0.6);
      e.racer.flame.scale.setScalar(1.5);
    } else if (z === ZIP.ACTIVE) {
      e.racer.flameMat.color.set(color);
      let size = s.zipEnhanced ? 1.35 : 1;
      // Level 3 blue: the flame builds while its sound charges (the push already started).
      const sinceStart = s.zipTotal - s.zipTime;
      if (s.zipSource === BOOST_SOURCE.BLUE3 && sinceStart < itemsCfg.blue3ChargeSec) {
        const f = sinceStart / itemsCfg.blue3ChargeSec;
        size *= 0.4 + 0.6 * f + 0.1 * Math.sin(performance.now() / 20);
      }
      e.racer.flame.scale.setScalar(size);
    } else if (z === ZIP.RECOVERY) {
      e.racer.flameMat.color.set(color);
      e.racer.flame.scale.setScalar(0.55);
    }
    e.racer.flameMat.opacity = z === ZIP.RECOVERY ? 0.45 : 0.9;
  }

  /** The nearest other racer within glancing distance, in this racer's local frame. */
  function nearestRival(e: Entrant): { x: number; z: number } | null {
    const s = e.state;
    let best: { x: number; z: number } | null = null;
    let bestD = 15;
    for (const o of entrants) {
      if (o === e) continue;
      const dx = o.state.x - s.x;
      const dz = o.state.z - s.z;
      const d = Math.hypot(dx, dz);
      if (d >= bestD) continue;
      bestD = d;
      const c = Math.cos(s.heading);
      const sn = Math.sin(s.heading);
      best = { x: dx * c - dz * sn, z: dx * sn + dz * c };
    }
    return best;
  }

  // The loop camera: on a loop it rides the road a little way behind the kart, rolling
  // with it, so the world turns over as you go upside down. It blends in from the chase
  // camera as you drive on, and back out once you (and it) are off the loop.
  let loopCamW = 0;
  const railPos = new THREE.Vector3();
  const railLook = new THREE.Vector3();
  const railUp = new THREE.Vector3();
  const blendUp = new THREE.Vector3();
  function loopCamera(alpha: number, frameSeconds: number) {
    if (!loops) return;
    const { camera: cam } = tuning;
    const view = loops.rail(0, you.state, alpha, {
      distance: cam.distance,
      height: cam.height * 0.8,
      lookHeight: cam.lookHeight,
      lookAhead: cam.lookAhead + 2,
      keep: loopCamW > 0.01,
    });
    const target = view?.hold ? 1 : 0;
    loopCamW += (target - loopCamW) * (1 - Math.exp(-(target ? 7 : 4) * frameSeconds));
    if (!view || loopCamW < 0.002) {
      loopCamW = view ? loopCamW : 0;
      return;
    }
    const w = loopCamW;
    railPos.set(view.px, view.py, view.pz);
    railLook.set(view.lx, view.ly, view.lz);
    railUp.set(view.ux, view.uy, view.uz);
    const camera = stage.camera;
    camera.position.lerpVectors(chase.pos, railPos, w);
    blendUp.set(0, 1, 0).lerp(railUp, w).normalize();
    camera.up.copy(blendUp);
    camera.lookAt(railLook.lerp(chase.look, 1 - w));
  }

  const orbitTarget = new THREE.Vector3();
  let resultsShown = false;
  function render(alpha: number, frameSeconds: number) {
    const { camera, world, vehicle } = tuning;
    // Racers who've crossed the line celebrate (a podium) or slump (the rest).
    const anyDone = race?.racers.some((r) => r.finished) ?? false;
    if (race && (anyDone || resultsShown)) {
      const order = standings(race, racePositions());
      entrants.forEach((e, i) =>
        e.racer.setResult(race!.racers[i]!.finished ? order.indexOf(i) + 1 : null, entrants.length),
      );
      resultsShown = anyDone;
    }
    for (const e of entrants) renderKart(e, alpha, frameSeconds);
    skidSound();
    hazards?.render(fxClock, frameSeconds, you.mesh.position);
    groundMat.color.set(park ? PARK_GROUND : (trackData.groundColor ?? world.groundColor));
    sceneryView?.render(tuning.scenery);
    fxClock += frameSeconds;
    pkg?.materials.update(fxClock);

    const s = you.state;
    const p = you.prev;
    const x = p.x + (s.x - p.x) * alpha;
    const y = p.y + (s.y - p.y) * alpha;
    const z = p.z + (s.z - p.z) * alpha;
    const heading = p.heading + wrapAngle(s.heading - p.heading) * alpha;
    const velAngle = p.velAngle + wrapAngle(s.velAngle - p.velAngle) * alpha;
    stage.followSun(x, z);
    stage.camera.fov = camera.fov;
    stage.camera.updateProjectionMatrix();
    if (demo) {
      // Title screen: a slow orbit round the lead kart, a little above it.
      orbit += frameSeconds * 0.16;
      orbitTarget.lerp(new THREE.Vector3(x, y + 1.2, z), orbitTarget.lengthSq() ? 0.08 : 1);
      const r = 11 + 2.5 * Math.sin(orbit * 0.7);
      stage.camera.position.set(
        orbitTarget.x + Math.sin(heading + orbit) * r,
        orbitTarget.y + 3.6 + Math.sin(orbit * 0.5) * 1.2,
        orbitTarget.z + Math.cos(heading + orbit) * r,
      );
      stage.camera.lookAt(orbitTarget);
    } else {
      // On a loop the chase camera follows the kart's place on the straight beneath, so
      // it's settled behind it when the loop camera hands back.
      const ride = loops?.riding(0) ? loops.rides[0]! : undefined;
      const at = ride ? loops!.racePos(0, s) : { x, y, z };
      const yaw = ride
        ? loops!.paths[ride.loop]!.heading + (ride.dir > 0 ? 0 : Math.PI) + ride.rel
        : 0;
      chase.update(
        {
          x: at.x,
          y: at.y,
          z: at.z,
          heading: ride ? yaw : heading,
          velAngle: ride ? yaw : velAngle,
          speedFrac: s.speed / vehicle.topSpeed,
        },
        camera,
        frameSeconds,
      );
      loopCamera(alpha, frameSeconds);
    }

    const now = performance.now() / 1000;
    courseView?.render(now, tuning.course);
    trackView?.render(tuning.track);
    for (const v of parkViews) v.render(tuning.track);
    for (const pk of pickupsToShow.splice(0)) bananaView.burst(pk);
    bananaView.render(bananaField, tuning.bananas, now, frameSeconds);
    itemView.render(
      itemWorld,
      entrants.map((e) => e.mesh.position),
      entrants.map((e) => e.items),
      now,
    );
    if (!demo) {
      ctx.boostLab.render(debug.overlay.visible);
      renderSpeedometer();
      startMeter.render(race, tuning.race, ctx.showTiming);
      if (debug.overlay.visible) debugReadout(frameSeconds);
      if (race) gateView?.update(race.racers[0]!);
    }
    if (toast && performance.now() > toast.until) toast = undefined;
  }

  function renderSpeedometer() {
    const s = you.state;
    const value = speedoValue(s.speed, tuning.hud, tuning.vehicle);
    const dialMax = tuning.hud.speedoDialMax;
    const pushing = s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING;
    speedometer.update({
      value,
      needleDeg: needleDeg(value, dialMax),
      dialMax,
      chevrons: boostChevrons(pushing, s.zipTime, s.zipTotal),
      color: FLAME_COLORS[s.zipSource] ?? FLAME_COLORS[0]!,
      rainbow: s.zipPhase === ZIP.ENDING,
      enhanced: pushing && s.zipEnhanced,
    });
  }

  function debugReadout(frameSeconds: number) {
    const s = you.state;
    if (race) {
      // Race progression: why you are (or aren't) gaining places.
      const r = race.racers[0]!;
      const order = standings(race, racePositions());
      const n = race.course.length;
      const ev = r.lastEvent;
      debug.overlay.set(
        "race",
        `lap ${Math.min(r.lap, tuning.race.laps)} (${r.completedLaps} done)  place ${order.indexOf(0) + 1}/${entrants.length}  route ${r.activeRoute}`,
      );
      debug.overlay.set(
        "cp",
        `next ${race.course[r.next]!.gates[0]!.id}  last ${r.lastGate.id}  passed ${r.passed} (best ${r.best}) of ${n}/lap`,
      );
      debug.overlay.set(
        "seg",
        `${Math.round(segmentProgress(race.course, r, s) * 100)}% to the next  (G shows gates)`,
      );
      debug.overlay.set("cross", ev ? `${ev.kind} ${ev.gate}${ev.why ? `: ${ev.why}` : ""}` : "-");
    }
    debug.overlay.set("speed", `${s.speed.toFixed(1)} m/s`);
    debug.overlay.set("slip", `${((slipAngle(s) * 180) / Math.PI).toFixed(1)}°`);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
    debug.overlay.set("air", s.grounded ? "-" : `${s.y.toFixed(1)} m`);
    debug.overlay.set("tap", `${Math.round(s.tapCharge * 100)}%`);
    const phases = ["normal", "ACTIVE", "ENDING (rainbow)", "recovery"];
    const youCfg = applyCharacter(tuning.vehicle, you.character, tuning.stats);
    debug.overlay.set("class", `${you.character.name} (1-${characters.length})`);
    debug.overlay.set("max", `${youCfg.topSpeed.toFixed(1)} m/s`);
    debug.overlay.set(
      "zip",
      s.zipPhase ? `${phases[s.zipPhase]} ${s.zipEnhanced ? "enhanced" : "ordinary"}` : "-",
    );
    debug.overlay.set(
      "zipT",
      s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING
        ? `${s.zipTime.toFixed(2)}s left`
        : "-",
    );
    debug.overlay.set(
      "zipPw",
      `${Math.round(s.zipPower * 100)}%  released ${s.zipReleasedAtStart ? "yes" : "no"}  early ${s.zipPressedEarly ? "yes" : "no"}`,
    );
    debug.overlay.set("accel", `${youAccel.toFixed(1)} m/s²`);
    const bs = bananaScales(s.bananas, tuning.vehicle);
    debug.overlay.set(
      "banana",
      `${s.bananas} held, ${effectiveBananas(s.bananas, tuning.vehicle)} effective, ×${bananaMult(s.bananas, tuning.vehicle).toFixed(3)}  (L lose 2, K add 1)`,
    );
    debug.overlay.set(
      "banTop",
      `${(youCfg.topSpeed * bs.top).toFixed(1)} m/s top, accel ×${bs.accel.toFixed(3)}`,
    );
    const it = you.items;
    debug.overlay.set(
      "item",
      `${heldLabel(it.held)}  shield ${it.shieldTime > 0 ? `L${it.shieldLevel} ${it.shieldTime.toFixed(1)}s` : "-"}  (B equip test)`,
    );
    debug.overlay.set(
      "boost",
      s.zipPhase
        ? `${["zipper", "blue 1", "blue 2", "blue 3"][s.zipSource]} ${phases[s.zipPhase]}`
        : s.boostTime > 0
          ? `boost ×${s.boostMult.toFixed(2)} ${s.boostTime.toFixed(1)}s`
          : "-",
    );
    debug.overlay.set(
      "lat",
      `${(Math.abs(s.speed) * Math.sin(Math.abs(slipAngle(s)))).toFixed(1)} m/s`,
    );
    const model = tuning.vehicle.driftModel >= 1 ? "offset" : "legacy";
    debug.overlay.set("model", `${model} (M)`);
    debug.overlay.set("stick", s.steerSmooth.toFixed(2));
    const pathRate = Math.abs(s.speed) * Math.abs(pathCurvature);
    debug.overlay.set(
      "arc",
      pathRate > 0.02 ? `${(Math.abs(s.speed) / pathRate).toFixed(0)} m` : "-",
    );
    debug.overlay.set("offs", `${((s.driftOffset * 180) / Math.PI).toFixed(0)}°`);
    debug.overlay.set("spin", s.spinTime > 0 ? "SPIN" : `${s.counterTime.toFixed(2)}s`);
    const tiers = ["-", "light", "moderate", "CRASH"];
    debug.overlay.set(
      "hit",
      s.lastImpactTier ? `${tiers[s.lastImpactTier]} ${s.lastImpactSpeed.toFixed(1)} m/s` : "-",
    );
    debug.overlay.set(
      "drift",
      s.driftDir === 0 ? "-" : `${s.driftDir > 0 ? "R" : "L"} ${s.driftTime.toFixed(1)}s`,
    );
    debug.overlay.frame(frameSeconds);
  }

  /** Everything the pixel HUD shows. */
  function hud(): HudState {
    const s = you.state;
    const base = {
      racers: entrants.length,
      bananas: s.bananas,
      item: heldLabel(you.items.held),
      held: you.items.held.color
        ? { color: you.items.held.color, level: you.items.held.level, ammo: you.items.held.ammo }
        : null,
      toast: toast?.text,
      laps: tuning.race.laps,
    };
    if (!race) {
      const on = park && streak ? (streak.loop >= 0 ? streak.loop : parkLoop) : 0;
      return {
        ...base,
        phase: "practice",
        countdown: 0,
        sinceGo: 99,
        lap: 0,
        lapTime: 0,
        totalTime: 0,
        finished: false,
        park:
          park && streak
            ? {
                loop: park.loops[on]!.name,
                streak: streakLaps(streak, park),
                best: streak.best[on]!,
                turning: parkReverse ? "right" : "left",
              }
            : undefined,
      };
    }
    const r = race.racers[0]!;
    const order = standings(race, racePositions());
    // The place shown changes only once the new one has held for a moment, so two karts
    // side by side don't make it flicker.
    const now = order.indexOf(0) + 1;
    if (now !== shownPlace.pending) shownPlace = { ...shownPlace, pending: now, since: race.clock };
    if (
      now !== shownPlace.shown &&
      (race.clock - shownPlace.since > 0.25 || r.finished || race.phase === "countdown")
    )
      shownPlace.shown = now;
    return {
      ...base,
      phase: race.phase,
      countdown: race.phase === "countdown" ? -race.clock : 0,
      sinceGo: race.phase === "countdown" ? 0 : race.clock,
      startTier: r.start?.tier,
      position: entrants.length > 1 ? shownPlace.shown : undefined,
      lap: Math.min(r.lap, tuning.race.laps),
      lapTime: lapClock(race, 0),
      bestLap: r.bestLap,
      totalTime: r.finished ? (r.totalTime ?? 0) : Math.max(0, race.clock),
      finished: r.finished,
    };
  }

  /** The player's result, once they've crossed the line. */
  function result(): RaceResult | undefined {
    if (!race || !race.racers[0]!.finished) return undefined;
    const r = race.racers[0]!;
    const order = standings(race, racePositions());
    return {
      position: entrants.length > 1 ? order.indexOf(0) + 1 : undefined,
      racers: entrants.length,
      totalTime: r.totalTime ?? 0,
      lapTimes: [...r.lapTimes],
      bestLap: r.bestLap ?? Math.min(...r.lapTimes),
      order: order.map((i) => ({
        name: entrants[i]!.name,
        racer: entrants[i]!.look,
        time: race!.racers[i]!.finished ? race!.racers[i]!.totalTime : undefined,
        you: i === 0,
      })),
    };
  }

  // Imported tracks reload live: T, or the dev server telling us the Blender add-on
  // exported (see main.ts).
  let reloading = false;
  async function reloadTrack() {
    if (!pkg || !opts.packageId || !track || reloading || disposed) return;
    reloading = true;
    try {
      const next = await loadTrackPackage(
        urlReader(packageBase(opts.packageId), String(Date.now())),
        { mode: lookMode },
      );
      if (disposed) {
        disposeObject(next.visual);
        return;
      }
      swapPackage(root, pkg, next);
      stage.setEnvironment(next.look);
      // Everything built from the route: the centre line, start line, AI racing line.
      Object.assign(trackData, next.trackData);
      trackData.gates = next.trackData.gates; // checkpoints may have been removed
      Object.assign(track, buildTrack(trackData, tuning.track.sampleSpacing));
      trackView?.dispose();
      trackView = createTrackView(root, track, tuning.track, zippers, { surface: false });
      line = lineOf(track);
      lapLines = lapLinesOf(next);
      entrants.forEach((e, i) => {
        if (!e.driver) return;
        e.driver.line = i > 0 ? lineFor(i) : line!;
        e.driver.index = 0;
      });
      for (const w of next.warnings) console.warn(`[track] ${w}`);
      resetRequested = true; // restart the race on the new geometry
      showToast(
        next.warnings.length
          ? `Track reloaded (${next.warnings.length} warnings: see the console)`
          : "Track reloaded",
        2,
      );
    } catch (err) {
      console.error(err);
      showToast(`Reload failed: ${(err as Error).message}`, 5);
    } finally {
      reloading = false;
    }
  }
  if (!demo)
    listen((e) => {
      if (e.code === "KeyT" && !e.repeat && pkg) void reloadTrack();
    });

  let disposed = false;

  // Your tyres skidding: a squeal while you drift (or slide hard), louder the more you
  // slide, higher at speed; a bark of the tyres going into a drift. Silent while the
  // race isn't running (paused, or in the demo).
  let skid: ReturnType<typeof sfx.skid>;
  let lastStepAt = 0;
  let lastDrift = 0;
  function skidSound() {
    const s = you.state;
    const running = !demo && performance.now() - lastStepAt < 120;
    const slide = Math.abs(wrapAngle(s.heading - s.velAngle));
    const fast = Math.min(1, s.speed / 18);
    const on = running && s.grounded && s.speed > 5 && (s.driftDir !== 0 || slide > 0.4);
    const level = on ? Math.min(1, 0.55 + slide * 0.9) * fast : 0;
    if (on && s.driftDir !== 0 && lastDrift === 0) sfx.skidChirp(itemsCfg.volume);
    lastDrift = running ? s.driftDir : 0;
    if (level > 0) skid ??= sfx.skid();
    skid?.set(level, fast * 0.7 + Math.min(1, slide) * 0.3);
  }
  /** Remove everything this session added (3D, HUD, listeners) and free GPU memory. */
  function dispose() {
    if (disposed) return;
    disposed = true;
    skid?.stop();
    abort.abort();
    hazards?.dispose();
    gateView?.dispose();
    stage.scene.remove(root);
    disposeObject(root);
    trackView?.dispose();
    hudRoot.remove();
    stage.setEnvironment(undefined);
  }

  if (packageError) showToast(packageError, 8);
  else if (pkg?.warnings.length)
    showToast(`${pkg.warnings.length} track warnings: see the console`, 4);

  return {
    update,
    render,
    restart,
    dispose,
    reloadTrack,
    hud,
    result,
    /** Seconds since the player finished (undefined while racing). */
    finishedFor: () => (finishedAt === undefined || !race ? undefined : race.clock - finishedAt),
    /**
     * Developer tool (?debug, screenshots and tests): finish racer `index` right now, as
     * if they'd just crossed the line on their last lap. Finish rivals first to set
     * the order.
     */
    debugFinish(index = 0) {
      if (!race) return;
      const r = race.racers[index];
      if (!r || r.finished) return;
      const clock = Math.max(race.clock, 30 + index);
      race.clock = clock;
      r.lapTimes = Array.from(
        { length: tuning.race.laps },
        (_, i) => clock / tuning.race.laps + (i - 1) * 0.37,
      );
      r.bestLap = Math.min(...r.lapTimes);
      r.totalTime = clock;
      r.finished = true;
      race.finishOrder.push(index);
    },
    setLookMode(mode: LookMode) {
      lookMode = mode;
      pkg?.materials.setMode(mode);
    },
    get packageId() {
      return opts.packageId;
    },
    get trackName() {
      return park ? "Drift Park" : SCENE === "practice" ? "Practice" : trackData.name;
    },
    get disposed() {
      return disposed;
    },
    showToast,
    /** Testing and demos: let the AI drive the player's kart. */
    autopilot() {
      if (line && !you.driver) you.driver = createDriver(line, 0, tuning.ai);
    },
    /** For tests and debugging (?debug). */
    /** Course hazards and creatures (Blender tracks), for the debug tools. */
    hazards,
    entrants,
    root,
    get race() {
      return race;
    },
  };
}
