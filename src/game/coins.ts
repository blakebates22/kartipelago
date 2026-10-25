/**
 * Silver coins: Adventure's treasure map challenge. Four on a ruined course; collect all
 * four AND win the race to earn that course's piece of the map (src/adventure/progress.ts).
 *
 * A coin is placed like a banana (distance along the lap, offset across the road) and
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

/** The coins in 3D: spinning silver discs with a soft glow, and a sparkle when taken. */
export function createCoinView(root: THREE.Object3D, field: CoinField) {
  const group = new THREE.Group();
  group.name = "Silver Coins";
  root.add(group);
  const geo = new THREE.CylinderGeometry(0.85, 0.85, 0.16, 20);
  geo.rotateX(Math.PI / 2);
  const rim = new THREE.TorusGeometry(0.85, 0.09, 6, 20);
  const mat = new THREE.MeshStandardMaterial({
    color: 0xdfe6ee,
    metalness: 0.85,
    roughness: 0.25,
    emissive: 0x5a6878,
    emissiveIntensity: 0.6,
  });
  const rimMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    metalness: 0.9,
    roughness: 0.2,
    emissive: 0x8090a0,
    emissiveIntensity: 0.5,
  });
  const meshes = field.coins.map((c) => {
    const m = new THREE.Group();
    m.add(new THREE.Mesh(geo, mat), new THREE.Mesh(rim, rimMat));
    m.position.set(c.x, c.y, c.z);
    group.add(m);
    return m;
  });
  /** Taken coins fly up and shrink away for a moment. */
  const leaving = new Map<number, number>();
  return {
    render(now: number, frameSeconds: number) {
      field.coins.forEach((c, i) => {
        const m = meshes[i]!;
        if (c.taken) {
          const t = (leaving.get(i) ?? 0) + frameSeconds;
          leaving.set(i, t);
          m.visible = t < 0.45;
          m.position.y = c.y + t * 6;
          m.scale.setScalar(Math.max(0.01, 1 - t * 2));
        } else {
          leaving.delete(i);
          m.visible = true;
          m.scale.setScalar(1);
          m.position.y = c.y + Math.sin(now * 2.4 + i) * 0.18;
        }
        m.rotation.y = now * 3 + i;
      });
    },
    dispose() {
      root.remove(group);
      geo.dispose();
      rim.dispose();
      mat.dispose();
      rimMat.dispose();
    },
  };
}
