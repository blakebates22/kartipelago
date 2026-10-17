/**
 * Starting grid: two columns of slots behind the start line, staggered, following the
 * track's curve (the line sits at the end of a corner, so "behind" isn't a straight line).
 */
import type { Track } from "../world/track";

export interface GridSlot {
  x: number;
  y: number;
  z: number;
  heading: number;
}

/** Metres between rows, distance of the first row behind the line, column offset. */
const ROW_GAP = 7;
const FIRST_ROW = 5;
const COLUMN = 4.5;

export function gridSlot(track: Track, slot: number): GridSlot {
  const row = Math.floor(slot / 2);
  const side = slot % 2 === 0 ? -1 : 1; // left column first
  // Odd slots sit half a row further back, so karts don't start side by side.
  const back = FIRST_ROW + row * ROW_GAP + (slot % 2) * (ROW_GAP / 2);
  const n = track.samples.length;
  const step = track.length / n;
  const s = track.samples[(n - Math.round(back / step)) % n]!;
  const h = Math.hypot(s.right.x, s.right.z);
  const x = s.pos.x + (s.right.x / h) * side * COLUMN;
  const z = s.pos.z + (s.right.z / h) * side * COLUMN;
  return { x, y: s.pos.y, z, heading: Math.atan2(s.forward.x, s.forward.z) };
}
