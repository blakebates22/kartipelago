/**
 * Racer preview ("garage"): inspect the racers away from the race.
 *
 * Open garage.html (or the "Racer preview" link with ?debug). Orbit with the mouse,
 * jump to front / side / rear / gameplay views, and trigger steering, drifting, boosts,
 * hits and jumps to see the animation. Nothing here touches the game's physics: the
 * racer is driven by a fake motion state.
 */
import * as THREE from "three";
import GUI from "lil-gui";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import "./styles.css";
import { DESIGNS, RACER_IDS, type RacerId } from "./render/racers/designs";
import { Racer, type RacerMotion } from "./render/racers/racer";
import { applyRetroLook } from "./render/retro";

const app = document.getElementById("app")!;
const renderer = new THREE.WebGLRenderer({ antialias: true });
app.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color("#8ecae6");
const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 500);
const sun = new THREE.DirectionalLight(0xffffff, 2.2);
sun.position.set(6, 10, 4);
scene.add(sun, new THREE.HemisphereLight(0xdff6ff, 0x557744, 1.1));
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(30, 48).rotateX(-Math.PI / 2),
  new THREE.MeshLambertMaterial({ color: "#6fae4b" }),
);
scene.add(floor);
const road = new THREE.Mesh(
  new THREE.PlaneGeometry(8, 60).rotateX(-Math.PI / 2),
  new THREE.MeshLambertMaterial({ color: "#8a8a8a" }),
);
road.position.y = 0.01;
scene.add(road);

const params = new URLSearchParams(location.search);
const state = {
  racer: (RACER_IDS as string[]).includes(params.get("racer") ?? "")
    ? (params.get("racer") as RacerId)
    : "moss",
  alt: false,
  lineup: params.has("lineup"),
  speed: Number(params.get("speed") ?? 0),
  steer: Number(params.get("steer") ?? 0),
  drift: Number(params.get("drift") ?? 0),
  view: params.get("view") ?? "threeQuarter",
  resolution: 0.75,
};

let racers: Racer[] = [];
function rebuild() {
  for (const r of racers) r.dispose(scene);
  const ids = state.lineup ? RACER_IDS : [state.racer];
  racers = ids.map((id, i) => {
    const r = new Racer(id, { alt: state.alt, seed: i + 3 });
    r.root.position.x = state.lineup ? (i - (ids.length - 1) / 2) * 2.6 : 0;
    scene.add(r.root, r.shadow);
    r.placeShadow(r.root.position.x, 0, 0, 0, 0);
    return r;
  });
}

// Fake motion, driven by the controls.
const motion: RacerMotion = {
  speed: 0,
  steer: 0,
  driftDir: 0,
  slip: 0,
  grounded: true,
  boostPhase: 0,
  boostEnhanced: false,
  boostLeft: 0,
  impactTier: 0,
  impactSpeed: 0,
  spinTime: 0,
};
let boostFor = 0;
let airFor = 0;
const actions = {
  boost: () => start(false),
  enhanced: () => start(true),
  scrape: () => hit(1),
  bump: () => hit(2),
  crash: () => hit(3),
  spin: () => (motion.spinTime = 1.2),
  jump: () => (airFor = 0.7),
};
function start(enhanced: boolean) {
  boostFor = 1.25;
  motion.boostEnhanced = enhanced;
}
function hit(tier: number) {
  motion.impactTier = tier;
  motion.impactSpeed = Math.random() * 20;
}

const VIEWS: Record<string, [number, number, number, number]> = {
  front: [0, 1.2, 5, 0.9],
  side: [5.5, 1.2, 0, 0.9],
  rear: [0, 1.4, -5, 0.9],
  threeQuarter: [3.6, 2, 3.8, 0.8],
  // The race camera: 7 m behind, 3 m up, looking just ahead.
  gameplay: [0, 3, -7, 1],
  far: [0, 6, -60, 1],
  top: [0, 5, 1.5, 0],
  hero: [-1.7, 0.85, 3.3, 0.95],
  face: [0, 1.75, 2.4, 1.7],
};
function setView(name: string) {
  const v = VIEWS[name] ?? VIEWS.threeQuarter!;
  const scale = state.lineup && name !== "gameplay" ? 1.9 : 1;
  camera.position.set(v[0] * scale, v[1] * (state.lineup ? 1.3 : 1), v[2] * scale);
  controls.target.set(0, v[3], name === "gameplay" ? 4 : 0);
  camera.fov = name === "gameplay" ? 65 : 45;
  camera.updateProjectionMatrix();
  controls.update();
}

const controls = new OrbitControls(camera, renderer.domElement);
const gui = new GUI({ title: "Racer preview" });
gui
  .add(state, "racer", Object.fromEntries(RACER_IDS.map((id) => [DESIGNS[id].name, id])))
  .onChange(rebuild);
gui.add(state, "alt").name("alternate paint").onChange(rebuild);
gui
  .add(state, "lineup")
  .name("all four")
  .onChange(() => (rebuild(), setView(state.view)));
gui.add(state, "view", Object.keys(VIEWS)).onChange(setView);
gui.add(state, "speed", 0, 50, 0.5).name("speed (m/s)");
gui.add(state, "steer", -1, 1, 0.01);
gui.add(state, "drift", { none: 0, left: -1, right: 1 });
gui.add(state, "resolution", 0.4, 1, 0.05).name("render scale").onChange(resize);
const fx = gui.addFolder("Reactions");
fx.add(actions, "boost");
fx.add(actions, "enhanced").name("enhanced boost");
fx.add(actions, "scrape").name("wall scrape");
fx.add(actions, "bump").name("wall bump");
fx.add(actions, "crash").name("wall crash");
fx.add(actions, "spin").name("weapon hit (spin)");
fx.add(actions, "jump");

function resize() {
  const w = app.clientWidth;
  const h = app.clientHeight;
  applyRetroLook(renderer, scene, { resolutionScale: state.resolution, fogNear: 60, fogFar: 260 });
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(1, h);
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);
resize();
rebuild();
setView(state.view);

let last = performance.now();
function frame(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  motion.speed = state.speed;
  motion.steer += (state.steer - motion.steer) * (1 - Math.exp(-12 * dt));
  motion.driftDir = state.drift;
  // In a drift the nose points into the turn: travel is offset from it.
  motion.slip = motion.driftDir * 0.6 * (state.speed > 2 ? 1 : 0);
  if (boostFor > 0) {
    boostFor -= dt;
    motion.boostLeft = boostFor;
    motion.boostPhase = motion.boostEnhanced && boostFor < 0.35 ? 2 : 1;
    if (boostFor <= 0) motion.boostPhase = 0;
  }
  motion.spinTime = Math.max(0, motion.spinTime - dt);
  if (airFor > 0) {
    airFor -= dt;
    motion.grounded = airFor <= 0;
  }
  for (const r of racers) {
    r.animate(dt, motion, { x: 3, z: 1 });
    // Flame, as in the game: shown while boosting, green core when enhanced.
    r.flame.visible = motion.boostPhase !== 0;
    r.core.visible = motion.boostPhase === 1 && motion.boostEnhanced;
    if (motion.boostPhase === 2) r.flameMat.color.setHSL((now / 250) % 1, 1, 0.6);
    else r.flameMat.color.set("#9b5de5");
  }
  controls.update();
  renderer.render(scene, camera);
  Object.assign(window as object, {
    ready: true,
    calls: renderer.info.render.calls,
    tris: renderer.info.render.triangles,
  });
  requestAnimationFrame(frame);
  // ?react=boost|enhanced|crash|spin|jump triggers a reaction shortly after loading.
  const react = params.get("react") as keyof typeof actions | null;
  if (react && actions[react]) setTimeout(actions[react], Number(params.get("after") ?? 500));
}
requestAnimationFrame(frame);
// ?react=boost|enhanced|crash|spin|jump triggers a reaction shortly after loading.
const react = params.get("react") as keyof typeof actions | null;
if (react && actions[react]) setTimeout(actions[react], Number(params.get("after") ?? 500));
