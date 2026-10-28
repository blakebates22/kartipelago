/**
 * A person on screen: the full rig near the camera (animated: looks, talks, gestures,
 * steps), and far away (or in a crowd) a baked version of the same person in a few
 * meshes whose legs swing from the hips. Built once per look and shared: each view is a
 * clone of the template, so a village full of folk costs little.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { lowDetail } from "../racers/kit/shapes";
import { shadowTexture } from "../racers/kit/paint";
import { PersonAnimator, type PersonCue } from "./animate";
import type { LegRig, PersonRig } from "./rig";

export type { PersonCue };

export interface PersonView {
  readonly root: THREE.Group;
  /**
   * Place it, facing `heading` (0 = +z), and animate (`t` seconds). The cue says what
   * they're doing; a number is how fast they're walking (0..1, the villages' old cue).
   */
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    cue: PersonCue | number,
    t: number,
  ): void;
  /** Their animator (the full rig), for poking at in previews and tests. */
  readonly anim: PersonAnimator;
  readonly rig: PersonRig;
  /** Where their face is (between the eyes, world), for the camera and others to look at. */
  headPosition(out: THREE.Vector3): THREE.Vector3;
  dispose(): void;
}

/** Between the eyes (or the head's pivot, without eyes), world space. */
export function facePoint(
  rig: { head: THREE.Object3D; face: { eyes: { group: THREE.Object3D }[] } },
  out: THREE.Vector3,
) {
  const eyes = rig.face.eyes;
  if (!eyes.length) return rig.head.getWorldPosition(out);
  out.set(0, 0, 0);
  const p = new THREE.Vector3();
  for (const e of eyes) out.add(e.group.getWorldPosition(p));
  return out.multiplyScalar(1 / eyes.length);
}

/** Map every object in a template to its clone, walking the two trees together. */
function cloneRig(t: PersonRig): PersonRig {
  const root = t.root.clone(true);
  const map = new Map<THREE.Object3D, THREE.Object3D>();
  const walk = (a: THREE.Object3D, b: THREE.Object3D) => {
    map.set(a, b);
    a.children.forEach((c, i) => walk(c, b.children[i]!));
  };
  walk(t.root, root);
  const m = <T extends THREE.Object3D>(o: T) => map.get(o) as T;
  return {
    ...t,
    root: root as THREE.Group,
    body: m(t.body),
    hips: m(t.hips),
    torso: m(t.torso),
    neck: m(t.neck),
    head: m(t.head),
    face: {
      ...t.face,
      eyes: t.face.eyes.map((e) => ({ ...e, group: m(e.group), lid: m(e.lid), look: m(e.look) })),
      brows: t.face.brows.map(m),
      jaw: t.face.jaw ? m(t.face.jaw) : null,
    },
    arms: t.arms.map((a) => ({ ...a, upper: m(a.upper), fore: m(a.fore), hand: m(a.hand) })),
    legs: t.legs.map((l): LegRig => ({
      ...l,
      upper: m(l.upper),
      fore: m(l.fore),
      hand: m(l.hand),
    })),
    tail: t.tail.map(m),
    hands: m(t.hands),
    feet: m(t.feet),
    props: Object.fromEntries(
      Object.entries(t.props).map(([k, p]) => [k, { ...p, obj: m(p.obj) }]),
    ),
    wiggles: t.wiggles.map((w) => ({ ...w, obj: m(w.obj) })),
    glow: t.glow.map(m),
  };
}

/** The crowd version: the body in one or two meshes, each leg its own, swinging from the hip. */
interface Baked {
  body: { geo: THREE.BufferGeometry; mat: THREE.Material }[];
  legs: {
    hip: THREE.Vector3;
    parts: { geo: THREE.BufferGeometry; mat: THREE.Material }[];
    phase: number;
  }[];
  /** Hip height (the legs' pivots), for the bob. */
  height: number;
}

function bake(rig: PersonRig): Baked {
  // Stand it at rest (arms hanging, feet under the hips, eyes open).
  const anim = new PersonAnimator(rig, 1);
  rig.root.updateMatrixWorld(true);
  for (let i = 0; i < 3; i++) anim.step(1 / 30, {}, 0);
  for (const e of rig.face.eyes) e.lid.rotation.x = rig.face.lidOpen;
  rig.root.updateMatrixWorld(true);
  const inv = rig.root.matrixWorld.clone().invert();
  const owner = new Map<THREE.Object3D, number>();
  rig.legs.forEach((l, i) => {
    owner.set(l.upper, i);
    owner.set(l.fore, i);
    owner.set(l.hand, i);
  });
  const legOf = (o: THREE.Object3D): number => {
    for (let p: THREE.Object3D | null = o; p; p = p.parent) {
      const k = owner.get(p);
      if (k !== undefined) return k;
    }
    return -1;
  };
  const buckets = new Map<number, Map<THREE.Material, THREE.BufferGeometry[]>>();
  rig.root.traverse((o) => {
    if (!(o instanceof THREE.Mesh) || !o.visible) return;
    let vis = true;
    for (let p: THREE.Object3D | null = o; p; p = p.parent) if (!p.visible) vis = false;
    if (!vis) return;
    const k = legOf(o);
    const g = (o.geometry as THREE.BufferGeometry).index
      ? (o.geometry as THREE.BufferGeometry).toNonIndexed()
      : (o.geometry as THREE.BufferGeometry).clone();
    const mx = inv.clone().multiply(o.matrixWorld);
    if (k >= 0) {
      const hip = rig.root.worldToLocal(
        (rig.legs[k]!.front ? rig.torso : rig.hips).localToWorld(rig.legs[k]!.shoulder.clone()),
      );
      mx.premultiply(new THREE.Matrix4().makeTranslation(-hip.x, -hip.y, -hip.z));
    }
    g.applyMatrix4(mx);
    if (mx.determinant() < 0) {
      // (A mirrored part: keep its faces outward.)
      const idx = g.getAttribute("position").count;
      for (const name of Object.keys(g.attributes)) {
        const a = g.getAttribute(name) as THREE.BufferAttribute;
        const n = a.itemSize;
        for (let i = 0; i < idx; i += 3)
          for (let c = 0; c < n; c++) {
            const tmp = a.array[(i + 1) * n + c]!;
            a.array[(i + 1) * n + c] = a.array[(i + 2) * n + c]!;
            a.array[(i + 2) * n + c] = tmp;
          }
      }
    }
    for (const name of Object.keys(g.attributes))
      if (!["position", "normal", "uv", "color"].includes(name)) g.deleteAttribute(name);
    if (!g.getAttribute("uv"))
      g.setAttribute(
        "uv",
        new THREE.Float32BufferAttribute(new Float32Array(g.getAttribute("position").count * 2), 2),
      );
    if (!g.getAttribute("color")) {
      const n = g.getAttribute("position").count;
      g.setAttribute("color", new THREE.Float32BufferAttribute(new Float32Array(n * 3).fill(1), 3));
    }
    const mat = o.material as THREE.Material;
    let b = buckets.get(k);
    if (!b) buckets.set(k, (b = new Map()));
    let list = b.get(mat);
    if (!list) b.set(mat, (list = []));
    list.push(g);
  });
  const merge = (m: Map<THREE.Material, THREE.BufferGeometry[]> | undefined) =>
    [...(m ?? new Map<THREE.Material, THREE.BufferGeometry[]>()).entries()].map(([mat, gs]) => {
      const geo = mergeGeometries(gs, false)!;
      for (const g of gs) g.dispose();
      geo.computeBoundingSphere();
      return { geo, mat };
    });
  return {
    body: merge(buckets.get(-1)),
    legs: rig.legs.map((l, i) => ({
      hip: rig.root.worldToLocal((l.front ? rig.torso : rig.hips).localToWorld(l.shoulder.clone())),
      parts: merge(buckets.get(i)),
      phase: l.phase,
    })),
    height: rig.stance.hipY,
  };
}

interface Template {
  rig: PersonRig;
  low: Baked;
}
const templates = new Map<string, Template>();

/** Build (once per look) and clone a person. */
function template(key: string, build: () => PersonRig): Template {
  let t = templates.get(key);
  if (!t) {
    const rig = build();
    const low = bake(lowDetail(build));
    t = { rig, low };
    templates.set(key, t);
  }
  return t;
}

/** Distance (m) beyond which the crowd version is drawn. */
export const PERSON_LOD = 22;

const SHADOW_MAT = () =>
  new THREE.MeshBasicMaterial({
    map: shadowTexture(),
    transparent: true,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -4,
  });

/**
 * A person in the world. `key` names the look (built once); `scale` sizes them; `shadow`
 * is the blob shadow's radius (m, before scale).
 */
export function createPersonView(
  parent: THREE.Object3D,
  key: string,
  build: () => PersonRig,
  opts: { scale?: number; shadow?: number; seed?: number; lod?: number } = {},
): PersonView {
  const tpl = template(key, build);
  const rig = cloneRig(tpl.rig);
  const anim = new PersonAnimator(rig, opts.seed ?? 1);
  const root = new THREE.Group();
  root.name = rig.root.name;
  const scale = opts.scale ?? 1;
  const lod = new THREE.LOD();
  lod.scale.setScalar(scale);
  lod.addLevel(rig.root, 0);
  const far = new THREE.Group();
  const lowBody = new THREE.Group();
  for (const p of tpl.low.body) lowBody.add(new THREE.Mesh(p.geo, p.mat));
  far.add(lowBody);
  const lowLegs = tpl.low.legs.map((l) => {
    const pivot = new THREE.Group();
    pivot.position.copy(l.hip);
    for (const p of l.parts) pivot.add(new THREE.Mesh(p.geo, p.mat));
    far.add(pivot);
    return { pivot, phase: l.phase, y: l.hip.y };
  });
  lod.addLevel(far, opts.lod ?? PERSON_LOD);
  root.add(lod);
  const shadowMat = SHADOW_MAT();
  const r = (opts.shadow ?? 0.55) * scale;
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry(r * 2.4, r * 2.4).rotateX(-Math.PI / 2),
    shadowMat,
  );
  shadow.position.y = 0.03;
  shadow.renderOrder = 1;
  root.add(shadow);
  parent.add(root);

  let last: { x: number; z: number; t: number } | null = null;
  let phase = 0;
  let walkW = 0;
  const stride = rig.stance.stride;
  return {
    root,
    anim,
    rig,
    update(x, y, z, heading, cue, t) {
      const moved = last ? Math.hypot(x - last.x, z - last.z) : 0;
      const dt = last ? Math.max(0, Math.min(0.1, t - last.t)) : 0;
      // (A jump, not a walk: someone placed afresh.)
      const step = moved > 3 ? 0 : moved;
      last = { x, z, t };
      root.position.set(x, y, z);
      root.rotation.y = heading;
      const c: PersonCue = typeof cue === "number" ? {} : cue;
      if (lod.getCurrentLevel() === 0) {
        root.updateMatrixWorld(true);
        anim.step(dt, c, step);
      } else {
        // The crowd version: legs swinging by the distance walked, a bob.
        phase = (phase + step / scale / (2 * stride)) % 1;
        const sp = dt > 0 ? step / dt : 0;
        walkW += ((sp > 0.15 ? 1 : 0) - walkW) * Math.min(1, dt * 6);
        lowLegs.forEach((l) => {
          l.pivot.rotation.x = Math.sin((phase + l.phase) * Math.PI * 2) * 0.5 * walkW;
        });
        lowBody.position.y = Math.abs(Math.cos(phase * Math.PI * 2)) * 0.03 * walkW;
      }
    },
    headPosition(out) {
      return facePoint(rig, out);
    },
    dispose() {
      parent.remove(root);
      shadow.geometry.dispose();
      shadowMat.dispose();
    },
  };
}
