import * as THREE from "three";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";

// Milestone 0: a bobbing, spinning box proves rendering, the fixed-step loop,
// JSON tuning and the debug tools all work end to end. It gets replaced in M1.

const app = document.getElementById("app")!;
const stage = createStage(app);
const debug = createDebug(document.body);
const input = createInput();

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(30, 48),
  new THREE.MeshStandardMaterial({ color: tuning.world.groundColor }),
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;

const box = new THREE.Mesh(
  new THREE.BoxGeometry(1.6, 0.8, 2.4),
  new THREE.MeshStandardMaterial({ color: tuning.m0Cube.color, flatShading: true }),
);
box.castShadow = true;
stage.scene.add(ground, box);

// Simulation state lives apart from the meshes so rendering can interpolate.
const state = { angle: 0, prevAngle: 0, time: 0 };

const loop = createLoop(tuning.loop.physicsHz, tuning.loop.maxStepsPerFrame, {
  update(dt) {
    input.sample(dt);
    state.prevAngle = state.angle;
    state.angle += tuning.m0Cube.spinSpeed * dt;
    state.time += dt;
  },
  render(alpha, frameSeconds) {
    const { m0Cube, camera, world } = tuning;
    box.rotation.y = state.prevAngle + (state.angle - state.prevAngle) * alpha;
    box.position.y = 0.6 + Math.sin(state.time * m0Cube.bobSpeed) * m0Cube.bobHeight;
    (box.material as THREE.MeshStandardMaterial).color.set(m0Cube.color);
    (ground.material as THREE.MeshStandardMaterial).color.set(world.groundColor);
    stage.scene.background = new THREE.Color(world.skyColor);

    stage.camera.fov = camera.fov;
    stage.camera.updateProjectionMatrix();
    stage.camera.position.set(0, camera.height, camera.distance);
    stage.camera.lookAt(0, 0.6, 0);

    debug.overlay.set("tick", loop.clock.tick);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
    debug.overlay.set("drift", input.state.drift ? "on" : "off");
    debug.overlay.frame(frameSeconds);
    stage.render();
  },
});

loop.start();
