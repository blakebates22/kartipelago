/**
 * An overworld gateway into a course (Blake, Oct 28: "way more grand and natural, like a
 * cave hole, and the sign above it more rugged"; Oct 29, review-valley_region 4 and 5:
 * "this rock piece is covering the sign", "pump up the fidelity of this fire ... high
 * def", "the backside ... is just black ... redo this portal rock structure to make it
 * look more natural", "redo the fonts of all the signs ... this is too plain jane"):
 *
 * a cave mouth in a hillock of the world's own rock (one mass, weathered in bands, moss
 * or snow on its top, the hill closing over the tunnel behind so it's rock from every
 * side), the way through a flat swirl of the course's glow filling the mouth (valley
 * polish 19), a carved sign hung clear in front of the rock
 * with the name cut in big painted letters, and a torch either side: a carved post, an
 * iron basket and a living fire (layered flames that flicker and lick, embers rising).
 * A dragon's lair is the same in scorched rock with a red glow and red fire.
 *
 * Visual only (the gateway's circle is what you drive into; the overworld makes its rock
 * and posts solid). Local space: the mouth faces +z (the way you come out).
 */
import * as THREE from "three";
import { batchStatic } from "./batchStatic";
import { createFire, type Fire } from "./fire";

export type ArchTheme =
  "prehistoric" | "ember" | "frostveil" | "desert" | "beach" | "dragon" | "lair";

const THEMES: Record<
  ArchTheme,
  {
    rock: string;
    dark: string;
    band: string;
    cap?: string;
    plank: string;
    paint: string;
    edge: string;
  }
> = {
  prehistoric: {
    rock: "#8a7658",
    dark: "#5a4c38",
    band: "#a08a66",
    cap: "#4f8a32",
    plank: "#7a5230",
    paint: "#f2c64a",
    edge: "#3a1e0c",
  },
  // (The volcano's: basalt with ash on its top, no green: Blake, Ember Peak note 8.)
  ember: {
    rock: "#5a4a44",
    dark: "#2a201c",
    band: "#6e5a50",
    cap: "#8a8078",
    plank: "#5a3a26",
    paint: "#ffb04a",
    edge: "#240c04",
  },
  frostveil: {
    rock: "#8e9aa8",
    dark: "#5a6474",
    band: "#a8b4c2",
    cap: "#f2f6fa",
    plank: "#6a4a32",
    paint: "#bfe6ff",
    edge: "#1e2a3a",
  },
  desert: {
    rock: "#c49a62",
    dark: "#8a6a42",
    band: "#d8b07a",
    plank: "#8a6038",
    paint: "#ffe08a",
    edge: "#4a2410",
  },
  beach: {
    rock: "#cbbca0",
    dark: "#8f8270",
    band: "#ddd0b4",
    cap: "#5a9a3a",
    plank: "#9a7048",
    paint: "#ffffff",
    edge: "#2a4a6a",
  },
  dragon: {
    rock: "#5a5262",
    dark: "#36303e",
    band: "#6e6676",
    plank: "#5a3a2a",
    paint: "#ffb040",
    edge: "#200a06",
  },
  lair: {
    rock: "#3a302c",
    dark: "#1e1814",
    band: "#4a3c34",
    plank: "#4a2a1a",
    paint: "#ff7a30",
    edge: "#120402",
  },
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

/** Smooth 3D value noise (for the rock's shape and weathering), -1..1. */
function noise3(seed: number) {
  const h = (x: number, y: number, z: number) => {
    const v = Math.sin(x * 127.1 + y * 311.7 + z * 74.7 + seed * 13.13) * 43758.5453;
    return v - Math.floor(v);
  };
  const sm = (t: number) => t * t * (3 - 2 * t);
  return (x: number, y: number, z: number) => {
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    const zi = Math.floor(z);
    const xf = sm(x - xi);
    const yf = sm(y - yi);
    const zf = sm(z - zi);
    const l = (a: number, b: number, t: number) => a + (b - a) * t;
    const c = (dx: number, dy: number, dz: number) => h(xi + dx, yi + dy, zi + dz);
    return (
      l(
        l(l(c(0, 0, 0), c(1, 0, 0), xf), l(c(0, 1, 0), c(1, 1, 0), xf), yf),
        l(l(c(0, 0, 1), c(1, 0, 1), xf), l(c(0, 1, 1), c(1, 1, 1), xf), yf),
        zf,
      ) *
        2 -
      1
    );
  };
}

// ---------------------------------------------------------------- the sign

/** The sign: three rough planks, the name cut into them in big chunky letters, each
 * letter its own tilt and bounce, painted, with a carved dark edge and a lit bevel; a
 * leaf (or a spark) at each end. */
function signTexture(label: string, th: (typeof THEMES)[ArchTheme], seed: number) {
  const W = 1024;
  const H = 256;
  const cv = document.createElement("canvas");
  cv.width = W;
  cv.height = H;
  const g = cv.getContext("2d")!;
  const r = rng(seed);
  const base = new THREE.Color(th.plank);
  for (let p = 0; p < 3; p++) {
    const y0 = 10 + p * 80;
    const shade = base.clone().multiplyScalar(0.82 + r() * 0.3);
    g.fillStyle = `#${shade.getHexString()}`;
    g.beginPath();
    const l = 8 + r() * 26;
    const rr = W - 8 - r() * 26;
    g.moveTo(l, y0);
    for (let x = l; x <= rr; x += 48) g.lineTo(x, y0 + (r() - 0.5) * 5);
    g.lineTo(rr + (r() - 0.5) * 14, y0 + 38);
    g.lineTo(rr, y0 + 76);
    for (let x = rr; x >= l; x -= 48) g.lineTo(x, y0 + 76 + (r() - 0.5) * 5);
    g.lineTo(l + (r() - 0.5) * 14, y0 + 38);
    g.closePath();
    g.fill();
    // Grain, knots, a lit top edge, nails.
    g.strokeStyle = "rgba(0,0,0,0.16)";
    g.lineWidth = 3;
    for (let k = 0; k < 5; k++) {
      const y = y0 + 10 + k * 14 + r() * 5;
      g.beginPath();
      g.moveTo(l + 10, y);
      g.bezierCurveTo(W * 0.3, y + (r() - 0.5) * 10, W * 0.7, y + (r() - 0.5) * 10, rr - 10, y);
      g.stroke();
    }
    g.fillStyle = "rgba(255,240,200,0.18)";
    g.fillRect(l + 6, y0 + 2, rr - l - 12, 4);
    g.fillStyle = "rgba(0,0,0,0.25)";
    for (let k = 0; k < 2; k++) {
      g.beginPath();
      g.ellipse(l + 80 + r() * (rr - l - 160), y0 + 20 + r() * 40, 9, 5, 0, 0, Math.PI * 2);
      g.fill();
    }
    g.fillStyle = "#2a2a2a";
    for (const x of [l + 22, rr - 22]) g.fillRect(x - 4, y0 + 34, 8, 8);
  }
  // The letters: chunky, each tilted and bounced a little, cut (a dark outline and
  // shadow), painted, and lit along their top.
  const text = label.toUpperCase();
  const size = Math.min(150, (W * 1.45) / Math.max(5, text.length));
  g.font = `900 ${size}px "Arial Black", "Trebuchet MS", Impact, sans-serif`;
  g.textBaseline = "middle";
  g.textAlign = "center";
  const widths = [...text].map((ch) => g.measureText(ch).width * 0.92);
  const total = widths.reduce((a, b) => a + b, 0);
  const sx = Math.min(1, (W - 120) / total);
  let x = W / 2 - (total * sx) / 2;
  [...text].forEach((ch, i) => {
    const w = widths[i]! * sx;
    const cx = x + w / 2;
    const cy = H / 2 + 6 + Math.sin(i * 1.7 + seed) * 7;
    g.save();
    g.translate(cx, cy);
    g.rotate((r() - 0.5) * 0.16);
    g.scale(sx, 1);
    g.lineJoin = "round";
    // The cut: shadow below, the dark edge.
    g.fillStyle = "rgba(0,0,0,0.45)";
    g.fillText(ch, 5, 7);
    g.strokeStyle = th.edge;
    g.lineWidth = size * 0.16;
    g.strokeText(ch, 0, 0);
    // The paint, lighter toward its top.
    const grad = g.createLinearGradient(0, -size * 0.45, 0, size * 0.45);
    const paint = new THREE.Color(th.paint);
    grad.addColorStop(0, `#${paint.clone().lerp(new THREE.Color("#ffffff"), 0.45).getHexString()}`);
    grad.addColorStop(0.55, `#${paint.getHexString()}`);
    grad.addColorStop(1, `#${paint.clone().multiplyScalar(0.7).getHexString()}`);
    g.fillStyle = grad;
    g.fillText(ch, 0, 0);
    g.restore();
    x += w;
  });
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

// ---------------------------------------------------------------- the rock

/** The rock: the mouth's arch and the hillock it's cut into, one weathered mass. */
function rockMass(th: (typeof THEMES)[ArchTheme], seed: number) {
  const n = noise3(seed);
  const rockC = new THREE.Color(th.rock);
  const darkC = new THREE.Color(th.dark);
  const bandC = new THREE.Color(th.band);
  const capC = th.cap ? new THREE.Color(th.cap) : undefined;
  const pos: number[] = [];
  const col: number[] = [];
  const tmp = new THREE.Color();
  // A shell over a grid of (u, v): u round the hill from one foot to the other (0..PI),
  // v from the mouth's face back over the top (0..1). Each point is pushed out by noise.
  // The mouth's hole is cut where the hill's front face is.
  const RI = 6.6; // the hole
  const shellAt = (u: number, v: number, out: THREE.Vector3) => {
    // The face: a ring from the hole's edge out to the hill's rim (v 0..0.25); then
    // the hill over the top and down behind (v 0.25..1).
    const ca = Math.cos(u);
    const sa = Math.sin(u);
    if (v <= 0.25) {
      const k = v / 0.25;
      const rad = RI + k * 4.6;
      out.set(ca * rad, sa * rad * 1.08 + 0.2, 1.6 - k * k * 0.8);
    } else {
      const k = (v - 0.25) / 0.75;
      // An ellipsoid behind the face: wide, tall at the front, falling away behind, and
      // closed right over at the back (it was open there, the black tunnel showing
      // through: Blake, Riverbend note 9, "cover this back on all of these").
      const ang = k * Math.PI * 0.5;
      const rad = 13.2 * Math.pow(Math.cos(ang), 0.75);
      out.set(ca * rad, sa * (rad * 1.08 + 0.2) * (1 - 0.15 * k), 0.8 - Math.sin(ang) * 19);
    }
    // Weathering: lumps and ledges.
    // (More of it, finer, and ledges stepped out along the strata: it read flat, "too
    // planar": Blake, Riverbend note 2.)
    const w0 = n(out.x * 0.3, out.y * 0.1, out.z * 0.3) * 0.6;
    const bed = (out.y * 0.42 + w0) % 1;
    const ledge = bed > 0.82 ? (bed - 0.82) * 6 : bed < 0.1 ? 1 - bed * 4 : 0;
    const d =
      n(out.x * 0.2, out.y * 0.2, out.z * 0.2) * 1.8 +
      n(out.x * 0.55, out.y * 0.55, out.z * 0.55) * 0.7 +
      n(out.x * 1.3, out.y * 1.3, out.z * 1.3) * 0.28 +
      n(out.x * 2.9, out.y * 2.9, out.z * 2.9) * 0.1 +
      (v > 0.25 ? Math.max(0, ledge) * 0.55 : 0);
    const nx = v <= 0.25 ? 0 : ca;
    const ny = v <= 0.25 ? 0 : sa;
    const nz = v <= 0.25 ? 1 : 0.4;
    out.x += nx * d;
    out.y += Math.max(-out.y, ny * d);
    out.z += nz * d * 0.8;
    // (Its feet run 6 m down into the ground, so where the land falls away under one
    // side it still meets the land: Blake, valley polish 18, note 1, "the portal is kind
    // of floating on this side".)
    if (out.y < 0.05) out.y = -6.0;
    return out;
  };
  const NU = 84;
  const NV = 52;
  const grid: THREE.Vector3[][] = [];
  for (let i = 0; i <= NU; i++) {
    const row: THREE.Vector3[] = [];
    for (let j = 0; j <= NV; j++)
      row.push(shellAt((i / NU) * Math.PI, j / NV, new THREE.Vector3()));
    grid.push(row);
  }
  const paint = (p: THREE.Vector3, nrm: THREE.Vector3) => {
    // Beds of strata (ledges, a dark seam under each), cracks, darker low down, and the
    // cap (moss, snow) on whatever faces up.
    const w = n(p.x * 0.3, p.y * 0.1, p.z * 0.3) * 0.6;
    const bed = (p.y * 0.42 + w) % 1;
    tmp.copy(rockC).lerp(bandC, (Math.floor(p.y * 0.42 + w) % 2) * 0.55);
    if (bed < 0.12) tmp.lerp(darkC, 0.75);
    const crack = Math.abs(n(p.x * 0.9, p.y * 0.35, p.z * 0.9));
    if (crack < 0.07) tmp.lerp(darkC, 0.8);
    tmp.multiplyScalar(0.88 + 0.22 * (0.5 + 0.5 * n(p.x * 1.7, p.y * 1.7, p.z * 1.7)));
    tmp.lerp(darkC, Math.max(0, 0.4 - p.y * 0.06));
    if (capC && nrm.y > 0.5 && p.y > 3.5) tmp.lerp(capC, Math.min(1, (nrm.y - 0.5) * 3));
    return tmp;
  };
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const nrm = new THREE.Vector3();
  const tri = (p0: THREE.Vector3, p1: THREE.Vector3, p2: THREE.Vector3) => {
    a.subVectors(p1, p0);
    b.subVectors(p2, p0);
    nrm.crossVectors(a, b).normalize();
    for (const p of [p0, p1, p2]) {
      pos.push(p.x, p.y, p.z);
      const c = paint(p, nrm);
      col.push(c.r, c.g, c.b);
    }
  };
  for (let i = 0; i < NU; i++)
    for (let j = 0; j < NV; j++) {
      const p00 = grid[i]![j]!;
      const p10 = grid[i + 1]![j]!;
      const p01 = grid[i]![j + 1]!;
      const p11 = grid[i + 1]![j + 1]!;
      // (Outward: the face toward +z, the hill away from its middle.)
      tri(p00, p01, p10);
      tri(p10, p01, p11);
    }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  g.computeVertexNormals();
  return g;
}

/** How the way through looks: 0 swirl, 1 light, 2 ripple, 3 window, 4 glow (a
 * debugging override: `window.__kpPortalStyle`). */
const PORTAL_STYLE = 1; // (B, light pouring out: Blake, Oct 30, "lets do b for now")
function portalStyle() {
  const o = (globalThis as { __kpPortalStyle?: number }).__kpPortalStyle;
  return typeof o === "number" ? o : PORTAL_STYLE;
}

/** The mouth's outline: upright sides from `bottom` up to the springing, a half circle of
 * radius `r` over the ground. */
function archShape(r: number, bottom: number) {
  const sh = new THREE.Shape();
  sh.moveTo(-r, bottom);
  sh.lineTo(-r, 0.2);
  sh.absarc(0, 0.2, r, Math.PI, 0, true);
  sh.lineTo(r, bottom);
  sh.lineTo(-r, bottom);
  return sh;
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
  const texs: THREE.Texture[] = [];
  const keep = <T extends THREE.Material>(m: T) => (mats.push(m), m);
  const geo = <T extends THREE.BufferGeometry>(g: T) => (geos.push(g), g);

  // The rock: the mouth and the hill over the tunnel, one mass.
  const rockMat = keep(
    new THREE.MeshLambertMaterial({
      vertexColors: true,
      flatShading: true,
      side: THREE.DoubleSide,
    }),
  );
  group.add(new THREE.Mesh(geo(rockMass(th, o.seed % 97)), rockMat));
  // (No stones at its feet or boulders against its flanks any more: Blake, valley polish
  // 14, note 8, "lets remove these rocks in front of al portals. they look weird". Their
  // draws are still taken, so the sign hangs as it did.)
  for (let k = 0; k < 2 * (4 * 7 + 3 * 6); k++) r();
  // The way through: one flat glowing surface filling the mouth, in the arch's own shape,
  // a slow swirl in the world's colour, bright in the middle, a soft rim where it meets the
  // rock, and on down into the ground so it always meets the floor. (It was a black tunnel
  // lined inside with a disc deep in it, which never met the ground: Blake, valley polish
  // 19, note 1, "maybe we just have the portal flat".)
  const portalGeo = geo(new THREE.ShapeGeometry(archShape(6.9, -2.5), 24));
  const portalMat = keep(
    new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color(o.glow) },
        uDeep: { value: new THREE.Color(o.glow).multiplyScalar(0.18) },
        uStyle: { value: portalStyle() },
      },
      vertexShader: /* glsl */ `
        varying vec2 vP;
        void main() {
          vP = position.xy;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`,
      fragmentShader: /* glsl */ `
        uniform float uTime;
        uniform float uStyle;
        uniform vec3 uColor;
        uniform vec3 uDeep;
        varying vec2 vP;
        float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        void main() {
          vec2 c = vP - vec2(0.0, 3.2);
          float r = length(c);
          float a = atan(c.y, c.x);
          vec3 col;
          if (uStyle < 0.5) {
            // Swirl: spiral arms turning slowly in, a bright core.
            float arms = 0.5 + 0.5 * sin(a * 3.0 + log(r + 0.4) * 5.0 - uTime * 1.6);
            col = mix(uDeep, uColor, 0.25 + 0.45 * arms * smoothstep(7.0, 0.5, r));
            col = mix(col, vec3(1.0, 0.97, 0.9), exp(-r * r * 0.09) * 0.85);
            col += uColor * smoothstep(4.8, 6.6, r) * (0.6 + 0.4 * sin(a * 9.0 + uTime * 2.3)) * 0.55;
          } else if (uStyle < 1.5) {
            // Light: warm light pouring out, brightest low in the middle, soft shafts
            // drifting up, motes of dust.
            float y = clamp(vP.y / 7.0, 0.0, 1.0);
            float x = abs(vP.x) / 6.9;
            float shafts = 0.5 + 0.5 * sin(vP.x * 2.3 + sin(vP.y * 0.7 + uTime * 0.4) * 1.5 + uTime * 0.3);
            float glow = (1.0 - y * 0.7) * (1.0 - x * x * 0.8);
            col = mix(uColor, vec3(1.0, 0.96, 0.86), glow * (0.75 + 0.25 * shafts));
            vec2 m = vec2(vP.x * 1.6, vP.y * 1.6 - uTime * 0.6);
            vec2 cell = floor(m);
            float mote = step(0.93, h21(cell)) * (1.0 - smoothstep(0.05, 0.14, length(fract(m) - 0.5)));
            col += mote * 0.6;
          } else if (uStyle < 2.5) {
            // Ripple: a standing pool on its side, rings spreading out from the middle.
            float rings = 0.5 + 0.5 * sin(r * 3.2 - uTime * 2.4);
            float shimmer = 0.5 + 0.5 * sin(a * 6.0 + r * 1.5 + uTime);
            col = mix(uDeep * 2.2, uColor, 0.35 + 0.35 * rings);
            col += vec3(0.9, 0.95, 1.0) * pow(rings, 8.0) * 0.35 * shimmer;
            col = mix(col, vec3(1.0), exp(-r * r * 0.25) * 0.6);
            col += uColor * smoothstep(5.6, 6.8, r) * 0.6;
          } else if (uStyle < 3.5) {
            // Window: a glimpse of the world beyond, its sky going pale to the horizon,
            // a sun, far hills.
            float y = vP.y;
            vec3 sky = mix(vec3(1.0, 0.95, 0.85), uColor, smoothstep(0.5, 7.0, y));
            float hills = 1.4 + 0.6 * sin(vP.x * 0.9 + 1.3) + 0.35 * sin(vP.x * 2.3);
            vec3 land = uDeep * 2.5;
            col = y < hills ? land : sky;
            col = mix(col, vec3(1.0, 0.98, 0.9), (1.0 - smoothstep(0.7, 1.0, length(vP - vec2(1.8, 4.6)))) * step(hills, y));
            col *= 0.85 + 0.15 * sin(uTime * 0.8 + vP.y);
          } else {
            // Glow: a cave going in, dark warm earth at the edges and a bright opening far
            // off in the middle (flat: it only looks deep).
            float d = length(vec2(vP.x * 0.9, (vP.y - 2.0) * 1.1));
            vec3 earth = uDeep * 1.6 + vec3(0.06, 0.04, 0.02);
            col = mix(vec3(1.0, 0.95, 0.85), uColor, smoothstep(0.4, 1.6, d));
            col = mix(col, earth, smoothstep(1.8, 6.5, d));
            col *= 0.92 + 0.08 * sin(uTime * 1.3);
          }
          gl_FragColor = vec4(col, 1.0);
        }`,
      side: THREE.DoubleSide,
    }),
  );
  const portal = new THREE.Mesh(portalGeo, portalMat);
  portal.position.set(0, 0, -0.6);
  group.add(portal);

  // The sign: in front of the rock, clear of it, hung from two pegs on ropes.
  const signTex = signTexture(o.label, th, o.seed);
  texs.push(signTex);
  const signMat = keep(
    new THREE.MeshLambertMaterial({ map: signTex, side: THREE.DoubleSide, alphaTest: 0.5 }),
  );
  const sign = new THREE.Group();
  sign.position.set(0, 9.6, 3.2);
  sign.rotation.z = (r() - 0.5) * 0.05;
  sign.add(new THREE.Mesh(geo(new THREE.PlaneGeometry(13, 3.25)), signMat));
  // (A plank's thickness behind it, so it isn't paper from the side.)
  const backBoard = new THREE.Mesh(
    geo(new THREE.BoxGeometry(12.4, 3.0, 0.18)),
    keep(new THREE.MeshLambertMaterial({ color: new THREE.Color(th.plank).multiplyScalar(0.7) })),
  );
  backBoard.position.z = -0.12;
  sign.add(backBoard);
  const rope = keep(new THREE.MeshLambertMaterial({ color: "#8a7450" }));
  for (const sd of [-1, 1]) {
    const rp = new THREE.Mesh(geo(new THREE.CylinderGeometry(0.07, 0.07, 2.6, 5)), rope);
    rp.position.set(sd * 4.6, 2.7, -0.4);
    rp.rotation.set(-0.35, 0, sd * 0.08);
    sign.add(rp);
  }
  group.add(sign);

  // Torches either side of the mouth: a carved post, an iron basket, a living fire.
  const lair = o.theme === "lair";
  const postMat = keep(new THREE.MeshLambertMaterial({ color: "#5a3a20", flatShading: true }));
  const ironMat = keep(new THREE.MeshLambertMaterial({ color: "#2e2a28", flatShading: true }));
  const fires: Fire[] = [];
  for (const sd of [-1, 1]) {
    const x = sd * 9.0;
    const z = 3.6;
    // (On down 2 m into the ground, so it stands on the land on a slope too: valley
    // polish 18, note 2, "this light pole is floating".)
    const post = new THREE.Mesh(geo(new THREE.CylinderGeometry(0.2, 0.3, 6.2, 7)), postMat);
    post.position.set(x, 1.1, z);
    group.add(post);
    for (let k = 0; k < 3; k++) {
      const ring = new THREE.Mesh(geo(new THREE.TorusGeometry(0.27, 0.06, 5, 10)), ironMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.set(x, 1.2 + k * 1.1, z);
      group.add(ring);
    }
    // The basket: iron straps opening up round the coals.
    const basket = new THREE.Mesh(
      geo(new THREE.CylinderGeometry(0.62, 0.3, 0.6, 8, 1, true)),
      ironMat,
    );
    basket.position.set(x, 4.45, z);
    group.add(basket);
    const coals = new THREE.Mesh(
      geo(new THREE.CircleGeometry(0.58, 10)),
      keep(new THREE.MeshBasicMaterial({ color: lair ? 0xff3010 : 0xff7a20 })),
    );
    coals.rotation.x = -Math.PI / 2;
    coals.position.set(x, 4.62, z);
    group.add(coals);
    const fire = createFire({ red: lair, seed: o.seed + sd });
    fire.group.position.set(x, 4.6, z);
    group.add(fire.group);
    fires.push(fire);
  }
  // (Its rock, stones, sign and posts drawn as a few batches, not ~30 meshes: the lag.)
  const batching = batchStatic(group);
  return {
    group,
    update(t) {
      (portalMat.uniforms.uTime as { value: number }).value = t + o.seed;
      for (const f of fires) f.update(t);
      sign.rotation.z = Math.sin(t * 0.9 + o.seed) * 0.015;
    },
    dispose() {
      parent.remove(group);
      batching.dispose();
      for (const f of fires) f.dispose();
      for (const tx of texs) tx.dispose();
      for (const m of mats) m.dispose();
      for (const g of geos) g.dispose();
    },
  };
}
