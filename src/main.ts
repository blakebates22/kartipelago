import * as THREE from "three";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";
import courseData from "../assets/data/course.json";
import trackData from "../assets/data/track.json";
import roster from "../assets/data/characters.json";
import { createChaseCamera } from "./render/chaseCamera";
import { createCourseView } from "./render/courseView";
import { createTrackView } from "./render/trackView";
import { createCourse, resetCourse, stepCourse } from "./world/course";
import { buildTrack, type TrackData } from "./world/track";
import { applyCharacter, type Character } from "./vehicles/character";
import { createKartState, slipAngle, stepKart, wrapAngle } from "./vehicles/kart";

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

// Simulation state lives apart from the meshes so rendering can interpolate.
const start = track ? track.start : courseData.start;
const state = createKartState(start.x, start.z, start.heading);
const prev = { x: 0, z: 0, heading: 0, velAngle: 0 };
let simTime = 0;

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
      Object.assign(state, createKartState(start.x, start.z, start.heading));
      if (course) resetCourse(course);
    }
    prev.x = state.x;
    prev.z = state.z;
    prev.heading = state.heading;
    prev.velAngle = state.velAngle;
    if (pickRequested) {
      character = pickRequested;
      pickRequested = undefined;
    }
    // Rebuilt each step so live tuning edits to the base kart apply immediately.
    const kartCfg = applyCharacter(tuning.vehicle, character, tuning.stats);
    stepKart(state, input.sample(dt), kartCfg, dt);
    if (course) stepCourse(course, state, tuning.course, kartCfg, dt);
    simTime += dt;
  },
  render(alpha, frameSeconds) {
    const { camera, world, vehicle } = tuning;
    const x = prev.x + (state.x - prev.x) * alpha;
    const z = prev.z + (state.z - prev.z) * alpha;
    const heading = prev.heading + wrapAngle(state.heading - prev.heading) * alpha;

    kart.position.set(x, 0.4, z);
    kart.rotation.y = heading;
    kartMat.color.set(character.color);
    groundMat.color.set(world.groundColor);
    stage.scene.background = new THREE.Color(world.skyColor);
    stage.followSun(x, z);

    stage.camera.fov = camera.fov;
    stage.camera.updateProjectionMatrix();
    const velAngle = prev.velAngle + wrapAngle(state.velAngle - prev.velAngle) * alpha;
    chase.update(
      { x, z, heading, velAngle, speedFrac: state.speed / vehicle.topSpeed },
      camera,
      frameSeconds,
    );

    courseView?.render(simTime, tuning.course);
    trackView?.render(tuning.track);
    const parts = [character.name, `${state.speed.toFixed(0)} m/s`];
    if (course) parts.push(`Pickups ${course.collected}`);
    parts.push(`1–${characters.length} character`, "R reset");
    hud.textContent = parts.join("  ·  ");

    debug.overlay.set("speed", `${state.speed.toFixed(1)} m/s`);
    debug.overlay.set("slip", `${((slipAngle(state) * 180) / Math.PI).toFixed(1)}°`);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
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
