/**
 * A winged dragon in flight (Blake, Nov 6, review journey_cause 2 note 1: "the dragons are
 * still the chinese dragons these need to be reworked completely"): the Dragon Kingdom's
 * kind, not a serpent. A deep chest and a long neck, a horned head with a frill of spines
 * and glowing eyes, four legs tucked up under it, a long tail ending in a spade, and great
 * bat wings that beat and then glide. It flies where it's sent (the head's point, as the
 * serpent did: render/islesFx.ts' SerpentView), facing the way it goes, banking into its
 * turns; its spine (for the shadow and the crowd) trails along its path.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import type { SerpentView } from "./islesFx";

export interface WyvernColors {
  body: string;
  belly: string;
  wing?: string;
}

const M = (x: number, y: number, z: number, sx = 1, sy = 1, sz = 1, rx = 0, ry = 0, rz = 0) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
    new THREE.Vector3(sx, sy, sz),
  );

function piece(g: THREE.BufferGeometry, m: THREE.Matrix4, top: string, under?: string) {
  if (!g.attributes.normal) g.computeVertexNormals();
  g.applyMatrix4(m);
  const geo = g.index ? g.toNonIndexed() : g;
  const nor = geo.attributes.normal!;
  const col = new Float32Array(nor.count * 3);
  const a = new THREE.Color(top);
  const b = new THREE.Color(under ?? top);
  const c = new THREE.Color();
  for (let i = 0; i < nor.count; i++) {
    const ny = nor.getY(i);
    c.copy(a).lerp(b, Math.max(0, Math.min(1, -ny * 1.4 + 0.2)));
    c.multiplyScalar(0.85 + 0.2 * Math.max(0, ny));
    col.set([c.r, c.g, c.b], i * 3);
  }
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  geo.deleteAttribute("uv");
  return geo;
}

/** A tapered limb along +z from 0 to len. */
const limb = (r0: number, r1: number, len: number, seg = 10) =>
  new THREE.CylinderGeometry(r1, r0, len, seg, 1).rotateX(Math.PI / 2).translate(0, 0, len / 2);

/** A wing (the right one: +x): its arm and fingers, the membrane between them. */
function wingGeometry(color: string, bone: string) {
  const parts: THREE.BufferGeometry[] = [];
  const elbow = new THREE.Vector3(0.3, 0.06, 0.06);
  const wrist = new THREE.Vector3(0.52, 0.04, 0.0);
  const tips = [
    new THREE.Vector3(0.82, 0.0, -0.08),
    new THREE.Vector3(0.7, -0.01, -0.26),
    new THREE.Vector3(0.52, -0.02, -0.38),
    new THREE.Vector3(0.3, -0.02, -0.4),
  ];
  const bone3 = (a: THREE.Vector3, b: THREE.Vector3, r: number) => {
    const d = b.clone().sub(a);
    const g = limb(r, r * 0.6, d.length(), 6);
    const q = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      d.clone().normalize(),
    );
    g.applyQuaternion(q).translate(a.x, a.y, a.z);
    return piece(g, new THREE.Matrix4(), bone);
  };
  parts.push(bone3(new THREE.Vector3(0, 0, 0), elbow, 0.03), bone3(elbow, wrist, 0.024));
  for (const t of tips) parts.push(bone3(wrist, t, 0.012));
  // (the claw on the wrist)
  parts.push(
    piece(
      new THREE.ConeGeometry(0.012, 0.05, 5),
      M(wrist.x, wrist.y + 0.03, wrist.z + 0.02, 1, 1, 1, -0.6),
      "#e8dcc0",
    ),
  );
  // The membrane: a fan from the wrist and the body's side between the fingers, both faces.
  const root = new THREE.Vector3(0.02, 0.0, -0.18);
  const fan = [wrist, ...tips, root];
  const pos: number[] = [];
  const tri = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3) => {
    // (a little sag below the bones)
    const s = (v: THREE.Vector3) => [v.x, v.y - 0.015 * (v === wrist ? 0 : 1), v.z];
    pos.push(...s(a), ...s(b), ...s(c), ...s(a), ...s(c), ...s(b));
  };
  for (let i = 1; i < fan.length - 1; i++) {
    const mid = fan[i]!.clone()
      .lerp(fan[i + 1]!, 0.5)
      .lerp(wrist, 0.35);
    mid.y -= 0.03;
    tri(wrist, fan[i]!, mid);
    tri(mid, fan[i]!, fan[i + 1]!);
  }
  tri(new THREE.Vector3(0, 0, 0), wrist, root);
  const m = new THREE.BufferGeometry();
  m.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
  m.computeVertexNormals();
  parts.push(piece(m, new THREE.Matrix4(), color));
  return mergeGeometries(parts)!;
}

export function createWyvernView(
  parent: THREE.Object3D,
  size: number,
  colors: WyvernColors,
  little = false,
): SerpentView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const lam = (o: THREE.MeshLambertMaterialParameters) => {
    const m = new THREE.MeshLambertMaterial({ vertexColors: true, ...o });
    mats.push(m);
    return m;
  };
  const body = lam({});
  const skin = lam({ side: THREE.DoubleSide });
  const eyeMat = new THREE.MeshBasicMaterial({ color: "#ffd84a" });
  mats.push(eyeMat);
  const S = (little ? 30 : 36) * size;
  const root = new THREE.Group();
  root.name = little ? "little dragon" : "great dragon";
  root.scale.setScalar(S);
  parent.add(root);
  const sc = colors.body;
  const bl = colors.belly;
  const horn = "#efe2c2";
  const spike = new THREE.Color(sc).multiplyScalar(0.55).getStyle();
  // ---- the body: the chest, the belly plates, the neck, spines down the back
  const torso = [
    piece(new THREE.SphereGeometry(1, 18, 12), M(0, 0, 0, 0.1, 0.09, 0.2), sc, bl),
    piece(new THREE.SphereGeometry(1, 16, 10), M(0, -0.02, -0.12, 0.08, 0.075, 0.12), sc, bl),
    piece(limb(0.06, 0.04, 0.2), M(0, 0.02, 0.14, 1, 1, 1, -0.35), sc, bl),
  ];
  for (let k = 0; k < 7; k++)
    torso.push(
      piece(
        new THREE.ConeGeometry(0.018, 0.06, 4),
        M(0, 0.085 - Math.abs(k - 2) * 0.006, 0.18 - k * 0.06, 0.5, 1, 1, -0.5),
        spike,
      ),
    );
  // (the legs, tucked up for flight: thighs and feet, claws pale)
  for (const [z, sd] of [
    [0.1, -1],
    [0.1, 1],
    [-0.13, -1],
    [-0.13, 1],
  ] as const) {
    torso.push(piece(limb(0.03, 0.02, 0.12), M(sd * 0.075, -0.05, z, 1, 1, 1, 2.3), sc, bl));
    torso.push(
      piece(
        new THREE.ConeGeometry(0.012, 0.04, 4),
        M(sd * 0.075, -0.1, z - 0.1, 1, 1, 1, -1.9),
        horn,
      ),
    );
  }
  const bodyMesh = new THREE.Mesh(mergeGeometries(torso)!, body);
  geos.push(bodyMesh.geometry);
  root.add(bodyMesh);
  // ---- the head: on its own pivot at the neck's end (it looks about)
  const neck = new THREE.Group();
  neck.position.set(0, 0.09, 0.31);
  root.add(neck);
  const head = [
    piece(new THREE.SphereGeometry(1, 14, 10), M(0, 0.0, 0.0, 0.045, 0.04, 0.06), sc, bl),
    piece(limb(0.035, 0.018, 0.1), M(0, -0.005, 0.03, 1, 0.75, 1), sc, bl),
    piece(limb(0.028, 0.014, 0.085), M(0, -0.03, 0.03, 1, 0.45, 1, 0.12), bl),
  ];
  for (const sd of [-1, 1]) {
    head.push(
      piece(
        new THREE.ConeGeometry(0.012, 0.09, 6),
        M(sd * 0.025, 0.035, -0.04, 1, 1, 1, -2.2, 0, -sd * 0.25),
        horn,
      ),
    );
    head.push(
      piece(
        new THREE.ConeGeometry(0.008, 0.05, 5),
        M(sd * 0.04, 0.0, -0.035, 1, 1, 1, -2.0, 0, -sd * 0.9),
        horn,
      ),
    );
    for (let k = 0; k < 3; k++)
      head.push(
        piece(
          new THREE.ConeGeometry(0.005, 0.016, 4),
          M(sd * 0.016, -0.022, 0.07 + k * 0.018, 1, 1, 1, Math.PI),
          "#fff8e8",
        ),
      );
  }
  for (let k = 0; k < 4; k++)
    head.push(
      piece(
        new THREE.ConeGeometry(0.01, 0.035, 4),
        M(0, 0.035, -0.01 - k * 0.022, 0.5, 1, 1, -0.7),
        spike,
      ),
    );
  const headMesh = new THREE.Mesh(mergeGeometries(head)!, body);
  geos.push(headMesh.geometry);
  neck.add(headMesh);
  for (const sd of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.009, 8, 6), eyeMat);
    geos.push(eye.geometry);
    eye.position.set(sd * 0.03, 0.018, 0.035);
    neck.add(eye);
  }
  // ---- the tail: segments, each swinging a little after the last; a spade at its end
  const tail: THREE.Group[] = [];
  let tParent: THREE.Object3D = root;
  const TS = 7;
  for (let k = 0; k < TS; k++) {
    const g = new THREE.Group();
    g.position.set(0, k === 0 ? 0.0 : 0, k === 0 ? -0.2 : -0.085);
    const r0 = 0.05 * (1 - k / TS) + 0.01;
    const r1 = 0.05 * (1 - (k + 1) / TS) + 0.008;
    const parts = [piece(limb(r1, r0, 0.09).translate(0, 0, -0.09), new THREE.Matrix4(), sc, bl)];
    if (k % 2 === 0)
      parts.push(
        piece(new THREE.ConeGeometry(0.01, 0.03, 4), M(0, r0, -0.04, 0.5, 1, 1, -0.6), spike),
      );
    if (k === TS - 1) {
      const sp = new THREE.Shape();
      sp.moveTo(0, 0);
      sp.lineTo(0.04, -0.05);
      sp.lineTo(0, -0.11);
      sp.lineTo(-0.04, -0.05);
      sp.closePath();
      const sg = new THREE.ShapeGeometry(sp).rotateX(Math.PI / 2).translate(0, 0, -0.09);
      parts.push(piece(sg, new THREE.Matrix4(), spike));
    }
    const mesh = new THREE.Mesh(mergeGeometries(parts)!, k === TS - 1 ? skin : body);
    geos.push(mesh.geometry);
    g.add(mesh);
    tParent.add(g);
    tail.push(g);
    tParent = g;
  }
  // ---- the wings
  const wingColor = colors.wing ?? new THREE.Color(sc).lerp(new THREE.Color(bl), 0.35).getStyle();
  const wg = wingGeometry(wingColor, new THREE.Color(sc).multiplyScalar(0.7).getStyle());
  geos.push(wg);
  const wings = [-1, 1].map((sd) => {
    const g = new THREE.Group();
    g.position.set(sd * 0.07, 0.07, 0.09);
    const mesh = new THREE.Mesh(wg, skin);
    mesh.scale.set(sd, 1, 1);
    g.add(mesh);
    root.add(g);
    return g;
  });
  root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) o.castShadow = !little;
  });

  // ---- flight: facing the way it's going, banking into turns; the spine along its trail
  const trail: THREE.Vector3[] = [];
  const spine: THREE.Vector3[] = Array.from({ length: 10 }, () => new THREE.Vector3());
  const headPos = new THREE.Vector3();
  const prevDir = new THREE.Vector3(0, 0, 1);
  const dir = new THREE.Vector3();
  const lookQ = new THREE.Quaternion();
  const m4 = new THREE.Matrix4();
  const up = new THREE.Vector3(0, 1, 0);
  let bank = 0;
  let last = 0;
  const L = 0.95 * S; // (head to tail tip, m)
  return {
    spine,
    head: headPos,
    update(p, t, look) {
      const dt = Math.min(0.1, Math.max(0.0001, t - last));
      last = t;
      headPos.copy(p);
      const lastP = trail[0];
      if (!lastP || lastP.distanceTo(p) > 0.05 * S) trail.unshift(p.clone());
      if (trail.length > 400) trail.length = 400;
      // (the way it's going: from a point a little back along its trail to its head)
      let back = trail[trail.length - 1]!;
      let acc = 0;
      for (let i = 1; i < trail.length; i++) {
        acc += trail[i]!.distanceTo(trail[i - 1]!);
        back = trail[i]!;
        if (acc > 0.3 * S) break;
      }
      dir.copy(p).sub(back);
      if (dir.lengthSq() < 1e-6) dir.copy(prevDir);
      dir.normalize();
      const turn = new THREE.Vector3().crossVectors(prevDir, dir).y / Math.max(dt, 1e-3);
      prevDir.lerp(dir, 1 - Math.exp(-4 * dt)).normalize();
      bank += (Math.max(-0.7, Math.min(0.7, -turn * 0.6)) - bank) * (1 - Math.exp(-2 * dt));
      // (the body sits behind the head: the root at its chest)
      root.position.copy(p).addScaledVector(prevDir, -0.36 * S);
      m4.lookAt(new THREE.Vector3(0, 0, 0), prevDir.clone().negate(), up);
      root.quaternion.setFromRotationMatrix(m4);
      root.rotateZ(bank);
      // (wings: a few strong beats, then a long glide; faster for the little ones)
      const rate = little ? 7.5 : 2.4;
      const cyc = (t * rate * 0.25 + size * 3.1) % 4;
      const beating = cyc < 2.4;
      const flap = beating ? Math.sin(t * rate) : 0;
      wings.forEach((w, k) => {
        const sd = k === 0 ? -1 : 1;
        w.rotation.z = sd * (beating ? 0.75 * flap : 0.12 + 0.03 * Math.sin(t * 2));
        w.rotation.y = sd * (beating ? 0.15 * Math.cos(t * rate) : 0.05);
      });
      root.position.y += (beating ? -0.03 * flap : 0) * S;
      // (the tail swings, each segment a beat behind)
      tail.forEach((g, k) => {
        g.rotation.y = 0.12 * Math.sin(t * 1.6 - k * 0.6);
        g.rotation.x = 0.04 * Math.sin(t * 1.1 - k * 0.5) + (k === 0 ? 0.08 : 0);
      });
      // (the head looks toward what it's watching)
      neck.rotation.set(0.15 * Math.sin(t * 0.9), 0, 0);
      if (look.amount > 0) {
        const want = look.at.clone().sub(p);
        want.applyQuaternion(root.quaternion.clone().invert());
        const yaw = Math.max(-0.9, Math.min(0.9, Math.atan2(want.x, want.z)));
        lookQ.setFromEuler(new THREE.Euler(0, yaw * look.amount, 0));
        neck.quaternion.multiply(lookQ);
      }
      // (the spine: along its trail from the head back its length)
      spine[0]!.copy(p);
      let need = L / (spine.length - 1);
      let k = 1;
      let walked = 0;
      for (let i = 1; i < trail.length && k < spine.length; i++) {
        const seg = trail[i]!.distanceTo(trail[i - 1]!);
        walked += seg;
        while (walked >= need && k < spine.length) {
          spine[k]!.copy(trail[i]!);
          k++;
          need += L / (spine.length - 1);
        }
      }
      for (; k < spine.length; k++)
        spine[k]!.copy(p).addScaledVector(prevDir, (-L * k) / (spine.length - 1));
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
