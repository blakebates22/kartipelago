/**
 * Dragon Isles' life (game/isles.ts says where): the great jade-and-gold dragon, a long
 * serpent whose body follows the path its head has flown; the little dragons; the
 * villagers (one instanced crowd); and the mill wheels.
 *
 * All original low-poly designs built in code; purely visual.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import {
  craneLoad,
  ROLES,
  villagerPose,
  type CraneConfig,
  type Villager,
  type WaterwheelConfig,
} from "../game/isles";

const lam = (
  mats: THREE.Material[],
  color: string | number,
  opts: THREE.MeshLambertMaterialParameters = {},
) => {
  const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
  mats.push(m);
  return m;
};

/** A part for a merged, vertex-coloured mesh: placed, flat-coloured, no UVs. */
function tinted(g: THREE.BufferGeometry, color: string, m: THREE.Matrix4) {
  const n = g.index ? g.toNonIndexed() : g.clone();
  g.dispose();
  n.applyMatrix4(m);
  n.deleteAttribute("uv");
  const c = new THREE.Color(color);
  const count = n.attributes.position!.count;
  const a = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) a.set([c.r, c.g, c.b], i * 3);
  n.setAttribute("color", new THREE.BufferAttribute(a, 3));
  return n;
}

const place = (x: number, y: number, z: number, rx = 0, ry = 0, rz = 0) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
    new THREE.Vector3(1, 1, 1),
  );

// ---------------------------------------------------------------- the dragon

export interface SerpentView {
  /** Fly the head to p (the body follows its trail); `look` turns the head toward a
   * point (0..1 how much); `shadowAt(x, z, y)` is the ground height there. */
  update(
    p: THREE.Vector3,
    t: number,
    look: { at: THREE.Vector3; amount: number },
    shadowAt?: (x: number, z: number, y: number) => number,
  ): void;
  /** Points along the body (head first), for the crowd and the shadow. */
  readonly spine: THREE.Vector3[];
  readonly head: THREE.Vector3;
  dispose(): void;
}

const RING = 8;

/**
 * A serpentine dragon (scale 1: about 120 m long): a jade body, gold belly and gold
 * dorsal crest, four short clawed legs, a long-muzzled head with swept-back antlers,
 * drooping whiskers and a gold mane, a gold tuft at the tail's tip. `simple` drops the
 * legs, mane and whiskers (the little dragons, seen from afar).
 */
export function createSerpentView(
  parent: THREE.Object3D,
  size: number,
  opts: { simple?: boolean; segments?: number; colors?: { body: string; belly: string } } = {},
): SerpentView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const root = new THREE.Group();
  root.name = opts.simple ? "little dragon" : "great dragon";
  parent.add(root);
  const SEG = opts.segments ?? (opts.simple ? 18 : 56);
  const LEN = 120 * size;
  const R = 3.2 * size;
  const jade = new THREE.Color(opts.colors?.body ?? "#34b888");
  const jadeDark = new THREE.Color(opts.colors?.body ?? "#2fa77e").multiplyScalar(0.62);
  const gold = new THREE.Color(opts.colors?.belly ?? "#ffe39a");

  // ---- the body: rings along the trail, rebuilt every frame
  const pos = new Float32Array((SEG + 1) * RING * 3);
  const col = new Float32Array((SEG + 1) * RING * 3);
  const idx: number[] = [];
  for (let k = 0; k < SEG; k++)
    for (let i = 0; i < RING; i++) {
      const a = k * RING + i;
      const b = k * RING + ((i + 1) % RING);
      const c = (k + 1) * RING + ((i + 1) % RING);
      const d = (k + 1) * RING + i;
      idx.push(a, d, b, b, d, c);
    }
  for (let k = 0; k <= SEG; k++)
    for (let i = 0; i < RING; i++) {
      // Ring vertex 0 is on top; the bottom three are the gold belly; scales banded.
      const a = (i / RING) * Math.PI * 2;
      const up = Math.cos(a);
      const c = up < -0.45 ? gold : k % 3 === 0 ? jadeDark : jade;
      col.set([c.r, c.g, c.b], (k * RING + i) * 3);
    }
  const body = new THREE.BufferGeometry();
  body.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  body.setAttribute("color", new THREE.BufferAttribute(col, 3));
  body.setIndex(idx);
  geos.push(body);
  const skin = lam(mats, "#ffffff", { vertexColors: true });
  const bodyMesh = new THREE.Mesh(body, skin);
  bodyMesh.frustumCulled = false;
  root.add(bodyMesh);
  // ---- the crest: a gold fin along the back
  const finPos = new Float32Array(SEG * 3 * 3 * 2);
  const fin = new THREE.BufferGeometry();
  fin.setAttribute("position", new THREE.BufferAttribute(finPos, 3));
  geos.push(fin);
  const goldMat = lam(mats, "#f2c64a", { side: THREE.DoubleSide });
  const finMesh = new THREE.Mesh(fin, goldMat);
  finMesh.frustumCulled = false;
  root.add(finMesh);

  // ---- the head (faces +z), built once: one mesh, coloured per part
  const head = new THREE.Group();
  root.add(head);
  const s = size * (opts.simple ? 1.3 : 1.45);
  const vc = lam(mats, "#ffffff", { vertexColors: true });
  const JADE = opts.colors?.body ?? "#34b888";
  const GOLD = "#f2c64a";
  const IVORY = "#f4ecd2";
  const parts: THREE.BufferGeometry[] = [];
  const add = (
    g: THREE.BufferGeometry,
    color: string,
    x: number,
    y: number,
    z: number,
    rx = 0,
    ry = 0,
    rz = 0,
  ) => parts.push(tinted(g, color, place(x * s, y * s, z * s, rx, ry, rz)));
  add(new THREE.BoxGeometry(5.2 * s, 3.8 * s, 5.4 * s), JADE, 0, 0.6, 0.6);
  add(new THREE.BoxGeometry(3.6 * s, 2.2 * s, 6.0 * s), JADE, 0, 0.5, 5.6);
  add(new THREE.BoxGeometry(3.8 * s, 0.6 * s, 2.2 * s), GOLD, 0, 1.5, 8.2);
  add(new THREE.BoxGeometry(3.2 * s, 1.0 * s, 6.2 * s), GOLD, 0, -1.2, 4.6, 0.18);
  for (const x of [-1.2, -0.4, 0.4, 1.2])
    add(new THREE.ConeGeometry(0.22 * s, 0.9 * s, 4), IVORY, x, -0.3, 8.2, Math.PI);
  for (const side of [-1, 1]) {
    add(new THREE.SphereGeometry(0.75 * s, 8, 6), "#ffe14a", side * 2.1, 1.7, 2.6);
    add(new THREE.SphereGeometry(0.38 * s, 6, 4), "#101010", side * 2.6, 1.8, 2.9);
    // Antlers swept back, a tine forward.
    add(
      new THREE.CylinderGeometry(0.3 * s, 0.55 * s, 6 * s, 5),
      GOLD,
      side * 1.6,
      4.2,
      -1.6,
      -0.9,
      0,
      side * -0.35,
    );
    add(
      new THREE.CylinderGeometry(0.15 * s, 0.3 * s, 2.4 * s, 4),
      GOLD,
      side * 2.3,
      5.0,
      -0.6,
      0.4,
      0,
      side * -0.5,
    );
    if (!opts.simple) {
      // Whiskers drooping from the muzzle, gold brows, the mane.
      add(
        new THREE.CylinderGeometry(0.08 * s, 0.18 * s, 9 * s, 4),
        GOLD,
        side * 3.2,
        -0.6,
        7.0,
        0.5,
        0,
        side * 1.1,
      );
      add(new THREE.BoxGeometry(1.8 * s, 0.6 * s, 2.4 * s), GOLD, side * 1.9, 2.6, 2.4, 0.2);
      for (let k = 0; k < 4; k++)
        add(
          new THREE.ConeGeometry(0.6 * s, 3.4 * s, 4),
          GOLD,
          side * (2.4 + 0.2 * k),
          0.4 - k * 0.8,
          -1.6 - k * 0.9,
          -1.9,
          0,
          side * 0.6,
        );
    }
  }
  const headGeo = mergeGeometries(parts, false)!;
  for (const g of parts) g.dispose();
  geos.push(headGeo);
  head.add(new THREE.Mesh(headGeo, vc));

  // ---- legs: four short clawed legs (one mesh each, one shape per side)
  const legs: { at: number; side: number; mesh: THREE.Object3D }[] = [];
  if (!opts.simple) {
    const legGeo = (side: number) => {
      const ps = [
        tinted(
          new THREE.CylinderGeometry(0.9 * s, 0.7 * s, 4.4 * s, 5),
          JADE,
          place(side * 1.0 * s, -2.0 * s, 0, 0, 0, side * 0.5),
        ),
      ];
      for (const dz of [-0.7, 0, 0.7])
        ps.push(
          tinted(
            new THREE.ConeGeometry(0.28 * s, 1.6 * s, 4),
            IVORY,
            place(side * 2.2 * s, -4.0 * s, dz * s + 0.4 * s, Math.PI * 0.6),
          ),
        );
      const g = mergeGeometries(ps, false)!;
      for (const p of ps) p.dispose();
      geos.push(g);
      return g;
    };
    const shapes = { [-1]: legGeo(-1), [1]: legGeo(1) } as Record<number, THREE.BufferGeometry>;
    for (const at of [0.17, 0.52])
      for (const side of [-1, 1]) {
        const m = new THREE.Mesh(shapes[side]!, vc);
        root.add(m);
        legs.push({ at, side, mesh: m });
      }
  }
  // The tail's tuft.
  const tuftGeo = new THREE.ConeGeometry(1.6 * s, 7 * s, 5);
  tuftGeo.rotateX(Math.PI / 2);
  geos.push(tuftGeo);
  const tuft = new THREE.Mesh(tuftGeo, goldMat);
  tuft.name = "tail tuft";
  root.add(tuft);

  // ---- the trail the body follows
  const trail: THREE.Vector3[] = [];
  const spine: THREE.Vector3[] = Array.from({ length: SEG + 1 }, () => new THREE.Vector3());
  const headPos = new THREE.Vector3();
  const tmp = new THREE.Vector3();
  const side = new THREE.Vector3();
  const upv = new THREE.Vector3();
  const tan = new THREE.Vector3();
  const UP = new THREE.Vector3(0, 1, 0);
  const STEP = Math.max(0.3, LEN / SEG / 2);

  function sample(d: number, out: THREE.Vector3) {
    // Walk back along the trail d metres from the head.
    let acc = 0;
    for (let i = trail.length - 1; i > 0; i--) {
      const a = trail[i]!;
      const b = trail[i - 1]!;
      const l = a.distanceTo(b);
      if (acc + l >= d) return out.copy(a).lerp(b, (d - acc) / Math.max(1e-6, l));
      acc += l;
    }
    return out.copy(trail[0] ?? headPos);
  }

  const lookQ = new THREE.Quaternion();
  const baseQ = new THREE.Quaternion();
  const m4 = new THREE.Matrix4();

  return {
    spine,
    head: headPos,
    update(p, t, look) {
      if (!trail.length) {
        // A straight trail behind the head to begin with.
        for (let i = Math.ceil(LEN / STEP) + 4; i >= 0; i--)
          trail.push(new THREE.Vector3(p.x, p.y, p.z + i * STEP));
      }
      const last = trail[trail.length - 1]!;
      if (last.distanceTo(p) >= STEP) {
        trail.push(p.clone());
        if (trail.length > LEN / STEP + 12) trail.shift();
      }
      headPos.copy(p);
      // ---- the spine (with a ripple running down it)
      for (let k = 0; k <= SEG; k++) {
        const f = k / SEG;
        sample(f * LEN, spine[k]!);
        spine[k]!.y += Math.sin(f * 11 - t * 2.4) * 1.4 * size * Math.min(1, f * 6);
      }
      // ---- rings
      let fp = 0;
      for (let k = 0; k <= SEG; k++) {
        const f = k / SEG;
        const r =
          R * (f < 0.28 ? 0.62 + 0.38 * (f / 0.28) : 1 - 0.88 * Math.pow((f - 0.28) / 0.72, 1.25));
        const a = spine[Math.max(0, k - 1)]!;
        const b = spine[Math.min(SEG, k + 1)]!;
        tan.subVectors(a, b).normalize();
        side.crossVectors(tan, UP);
        if (side.lengthSq() < 1e-6) side.set(1, 0, 0);
        side.normalize();
        upv.crossVectors(side, tan).normalize();
        const c = spine[k]!;
        for (let i = 0; i < RING; i++) {
          const ang = (i / RING) * Math.PI * 2;
          tmp
            .copy(c)
            .addScaledVector(upv, Math.cos(ang) * r)
            .addScaledVector(side, Math.sin(ang) * r * 1.1);
          pos.set([tmp.x, tmp.y, tmp.z], (k * RING + i) * 3);
        }
        if (k < SEG) {
          // A crest fin on top of each segment.
          const top = tmp.copy(c).addScaledVector(upv, r);
          const tip = top
            .clone()
            .addScaledVector(upv, r * 0.9 + 0.5 * size)
            .addScaledVector(tan, -r * 0.5);
          const nxt = spine[k + 1]!;
          const nTop = nxt.clone().addScaledVector(upv, r * 0.95);
          finPos.set([top.x, top.y, top.z, tip.x, tip.y, tip.z, nTop.x, nTop.y, nTop.z], fp);
          fp += 9;
          finPos.set([nTop.x, nTop.y, nTop.z, tip.x, tip.y, tip.z, top.x, top.y, top.z], fp);
          fp += 9;
        }
        if (k === SEG) {
          tuft.position.copy(c);
          tuft.lookAt(tmp.copy(c).sub(tan));
        }
      }
      body.attributes.position!.needsUpdate = true;
      body.computeVertexNormals();
      fin.attributes.position!.needsUpdate = true;
      fin.computeVertexNormals();
      // ---- the head, along its path, turning toward what it looks at
      const nose = spine[0]!;
      const neck = spine[Math.min(SEG, 2)]!;
      head.position.copy(nose);
      // (Matrix4.lookAt(eye, target) aims +z from target to eye: the head's +z leads.)
      m4.lookAt(nose, neck, UP);
      baseQ.setFromRotationMatrix(m4);
      head.quaternion.copy(baseQ);
      if (look.amount > 0) {
        m4.lookAt(look.at, nose, UP);
        lookQ.setFromRotationMatrix(m4);
        head.quaternion.slerp(lookQ, Math.min(0.6, look.amount));
      }
      for (const l of legs) {
        const k = Math.round(l.at * SEG);
        const c = spine[k]!;
        const a = spine[Math.max(0, k - 1)]!;
        const b = spine[Math.min(SEG, k + 1)]!;
        l.mesh.position.copy(c);
        m4.lookAt(a, b, UP);
        l.mesh.quaternion.setFromRotationMatrix(m4);
        l.mesh.rotateX(0.25 * Math.sin(t * 2 + l.at * 9 + l.side));
      }
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- the dragon's shadow

export interface ShadowView {
  update(spine: THREE.Vector3[], groundAt: (x: number, z: number, y: number) => number): void;
  dispose(): void;
}

export function createShadowView(parent: THREE.Object3D, size: number, count = 14): ShadowView {
  const geo = new THREE.CircleGeometry(1, 16).rotateX(-Math.PI / 2);
  const mat = new THREE.MeshBasicMaterial({
    color: 0x0a1a20,
    transparent: true,
    opacity: 0.32,
    depthWrite: false,
  });
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = -2;
  const mesh = new THREE.InstancedMesh(geo, mat, count);
  mesh.frustumCulled = false;
  mesh.renderOrder = 2;
  parent.add(mesh);
  const o = new THREE.Object3D();
  return {
    update(spine, groundAt) {
      for (let k = 0; k < count; k++) {
        const p = spine[Math.round((k / (count - 1)) * 0.8 * (spine.length - 1))]!;
        const g = groundAt(p.x, p.z, p.y);
        const h = p.y - g;
        const fade = Math.max(0, Math.min(1, (160 - h) / 100));
        const r = 3.6 * size * (1 - (k / count) * 0.6) * (0.6 + fade * 0.6) * fade;
        o.position.set(p.x, g + 0.15, p.z);
        o.scale.set(Math.max(0.001, r), 1, Math.max(0.001, r));
        o.updateMatrix();
        mesh.setMatrixAt(k, o.matrix);
      }
      mesh.instanceMatrix.needsUpdate = true;
    },
    dispose() {
      mesh.removeFromParent();
      geo.dispose();
      mat.dispose();
    },
  };
}

// ---------------------------------------------------------------- the villagers

export interface CrowdView {
  /** Pose everyone near the camera. `bowOf(i)` is villager i's awe of the dragon. */
  update(t: number, cam: THREE.Vector3, bowOf: (i: number) => number): void;
  dispose(): void;
}

const ROBES = [
  "#d8342c",
  "#2a9a7a",
  "#3a6ad0",
  "#f0b83a",
  "#f4ecd8",
  "#e86aa0",
  "#e8782a",
  "#2ab0c0",
];
/** The quarry's workers: dusty, faded clothes. */
const DUSTY = ["#8a6a4a", "#9a7a56", "#6e5a48", "#a88a64", "#7a6450"];
const SKINS = ["#f2c8a0", "#e0aa7c", "#c88a5c", "#f6d6b4"];

/**
 * Everyone in one go: instanced skirts, torsos, heads, hats, arms (and the guards'
 * halberds and the fishers' rods). Robes in festival colours; guards in deep red with
 * gold helmets.
 */
export function createCrowdView(parent: THREE.Object3D, people: Villager[]): CrowdView {
  const n = people.length;
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const root = new THREE.Group();
  root.name = "villagers";
  parent.add(root);
  const inst = (g: THREE.BufferGeometry, count: number, color = "#ffffff") => {
    geos.push(g);
    const m = new THREE.InstancedMesh(g, lam(mats, color), Math.max(1, count));
    m.frustumCulled = false;
    m.count = count;
    root.add(m);
    return m;
  };
  const skirtGeo = new THREE.CylinderGeometry(0.3, 0.46, 0.75, 6).translate(0, 0.375, 0);
  const torsoGeo = new THREE.CylinderGeometry(0.24, 0.3, 0.6, 6).translate(0, 0.3, 0);
  const headGeo = new THREE.IcosahedronGeometry(0.22, 0).translate(0, 0.86, 0);
  const strawGeo = new THREE.ConeGeometry(0.5, 0.28, 8).translate(0, 1.16, 0);
  const capGeo = new THREE.CylinderGeometry(0.16, 0.22, 0.32, 6).translate(0, 1.12, 0);
  const armGeo = new THREE.BoxGeometry(0.13, 0.55, 0.13).translate(0, -0.27, 0);
  const poleGeo = new THREE.CylinderGeometry(0.035, 0.035, 2.8, 4).translate(0, 1.0, 0);
  const guards = people.filter((p) => p.role === "guard").length;
  const fishers = people.filter((p) => p.role === "fisher").length;
  const skirts = inst(skirtGeo, n);
  const torsos = inst(torsoGeo, n);
  const heads = inst(headGeo, n);
  const straws = inst(strawGeo, n, "#e8cf86");
  const caps = inst(capGeo, n);
  const armsL = inst(armGeo, n);
  const armsR = inst(armGeo, n);
  const poles = inst(poleGeo, guards + fishers, "#6a4a2a");
  const color = new THREE.Color();
  const hatOf: ("straw" | "cap" | "none")[] = [];
  people.forEach((p, i) => {
    const guard = p.role === "guard";
    const labour = p.role === "worker" || p.role === "hauler";
    const robe = guard
      ? "#8a1c1c"
      : labour
        ? DUSTY[(p.variant + i) % DUSTY.length]!
        : ROBES[(p.variant + i) % ROBES.length]!;
    color.set(robe);
    skirts.setColorAt(i, color);
    torsos.setColorAt(i, guard ? color.set("#b02a22") : color);
    armsL.setColorAt(i, color);
    armsR.setColorAt(i, color);
    heads.setColorAt(i, color.set(SKINS[(p.variant * 3 + i) % SKINS.length]!));
    const hat = guard
      ? "cap"
      : labour || p.role === "fisher" || p.role === "gardener" || p.variant % 4 === 1
        ? "straw"
        : p.variant % 4 === 2
          ? "cap"
          : "none";
    hatOf.push(hat);
    caps.setColorAt(i, color.set(guard ? "#e8b830" : p.variant % 2 ? "#222222" : "#3a2a6a"));
    straws.setColorAt(i, color.set("#e8cf86"));
  });
  for (const m of [skirts, torsos, heads, caps, straws, armsL, armsR])
    if (m.instanceColor) m.instanceColor.needsUpdate = true;

  const base = new THREE.Matrix4();
  const torso = new THREE.Matrix4();
  const m = new THREE.Matrix4();
  const r = new THREE.Matrix4();
  const hidden = new THREE.Matrix4().makeScale(0, 0, 0);
  const NEAR = 320;
  let first = true;

  return {
    update(t, cam, bowOf) {
      let pi = 0;
      for (let i = 0; i < n; i++) {
        const p = people[i]!;
        const far = Math.hypot(p.x - cam.x, p.z - cam.z) > NEAR;
        if (far && !first) {
          if (p.role === "guard" || p.role === "fisher") pi++;
          continue;
        }
        const pose = villagerPose(p, i, t, far ? 0 : bowOf(i));
        const yaw = Math.atan2(p.fx, p.fz) + pose.turn;
        base
          .makeRotationY(yaw)
          .setPosition(p.x + p.fx * pose.step, p.y + pose.hop, p.z + p.fz * pose.step);
        skirts.setMatrixAt(i, base);
        torso
          .copy(base)
          .multiply(m.makeTranslation(0, 0.7, 0))
          .multiply(r.makeRotationX(pose.lean));
        torsos.setMatrixAt(i, torso);
        heads.setMatrixAt(i, torso);
        const hat = hatOf[i];
        straws.setMatrixAt(i, hat === "straw" ? torso : hidden);
        caps.setMatrixAt(i, hat === "cap" ? torso : hidden);
        for (const [arm, sd, raise] of [
          [armsL, 1, pose.armL],
          [armsR, -1, pose.armR],
        ] as const) {
          m.copy(torso)
            .multiply(r.makeTranslation(sd * 0.33, 0.55, 0))
            .multiply(r.makeRotationZ(sd * (0.2 + 0.25 * raise)))
            .multiply(r.makeRotationX(-raise * Math.PI * 0.92));
          arm.setMatrixAt(i, m);
        }
        if (p.role === "guard") {
          m.copy(base).multiply(r.makeTranslation(-0.48, 0.0, 0.18));
          poles.setMatrixAt(pi++, m);
        } else if (p.role === "fisher") {
          m.copy(torso)
            .multiply(r.makeTranslation(-0.35, 0.3, 0.3))
            .multiply(r.makeRotationX(1.0 + 0.05 * Math.sin(t * 1.3 + i)));
          poles.setMatrixAt(pi++, m);
        }
      }
      first = false;
      for (const mm of [skirts, torsos, heads, straws, caps, armsL, armsR, poles])
        mm.instanceMatrix.needsUpdate = true;
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const mm of mats) mm.dispose();
    },
  };
}

void ROLES;

// ---------------------------------------------------------------- the mill wheel

export interface WheelView {
  update(t: number): void;
  dispose(): void;
}

/** A wooden mill wheel: two rims, spokes and paddles, turning about its axle. */
export function createWaterwheelView(parent: THREE.Object3D, c: WaterwheelConfig): WheelView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const pivot = new THREE.Group();
  pivot.position.set(c.x, c.y, c.z);
  pivot.rotation.y = c.heading;
  parent.add(pivot);
  const r = c.radius;
  const WOOD = "#7a5434";
  const DARK = "#4a3020";
  const ps: THREE.BufferGeometry[] = [];
  for (const z of [-0.7, 0.7])
    ps.push(tinted(new THREE.TorusGeometry(r, 0.14, 4, 16), WOOD, place(0, 0, z)));
  for (let k = 0; k < 4; k++)
    for (const z of [-0.7, 0.7])
      ps.push(
        tinted(
          new THREE.BoxGeometry(0.16, r * 2, 0.16),
          DARK,
          place(0, 0, z, 0, 0, (k * Math.PI) / 4),
        ),
      );
  for (let k = 0; k < 12; k++) {
    const a = (k / 12) * Math.PI * 2;
    ps.push(
      tinted(
        new THREE.BoxGeometry(0.12, 0.9, 1.7),
        WOOD,
        place(Math.cos(a) * r, Math.sin(a) * r, 0, 0, 0, a),
      ),
    );
  }
  ps.push(tinted(new THREE.CylinderGeometry(0.2, 0.2, 2.4, 6), DARK, place(0, 0, 0, Math.PI / 2)));
  const wg = mergeGeometries(ps, false)!;
  for (const p of ps) p.dispose();
  geos.push(wg);
  const wheel = new THREE.Mesh(wg, lam(mats, "#ffffff", { vertexColors: true }));
  pivot.add(wheel);
  return {
    update(t) {
      wheel.rotation.z = -t * c.speed;
    },
    dispose() {
      pivot.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- the quarry cranes

export interface CraneView {
  update(t: number): void;
  dispose(): void;
}

/** A crane's rope and the sandstone block it raises and lowers, swaying a little. */
export function createCraneView(parent: THREE.Object3D, c: CraneConfig): CraneView {
  const mats: THREE.Material[] = [];
  const ropeGeo = new THREE.CylinderGeometry(0.05, 0.05, 1, 4).translate(0, -0.5, 0);
  const blockGeo = new THREE.BoxGeometry(1.8, 1.4, 1.8);
  const rope = new THREE.Mesh(ropeGeo, lam(mats, "#4a3420"));
  const block = new THREE.Mesh(blockGeo, lam(mats, "#e4ae82"));
  parent.add(rope, block);
  return {
    update(t) {
      const l = craneLoad(c, t);
      rope.position.set(l.tip.x, l.tip.y, l.tip.z);
      rope.scale.set(1, l.rope, 1);
      // (Tilted toward the swaying block.)
      rope.rotation.set(
        -Math.atan2(l.block.z - l.tip.z, l.rope),
        0,
        Math.atan2(l.block.x - l.tip.x, l.rope),
      );
      block.position.set(l.block.x, l.block.y, l.block.z);
      block.rotation.y = c.heading + 0.2 * Math.sin(t * 0.4);
    },
    dispose() {
      rope.removeFromParent();
      block.removeFromParent();
      ropeGeo.dispose();
      blockGeo.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
