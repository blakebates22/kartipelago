/**
 * Where the overworld puts you out of a gateway (after its race) or a passage (coming in
 * from the next region): on its heading, `radius` + 6 m out, the first of a few
 * distances where a kart fits (Blake, Oct 27: out of Cascade Caverns' arch you came out
 * against the bridge's parapet; out of Dragon Canyon's in the ruin, into rubble).
 */
export const EXIT_OUT = [6, 8, 4, 10, 3, 12, 2];

export function exitSpot(
  mark: { x: number; z: number; radius: number; heading: number },
  /** Does a kart fit at (x, z) (no wall in it)? */
  fits: (x: number, z: number) => boolean,
): { x: number; z: number; heading: number } {
  const at = (d: number) => ({
    x: mark.x + Math.sin(mark.heading) * (mark.radius + d),
    z: mark.z + Math.cos(mark.heading) * (mark.radius + d),
    heading: mark.heading,
  });
  for (const d of EXIT_OUT) {
    const p = at(d);
    if (fits(p.x, p.z)) return p;
  }
  return at(EXIT_OUT[0]!);
}
