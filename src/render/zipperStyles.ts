/**
 * The zipper pads' look: floating arrows. No slab, just chunky glowing chevrons sitting
 * on the road, red rims round bright yellow middles, outlined in dark ink, scrolling forward
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
      // Ink outline, a red rim, then orange into a bright yellow middle.
      if (k < 0.2) px(x, y, "#3a2414", "#000000");
      else if (k < 0.45) px(x, y, "#e8302a", "#701808");
      else if (k < 0.7) px(x, y, "#ff9a1a", "#a05008");
      else px(x, y, "#fff06a", "#fff06a");
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

/** The pad material: red and yellow arrows on every track (easy to spot on any road). */
export function zipperMaterial() {
  const { map, glow } = zipperTextures();
  return new THREE.MeshStandardMaterial({
    map,
    color: "#ffffff",
    emissive: "#ffffff",
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

/** A soft canvas gradient texture (smoothed: glows aren't pixel art). */
function gradient(w: number, h: number, paint: (g: CanvasRenderingContext2D) => void) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  paint(c.getContext("2d")!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * The glow round a pad: a soft pool of warm yellow light on the ground (brightest in the
 * middle, fading to nothing at its rounded edges) and a faint haze rising off it. Both
 * add light (additive) and never hide what's behind them.
 */
export function zipperGlowMaterials() {
  const pool = gradient(64, 64, (g) => {
    // Fades to nothing before the edges, so no outline shows (the quad stretches it).
    const r = g.createRadialGradient(32, 32, 2, 32, 32, 31);
    r.addColorStop(0, "rgba(255, 220, 90, 1)");
    r.addColorStop(0.5, "rgba(255, 200, 60, 0.45)");
    r.addColorStop(1, "rgba(255, 180, 40, 0)");
    g.fillStyle = r;
    g.fillRect(0, 0, 64, 64);
  });
  const haze = gradient(8, 64, (g) => {
    const l = g.createLinearGradient(0, 64, 0, 0);
    l.addColorStop(0, "rgba(255, 220, 90, 1)");
    l.addColorStop(0.35, "rgba(255, 210, 80, 0.4)");
    l.addColorStop(1, "rgba(255, 200, 60, 0)");
    g.fillStyle = l;
    g.fillRect(0, 0, 8, 64);
  });
  const common = {
    color: "#ffd84a",
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  } as const;
  return {
    glowMat: new THREE.MeshBasicMaterial({
      ...common,
      map: pool,
      opacity: 0.42,
      polygonOffset: true,
      polygonOffsetFactor: -3,
      polygonOffsetUnits: -6,
    }),
    hazeMat: new THREE.MeshBasicMaterial({
      ...common,
      map: haze,
      opacity: 0.16,
      side: THREE.DoubleSide,
    }),
  };
}
