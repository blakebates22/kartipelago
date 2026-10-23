/**
 * The zipper pads' look: floating arrows. No slab, just chunky glowing chevrons sitting
 * on the road in the track's zipper colour, outlined in dark ink, scrolling forward
 * (Blake's pick from four prototypes: rune stone, lava rock, painted planks, arrows).
 *
 * A small pixel texture (32 x 64, nearest, cut out), with a second "glow" texture for
 * the bright middles. The chevrons point along the pad (toward +Z once laid flat).
 * All original artwork.
 */
import * as THREE from "three";

const TW = 32;
const TH = 64;

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

function zipperTextures(): { map: THREE.Texture; glow: THREE.Texture } {
  const c = document.createElement("canvas");
  const e = document.createElement("canvas");
  c.width = e.width = TW;
  c.height = e.height = TH;
  const g = c.getContext("2d")!;
  const ge = e.getContext("2d")!;
  ge.fillStyle = "#000000";
  ge.fillRect(0, 0, TW, TH);
  const px = (x: number, y: number, col: string, glow: string) => {
    g.fillStyle = col;
    g.fillRect(x, y, 1, 1);
    ge.fillStyle = glow;
    ge.fillRect(x, y, 1, 1);
  };
  for (let y = 0; y < TH; y++)
    for (let x = 0; x < TW; x++) {
      const k = chevron(x, y, 13);
      if (k < 0) continue;
      if (k < 0.25) px(x, y, "#3a2414", "#000000");
      else if (k < 0.6) px(x, y, "#c8c8c8", "#808080");
      else px(x, y, "#ffffff", "#ffffff");
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

/** The pad material, tinted by the track's zipper colour. */
export function zipperMaterial(zipperColor: string) {
  const { map, glow } = zipperTextures();
  return new THREE.MeshStandardMaterial({
    map,
    color: zipperColor,
    emissive: zipperColor,
    emissiveMap: glow,
    emissiveIntensity: 0.9,
    roughness: 0.8,
    transparent: true,
    alphaTest: 0.5,
    polygonOffset: true,
    polygonOffsetFactor: -4,
    polygonOffsetUnits: -8,
  });
}
