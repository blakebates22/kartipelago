/**
 * A painted sky that wraps the whole horizon: a gradient dome (deep blue overhead,
 * pale at the horizon), a glowing sun where the track's sunlight comes from, and puffy
 * cartoon clouds drifting slowly round. Everything is painted in code (original art),
 * kept far away (it follows the camera, so you never get closer) and drawn behind the
 * world, outside the fog.
 *
 * A track asks for one in look.json:
 *
 *   "skyDome": {
 *     "top": "#2f8fe8", "horizon": "#c4ecff", "bottom": "#a8dcff",
 *     "sun": { "color": "#fff4c2", "size": 7, "glow": "#ffe58a" },
 *     "clouds": { "count": 24, "color": "#ffffff", "shade": "#cfe6ff", "seed": 3,
 *                 "low": 3, "high": 24, "drift": 0.004 }
 *   }
 *
 * Every field is optional. The sun's direction is the look's sun direction. An evening
 * sky can add twinkling stars: "stars": { "count": 500, "color": "#ffffff", "low": 12 }.
 * A night sky can add the northern lights: "aurora": { "count": 6, "low": 16, "high": 60,
 * "colors": ["#2effa0", "#36d8ff", "#9a5aff", "#ff4ab8"], "speed": 1, "intensity": 1 }:
 * broad luminous curtains, bright at their lower hem and fading up into violet, slowly
 * folding, rippling and drifting (a small shader: no textures).
 *
 * A night sky can make the sun a full moon ("sun": { "face": "moon", ... }: a pale disc
 * with grey seas and craters, a soft halo) and hang a cloud over the land that now and
 * then gathers into the shape of a skull ("skull": { "azimuth": 50, "elevation": 30,
 * "size": 30, "color", "shade", "period": 45 }): for a few seconds of every period it
 * slowly forms, lingers and drifts apart again, and the rest of the time it's gone.
 */
import * as THREE from "three";

export interface SkyDomeSpec {
  top?: string;
  horizon?: string;
  bottom?: string;
  /**
   * The sun's disc. `elevation` (degrees above the horizon) can put it lower in the
   * sky than the light really comes from, so you see it while racing; its compass
   * direction always matches the light.
   */
  sun?: { color?: string; size?: number; glow?: string; elevation?: number; face?: "moon" };
  clouds?: {
    count?: number;
    color?: string;
    shade?: string;
    seed?: number;
    /** Lowest and highest cloud, degrees above the horizon. */
    low?: number;
    high?: number;
    /** How fast the clouds drift round, radians per second. */
    drift?: number;
  };
  /**
   * Distant hills all round the horizon (so a track's open ends never look out into
   * empty sky): rings of jagged silhouettes, the far ones paler. `height` is the
   * tallest peak, degrees above the horizon. `style: "mesas"` makes them desert
   * mesas and buttes instead: flat tops, steep sides, the odd spire.
   */
  hills?: {
    color?: string;
    far?: string;
    height?: number;
    seed?: number;
    layers?: number;
    style?: "mesas" | "karst";
  };
  /** Stars twinkling in the sky above `low` degrees (for evening and night skies). */
  stars?: { count?: number; color?: string; seed?: number; low?: number };
  /** A cloud that slowly gathers into a skull now and then (degrees, seconds). */
  skull?: {
    azimuth?: number;
    elevation?: number;
    size?: number;
    color?: string;
    shade?: string;
    period?: number;
  };
  /** The northern lights: curtains between `low` and `high` degrees. */
  aurora?: {
    count?: number;
    seed?: number;
    low?: number;
    high?: number;
    speed?: number;
    intensity?: number;
    /** Hem, middle, top and highlight colours. */
    colors?: string[];
    /** Centre the first curtain on this compass direction (degrees, world X toward Z). */
    azimuth?: number;
  };
}

const AURORA_VERT = /* glsl */ `
  attribute float u;
  attribute float v;
  uniform float time;
  uniform float speed;
  uniform float az0;
  uniform float span;
  uniform float low;
  uniform float high;
  uniform float seed;
  uniform float radius;
  varying float vu;
  varying float vv;
  void main() {
    vu = u;
    vv = v;
    float t = time * speed;
    // The curtain's foot: an arc across the sky that folds and drifts slowly.
    float az = az0 + span * u
      + 0.10 * sin(u * 7.0 + t * 0.21 + seed)
      + 0.05 * sin(u * 17.0 - t * 0.37 + seed * 2.0)
      + 0.03 * sin(t * 0.05 + seed);
    float fold = 0.5 + 0.5 * sin(u * 5.0 + t * 0.13 + seed * 3.0);
    float el = low + (high - low) * v * (0.65 + 0.35 * fold)
      + 0.03 * sin(u * 9.0 + t * 0.3 + seed);
    // Lean the top over a little, like a hanging sheet.
    az += v * 0.08 * sin(u * 3.0 + t * 0.17 + seed);
    vec3 p = vec3(cos(az) * cos(el), sin(el), sin(az) * cos(el)) * radius;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }
`;

const AURORA_FRAG = /* glsl */ `
  uniform float time;
  uniform float speed;
  uniform float seed;
  uniform float intensity;
  uniform vec3 hem;
  uniform vec3 mid;
  uniform vec3 top;
  uniform vec3 flash;
  varying float vu;
  varying float vv;
  void main() {
    float t = time * speed;
    // Fine vertical rays drifting along the curtain.
    float rays = 0.55
      + 0.25 * sin(vu * 140.0 + t * 0.9 + seed)
      + 0.20 * sin(vu * 61.0 - t * 0.55 + seed * 1.7);
    // Brightness rippling along it.
    float wave = 0.6 + 0.4 * sin(vu * 9.0 - t * 0.8 + seed * 4.0);
    // Bright at the hem, fading out towards the top and both ends.
    float hemGlow = smoothstep(0.0, 0.06, vv) * (1.0 - smoothstep(0.08, 1.0, vv));
    float ends = smoothstep(0.0, 0.12, vu) * (1.0 - smoothstep(0.88, 1.0, vu));
    vec3 c = mix(hem, mid, smoothstep(0.05, 0.45, vv));
    c = mix(c, top, smoothstep(0.45, 1.0, vv));
    // Now and then a pink flare runs along the lower edge.
    float flare = smoothstep(0.75, 1.0, sin(vu * 4.0 + t * 0.4 + seed * 5.0)) * (1.0 - vv);
    c = mix(c, flash, flare * 0.6);
    float a = intensity * rays * wave * (hemGlow + 0.25 * (1.0 - vv)) * ends;
    gl_FragColor = vec4(c * a, 1.0);
  }
`;

export interface SkyDome {
  readonly group: THREE.Group;
  /** Keep it centred on the camera, and drift the clouds. */
  update(camera: THREE.Camera, dt: number): void;
  dispose(): void;
}

const RADIUS = 1400;

function rng(seed: number) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };
}

function canvas(w: number, h: number) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return { c, g: c.getContext("2d")! };
}

/** A chunky, friendly cloud: overlapping puffs with a flat, shaded underside. */
function cloudTexture(seed: number, color: string, shade: string) {
  const { c, g } = canvas(128, 64);
  const r = rng(seed);
  const puffs: [number, number, number][] = [];
  const n = 4 + Math.floor(r() * 4);
  for (let i = 0; i < n; i++) {
    const x = 22 + (84 * i) / (n - 1) + (r() - 0.5) * 10;
    const rad = 12 + r() * 14 * Math.sin((Math.PI * (i + 0.5)) / n);
    puffs.push([x, 46 - rad * 0.6, rad]);
  }
  // Shade first (offset down), then the bright body, then a flat bottom.
  for (const [pass, col, dy] of [
    [0, shade, 4],
    [1, color, 0],
  ] as const) {
    g.fillStyle = col;
    for (const [x, y, rad] of puffs) {
      g.beginPath();
      g.arc(x, y + dy, rad, 0, Math.PI * 2);
      g.fill();
    }
    if (pass === 0) g.fillRect(16, 40, 96, 10);
  }
  g.clearRect(0, 52, 128, 12);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.LinearFilter;
  t.generateMipmaps = false;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** The sun: a bright disc with soft rings of glow. */
function sunTexture(color: string, glow: string) {
  const { c, g } = canvas(128, 128);
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, color);
  grad.addColorStop(0.28, color);
  grad.addColorStop(0.32, glow);
  grad.addColorStop(0.6, `${glow}55`);
  grad.addColorStop(1, `${glow}00`);
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** A full moon: a pale disc with grey seas and a few craters, and a soft halo. */
function moonTexture(color: string, glow: string) {
  const { c, g } = canvas(256, 256);
  const halo = g.createRadialGradient(128, 128, 40, 128, 128, 128);
  halo.addColorStop(0, `${glow}cc`);
  halo.addColorStop(0.25, `${glow}55`);
  halo.addColorStop(1, `${glow}00`);
  g.fillStyle = halo;
  g.fillRect(0, 0, 256, 256);
  g.fillStyle = color;
  g.beginPath();
  g.arc(128, 128, 64, 0, Math.PI * 2);
  g.fill();
  g.save();
  g.beginPath();
  g.arc(128, 128, 64, 0, Math.PI * 2);
  g.clip();
  // The seas: soft grey blotches (our own arrangement).
  const r = rng(29);
  for (const [x, y, rad, a] of [
    [104, 98, 26, 0.32],
    [140, 112, 20, 0.28],
    [118, 140, 18, 0.25],
    [150, 150, 14, 0.22],
    [94, 132, 12, 0.2],
    [160, 88, 10, 0.18],
  ] as const) {
    const sea = g.createRadialGradient(x, y, 0, x, y, rad);
    sea.addColorStop(0, `rgba(120,124,150,${a})`);
    sea.addColorStop(1, "rgba(120,124,150,0)");
    g.fillStyle = sea;
    g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  // Craters: little rings, lit on one side.
  for (let k = 0; k < 9; k++) {
    const x = 84 + r() * 88;
    const y = 84 + r() * 88;
    const rad = 2 + r() * 4;
    g.strokeStyle = "rgba(110,112,140,0.16)";
    g.lineWidth = 1.2;
    g.beginPath();
    g.arc(x, y, rad, 0, Math.PI * 2);
    g.stroke();
    g.strokeStyle = "rgba(255,255,255,0.14)";
    g.beginPath();
    g.arc(x, y, rad, Math.PI * 0.9, Math.PI * 1.6);
    g.stroke();
  }
  // A faint shade round the limb.
  const limb = g.createRadialGradient(128, 128, 44, 128, 128, 64);
  limb.addColorStop(0, "rgba(90,90,140,0)");
  limb.addColorStop(1, "rgba(90,90,140,0.3)");
  g.fillStyle = limb;
  g.fillRect(0, 0, 256, 256);
  g.restore();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * A billowing cloud in the shape of a skull: puffs for the dome of the head, the cheeks
 * and the jaw, two hollow eyes, a hollow nose and gaps between the teeth, all soft-edged
 * like any other cloud.
 */
function skullTexture(color: string, shade: string) {
  const { c, g } = canvas(256, 256);
  const puffs: [number, number, number][] = [];
  // The cranium: a ring of big puffs, then filled.
  for (let k = 0; k <= 9; k++) {
    const a = Math.PI * (1.05 + (k / 9) * 0.9);
    puffs.push([128 + Math.cos(a) * 70, 112 + Math.sin(a) * 66, 30 + (k % 3) * 4]);
  }
  puffs.push([128, 100, 62], [92, 130, 34], [164, 130, 34]);
  // Cheeks and the jaw.
  puffs.push([86, 160, 26], [170, 160, 26], [104, 186, 22], [152, 186, 22], [128, 192, 24]);
  for (const pass of [0, 1]) {
    g.fillStyle = pass ? color : shade;
    for (const [x, y, r] of puffs) {
      g.beginPath();
      g.arc(x, y + (pass ? 0 : 7), r, 0, Math.PI * 2);
      g.fill();
    }
  }
  // Cut out the eyes, the nose and the gaps between the teeth.
  g.globalCompositeOperation = "destination-out";
  for (const x of [98, 158]) {
    const eye = g.createRadialGradient(x, 132, 4, x, 132, 24);
    eye.addColorStop(0, "rgba(0,0,0,1)");
    eye.addColorStop(0.75, "rgba(0,0,0,0.9)");
    eye.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = eye;
    g.beginPath();
    g.ellipse(x, 132, 24, 20, x < 128 ? 0.2 : -0.2, 0, Math.PI * 2);
    g.fill();
  }
  g.fillStyle = "rgba(0,0,0,0.85)";
  g.beginPath();
  g.moveTo(128, 150);
  g.lineTo(118, 172);
  g.lineTo(138, 172);
  g.closePath();
  g.fill();
  for (let k = -2; k <= 2; k++) {
    g.fillRect(128 + k * 12 - 1.5, 184, 3, 20);
  }
  g.globalCompositeOperation = "source-over";
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * How visible the skull cloud is at time `t` (0..1): each period it gathers over 8 s,
 * lingers 10 s and drifts apart over 8 s; gone the rest of the time.
 */
export function skullShown(t: number, period: number): number {
  const p = Math.max(30, period);
  const u = ((t % p) + p) % p;
  const start = p * 0.35;
  const k = u - start;
  if (k < 0 || k > 26) return 0;
  if (k < 8) return k / 8;
  if (k < 18) return 1;
  return 1 - (k - 18) / 8;
}

/**
 * Desert skyline: flat-topped mesas and buttes with steep, slightly stepped sides on a
 * low rolling base, and now and then a thin spire. Fills lifts (0..1) round the circle.
 */
/** Karst country: a low haze of hills with tall, round-shouldered towers standing out of
 * it, crowded together, some with a lean (Dragon Isles). */
function karstProfile(lifts: Float32Array, r: () => number) {
  const n = lifts.length - 1;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    lifts[i] = 0.12 + 0.06 * Math.sin(a * 4 + 2) + 0.03 * Math.sin(a * 19);
  }
  const count = 40 + Math.floor(r() * 16);
  for (let k = 0; k < count; k++) {
    const c = r() * n;
    const half = (3 + r() * 9) * (n / 720);
    const h = 0.3 + r() * 0.7;
    const lean = (r() - 0.5) * 0.5;
    for (let j = Math.floor(c - half * 1.3); j <= Math.ceil(c + half * 1.3); j++) {
      const i = ((j % n) + n) % n;
      const d = (j - c) / half + lean * 0.4;
      // Steep sides, a rounded top.
      const ad = Math.abs(d);
      const v = ad < 1 ? h * Math.sqrt(1 - ad * ad * ad * ad) : 0;
      lifts[i] = Math.max(lifts[i]!, v);
      if (i === 0) lifts[n] = lifts[0]!;
    }
  }
  lifts[n] = lifts[0]!;
}

function mesaProfile(lifts: Float32Array, r: () => number) {
  const n = lifts.length - 1;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    lifts[i] = 0.1 + 0.05 * Math.sin(a * 5 + 1) + 0.03 * Math.sin(a * 23);
  }
  const count = 18 + Math.floor(r() * 8);
  for (let k = 0; k < count; k++) {
    const c = r() * n;
    const half = (r() < 0.25 ? 2 + r() * 4 : 8 + r() * 28) * (n / 720);
    const h = 0.35 + r() * 0.65;
    const step = r() < 0.6;
    for (let j = Math.floor(c - half * 1.4); j <= Math.ceil(c + half * 1.4); j++) {
      const i = ((j % n) + n) % n;
      const d = Math.abs(j - c) / half;
      // Flat top, a steep cliff, then (sometimes) a ledge and a talus foot.
      let v =
        d < 1 ? h : d < 1.12 ? h * (1 - (d - 1) / 0.12) * 0.6 + h * 0.4 * (1 - (d - 1) / 0.4) : 0;
      if (step && d >= 1 && d < 1.4) v = Math.max(v, h * 0.45 * (1 - (d - 1) / 0.4));
      v *= 1 - 0.03 * Math.sin(j * 1.7);
      lifts[i] = Math.max(lifts[i]!, v);
      if (i === 0) lifts[n] = lifts[0]!;
    }
  }
  lifts[n] = lifts[0]!;
}

export function createSkyDome(
  spec: SkyDomeSpec,
  sunDirection: [number, number, number] = [0.5, 0.8, 0.3],
): SkyDome {
  const group = new THREE.Group();
  group.name = "sky dome";
  group.renderOrder = -10;
  const disposables: { dispose(): void }[] = [];

  // The dome: a sphere seen from inside, coloured by height.
  const geo = new THREE.SphereGeometry(RADIUS, 32, 16);
  const top = new THREE.Color(spec.top ?? "#2f8fe8");
  const hor = new THREE.Color(spec.horizon ?? "#c4ecff");
  const bot = new THREE.Color(spec.bottom ?? spec.horizon ?? "#a8dcff");
  const pos = geo.attributes.position!;
  const cols = new Float32Array(pos.count * 3);
  const c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const h = pos.getY(i) / RADIUS; // -1 .. 1
    if (h >= 0) c.copy(hor).lerp(top, Math.pow(h, 0.6));
    else c.copy(hor).lerp(bot, Math.min(1, -h * 4));
    cols[i * 3] = c.r;
    cols[i * 3 + 1] = c.g;
    cols[i * 3 + 2] = c.b;
  }
  geo.setAttribute("color", new THREE.BufferAttribute(cols, 3));
  const domeMat = new THREE.MeshBasicMaterial({
    vertexColors: true,
    side: THREE.BackSide,
    fog: false,
    depthWrite: false,
  });
  const dome = new THREE.Mesh(geo, domeMat);
  dome.renderOrder = -10;
  dome.frustumCulled = false;
  group.add(dome);
  disposables.push(geo, domeMat);

  // The sun, where the light comes from.
  const sd = new THREE.Vector3(...sunDirection).normalize();
  if (spec.sun?.elevation !== undefined) {
    const flat = Math.hypot(sd.x, sd.z) || 1;
    const el = (spec.sun.elevation * Math.PI) / 180;
    sd.set((sd.x / flat) * Math.cos(el), Math.sin(el), (sd.z / flat) * Math.cos(el));
  }
  const moon = spec.sun?.face === "moon";
  const sunTex = moon
    ? moonTexture(spec.sun?.color ?? "#f4f2ea", spec.sun?.glow ?? "#9ab0ff")
    : sunTexture(spec.sun?.color ?? "#fff4c2", spec.sun?.glow ?? "#ffe58a");
  const sunMat = new THREE.SpriteMaterial({
    map: sunTex,
    fog: false,
    depthWrite: false,
    transparent: true,
  });
  const sun = new THREE.Sprite(sunMat);
  // (The moon's picture has more halo round its disc, so it's drawn bigger.)
  const size = (((spec.sun?.size ?? 7) * Math.PI) / 180) * RADIUS * (moon ? 3.2 : 2.6);
  sun.scale.set(size, size, 1);
  sun.position.copy(sd).multiplyScalar(RADIUS * 0.92);
  sun.renderOrder = -9;
  group.add(sun);
  disposables.push(sunTex, sunMat);

  // Clouds all round the horizon.
  const clouds = new THREE.Group();
  group.add(clouds);
  const cs = spec.clouds ?? {};
  const r = rng(cs.seed ?? 3);
  const textures = [0, 1, 2, 3].map((k) =>
    cloudTexture((cs.seed ?? 3) * 10 + k, cs.color ?? "#ffffff", cs.shade ?? "#cfe6ff"),
  );
  disposables.push(...textures);
  const count = cs.count ?? 24;
  const low = cs.low ?? 3;
  const high = cs.high ?? 24;
  const cloudGeo = new THREE.PlaneGeometry(1, 0.5);
  disposables.push(cloudGeo);
  for (let i = 0; i < count; i++) {
    const az = (i / count) * Math.PI * 2 + (r() - 0.5) * 0.4;
    const el = ((low + (high - low) * Math.pow(r(), 1.2)) * Math.PI) / 180;
    // Keep clouds from covering the sun.
    const p = new THREE.Vector3(
      Math.cos(az) * Math.cos(el),
      Math.sin(el),
      Math.sin(az) * Math.cos(el),
    );
    if (p.angleTo(sd) < 0.14) continue;
    const mat = new THREE.MeshBasicMaterial({
      map: textures[i % textures.length],
      transparent: true,
      alphaTest: 0.5,
      fog: false,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    disposables.push(mat);
    const m = new THREE.Mesh(cloudGeo, mat);
    const w = 220 + r() * 300;
    m.scale.set(w, w, 1);
    m.position.copy(p).multiplyScalar(RADIUS * 0.85);
    m.lookAt(0, m.position.y * 0.6, 0);
    m.renderOrder = -8;
    clouds.add(m);
  }

  // Hills round the horizon, far (pale) to near (dark), drawn over the low clouds.
  if (spec.hills) {
    const hs = spec.hills;
    const layers = Math.max(1, Math.min(4, hs.layers ?? 2));
    const hr = rng((hs.seed ?? 7) * 31 + 5);
    const near = new THREE.Color(hs.color ?? "#2f5a34");
    const far = new THREE.Color(hs.far ?? spec.horizon ?? "#9cc8b0");
    const base = new THREE.Color(spec.horizon ?? "#c4ecff");
    const mesas = hs.style === "mesas";
    const karst = hs.style === "karst";
    const SEG = mesas || karst ? 720 : 128;
    for (let l = 0; l < layers; l++) {
      const k = layers === 1 ? 1 : l / (layers - 1); // 0 far .. 1 near
      const top = near.clone().lerp(far, 1 - k);
      const foot = top.clone().lerp(base, 0.55 - 0.25 * k);
      const r = RADIUS * (0.8 - l * 0.04);
      const peak = ((hs.height ?? 9) * (0.65 + 0.35 * k) * Math.PI) / 180;
      // A jagged ridge: a few big peaks plus small bumps, all smooth-ish.
      const phase = [hr() * 6.28, hr() * 6.28, hr() * 6.28];
      const lifts = new Float32Array(SEG + 1);
      if (mesas) mesaProfile(lifts, hr);
      else if (karst) karstProfile(lifts, hr);
      else
        for (let i = 0; i <= SEG; i++) {
          const a = (i / SEG) * Math.PI * 2;
          const v =
            0.45 +
            0.3 * Math.sin(a * 3 + phase[0]!) +
            0.18 * Math.sin(a * 7 + phase[1]!) +
            0.1 * Math.sin(a * 17 + phase[2]!) +
            (hr() - 0.5) * 0.08;
          lifts[i] = Math.max(0.08, Math.min(1, v));
        }
      lifts[SEG] = lifts[0]!;
      const pos: number[] = [];
      const col: number[] = [];
      const idx: number[] = [];
      for (let i = 0; i <= SEG; i++) {
        const a = (i / SEG) * Math.PI * 2;
        const el = peak * lifts[i]!;
        const cx = Math.cos(a);
        const cz = Math.sin(a);
        pos.push(
          cx * r,
          -r * 0.05,
          cz * r,
          cx * r * Math.cos(el),
          r * Math.sin(el),
          cz * r * Math.cos(el),
        );
        col.push(foot.r, foot.g, foot.b, top.r, top.g, top.b);
        if (i < SEG) {
          const o = i * 2;
          idx.push(o, o + 2, o + 1, o + 1, o + 2, o + 3);
        }
      }
      const hg = new THREE.BufferGeometry();
      hg.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      hg.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
      hg.setIndex(idx);
      const hm = new THREE.MeshBasicMaterial({
        vertexColors: true,
        side: THREE.DoubleSide,
        fog: false,
        depthWrite: false,
      });
      const ring = new THREE.Mesh(hg, hm);
      ring.renderOrder = -7 + l * 0.1;
      ring.frustumCulled = false;
      group.add(ring);
      disposables.push(hg, hm);
    }
  }

  // Stars: little points over the upper sky, each twinkling at its own pace.
  let twinkle: ((t: number) => void) | undefined;
  if (spec.stars) {
    const st = spec.stars;
    const n = Math.max(0, Math.min(2000, st.count ?? 400));
    const sr = rng((st.seed ?? 11) * 17 + 3);
    const low = ((st.low ?? 10) * Math.PI) / 180;
    const pos = new Float32Array(n * 3);
    const col = new Float32Array(n * 3);
    const base = new THREE.Color(st.color ?? "#ffffff");
    const phase = new Float32Array(n);
    const bright = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const az = sr() * Math.PI * 2;
      const el = low + Math.asin(sr()) * (1 - low / (Math.PI / 2));
      const r = RADIUS * 0.95;
      pos[i * 3] = Math.cos(az) * Math.cos(el) * r;
      pos[i * 3 + 1] = Math.sin(el) * r;
      pos[i * 3 + 2] = Math.sin(az) * Math.cos(el) * r;
      phase[i] = sr() * 100;
      bright[i] = 0.45 + 0.55 * sr();
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    const m = new THREE.PointsMaterial({
      size: 2.2,
      sizeAttenuation: false,
      vertexColors: true,
      fog: false,
      depthWrite: false,
      transparent: true,
    });
    const pts = new THREE.Points(g, m);
    pts.renderOrder = -9.5;
    pts.frustumCulled = false;
    group.add(pts);
    disposables.push(g, m);
    twinkle = (t) => {
      for (let i = 0; i < n; i++) {
        const k = bright[i]! * (0.7 + 0.3 * Math.sin(t * (1.3 + (phase[i]! % 2)) + phase[i]!));
        col[i * 3] = base.r * k;
        col[i * 3 + 1] = base.g * k;
        col[i * 3 + 2] = base.b * k;
      }
      g.attributes.color!.needsUpdate = true;
    };
    twinkle(0);
  }
  // The aurora: a few curtains spread round the sky, each its own slowly moving sheet.
  const aurora: THREE.ShaderMaterial[] = [];
  if (spec.aurora) {
    const au = spec.aurora;
    const n = Math.max(0, Math.min(12, Math.round(au.count ?? 5)));
    const ar = rng((au.seed ?? 5) * 13 + 7);
    const cols = (au.colors?.length ? au.colors : ["#2effa0", "#36d8ff", "#9a5aff", "#ff4ab8"]).map(
      (h) => new THREE.Color(h),
    );
    const low = ((au.low ?? 16) * Math.PI) / 180;
    const high = ((au.high ?? 60) * Math.PI) / 180;
    const COLS = 96;
    for (let i = 0; i < n; i++) {
      const g = new THREE.BufferGeometry();
      const uu = new Float32Array((COLS + 1) * 2);
      const vv = new Float32Array((COLS + 1) * 2);
      const idx: number[] = [];
      for (let k = 0; k <= COLS; k++) {
        uu[k * 2] = uu[k * 2 + 1] = k / COLS;
        vv[k * 2] = 0;
        vv[k * 2 + 1] = 1;
        if (k < COLS) idx.push(k * 2, k * 2 + 2, k * 2 + 1, k * 2 + 1, k * 2 + 2, k * 2 + 3);
      }
      // Positions come from the shader; these only size the bounds.
      g.setAttribute("position", new THREE.BufferAttribute(new Float32Array((COLS + 1) * 6), 3));
      g.setAttribute("u", new THREE.BufferAttribute(uu, 1));
      g.setAttribute("v", new THREE.BufferAttribute(vv, 1));
      g.setIndex(idx);
      const lift = ar();
      const m = new THREE.ShaderMaterial({
        vertexShader: AURORA_VERT,
        fragmentShader: AURORA_FRAG,
        uniforms: {
          time: { value: 0 },
          speed: { value: (au.speed ?? 1) * (0.7 + ar() * 0.6) },
          az0: {
            value:
              i === 0 && au.azimuth !== undefined
                ? (au.azimuth * Math.PI) / 180 - 0.6
                : (i / n) * Math.PI * 2 + ar() * 0.8,
          },
          span: { value: 0.9 + ar() * 0.9 },
          low: { value: low + (high - low) * 0.15 * lift },
          high: { value: high - (high - low) * 0.25 * ar() },
          seed: { value: ar() * 50 },
          radius: { value: RADIUS * 0.9 },
          intensity: { value: (au.intensity ?? 1) * (0.7 + ar() * 0.5) },
          hem: { value: cols[0]!.clone() },
          mid: { value: (cols[1] ?? cols[0]!).clone() },
          top: { value: (cols[2] ?? cols[0]!).clone() },
          flash: { value: (cols[3] ?? cols[2] ?? cols[0]!).clone() },
        },
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide,
        fog: false,
      });
      const mesh = new THREE.Mesh(g, m);
      mesh.frustumCulled = false;
      mesh.renderOrder = -9.2;
      group.add(mesh);
      aurora.push(m);
      disposables.push(g, m);
    }
  }
  // The skull cloud: one soft billboard, faded in and out on its period.
  let skull: { mat: THREE.MeshBasicMaterial; mesh: THREE.Mesh; period: number } | undefined;
  if (spec.skull) {
    const sk = spec.skull;
    const tex = skullTexture(sk.color ?? "#6a4e9a", sk.shade ?? "#2c1c58");
    const mat = new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      opacity: 0,
      fog: false,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const az = ((sk.azimuth ?? 50) * Math.PI) / 180;
    const el = ((sk.elevation ?? 30) * Math.PI) / 180;
    const w = (((sk.size ?? 30) * Math.PI) / 180) * RADIUS;
    const geo2 = new THREE.PlaneGeometry(1, 1);
    const mesh = new THREE.Mesh(geo2, mat);
    mesh.scale.set(w, w, 1);
    mesh.position
      .set(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el))
      .multiplyScalar(RADIUS * 0.84);
    mesh.lookAt(0, mesh.position.y * 0.5, 0);
    mesh.renderOrder = -7.9;
    mesh.frustumCulled = false;
    mesh.visible = false;
    group.add(mesh);
    disposables.push(tex, mat, geo2);
    skull = { mat, mesh, period: sk.period ?? 45 };
  }
  let clockT = 0;

  const drift = cs.drift ?? 0.004;
  return {
    group,
    update(camera, dt) {
      group.position.copy(camera.position);
      clouds.rotation.y += drift * dt;
      clockT += dt;
      twinkle?.(clockT);
      for (const m of aurora) m.uniforms.time!.value = clockT;
      if (skull) {
        const k = skullShown(clockT, skull.period);
        skull.mat.opacity = 0.85 * k;
        skull.mesh.visible = k > 0;
        // Forming, it swells a little and settles; drifting apart, it stretches.
        const sw = 1 + 0.06 * (1 - k);
        skull.mesh.scale.y = skull.mesh.scale.x * sw;
      }
    },
    dispose() {
      group.removeFromParent();
      for (const d of disposables) d.dispose();
    },
  };
}
