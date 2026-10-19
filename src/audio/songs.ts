/**
 * The soundtrack: original compositions written for Kartipelago (MIT, like the code).
 *
 * Five pieces for now, all bright, melodic and toy-like, played by the synthesized
 * band in instruments.ts:
 *
 *   title       "Kartipelago!"      title and main menus: welcoming, a little heroic
 *   select      "Pick Your Racer"   one groove, four synchronized racer layers
 *   map         "Course Map"        mode and track select: relaxed, exploring
 *   race        "Lakeside Dash"     racing: quick and bouncy
 *   fanfare     "Finish Line!"      the results jingle (doesn't loop)
 *
 * And a theme per Prehistoric World course:
 *
 *   riverbend   "Riverbend Palms"   F major, 138: a beach party. Steel pan lead, strummed
 *                                   marimba off-beats, brass hits, a whistling flute,
 *                                   a bouncing bass, four-on-the-floor kick, busy congas
 *                                   (bongos), shaker, tambourine and a cowbell-ish clave
 *   riverbend_classic  "Riverbend Palms (Classic)"  C major, 132: the gentler v1 theme
 *                                   (steel pan, marimba, flute, bongos)
 *   cascade     "Cascade Caverns"   D minor, 142: flute over pizzicato, wood, bells
 *   bonebog     "Bonebog Pyramid"   E minor, 116: low marimba groove, clarinet, toms,
 *                                   chimes, with friendly surprise chords (A, Ab, F)
 *   ember       "Ember Peak"        A minor, 158: driving drums, low brass, fast
 *                                   marimba, strings, square-wave accents
 *
 * "Pick Your Racer" is one arrangement split into stems that always play in sync: a
 * base groove, plus a layer per racer playing the same tune in their own instruments
 * (Moss: marimba and woodblocks; Bramble: pizzicato, walking bass and bassoon; Poppy:
 * flute, celesta and light pizzicato; Otto: clarinet, soft horns and lazy marimba). The
 * game fades between racer layers as you browse, without restarting the piece.
 */
import type { InstrumentId } from "./instruments";
import {
  arpeggio,
  bassLine,
  chart,
  drums,
  dyn,
  pads,
  seq,
  shift,
  stabs,
  voicing,
  type Note,
  type Part,
  type Song,
} from "./score";

const part = (inst: InstrumentId, stem: string, gain: number, notes: Note[]): Part => ({
  inst,
  stem,
  gain,
  notes,
});

const drumParts = (stem: string, gain: number, list: ReturnType<typeof drums>): Part[] =>
  list.map((d) => part(d.inst, stem, gain, d.notes));

const KIT: Record<string, InstrumentId> = {
  k: "kick",
  s: "snare",
  h: "shaker",
  i: "hat",
  w: "woodblock",
  b: "bongo",
  t: "tamb",
  c: "crash",
  o: "tom",
};

/** Bars of melody, joined (each bar is its own string so the bar lines stay visible). */
const bars = (...b: string[]) => b.join(" ");

// ---------------------------------------------------------------- "Kartipelago!"

export const TITLE_MELODY_A = bars(
  "C5:.5 F5:.5 A5:1 G5:.5 F5:.5 C5:1",
  "E5:.5 F5:.5 G5:1 A5:1 r:1",
  "D5:.5 F5:.5 Bb5:1 A5:.5 G5:.5 F5:1",
  "G5:1.5 F5:.5 E5:1 C5:1",
  "C5:.5 F5:.5 A5:1 G5:.5 F5:.5 C6:1",
  "A5:1.5 G5:.5 F5:1 D5:1",
  "Bb5:.5 A5:.5 G5:.5 F5:.5 E5:.5 F5:.5 G5:1",
  "C6:2 r:1 C5:.5 C5:.5",
);
export const TITLE_MELODY_A2 = bars(
  "F5:1 A5:1 G5:.5 F5:.5 C5:1",
  "E5:.5 F5:.5 G5:1 A5:1 C6:1",
  "D6:1.5 C6:.5 Bb5:1 A5:1",
  "G5:1 A5:.5 G5:.5 E5:2",
  "F5:.5 G5:.5 A5:1 C6:1 A5:1",
  "F#5:1 A5:.5 F#5:.5 D5:1 C6:1",
  "Bb5:1 A5:.5 G5:.5 E5:1 G5:1",
  "F5:3! r:1",
);
export const TITLE_MELODY_B = bars(
  "A5:1 D6:1 C6:.5 A5:.5 F5:1",
  "G5:1 F5:.5 D5:.5 F5:2",
  "C6:1 A5:.5 C6:.5 F6:1 E6:.5 D6:.5",
  "C6:2 G5:2",
  "A5:1 D6:1 C6:.5 A5:.5 F5:1",
  "G5:.5 A5:.5 Bb5:1 D6:1 C6:1",
  "Bb5:1 A5:1 G5:1 F5:1",
  "E5:.5 F5:.5 G5:.5 A5:.5 Bb5:.5 A5:.5 G5:.5 E5:.5",
);
export const TITLE_CHORDS =
  "F:4 Am:4 Bb:4 C:4 F:4 Dm:4 Gm7:2 C7:2 C7:4 " +
  "F:4 Am:4 Bb:4 C:4 F/C:4 D7:4 Gm:2 C7:2 F:4 " +
  "Dm:4 Bb:4 F:4 C:4 Dm:4 Bb:4 Gm:4 C7:4";

function title(): Song {
  const ch = chart(TITLE_CHORDS);
  const a = seq(TITLE_MELODY_A, 0, 0.82);
  const a2 = seq(TITLE_MELODY_A2, 32, 0.85);
  const b = seq(TITLE_MELODY_B, 64, 0.78);
  const beats = 96;
  const bass: [number, number, string][] = [
    [0, 1, "R"],
    [1, 0.5, "5"],
    [1.5, 0.5, "8"],
    [2, 1, "5"],
    [3, 0.5, "R"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "title",
    title: "Kartipelago!",
    role: "Title & menus",
    bpm: 132,
    beats,
    loop: true,
    stems: [],
    parts: [
      part("brass", "base", 1, [...a, ...a2]),
      part("xylophone", "base", 0.55, shift(a2, 0, 12)),
      part("flute", "base", 1, b),
      part("marimba", "base", 0.8, shift(b, 0, -12)),
      part(
        "horn",
        "base",
        0.55,
        pads(
          ch.filter((c) => c.t >= 64),
          53,
          2,
          0.55,
        ),
      ),
      part(
        "brass",
        "base",
        0.5,
        stabs(
          ch.filter((c) => c.t >= 32 && c.t < 64),
          [0, 2.5],
          60,
          0.35,
          0.6,
        ),
      ),
      part(
        "marimba",
        "base",
        0.7,
        dyn(arpeggio(ch, 0.5, [0, 2, 1, 2, 3, 2, 1, 2], 60, 0.5, 0.55), 1),
      ),
      part("bass", "base", 1, bassLine(ch, bass, 38, 0.85)),
      part("pad", "base", 0.6, pads(ch, 57, 4, 0.5)),
      ...drumParts("base", 0.9, drums("K...k.k.", KIT, 0.5, 24)),
      ...drumParts("base", 0.8, drums("..S...S.", KIT, 0.5, 24)),
      ...drumParts("base", 0.7, drums("hhHhhhHh", KIT, 0.5, 24)),
      ...drumParts("base", 0.6, drums("...w..w.", KIT, 0.5, 24)),
      ...drumParts("base", 0.8, drums("C", KIT, 32, 3)),
    ],
  };
}

// ---------------------------------------------------------------- "Pick Your Racer"

export const SELECT_MELODY = bars(
  "B4:.5 D5:.5 G5:.75 F#5:.25 E5:.5 D5:.5 B4:1",
  "E5:.5 G5:.5 B5:1 A5:.5 G5:.5 E5:1",
  "C5:.5 E5:.5 G5:.75 A5:.25 G5:.5 E5:.5 C5:1",
  "D5:.5 F#5:.5 A5:1 r:.5 F#5:.5 A5:1",
  "B4:.5 D5:.5 G5:.75 F#5:.25 E5:.5 D5:.5 G5:1",
  "B5:1.5 A5:.5 G5:1 E5:1",
  "A5:.5 G5:.5 E5:.5 C5:.5 D5:.5 F#5:.5 A5:.5 C6:.5",
  "B5:2 G5:1 r:1",
  "E5:1 G5:.5 E5:.5 C6:1 G5:1",
  "F#5:1 A5:.5 F#5:.5 D6:1 A5:1",
  "D6:.5 B5:.5 F#5:1 B5:1 A5:1",
  "G5:1.5 F#5:.5 E5:2",
  "E5:.5 F#5:.5 G5:.5 A5:.5 B5:1 G5:1",
  "A5:.5 B5:.5 C6:.5 D6:.5 A5:2",
  "B5:1 G5:1 C6:1 E6:1",
  "D6:1 C6:.5 A5:.5 F#5:1 D5:1",
);
export const SELECT_CHORDS =
  "G:4 Em:4 C:4 D:4 G:4 Em:4 Am7:2 D7:2 G:4 " + "C:4 D:4 Bm:4 Em:4 C:4 D:4 G/B:2 C:2 D7:4";

/** The racer layers of "Pick Your Racer", by racer id. */
export const RACER_STEMS = ["moss", "bramble", "poppy", "otto"] as const;

function select(): Song {
  const ch = chart(SELECT_CHORDS);
  const mel = seq(SELECT_MELODY, 0, 0.8);
  const beats = 64;
  const T = 16; // bars
  // The thirds of each chord, held low: Bramble's bassoon line.
  const thirds: Note[] = ch.map((c) => ({ t: c.t, d: c.d, m: voicing(c, 50)[1]!, v: 0.6 }));
  return {
    id: "select",
    title: "Pick Your Racer",
    role: "Racer select",
    bpm: 112,
    beats,
    loop: true,
    stems: [...RACER_STEMS],
    parts: [
      // Base: everyone hears this.
      part(
        "bass",
        "base",
        0.7,
        bassLine(
          ch,
          [
            [0, 1.5, "R"],
            [2, 1.5, "5"],
          ],
          38,
          0.7,
        ),
      ),
      part("pad", "base", 0.45, pads(ch, 57, 4, 0.5)),
      ...drumParts("base", 0.6, drums("K...k...", KIT, 0.5, T)),
      ...drumParts("base", 0.65, drums("hhHhhhHh", KIT, 0.5, T)),
      ...drumParts("base", 0.4, drums("..s...s.", KIT, 0.5, T)),
      // Moss: marimba and xylophone, bouncy woodblocks and bongos.
      part("marimba", "moss", 1, mel),
      part("xylophone", "moss", 0.35, shift(mel, 0, 12)),
      part("marimba", "moss", 0.45, stabs(ch, [1.5, 3.5], 60, 0.3, 0.5)),
      ...drumParts("moss", 0.7, drums("..w..w.W", KIT, 0.5, T)),
      ...drumParts("moss", 0.55, drums("b.b..bB.", KIT, 0.5, T)),
      // Bramble: pizzicato tune, walking bass, a low bassoon line.
      part("pizz", "bramble", 1.1, mel),
      part(
        "bass",
        "bramble",
        0.9,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [1, 1, "3"],
            [2, 1, "5"],
            [3, 1, "A"],
          ],
          40,
          0.8,
        ),
      ),
      part("bassoon", "bramble", 0.6, thirds),
      // Poppy: flute, a celesta sparkle and light pizzicato chords.
      part("flute", "poppy", 1, mel),
      part("celesta", "poppy", 0.45, arpeggio(ch, 0.5, [0, 1, 2, 3], 72, 0.5, 0.5)),
      part("pizz", "poppy", 0.35, stabs(ch, [0.5, 1.5, 2.5, 3.5], 64, 0.25, 0.5)),
      // Otto: a mellow clarinet an octave down, soft horns, relaxed marimba.
      part("clarinet", "otto", 1, shift(mel, 0, -12)),
      part("horn", "otto", 0.55, pads(ch, 55, 4, 0.5)),
      part("marimba", "otto", 0.5, stabs(ch, [1, 3], 55, 0.4, 0.55)),
    ],
  };
}

// ---------------------------------------------------------------- "Course Map"

export const MAP_MELODY = bars(
  "F#5:1.5 A5:.5 D6:1 A5:1",
  "G5:1.5 E5:.5 C5:1 E5:1",
  "D5:.5 G5:.5 B5:1 A5:.5 G5:.5 E5:1",
  "F#5:3 r:1",
  "D6:.5 C#6:.5 B5:.5 F#5:.5 D5:1 F#5:1",
  "G5:.5 A5:.5 B5:.5 D6:.5 B5:2",
  "E5:.5 G5:.5 B5:.5 E6:.5 D6:1 B5:1",
  "C#6:1 A5:1 E5:1 r:1",
  "F#5:1.5 A5:.5 D6:1 F#6:1",
  "E6:1.5 D6:.5 C6:1 G5:1",
  "B5:.5 A5:.5 G5:.5 E5:.5 D5:1 G5:1",
  "A5:3 r:1",
  "B5:1 D6:1 G6:1 F#6:.5 E6:.5",
  "E6:1 C#6:1 A5:2",
  "F#5:.5 A5:.5 D6:.5 F#6:.5 E6:1 C#6:1",
  "D6:2 r:2",
);
export const MAP_CHORDS = "D:4 C:4 G:4 D:4 Bm:4 G:4 Em:4 A:4 D:4 C:4 G:4 D:4 G:4 A:4 D:4 D:4";

function map(): Song {
  const ch = chart(MAP_CHORDS);
  const mel = seq(MAP_MELODY, 0, 0.75);
  const inBars = (from: number, to: number) => mel.filter((n) => n.t >= from * 4 && n.t < to * 4);
  const T = 16;
  return {
    id: "map",
    title: "Course Map",
    role: "Mode & track select",
    bpm: 98,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("flute", "base", 1, [...inBars(0, 4), ...inBars(8, 12), ...inBars(12, 16)]),
      part("xylophone", "base", 0.9, [...inBars(4, 8), ...inBars(12, 16)]),
      part("marimba", "base", 0.6, arpeggio(ch, 1, [0, 1, 2, 1], 62, 0.9, 0.5)),
      part(
        "bass",
        "base",
        0.85,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [1.5, 0.5, "R"],
            [2, 1, "5"],
            [3, 1, "8"],
          ],
          38,
          0.75,
        ),
      ),
      part("pad", "base", 0.4, pads(ch, 57, 4, 0.45)),
      ...drumParts("base", 0.6, drums("B..b.Bb.", KIT, 0.5, T)),
      ...drumParts("base", 0.5, drums("h.h.h.hh", KIT, 0.5, T)),
      ...drumParts("base", 0.4, drums("......w.", KIT, 0.5, T)),
    ],
  };
}

// ---------------------------------------------------------------- "Lakeside Dash"

export const RACE_MELODY = bars(
  "A4:.5 C5:.5 E5:.5 A5:.5 G5:.5 E5:.5 C5:.5 E5:.5",
  "F5:1 E5:.5 D5:.5 C5:1 A4:1",
  "G4:.5 C5:.5 E5:.5 G5:.5 C6:1 B5:.5 G5:.5",
  "D6:1.5 B5:.5 G5:1 r:1",
  "A5:.5 G5:.5 E5:.5 G5:.5 A5:1 C6:1",
  "C6:.5 A5:.5 F5:.5 A5:.5 C6:1 F6:1",
  "E6:.5 D6:.5 B5:.5 G5:.5 D6:1 B5:1",
  "G#5:1 B5:1 E6:1.5 r:.5",
  "E6:.5 D6:.5 C6:1 G5:1 E5:1",
  "D6:.5 C6:.5 B5:1 G5:2",
  "C6:.5 B5:.5 A5:1 E5:1 A5:1",
  "F5:.5 G5:.5 A5:.5 C6:.5 F6:2",
  "E6:1 G6:1 E6:.5 D6:.5 C6:1",
  "B5:1 D6:1 G5:2",
  "A5:.5 C6:.5 F6:1 G5:.5 B5:.5 D6:1",
  "C6:2 G5:.5 E5:.5 C5:.5 E5:.5",
);
export const RACE_CHORDS =
  "Am:4 F:4 C:4 G:4 Am:4 F:4 G:4 E7:4 C:4 G:4 Am:4 F:4 C:4 G:4 F:2 G:2 C:4";

function race(): Song {
  const ch = chart(RACE_CHORDS);
  const mel = seq(RACE_MELODY, 0, 0.82);
  const a = mel.filter((n) => n.t < 32);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  const drive: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.5, "R"],
    [1, 0.5, "8"],
    [1.5, 0.5, "R"],
    [2, 0.5, "5"],
    [2.5, 0.5, "R"],
    [3, 0.5, "8"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "race",
    title: "Lakeside Dash",
    role: "Racing",
    bpm: 152,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("brass", "base", 1, a),
      part("square", "base", 0.3, shift(a, 0, 12)),
      part("marimba", "base", 1, b),
      part("flute", "base", 0.7, b),
      part(
        "brass",
        "base",
        0.45,
        stabs(
          ch.filter((c) => c.t >= 32),
          [0.5, 2.5],
          60,
          0.3,
          0.6,
        ),
      ),
      part(
        "square",
        "base",
        0.2,
        arpeggio(
          ch.filter((c) => c.t >= 32),
          0.25,
          [0, 1, 2, 3],
          72,
          0.2,
          0.5,
        ),
      ),
      part(
        "marimba",
        "base",
        0.55,
        arpeggio(
          ch.filter((c) => c.t < 32),
          0.5,
          [0, 2, 1, 2],
          60,
          0.4,
          0.5,
        ),
      ),
      part("bass", "base", 1, bassLine(ch, drive, 38, 0.85)),
      ...drumParts("base", 0.95, drums("K..kK.k.", KIT, 0.5, T)),
      ...drumParts("base", 0.85, drums("..S...S.", KIT, 0.5, T)),
      ...drumParts("base", 0.6, drums("iIiiiIii", KIT, 0.5, T)),
      ...drumParts("base", 0.5, drums(".t.t.t.t", KIT, 0.5, 8, 32)),
      ...drumParts("base", 0.8, drums("C", KIT, 32, 2)),
    ],
  };
}

// ---------------------------------------------------------------- "Riverbend Palms"
// A beach party: calypso-style 3+3+2 phrases on the steel pan, everything bouncing.

export const RIVERBEND_MELODY = bars(
  "F5:.5 A5:.5 C6:.5 A5:1 C6:.5 F6:1",
  "F6:.5 D6:.5 Bb5:1 D6:.5 F6:1 D6:.5",
  "E6:.5 C6:.5 G5:.5 E5:1 G5:.5 C6:1",
  "A5:1.5 C6:1.5 F5:1",
  "D6:.5 F6:.5 A6:.5 F6:1 D6:.5 A5:1",
  "Bb5:.5 D6:.5 F6:.5 D6:1 C6:.5 Bb5:1",
  "C6:.5 E6:.5 G6:.5 E6:1 D6:.5 C6:1",
  "G6:.5 F6:.5 E6:.5 D6:.5 C6:.5 Bb5:.5 G5:1",
  "D6:1 r:.5 D6:.5 F6:.5 D6:.5 Bb5:1",
  "E6:1 r:.5 E6:.5 G6:.5 E6:.5 C6:1",
  "C6:.5 E6:.5 A6:1 G6:.5 E6:.5 C6:1",
  "D6:.5 F6:.5 A6:1 F6:.5 E6:.5 D6:1",
  "F6:.5 F6:.5 D6:.5 Bb5:1 C6:.5 D6:1",
  "E6:.5 G6:.5 Bb6:.5 G6:1 E6:.5 C6:1",
  "A6:.5 G6:.5 F6:.5 C6:1 A5:.5 C6:.5 D6:.5",
  "F6:2! r:1 C6:.5 D6:.5",
);
export const RIVERBEND_CHORDS =
  "F:4 Bb:4 C:4 F:4 Dm:4 Bb:4 C:4 C7:4 Bb:4 C:4 Am:4 Dm:4 Bb:4 C7:4 F:4 F:4";

function riverbend(): Song {
  const ch = chart(RIVERBEND_CHORDS);
  const mel = seq(RIVERBEND_MELODY, 0, 0.86);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  // Soca bass: bouncing between root and octave on the off-beats, a walk into each chord.
  const bounce: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.5, "8"],
    [1.5, 0.5, "R"],
    [2, 0.5, "5"],
    [2.5, 0.5, "8"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  // The flute's whistle: a high answer at the end of every other bar.
  const whistle = seq(
    bars(
      "r:4",
      "r:2 F6:.25 G6:.25 A6:.5 r:1",
      "r:4",
      "r:2 C7:.25 A6:.25 F6:.5 r:1",
      "r:4",
      "r:2 F6:.25 G6:.25 A6:.5 r:1",
      "r:4",
      "r:2 E6:.25 F6:.25 G6:.5 r:1",
    ),
    0,
    0.7,
  );
  return {
    id: "riverbend",
    title: "Riverbend Palms",
    role: "Prehistoric World",
    bpm: 138,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("steelpan", "base", 1, mel),
      part("xylophone", "base", 0.3, shift(b, 0, 12)),
      part("flute", "base", 0.5, [...whistle, ...shift(whistle, 32)]),
      // A strummed off-beat "skank" on the marimba, and a lower arpeggio under it.
      part("marimba", "base", 0.55, stabs(ch, [0.5, 1.5, 2.5, 3.5], 62, 0.2, 0.6)),
      part("marimba", "base", 0.35, arpeggio(ch, 0.5, [0, 2, 1, 2], 53, 0.35, 0.5)),
      // Brass hits on the push before beats 3 and 1.
      part("brass", "base", 0.5, stabs(ch, [1.5, 3.5], 60, 0.22, 0.7)),
      part(
        "pad",
        "base",
        0.35,
        pads(
          ch.filter((c) => c.t >= 32),
          57,
          4,
          0.45,
        ),
      ),
      part("bass", "base", 1, bassLine(ch, bounce, 34, 0.9)),
      ...drumParts("base", 0.85, drums("K...K...K...K...", KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("....s.......s..s", KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("hhHhhhHhhhHhhhHh", KIT, 0.25, T)),
      ...drumParts("base", 0.45, drums("..t...t...t...t.", KIT, 0.25, T)),
      ...drumParts("base", 0.55, drums("w..w..w...w.w...", KIT, 0.25, T)),
      ...drumParts("base", 0.7, drums("b.bbB.b.b.bbB.bb", KIT, 0.25, T)),
      ...drumParts("base", 0.8, drums("C", KIT, 32, 2)),
    ],
  };
}

// ---------------------------------------------------------------- "Riverbend Palms (Classic)"
// The original (v1) Riverbend theme, kept in the music player. To put it back on the
// course, set the track's music to "riverbend_classic" in src/game/tracks.ts.

export const RIVERBEND_CLASSIC_MELODY = bars(
  "E5:.5 G5:.5 C6:1 G5:.5 E5:.5 G5:1",
  "A5:.5 C6:.5 A5:1 F5:.5 A5:.5 C6:1",
  "B5:.5 D6:.5 G5:1 B5:.5 A5:.5 G5:1",
  "C6:1.5 G5:.5 E5:1 r:1",
  "E5:.5 A5:.5 C6:1 A5:.5 B5:.5 C6:1",
  "C6:.5 D6:.5 C6:1 A5:1 F5:1",
  "G5:.5 A5:.5 B5:1 D6:1 B5:1",
  "A5:.5 B5:.5 D6:.5 F6:.5 G6:2",
  "A5:1 C6:.5 A5:.5 F6:1 C6:1",
  "B5:1 D6:.5 B5:.5 G6:1 D6:1",
  "G5:.5 B5:.5 E6:1 D6:.5 B5:.5 G5:1",
  "A5:.5 C6:.5 E6:1 C6:.5 B5:.5 A5:1",
  "F6:.5 E6:.5 C6:1 A5:1 C6:1",
  "D6:.5 C6:.5 B5:1 G5:1 B5:1",
  "C6:.5 D6:.5 E6:1 G6:1 E6:1",
  "C6:3 r:1",
);
export const RIVERBEND_CLASSIC_CHORDS =
  "C:4 F:4 G:4 C:4 Am:4 F:4 G:4 G7:4 F:4 G:4 Em:4 Am:4 F:4 G:4 C:4 C:4";

function riverbendClassic(): Song {
  const ch = chart(RIVERBEND_CLASSIC_CHORDS);
  const mel = seq(RIVERBEND_CLASSIC_MELODY, 0, 0.85);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  // A bouncy island bass: root, a push on the "and" of two, the fifth, an approach.
  const bounce: [number, number, string][] = [
    [0, 1, "R"],
    [1.5, 0.5, "R"],
    [2, 1, "5"],
    [3, 0.5, "8"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "riverbend_classic",
    title: "Riverbend Palms (Classic)",
    role: "Prehistoric World",
    bpm: 132,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("steelpan", "base", 1, mel),
      part("flute", "base", 0.55, shift(b, 0, -12)),
      part("marimba", "base", 0.6, arpeggio(ch, 0.5, [0, 1, 2, 1, 3, 2, 1, 2], 60, 0.4, 0.55)),
      part("brass", "base", 0.35, stabs(ch, [1.5, 3.5], 60, 0.25, 0.55)),
      part(
        "pad",
        "base",
        0.5,
        pads(
          ch.filter((c) => c.t >= 32),
          55,
          4,
          0.5,
        ),
      ),
      part("bass", "base", 1, bassLine(ch, bounce, 36, 0.85)),
      ...drumParts("base", 0.8, drums("K..k..K.", KIT, 0.5, T)),
      ...drumParts("base", 0.55, drums("hhhhhhhh", KIT, 0.5, T)),
      ...drumParts("base", 0.6, drums("w..w..w...w.w...", KIT, 0.25, T)),
      ...drumParts("base", 0.7, drums("..b.Bb.b..b.Bbbb", KIT, 0.25, 8, 32)),
      ...drumParts("base", 0.8, drums("C", KIT, 32, 2)),
    ],
  };
}

// ---------------------------------------------------------------- "Cascade Caverns"

export const CASCADE_MELODY = bars(
  "D5:.5 F5:.5 A5:.5 D6:.5 A5:.5 C6:.5 A5:1",
  "D6:.5 C6:.5 Bb5:1 F5:.5 G5:.5 F5:1",
  "E5:.5 G5:.5 C6:1 E6:.5 D6:.5 C6:1",
  "D6:1.5 A5:.5 F5:1 r:1",
  "A5:.5 D6:.5 F6:1 E6:.5 D6:.5 A5:1",
  "F6:.5 D6:.5 Bb5:1 D6:.5 C6:.5 Bb5:1",
  "G5:.5 Bb5:.5 D6:1 C6:.5 Bb5:.5 G5:1",
  "A5:.5 C#6:.5 E6:1 A6:2",
  "C6:.5 A5:.5 F5:1 A5:.5 C6:.5 F6:1",
  "E6:.5 D6:.5 C6:1 G5:1 E5:1",
  "D6:.5 F6:.5 D6:1 Bb5:1 F5:1",
  "A5:1 C6:1 F6:1.5 r:.5",
  "G6:.5 F6:.5 D6:1 Bb5:1 G5:1",
  "A5:.5 B5:.5 C#6:1 E6:1 A6:1",
  "F6:.5 E6:.5 D6:1 A5:1 F5:1",
  "E5:.5 G5:.5 A5:1 C#6:1 E6:1",
);
export const CASCADE_CHORDS =
  "Dm:4 Bb:4 C:4 Dm:4 Dm:4 Bb:4 Gm:4 A:4 F:4 C:4 Bb:4 F:4 Gm:4 A:4 Dm:4 A7:4";

function cascade(): Song {
  const ch = chart(CASCADE_CHORDS);
  const mel = seq(CASCADE_MELODY, 0, 0.82);
  const a = mel.filter((n) => n.t < 32);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  const run: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.5, "8"],
    [1, 0.5, "R"],
    [1.5, 0.5, "5"],
    [2, 0.5, "R"],
    [2.5, 0.5, "8"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "cascade",
    title: "Cascade Caverns",
    role: "Prehistoric World",
    bpm: 142,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("flute", "base", 1, mel),
      part("xylophone", "base", 0.5, shift(b, 0, 0)),
      part("pizz", "base", 0.8, arpeggio(ch, 0.25, [0, 2, 1, 2, 3, 2, 1, 2], 57, 0.2, 0.6)),
      part("bell", "base", 0.5, arpeggio(ch, 2, [3, 2], 72, 1.5, 0.45)),
      part("celesta", "base", 0.5, shift(a, 0, 12)),
      part(
        "strings",
        "base",
        0.45,
        pads(
          ch.filter((c) => c.t >= 32),
          50,
          2,
          0.5,
        ),
      ),
      part("bass", "base", 1, bassLine(ch, run, 33, 0.8)),
      ...drumParts("base", 0.85, drums("K...k.K.K...k...", KIT, 0.25, T)),
      ...drumParts("base", 0.7, drums("w.ww.w.ww.w.w.ww", KIT, 0.25, T)),
      ...drumParts("base", 0.6, drums("..b...b...b.b.b.", KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("....S.......S...", KIT, 0.25, 8, 32)),
      ...drumParts("base", 0.8, drums("C", KIT, 32, 2)),
    ],
  };
}

// ---------------------------------------------------------------- "Bonebog Pyramid"

export const BONEBOG_MELODY = bars(
  "E4:1 G4:.5 B4:.5 E5:1 B4:.5 D5:.5",
  "C#5:1 E5:.5 C#5:.5 A4:1 r:1",
  "B4:.5 A4:.5 G4:1 E4:1 G4:1",
  "A4:.5 C#5:.5 E5:1 F#5:.5 E5:.5 C#5:1",
  "G4:.5 C5:.5 E5:1 G5:1 E5:1",
  "F#5:.5 E5:.5 D5:1 A4:1 F#4:1",
  "G4:.5 B4:.5 E5:1.5 r:.5 B4:1",
  "D#5:.5 F#5:.5 A5:1 F#5:1 D#5:1",
  "E5:1 G5:.5 E5:.5 C5:1 G4:1",
  "C5:.5 Eb5:.5 Ab5:1 G5:.5 Eb5:.5 C5:1",
  "B4:.5 E5:.5 G5:1 B5:1 G5:1",
  "E5:.5 C#5:.5 A4:1 C#5:1 E5:1",
  "G5:1 E5:.5 G5:.5 C6:1 G5:1",
  "A5:1 F#5:.5 D5:.5 A4:1 D5:1",
  "E5:.5 B4:.5 G4:1 F4:.5 A4:.5 C5:1",
  "E4:3 r:1",
);
export const BONEBOG_CHORDS =
  "Em:4 A:4 Em:4 A:4 C:4 D:4 Em:4 B7:4 C:4 Ab:4 Em:4 A:4 C:4 D:4 Em:2 F:2 Em:4";

function bonebog(): Song {
  const ch = chart(BONEBOG_CHORDS);
  const mel = seq(BONEBOG_MELODY, 0, 0.8);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  // A lazy, bouncing groove: root, a ghosted octave, the fifth, a slide in.
  const groove: [number, number, string][] = [
    [0, 0.75, "R"],
    [0.75, 0.25, "8"],
    [1.5, 0.5, "5"],
    [2, 0.75, "R"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "bonebog",
    title: "Bonebog Pyramid",
    role: "Prehistoric World",
    bpm: 116,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("clarinet", "base", 1, mel),
      part("bassoon", "base", 0.45, shift(b, 0, -12)),
      part("marimba", "base", 0.85, arpeggio(ch, 0.5, [0, 2, 1, 2, 0, 2, 1, 3], 45, 0.45, 0.6)),
      part("pizz", "base", 0.6, stabs(ch, [0.5, 1.5, 2.5, 3.5], 55, 0.2, 0.45)),
      part("bell", "base", 0.4, arpeggio(ch, 4, [3, 4], 76, 3, 0.4)),
      part("pad", "base", 0.5, pads(ch, 52, 4, 0.4)),
      part("bass", "base", 1, bassLine(ch, groove, 28, 0.85)),
      ...drumParts("base", 0.8, drums("K.....k.K.......", KIT, 0.25, T)),
      ...drumParts("base", 0.75, drums("....o.......o.oo", KIT, 0.25, T)),
      ...drumParts("base", 0.45, drums("h.hhh.hhh.hhh.hh", KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("....w.......w..w", KIT, 0.25, 8, 32)),
    ],
  };
}

// ---------------------------------------------------------------- "Ember Peak"

export const EMBER_MELODY = bars(
  "A4:.5 A4:.5 C5:.5 E5:.5 A5:1 E5:.5 G5:.5",
  "A5:1.5 G5:.5 E5:1 C5:1",
  "F5:.5 A5:.5 C6:1 A5:.5 F5:.5 C5:1",
  "B4:.5 E5:.5 G#5:1 B5:2",
  "C6:.5 B5:.5 A5:1 E5:1 A5:1",
  "C6:.5 D6:.5 E6:1 D6:.5 C6:.5 A5:1",
  "F6:.5 E6:.5 D6:1 A5:1 F5:1",
  "G#5:.5 A5:.5 B5:1 E6:1.5 r:.5",
  "A5:.5 C6:.5 F6:1 C6:1 A5:1",
  "B5:.5 D6:.5 G6:1 D6:1 B5:1",
  "C6:.5 E6:.5 A6:1 E6:1 C6:1",
  "B5:.5 G5:.5 E5:1 G5:1 B5:1",
  "C6:1 A5:.5 C6:.5 F6:1 A6:1",
  "G6:1 D6:.5 B5:.5 G5:1 D6:1",
  "E6:.5 D6:.5 B5:1 G#5:1 E5:1",
  "D6:.5 B5:.5 G#5:.5 E5:.5 D5:2",
);
export const EMBER_CHORDS =
  "Am:4 Am:4 F:4 E:4 Am:4 Am:4 Dm:4 E:4 F:4 G:4 Am:4 Em:4 F:4 G:4 E:4 E7:4";

function ember(): Song {
  const ch = chart(EMBER_CHORDS);
  const mel = seq(EMBER_MELODY, 0, 0.85);
  const a = mel.filter((n) => n.t < 32);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  // A galloping eighth-note bass, pushing into every bar.
  const gallop: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.5, "R"],
    [1, 0.5, "8"],
    [1.5, 0.5, "R"],
    [2, 0.5, "R"],
    [2.5, 0.5, "5"],
    [3, 0.5, "8"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "ember",
    title: "Ember Peak",
    role: "Prehistoric World",
    bpm: 158,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("strings", "base", 1, mel),
      part("horn", "base", 0.6, shift(a, 0, -12)),
      part("brass", "base", 0.8, b),
      part("square", "base", 0.25, shift(b, 0, 12)),
      part("marimba", "base", 0.6, arpeggio(ch, 0.25, [0, 1, 2, 3, 2, 1, 2, 3], 57, 0.2, 0.5)),
      part("horn", "base", 0.55, stabs(ch, [0, 1.5, 3], 45, 0.35, 0.6)),
      part(
        "square",
        "base",
        0.18,
        stabs(
          ch.filter((c) => c.t >= 32),
          [0.75, 2.75],
          69,
          0.15,
          0.5,
        ),
      ),
      part("bass", "base", 1.1, bassLine(ch, gallop, 33, 0.9)),
      ...drumParts("base", 1, drums("K.k.K.k.K.k.K.kk", KIT, 0.25, T)),
      ...drumParts("base", 0.85, drums("....S.......S.S.", KIT, 0.25, T)),
      ...drumParts("base", 0.55, drums("iiIiiiIiiiIiiiIi", KIT, 0.25, T)),
      ...drumParts("base", 0.7, drums("..............oo", KIT, 0.25, T)),
      ...drumParts("base", 0.85, drums("C", KIT, 16, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Finish Line!"

export const FANFARE_MELODY =
  "C5:.25 E5:.25 G5:.25 C6:.75 r:.5 A5:.5 B5:.5 C6:.5 D6:.5 [E5,G5,C6,E6]:3! r:5";

function fanfare(): Song {
  const brass = seq(FANFARE_MELODY, 0, 0.9);
  const roll: Note[] = [];
  for (let t = 4; t < 7; t += 0.25)
    for (const m of [60, 64, 67, 72])
      roll.push({ t, d: 0.25, m: m + (t % 1 === 0 ? 12 : 0), v: 0.55 });
  const snareRoll: Note[] = [];
  for (let t = 2; t < 4; t += 0.125) snareRoll.push({ t, d: 0.125, m: 0, v: 0.3 + (t - 2) * 0.25 });
  return {
    id: "fanfare",
    title: "Finish Line!",
    role: "Results",
    bpm: 120,
    beats: 12,
    loop: false,
    stems: [],
    parts: [
      part("brass", "base", 1.1, brass),
      part("square", "base", 0.25, shift(brass, 0, 12)),
      part("marimba", "base", 0.8, roll),
      part("bass", "base", 1, seq("C3:1 r:1 G2:1 r:1 C3:3", 0, 0.9)),
      part("snare", "base", 0.8, snareRoll),
      part("crash", "base", 1, [{ t: 4, d: 2, m: 0, v: 1 }]),
      part("kick", "base", 1, [
        { t: 0, d: 1, m: 0, v: 0.9 },
        { t: 4, d: 1, m: 0, v: 1 },
      ]),
    ],
  };
}

/** Every composed piece, by id. */
export const SONGS: Record<string, Song> = {
  title: title(),
  select: select(),
  map: map(),
  race: race(),
  fanfare: fanfare(),
  riverbend: riverbend(),
  riverbend_classic: riverbendClassic(),
  cascade: cascade(),
  bonebog: bonebog(),
  ember: ember(),
};

/** The music player's list: composed pieces, then planned ones not written yet. */
export const CATALOG: { id: string; title: string; role: string; available: boolean }[] = [
  ...Object.values(SONGS).map((s) => ({ id: s.id, title: s.title, role: s.role, available: true })),
  { id: "adventure", title: "Adventure Map", role: "Adventure mode", available: false },
];
