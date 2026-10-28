/**
 * Shard pieces: Adventure's light shards (Blake, Oct 27: the map pieces became shard
 * pieces). Four pieces of Lumen's light on a ruined course; collect all four AND win the
 * race to earn that course's light shard (src/adventure/progress.ts). (Silver coins at
 * first, then torn map fragments; the code still calls each one a coin.)
 *
 * A piece is placed like a banana (distance along the lap, offset across the road) and
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

/** A shard piece: a long crystal, a little different each (`i`). */
function pieceGeometry(i: number) {
  const g = new THREE.OctahedronGeometry(0.62, 0);
  const pos = g.getAttribute("position") as THREE.BufferAttribute;
  for (let v = 0; v < pos.count; v++) {
    const y = pos.getY(v);
    pos.setXYZ(
      v,
      pos.getX(v) * (0.7 + 0.1 * (i % 2)),
      y * (1.9 + 0.25 * (i % 3)),
      pos.getZ(v) * 0.55,
    );
  }
  g.computeVertexNormals();
  return g;
}

/**
 * The shard pieces in 3D: four crystals of pale gold light, turning and bobbing in a
 * glow; a taken one flies up and away.
 */
export function createCoinView(root: THREE.Object3D, field: CoinField) {
  const group = new THREE.Group();
  group.name = "Shard Pieces";
  root.add(group);
  const mat = new THREE.MeshLambertMaterial({
    color: "#fff0b0",
    emissive: new THREE.Color("#f0c850"),
    emissiveIntensity: 0.9,
    flatShading: true,
  });
  const glowMat = new THREE.SpriteMaterial({
    map: glowTexture(),
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const geos = field.coins.map((_, i) => pieceGeometry(i));
  const meshes = field.coins.map((c, i) => {
    const m = new THREE.Group();
    const paper = new THREE.Mesh(geos[i]!, mat);
    paper.rotation.z = (i % 2 ? -1 : 1) * 0.25;
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
      glowMat.map?.dispose();
      glowMat.dispose();
    },
  };
}
