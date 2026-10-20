/**
 * How an imported track's materials are drawn: the late-90s console look.
 *
 * The Blender add-on exports ordinary glTF materials (see docs/materials.md): a small
 * repeating base colour texture, the vertex paint as COLOR_0, tint as the base colour
 * factor, glow as emissive and opacity as alpha. Here they become simple diffuse
 * (Lambert) materials: no specular highlights, no normal maps, just texture × vertex
 * colour × light, fog included.
 *
 * Water and lava animate by scrolling and rippling their texture, described by the
 * `kp_fx` material extra. The animation is purely visual: driving on water or lava is
 * the collision mesh's `kp_surface`, which this file never looks at.
 *
 * Two texture looks share the same art:
 *   authentic  soft bilinear magnification, no anisotropic sharpening (N64-like)
 *   enhanced   crisp texels up close, trilinear + anisotropic in the distance
 */
import * as THREE from "three";

export type LookMode = "authentic" | "enhanced";

/** Water/lava animation, from the `kp_fx` material extra. */
export interface MaterialFx {
  /** Texture scroll, repeats per second. */
  scrollU: number;
  scrollV: number;
  /** Looping wobble, as a fraction of a repeat, and its period in seconds. */
  wave: number;
  wavePeriod: number;
  /** The glow swelling and fading by this share (a living crystal), and its period. */
  pulse: number;
  pulsePeriod: number;
}

const num = (v: unknown, lo: number, hi: number, fallback: number) =>
  typeof v === "number" && Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : fallback;

/** The animation in a material's extras, or undefined if it doesn't move. */
export function parseFx(userData: Record<string, unknown> | undefined): MaterialFx | undefined {
  const raw = userData?.kp_fx;
  if (typeof raw !== "object" || raw === null) return undefined;
  const r = raw as Record<string, unknown>;
  const fx: MaterialFx = {
    scrollU: num(r.scroll_u, -10, 10, 0),
    scrollV: num(r.scroll_v, -10, 10, 0),
    wave: num(r.wave, 0, 1, 0),
    wavePeriod: num(r.wave_period, 0.05, 600, 4),
    pulse: num(r.pulse, 0, 1, 0),
    pulsePeriod: num(r.pulse_period, 0.1, 600, 4),
  };
  return fx.scrollU || fx.scrollV || fx.wave || fx.pulse ? fx : undefined;
}

/** A texture's offset at time `t` (seconds): steady scroll plus a small circular ripple. */
export function fxOffset(fx: MaterialFx, t: number): [number, number] {
  const a = (2 * Math.PI * t) / fx.wavePeriod;
  const wrap = (v: number) => v - Math.floor(v);
  return [
    wrap(fx.scrollU * t + fx.wave * Math.sin(a)),
    wrap(fx.scrollV * t + fx.wave * Math.cos(a)),
  ];
}

/** The glow's strength at time `t` as a share of its own (1 when steady). */
export function pulseAt(fx: MaterialFx, t: number): number {
  if (!fx.pulse) return 1;
  return 1 - fx.pulse / 2 + (fx.pulse / 2) * Math.sin((2 * Math.PI * t) / fx.pulsePeriod);
}

/** Sampler settings for each look. */
export function filterFor(mode: LookMode) {
  return mode === "authentic"
    ? {
        magFilter: THREE.LinearFilter,
        minFilter: THREE.LinearMipmapLinearFilter,
        anisotropy: 1,
      }
    : {
        magFilter: THREE.NearestFilter,
        minFilter: THREE.LinearMipmapLinearFilter,
        anisotropy: 8,
      };
}

export interface TrackMaterials {
  /** Every texture on the track (for switching the look). */
  textures: Set<THREE.Texture>;
  /** Textures that move, with their animation (and glows that pulse: their material). */
  animated: {
    texture: THREE.Texture;
    fx: MaterialFx;
    pulse?: { mat: THREE.MeshLambertMaterial; base: number };
  }[];
  setMode(mode: LookMode): void;
  /** Advance water and lava to time `t`, seconds. */
  update(t: number): void;
}

type GltfMaterial = THREE.MeshStandardMaterial & { userData: Record<string, unknown> };

/** The retro version of one glTF material. */
function toRetro(src: GltfMaterial, animated: TrackMaterials["animated"]) {
  const fx = parseFx(src.userData);
  let map = src.map;
  // A moving texture gets its own copy, so other materials sharing the image stay still.
  if (map && fx) {
    map = map.clone();
    map.needsUpdate = true;
    animated.push({ texture: map, fx });
  }
  const glows = src.emissive.r + src.emissive.g + src.emissive.b > 0;
  const mat = new THREE.MeshLambertMaterial({
    name: src.name,
    color: src.color,
    map,
    vertexColors: src.vertexColors,
    transparent: src.transparent,
    opacity: src.opacity,
    alphaTest: src.alphaTest,
    side: src.side,
    emissive: glows ? src.emissive : new THREE.Color(0),
    // Glow follows the same (scrolling) texture.
    emissiveMap: glows ? (src.emissiveMap === src.map ? map : src.emissiveMap) : null,
    emissiveIntensity: src.emissiveIntensity,
    depthWrite: !src.transparent,
  });
  mat.userData = { ...src.userData };
  if (fx?.pulse && glows) {
    const entry = animated.find((a) => a.texture === map);
    if (entry) entry.pulse = { mat, base: mat.emissiveIntensity };
  }
  return mat;
}

/**
 * Give every mesh under `root` its retro material (converted once per glTF material,
 * so shared materials stay shared) and set the look.
 */
export function prepareTrackMaterials(root: THREE.Object3D, mode: LookMode): TrackMaterials {
  const animated: TrackMaterials["animated"] = [];
  const done = new Map<THREE.Material, THREE.Material>();
  const textures = new Set<THREE.Texture>();
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const convert = (src: THREE.Material) => {
      let out = done.get(src);
      if (!out) {
        out = (src as GltfMaterial).isMeshStandardMaterial
          ? toRetro(src as GltfMaterial, animated)
          : src;
        done.set(src, out);
      }
      return out;
    };
    m.material = Array.isArray(m.material) ? m.material.map(convert) : convert(m.material);
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of mats) {
      for (const v of Object.values(mat)) if (v instanceof THREE.Texture) textures.add(v);
    }
    // See-through and glowing surfaces don't cast shadows.
    m.castShadow = mats.every((x) => !x.transparent);
    m.receiveShadow = true;
  });
  for (const src of done.keys()) if (done.get(src) !== src) src.dispose();
  const tm: TrackMaterials = {
    textures,
    animated,
    setMode(next) {
      const f = filterFor(next);
      for (const t of textures) {
        if (
          t.magFilter === f.magFilter &&
          t.minFilter === f.minFilter &&
          t.anisotropy === f.anisotropy
        )
          continue;
        t.magFilter = f.magFilter;
        t.minFilter = f.minFilter;
        t.anisotropy = f.anisotropy;
        t.needsUpdate = true;
      }
    },
    update(t) {
      for (const a of animated) {
        a.texture.offset.set(...fxOffset(a.fx, t));
        if (a.pulse) a.pulse.mat.emissiveIntensity = a.pulse.base * pulseAt(a.fx, t);
      }
    },
  };
  tm.setMode(mode);
  return tm;
}
