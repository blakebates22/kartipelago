/**
 * The racers' shared "hand-painted" look: one small soft texture and a couple of
 * shared materials.
 *
 * The texture is 64x64 and mostly white. It carries a gentle light-to-dark wash
 * (lighter on top, like painted-in shading) and a few faint brush blotches. It's
 * multiplied by each part's vertex colour, so every part looks softly painted
 * without any fine detail. Lambert lighting gives the smooth Gouraud look of the era,
 * rather than modern shiny materials.
 */
import * as THREE from "three";

let paint: THREE.CanvasTexture | undefined;
let shadowTex: THREE.CanvasTexture | undefined;

function rand(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), a | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function paintTexture(): THREE.CanvasTexture {
  if (paint) return paint;
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const g = canvas.getContext("2d")!;
  // Sphere UVs run top (v = 1) to bottom (v = 0): light on top, a soft darker band low.
  const wash = g.createLinearGradient(0, 0, 0, size);
  wash.addColorStop(0, "#ffffff");
  wash.addColorStop(0.55, "#f4f4f4");
  wash.addColorStop(1, "#cfcfcf");
  g.fillStyle = wash;
  g.fillRect(0, 0, size, size);
  const r = rand(11);
  for (let i = 0; i < 26; i++) {
    const x = r() * size;
    const y = r() * size;
    const rad = 3 + r() * 7;
    const light = r() < 0.5;
    const grad = g.createRadialGradient(x, y, 0, x, y, rad);
    grad.addColorStop(0, light ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.06)");
    grad.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = grad;
    g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  paint = new THREE.CanvasTexture(canvas);
  paint.colorSpace = THREE.SRGBColorSpace;
  paint.wrapS = paint.wrapT = THREE.RepeatWrapping;
  // Soft, filtered sampling (the era's bilinear look), never razor-sharp.
  paint.magFilter = THREE.LinearFilter;
  paint.minFilter = THREE.LinearMipmapLinearFilter;
  return paint;
}

/** A soft round "blob" shadow, like the era's karts cast. */
export function shadowTexture(): THREE.CanvasTexture {
  if (shadowTex) return shadowTex;
  const size = 32;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const g = canvas.getContext("2d")!;
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, "rgba(0,0,0,0.55)");
  grad.addColorStop(0.6, "rgba(0,0,0,0.4)");
  grad.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  shadowTex = new THREE.CanvasTexture(canvas);
  return shadowTex;
}

let painted: THREE.MeshLambertMaterial | undefined;
let plain: THREE.MeshLambertMaterial | undefined;

/** Vertex colours times the painted wash: bodies, karts, fur, scales. */
export function paintedMaterial() {
  painted ??= new THREE.MeshLambertMaterial({ vertexColors: true, map: paintTexture() });
  return painted;
}

/** Vertex colours only (crisp): eyes, mouths, small face details. */
export function plainMaterial() {
  plain ??= new THREE.MeshLambertMaterial({ vertexColors: true });
  return plain;
}
