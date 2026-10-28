/**
 * Helpers the story dragons' designs share: skull and jaw lofts painted by position,
 * rows of teeth, pairs of horns, brows, and the head's groups.
 */
import * as THREE from "three";
import { horn, loft, type Section } from "../../racers/kit/shapes";
import { Parts, clawGeo, mix, smoothstep, type Paint, type V3 } from "../parts";

export { mix, smoothstep };

/** A smooth loft through sections (centre, half-width, half-height), many sides. */
export function skull(
  sections: { at: V3; rx: number; ry: number; sq?: number; flat?: number }[],
  sides = 22,
  steps = 4,
  caps: { start?: boolean; end?: boolean } = { end: true },
) {
  return loft(
    sections.map((s) => ({ ...s, color: "#ffffff" }) as Section),
    {
      sides: Math.min(sides, 20),
      steps: Math.min(steps, 3),
      capStart: caps.start,
      capEnd: caps.end,
    },
  );
}

/** Paint by height and side: `top` above, `side` round the middle, `under` beneath. */
export const shade =
  (top: string, side: string, under: string, mid = 0, soft = 0.6) =>
  (p: THREE.Vector3, n: THREE.Vector3): THREE.Color => {
    const c = new THREE.Color(side);
    if (n.y > 0) c.lerp(new THREE.Color(top), smoothstep(0.15, 0.15 + soft, n.y));
    else c.lerp(new THREE.Color(under), smoothstep(-0.1, -0.1 - soft, n.y));
    void mid;
    void p;
    return c;
  };

/** Teeth along a jaw's edge (left side; mirrored): from z0 to z1, `count` of them. */
export function teeth(
  parts: Parts,
  o: {
    z0: number;
    z1: number;
    count: number;
    x: (z: number) => number;
    y: (z: number) => number;
    len: (k: number) => number;
    r: number;
    down: boolean;
    color: string;
    /** Lean them forward (radians). */
    rake?: number;
  },
) {
  for (let i = 0; i < o.count; i++) {
    const k = o.count === 1 ? 0 : i / (o.count - 1);
    const z = o.z0 + (o.z1 - o.z0) * k;
    const len = o.len(k);
    const g = new THREE.ConeGeometry(o.r * (0.7 + 0.3 * len), len, 6, 1);
    g.translate(0, -len / 2, 0);
    if (!o.down) g.rotateX(Math.PI);
    parts.both(g, o.color, {
      p: [o.x(z), o.y(z), z],
      r: [o.rake ?? 0, 0, 0],
    });
  }
}

/** A pair of horns (left given; mirrored). */
export function hornPair(
  parts: Parts,
  base: V3,
  tip: V3,
  r: number,
  color: Paint,
  bend: V3 = [0, 0, 0],
  sides = 10,
) {
  parts.both(horn(base, tip, r, "#ffffff", bend, sides), color, { rep: [2, 3] });
}

/** A horn coloured from root to tip (by distance from the base). */
export const hornPaint =
  (base: V3, tipAt: V3, root: string, tip: string): Paint =>
  (p) => {
    const L = Math.hypot(tipAt[0] - base[0], tipAt[1] - base[1], tipAt[2] - base[2]);
    const d = Math.hypot(p.x - base[0], p.y - base[1], p.z - base[2]);
    return mix(root, tip, smoothstep(0.2, 1, d / L));
  };

/** A mesh of some parts. */
export const mesh = (p: Parts, m: THREE.Material) => new THREE.Mesh(p.build(), m);

/** A brow group at `at` (left; `side` -1 for the right), its ridge built by `make`. */
export function brow(
  head: THREE.Object3D,
  at: V3,
  side: number,
  make: (p: Parts, mirror: boolean) => void,
  m: THREE.Material,
) {
  const g = new THREE.Group();
  g.position.set(at[0] * side, at[1], at[2]);
  const p = new Parts();
  make(p, side < 0);
  g.add(mesh(p, m));
  head.add(g);
  return g;
}

/** A claw-ish curved spike geometry (along +y). */
export const spike = (r: number, len: number) => clawGeo(r, len);

/** A soft ellipsoid. */
export const ball = (w = 18, h = 12) => new THREE.SphereGeometry(1, w, h);

/** How far out (x) a skull's surface is at height y and depth z: for seating eyes, brows
 * and horns on it. */
export function surfaceX(
  sections: { at: V3; rx: number; ry: number; sq?: number }[],
  y: number,
  z: number,
) {
  let i = 0;
  while (i < sections.length - 2 && sections[i + 1]!.at[2] < z) i++;
  const a = sections[i]!;
  const b = sections[i + 1]!;
  const t = Math.max(0, Math.min(1, (z - a.at[2]) / (b.at[2] - a.at[2] || 1)));
  const e = t * t * (3 - 2 * t);
  const cy = a.at[1] + (b.at[1] - a.at[1]) * t;
  const rx = a.rx + (b.rx - a.rx) * e;
  const ry = a.ry + (b.ry - a.ry) * e;
  const sq = (a.sq ?? 2) + ((b.sq ?? 2) - (a.sq ?? 2)) * e;
  const k = Math.min(1, Math.abs((y - cy) / ry));
  return rx * Math.max(0, 1 - k ** sq) ** (1 / sq);
}

/** A skull's section at depth z (interpolated as the loft does, near enough). */
export function sectionAt(
  sections: { at: V3; rx: number; ry: number; sq?: number; flat?: number }[],
  z: number,
) {
  let i = 0;
  while (i < sections.length - 2 && sections[i + 1]!.at[2] < z) i++;
  const a = sections[i]!;
  const b = sections[i + 1]!;
  const t = Math.max(0, Math.min(1, (z - a.at[2]) / (b.at[2] - a.at[2] || 1)));
  const e = t * t * (3 - 2 * t);
  return {
    cy: a.at[1] + (b.at[1] - a.at[1]) * t,
    rx: a.rx + (b.rx - a.rx) * e,
    ry: a.ry + (b.ry - a.ry) * e,
    sq: (a.sq ?? 2) + ((b.sq ?? 2) - (a.sq ?? 2)) * e,
    flat: (a.flat ?? 0) + ((b.flat ?? 0) - (a.flat ?? 0)) * e,
  };
}

/** The height of a skull's underside (or top, `top`) at x (a fraction of its half-width)
 * and depth z: where its teeth hang from. */
export function surfaceY(
  sections: { at: V3; rx: number; ry: number; sq?: number; flat?: number }[],
  xf: number,
  z: number,
  top = false,
) {
  const s = sectionAt(sections, z);
  const h = s.ry * Math.max(0, 1 - Math.abs(xf) ** s.sq) ** (1 / s.sq);
  if (top) return s.cy + h * (s.flat < 0 ? 1 + s.flat : 1);
  return s.cy - h * (s.flat > 0 ? 1 - s.flat : 1);
}

/**
 * A fan of spines with a membrane between them (a frill, a tail fan, a fin): spines from
 * `bases[i]` to `tips[i]`; the membrane dips between neighbouring tips. Returns the
 * spines (skin) and the membrane (two-sided) as separate parts.
 */
export function fan(
  bases: V3[],
  tips: V3[],
  o: {
    spineR: number;
    spine: string;
    color: (i: number, along: number, across: number) => THREE.Color;
    dip?: number;
    rows?: number;
  },
) {
  const spines = new Parts();
  for (let i = 0; i < bases.length; i++)
    spines.add(horn(bases[i]!, tips[i]!, o.spineR, "#ffffff", [0, 0, 0], 6), o.spine);
  const R = o.rows ?? 4;
  const Q = 4;
  const pos: number[] = [];
  const col: number[] = [];
  const idx: number[] = [];
  const v = new THREE.Vector3();
  for (let i = 0; i < bases.length - 1; i++) {
    const b0 = new THREE.Vector3(...bases[i]!);
    const b1 = new THREE.Vector3(...bases[i + 1]!);
    const t0 = new THREE.Vector3(...tips[i]!);
    const t1 = new THREE.Vector3(...tips[i + 1]!);
    const start = pos.length / 3;
    for (let r = 0; r <= R; r++)
      for (let q = 0; q <= Q; q++) {
        const a = r / R;
        const c = q / Q;
        const dip = 1 - (o.dip ?? 0.25) * Math.sin(Math.PI * c) * a * a;
        const bx = b0.clone().lerp(b1, c);
        const tx = t0.clone().lerp(t1, c);
        v.copy(bx).lerp(tx, a * dip);
        pos.push(v.x, v.y, v.z);
        const k = o.color(i + c, a * dip, c);
        col.push(k.r, k.g, k.b);
      }
    for (let r = 0; r < R; r++)
      for (let q = 0; q < Q; q++) {
        const a = start + r * (Q + 1) + q;
        idx.push(a, a + 1, a + Q + 1, a + 1, a + Q + 2, a + Q + 1);
      }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return { spines, membrane: g };
}
