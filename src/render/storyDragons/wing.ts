/**
 * A story dragon's wing: an arm (upper arm and forearm) and a hand of long fingers
 * fanning from the wrist, with a membrane stretched between them and back to the flank,
 * sagging a little between the bones and scalloped along its trailing edge. It folds
 * (the elbow back, the wrist up by the shoulder, the fingers laid back along the body),
 * spreads, and beats; every frame the bones are placed and the membrane re-made.
 *
 * Fin-wings (Tidewyrm's) are the same with more, finer rays and deep round scallops.
 * Everything here is in the dragon's body space; the left wing is built and the right
 * mirrors it.
 */
import * as THREE from "three";
import type { WingDesign } from "./types";

const lerpDir = (a: THREE.Vector3, b: THREE.Vector3, t: number, out: THREE.Vector3) =>
  out.copy(a).lerp(b, t).normalize();

const dir = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z).normalize();

export interface WingPose {
  /** 0 folded .. 1 spread. */
  spread: number;
  /** Rotation of the whole wing about the body's long axis (radians, + = up). */
  lift: number;
  /** Sweep the wing forward (+) or back (-) (radians, about the vertical). */
  sweep: number;
  /** Twist/droop of the fingers (radians): a limp wing's tips sag. */
  droop: number;
}

export class Wing {
  readonly group = new THREE.Group();
  private bones: THREE.Mesh[] = [];
  private knuckles: THREE.Mesh[] = [];
  private thumb: THREE.Mesh;
  private geo = new THREE.BufferGeometry();
  private pos: Float32Array;
  private panels: { a: number; b: number; c: number; fan: boolean; scallop: number }[] = [];
  private R = 7;
  private Q = 6;
  /** Points: 0 shoulder, 1 elbow, 2 wrist, 3.. finger tips, then the flank. */
  readonly pts: THREE.Vector3[] = [];
  private fold: THREE.Vector3[];
  private open: THREE.Vector3[];
  private lens: number[];

  constructor(
    readonly d: WingDesign,
    readonly side: number,
    mats: { bone: THREE.Material; membrane: THREE.Material },
    boneGeo: THREE.BufferGeometry,
    knuckleGeo: THREE.BufferGeometry,
    clawGeo: THREE.BufferGeometry,
  ) {
    const n = d.fingers.length;
    // Directions (left wing; x out, y up, z forward) for folded and spread.
    this.fold = [dir(0.3, 0.06, -0.95), dir(0.1, 0.02, 1)];
    this.open = [dir(1, 0.3, -0.2), dir(1, 0.08, 0.28)];
    const [a0, a1] = d.fan;
    for (let i = 0; i < n; i++) {
      const k = n === 1 ? 0 : i / (n - 1);
      const th = a0 + (a1 - a0) * k;
      this.open.push(dir(Math.cos(th), -0.05 - 0.1 * k, Math.sin(th)));
      this.fold.push(dir(0.16 + 0.16 * k, 0.05 - 0.95 * k, -1 + 0.62 * k));
    }
    this.lens = [d.humerus, d.forearm, ...d.fingers];
    for (let i = 0; i < n + 4; i++) this.pts.push(new THREE.Vector3());
    // Bones: upper arm, forearm, fingers.
    for (let i = 0; i < n + 2; i++) {
      const m = new THREE.Mesh(boneGeo, mats.bone);
      this.bones.push(m);
      this.group.add(m);
    }
    for (let i = 0; i < 2; i++) {
      const m = new THREE.Mesh(knuckleGeo, mats.bone);
      this.knuckles.push(m);
      this.group.add(m);
    }
    this.thumb = new THREE.Mesh(clawGeo, mats.bone);
    this.group.add(this.thumb);
    // Membrane panels, each a fan from an apex (a) between two rays (to b and c).
    const W = 2;
    for (let i = 0; i < n - 1; i++)
      this.panels.push({ a: W, b: 3 + i, c: 4 + i, fan: true, scallop: d.scallop });
    const F = 3 + n; // the flank point
    this.panels.push({ a: W, b: 3 + n - 1, c: F, fan: true, scallop: d.scallop * 0.8 });
    this.panels.push({ a: F, b: 1, c: W, fan: false, scallop: 0 });
    this.panels.push({ a: F, b: 0, c: 1, fan: false, scallop: 0 });
    const R = this.R;
    const Q = this.Q;
    const per = (R + 1) * (Q + 1);
    this.pos = new Float32Array(this.panels.length * per * 3);
    const col = new Float32Array(this.panels.length * per * 3);
    const idx: number[] = [];
    const cm = new THREE.Color(d.membrane);
    const ce = new THREE.Color(d.edge);
    const cv = new THREE.Color(d.vein ?? d.membrane);
    const c = new THREE.Color();
    this.panels.forEach((pn, pi) => {
      const base = pi * per;
      for (let r = 0; r <= R; r++)
        for (let q = 0; q <= Q; q++) {
          const sr = r / R;
          const a = q / Q;
          // Darker along the bones, the edge colour toward the trailing edge.
          c.copy(cm);
          const nearBone = pn.fan ? Math.max(0, 1 - Math.min(a, 1 - a) * 5) : 0;
          c.lerp(cv, nearBone * 0.6);
          const edgeK = pn.fan ? sr : a;
          c.lerp(ce, Math.max(0, (edgeK - 0.62) / 0.38) ** 1.5);
          if (d.paint) c.copy(d.paint(c, pn.fan ? pi : -1, sr, a));
          col.set([c.r, c.g, c.b], (base + r * (Q + 1) + q) * 3);
        }
      for (let r = 0; r < R; r++)
        for (let q = 0; q < Q; q++) {
          const i0 = base + r * (Q + 1) + q;
          const i1 = i0 + 1;
          const i2 = i0 + Q + 1;
          const i3 = i2 + 1;
          if (side > 0) idx.push(i0, i2, i1, i1, i2, i3);
          else idx.push(i0, i1, i2, i1, i3, i2);
        }
    });
    this.geo.setAttribute("position", new THREE.BufferAttribute(this.pos, 3));
    this.geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    this.geo.setIndex(idx);
    const mem = new THREE.Mesh(this.geo, mats.membrane);
    mem.frustumCulled = false;
    this.group.add(mem);
  }

  private q = new THREE.Quaternion();
  private q2 = new THREE.Quaternion();
  private v = new THREE.Vector3();
  private w = new THREE.Vector3();
  private Y = new THREE.Vector3(0, 1, 0);
  private axZ = new THREE.Vector3();
  private axY = new THREE.Vector3();

  /**
   * Place the wing: `root` the shoulder and `flank` the membrane's root on the body (body
   * space), `basis` the torso's frame (x side, y up, z forward).
   */
  update(
    root: THREE.Vector3,
    flank: THREE.Vector3,
    side: THREE.Vector3,
    up: THREE.Vector3,
    fwd: THREE.Vector3,
    p: WingPose,
    /** Push a point out of the body (and off the ground): the membrane drapes over it. */
    collide?: (v: THREE.Vector3) => void,
  ) {
    const d = this.d;
    const n = d.fingers.length;
    const sd = this.side;
    const v = this.v;
    // Lift about the long axis, sweep about the vertical (in the torso's frame).
    this.axZ.copy(fwd);
    this.axY.copy(up);
    this.q.setFromAxisAngle(this.axZ, p.lift * sd);
    this.q2.setFromAxisAngle(this.axY, -p.sweep * sd);
    this.q.premultiply(this.q2);
    const P = this.pts;
    P[0]!.copy(root);
    const s = Math.max(0, Math.min(1, p.spread));
    const toBody = (lx: number, ly: number, lz: number, out: THREE.Vector3) =>
      out
        .set(0, 0, 0)
        .addScaledVector(side, lx * sd)
        .addScaledVector(up, ly)
        .addScaledVector(fwd, lz)
        .applyQuaternion(this.q);
    const ld = new THREE.Vector3();
    // Upper arm and forearm.
    for (let i = 0; i < 2; i++) {
      lerpDir(this.fold[i]!, this.open[i]!, s, ld);
      toBody(ld.x, ld.y, ld.z, v);
      P[i + 1]!.copy(P[i]!).addScaledVector(v, this.lens[i]! * (i === 1 ? 1 : 1));
    }
    // Fingers from the wrist (drooping toward their tips when limp).
    for (let i = 0; i < n; i++) {
      lerpDir(this.fold[2 + i]!, this.open[2 + i]!, s, ld);
      ld.y -= p.droop * (0.3 + 0.7 * (i / Math.max(1, n - 1)));
      ld.normalize();
      toBody(ld.x, ld.y, ld.z, v);
      P[3 + i]!.copy(P[2]!).addScaledVector(v, this.lens[2 + i]! * (0.82 + 0.18 * s));
    }
    P[3 + n]!.copy(flank);
    if (collide) for (let i = 1; i < 3 + n; i++) collide(P[i]!);
    // Bones.
    const place = (m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3, r: number) => {
      v.subVectors(b, a);
      const len = v.length();
      m.position.copy(a);
      m.quaternion.setFromUnitVectors(this.Y, v.normalize());
      m.scale.set(r, len, r);
    };
    // (Folded, the bones lie thin along the body; spread, they stand out.)
    const br = d.boneR * (0.6 + 0.4 * s);
    place(this.bones[0]!, P[0]!, P[1]!, br * 1.5);
    place(this.bones[1]!, P[1]!, P[2]!, br * 1.15);
    for (let i = 0; i < n; i++) place(this.bones[2 + i]!, P[2]!, P[3 + i]!, br * 0.8);
    this.knuckles[0]!.position.copy(P[1]!);
    this.knuckles[0]!.scale.setScalar(br * 1.25);
    this.knuckles[1]!.position.copy(P[2]!);
    this.knuckles[1]!.scale.setScalar(br * 1.05);
    // The thumb claw at the wrist, pointing forward and up.
    this.thumb.position.copy(P[2]!);
    this.w.copy(fwd).multiplyScalar(0.8).addScaledVector(up, 0.6).normalize();
    this.thumb.quaternion.setFromUnitVectors(this.Y, this.w);
    this.thumb.scale.setScalar(d.thumb);
    // The membrane.
    const R = this.R;
    const Q = this.Q;
    const per = (R + 1) * (Q + 1);
    const pos = this.pos;
    const A = new THREE.Vector3();
    const B = new THREE.Vector3();
    const Cc = new THREE.Vector3();
    const nrm = new THREE.Vector3();
    const e1 = new THREE.Vector3();
    const e2 = new THREE.Vector3();
    this.panels.forEach((pn, pi) => {
      A.copy(P[pn.a]!);
      B.copy(P[pn.b]!);
      Cc.copy(P[pn.c]!);
      e1.subVectors(B, A);
      e2.subVectors(Cc, A);
      nrm.crossVectors(e1, e2);
      const area = nrm.length();
      nrm.normalize();
      // Sag downward (toward the ground side of the membrane), scaled by the panel.
      const sag = d.sag * Math.sqrt(area) * 0.12 * (0.4 + 0.6 * s);
      if (nrm.dot(up) > 0) nrm.negate();
      const base = pi * per;
      for (let r = 0; r <= R; r++)
        for (let q = 0; q <= Q; q++) {
          const sr = r / R;
          const a = q / Q;
          const o = (base + r * (Q + 1) + q) * 3;
          let x: number;
          let y: number;
          let z: number;
          if (pn.fan) {
            // Out from the apex between the two rays; the far edge scalloped inward.
            const bow = 1 - pn.scallop * Math.sin(Math.PI * a) * sr ** 2.2;
            const k = sr * bow;
            x = A.x + (e1.x + (e2.x - e1.x) * a) * k;
            y = A.y + (e1.y + (e2.y - e1.y) * a) * k;
            z = A.z + (e1.z + (e2.z - e1.z) * a) * k;
            const sg = sag * Math.sin(Math.PI * a) * Math.sin(Math.PI * Math.min(1, sr * 1.1));
            x += nrm.x * sg;
            y += nrm.y * sg;
            z += nrm.z * sg;
          } else {
            // A triangle from the flank to the arm: rows toward the bone.
            const bx = B.x + (Cc.x - B.x) * a;
            const by = B.y + (Cc.y - B.y) * a;
            const bz = B.z + (Cc.z - B.z) * a;
            x = A.x + (bx - A.x) * sr;
            y = A.y + (by - A.y) * sr;
            z = A.z + (bz - A.z) * sr;
            const sg = sag * 0.7 * Math.sin(Math.PI * sr) * (0.5 + 0.5 * Math.sin(Math.PI * a));
            x += nrm.x * sg;
            y += nrm.y * sg;
            z += nrm.z * sg;
          }
          if (collide) {
            const t = this.w.set(x, y, z);
            collide(t);
            x = t.x;
            y = t.y;
            z = t.z;
          }
          pos[o] = x;
          pos[o + 1] = y;
          pos[o + 2] = z;
        }
    });
    this.geo.attributes.position!.needsUpdate = true;
    this.geo.computeVertexNormals();
    this.geo.computeBoundingSphere();
  }

  dispose() {
    this.geo.dispose();
  }
}
