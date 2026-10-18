/**
 * The faceted, hand-textured look (first used for Moss):
 * - flat-shaded low-poly shapes, so every facet catches the light on its own;
 * - tiny textures sampled with nearest-neighbour filtering, so their texels show as
 *   soft pixel blocks;
 * - faces painted as pixel-art texture decals, swapped for expressions.
 */
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";

function seeded(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), a | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const pixelTex = (canvas: HTMLCanvasElement) => {
  const t = new THREE.CanvasTexture(canvas);
  t.colorSpace = THREE.SRGBColorSpace;
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestMipmapLinearFilter;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
};

let grain: THREE.CanvasTexture | undefined;
/** 16x16 near-white texels with gentle variation: a hand-painted, pixelly surface. */
export function grainTexture() {
  if (grain) return grain;
  const c = document.createElement("canvas");
  c.width = c.height = 16;
  const g = c.getContext("2d")!;
  const r = seeded(5);
  for (let y = 0; y < 16; y++)
    for (let x = 0; x < 16; x++) {
      const v = Math.round(255 * (0.86 + r() * 0.14));
      g.fillStyle = `rgb(${v},${v},${v})`;
      g.fillRect(x, y, 1, 1);
    }
  grain = pixelTex(c);
  return grain;
}

let facetMat: THREE.MeshLambertMaterial | undefined;
/** Flat-shaded vertex colours times the pixel grain. */
export function facetMaterial() {
  facetMat ??= new THREE.MeshLambertMaterial({
    vertexColors: true,
    flatShading: true,
    map: grainTexture(),
  });
  return facetMat;
}

/** A faceted ball (icosphere). detail 1 = chunky, 2 = rounder. */
export const gem = (detail = 1) => new THREE.IcosahedronGeometry(1, detail);

/** A box with chamfered (single-bevel) edges. */
export const chamferBox = (w: number, h: number, d: number, bevel = 0.05) =>
  new RoundedBoxGeometry(w, h, d, 1, Math.min(bevel, w / 2.01, h / 2.01, d / 2.01));

/**
 * Taper a shape toward +Z: at the front its width and height shrink to `fx` / `fy`
 * of the original (linearly along its length), and it can drop by `dropFront`.
 */
export function taper(geo: THREE.BufferGeometry, fx: number, fy: number, dropFront = 0) {
  geo.computeBoundingBox();
  const b = geo.boundingBox!;
  const pos = geo.getAttribute("position") as THREE.BufferAttribute;
  for (let i = 0; i < pos.count; i++) {
    const t = (pos.getZ(i) - b.min.z) / Math.max(1e-6, b.max.z - b.min.z);
    const sx = 1 + (fx - 1) * t;
    const sy = 1 + (fy - 1) * t;
    pos.setX(i, pos.getX(i) * sx);
    pos.setY(i, b.min.y + (pos.getY(i) - b.min.y) * sy - dropFront * t);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();
  return geo;
}

/** A chunky octagonal tyre with chamfered edges, axis along X. */
export function octTyre(radius: number, width: number, chamfer: number, sides = 8) {
  const h = width / 2;
  const pts = [
    new THREE.Vector2(0.001, -h),
    new THREE.Vector2(radius - chamfer, -h),
    new THREE.Vector2(radius, -h + chamfer),
    new THREE.Vector2(radius, h - chamfer),
    new THREE.Vector2(radius - chamfer, h),
    new THREE.Vector2(0.001, h),
  ];
  return new THREE.LatheGeometry(pts, sides, Math.PI / sides).rotateZ(Math.PI / 2);
}

/**
 * A texture decal that lies exactly on a mesh's own facets: keeps the triangles of
 * `geo` that face `dir` (within `minDot`) and fall inside the rectangle, and maps the
 * texture over that rectangle by planar projection. `rect` is in the plane across
 * `dir`: [left, right, bottom, top] for a decal facing +Z (x, y), or (x, z) facing +Y.
 */
export function decalOn(
  geo: THREE.BufferGeometry,
  dir: "front" | "top",
  rect: [number, number, number, number],
  minDot = 0.15,
  lift = 0.004,
) {
  const src = geo.index ? geo.toNonIndexed() : geo;
  const pos = src.getAttribute("position") as THREE.BufferAttribute;
  const out: number[] = [];
  const uv: number[] = [];
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const n = new THREE.Vector3();
  const [l, r, bot, top] = rect;
  const axis = dir === "front" ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < pos.count; i += 3) {
    a.fromBufferAttribute(pos, i);
    b.fromBufferAttribute(pos, i + 1);
    c.fromBufferAttribute(pos, i + 2);
    n.subVectors(b, a).cross(c.clone().sub(a)).normalize();
    if (n.dot(axis) < minDot) continue;
    const pu = (p: THREE.Vector3) => p.x;
    const pv = (p: THREE.Vector3) => (dir === "front" ? p.y : -p.z);
    // Keep the triangle if it overlaps the rectangle at all (big facets may have no
    // corner inside it).
    const us = [pu(a), pu(b), pu(c)];
    const vs = [pv(a), pv(b), pv(c)];
    const inside =
      Math.max(...us) >= l &&
      Math.min(...us) <= r &&
      Math.max(...vs) >= bot &&
      Math.min(...vs) <= top;
    if (!inside) continue;
    for (const p of [a, b, c]) {
      const q = p.clone().addScaledVector(n, lift);
      out.push(q.x, q.y, q.z);
      uv.push((pu(p) - l) / (r - l), (pv(p) - bot) / (top - bot));
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(out, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.computeVertexNormals();
  return g;
}

/** A decal material: pixel-art texture, cut out where transparent, flat-shaded. */
export function decalMaterial(map: THREE.Texture) {
  return new THREE.MeshLambertMaterial({
    map,
    transparent: false,
    alphaTest: 0.5,
    flatShading: true,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
  });
}

/** A tiny pixel-art canvas painter (no anti-aliasing: every pixel is solid). */
export class PixelArt {
  readonly canvas = document.createElement("canvas");
  private g: CanvasRenderingContext2D;
  constructor(
    readonly w: number,
    readonly h: number,
  ) {
    this.canvas.width = w;
    this.canvas.height = h;
    this.g = this.canvas.getContext("2d")!;
  }
  px(x: number, y: number, color: string) {
    this.g.fillStyle = color;
    this.g.fillRect(Math.round(x), Math.round(y), 1, 1);
  }
  rect(x: number, y: number, w: number, h: number, color: string) {
    this.g.fillStyle = color;
    this.g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  }
  /** Fill pixels whose centres pass a test (y down, like the canvas). */
  fill(test: (x: number, y: number) => boolean, color: string) {
    this.g.fillStyle = color;
    for (let y = 0; y < this.h; y++)
      for (let x = 0; x < this.w; x++) if (test(x + 0.5, y + 0.5)) this.g.fillRect(x, y, 1, 1);
  }
  ellipse(cx: number, cy: number, rx: number, ry: number, color: string) {
    this.fill((x, y) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1, color);
  }
  texture() {
    const t = pixelTex(this.canvas);
    // Decals stop at their edges instead of repeating.
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    return t;
  }
}

/**
 * A painted face on a head: a decal on the head's front facets whose texture is
 * swapped by key (e.g. "grin/determined"). Textures are painted on first use and kept.
 * Returns the function that shows a given face.
 */
export function paintedFace(
  head: THREE.Object3D,
  headGeo: THREE.BufferGeometry,
  rect: [number, number, number, number],
  paint: (key: string) => THREE.Texture,
) {
  const cache = new Map<string, THREE.Texture>();
  const get = (key: string) => {
    let t = cache.get(key);
    if (!t) cache.set(key, (t = paint(key)));
    return t;
  };
  const mat = decalMaterial(get("smile/open"));
  // Freeing the material frees every expression painted for it (only one is on it).
  mat.addEventListener("dispose", () => {
    for (const t of cache.values()) t.dispose();
  });
  head.add(new THREE.Mesh(decalOn(headGeo, "front", rect, 0.12), mat));
  let current = "smile/open";
  return (key: string) => {
    if (key === current) return;
    current = key;
    mat.map = get(key);
    mat.needsUpdate = true;
  };
}
