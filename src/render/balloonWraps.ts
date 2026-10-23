/**
 * The painted wraps on the balloons, in colour (prototypes, ?wrap=1|2|3|4; 0 is the
 * original grey cave-painting marks that only darken the balloon's colour).
 *
 *   1  painted bands: a cream zigzag band edged in ink, accent-colour dots, cream
 *      triangles round the top, like tribal body paint.
 *   2  hot-air gores: eight panels alternating the balloon's colour and a lighter tint,
 *      a cream band with an accent zigzag round the middle, a gold crown.
 *   3  cave glyphs: two gold bands, between them cream spirals and three-toed
 *      footprints outlined in ink.
 *   4  sunburst: rays from the top in two tints with an accent between, and a band of
 *      chequers round the middle.
 *
 * Each is a small unfiltered (nearest) texture wrapped round the sphere: u goes round,
 * v from top (0) to bottom (1). All original artwork.
 */
import * as THREE from "three";
import type { BalloonColor } from "../items/inventory";

export type WrapStyle = 0 | 1 | 2 | 3 | 4;

export function wrapStyle(): WrapStyle {
  const v =
    typeof location !== "undefined" ? new URLSearchParams(location.search).get("wrap") : null;
  const n = Number(v);
  return n >= 1 && n <= 4 ? (n as WrapStyle) : 0;
}

/** Per balloon: the base, a lighter tint, a contrasting accent. */
const PAINT: Record<BalloonColor, { base: string; light: string; accent: string }> = {
  red: { base: "#e63946", light: "#ff7a6a", accent: "#ffd23f" },
  blue: { base: "#2f80ed", light: "#6ab4ff", accent: "#ff9a2a" },
  green: { base: "#2bb24c", light: "#7ade6a", accent: "#ffe24a" },
  yellow: { base: "#ffd23f", light: "#fff08a", accent: "#e2453a" },
  rainbow: { base: "#ff6ae0", light: "#ffffff", accent: "#5ad8ff" },
};
const CREAM = "#fff3d6";
const INK = "#3a2414";
const GOLD = "#ffc42a";
const RAINBOW = ["#ff5a4a", "#ffb02a", "#ffe24a", "#5ade5a", "#4ab4ff", "#9a6aff"];

const W = 64;
const H = 32;

export function wrapTexture(style: Exclude<WrapStyle, 0>, color: BalloonColor): THREE.Texture {
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const g = c.getContext("2d")!;
  const p = PAINT[color];
  const rainbow = color === "rainbow";
  const px = (x: number, y: number, col: string) => {
    g.fillStyle = col;
    g.fillRect(((x % W) + W) % W, y, 1, 1);
  };
  /** The balloon's colour at column x (the rainbow balloon cycles round). */
  const base = (x: number) => (rainbow ? RAINBOW[Math.floor((x / W) * 6) % 6]! : p.base);
  for (let x = 0; x < W; x++) for (let y = 0; y < H; y++) px(x, y, base(x));

  if (style === 1) {
    for (let x = 0; x < W; x++) {
      const z = Math.abs((x % 8) - 4);
      px(x, 12, INK);
      px(x, 21, INK);
      for (let y = 13; y < 21; y++) px(x, y, CREAM);
      px(x, 14 + z, INK);
      px(x, 15 + z, p.accent);
      px(x, 16 + z, INK);
    }
    for (let x = 1; x < W; x += 6)
      for (const y of [7, 25])
        for (const [dx, dy] of [
          [0, 0],
          [1, 0],
          [0, 1],
          [1, 1],
        ])
          px(x + dx!, y + dy!, p.accent);
    for (let x = 0; x < W; x += 8)
      for (let r = 0; r < 3; r++) for (let k = -r; k <= r; k++) px(x + 4 + k, 2 + r, CREAM);
  } else if (style === 2) {
    for (let x = 0; x < W; x++) {
      const gore = Math.floor(x / 8) % 2;
      for (let y = 0; y < H; y++) if (gore) px(x, y, rainbow ? "#ffffff" : p.light);
      if (x % 8 === 0) for (let y = 0; y < H; y++) px(x, y, INK);
      for (let y = 0; y < 3; y++) px(x, y, GOLD);
      px(x, 3, INK);
      px(x, 13, INK);
      px(x, 19, INK);
      for (let y = 14; y < 19; y++) px(x, y, CREAM);
      const z = Math.abs((x % 6) - 3);
      px(x, 15 + Math.min(2, z), p.accent);
    }
  } else if (style === 3) {
    for (let x = 0; x < W; x++) {
      for (const y of [6, 7, 24, 25]) px(x, y, GOLD);
      px(x, 5, INK);
      px(x, 8, INK);
      px(x, 23, INK);
      px(x, 26, INK);
    }
    // Spirals and footprints, alternating round the middle.
    const spiral = ["..###..", ".#...#.", "#..#..#", "#.#.#.#", "#.#..#.", ".#.....", "..####."];
    const foot = ["#...#", "#.#.#", ".#.#.", "..#..", ".###.", ".###.", "..#.."];
    for (let k = 0; k < 4; k++) {
      const art = k % 2 ? foot : spiral;
      const ox = k * 16 + 4;
      art.forEach((row, j) => {
        for (let i = 0; i < row.length; i++) if (row[i] === "#") px(ox + i, 12 + j, CREAM);
      });
    }
  } else {
    for (let x = 0; x < W; x++) {
      const ray = Math.floor(x / 4) % 3;
      for (let y = 0; y < 12; y++) {
        // Rays narrow toward the top.
        if (y < 12 - (x % 4) * 3) {
          const col = ray === 0 ? (rainbow ? "#ffffff" : p.light) : ray === 1 ? base(x) : p.accent;
          px(x, y, col);
        }
      }
      for (let y = 14; y < 20; y++) {
        const ch = (Math.floor(x / 3) + Math.floor((y - 14) / 3)) % 2;
        px(x, y, ch ? CREAM : INK);
      }
      px(x, 13, GOLD);
      px(x, 20, GOLD);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** A balloon's material for a wrap style. */
export function wrapMaterial(style: Exclude<WrapStyle, 0>, color: BalloonColor) {
  const map = wrapTexture(style, color);
  return new THREE.MeshStandardMaterial({
    color: "#ffffff",
    map,
    emissive: "#ffffff",
    emissiveMap: map,
    emissiveIntensity: color === "rainbow" ? 0.3 : 0.18,
    roughness: 0.55,
  });
}
