/**
 * Trophy Race: all of a world's tracks in a row against the same seven rivals, points
 * for every finishing place, most points at the end wins the trophy.
 *
 * The rules (Blake's): eight racers, points 10 8 6 5 4 3 2 1 for 1st to 8th, every race
 * counts (no retries). Ties go to whoever has the most wins, then most 2nds, and so on;
 * still tied, the better place in the last race.
 *
 * Plain data and functions (no rendering): the screens keep a cup on `game.trophy`.
 */

/** Points for 1st, 2nd, ... 8th. */
export const TROPHY_POINTS = [10, 8, 6, 5, 4, 3, 2, 1] as const;

export interface CupRacer {
  /** Their slot in every race of the cup (0 is you; rivals keep theirs). */
  slot: number;
  name: string;
  /** Which racer they look like (for portraits). */
  look: string;
  points: number;
  /** Finishing place in each race so far (1-based). */
  places: number[];
}

export interface TrophyCup {
  worldId: string;
  worldName: string;
  /** Track ids, in the order they're raced. */
  tracks: string[];
  /** Races finished so far. */
  raced: number;
  /** Everyone in the cup, by slot (filled in by the first race's result). */
  racers: CupRacer[];
}

export const pointsFor = (place: number) => TROPHY_POINTS[place - 1] ?? 0;

export function startCup(worldId: string, worldName: string, tracks: string[]): TrophyCup {
  return { worldId, worldName, tracks: [...tracks], raced: 0, racers: [] };
}

/** The track to race next, or undefined once the cup is over. */
export const nextTrack = (cup: TrophyCup) => cup.tracks[cup.raced];
export const cupOver = (cup: TrophyCup) => cup.raced >= cup.tracks.length;

/**
 * Score a finished race. `order` is everyone from 1st to last (their slot, name and look).
 * Returns the points each slot won this race.
 */
export function scoreRace(
  cup: TrophyCup,
  order: { slot: number; name: string; look: string }[],
): Map<number, number> {
  const won = new Map<number, number>();
  order.forEach((o, i) => {
    let r = cup.racers.find((c) => c.slot === o.slot);
    if (!r) {
      r = { slot: o.slot, name: o.name, look: o.look, points: 0, places: [] };
      cup.racers.push(r);
    }
    const place = i + 1;
    const pts = pointsFor(place);
    r.points += pts;
    r.places.push(place);
    won.set(o.slot, pts);
  });
  cup.raced++;
  return won;
}

/** Everyone from first to last in the cup so far. */
export function cupStandings(cup: TrophyCup): CupRacer[] {
  const count = (r: CupRacer, place: number) => r.places.filter((p) => p === place).length;
  return [...cup.racers].sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points;
    for (let place = 1; place <= TROPHY_POINTS.length; place++) {
      const d = count(b, place) - count(a, place);
      if (d) return d;
    }
    return (a.places.at(-1) ?? 99) - (b.places.at(-1) ?? 99);
  });
}

/** Your place in the cup (1-based), or undefined before the first race. */
export function yourCupPlace(cup: TrophyCup): number | undefined {
  const i = cupStandings(cup).findIndex((r) => r.slot === 0);
  return i < 0 ? undefined : i + 1;
}
