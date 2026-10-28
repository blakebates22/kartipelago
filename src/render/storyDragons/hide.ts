/**
 * A story dragon's hide, painted in code into three small textures laid over its body's
 * skin (u round the body from the belly, v along it): the colour, a height for bump
 * (scales standing out of their grooves) and a glow (embers between Cinderjaw's plates,
 * Tidewyrm's shining belly line, Lumen's markings). Painted once per design.
 *
 * Plus the little pattern helpers the designs paint with: overlapping scales, cracked
 * plates, belly bands, noise.
 */
import * as THREE from "three";
import type { LiveLoft } from "./liveLoft";
import type { DragonDesign, HideContext } from "./types";

export interface HideMaps {
  color: THREE.DataTexture;
  bump: THREE.DataTexture;
  glow: THREE.DataTexture | null;
}

const cache = new Map<string, HideMaps>();

export function hideMaps(d: DragonDesign, skin: LiveLoft, W = 160, H = 640): HideMaps {
  const hit = cache.get(d.id);
  if (hit) return hit;
  const col = new Uint8Array(W * H * 4);
  const bump = new Uint8Array(W * H * 4);
  const glow = d.glow ? new Uint8Array(W * H * 4) : null;
  const R = skin.rings;
  const L = skin.length;
  const uv1 = skin.geometry.getAttribute("uv1");
  const ring = skin.sides + 1;
  // Landmarks along the spine (distance from the tail tip).
  const n = d.spine.length;
  const sAt = (ctrlIndex: number) => skin.arc[Math.round((ctrlIndex / (n - 1)) * (R - 1))]!;
  const ctx: HideContext = {
    u: 0,
    s: 0,
    hip: sAt(d.hip),
    shoulder: sAt(d.shoulder),
    head: sAt(n - 1),
    length: L,
    cu: 0,
    cv: 0,
    up: 0,
  };
  const g = new THREE.Color();
  let ri = 0;
  for (let y = 0; y < H; y++) {
    const s = ((y + 0.5) / H) * L;
    while (ri < R - 2 && skin.arc[ri + 1]! < s) ri++;
    const a0 = skin.arc[ri]!;
    const a1 = skin.arc[ri + 1]!;
    const e = a1 > a0 ? Math.max(0, Math.min(1, (s - a0) / (a1 - a0))) : 0;
    const cv0 = uv1.getY(ri * ring);
    const cv1 = uv1.getY((ri + 1) * ring);
    ctx.s = s;
    ctx.cv = cv0 + (cv1 - cv0) * e;
    for (let x = 0; x < W; x++) {
      const u = (x + 0.5) / W;
      ctx.u = u;
      ctx.cu = u * d.cells;
      ctx.up = Math.sin(-Math.PI / 2 + u * Math.PI * 2);
      const h = d.hide(ctx);
      const o = (y * W + x) * 4;
      g.copy(h.color).convertLinearToSRGB();
      col[o] = Math.round(Math.max(0, Math.min(1, g.r)) * 255);
      col[o + 1] = Math.round(Math.max(0, Math.min(1, g.g)) * 255);
      col[o + 2] = Math.round(Math.max(0, Math.min(1, g.b)) * 255);
      col[o + 3] = 255;
      const b = Math.round(Math.max(0, Math.min(1, h.height)) * 255);
      bump[o] = bump[o + 1] = bump[o + 2] = b;
      bump[o + 3] = 255;
      if (glow) {
        const k = Math.max(0, Math.min(1, h.glow));
        g.set(d.glow!).convertLinearToSRGB();
        glow[o] = Math.round(g.r * k * 255);
        glow[o + 1] = Math.round(g.g * k * 255);
        glow[o + 2] = Math.round(g.b * k * 255);
        glow[o + 3] = 255;
      }
    }
  }
  const tex = (data: Uint8Array, srgb: boolean) => {
    const t = new THREE.DataTexture(data, W, H, THREE.RGBAFormat);
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.generateMipmaps = true;
    t.wrapS = THREE.RepeatWrapping;
    t.wrapT = THREE.ClampToEdgeWrapping;
    t.anisotropy = 4;
    t.needsUpdate = true;
    return t;
  };
  const maps: HideMaps = {
    color: tex(col, true),
    bump: tex(bump, false),
    glow: glow ? tex(glow, true) : null,
  };
  cache.set(d.id, maps);
  return maps;
}

let tile: THREE.DataTexture | undefined;
/** A small tiling height texture of scales (4 x 4 a tile) for the rigid parts' bump. */
export function partBump() {
  if (tile) return tile;
  const N = 64;
  const data = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++)
    for (let x = 0; x < N; x++) {
      const { h } = scales(((x + 0.5) / N) * 4, ((y + 0.5) / N) * 4, 4);
      const o = (y * N + x) * 4;
      data[o] = data[o + 1] = data[o + 2] = Math.round(h * 255);
      data[o + 3] = 255;
    }
  tile = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  tile.wrapS = tile.wrapT = THREE.RepeatWrapping;
  tile.magFilter = THREE.LinearFilter;
  tile.minFilter = THREE.LinearMipmapLinearFilter;
  tile.generateMipmaps = true;
  tile.channel = 1;
  tile.needsUpdate = true;
  return tile;
}

// ------------------------------------------------------------------ pattern helpers

const fract = (x: number) => x - Math.floor(x);
/** A hash of a cell: 0..1. */
export const hash = (x: number, y: number) => fract(Math.sin(x * 127.1 + y * 311.7) * 43758.5453);

/** Smooth value noise. */
export function noise(x: number, y: number) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const a = hash(ix, iy);
  const b = hash(ix + 1, iy);
  const c = hash(ix, iy + 1);
  const d = hash(ix + 1, iy + 1);
  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
}

/** Overlapping scales (each row offset by half), pointing back along the body: the
 * height (1 on a scale's crown, 0 in the grooves) and a per-scale random. The cell
 * coordinates wrap round the body every `cells`. */
export function scales(cu: number, cv: number, cells: number) {
  const row = Math.floor(cv);
  const shift = row % 2 ? 0.5 : 0;
  const cx = cu + shift;
  const col = Math.floor(cx);
  const fx = cx - col - 0.5;
  const fy = cv - row;
  // A scale: round toward the tail (low v), its crown toward the head.
  const d = Math.hypot(fx * 1.15, (fy - 0.62) * 1.0);
  const crown = Math.max(0, 1 - d / 0.62);
  // The next row's scales overlap this one's back edge.
  const h = Math.min(1, crown * 1.6) * (0.55 + 0.45 * fy);
  return { h, r: hash(((col % cells) + cells) % cells, row) };
}

/** Cracked plates: a cell pattern of irregular slabs (height 1 in a slab's middle, 0 in
 * the cracks) and a per-slab random. */
export function plates(cu: number, cv: number, cells: number) {
  const ix = Math.floor(cu);
  const iy = Math.floor(cv);
  let d1 = 9;
  let d2 = 9;
  let id = 0;
  for (let j = -1; j <= 1; j++)
    for (let i = -1; i <= 1; i++) {
      const cx = ix + i;
      const cy = iy + j;
      const wx = ((cx % cells) + cells) % cells;
      const px = cx + 0.2 + 0.6 * hash(wx, cy);
      const py = cy + 0.2 + 0.6 * hash(wx + 31, cy + 17);
      const d = Math.hypot(cu - px, (cv - py) * 1.1);
      if (d < d1) {
        d2 = d1;
        d1 = d;
        id = hash(wx + 7, cy + 3);
      } else if (d < d2) d2 = d;
    }
  const edge = d2 - d1;
  return { h: Math.min(1, edge / 0.22), r: id, edge };
}

/** Belly bands: 1 in a band's middle, 0 in the creases between (every `every` metres). */
export function bands(s: number, every: number) {
  const f = fract(s / every);
  return Math.min(1, Math.sin(Math.PI * f) * 2.2);
}

export const smoothstep = (a: number, b: number, x: number) => {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
