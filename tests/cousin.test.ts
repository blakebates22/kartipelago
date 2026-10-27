// Racing Adventure as a kingdom's own champion (Blake, Oct 27): their cousin takes their
// part, in the other paint, and doesn't join your crew.
import { describe, expect, it } from "vitest";
import { KINGDOMS } from "../src/adventure/data";
import { kingdomField, sessionExtras } from "../src/adventure/run";
import { SCENES, beatsFor } from "../src/adventure/scenes";

describe("a champion's cousin", () => {
  for (const k of KINGDOMS.filter((k) => k.champion)) {
    const champ = k.champion!.look;
    it(`${k.id}: races as ${champ}'s cousin, never ${champ} again`, () => {
      const field = kingdomField(k.id, champ, new Set());
      expect(field.filter((f) => f.id === champ && !f.alt)).toEqual([]);
      expect(field[0]).toEqual({ id: champ, alt: true });
      const duel = sessionExtras({ kind: "duel", kingdom: k.id }, champ, new Set());
      expect(duel.field?.looks?.[0]).toEqual({ id: champ, alt: true });
      expect(duel.field?.names?.[0]).toMatch(/Cousin/);
    });
    it(`${k.id}: the cousin gives their respect and stays home`, () => {
      const beats = beatsFor(SCENES[k.scenes.catastrophe]!, champ);
      expect(beats.some((b) => /JOINS YOUR CREW/.test(b.text))).toBe(false);
      expect(beats.some((b) => b.who === champ)).toBe(false);
      expect(beats[0]!.text).toMatch(/RESPECT/);
      // (Anyone else's file plays it as written.)
      expect(beatsFor(SCENES[k.scenes.catastrophe]!, "tiko")).toBe(
        SCENES[k.scenes.catastrophe]!.beats,
      );
    });
  }
});
