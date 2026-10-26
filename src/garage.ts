/**
 * The character viewer ("garage"): inspect the racers away from the race.
 *
 * Open garage.html (or the "Racer preview" link with ?debug). Orbit with the mouse,
 * jump to front / side / rear / three-quarter / race-camera views, show the turnaround
 * (four views side by side) or all the racers together, and put a racer into any
 * animation state (drifting, boosting, airborne, victory...) to see it move. "Save
 * sheet" downloads a PNG turnaround of the current racer.
 *
 * Nothing here touches the game's physics: the racer is driven by a fake motion state.
 *
 * URL options (for scripted screenshots): ?racer=tiko&view=rear&state=DRIFTING_LEFT
 * &turnaround&lineup&alt&scale=1
 */
import * as THREE from "three";
import GUI from "lil-gui";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import "./styles.css";
import { DESIGNS, RACER_IDS, type RacerId } from "./render/racers/designs";
import { Racer, type AnimState, type RacerMotion } from "./render/racers/racer";
import { STATES } from "./render/racers/animator";
import { DRAGON_PALETTES } from "./render/racers/roster/dragon";
import { applyRetroLook } from "./render/retro";

const app = document.getElementById("app")!;
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
app.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color("#8ecae6");
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
const sun = new THREE.DirectionalLight(0xfff2dc, 2.3);
sun.position.set(5, 10, 6);
scene.add(sun, new THREE.HemisphereLight(0xdff6ff, 0x557744, 1.15));
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(40, 48).rotateX(-Math.PI / 2),
  new THREE.MeshLambertMaterial({ color: "#6fae4b" }),
);
scene.add(floor);
const road = new THREE.Mesh(
  new THREE.PlaneGeometry(9, 80).rotateX(-Math.PI / 2),
  new THREE.MeshLambertMaterial({ color: "#c9925a" }),
);
road.position.y = 0.01;
scene.add(road);

const params = new URLSearchParams(location.search);
const state = {
  // (?racer=dragon&dragon=cinderjaw|rimefang|scorchwind|tidewyrm|king: Adventure's dragons.)
  racer: (([...RACER_IDS, "dragon"] as string[]).includes(params.get("racer") ?? "")
    ? params.get("racer")
    : "tiko") as RacerId,
  alt: params.has("alt"),
  lineup: params.has("lineup"),
  turnaround: params.has("turnaround"),
  state: (STATES as readonly string[]).includes(params.get("state") ?? "")
    ? (params.get("state") as AnimState)
    : "IDLE",
  view: params.get("view") ?? "threeQuarter",
  scale: Number(params.get("scale") ?? 0.75),
  spin: false,
};

let racers: Racer[] = [];
function rebuild() {
  for (const r of racers) r.dispose(scene);
  let list: { id: RacerId; x: number; turn: number }[];
  if (state.lineup)
    list = RACER_IDS.map((id, i) => ({ id, x: (i - (RACER_IDS.length - 1) / 2) * 2.8, turn: 0 }));
  else if (state.turnaround)
    // Front, three-quarter, side and rear, side by side (seen from the front view).
    list = [0, 0.75, Math.PI / 2, Math.PI].map((turn, i) => ({
      id: state.racer,
      x: (i - 1.5) * 3.2,
      turn,
    }));
  // (&boss: the dragon as a boss races, on foot, with a kart beside it for size.)
  else if (params.has("boss"))
    list = [
      { id: state.racer, x: 2.5, turn: 0 },
      { id: "tiko", x: -5.5, turn: 0 },
    ];
  else list = [{ id: state.racer, x: 0, turn: 0 }];
  racers = list.map(({ id, x, turn }, i) => {
    const r = new Racer(id, {
      alt: state.alt,
      seed: i + 3,
      palette: id === "dragon" ? DRAGON_PALETTES[params.get("dragon") ?? "cinderjaw"] : undefined,
      boss: id === "dragon" && params.has("boss"),
    });
    r.root.position.x = x;
    r.root.rotation.y = turn;
    scene.add(r.root, r.shadow);
    r.placeShadow(x, 0, 0, turn, 0);
    return r;
  });
  enter(state.state);
}

// Fake motion for each state.
const motion: RacerMotion = {
  speed: 0,
  steer: 0,
  driftDir: 0,
  slip: 0,
  grounded: true,
  throttle: false,
  boostPhase: 0,
  boostEnhanced: false,
  boostLeft: 0,
  impactTier: 0,
  impactSpeed: 0,
  spinTime: 0,
};
let since = 0;
function enter(s: AnimState) {
  state.state = s;
  since = 0;
  Object.assign(motion, {
    speed: 0,
    steer: 0,
    driftDir: 0,
    slip: 0,
    grounded: true,
    throttle: false,
    boostPhase: 0,
    boostEnhanced: false,
    boostLeft: 0,
    spinTime: 0,
  });
  for (const r of racers) r.setResult(s === "VICTORY" ? 1 : s === "DEFEAT" ? 7 : null, 8);
  if (s === "COLLISION") {
    motion.impactTier = 3;
    motion.impactSpeed = Math.random() * 20 + 10;
  }
}
/** Keep the fake motion in its state (some states are events and need re-triggering). */
function drive(dt: number) {
  since += dt;
  const s = state.state;
  const moving = s !== "IDLE" && s !== "VICTORY" && s !== "DEFEAT";
  if (moving) motion.speed = 18;
  if (s === "VICTORY" || s === "DEFEAT") motion.speed = 8;
  motion.throttle = moving && s !== "BRAKING";
  if (s === "BRAKING") motion.speed = Math.max(4, 20 - (since % 2) * 12);
  if (s === "STEERING_LEFT" || s === "DRIFTING_LEFT") motion.steer = -0.8;
  if (s === "STEERING_RIGHT" || s === "DRIFTING_RIGHT") motion.steer = 0.8;
  if (s === "DRIFTING_LEFT") ((motion.driftDir = -1), (motion.slip = -0.6), (motion.steer = -0.5));
  if (s === "DRIFTING_RIGHT") ((motion.driftDir = 1), (motion.slip = 0.6), (motion.steer = 0.5));
  if (s === "BOOSTING") {
    motion.boostPhase = 1;
    motion.boostLeft = 1.2 - (since % 1.2);
    motion.boostEnhanced = true;
  }
  if (s === "AIRBORNE") motion.grounded = false;
  if (s === "LANDING") motion.grounded = since % 1.4 > 0.8;
  if (s === "COLLISION" && since > 1.6) {
    since = 0;
    motion.impactSpeed = Math.random() * 20 + 10;
  }
}

const VIEWS: Record<string, [number, number, number, number]> = {
  front: [0, 1.3, 5, 1.0],
  side: [5.5, 1.3, 0, 1.0],
  rear: [0, 1.5, -5, 1.0],
  threeQuarter: [3.6, 2, 3.8, 0.95],
  // The race camera: 7 m behind, 3 m up, looking just ahead.
  gameplay: [0, 3, -7, 1],
  far: [0, 6, -40, 1],
  top: [0, 6, 0.5, 0],
  face: [0.9, 1.9, 2.2, 1.85],
};
function setView(name: string) {
  if (state.turnaround && name !== "gameplay") name = "front";
  state.view = name;
  const v = VIEWS[name] ?? VIEWS.threeQuarter!;
  const wide = state.lineup || state.turnaround;
  // (A boss is huge: stand well back.)
  const boss = params.has("boss") ? 4 : 1;
  const k = (wide && name !== "gameplay" ? 2.1 : 1) * boss;
  camera.position.set(v[0] * k, v[1] * (wide ? 1.15 : 1) * boss, v[2] * k);
  controls.target.set(0, v[3] * boss * 0.8, name === "gameplay" ? 4 : 0);
  camera.fov = name === "gameplay" ? 65 : 40;
  camera.updateProjectionMatrix();
  controls.update();
}

const controls = new OrbitControls(camera, renderer.domElement);
const gui = new GUI({ title: "Character viewer" });
gui
  .add(state, "racer", Object.fromEntries(RACER_IDS.map((id) => [DESIGNS[id].name, id])))
  .onChange(rebuild);
gui.add(state, "alt").name("alternate colours").onChange(rebuild);
gui
  .add(state, "turnaround")
  .name("turnaround (4 views)")
  .onChange(() => ((state.lineup = false), rebuild(), setView(state.view)));
gui
  .add(state, "lineup")
  .name("all racers")
  .onChange(() => ((state.turnaround = false), rebuild(), setView(state.view)));
gui.add(state, "view", Object.keys(VIEWS)).onChange(setView);
gui
  .add(state, "state", [...STATES])
  .name("animation")
  .onChange((s: AnimState) => enter(s));
gui.add(state, "spin").name("turntable");
gui.add(state, "scale", 0.3, 1, 0.05).name("render scale").onChange(resize);
gui.add({ save: () => saveSheet() }, "save").name("save sheet (PNG)");

function resize() {
  const w = app.clientWidth;
  const h = app.clientHeight;
  applyRetroLook(renderer, scene, { resolutionScale: state.scale, fogNear: 60, fogFar: 260 });
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(1, h);
  camera.updateProjectionMatrix();
}

/** Render front, side, rear, three-quarter and race-camera views into one PNG. */
function saveSheet() {
  const views = ["front", "side", "rear", "threeQuarter", "gameplay"];
  const was = { turnaround: state.turnaround, lineup: state.lineup, view: state.view };
  state.turnaround = false;
  state.lineup = false;
  rebuild();
  const size = 320;
  const sheet = document.createElement("canvas");
  sheet.width = size * views.length;
  sheet.height = size + 28;
  const g = sheet.getContext("2d")!;
  g.fillStyle = "#1d2433";
  g.fillRect(0, 0, sheet.width, sheet.height);
  const old = {
    w: renderer.domElement.width,
    h: renderer.domElement.height,
    aspect: camera.aspect,
  };
  renderer.setSize(size, size, false);
  camera.aspect = 1;
  views.forEach((v, i) => {
    setView(v);
    for (let k = 0; k < 4; k++) for (const r of racers) r.animate(1 / 30, motion, null);
    renderer.render(scene, camera);
    g.drawImage(renderer.domElement, i * size, 0, size, size);
    g.fillStyle = "#fff6dc";
    g.font = "16px monospace";
    g.fillText(v, i * size + 8, size + 20);
  });
  renderer.setSize(old.w, old.h, false);
  camera.aspect = old.aspect;
  Object.assign(state, was);
  rebuild();
  setView(was.view);
  resize();
  const a = document.createElement("a");
  a.download = `${state.racer}${state.alt ? "-alt" : ""}-sheet.png`;
  a.href = sheet.toDataURL("image/png");
  a.click();
}

window.addEventListener("resize", resize);
resize();
rebuild();
setView(state.view);

let last = performance.now();
function frame(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  drive(dt);
  for (const r of racers) {
    if (state.spin && !state.turnaround) r.root.rotation.y += dt * 0.6;
    r.animate(dt, motion, { x: 3, z: 1 });
    r.flame.visible = motion.boostPhase !== 0;
    r.core.visible = motion.boostPhase === 1 && motion.boostEnhanced;
  }
  controls.update();
  renderer.render(scene, camera);
  Object.assign(window as object, {
    ready: true,
    calls: renderer.info.render.calls,
    tris: renderer.info.render.triangles,
  });
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
// For scripted screenshots.
Object.assign(window as object, {
  garage: { enter, setView, rebuild, state },
});
