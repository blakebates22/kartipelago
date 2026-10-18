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
};

/** The music player's list: composed pieces, then planned ones not written yet. */
export const CATALOG: { id: string; title: string; role: string; available: boolean }[] = [
  ...Object.values(SONGS).map((s) => ({ id: s.id, title: s.title, role: s.role, available: true })),
  { id: "ancient_lake", title: "Ancient Lake", role: "Track theme", available: false },
  { id: "fossil_canyon", title: "Fossil Canyon", role: "Track theme", available: false },
  { id: "jungle_falls", title: "Jungle Falls", role: "Track theme", available: false },
  { id: "hot_top_volcano", title: "Hot Top Volcano", role: "Track theme", available: false },
  { id: "adventure", title: "Adventure Map", role: "Adventure mode", available: false },
];
