import * as THREE from "three";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";
import { createStartMeter } from "./debug/startMeter";
import courseData from "../assets/data/course.json";
import trackData from "../assets/data/track.json";
import roster from "../assets/data/characters.json";
import { createChaseCamera } from "./render/chaseCamera";
import { createCourseView } from "./render/courseView";
import { createTrackView } from "./render/trackView";
import { createCourse, resetCourse, stepCourse } from "./world/course";
import { buildTrack, type TrackData } from "./world/track";
import { createTrackGround, flatGround } from "./physics/ground";
import { stepVertical } from "./physics/vertical";
import { stepWalls } from "./physics/walls";
import { NEUTRAL } from "./core/input";
import { canDrive, createRace, formatTime, lapClock, stepRace } from "./race/race";
import { applyCharacter, type Character } from "./vehicles/character";
import { applyBoost, createKartState, slipAngle, stepKart, wrapAngle } from "./vehicles/kart";

// Two scenes: the first track (default) and the M1 practice course of pickups and boost
// pads (open with ?scene=practice). Press R to reset to the start.

const SCENE =
  new URLSearchParams(location.search).get("scene") === "practice" ? "practice" : "track";
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

const characters = roster.characters as Character[];
let character = characters.find((c) => c.id === roster.default) ?? characters[0]!;

const kartMat = new THREE.MeshStandardMaterial({ color: character.color, flatShading: true });
const kart = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.8, 2.4), kartMat);
kart.castShadow = true;
// A darker nose so you can tell which way is forward.
const nose = new THREE.Mesh(
  new THREE.BoxGeometry(1.2, 0.3, 0.4),
  new THREE.MeshStandardMaterial({ color: "#333333", flatShading: true }),
);
nose.position.set(0, 0.2, 1.2);
kart.add(nose);
stage.scene.add(ground, kart);

const course = SCENE === "practice" ? createCourse(courseData) : undefined;
const courseView = course ? createCourseView(stage.scene, course, tuning.course) : undefined;
const track =
  SCENE === "track" ? buildTrack(trackData as TrackData, tuning.track.sampleSpacing) : undefined;
const trackView = track ? createTrackView(stage.scene, track, tuning.track) : undefined;

// Always-on readout so you can judge a line without opening the debug tools.
const hud = document.createElement("div");
hud.className = "hud";
document.body.appendChild(hud);

// Visual tilt: sit flat on the surface when grounded; in the air, pitch with the arc of
// the jump. Smoothed, so bumps and landings don't snap the mesh.
const tilt = { up: new THREE.Vector3(), fwd: new THREE.Vector3(), right: new THREE.Vector3() };
const tiltBasis = new THREE.Matrix4();
const tiltTarget = new THREE.Quaternion();
function tiltKart(heading: number, frameSeconds: number) {
  const { up, fwd, right } = tilt;
  fwd.set(Math.sin(heading), 0, Math.cos(heading));
  if (state.grounded) up.set(state.nx, state.ny, state.nz);
  else
    up.set(0, 1, 0)
      .addScaledVector(fwd, -state.vy / Math.max(8, Math.abs(state.speed)))
      .normalize();
  right.crossVectors(up, fwd).normalize();
  fwd.crossVectors(right, up).normalize();
  tiltBasis.makeBasis(right, up, fwd);
  tiltTarget.setFromRotationMatrix(tiltBasis);
  kart.quaternion.slerp(tiltTarget, 1 - Math.exp(-14 * frameSeconds));
}

// Simulation state lives apart from the meshes so rendering can interpolate.
const surface = track ? createTrackGround(track) : flatGround;
const start = track ? track.start : courseData.start;
const spawn = () =>
  createKartState(start.x, start.z, start.heading, surface.at(start.x, start.z).height);
const state = spawn();
const prev = { x: state.x, y: state.y, z: state.z, heading: 0, velAngle: 0 };
let simTime = 0;

// The race (track scene only): countdown, checkpoints, laps, finish, respawn.
const newRace = () => (track ? createRace(track, tuning.race) : undefined);
let race = newRace();

// Big centred text for the countdown and the finish.
// The start-boost timing bar is a tuning tool: only shown with ?timing in the URL.
const SHOW_TIMING = new URLSearchParams(location.search).has("timing");
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

// Reset is requested from a key event but applied on the fixed step, like all gameplay.
let resetRequested = false;
// Number keys pick a character (1 = first in characters.json, and so on).
let pickRequested: Character | undefined;
window.addEventListener("keydown", (e) => {
  if (e.code === "KeyR") resetRequested = true;
  const n = /^Digit([1-9])$/.exec(e.code);
  if (n) pickRequested = characters[Number(n[1]) - 1];
});

const loop = createLoop(tuning.loop.physicsHz, tuning.loop.maxStepsPerFrame, {
  update(dt) {
    if (resetRequested) {
      resetRequested = false;
      Object.assign(state, spawn());
      if (course) resetCourse(course);
      race = newRace();
    }
    prev.x = state.x;
    prev.y = state.y;
    prev.z = state.z;
    prev.heading = state.heading;
    prev.velAngle = state.velAngle;
    if (pickRequested) {
      character = pickRequested;
      pickRequested = undefined;
    }
    // Rebuilt each step so live tuning edits to the base kart apply immediately.
    const kartCfg = applyCharacter(tuning.vehicle, character, tuning.stats);
    const held = input.sample(dt);
    // During the countdown the kart sits on the line.
    stepKart(state, !race || canDrive(race) ? held : NEUTRAL, kartCfg, dt);
    stepWalls(state, surface, { ...tuning.physics, wallHeight: tuning.track.wallHeight }, dt);
    stepVertical(state, surface, tuning.physics, dt);
    if (course) stepCourse(course, state, tuning.course, kartCfg, dt);
    if (race) {
      const laps = race.lapTimes.length;
      const onRoad = surface.at(state.x, state.z).onRoad;
      const events = stepRace(race, state, onRoad, held.throttle, tuning.race, dt);
      if (race.lapTimes.length > laps) saveBest(race.lapTimes.at(-1)!);
      if (events.boost) applyBoost(state, kartCfg, events.boost.mult, events.boost.seconds);
      const respawnAt = events.respawn;
      if (respawnAt) {
        Object.assign(
          state,
          createKartState(respawnAt.x, respawnAt.z, respawnAt.heading, respawnAt.y),
        );
        Object.assign(prev, { x: state.x, y: state.y, z: state.z, heading: state.heading });
      }
    }
    simTime += dt;
  },
  render(alpha, frameSeconds) {
    const { camera, world, vehicle } = tuning;
    const x = prev.x + (state.x - prev.x) * alpha;
    const y = prev.y + (state.y - prev.y) * alpha;
    const z = prev.z + (state.z - prev.z) * alpha;
    const heading = prev.heading + wrapAngle(state.heading - prev.heading) * alpha;

    kart.position.set(x, y + 0.4, z);
    tiltKart(heading, frameSeconds);
    kartMat.color.set(character.color);
    groundMat.color.set(world.groundColor);
    stage.scene.background = new THREE.Color(world.skyColor);
    stage.followSun(x, z);

    stage.camera.fov = camera.fov;
    stage.camera.updateProjectionMatrix();
    const velAngle = prev.velAngle + wrapAngle(state.velAngle - prev.velAngle) * alpha;
    chase.update(
      { x, y, z, heading, velAngle, speedFrac: state.speed / vehicle.topSpeed },
      camera,
      frameSeconds,
    );

    courseView?.render(simTime, tuning.course);
    trackView?.render(tuning.track);
    const parts = [character.name, `${state.speed.toFixed(0)} m/s`];
    if (course) parts.push(`Pickups ${course.collected}`);
    if (race) {
      parts.push(`Lap ${Math.min(race.lap, tuning.race.laps)}/${tuning.race.laps}`);
      parts.push(formatTime(lapClock(race)));
      if (race.bestLap !== undefined) parts.push(`Best ${formatTime(race.bestLap)}`);
      if (bestEver !== undefined) parts.push(`Record ${formatTime(bestEver)}`);
    }
    parts.push(`1–${characters.length} character`, "R restart");
    hud.textContent = parts.join("  ·  ");

    let message = "";
    if (race?.phase === "countdown") message = "Get ready!";
    else if (race?.phase === "racing" && race.clock < tuning.race.goShowSec) {
      const tier = race.start?.tier;
      message =
        tier === "perfect" ? "GO!\nPerfect start!" : tier === "good" ? "GO!\nGood start" : "GO!";
    } else if (race?.phase === "finished") {
      const laps = race.lapTimes.map((t, i) => `Lap ${i + 1}  ${formatTime(t)}`).join("\n");
      message = `Finished  ${formatTime(race.totalTime ?? 0)}\n${laps}\nR to race again`;
    }
    banner.textContent = message;
    banner.hidden = message === "";
    startMeter.render(race, tuning.race, SHOW_TIMING);

    debug.overlay.set("speed", `${state.speed.toFixed(1)} m/s`);
    debug.overlay.set("slip", `${((slipAngle(state) * 180) / Math.PI).toFixed(1)}°`);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
    debug.overlay.set("air", state.grounded ? "-" : `${state.y.toFixed(1)} m`);
    debug.overlay.set(
      "drift",
      state.driftDir === 0
        ? "-"
        : `${state.driftDir > 0 ? "R" : "L"} ${state.driftTime.toFixed(1)}s`,
    );
    debug.overlay.frame(frameSeconds);
    stage.render();
  },
});

loop.start();
