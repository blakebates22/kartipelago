/**
 * Building blocks for the racers: simple rounded shapes, each painted with one vertex
 * colour, merged into a single mesh per rigid part. One shared material (soft
 * Gouraud-style Lambert lighting, a small hand-painted texture, vertex colours) means
 * a whole racer is a handful of draw calls.
 *
 * Shapes are deliberately low-poly but smooth-shaded, like late-N64 characters: strong
 * chunky silhouettes, no fine detail.
 */
import * as THREE from "three";
import { mergeGeometries, mergeVertices } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export interface Place {
  /** Position, metres. */
  p?: [number, number, number];
  /** Rotation, radians (XYZ order). */
  r?: [number, number, number];
  /** Scale. */
  s?: [number, number, number] | number;
}

const tmp = new THREE.Matrix4();
const q = new THREE.Quaternion();
const e = new THREE.Euler();
const v = new THREE.Vector3();
const sv = new THREE.Vector3();

/** Collects coloured shapes and merges them into one geometry. */
export class Parts {
  private list: THREE.BufferGeometry[] = [];

  add(geo: THREE.BufferGeometry, color: string | THREE.Color, at: Place = {}): this {
    let g = geo.index ? geo.toNonIndexed() : geo.clone();
    if (!g.getAttribute("uv")) {
      const n = g.getAttribute("position").count;
      g.setAttribute("uv", new THREE.Float32BufferAttribute(new Float32Array(n * 2), 2));
    }
    // Keep only the attributes every part shares, so they merge.
    for (const name of Object.keys(g.attributes))
      if (!["position", "normal", "uv"].includes(name)) g.deleteAttribute(name);
    const s = at.s ?? 1;
    tmp.compose(
      v.set(...(at.p ?? [0, 0, 0])),
      q.setFromEuler(e.set(...(at.r ?? [0, 0, 0]))),
      typeof s === "number" ? sv.set(s, s, s) : sv.set(...s),
    );
    g.applyMatrix4(tmp);
    const c = color instanceof THREE.Color ? color : new THREE.Color(color);
    const n = g.getAttribute("position").count;
    const cols = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      cols[i * 3] = c.r;
      cols[i * 3 + 1] = c.g;
      cols[i * 3 + 2] = c.b;
    }
    g.setAttribute("color", new THREE.BufferAttribute(cols, 3));
    if (g !== geo) geo.dispose();
    this.list.push(g);
    return this;
  }

  /** Add an already-coloured geometry (e.g. a built wheel), keeping its colours. */
  addColored(geo: THREE.BufferGeometry, at: Place = {}): this {
    const g = (geo.index ? geo.toNonIndexed() : geo.clone()).applyMatrix4(
      tmp.compose(
        v.set(...(at.p ?? [0, 0, 0])),
        q.setFromEuler(e.set(...(at.r ?? [0, 0, 0]))),
        sv.setScalar(1),
      ),
    );
    this.list.push(g);
    return this;
  }

  build(): THREE.BufferGeometry {
    const merged = mergeGeometries(this.list, false);
    for (const g of this.list) g.dispose();
    this.list = [];
    merged.computeBoundingSphere();
    return merged;
  }
}

// Low segment counts: chunky but smooth. Far-away versions are built at lower detail.
let detail = 1;
const n = (seg: number, min = 5) => Math.max(min, Math.round(seg * detail));
/** Build something at a fraction of the normal segment counts. */
export function atDetail<T>(f: number, build: () => T): T {
  const was = detail;
  detail = f;
  try {
    return build();
  } finally {
    detail = was;
  }
}
export const ball = (seg = 10) => new THREE.SphereGeometry(1, n(seg), n(seg * 0.75, 4));
export const halfBall = (seg = 10) =>
  new THREE.SphereGeometry(1, n(seg), n(seg * 0.4, 3), 0, Math.PI * 2, 0, Math.PI / 2);
export const tube = (rTop = 1, rBottom = 1, seg = 10) =>
  new THREE.CylinderGeometry(rTop, rBottom, 1, n(seg));
export const cone = (seg = 8) => new THREE.ConeGeometry(1, 1, n(seg));
export const capsule = (r: number, len: number, seg = 8) =>
  new THREE.CapsuleGeometry(r, len, 2, n(seg));
export const ring = (r: number, t: number, seg = 14) =>
  new THREE.TorusGeometry(r, t, n(6, 4), n(seg));

/**
 * A rounded slab: a side profile extruded across, with rounded edges. Used for the
 * kart body and fenders. `profile` points are (z forward, y up).
 */
export function slab(profile: [number, number][], width: number, bevel: number) {
  const shape = new THREE.Shape();
  profile.forEach(([z, y], i) => (i === 0 ? shape.moveTo(z, y) : shape.lineTo(z, y)));
  shape.closePath();
  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: Math.max(0.01, width - bevel * 2),
    bevelEnabled: true,
    bevelThickness: bevel,
    bevelSize: bevel,
    bevelSegments: 3,
    curveSegments: 8,
  });
  // Extruded along +Z; turn so the profile's first axis runs forward (+Z) and the
  // width runs across (X), centred.
  geo.translate(0, 0, -(width - bevel * 2) / 2);
  geo.rotateY(-Math.PI / 2);
  // Weld the seams so the whole slab shades smoothly, like one rounded toy part.
  geo.deleteAttribute("uv");
  geo.deleteAttribute("normal");
  const welded = mergeVertices(geo, 1e-3);
  geo.dispose();
  welded.computeVertexNormals();
  return welded;
}

/** A smooth closed outline through points (Catmull-Rom), for slab profiles. */
export function smooth(points: [number, number][], samples = 40): [number, number][] {
  const curve = new THREE.CatmullRomCurve3(
    points.map(([a, b]) => new THREE.Vector3(a, b, 0)),
    true,
    "centripetal",
  );
  return curve
    .getSpacedPoints(samples)
    .slice(0, -1)
    .map((p) => [p.x, p.y]);
}
