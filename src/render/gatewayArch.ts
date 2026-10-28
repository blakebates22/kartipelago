/**
 * An overworld gateway into a course (Blake, Oct 28: "way more grand and natural, like a
 * cave hole, and the sign above it more rugged; the portals look terrible"): a mouth of
 * piled boulders in the world's own rock round a dark tunnel, the course's glow deep in
 * it, a rugged plank sign hung from the top on ropes with the name burned in, and a
 * torch either side. A dragon's lair is the same in scorched rock with a red glow.
 *
 * Visual only (the gateway's circle is what you drive into). Local space: the mouth
 * faces +z (the way you come out), the tunnel runs back to -z.
 */
import * as THREE from "three";

export type ArchTheme = "prehistoric" | "frostveil" | "desert" | "beach" | "dragon" | "lair";

const THEMES: Record<
  ArchTheme,
  { rock: string; dark: string; cap?: string; plank: string; ink: string }
> = {
  prehistoric: {
    rock: "#7a6a52",
    dark: "#4e4434",
    cap: "#4f7a32",
    plank: "#7a5230",
    ink: "#2a160a",
  },
  frostveil: { rock: "#8a96a4", dark: "#5a6474", cap: "#f2f6fa", plank: "#6a4a32", ink: "#1e1008" },
  desert: { rock: "#c49a62", dark: "#8a6a42", plank: "#8a6038", ink: "#2a160a" },
  beach: { rock: "#cbbca0", dark: "#8f8270", cap: "#5a9a3a", plank: "#9a7048", ink: "#2a160a" },
  dragon: { rock: "#5a5262", dark: "#36303e", plank: "#5a3a2a", ink: "#140a06" },
  lair: { rock: "#3a302c", dark: "#1e1814", plank: "#4a2a1a", ink: "#120804" },
};

function rng(seed: number) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };
}

/** The sign's face: rough planks with the name burned into them, ragged edges. */
function signTexture(label: string, plank: string, ink: string, seed: number) {
  const W = 512;
  const H = 128;
  const cv = document.createElement("canvas");
  cv.width = W;
  cv.height = H;
  const g = cv.getContext("2d")!;
  const r = rng(seed);
  const base = new THREE.Color(plank);
  // Three planks, each its own shade, ragged ends, grain lines, nails.
  for (let p = 0; p < 3; p++) {
    const y0 = 6 + p * 40;
    const shade = base.clone().multiplyScalar(0.85 + r() * 0.3);
    g.fillStyle = `#${shade.getHexString()}`;
    g.beginPath();
    const l = 4 + r() * 14;
    const rr = W - 4 - r() * 14;
    g.moveTo(l, y0);
    for (let x = l; x <= rr; x += 32) g.lineTo(x, y0 + (r() - 0.5) * 3);
    g.lineTo(rr + (r() - 0.5) * 8, y0 + 18);
    g.lineTo(rr, y0 + 38);
    for (let x = rr; x >= l; x -= 32) g.lineTo(x, y0 + 38 + (r() - 0.5) * 3);
    g.lineTo(l + (r() - 0.5) * 8, y0 + 18);
    g.closePath();
    g.fill();
    g.strokeStyle = "rgba(0,0,0,0.18)";
    g.lineWidth = 2;
    for (let k = 0; k < 4; k++) {
      const y = y0 + 6 + k * 8 + r() * 3;
      g.beginPath();
      g.moveTo(l + 6, y);
      g.bezierCurveTo(W * 0.3, y + (r() - 0.5) * 6, W * 0.7, y + (r() - 0.5) * 6, rr - 6, y);
      g.stroke();
    }
    g.fillStyle = "#2a2a2a";
    for (const x of [l + 12, rr - 12]) g.fillRect(x - 2, y0 + 17, 4, 4);
  }
  // The name, burned in: a dark scorch with a lighter edge.
  const size = Math.min(64, (W * 1.7) / Math.max(6, label.length));
  g.font = `bold ${size}px serif`;
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.lineJoin = "round";
  g.strokeStyle = "rgba(255,220,160,0.35)";
  g.lineWidth = 6;
  g.strokeText(label, W / 2, H / 2 + 2, W - 40);
  g.fillStyle = ink;
  g.fillText(label, W / 2, H / 2 + 2, W - 40);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** The glow deep in the tunnel: the course's colour, swirling. */
function glowTexture(color: string) {
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
  g.strokeStyle = "rgba(255,255,255,0.35)";
  g.lineWidth = 3;
  for (let k = 0; k < 3; k++) {
    g.beginPath();
    g.arc(64, 64, 18 + k * 14, k, k + 3.6);
    g.stroke();
  }
  return new THREE.CanvasTexture(cv);
}

export interface GatewayArch {
  readonly group: THREE.Group;
  update(t: number): void;
  dispose(): void;
}

export function createGatewayArch(
  parent: THREE.Object3D,
  o: { label: string; theme: ArchTheme; glow: string; seed: number },
): GatewayArch {
  const th = THEMES[o.theme];
  const r = rng(o.seed + 7);
  const group = new THREE.Group();
  group.name = `Gateway ${o.label}`;
  parent.add(group);
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const mat = (color: string, extra: THREE.MeshLambertMaterialParameters = {}) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...extra });
    mats.push(m);
    return m;
  };
  const rock = mat(th.rock);
  const dark = mat(th.dark);
  const cap = th.cap ? mat(th.cap) : undefined;
  const boulder = (x: number, y: number, z: number, s: number, m = rock) => {
    const g = new THREE.IcosahedronGeometry(s, 1);
    const p = g.getAttribute("position") as THREE.BufferAttribute;
    // (The same nudge for the same corner, so the faces stay joined.)
    const salt = r() * 100;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i);
      const y = p.getY(i);
      const z = p.getZ(i);
      const h = Math.sin(x * 12.9898 + y * 78.233 + z * 37.719 + salt) * 43758.5453;
      const k = 0.84 + 0.32 * (h - Math.floor(h));
      p.setXYZ(i, x * k, y * k, z * k);
    }
    g.computeVertexNormals();
    geos.push(g);
    const b = new THREE.Mesh(g, m);
    b.position.set(x, y, z);
    b.rotation.set(r() * 3, r() * 3, r() * 3);
    b.scale.set(1, 0.8 + r() * 0.4, 0.9 + r() * 0.3);
    group.add(b);
    return b;
  };
  // The mouth: boulders piled in an arch, bigger at the feet, two deep (front and back).
  const R = 7.4;
  const N = 11;
  for (let row = 0; row < 2; row++)
    for (let i = 0; i < N; i++) {
      const a = (i / (N - 1)) * Math.PI;
      const s = (i === 0 || i === N - 1 ? 3.4 : 2.3 + r() * 0.8) * (row ? 0.95 : 1);
      const b = boulder(
        Math.cos(a) * R,
        Math.sin(a) * (R + 1.2) + (i === 0 || i === N - 1 ? 1.2 : 1.6),
        row ? -3.2 : 0.4,
        s,
        row ? dark : rock,
      );
      // Moss, or snow, on the top stones.
      if (cap && row === 0 && Math.sin(a) > 0.55) {
        const c = boulder(b.position.x, b.position.y + s * 0.55, b.position.z + 0.2, s * 0.62, cap);
        c.scale.y *= 0.45;
      }
    }
  // Shoulders: rock spilling out to either side, and a few stones on the ground.
  for (const sd of [-1, 1]) {
    boulder(sd * 10.6, 1.6, -1.5, 3.0);
    boulder(sd * 12.4, 0.8, 0.8, 1.9);
    boulder(sd * 9.2, 5.6, -2.4, 2.2, dark);
    boulder(sd * (7 + r() * 4), 0.3, 3.5 + r() * 2, 0.7 + r() * 0.5);
  }
  // The hole: a dark tunnel back into the rock, the course's glow deep inside.
  const tunnelG = new THREE.CylinderGeometry(6.2, 6.2, 12, 14, 1, true, -Math.PI / 2, Math.PI);
  geos.push(tunnelG);
  const inside = new THREE.MeshBasicMaterial({ color: 0x0a0806, side: THREE.DoubleSide });
  mats.push(inside);
  const tunnel = new THREE.Mesh(tunnelG, inside);
  tunnel.rotation.x = -Math.PI / 2;
  tunnel.position.set(0, 0.2, -6.5);
  group.add(tunnel);
  const backG = new THREE.CircleGeometry(6.2, 16, 0, Math.PI);
  geos.push(backG);
  const back = new THREE.Mesh(backG, inside);
  back.position.set(0, 0.2, -12.4);
  group.add(back);
  const glowTex = glowTexture(o.glow);
  const glowMat = new THREE.MeshBasicMaterial({
    map: glowTex,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
  });
  mats.push(glowMat);
  const glowG = new THREE.PlaneGeometry(9, 9);
  geos.push(glowG);
  const glow = new THREE.Mesh(glowG, glowMat);
  glow.position.set(0, 3.6, -11.8);
  group.add(glow);
  // The sign: planks hung on ropes from the top of the arch.
  const signTex = signTexture(o.label.toUpperCase(), th.plank, th.ink, o.seed);
  const signMat = new THREE.MeshLambertMaterial({
    map: signTex,
    side: THREE.DoubleSide,
    transparent: true,
    alphaTest: 0.5,
  });
  mats.push(signMat);
  const signG = new THREE.PlaneGeometry(14, 3.5);
  geos.push(signG);
  const sign = new THREE.Group();
  sign.position.set(0, R + 3.6, 3.3);
  sign.rotation.z = (r() - 0.5) * 0.06;
  const board = new THREE.Mesh(signG, signMat);
  sign.add(board);
  const rope = mat("#8a7450");
  for (const sd of [-1, 1]) {
    const rg = new THREE.CylinderGeometry(0.06, 0.06, 2.4, 4);
    geos.push(rg);
    const rp = new THREE.Mesh(rg, rope);
    rp.position.set(sd * 4.6, 2.6, -0.3);
    rp.rotation.z = sd * 0.1;
    sign.add(rp);
  }
  group.add(sign);
  // Torches either side of the mouth.
  const flames: THREE.Mesh[] = [];
  const pole = mat("#4a3420");
  const flameM = new THREE.MeshBasicMaterial({ color: o.theme === "lair" ? 0xff4010 : 0xffa030 });
  mats.push(flameM);
  for (const sd of [-1, 1]) {
    const pg = new THREE.CylinderGeometry(0.16, 0.22, 3.6, 5);
    const fg = new THREE.ConeGeometry(0.42, 1.1, 6);
    geos.push(pg, fg);
    const p = new THREE.Mesh(pg, pole);
    p.position.set(sd * 8.6, 1.8, 3.4);
    const f = new THREE.Mesh(fg, flameM);
    f.position.set(sd * 8.6, 4.1, 3.4);
    group.add(p, f);
    flames.push(f);
  }
  return {
    group,
    update(t) {
      glow.rotation.z = t * 0.6;
      glowMat.opacity = 0.75 + 0.2 * Math.sin(t * 2.1 + o.seed);
      flames.forEach((f, i) => {
        const k = 1 + 0.18 * Math.sin(t * 11 + i * 2) + 0.1 * Math.sin(t * 17 + i);
        f.scale.set(1, k, 1);
      });
      sign.rotation.z = Math.sin(t * 0.9 + o.seed) * 0.02;
    },
    dispose() {
      parent.remove(group);
      signTex.dispose();
      glowTex.dispose();
      for (const m of mats) m.dispose();
      for (const g of geos) g.dispose();
    },
  };
}
