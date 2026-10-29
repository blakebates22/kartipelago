import { describe, expect, it } from "vitest";
import { INTRO, renderSongData } from "../src/audio/dsp";
import { CUE_IDS } from "../src/audio/cues";
import { DRUMS } from "../src/audio/instruments";
import type { Note, Song } from "../src/audio/score";
import { SONGS } from "../src/audio/songs";

const cues = CUE_IDS.map((id) => SONGS[id]!);
const seconds = (s: Song) => (s.beats * 60) / s.bpm;

/** The melodic lines of a song: its single-voice, pitched parts, notes in time order. */
function lines(s: Song): Note[][] {
  return s.parts
    .filter((p) => !DRUMS.has(p.inst) && p.inst !== "riser")
    .map((p) => [...p.notes].sort((a, b) => a.t - b.t))
    .filter((n) => new Set(n.map((x) => x.t)).size === n.length);
}

/** Does any line of the song contain consecutive intervals matching `test`? */
function hasFigure(s: Song, len: number, test: (iv: number[]) => boolean) {
  for (const l of lines(s))
    for (let i = 0; i + len < l.length; i++) {
      const iv: number[] = [];
      for (let k = 0; k < len; k++) iv.push(l[i + k + 1]!.m - l[i + k]!.m);
      if (test(iv)) return true;
    }
  return false;
}

const same = (a: number[], b: number[]) => a.every((x, i) => x === b[i]);
/** DRAGON: up a half step, back, up a tritone (C Db C F#). */
const dragon = (iv: number[]) => same(iv, [1, -1, 6]);
/** PACT: up a fourth, a step, a step (or half step, in minor), back down. */
const pact = (iv: number[]) => same(iv, [5, 2, 2, -2, -2]) || same(iv, [5, 2, 1, -1, -2]);
/** LUMEN: a rising sixth, a step up, a fall of a third or so (its fourth note). */
const lumen = (iv: number[]) =>
  iv[0]! >= 8 && iv[0]! <= 9 && iv[1]! >= 1 && iv[1]! <= 3 && iv[2]! <= -3 && iv[2]! >= -5;

describe("the cutscene score", () => {
  it("has every cue the scenes name, ready to loop, 20-60 s long, with an intro", () => {
    expect(CUE_IDS).toHaveLength(24);
    for (const s of cues) {
      expect(s, s.id).toBeDefined();
      expect(s.role.startsWith("Cutscenes"), s.id).toBe(true);
      expect(s.loop, s.id).toBe(s.id !== "shatter");
      expect(seconds(s), s.id).toBeGreaterThanOrEqual(20);
      expect(seconds(s), s.id).toBeLessThanOrEqual(60);
      // A short lead-in (a pickup, a roll, a glissando), so a switch lands on a phrase.
      expect(s.intro, s.id).toBeGreaterThan(0);
      expect((s.intro! * 60) / s.bpm, s.id).toBeLessThanOrEqual(7);
      for (const p of s.parts)
        for (const n of p.notes) {
          expect(n.t, `${s.id}/${p.inst}`).toBeGreaterThanOrEqual(-s.intro! - 1e-9);
          expect(n.t, `${s.id}/${p.inst}`).toBeLessThan(s.beats);
          if (n.t < 0) expect(p.stem, s.id).toBe("base");
          expect(Number.isFinite(n.m) && n.d > 0 && n.v > 0 && n.v <= 1, s.id).toBe(true);
        }
      // Something is playing on every bar of the loop (no dead air), but in the
      // shattering's ringing silence.
      const bar = 4;
      for (let t = 0; t < Math.min(s.beats, s.id === "shatter" ? 16 : s.beats); t += bar)
        expect(
          s.parts.some((p) => p.notes.some((n) => n.t < t + bar && n.t + n.d > t)),
          `${s.id} @${t}`,
        ).toBe(true);
    }
    // "The Dragon's Shadow" stays the dragons' arrival.
    expect(SONGS.dread!.title).toBe("The Dragon's Shadow");
  });

  it("weaves the leitmotifs through the cues", () => {
    const where = (len: number, test: (iv: number[]) => boolean) =>
      cues.filter((s) => hasFigure(s, len, test)).map((s) => s.id);
    const d = where(3, dragon);
    for (const id of [
      "conquered",
      "rimefang",
      "scorchwind",
      "tidewyrm",
      "king",
      "court",
      "rage",
      "yield",
    ])
      expect(d, `DRAGON in ${id}`).toContain(id);
    const p = where(5, pact);
    for (const id of [
      "festival",
      "conquered",
      "false_victory",
      "new_stone",
      "yield",
      "confession",
      "finale",
      "home",
    ])
      expect(p, `PACT in ${id}`).toContain(id);
    const l = where(3, lumen);
    for (const id of ["lumen", "shatter", "sorrow", "hope", "new_stone", "finale", "home"])
      expect(l, `LUMEN in ${id}`).toContain(id);
    // And the dragon's motif comes from "The Dragon's Shadow" itself.
    expect(hasFigure(SONGS.dread!, 1, (iv) => iv[0] === 1)).toBe(true);
  });

  it("renders every cue cleanly: in sync, intro and all, no clipping, not silent", () => {
    const rate = 12000; // a low rate keeps the test quick
    for (const s of cues) {
      const stems = renderSongData(s, rate);
      const len = Math.round(seconds(s) * rate);
      if (s.loop) expect(stems.base!.length, s.id).toBe(len);
      expect(stems[INTRO], s.id).toBeDefined();
      for (const [name, d] of Object.entries(stems)) {
        let peak = 0;
        let sum = 0;
        for (const x of d) {
          expect(Number.isFinite(x), `${s.id}/${name}`).toBe(true);
          peak = Math.max(peak, Math.abs(x));
          sum += x * x;
        }
        expect(peak, `${s.id}/${name}`).toBeLessThanOrEqual((s.peak ?? 0.85) + 1e-6);
        // (An intro is short and its buffer carries 2.5 s of tail, so it measures quieter.)
        const floor = name === INTRO ? 0.003 : 0.005;
        expect(Math.sqrt(sum / d.length), `${s.id}/${name}`).toBeGreaterThan(floor);
      }
    }
  }, 600000);

  it("keeps the quiet cues quiet", () => {
    for (const id of ["suspense", "sorrow", "confession", "lumen"])
      expect(SONGS[id]!.peak ?? 0.85, id).toBeLessThan(0.75);
    for (const id of ["rage", "false_victory", "finale", "conquered"])
      expect(SONGS[id]!.peak ?? 0.85, id).toBe(0.85);
  });
});
