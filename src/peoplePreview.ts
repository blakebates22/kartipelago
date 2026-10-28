/**
 * The people preview (people.html): the story's characters on a turntable, for checking
 * them over away from the game, like garage.html for the racers.
 *
 * URL options (for scripted screenshots):
 *   who=elder | lumen | guard:<folk>:<seed> | villager:<folk>:<seed>[:<species>] | racer:<id>
 *       (a comma list: one each, side by side in "strip" mode)
 *   mode=sheet   one character from front, three-quarter, side, rear, and a face close-up,
 *                with a racer beside them for comparison (&racer=rex)
 *   mode=strip   each `who` (or each of &gestures=a,b,c on the first who) in its own cell
 *   mode=seq     one gesture (&gesture=) at the times in &times=0.3,0.8,1.4
 *   gesture=wave&talk&walk   what they're doing; time=2 (seconds simulated, then frozen)
 *   view=threeQuarter|front|side|rear|face|back   for strip/seq cells; cols=4; live
 */
import * as THREE from "three";
import "./styles.css";
import { Racer } from "./render/racers/racer";
import type { RacerId } from "./render/racers/designs";
import { GESTURES, type Gesture, type PersonView } from "./render/people";
import { createPerson } from "./render/people/cast";
import { actRacer, type RacerActing } from "./render/people/racerActing";
import { facePoint } from "./render/people/view";
import { createDinoView } from "./render/dinosaur";

const params = new URLSearchParams(location.search);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Number(params.get("scale") ?? 1));
document.body.appendChild(renderer.domElement);
const labels = document.createElement("div");
labels.style.cssText =
  "position:fixed;inset:0;pointer-events:none;font:12px monospace;color:#fff6dc";
document.body.appendChild(labels);

const scene = new THREE.Scene();
scene.background = new THREE.Color("#8ecae6");
scene.fog = new THREE.Fog("#8ecae6", 60, 200);
const sun = new THREE.DirectionalLight(0xfff2dc, 2.3);
sun.position.set(5, 10, 6);
scene.add(sun, new THREE.HemisphereLight(0xdff6ff, 0x557744, 1.15));
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(400, 48).rotateX(-Math.PI / 2),
  new THREE.MeshLambertMaterial({ color: "#6fae4b" }),
);
scene.add(floor);

type Thing =
  | {
      kind: "person";
      view: PersonView;
      at: THREE.Vector3;
      heading: number;
      gesture: Gesture | null;
    }
  | { kind: "racer"; racer: Racer; acting: RacerActing; at: THREE.Vector3; heading: number };

function make(who: string, x: number, gesture: Gesture | null): Thing {
  const at = new THREE.Vector3(x, 0, 0);
  if (who.startsWith("racer:")) {
    const racer = new Racer(who.slice(6) as RacerId, { seed: 3 });
    racer.root.position.copy(at);
    scene.add(racer.root, racer.shadow);
    racer.placeShadow(at.x, 0, at.z, 0, 0);
    return { kind: "racer", racer, acting: actRacer(racer), at, heading: 0 };
  }
  return { kind: "person", view: createPerson(scene, who), at, heading: 0, gesture };
}

const mode = params.get("mode") ?? "sheet";
const whoList = (params.get("who") ?? "elder").split(",");
const gestureParam = params.get("gesture") as Gesture | null;
const gestures = (params.get("gestures") ?? "").split(",").filter((g) => g) as Gesture[];
const times = (params.get("times") ?? "0.4,0.9,1.4,2.2").split(",").map(Number);
const talk = params.has("talk");
const walk = params.has("walk");
const simTime = Number(params.get("time") ?? 1.5);

interface Cell {
  thing: Thing;
  view: string;
  label: string;
  time: number;
}
const things: Thing[] = [];
const cells: Cell[] = [];
const SPACING = 30;
if (mode === "sheet") {
  const t = make(whoList[0]!, 0, gestureParam);
  things.push(t);
  const racerId = params.get("racer") ?? "rex";
  const r = make(`racer:${racerId}`, 2.4, null);
  r.at.z = 0.6;
  (r as { racer: Racer }).racer.root.position.z = 0.6;
  r.heading = -0.5;
  (r as { racer: Racer }).racer.root.rotation.y = -0.5;
  things.push(r);
  // The long-neck (dinosaur.ts), small, for comparing the smoothness of the skin.
  const dino = createDinoView(scene, 0.16);
  dino.update(4.2, 0, -3.2, -0.7, 0, 0, 0, 1);
  for (const v of ["front", "threeQuarter", "side", "rear", "face", "faceSide"])
    cells.push({ thing: t, view: v, label: v, time: simTime });
  cells.push({ thing: t, view: "withRacer", label: `beside ${racerId}`, time: simTime });
  cells.push({ thing: r, view: "face", label: `${racerId} face`, time: simTime });
  cells.push({ thing: t, view: "withDino", label: "beside the long-neck", time: simTime });
} else if (mode === "strip") {
  const list = gestures.length
    ? gestures.map((g) => [whoList[0]!, g] as const)
    : whoList.map((w) => [w, gestureParam] as const);
  list.forEach(([w, g], i) => {
    const t = make(w, i * SPACING, g);
    things.push(t);
    cells.push({
      thing: t,
      view: params.get("view") ?? "threeQuarter",
      label: g ?? w,
      time: simTime,
    });
  });
} else {
  times.forEach((tm, i) => {
    const t = make(whoList[0]!, i * SPACING, gestureParam);
    things.push(t);
    cells.push({
      thing: t,
      view: params.get("view") ?? "threeQuarter",
      label: `${gestureParam ?? ""} ${tm}s`,
      time: tm,
    });
  });
}

/** Each thing's own clock (a seq's are frozen at different moments). */
const clocks = new Map<Thing, number>();
for (const c of cells) clocks.set(c.thing, Math.max(clocks.get(c.thing) ?? 0, c.time));

const look = new THREE.Vector3();
function step(th: Thing, t: number, dt: number) {
  if (th.kind === "racer") {
    th.acting.update(dt, { talk, look: null });
    return;
  }
  let x = th.at.x;
  let z = th.at.z;
  let h = th.heading;
  if (walk) {
    // Round a circle, a metre a second.
    const a = t / 2.2;
    x = th.at.x + Math.sin(a) * 2.2;
    z = th.at.z + Math.cos(a) * 2.2 - 2.2;
    h = a + Math.PI / 2;
  }
  th.view.root.userData.pose = { x, z, h };
  // Looking at whoever's in front of them (about where the camera is).
  look.set(x + Math.sin(h) * 4, 1.4, z + Math.cos(h) * 4);
  th.view.update(
    x,
    0,
    z,
    h,
    { talk, gesture: th.gesture, look: params.has("nolook") ? null : look },
    t,
  );
}

// Simulate each thing to its time.
const DT = 1 / 30;
for (const th of things) {
  const end = clocks.get(th) ?? simTime;
  for (let t = 0; t <= end; t += DT) step(th, t, DT);
}

/** A camera for a cell. */
function aim(cam: THREE.PerspectiveCamera, c: Cell) {
  const th = c.thing;
  const p =
    th.kind === "person"
      ? (th.view.root.userData.pose as { x: number; z: number; h: number })
      : { x: th.at.x, z: th.at.z, h: th.heading };
  const head = new THREE.Vector3();
  if (th.kind === "person") th.view.headPosition(head);
  else facePoint(th.racer.rig, head);
  const fwd = new THREE.Vector3(Math.sin(p.h), 0, Math.cos(p.h));
  const right = new THREE.Vector3(fwd.z, 0, -fwd.x);
  const at = (f: number, r: number, y: number) =>
    new THREE.Vector3(p.x, y, p.z).addScaledVector(fwd, f).addScaledVector(right, r);
  const mid = head.y * 0.52;
  cam.fov = 30;
  switch (c.view) {
    case "front":
      cam.position.copy(at(4.6, 0, mid + 0.25));
      cam.lookAt(p.x, mid, p.z);
      break;
    case "side":
      cam.position.copy(at(0.2, -4.6, mid + 0.25));
      cam.lookAt(p.x, mid, p.z);
      break;
    case "rear":
      cam.position.copy(at(-4.6, 0.4, mid + 0.4));
      cam.lookAt(p.x, mid, p.z);
      break;
    case "back":
      cam.position.copy(at(-3.2, -3.2, mid + 0.6));
      cam.lookAt(p.x, mid, p.z);
      break;
    case "face":
      cam.position.copy(
        at(1.3, -0.35, head.y + 0.05).add(new THREE.Vector3(head.x - p.x, 0, head.z - p.z)),
      );
      cam.lookAt(head.x, head.y - 0.06, head.z);
      break;
    case "faceSide":
      cam.position.copy(
        at(0.9, -1.05, head.y + 0.1).add(new THREE.Vector3(head.x - p.x, 0, head.z - p.z)),
      );
      cam.lookAt(head.x, head.y - 0.06, head.z);
      break;
    case "withRacer":
      cam.position.copy(at(5.5, -1.2, 1.6));
      cam.lookAt(p.x + 1.1, 0.8, p.z + 0.2);
      cam.fov = 38;
      break;
    case "withDino":
      cam.position.set(p.x + 1.2, 1.7, p.z + 7.5);
      cam.lookAt(p.x + 2.0, 0.9, p.z - 1.2);
      cam.fov = 40;
      break;
    case "closeUp": {
      // As the cutscenes frame a speaker (staged.ts closeUp; the game's camera).
      const up = head.y < 1.2 ? 0.02 : 0.14;
      cam.position.copy(at(1.4 + 0.2, 0.5, head.y + up));
      cam.lookAt(p.x + fwd.x * 0.2, head.y - 0.2, p.z + fwd.z * 0.2);
      cam.fov = 62;
      break;
    }
    default:
      cam.position.copy(at(3.4, -2.6, mid + 0.55));
      cam.lookAt(p.x, mid, p.z);
  }
  cam.updateProjectionMatrix();
}

const cols = Number(params.get("cols") ?? (mode === "sheet" ? 3 : Math.min(cells.length, 4)));
const rows = Math.ceil(cells.length / cols);
const cams = cells.map(() => new THREE.PerspectiveCamera(30, 1, 0.05, 400));
function render() {
  const W = window.innerWidth;
  const H = window.innerHeight;
  renderer.setSize(W, H, false);
  renderer.setScissorTest(true);
  const cw = Math.floor(W / cols);
  const ch = Math.floor(H / rows);
  labels.innerHTML = "";
  cells.forEach((c, i) => {
    const cx = (i % cols) * cw;
    const cy = Math.floor(i / cols) * ch;
    const cam = cams[i]!;
    cam.aspect = cw / ch;
    aim(cam, c);
    renderer.setViewport(cx + 1, H - cy - ch + 1, cw - 2, ch - 2);
    renderer.setScissor(cx + 1, H - cy - ch + 1, cw - 2, ch - 2);
    renderer.render(scene, cam);
    const l = document.createElement("div");
    l.textContent = c.label;
    l.style.cssText = `position:absolute;left:${cx + 6}px;top:${cy + 4}px;text-shadow:0 1px 2px #000`;
    labels.appendChild(l);
  });
}

let last = performance.now();
const live = params.has("live");
function frame(now: number) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  if (live)
    for (const th of things) {
      const t = (clocks.get(th) ?? 0) + dt;
      clocks.set(th, t);
      step(th, t, dt);
    }
  render();
  Object.assign(window as object, { ready: true });
  // (Frozen: one picture is enough; software GL is slow.)
  if (live) requestAnimationFrame(frame);
}
window.addEventListener("resize", render);
requestAnimationFrame(frame);
Object.assign(window as object, { people: { things, cells, GESTURES } });
