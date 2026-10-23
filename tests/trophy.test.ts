import { describe, expect, it } from "vitest";
import {
  TROPHY_POINTS,
  cupOver,
  cupStandings,
  nextTrack,
  pointsFor,
  scoreRace,
  startCup,
  yourCupPlace,
} from "../src/game/trophy";

const field = (slots: number[]) => slots.map((slot) => ({ slot, name: `R${slot}`, look: "tiko" }));

describe("trophy race", () => {
  it("scores 10 8 6 5 4 3 2 1 for 1st to 8th", () => {
    expect(TROPHY_POINTS).toEqual([10, 8, 6, 5, 4, 3, 2, 1]);
    expect(pointsFor(1)).toBe(10);
    expect(pointsFor(8)).toBe(1);
    expect(pointsFor(9)).toBe(0);
  });

  it("runs every track of the world in order, then ends", () => {
    const cup = startCup("prehistoric", "Prehistoric World", ["a", "b", "c", "d"]);
    expect(nextTrack(cup)).toBe("a");
    for (const t of ["a", "b", "c", "d"]) {
      expect(nextTrack(cup)).toBe(t);
      scoreRace(cup, field([0, 1, 2, 3, 4, 5, 6, 7]));
    }
    expect(cupOver(cup)).toBe(true);
    expect(nextTrack(cup)).toBeUndefined();
  });

  it("adds up points across races and ranks the cup", () => {
    const cup = startCup("w", "W", ["a", "b"]);
    const won = scoreRace(cup, field([3, 0, 1, 2, 4, 5, 6, 7]));
    expect(won.get(3)).toBe(10);
    expect(won.get(0)).toBe(8);
    scoreRace(cup, field([0, 1, 3, 2, 4, 5, 6, 7]));
    // You: 8 + 10 = 18. Slot 3: 10 + 6 = 16. Slot 1: 6 + 8 = 14.
    const s = cupStandings(cup);
    expect(s.map((r) => [r.slot, r.points]).slice(0, 3)).toEqual([
      [0, 18],
      [3, 16],
      [1, 14],
    ]);
    expect(yourCupPlace(cup)).toBe(1);
    expect(s[0]!.places).toEqual([2, 1]);
  });

  it("breaks ties on wins, then the last race", () => {
    const cup = startCup("w", "W", ["a", "b"]);
    // Slot 1 wins then comes 3rd (10 + 6 = 16); you come 2nd twice (8 + 8 = 16).
    scoreRace(cup, field([1, 0, 2, 3, 4, 5, 6, 7]));
    scoreRace(cup, field([2, 0, 1, 3, 4, 5, 6, 7]));
    const s = cupStandings(cup);
    const you = s.findIndex((r) => r.slot === 0);
    const one = s.findIndex((r) => r.slot === 1);
    expect(s[you]!.points).toBe(s[one]!.points);
    // Slot 1 has a win; you don't.
    expect(one).toBeLessThan(you);
  });
});
