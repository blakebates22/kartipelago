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
 * Every field is optional. The sun's direction is the look's sun direction.
 */
import * as THREE from "three";

export interface SkyDomeSpec {
  top?: string;
  horizon?: string;
  bottom?: string;
  sun?: { color?: string; size?: number; glow?: string };
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
}

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
  const sunTex = sunTexture(spec.sun?.color ?? "#fff4c2", spec.sun?.glow ?? "#ffe58a");
  const sunMat = new THREE.SpriteMaterial({
    map: sunTex,
    fog: false,
    depthWrite: false,
    transparent: true,
  });
  const sun = new THREE.Sprite(sunMat);
  const size = (((spec.sun?.size ?? 7) * Math.PI) / 180) * RADIUS * 2.6;
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
    const el = ((low + (high - low) * Math.pow(r(), 1.6)) * Math.PI) / 180;
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
    const w = 160 + r() * 260;
    m.scale.set(w, w, 1);
    m.position.copy(p).multiplyScalar(RADIUS * 0.85);
    m.lookAt(0, m.position.y * 0.6, 0);
    m.renderOrder = -8;
    clouds.add(m);
  }

  const drift = cs.drift ?? 0.004;
  return {
    group,
    update(camera, dt) {
      group.position.copy(camera.position);
      clouds.rotation.y += drift * dt;
    },
    dispose() {
      group.removeFromParent();
      for (const d of disposables) d.dispose();
    },
  };
}
