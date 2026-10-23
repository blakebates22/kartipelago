/**
 * Baked nudges: public/tracks/<id>/edits.json (optional). Props moved, turned, resized,
 * copied or deleted in the review tool (src/review/), once Claude has checked them, are
 * listed here and applied when the track loads, to what you see (visual.glb) and to what
 * you hit (collision.glb) alike, by the prop's name.
 *
 *   {
 *     "schemaVersion": 1,
 *     "edits": [
 *       { "op": "move", "node": "Bush_1026", "to": { "pos": [..], "quat": [..], "scale": [..] } },
 *       { "op": "copy", "node": "Palm_12 copy 1", "copyOf": "Palm_12", "to": { ... } },
 *       { "op": "delete", "node": "Rock_7" }
 *     ]
 *   }
 *
 * Transforms are in the game's world (three.js, Y up), which is the glTF scene's own
 * frame: props are the scene's direct children. A prop missing from one of the two files
 * (a bush has no collision) is skipped there.
 *
 * Note: a Blender re-export can rename generated props; check edits.json after one.
 */
import * as THREE from "three";

export interface BakedTransform {
  pos: [number, number, number];
  quat: [number, number, number, number];
  scale: [number, number, number];
}
export interface BakedEdit {
  op: "move" | "copy" | "delete";
  node: string;
  copyOf?: string;
  to?: BakedTransform;
}

const isNum3 = (v: unknown): v is [number, number, number] =>
  Array.isArray(v) && v.length === 3 && v.every((x) => Number.isFinite(x));
const isNum4 = (v: unknown): v is [number, number, number, number] =>
  Array.isArray(v) && v.length === 4 && v.every((x) => Number.isFinite(x));

/** Check edits.json; bad entries are skipped with a warning. */
export function parseEdits(json: unknown, warnings: string[] = []): BakedEdit[] {
  const list = (json as { edits?: unknown })?.edits;
  if (!Array.isArray(list)) {
    warnings.push("edits.json: no edits list");
    return [];
  }
  const out: BakedEdit[] = [];
  for (const e of list as Record<string, unknown>[]) {
    const op = e?.op;
    const node = e?.node;
    if ((op !== "move" && op !== "copy" && op !== "delete") || typeof node !== "string") {
      warnings.push(`edits.json: skipped a bad edit (${JSON.stringify(e).slice(0, 60)})`);
      continue;
    }
    const t = e.to as Record<string, unknown> | undefined;
    const to =
      t && isNum3(t.pos) && isNum4(t.quat) && isNum3(t.scale)
        ? { pos: t.pos, quat: t.quat, scale: t.scale }
        : undefined;
    if (op !== "delete" && !to) {
      warnings.push(`edits.json: ${node} has no "to" transform`);
      continue;
    }
    if (op === "copy" && typeof e.copyOf !== "string") {
      warnings.push(`edits.json: copy ${node} doesn't say what it copies`);
      continue;
    }
    out.push({
      op,
      node,
      ...(op === "copy" ? { copyOf: e.copyOf as string } : {}),
      ...(to ? { to } : {}),
    });
  }
  return out;
}

/** Apply edits to a loaded glTF scene (its direct children are the props). */
export function applyEdits(scene: THREE.Object3D, edits: BakedEdit[]) {
  const byName = new Map<string, THREE.Object3D>();
  for (const c of scene.children) if (c.name) byName.set(c.name, c);
  const place = (o: THREE.Object3D, t: BakedTransform) => {
    o.position.set(...t.pos);
    o.quaternion.set(...t.quat);
    o.scale.set(...t.scale);
    o.updateMatrixWorld(true);
  };
  for (const e of edits) {
    if (e.op === "copy") {
      const src = byName.get(e.copyOf!);
      if (!src || byName.has(e.node)) continue;
      const c = src.clone();
      c.name = e.node;
      scene.add(c);
      byName.set(e.node, c);
      place(c, e.to!);
      continue;
    }
    const o = byName.get(e.node);
    if (!o) continue;
    if (e.op === "delete") o.removeFromParent();
    else place(o, e.to!);
  }
}
