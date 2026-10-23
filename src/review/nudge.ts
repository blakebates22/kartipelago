/**
 * Nudges in the review tool: pick up a track prop (a tree, a rock, a hut...) and move,
 * turn or resize it with handles, copy it or delete it. Each edit is saved as a review
 * note (kind "edit") with the prop's name and its transform before and after, for Claude
 * to bake into the track's build. Until then the edits are a preview: shown in the game
 * (when the review tool has been opened in this race) but the karts' collision doesn't
 * change.
 */
import * as THREE from "three";
import type { EditOp, ReviewNote, Transform } from "./notes";

/** Props bigger than this (bounding radius, metres) are terrain or road: pin those. */
export const MAX_PROP_RADIUS = 45;

/** The track's root node (named "track:<id>") above an object, if any. */
function trackRoot(o: THREE.Object3D): THREE.Object3D | undefined {
  for (let p: THREE.Object3D | null = o; p; p = p.parent) if (p.name.startsWith("track:")) return p;
  return undefined;
}

/** The whole prop an object belongs to: the node just under the track's root. */
export function propOf(o: THREE.Object3D): THREE.Object3D | undefined {
  const root = trackRoot(o);
  if (!root) return undefined;
  let p = o;
  while (p.parent && p.parent !== root) p = p.parent;
  return p.parent === root ? p : undefined;
}

export function radiusOf(o: THREE.Object3D) {
  const box = new THREE.Box3().setFromObject(o);
  return box.isEmpty() ? 0 : box.getBoundingSphere(new THREE.Sphere()).radius;
}

const round = (v: number, d = 3) => +v.toFixed(d);

/** An object's transform in the world. */
export function worldTransform(o: THREE.Object3D): Transform {
  o.updateWorldMatrix(true, false);
  const p = new THREE.Vector3();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  o.matrixWorld.decompose(p, q, s);
  return {
    pos: [round(p.x, 2), round(p.y, 2), round(p.z, 2)],
    quat: [round(q.x, 4), round(q.y, 4), round(q.z, 4), round(q.w, 4)],
    scale: [round(s.x), round(s.y), round(s.z)],
  };
}

/** Put an object at a world transform (under its own parent). */
export function setWorldTransform(o: THREE.Object3D, t: Transform) {
  const m = new THREE.Matrix4().compose(
    new THREE.Vector3(...t.pos),
    new THREE.Quaternion(...t.quat),
    new THREE.Vector3(...t.scale),
  );
  if (o.parent) {
    o.parent.updateWorldMatrix(true, false);
    m.premultiply(new THREE.Matrix4().copy(o.parent.matrixWorld).invert());
  }
  m.decompose(o.position, o.quaternion, o.scale);
  o.updateMatrixWorld(true);
}

/** Find a prop by name under any track root in the scene. */
export function findProp(scene: THREE.Object3D, name: string): THREE.Object3D | undefined {
  let found: THREE.Object3D | undefined;
  scene.traverse((o) => {
    if (!found && o.name === name && o.parent?.name.startsWith("track:")) found = o;
  });
  return found;
}

/**
 * Show a saved edit in the scene (once per race: a prop remembers which edit it has).
 * Copies are made from their source prop; deletes hide the prop.
 */
export function applyEdit(scene: THREE.Object3D, n: ReviewNote) {
  const e = n.edit;
  if (!e || n.status === "done") return;
  if (e.op === "copy") {
    if (findProp(scene, e.node)) return;
    const src = e.copyOf ? findProp(scene, e.copyOf) : undefined;
    if (!src?.parent) return;
    const c = src.clone();
    c.name = e.node;
    c.userData.reviewEdit = n.id;
    src.parent.add(c);
    setWorldTransform(c, e.to);
    return;
  }
  const o = findProp(scene, e.node);
  if (!o || o.userData.reviewEdit === `${n.id}:${n.created}`) return;
  if (e.op === "delete") o.visible = false;
  else setWorldTransform(o, e.to);
  o.userData.reviewEdit = `${n.id}:${n.created}`;
}

/** Undo a saved edit in the scene (when its note is deleted). */
export function revertEdit(scene: THREE.Object3D, n: ReviewNote) {
  const e = n.edit;
  if (!e) return;
  const o = findProp(scene, e.node);
  if (!o) return;
  if (e.op === "copy") {
    o.removeFromParent();
    return;
  }
  o.visible = true;
  setWorldTransform(o, e.from);
  delete o.userData.reviewEdit;
}

export type { EditOp };
