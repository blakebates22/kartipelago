/**
 * The Drift Park: isolated practice loops, each one meant to be driven all the way round
 * in a single drift without letting go.
 *
 * The loops are not drawn by hand. Their shapes come from the drift itself:
 * - A drift can only hold one direction, so every loop turns one way all the way round
 *   (no S-bends, no straights).
 * - The tightest a drift can carve is `driftRadiusTight` (full lock).
 * - The widest it can hold for long is set by the spin-out: countersteer past
 *   `spinThreshold` for `spinOutAfterSec` spins you. That steer gives the "spin radius"
 *   (about 53 m). Wider than that is only possible in short bursts.
 *
 * Each loop's curvature rises and falls smoothly between a tightest and a widest radius,
 * `lobes` times round the loop (a rounded triangle, oval or square). So you can't just
 * hold the stick still: you steer in through the tight parts and ease out (or
 * countersteer) through the wide parts. The four sizes step across the drift's range,
 * from "near full lock all the way" to "manage your countersteer without spinning".
 *
 * Every size comes three ways: plain, with bananas sprinkled on the line (they come
 * back a few seconds after you take them), and with zippers on the wide parts.
 */
import type { GroundQuery, Surface } from "../physics/ground";
import { driftCurvature, type KartConfig } from "../vehicles/kart";
import { buildTrack, type Track, type TrackData, type TrackPoint } from "./track";

export interface DriftRadii {
  driftRadiusTight: number;
  driftRadiusNeutral: number;
  driftRadiusCounter: number;
  driftInCurve: number;
  driftCounterCurve: number;
  spinThreshold: number;
}

export interface ParkConfig {
  /** Road width of every loop, metres. */
  loopWidth: number;
  /** Space between neighbouring loops, metres. */
  loopGap: number;
  /** Seconds before a banana you took on a banana loop comes back. */
  bananaRespawnSec: number;
}

export interface LoopSize {
  id: string;
  name: string;
  /** How many tight-wide cycles round the loop (3 = rounded triangle). */
  lobes: number;
  /** Tightest and widest radius on the centre line, metres. */
  rMin: number;
  rMax: number;
}

export type LoopVariant = "plain" | "bananas" | "zipper";

export interface ParkLoop {
  /** 0-based position in the park (the order [ and ] step through). */
  index: number;
  size: LoopSize;
  variant: LoopVariant;
  name: string;
  track: Track;
  /** Bounding box of the road, metres. */
  box: { minX: number; maxX: number; minZ: number; maxZ: number };
}

export interface DriftPark {
  loops: ParkLoop[];
}

/** The widest radius a drift can hold indefinitely (just under the spin-out steer). */
export function spinRadius(r: DriftRadii) {
  // The park's loops are sized on the original countersteer shape (where countersteer
  // only widens the arc), whichever shape is in use.
  return 1 / driftCurvature(-r.spinThreshold, { ...r, driftCounterOut: false } as KartConfig);
}

/**
 * The four sizes, all taken from the drift's own radii:
 * 1. Tight: inside the hands-off radius all the way; steer in hard, ease a little.
 * 2. Neutral: swings either side of the hands-off radius.
 * 3. Wide: mostly countersteer, touching the spin radius on the wide parts.
 * 4. Grand: big and sweeping; short bursts past the spin radius, so you have to ease
 *    off the countersteer now and then to reset the spin-out count.
 */
export function loopSizes(r: DriftRadii): LoopSize[] {
  const tight = r.driftRadiusTight;
  const neutral = r.driftRadiusNeutral;
  const spin = spinRadius(r);
  return [
    { id: "tight", name: "Tight", lobes: 3, rMin: tight * 1.3, rMax: neutral * 0.95 },
    { id: "neutral", name: "Neutral", lobes: 2, rMin: tight * 1.4, rMax: neutral * 1.3 },
    { id: "wide", name: "Wide", lobes: 3, rMin: neutral * 0.9, rMax: spin * 1.05 },
    { id: "grand", name: "Grand", lobes: 5, rMin: neutral * 1.05, rMax: spin * 1.35 },
  ];
}

/** Curvature profile: widest at the start line, tightest half a lobe later. */
function profile(size: LoopSize) {
  const kMid = (1 / size.rMin + 1 / size.rMax) / 2;
  const kAmp = (1 / size.rMin - 1 / size.rMax) / 2;
  // Turning 360° in all means kMid × length = 2π.
  const length = (2 * Math.PI) / kMid;
  return { kMid, kAmp, length };
}

/** Length of a loop's centre line, metres. */
export const loopLength = (size: LoopSize) => profile(size).length;

/** Distances along the loop (from the start line) of its widest and tightest points. */
export function loopMarks(size: LoopSize) {
  const { length } = profile(size);
  const wide: number[] = [];
  const apex: number[] = [];
  for (let j = 0; j < size.lobes; j++) {
    wide.push((j / size.lobes) * length);
    apex.push(((j + 0.5) / size.lobes) * length);
  }
  return { wide, apex };
}

/**
 * Centre points of a loop starting at (0, 0) heading +z and turning left, about `step`
 * metres apart. With the curvature repeating `lobes` (2 or more) times round the loop
 * and 360° of turning in all, the shape closes on itself exactly.
 */
export function loopPoints(size: LoopSize, step = 5): TrackPoint[] {
  const { kMid, kAmp, length } = profile(size);
  const count = Math.max(24, Math.round(length / step));
  const sub = 40; // fine integration steps between points
  const ds = length / (count * sub);
  const heading = (s: number) =>
    kMid * s -
    (kAmp * length * Math.sin((2 * Math.PI * size.lobes * s) / length)) /
      (2 * Math.PI * size.lobes);
  const pts: TrackPoint[] = [];
  let x = 0;
  let z = 0;
  for (let i = 0; i < count; i++) {
    pts.push({ x, z });
    for (let k = 0; k < sub; k++) {
      const s = (i * sub + k + 0.5) * ds;
      const h = heading(s);
      x += Math.sin(h) * ds;
      z += Math.cos(h) * ds;
    }
  }
  return pts;
}

/** Bananas on a loop: a row on the inside at each apex, and singles between. */
function bananaSpots(size: LoopSize, respawn: number): NonNullable<TrackData["bananas"]> {
  const { wide, apex } = loopMarks(size);
  const lobe = loopLength(size) / size.lobes;
  const spots: NonNullable<TrackData["bananas"]> = [];
  // The loops turn left, so the inside is to the left (negative across).
  for (let j = 0; j < size.lobes; j++) {
    spots.push({ at: apex[j]! - 5, across: -2.5, count: 3, gap: 5, respawn });
    spots.push({ at: apex[j]! + lobe * 0.25, across: 3, respawn });
    if (j > 0) spots.push({ at: wide[j]!, across: 0, respawn });
    spots.push({ at: wide[j]! + lobe * 0.2, across: -2, respawn });
  }
  return spots;
}

/** Zippers on the wide parts: one just past the start, and one more on the big loops. */
function zipperSpots(size: LoopSize): NonNullable<TrackData["zippers"]> {
  const { wide } = loopMarks(size);
  const spots = [{ at: 18 }];
  if (size.lobes >= 3) spots.push({ at: wide[Math.floor(size.lobes / 2)]! });
  return spots;
}

const VARIANTS: LoopVariant[] = ["plain", "bananas", "zipper"];
const VARIANT_LABEL: Record<LoopVariant, string> = {
  plain: "",
  bananas: " + bananas",
  zipper: " + zipper",
};

function loopData(size: LoopSize, variant: LoopVariant, cfg: ParkConfig, ox: number, oz: number) {
  const data: TrackData = {
    name: size.name + VARIANT_LABEL[variant],
    defaultWidth: cfg.loopWidth,
    open: true,
    points: loopPoints(size).map((p) => ({ x: p.x + ox, z: p.z + oz })),
  };
  if (variant === "bananas") data.bananas = bananaSpots(size, cfg.bananaRespawnSec);
  if (variant === "zipper") data.zippers = zipperSpots(size);
  return data;
}

function boxOf(points: TrackPoint[], halfWidth: number) {
  let minX = Infinity;
  let maxX = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;
  for (const p of points) {
    minX = Math.min(minX, p.x - halfWidth);
    maxX = Math.max(maxX, p.x + halfWidth);
    minZ = Math.min(minZ, p.z - halfWidth);
    maxZ = Math.max(maxZ, p.z + halfWidth);
  }
  return { minX, maxX, minZ, maxZ };
}

/**
 * Lay the park out as a grid: one column per size (smallest on the left), one row per
 * variant (plain, bananas, zipper), centred on the origin.
 */
export function buildDriftPark(
  radii: DriftRadii,
  cfg: ParkConfig,
  sampleSpacing: number,
): DriftPark {
  const sizes = loopSizes(radii);
  const half = cfg.loopWidth / 2;
  const shapes = sizes.map((size) => boxOf(loopPoints(size), half));
  const colW = shapes.map((b) => b.maxX - b.minX);
  const rowH = Math.max(...shapes.map((b) => b.maxZ - b.minZ));
  const totalW = colW.reduce((a, b) => a + b, 0) + cfg.loopGap * (sizes.length - 1);
  const totalH = rowH * VARIANTS.length + cfg.loopGap * (VARIANTS.length - 1);

  const loops: ParkLoop[] = [];
  VARIANTS.forEach((variant, row) => {
    let left = -totalW / 2;
    sizes.forEach((size, col) => {
      const b = shapes[col]!;
      // Place the loop's box at (left, top of this row), centred in the row's height.
      const top = -totalH / 2 + row * (rowH + cfg.loopGap) + (rowH - (b.maxZ - b.minZ)) / 2;
      const ox = left - b.minX;
      const oz = top - b.minZ;
      left += colW[col]! + cfg.loopGap;
      const data = loopData(size, variant, cfg, ox, oz);
      const track = buildTrack(data, sampleSpacing);
      loops.push({
        index: loops.length,
        size,
        variant,
        name: `${loops.length + 1} · ${data.name}`,
        track,
        box: boxOf(data.points, half),
      });
    });
  });
  return { loops };
}

// ------------------------------------------------------------------ finding a kart

export interface LoopSpot {
  loop: ParkLoop;
  /** Nearest centre-line sample. */
  sample: number;
  /** Signed distance from the centre line toward the right edge, metres. */
  across: number;
  onRoad: boolean;
}

/**
 * Which loop is a point on (or nearest to)? Each locator remembers where it last found
 * its kart on every loop, so most lookups only check a few nearby samples.
 */
export function createLocator(park: DriftPark) {
  const hints = park.loops.map(() => 0);
  const MARGIN = 20;

  const nearestOn = (l: ParkLoop, x: number, z: number) => {
    const s = l.track.samples;
    const n = s.length;
    const d2 = (i: number) => {
      const p = s[((i % n) + n) % n]!.pos;
      return (p.x - x) ** 2 + (p.z - z) ** 2;
    };
    let best = hints[l.index]!;
    let bestD = d2(best);
    for (let k = -25; k <= 25; k++) {
      const d = d2(best + k);
      if (d < bestD) {
        bestD = d;
        best = best + k;
      }
    }
    if (bestD > 15 * 15)
      for (let i = 0; i < n; i++) {
        const d = d2(i);
        if (d < bestD) {
          bestD = d;
          best = i;
        }
      }
    best = ((best % n) + n) % n;
    hints[l.index] = best;
    return best;
  };

  return {
    at(x: number, z: number): LoopSpot | undefined {
      let found: LoopSpot | undefined;
      let foundEdge = Infinity;
      for (const l of park.loops) {
        const b = l.box;
        if (
          x < b.minX - MARGIN ||
          x > b.maxX + MARGIN ||
          z < b.minZ - MARGIN ||
          z > b.maxZ + MARGIN
        )
          continue;
        const i = nearestOn(l, x, z);
        const s = l.track.samples[i]!;
        const across = (x - s.pos.x) * s.right.x + (z - s.pos.z) * s.right.z;
        const edge = Math.abs(across) - s.width / 2;
        if (edge < foundEdge) {
          foundEdge = edge;
          found = { loop: l, sample: i, across, onRoad: edge <= 0 };
        }
      }
      return found;
    },
  };
}

// ------------------------------------------------------------------ drift streaks

export interface StreakState {
  /** Loop the streak is on (-1 = none). */
  loop: number;
  sample: number;
  /** Distance driven round the loop in the current unbroken drift, metres. */
  held: number;
  /** Best streak per loop, in laps. */
  best: number[];
  /** Whole laps already announced for the current streak. */
  announced: number;
}

export const createStreak = (park: DriftPark): StreakState => ({
  loop: -1,
  sample: 0,
  held: 0,
  best: park.loops.map(() => 0),
  announced: 0,
});

/**
 * One step of the drift streak: the distance round the loop covered in one unbroken
 * drift, staying on the road. Letting go of the drift, spinning out or leaving the road
 * ends it. Returns the number of whole laps when one has just been completed.
 */
export function stepStreak(
  st: StreakState,
  park: DriftPark,
  spot: LoopSpot | undefined,
  drifting: boolean,
): number | undefined {
  const onLoop = spot && spot.onRoad ? spot.loop.index : -1;
  if (!drifting || onLoop < 0 || onLoop !== st.loop) {
    st.held = 0;
    st.announced = 0;
    st.loop = onLoop;
    if (spot && onLoop >= 0) st.sample = spot.sample;
    return undefined;
  }
  const track = park.loops[onLoop]!.track;
  const n = track.samples.length;
  let step = spot!.sample - st.sample;
  if (step > n / 2) step -= n;
  if (step < -n / 2) step += n;
  st.sample = spot!.sample;
  st.held += (Math.abs(step) * track.length) / n;
  const laps = st.held / track.length;
  if (laps > st.best[onLoop]!) st.best[onLoop] = laps;
  if (Math.floor(laps) > st.announced) {
    st.announced = Math.floor(laps);
    return st.announced;
  }
  return undefined;
}

/** Laps held in the current streak. */
export const streakLaps = (st: StreakState, park: DriftPark) =>
  st.loop < 0 ? 0 : st.held / park.loops[st.loop]!.track.length;

// ------------------------------------------------------------------ ground

/**
 * "What's under me?" for the park: flat ground everywhere, with the road of whichever
 * loop the kart is on (or nearest to) for on-road checks.
 */
export function createParkGround(park: DriftPark): GroundQuery {
  const locate = createLocator(park);
  return {
    at(x, z): Surface {
      const spot = locate.at(x, z);
      if (!spot) return { height: 0, nx: 0, ny: 1, nz: 0, onRoad: false };
      const s = spot.loop.track.samples[spot.sample]!;
      return {
        height: 0,
        nx: 0,
        ny: 1,
        nz: 0,
        onRoad: spot.onRoad,
        road: {
          across: spot.across,
          halfWidth: s.width / 2,
          rx: s.right.x,
          rz: s.right.z,
          centreY: 0,
          rise: 0,
        },
      };
    },
  };
}

/** Distance from (x, z) to the nearest road edge in the park (negative = on a road). */
export function distanceToRoad(park: DriftPark, x: number, z: number) {
  let best = Infinity;
  for (const l of park.loops)
    for (const s of l.track.samples)
      best = Math.min(best, Math.hypot(s.pos.x - x, s.pos.z - z) - s.width / 2);
  return best;
}

/** Where to start on a loop: its start line, facing either way round. */
export function loopStart(loop: ParkLoop, reverse: boolean) {
  const { x, z, heading } = loop.track.start;
  return { x, z, y: 0, heading: reverse ? heading + Math.PI : heading };
}
