/**
 * What a racer file provides: colours (a main look and an alternate, used when the same
 * racer appears twice in a race), a kart body kit on the shared chassis, and a rider on
 * the shared rig. See docs/racer-pipeline.md.
 */
import type { BodyKit } from "../kit/chassis";
import type { RiderRig } from "../kit/rig";

export type Palette = Record<string, string>;

export interface RacerBuild<P extends Palette = Palette> {
  palettes: { main: P; alt: P };
  /** The kart's body kit (the chassis itself is shared). */
  kart(p: P): BodyKit;
  /** The rider (detail 0 near; the far version is its `low` mesh). */
  rider(p: P): RiderRig;
}
