// The still scenery drawn in batches (src/render/batchStatic.ts: Blake, Oct 29, "things
// are very very laggy": thousands of props, a draw call each).
import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { batchStatic } from "../src/render/batchStatic";

function world() {
  const root = new THREE.Group();
  root.name = "track:test";
  const mats = [0, 1, 2].map((k) => new THREE.MeshLambertMaterial({ color: 0x224466 + k }));
  const box = new THREE.BoxGeometry(1, 1, 1);
  const props: THREE.Mesh[] = [];
  for (let i = 0; i < 300; i++) {
    const m = new THREE.Mesh(box, mats[i % 3]);
    m.name = `Prop ${i}`;
    m.position.set((i % 20) * 9 - 90, 0, Math.floor(i / 20) * 9 - 70);
    m.rotation.y = i;
    root.add(m);
    props.push(m);
  }
  const glass = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.5 });
  const seen = [0, 1, 2].map((k) => {
    const m = new THREE.Mesh(box, glass);
    m.position.set(k * 3, 0, 0);
    root.add(m);
    return m;
  });
  const pads = [0, 1, 2].map((k) => {
    const g = new THREE.Group();
    g.name = `Lily_Pad_${k}`;
    g.add(new THREE.Mesh(box, mats[0]));
    g.position.set(k * 4, 0, 5);
    root.add(g);
    return g;
  });
  return { root, props, seen, pads };
}

const drawn = (root: THREE.Object3D) => {
  let n = 0;
  root.traverse((o) => {
    if (!(o as THREE.Mesh).isMesh) return;
    for (let p: THREE.Object3D | null = o; p; p = p.parent) if (!p.visible) return;
    n++;
  });
  return n;
};

describe("batching the still scenery", () => {
  it("draws 300 props of 3 materials as a handful of batches", () => {
    const { root } = world();
    expect(drawn(root)).toBe(306);
    const b = batchStatic(root);
    expect(b.merged).toBe(300 + 0);
    // (3 materials, a few patches of the map each; the 3 see-through ones and the 3 pads
    // as they were.)
    expect(drawn(root)).toBeLessThanOrEqual(3 * 4 + 6);
  });
  it("keeps every prop's triangles, in place", () => {
    const { root } = world();
    const box = new THREE.Box3().setFromObject(root);
    batchStatic(root);
    let tris = 0;
    root.traverse((o) => {
      if (o.userData.batch) tris += ((o as THREE.Mesh).geometry.index?.count ?? 0) / 3;
    });
    expect(tris).toBe(300 * 12);
    const after = new THREE.Box3();
    root.traverse((o) => {
      if (o.userData.batch) after.union(new THREE.Box3().setFromObject(o));
    });
    expect(after.min.distanceTo(box.min)).toBeLessThan(1.5);
  });
  it("leaves see-through things and the bobbing lily pads alone", () => {
    const { root, seen, pads } = world();
    batchStatic(root);
    for (const m of seen) expect(m.visible).toBe(true);
    for (const p of pads) expect(p.children[0]!.visible).toBe(true);
  });
  it("turns off for the review tool: the props themselves, named, drawn again", () => {
    const { root, props } = world();
    const b = batchStatic(root);
    expect(props.every((p) => !p.visible)).toBe(true);
    b.off();
    expect(props.every((p) => p.visible && p.matrixAutoUpdate)).toBe(true);
    expect(drawn(root)).toBe(306);
  });
});
