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
  /** Living water (0 = off): rolling waves, ripples, sun glitter and sky sheen. */
  lagoon: number;
  /** Swaying in the breeze, metres (palm fronds, banners, awnings). */
  sway: number;
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
    lagoon: num(r.lagoon, 0, 4, 0),
    sway: num(r.sway, 0, 2, 0),
  };
  return fx.scrollU || fx.scrollV || fx.wave || fx.pulse || fx.lagoon || fx.sway ? fx : undefined;
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
  /** The living water's and swaying plants' shared clock and light. */
  water: WaterUniforms;
  /** Advance water and lava to time `t`, seconds. */
  update(t: number): void;
}

type GltfMaterial = THREE.MeshStandardMaterial & { userData: Record<string, unknown> };

/** What the living-water and swaying shaders share: the clock, the sun and the sky. */
export interface WaterUniforms {
  kpTime: { value: number };
  kpSun: { value: THREE.Vector3 };
  kpSky: { value: THREE.Color };
}

// Waves: a few travelling sine waves (direction, wavelength, speed, height) summed, with
// their slopes, so the surface rolls, its normal tilts and the sun glitters off it.
const WAVES = /* glsl */ `
  vec3 kpWaves(vec2 p, float t) {
    vec3 h = vec3(0.0);
    vec4 W[5];
    W[0] = vec4(0.83, 0.55, 23.0, 0.32);
    W[1] = vec4(-0.45, 0.89, 13.0, 0.18);
    W[2] = vec4(0.98, -0.2, 7.5, 0.09);
    W[3] = vec4(-0.7, -0.71, 4.3, 0.05);
    W[4] = vec4(0.2, 0.98, 2.6, 0.03);
    for (int i = 0; i < 5; i++) {
      float k = 6.2832 / W[i].z;
      float ph = k * dot(W[i].xy, p) + t * sqrt(9.8 * k) * 0.6;
      h.x += W[i].w * sin(ph);
      h.yz += W[i].w * k * cos(ph) * W[i].xy;
    }
    return h;
  }
  float kpHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
`;

/**
 * Patch a Lambert material's shaders: living water (waves, ripples, glitter, sky sheen)
 * and/or swaying (a gentle breeze). Purely visual; collision never moves.
 */
function patchShader(mat: THREE.MeshLambertMaterial, fx: MaterialFx, u: WaterUniforms) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.kpTime = u.kpTime;
    sh.uniforms.kpSun = u.kpSun;
    sh.uniforms.kpSky = u.kpSky;
    sh.uniforms.kpLagoon = { value: fx.lagoon };
    sh.uniforms.kpSway = { value: fx.sway };
    const head = /* glsl */ `
      uniform float kpTime;
      uniform float kpLagoon;
      uniform float kpSway;
      varying vec3 vKpWorld;
      ${WAVES}
    `;
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", `#include <common>\n${head}`)
      .replace(
        "#include <begin_vertex>",
        /* glsl */ `#include <begin_vertex>
        {
          vec4 kpW = modelMatrix * vec4(transformed, 1.0);
          if (kpSway > 0.0) {
            float ph = kpW.x * 0.37 + kpW.z * 0.29;
            transformed.x += kpSway * (sin(kpTime * 1.7 + ph) + 0.4 * sin(kpTime * 3.1 + ph * 1.7));
            transformed.z += kpSway * 0.6 * cos(kpTime * 1.3 + ph);
            transformed.y += kpSway * 0.25 * sin(kpTime * 2.3 + ph * 0.7);
          }
          if (kpLagoon > 0.0) transformed.y += kpLagoon * kpWaves(kpW.xz, kpTime).x;
          vKpWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;
        }`,
      );
    sh.fragmentShader = sh.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>\n${head}\nuniform vec3 kpSun;\nuniform vec3 kpSky;`,
      )
      .replace(
        "#include <map_fragment>",
        /* glsl */ `#include <map_fragment>
        if (kpLagoon > 0.0) {
          vec2 p = vKpWorld.xz;
          float t = kpTime;
          // Bright ribbons of light rippling over it (like sunlight through the waves).
          vec2 q = p * 0.42 + vec2(t * 0.35, -t * 0.27);
          float net = abs(sin(q.x) + sin(q.y * 1.13) + sin((q.x + q.y) * 0.71 + t * 0.6));
          float caustic = 1.0 - smoothstep(0.0, 0.45, net);
          vec3 w = kpWaves(p, t);
          float crest = smoothstep(0.1, 0.45, w.x);
          diffuseColor.rgb *= 0.9 + 0.12 * kpLagoon * crest;
          diffuseColor.rgb += kpLagoon * caustic * vec3(0.10, 0.16, 0.16);
        }`,
      )
      .replace(
        "#include <opaque_fragment>",
        /* glsl */ `#include <opaque_fragment>
        if (kpLagoon > 0.0) {
          vec2 p = vKpWorld.xz;
          vec3 w = kpWaves(p, kpTime);
          // Fine ripples on top of the waves, for the glitter.
          vec2 r = vec2(sin(p.x * 1.9 + kpTime * 3.1) + sin(p.y * 2.3 - kpTime * 2.7),
                        cos(p.y * 1.7 + kpTime * 2.9) + cos(p.x * 2.1 - kpTime * 3.3)) * 0.06;
          vec3 N = normalize(vec3(-w.y - r.x, 1.0, -w.z - r.y));
          vec3 V = normalize(cameraPosition - vKpWorld);
          vec3 R = reflect(-V, N);
          float sun = pow(max(dot(R, kpSun), 0.0), 90.0);
          // Sparkles: tiny points winking on and off where the sun catches a ripple.
          vec2 cp = p * 1.3 + vec2(kpTime * 0.15, kpTime * 0.1);
          vec2 cell = floor(cp);
          float g = kpHash(cell);
          vec2 off = vec2(kpHash(cell + 7.1), kpHash(cell + 3.3)) * 0.6 + 0.2;
          float dot_ = 1.0 - smoothstep(0.04, 0.12, length(fract(cp) - off));
          float wink = max(0.0, sin(kpTime * (3.0 + 4.0 * g) + g * 60.0));
          float spark = step(0.82, g) * wink * dot_ * pow(max(dot(R, kpSun), 0.0), 6.0);
          float fres = pow(1.0 - max(V.y, 0.0), 4.0);
          gl_FragColor.rgb = mix(gl_FragColor.rgb, kpSky, clamp(fres * 0.4, 0.0, 0.45) * min(kpLagoon, 1.0));
          gl_FragColor.rgb += kpLagoon * (sun * vec3(1.0, 0.97, 0.88) * 1.3 + spark * vec3(2.2));
        }`,
      );
  };
  mat.customProgramCacheKey = () => `kp:${fx.lagoon > 0 ? 1 : 0}:${fx.sway > 0 ? 1 : 0}`;
}

/** The retro version of one glTF material. */
function toRetro(src: GltfMaterial, animated: TrackMaterials["animated"], water: WaterUniforms) {
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
  if (fx && (fx.lagoon > 0 || fx.sway > 0)) patchShader(mat, fx, water);
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
export function prepareTrackMaterials(
  root: THREE.Object3D,
  mode: LookMode,
  light: { sun?: [number, number, number]; sky?: string } = {},
): TrackMaterials {
  const animated: TrackMaterials["animated"] = [];
  const s = light.sun ?? [-0.35, 0.86, 0.38];
  const water: WaterUniforms = {
    kpTime: { value: 0 },
    kpSun: { value: new THREE.Vector3(s[0], s[1], s[2]).normalize() },
    kpSky: { value: new THREE.Color(light.sky ?? "#a8dcff") },
  };
  const done = new Map<THREE.Material, THREE.Material>();
  const textures = new Set<THREE.Texture>();
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const convert = (src: THREE.Material) => {
      let out = done.get(src);
      if (!out) {
        out = (src as GltfMaterial).isMeshStandardMaterial
          ? toRetro(src as GltfMaterial, animated, water)
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
    water,
    update(t) {
      water.kpTime.value = t;
      for (const a of animated) {
        a.texture.offset.set(...fxOffset(a.fx, t));
        if (a.pulse) a.pulse.mat.emissiveIntensity = a.pulse.base * pulseAt(a.fx, t);
      }
    },
  };
  tm.setMode(mode);
  return tm;
}
