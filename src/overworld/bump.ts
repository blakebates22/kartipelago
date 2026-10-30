/**
 * Bumping into someone on foot (Blake, valley polish 20: "the guards should have hit boxes
 * and maybe move a little when we bump into them"; "it would be kind of cool if all npc
 * flinched or something if you crashed into them"). Each person is solid (a circle the
 * kart hits); when the kart runs into them they cower for a moment and are shoved a step
 * back from it, then ease back to where they stood.
 */
import type { PersonCue } from "../render/people/animate";
import type { SolidCircle } from "../world/solids";

/** How close (between the kart's middle and theirs, past their own radius) is a bump. */
const KART_R = 1.3;

export interface Bumpable {
  /** Where they stand (their post), and how far round them is solid. */
  x: number;
  z: number;
  radius: number;
  /** Their solid, kept on them as they're shoved. */
  solid: SolidCircle;
  /** Shoved this far off their post, easing back. */
  ox: number;
  oz: number;
  /** Seconds of cowering left. */
  flinch: number;
}

export function bumpable(x: number, z: number, radius: number, top: number): Bumpable {
  return {
    x,
    z,
    radius,
    solid: { kind: "circle", look: "creature", x, z, radius, height: top },
    ox: 0,
    oz: 0,
    flinch: 0,
  };
}

/** Once a frame: a bump from your kart (at `you`, `speed` m/s), the shove easing off.
 * `free(x, z)`: whether they can stand there (no wall). Returns where they are now and
 * their cue (cowering, or `cue` as it was). */
export function stepBump(
  b: Bumpable,
  you: { x: number; z: number; speed: number },
  dt: number,
  free: (x: number, z: number) => boolean = () => true,
  cue: PersonCue | number = 0,
): { x: number; z: number; cue: PersonCue | number } {
  const px = b.x + b.ox;
  const pz = b.z + b.oz;
  const dx = px - you.x;
  const dz = pz - you.z;
  const d = Math.hypot(dx, dz) || 1;
  if (d < b.radius + KART_R && Math.abs(you.speed) > 2 && b.flinch < 0.4) {
    b.flinch = 0.9;
    const push = Math.min(0.9, 0.12 * Math.abs(you.speed));
    const nx = b.ox + (dx / d) * push;
    const nz = b.oz + (dz / d) * push;
    if (free(b.x + nx, b.z + nz)) {
      b.ox = nx;
      b.oz = nz;
    }
  }
  b.flinch = Math.max(0, b.flinch - dt);
  if (b.flinch < 0.3) {
    // (Back to their post, slowly.)
    const k = Math.min(1, dt * 1.2);
    b.ox -= b.ox * k;
    b.oz -= b.oz * k;
  }
  b.solid.x = b.x + b.ox;
  b.solid.z = b.z + b.oz;
  return {
    x: b.solid.x,
    z: b.solid.z,
    cue: b.flinch > 0 ? { ...(typeof cue === "number" ? {} : cue), gesture: "cower" } : cue,
  };
}
