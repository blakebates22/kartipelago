/**
 * Shared bits for racers and karts: leaves, packs, bedrolls, straps, painted emblems.
 * Each is built from the kit's shapes, so any racer can borrow them.
 */
import * as THREE from "three";
import { Build, box, card, cyl, ellipsoid, loft, type ColorLike, type V3 } from "./shapes";
import { Pix, decalMaterial } from "./paint";

/** A tropical leaf card (both faces), base at the origin, pointing along +Y. */
export function leaf(length: number, width: number, color: string, rib: string) {
  const pts: [number, number][] = [];
  const n = 8;
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    pts.push([Math.sin(t * Math.PI) * width * (1 - t * 0.35), t * length]);
  }
  for (let i = n - 1; i > 0; i--) {
    const t = i / n;
    pts.push([-Math.sin(t * Math.PI) * width * (1 - t * 0.35), t * length]);
  }
  const b = new Build().add(card(pts), (p) =>
    new THREE.Color(color).lerp(
      new THREE.Color(rib),
      Math.max(0, 1 - Math.abs(p.x) / (width * 0.25)) * 0.6,
    ),
  );
  return b.build();
}

/**
 * A feather card (both faces), base at the origin, pointing along +Y: slim, pointed,
 * shading from `base` at the root to `tip`, a dark band across near the tip.
 */
export function feather(length: number, width: number, base: string, tip: string, band?: string) {
  const pts: [number, number][] = [];
  const n = 6;
  const half = (t: number) =>
    Math.sin(Math.min(1, t * 1.3) * Math.PI * 0.75 + 0.2) * width * (1 - t * 0.5);
  for (let i = 0; i <= n; i++) pts.push([half(i / n), (i / n) * length]);
  for (let i = n - 1; i > 0; i--) pts.push([-half(i / n), (i / n) * length]);
  const a = new THREE.Color(base);
  const b = new THREE.Color(tip);
  const k = band ? new THREE.Color(band) : null;
  return new Build()
    .add(card(pts), (p) => {
      const t = p.y / length;
      if (k && t > 0.62 && t < 0.72) return k;
      return a.clone().lerp(b, Math.min(1, Math.max(0, (t - 0.2) * 1.6)));
    })
    .build();
}

/** A rounded backpack with a flap, a pocket and buckles, its back against +Z. */
export function backpack(
  w: number,
  h: number,
  d: number,
  c: { bag: string; flap: string; buckle: string },
) {
  return new Build()
    .add(box(w, h, d, d * 0.35), c.bag)
    .add(box(w * 1.02, h * 0.36, d * 1.06, d * 0.3), c.flap, { p: [0, h * 0.34, -d * 0.03] })
    .add(box(w * 0.62, h * 0.34, d * 0.4, d * 0.18), c.flap, { p: [0, -h * 0.16, -d * 0.55] })
    .add(box(w * 0.12, h * 0.1, d * 0.12, 0.01), c.buckle, { p: [w * 0.2, h * 0.12, -d * 0.55] })
    .add(box(w * 0.12, h * 0.1, d * 0.12, 0.01), c.buckle, { p: [-w * 0.2, h * 0.12, -d * 0.55] })
    .build();
}

/** A rolled bedroll lying across (along X), with two straps. */
export function bedroll(len: number, r: number, c: { roll: string; strap: string; end?: string }) {
  const b = new Build()
    .add(cyl(r, r, len, 9), c.roll, { r: [0, 0, Math.PI / 2] })
    .add(cyl(r * 0.7, r * 0.7, len + 0.01, 9), c.end ?? c.strap, { r: [0, 0, Math.PI / 2] });
  for (const s of [-0.3, 0.3])
    b.add(cyl(r * 1.08, r * 1.08, len * 0.08, 9), c.strap, {
      p: [len * s, 0, 0],
      r: [0, 0, Math.PI / 2],
    });
  return b.build();
}

/** A strap: a thin band following points (over a shoulder, round a bag). */
export function strap(points: V3[], width: number, thick: number, color: ColorLike) {
  return loft(
    points.map((at) => ({ at, rx: width, ry: thick, color, sq: 4 })),
    { sides: 4, phase: Math.PI / 4, up: [0, 0, 1] },
  );
}

/** Aviator goggles: two round lenses in a band (the band runs round the head). */
export function goggles(
  c: { frame: string; lens: string; glint: string },
  spread: number,
  r: number,
) {
  const b = new Build();
  for (const s of [1, -1]) {
    b.add(new THREE.TorusGeometry(r, r * 0.3, 5, 10), c.frame, { p: [s * spread, 0, 0] });
    b.add(ellipsoid(9, 6), c.lens, {
      p: [s * spread, 0, -r * 0.05],
      s: [r * 0.9, r * 0.9, r * 0.35],
    });
    b.add(ellipsoid(5, 4), c.glint, {
      p: [s * spread + r * 0.3, r * 0.3, r * 0.25],
      s: [r * 0.22, r * 0.18, r * 0.05],
    });
  }
  b.add(box(spread * 0.6, r * 0.3, r * 0.3, 0.01), c.frame);
  return b.build();
}

// ------------------------------------------------------------------ emblems

export type Emblem = "palm" | "footprint" | "spiral" | "wing" | "claw" | "fang" | "flower" | "leaf";

/** Paint a kart emblem (32x32): a symbol on a disc, with an outline. */
export function emblemTexture(kind: Emblem, c: { disc: string; ink: string; rim: string }) {
  const p = new Pix(32, 32);
  p.ellipse(16, 16, 15.5, 15.5, c.rim);
  p.ellipse(16, 16, 13.5, 13.5, c.disc);
  if (kind === "palm") {
    // A palm: a curved trunk and five fronds.
    p.line(16, 27, 15, 15, 2.6, c.ink);
    for (const [x, y] of [
      [6, 12],
      [9, 7],
      [16, 5],
      [23, 7],
      [26, 13],
    ])
      p.line(15.5, 14, x!, y!, 3, c.ink);
    p.ellipse(15.5, 14, 3, 2.4, c.ink);
  } else if (kind === "footprint") {
    // A three-toed dinosaur footprint.
    p.ellipse(16, 20, 5.5, 5, c.ink);
    for (const [x, y, a] of [
      [9, 10, -0.5],
      [16, 7, 0],
      [23, 10, 0.5],
    ]) {
      p.line(16, 17, x!, y!, 4, c.ink);
      p.ellipse(x! + Math.sin(a!) * 1, y! - 1, 2.4, 2.8, c.ink);
    }
  } else if (kind === "spiral") {
    // A seashell spiral, drawn as a thick line winding out.
    for (let t = 0; t < 1; t += 0.002) {
      const a = t * Math.PI * 4.2;
      const r = 1.2 + t * 10.8;
      const w = 1.3 + t * 0.9;
      p.ellipse(16 + Math.cos(a) * r, 16 + Math.sin(a) * r, w, w, c.ink);
    }
  } else if (kind === "claw") {
    // Three claw slashes, curving down to the right.
    for (const dx of [-6, 0, 6])
      for (let t = 0; t <= 1; t += 0.02) {
        const x = 11 + dx + t * 9;
        const y = 6 + t * 19 + Math.sin(t * Math.PI) * -2;
        const w = 2.4 * (1 - t * 0.75) + 0.4;
        p.ellipse(x, y, w, w, c.ink);
      }
  } else if (kind === "fang") {
    // A big curved fang.
    p.fill((x, y) => {
      const t = (y - 5) / 22;
      if (t < 0 || t > 1) return false;
      const cx = 15 + t * t * 4;
      return Math.abs(x - cx) <= 6.5 * (1 - t) + 0.6;
    }, c.ink);
  } else if (kind === "flower") {
    // A five-petal island flower.
    for (let k = 0; k < 5; k++) {
      const a = -Math.PI / 2 + (k * Math.PI * 2) / 5;
      p.ellipse(16 + Math.cos(a) * 6.5, 16 + Math.sin(a) * 6.5, 4.6, 4.6, c.ink);
    }
    p.ellipse(16, 16, 3, 3, c.disc);
  } else if (kind === "leaf") {
    // A broad leaf on a stem, its veins showing.
    p.fill((x, y) => {
      const t = (y - 5) / 20;
      if (t < 0 || t > 1) return false;
      return Math.abs(x - 16) <= Math.sin(t * Math.PI) * 8.5;
    }, c.ink);
    p.line(16, 25, 16, 29, 2, c.ink);
    p.line(16, 8, 16, 25, 1.2, c.disc);
    for (const y of [12, 16, 20]) {
      p.line(16, y + 2, 11, y - 1, 1, c.disc);
      p.line(16, y + 2, 21, y - 1, 1, c.disc);
    }
  } else {
    // A swept wing: three feathers fanning back from a point.
    for (const [len, dy, w] of [
      [21, -6, 4],
      [18, 0, 3.6],
      [14, 6, 3.2],
    ])
      p.fill((x, y) => {
        const t = (x - 5) / len!;
        if (t < 0 || t > 1) return false;
        const cy = 16 + dy! * t - (1 - t) * 1;
        return Math.abs(y - cy) <= w! * (1 - t * 0.7) * 0.5 + 0.6;
      }, c.ink);
    p.ellipse(6, 15, 2.6, 2.6, c.ink);
  }
  return p.texture();
}

/** An emblem as a little sticker: a disc facing +Z (place it on the kart's nose). */
export function emblemMesh(
  kind: Emblem,
  c: { disc: string; ink: string; rim: string },
  size: number,
) {
  const geo = new THREE.CircleGeometry(size / 2, 16);
  const mesh = new THREE.Mesh(geo, decalMaterial(emblemTexture(kind, c)));
  mesh.name = `emblem ${kind}`;
  return mesh;
}
