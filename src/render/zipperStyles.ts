/**
 * Zipper pad looks (prototypes, ?zip=1|2|3|4; 0 is the original orange chevrons, tinted
 * by each track's zipper colour).
 *
 *   1  rune stone: a carved stone slab with chevrons cut into it, glowing amber.
 *   2  lava rock: dark basalt split by white-hot chevrons and little cracks.
 *   3  painted planks: wooden boards across the road with cream chevrons painted on in
 *      tribal red, like the balloons' painted bands.
 *   4  floating arrows: no slab at all, three chunky glowing chevrons sitting on the
 *      road, in the track's zipper colour.
 *
 * Small pixel textures (32 x 64, nearest), with a second "glow" texture holding only
 * the parts that shine. The chevrons point along the pad (toward +Z once laid flat) and
 * scroll forward. All original artwork.
 */
import * as THREE from "three";

export type ZipStyle = 0 | 1 | 2 | 3 | 4;

export function zipStyle(): ZipStyle {
  const v =
    typeof location !== "undefined" ? new URLSearchParams(location.search).get("zip") : null;
  const n = Number(v);
  return n >= 1 && n <= 4 ? (n as ZipStyle) : 0;
}

const TW = 32;
const TH = 64;

function hash(x: number, y: number, s = 0) {
  const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453;
  return v - Math.floor(v);
}

/** Is (x, y) on a chevron (two per tile), and how far into its stroke (0 edge .. 1 middle)? */
function chevron(x: number, y: number, thick: number): number {
  const cx = TW / 2 - 0.5;
  for (const top of [3, 35]) {
    // The point is lower (toward +Z): y = top + 15 - |x - cx| * 1.15.
    const line = top + 15 - Math.abs(x - cx) * 1.15;
    const d = y - line;
    if (d >= 0 && d < thick && Math.abs(x - cx) < TW / 2 - 3)
      return 1 - Math.abs(d - thick / 2) / (thick / 2);
  }
  return -1;
}

export function zipperTextures(style: Exclude<ZipStyle, 0>): {
  map: THREE.Texture;
  glow: THREE.Texture;
} {
  const c = document.createElement("canvas");
  const e = document.createElement("canvas");
  c.width = e.width = TW;
  c.height = e.height = TH;
  const g = c.getContext("2d")!;
  const ge = e.getContext("2d")!;
  ge.fillStyle = "#000000";
  ge.fillRect(0, 0, TW, TH);
  const px = (x: number, y: number, col: string, glow?: string) => {
    g.fillStyle = col;
    g.fillRect(x, y, 1, 1);
    if (glow) {
      ge.fillStyle = glow;
      ge.fillRect(x, y, 1, 1);
    }
  };
  for (let y = 0; y < TH; y++)
    for (let x = 0; x < TW; x++) {
      const n = hash(x, y, style);
      const edge = x < 2 || x >= TW - 2;
      if (style === 1) {
        let col = n < 0.15 ? "#7a6e5e" : n > 0.9 ? "#a89c88" : "#8e826e";
        if (edge) col = x === 0 || x === TW - 1 ? "#3e352a" : "#b8ad94";
        const k = chevron(x, y, 11);
        if (k >= 0) {
          if (k < 0.3) px(x, y, "#3a3026");
          else if (k < 0.7) px(x, y, "#ffb02a", "#ff8a1a");
          else px(x, y, "#fff06a", "#ffe04a");
        } else px(x, y, col);
      } else if (style === 2) {
        let col = n < 0.2 ? "#1e1618" : n > 0.92 ? "#3e3034" : "#2a2024";
        if (edge) col = "#140e10";
        const k = chevron(x, y, 12);
        // Hairline cracks glowing faintly.
        const crack = Math.abs(Math.sin(x * 0.7 + y * 0.31) * 6 - (y % 16) + 8) < 0.6 && !edge;
        if (k >= 0) {
          if (k < 0.3) px(x, y, "#e8402a", "#c82a10");
          else if (k < 0.65) px(x, y, "#ffb02a", "#ff9a1a");
          else px(x, y, "#fff6c0", "#fff0a0");
        } else if (crack) px(x, y, "#a8301a", "#6a1a08");
        else px(x, y, col);
      } else if (style === 3) {
        // Boards across the pad, 8 px each, with dark gaps and the odd knot.
        const board = Math.floor(y / 8);
        let col = board % 2 ? "#a8784a" : "#966a3e";
        if (y % 8 === 7) col = "#4a2e18";
        else if (hash(x >> 2, board, 9) > 0.93) col = "#6a4424";
        if (edge) col = "#4a2e18";
        const k = chevron(x, y, 11);
        if (k >= 0) px(x, y, k < 0.35 ? "#c8302a" : "#fff3d6", k < 0.35 ? undefined : "#3a3020");
        else px(x, y, col);
      } else {
        const k = chevron(x, y, 13);
        if (k >= 0) {
          if (k < 0.25) px(x, y, "#3a2414");
          else if (k < 0.6) px(x, y, "#c8c8c8", "#808080");
          else px(x, y, "#ffffff", "#ffffff");
        }
      }
    }
  const tex = (cv: HTMLCanvasElement) => {
    const t = new THREE.CanvasTexture(cv);
    t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.NearestFilter;
    t.minFilter = THREE.NearestFilter;
    t.generateMipmaps = false;
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  };
  return { map: tex(c), glow: tex(e) };
}

/** The pad material for a style; style 4 is cut out and tinted by the zipper colour. */
export function zipperMaterial(style: Exclude<ZipStyle, 0>, zipperColor: string) {
  const { map, glow } = zipperTextures(style);
  const tinted = style === 4;
  return new THREE.MeshStandardMaterial({
    map,
    color: tinted ? zipperColor : "#ffffff",
    emissive: tinted ? zipperColor : "#ffffff",
    emissiveMap: glow,
    emissiveIntensity: tinted ? 0.9 : 0.85,
    roughness: 0.8,
    transparent: tinted,
    alphaTest: tinted ? 0.5 : 0,
    polygonOffset: true,
    polygonOffsetFactor: -4,
    polygonOffsetUnits: -8,
  });
}
