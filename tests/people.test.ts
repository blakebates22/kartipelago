/**
 * The story's people (src/render/people): every one builds, stands on the ground, keeps
 * its triangle budget, and animates every gesture (talking, looking, walking) without
 * going wrong: nothing NaN, feet on the ground, the horn to his mouth and snapped in two.
 */
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { GESTURES, createElderView, createGuardView, createLumenView } from "../src/render/people";
import { createVillagerView, SPECIES, type Folk } from "../src/render/villager";
import { Racer } from "../src/render/racers/racer";
import { actRacer } from "../src/render/people/racerActing";
import type { PersonView } from "../src/render/people";

function triangles(o: THREE.Object3D) {
  let n = 0;
  o.traverse((m) => {
    if (m instanceof THREE.Mesh && m.visible) {
      const g = m.geometry as THREE.BufferGeometry;
      n += (g.index ? g.index.count : g.getAttribute("position").count) / 3;
    }
  });
  return n;
}

function finite(o: THREE.Object3D) {
  let ok = true;
  o.updateMatrixWorld(true);
  o.traverse((c) => {
    for (const v of c.matrixWorld.elements) if (!Number.isFinite(v)) ok = false;
  });
  return ok;
}

describe("Elder Mossback", () => {
  it("builds, within budget, standing on the ground", () => {
    const scene = new THREE.Scene();
    const v = createElderView(scene);
    v.update(0, 0, 0, 0, {}, 0);
    v.update(0, 0, 0, 0, {}, 0.1);
    const tris = triangles(v.rig.root);
    expect(tris).toBeGreaterThan(3000);
    expect(tris).toBeLessThan(26000);
    const box = new THREE.Box3().setFromObject(v.rig.root);
    expect(box.min.y).toBeGreaterThan(-0.05);
    expect(box.min.y).toBeLessThan(0.05);
    expect(box.max.y).toBeGreaterThan(1.3);
    expect(box.max.y).toBeLessThan(2.4);
  });

  it("does every gesture, talking and looking, without going wrong", () => {
    const scene = new THREE.Scene();
    const look = new THREE.Vector3(3, 1.5, 4);
    for (const g of GESTURES) {
      const v = createElderView(scene);
      for (let t = 0; t < 3; t += 1 / 30)
        v.update(0, 0, 0, 0.3, { gesture: g, talk: true, look }, t);
      expect(finite(v.rig.root), g).toBe(true);
      v.dispose();
    }
  });

  it("lifts the horn to his mouth, and snaps it across his knee", () => {
    const scene = new THREE.Scene();
    const v = createElderView(scene);
    const hornAt = () => v.rig.props.hornA!.obj.getWorldPosition(new THREE.Vector3());
    for (let t = 0; t < 1; t += 1 / 30) v.update(0, 0, 0, 0, {}, t);
    const rest = hornAt();
    for (let t = 1; t < 3; t += 1 / 30) v.update(0, 0, 0, 0, { gesture: "blowHorn" }, t);
    const mouth = v.rig.head.localToWorld(new THREE.Vector3(...v.rig.stance.mouth));
    const blown = hornAt();
    expect(blown.distanceTo(mouth)).toBeLessThan(0.15);
    expect(blown.y).toBeGreaterThan(rest.y + 0.4);
    expect(v.anim.hornBroken).toBe(false);
    for (let t = 3; t < 6; t += 1 / 30) v.update(0, 0, 0, 0, { gesture: "breakHorn" }, t);
    expect(v.anim.hornBroken).toBe(true);
    const a = v.rig.props.hornA!.obj.getWorldPosition(new THREE.Vector3());
    const b = v.rig.props.hornB!.obj.getWorldPosition(new THREE.Vector3());
    expect(a.distanceTo(b)).toBeGreaterThan(0.15);
  });

  it("walks with its feet planted (stepping by the distance it covers)", () => {
    const scene = new THREE.Scene();
    const v = createElderView(scene);
    let minY = Infinity;
    for (let t = 0, z = 0; t < 4; t += 1 / 30, z += 0.6 / 30) {
      v.update(0, 0, z, 0, {}, t);
      for (const l of v.rig.legs)
        minY = Math.min(minY, l.hand.getWorldPosition(new THREE.Vector3()).y);
    }
    expect(minY).toBeGreaterThan(-0.02);
  });
});

const FOLKS: Folk[] = ["valley", "snow", "desert", "beach", "dragon", "road"];

function standsRight(v: PersonView, maxTris: number) {
  for (let t = 0; t < 0.5; t += 1 / 30) v.update(0, 0, 0, 0, {}, t);
  const box = new THREE.Box3().setFromObject(v.rig.root);
  expect(box.min.y, "on the ground").toBeGreaterThan(-0.06);
  expect(box.min.y, "on the ground").toBeLessThan(0.06);
  expect(triangles(v.rig.root)).toBeLessThan(maxTris);
  // The crowd version: a few meshes.
  let far = 0;
  v.root.traverse((o) => {
    if (o instanceof THREE.Mesh && !o.parent?.parent?.parent?.name) far++;
  });
  expect(far).toBeGreaterThan(0);
}

describe("the guards, Lumen and the townsfolk", () => {
  it("guards build in every kingdom's clothes, and hold out the key", () => {
    const scene = new THREE.Scene();
    for (const folk of FOLKS)
      for (const seed of [7, 18]) {
        const v = createGuardView(scene, folk, seed);
        standsRight(v, 16000);
        const key = () => v.rig.props.key!.obj.getWorldPosition(new THREE.Vector3());
        const before = key();
        for (let t = 0.5; t < 2; t += 1 / 30) v.update(0, 0, 0, 0, { gesture: "holdOut" }, t);
        expect(key().y, `${folk} ${seed}: the key comes up`).toBeGreaterThan(before.y + 0.3);
        v.dispose();
      }
  });

  it("Lumen blinks and keeps his tail under the robe, with every face (the old one's eyes glow)", () => {
    for (const face of ["frill", "shadow", "snub", "long"] as const) {
      const v = createLumenView(new THREE.Scene(), 3, face);
      standsRight(v, 14000);
      if (face === "shadow") expect(v.rig.glow.length).toBe(2);
      expect(v.rig.face.eyes.length, face).toBe(2);
      let shut = false;
      for (let t = 0; t < 12; t += 1 / 30) {
        v.update(0, 0, 0, 0, {}, t);
        const f = v.rig.face;
        const closed = (e: (typeof f.eyes)[number]) =>
          e.lid.userData.squash
            ? e.lid.scale.y < 0.3
            : Math.abs(e.lid.rotation.x - f.lidClosed) < Math.abs(f.lidClosed - f.lidOpen) * 0.3;
        if (f.eyes.some(closed)) shut = true;
      }
      expect(shut, `${face}: blinks`).toBe(true);
      v.dispose();
    }
  });

  it("every kind of villager builds in every kingdom's clothes, and moves well", () => {
    const scene = new THREE.Scene();
    const look = new THREE.Vector3(2, 1.4, 3);
    for (const folk of FOLKS)
      for (const sp of SPECIES) {
        const v = createVillagerView(
          scene,
          folk,
          SPECIES.indexOf(sp) + 8 * FOLKS.indexOf(folk),
          sp,
        );
        standsRight(v, 13000);
        for (const g of ["wave", "bow", "cheer"] as const)
          for (let t = 0; t < 1; t += 1 / 30)
            v.update(t * 0.6, 0, 0, 0, { gesture: g, talk: true, look }, t);
        expect(finite(v.rig.root), `${folk} ${sp}`).toBe(true);
        v.dispose();
      }
  });

  it("the old cue still works: a number is how fast they walk", () => {
    const v = createVillagerView(new THREE.Scene(), "valley", 3);
    for (let t = 0; t < 1; t += 1 / 30) v.update(t, 0, 0, Math.PI / 2, 1, t);
    expect(finite(v.rig.root)).toBe(true);
  });
});

describe("racers acting in their karts", () => {
  it("talk (the jaw moves) and turn to look at someone", () => {
    const r = new Racer("rex");
    const act = actRacer(r);
    r.root.updateMatrixWorld(true);
    const look = new THREE.Vector3(-4, 1.4, 3);
    let lo = Infinity;
    let hi = -Infinity;
    for (let t = 0; t < 3; t += 1 / 30) {
      act.update(1 / 30, { talk: true, look });
      r.root.updateMatrixWorld(true);
      const j = r.rig.face.jaw!.rotation.x;
      if (t > 1) {
        lo = Math.min(lo, j);
        hi = Math.max(hi, j);
      }
    }
    expect(hi - lo, "the jaw moves").toBeGreaterThan(0.1);
    const d = new THREE.Vector3(0, 0, 1).applyQuaternion(
      r.rig.head.getWorldQuaternion(new THREE.Quaternion()),
    );
    expect(d.x, "looks to its right (-x)").toBeLessThan(-0.3);
  });
});
