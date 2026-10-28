/**
 * The story dragons' viewer (dragons.html): each of Adventure's dragons on a turntable,
 * in any pose, away from the cutscenes. Orbit with the mouse; the panel picks the
 * dragon, the pose and the view, cycles the poses, or lines them all up.
 *
 * URL options (for scripted screenshots): ?d=rimefang&pose=rear&view=front&time=2.5
 * &lineup (all of them side by side) &spin (turntable) &cycle (step through the poses).
 * `window.preview.show({ d, pose, view, time })` poses it and renders one frame.
 */
import * as THREE from "three";
import GUI from "lil-gui";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import "./styles.css";
import { createStoryDragon, type StoryDragonView } from "./render/storyDragon";
import type { DesignId } from "./render/storyDragons/types";
import type { StoryPose } from "./adventure/staged";
import { applyRetroLook } from "./render/retro";
import { createDinoView, type DinoView } from "./render/dinosaur";
import { Racer } from "./render/racers/racer";

const IDS: DesignId[] = [
  "cinderjaw",
  "rimefang",
  "scorchwind",
  "tidewyrm",
  "king",
  "lumen",
  "lumen_grown",
];
const POSES: StoryPose[] = [
  "idle",
  "rear",
  "breathe",
  "fly",
  "land",
  "roar",
  "bow",
  "stunned",
  "claw",
  "walk",
  "turn",
];

const app = document.getElementById("app")!;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
app.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color("#8ecae6");
const camera = new THREE.PerspectiveCamera(40, 1, 0.5, 3000);
// The game's lights (render/stage.ts).
const sun = new THREE.DirectionalLight(0xffffff, 2.2);
sun.position.set(8, 14, 6).multiplyScalar(10);
scene.add(sun, new THREE.HemisphereLight(0xdff6ff, 0x335533, 1.1));
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(400, 64).rotateX(-Math.PI / 2),
  new THREE.MeshLambertMaterial({ color: "#7aa85a" }),
);
scene.add(floor);
// A kart-sized block for scale.
const kart = new THREE.Mesh(
  new THREE.BoxGeometry(1.4, 1.1, 2.2).translate(0, 0.55, 0),
  new THREE.MeshLambertMaterial({ color: "#d84a3a" }),
);
scene.add(kart);

const params = new URLSearchParams(location.search);
const state = {
  d: (IDS as string[]).includes(params.get("d") ?? "")
    ? (params.get("d") as DesignId)
    : "cinderjaw",
  pose: (POSES as string[]).includes(params.get("pose") ?? "")
    ? (params.get("pose") as StoryPose)
    : "idle",
  view: params.get("view") ?? "threeQuarter",
  lineup: params.has("lineup"),
  spin: params.has("spin"),
  cycle: params.has("cycle"),
  talk: params.has("talk"),
  scale: Number(params.get("scale") ?? 1),
  lookAtCamera: !params.has("ahead"),
};

let dragons: StoryDragonView[] = [];
// The benchmark (&bench): Riverbend's long-neck and a racer (scaled up 8x) beside it.
let dino: DinoView | undefined;
let racer: Racer | undefined;
function rebuild() {
  for (const d of dragons) d.dispose();
  dino?.dispose();
  dino = undefined;
  if (racer) racer.dispose(scene);
  racer = undefined;
  if (params.has("bench")) {
    dino = createDinoView(scene, 1);
    dino.update(-34, 0, -4, 0.5, 0, 0, 0.3, 1);
    racer = new Racer("tiko", { seed: 3 });
    racer.root.scale.setScalar(8);
    racer.root.position.set(30, 0, 6);
    racer.root.rotation.y = -0.4;
    scene.add(racer.root);
  }
  const list = state.lineup ? IDS : [state.d];
  dragons = list.map((id, i) => {
    const v = createStoryDragon(scene, id, id === "lumen" && state.lineup ? 0.45 : state.scale);
    v.root.position.x = state.lineup ? (i - (list.length - 1) / 2) * 46 : 0;
    v.ground = 0;
    return v;
  });
  kart.position.set(state.lineup ? 0 : 16, 0, 26);
  clock = 0;
}

/** Views: direction from the dragon (x, y, z) and how far, in its size. */
const VIEWS: Record<string, [number, number, number]> = {
  front: [0, 0.25, 1],
  threeQuarter: [0.75, 0.3, 0.75],
  side: [1, 0.15, 0.05],
  rear: [-0.3, 0.35, -1],
  top: [0.2, 1, 0.3],
};
const box = new THREE.Box3();
const tmp = new THREE.Vector3();
function frameView() {
  const v = VIEWS[state.view];
  if (state.view === "head" || state.view === "face" || state.view === "profile") {
    // A close-up of the head: three-quarter, straight on, or in profile.
    const d = dragons[0]!;
    const h = new THREE.Vector3();
    const fwd = new THREE.Vector3();
    d.headFrame(h, fwd);
    const s = d.root.scale.x * (d.design === "lumen" ? 1.4 : 1.1);
    const side = new THREE.Vector3(0, 1, 0).cross(fwd).normalize();
    const [f, r] =
      state.view === "face" ? [1, 0] : state.view === "profile" ? [0.05, 1] : [0.75, 0.62];
    camera.position
      .copy(h)
      .addScaledVector(fwd, 17 * s * f)
      .addScaledVector(side, 17 * s * r)
      .add(new THREE.Vector3(0, 2 * s, 0));
    controls.target.copy(h);
    camera.fov = 40;
  } else {
    box.makeEmpty();
    for (const d of dragons) box.expandByObject(d.root);
    if (dino) box.expandByObject(dino.root);
    if (racer) box.expandByObject(racer.root);
    const c = box.getCenter(new THREE.Vector3());
    const size = box.getSize(tmp).length();
    const dir = new THREE.Vector3(...(v ?? VIEWS.threeQuarter!)).normalize();
    camera.position.copy(c).addScaledVector(dir, size * (state.lineup ? 0.5 : 1.05));
    controls.target.copy(c);
    camera.fov = 40;
  }
  camera.updateProjectionMatrix();
  controls.update();
}

const controls = new OrbitControls(camera, renderer.domElement);
const gui = new GUI({ title: "Story dragons" });
gui
  .add(state, "d", IDS)
  .name("dragon")
  .onChange(() => (rebuild(), frameView()));
gui.add(state, "pose", POSES).onChange(() => (since = 0));
gui
  .add(state, "view", [...Object.keys(VIEWS), "head", "face", "profile"])
  .onChange(() => frameView());
gui.add(state, "lineup").onChange(() => (rebuild(), frameView()));
gui.add(state, "talk");
gui.add(state, "spin").name("turntable");
gui.add(state, "cycle").name("cycle poses");
gui.add(state, "lookAtCamera").name("look at camera");

function resize() {
  const w = app.clientWidth;
  const h = app.clientHeight;
  applyRetroLook(renderer, scene, { resolutionScale: 1, fogNear: 400, fogFar: 2400 });
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(1, h);
  camera.updateProjectionMatrix();
}

let clock = 0;
let since = 0;
const MOTION = {
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
const lookAt = new THREE.Vector3();
function step(dt: number) {
  clock += dt;
  since += dt;
  if (state.cycle && since > 4) {
    since = 0;
    state.pose = POSES[(POSES.indexOf(state.pose) + 1) % POSES.length]!;
  }
  racer?.animate(dt, MOTION, null);
  for (const d of dragons) {
    if (state.spin) d.root.rotation.y += dt * 0.4;
    // Flyers hang in the air.
    const fly = state.pose === "fly" || state.pose === "land";
    d.root.position.y = fly ? 14 * d.root.scale.x : 0;
    if (state.lookAtCamera) lookAt.copy(camera.position);
    else lookAt.set(0, 0, 40).applyQuaternion(d.root.quaternion).add(d.root.position);
    d.update(state.pose, since, clock, lookAt, state.talk);
  }
}

/** Pose it at `time` seconds into the pose (run from rest), and render. */
function show(o: {
  d?: DesignId;
  pose?: StoryPose;
  view?: string;
  time?: number;
  talk?: boolean;
  turn?: number;
}) {
  const lineup = o.d === undefined || (o.d as string) === "all";
  if (lineup !== state.lineup || (!lineup && o.d !== state.d)) {
    state.lineup = lineup;
    if (!lineup) state.d = o.d!;
    rebuild();
  }
  if (o.pose) state.pose = o.pose;
  if (o.view) state.view = o.view;
  if (o.talk !== undefined) state.talk = o.talk;
  for (const d of dragons) d.root.rotation.y = o.turn ?? 0;
  since = 0;
  clock = 0;
  const T = o.time ?? 2;
  // From rest: idle a moment, then the pose.
  const pose = state.pose;
  state.pose = "idle";
  for (let i = 0; i < 10; i++) step(1 / 30);
  state.pose = pose;
  since = 0;
  frameView();
  for (let t = 0; t < T; t += 1 / 30) step(1 / 30);
  frameView();
  renderer.render(scene, camera);
  return true;
}

window.addEventListener("resize", resize);
resize();
rebuild();
frameView();
let paused = params.has("paused");
let last = performance.now();
function frame(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  if (!paused) {
    step(dt);
    controls.update();
    renderer.render(scene, camera);
  }
  Object.assign(window as object, {
    ready: true,
    tris: renderer.info.render.triangles,
    calls: renderer.info.render.calls,
  });
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
Object.assign(window as object, {
  preview: {
    show,
    state,
    pause: (p = true) => (paused = p),
    tris: () => {
      renderer.render(scene, camera);
      return renderer.info.render.triangles;
    },
    /** Where each design's head is (centre, at scale 1, idle, looking ahead). */
    measure: () =>
      Object.fromEntries(
        IDS.map((id) => {
          const v = createStoryDragon(scene, id, 1);
          v.ground = 0;
          for (let k = 0; k < 60; k++)
            v.update("idle", k / 30, k / 30, new THREE.Vector3(0, 10, 200), false);
          const c = new THREE.Vector3();
          v.headFrame(c, new THREE.Vector3());
          v.dispose();
          return [id, [+c.y.toFixed(1), +c.z.toFixed(1)]];
        }),
      ),
    /** Triangles per mesh of the first dragon (biggest first). */
    breakdown: () => {
      const out: [string, number][] = [];
      dragons[0]!.root.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        const g = m.geometry;
        const n = (g.index ? g.index.count : g.getAttribute("position").count) / 3;
        const k = (m as THREE.InstancedMesh).isInstancedMesh ? (m as THREE.InstancedMesh).count : 1;
        out.push([`${m.parent?.name ?? ""}/${m.name}/${g.type}`, Math.round(n * k)]);
      });
      return out.sort((a, b) => b[1] - a[1]);
    },
  },
});
