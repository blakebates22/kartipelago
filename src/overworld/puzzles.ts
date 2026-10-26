/**
 * The overworld's switches and puzzles (Blake, Oct 26: "have some switches or puzzles
 * that need to be solved also in the overworld, like banjo kazooie overworld has
 * switches and stuff").
 *
 * Two kinds so far, both opening a gate for good:
 *
 * - Timed (Dinosaur Valley's Three Stones): drive over one switch and the drums start;
 *   press the rest before they stop. Miss, and every switch pops back up.
 * - In order (the Snow Kingdom's Ice Bells): the switches must go in a set order, which
 *   the world gives away (the bells' lanterns: one, two, three). A wrong one and they
 *   all go quiet again.
 *
 * A switch goes down when you drive onto it (not while you sit on it). Pure: where you
 * are and the time are all it needs.
 */

export interface PuzzleSwitch {
  x: number;
  z: number;
  /** The clue beside it (bells): how many lanterns. */
  lanterns?: number;
}

export interface Puzzle {
  id: string;
  /** Its name on screen. */
  label: string;
  /** What the switches are: stones in the ground, or bells or gongs in a frame. */
  look: "stone" | "bell" | "gong";
  /** The switches (game coordinates), in their order when `ordered`. */
  switches: PuzzleSwitch[];
  /** How close counts as on a switch, metres. */
  radius: number;
  /** Seconds to press the rest once the first is down (0: no clock). */
  seconds: number;
  /** They must be pressed in the order listed. */
  ordered?: boolean;
  /** Said when the first goes down, and after a wrong one. */
  hint: string;
  /** The gate it opens: its middle, the way its face looks (out of what it shuts) and
   * its width. Its posts and walls are in the region's build; the gate is the game's. */
  gate: { x: number; z: number; heading: number; width: number };
  /** What's behind it. A key: the kingdom's hidden key (the overworld doc), which opens
   * its mini-game slot one day. */
  prize?: { kind: "key"; x: number; z: number };
}

export interface PuzzleState {
  pressed: boolean[];
  /** Seconds left on the clock (0 when it isn't going). */
  left: number;
  solved: boolean;
  /** The switch you're on (-1: none), so it only goes down as you arrive. */
  on: number;
}

export type PuzzleEvent =
  | { kind: "press"; index: number; count: number }
  | { kind: "solved" }
  /** Every switch back up: the clock ran out, or (`wrong`) one out of order. */
  | { kind: "reset"; wrong: boolean };

export const newPuzzleState = (p: Puzzle, solved = false): PuzzleState => ({
  pressed: p.switches.map(() => solved),
  left: 0,
  solved,
  on: -1,
});

/** One step: you're at (x, z), `dt` seconds on. What happened, in order. */
export function stepPuzzle(
  p: Puzzle,
  st: PuzzleState,
  x: number,
  z: number,
  dt: number,
): PuzzleEvent[] {
  if (st.solved) return [];
  const out: PuzzleEvent[] = [];
  if (p.seconds > 0 && st.pressed.some(Boolean)) {
    st.left -= dt;
    if (st.left <= 0) {
      st.pressed.fill(false);
      st.left = 0;
      out.push({ kind: "reset", wrong: false });
    }
  }
  const on = p.switches.findIndex((s) => Math.hypot(x - s.x, z - s.z) < p.radius);
  const arrived = on >= 0 && on !== st.on;
  st.on = on;
  if (!arrived || st.pressed[on]) return out;
  const count = st.pressed.filter(Boolean).length;
  if (p.ordered && on !== count) {
    st.pressed.fill(false);
    st.left = 0;
    out.push({ kind: "reset", wrong: true });
    return out;
  }
  if (count === 0 && p.seconds > 0) st.left = p.seconds;
  st.pressed[on] = true;
  out.push({ kind: "press", index: on, count: count + 1 });
  if (st.pressed.every(Boolean)) {
    st.solved = true;
    st.left = 0;
    out.push({ kind: "solved" });
  }
  return out;
}

/** The gate's collision (a box across the gateway, its length along `heading`). */
export function gateSolid(p: Pick<Puzzle, "gate">, groundY: number) {
  return {
    kind: "box" as const,
    look: "boundary" as const,
    x: p.gate.x,
    z: p.gate.z,
    heading: p.gate.heading + Math.PI / 2,
    halfLength: p.gate.width / 2 + 0.6,
    halfWidth: 0.8,
    height: groundY + 7,
  };
}

/** A bell's frame posts (they're solid): either side of it, across the way it faces. */
export function bellPosts(p: Puzzle) {
  if (p.look === "stone") return [];
  return p.switches.flatMap((s) => {
    const h = bellHeading(s);
    return [-1, 1].map((side) => ({
      x: s.x + Math.cos(h) * side * BELL_HALF_SPAN,
      z: s.z - Math.sin(h) * side * BELL_HALF_SPAN,
    }));
  });
}
export const BELL_HALF_SPAN = 5.5;
/** Which way a bell's frame faces: towards the middle of the region. */
export const bellHeading = (s: { x: number; z: number }) => Math.atan2(-s.x, -s.z);
