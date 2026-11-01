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

/**
 * In front of a mark, facing it (the lair once the map is whole, the way on once the
 * dragon's beaten: Blake, Oct 27, put there rather than driving across the kingdom).
 */
export function frontSpot(
  mark: { x: number; z: number; radius: number; heading: number },
  fits: (x: number, z: number) => boolean,
): { x: number; z: number; heading: number } {
  const at = (d: number) => ({
    x: mark.x + Math.sin(mark.heading) * (mark.radius + d),
    z: mark.z + Math.cos(mark.heading) * (mark.radius + d),
    heading: mark.heading + Math.PI,
  });
  for (const d of [8, 10, 6, 12, 14]) {
    const p = at(d);
    if (fits(p.x, p.z)) return p;
  }
  // (Close in: the chase camera sits behind you, and behind you can be a slope.)
  return at(8);
}

/** How far down the road a gateway's way out faces you (metres). */
const AIM_AHEAD = 20;

/**
 * Out of a gateway after its race (Blake, Oct 27: always facing the way the road goes,
 * never across it at a wall): onto the main road where the gateway's way out meets it,
 * facing along the lap. `near`: where exitSpot would put you. Undefined when the road's
 * not near (then exitSpot's spot it is).
 */
export function roadSpot(
  samples: readonly {
    pos: { x: number; y: number; z: number };
    forward: { x: number; z: number };
  }[],
  near: { x: number; z: number },
  fits: (x: number, z: number) => boolean,
): { x: number; z: number; heading: number } | undefined {
  let bi = -1;
  let bd = Infinity;
  samples.forEach((s, i) => {
    const d = (s.pos.x - near.x) ** 2 + (s.pos.z - near.z) ** 2;
    if (d < bd) {
      bd = d;
      bi = i;
    }
  });
  if (bi < 0 || bd > 45 * 45) return undefined;
  const best = samples[bi]!;
  // Facing a point on the road AHEAD, not just along it here: where it bends just past
  // the gateway (Frostveil's walled street) the tangent points you into the wall on the
  // bend's outside.
  let ahead = best;
  for (let k = 1; k < samples.length; k++) {
    ahead = samples[(bi + k) % samples.length]!;
    if (Math.hypot(ahead.pos.x - best.pos.x, ahead.pos.z - best.pos.z) >= AIM_AHEAD) break;
  }
  const heading =
    ahead === best
      ? Math.atan2(best.forward.x, best.forward.z)
      : Math.atan2(ahead.pos.x - best.pos.x, ahead.pos.z - best.pos.z);
  const p = { x: best.pos.x, z: best.pos.z, heading };
  return fits(p.x, p.z) ? p : undefined;
}
