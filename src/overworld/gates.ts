/**
 * A walled yard's gate as collision (a box across the way in, its length across the
 * gate's heading): the smugglers' caves' guards, the secrets' obstacles, the passages'
 * blockers. (Once the overworld puzzles' gates: Blake cut the puzzles, Oct 27.)
 */
export function gateSolid(
  p: { gate: { x: number; z: number; heading: number; width: number } },
  groundY: number,
) {
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
