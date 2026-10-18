import * as THREE from "three";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput, NEUTRAL } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";
import { createStartMeter } from "./debug/startMeter";
import courseData from "../assets/data/course.json";
import driftLoop from "../assets/data/track.json";
import ribbonRidge from "../assets/data/track2.json";
import roster from "../assets/data/characters.json";
import { createChaseCamera } from "./render/chaseCamera";
import { createCourseView } from "./render/courseView";
import { createTrackView } from "./render/trackView";
import { createCourse, resetCourse, stepCourse } from "./world/course";
import { buildTrack, type TrackData } from "./world/track";
import { createTrackGround, flatGround, type GroundQuery } from "./physics/ground";
import { stepVertical } from "./physics/vertical";
import { stepWalls } from "./physics/walls";
import { bumpKarts } from "./physics/bump";
import { buildRacingLine } from "./ai/racingLine";
import { createDriver, driveAi, type Driver } from "./ai/driver";
import {
  canDrive,
  createRace,
  formatTime,
  lapClock,
  standings,
  startTarget,
  stepRacer,
  tickRace,
} from "./race/race";
import { gridSlot } from "./race/grid";
import { applyCharacter, type Character } from "./vehicles/character";
import {
  applyBoost,
  createKartState,
  slipAngle,
  stepKart,
  wrapAngle,
  type KartState,
} from "./vehicles/kart";

// Two scenes: a race on a track with seven AI rivals (default; pick the track with
// ?track=1 or ?track=2) and the M1 practice course of pickups and boost pads (open with
// ?scene=practice). Press R to restart.

const PARAMS = new URLSearchParams(location.search);
const SCENE = PARAMS.get("scene") === "practice" ? "practice" : "track";
// The start-boost timing bar is a tuning tool: only shown with ?timing in the URL.
const SHOW_TIMING = PARAMS.has("timing");
// Tracks: ?track=1 (Drift Loop, the default) or ?track=2 (Ribbon Ridge).
const TRACKS = [driftLoop, ribbonRidge] as TrackData[];
const trackData = TRACKS[Number(PARAMS.get("track") ?? 1) - 1] ?? TRACKS[0]!;
const GROUND_SIZE = 1200;
const GROUND_TILE = 5; // metres per grid square

const app = document.getElementById("app")!;
const stage = createStage(app);
const debug = createDebug(document.body);
const input = createInput();
const chase = createChaseCamera(stage.camera);

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

const groundMat = new THREE.MeshStandardMaterial({
  color: tuning.world.groundColor,
  map: groundTexture(),
});
const ground = new THREE.Mesh(new THREE.PlaneGeometry(GROUND_SIZE, GROUND_SIZE), groundMat);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
stage.scene.add(ground);

const course = SCENE === "practice" ? createCourse(courseData) : undefined;
const courseView = course ? createCourseView(stage.scene, course, tuning.course) : undefined;
const track = SCENE === "track" ? buildTrack(trackData, tuning.track.sampleSpacing) : undefined;
const trackView = track ? createTrackView(stage.scene, track, tuning.track) : undefined;
const line = track
  ? buildRacingLine(track, {
      margin: tuning.ai.lineMargin,
      span: tuning.ai.lineSpan,
      iterations: tuning.ai.lineIterations,
    })
  : undefined;

const characters = roster.characters as Character[];
const findCharacter = (id: string) => characters.find((c) => c.id === id) ?? characters[0]!;

/** A box kart with a darker nose, so you can tell which way is forward. */
function makeKartMesh() {
  const mat = new THREE.MeshStandardMaterial({ flatShading: true });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.8, 2.4), mat);
  mesh.castShadow = true;
  const nose = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, 0.3, 0.4),
    new THREE.MeshStandardMaterial({ color: "#333333", flatShading: true }),
  );
  nose.position.set(0, 0.2, 1.2);
  mesh.add(nose);
  stage.scene.add(mesh);
  return { mesh, mat };
}

interface Entrant {
  name: string;
  character: Character;
  color: string;
  state: KartState;
  /** State at the previous step, for smooth rendering between steps. */
  prev: { x: number; y: number; z: number; heading: number; velAngle: number };
  mesh: THREE.Mesh;
  mat: THREE.MeshStandardMaterial;
  /** Each kart keeps its own ground lookup (it remembers where on the track it was). */
  ground: GroundQuery;
  driver?: Driver;
}

const player = findCharacter(roster.default);
const rivals = track ? roster.rivals : [];
const entrants: Entrant[] = [
  { name: "You", character: player, color: player.color },
  ...rivals.map((r) => ({ name: r.name, character: findCharacter(r.character), color: r.color })),
].map((e, i) => {
  const { mesh, mat } = makeKartMesh();
  const state = createKartState();
  return {
    ...e,
    state,
    prev: { x: 0, y: 0, z: 0, heading: 0, velAngle: 0 },
    mesh,
    mat,
    ground: track ? createTrackGround(track) : flatGround,
    driver: i > 0 && line ? createDriver(line, i, tuning.ai) : undefined,
  };
});
const you = entrants[0]!;

/** Put every kart in its starting spot. The player starts at the back of the grid. */
function placeKarts() {
  entrants.forEach((e, i) => {
    let spot = { x: courseData.start.x, y: 0, z: courseData.start.z, heading: 0 };
    if (track) spot = gridSlot(track, i === 0 ? entrants.length - 1 : i - 1);
    Object.assign(e.state, createKartState(spot.x, spot.z, spot.heading, spot.y));
    e.state.y = e.ground.at(spot.x, spot.z).height;
    snapPrev(e);
    if (e.driver) e.driver.driftHeld = false;
  });
}
function snapPrev(e: Entrant) {
  const s = e.state;
  Object.assign(e.prev, { x: s.x, y: s.y, z: s.z, heading: s.heading, velAngle: s.velAngle });
}

const newRace = () => (track ? createRace(track, tuning.race, entrants.length) : undefined);
let race = newRace();
placeKarts();

// Always-on readout, plus big centred text for the start and the finish.
const hud = document.createElement("div");
hud.className = "hud";
document.body.appendChild(hud);
const startMeter = createStartMeter(document.body);
const banner = document.createElement("div");
banner.className = "banner";
document.body.appendChild(banner);

// Best lap ever on this track, kept in this browser only. Storage can be unavailable
// (private windows, blocked site data), so every access is guarded.
const bestKey = `kartipelago.bestLap.${trackData.name}`;
function loadBest(): number | undefined {
  try {
    const v = Number(localStorage.getItem(bestKey));
    return v > 0 ? v : undefined;
  } catch {
    return undefined;
  }
}
let bestEver = loadBest();
function saveBest(time: number) {
  if (bestEver !== undefined && bestEver <= time) return;
  bestEver = time;
  try {
    localStorage.setItem(bestKey, String(time));
  } catch {
    // Not saved; it still shows for this session.
  }
}

let pathCurvature = 0;

// Key events only request changes; they're applied on the fixed step, like all gameplay.
let resetRequested = false;
// Number keys pick your character (1 = first in characters.json, and so on).
let pickRequested: Character | undefined;
window.addEventListener("keydown", (e) => {
  if (e.code === "KeyR") resetRequested = true;
  // M flips between the legacy and offset drift models, for side-by-side comparison.
  if (e.code === "KeyM") tuning.vehicle.driftModel = tuning.vehicle.driftModel >= 1 ? 0 : 1;
  const n = /^Digit([1-9])$/.exec(e.code);
  if (n) pickRequested = characters[Number(n[1]) - 1];
});

const loop = createLoop(tuning.loop.physicsHz, tuning.loop.maxStepsPerFrame, {
  update(dt) {
    if (resetRequested) {
      resetRequested = false;
      race = newRace();
      placeKarts();
      if (course) resetCourse(course);
    }
    if (pickRequested) {
      you.character = pickRequested;
      you.color = pickRequested.color;
      pickRequested = undefined;
    }
    for (const e of entrants) snapPrev(e);
    const pathBefore = you.state.velAngle;
    const posBefore = { x: you.state.x, z: you.state.z };
    if (race) tickRace(race, dt);

    const held = input.sample(dt);
    const moment = race && {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startTarget: startTarget(tuning.race),
    };
    const walls = { ...tuning.physics, wallHeight: tuning.track.wallHeight };

    entrants.forEach((e, i) => {
      // Rebuilt each step so live tuning edits apply immediately.
      let cfg = applyCharacter(tuning.vehicle, e.character, tuning.stats);
      if (e.driver) cfg = { ...cfg, topSpeed: cfg.topSpeed * tuning.ai.speedMult };
      const want = e.driver && moment ? driveAi(e.driver, e.state, cfg, tuning.ai, moment) : held;
      // During the countdown every kart sits on the line.
      stepKart(e.state, !race || canDrive(race) ? want : NEUTRAL, cfg, dt);
      stepWalls(e.state, e.ground, walls, dt);
      stepVertical(e.state, e.ground, tuning.physics, dt);
      if (course && i === 0) stepCourse(course, e.state, tuning.course, cfg, dt);
      if (!race) return;

      const laps = race.racers[i]!.lapTimes.length;
      const onRoad = e.ground.at(e.state.x, e.state.z).onRoad;
      const events = stepRacer(race, i, e.state, onRoad, want.throttle, tuning.race, dt);
      if (i === 0 && race.racers[0]!.lapTimes.length > laps)
        saveBest(race.racers[0]!.lapTimes.at(-1)!);
      if (events.boost) applyBoost(e.state, cfg, events.boost.mult, events.boost.seconds);
      if (events.respawn) {
        const g = events.respawn;
        Object.assign(e.state, createKartState(g.x, g.z, g.heading, g.y));
        snapPrev(e);
      }
    });
    bumpKarts(
      entrants.map((e) => e.state),
      tuning.physics.kartBump,
    );
    // Telemetry: how sharply the player's path is curving (1/m), for the debug overlay.
    const moved = Math.hypot(you.state.x - posBefore.x, you.state.z - posBefore.z);
    if (moved > 1e-3) pathCurvature = wrapAngle(you.state.velAngle - pathBefore) / moved;
  },

  render(alpha, frameSeconds) {
    const { camera, world, vehicle } = tuning;
    for (const e of entrants) renderKart(e, alpha, frameSeconds);
    groundMat.color.set(world.groundColor);
    stage.scene.background = new THREE.Color(world.skyColor);

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
    chase.update(
      { x, y, z, heading, velAngle, speedFrac: s.speed / vehicle.topSpeed },
      camera,
      frameSeconds,
    );

    courseView?.render(performance.now() / 1000, tuning.course);
    trackView?.render(tuning.track);
    renderHud();
    startMeter.render(race, tuning.race, SHOW_TIMING);

    debug.overlay.set("speed", `${s.speed.toFixed(1)} m/s`);
    debug.overlay.set("slip", `${((slipAngle(s) * 180) / Math.PI).toFixed(1)}°`);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
    debug.overlay.set("air", s.grounded ? "-" : `${s.y.toFixed(1)} m`);
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
    debug.overlay.set(
      "drift",
      s.driftDir === 0 ? "-" : `${s.driftDir > 0 ? "R" : "L"} ${s.driftTime.toFixed(1)}s`,
    );
    debug.overlay.frame(frameSeconds);
    stage.render();
  },
});

// Visual tilt: sit flat on the surface when grounded; in the air, pitch with the arc of
// the jump. Smoothed, so bumps and landings don't snap the mesh.
const tilt = { up: new THREE.Vector3(), fwd: new THREE.Vector3(), right: new THREE.Vector3() };
const tiltBasis = new THREE.Matrix4();
const tiltTarget = new THREE.Quaternion();
function renderKart(e: Entrant, alpha: number, frameSeconds: number) {
  const { state: s, prev: p, mesh } = e;
  const heading = p.heading + wrapAngle(s.heading - p.heading) * alpha;
  mesh.position.set(
    p.x + (s.x - p.x) * alpha,
    p.y + (s.y - p.y) * alpha + 0.4,
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
  e.mat.color.set(e.color);
}

const ordinal = (n: number) =>
  `${n}${["th", "st", "nd", "rd"][n % 10 < 4 && Math.floor(n / 10) !== 1 ? n % 10 : 0]}`;

function renderHud() {
  const s = you.state;
  const parts = [you.character.name, `${s.speed.toFixed(0)} m/s`];
  if (course) parts.push(`Pickups ${course.collected}`);
  let order: number[] = [];
  if (race) {
    const r = race.racers[0]!;
    order = standings(
      race,
      entrants.map((e) => e.state),
    );
    parts.unshift(`${ordinal(order.indexOf(0) + 1)} / ${entrants.length}`);
    parts.push(`Lap ${Math.min(r.lap, tuning.race.laps)}/${tuning.race.laps}`);
    parts.push(formatTime(lapClock(race, 0)));
    if (r.bestLap !== undefined) parts.push(`Best ${formatTime(r.bestLap)}`);
    parts.unshift(trackData.name);
    if (bestEver !== undefined) parts.push(`Record ${formatTime(bestEver)}`);
  }
  parts.push(`1–${characters.length} character`, "R restart");
  hud.textContent = parts.join("  ·  ");

  let message = "";
  const r = race?.racers[0];
  if (race?.phase === "countdown") message = "Get ready!";
  else if (race && r?.finished) {
    // Finished racers keep their order; anyone still racing is listed by position.
    const rows = order.map((i, place) => {
      const racer = race!.racers[i]!;
      const time = racer.finished ? formatTime(racer.totalTime ?? 0) : "racing";
      return `${ordinal(place + 1).padEnd(4)} ${entrants[i]!.name.padEnd(8)} ${time}`;
    });
    message = `Finished ${ordinal(order.indexOf(0) + 1)}!\n${rows.join("\n")}\nR to race again`;
  } else if (race && race.clock < tuning.race.goShowSec) {
    const tier = r?.start?.tier;
    message =
      tier === "perfect" ? "GO!\nPerfect start!" : tier === "good" ? "GO!\nGood start" : "GO!";
  }
  banner.textContent = message;
  banner.hidden = message === "";
  banner.classList.toggle("standings", Boolean(r?.finished));
}

loop.start();
