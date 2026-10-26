/**
 * The overworld's switches and puzzles (Blake, Oct 26: "have some switches or puzzles
 * that need to be solved also in the overworld, like banjo kazooie overworld has
 * switches and stuff").
 *
 * The first one is a timed switch puzzle: drive over one of the switch stones and the
 * drums start; press the rest before they stop and the gate it works opens for good.
 * Miss and every stone pops back up. Pure: where you are and the time are all it needs.
 */

export interface Puzzle {
  id: string;
  /** Its name on screen. */
  label: string;
  /** The switch stones (game coordinates): drive over each one. */
  switches: { x: number; z: number }[];
  /** How close counts as on a stone, metres. */
  radius: number;
  /** Seconds to press the rest once the first is down. */
  seconds: number;
  /** The gate it opens: its middle, the way its face looks (out of what it shuts) and
   * its width. Its posts and walls are in the region's build; the gate is the game's. */
  gate: { x: number; z: number; heading: number; width: number };
  /** What's behind it. A key: the kingdom's hidden key (the overworld doc), which opens
   * its mini-game slot one day. */
  prize?: { kind: "key"; x: number; z: number };
}

export interface PuzzleState {
  pressed: boolean[];
  /** Seconds left on the drums (0 when they aren't going). */
  left: number;
  solved: boolean;
}

export type PuzzleEvent =
  { kind: "press"; index: number; count: number } | { kind: "solved" } | { kind: "reset" };

export const newPuzzleState = (p: Puzzle, solved = false): PuzzleState => ({
  pressed: p.switches.map(() => solved),
  left: 0,
  solved,
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
  const going = st.pressed.some(Boolean);
  if (going) {
    st.left -= dt;
    if (st.left <= 0) {
      st.pressed.fill(false);
      st.left = 0;
      out.push({ kind: "reset" });
    }
  }
  p.switches.forEach((s, i) => {
    if (st.pressed[i] || Math.hypot(x - s.x, z - s.z) >= p.radius) return;
    if (!st.pressed.some(Boolean)) st.left = p.seconds;
    st.pressed[i] = true;
    out.push({ kind: "press", index: i, count: st.pressed.filter(Boolean).length });
  });
  if (st.pressed.every(Boolean)) {
    st.solved = true;
    st.left = 0;
    out.push({ kind: "solved" });
  }
  return out;
}

/** The gate's collision (a box across the gateway, its length along `heading`). */
export function gateSolid(p: Puzzle, groundY: number) {
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
