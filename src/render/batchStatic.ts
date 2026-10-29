/**
 * The track's still scenery drawn in batches (Blake, Oct 29: "things are very very laggy"):
 * a world has thousands of separate props (the valley about 4,700: every tree, fern,
 * rock, cattail and post its own mesh), and each was a draw call of its own, up to 2,000
 * a frame. Here the props that never move are merged, one mesh per material per patch of
 * the map (CELL metres square), and drawn instead of the props themselves; frustum culling
 * still works patch by patch.
 *
 * The props themselves stay in the scene, hidden, with their names: the review tool turns
 * the batching off when it opens (it picks, moves and hides the props themselves).
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

const CELL = 120;
/** A prop alone of its kind in its patch joins the others like it anywhere on the map, if
 * it's small (no more triangles than this): one draw for all of them. */
const LONE_TRIS = 6000;
/** Props that move (the lily pads bob: villageDecor draws them its own way), and the sky:
 * left as they are. (Anything seen through, or with a shader of its own, is too.) */
const SKIP = /^(Lily_Pad|Lotus)|sky/i;

export interface Batching {
  /** Draw the batches (the props hidden). */
  on(): void;
  /** Draw the props themselves (the batches hidden). */
  off(): void;
  /** How many meshes were merged, into how many batches. */
  readonly merged: number;
  readonly batches: number;
  dispose(): void;
}

function skipped(o: THREE.Object3D, root: THREE.Object3D) {
  for (let p: THREE.Object3D | null = o; p && p !== root; p = p.parent) {
    if (!p.visible || SKIP.test(p.name)) return true;
  }
  return false;
}

export function batchStatic(root: THREE.Object3D): Batching {
  root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const groups = new Map<string, THREE.Mesh[]>();
  const box = new THREE.Box3();
  const c = new THREE.Vector3();
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (
      !m.isMesh ||
      (m as THREE.SkinnedMesh).isSkinnedMesh ||
      (m as THREE.InstancedMesh).isInstancedMesh
    )
      return;
    if (Array.isArray(m.material) || !m.material || !m.material.visible) return;
    const mat = m.material;
    if (mat.transparent || (mat as THREE.ShaderMaterial).isShaderMaterial) return;
    if (m.morphTargetInfluences || skipped(m, root)) return;
    const g = m.geometry as THREE.BufferGeometry;
    if (!g.getAttribute("position")) return;
    box.setFromObject(m).getCenter(c);
    const sig = Object.keys(g.attributes)
      .sort()
      .map((k) => `${k}${g.getAttribute(k).itemSize}`)
      .join(",");
    const key = `${mat.uuid}|${Math.floor(c.x / CELL)},${Math.floor(c.z / CELL)}|${sig}|${g.index ? 1 : 0}`;
    const list = groups.get(key);
    if (list) list.push(m);
    else groups.set(key, [m]);
  });
  // (Lone props, small ones: gathered map-wide by material.)
  for (const [key, list] of [...groups]) {
    if (list.length !== 1) continue;
    const g = list[0]!.geometry as THREE.BufferGeometry;
    const tris = (g.index ? g.index.count : g.getAttribute("position").count) / 3;
    if (tris > LONE_TRIS) continue;
    const parts = key.split("|");
    const wide = `${parts[0]}|*|${parts[2]}|${parts[3]}`;
    groups.delete(key);
    const w = groups.get(wide);
    if (w) w.push(list[0]!);
    else groups.set(wide, [list[0]!]);
  }
  const batches: THREE.Mesh[] = [];
  const hidden: THREE.Mesh[] = [];
  const tmp = new THREE.Matrix4();
  for (const list of groups.values()) {
    if (list.length < 2) continue;
    const parts = list.map((m) => {
      const g = (m.geometry as THREE.BufferGeometry).clone();
      g.morphAttributes = {};
      g.applyMatrix4(tmp.multiplyMatrices(inv, m.matrixWorld));
      return g;
    });
    const merged = mergeGeometries(parts, false);
    for (const p of parts) p.dispose();
    if (!merged) continue;
    merged.computeBoundingSphere();
    const first = list[0]!;
    const b = new THREE.Mesh(merged, first.material);
    b.name = "batch";
    b.castShadow = first.castShadow;
    b.receiveShadow = first.receiveShadow;
    b.matrixAutoUpdate = false;
    b.userData.batch = true;
    root.add(b);
    batches.push(b);
    for (const m of list) hidden.push(m);
  }
  // (Still things: their matrices worked out once, not every frame. The review tool, which
  // moves them, turns this off with the batching.)
  const still: THREE.Object3D[] = [];
  root.traverse((o) => {
    if (o !== root && o.matrixAutoUpdate && !skipped(o, root)) still.push(o);
  });
  const set = (on: boolean) => {
    for (const b of batches) b.visible = on;
    for (const m of hidden) m.visible = !on;
    for (const o of still) o.matrixAutoUpdate = !on;
  };
  set(true);
  return {
    on: () => set(true),
    off: () => set(false),
    merged: hidden.length,
    batches: batches.length,
    dispose() {
      for (const b of batches) {
        b.removeFromParent();
        b.geometry.dispose();
      }
      set(false);
    },
  };
}
