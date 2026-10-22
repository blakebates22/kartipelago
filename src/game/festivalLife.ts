/**
 * Celestial Dragon Festival's fireworks, lanterns and observatory (game/festival.ts has
 * the rules): the city's rockets going up all night, the set pieces as you reach their
 * landmarks, the sky lanterns rising, the observatory's great golden rings turning and
 * the flash of each burst lighting the kingdom. Created by game/hazards.ts; nothing
 * here touches a kart.
 *
 * Cheap enough for a browser at the grand finale's peak: every star of every firework is
 * one point in one pooled buffer, and the GPU works out where each is from when and where
 * it was fired (the CPU only writes a star once, when it's born, and only the stretch of
 * the buffer it wrote). Rockets are a short list on the CPU, which drops embers behind
 * them. The lanterns are one more set of points animated entirely on the GPU. The flash
 * is a single hemisphere light. Stars never write depth (they're glows, not things) and
 * fog never hides them.
 */
import * as THREE from "three";
import type { Sfx } from "../audio/sfx";
import type { Track } from "../world/track";
import {
  ambientAt,
  festivalLevel,
  festivalStage,
  hash01,
  lanternCount,
  orient,
  parseFestival,
  patternCount,
  patternLife,
  patternPoints,
  piecesDue,
  TICK,
  type FestivalConfig,
  type Pattern,
  type SetPiece,
  type Stage,
  type V3,
} from "./festival";
import { nearestSample } from "./isles";

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

export interface FestivalLife {
  render(t: number, dt: number, listener: { x: number; y: number; z: number }): void;
  /** The festival's stage now (1: opening, 2: intensifying, 3: grand finale). */
  stage(): Stage;
  /** How festive it is now (0..1). */
  level(): number;
  /** Stars alive right now (tests, the debug HUD). */
  readonly live: number;
  /** Set pieces fired so far, by id (tests). */
  readonly fired: string[];
  /** Fire a set piece now, by id (tools, tests); false if there's no such piece. */
  fire(id: string, listener: { x: number; y: number; z: number }): boolean;
  dispose(): void;
}

export function hasFestivalLife(entities: unknown[]): boolean {
  return entities.some((e) => isObj(e) && e.type === "festival");
}

/** Stars in the pool (the grand finale's peak stays well under it). */
export const POOL = 24000;
const LANTERNS = 700;
const GRAVITY = 9;
const FUSE = 1.9;

// Particle kinds (the shader's switch): 0 star, 1 willow, 2 glitter, 3 shape, 4 ember,
// 5 rocket head, 6 constellation star.
const VERT = /* glsl */ `
  attribute vec3 aVel;
  attribute vec3 aColor;
  attribute vec4 aInfo;
  uniform float uTime;
  uniform float uScale;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    float kind = floor(aInfo.w + 0.001);
    float seed = fract(aInfo.w);
    float t = uTime - aInfo.x;
    float life = aInfo.y;
    if (t < 0.0 || t > life) {
      gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
      gl_PointSize = 0.0;
      vColor = vec3(0.0);
      vAlpha = 0.0;
      return;
    }
    float u = t / life;
    vec3 p = position;
    if (kind == 5.0) {
      p += aVel * t + vec3(0.0, -0.5 * ${GRAVITY.toFixed(1)} * t * t, 0.0);
    } else {
      float k = kind == 3.0 ? 2.6 : (kind == 1.0 ? 1.6 : (kind == 6.0 ? 3.0 : (kind == 4.0 ? 3.5 : 2.3)));
      p += aVel * ((1.0 - exp(-k * t)) / k);
      float droop = kind == 1.0 ? 4.2 : (kind == 4.0 ? 1.5 : (kind == 2.0 ? 1.4 : 2.0));
      if (kind == 3.0 || kind == 6.0) droop = 0.0;
      p.y -= 0.5 * droop * t * t;
      if (kind == 3.0) p.y -= 1.5 * max(0.0, t - life * 0.6) * max(0.0, t - life * 0.6);
    }
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    float fade = smoothstep(0.0, 0.04, t) * (1.0 - smoothstep(kind == 3.0 || kind == 6.0 ? 0.72 : 0.55, 1.0, u));
    if (kind == 2.0) fade *= step(0.4, fract(sin(floor(t * 17.0) * 12.9898 + seed * 78.233) * 43758.5453));
    if (kind == 6.0) fade *= 0.7 + 0.3 * sin(t * 2.7 + seed * 40.0);
    vec3 c = mix(vec3(1.0), aColor, smoothstep(0.0, 0.16, t));
    if (kind == 1.0) c = mix(c, vec3(1.0, 0.42, 0.1), smoothstep(0.35, 1.0, u));
    vColor = c;
    vAlpha = fade;
    float size = aInfo.z * (kind == 4.0 ? 1.0 - u * 0.7 : 1.0 - u * 0.35);
    gl_PointSize = clamp(size * uScale / max(1.0, -mv.z), 1.5, 90.0);
  }
`;

const FRAG = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    vec2 d = gl_PointCoord - 0.5;
    float r = length(d) * 2.0;
    if (r > 1.0) discard;
    float a = (1.0 - r);
    a *= a;
    float core = smoothstep(0.4, 0.0, r);
    gl_FragColor = vec4((vColor * a + vec3(core) * 0.8) * vAlpha, 1.0);
  }
`;

const LANTERN_VERT = /* glsl */ `
  attribute vec3 aSeed;
  attribute float aIndex;
  uniform float uTime;
  uniform float uActive;
  uniform float uRise;
  uniform float uScale;
  varying float vAlpha;
  varying float vFlick;
  void main() {
    float on = clamp(uActive - aIndex, 0.0, 1.0);
    float ph = fract(aSeed.x + uTime * aSeed.y / uRise);
    vec3 p = position;
    p.y += ph * uRise;
    p.x += sin(uTime * 0.21 + aSeed.z * 6.283) * 14.0 * ph;
    p.z += cos(uTime * 0.17 + aSeed.z * 4.1) * 14.0 * ph;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    vAlpha = on * smoothstep(0.0, 0.04, ph) * (1.0 - smoothstep(0.7, 1.0, ph));
    vFlick = 0.85 + 0.15 * sin(uTime * 9.0 + aSeed.z * 50.0);
    gl_PointSize = clamp(2.2 * uScale / max(1.0, -mv.z), 1.0, 22.0) * (on > 0.0 ? 1.0 : 0.0);
  }
`;

const LANTERN_FRAG = /* glsl */ `
  varying float vAlpha;
  varying float vFlick;
  void main() {
    vec2 d = gl_PointCoord - 0.5;
    // A paper lantern: a rounded box, brighter in the middle.
    float box = max(abs(d.x) * 1.5, abs(d.y) * 1.15);
    if (box > 0.5) discard;
    float k = 1.0 - box * 2.0;
    vec3 c = mix(vec3(1.0, 0.3, 0.12), vec3(1.0, 0.86, 0.5), k) * vFlick;
    gl_FragColor = vec4(c * (0.35 + 0.65 * k) * vAlpha, 1.0);
  }
`;

interface Rocket {
  born: number;
  /** When it bursts (or, for a comet, fades). */
  until: number;
  o: V3;
  v: V3;
  emitIn: number;
  burst?: {
    pattern: Pattern;
    size: number;
    colors: string[];
    yaw: number;
    tilt: number;
    seed: number;
  };
  comet: boolean;
  color: THREE.Color;
}

const tmpColor = new THREE.Color();

export function createFestivalLife(opts: {
  group: THREE.Group;
  entities: unknown[];
  track: Track;
  sfx?: Sfx;
  volume: () => number;
  clock: () => number;
  /** The racer's lap (the festival follows yours), if there's a race. */
  lap?: () => { lap: number; laps: number; finished: boolean } | undefined;
  quiet?: boolean;
  headless?: boolean;
}): FestivalLife {
  let cfg: FestivalConfig = { length: 1, sites: [], pieces: [], lanterns: [] };
  for (const e of opts.entities) if (isObj(e) && e.type === "festival") cfg = parseFestival(e);
  const { group } = opts;

  // ---- the star pool
  const pos = new Float32Array(POOL * 3);
  const vel = new Float32Array(POOL * 3);
  const col = new Float32Array(POOL * 3);
  const info = new Float32Array(POOL * 4);
  for (let i = 0; i < POOL; i++) info[i * 4 + 1] = -1; // dead
  const geo = new THREE.BufferGeometry();
  const attrs = {
    position: new THREE.BufferAttribute(pos, 3),
    aVel: new THREE.BufferAttribute(vel, 3),
    aColor: new THREE.BufferAttribute(col, 3),
    aInfo: new THREE.BufferAttribute(info, 4),
  };
  for (const [k, a] of Object.entries(attrs)) {
    a.setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute(k, a);
  }
  geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
  const uniforms = { uTime: { value: 0 }, uScale: { value: 500 } };
  const mat = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: VERT,
    fragmentShader: FRAG,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    fog: false,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.renderOrder = 5;
  const setScale = (
    renderer: THREE.WebGLRenderer,
    _s: THREE.Scene,
    camera: THREE.Camera,
    u: { uScale: { value: number } },
  ) => {
    const h = renderer.getDrawingBufferSize(new THREE.Vector2()).y;
    const fov = (camera as THREE.PerspectiveCamera).fov ?? 60;
    u.uScale.value = h / (2 * Math.tan((fov * Math.PI) / 180 / 2));
  };
  points.onBeforeRender = (r, s, c) => setScale(r, s, c, uniforms);
  if (!opts.headless) group.add(points);

  let head = 0;
  const ranges: [number, number][] = [];
  let rangeStart = -1;
  let rangeEnd = -1;
  let fxTime = 0;

  function flushRange() {
    if (rangeStart >= 0) ranges.push([rangeStart, rangeEnd]);
    rangeStart = rangeEnd = -1;
  }

  function star(
    o: V3,
    v: V3,
    color: THREE.Color,
    life: number,
    size: number,
    kind: number,
    seed: number,
    delay = 0,
  ) {
    const i = head;
    head = (head + 1) % POOL;
    if (i === 0) flushRange();
    if (rangeStart < 0) rangeStart = i;
    rangeEnd = i;
    pos[i * 3] = o.x;
    pos[i * 3 + 1] = o.y;
    pos[i * 3 + 2] = o.z;
    vel[i * 3] = v.x;
    vel[i * 3 + 1] = v.y;
    vel[i * 3 + 2] = v.z;
    col[i * 3] = color.r;
    col[i * 3 + 1] = color.g;
    col[i * 3 + 2] = color.b;
    info[i * 4] = fxTime + delay;
    info[i * 4 + 1] = life;
    info[i * 4 + 2] = size;
    info[i * 4 + 3] = kind + Math.min(0.999, Math.max(0, seed));
  }

  function upload() {
    flushRange();
    if (!ranges.length) return;
    for (const [k, a] of Object.entries(attrs)) {
      const n = k === "aInfo" ? 4 : 3;
      a.clearUpdateRanges();
      for (const [s, e] of ranges) a.addUpdateRange(s * n, (e - s + 1) * n);
      a.needsUpdate = true;
    }
    ranges.length = 0;
  }

  // ---- bursts
  const DRAG: Record<number, number> = { 0: 2.3, 1: 1.6, 2: 2.3, 3: 2.6, 6: 3.0 };
  let flash = 0;
  const flashColor = new THREE.Color(1, 0.85, 0.6);

  function burst(
    at: V3,
    pattern: Pattern,
    size: number,
    colors: string[],
    yaw: number,
    tilt: number,
    seed: number,
    listener: V3,
  ) {
    const { life, kind } = patternLife(pattern);
    const count =
      pattern === "chrysanthemum"
        ? Math.round(patternCount(pattern, size) * 0.5)
        : patternCount(pattern, size);
    const shape = patternPoints(pattern, count, seed);
    const k = DRAG[kind] ?? 2.3;
    const cols = colors.map((c) => new THREE.Color(c));
    const n = shape.w.length;
    const starSize = pattern === "constellation" ? 7 : pattern === "dragon" ? 5 : 3 + size * 0.05;
    const flat = pattern === "ring" || pattern === "dragon" || pattern === "constellation";
    const c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      let x = shape.p[i * 3]!;
      let y = shape.p[i * 3 + 1]!;
      let z = shape.p[i * 3 + 2]!;
      if (flat) [x, y, z] = orient(x, y, z, yaw, tilt);
      const w = shape.w[i]!;
      c.copy(cols[i % cols.length]!).multiplyScalar(0.55 + 0.45 * w);
      const jitter = 1 + (hash01(seed, i) - 0.5) * 0.25;
      const v = { x: x * size * k, y: y * size * k, z: z * size * k };
      const l = life * (pattern === "constellation" ? 1 : jitter);
      star(at, v, c, l, starSize * (0.6 + 0.4 * w), kind, hash01(seed + 7, i));
      if (pattern === "chrysanthemum") {
        // Trailing sparks behind each star (they draw the streaks).
        for (const f of [0.9, 0.8]) {
          star(
            at,
            { x: v.x * f, y: v.y * f, z: v.z * f },
            c,
            l * 0.85,
            starSize * 0.7,
            0,
            hash01(seed + 9, i),
          );
        }
      }
    }
    // The flash of light on the kingdom, and the bang a moment later.
    const d = Math.hypot(at.x - listener.x, at.y - listener.y, at.z - listener.z);
    const near = Math.max(0, Math.min(1, 520 / (d + 120)));
    flash = Math.min(1.2, flash + near * (0.25 + size / 120));
    flashColor.lerp(cols[0]!, 0.5);
    sound(d / 340, (v) => opts.sfx?.fireworkBurst?.(v, size > 45), near);
  }

  // ---- rockets
  const rockets: Rocket[] = [];
  const gold = new THREE.Color("#ffc870");

  function launch(from: V3, to: V3, fuse: number, b: Rocket["burst"], listener: V3, comet = false) {
    // Ballistic from `from` to `to` in `fuse` seconds.
    const v = {
      x: (to.x - from.x) / fuse,
      y: (to.y - from.y) / fuse + 0.5 * GRAVITY * fuse,
      z: (to.z - from.z) / fuse,
    };
    const color = comet ? new THREE.Color(b?.colors[0] ?? "#ffd060") : gold;
    rockets.push({
      born: fxTime,
      until: fxTime + fuse,
      o: { ...from },
      v,
      emitIn: 0,
      burst: b,
      comet,
      color,
    });
    star(from, v, color, fuse, comet ? 6 : 3.2, 5, 0.5);
    const d = Math.hypot(from.x - listener.x, from.y - listener.y, from.z - listener.z);
    if (d < 400) sound(d / 340, (v) => opts.sfx?.fireworkLaunch?.(v), Math.max(0, 1 - d / 400));
  }

  function stepRockets(dt: number, listener: V3) {
    for (let i = rockets.length - 1; i >= 0; i--) {
      const r = rockets[i]!;
      const t = Math.min(fxTime, r.until) - r.born;
      const p = {
        x: r.o.x + r.v.x * t,
        y: r.o.y + r.v.y * t - 0.5 * GRAVITY * t * t,
        z: r.o.z + r.v.z * t,
      };
      // Embers behind it.
      r.emitIn -= dt;
      while (r.emitIn <= 0) {
        r.emitIn += r.comet ? 0.012 : 0.03;
        const s = hash01(Math.floor(fxTime * 1000), i);
        star(
          p,
          { x: (s - 0.5) * 3, y: -1 - s * 2, z: (hash01(i, Math.floor(fxTime * 997)) - 0.5) * 3 },
          r.color,
          r.comet ? 1.4 : 0.7,
          r.comet ? 4.5 : 2.2,
          4,
          s,
        );
      }
      if (fxTime >= r.until) {
        rockets.splice(i, 1);
        if (r.burst)
          burst(
            p,
            r.burst.pattern,
            r.burst.size,
            r.burst.colors,
            r.burst.yaw,
            r.burst.tilt,
            r.burst.seed,
            listener,
          );
      }
    }
  }

  // ---- sounds, a moment late with distance
  const pending: { at: number; play: (v: number) => void; v: number }[] = [];
  function sound(delay: number, play: (v: number) => void, v: number) {
    if (opts.quiet || !opts.sfx || v <= 0.01) return;
    pending.push({ at: fxTime + delay, play, v });
  }
  function playSounds() {
    const vol = opts.quiet ? 0 : opts.volume();
    for (let i = pending.length - 1; i >= 0; i--)
      if (pending[i]!.at <= fxTime) {
        const p = pending.splice(i, 1)[0]!;
        p.play(vol * p.v);
      }
  }

  // ---- set pieces: their bursts, scheduled on the effects clock
  const queued: { at: number; run: () => void }[] = [];
  const fired: string[] = [];

  function runPiece(p: SetPiece, listener: V3) {
    fired.push(p.id);
    const t0 = fxTime;
    p.bursts.forEach((b, k) => {
      const seed = (hashString(p.id) + k * 131) | 0;
      const bb = {
        pattern: b.pattern,
        size: b.size,
        colors: b.colors,
        yaw: b.yaw,
        tilt: b.tilt,
        seed,
      };
      const to = { x: b.x, y: b.y, z: b.z };
      if (b.pattern === "comet") {
        queued.push({
          at: t0 + b.t,
          run: () => launch(b.from ?? { x: b.x, y: 0, z: b.z }, to, 3.0, undefined, listener, true),
        });
        return;
      }
      if (b.from) queued.push({ at: t0 + b.t, run: () => launch(b.from!, to, FUSE, bb, listener) });
      else
        queued.push({
          at: t0 + b.t,
          run: () => burst(to, b.pattern, b.size, b.colors, b.yaw, b.tilt, seed, listener),
        });
    });
    const vol = opts.quiet ? 0 : opts.volume();
    const s = opts.sfx;
    if (s)
      switch (p.cue) {
        case "gong":
          s.gong?.(vol * 0.8);
          break;
        case "roar":
          s.dragonCall?.(vol * 0.9);
          break;
        case "bells":
          s.monasteryBell?.(vol * 0.6);
          break;
        case "cheer":
          s.crowdCheer?.(vol * 0.7);
          break;
        case "finale":
          s.gong?.(vol);
          s.crowdCheer?.(vol);
          break;
      }
  }

  // ---- the lanterns
  let lanternMat: THREE.ShaderMaterial | undefined;
  let lanternGeo: THREE.BufferGeometry | undefined;
  const lanternU = {
    uTime: { value: 0 },
    uActive: { value: 0 },
    uRise: { value: 280 },
    uScale: { value: 500 },
  };
  if (!opts.headless && cfg.lanterns.length) {
    const lp = new Float32Array(LANTERNS * 3);
    const ls = new Float32Array(LANTERNS * 3);
    const li = new Float32Array(LANTERNS);
    for (let i = 0; i < LANTERNS; i++) {
      const g = cfg.lanterns[i % cfg.lanterns.length]!;
      const a = hash01(i, 71) * Math.PI * 2;
      const r = Math.sqrt(hash01(i, 72)) * g.r;
      lp[i * 3] = g.x + Math.cos(a) * r;
      lp[i * 3 + 1] = g.y + 4;
      lp[i * 3 + 2] = g.z + Math.sin(a) * r;
      ls[i * 3] = hash01(i, 73);
      ls[i * 3 + 1] = 1.1 + hash01(i, 74) * 1.4;
      ls[i * 3 + 2] = hash01(i, 75);
      li[i] = i;
    }
    lanternGeo = new THREE.BufferGeometry();
    lanternGeo.setAttribute("position", new THREE.BufferAttribute(lp, 3));
    lanternGeo.setAttribute("aSeed", new THREE.BufferAttribute(ls, 3));
    lanternGeo.setAttribute("aIndex", new THREE.BufferAttribute(li, 1));
    lanternGeo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
    lanternMat = new THREE.ShaderMaterial({
      uniforms: lanternU,
      vertexShader: LANTERN_VERT,
      fragmentShader: LANTERN_FRAG,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      fog: false,
    });
    const lanterns = new THREE.Points(lanternGeo, lanternMat);
    lanterns.frustumCulled = false;
    lanterns.onBeforeRender = (r, s, c) => setScale(r, s, c, lanternU);
    group.add(lanterns);
  }

  // ---- the observatory's rings
  const rings: { mesh: THREE.Mesh; axis: THREE.Vector3; speed: number }[] = [];
  let ringMat: THREE.MeshBasicMaterial | undefined;
  let starMat: THREE.SpriteMaterial | undefined;
  let starTex: THREE.Texture | undefined;
  let core: THREE.Sprite | undefined;
  const ringGroup = new THREE.Group();
  if (!opts.headless && cfg.observatory) {
    const ob = cfg.observatory;
    ringGroup.position.set(ob.x, ob.y, ob.z);
    ringMat = new THREE.MeshBasicMaterial({ color: new THREE.Color("#e8b440") });
    const spec: [number, number, THREE.Vector3, number][] = [
      [1.0, 0.035, new THREE.Vector3(0.3, 1, 0.1).normalize(), 0.11],
      [0.82, 0.03, new THREE.Vector3(1, 0.4, 0.2).normalize(), -0.17],
      [0.64, 0.028, new THREE.Vector3(0.2, 0.3, 1).normalize(), 0.23],
      [1.18, 0.02, new THREE.Vector3(0, 1, 0), 0.05],
    ];
    for (const [r, tube, axis, speed] of spec) {
      const g = new THREE.TorusGeometry(ob.r * r, ob.r * tube, 6, 72);
      const m = new THREE.Mesh(g, ringMat);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), axis);
      rings.push({ mesh: m, axis: new THREE.Vector3(0, 0, 1), speed });
      ringGroup.add(m);
      // A little gold planet riding each ring.
      const planet = new THREE.Mesh(new THREE.SphereGeometry(ob.r * 0.05, 8, 6), ringMat);
      planet.position.set(ob.r * r, 0, 0);
      m.add(planet);
    }
    starTex = glowTexture();
    starMat = new THREE.SpriteMaterial({
      map: starTex,
      color: new THREE.Color("#fff0b0"),
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      fog: false,
    });
    core = new THREE.Sprite(starMat);
    core.scale.setScalar(ob.r * 0.9);
    ringGroup.add(core);
    group.add(ringGroup);
  }

  // ---- the flash
  const light = new THREE.HemisphereLight(0xffffff, 0x6040a0, 0);
  if (!opts.headless) group.add(light);

  // ---- the racer's place, the stage
  let hint = 0;
  let lastS: number | undefined;
  let lastTick: number | undefined;
  let stageNow: Stage = 1;
  let levelNow = 0.22;
  let activeLanterns = LANTERNS * 0.2;

  function where(listener: V3) {
    const samples = opts.track.samples;
    hint = nearestSample(samples, listener.x, listener.z, hint);
    return samples[hint]?.dist ?? 0;
  }

  return {
    get live() {
      let n = 0;
      for (let i = 0; i < POOL; i++) {
        const b = info[i * 4]!;
        if (fxTime >= b && fxTime <= b + info[i * 4 + 1]!) n++;
      }
      return n;
    },
    fired,
    fire(id, listener) {
      const p = cfg.pieces.find((q) => q.id === id);
      if (p) runPiece(p, listener);
      return !!p;
    },
    stage: () => stageNow,
    level: () => levelNow,
    render(t, dt, listener) {
      void t;
      fxTime += dt;
      const lp = opts.lap?.();
      const s = where(listener);
      stageNow = lp ? festivalStage(lp.lap, lp.laps, lp.finished) : 1;
      const u = lp?.finished ? 1 : s / cfg.length;
      levelNow = festivalLevel(stageNow, u);
      // Set pieces as you reach them.
      if (lastS !== undefined && lp && !lp.finished)
        for (const p of piecesDue(cfg, lastS, s, stageNow)) runPiece(p, listener);
      lastS = s;
      // The city's own rockets, on the race clock.
      const clock = opts.clock();
      const tick = Math.floor(clock / TICK);
      if (lastTick === undefined || tick < lastTick || tick - lastTick > 40) lastTick = tick - 1;
      for (let k = lastTick + 1; k <= tick; k++)
        for (const a of ambientAt(cfg, k, stageNow, levelNow)) {
          const site = cfg.sites[a.site]!;
          launch(
            site,
            a,
            a.fuse,
            {
              pattern: a.pattern,
              size: a.size,
              colors: a.colors,
              yaw: 0,
              tilt: 0,
              seed: k * 7 + a.site,
            },
            listener,
          );
        }
      lastTick = tick;
      for (let i = queued.length - 1; i >= 0; i--)
        if (queued[i]!.at <= fxTime) queued.splice(i, 1)[0]!.run();
      stepRockets(dt, listener);
      upload();
      uniforms.uTime.value = fxTime;
      playSounds();
      // The flash fades fast; its colour drifts back to warm white.
      flash *= Math.exp(-5 * dt);
      light.intensity = Math.min(0.9, flash * 0.8);
      light.color.copy(flashColor);
      flashColor.lerp(tmpColor.set(1, 0.85, 0.6), 1 - Math.exp(-2 * dt));
      // Lanterns, rings.
      activeLanterns +=
        (lanternCount(levelNow, LANTERNS) - activeLanterns) * (1 - Math.exp(-0.5 * dt));
      lanternU.uTime.value = fxTime + 400;
      lanternU.uActive.value = activeLanterns;
      for (const r of rings) r.mesh.rotateOnAxis(r.axis, r.speed * dt * (0.6 + levelNow * 1.6));
      if (ringMat)
        ringMat.color.setRGB(
          0.75 + 0.45 * levelNow,
          0.56 + 0.32 * levelNow,
          0.18 + 0.25 * levelNow,
        );
      if (core && cfg.observatory) {
        const pulse = 1 + 0.08 * Math.sin(fxTime * 2.2);
        core.scale.setScalar(cfg.observatory.r * (0.6 + 0.9 * levelNow) * pulse);
        if (starMat) starMat.opacity = 0.6 + 0.4 * levelNow;
      }
    },
    dispose() {
      geo.dispose();
      mat.dispose();
      lanternGeo?.dispose();
      lanternMat?.dispose();
      ringMat?.dispose();
      for (const r of rings) r.mesh.geometry.dispose();
      starMat?.dispose();
      starTex?.dispose();
      group.remove(points, ringGroup, light);
    },
  };
}

function hashString(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

/** A soft radiant star: a bright core, a halo, eight thin rays. */
function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d")!;
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.15, "rgba(255,240,180,0.9)");
  grad.addColorStop(0.45, "rgba(255,200,90,0.25)");
  grad.addColorStop(1, "rgba(255,180,60,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  g.strokeStyle = "rgba(255,240,200,0.6)";
  for (let k = 0; k < 8; k++) {
    const a = (k * Math.PI) / 4;
    g.lineWidth = k % 2 ? 1 : 2;
    g.beginPath();
    g.moveTo(64, 64);
    g.lineTo(64 + Math.cos(a) * (k % 2 ? 40 : 62), 64 + Math.sin(a) * (k % 2 ? 40 : 62));
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
