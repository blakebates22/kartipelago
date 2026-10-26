/**
 * Map fragments: Adventure's treasure map challenge. Four torn fragments of the map on a
 * ruined course; collect all four AND win the race to earn that course's piece of the map
 * (src/adventure/progress.ts). (Silver coins at first; Blake wanted the map itself. The
 * code still calls each one a coin.)
 *
 * A fragment is placed like a banana (distance along the lap, offset across the road) and
 * hangs a little above the road. Only the player collects them, once per race (they
 * don't come back on the next lap); a restart puts them all back. Without spots of its
 * own, a course gets four spread round the lap (`autoCoinSpots`).
 */
import * as THREE from "three";
import type { Track } from "../world/track";

export interface CoinSpot {
  /** Distance along the lap from the start line, metres. */
  at: number;
  /** Offset across the road, metres; positive is toward the right edge. */
  across?: number;
  /** Height above the road, metres (default 1.3: a kart drives through it). */
  up?: number;
}

export interface Coin {
  x: number;
  y: number;
  z: number;
  taken: boolean;
}

export interface CoinField {
  coins: Coin[];
}

/** How close (metres, flat) and how far above or below a kart can be to take a coin. */
export const COIN_RADIUS = 2.6;
const COIN_HEIGHT = 3.0;

/** Four spots spread round the lap, alternating sides, clear of the start line. */
export function autoCoinSpots(lapLength: number, count = 4): CoinSpot[] {
  const fractions = [0.18, 0.41, 0.63, 0.86];
  return Array.from({ length: count }, (_, i) => ({
    at: Math.round(lapLength * (fractions[i] ?? (i + 0.5) / count)),
    across: i % 2 ? 3.5 : -3.5,
  }));
}

export function createCoinField(track: Track | undefined, spots: CoinSpot[]): CoinField {
  const coins: Coin[] = [];
  if (track) {
    const n = track.samples.length;
    for (const spot of spots) {
      const s = track.samples[((Math.round((spot.at / track.length) * n) % n) + n) % n]!;
      const rh = Math.hypot(s.right.x, s.right.z) || 1;
      const across = Math.max(-s.width / 2 + 1.5, Math.min(s.width / 2 - 1.5, spot.across ?? 0));
      coins.push({
        x: s.pos.x + (s.right.x / rh) * across,
        y: s.pos.y + s.right.y * (across / rh) + (spot.up ?? 1.3),
        z: s.pos.z + (s.right.z / rh) * across,
        taken: false,
      });
    }
  }
  return { coins };
}

/** The player at (x, y, z): returns how many coins they took this step. */
export function collectCoins(field: CoinField, x: number, y: number, z: number): number {
  let got = 0;
  for (const c of field.coins) {
    if (c.taken) continue;
    if (Math.hypot(c.x - x, c.z - z) < COIN_RADIUS && Math.abs(c.y - 1.0 - y) < COIN_HEIGHT) {
      c.taken = true;
      got++;
    }
  }
  return got;
}

export const coinsTaken = (field: CoinField) => field.coins.filter((c) => c.taken).length;

export function resetCoins(field: CoinField) {
  for (const c of field.coins) c.taken = false;
}

/** The parchment the map is drawn on: one drawing, each fragment shows its quarter. */
function mapTexture() {
  const size = 256;
  const cv = document.createElement("canvas");
  cv.width = cv.height = size;
  const g = cv.getContext("2d")!;
  g.fillStyle = "#e8cf98";
  g.fillRect(0, 0, size, size);
  // Stains and age.
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let k = 0; k < 40; k++) {
    g.fillStyle = `rgba(150,105,50,${0.05 + rnd() * 0.08})`;
    g.beginPath();
    g.arc(rnd() * size, rnd() * size, 8 + rnd() * 30, 0, Math.PI * 2);
    g.fill();
  }
  // Coastlines, mountains, a winding dotted trail and the red X.
  g.strokeStyle = "#6a4420";
  g.lineWidth = 4;
  g.beginPath();
  g.moveTo(20, 60);
  g.bezierCurveTo(80, 20, 120, 110, 200, 50);
  g.bezierCurveTo(240, 120, 180, 200, 230, 236);
  g.stroke();
  g.lineWidth = 3;
  for (const [x, y] of [
    [60, 170],
    [84, 150],
    [108, 176],
  ]) {
    g.beginPath();
    g.moveTo(x! - 14, y! + 12);
    g.lineTo(x!, y! - 14);
    g.lineTo(x! + 14, y! + 12);
    g.stroke();
  }
  g.setLineDash([7, 7]);
  g.strokeStyle = "#8a2a1a";
  g.beginPath();
  g.moveTo(30, 230);
  g.bezierCurveTo(70, 120, 150, 230, 140, 130);
  g.bezierCurveTo(130, 80, 170, 90, 186, 150);
  g.stroke();
  g.setLineDash([]);
  g.lineWidth = 8;
  g.strokeStyle = "#c8261a";
  g.beginPath();
  g.moveTo(174, 138);
  g.lineTo(198, 162);
  g.moveTo(198, 138);
  g.lineTo(174, 162);
  g.stroke();
  // The edge, darkened.
  g.strokeStyle = "rgba(110,70,30,0.6)";
  g.lineWidth = 10;
  g.strokeRect(0, 0, size, size);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Fragment `i` of 4: a quarter of the map, torn along its two inner edges. */
function fragmentGeometry(i: number, size: number) {
  const qx = i % 2;
  const qy = Math.floor(i / 2) % 2;
  const tear = (k: number) => 0.06 * Math.sin(k * 2.7 + i * 1.3) + 0.04 * Math.sin(k * 6.1 + i);
  // The quarter in 0..1, its torn sides towards the map's middle.
  const pts: [number, number][] = [];
  const n = 7;
  const tornX = qx === 0 ? 1 : 0; // which vertical edge is the tear
  const tornY = qy === 0 ? 0 : 1;
  const corners: [number, number][] = [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
  ];
  for (let e = 0; e < 4; e++) {
    const [ax, ay] = corners[e]!;
    const [bx, by] = corners[(e + 1) % 4]!;
    const vertical = ax === bx;
    const torn = vertical ? ax === tornX : ay === tornY;
    for (let k = 0; k < (torn ? n : 1); k++) {
      const f = k / (torn ? n : 1);
      let x = ax + (bx - ax) * f;
      let y = ay + (by - ay) * f;
      if (torn && k > 0) {
        if (vertical) x += tear(k + e * 3) * (tornX ? -1 : 1);
        else y += tear(k + e * 3) * (tornY ? -1 : 1);
      }
      pts.push([x, y]);
    }
  }
  const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x - 0.5, y - 0.5)));
  const geo = new THREE.ShapeGeometry(shape);
  const pos = geo.getAttribute("position") as THREE.BufferAttribute;
  const uv = geo.getAttribute("uv") as THREE.BufferAttribute;
  for (let v = 0; v < pos.count; v++) {
    const u = pos.getX(v) + 0.5;
    const w = pos.getY(v) + 0.5;
    // Quarter qx, qy of the drawing (qy 0 is its top half).
    uv.setXY(v, (qx + u) / 2, (1 - qy + w) / 2);
    pos.setXYZ(v, pos.getX(v) * size, pos.getY(v) * size, 0);
  }
  geo.computeBoundingSphere();
  return geo;
}

/** A soft golden glow behind each fragment, so you can spot them down the road. */
function glowTexture() {
  const cv = document.createElement("canvas");
  cv.width = cv.height = 64;
  const g = cv.getContext("2d")!;
  const grad = g.createRadialGradient(32, 32, 2, 32, 32, 32);
  grad.addColorStop(0, "rgba(255,230,140,0.9)");
  grad.addColorStop(1, "rgba(255,200,80,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(cv);
}

/**
 * The fragments in 3D: four torn quarters of a treasure map (each its own corner of the
 * same drawing), turning and bobbing in a golden glow; a taken one flies up and away.
 */
export function createCoinView(root: THREE.Object3D, field: CoinField) {
  const group = new THREE.Group();
  group.name = "Map Fragments";
  root.add(group);
  const tex = mapTexture();
  const mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide });
  const glowMat = new THREE.SpriteMaterial({
    map: glowTexture(),
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const geos = field.coins.map((_, i) => fragmentGeometry(i, 2.6));
  const meshes = field.coins.map((c, i) => {
    const m = new THREE.Group();
    const paper = new THREE.Mesh(geos[i]!, mat);
    paper.rotation.z = (i % 2 ? -1 : 1) * 0.2;
    const glow = new THREE.Sprite(glowMat);
    glow.scale.setScalar(4.6);
    m.add(glow, paper);
    m.position.set(c.x, c.y + 0.3, c.z);
    group.add(m);
    return m;
  });
  /** Taken fragments fly up and shrink away for a moment. */
  const leaving = new Map<number, number>();
  return {
    render(now: number, frameSeconds: number) {
      field.coins.forEach((c, i) => {
        const m = meshes[i]!;
        if (c.taken) {
          const t = (leaving.get(i) ?? 0) + frameSeconds;
          leaving.set(i, t);
          m.visible = t < 0.45;
          m.position.y = c.y + 0.3 + t * 6;
          m.scale.setScalar(Math.max(0.01, 1 - t * 2));
        } else {
          leaving.delete(i);
          m.visible = true;
          m.scale.setScalar(1);
          m.position.y = c.y + 0.3 + Math.sin(now * 2.4 + i) * 0.18;
        }
        m.rotation.y = now * 1.8 + i;
        m.rotation.x = Math.sin(now * 1.3 + i) * 0.15;
      });
    },
    dispose() {
      root.remove(group);
      for (const g of geos) g.dispose();
      mat.dispose();
      tex.dispose();
      glowMat.map?.dispose();
      glowMat.dispose();
    },
  };
}
