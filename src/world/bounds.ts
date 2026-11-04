/**
 * The overworld's bounds (Blake, Nov 4: "Whenever I drive around and go to the river or
 * anywhere off the main road it's very easy to get out of bounds"). A region's land goes
 * on past where it's meant to be driven: up the snow's mountains and off the world's
 * edge, across the isles' sea floor, out of the desert past its canyon walls. Each
 * package's bounds.json (baked from its collision by tools/audit/bounds.audit.ts BAKE=1)
 * marks, on a 2 m grid, where a kart may be and how high: the land you can drive to from
 * the road without climbing more than a few metres over every road near, inside the
 * layout's walls, clear of the world's edge.
 *
 * Driving out of it is like hitting a wall you can't see: you're held at the last spot
 * in bounds and bounce off it, so you turn back. Landing out of it past the edge (off a
 * jump, or flung), you're put back on the road like a fall.
 */
import type { KartState } from "../vehicles/kart";

export interface BoundsMask {
  cell: number;
  x0: number;
  z0: number;
  w: number;
  h: number;
  /** Each cell's top: the highest a kart may be there (m; Infinity: no cap), NaN out. */
  top: Float32Array;
}

/**
 * bounds.json: the grid, and its tops run-length coded row by row ([top, n]...): a top in
 * dm, NO_CAP where nothing out of bounds is over the land, null out of bounds.
 */
export interface BoundsFile {
  builtFrom: string;
  cell: number;
  x0: number;
  z0: number;
  w: number;
  h: number;
  runs: [number | null, number][];
}

export const NO_CAP = 99999;

/** How far over a cell's top still counts (a hop, a bump, a kart on a ramp's lip). */
export const BOUNDS_SLACK = 3;

export function parseBounds(json: unknown): BoundsMask | undefined {
  const f = json as Partial<BoundsFile> | undefined;
  if (!f || typeof f !== "object" || !Array.isArray(f.runs)) return undefined;
  const { cell, x0, z0, w, h } = f;
  if (![cell, x0, z0, w, h].every((v) => typeof v === "number" && Number.isFinite(v)))
    return undefined;
  const top = new Float32Array(w! * h!).fill(NaN);
  let k = 0;
  for (const [v, n] of f.runs) {
    if (v !== null) top.fill(v === NO_CAP ? Infinity : v / 10, k, k + n);
    k += n;
  }
  if (k !== w! * h!) return undefined;
  return { cell: cell!, x0: x0!, z0: z0!, w: w!, h: h!, top };
}

/** Encode a grid of tops (NaN out) as bounds.json's runs. */
export function encodeBounds(top: Float32Array): [number | null, number][] {
  const runs: [number | null, number][] = [];
  for (let k = 0; k < top.length; k++) {
    const t = top[k]!;
    const v = Number.isNaN(t) ? null : t === Infinity ? NO_CAP : Math.ceil(t * 10);
    const last = runs[runs.length - 1];
    if (last && last[0] === v) last[1]++;
    else runs.push([v, 1]);
  }
  return runs;
}

/** In bounds at (x, z), at height y: this cell or one next to it lets you be there. */
export function inBounds(b: BoundsMask, x: number, y: number, z: number): boolean {
  const i = Math.round((x - b.x0) / b.cell);
  const j = Math.round((z - b.z0) / b.cell);
  for (let dj = -1; dj <= 1; dj++)
    for (let di = -1; di <= 1; di++) {
      const a = i + di;
      const c = j + dj;
      if (a < 0 || c < 0 || a >= b.w || c >= b.h) continue;
      const t = b.top[c * b.w + a]!;
      if (y <= t + BOUNDS_SLACK) return true;
    }
  return false;
}

/** One kart's fence: the last spot it was in bounds, and how long it's been out. */
export interface Fence {
  x: number;
  y: number;
  z: number;
  out: number;
  set: boolean;
}

export const createFence = (): Fence => ({ x: 0, y: 0, z: 0, out: 0, set: false });

/** How long landed out of bounds, past the edge, before you're put back on the road (s). */
export const BOUNDS_RESPAWN = 0.3;

/**
 * Keep a kart in bounds, after its physics step. Returns "held" when it was stopped at
 * the edge, "respawn" when it landed out of bounds past it, else undefined.
 */
export function stepBounds(
  f: Fence,
  k: KartState,
  b: BoundsMask,
  dt: number,
): "held" | "respawn" | undefined {
  if (inBounds(b, k.x, k.y, k.z)) {
    f.x = k.x;
    f.y = k.y;
    f.z = k.z;
    f.set = true;
    f.out = 0;
    return undefined;
  }
  // (never in bounds yet, put down somewhere odd by a warp: leave it be; in the air, off
  // an edge or flung over a gap: the ground decides)
  if (!f.set || !k.grounded) return undefined;
  // (landed out of bounds, past the edge: a moment to see it, then back on the road)
  if (Math.hypot(k.x - f.x, k.z - f.z) > 6) {
    f.out += dt;
    return f.out > BOUNDS_RESPAWN ? "respawn" : undefined;
  }
  // (driven into the edge: the invisible wall, held at the last spot in bounds)
  k.x = f.x;
  k.z = f.z;
  if (k.y < f.y) k.y = f.y;
  k.speed *= -0.25;
  if (Math.abs(k.speed) < 1) k.speed = 0;
  f.out = 0;
  return "held";
}
