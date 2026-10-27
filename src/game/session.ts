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
import { createBossMech, hasBossMech, parseBossMech } from "./bossMech";
import * as THREE from "three";
import { tuning } from "../core/tuning";
import { NEUTRAL, type DeviceReading, type Input } from "../core/input";
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
import { activateBlue } from "../items/boosts";
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
import { ENGINE_VOICE, type Sfx } from "../audio/sfx";
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
import { createBoostFx } from "../render/boostFx";
import { buildRacingLine } from "../ai/racingLine";
import { createDriver, driveAi, type AiWorld, type Driver } from "../ai/driver";
import { createAiDebug } from "../debug/aiDebug";
import { aiItem } from "../ai/items";
import { rivalSkill, type SkillConfig } from "../ai/skill";
import rivalSetups from "../../assets/data/rivals.json";
import { catchUp, type CatchUpConfig } from "../ai/catchup";
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
import { DRAGON_PALETTES } from "../render/racers/roster/dragon";
import {
  autoCoinSpots,
  coinsTaken,
  collectCoins,
  createCoinField,
  createCoinView,
  resetCoins,
  type CoinSpot,
} from "./coins";
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
import { basisOf, fingerprint, tiltOf, type GhostChoice, type GhostSample } from "./ghost";
import { createGhostRunner, type GhostRunner } from "./ghostRunner";
import { createGhostStore, type GhostStore } from "../app/ghostStore";

/** Saved Time Trial ghosts (one store for the whole game). */
let ghostStore: GhostStore | undefined;

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
  /** The course's id (track menu), for its saved Time Trial ghost. */
  trackId?: string;
  /** Time Trial: race your personal best ghost, or none. */
  ghost?: GhostChoice;
  /**
   * If an imported track can't load: fall back to Drift Loop (the old URL behaviour),
   * instead of failing.
   */
  fallback?: boolean;
  /** Adventure's treasure map challenge: map fragments on the course ("auto": four spread
   * round the lap). */
  coins?: CoinSpot[] | "auto";
  /** Adventure: the field. How many rivals, their names on screen, and a top-speed
   * multiplier for them (a boss's advantage; 1 = none). */
  field?: {
    count?: number;
    names?: string[];
    speed?: number;
    /** The rivals' looks in order (alt: the alternate paint, a local cousin; palette: a
     * dragon's colours, render/racers/roster/dragon.ts; boss: a huge dragon on foot,
     * render/racers/bossDragon.ts). */
    looks?: { id: RacerId; alt: boolean; palette?: string; boss?: boolean }[];
    /** The rivals' catch-up instead of the field's (a boss waits for you more, like the
     * old kart racers' bosses: src/ai/catchup.ts). */
    catchUp?: Partial<CatchUpConfig>;
  };
  /** Adventure: the player's name on screen (the Chosen One's race). */
  playerName?: string;
  /** The overworld (src/overworld): drive the course's land freely. No countdown, no laps
   * to finish, no clock on screen, no rivals and no Time Trial (the race underneath only
   * keeps the respawns working). */
  freeRoam?: boolean;
  /** A mini-game (src/game/minigames.ts): free roam with rivals, who drive by the game's
   * own minds (`drive`: what rival i does this step, undefined for the race AI; `fire`:
   * whether it uses its item now), and the game hears the item events. */
  arena?: ArenaHooks;
  /** A boss race's mechanic: its main one or its alternative (game/bossMech.ts). */
  bossVariant?: "main" | "alt";
}

export interface ArenaHooks {
  drive?(i: number, kart: KartState, dt: number): DeviceReading | undefined;
  fire?(i: number, kart: KartState): boolean;
  onItem?(ev: ItemEvent): void;
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
  /** Your boost, for the screen's speed lines: 0 none, 0.7 pushing, 1 enhanced. */
  boost: number;
  boostColor: string;
  /** The rainbow window (press the throttle now). */
  rainbow: boolean;
  /** The held balloon, for the item box's icon (null when holding nothing). */
  held: { color: BalloonColor; level: number; ammo: number } | null;
  /** Drift Park: loop name, current drift streak (laps), best streak, direction. */
  park?: { loop: string; streak: number; best: number; turning: "left" | "right" };
  toast?: string;
  /** Time Trial: the ghost on or off, its (personal best) time, and the gap to it at the
   * last checkpoint while that's showing (negative: ahead). */
  ghost?: { on: boolean; best?: number; delta?: number };
  /** Adventure: map fragments taken of all there are. */
  coins?: { got: number; total: number };
  /** A boss race's gauge (Cinderjaw's HEAT): 0..1. */
  gauge?: { label: string; value: number };
}

/** The player's finished race. */
export interface RaceResult {
  position?: number;
  racers: number;
  totalTime: number;
  lapTimes: number[];
  bestLap: number;
  /** Everyone's finishing order (names and times), when racing the AI. */
  order: { name: string; racer: RacerId; time?: number; you: boolean; slot: number }[];
  /** Adventure: map fragments taken of all there were. */
  coins?: { got: number; total: number };
}

interface Entrant {
  name: string;
  look: RacerId;
  character: Character;
  color: string;
  state: KartState;
  /** State at the previous step, for smooth rendering between steps. */
  prev: { x: number; y: number; z: number; heading: number; velAngle: number; roll: number };
  /** The kart's tilt onto the ground (smoothed), before the sharp turn's roll goes on top. */
  tiltQ: THREE.Quaternion;
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
  /** A rival's skill tier and racing style (for the AI debug view). */
  style?: { tier: string; style: string };
}

/** Exhaust colour by boost source: zipper, blue 1, blue 2, blue 3. */
const FLAME_COLORS = ["#ffb347", "#ff7b00", "#2f80ed", "#9b5de5"];
/** Any boost you let off the throttle for (enhanced): a red flame. */
const ENHANCED_FLAME = "#ff2a1a";
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
  /** Laps in a race: the track's own (track.json's race.laps: a boss race's one long lap,
   * say), else the usual. */
  const LAPS = pkg?.meta.race?.laps ?? tuning.race.laps;
  /** The race rules with the course's own lap count (a one-lap boss race ends after one). */
  const raceRules = () =>
    opts.freeRoam || opts.arena
      ? { ...tuning.race, laps: 1_000_000, readySec: 0 }
      : { ...tuning.race, laps: LAPS };
  const root = new THREE.Group();
  root.name = "session";
  stage.scene.add(root);
  stage.setEnvironment(pkg?.look);
  // The rivals' minds drawn over them (dev server only): ?aidebug.
  const aiDebug =
    import.meta.env.DEV && new URLSearchParams(location.search).has("aidebug")
      ? createAiDebug(root)
      : undefined;
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
  // Zipper pads lie on the ground under them (asked on the first frame, once it's built).
  const drapeOn = (x: number, z: number, y: number) => makeGround().at(x, z, y).height;
  let trackView = track
    ? createTrackView(root, track, tuning.track, zippers, { surface: !pkg, drape: drapeOn })
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
  // A Time Trial (racing on your own) keeps only the blue balloons: the boosts. The
  // weapons and shields have nobody to use them on.
  const timeTrial = SCENE === "track" && !opts.rivals && !demo && !opts.freeRoam && Boolean(track);
  for (const [t, s] of byRoute(trackData.balloons))
    itemWorld.balloons.push(
      ...createItemWorld(t, timeTrial ? s.filter((b) => b.color === "blue") : s, makeGround)
        .balloons,
    );
  const itemView = createItemView(root);
  // Adventure's map fragments (only the player takes them).
  const coinField =
    opts.coins && track
      ? createCoinField(track, opts.coins === "auto" ? autoCoinSpots(track.length) : opts.coins)
      : undefined;
  const coinView = coinField ? createCoinView(root, coinField) : undefined;
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
  const rivalLook = (
    i: number,
  ): { id: RacerId; alt: boolean; palette?: string; boss?: boolean } => {
    const set = opts.field?.looks?.[i - 1];
    if (set) return set;
    const others = RACER_IDS.filter((id) => id !== playerLook);
    return { id: others[(i - 1) % others.length]!, alt: i > others.length };
  };
  const makeRacer = (i: number): RacerView => {
    const look = i === 0 ? { id: playerLook, alt: false } : rivalLook(i);
    const palette = "palette" in look && look.palette ? DRAGON_PALETTES[look.palette] : undefined;
    const boss = "boss" in look && look.boss;
    const r = new RacerView(look.id, { alt: look.alt, seed: i * 17 + 5, palette, boss });
    root.add(r.root, r.shadow);
    return r;
  };

  const player = findCharacter(opts.character ?? roster.default);
  const rivals =
    track && opts.rivals ? roster.rivals.slice(0, opts.field?.count ?? roster.rivals.length) : [];
  // Each rival's skill and racing style (src/ai/skill.ts; tuning.ai.rivals by name).
  const skills = rivals.map((r) => rivalSkill(r.name, rivalSetups as SkillConfig));
  const entrants: Entrant[] = [
    { name: opts.playerName ?? DESIGNS[playerLook].name, character: player, color: player.color },
    ...rivals.map((r, i) => ({
      // The first rivals are the other racers; their alternate-paint cousins keep their
      // roster names. (Adventure can name them: a boss.)
      name:
        opts.field?.names?.[i] ??
        (opts.field?.looks
          ? opts.field.looks[i]?.alt
            ? r.name
            : DESIGNS[rivalLook(i + 1).id].name
          : i < RACER_IDS.length - 1
            ? DESIGNS[rivalLook(i + 1).id].name
            : r.name),
      // Every rival drives the player's kart: the racer you pick never changes the
      // driving, so a race is won by how it's driven (src/ai/skill.ts), not by a kart.
      character: player,
      color: r.color,
    })),
  ].map((e, i) => {
    const racer = makeRacer(i);
    return {
      ...e,
      look: i === 0 ? playerLook : rivalLook(i).id,
      state: createKartState(),
      prev: { x: 0, y: 0, z: 0, heading: 0, velAngle: 0, roll: 0 },
      tiltQ: new THREE.Quaternion(),
      racer,
      mesh: racer.root,
      items: racerItems(),
      ground: makeGround(),
      driver:
        (i > 0 || demo) && line
          ? createDriver(i > 0 ? lineFor(i) : line, i, tuning.ai, skills[i - 1]?.skill)
          : undefined,
      style: i > 0 ? skills[i - 1] : undefined,
    };
  });
  const you = entrants[0]!;
  // Loop-the-loops (src/game/loops.ts): each kart rides them in its own loop mode.
  const loops = pkg ? createLoops(pkg.meta.entities ?? [], entrants.length) : undefined;
  /** Each kart's last spot on the road, grounded (respawn zones look it up too). */
  const lastRoad = entrants.map(() => ({ x: NaN, y: NaN, z: NaN }));
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
            return r ? { lap: r.lap, laps: LAPS, finished: r.finished } : undefined;
          },
        })
      : undefined;

  // A boss race's mechanic (game/bossMech.ts): the fire sweeps and vents, the crumbling
  // road. On you only: the boss is its master.
  const mechCfg = pkg
    ? parseBossMech(pkg.meta.entities ?? [], opts.bossVariant ?? "main")
    : undefined;
  const roadAt = (d: number) => {
    const ss = track!.samples;
    const L = track!.length;
    const u = ((d % L) + L) % L;
    const q = ss[Math.min(ss.length - 1, Math.round((u / L) * ss.length) % ss.length)]!;
    return {
      x: q.pos.x,
      y: q.pos.y,
      z: q.pos.z,
      heading: Math.atan2(q.forward.x, q.forward.z),
      width: q.width,
    };
  };
  let lastItem = false;
  const bossMech =
    mechCfg && track && hasBossMech(mechCfg)
      ? createBossMech({ cfg: mechCfg, root: demo ? undefined : root, roadAt })
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
    Object.assign(e.prev, {
      x: s.x,
      y: s.y,
      z: s.z,
      heading: s.heading,
      velAngle: s.velAngle,
      roll: s.sharpRoll,
    });
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

  const newRace = (): Race | undefined => {
    const r = track ? createRace(track, raceRules(), entrants.length) : undefined;
    // (Free roam: leaving the road is the point, so it never puts you back.)
    if (r && (opts.freeRoam || opts.arena)) r.open = true;
    return r;
  };
  let race = newRace();
  placeKarts();

  // Time Trial: record this run, and race your saved best's ghost (ghostRunner.ts).
  const rollPivot = 0.98;
  const ghost: GhostRunner | undefined =
    timeTrial && race && opts.trackId
      ? createGhostRunner({
          root,
          store: (ghostStore ??= createGhostStore()),
          track: opts.trackId,
          // The layout: the centre line, the gates, the boosts on it.
          layout: fingerprint({
            p: trackData.points
              .filter((_, i) => i % 4 === 0)
              .map((q) => [Math.round(q.x * 2), Math.round((q.y ?? 0) * 2), Math.round(q.z * 2)]),
            g: race.course.length,
            z: trackData.zippers?.map((z) => [z.at, z.across]),
            b: trackData.balloons?.filter((b) => b.color === "blue").map((b) => [b.at, b.across]),
          }),
          // The physics: everything about how a kart drives.
          physics: fingerprint({
            v: tuning.vehicle,
            p: tuning.physics,
            c: tuning.collision,
            s: tuning.stats,
            laps: LAPS,
          }),
          racer: playerLook,
          character: player.id,
          hz: tuning.ghost.hz,
          opacity: tuning.ghost.opacity,
          choice: opts.ghost ?? "best",
          flames: ghostFlames,
          rollPivot,
        })
      : undefined;
  /** The player's kart as the race draws it, for the ghost's recording. */
  const ghostQ = new THREE.Quaternion();
  const sampleYou = (): GhostSample => {
    const s = you.state;
    const lp = loops?.pose(0, 1);
    if (lp) basisOf(lp.ux, lp.uy, lp.uz, lp.fx, lp.fy, lp.fz, ghostQ);
    else tiltOf(s, ghostQ);
    return {
      t: 0,
      x: lp ? lp.x : s.x,
      y: lp ? lp.y : s.y,
      z: lp ? lp.z : s.z,
      qx: ghostQ.x,
      qy: ghostQ.y,
      qz: ghostQ.z,
      qw: ghostQ.w,
      roll: s.sharpRoll,
      speed: s.speed,
      steer: s.steerSmooth,
      driftDir: s.driftDir,
      slip: wrapAngle(s.heading - s.velAngle),
      grounded: s.grounded,
      throttle: s.throttleOn,
      zipPhase: s.zipPhase,
      zipEnhanced: s.zipEnhanced,
      zipTime: s.zipTime,
      zipSource: s.zipSource,
      spinTime: s.spinTime,
    };
  };
  /** The ghost's exhaust flame (the same colours as yours, without the trail effects). */
  function ghostFlames(r: RacerView, s: GhostSample) {
    const z = s.zipPhase;
    const pushing = z === ZIP.ACTIVE || z === ZIP.ENDING;
    const dying = z === ZIP.RECOVERY ? Math.max(0, 1 - s.zipTime / 0.5) : 0;
    r.flame.visible = pushing || dying > 0;
    r.core.visible = pushing && s.zipEnhanced && z !== ZIP.ENDING;
    r.rainbowFlame(z === ZIP.ENDING, performance.now() / 1000);
    const color = s.zipEnhanced ? ENHANCED_FLAME : (FLAME_COLORS[s.zipSource] ?? FLAME_COLORS[0]!);
    if (z === ZIP.ENDING) r.flame.scale.setScalar(1.9);
    else if (z === ZIP.ACTIVE) {
      r.flameMat.color.set(color);
      r.flame.scale.setScalar(s.zipEnhanced ? 1.35 : 1);
    } else if (z === ZIP.RECOVERY) {
      r.flameMat.color.set(color);
      r.flame.scale.setScalar(0.25 + 0.4 * dying);
    }
    r.flameMat.opacity = (z === ZIP.RECOVERY ? 0.6 * dying : 0.9) * tuning.ghost.opacity;
    if (r.flame.visible) r.animateFlame(performance.now() / 1000, pushing ? 0.7 : 0.1);
  }
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
    opts.arena?.onItem?.(ev);
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

  /** The fixed step's length, for placing the ghost between steps. */
  let lastDt = 1 / 120;
  /** Extra seconds before the countdown after a restart. */
  const RESTART_PAUSE = 0.5;
  function restart() {
    resetRequested = true;
  }

  function update(dt: number) {
    lastStepAt = performance.now();
    if (resetRequested) {
      resetRequested = false;
      race = newRace();
      // A restart waits a breath before GET READY, so it doesn't start the instant the
      // menu closes.
      if (race) race.clock -= RESTART_PAUSE;
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
      if (coinField) resetCoins(coinField);
      if (course) resetCourse(course);
      finishedAt = undefined;
      ghost?.takeNewBest();
      ghost?.reset();
    }
    if (bananaAddRequested) {
      ghost?.invalidate();
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
    const progressOfEarly = (j: number) => {
      if (!race) return 0;
      const at = loops?.riding(j) ? loops.racePos(j, entrants[j]!.state) : entrants[j]!.state;
      return progress(race, j, at.x, at.z, at.y) * race.metresPerCheckpoint;
    };
    // Rebuilt each step so live tuning edits apply immediately.
    const racers: Racer[] = entrants.map((e, i) => {
      let cfg = applyCharacter(tuning.vehicle, e.character, tuning.stats);
      if (e.driver && (i > 0 || demo)) {
        // The field's trim, the rival's own (tiny) pace, and the bounded catch-up.
        const gap = race && i > 0 && !demo ? progressOfEarly(i) - progressOfEarly(0) : 0;
        const trim = tuning.ai.speedMult * e.driver.skill.pace;
        const assist = catchUp(gap, { ...(tuning.ai as CatchUpConfig), ...opts.field?.catchUp });
        const boss = i > 0 && !demo ? (opts.field?.speed ?? 1) : 1;
        cfg = { ...cfg, topSpeed: cfg.topSpeed * trim * assist * boss };
      }
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
      return progress(race, j, at.x, at.z, at.y) * race.metresPerCheckpoint;
    };
    const events: ItemEvent[] = [];
    if (!demo && boostLab.equip(you.items.held)) sfx.balloon(itemsCfg.volume, "new");
    const canGo = !race || canDrive(race);

    // What the rivals can see of the race: the other karts, the pads, the traps.
    const padsSeen = zippers.map((z) => ({ x: z.x, y: z.y, z: z.z }));
    const aiWorldFor = (i: number): AiWorld => ({
      others: entrants
        .filter((_, j) => j !== i)
        .map((o) => ({
          x: o.state.x,
          y: o.state.y,
          z: o.state.z,
          speed: o.state.speed,
          heading: o.state.heading,
          shield: o.items.shieldTime > 0,
        })),
      pads: padsSeen,
      traps: itemWorld.traps,
    });
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
              aiWorldFor(i),
              dt,
            )
          : held;
      // A mini-game's own minds drive its rivals (and choose when to fire).
      const own = i > 0 && opts.arena?.drive?.(i, e.state, dt);
      if (own) want = own;
      if (i > 0 && opts.arena?.fire && race && canGo && !moment?.countdown) {
        if (e.items.held.color && opts.arena.fire(i, e.state)) {
          const ev = fireItem(itemWorld, racers, i, want.throttle, itemsCfg, progressOf);
          if (ev) events.push(ev);
        }
      }
      // Rivals use their items too (the same fireItem, ammo and rules as the player).
      else if (e.driver && i > 0 && race && canGo && !moment?.countdown) {
        const it = aiItem(e.driver, i, racers, itemWorld, itemsCfg, progressOf, dt);
        if (it.fire) {
          const ev = fireItem(
            itemWorld,
            racers,
            i,
            it.lift ? 0 : want.throttle,
            itemsCfg,
            progressOf,
          );
          if (ev) {
            events.push(ev);
            if (ev.type === "fire" && ev.color === "blue") e.driver.boostTechnique = it.lift;
          }
        }
      }
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
        if (i === 0 && !demo) sfx.zipper(itemsCfg.volume);
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
        if (onBoost && !e.onBoost) {
          startZipper(e.state, want.throttle, cfg);
          if (i === 0 && !demo) sfx.zipper(itemsCfg.volume);
        }
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
        raceRules(),
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
      const road = lastRoad[i]!;
      if (onRoad && !riding && e.state.grounded)
        [road.x, road.y, road.z] = [e.state.x, e.state.y, e.state.z];
      if (hazards && !riding) {
        const hz = hazards.stepKart(i, e.state, under, lastGate, dt, road);
        if (hz.burnt) e.racer.react("burn");
        if (hz.splashed === "deep") e.racer.react("splash");
        if (hz.struck) e.racer.react("burn");
        // A present bursts into confetti and gives a small boost: a level 1 blue balloon's.
        if (hz.smashed) {
          activateBlue(e.state, 1, drive.throttle, cfg, itemsCfg);
          if (i === 0 && !demo) sfx.blueBoost(itemsCfg.volume, 1, itemsCfg.blue3ChargeSec);
        }
        if (hz.respawned) {
          loops?.reset(i);
          snapPrev(e);
          teleported(race, i, e.state);
        }
      }
      if (bossMech && i === 0 && race && !riding) {
        const lead = Math.max(...entrants.map((_, j) => progressOf(j)));
        const boss = entrants[1]?.state;
        const mv = bossMech.step(e.state, race.clock, dt, progressOf(0), lead, track!.length, {
          boss: boss && { x: boss.x, y: boss.y, z: boss.z },
          item: want.item && !lastItem,
          airborne: !e.state.grounded,
        });
        lastItem = want.item;
        if (mv.burnt || mv.overheated) e.racer.react("burn");
        if (mv.splashed || mv.buried) e.racer.react("splash");
        if (mv.bumped && !demo) sfx.explosion(itemsCfg.volume * 0.25);
        if (mv.boosted) {
          startZipper(e.state, want.throttle, cfg);
          if (!demo) sfx.zipper(itemsCfg.volume);
        }
        if (mv.reflected && !demo) sfx.enhanced(itemsCfg.volume);
        if (mv.bossHit && boss) {
          boss.spinTime = 1.2;
          boss.spinDir = 1;
          boss.speed *= 0.3;
        }
        if (mv.overheated && !demo) sfx.explosion(itemsCfg.volume * 0.6);
        if (mv.vented) {
          startZipper(e.state, want.throttle, cfg);
          if (!demo) sfx.zipper(itemsCfg.volume);
        }
        if (mv.dropAt !== undefined) {
          const p = roadAt(mv.dropAt);
          const bananas = e.state.bananas;
          Object.assign(e.state, createKartState(p.x, p.z, p.heading, p.y + 0.5));
          e.state.bananas = bananas;
          e.racer.react("burn");
          snapPrev(e);
          teleported(race, i, e.state);
        }
      }
      const surfaceDef =
        pkg && e.state.grounded && !hazards?.handles(under) ? SURFACES[under ?? ""] : undefined;
      const fell =
        pkg && !riding && (e.state.y < pkg.killY || surfaceDef?.respawn)
          ? (hazards?.respawnSpot(e.state.x, e.state.y, e.state.z, road) ?? lastGate)
          : undefined;
      // A rival lost off the road for a long while (src/ai/driver.ts): its checkpoint.
      const lost = e.driver?.wantsRespawn && !riding ? lastGate : undefined;
      if (e.driver) e.driver.wantsRespawn = false;
      if (raceEvents.respawn || fell || lost) {
        const g = (raceEvents.respawn ?? fell ?? lost)!;
        const bananas = e.state.bananas; // a respawn keeps what you've collected
        Object.assign(e.state, createKartState(g.x, g.z, g.heading, g.y));
        e.state.bananas = bananas;
        loops?.reset(i);
        snapPrev(e);
        teleported(race, i, e.state); // a respawn never passes (or un-passes) a gate
      }
    });
    if (ghost && race) {
      const r = race.racers[0]!;
      ghost.step(race.clock, r.best, r.finished, sampleYou);
      if (r.finished && finishedAt === undefined)
        void ghost.finish(race.clock, r.totalTime ?? race.clock, r.lapTimes, LAPS, sampleYou);
    }
    lastDt = dt;
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
    if (coinField && race && race.phase === "racing" && !race.racers[0]!.finished) {
      const got = collectCoins(coinField, you.state.x, you.state.y, you.state.z);
      if (got) {
        const n = coinsTaken(coinField);
        const all = coinField.coins.length;
        sfx.balloon(itemsCfg.volume, "new");
        showToast(
          n === all ? `ALL ${all} MAP FRAGMENTS! NOW WIN!` : `MAP FRAGMENT ${n}/${all}`,
          1.6,
        );
      }
    }
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
  const rollQ = new THREE.Quaternion();
  const rollShift = new THREE.Vector3();
  const FORWARD = new THREE.Vector3(0, 0, 1);
  /** Half the kart's width at the outer edge of its rear tyres (CHASSIS), m. */
  const ROLL_PIVOT = 0.98;
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
      e.tiltQ.copy(mesh.quaternion);
      e.racer.shadow.visible = false;
      e.racer.animate(frameSeconds, motionOf(s), nearestRival(e));
      flames(e, frameSeconds);
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
    e.tiltQ.slerp(tiltTarget, 1 - Math.exp(-14 * frameSeconds));
    mesh.quaternion.copy(e.tiltQ);
    // The sharp turn: the whole kart (chassis, wheels, driver) rolls onto its outside
    // wheels, pivoting on their outer edge so they stay on the ground. Visual only.
    const roll = p.roll + (s.sharpRoll - p.roll) * alpha;
    if (roll !== 0) {
      rollQ.setFromAxisAngle(FORWARD, roll);
      mesh.quaternion.multiply(rollQ);
      const px = -Math.sign(roll) * ROLL_PIVOT;
      rollShift.set(px * (1 - Math.cos(roll)), -px * Math.sin(roll), 0).applyQuaternion(e.tiltQ);
      mesh.position.add(rollShift);
    }

    // The blob shadow stays on the ground under the kart, smaller the higher it flies.
    const r = e.racer;
    const g = e.ground.at(mesh.position.x, mesh.position.z, mesh.position.y + 0.5);
    r.placeShadow(
      mesh.position.x,
      g.height,
      mesh.position.z,
      heading,
      mesh.position.y - g.height,
      g.nx,
      g.ny,
      g.nz,
    );
    // Character and kart animation: a visual layer on top of the physics state.
    r.animate(frameSeconds, motionOf(s), nearestRival(e));
    flames(e, frameSeconds);
  }

  function flames(e: Entrant, frameSeconds: number) {
    const s = e.state;

    // Exhaust: the colour says which boost (zipper amber; blue balloons orange / blue /
    // purple by level). A red flame with a white-hot core says you let off the throttle
    // in time and the enhanced boost took; rainbow says "press the throttle now"; a small
    // dim flame means the push has ended.
    const z = s.zipPhase;
    const color = s.zipEnhanced ? ENHANCED_FLAME : (FLAME_COLORS[s.zipSource] ?? FLAME_COLORS[0]!);
    const pushing = z === ZIP.ACTIVE || z === ZIP.ENDING;
    // After the push, a small flame dies away over half a second. (The recovery itself
    // can go on much longer, while the extra speed bleeds off: it once kept the flame lit
    // all that time, as if the boost were still going.)
    const dying = z === ZIP.RECOVERY ? Math.max(0, 1 - s.zipTime / 0.5) : 0;
    e.racer.flame.visible = pushing || dying > 0;
    e.racer.core.visible = pushing && s.zipEnhanced && z !== ZIP.ENDING;
    e.racer.rainbowFlame(z === ZIP.ENDING, performance.now() / 1000);
    if (z === ZIP.ENDING) {
      // The rainbow window: a big flame, every layer a different colour, cycling fast and
      // pulsing, so "press the throttle now" can't be missed.
      const pulse = 1 + 0.18 * Math.sin(performance.now() / 45);
      e.racer.flame.scale.setScalar(1.9 * pulse);
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
      e.racer.flame.scale.setScalar(0.25 + 0.4 * dying);
    }
    e.racer.flameMat.opacity = z === ZIP.RECOVERY ? 0.6 * dying : 0.9;
    boostFx.update(
      entrants.indexOf(e),
      e.mesh,
      { pushing, color, enhanced: s.zipEnhanced, rainbow: z === ZIP.ENDING },
      performance.now() / 1000,
      frameSeconds,
    );
    if (e.racer.flame.visible)
      e.racer.animateFlame(
        performance.now() / 1000 + entrants.indexOf(e) * 0.37,
        pushing ? (s.zipEnhanced ? 1 : 0.7) : 0.1,
      );
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
  /** Boost light trails and launch bursts. */
  const boostFx = createBoostFx(root);
  /** The camera's boost kick (0..1): it widens a little while your boost pushes. */
  let fovKick = 0;
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
    // The ghost, at the moment this frame shows (between the last two steps).
    if (ghost && race) ghost.render(race.clock - (1 - alpha) * lastDt, frameSeconds);
    aiDebug?.update(
      entrants.flatMap((e, i) =>
        e.driver && (i > 0 || demo)
          ? [
              {
                i,
                name: e.name,
                driver: e.driver,
                at: e.mesh.position,
                speed: e.state.speed,
                drifting: e.state.driftDir !== 0,
              },
            ]
          : [],
      ),
    );
    skidSound();
    hazards?.render(fxClock, frameSeconds, you.mesh.position);
    bossMech?.render(race?.clock ?? 0);
    // Scorchwind's sandstorm: the air thick with sand.
    const storm = bossMech?.fog() ?? 0;
    if (storm > 0 && stage.scene.fog instanceof THREE.Fog) {
      stage.scene.fog.color.set(0xc8a070);
      stage.scene.fog.near = 2;
      stage.scene.fog.far = 30 + (1 - storm) * 120;
    }
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
    // While your boost pushes the view widens a little (more for an enhanced boost), so
    // the speed lands; it eases back after.
    const boosting = !demo && (s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING);
    const kickTo = boosting ? (s.zipEnhanced ? 1 : 0.7) : 0;
    fovKick += (kickTo - fovKick) * (1 - Math.exp(-(kickTo > fovKick ? 8 : 2.5) * frameSeconds));
    stage.camera.fov = camera.fov + fovKick * 10;
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
    coinView?.render(now, frameSeconds);
    itemView.render(
      itemWorld,
      entrants.map((e) => e.mesh.position),
      entrants.map((e) => e.items),
      now,
      entrants.map((e) => e.mesh),
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
        `lap ${Math.min(r.lap, LAPS)} (${r.completedLaps} done)  place ${order.indexOf(0) + 1}/${entrants.length}  route ${r.activeRoute}`,
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
    debug.overlay.set(
      "sharp",
      s.sharp > 0.01
        ? `${Math.round(s.sharp * 100)}% roll ${((Math.abs(s.sharpRoll) * 180) / Math.PI).toFixed(0)}°`
        : "-",
    );
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
    debug.overlay.set("yaw", `${((pathRate * 180) / Math.PI).toFixed(0)}°/s`);
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
      boost: s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING ? (s.zipEnhanced ? 1 : 0.7) : 0,
      boostColor: FLAME_COLORS[s.zipSource] ?? FLAME_COLORS[0]!,
      rainbow: s.zipPhase === ZIP.ENDING,
      held: you.items.held.color
        ? { color: you.items.held.color, level: you.items.held.level, ammo: you.items.held.ammo }
        : null,
      toast: toast?.text,
      laps: LAPS,
      coins: coinField ? { got: coinsTaken(coinField), total: coinField.coins.length } : undefined,
      gauge: bossMech?.gauge(),
    };
    if (!race || opts.freeRoam || opts.arena) {
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
      lap: Math.min(r.lap, LAPS),
      lapTime: lapClock(race, 0),
      bestLap: r.bestLap,
      totalTime: r.finished ? (r.totalTime ?? 0) : Math.max(0, race.clock),
      finished: r.finished,
      ghost: ghost?.hud(race.clock),
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
      coins: coinField ? { got: coinsTaken(coinField), total: coinField.coins.length } : undefined,
      order: order.map((i) => ({
        name: entrants[i]!.name,
        racer: entrants[i]!.look,
        time: race!.racers[i]!.finished ? race!.racers[i]!.totalTime : undefined,
        you: i === 0,
        slot: i,
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
      trackView = createTrackView(root, track, tuning.track, zippers, {
        surface: false,
        drape: drapeOn,
      });
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

  // Your kart's sounds. The engine: a quiet hum rising with speed. The tyres (switched
  // off for now, DRIFT_SOUND): a squeal while you drift or slide hard and a bark going
  // into a drift. Silent while the race isn't running (paused, or in the demo).
  const DRIFT_SOUND = false;
  let skid: ReturnType<typeof sfx.skid>;
  let engine: ReturnType<typeof sfx.engine>;
  let lastStepAt = 0;
  let lastDrift = 0;
  function skidSound() {
    const s = you.state;
    const running = !demo && performance.now() - lastStepAt < 120;
    const slide = Math.abs(wrapAngle(s.heading - s.velAngle));
    const fast = Math.min(1, s.speed / 18);
    const on =
      DRIFT_SOUND && running && s.grounded && s.speed > 5 && (s.driftDir !== 0 || slide > 0.4);
    const level = on ? Math.min(1, 0.55 + slide * 0.9) * fast : 0;
    if (on && s.driftDir !== 0 && lastDrift === 0) sfx.skidChirp(itemsCfg.volume);
    lastDrift = running ? s.driftDir : 0;
    if (level > 0) skid ??= sfx.skid();
    skid?.set(level, fast * 0.7 + Math.min(1, slide) * 0.3);
    // The engine: a quiet hum that rises with speed (a little higher on boost).
    if (running) engine ??= sfx.engine(ENGINE_VOICE[playerLook] ?? 1);
    const pushing = s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING;
    const speedFrac = Math.abs(s.speed) / tuning.vehicle.topSpeed;
    engine?.set(
      running ? 0.45 + Math.min(1, speedFrac) * 0.55 : 0,
      speedFrac + (pushing ? 0.15 : 0),
    );
  }
  /** Remove everything this session added (3D, HUD, listeners) and free GPU memory. */
  function dispose() {
    if (disposed) return;
    disposed = true;
    ghost?.dispose();
    skid?.stop();
    engine?.stop();
    boostFx.dispose();
    abort.abort();
    hazards?.dispose();
    bossMech?.dispose();
    aiDebug?.dispose();
    gateView?.dispose();
    coinView?.dispose();
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
    /** Time Trial: is there a ghost system here, and turn the ghost on or off. */
    get timeTrial() {
      return Boolean(ghost);
    },
    get ghostChoice(): GhostChoice | undefined {
      return ghost?.choice;
    },
    setGhost(c: GhostChoice) {
      ghost?.setChoice(c);
    },
    /** For tests and debugging: the ghost runner itself. */
    ghostRunner: ghost,
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
      if (index === 0) ghost?.invalidate();
      const clock = Math.max(race.clock, 30 + index);
      race.clock = clock;
      r.lapTimes = Array.from({ length: LAPS }, (_, i) => clock / LAPS + (i - 1) * 0.37);
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
    /**
     * The review tool's "drive from here": put your kart on the ground at (x, z) (the
     * surface at or below height y) facing `heading`, stopped. If the race is still
     * counting down, it starts now.
     */
    placeYou(x: number, z: number, heading: number, y: number) {
      ghost?.invalidate();
      const g = you.ground.at(x, z, y);
      const bananas = you.state.bananas;
      Object.assign(you.state, createKartState(x, z, heading, g.height));
      you.state.bananas = bananas;
      loops?.reset(0);
      snapPrev(you);
      if (race) {
        teleported(race, 0, you.state);
        if (race.phase === "countdown") race.clock = -1e-4;
      }
    },
    /** Put kart i (a mini-game's start) at (x, z) facing `heading`. */
    place(i: number, x: number, z: number, heading: number, y = 200) {
      const e = entrants[i];
      if (!e) return;
      const g = e.ground.at(x, z, y);
      Object.assign(e.state, createKartState(x, z, heading, g.height));
      snapPrev(e);
      if (race) teleported(race, i, e.state);
    },
    /** Testing and demos: let the AI drive the player's kart. */
    autopilot() {
      if (line && !you.driver) you.driver = createDriver(line, 0, tuning.ai);
    },
    /** The lap's centre line (the overworld's map draws its ring road from it). */
    track,
    /** The solid things karts hit besides the track's own collision (the overworld adds
     * its puzzles' gates here, and takes them away again when they open). */
    solids,
    /** For tests and debugging (?debug). */
    /** Course hazards and creatures (Blender tracks), for the debug tools. */
    hazards,
    entrants,
    itemWorld,
    /** Adventure's map fragments (tests and debugging). */
    coins: coinField,
    zippers,
    root,
    /** The package's track.json entities (the overworld reads its villagers' homes). */
    entities: (pkg?.meta.entities ?? []) as unknown[],
    /** A fresh ground lookup of its own (for things walking about: villagers). */
    makeGround,
    get race() {
      return race;
    },
  };
}
