/**
 * A racing line, computed from a track's samples. Start on the centre line and
 * repeatedly pull every point toward the midpoint of its neighbours, keeping it inside
 * the road. Smoothing straightens the path, so it cuts the inside of corners and swings
 * wide on entry and exit, which is what a racing line does.
 */
import type { Track } from "../world/track";

export interface LineConfig {
  /** Keep the line this far inside the road edges, metres. */
  margin: number;
  /** Neighbour distance used when smoothing, metres. Larger = straighter line. */
  span: number;
  iterations: number;
}

export interface RacingLine {
  n: number;
  /** Metres between points. */
  spacing: number;
  x: Float64Array;
  z: Float64Array;
  /** Direction of travel along the line (kart heading convention). */
  heading: Float64Array;
  /** Signed curvature, 1/m: positive turns left, negative turns right. */
  curvature: Float64Array;
  /** Road height at each point (for telling stacked roads apart). */
  y: Float64Array;
  /** The road's right (horizontal unit vector) at each point. */
  rx: Float64Array;
  rz: Float64Array;
  /** How far a kart can move off the line to the left (negative) and right (positive)
   * and still be on the road, metres (a little short of the edges). */
  roomLeft: Float64Array;
  roomRight: Float64Array;
  /** The road's width at each point, metres. */
  width: Float64Array;
}

/** Keep this far inside the road's edges when moving off the line, metres. */
const EDGE = 1.4;

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

export function buildRacingLine(track: Track, cfg: LineConfig): RacingLine {
  const s = track.samples;
  const n = s.length;
  const spacing = track.length / n;
  const k = Math.max(1, Math.round(cfg.span / spacing));
  const at = (i: number) => s[((i % n) + n) % n]!;

  // Horizontal unit right vector and allowed offset at each sample.
  const rx = new Float64Array(n);
  const rz = new Float64Array(n);
  const lim = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const r = s[i]!.right;
    const h = Math.hypot(r.x, r.z);
    rx[i] = r.x / h;
    rz[i] = r.z / h;
    lim[i] = Math.max(0, s[i]!.width / 2 - cfg.margin);
  }

  let off = new Float64Array(n);
  const px = (i: number, o: Float64Array) =>
    at(i).pos.x + rx[((i % n) + n) % n]! * o[((i % n) + n) % n]!;
  const pz = (i: number, o: Float64Array) =>
    at(i).pos.z + rz[((i % n) + n) % n]! * o[((i % n) + n) % n]!;
  for (let it = 0; it < cfg.iterations; it++) {
    const next = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const mx = (px(i - k, off) + px(i + k, off)) / 2;
      const mz = (pz(i - k, off) + pz(i + k, off)) / 2;
      const c = s[i]!.pos;
      const want = (mx - c.x) * rx[i]! + (mz - c.z) * rz[i]!;
      // Relax halfway toward the smoothed position, then keep it on the road.
      const o = off[i]! + (want - off[i]!) * 0.5;
      next[i] = Math.max(-lim[i]!, Math.min(lim[i]!, o));
    }
    off = next;
  }

  const x = new Float64Array(n);
  const z = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    x[i] = px(i, off);
    z[i] = pz(i, off);
  }
  const heading = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const a = (i - 1 + n) % n;
    const b = (i + 1) % n;
    heading[i] = Math.atan2(x[b]! - x[a]!, z[b]! - z[a]!);
  }
  // Curvature over a few metres either side, so sampling noise doesn't dominate.
  const c = Math.max(1, Math.round(4 / spacing));
  const curvature = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const turn = wrap(heading[(i + c) % n]! - heading[(i - c + n) % n]!);
    curvature[i] = turn / (2 * c * spacing);
  }
  const y = new Float64Array(n);
  const roomLeft = new Float64Array(n);
  const roomRight = new Float64Array(n);
  const width = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    y[i] = s[i]!.pos.y;
    const half = Math.max(0, s[i]!.width / 2 - EDGE);
    roomRight[i] = Math.max(0, half - off[i]!);
    roomLeft[i] = -Math.max(0, half + off[i]!);
    width[i] = s[i]!.width;
  }
  return { n, spacing, x, z, heading, curvature, y, rx, rz, roomLeft, roomRight, width };
}
