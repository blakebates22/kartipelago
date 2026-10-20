/**
 * Small painted textures for the racers, painted in code into plain pixel buffers (no
 * canvas, so they also build in tests), and the racers' few shared materials.
 *
 * The era's look: tiny textures (16 to 64 texels a side) sampled so their texels show as
 * soft blocks, multiplied by vertex colours, lit by simple Lambert (Gouraud) lighting.
 * No shine, no normal maps.
 */
import * as THREE from "three";

export type RGBA = [number, number, number, number];

/** "#rrggbb" or "#rrggbbaa" to 0..255 components. */
export function rgba(hex: string, alpha = 255): RGBA {
  const h = hex.replace("#", "");
  const n = (i: number) => parseInt(h.slice(i, i + 2), 16);
  return [n(0), n(2), n(4), h.length >= 8 ? n(6) : alpha];
}

/** A deterministic random sequence. */
export function seeded(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), a | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * A tiny pixel-art painter. Coordinates are texels with y running down the picture
 * (like an image editor); `texture()` turns it the right way up for the GPU.
 */
export class Pix {
  readonly data: Uint8Array;
  constructor(
    readonly w: number,
    readonly h: number,
    background: string | null = null,
  ) {
    this.data = new Uint8Array(w * h * 4);
    if (background) this.rect(0, 0, w, h, background);
  }
  /** Set one texel. Colours may carry alpha ("#rrggbbaa"); partial alpha blends. */
  px(x: number, y: number, color: string | RGBA) {
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    if (xi < 0 || yi < 0 || xi >= this.w || yi >= this.h) return;
    const c = typeof color === "string" ? rgba(color) : color;
    const i = (yi * this.w + xi) * 4;
    const a = c[3] / 255;
    if (a >= 1) {
      this.data.set(c, i);
      return;
    }
    for (let k = 0; k < 3; k++)
      this.data[i + k] = Math.round(this.data[i + k]! * (1 - a) + c[k]! * a);
    this.data[i + 3] = Math.max(this.data[i + 3]!, c[3]);
  }
  /** Fill the texels whose centres pass a test. */
  fill(
    test: (x: number, y: number) => boolean,
    color: string | ((x: number, y: number) => string),
  ) {
    for (let y = 0; y < this.h; y++)
      for (let x = 0; x < this.w; x++)
        if (test(x + 0.5, y + 0.5))
          this.px(x, y, typeof color === "string" ? color : color(x + 0.5, y + 0.5));
  }
  rect(x: number, y: number, w: number, h: number, color: string) {
    this.fill((px, py) => px >= x && px < x + w && py >= y && py < y + h, color);
  }
  ellipse(cx: number, cy: number, rx: number, ry: number, color: string) {
    this.fill((x, y) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1, color);
  }
  /** A thick line from (x0, y0) to (x1, y1). */
  line(x0: number, y0: number, x1: number, y1: number, width: number, color: string) {
    const dx = x1 - x0;
    const dy = y1 - y0;
    const len2 = dx * dx + dy * dy || 1;
    this.fill((x, y) => {
      const t = Math.max(0, Math.min(1, ((x - x0) * dx + (y - y0) * dy) / len2));
      return Math.hypot(x - (x0 + dx * t), y - (y0 + dy * t)) <= width / 2;
    }, color);
  }
  /** Lighten (k > 0) or darken (k < 0) every texel a little at random: hand-painted grain. */
  grain(amount: number, seed = 1) {
    const r = seeded(seed);
    for (let i = 0; i < this.w * this.h; i++) {
      const k = 1 + (r() - 0.5) * 2 * amount;
      for (let c = 0; c < 3; c++)
        this.data[i * 4 + c] = Math.max(0, Math.min(255, Math.round(this.data[i * 4 + c]! * k)));
    }
  }
  /** The texture, nearest-neighbour sampled so texels show as soft blocks. */
  texture(wrap = false): THREE.DataTexture {
    // Flip so row 0 of the picture is the top (v = 1).
    const flipped = new Uint8Array(this.data.length);
    const row = this.w * 4;
    for (let y = 0; y < this.h; y++)
      flipped.set(this.data.subarray(y * row, (y + 1) * row), (this.h - 1 - y) * row);
    const t = new THREE.DataTexture(flipped, this.w, this.h, THREE.RGBAFormat);
    t.colorSpace = THREE.SRGBColorSpace;
    t.magFilter = THREE.NearestFilter;
    t.minFilter = THREE.NearestMipmapLinearFilter;
    t.generateMipmaps = true;
    t.wrapS = t.wrapT = wrap ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
    t.needsUpdate = true;
    return t;
  }
}

let grain: THREE.DataTexture | undefined;
/** 16x16 near-white texels with gentle variation, multiplied over every vertex colour. */
export function grainTexture() {
  if (grain) return grain;
  const p = new Pix(16, 16, "#ffffff");
  // Lighter at the top of each tile (a painted-in highlight), with soft noise.
  const r = seeded(5);
  p.fill(
    () => true,
    (_x, y) => {
      const v = Math.round(255 * (0.9 + r() * 0.1 - (y / 16) * 0.05));
      const h = v.toString(16).padStart(2, "0");
      return `#${h}${h}${h}`;
    },
  );
  grain = p.texture(true);
  return grain;
}

let shadowTex: THREE.DataTexture | undefined;
/** A soft round blob shadow. */
export function shadowTexture() {
  if (shadowTex) return shadowTex;
  const p = new Pix(32, 32);
  p.fill(
    () => true,
    (x, y) => {
      const d = Math.hypot(x - 16, y - 16) / 16;
      const a = Math.round(
        255 * Math.max(0, Math.min(0.55, 0.55 * (1 - Math.max(0, d - 0.55) / 0.45))),
      );
      return `#000000${a.toString(16).padStart(2, "0")}`;
    },
  );
  shadowTex = p.texture();
  shadowTex.magFilter = THREE.LinearFilter;
  shadowTex.minFilter = THREE.LinearFilter;
  shadowTex.generateMipmaps = false;
  return shadowTex;
}

let skin: THREE.MeshLambertMaterial | undefined;
let facet: THREE.MeshLambertMaterial | undefined;

/**
 * Characters: smooth (Gouraud) shading over low-poly shapes, like the era's mascots.
 * The silhouettes stay faceted; the light rolls softly across them.
 */
export function skinMaterial() {
  skin ??= new THREE.MeshLambertMaterial({ vertexColors: true, map: grainTexture() });
  return skin;
}

/** Karts and hard props: flat-shaded facets, like painted wooden toys. */
export function facetMaterial() {
  facet ??= new THREE.MeshLambertMaterial({
    vertexColors: true,
    flatShading: true,
    map: grainTexture(),
  });
  return facet;
}

/** A painted decal (emblems, wing membranes): cut out where transparent. */
export function decalMaterial(
  map: THREE.Texture,
  opts: { flat?: boolean; doubleSided?: boolean } = {},
) {
  return new THREE.MeshLambertMaterial({
    map,
    alphaTest: 0.5,
    flatShading: opts.flat ?? true,
    side: opts.doubleSided ? THREE.DoubleSide : THREE.FrontSide,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
  });
}

/** A painted texture on a shape of its own (wing membranes): vertex colours times the texture. */
export function paintedMaterial(map: THREE.Texture, doubleSided = false) {
  return new THREE.MeshLambertMaterial({
    map,
    vertexColors: true,
    side: doubleSided ? THREE.DoubleSide : THREE.FrontSide,
  });
}
