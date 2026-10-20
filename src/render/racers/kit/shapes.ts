/**
 * Shapes for the racers, and the builder that merges them.
 *
 * The main tool is `loft`: a run of cross-sections (centre, half-width, half-height)
 * joined into one smooth low-poly skin, like a modeller would box-model a body, neck,
 * tail, snout or crest. A handful of sections and 8-12 sides give rounded, faceted
 * silhouettes on a few hundred triangles, with colours that can change along the
 * shape (a crest going from gold to orange) and around it (a pale belly).
 *
 * Everything is in metres with +Z forward, +Y up and +X to the racer's left.
 */
import * as THREE from "three";
import { ConvexGeometry } from "three/examples/jsm/geometries/ConvexGeometry.js";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export type V3 = [number, number, number];
export type ColorLike = string | THREE.Color;
const col = (c: ColorLike) => (c instanceof THREE.Color ? c.clone() : new THREE.Color(c));

export interface Place {
  /** Position. */
  p?: V3;
  /** Rotation, radians (XYZ order). */
  r?: V3;
  /** Scale. */
  s?: V3 | number;
  /** Mirror across X (the other side of the body). */
  mirror?: boolean;
}

const m4 = new THREE.Matrix4();
const qt = new THREE.Quaternion();
const eu = new THREE.Euler();
const v3 = new THREE.Vector3();
const s3 = new THREE.Vector3();

function placeMatrix(at: Place) {
  const s = at.s ?? 1;
  m4.compose(
    v3.set(...(at.p ?? [0, 0, 0])),
    qt.setFromEuler(eu.set(...(at.r ?? [0, 0, 0]))),
    typeof s === "number" ? s3.set(s, s, s) : s3.set(...s),
  );
  if (at.mirror) m4.premultiply(new THREE.Matrix4().makeScale(-1, 1, 1));
  return m4;
}

/** Reverse every triangle's winding (after a mirror), keeping the faces outward. */
function flipWinding(g: THREE.BufferGeometry) {
  for (const name of Object.keys(g.attributes)) {
    const a = g.getAttribute(name) as THREE.BufferAttribute;
    const n = a.itemSize;
    for (let i = 0; i < a.count; i += 3)
      for (let k = 0; k < n; k++) {
        const t = a.array[(i + 1) * n + k]!;
        a.array[(i + 1) * n + k] = a.array[(i + 2) * n + k]!;
        a.array[(i + 2) * n + k] = t;
      }
    a.needsUpdate = true;
  }
}

function prepare(geo: THREE.BufferGeometry, at: Place) {
  const g = geo.index ? geo.toNonIndexed() : geo.clone();
  if (!g.getAttribute("normal")) g.computeVertexNormals();
  const n = g.getAttribute("position").count;
  if (!g.getAttribute("uv"))
    g.setAttribute("uv", new THREE.Float32BufferAttribute(new Float32Array(n * 2), 2));
  for (const name of Object.keys(g.attributes))
    if (!["position", "normal", "uv", "color"].includes(name)) g.deleteAttribute(name);
  g.applyMatrix4(placeMatrix(at));
  if (at.mirror) flipWinding(g);
  return g;
}

/** Collects coloured shapes and merges them into one geometry (one draw call). */
export class Build {
  private list: THREE.BufferGeometry[] = [];

  /**
   * Add a shape in one colour, or coloured per vertex by `color(position, normal)` in
   * the shape's own space (before it's placed): gradients, bellies, tips.
   */
  add(
    geo: THREE.BufferGeometry,
    color: ColorLike | ((p: THREE.Vector3, n: THREE.Vector3) => ColorLike),
    at: Place = {},
  ): this {
    const g = geo.index ? geo.toNonIndexed() : geo.clone();
    if (!g.getAttribute("normal")) g.computeVertexNormals();
    const pos = g.getAttribute("position");
    const nor = g.getAttribute("normal");
    const cols = new Float32Array(pos.count * 3);
    const p = new THREE.Vector3();
    const nn = new THREE.Vector3();
    const fixed = typeof color === "function" ? undefined : col(color);
    for (let i = 0; i < pos.count; i++) {
      const c =
        fixed ??
        col(
          (color as (p: THREE.Vector3, n: THREE.Vector3) => ColorLike)(
            p.fromBufferAttribute(pos, i),
            nn.fromBufferAttribute(nor, i),
          ),
        );
      cols.set([c.r, c.g, c.b], i * 3);
    }
    g.setAttribute("color", new THREE.BufferAttribute(cols, 3));
    geo.dispose();
    this.list.push(prepare(g, at));
    g.dispose();
    return this;
  }

  /** Add a shape that already has its colours (a loft, a built wheel). */
  addColored(geo: THREE.BufferGeometry, at: Place = {}): this {
    this.list.push(prepare(geo, at));
    return this;
  }

  /** Add the same shape on both sides: as given (left, +X) and mirrored (right). */
  both(
    geo: THREE.BufferGeometry,
    color: ColorLike | ((p: THREE.Vector3, n: THREE.Vector3) => ColorLike) | null,
    at: Place = {},
  ): this {
    const copy = geo.clone();
    if (color === null) {
      this.addColored(geo, at);
      this.addColored(copy, { ...at, mirror: true });
    } else {
      this.add(geo, color, at);
      this.add(copy, color, { ...at, mirror: true });
    }
    return this;
  }

  get empty() {
    return this.list.length === 0;
  }

  build(): THREE.BufferGeometry {
    const merged = mergeGeometries(this.list, false);
    for (const g of this.list) g.dispose();
    this.list = [];
    merged.computeBoundingSphere();
    merged.computeBoundingBox();
    return merged;
  }
}

// ------------------------------------------------------------------ primitives

let low = false;
/**
 * Build something in its far-away version: boxes lose their chamfers, balls and lofts
 * lose sides. Everything built inside `fn` is affected.
 */
export function lowDetail<T>(fn: () => T): T {
  const was = low;
  low = true;
  try {
    return fn();
  } finally {
    low = was;
  }
}
export const isLowDetail = () => low;

export const ellipsoid = (sides = 12, rings = 8) =>
  low
    ? new THREE.SphereGeometry(1, Math.max(5, sides >> 1), Math.max(3, rings >> 1))
    : new THREE.SphereGeometry(1, sides, rings);
/** A faceted ball (icosphere): 0 = chunky rock, 1 = pebble, 2 = rounder. */
export const gem = (detail = 1) => new THREE.IcosahedronGeometry(1, low ? 0 : detail);
/** A box with chamfered edges and corners (26 faces, like a carved toy block). */
export function box(w: number, h: number, d: number, bevel = 0.04) {
  if (low || bevel <= 0) return new THREE.BoxGeometry(w, h, d);
  const b = Math.min(bevel, w / 2.01, h / 2.01, d / 2.01);
  const pts: THREE.Vector3[] = [];
  for (const sx of [-1, 1])
    for (const sy of [-1, 1])
      for (const sz of [-1, 1]) {
        const x = (sx * w) / 2;
        const y = (sy * h) / 2;
        const z = (sz * d) / 2;
        pts.push(new THREE.Vector3(x - sx * b, y, z - sz * b));
        pts.push(new THREE.Vector3(x, y - sy * b, z - sz * b));
        pts.push(new THREE.Vector3(x - sx * b, y - sy * b, z));
      }
  return new ConvexGeometry(pts);
}
export const cyl = (rTop: number, rBottom: number, h: number, sides = 8) =>
  new THREE.CylinderGeometry(rTop, rBottom, h, sides);
export const cone = (r: number, h: number, sides = 6) => new THREE.ConeGeometry(r, h, sides);
export const torus = (r: number, t: number, sides = 6, seg = 12, arc = Math.PI * 2) =>
  new THREE.TorusGeometry(r, t, sides, seg, arc);

/**
 * Taper a shape toward +Z: at the front its width and height shrink to `fx` / `fy` of
 * the original, and it can drop by `dropFront`.
 */
export function taper(geo: THREE.BufferGeometry, fx: number, fy: number, dropFront = 0) {
  geo.computeBoundingBox();
  const b = geo.boundingBox!;
  const pos = geo.getAttribute("position") as THREE.BufferAttribute;
  for (let i = 0; i < pos.count; i++) {
    const t = (pos.getZ(i) - b.min.z) / Math.max(1e-6, b.max.z - b.min.z);
    pos.setX(i, pos.getX(i) * (1 + (fx - 1) * t));
    pos.setY(i, b.min.y + (pos.getY(i) - b.min.y) * (1 + (fy - 1) * t) - dropFront * t);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();
  return geo;
}

/** A chunky polygonal tyre with chamfered edges, axis along X. */
export function tyre(radius: number, width: number, chamfer: number, sides = 8) {
  const h = width / 2;
  const pts = [
    [0.001, -h],
    [radius - chamfer, -h],
    [radius, -h + chamfer],
    [radius, h - chamfer],
    [radius - chamfer, h],
    [0.001, h],
  ].map(([x, y]) => new THREE.Vector2(x, y));
  return new THREE.LatheGeometry(pts, sides, Math.PI / sides).rotateZ(Math.PI / 2);
}

/** A flat outline (x, y points) lying in the XY plane, with both faces (or a thin slab). */
export function card(outline: [number, number][], thickness = 0) {
  const shape = new THREE.Shape(outline.map(([x, y]) => new THREE.Vector2(x, y)));
  if (thickness > 0)
    return new THREE.ExtrudeGeometry(shape, { depth: thickness, bevelEnabled: false })
      .translate(0, 0, -thickness / 2)
      .toNonIndexed();
  const shapeGeo = new THREE.ShapeGeometry(shape);
  const front = shapeGeo.toNonIndexed();
  shapeGeo.dispose();
  const back = front.clone();
  flipWinding(back);
  const n = back.getAttribute("normal") as THREE.BufferAttribute;
  for (let i = 0; i < n.count; i++) n.setZ(i, -n.getZ(i));
  return mergeGeometries([front, back], false);
}

// ------------------------------------------------------------------ loft

/** One cross-section of a loft. */
export interface Section {
  /** Centre. */
  at: V3;
  /** Half-width (across, X-ish) and half-height (Y-ish). */
  rx: number;
  ry: number;
  /** Colour here (blended between sections). */
  color?: ColorLike;
  /**
   * Squareness: 2 is an ellipse, higher is boxier (3-4 for chunky toy shapes), lower
   * is pinched (1.5 gives a diamond-ish keel).
   */
  sq?: number;
  /** Shift the section's top or bottom: >0 flattens the bottom (a belly), etc. */
  flat?: number;
}

export interface LoftOptions {
  /** Sides round each section (8-12). */
  sides?: number;
  /** Extra sections added between each given pair, following a smooth curve. */
  steps?: number;
  /**
   * The direction that counts as "up" for the cross-sections (default +Y; use +Z for
   * shapes that run up and down, like a torso).
   */
  up?: V3;
  /** Close the ends. */
  capStart?: boolean;
  capEnd?: boolean;
  /**
   * Colour per vertex: `t` is 0..1 along the loft, `a` the angle round the section
   * (0 = the +side direction, pi/2 = up, -pi/2 = down), `base` the section colour.
   */
  paint?: (t: number, a: number, base: THREE.Color) => ColorLike;
  /** Turn the ring of vertices (radians), e.g. half a step so a facet faces up. */
  phase?: number;
}

const smoothstep = (e: number) => e * e * (3 - 2 * e);

/** A smooth low-poly skin through cross-sections. Returns coloured, indexed geometry. */
export function loft(sections: Section[], opts: LoftOptions = {}): THREE.BufferGeometry {
  const sides = low ? Math.max(5, Math.round((opts.sides ?? 10) / 2)) : (opts.sides ?? 10);
  const steps = low ? 1 : (opts.steps ?? 1);
  const upRef = new THREE.Vector3(...(opts.up ?? [0, 1, 0])).normalize();
  // Resample along a Catmull-Rom curve through the centres, easing the radii.
  const curve = new THREE.CatmullRomCurve3(
    sections.map((s) => new THREE.Vector3(...s.at)),
    false,
    "centripetal",
  );
  const rings: {
    p: THREE.Vector3;
    rx: number;
    ry: number;
    color: THREE.Color;
    sq: number;
    flat: number;
    t: number;
  }[] = [];
  const nSeg = sections.length - 1;
  for (let i = 0; i < nSeg; i++) {
    const a = sections[i]!;
    const b = sections[i + 1]!;
    for (let k = 0; k < steps + (i === nSeg - 1 ? 1 : 0); k++) {
      const f = k / (steps + 0);
      const e = smoothstep(f);
      const u = (i + f) / nSeg;
      const ca = col(a.color ?? "#ffffff");
      const cb = col(b.color ?? a.color ?? "#ffffff");
      rings.push({
        p: steps > 1 ? curve.getPoint(u) : new THREE.Vector3(...(f === 0 ? a.at : b.at)),
        rx: a.rx + (b.rx - a.rx) * e,
        ry: a.ry + (b.ry - a.ry) * e,
        color: ca.lerp(cb, f),
        sq: (a.sq ?? 2) + ((b.sq ?? 2) - (a.sq ?? 2)) * e,
        flat: (a.flat ?? 0) + ((b.flat ?? 0) - (a.flat ?? 0)) * e,
        t: u,
      });
    }
  }
  if (steps <= 1) {
    // Without resampling, the last ring is the last section itself.
    const last = sections[nSeg]!;
    rings[rings.length - 1] = {
      ...rings[rings.length - 1]!,
      p: new THREE.Vector3(...last.at),
      rx: last.rx,
      ry: last.ry,
      color: col(last.color ?? sections[nSeg - 1]!.color ?? "#ffffff"),
    };
  }

  const pos: number[] = [];
  const cols: number[] = [];
  const uvs: number[] = [];
  const idx: number[] = [];
  const tan = new THREE.Vector3();
  const side = new THREE.Vector3();
  const up = new THREE.Vector3();
  const phase = opts.phase ?? 0;
  const ring = sides + 1; // a seam column for the UVs
  rings.forEach((r, i) => {
    const prev = rings[Math.max(0, i - 1)]!.p;
    const next = rings[Math.min(rings.length - 1, i + 1)]!.p;
    tan.subVectors(next, prev).normalize();
    let ref = upRef;
    if (Math.abs(tan.dot(ref)) > 0.97) ref = new THREE.Vector3(0, 0, 1);
    side.crossVectors(ref, tan).normalize();
    up.crossVectors(tan, side).normalize();
    for (let k = 0; k <= sides; k++) {
      const a = phase + (k / sides) * Math.PI * 2;
      const c = Math.cos(a);
      const s = Math.sin(a);
      const e = 2 / r.sq;
      const x = Math.sign(c) * Math.abs(c) ** e * r.rx;
      let y = Math.sign(s) * Math.abs(s) ** e * r.ry;
      if (r.flat > 0 && y < 0) y *= 1 - r.flat;
      if (r.flat < 0 && y > 0) y *= 1 + r.flat;
      pos.push(
        r.p.x + side.x * x + up.x * y,
        r.p.y + side.y * x + up.y * y,
        r.p.z + side.z * x + up.z * y,
      );
      const ang = Math.atan2(s, c);
      const cc = opts.paint ? col(opts.paint(r.t, ang, r.color.clone())) : r.color;
      cols.push(cc.r, cc.g, cc.b);
      uvs.push(k / sides, r.t);
    }
  });
  for (let i = 0; i < rings.length - 1; i++)
    for (let k = 0; k < sides; k++) {
      const a = i * ring + k;
      const b = a + ring;
      idx.push(a, a + 1, b, a + 1, b + 1, b);
    }
  const cap = (i: number, flip: boolean) => {
    const r = rings[i]!;
    const centre = pos.length / 3;
    pos.push(r.p.x, r.p.y, r.p.z);
    const cc = opts.paint ? col(opts.paint(r.t, Math.PI / 2, r.color.clone())) : r.color;
    cols.push(cc.r, cc.g, cc.b);
    uvs.push(0.5, r.t);
    for (let k = 0; k < sides; k++) {
      const a = i * ring + k;
      if (flip) idx.push(centre, a + 1, a);
      else idx.push(centre, a, a + 1);
    }
  };
  if (opts.capStart) cap(0, true);
  if (opts.capEnd) cap(rings.length - 1, false);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.Float32BufferAttribute(cols, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/** A tapering tube through points (tails, limbs, straps, horns). */
export function tube(
  points: V3[],
  radius: number | number[],
  color: ColorLike | ColorLike[],
  opts: LoftOptions = {},
) {
  return loft(
    points.map((at, i) => {
      const r = Array.isArray(radius) ? radius[i]! : radius;
      return { at, rx: r, ry: r, color: Array.isArray(color) ? color[i] : color };
    }),
    { sides: 7, capStart: true, capEnd: true, ...opts },
  );
}

/** A horn or spike: a curved cone from `base` to `tip`, bending by `bend`. */
export function horn(
  base: V3,
  tip: V3,
  r: number,
  color: ColorLike,
  bend: V3 = [0, 0, 0],
  sides = 6,
) {
  const mid: V3 = [
    (base[0] + tip[0]) / 2 + bend[0],
    (base[1] + tip[1]) / 2 + bend[1],
    (base[2] + tip[2]) / 2 + bend[2],
  ];
  return loft(
    [
      { at: base, rx: r, ry: r, color },
      { at: mid, rx: r * 0.6, ry: r * 0.6, color },
      { at: tip, rx: r * 0.06, ry: r * 0.06, color },
    ],
    { sides, steps: 2, capStart: true },
  );
}

/** Triangle count of a geometry. */
export function triangles(g: THREE.BufferGeometry) {
  return (g.index ? g.index.count : g.getAttribute("position").count) / 3;
}
