/**
 * A live loft: one smooth skin round a spine curve, re-bent every frame (the way
 * render/dinosaur.ts does its long-neck). The spine is a Catmull-Rom curve through a few
 * control points; rings of vertices are swept along it with rotation-minimising frames
 * (so a neck can turn and a tail can curl without the skin twisting), each ring a
 * superellipse whose half-width and half-height ease between the control points'.
 *
 * Two UV sets: `uv` (0..1 round the ring from the belly, 0..1 along the rest length) for
 * a painted colour atlas, and `uv1` for a tiling detail texture (scales) whose cells keep
 * roughly square and grow with the girth, like a reptile's.
 *
 * The ring frames are kept (`frame()`), so legs, wings, spines and fins can ride the
 * skin wherever it bends.
 */
import * as THREE from "three";

export interface LoftRing {
  rx: number;
  ry: number;
  /** Squareness (2 = ellipse, 3 = boxy). */
  sq?: number;
  /** Flatten the underside (0..1): a belly that sits on the ground, a jaw's floor. */
  keel?: number;
}

export interface LiveLoftOptions {
  /** One shape per control point (the spine's), eased between. */
  shape: LoftRing[];
  rings: number;
  sides: number;
  /** Detail cells round the body (uv1.x runs 0..cells round every ring). */
  cells?: number;
  /** Cell length along the body, per unit of half-girth. */
  cellAlong?: number;
  /** Vertex colours (0..1 along, angle round from the belly), if wanted. */
  paint?: (u: number, a: number) => THREE.Color;
}

const smooth = (e: number) => e * e * (3 - 2 * e);

export class LiveLoft {
  readonly geometry = new THREE.BufferGeometry();
  readonly ctrl: THREE.Vector3[];
  readonly rings: number;
  readonly sides: number;
  /** Per ring: centre, tangent, side and up (rebuilt by update()). */
  readonly P: THREE.Vector3[] = [];
  readonly T: THREE.Vector3[] = [];
  readonly S: THREE.Vector3[] = [];
  readonly U: THREE.Vector3[] = [];
  /** Per ring: half-width and half-height as built (before any swell). */
  readonly rx: Float32Array;
  readonly ry: Float32Array;
  /** Per ring: its rest arc length from the start (set on the first update). */
  readonly arc: Float32Array;
  length = 0;
  private sq: Float32Array;
  private keel: Float32Array;
  private pos: Float32Array;
  private uv: Float32Array;
  private uv1: Float32Array;
  private curve: THREE.CatmullRomCurve3;
  private first = true;
  private cells: number;
  private cellAlong: number;
  /** Cos and sin of each side's angle (the superellipse already applied). */
  private ca: Float32Array;
  private sa: Float32Array;

  constructor(opts: LiveLoftOptions) {
    const n = opts.shape.length;
    this.rings = opts.rings;
    this.sides = opts.sides;
    this.cells = opts.cells ?? 18;
    this.cellAlong = opts.cellAlong ?? 1;
    this.ctrl = opts.shape.map(() => new THREE.Vector3());
    this.curve = new THREE.CatmullRomCurve3(this.ctrl, false, "centripetal");
    const R = this.rings;
    const ring = this.sides + 1;
    this.rx = new Float32Array(R);
    this.ry = new Float32Array(R);
    this.sq = new Float32Array(R);
    this.keel = new Float32Array(R);
    this.arc = new Float32Array(R);
    for (let i = 0; i < R; i++) {
      const f = (i / (R - 1)) * (n - 1);
      const k = Math.min(n - 2, Math.floor(f));
      const e = smooth(f - k);
      const a = opts.shape[k]!;
      const b = opts.shape[k + 1]!;
      this.rx[i] = a.rx + (b.rx - a.rx) * e;
      this.ry[i] = a.ry + (b.ry - a.ry) * e;
      this.sq[i] = (a.sq ?? 2) + ((b.sq ?? 2) - (a.sq ?? 2)) * e;
      this.keel[i] = (a.keel ?? 0) + ((b.keel ?? 0) - (a.keel ?? 0)) * e;
      this.P.push(new THREE.Vector3());
      this.T.push(new THREE.Vector3());
      this.S.push(new THREE.Vector3());
      this.U.push(new THREE.Vector3());
    }
    this.ca = new Float32Array(R * ring);
    this.sa = new Float32Array(R * ring);
    for (let i = 0; i < R; i++)
      for (let k = 0; k <= this.sides; k++) {
        // k = 0 on the belly's midline (the seam), up the +side to the back.
        const a = -Math.PI / 2 + (k / this.sides) * Math.PI * 2;
        const c = Math.cos(a);
        const s = Math.sin(a);
        const e = 2 / this.sq[i]!;
        let y = Math.sign(s) * Math.abs(s) ** e;
        if (y < 0) y *= 1 - this.keel[i]!;
        this.ca[i * ring + k] = Math.sign(c) * Math.abs(c) ** e;
        this.sa[i * ring + k] = y;
      }
    this.pos = new Float32Array(R * ring * 3);
    this.uv = new Float32Array(R * ring * 2);
    this.uv1 = new Float32Array(R * ring * 2);
    const idx: number[] = [];
    for (let i = 0; i < R - 1; i++)
      for (let k = 0; k < this.sides; k++) {
        const a = i * ring + k;
        const b = a + ring;
        idx.push(a, a + 1, b, a + 1, b + 1, b);
      }
    const g = this.geometry;
    if (opts.paint) {
      const col = new Float32Array(R * ring * 3);
      for (let i = 0; i < R; i++)
        for (let k = 0; k <= this.sides; k++) {
          const c = opts.paint(i / (R - 1), (k / this.sides) * Math.PI * 2);
          col.set([c.r, c.g, c.b], (i * ring + k) * 3);
        }
      g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    }
    g.setAttribute("position", new THREE.BufferAttribute(this.pos, 3));
    g.setAttribute("uv", new THREE.BufferAttribute(this.uv, 2));
    g.setAttribute("uv1", new THREE.BufferAttribute(this.uv1, 2));
    g.setIndex(idx);
  }

  /** Where a 0..1 position along the spine falls among the rings. */
  ringAt(u: number) {
    return Math.max(0, Math.min(this.rings - 1, u * (this.rings - 1)));
  }

  /**
   * Re-sweep the skin through the control points (set `ctrl` first). `swell(i)` scales
   * ring i (breathing, a throat filling with fire), 1 by default.
   */
  update(swell?: (i: number, u: number) => number) {
    const R = this.rings;
    const ring = this.sides + 1;
    const c = this.curve;
    for (let i = 0; i < R; i++) c.getPoint(i / (R - 1), this.P[i]!);
    // Tangents from the neighbours; frames by rotation-minimising transport.
    for (let i = 0; i < R; i++) {
      const a = this.P[Math.max(0, i - 1)]!;
      const b = this.P[Math.min(R - 1, i + 1)]!;
      const t = this.T[i]!.subVectors(b, a);
      if (t.lengthSq() < 1e-10) t.copy(i > 0 ? this.T[i - 1]! : new THREE.Vector3(0, 0, 1));
      t.normalize();
      const s = this.S[i]!;
      if (i === 0) s.set(1, 0, 0);
      else s.copy(this.S[i - 1]!);
      s.addScaledVector(t, -s.dot(t));
      if (s.lengthSq() < 1e-8) s.set(0, 1, 0).cross(t);
      s.normalize();
      this.U[i]!.crossVectors(t, s).normalize();
    }
    if (this.first) {
      let L = 0;
      for (let i = 0; i < R; i++) {
        if (i > 0) L += this.P[i]!.distanceTo(this.P[i - 1]!);
        this.arc[i] = L;
      }
      this.length = L;
      // uv: round the ring, along the rest length. uv1: square-ish cells that grow with
      // the girth (integrated along the body).
      let v1 = 0;
      for (let i = 0; i < R; i++) {
        const girth = Math.max(0.25, (this.rx[i]! + this.ry[i]!) * 0.5);
        if (i > 0)
          v1 +=
            (this.arc[i]! - this.arc[i - 1]!) /
            (((girth * Math.PI * 2) / this.cells) * this.cellAlong);
        for (let k = 0; k <= this.sides; k++) {
          const o = (i * ring + k) * 2;
          this.uv[o] = k / this.sides;
          this.uv[o + 1] = L > 0 ? this.arc[i]! / L : 0;
          this.uv1[o] = (k / this.sides) * this.cells;
          this.uv1[o + 1] = v1;
        }
      }
      this.geometry.attributes.uv!.needsUpdate = true;
      this.geometry.attributes.uv1!.needsUpdate = true;
      this.first = false;
    }
    const pos = this.pos;
    for (let i = 0; i < R; i++) {
      const p = this.P[i]!;
      const s = this.S[i]!;
      const up = this.U[i]!;
      const w = swell ? swell(i, i / (R - 1)) : 1;
      const rx = this.rx[i]! * w;
      const ry = this.ry[i]! * w;
      for (let k = 0; k <= this.sides; k++) {
        const j = i * ring + k;
        const x = this.ca[j]! * rx;
        const y = this.sa[j]! * ry;
        const o = j * 3;
        pos[o] = p.x + s.x * x + up.x * y;
        pos[o + 1] = p.y + s.y * x + up.y * y;
        pos[o + 2] = p.z + s.z * x + up.z * y;
      }
    }
    const g = this.geometry;
    g.attributes.position!.needsUpdate = true;
    g.computeVertexNormals();
    // Weld the seam's normals (the belly's midline), so it doesn't show.
    const nor = g.attributes.normal!.array as Float32Array;
    for (let i = 0; i < R; i++) {
      const a = i * ring * 3;
      const b = (i * ring + this.sides) * 3;
      for (let q = 0; q < 3; q++) {
        const m = (nor[a + q]! + nor[b + q]!) * 0.5;
        nor[a + q] = m;
        nor[b + q] = m;
      }
    }
    // The ends: a collapsed ring's normals point along the spine.
    g.computeBoundingSphere();
  }

  /**
   * The frame at 0..1 along the spine (interpolated between rings): centre, tangent,
   * side, up, and the half-width and half-height there.
   */
  frame(
    u: number,
    out: { p: THREE.Vector3; t: THREE.Vector3; s: THREE.Vector3; up: THREE.Vector3 },
  ) {
    const f = this.ringAt(u);
    const i = Math.min(this.rings - 2, Math.floor(f));
    const e = f - i;
    out.p.lerpVectors(this.P[i]!, this.P[i + 1]!, e);
    out.t.lerpVectors(this.T[i]!, this.T[i + 1]!, e).normalize();
    out.s.lerpVectors(this.S[i]!, this.S[i + 1]!, e).normalize();
    out.up.lerpVectors(this.U[i]!, this.U[i + 1]!, e).normalize();
    return {
      rx: this.rx[i]! + (this.rx[i + 1]! - this.rx[i]!) * e,
      ry: this.ry[i]! + (this.ry[i + 1]! - this.ry[i]!) * e,
    };
  }

  dispose() {
    this.geometry.dispose();
  }
}

/** A reusable frame for LiveLoft.frame(). */
export const newFrame = () => ({
  p: new THREE.Vector3(),
  t: new THREE.Vector3(),
  s: new THREE.Vector3(),
  up: new THREE.Vector3(),
});
