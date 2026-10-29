/**
 * A living fire (Blake, Oct 29: "can we really pump up the fidelity of this fire? like
 * high def"; "improve the quality of the fire and the torches"): three crossed sheets of
 * flame playing a flipbook of licking tongues (each sheet a moment apart), a soft halo
 * round it, and embers rising off it, drifting and winking out. Used by the gateways'
 * torches and the tunnels' wall sconces (the build's `fire` entities).
 *
 * Local space: the fire's base at the origin, flames rising up +y.
 */
import * as THREE from "three";

const FRAMES = 8;
const sheets = new Map<string, HTMLCanvasElement>();

/** A flame in FRAMES frames side by side: tongues licking up from a hot white heart,
 * yellow to orange to red at their tips, each frame a moment later. */
function flameSheet(hot: string, mid: string, tip: string) {
  const key = hot + mid + tip;
  const have = sheets.get(key);
  if (have) return have;
  const FW = 64;
  const FH = 128;
  const cv = document.createElement("canvas");
  cv.width = FW * FRAMES;
  cv.height = FH;
  const g = cv.getContext("2d")!;
  g.globalCompositeOperation = "lighter";
  for (let f = 0; f < FRAMES; f++) {
    const ox = f * FW;
    const t = (f / FRAMES) * Math.PI * 2;
    for (let k = 0; k < 5; k++) {
      const ph = t + k * 1.3;
      const hgt = FH * (0.55 + 0.3 * Math.abs(Math.sin(ph * (k % 2 ? 1 : 2) + k)));
      const w = FW * (0.36 - k * 0.04);
      const sway = Math.sin(ph) * FW * 0.12;
      const bx = ox + FW / 2 + (k - 2) * FW * 0.06;
      const by = FH - 10;
      const grad = g.createLinearGradient(0, by, 0, by - hgt);
      grad.addColorStop(0, hot);
      grad.addColorStop(0.35, mid);
      grad.addColorStop(0.8, tip);
      grad.addColorStop(1, "rgba(0,0,0,0)");
      g.fillStyle = grad;
      g.globalAlpha = 0.55;
      g.beginPath();
      g.moveTo(bx - w / 2, by);
      g.bezierCurveTo(
        bx - w / 2,
        by - hgt * 0.4,
        bx + sway - w * 0.2,
        by - hgt * 0.7,
        bx + sway * 1.6,
        by - hgt,
      );
      g.bezierCurveTo(
        bx + sway + w * 0.2,
        by - hgt * 0.7,
        bx + w / 2,
        by - hgt * 0.4,
        bx + w / 2,
        by,
      );
      g.closePath();
      g.fill();
    }
    const heart = g.createRadialGradient(ox + FW / 2, FH - 22, 2, ox + FW / 2, FH - 22, FW * 0.34);
    heart.addColorStop(0, "rgba(255,255,240,0.95)");
    heart.addColorStop(1, "rgba(255,200,80,0)");
    g.globalAlpha = 1;
    g.fillStyle = heart;
    g.fillRect(ox, FH - 60, FW, 60);
  }
  sheets.set(key, cv);
  return cv;
}

/** A soft round glow (round a flame, deep in a tunnel); `rings` adds swirls. */
export function glowTexture(color: string, rings = false) {
  const cv = document.createElement("canvas");
  cv.width = cv.height = 128;
  const g = cv.getContext("2d")!;
  const c = new THREE.Color(color);
  const rgb = `${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)}`;
  const grad = g.createRadialGradient(64, 64, 4, 64, 64, 64);
  grad.addColorStop(0, `rgba(255,255,240,0.95)`);
  grad.addColorStop(0.25, `rgba(${rgb},0.85)`);
  grad.addColorStop(1, `rgba(${rgb},0)`);
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  if (rings) {
    g.strokeStyle = "rgba(255,255,255,0.35)";
    g.lineWidth = 3;
    for (let k = 0; k < 3; k++) {
      g.beginPath();
      g.arc(64, 64, 18 + k * 14, k, k + 3.6);
      g.stroke();
    }
  }
  return new THREE.CanvasTexture(cv);
}

export interface Fire {
  readonly group: THREE.Group;
  update(t: number): void;
  dispose(): void;
}

/** A fire `size` tall-ish (1 = a torch's), red for a dragon's lair. */
export function createFire(o: { size?: number; red?: boolean; seed?: number } = {}): Fire {
  const size = o.size ?? 1;
  const seed = o.seed ?? Math.random() * 10;
  const group = new THREE.Group();
  group.name = "fire";
  const sheet = o.red
    ? flameSheet("rgba(255,240,200,1)", "rgba(255,90,20,0.9)", "rgba(160,10,0,0.7)")
    : flameSheet("rgba(255,250,220,1)", "rgba(255,170,40,0.9)", "rgba(220,60,10,0.7)");
  const disposables: { dispose(): void }[] = [];
  const mats: THREE.MeshBasicMaterial[] = [];
  const planes: THREE.Mesh[] = [];
  const plane = new THREE.PlaneGeometry(1.5 * size, 2.6 * size);
  plane.translate(0, 1.15 * size, 0);
  disposables.push(plane);
  for (let k = 0; k < 3; k++) {
    const tex = new THREE.CanvasTexture(sheet);
    tex.repeat.set(1 / FRAMES, 1);
    const m = new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    disposables.push(tex, m);
    mats.push(m);
    const pl = new THREE.Mesh(plane, m);
    pl.rotation.y = (k / 3) * Math.PI;
    group.add(pl);
    planes.push(pl);
  }
  const haloTex = glowTexture(o.red ? "#ff4010" : "#ffa030");
  const haloMat = new THREE.SpriteMaterial({
    map: haloTex,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    opacity: 0.5,
  });
  disposables.push(haloTex, haloMat);
  const halo = new THREE.Sprite(haloMat);
  halo.scale.setScalar(4.2 * size);
  halo.position.y = 0.8 * size;
  group.add(halo);
  const NE = 12;
  const eg = new THREE.BufferGeometry();
  eg.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(NE * 3), 3));
  const em = new THREE.PointsMaterial({
    color: o.red ? 0xff5020 : 0xffb040,
    size: 0.16 * size,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  disposables.push(eg, em);
  const embers = new THREE.Points(eg, em);
  embers.frustumCulled = false;
  group.add(embers);
  const seeds = [...Array(NE)].map((_, i) => (Math.sin(i * 12.9898 + seed) * 43758.5453) % 1);
  return {
    group,
    update(t) {
      mats.forEach((m, k) => {
        const frame = Math.floor(t * 14 + k * 2.7 + seed) % FRAMES;
        m.map!.offset.x = frame / FRAMES;
      });
      const k = 1 + 0.12 * Math.sin(t * 9 + seed) + 0.07 * Math.sin(t * 23 + seed);
      planes.forEach((p) => p.scale.set(1, k, 1));
      haloMat.opacity = 0.42 + 0.12 * Math.sin(t * 13 + seed) + 0.06 * Math.sin(t * 31);
      const pa = eg.getAttribute("position") as THREE.BufferAttribute;
      seeds.forEach((s0, e) => {
        const s = Math.abs(s0);
        const life = (t * (0.5 + s * 0.4) + s * 7) % 1;
        pa.setXYZ(
          e,
          Math.sin(s * 40 + t * 1.3) * 0.35 * life * size,
          (0.6 + life * 3.0) * size,
          Math.cos(s * 31 + t * 1.1) * 0.35 * life * size,
        );
      });
      pa.needsUpdate = true;
    },
    dispose() {
      group.removeFromParent();
      for (const d of disposables) d.dispose();
    },
  };
}
