/**
 * The story dragons' breath, as soft particles: Cinderjaw's and the King's fire (the
 * King's with a white-gold core), Rimefang's frost (a white-blue mist with ice glinting
 * in it), Scorchwind's sandstorm (dust whirling round the blast), Tidewyrm's water (a jet
 * and its spray), Lumen's golden light, and puffs of smoke from a nostril.
 *
 * Two layers of points: glowing ones added onto the picture (flame, sparkle, light) and
 * soft solid ones (smoke, mist, sand, spray). Particles live in world space, so a dragon
 * that moves leaves its breath behind, and they spread along the ground where they hit
 * it.
 */
import * as THREE from "three";

export type BreathKind = "fire" | "kingfire" | "frost" | "sand" | "water" | "light";

const VERT = /* glsl */ `
  attribute float size;
  attribute vec4 tint;
  varying vec4 vTint;
  uniform float uScale;
  void main() {
    vTint = tint;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = size * uScale / max(0.5, -mv.z);
    gl_Position = projectionMatrix * mv;
  }
`;
const FRAG = /* glsl */ `
  varying vec4 vTint;
  uniform float uSoft;
  void main() {
    vec2 d = gl_PointCoord - 0.5;
    float r = length(d) * 2.0;
    float a = smoothstep(1.0, uSoft, r);
    if (a <= 0.003) discard;
    gl_FragColor = vec4(vTint.rgb, vTint.a * a);
  }
`;

interface Layer {
  points: THREE.Points;
  geo: THREE.BufferGeometry;
  pos: Float32Array;
  size: Float32Array;
  tint: Float32Array;
  mat: THREE.ShaderMaterial;
}

function layer(n: number, additive: boolean, soft: number): Layer {
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3);
  const size = new Float32Array(n);
  const tint = new Float32Array(n * 4);
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("size", new THREE.BufferAttribute(size, 1));
  geo.setAttribute("tint", new THREE.BufferAttribute(tint, 4));
  const mat = new THREE.ShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    uniforms: { uScale: { value: 300 }, uSoft: { value: soft } },
    transparent: true,
    depthWrite: false,
    blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.renderOrder = additive ? 3 : 2;
  points.onBeforeRender = (renderer, _s, camera) => {
    const h = renderer.getDrawingBufferSize(tmp2).y;
    const cam = camera as THREE.PerspectiveCamera;
    mat.uniforms.uScale!.value = (h * 0.5) / Math.tan(((cam.fov ?? 60) * Math.PI) / 360);
  };
  return { points, geo, pos, size, tint, mat };
}
const tmp2 = new THREE.Vector2();

interface P {
  alive: boolean;
  glow: boolean;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  age: number;
  life: number;
  s0: number;
  s1: number;
  /** Colour ramp start and end (r, g, b, a). */
  c0: [number, number, number, number];
  c1: [number, number, number, number];
  drag: number;
  rise: number;
  /** Whirl round the blast's axis (sand), radians per second, and its centre line. */
  whirl: number;
  ax: number;
  ay: number;
  az: number;
  dx: number;
  dy: number;
  dz: number;
  twinkle: number;
}

const hex = (c: string, a: number): [number, number, number, number] => {
  // (The points' shader writes its colour straight out: keep it in sRGB.)
  const k = new THREE.Color(c).convertLinearToSRGB();
  return [k.r, k.g, k.b, a];
};

export class Breath {
  readonly group = new THREE.Group();
  private glow: Layer;
  private dust: Layer;
  private ps: P[] = [];
  private acc = 0;
  private smokeAcc = 0;
  private auraAcc = 0;
  private last = -1;
  private seed = 1;

  constructor(
    parent: THREE.Object3D,
    readonly kind: BreathKind,
    n = 700,
  ) {
    this.glow = layer(n, true, 0.15);
    this.dust = layer(n, false, 0.35);
    this.group.add(this.glow.points, this.dust.points);
    this.group.name = "dragon breath";
    parent.add(this.group);
    for (let i = 0; i < n; i++) this.ps.push({ alive: false } as P);
  }

  private rnd() {
    this.seed = (this.seed * 16807) % 2147483647;
    return (this.seed - 1) / 2147483646;
  }

  private spawn(): P | undefined {
    for (const p of this.ps) if (!p.alive) return p;
    return undefined;
  }

  /**
   * Run the breath: `on` 0..1 (how hard), from `mouth` along `dir` (world, unit), the
   * blast `scale` (the dragon's size), the ground's height; `smoke` puffs from `nose`
   * (0..1), and `aura` motes round `centre` (Lumen's glow).
   */
  update(
    time: number,
    on: number,
    mouth: THREE.Vector3,
    dir: THREE.Vector3,
    scale: number,
    ground: number,
    smoke = 0,
    nose?: THREE.Vector3,
    aura = 0,
    centre?: THREE.Vector3,
  ) {
    const dt = this.last < 0 ? 0 : Math.min(0.05, Math.max(0, time - this.last));
    this.last = time;
    const r = () => this.rnd();
    const k = this.kind;
    // Emit.
    const rate = on * (k === "sand" ? 190 : k === "frost" ? 170 : k === "water" ? 230 : 210);
    this.acc += rate * dt;
    const speed = scale * (k === "water" ? 30 : k === "sand" ? 17 : k === "frost" ? 15 : 22);
    // A frame round the blast's axis.
    const ax = new THREE.Vector3(1, 0, 0);
    if (Math.abs(dir.y) < 0.9) ax.crossVectors(dir, new THREE.Vector3(0, 1, 0)).normalize();
    const ay = new THREE.Vector3().crossVectors(ax, dir).normalize();
    while (this.acc >= 1) {
      this.acc -= 1;
      const p = this.spawn();
      if (!p) break;
      const cone = k === "water" ? 0.05 : k === "sand" ? 0.22 : k === "frost" ? 0.2 : 0.14;
      const a = r() * Math.PI * 2;
      const rr = Math.sqrt(r()) * cone;
      const vx = dir.x + (ax.x * Math.cos(a) + ay.x * Math.sin(a)) * rr;
      const vy = dir.y + (ax.y * Math.cos(a) + ay.y * Math.sin(a)) * rr;
      const vz = dir.z + (ax.z * Math.cos(a) + ay.z * Math.sin(a)) * rr;
      const sp = speed * (0.75 + r() * 0.5);
      Object.assign(p, {
        alive: true,
        x: mouth.x,
        y: mouth.y,
        z: mouth.z,
        vx: vx * sp,
        vy: vy * sp,
        vz: vz * sp,
        age: 0,
        drag: 0.9,
        rise: 0,
        whirl: 0,
        twinkle: 0,
        ax: mouth.x,
        ay: mouth.y,
        az: mouth.z,
        dx: dir.x,
        dy: dir.y,
        dz: dir.z,
      });
      const s = scale;
      if (k === "fire" || k === "kingfire") {
        const king = k === "kingfire";
        const core = r() < (king ? 0.45 : 0.3);
        p.glow = true;
        p.life = 0.7 + r() * 0.5;
        p.s0 = s * (core ? 0.9 : 1.4);
        p.s1 = s * (core ? 3.5 : 6.5);
        p.c0 = core ? hex(king ? "#fffbe8" : "#fff2b0", 0.95) : hex("#ffb030", 0.9);
        p.c1 = core ? hex(king ? "#ffc040" : "#ff7a10", 0.0) : hex("#c02008", 0.0);
        p.rise = s * 4;
        // Some smoke rolls off the flames.
        if (r() < 0.22) {
          p.glow = false;
          p.life = 1.4 + r();
          p.s0 = s * 2;
          p.s1 = s * 8;
          p.c0 = hex("#4a3a34", 0.0);
          p.c1 = hex("#2a2220", 0.0);
          p.c0[3] = 0.35;
          p.c1[3] = 0;
          p.rise = s * 5;
        }
      } else if (k === "frost") {
        const glint = r() < 0.3;
        p.glow = glint;
        p.life = glint ? 0.6 + r() * 0.6 : 1.1 + r() * 0.6;
        p.s0 = s * (glint ? 0.4 : 1.6);
        p.s1 = s * (glint ? 0.25 : 7.5);
        p.c0 = glint ? hex("#ffffff", 1) : hex("#eaf6ff", 0.55);
        p.c1 = glint ? hex("#9ad8ff", 0.0) : hex("#b8dcf8", 0.0);
        p.drag = 1.6;
        p.rise = -s * 1.5;
        p.twinkle = glint ? 1 : 0;
      } else if (k === "sand") {
        const gold = r() < 0.25;
        p.glow = gold;
        p.life = 1.0 + r() * 0.7;
        p.s0 = s * (gold ? 0.35 : 1.4);
        p.s1 = s * (gold ? 0.3 : 6);
        p.c0 = gold ? hex("#ffe08a", 0.9) : hex(r() < 0.5 ? "#e8c88a" : "#d0a060", 0.75);
        p.c1 = gold ? hex("#ffb040", 0) : hex("#b88a50", 0);
        p.whirl = (6 + r() * 4) * (r() < 0.5 ? 1 : 1);
        p.drag = 0.7;
        p.twinkle = gold ? 1 : 0;
      } else if (k === "water") {
        const spray = r() < 0.4;
        p.glow = !spray && r() < 0.35;
        p.life = spray ? 0.9 + r() * 0.5 : 0.55 + r() * 0.3;
        p.s0 = s * (spray ? 0.5 : 1.1);
        p.s1 = s * (spray ? 2.4 : 2.0);
        p.c0 = p.glow ? hex("#d8fbff", 0.7) : hex(spray ? "#e8f8ff" : "#5ac8e8", 0.8);
        p.c1 = p.glow ? hex("#6ad8f0", 0) : hex(spray ? "#ffffff" : "#2a8ab8", 0);
        p.rise = spray ? -s * 18 : -s * 9;
        p.drag = spray ? 1.4 : 0.3;
        if (spray) {
          p.vx += (r() - 0.5) * sp * 0.5;
          p.vy += r() * sp * 0.3;
          p.vz += (r() - 0.5) * sp * 0.5;
        }
      } else {
        // Light: a warm beam of motes and a soft bloom.
        const bloom = r() < 0.2;
        p.glow = true;
        p.life = bloom ? 0.8 + r() * 0.4 : 0.9 + r() * 0.8;
        p.s0 = s * (bloom ? 1.6 : 0.5);
        p.s1 = s * (bloom ? 5 : 0.3);
        p.c0 = bloom ? hex("#ffd878", 0.16) : hex("#fff2c0", 0.85);
        p.c1 = bloom ? hex("#ffc850", 0) : hex("#ffd060", 0);
        p.drag = 0.8;
        p.whirl = bloom ? 0 : 3;
        p.twinkle = bloom ? 0 : 1;
      }
    }
    // Smoke from a nostril (Cinderjaw's temper).
    if (nose && smoke > 0) {
      this.smokeAcc += smoke * 5 * dt;
      while (this.smokeAcc >= 1) {
        this.smokeAcc -= 1;
        const p = this.spawn();
        if (!p) break;
        Object.assign(p, {
          alive: true,
          glow: r() < 0.15,
          x: nose.x,
          y: nose.y,
          z: nose.z,
          vx: dir.x * scale * 2 + (r() - 0.5) * scale,
          vy: scale * (1.5 + r()),
          vz: dir.z * scale * 2 + (r() - 0.5) * scale,
          age: 0,
          life: 1.4 + r(),
          s0: scale * 0.3,
          s1: scale * 1.9,
          c0: hex("#6a5a52", 0.28),
          c1: hex("#3a302c", 0),
          drag: 1.2,
          rise: scale * 1.2,
          whirl: 0,
          twinkle: 0,
        });
        if (p.glow) {
          p.c0 = hex("#ff8a30", 0.8);
          p.c1 = hex("#ff4010", 0);
          p.s0 = scale * 0.25;
          p.s1 = scale * 0.15;
          p.life = 0.8;
        }
      }
    }
    // Lumen's aura: motes drifting up round him.
    if (centre && aura > 0) {
      this.auraAcc += aura * 26 * dt;
      while (this.auraAcc >= 1) {
        this.auraAcc -= 1;
        const p = this.spawn();
        if (!p) break;
        const a = r() * Math.PI * 2;
        const rad = scale * (3 + r() * 9);
        Object.assign(p, {
          alive: true,
          glow: true,
          x: centre.x + Math.cos(a) * rad,
          y: centre.y + (r() - 0.6) * scale * 10,
          z: centre.z + Math.sin(a) * rad,
          vx: 0,
          vy: scale * (1 + r() * 1.5),
          vz: 0,
          age: 0,
          life: 1.5 + r() * 1.5,
          s0: scale * 0.45,
          s1: scale * 0.1,
          c0: hex("#fff2b0", 0.9),
          c1: hex("#ffc040", 0),
          drag: 0.5,
          rise: 0,
          whirl: 0,
          twinkle: 1,
        });
      }
    }
    // Move and draw.
    let ng = 0;
    let nd = 0;
    const G = this.glow;
    const D = this.dust;
    for (const p of this.ps) {
      if (!p.alive) continue;
      p.age += dt;
      if (p.age >= p.life) {
        p.alive = false;
        continue;
      }
      const f = Math.exp(-p.drag * dt);
      p.vx *= f;
      p.vy = p.vy * f + p.rise * dt;
      p.vz *= f;
      if (p.whirl) {
        // Swirl round the blast's axis.
        const ox = p.x - p.ax;
        const oy = p.y - p.ay;
        const oz = p.z - p.az;
        const along = ox * p.dx + oy * p.dy + oz * p.dz;
        const rx = ox - p.dx * along;
        const ry = oy - p.dy * along;
        const rz = oz - p.dz * along;
        // Tangent = d x r.
        const tx = p.dy * rz - p.dz * ry;
        const ty = p.dz * rx - p.dx * rz;
        const tz = p.dx * ry - p.dy * rx;
        const w = p.whirl * dt;
        p.x += tx * w;
        p.y += ty * w;
        p.z += tz * w;
        // And widen as it goes.
        const grow = 0.6 * dt;
        p.x += rx * grow;
        p.y += ry * grow;
        p.z += rz * grow;
      }
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.z += p.vz * dt;
      // Spread along the ground.
      if (p.y < ground + 0.3 * scale) {
        p.y = ground + 0.3 * scale;
        if (p.vy < 0) {
          const hs = Math.hypot(p.vx, p.vz) || 1;
          const add = -p.vy * 0.6;
          p.vx += (p.vx / hs) * add;
          p.vz += (p.vz / hs) * add;
          p.vy = k === "water" ? -p.vy * 0.25 : 0;
        }
      }
      const e = p.age / p.life;
      const L = p.glow ? G : D;
      const i = p.glow ? ng++ : nd++;
      L.pos[i * 3] = p.x;
      L.pos[i * 3 + 1] = p.y;
      L.pos[i * 3 + 2] = p.z;
      const tw = p.twinkle ? 0.55 + 0.45 * Math.sin(time * 23 + p.s0 * 97 + i) : 1;
      L.size[i] = (p.s0 + (p.s1 - p.s0) * Math.sqrt(e)) * tw;
      const fadeIn = Math.min(1, p.age / 0.08);
      for (let c = 0; c < 3; c++) L.tint[i * 4 + c] = p.c0[c]! + (p.c1[c]! - p.c0[c]!) * e;
      L.tint[i * 4 + 3] = (p.c0[3] + (p.c1[3] - p.c0[3]) * e) * fadeIn * tw;
    }
    for (const [L, n] of [
      [G, ng],
      [D, nd],
    ] as const) {
      L.geo.setDrawRange(0, n);
      L.geo.attributes.position!.needsUpdate = true;
      L.geo.attributes.size!.needsUpdate = true;
      L.geo.attributes.tint!.needsUpdate = true;
      L.points.visible = n > 0;
    }
  }

  /** Is anything still in the air? */
  get busy() {
    return this.ps.some((p) => p.alive);
  }

  dispose() {
    this.group.removeFromParent();
    for (const L of [this.glow, this.dust]) {
      L.geo.dispose();
      L.mat.dispose();
    }
  }
}
