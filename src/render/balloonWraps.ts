/**
 * The painted wrap on the balloons: cave glyphs (Blake's pick from four prototypes).
 * Two gold bands edged in ink round the balloon, and between them cream spirals and
 * three-toed footprints, with dots between, on the balloon's own colour (the rainbow
 * balloon's is white, and its material cycles through the colours).
 *
 * A small unfiltered (nearest) texture wrapped round the sphere: u goes round, v from
 * top (0) to bottom (1). All original artwork.
 */
import * as THREE from "three";
import type { BalloonColor } from "../items/inventory";

const BASE: Record<BalloonColor, string> = {
  red: "#e63946",
  blue: "#2f80ed",
  green: "#2bb24c",
  yellow: "#ffd23f",
  rainbow: "#ffffff",
};
const CREAM = "#fff3d6";
const INK = "#3a2414";
const GOLD = "#ffc42a";

const W = 64;
const H = 32;

const SPIRAL = ["..###..", ".#...#.", "#..#..#", "#.#.#.#", "#.#..#.", ".#.....", "..####."];
const FOOT = ["#...#", "#.#.#", ".#.#.", "..#..", ".###.", ".###.", "..#.."];

function wrapTexture(color: BalloonColor): THREE.Texture {
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const g = c.getContext("2d")!;
  const px = (x: number, y: number, col: string) => {
    g.fillStyle = col;
    g.fillRect(((x % W) + W) % W, y, 1, 1);
  };
  // The rainbow balloon is painted on white: its material cycles through the colours.
  const base = () => BASE[color];
  for (let x = 0; x < W; x++) {
    for (let y = 0; y < H; y++) px(x, y, base());
    for (const y of [6, 7, 24, 25]) px(x, y, GOLD);
    for (const y of [5, 8, 23, 26]) px(x, y, INK);
  }
  // Spirals and footprints, alternating round the middle, with a dot between each.
  for (let k = 0; k < 4; k++) {
    const art = k % 2 ? FOOT : SPIRAL;
    const ox = k * 16 + 4;
    art.forEach((row, j) => {
      for (let i = 0; i < row.length; i++) if (row[i] === "#") px(ox + i, 12 + j, CREAM);
    });
    for (const [dx, dy] of [
      [0, 0],
      [1, 0],
      [0, 1],
      [1, 1],
    ] as const)
      px(k * 16 + 13 + dx, 15 + dy, CREAM);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** A balloon's material: the wrap, lit, with a little glow of its own. */
export function wrapMaterial(color: BalloonColor) {
  const map = wrapTexture(color);
  return new THREE.MeshStandardMaterial({
    color: "#ffffff",
    map,
    emissive: "#ffffff",
    emissiveMap: map,
    emissiveIntensity: color === "rainbow" ? 0.3 : 0.18,
    roughness: 0.55,
  });
}
