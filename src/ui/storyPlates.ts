/**
 * The opening storybook's pictures (The First Race): each page an inked, washed plate
 * of the real models (the story dragons, the racers in their karts, the Pact Stones, the
 * Founders' Horn) in a small 3D set, rendered offscreen and turned into an illustration:
 *
 *   - a colour pass, softened into a watercolour wash: colours eased toward the paper,
 *     stepped into a few tones, dark tones hatched with ink;
 *   - a normal pass and a depth pass, from which the ink lines are found (outlines where
 *     the depth jumps, lighter creases where the surface turns);
 *   - edges that bleed out into the paper.
 *
 * The plate is drawn over the parchment with "multiply", so the paper shows through the
 * wash like paint on a page. Animated (wings beat, karts roll, the camera drifts) at a
 * storybook's twelve pictures a second, or a still with reduced motion.
 *
 *   const plates = createStoryPlates(renderer);
 *   const img = plates.draw(page, t, still);   // a canvas, plates.W x plates.H
 *   plates.dispose();
 */
import * as THREE from "three";
import { Racer, type RacerMotion } from "../render/racers/racer";
import type { RacerId } from "../render/racers/designs";
import { createStoryDragon, type DesignId, type StoryDragonView } from "../render/storyDragon";
import type { StoryPose } from "../adventure/staged";
import { createPactStoneView, type PropView } from "../render/storyProps";
import { hornGeometry } from "../render/people/parts";
import { skinMaterial } from "../render/racers/kit/paint";
import { createVillagerView, type Folk, type Species } from "../render/villager";
import type { PersonView } from "../render/people/view";

/** The plate's size in UI pixels (2:1), and how many rendered pixels to each. */
export const PLATE_W = 264;
export const PLATE_H = 132;
const RES = 3;

/** The ink. */
const INK: [number, number, number] = [42, 26, 16];

/** One page's set. */
interface Plate {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  update(t: number, dt: number): void;
  /** Ink drawn over the finished plate (the horn's blast), in plate pixels. */
  overlay?(
    g: CanvasRenderingContext2D,
    t: number,
    project: (p: THREE.Vector3) => THREE.Vector2,
  ): void;
  dispose(): void;
}

// ------------------------------------------------------------------ the set's kit

/** The war's dragons, each a shade off the one who carries the line now. */
const FOREBEAR: Partial<Record<DesignId, string>> = {
  cinderjaw: "#b8c4a0",
  rimefang: "#dcc4e4",
  scorchwind: "#b0d0c4",
  tidewyrm: "#e4ccac",
};

const rnd = (seed: number) => {
  let s = seed >>> 0 || 1;
  return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
};
const smooth = (a: number, b: number, x: number) => {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

const still = (): RacerMotion => ({
  speed: 0,
  steer: 0,
  driftDir: 0,
  slip: 0,
  grounded: true,
  throttle: false,
  boostPhase: 0,
  boostEnhanced: false,
  boostLeft: 0,
  impactTier: 0,
  impactSpeed: 0,
  spinTime: 0,
});

/** Builds a set, and keeps what it made so it can all be thrown away. */
class Kit {
  readonly scene = new THREE.Scene();
  private geos: THREE.BufferGeometry[] = [];
  private mats = new Map<string, THREE.Material>();
  private extra: THREE.Material[] = [];
  racers: { r: Racer; m: RacerMotion }[] = [];
  dragons: StoryDragonView[] = [];
  props: PropView[] = [];
  people: PersonView[] = [];
  /** Things the line passes skip (light, glow, smoke). */
  readonly fx = new Set<THREE.Object3D>();
  /** The ground's height (set by ground()). */
  height: (x: number, z: number) => number = () => 0;

  constructor() {
    const sun = new THREE.DirectionalLight("#fff2dc", 2.4);
    sun.position.set(40, 80, 50);
    this.scene.add(sun, new THREE.HemisphereLight("#f4f0e4", "#8a7458", 1.5));
  }

  mat(color: string, glow = 0, flat = true): THREE.Material {
    const key = `${color}|${glow}|${flat}`;
    let m = this.mats.get(key);
    if (!m) {
      m = new THREE.MeshLambertMaterial({
        color,
        flatShading: flat,
        ...(glow ? { emissive: new THREE.Color(color), emissiveIntensity: glow } : {}),
      });
      this.mats.set(key, m);
    }
    return m;
  }

  /** A material seen from both sides (ribbons laid on the ground). */
  twoSided(color: string) {
    const m = new THREE.MeshLambertMaterial({ color, side: THREE.DoubleSide });
    this.extra.push(m);
    return m;
  }

  mesh(g: THREE.BufferGeometry, m: THREE.Material, parent: THREE.Object3D = this.scene) {
    this.geos.push(g);
    const o = new THREE.Mesh(g, m);
    parent.add(o);
    return o;
  }

  /** Something drawn in the colour pass only (glowing, see-through). */
  glow(g: THREE.BufferGeometry, color: string, opacity: number, parent?: THREE.Object3D) {
    const m = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      depthWrite: false,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
    });
    this.extra.push(m);
    const o = this.mesh(g, m, parent);
    this.fx.add(o);
    return o;
  }

  /** Rolling ground in the land's colours, flat in the middle where the action is. */
  ground(colors: [string, string], hills = 1, flat = 90) {
    const g = new THREE.PlaneGeometry(900, 900, 150, 150);
    g.rotateX(-Math.PI / 2);
    const h = (x: number, z: number) => {
      const d = Math.hypot(x, z);
      const k = smooth(flat, flat + 200, d);
      return (
        (Math.sin(x * 0.045) * Math.cos(z * 0.038) * 0.6 +
          k * (Math.sin(x * 0.021 + 1.3) * Math.cos(z * 0.017) * 9 + Math.sin(x * 0.06) * 2 + 4)) *
        hills
      );
    };
    this.height = h;
    const p = g.getAttribute("position") as THREE.BufferAttribute;
    const col = new Float32Array(p.count * 3);
    const a = new THREE.Color(colors[0]);
    const b = new THREE.Color(colors[1]);
    const c = new THREE.Color();
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i);
      const z = p.getZ(i);
      p.setY(i, h(x, z));
      const n = 0.5 + 0.5 * Math.sin(x * 0.13 + Math.cos(z * 0.11) * 2) * Math.cos(z * 0.09);
      c.copy(a).lerp(b, n);
      col.set([c.r, c.g, c.b], i * 3);
    }
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    g.computeVertexNormals();
    const m = new THREE.MeshLambertMaterial({ vertexColors: true });
    this.extra.push(m);
    this.mesh(g, m);
  }

  /** A dirt road along a smooth curve through `pts` (x, z). Returns the curve. */
  road(pts: [number, number][], w = 9, color = "#c8a878") {
    const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, 0, z)));
    const n = 120;
    const pos: number[] = [];
    const idx: number[] = [];
    const t = new THREE.Vector3();
    for (let i = 0; i <= n; i++) {
      const u = i / n;
      const p = curve.getPointAt(u);
      curve.getTangentAt(u, t);
      const sx = -t.z;
      const sz = t.x;
      for (const s of [-1, 1]) {
        const x = p.x + sx * s * (w / 2);
        const z = p.z + sz * s * (w / 2);
        pos.push(x, this.height(x, z) + 0.3, z);
      }
      if (i < n) {
        const k = i * 2;
        idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    this.mesh(g, this.twoSided(color));
    // Its worn edges, a darker rut each side.
    for (const s of [-1, 1]) {
      const e: number[] = [];
      for (let i = 0; i <= n; i++) {
        const u = i / n;
        const p = curve.getPointAt(u);
        curve.getTangentAt(u, t);
        for (const o of [w / 2 - 0.5, w / 2 + 0.3]) {
          const x = p.x - t.z * s * o;
          const z = p.z + t.x * s * o;
          e.push(x, this.height(x, z) + 0.36, z);
        }
      }
      const eg = new THREE.BufferGeometry();
      eg.setAttribute("position", new THREE.Float32BufferAttribute(e, 3));
      eg.setIndex(idx);
      eg.computeVertexNormals();
      this.mesh(eg, this.twoSided("#9a7a52"));
    }
    return curve;
  }

  /** A point along a road, its heading, and a point off to its side. */
  along(curve: THREE.CatmullRomCurve3, u: number, side = 0) {
    const p = curve.getPointAt(u);
    const t = curve.getTangentAt(u);
    const x = p.x - t.z * side;
    const z = p.z + t.x * side;
    return { x, y: this.height(x, z), z, heading: Math.atan2(t.x, t.z) };
  }

  /** A chequered line across the road, and an arch over it hung with a banner. */
  startLine(x: number, z: number, heading: number, w = 10, arch = true) {
    const grp = new THREE.Group();
    grp.position.set(x, this.height(x, z) + 0.14, z);
    grp.rotation.y = heading;
    this.scene.add(grp);
    const cells = 10;
    for (let i = 0; i < cells; i++)
      for (let j = 0; j < 2; j++) {
        const c = this.mesh(
          new THREE.BoxGeometry(w / cells, 0.06, 0.7),
          this.mat((i + j) % 2 ? "#2a2018" : "#f4ecd8"),
          grp,
        );
        c.position.set(-w / 2 + (i + 0.5) * (w / cells), 0, (j - 0.5) * 0.7);
      }
    if (arch) {
      for (const s of [-1, 1]) {
        const post = this.mesh(
          new THREE.CylinderGeometry(0.28, 0.36, 9, 6),
          this.mat("#7a5434"),
          grp,
        );
        post.position.set(s * (w / 2 + 0.8), 4.5, 0);
        const cap = this.mesh(new THREE.ConeGeometry(0.6, 1.2, 6), this.mat("#b03a24"), grp);
        cap.position.set(s * (w / 2 + 0.8), 9.6, 0);
      }
      const bar = this.mesh(new THREE.BoxGeometry(w + 2.2, 0.4, 0.4), this.mat("#7a5434"), grp);
      bar.position.y = 8.6;
      const flag = this.mesh(new THREE.BoxGeometry(w * 0.8, 1.6, 0.12), this.mat("#e8d8b0"), grp);
      flag.position.y = 7.5;
      for (let i = 0; i < 8; i++) {
        const c = this.mesh(
          new THREE.BoxGeometry((w * 0.8) / 8, 0.8, 0.14),
          this.mat("#2a2018"),
          grp,
        );
        c.position.set(-w * 0.4 + (i + 0.5) * ((w * 0.8) / 8), 7.5 + (i % 2 ? 0.4 : -0.4), 0);
      }
    }
    return grp;
  }

  tree(x: number, z: number, kind: "pine" | "round" | "palm" | "burnt", s = 1) {
    const y = this.height(x, z);
    const grp = new THREE.Group();
    grp.position.set(x, y, z);
    grp.scale.setScalar(s);
    this.scene.add(grp);
    const trunk = this.mesh(
      new THREE.CylinderGeometry(0.3, 0.5, kind === "palm" ? 7 : 3.4, 5),
      this.mat(kind === "burnt" ? "#2a2420" : "#6a4a2c"),
      grp,
    );
    trunk.position.y = kind === "palm" ? 3.5 : 1.7;
    if (kind === "pine")
      for (let i = 0; i < 3; i++) {
        const c = this.mesh(
          new THREE.ConeGeometry(2.4 - i * 0.6, 3, 7),
          this.mat(i % 2 ? "#4a6e3a" : "#3e6232"),
          grp,
        );
        c.position.y = 3.2 + i * 1.6;
      }
    else if (kind === "round") {
      const c = this.mesh(new THREE.IcosahedronGeometry(2.4, 1), this.mat("#6a8a42"), grp);
      c.position.y = 4.6;
      c.scale.set(1, 0.85, 1);
    } else if (kind === "palm")
      for (let i = 0; i < 6; i++) {
        const leaf = this.mesh(new THREE.ConeGeometry(0.6, 4.4, 4), this.mat("#5a8a3a"), grp);
        const a = (i / 6) * Math.PI * 2;
        leaf.position.set(Math.sin(a) * 1.6, 6.9, Math.cos(a) * 1.6);
        leaf.rotation.set(Math.cos(a) * 1.9, 0, -Math.sin(a) * 1.9);
      }
    else
      for (let i = 0; i < 3; i++) {
        const b = this.mesh(
          new THREE.CylinderGeometry(0.1, 0.18, 1.8, 4),
          this.mat("#2a2420"),
          grp,
        );
        b.position.set((i - 1) * 0.5, 2.8 + i * 0.3, 0);
        b.rotation.z = (i - 1) * 0.8;
      }
    return grp;
  }

  house(x: number, z: number, rot: number, wall = "#e0cca0", roof = "#9a4a2a", s = 1) {
    const grp = new THREE.Group();
    grp.position.set(x, this.height(x, z), z);
    grp.rotation.y = rot;
    grp.scale.setScalar(s);
    this.scene.add(grp);
    const w = this.mesh(new THREE.BoxGeometry(5, 3.4, 4), this.mat(wall), grp);
    w.position.y = 1.7;
    const r = this.mesh(new THREE.CylinderGeometry(0.01, 3.6, 2.6, 4, 1), this.mat(roof), grp);
    r.rotation.y = Math.PI / 4;
    r.scale.set(1, 1, 0.8);
    r.position.y = 4.7;
    const d = this.mesh(new THREE.BoxGeometry(1.1, 1.8, 0.1), this.mat("#5a3a22"), grp);
    d.position.set(0, 0.9, 2.02);
    const win = this.mesh(new THREE.BoxGeometry(0.9, 0.8, 0.1), this.mat("#3a2a1a"), grp);
    win.position.set(1.5, 2.1, 2.02);
    return grp;
  }

  mountain(x: number, z: number, h: number, r: number, snow = true, color = "#8a8070") {
    const y = this.height(x, z) - 4;
    h *= 0.55;
    r *= 0.8;
    const m = this.mesh(new THREE.ConeGeometry(r, h, 7, 2), this.mat(color));
    m.position.set(x, y + h / 2, z);
    m.rotation.y = x * 0.1;
    if (snow) {
      const s = this.mesh(new THREE.ConeGeometry(r * 0.36, h * 0.36, 7), this.mat("#f4f0e8"));
      s.position.set(x, y + h - h * 0.18 + 0.2, z);
      s.rotation.y = m.rotation.y;
    }
  }

  /** The Dragon Kingdom's citadel, far off: towers on a crag. */
  citadel(x: number, z: number, s = 1) {
    const grp = new THREE.Group();
    grp.position.set(x, this.height(x, z), z);
    grp.scale.setScalar(s);
    this.scene.add(grp);
    const crag = this.mesh(new THREE.ConeGeometry(16, 22, 6), this.mat("#6a5a50"), grp);
    crag.position.y = 8;
    const towers: [number, number, number, number][] = [
      [0, 0, 3.2, 26],
      [-6, 2, 2.2, 18],
      [6, 1, 2.4, 20],
      [-3, -4, 1.8, 15],
      [4, -4, 1.8, 16],
    ];
    for (const [tx, tz, r, h] of towers) {
      const t = this.mesh(new THREE.CylinderGeometry(r * 0.8, r, h, 6), this.mat("#5a4a48"), grp);
      t.position.set(tx, 14 + h / 2, tz);
      const c = this.mesh(new THREE.ConeGeometry(r * 1.3, r * 2.6, 6), this.mat("#8a2a20"), grp);
      c.position.set(tx, 14 + h + r * 1.3, tz);
    }
  }

  /** The border: a standing curtain of dragon light along `pts`. */
  border(pts: [number, number][], h = 26) {
    const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, 0, z)));
    const n = 60;
    const pos: number[] = [];
    const uv: number[] = [];
    const idx: number[] = [];
    for (let i = 0; i <= n; i++) {
      const p = curve.getPointAt(i / n);
      const y = this.height(p.x, p.z);
      pos.push(p.x, y, p.z, p.x, y + h, p.z);
      uv.push(i / n, 0, i / n, 1);
      if (i < n) idx.push(i * 2, i * 2 + 2, i * 2 + 1, i * 2 + 1, i * 2 + 2, i * 2 + 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    // Brightest at the foot, fading up.
    const cv = document.createElement("canvas");
    cv.width = 64;
    cv.height = 64;
    const c = cv.getContext("2d")!;
    const grad = c.createLinearGradient(0, 64, 0, 0);
    grad.addColorStop(0, "rgba(214,138,24,1)");
    grad.addColorStop(0.45, "rgba(228,160,50,0.75)");
    grad.addColorStop(1, "rgba(240,190,90,0)");
    c.fillStyle = grad;
    c.fillRect(0, 0, 64, 64);
    // Streaks of light rising through it.
    c.globalCompositeOperation = "destination-out";
    for (let i = 0; i < 64; i += 4) {
      c.fillStyle = `rgba(0,0,0,${0.25 + ((i * 7) % 5) * 0.1})`;
      c.fillRect(i, 0, 2, 64);
    }
    const tex = new THREE.CanvasTexture(cv);
    tex.wrapS = THREE.RepeatWrapping;
    tex.repeat.set(12, 1);
    const m = new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      opacity: 1,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    this.extra.push(m);
    const o = this.mesh(g, m);
    o.userData.fx = true;
    // Marker posts along its foot (stone cairns), drawn in ink.
    for (let i = 0; i <= 10; i++) {
      const p = curve.getPointAt(i / 10);
      const cairn = this.mesh(new THREE.DodecahedronGeometry(1.1, 0), this.mat("#8a8070"));
      cairn.position.set(p.x, this.height(p.x, p.z) + 0.6, p.z);
      cairn.scale.set(1, 1.5, 1);
    }
    return { mesh: o, material: m, texture: tex };
  }

  /** An hourglass on a stone post: `sand` 1 all in the top, 0 all run out. */
  hourglass(x: number, z: number, sand: number, tipped = 0) {
    const grp = new THREE.Group();
    grp.position.set(x, this.height(x, z), z);
    this.scene.add(grp);
    const post = this.mesh(new THREE.CylinderGeometry(1.1, 1.3, 3, 6), this.mat("#8a8070"), grp);
    post.position.y = 1.5;
    const glass = new THREE.Group();
    glass.position.y = 3;
    glass.rotation.z = tipped;
    grp.add(glass);
    const wood = this.mat("#6a4426");
    for (const y of [0.15, 4.25]) {
      const disc = this.mesh(new THREE.CylinderGeometry(1.4, 1.4, 0.3, 8), wood, glass);
      disc.position.y = y;
    }
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2;
      const rod = this.mesh(new THREE.CylinderGeometry(0.1, 0.1, 4.1, 4), wood, glass);
      rod.position.set(Math.cos(a) * 1.15, 2.2, Math.sin(a) * 1.15);
    }
    // The two bulbs, and the sand.
    const bulb = this.mat("#e8e0cc");
    const top = this.mesh(new THREE.ConeGeometry(1, 1.9, 10), bulb, glass);
    top.position.y = 3.2;
    top.rotation.x = Math.PI;
    const bot = this.mesh(new THREE.ConeGeometry(1, 1.9, 10), bulb, glass);
    bot.position.y = 1.25;
    bot.rotation.x = Math.PI;
    bot.scale.y = -1;
    const sandMat = this.mat("#d0a050");
    if (sand > 0.05) {
      const s = this.mesh(new THREE.ConeGeometry(0.85 * sand, 1.6 * sand, 10), sandMat, glass);
      s.position.y = 2.3 + 0.8 * sand + 0.2;
      s.rotation.x = Math.PI;
    }
    if (sand < 0.95) {
      const k = 1 - sand;
      const s = this.mesh(new THREE.ConeGeometry(0.9, 1.4 * k, 10), sandMat, glass);
      s.position.y = 0.3 + 0.7 * k;
    }
    return grp;
  }

  /** A racer of the first crews: today's racers' ancestors, in their other paint. */
  racer(id: RacerId, x: number, z: number, heading: number, speed = 0, alt = true) {
    const r = new Racer(id, { seed: id.length * 5 + 1, alt });
    r.lod.autoUpdate = false;
    r.lod.levels.forEach((l, i) => (l.object.visible = i === 0));
    r.root.position.set(x, this.height(x, z), z);
    r.root.rotation.y = heading;
    this.scene.add(r.root);
    const m = still();
    m.speed = speed;
    m.throttle = speed > 0;
    this.racers.push({ r, m });
    return r;
  }

  /** A dragon of the war. The King is the King (he's lived the thousand years); the
   * others are their forebears, today's dragons a shade different. */
  dragon(who: DesignId, x: number, y: number, z: number, heading: number, scale: number) {
    const d = createStoryDragon(this.scene, who, scale);
    const tint = FOREBEAR[who];
    if (tint) {
      const c = new THREE.Color(tint);
      const seen = new Set<THREE.Material>();
      d.root.traverse((o) => {
        const m = (o as THREE.Mesh).material as THREE.MeshLambertMaterial | undefined;
        if (!m || Array.isArray(m) || seen.has(m) || !m.color || m.transparent) return;
        seen.add(m);
        m.color.multiply(c);
      });
    }
    d.root.position.set(x, this.height(x, z) + y, z);
    d.root.rotation.y = heading;
    d.ground = this.height(x, z);
    this.dragons.push(d);
    return d;
  }

  stone(x: number, z: number, heading: number, big = false, s = 1) {
    const v = createPactStoneView(this.scene, "old", big);
    v.root.scale.setScalar(s);
    v.update(x, this.height(x, z), z, heading, 0);
    this.props.push(v);
    return v;
  }

  folk(folk: Folk, seed: number, x: number, z: number, heading: number, kind?: Species) {
    const p = createVillagerView(this.scene, folk, seed, kind);
    p.update(x, this.height(x, z), z, heading, { gesture: "cheer" }, 0);
    this.people.push(p);
    return p;
  }

  /** Puffs of smoke (drawn in the colour pass only). */
  smoke(x: number, y: number, z: number, n: number, seed: number) {
    const r = rnd(seed);
    for (let i = 0; i < n; i++) {
      const s = this.mesh(
        new THREE.IcosahedronGeometry(2 + r() * 2.5, 0),
        this.mat(i % 2 ? "#6a625a" : "#847a70"),
      );
      s.position.set(x + (r() - 0.5) * 6, y + i * 2.6, z + (r() - 0.5) * 6);
    }
  }

  animate(dt: number) {
    for (const { r, m } of this.racers) r.animate(dt, m, null);
  }

  dispose() {
    for (const { r } of this.racers) r.root.removeFromParent();
    for (const d of this.dragons) d.dispose();
    for (const p of this.props) p.dispose();
    for (const p of this.people) p.dispose();
    for (const g of this.geos) g.dispose();
    for (const m of this.mats.values()) m.dispose();
    for (const m of this.extra) {
      (m as THREE.MeshBasicMaterial).map?.dispose();
      m.dispose();
    }
  }
}

/** The camera, drifting slowly from `a` toward `b` while looking at `at`. */
function drift(
  camera: THREE.PerspectiveCamera,
  a: [number, number, number],
  b: [number, number, number],
  at: [number, number, number],
  t: number,
) {
  const k = smooth(0, 1, t / 14);
  camera.position.set(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k);
  camera.lookAt(at[0], at[1], at[2]);
}

const camOf = (fov = 38) => new THREE.PerspectiveCamera(fov, PLATE_W / PLATE_H, 1, 900);
const look = new THREE.Vector3();

/** Pose a dragon (and flap): `bob` metres of rise and fall. */
function fly(
  d: StoryDragonView,
  pose: StoryPose,
  t: number,
  y0: number,
  bob = 0.8,
  at?: THREE.Vector3,
) {
  d.root.position.y = y0 + Math.sin(t * 1.6 + d.root.position.x) * bob;
  const fwd = new THREE.Vector3(Math.sin(d.root.rotation.y), 0, Math.cos(d.root.rotation.y));
  d.update(pose, t, t, at ?? look.copy(d.root.position).addScaledVector(fwd, 60), false);
}

// ------------------------------------------------------------------ the pages

/** 1. The war: dragons over the crews' karts, fire on the plain. */
function war(): Plate {
  const k = new Kit();
  k.ground(["#a8b878", "#8aa060"]);
  k.road([
    [-90, 40],
    [-30, 18],
    [10, 2],
    [50, -22],
    [120, -70],
  ]);
  const flee = Math.atan2(-1, 0.4);
  k.racer("tiko", -6, 20, flee, 30);
  k.racer("brakka", 2, 15, flee, 30);
  k.racer("pebble", 10, 10, flee, 30);
  const fire = k.dragon("cinderjaw", 16, 10, 0, -Math.PI / 2 - 0.25, 0.3);
  const frost = k.dragon("rimefang", -12, 14, -8, -Math.PI / 2 + 0.2, 0.26);
  const sand = k.dragon("scorchwind", 30, 16, -20, -Math.PI / 2, 0.24);
  const r = rnd(4);
  for (let i = 0; i < 16; i++)
    k.tree(-90 + r() * 180, -40 - r() * 60, i % 3 ? "pine" : "round", 1 + r() * 0.6);
  for (let i = 0; i < 4; i++) k.tree(14 + i * 5, -14 + (i % 2) * 4, "burnt", 1.1);
  k.mountain(-160, -320, 90, 80, true);
  k.mountain(60, -360, 120, 100, true);
  k.mountain(220, -300, 80, 70, true);
  const camera = camOf(40);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      fly(fire, "breathe", t, 8, 0.5, look.set(-6, 0, 20));
      fly(frost, "fly", t, 10.5);
      fly(sand, "fly", t, 12);
      drift(camera, [-2, 6, 40], [1, 6, 37], [4, 6, 4], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 2. The oath, before the race: the King and the crews either side of the start line,
 * the oath's light rising between them. */
function oath(): Plate {
  const k = new Kit();
  k.ground(["#b8c088", "#a0ac74"]);
  k.road([
    [0, 80],
    [0, 20],
    [0, -40],
    [6, -160],
  ]);
  k.startLine(0, 0, 0, 12);
  const king = k.dragon("king", -15, 0, -4, Math.PI / 2 - 0.35, 0.34);
  const crew: [RacerId, number, number][] = [
    ["tiko", 9, 2],
    ["brakka", 12, -3],
    ["zephyr", 14, 5],
  ];
  for (const [id, x, z] of crew) k.racer(id, x, z, -Math.PI / 2 - 0.3, 0);
  // The oath: a ring of light on the line, a column rising from it.
  const ring = k.glow(new THREE.TorusGeometry(2.6, 0.22, 6, 32), "#ffd070", 0.9);
  ring.rotation.x = Math.PI / 2;
  ring.position.set(0, 0.5, 0);
  const column = k.glow(new THREE.CylinderGeometry(2.2, 2.6, 26, 20, 1, true), "#ffd890", 0.35);
  column.position.set(0, 13, 0);
  // Both sides' banners behind.
  for (const [x, c] of [
    [-22, "#8a2a20"],
    [22, "#2a5a8a"],
  ] as const) {
    const pole = k.mesh(new THREE.CylinderGeometry(0.25, 0.25, 13, 5), k.mat("#6a4426"));
    pole.position.set(x, 6.5, -14);
    const cloth = k.mesh(new THREE.BoxGeometry(4, 5.5, 0.2), k.mat(c));
    cloth.position.set(x - 2.2 * Math.sign(x), 10, -14);
  }
  const r = rnd(7);
  for (let i = 0; i < 12; i++) k.tree(-90 + r() * 180, -36 - r() * 50, "pine", 1.1 + r());
  k.mountain(-100, -320, 90, 90, true);
  k.mountain(90, -340, 110, 100, true);
  const camera = camOf(38);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      king.ground = 0;
      king.update("bow", t, t, look.set(0, 3, 0), false);
      ring.rotation.z = t * 0.4;
      (column.material as THREE.MeshBasicMaterial).opacity = 0.3 + 0.08 * Math.sin(t * 2);
      drift(camera, [0, 6, 32], [0, 5.5, 28], [0, 5, -3], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 3. Rule one: the border of light; a dragon beyond it, the villages safe this side. */
function ruleBorder(): Plate {
  const k = new Kit();
  k.ground(["#b8c088", "#9eae76"]);
  const b = k.border([
    [-120, -8],
    [-40, -14],
    [20, -10],
    [80, -18],
    [150, -14],
  ]);
  k.house(-16, 4, 0.3);
  k.house(-6, 9, -0.2, "#e8d4a8", "#7a4a2a");
  k.house(-24, 12, 0.6, "#dcc8a0", "#8a3a22");
  k.racer("pebble", 5, 10, 2.4, 0);
  k.tree(14, 20, "round", 1);
  k.tree(-32, 8, "round", 1);
  const d = k.dragon("cinderjaw", 14, 0, -26, -1.25, 0.34);
  k.citadel(30, -170, 1.3);
  k.mountain(-110, -220, 90, 70, true, "#7a6a64");
  k.mountain(130, -230, 90, 70, true, "#7a6a64");
  const camera = camOf(40);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      d.ground = d.root.position.y;
      d.update("idle", t, t, look.set(-6, 4, 24), false);
      b.material.opacity = 0.85 + 0.15 * Math.sin(t * 1.7);
      drift(camera, [-4, 8, 44], [-2, 7.5, 40], [2, 6, -8], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 4. Rule two: every hundred years, a champion at the line facing the King. */
function ruleChampion(): Plate {
  const k = new Kit();
  k.ground(["#c0bc88", "#a8a474"]);
  k.road([
    [-160, 0],
    [0, 0],
    [160, 0],
  ]);
  k.startLine(0, 0, Math.PI / 2, 12, false);
  const champ = k.racer("tiko", -5, 0, Math.PI / 2, 0);
  // The champion's gold pennant.
  const pole = k.mesh(new THREE.CylinderGeometry(0.06, 0.06, 4, 4), k.mat("#5a3a22"), champ.root);
  pole.position.set(-0.7, 2.6, -1.6);
  const pen = k.mesh(new THREE.ConeGeometry(0.55, 1.8, 3), k.mat("#e8b830", 0.2), champ.root);
  pen.rotation.z = -Math.PI / 2;
  pen.position.set(-0.7, 4.1, -1.6);
  const king = k.dragon("king", 13, 0, -1, -Math.PI / 2, 0.26);
  k.hourglass(0, -7, 1);
  const r = rnd(2);
  for (let i = 0; i < 10; i++) k.tree(-100 + r() * 200, -30 - r() * 50, "round", 1 + r() * 0.6);
  k.mountain(0, -320, 110, 100, true);
  const camera = camOf(38);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      king.ground = 0;
      king.update("idle", t, t, look.set(-6, 2, 0), false);
      drift(camera, [-2, 4, 24], [0, 4, 21], [2, 4, -1], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 5. Rule three: the hundred years run out, no champion at the line, and the dragons
 * come over the villages. */
function ruleForfeit(): Plate {
  const k = new Kit();
  k.ground(["#b8b080", "#a09868"]);
  k.road([
    [-160, 8],
    [0, 8],
    [160, 8],
  ]);
  k.startLine(-12, 8, Math.PI / 2, 12, false);
  k.hourglass(-9, 3, 0, 0);
  k.house(8, -10, 0.2);
  k.house(20, -4, -0.4, "#e8d4a8", "#7a4a2a");
  k.house(18, -20, 0.5, "#dcc8a0", "#8a3a22");
  k.house(32, -14, 0.1);
  k.tree(2, -22, "round", 1.1);
  k.tree(36, -2, "round", 1.1);
  const d1 = k.dragon("cinderjaw", 14, 11, -8, -2.5, 0.27);
  const d2 = k.dragon("scorchwind", 0, 18, -30, -2.0, 0.2);
  k.mountain(-60, -300, 100, 90, true);
  k.mountain(120, -320, 110, 90, true);
  const camera = camOf(40);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      fly(d1, "fly", t, 11, 0.6, look.set(0, 0, 30));
      fly(d2, "fly", t, 18);
      drift(camera, [-14, 5, 24], [-12, 5, 21], [4, 6, -6], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 6. The race begins: the crews' karts off the line, the dragons lifting off beside
 * them, both sides' banners, the crowd. */
function raceStart(): Plate {
  const k = new Kit();
  k.ground(["#b8c088", "#a0ac74"]);
  k.road(
    [
      [0, -120],
      [0, -20],
      [0, 40],
      [-8, 140],
    ],
    14,
  );
  k.startLine(0, -2, 0, 15);
  k.racer("tiko", -4, 4, 0.05, 40);
  k.racer("brakka", 1, 6.5, -0.03, 40);
  k.racer("pebble", 5, 3, 0.02, 40);
  const d1 = k.dragon("cinderjaw", -9.5, 3, 2, 0.1, 0.2);
  const d2 = k.dragon("rimefang", 10, 4.5, 0, -0.1, 0.18);
  // Both sides' banners at the line, and the crowd either side.
  for (const [x, c] of [
    [-11, "#8a2a20"],
    [11, "#2a5a8a"],
  ] as const) {
    const pole = k.mesh(new THREE.CylinderGeometry(0.2, 0.2, 10, 5), k.mat("#6a4426"));
    pole.position.set(x, 5, -4);
    const cloth = k.mesh(new THREE.BoxGeometry(3, 4, 0.15), k.mat(c));
    cloth.position.set(x - 1.6 * Math.sign(x), 7.6, -4);
  }
  const r = rnd(21);
  for (let i = 0; i < 6; i++) k.folk("valley", 70 + i, -13 - r() * 4, 2 + i * 3.5, Math.PI / 2);
  for (let i = 0; i < 6; i++) k.folk("valley", 80 + i, 13 + r() * 4, 2 + i * 3.5, -Math.PI / 2);
  for (let i = 0; i < 10; i++) k.tree(-90 + r() * 180, -40 - r() * 50, "round", 1 + r());
  k.mountain(-80, -300, 100, 90, true);
  k.mountain(90, -320, 110, 90, true);
  const camera = camOf(42);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      fly(d1, "fly", t, 3 + Math.min(1, t / 6) * 2, 0.3);
      fly(d2, "fly", t, 4.5 + Math.min(1, t / 6) * 2, 0.3);
      drift(camera, [3, 3.6, 26], [2, 3.6, 24], [0, 4.5, -2], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 7. The race's last turn: the dragons ahead, the karts behind, and a horn raised out
 * of the crowd at the bend (whose hand, the picture doesn't show). */
function horn(): Plate {
  const k = new Kit();
  k.ground(["#b4bc84", "#9cac70"]);
  k.road(
    [
      [8, 40],
      [3, 16],
      [-1, 7],
      [-8, 2],
      [-20, -2],
      [-60, -4],
    ],
    9,
  );
  // The dragons ahead round the bend, flying low; the karts behind them.
  const d1 = k.dragon("cinderjaw", -9, 5.5, 1, -Math.PI / 2 - 0.15, 0.24);
  const d2 = k.dragon("rimefang", -20, 4.5, -6, -Math.PI / 2 + 0.1, 0.22);
  const into = Math.atan2(-8.8, -6.3);
  k.racer("tiko", 0.6, 8.6, into, 30);
  k.racer("brakka", -5.6, 4.6, into, 30);
  // The crowd at the bend.
  const r = rnd(11);
  for (let i = 0; i < 8; i++) k.folk("valley", 20 + i, 8 + r() * 7, -1 + r() * 6, -1.8 + r() * 0.5);
  // At the front of it, a dinosaur raises a horn to its lips and blows, at the dragons.
  const hx = 5.6;
  const hz = 7.2;
  const blower = k.folk("valley", 13, hx, hz, -Math.PI / 2 + 0.05, "parasaur");
  blower.root.scale.multiplyScalar(1.25);
  const horns: THREE.Object3D[] = [];
  for (const part of ["a", "b"] as const) {
    const h = new THREE.Group();
    h.add(new THREE.Mesh(hornGeometry(part), skinMaterial()));
    h.userData.inHand =
      part === "a"
        ? { at: [0.0, 0.0, 0.03], rot: [-1.2, 0, 0.2] }
        : { at: [0.0, -0.02, -0.12], rot: [-1.0, 0, -0.2] };
    blower.rig.root.add(h);
    blower.rig.props[part === "a" ? "hornA" : "hornB"] = {
      obj: h,
      restAt: [-0.3, 0.02, -0.12],
      restRot: [0.75, 0.2, 0.15],
    };
    horns.push(h);
  }
  const blow = (t: number) =>
    blower.update(hx, k.height(hx, hz), hz, -Math.PI / 2 + 0.05, { gesture: "blowHorn" }, t);
  for (let i = 0; i < 30; i++) blow(i / 12);
  for (let i = 0; i < 8; i++) k.tree(-60 + r() * 140, -60 - r() * 40, "pine", 1.1 + r());
  k.mountain(-80, -300, 90, 80, true);
  k.mountain(100, -320, 110, 90, true);
  const camera = camOf(40);
  const bell = new THREE.Vector3();
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      fly(d1, "fly", t, 5.5, 0.4);
      fly(d2, "fly", t, 4.5, 0.4);
      blow(2.5 + t);
      drift(camera, [8, 3.6, 20.5], [7.5, 3.6, 19.5], [-4, 4.5, -2], t);
    },
    overlay(g, t, project) {
      // The blast: rings spreading from the bell toward the dragons.
      const hornB = horns[1]!;
      hornB.updateMatrixWorld(true);
      hornB.localToWorld(bell.set(0, 0.19, 0.36));
      const p = project(bell);
      const q = project(d1.root.position);
      const aim = Math.atan2(q.y - p.y, q.x - p.x);
      g.strokeStyle = `rgb(${INK.join(",")})`;
      g.lineWidth = RES * 1.3;
      g.lineCap = "round";
      for (let i = 0; i < 4; i++) {
        const r0 = (6 + i * 8 + ((t * 14) % 8)) * RES;
        g.globalAlpha = 1 - i * 0.18;
        g.beginPath();
        g.arc(p.x, p.y, r0, aim - 0.7, aim + 0.7);
        g.stroke();
      }
      g.globalAlpha = 1;
    },
    dispose: () => k.dispose(),
  };
}

/** 8. The finish: the crews over the line, the dragons faltering behind. */
function finish(): Plate {
  const k = new Kit();
  k.ground(["#b8c088", "#a0ac74"]);
  k.road(
    [
      [0, 120],
      [0, 40],
      [0, -20],
      [-6, -140],
    ],
    12,
  );
  k.startLine(0, 2, 0, 13);
  k.racer("tiko", -2.4, 12, 0, 40);
  k.racer("brakka", 2.8, 9.5, 0, 40);
  const d1 = k.dragon("cinderjaw", -5, 5, -10, 0.3, 0.22);
  const d2 = k.dragon("rimefang", 7, 7, -18, -0.2, 0.2);
  const r = rnd(5);
  for (let i = 0; i < 7; i++) k.folk("valley", 40 + i, -11 - r() * 4, -10 + i * 4, Math.PI / 2);
  for (let i = 0; i < 7; i++) k.folk("valley", 60 + i, 11 + r() * 4, -10 + i * 4, -Math.PI / 2);
  for (let i = 0; i < 10; i++) k.tree(-90 + r() * 180, -50 - r() * 50, "round", 1 + r());
  const camera = camOf(40);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      fly(d1, "stunned", t, 5, 0.3, look.set(-20, 0, 10));
      fly(d2, "stunned", t, 7, 0.3, look.set(20, 0, 10));
      drift(camera, [5, 3.5, 25], [4, 3.5, 23], [0, 4, -2], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 9. The dragons keep their oath: away over the border, home to the Dragon Kingdom. */
function withdraw(): Plate {
  const k = new Kit();
  k.ground(["#b8c088", "#9eae76"]);
  const b = k.border([
    [-160, -60],
    [-60, -70],
    [20, -66],
    [100, -78],
    [180, -72],
  ]);
  const ds = [
    k.dragon("king", 0, 22, -40, Math.PI + 0.1, 0.36),
    k.dragon("cinderjaw", -16, 15, -26, Math.PI - 0.2, 0.28),
    k.dragon("rimefang", 16, 17, -30, Math.PI + 0.3, 0.26),
    k.dragon("scorchwind", -30, 21, -52, Math.PI - 0.1, 0.24),
    k.dragon("tidewyrm", 30, 19, -56, Math.PI + 0.2, 0.24),
  ];
  const ys = [22, 16, 18, 22, 20];
  k.citadel(6, -200, 1.6);
  k.mountain(-120, -260, 110, 90, true, "#7a6a64");
  k.mountain(150, -250, 100, 80, true, "#7a6a64");
  k.racer("tiko", -4, 9, Math.PI + 0.2, 0);
  k.racer("brakka", 4, 10, Math.PI - 0.1, 0);
  k.house(-22, 18, 0.2);
  k.house(22, 22, -0.3, "#e8d4a8", "#7a4a2a");
  const camera = camOf(42);
  return {
    scene: k.scene,
    camera,
    update(t, dt) {
      k.animate(dt);
      ds.forEach((d, i) => fly(d, "fly", t, ys[i]!, 0.8));
      b.material.opacity = 0.85 + 0.15 * Math.sin(t * 1.5);
      drift(camera, [0, 6, 30], [0, 6, 27], [0, 8, -20], t);
    },
    dispose: () => k.dispose(),
  };
}

/** 10. The stones: one in each land, the Heart Stone behind them in the Dragon Kingdom. */
function stones(): Plate {
  const k = new Kit();
  k.ground(["#c4c094", "#aeaa80"], 0.6);
  // Each land's patch round its stone: valley, snow, desert, isles.
  const lands: [number, number, string, "pine" | "round" | "palm"][] = [
    [-18, 4, "#7a9a52", "round"],
    [-6, 8, "#e8eef0", "pine"],
    [6, 8, "#e0c080", "palm"],
    [18, 4, "#7ab8a8", "palm"],
  ];
  for (const [x, z, c, tree] of lands) {
    const patch = k.mesh(new THREE.CircleGeometry(5.5, 9), k.mat(c));
    patch.rotation.x = -Math.PI / 2;
    patch.position.set(x, k.height(x, z) + 0.3, z);
    k.stone(x, z, -x * 0.012, false, 1.3);
    k.tree(x + 3.6 * Math.sign(x), z - 3, tree, 0.6);
  }
  k.stone(0, -12, 0, true, 1.35);
  k.citadel(60, -160, 1.2);
  k.mountain(-100, -240, 100, 80, true, "#7a6a64");
  k.mountain(110, -250, 110, 80, true, "#7a6a64");
  const camera = camOf(40);
  return {
    scene: k.scene,
    camera,
    update(t) {
      drift(camera, [0, 7, 40], [0, 6.5, 37], [0, 6, -6], t);
    },
    dispose: () => k.dispose(),
  };
}

const PAGES = [
  war,
  oath,
  ruleBorder,
  ruleChampion,
  ruleForfeit,
  raceStart,
  horn,
  finish,
  withdraw,
  stones,
];
export const PLATE_COUNT = PAGES.length;

/** The ribbon over each rules page (the oath, then rules I, II and III). */
export const PLATE_RIBBONS: (string | undefined)[] = [
  undefined,
  "THE DRAGON PACT",
  "RULE I",
  "RULE II",
  "RULE III",
];

// ------------------------------------------------------------------ the inking

/** The wash and the ink, on the GPU: from the colour, normal and depth passes. */
const INK_VERT = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

const INK_FRAG = /* glsl */ `
uniform sampler2D tColor;
uniform sampler2D tNormal;
uniform sampler2D tDepth;
uniform sampler2D tEdge;
uniform vec2 res;
uniform float near;
uniform float far;
uniform float res3;
uniform vec3 ink;
varying vec2 vUv;

float lin(float d) {
  if (d >= 0.9999) return far;
  float z = d * 2.0 - 1.0;
  return 2.0 * near * far / (far + near - z * (far - near));
}
vec3 toSrgb(vec3 c) {
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}

void main() {
  vec2 px = 1.0 / res;
  vec4 col = texture2D(tColor, vUv);
  vec3 c = toSrgb(col.rgb);
  // The wash: stepped into tones, a little less saturated, eased toward the paper.
  float lum = dot(c, vec3(0.3, 0.59, 0.11));
  float q = floor(lum * 5.0 + 0.5) / 5.0;
  c *= (q + 0.1) / (lum + 0.1);
  float L = dot(c, vec3(0.3, 0.59, 0.11));
  c = L + (c - L) * 0.85;
  c = c * 0.78 + 0.22;
  // The ink. Outlines where the depth breaks: in inverse depth (straight across any flat
  // surface, however steeply it's seen) a kink or a jump, one and two pixels out (a bolder
  // line), inked on the far side. Lighter creases where the surface turns.
  float zc = lin(texture2D(tDepth, vUv).r);
  float wc = 1.0 / zc;
  bool cover = zc < far * 0.999;
  vec3 nc = texture2D(tNormal, vUv).rgb * 2.0 - 1.0;
  float line = 0.0;
  for (int i = 0; i < 4; i++) {
    vec2 o = i == 0 ? vec2(1, 0) : i == 1 ? vec2(0, 1) : i == 2 ? vec2(2, 0) : vec2(0, 2);
    float wa = 1.0 / lin(texture2D(tDepth, vUv + o * px).r);
    float wb = 1.0 / lin(texture2D(tDepth, vUv - o * px).r);
    if (abs(wa + wb - 2.0 * wc) / wc > 0.08 && wc < max(wa, wb)) line = 1.0;
    if (i < 2 && cover) {
      vec3 na = texture2D(tNormal, vUv + o * px).rgb * 2.0 - 1.0;
      vec3 nb = texture2D(tNormal, vUv - o * px).rgb * 2.0 - 1.0;
      if (min(dot(nc, na), dot(nc, nb)) < 0.6) line = max(line, 0.55);
    }
  }
  // Hatching in the dark tones, cross-hatching in the darkest.
  vec2 f = floor(gl_FragCoord.xy);
  float step2 = 2.0 * res3;
  if (col.a > 0.5 && q <= 0.4 && mod(f.x + f.y, step2) < 0.5) line = max(line, 0.4);
  if (col.a > 0.5 && q <= 0.2 && mod(f.x - f.y + 4000.0, step2) < 0.5) line = max(line, 0.4);
  float e = texture2D(tEdge, vUv).r;
  vec3 rgb = mix(c, ink, line);
  float a = clamp(max(col.a * 0.95, line), 0.0, 1.0) * e;
  gl_FragColor = vec4(rgb, a);
}`;

export function createStoryPlates(renderer: THREE.WebGLRenderer) {
  const w = PLATE_W * RES;
  const h = PLATE_H * RES;
  const colorRT = new THREE.WebGLRenderTarget(w, h, { samples: 4 });
  const auxRT = new THREE.WebGLRenderTarget(w, h, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    depthTexture: Object.assign(new THREE.DepthTexture(w, h), { type: THREE.FloatType }),
  });
  const outRT = new THREE.WebGLRenderTarget(w, h, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
  });
  const normalMat = new THREE.MeshNormalMaterial();
  const buf = new Uint8Array(w * h * 4);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const img = ctx.createImageData(w, h);
  // The edge where the wash bleeds into the paper (fixed noise).
  const edgeData = new Uint8Array(w * h);
  {
    const r = rnd(17);
    const bumps = Array.from({ length: 24 }, () => [r() * 6.28, 2 + r() * 9, r() * 0.5]);
    const wob = (a: number) =>
      bumps.reduce((s, [p, f, k]) => s + Math.sin(a * f! + p!) * k!, 0) * 0.018;
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const u = (x / w) * 2 - 1;
        const v = (y / h) * 2 - 1;
        const a = Math.atan2(v, u);
        // A rounded rectangle's distance, its rim wobbling.
        const d = (Math.abs(u) ** 6 + Math.abs(v) ** 6) ** (1 / 6);
        edgeData[y * w + x] = Math.round(255 * (1 - smooth(0.86 + wob(a), 0.99 + wob(a), d)));
      }
  }
  const edgeTex = new THREE.DataTexture(edgeData, w, h, THREE.RedFormat);
  edgeTex.needsUpdate = true;
  const inkMat = new THREE.ShaderMaterial({
    vertexShader: INK_VERT,
    fragmentShader: INK_FRAG,
    uniforms: {
      tColor: { value: colorRT.texture },
      tNormal: { value: auxRT.texture },
      tDepth: { value: auxRT.depthTexture },
      tEdge: { value: edgeTex },
      res: { value: new THREE.Vector2(w, h) },
      near: { value: 1 },
      far: { value: 900 },
      res3: { value: RES },
      ink: { value: new THREE.Vector3(INK[0] / 255, INK[1] / 255, INK[2] / 255) },
    },
    depthTest: false,
    depthWrite: false,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), inkMat);
  quad.frustumCulled = false;
  const post = new THREE.Scene();
  post.add(quad);
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  let page = -1;
  let plate: Plate | undefined;
  let clock = 0;
  let lastDrawn = -1;
  let fresh = false;
  const proj = new THREE.Vector3();

  const project = (p: THREE.Vector3) => {
    proj.copy(p).project(plate!.camera);
    return new THREE.Vector2(((proj.x + 1) / 2) * w, ((1 - proj.y) / 2) * h);
  };

  function render() {
    const p = plate!;
    const prevTarget = renderer.getRenderTarget();
    const clear = new THREE.Color();
    renderer.getClearColor(clear);
    const prevAlpha = renderer.getClearAlpha();
    renderer.setClearColor(0x000000, 0);
    // Colour.
    renderer.setRenderTarget(colorRT);
    renderer.clear();
    renderer.render(p.scene, p.camera);
    // Normals and depth, without the glows.
    const hidden: THREE.Object3D[] = [];
    p.scene.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.Material | undefined;
      const glowy =
        o.userData.fx === true ||
        (o as THREE.Sprite).isSprite ||
        (o as THREE.Points).isPoints ||
        (m && !Array.isArray(m) && m.transparent && m.blending === THREE.AdditiveBlending);
      if (o.visible && glowy) {
        o.visible = false;
        hidden.push(o);
      }
    });
    renderer.setRenderTarget(auxRT);
    p.scene.overrideMaterial = normalMat;
    renderer.setClearColor(0x8080ff, 0);
    renderer.clear();
    renderer.render(p.scene, p.camera);
    p.scene.overrideMaterial = null;
    for (const o of hidden) o.visible = true;
    // The wash and the ink.
    inkMat.uniforms.near!.value = p.camera.near;
    inkMat.uniforms.far!.value = p.camera.far;
    renderer.setRenderTarget(outRT);
    renderer.setClearColor(0x000000, 0);
    renderer.clear();
    renderer.render(post, postCam);
    renderer.readRenderTargetPixels(outRT, 0, 0, w, h, buf);
    renderer.setRenderTarget(prevTarget);
    renderer.setClearColor(clear, prevAlpha);
    // (The target is upside down.)
    const row = w * 4;
    for (let y = 0; y < h; y++)
      img.data.set(buf.subarray((h - 1 - y) * row, (h - y) * row), y * row);
    ctx.putImageData(img, 0, 0);
    p.overlay?.(ctx, clock, project);
    // A faint wash of sky behind it all, inside the bled edge.
    ctx.globalCompositeOperation = "destination-over";
    const sky = ctx.createLinearGradient(0, 0, 0, h * 0.7);
    sky.addColorStop(0, "rgba(176,196,206,0.35)");
    sky.addColorStop(1, "rgba(236,220,184,0)");
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "destination-in";
    ctx.drawImage(edgeMask(), 0, 0);
    ctx.globalCompositeOperation = "source-over";
  }

  let mask: HTMLCanvasElement | undefined;
  function edgeMask() {
    if (mask) return mask;
    mask = document.createElement("canvas");
    mask.width = w;
    mask.height = h;
    const m = mask.getContext("2d")!;
    const d = m.createImageData(w, h);
    // (The texture's rows run bottom-up; the canvas's top-down.)
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) d.data[((h - 1 - y) * w + x) * 4 + 3] = edgeData[y * w + x]!;
    m.putImageData(d, 0, 0);
    return mask;
  }

  return {
    /** Rendered pixels across and down (draw it PLATE_W x PLATE_H on the UI). */
    w,
    h,
    /** This page's plate now: `t` seconds into the page. */
    draw(n: number, t: number, still: boolean): HTMLCanvasElement {
      const want = Math.max(0, Math.min(PAGES.length - 1, n));
      if (want !== page) {
        plate?.dispose();
        plate = PAGES[want]!();
        page = want;
        lastDrawn = -1;
        fresh = true;
      }
      // Twelve pictures a second; with reduced motion, one.
      const frame = still ? 0 : Math.floor(t * 12);
      if (frame !== lastDrawn) {
        const dt = fresh ? 0 : Math.min(0.25, (frame - lastDrawn) / 12);
        clock = still ? 2 : frame / 12;
        // (A fresh page settles first: a few steps so the poses blend in.)
        if (fresh) for (let s = 0; s < 6; s++) plate!.update(clock, 1 / 12);
        else plate!.update(clock, dt);
        fresh = false;
        lastDrawn = frame;
        render();
      }
      return canvas;
    },
    dispose() {
      plate?.dispose();
      plate = undefined;
      page = -1;
      colorRT.dispose();
      auxRT.depthTexture?.dispose();
      auxRT.dispose();
      outRT.dispose();
      normalMat.dispose();
      inkMat.dispose();
      quad.geometry.dispose();
      edgeTex.dispose();
    },
  };
}

export type StoryPlates = ReturnType<typeof createStoryPlates>;
