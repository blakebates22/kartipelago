/**
 * Where each story dragon's head is at rest, [up, forward] of its feet in metres at
 * scale 1 (measured from the designs: dragons.html's `preview.measure()`). The staging's
 * close-ups frame it (adventure/staged.ts). Plain data, so the staging needs no models.
 */
import type { DragonLook } from "../dragon";

export const DRAGON_HEAD: Record<DragonLook, [number, number]> = {
  ember: [16, 18.4],
  obsidian: [16, 18.4],
  frost: [28.7, 16.1],
  sand: [24.1, 16.5],
  sea: [19.8, 16.6],
  king: [28.3, 19.8],
  lumen: [16.7, 13.5],
  lumen_grown: [26, 17.2],
};
