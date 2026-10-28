// Racing Adventure as a kingdom's own champion (Blake, Oct 27): their cousin takes their
// place, in the other paint: their challenge, their lines, their seat in your crew.
import { describe, expect, it } from "vitest";
import { KINGDOMS, sceneOf } from "../src/adventure/data";
import { kingdomField, sessionExtras } from "../src/adventure/run";
import { SCENES, beatsFor } from "../src/adventure/scenes";

describe("a champion's cousin", () => {
  for (const k of KINGDOMS) {
    const champ = k.champion.look;
    it(`${k.id}: races as ${champ}'s cousin, never ${champ} again`, () => {
      const field = kingdomField(k.id, champ, new Set());
      expect(field.filter((f) => f.id === champ && !f.alt)).toEqual([]);
      expect(field[0]).toEqual({ id: champ, alt: true });
      const duel = sessionExtras({ kind: "duel", kingdom: k.id }, champ, new Set());
      expect(duel.field?.looks?.[0]).toEqual({ id: champ, alt: true });
      expect(duel.field?.names?.[0]).toMatch(/Cousin/);
    });
    it(`${k.id}: the cousin speaks ${champ}'s lines and joins in their place`, () => {
      const prize = SCENES[sceneOf(k.id, "prize")]!;
      const beats = beatsFor(prize, champ);
      expect(beats.some((b) => b.who === champ)).toBe(false);
      expect(beats.some((b) => b.who === `${champ}_cousin`)).toBe(true);
      expect(beats.find((b) => b.crew === champ)!.text).toMatch(/COUSIN JOINS YOUR CREW/);
      expect(beats.some((b) => /SWITCH TO/.test(b.text))).toBe(false);
      // (Anyone else's file plays it as written.)
      expect(beatsFor(prize, "tiko")).toBe(prize.beats);
    });
  }
});
