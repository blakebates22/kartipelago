/**
 * The people of the story, ready to put in a scene: Elder Mossback, Lumen in his robe,
 * the smugglers' guards and the townsfolk (render/villager.ts makes those). Each is a
 * PersonView (view.ts): placed and animated with a cue (talk, gesture, look).
 */
import type * as THREE from "three";
import { createPersonView, type PersonView } from "./view";
import { buildMossback } from "./mossback";
import { buildGuard } from "./guard";
import { buildLumen, type LumenFace } from "./lumen";
import type { Folk } from "../villager";

export { GESTURES, type Gesture, type PersonCue } from "./animate";
export type { PersonView } from "./view";

/** Elder Mossback (the Founders' Horn at his hip, his staff in his hand). */
export function createElderView(parent: THREE.Object3D, seed = 5): PersonView {
  return createPersonView(parent, "elder", buildMossback, { scale: 1.12, shadow: 0.6, seed });
}

/** A smugglers' guard, dressed for his kingdom; the seed picks his look. */
export function createGuardView(parent: THREE.Object3D, folk: Folk, seed: number): PersonView {
  return createPersonView(parent, `guard|${folk}|${seed}`, () => buildGuard(folk, seed), {
    scale: 1.1,
    shadow: 0.65,
    seed,
  });
}

/** Lumen in his robe (the hatchling under it): his face shows in the hood, a young
 * dinosaur's as far as anyone knows, the little fins at his cheeks the only hint (Blake
 * picked the frill face, Oct 28). */
export function createLumenView(
  parent: THREE.Object3D,
  seed = 3,
  face: LumenFace = "frill",
): PersonView {
  return createPersonView(parent, `lumen|${face}`, () => buildLumen(face), {
    scale: 1.08,
    shadow: 0.5,
    seed,
  });
}
