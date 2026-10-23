/**
 * REVIEW: the level review tool. Fly round a track with the race frozen and leave notes
 * exactly where you mean them, for Claude to act on (docs/review-tool.md).
 *
 * Open it with F2 in a race (or REVIEW TRACK in the pause menu, or ?review on the URL).
 *
 * Flying: WASD, Q / E down and up, Shift fast, the wheel sets the speed. Look with the
 * arrow keys, by dragging with the right mouse button, or press F to steer with the
 * mouse (a crosshair; click to place at it; F or Esc to let go).
 *
 * Tools (keys 1-5):
 *   1 PIN      click a surface: an arrow points at that exact spot, and the note records
 *              what was hit (its name in the track file) and where.
 *   2 BOX      click two corners on the ground: an area, then set its height.
 *   3 PATH     click along the ground, Enter to finish (Backspace takes a point back).
 *   4 MEASURE  click two points: the distance in metres.
 *   5 NOTE     a note about the whole track (no marker; the view is kept).
 * And RECORD LINE: drive the line you mean, F2 to stop.
 *
 * Every note keeps a screenshot (you can draw on it), the camera's view, tags and an
 * "important" flag. K jumps to your kart, Tab goes back to driving, Esc leaves.
 */
import * as THREE from "three";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import type { Session } from "../game/session";
import type { TrackEntry } from "../game/tracks";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";
import { TransformControls } from "three/examples/jsm/controls/TransformControls.js";
import { animateMarkers, disposeMarker, noteMarker } from "./markers";
import {
  MAX_PROP_RADIUS,
  applyEdit,
  propOf,
  radiusOf,
  revertEdit,
  setWorldTransform,
  worldTransform,
} from "./nudge";
import {
  newNoteId,
  openStore,
  type NoteKind,
  type NoteStore,
  type EditOp,
  type NoteTag,
  type Transform,
  type ReviewNote,
  type Vec3,
} from "./notes";

type Tool = "pin" | "box" | "path" | "measure" | "general" | "move";
const TOOLS: [Tool, string, string][] = [
  ["pin", "1", "PIN"],
  ["box", "2", "BOX"],
  ["path", "3", "PATH"],
  ["measure", "4", "MEASURE"],
  ["general", "5", "NOTE"],
  ["move", "6", "MOVE"],
];
const TAGS: NoteTag[] = ["art", "layout", "gameplay", "bug"];

const vec = (v: THREE.Vector3): Vec3 => [+v.x.toFixed(2), +v.y.toFixed(2), +v.z.toFixed(2)];

// ---------------------------------------------------------------------------------------
// Recording a driving line (while racing, between visits to the review screen).

let recording: { points: Vec3[]; last?: THREE.Vector3 } | undefined;
let recorded: Vec3[] | undefined;

export const isRecordingLine = () => recording !== undefined;

/** Called by the race screen every frame: samples your kart while a line is recording. */
export function recordLineFrame(session: Session) {
  if (!recording) return;
  const p = session.entrants[0]!.mesh.position;
  if (!recording.last || recording.last.distanceTo(p) > 1.2) {
    recording.points.push(vec(p));
    recording.last = p.clone();
  }
}

/** Stop recording (F2): the line goes to the review screen as a new note. */
export function stopRecordingLine() {
  recorded = recording?.points;
  recording = undefined;
}

// ---------------------------------------------------------------------------------------

const CSS = `
.kp-review { position: fixed; top: 0; right: 0; bottom: 0; width: 320px; z-index: 50;
  background: rgba(28, 18, 12, 0.94); color: #f6ecd2; font: 13px/1.35 ui-monospace, Menlo, monospace;
  display: flex; flex-direction: column; border-left: 3px solid #8a5a32; box-sizing: border-box; }
.kp-review * { box-sizing: border-box; }
.kp-review.hidden { transform: translateX(100%); }
.kp-review header { padding: 10px 12px 6px; border-bottom: 1px solid #5a3a20; }
.kp-review h1 { font-size: 15px; margin: 0; color: #ffd84a; letter-spacing: 1px; }
.kp-review .where { font-size: 11px; color: #c8a878; margin-top: 2px; }
.kp-review .banner { display: none; margin: 8px 12px 0; padding: 8px 10px; border-radius: 4px;
  font-weight: bold; font-size: 12px; line-height: 1.3; }
.kp-review .banner.bad { display: block; background: #b8241c; color: #fff; border: 2px solid #ff8a6a; }
.kp-review .banner.ok { display: block; background: #24561e; color: #e8ffe0; border: 2px solid #6ade5a; }
.kp-review .tools { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; padding: 8px 12px; }
.kp-review button, .kp-review-editor button { font: inherit; color: #f6ecd2; background: #5a3a20; border: 2px solid #8a5a32;
  border-radius: 4px; padding: 5px 4px; cursor: pointer; }
.kp-review button:hover, .kp-review-editor button:hover { background: #6a4628; }
.kp-review button.on, .kp-review-editor button.on { background: #ffd84a; color: #2b1b14; border-color: #fff0a0; }
.kp-review button.small, .kp-review-editor button.small { padding: 2px 6px; font-size: 11px; }
.kp-review button.danger { background: #7a2418; border-color: #a8301a; }
.kp-review .row { display: flex; gap: 6px; padding: 0 12px 8px; flex-wrap: wrap; }
.kp-review .hint { padding: 0 12px 8px; color: #ffd84a; min-height: 18px; font-size: 12px; }
.kp-review .list { flex: 1; overflow-y: auto; padding: 4px 8px; border-top: 1px solid #5a3a20; }
.kp-review .note { padding: 6px 8px; margin: 4px 0; background: #3a2616; border-radius: 4px;
  border-left: 4px solid #ff4ad8; cursor: pointer; }
.kp-review .note.done { border-left-color: #4ade5a; opacity: 0.75; }
.kp-review .note.important { border-left-color: #ff3a2a; }
.kp-review .note .meta { font-size: 11px; color: #c8a878; }
.kp-review .note .reply { margin-top: 4px; padding: 4px 6px; background: #24361e; border-radius: 3px; font-size: 12px; }
.kp-review .note .acts { margin-top: 4px; display: flex; gap: 4px; }
.kp-review footer { padding: 6px 12px 10px; font-size: 11px; color: #c8a878; border-top: 1px solid #5a3a20; }
.kp-review-editor * { box-sizing: border-box; }
.kp-review-editor { position: fixed; left: 16px; bottom: 16px; width: min(560px, calc(100vw - 370px));
  background: rgba(28, 18, 12, 0.97); border: 3px solid #ffd84a; border-radius: 6px; padding: 10px;
  z-index: 51; color: #f6ecd2; font: 13px/1.35 ui-monospace, Menlo, monospace; }
.kp-review-editor h2 { margin: 0 0 6px; font-size: 14px; color: #ffd84a; }
.kp-review-editor textarea { width: 100%; height: 84px; font: inherit; background: #f6ecd2; color: #2b1b14;
  border: 2px solid #8a5a32; border-radius: 4px; padding: 6px; resize: vertical; }
.kp-review-editor .shot { position: relative; margin-top: 6px; }
.kp-review-editor canvas { width: 100%; display: block; border: 2px solid #5a3a20; border-radius: 3px; }
.kp-review-editor canvas.pen { cursor: crosshair; border-color: #ff3a2a; }
.kp-review-editor .opts { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 6px; }
.kp-review-editor label { display: inline-flex; gap: 4px; align-items: center; cursor: pointer; }
.kp-review-editor .what { font-size: 11px; color: #c8a878; margin-bottom: 4px; word-break: break-all; }
`;

const el = <K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Partial<HTMLElementTagNameMap[K]> & { cls?: string } = {},
  ...kids: (Node | string)[]
) => {
  const e = document.createElement(tag);
  const { cls, ...rest } = props;
  if (cls) e.className = cls;
  Object.assign(e, rest);
  for (const k of kids) e.append(k);
  return e;
};

export function reviewScreen(game: Game, session: Session, entry: TrackEntry): Screen {
  const stage = game.stage;
  const scene = stage.scene;
  const cam = stage.camera;
  let store: NoteStore | undefined;
  let notes: ReviewNote[] = [];
  const markers = new THREE.Group();
  markers.name = "review-markers";
  const pending = new THREE.Group();
  pending.name = "review-pending";
  const markerOf = new Map<string, THREE.Object3D>();

  // The fly camera.
  const pos = new THREE.Vector3();
  let yaw = 0;
  let pitch = 0;
  let fov = 60;
  let speed = 14;
  const held = new Set<string>();
  let looking = false; // pointer locked: the mouse steers, click at the crosshair
  let dragging = false; // right button held: the mouse steers
  const mouse = { x: 0, y: 0 };

  let tool: Tool = "pin";
  let pts: THREE.Vector3[] = []; // corners / path points / measure ends being placed
  let boxYaw = 0;
  let hint = "";
  /** When Esc was last pressed with nothing to cancel (a second one leaves). */
  let escAt = -1e9;
  let seconds = 0;
  let wasLines = stage.lines;
  let capture: ((url: string) => void) | undefined;
  /** The note being written: new (not yet saved) or an existing one. */
  let editing: { note: ReviewNote; isNew: boolean; shot?: string } | undefined;

  // ----- The panel ---------------------------------------------------------------------
  const style = el("style", { textContent: CSS });
  const panel = el("div", { cls: "kp-review" });
  const where = el("div", { cls: "where", textContent: "Loading notes..." });
  const banner = el("div", { cls: "banner" });
  const toolButtons = new Map<Tool, HTMLButtonElement>();
  const tools = el("div", { cls: "tools" });
  for (const [t, key, name] of TOOLS) {
    const b = el("button", { textContent: `${key} ${name}`, title: name });
    b.onclick = () => pickTool(t);
    toolButtons.set(t, b);
    tools.append(b);
  }
  const hintEl = el("div", { cls: "hint" });
  const recordBtn = el("button", {
    textContent: "● RECORD LINE",
    title: "Drive the line you mean; F2 stops",
  });
  recordBtn.onclick = () => {
    recording = { points: [] };
    session.showToast("● RECORDING YOUR LINE: F2 TO STOP", 3);
    leave();
  };
  const kartBtn = el("button", { textContent: "K TO KART" });
  kartBtn.onclick = () => toKart();
  const exportBtn = el("button", { textContent: "EXPORT" });
  exportBtn.onclick = () => exportNotes();
  const driveBtn = el("button", {
    textContent: "TAB DRIVE FROM HERE",
    title: "Your kart, put down under the camera (Shift+Tab: back to it where it was)",
  });
  driveBtn.onclick = () => driveFromHere();
  const list = el("div", { cls: "list" });
  panel.append(
    el("header", {}, el("h1", { textContent: `REVIEW · ${entry.name.toUpperCase()}` }), where),
    banner,
    tools,
    hintEl,
    el("div", { cls: "row" }, recordBtn, kartBtn, exportBtn, driveBtn),
    list,
    el("footer", {
      innerHTML:
        "WASD fly · Q/E down/up · Shift fast · wheel speed<br>Arrows or right-drag look · F mouse-look<br>Tab drive from here · Shift+Tab back to kart<br>Enter finish path · Backspace undo · H hide · Esc Esc leave",
    }),
  );

  function pickTool(t: Tool) {
    if (grabbed && t !== "move") cancelGrab();
    tool = t;
    clearPending();
    for (const [k, b] of toolButtons) b.classList.toggle("on", k === t);
    if (t === "general") startNote("general", {});
    updateHint();
  }

  function updateHint() {
    hint =
      editing !== undefined
        ? "WRITE YOUR NOTE, THEN SAVE"
        : tool === "move"
          ? grabbed
            ? "DRAG THE HANDLES · G MOVE · R TURN · T SIZE"
            : "CLICK A PROP (TREE, ROCK, HUT...) TO PICK IT UP"
          : tool === "pin"
            ? "CLICK THE THING YOU MEAN"
            : tool === "box"
              ? pts.length
                ? "CLICK THE OPPOSITE CORNER"
                : "CLICK ONE CORNER OF THE AREA"
              : tool === "path"
                ? pts.length
                  ? `${pts.length} POINTS · ENTER TO FINISH · BACKSPACE UNDO`
                  : "CLICK ALONG THE GROUND"
                : tool === "measure"
                  ? pts.length
                    ? "CLICK THE OTHER END"
                    : "CLICK THE FIRST POINT"
                  : "";
    hintEl.textContent = hint;
  }

  function renderList() {
    list.replaceChildren();
    if (!notes.length)
      list.append(
        el("div", { cls: "meta", textContent: "No notes yet. Pick a tool and click the track." }),
      );
    for (const n of [...notes].reverse()) {
      const kind = n.kind === "line" ? "LINE" : n.kind.toUpperCase();
      const item = el(
        "div",
        { cls: `note${n.status === "done" ? " done" : ""}${n.important ? " important" : ""}` },
        el("div", {
          cls: "meta",
          textContent: `#${n.number} ${kind}${n.tags.length ? " · " + n.tags.join(", ") : ""}${n.status === "done" ? " · DONE" : ""}`,
        }),
        el("div", { textContent: n.text || "(no text)" }),
      );
      if (n.reply) item.append(el("div", { cls: "reply", textContent: `Claude: ${n.reply}` }));
      const go = el("button", { cls: "small", textContent: "GO" });
      go.onclick = (e) => {
        e.stopPropagation();
        flyTo(n);
      };
      const edit = el("button", { cls: "small", textContent: "EDIT" });
      edit.onclick = (e) => {
        e.stopPropagation();
        flyTo(n);
        openEditor({ note: structuredClone(n), isNew: false });
      };
      const state = el("button", {
        cls: "small",
        textContent: n.status === "done" ? "REOPEN" : "DONE",
      });
      state.onclick = (e) => {
        e.stopPropagation();
        n.status = n.status === "done" ? "open" : "done";
        void persist(n);
      };
      const del = el("button", { cls: "small danger", textContent: "DELETE" });
      del.onclick = (e) => {
        e.stopPropagation();
        if (del.dataset.sure) {
          void store?.remove(n.id).then(() => {
            if (n.kind === "edit") revertEdit(scene, n);
            notes = notes.filter((x) => x.id !== n.id);
            refreshMarkers();
            renderList();
          });
        } else {
          del.dataset.sure = "1";
          del.textContent = "SURE?";
        }
      };
      item.append(el("div", { cls: "acts" }, go, edit, state, del));
      item.onclick = () => flyTo(n);
      list.append(item);
    }
  }

  // ----- Markers -----------------------------------------------------------------------
  function refreshMarkers() {
    for (const m of markerOf.values()) {
      markers.remove(m);
      disposeMarker(m);
    }
    markerOf.clear();
    for (const n of notes) {
      const m = noteMarker(n, editing?.note.id === n.id);
      markers.add(m);
      markerOf.set(n.id, m);
    }
  }
  function clearPending() {
    pts = [];
    for (const c of [...pending.children]) {
      pending.remove(c);
      disposeMarker(c);
    }
  }
  /** Show the note being placed (yellow). */
  function showPending(n?: ReviewNote) {
    for (const c of [...pending.children]) {
      pending.remove(c);
      disposeMarker(c);
    }
    if (n) pending.add(noteMarker(n, true));
    else if (pts.length) {
      // Points so far.
      const dummy = draft("path", { path: pts.map(vec) });
      pending.add(noteMarker(dummy, true));
    }
  }

  // ----- Camera ------------------------------------------------------------------------
  const euler = new THREE.Euler(0, 0, 0, "YXZ");
  function applyCamera() {
    euler.set(pitch, yaw, 0, "YXZ");
    cam.position.copy(pos);
    cam.up.set(0, 1, 0);
    cam.quaternion.setFromEuler(euler);
    cam.fov = fov;
    cam.updateProjectionMatrix();
  }
  function flyTo(n: ReviewNote) {
    pos.fromArray(n.camera.pos);
    euler.setFromQuaternion(new THREE.Quaternion().fromArray(n.camera.quat), "YXZ");
    yaw = euler.y;
    pitch = euler.x;
    fov = n.camera.fov;
  }
  function toKart() {
    const m = session.entrants[0]!.mesh;
    const h = m.rotation.y;
    pos.set(m.position.x - Math.sin(h) * 7, m.position.y + 3.5, m.position.z - Math.cos(h) * 7);
    yaw = h + Math.PI;
    pitch = -0.25;
  }

  // ----- Picking -----------------------------------------------------------------------
  const ray = new THREE.Raycaster();
  function pick():
    | { point: THREE.Vector3; normal: THREE.Vector3; object: THREE.Object3D; instance?: number }
    | undefined {
    applyCamera();
    cam.updateMatrixWorld();
    const ndc = looking ? new THREE.Vector2(0, 0) : new THREE.Vector2(mouse.x, mouse.y);
    ray.setFromCamera(ndc, cam);
    const targets = scene.children.filter(
      (o) =>
        o !== markers && o !== pending && o !== gizmoHelper && o.name !== "sky dome" && o.visible,
    );
    for (const hit of ray.intersectObjects(targets, true)) {
      const o = hit.object;
      if (!(o as THREE.Mesh).isMesh || (o as THREE.Sprite).isSprite) continue;
      let vis = true;
      for (let p: THREE.Object3D | null = o; p; p = p.parent) if (!p.visible) vis = false;
      if (!vis) continue;
      const mat = (o as THREE.Mesh).material as THREE.Material;
      if (mat && !Array.isArray(mat) && mat.transparent && mat.opacity < 0.2) continue;
      const normal = hit.face
        ? hit.face.normal.clone().transformDirection(o.matrixWorld)
        : new THREE.Vector3(0, 1, 0);
      if (normal.dot(ray.ray.direction) > 0) normal.negate();
      return { point: hit.point.clone(), normal, object: o, instance: hit.instanceId };
    }
    return undefined;
  }
  const pathOf = (o: THREE.Object3D) => {
    const names: string[] = [];
    for (let p: THREE.Object3D | null = o; p && p !== scene; p = p.parent)
      if (p.name) names.unshift(p.name);
    return names;
  };

  function draft(kind: NoteKind, extra: Partial<ReviewNote>): ReviewNote {
    return {
      id: newNoteId(),
      number: Math.max(0, ...notes.map((n) => n.number)) + 1,
      kind,
      text: "",
      tags: [],
      important: false,
      status: "open",
      created: new Date().toISOString(),
      camera: {
        pos: vec(pos),
        quat: cam.quaternion.toArray().map((x) => +x.toFixed(4)) as [
          number,
          number,
          number,
          number,
        ],
        fov,
      },
      ...extra,
    };
  }

  function clickAt() {
    if (editing) return;
    if (tool === "general") return;
    if (tool === "move" && (gizmo?.dragging || gizmo?.axis)) return;
    const hit = pick();
    if (!hit) {
      hint = "NOTHING THERE: CLICK A SURFACE";
      hintEl.textContent = hint;
      return;
    }
    if (tool === "move") {
      const prop = propOf(hit.object);
      if (!prop) hintEl.textContent = "THAT'S NOT PART OF THE TRACK: USE A PIN";
      else if (radiusOf(prop) > MAX_PROP_RADIUS)
        hintEl.textContent = "TOO BIG TO MOVE HERE (GROUND OR ROAD): USE A PIN OR A BOX";
      else grab(prop);
      return;
    }
    if (tool === "pin") {
      const p = pathOf(hit.object);
      startNote("pin", {
        pin: {
          point: vec(hit.point),
          normal: vec(hit.normal),
          object: p[p.length - 1] ?? hit.object.type,
          path: p,
          ...(hit.instance !== undefined ? { instance: hit.instance } : {}),
        },
      });
    } else if (tool === "box") {
      if (!pts.length) {
        pts = [hit.point];
        boxYaw = yaw;
        showPending();
      } else {
        pts.push(hit.point);
        startNote("box", { box: boxFrom(pts[0]!, pts[1]!, 6) });
      }
    } else if (tool === "measure") {
      if (!pts.length) {
        pts = [hit.point];
        showPending();
      } else {
        const a = pts[0]!;
        const b = hit.point;
        startNote("measure", {
          measure: { a: vec(a), b: vec(b), metres: +a.distanceTo(b).toFixed(2) },
        });
      }
    } else if (tool === "path") {
      pts.push(hit.point);
      showPending();
    }
    updateHint();
  }

  function boxFrom(a: THREE.Vector3, b: THREE.Vector3, height: number) {
    // Corners in the frame turned to the camera's heading when the first was placed.
    const c = Math.cos(boxYaw);
    const s = Math.sin(boxYaw);
    const local = (p: THREE.Vector3) => ({ x: p.x * c - p.z * s, z: p.x * s + p.z * c });
    const la = local(a);
    const lb = local(b);
    const cx = (la.x + lb.x) / 2;
    const cz = (la.z + lb.z) / 2;
    const w = Math.max(1, Math.abs(la.x - lb.x));
    const d = Math.max(1, Math.abs(la.z - lb.z));
    const base = Math.min(a.y, b.y) - 0.5;
    const center = new THREE.Vector3(cx * c + cz * s, base + height / 2, -cx * s + cz * c);
    const box = {
      center: vec(center),
      size: [+w.toFixed(2), height, +d.toFixed(2)] as Vec3,
      yaw: +boxYaw.toFixed(3),
    };
    return { ...box, objects: objectsIn(box) };
  }
  /** The named things whose middles are inside a box (for Claude: what's in the area). */
  function objectsIn(b: { center: Vec3; size: Vec3; yaw: number }) {
    const inv = new THREE.Matrix4()
      .makeRotationY(b.yaw)
      .setPosition(b.center[0], b.center[1], b.center[2])
      .invert();
    const out = new Set<string>();
    const v = new THREE.Vector3();
    scene.traverse((o) => {
      if (out.size >= 40 || !(o as THREE.Mesh).isMesh) return;
      // Only the track's own things (not karts, items or markers), by prop name.
      const prop = propOf(o);
      if (!prop?.name || out.has(prop.name)) return;
      const m = o as THREE.Mesh;
      if (!m.geometry.boundingSphere) m.geometry.computeBoundingSphere();
      v.copy(m.geometry.boundingSphere!.center).applyMatrix4(o.matrixWorld).applyMatrix4(inv);
      if (
        Math.abs(v.x) <= b.size[0] / 2 &&
        Math.abs(v.y) <= b.size[1] / 2 &&
        Math.abs(v.z) <= b.size[2] / 2
      )
        out.add(prop.name);
    });
    return [...out];
  }

  function finishPath() {
    if (tool !== "path" || pts.length < 2 || editing) return;
    startNote("path", { path: pts.map(vec) });
  }

  // ----- Writing a note ----------------------------------------------------------------
  function startNote(kind: NoteKind, extra: Partial<ReviewNote>) {
    const note = draft(kind, extra);
    showPending(note);
    // Take the screenshot with the new marker in it, then open the editor.
    capture = (url) => openEditor({ note, isNew: true, shot: url });
  }

  let editorEl: HTMLElement | undefined;
  function closeEditor() {
    editorEl?.remove();
    editorEl = undefined;
    editing = undefined;
    clearPending();
    refreshMarkers();
    updateHint();
  }

  function openEditor(ed: NonNullable<typeof editing>) {
    editorEl?.remove();
    editing = ed;
    const n = ed.note;
    if (!ed.isNew) refreshMarkers();
    const kind = n.kind === "line" ? "DRIVING LINE" : n.kind.toUpperCase();
    const text = el("textarea", {
      value: n.text,
      placeholder:
        n.kind === "general"
          ? "What would you change about the whole track?"
          : "What should change here? (Be as rough as you like.)",
    });
    const what = el("div", {
      cls: "what",
      textContent: n.pin
        ? `On: ${n.pin.path.join(" › ") || n.pin.object}${n.pin.instance !== undefined ? ` [#${n.pin.instance}]` : ""}`
        : n.box
          ? `Area ${n.box.size[0]} × ${n.box.size[2]} m${n.box.objects.length ? ` · has ${n.box.objects.slice(0, 8).join(", ")}${n.box.objects.length > 8 ? "…" : ""}` : ""}`
          : n.measure
            ? `Distance: ${n.measure.metres.toFixed(1)} m`
            : n.path
              ? `${n.path.length} points`
              : "The whole track",
    });
    const tagBoxes = TAGS.map((t) => {
      const c = el("input", { type: "checkbox", checked: n.tags.includes(t) });
      return [t, c, el("label", {}, c, t.toUpperCase())] as const;
    });
    const imp = el("input", { type: "checkbox", checked: n.important });
    const opts = el(
      "div",
      { cls: "opts" },
      ...tagBoxes.map((x) => x[2]),
      el("label", {}, imp, "IMPORTANT"),
    );
    let height: HTMLInputElement | undefined;
    if (n.box) {
      height = el("input", { type: "range", min: "1", max: "40", value: String(n.box.size[1]) });
      height.oninput = () => {
        if (!n.box || pts.length < 2) return;
        n.box = boxFrom(pts[0]!, pts[1]!, Number(height!.value));
        showPending(n);
      };
      opts.append(el("label", {}, "HEIGHT", height));
    }
    // The screenshot, to draw on.
    const shot = el("canvas");
    const strokes: { x: number; y: number }[][] = [];
    let img: HTMLImageElement | undefined;
    let pen = false;
    const redraw = () => {
      const g = shot.getContext("2d")!;
      if (img) g.drawImage(img, 0, 0, shot.width, shot.height);
      g.strokeStyle = "#ff2a2a";
      g.lineWidth = Math.max(3, shot.width / 220);
      g.lineCap = g.lineJoin = "round";
      for (const s of strokes) {
        g.beginPath();
        s.forEach((p, i) => (i ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y)));
        g.stroke();
      }
    };
    const loadShot = (src?: string) => {
      if (!src) return;
      img = new Image();
      img.onload = () => {
        shot.width = img!.naturalWidth;
        shot.height = img!.naturalHeight;
        redraw();
      };
      img.src = src;
    };
    loadShot(ed.shot ?? (store ? store.shotUrl(n) : undefined));
    const at = (e: PointerEvent) => {
      const r = shot.getBoundingClientRect();
      return {
        x: ((e.clientX - r.left) / r.width) * shot.width,
        y: ((e.clientY - r.top) / r.height) * shot.height,
      };
    };
    shot.onpointerdown = (e) => {
      if (!pen) return;
      shot.setPointerCapture(e.pointerId);
      strokes.push([at(e)]);
    };
    shot.onpointermove = (e) => {
      if (!pen || !(e.buttons & 1) || !strokes.length) return;
      strokes[strokes.length - 1]!.push(at(e));
      redraw();
    };
    const penBtn = el("button", { cls: "small", textContent: "✎ DRAW" });
    penBtn.onclick = () => {
      pen = !pen;
      penBtn.classList.toggle("on", pen);
      shot.classList.toggle("pen", pen);
    };
    const undoBtn = el("button", { cls: "small", textContent: "UNDO LINE" });
    undoBtn.onclick = () => {
      strokes.pop();
      redraw();
    };
    const retake = el("button", { cls: "small", textContent: "RETAKE SHOT" });
    retake.onclick = () => {
      editorEl!.style.visibility = "hidden";
      capture = (url) => {
        editorEl!.style.visibility = "";
        ed.shot = url;
        strokes.length = 0;
        loadShot(url);
      };
    };
    const save = el("button", { textContent: "SAVE NOTE" });
    const cancel = el("button", { textContent: "CANCEL" });
    cancel.onclick = () => closeEditor();
    save.onclick = () => {
      n.text = text.value.trim();
      n.tags = tagBoxes.filter((x) => x[1].checked).map((x) => x[0]);
      n.important = imp.checked;
      const changedShot = ed.isNew || strokes.length > 0 || ed.shot !== undefined;
      const url = changedShot && img ? (redraw(), shot.toDataURL("image/jpeg", 0.85)) : undefined;
      save.disabled = true;
      void persist(n, url).then(() => closeEditor());
    };
    editorEl = el(
      "div",
      { cls: "kp-review-editor" },
      el("h2", { textContent: `${ed.isNew ? "NEW" : "EDIT"} ${kind} · #${n.number}` }),
      what,
      text,
      opts,
      el("div", { cls: "shot" }, shot),
      el(
        "div",
        { cls: "opts" },
        penBtn,
        undoBtn,
        retake,
        el("span", { style: "flex: 1" } as never),
        cancel,
        save,
      ),
    );
    document.body.append(editorEl);
    updateHint();
    setTimeout(() => text.focus(), 0);
  }

  async function persist(n: ReviewNote, shot?: string) {
    if (!store) return;
    try {
      await store.save(n, shot);
      const i = notes.findIndex((x) => x.id === n.id);
      if (i >= 0) notes[i] = n;
      else notes.push(n);
      where.textContent = savedWhere();
    } catch (err) {
      where.textContent = `Couldn't save: ${(err as Error).message}`;
    }
    refreshMarkers();
    renderList();
  }

  /** Say loudly where notes are going, and if browser-only notes were just sent up. */
  function showWhere(w: "repo" | "local", synced: number) {
    banner.className = `banner ${w === "repo" ? (synced ? "ok" : "") : "bad"}`;
    banner.textContent =
      w === "local"
        ? import.meta.env.DEV
          ? "NOT SAVING TO THE PROJECT: the dev server didn't answer. Notes are kept in this browser and sent to the project automatically next time it does."
          : "This build can't save into the project (run npm run dev). Notes stay in this browser: use EXPORT."
        : synced
          ? `Sent ${synced} note${synced === 1 ? "" : "s"} kept in this browser to the project.`
          : "";
  }
  const savedWhere = () =>
    store?.where === "repo"
      ? `${notes.length} notes · saved into the repo: reviews/${entry.id}/`
      : `${notes.length} notes · kept in this browser only (EXPORT to send them)`;

  function exportNotes() {
    if (!store) return;
    const blob = new Blob([JSON.stringify(store.exportFile(), null, 2)], {
      type: "application/json",
    });
    const a = el("a", { href: URL.createObjectURL(blob), download: `review-${entry.id}.json` });
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ----- Nudges (the MOVE tool) -------------------------------------------------------
  let gizmo: TransformControls | undefined;
  let gizmoHelper: THREE.Object3D | undefined;
  /** The prop picked up: how it was before (to cancel), and the edit so far. */
  let grabbed:
    | {
        prop: THREE.Object3D;
        before: Transform;
        wasVisible: boolean;
        op: EditOp;
        copyOf?: string;
        /** The prop's open edit note, if it already has one (it's updated, not doubled). */
        note?: ReviewNote;
        from: Transform;
      }
    | undefined;
  let nudgeEl: HTMLElement | undefined;

  const openEditFor = (name: string) =>
    notes.find((n) => n.kind === "edit" && n.status === "open" && n.edit?.node === name);

  function grab(prop: THREE.Object3D, op: EditOp = "move", copyOf?: string, from?: Transform) {
    if (grabbed) cancelGrab();
    const note = op === "move" ? openEditFor(prop.name) : undefined;
    const before = worldTransform(prop);
    grabbed = {
      prop,
      before,
      wasVisible: prop.visible,
      op,
      copyOf,
      note,
      from: from ?? note?.edit?.from ?? before,
    };
    gizmo?.attach(prop);
    showNudgePanel();
    updateHint();
  }

  function releaseGizmo() {
    gizmo?.detach();
    nudgeEl?.remove();
    nudgeEl = undefined;
  }

  function cancelGrab() {
    const g = grabbed;
    if (!g) return;
    grabbed = undefined;
    releaseGizmo();
    if (g.op === "copy") g.prop.removeFromParent();
    else {
      g.prop.visible = g.wasVisible;
      setWorldTransform(g.prop, g.before);
    }
    updateHint();
  }

  function saveGrab(text: string) {
    const g = grabbed;
    if (!g) return;
    grabbed = undefined;
    releaseGizmo();
    const n = g.note ?? draft("edit", {});
    n.text = text || n.text;
    n.edit = {
      op: g.op === "move" && !g.prop.visible ? "delete" : g.op,
      node: g.prop.name,
      ...(g.copyOf ? { copyOf: g.copyOf } : {}),
      from: g.from,
      to: worldTransform(g.prop),
    };
    g.prop.userData.reviewEdit = g.op === "copy" ? n.id : `${n.id}:${n.created}`;
    // The screenshot shows the prop where it now is.
    capture = (url) => void persist(n, url);
    updateHint();
  }

  function copyGrabbed() {
    const g = grabbed;
    if (!g?.prop.parent) return;
    const src = g.prop;
    const base = g.copyOf ?? src.name;
    let k = 1;
    const taken = (name: string) => {
      let hit = false;
      scene.traverse((o) => (hit ||= o.name === name));
      return hit;
    };
    while (taken(`${base} copy ${k}`)) k++;
    // Keep the original where it was (and its edit, if it moved), and pick up the copy.
    const c = src.clone();
    c.name = `${base} copy ${k}`;
    src.parent!.add(c);
    const r = new THREE.Vector3(1, 0, 0).applyEuler(new THREE.Euler(0, yaw, 0));
    const t = worldTransform(src);
    t.pos = [t.pos[0] + r.x * 3, t.pos[1], t.pos[2] + r.z * 3];
    setWorldTransform(c, t);
    if (g.op === "move" && g.note === undefined) {
      // The original wasn't saved as moved: put it back.
      src.visible = g.wasVisible;
      setWorldTransform(src, g.before);
    }
    grabbed = undefined;
    releaseGizmo();
    grab(c, "copy", base, worldTransform(src));
  }

  function showNudgePanel() {
    nudgeEl?.remove();
    const g = grabbed!;
    const modes: [string, "translate" | "rotate" | "scale"][] = [
      ["G MOVE", "translate"],
      ["R TURN", "rotate"],
      ["T SIZE", "scale"],
    ];
    const modeBtns = modes.map(([label, m]) => {
      const b = el("button", { cls: "small", textContent: label });
      b.onclick = () => setMode(m);
      return [m, b] as const;
    });
    const setMode = (m: "translate" | "rotate" | "scale") => {
      gizmo?.setMode(m);
      for (const [k, b] of modeBtns) b.classList.toggle("on", k === m);
    };
    setMode("translate");
    const snap = el("input", { type: "checkbox" });
    snap.onchange = () => {
      gizmo?.setTranslationSnap(snap.checked ? 0.5 : null);
      gizmo?.setRotationSnap(snap.checked ? Math.PI / 12 : null);
      gizmo?.setScaleSnap(snap.checked ? 0.1 : null);
    };
    const copy = el("button", { cls: "small", textContent: "COPY" });
    copy.onclick = () => copyGrabbed();
    const del = el("button", { cls: "small danger", textContent: "DELETE" });
    del.onclick = () => {
      g.prop.visible = false;
      del.classList.add("on");
    };
    const text = el("textarea", {
      value: g.note?.text ?? "",
      placeholder: "Anything to add? (optional)",
    });
    text.style.height = "54px";
    const save = el("button", { textContent: "SAVE EDIT" });
    save.onclick = () => saveGrab(text.value.trim());
    const cancel = el("button", { textContent: "CANCEL" });
    cancel.onclick = () => cancelGrab();
    nudgeEl = el(
      "div",
      { cls: "kp-review-editor" },
      el("h2", {
        textContent: `${g.op === "copy" ? "COPY OF" : "MOVING"} ${g.copyOf ?? g.prop.name}`,
      }),
      el("div", {
        cls: "what",
        textContent:
          "Drag the handles. It's a preview: karts don't bump into the new spot until Claude bakes it into the track.",
      }),
      el(
        "div",
        { cls: "opts" },
        ...modeBtns.map((x) => x[1]),
        el("label", {}, snap, "SNAP"),
        copy,
        del,
      ),
      text,
      el("div", { cls: "opts" }, el("span", { style: "flex: 1" } as never), cancel, save),
    );
    document.body.append(nudgeEl);
  }

  // ----- Input -------------------------------------------------------------------------
  const typing = (e: Event) => {
    const t = e.target as HTMLElement | null;
    return t?.tagName === "TEXTAREA" || t?.tagName === "INPUT";
  };
  const inPanel = (e: Event) => panel.contains(e.target as Node);
  const onKey = (e: KeyboardEvent) => {
    if (typing(e)) {
      if (e.code === "Escape") (e.target as HTMLElement).blur();
      return;
    }
    if (e.code === "Tab") {
      // Tab: drive from here (your kart put down where you're looking from). Shift+Tab:
      // back to your kart where it was.
      e.preventDefault();
      if (e.repeat) return;
      if (e.shiftKey) leave();
      else driveFromHere();
      return;
    }
    if (e.repeat && !/^Arrow|^Key[WASDQE]$|^Shift/.test(e.code)) return;
    held.add(e.code);
    const toolKey = TOOLS.find(([, k]) => e.code === `Digit${k}`);
    if (toolKey && !editing) pickTool(toolKey[0]);
    else if (grabbed && e.code === "KeyG") gizmo?.setMode("translate");
    else if (grabbed && e.code === "KeyR") gizmo?.setMode("rotate");
    else if (grabbed && e.code === "KeyT") gizmo?.setMode("scale");
    else if (e.code === "KeyF") toggleLook();
    else if (e.code === "KeyK") toKart();
    else if (e.code === "KeyH") panel.classList.toggle("hidden");
    else if (e.code === "Enter") finishPath();
    else if (e.code === "Backspace" && pts.length && !editing) {
      pts.pop();
      showPending();
      updateHint();
    } else if (e.code === "Escape") {
      if (looking) toggleLook();
      else if (grabbed) cancelGrab();
      else if (editing) closeEditor();
      else if (pts.length) {
        clearPending();
        updateHint();
      } else if (performance.now() - escAt < 2000) leave();
      else {
        // Leaving takes a second Esc, so a stray one doesn't drop you out of the tool.
        escAt = performance.now();
        hint = "PRESS ESC AGAIN TO LEAVE · TAB DRIVES FROM HERE";
        hintEl.textContent = hint;
      }
    }
    if (/^Arrow|^Space/.test(e.code)) e.preventDefault();
  };
  const onKeyUp = (e: KeyboardEvent) => held.delete(e.code);
  const canvas = stage.renderer.domElement;
  const toNdc = (e: MouseEvent) => {
    const r = canvas.getBoundingClientRect();
    mouse.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    mouse.y = -((e.clientY - r.top) / r.height) * 2 + 1;
  };
  const onDown = (e: MouseEvent) => {
    if (inPanel(e)) return;
    toNdc(e);
    if (e.button === 2) dragging = true;
    else if (e.button === 0) clickAt();
  };
  const onUp = (e: MouseEvent) => {
    if (e.button === 2) dragging = false;
  };
  const onMove = (e: MouseEvent) => {
    if (inPanel(e) && !looking) return;
    toNdc(e);
    if (looking || dragging) {
      yaw -= e.movementX * 0.0035;
      pitch = Math.max(-1.5, Math.min(1.5, pitch - e.movementY * 0.0035));
    }
  };
  const onWheel = (e: WheelEvent) => {
    if (inPanel(e)) return;
    speed = Math.max(2, Math.min(120, speed * (e.deltaY > 0 ? 0.85 : 1.18)));
    hintEl.textContent = `FLY SPEED ${speed.toFixed(0)} M/S`;
  };
  const noMenu = (e: Event) => {
    if (!inPanel(e)) e.preventDefault();
  };
  const onLock = () => {
    looking = document.pointerLockElement === canvas;
  };
  function toggleLook() {
    if (looking) document.exitPointerLock();
    else void canvas.requestPointerLock();
  }

  function leave() {
    game.screens.pop();
  }

  /** Put your kart on the ground under the camera, facing the way you're looking, and go. */
  function driveFromHere() {
    session.placeYou(pos.x, pos.z, yaw + Math.PI, pos.y);
    leave();
  }

  return {
    id: "REVIEW",
    seeThrough: false,
    enter() {
      game.ui.interactive = false;
      wasLines = stage.lines;
      stage.setResolution(0);
      // Start where the race camera is.
      pos.copy(cam.position);
      euler.setFromQuaternion(cam.quaternion, "YXZ");
      yaw = euler.y;
      pitch = euler.x;
      fov = cam.fov;
      scene.add(markers, pending);
      gizmo = new TransformControls(cam, stage.renderer.domElement);
      gizmo.setSize(1.1);
      gizmoHelper = gizmo.getHelper();
      scene.add(gizmoHelper);
      document.head.append(style);
      document.body.append(panel);
      window.addEventListener("keydown", onKey);
      window.addEventListener("keyup", onKeyUp);
      window.addEventListener("mousedown", onDown);
      window.addEventListener("mouseup", onUp);
      window.addEventListener("mousemove", onMove);
      window.addEventListener("wheel", onWheel, { passive: true });
      window.addEventListener("contextmenu", noMenu);
      document.addEventListener("pointerlockchange", onLock);
      pickTool("pin");
      void openStore(entry.id, entry.name).then(async (s) => {
        store = s;
        notes = await s.load();
        showWhere(s.where, s.synced);
        // Show the edits not yet baked into the track.
        for (const n of notes) if (n.kind === "edit") applyEdit(scene, n);
        where.textContent = savedWhere();
        refreshMarkers();
        renderList();
        // Back from recording a driving line: write it up.
        if (recorded && recorded.length > 1) {
          const line = recorded;
          recorded = undefined;
          startNote("line", { path: line });
        }
      });
      renderList();
    },
    exit() {
      if (looking) document.exitPointerLock();
      if (grabbed) cancelGrab();
      if (gizmoHelper) scene.remove(gizmoHelper);
      gizmo?.dispose();
      gizmo = undefined;
      gizmoHelper = undefined;
      stage.setResolution(wasLines);
      scene.remove(markers, pending);
      for (const m of markerOf.values()) disposeMarker(m);
      clearPending();
      editorEl?.remove();
      editorEl = undefined;
      editing = undefined;
      panel.remove();
      style.remove();
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("keyup", onKeyUp);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("contextmenu", noMenu);
      document.removeEventListener("pointerlockchange", onLock);
    },
    frame(dt) {
      seconds += dt;
      // Fly.
      const fast = held.has("ShiftLeft") || held.has("ShiftRight") ? 4 : 1;
      const step = speed * fast * dt;
      euler.set(pitch, yaw, 0, "YXZ");
      const fwd = new THREE.Vector3(0, 0, -1).applyEuler(euler);
      const right = new THREE.Vector3(1, 0, 0).applyEuler(euler);
      if (held.has("KeyW")) pos.addScaledVector(fwd, step);
      if (held.has("KeyS")) pos.addScaledVector(fwd, -step);
      if (held.has("KeyD")) pos.addScaledVector(right, step);
      if (held.has("KeyA")) pos.addScaledVector(right, -step);
      if (held.has("KeyE")) pos.y += step;
      if (held.has("KeyQ")) pos.y -= step;
      const turn = 1.6 * dt;
      if (held.has("ArrowLeft")) yaw += turn;
      if (held.has("ArrowRight")) yaw -= turn;
      if (held.has("ArrowUp")) pitch = Math.min(1.5, pitch + turn);
      if (held.has("ArrowDown")) pitch = Math.max(-1.5, pitch - turn);
    },
    render3d() {
      // The race stays frozen: drawn as it stands, from the fly camera.
      session.render(1, 0);
      applyCamera();
      animateMarkers(markers, seconds);
      animateMarkers(pending, seconds);
      stage.render();
      if (capture) {
        const done = capture;
        capture = undefined;
        done(stage.renderer.domElement.toDataURL("image/jpeg", 0.85));
      }
      return true;
    },
    draw(ui: UiLayer) {
      if (looking) {
        const cx = Math.round(ui.W / 2);
        const cy = Math.round(ui.H / 2);
        ui.rect(cx - 5, cy, 4, 1, PAL.gold);
        ui.rect(cx + 2, cy, 4, 1, PAL.gold);
        ui.rect(cx, cy - 5, 1, 4, PAL.gold);
        ui.rect(cx, cy + 2, 1, 4, PAL.gold);
      }
      ui.text("REVIEW", 6, 6, { color: PAL.gold, outline: PAL.shadow });
      // The hint is on the panel; repeat it here only while the mouse steers (no cursor).
      if (hint && looking) ui.text(hint, 6, 16, { color: PAL.cream, outline: PAL.shadow });
    },
  };
}
