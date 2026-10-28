/**
 * Rigid parts for the story dragons (heads, jaws, feet, horns, club tails), merged into
 * one geometry per piece, each part coloured per vertex. Like the racer kit's Build, but
 * every part also gets a second UV set (`uv1`, its own UVs times a repeat) so a tiling
 * scale texture can be bumped over it.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export type V3 = [number, number, number];
export type Paint =
  THREE.ColorRepresentation | ((p: THREE.Vector3, n: THREE.Vector3) => THREE.Color);

export interface Place {
  p?: V3;
  r?: V3;
  s?: V3 | number;
  /** Mirror across x (the dragon's other side). */
  mirror?: boolean;
  /** Repeat of the detail texture over the part's own UVs. */
  rep?: [number, number];
}

const m4 = new THREE.Matrix4();
const qt = new THREE.Quaternion();
const eu = new THREE.Euler();
const v = new THREE.Vector3();
const sv = new THREE.Vector3();
const tc = new THREE.Color();

function flip(g: THREE.BufferGeometry) {
  for (const name of Object.keys(g.attributes)) {
    const a = g.getAttribute(name) as THREE.BufferAttribute;
    const n = a.itemSize;
    for (let i = 0; i < a.count; i += 3)
      for (let k = 0; k < n; k++) {
        const t = a.array[(i + 1) * n + k]!;
        a.array[(i + 1) * n + k] = a.array[(i + 2) * n + k]!;
        a.array[(i + 2) * n + k] = t;
      }
  }
}

export class Parts {
  private list: THREE.BufferGeometry[] = [];

  /** Add a shape, painted one colour, per vertex by `paint(p, n)` (its own space), or
   * keeping its own colours (`null`, for lofts that carry them). */
  add(geo: THREE.BufferGeometry, paint: Paint | null, at: Place = {}): this {
    const g = geo.index ? geo.toNonIndexed() : geo.clone();
    geo.dispose();
    if (!g.getAttribute("normal")) g.computeVertexNormals();
    const pos = g.getAttribute("position");
    const nor = g.getAttribute("normal");
    if (paint !== null || !g.getAttribute("color")) {
      const cols = new Float32Array(pos.count * 3);
      const p = new THREE.Vector3();
      const n = new THREE.Vector3();
      const fixed = typeof paint === "function" ? undefined : tc.set(paint ?? "#ffffff").clone();
      for (let i = 0; i < pos.count; i++) {
        const c =
          fixed ??
          (paint as (p: THREE.Vector3, n: THREE.Vector3) => THREE.Color)(
            p.fromBufferAttribute(pos, i),
            n.fromBufferAttribute(nor, i),
          );
        cols[i * 3] = c.r;
        cols[i * 3 + 1] = c.g;
        cols[i * 3 + 2] = c.b;
      }
      g.setAttribute("color", new THREE.BufferAttribute(cols, 3));
    }
    if (!g.getAttribute("uv"))
      g.setAttribute("uv", new THREE.BufferAttribute(new Float32Array(pos.count * 2), 2));
    const uv = g.getAttribute("uv");
    const [ru, rv] = at.rep ?? [4, 4];
    const uv1 = new Float32Array(pos.count * 2);
    for (let i = 0; i < pos.count; i++) {
      uv1[i * 2] = uv.getX(i) * ru;
      uv1[i * 2 + 1] = uv.getY(i) * rv;
    }
    g.setAttribute("uv1", new THREE.BufferAttribute(uv1, 2));
    for (const name of Object.keys(g.attributes))
      if (!["position", "normal", "uv", "uv1", "color"].includes(name)) g.deleteAttribute(name);
    const s = at.s ?? 1;
    m4.compose(
      v.set(...(at.p ?? [0, 0, 0])),
      qt.setFromEuler(eu.set(...(at.r ?? [0, 0, 0]))),
      typeof s === "number" ? sv.set(s, s, s) : sv.set(...s),
    );
    if (at.mirror) m4.premultiply(new THREE.Matrix4().makeScale(-1, 1, 1));
    g.applyMatrix4(m4);
    if (at.mirror) flip(g);
    this.list.push(g);
    return this;
  }

  /** The same shape on both sides: as given (+x) and mirrored. */
  both(geo: THREE.BufferGeometry, paint: Paint | null, at: Place = {}): this {
    const copy = geo.clone();
    this.add(geo, paint, at);
    return this.add(copy, paint, { ...at, mirror: true });
  }

  get empty() {
    return this.list.length === 0;
  }

  build(): THREE.BufferGeometry {
    const merged = mergeGeometries(this.list, false);
    for (const g of this.list) g.dispose();
    this.list = [];
    merged.computeBoundingSphere();
    return merged;
  }
}

/** A colour (for paint functions). */
export const C = (c: THREE.ColorRepresentation) => new THREE.Color(c);
/** Mix two colours. */
export const mix = (a: THREE.ColorRepresentation, b: THREE.ColorRepresentation, t: number) =>
  new THREE.Color(a).lerp(new THREE.Color(b), Math.max(0, Math.min(1, t)));
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smoothstep = (a: number, b: number, x: number) => {
  const t = clamp01((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};

/** A curved claw (or horn): a cone bent down toward its tip, built along +y. */
export function clawGeo(r: number, len: number) {
  const pts: THREE.Vector2[] = [];
  const N = 4;
  for (let i = 0; i <= N; i++) {
    const k = i / N;
    pts.push(new THREE.Vector2(r * (1 - k) ** 0.8 + 0.001, len * k));
  }
  const g = new THREE.LatheGeometry(pts, 7);
  // Bend it: the tip curls toward -z.
  const p = g.getAttribute("position") as THREE.BufferAttribute;
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i) / len;
    p.setZ(i, p.getZ(i) - y * y * len * 0.35);
  }
  g.computeVertexNormals();
  return g;
}
