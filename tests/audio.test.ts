import { describe, expect, it } from "vitest";
import { normalise, renderSongData } from "../src/audio/dsp";
import { chart, midi, seq, seqLength, voicing } from "../src/audio/score";
import * as S from "../src/audio/songs";
import { RACER_IDS } from "../src/render/racers/designs";

describe("score notation", () => {
  it("reads notes, rests, chords and accents", () => {
    expect(midi("C4")).toBe(60);
    expect(midi("F#5")).toBe(78);
    expect(midi("Bb3")).toBe(58);
    const n = seq("C4:1 r:.5 [E4,G4]:.5 A4:2!");
    expect(n.map((x) => [x.t, x.m])).toEqual([
      [0, 60],
      [1.5, 64],
      [1.5, 67],
      [2, 69],
    ]);
    expect(n[3]!.v).toBeGreaterThan(n[0]!.v);
    expect(() => seq("H4:1")).toThrow();
    expect(chart("G/B:2 Am7:2")[0]).toMatchObject({ root: 7, bass: 11, d: 2 });
  });
});

const melodies: [string, string, number][] = [
  ["title A", S.TITLE_MELODY_A, 32],
  ["title A2", S.TITLE_MELODY_A2, 32],
  ["title B", S.TITLE_MELODY_B, 32],
  ["select", S.SELECT_MELODY, 64],
  ["map", S.MAP_MELODY, 64],
  ["race", S.RACE_MELODY, 64],
  ["fanfare", S.FANFARE_MELODY, 12],
  ["riverbend", S.RIVERBEND_MELODY, 64],
  ["riverbend_classic", S.RIVERBEND_CLASSIC_MELODY, 64],
  ["cascade", S.CASCADE_MELODY, 64],
  ["bonebog", S.BONEBOG_MELODY, 64],
  ["ember", S.EMBER_MELODY, 64],
];
const charts: [string, string, number, string][] = [
  [
    "title",
    S.TITLE_CHORDS,
    96,
    S.TITLE_MELODY_A + " " + S.TITLE_MELODY_A2 + " " + S.TITLE_MELODY_B,
  ],
  ["select", S.SELECT_CHORDS, 64, S.SELECT_MELODY],
  ["map", S.MAP_CHORDS, 64, S.MAP_MELODY],
  ["race", S.RACE_CHORDS, 64, S.RACE_MELODY],
  ["riverbend", S.RIVERBEND_CHORDS, 64, S.RIVERBEND_MELODY],
  ["riverbend_classic", S.RIVERBEND_CLASSIC_CHORDS, 64, S.RIVERBEND_CLASSIC_MELODY],
  ["cascade", S.CASCADE_CHORDS, 64, S.CASCADE_MELODY],
  ["bonebog", S.BONEBOG_CHORDS, 64, S.BONEBOG_MELODY],
  ["ember", S.EMBER_CHORDS, 64, S.EMBER_MELODY],
];

describe("the soundtrack", () => {
  it("has whole bars: every melody and chord chart is the length of its piece", () => {
    for (const [name, m, beats] of melodies) expect(seqLength(m), name).toBeCloseTo(beats, 6);
    for (const [name, c, beats] of charts) {
      const ch = chart(c);
      expect(ch.at(-1)!.t + ch.at(-1)!.d, name).toBe(beats);
      expect(S.SONGS[name]!.beats).toBe(beats);
    }
  });

  it("puts melody notes on the beat into the chord most of the time", () => {
    for (const [name, c, , m] of charts) {
      const ch = chart(c);
      const notes = seq(m).filter((n) => Number.isInteger(n.t));
      let inChord = 0;
      for (const n of notes) {
        const k = ch.find((x) => n.t >= x.t && n.t < x.t + x.d)!;
        const pcs = voicing(k, 60).map((p) => p % 12);
        if (pcs.includes(n.m % 12)) inChord++;
      }
      expect(inChord / notes.length, name).toBeGreaterThan(0.75);
    }
  });

  it("gives Pick Your Racer a layer for every racer", () => {
    expect([...S.RACER_STEMS].sort()).toEqual([...RACER_IDS].sort());
    for (const r of RACER_IDS)
      expect(
        S.SONGS.select!.parts.some((p) => p.stem === r),
        r,
      ).toBe(true);
  });

  it("lists every composed piece in the music player, and marks planned ones unavailable", () => {
    for (const id of Object.keys(S.SONGS))
      expect(S.CATALOG.find((c) => c.id === id)?.available).toBe(true);
    expect(S.CATALOG.some((c) => !c.available)).toBe(true);
  });

  it("renders every piece cleanly: right length, in sync, no clipping, not silent", () => {
    const rate = 16000; // half rate keeps the test quick
    for (const song of Object.values(S.SONGS)) {
      const stems = renderSongData(song, rate);
      const len = Math.round(((song.beats * 60) / song.bpm) * rate);
      for (const [name, d] of Object.entries(stems)) {
        if (song.loop) expect(d.length, `${song.id}/${name}`).toBe(len);
        let peak = 0;
        let sum = 0;
        for (const x of d) {
          expect(Number.isFinite(x)).toBe(true);
          peak = Math.max(peak, Math.abs(x));
          sum += x * x;
        }
        expect(peak, `${song.id}/${name}`).toBeLessThanOrEqual(0.86);
        expect(Math.sqrt(sum / d.length), `${song.id}/${name}`).toBeGreaterThan(0.01);
      }
    }
  }, 60000);

  it("normalises layers together, keeping their balance", () => {
    const stems = { base: new Float32Array([0.5, -1]), a: new Float32Array([0.5, 0]) };
    normalise(stems, 0.5);
    expect(stems.base[1]).toBeCloseTo(-0.5);
    expect(stems.a[0]).toBeCloseTo(0.25);
  });
});
