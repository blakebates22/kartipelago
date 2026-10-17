import * as THREE from "three";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";
import { createKartState, slipAngle, stepKart, wrapAngle } from "./vehicles/kart";

// M1: drive a box around a big flat plane. The camera is a plain rigid follow for now;
// smoothing and look-ahead come in the chase-camera PR.

const GROUND_SIZE = 600;
const GROUND_TILE = 5; // metres per grid square

const app = document.getElementById("app")!;
const stage = createStage(app);
const debug = createDebug(document.body);
const input = createInput();

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

const kartMat = new THREE.MeshStandardMaterial({ color: tuning.vehicle.color, flatShading: true });
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

// Simulation state lives apart from the meshes so rendering can interpolate.
const state = createKartState();
const prev = { x: 0, z: 0, heading: 0 };

const loop = createLoop(tuning.loop.physicsHz, tuning.loop.maxStepsPerFrame, {
  update(dt) {
    prev.x = state.x;
    prev.z = state.z;
    prev.heading = state.heading;
    stepKart(state, input.sample(dt), tuning.vehicle, dt);
  },
  render(alpha, frameSeconds) {
    const { camera, world, vehicle } = tuning;
    const x = prev.x + (state.x - prev.x) * alpha;
    const z = prev.z + (state.z - prev.z) * alpha;
    const heading = prev.heading + wrapAngle(state.heading - prev.heading) * alpha;

    kart.position.set(x, 0.4, z);
    kart.rotation.y = heading;
    kartMat.color.set(vehicle.color);
    groundMat.color.set(world.groundColor);
    stage.scene.background = new THREE.Color(world.skyColor);
    stage.followSun(x, z);

    stage.camera.fov = camera.fov;
    stage.camera.updateProjectionMatrix();
    stage.camera.position.set(
      x - Math.sin(heading) * camera.distance,
      camera.height,
      z - Math.cos(heading) * camera.distance,
    );
    stage.camera.lookAt(x, camera.lookHeight, z);

    debug.overlay.set("speed", `${state.speed.toFixed(1)} m/s`);
    debug.overlay.set("slip", `${((slipAngle(state) * 180) / Math.PI).toFixed(1)}°`);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
    debug.overlay.set("drift", input.state.drift ? "on" : "off");
    debug.overlay.frame(frameSeconds);
    stage.render();
  },
});

loop.start();
