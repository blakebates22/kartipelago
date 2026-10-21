/**
 * Geysers (Snowy Summit Pass): hot springs that blow on a fixed beat of the race clock,
 * so every race (and every time trial) sees exactly the same eruptions.
 *
 * From the track.json entity:
 *
 *   { "type": "geyser", "x", "y", "z",          the vent (y is its surface)
 *     "r": 4, "height": 20,                     the column's radius and height
 *     "period": 7, "offset": 0, "warn": 1.4, "blast": 2.2,
 *     "launch": 15,                             upward speed it gives a kart (0: none)
 *     "lava": false }                           a lava geyser: it burns instead (below)
 *
 * Each period runs IDLE (a gentle steam) -> WARNING (it bubbles and gurgles, steam
 * thickening) -> BLAST (a roaring column of water and steam). A kart inside the column
 * during the blast is thrown into the air at `launch` m/s, keeping its speed and
 * heading: a free jump, not a penalty. Hit the geyser in the road as it blows and you
 * fly; drive over it the rest of the time and nothing happens.
 *
 * A lava geyser (Impact Depths) keeps the same beat, but its column is fire: caught in
 * it as it blows and you get the same burning bounce as lava. Its warning (the vent
 * glowing, spitting sparks) gives you time to go round.
 */

export type GeyserPhase = "idle" | "warning" | "blast";

export interface GeyserConfig {
  x: number;
  y: number;
  z: number;
  r: number;
  height: number;
  period: number;
  offset: number;
  warn: number;
  blast: number;
  launch: number;
  lava: boolean;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

/** A geyser from a track.json entity (defaults for anything missing). */
export function parseGeyser(e: Record<string, unknown>): GeyserConfig {
  const warn = Math.max(0.2, num(e.warn, 1.4));
  const blast = Math.max(0.3, num(e.blast, 2.2));
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    r: Math.max(0.5, num(e.r, 4)),
    height: Math.max(2, num(e.height, 18)),
    // At least a moment of quiet between eruptions.
    period: Math.max(num(e.period, 7), warn + blast + 0.5),
    offset: num(e.offset, 0),
    warn,
    blast,
    launch: Math.max(0, num(e.launch, 0)),
    lava: e.lava === true,
  };
}

/** Where the geyser is in its cycle at race time `clock`, and how far through that
 * phase (0..1). Pure: the same clock always gives the same answer. */
export function geyserPhase(g: GeyserConfig, clock: number): { phase: GeyserPhase; t: number } {
  const u = (((clock - g.offset) % g.period) + g.period) % g.period;
  const idle = g.period - g.warn - g.blast;
  if (u < idle) return { phase: "idle", t: u / idle };
  if (u < idle + g.warn) return { phase: "warning", t: (u - idle) / g.warn };
  return { phase: "blast", t: (u - idle - g.warn) / g.blast };
}

/** Is (x, y, z) inside the column (whether it's blowing or not)? */
export function inColumn(g: GeyserConfig, x: number, y: number, z: number): boolean {
  return Math.hypot(x - g.x, z - g.z) <= g.r && y >= g.y - 1.5 && y <= g.y + g.height;
}

/** Does the geyser throw a kart at (x, y, z) into the air at race time `clock`? (Only
 * while blowing, and not in the last fifth of the blast, as the column falls.) */
export function geyserLifts(
  g: GeyserConfig,
  clock: number,
  x: number,
  y: number,
  z: number,
): boolean {
  if (g.launch <= 0) return false;
  const { phase, t } = geyserPhase(g, clock);
  return phase === "blast" && t < 0.8 && inColumn(g, x, y, z);
}

/** Does a lava geyser burn a kart at (x, y, z) at race time `clock`? (While blowing,
 * until the column has mostly fallen.) */
export function geyserBurns(
  g: GeyserConfig,
  clock: number,
  x: number,
  y: number,
  z: number,
): boolean {
  if (!g.lava) return false;
  const { phase, t } = geyserPhase(g, clock);
  return phase === "blast" && t < 0.85 && inColumn(g, x, y, z);
}
