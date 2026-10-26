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
 *   cascade     "Cascade Caverns"   D minor, 128: deep in the jungle temple. Pan flute
 *                                   lead with bird calls, a hollow log-drum ostinato,
 *                                   a buzzing drone, hand drums (djembe, toms, bongos),
 *                                   shakers, and horns for the big moments
 *   cascade_classic  "Cascade Caverns (Classic)"  D minor, 142: the v1 theme (flute
 *                                   over pizzicato, wood, bells)
 *   frostveil   "Frostveil Citadel" E minor, 138: a journey to a lost mountain citadel.
 *                                   Celesta and bells in the moonlit first half, then a
 *                                   wooden flute and warm horns lift it; plucked strings,
 *                                   a bright marimba, deep toms and a driving bass
 *   summit      "Snowy Summit Pass" D major, 152: a bright gallop round a sunny mountain
 *                                   lake. Flute and xylophone, then brass, then strings
 *                                   and bells in the treetops, over a running marimba,
 *                                   a skipping bass, shaker and tambourine
 *   hearthglow  "Hearthglow Hollow" G major, 160: a Christmas-village gallop. Sleigh bells
 *                                   throughout; celesta and bells, then flute, then
 *                                   strings and brass, over plucked strings, a twinkling
 *                                   glockenspiel and an oom-pah walking bass
 *   aurora      "Aurora Rift"       F# minor, 148: down into the glacier under the northern
 *                                   lights. Celesta over shimmering crystal bells in the
 *                                   Cathedral, flute and a running marimba on the lake,
 *                                   brass and strings soaring for the Loop and the climb
 *   canyon      "Canyon Dash"       D minor, 168: a desert gallop round the red-rock canyon.
 *                                   Brass and flute trading a sun-baked tune over a
 *                                   clip-clopping woodblock, strummed pizzicato, a rolling
 *                                   marimba, bongos, and strings for the bridge and the falls
 *   oasis       "Oasis Haven"       A major, 150: a sunny resort holiday. Steel pan and flute
 *                                   trading a carefree tune, strings over the falls,
 *                                   marimba arpeggios like sparkling water, a bouncy bass,
 *                                   congas, shaker and tambourine
 *   depths      "Impact Depths"     D minor, 140: down through the world under the desert.
 *                                   Brass and flute over the sands, celesta and bells in
 *                                   the crystal halls, low marimba, horns and toms in the
 *                                   jungle and the lava, strings climbing back to the sun
 *   dragon      "Dragon Isles"      G major pentatonic, 152: a festival lap of the dragon
 *                                   kingdom. Bamboo flute over plucked strings and bright
 *                                   mallets in the market, bells and celesta for the great
 *                                   dragon's theme, brass for the palace; festival drums,
 *                                   bongos and a gong-like crash
 *   dragon_canyon "Dragon Canyon"   D minor, 168: the kingdom's desert frontier. A galloping
 *                                   flute over plucked strings, the quarry's low brass and
 *                                   marimba, strings soaring over the High Bridges, and
 *                                   flute and xylophone racing through the Final Twist;
 *                                   driving toms, bongos and shaker throughout
 *   celestial   "Celestial Dragon Festival"  D major, 144: the grand finale, in three
 *                                   layers that grow lap by lap with the fireworks
 *   snow_dragon "Snow Dragon Pass"  B minor, 150: the kingdom in winter. Cold bells and
 *                                   celesta over a pulsing drone, a lamenting string
 *                                   melody for the village and the ration lines, low
 *                                   horns and toms for the ice dragon, flute and
 *                                   strings together for the climb to the citadel
 *   bonebog     "Bonebog Pyramid"   E minor, 116: low marimba groove, clarinet, toms,
 *                                   chimes, with friendly surprise chords (A, Ab, F)
 *   ember       "Ember Peak"        D minor, 160: the Volcanic Apocalypse. Low brass
 *                                   over a hammering marimba and heavy toms, then strings
 *                                   and brass soaring as you escape the eruption
 *   ember_classic "Ember Peak (Classic)" A minor, 158: the original volcano march
 *
 * "Pick Your Racer" is one arrangement split into stems that always play in sync: a
 * base groove, plus a layer per racer playing the same tune in their own instruments
 * (Tiko: marimba and woodblocks; Brakka: pizzicato, walking bass and bassoon; Zephyr:
 * flute, celesta and light pizzicato; Pebble: clarinet, soft horns and lazy marimba). The
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
export const RACER_STEMS = [
  "tiko",
  "brakka",
  "pebble",
  "zephyr",
  "raptor",
  "rex",
  "brachio",
  "stego",
] as const;

function select(): Song {
  const ch = chart(SELECT_CHORDS);
  const mel = seq(SELECT_MELODY, 0, 0.8);
  const beats = 64;
  const T = 16; // bars
  // The thirds of each chord, held low: Brakka's bassoon line.
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
      // Tiko: marimba and xylophone, bouncy woodblocks and bongos.
      part("marimba", "tiko", 1, mel),
      part("xylophone", "tiko", 0.35, shift(mel, 0, 12)),
      part("marimba", "tiko", 0.45, stabs(ch, [1.5, 3.5], 60, 0.3, 0.5)),
      ...drumParts("tiko", 0.7, drums("..w..w.W", KIT, 0.5, T)),
      ...drumParts("tiko", 0.55, drums("b.b..bB.", KIT, 0.5, T)),
      // Brakka: pizzicato tune, walking bass, a low bassoon line.
      part("pizz", "brakka", 1.1, mel),
      part(
        "bass",
        "brakka",
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
      part("bassoon", "brakka", 0.6, thirds),
      // Zephyr: flute, a celesta sparkle and light pizzicato chords.
      part("flute", "zephyr", 1, mel),
      part("celesta", "zephyr", 0.45, arpeggio(ch, 0.5, [0, 1, 2, 3], 72, 0.5, 0.5)),
      part("pizz", "zephyr", 0.35, stabs(ch, [0.5, 1.5, 2.5, 3.5], 64, 0.25, 0.5)),
      // Pebble: a mellow clarinet an octave down, soft horns, relaxed marimba.
      part("clarinet", "pebble", 1, shift(mel, 0, -12)),
      part("horn", "pebble", 0.55, pads(ch, 55, 4, 0.5)),
      part("marimba", "pebble", 0.5, stabs(ch, [1, 3], 55, 0.4, 0.55)),
      // Raptor: a quick xylophone an octave up, snappy pizzicato offbeats, woodblocks.
      part("xylophone", "raptor", 0.9, shift(mel, 0, 12)),
      part("pizz", "raptor", 0.45, stabs(ch, [0.5, 1.5, 2.5, 3.5], 67, 0.2, 0.5)),
      ...drumParts("raptor", 0.6, drums("w.ww.w.W", KIT, 0.5, T)),
      // Rex: the tune on horns, low and proud, a stomping kick and a bassoon under it.
      part("horn", "rex", 1, shift(mel, 0, -12)),
      part("bassoon", "rex", 0.6, thirds),
      ...drumParts("rex", 0.7, drums("K.K...K.", KIT, 0.5, T)),
      // Brachio: a gentle clarinet, celesta drifting over it.
      part("clarinet", "brachio", 0.9, mel),
      part("celesta", "brachio", 0.4, arpeggio(ch, 1, [0, 1, 2, 1], 67, 0.6, 0.45)),
      // Stego: laid-back: the tune on marimba an octave down, a lazy walking pizz bass.
      part("marimba", "stego", 0.9, shift(mel, 0, -12)),
      part(
        "pizz",
        "stego",
        0.7,
        bassLine(
          ch,
          [
            [0, 1.5, "R"],
            [2, 1.5, "5"],
          ],
          43,
          0.6,
        ),
      ),
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
// Deep in the jungle, exploring the temple: a wooden pan flute over a hollow log-drum
// ostinato and a buzzing drone, hand drums underneath, birds calling overhead, and
// horns rising in the second half (the bridge, the leap).

export const CASCADE_MELODY = bars(
  "D5:1 F5:.5 A5:.5 D6:1.5 C6:.5",
  "E6:1 D6:.5 C6:.5 G5:1 E5:1",
  "F5:.5 A5:.5 D6:1 F6:1 E6:.5 D6:.5",
  "E6:1.5 C6:.5 A5:2",
  "A5:.5 D6:.5 F6:.5 A6:.5 G6:1 F6:1",
  "A6:1 F6:.5 C6:.5 A5:1 C6:1",
  "G5:.5 C6:.5 E6:1 G6:1 E6:.5 C6:.5",
  "E6:1 C#6:1 A5:2!",
  "D6:.5 F6:.5 Bb6:1 A6:.5 F6:.5 D6:1",
  "E6:.5 G6:.5 C7:1 G6:1 E6:1",
  "F6:1 E6:.5 D6:.5 A5:1 D6:1",
  "A5:1.5 r:.5 D5:.5 E5:.5 F5:1",
  "F5:.5 Bb5:.5 D6:1 F6:1 D6:1",
  "E6:.5 D6:.5 C6:1 G5:1 C6:1",
  "C#6:.5 D6:.5 E6:1 A6:1 G6:1",
  "E6:1 C#6:1 A5:1 r:1",
);
export const CASCADE_CHORDS =
  "Dm:4 C:4 Dm:4 Am:4 Dm:4 F:4 C:4 A:4 Bb:4 C:4 Dm:4 Dm:4 Bb:4 C:4 A:4 A7:4";

const JUNGLE_KIT: Record<string, InstrumentId> = {
  ...KIT,
  d: "djembe",
};

function cascade(): Song {
  const ch = chart(CASCADE_CHORDS);
  const mel = seq(CASCADE_MELODY, 0, 0.84);
  const b = mel.filter((n) => n.t >= 32);
  const T = 16;
  // Birds calling over the canopy: quick high trills on the pan flute, now and then.
  const birds = seq(
    bars(
      "r:4",
      "r:3 A6:.25 D7:.25 A6:.25 D7:.25",
      "r:4",
      "r:4",
      "r:4",
      "r:3 C7:.25 F7:.25 C7:.5",
      "r:4",
      "r:4",
    ),
    0,
    0.5,
  );
  // The log drum: a 3+3+2 ostinato on the chord, round and round.
  const logs = arpeggio(ch, 0.5, [0, 1, 0, 2, 0, 1, 2, 1], 50, 0.4, 0.62);
  // The drone sits on the chord's root, a long blow per bar.
  const drone = bassLine(ch, [[0, 3.9, "R"]], 38, 0.75);
  // A walking bass that only joins in the second half.
  const walk = bassLine(
    ch.filter((c) => c.t >= 32),
    [
      [0, 1, "R"],
      [1.5, 0.5, "5"],
      [2, 1, "8"],
      [3, 0.5, "5"],
      [3.5, 0.5, "A"],
    ],
    33,
    0.8,
  );
  return {
    id: "cascade",
    title: "Cascade Caverns",
    role: "Prehistoric World",
    bpm: 128,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      part("panflute", "base", 1, mel),
      part("panflute", "base", 0.5, [...birds, ...shift(birds, 32)]),
      part("marimba", "base", 0.35, shift(b, 0, -12)),
      part("logdrum", "base", 0.9, logs),
      part("drone", "base", 0.8, drone),
      part("bass", "base", 0.8, walk),
      // Horns swell under the second half.
      part(
        "horn",
        "base",
        0.4,
        pads(
          ch.filter((c) => c.t >= 32),
          53,
          4,
          0.5,
        ),
      ),
      part("strings", "base", 0.25, pads(ch, 57, 4, 0.4)),
      // Hand drums: a djembe groove, toms answering, bongo chatter, kick on the one.
      ...drumParts("base", 0.85, drums("D..d..D.d.D..d..", JUNGLE_KIT, 0.25, T)),
      ...drumParts("base", 0.6, drums("....o.......o.oo", JUNGLE_KIT, 0.25, T)),
      ...drumParts("base", 0.55, drums("..b.b..b..b.b.bB", JUNGLE_KIT, 0.25, T)),
      ...drumParts("base", 0.7, drums("K.......K.......", JUNGLE_KIT, 0.25, T)),
      ...drumParts("base", 0.45, drums("hhHhhhHhhhHhhhHh", JUNGLE_KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("w.....w.....w.w.", JUNGLE_KIT, 0.25, T)),
      ...drumParts("base", 0.6, drums("C", JUNGLE_KIT, 32, 2)),
    ],
  };
}

// ---------------------------------------------------------------- "Cascade Caverns (Classic)"
// The original (v1) Cascade theme, kept in the music player. To put it back on the
// course, set the track's music to "cascade_classic" in src/game/tracks.ts.

export const CASCADE_CLASSIC_MELODY = bars(
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
export const CASCADE_CLASSIC_CHORDS =
  "Dm:4 Bb:4 C:4 Dm:4 Dm:4 Bb:4 Gm:4 A:4 F:4 C:4 Bb:4 F:4 Gm:4 A:4 Dm:4 A7:4";

function cascadeClassic(): Song {
  const ch = chart(CASCADE_CLASSIC_CHORDS);
  const mel = seq(CASCADE_CLASSIC_MELODY, 0, 0.82);
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
    id: "cascade_classic",
    title: "Cascade Caverns (Classic)",
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

// ---------------------------------------------------------------- "Frostveil Citadel"
// Mysterious, then gradually uplifting: the climb to a lost city in the snow. The first
// half is moonlight (celesta and bells over plucked strings); in the second the wooden
// flute takes the tune and warm horns swell under it as the citadel comes into view.

export const FROSTVEIL_MELODY = bars(
  "E5:1 G5:.5 B5:.5 E6:1.5 D6:.5",
  "C6:1 B5:.5 G5:.5 E5:1 G5:1",
  "D6:.5 B5:.5 G5:1 B5:1 D6:1",
  "F#6:1.5 E6:.5 D6:2",
  "B5:.5 E6:.5 G6:1 F#6:.5 E6:.5 B5:1",
  "E6:1 G6:1 C7:1 B6:1",
  "A6:.5 G6:.5 E6:1 C6:1 E6:1",
  "D#6:1 F#6:1 B6:2!",
  "G5:.5 C6:.5 E6:1 G6:1.5 E6:.5",
  "F#6:1 E6:.5 D6:.5 A5:1 D6:1",
  "B5:.5 D6:.5 G6:1 B6:1 A6:1",
  "G6:1.5 E6:.5 B5:2",
  "E6:.5 G6:.5 C7:1 B6:.5 G6:.5 E6:1",
  "F#6:.5 A6:.5 D7:1 C7:.5 A6:.5 F#6:1",
  "D#6:.5 F#6:.5 B6:1 A6:1 F#6:1",
  "B6:1 A6:1 F#6:1 D#6:1",
);
export const FROSTVEIL_CHORDS =
  "Em:4 C:4 G:4 D:4 Em:4 C:4 Am:4 B:4 C:4 D:4 G:4 Em:4 C:4 D:4 B:4 B7:4";

function frostveil(): Song {
  const ch = chart(FROSTVEIL_CHORDS);
  const mel = seq(FROSTVEIL_MELODY, 0, 0.82);
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
  const second = ch.filter((c) => c.t >= 32);
  return {
    id: "frostveil",
    title: "Frostveil Citadel",
    role: "Snowy Peaks",
    bpm: 138,
    beats: 64,
    loop: true,
    stems: [],
    parts: [
      // The tune: celesta (doubled by bells an octave down) in the moonlit half, then
      // the wooden flute with a horn line under it.
      part("celesta", "base", 1, a),
      part("bell", "base", 0.35, shift(a, 0, -12)),
      part("panflute", "base", 1, b),
      part("horn", "base", 0.45, shift(b, 0, -12)),
      // Plucked strings all the way, a bright marimba ostinato in the second half.
      part("pizz", "base", 0.7, arpeggio(ch, 0.5, [0, 1, 2, 1, 3, 2, 1, 2], 52, 0.3, 0.55)),
      part("marimba", "base", 0.45, arpeggio(second, 0.25, [0, 2, 1, 2, 3, 2, 1, 2], 64, 0.2, 0.5)),
      // Sparkle at the top of each bar.
      part("bell", "base", 0.4, arpeggio(ch, 2, [3, 2], 76, 1.5, 0.4)),
      // Pads: cold strings throughout, warm horns swelling under the second half.
      part("strings", "base", 0.4, pads(ch, 55, 4, 0.45)),
      part("horn", "base", 0.3, pads(second, 52, 4, 0.5)),
      part("bass", "base", 0.95, bassLine(ch, drive, 28, 0.8)),
      // Deep drums: kick and low toms, hand drums and a shaker.
      ...drumParts("base", 0.85, drums("K.....k.K.......", KIT, 0.25, T)),
      ...drumParts("base", 0.65, drums("........o..o.oOo", KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("....S.......S...", KIT, 0.25, 8, 32)),
      ...drumParts("base", 0.45, drums("hhHhhhHhhhHhhhHh", KIT, 0.25, T)),
      ...drumParts("base", 0.5, drums("..b...b...b.b..b", KIT, 0.25, T)),
      ...drumParts("base", 0.7, drums("C", KIT, 32, 2)),
    ],
  };
}

// ---------------------------------------------------------------- "Snowy Summit Pass"
// A bright, adventurous gallop round a sunny mountain lake: flute and xylophone over a
// running marimba on the frozen bay, brass taking the tune up through the caves and
// canyons, strings and bells soaring in the treetops, and everything together for the
// plunge back down.

export const SUMMIT_MELODY = bars(
  "D5:.5 F#5:.5 A5:1 D6:1 A5:1",
  "C#6:1.5 B5:.5 A5:1 E5:1",
  "B5:.5 C#6:.5 D6:1 F#6:1 D6:1",
  "D6:.5 E6:.5 D6:1 B5:1 G5:1",
  "A5:.5 D6:.5 F#6:1 E6:.5 D6:.5 A5:1",
  "E6:1 C#6:.5 E6:.5 A6:1.5 r:.5",
  "G6:.5 F#6:.5 E6:.5 D6:.5 B5:1 D6:1",
  "C#6:1 E6:1 A5:2",
  "F#5:.5 B5:.5 D6:1 F#6:1 D6:.5 B5:.5",
  "G6:1.5 F#6:.5 D6:1 B5:1",
  "A5:.5 B5:.5 D6:1 A5:1 F#5:1",
  "E5:.5 A5:.5 C#6:1 E6:2!",
  "G5:.5 B5:.5 E6:1 G6:1 E6:1",
  "D6:.5 G6:.5 B6:1 A6:.5 G6:.5 D6:1",
  "C#6:1 E6:.5 F#6:.5 E6:1 C#6:1",
  "G6:1 E6:1 C#6:1 A5:1",
  "B5:1 D6:1 G6:1.5 F#6:.5",
  "E6:1 C#6:1 A6:2",
  "A6:1 F#6:.5 E6:.5 C#6:1 A5:1",
  "B5:.5 C#6:.5 D6:1 F#6:1 B6:1",
  "B6:1.5 A6:.5 G6:1 D6:1",
  "C#6:.5 D6:.5 E6:1 A6:1 C#7:1",
  "D7:1.5 A6:.5 F#6:1 A6:1",
  "C7:1 A6:.5 F#6:.5 D6:2",
  "D6:.5 G6:.5 B6:1 D7:1 B6:1",
  "Bb6:1 G6:.5 Bb6:.5 D7:1 G6:1",
  "F#6:1 A6:.5 F#6:.5 D6:1 A5:1",
  "B5:.5 D6:.5 F#6:1 B6:1.5 r:.5",
  "G6:1 E6:.5 G6:.5 B6:1 E6:1",
  "C#7:1 B6:.5 A6:.5 E6:1 C#6:1",
  "D6:.5 F#6:.5 A6:1 D7:2!",
  "C#7:.5 A6:.5 E6:.5 C#6:.5 A5:1 r:1",
);
export const SUMMIT_CHORDS =
  "D:4 A:4 Bm:4 G:4 D:4 A:4 G:4 A7:4 " +
  "Bm:4 G:4 D:4 A:4 Em:4 G:4 A:4 A7:4 " +
  "G:4 A:4 F#m:4 Bm:4 G:4 A:4 D:4 D7:4 " +
  "G:4 Gm:4 D:4 Bm:4 Em:4 A:4 D:4 A7:4";

function summit(): Song {
  const ch = chart(SUMMIT_CHORDS);
  const mel = seq(SUMMIT_MELODY, 0, 0.86);
  const part1 = mel.filter((n) => n.t < 32);
  const part2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const part3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const part4 = mel.filter((n) => n.t >= 96);
  const upper = ch.filter((c) => c.t >= 64);
  // A bouncing, skipping bass: root, octave, fifth, and a push into the next bar.
  const skip: [number, number, string][] = [
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
    id: "summit",
    title: "Snowy Summit Pass",
    role: "Snowy Peaks",
    bpm: 152,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      // The tune: flute and xylophone, then brass, then strings and bells, then all.
      part("flute", "base", 0.95, part1),
      part("xylophone", "base", 0.5, part1),
      part("brass", "base", 0.85, part2),
      part("flute", "base", 0.45, part2),
      part("strings", "base", 1, part3),
      part("bell", "base", 0.4, part3),
      part("brass", "base", 0.8, part4),
      part("flute", "base", 0.6, part4),
      part("square", "base", 0.16, shift(part4, 0, 12)),
      // A running marimba under everything, bright pizzicato stabs, sparkling celesta.
      part("marimba", "base", 0.55, arpeggio(ch, 0.25, [0, 1, 2, 3, 2, 1, 2, 1], 62, 0.2, 0.5)),
      part("pizz", "base", 0.45, stabs(ch, [0.5, 1.5, 2.5, 3.5], 57, 0.2, 0.5)),
      part("celesta", "base", 0.35, arpeggio(upper, 1, [3, 2, 1, 2], 79, 0.6, 0.35)),
      // Pads: warm horns, then strings in the treetops.
      part("horn", "base", 0.35, pads(ch, 52, 4, 0.4)),
      part("strings", "base", 0.3, pads(upper, 60, 4, 0.4)),
      part("bass", "base", 1, bassLine(ch, skip, 33, 0.85)),
      // Bright, driving drums: kick, backbeat snare, shaker sixteenths, tambourine,
      // a tom fill at the end of every phrase and a crash at the top of each section.
      ...drumParts("base", 0.9, drums("K...k.K.K...k.k.", KIT, 0.25, 32)),
      ...drumParts("base", 0.75, drums("....S.......S...", KIT, 0.25, 32)),
      ...drumParts("base", 0.45, drums("hhHhhhHhhhHhhhHh", KIT, 0.25, 32)),
      ...drumParts("base", 0.4, drums("..t...t...t...tt", KIT, 0.25, 32)),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("base", 0.8, drums("o.o.O.o.OoOoOOOO", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.85, drums("C", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Hearthglow Hollow"
// A Christmas-village gallop: sleigh bells all the way, celesta and bells on the
// cobbled streets, a flute through the forest, strings and brass up the mountain, and
// everyone together down the sleigh run.

export const HEARTHGLOW_MELODY = bars(
  "D5:1 B4:.5 C5:.5 D5:1 G5:1",
  "E5:1 G5:1 B5:1.5 A5:.5",
  "G5:.5 E5:.5 C5:1 E5:1 G5:1",
  "F#5:1.5 E5:.5 D5:2",
  "B4:.5 D5:.5 G5:1 B5:1 G5:1",
  "B5:1 A5:.5 G5:.5 E5:1 G5:1",
  "C6:1 B5:.5 A5:.5 E5:1 A5:1",
  "A5:1 F#5:1 D5:1 C5:1",
  "E5:.5 G5:.5 C6:1 G5:1 E5:1",
  "F#5:.5 A5:.5 D6:1 A5:1 F#5:1",
  "D6:1 B5:.5 D6:.5 F#6:1 D6:1",
  "E6:1.5 D6:.5 B5:2",
  "C6:.5 D6:.5 E6:1 G6:1 E6:1",
  "F#6:1 E6:.5 D6:.5 A5:1 D6:1",
  "G6:1 D6:.5 B5:.5 G5:1 B5:1",
  "F5:1 G5:1 B5:1 D6:1",
  "E6:1.5 D6:.5 C6:1 G5:1",
  "Eb6:1.5 D6:.5 C6:1 G5:1",
  "D6:1 B5:.5 G5:.5 D5:1 G5:1",
  "G#5:1 B5:1 E6:1 D6:1",
  "C6:.5 B5:.5 A5:1 E5:1 A5:1",
  "D6:1 F#5:.5 A5:.5 D6:1 F#6:1",
  "G6:1.5 D6:.5 B5:2",
  "A5:1 C6:1 D6:1 F#6:1",
  "G6:.5 F#6:.5 G6:1 D6:1 B5:1",
  "D#6:1 F#6:1 B6:1 A6:1",
  "G6:1 E6:.5 G6:.5 B6:1 G6:1",
  "F6:1 D6:1 B5:1 G5:1",
  "E6:.5 G6:.5 C7:1 G6:1 E6:1",
  "F#6:.5 A6:.5 D7:1 C7:.5 A6:.5 F#6:1",
  "G6:2! D6:1 B5:1",
  "C6:.5 B5:.5 A5:.5 F#5:.5 D5:1 r:1",
);
export const HEARTHGLOW_CHORDS =
  "G:4 Em:4 C:4 D:4 G:4 Em:4 Am:4 D7:4 " +
  "C:4 D:4 Bm:4 Em:4 C:4 D:4 G:4 G7:4 " +
  "C:4 Cm:4 G:4 E7:4 Am:4 D:4 G:4 D7:4 " +
  "G:4 B7:4 Em:4 G7:4 C:4 D:4 G:4 D7:4";

function hearthglow(): Song {
  const ch = chart(HEARTHGLOW_CHORDS);
  const mel = seq(HEARTHGLOW_MELODY, 0, 0.84);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const late = ch.filter((c) => c.t >= 64);
  // An oom-pah walking bass: root, fifth, octave, a step into the next chord.
  const walk: [number, number, string][] = [
    [0, 1, "R"],
    [1, 1, "5"],
    [2, 1, "8"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "hearthglow",
    title: "Hearthglow Hollow",
    role: "Snowy Peaks",
    bpm: 160,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      // The tune: celesta and bells, then flute, then strings and brass, then all.
      part("celesta", "base", 1, p1),
      part("bell", "base", 0.45, p1),
      part("flute", "base", 0.95, p2),
      part("celesta", "base", 0.35, shift(p2, 0, 12)),
      part("strings", "base", 1, p3),
      part("brass", "base", 0.55, p3),
      part("brass", "base", 0.85, p4),
      part("flute", "base", 0.6, p4),
      part("bell", "base", 0.3, shift(p4, 0, 12)),
      // Plucked strings on the off-beats, a twinkling glockenspiel arpeggio, warm horns.
      part("pizz", "base", 0.55, stabs(ch, [0.5, 1.5, 2.5, 3.5], 57, 0.2, 0.5)),
      part("bell", "base", 0.3, arpeggio(ch, 0.5, [0, 1, 2, 3, 2, 1, 2, 3], 79, 0.3, 0.32)),
      part("horn", "base", 0.4, pads(ch, 52, 4, 0.42)),
      part("strings", "base", 0.3, pads(late, 60, 4, 0.4)),
      part("bass", "base", 1, bassLine(ch, walk, 31, 0.85)),
      // Sleigh bells (tambourine and shaker) all the way, a light kick and snare, a
      // woodblock clip-clop, and a crash at the top of each section.
      ...drumParts("base", 0.6, drums("tttTtttTtttTtttT", KIT, 0.25, 32)),
      ...drumParts("base", 0.35, drums("h.h.h.h.h.h.h.h.", KIT, 0.25, 32)),
      ...drumParts("base", 0.8, drums("K.......K.k.....", KIT, 0.25, 32)),
      ...drumParts("base", 0.65, drums("....S.......S...", KIT, 0.25, 32)),
      ...drumParts("base", 0.45, drums("w..w..w.w..w..w.", KIT, 0.25, 32)),
      ...drumParts("base", 0.85, drums("C", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Aurora Rift"
// Down into the glacier under the northern lights: a hushed celesta over shimmering
// crystal bells in the Cathedral, a flute and a running marimba across Mirror Lake,
// brass and strings soaring for the Loop and the climb, and everything together on the
// Great Rift Bridge.

export const AURORA_MELODY = bars(
  "C#5:1 F#5:.5 G#5:.5 A5:1 C#6:1",
  "B5:1.5 A5:.5 F#5:1 D5:1",
  "E5:.5 A5:.5 C#6:1 B5:1 A5:1",
  "G#5:1.5 F#5:.5 E5:2",
  "F#5:.5 A5:.5 C#6:1 F#6:1 E6:1",
  "D6:1 C#6:.5 B5:.5 A5:1 F#5:1",
  "B5:.5 D6:.5 F#6:1 E6:.5 D6:.5 B5:1",
  "F5:1 G#5:1 C#6:1.5 r:.5",
  "A5:.5 B5:.5 D6:1 F#6:1 D6:1",
  "E6:1 G#5:.5 B5:.5 E6:1 B5:1",
  "C#6:.5 E6:.5 G#6:1 E6:1 C#6:1",
  "A5:1 C#6:1 F#6:2!",
  "D6:.5 C#6:.5 B5:1 F#5:1 B5:1",
  "G#5:.5 B5:.5 E6:1 D6:.5 B5:.5 G#5:1",
  "A5:.5 C#6:.5 E6:1 A6:1 E6:1",
  "F6:1 E6:.5 C#6:.5 G#5:1 F5:1",
  "F#6:1.5 E6:.5 D6:1 A5:1",
  "G#6:1.5 F#6:.5 E6:1 B5:1",
  "A6:1 G#6:.5 F#6:.5 C#6:1 F#6:1",
  "E6:1 C#6:1 A5:1 C#6:1",
  "D6:.5 F#6:.5 B6:1 A6:.5 F#6:.5 D6:1",
  "A6:1 F#6:.5 D6:.5 A5:1 D6:1",
  "B6:1.5 A6:.5 G#6:1 E6:1",
  "D6:1 B5:1 G#5:1 E5:1",
  "C#6:.5 F#6:.5 A6:1 C#7:1 A6:1",
  "F#6:1 A6:.5 F#6:.5 D6:1 A5:1",
  "E6:.5 A6:.5 C#7:1 B6:.5 A6:.5 E6:1",
  "G#6:1 B6:1 E7:2!",
  "D7:1 B6:.5 F#6:.5 D6:1 B5:1",
  "E6:1 C#6:.5 G#5:.5 C#6:1 E6:1",
  "F#6:1 D6:1 G#6:1 E6:1",
  "F#6:2! C#6:1 r:1",
);
export const AURORA_CHORDS =
  "F#m:4 D:4 A:4 E:4 F#m:4 D:4 Bm:4 C#7:4 " +
  "D:4 E:4 C#m:4 F#m:4 Bm:4 E:4 A:4 C#7:4 " +
  "D:4 E:4 F#m:4 A:4 Bm:4 D:4 E:4 E7:4 " +
  "F#m:4 D:4 A:4 E:4 Bm:4 C#m:4 D:2 E:2 F#m:4";

function aurora(): Song {
  const ch = chart(AURORA_CHORDS);
  const mel = seq(AURORA_MELODY, 0, 0.82);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const later = ch.filter((c) => c.t >= 32);
  const soar = ch.filter((c) => c.t >= 64);
  // A pulsing bass: eighths on the root, the octave on the off-beats, a step in.
  const pulse: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.5, "8"],
    [1, 0.5, "R"],
    [1.5, 0.5, "8"],
    [2, 0.5, "R"],
    [2.5, 0.5, "5"],
    [3, 0.5, "8"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "aurora",
    title: "Aurora Rift",
    role: "Snowy Peaks",
    bpm: 148,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      // The tune: celesta in the Cathedral, the flute on the lake, brass and strings
      // for the Loop and the climb, and all of them on the bridge.
      part("celesta", "base", 1, p1),
      part("bell", "base", 0.35, shift(p1, 0, -12)),
      part("flute", "base", 1, p2),
      part("celesta", "base", 0.3, shift(p2, 0, 12)),
      part("brass", "base", 0.8, p3),
      part("strings", "base", 0.9, p3),
      part("strings", "base", 1, p4),
      part("flute", "base", 0.6, p4),
      part("brass", "base", 0.45, shift(p4, 0, -12)),
      part("bell", "base", 0.3, shift(p4, 0, 12)),
      // Crystal shimmer all the way: bells running up and down the chord.
      part("bell", "base", 0.22, arpeggio(ch, 0.25, [0, 1, 2, 3, 2, 1, 2, 3], 76, 0.2, 0.26)),
      // A running marimba from the lake on, plucked strings on the off-beats.
      part("marimba", "base", 0.5, arpeggio(later, 0.5, [0, 2, 1, 2, 3, 2, 1, 2], 57, 0.3, 0.5)),
      part("pizz", "base", 0.45, stabs(later, [0.5, 1.5, 2.5, 3.5], 57, 0.2, 0.45)),
      // Pads: a cold drone and strings, horns swelling under the soaring half.
      part("pad", "base", 0.5, pads(ch, 54, 4, 0.42)),
      part("drone", "base", 0.25, pads(ch, 42, 4, 0.3)),
      part("horn", "base", 0.35, pads(soar, 52, 4, 0.45)),
      part("bass", "base", 0.95, bassLine(ch, pulse, 30, 0.8)),
      // Drums: a hushed pulse in the Cathedral, then the full kit; a crash on each
      // section, a tom fill into the Loop.
      ...drumParts("base", 0.7, drums("K.......K.......", KIT, 0.25, 8)),
      ...drumParts("base", 0.4, drums("h.h.h.h.h.h.h.h.", KIT, 0.25, 32)),
      ...drumParts("base", 0.85, drums("K.....k.K..k....", KIT, 0.25, 24, 32)),
      ...drumParts("base", 0.65, drums("....S.......S...", KIT, 0.25, 24, 32)),
      ...drumParts("base", 0.4, drums("..t...t...t...t.", KIT, 0.25, 24, 32)),
      ...[60, 92, 124].flatMap((at) =>
        drumParts("base", 0.75, drums("o.o.O.o.OoOoOOOO", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.85, drums("C", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Canyon Dash"

export const CANYON_MELODY = bars(
  "D5:.5 E5:.5 F5:1 A5:1 D6:1",
  "C#6:.5 D6:.5 A5:1 F5:1 D5:1",
  "F5:.5 G5:.5 Bb5:1 D6:.5 C6:.5 Bb5:1",
  "E5:1 C#5:.5 E5:.5 A5:2",
  "A5:.5 G5:.5 F5:1 E5:.5 F5:.5 D5:1",
  "Bb5:1 G5:.5 Bb5:.5 D6:1 C6:1",
  "C#6:.5 E6:.5 G6:1 F6:.5 E6:.5 C#6:1",
  "D6:2! A5:1 r:1",
  "C6:.5 A5:.5 F5:1 A5:1 C6:1",
  "E6:1 D6:.5 C6:.5 G5:1 E5:1",
  "F5:.5 A5:.5 D6:1 F6:1 D6:1",
  "E6:1.5 C#6:.5 A5:2",
  "D6:.5 F6:.5 Bb6:1 A6:.5 G6:.5 F6:1",
  "A6:1 F6:.5 C6:.5 A5:1 C6:1",
  "Bb5:.5 D6:.5 G6:1 F6:.5 D6:.5 Bb5:1",
  "A5:1 C#6:1 E6:1 G6:1",
  "F6:1 E6:.5 D6:.5 A5:1 F5:1",
  "Bb5:1 D6:.5 F6:.5 Bb6:2",
  "A6:.5 G6:.5 F6:1 C6:1 A5:1",
  "G5:.5 C6:.5 E6:1 G6:1 E6:1",
  "D6:1 Bb5:.5 D6:.5 G6:1 Bb6:1",
  "A6:1.5 F6:.5 D6:2",
  "F6:.5 E6:.5 D6:1 Bb5:1 D6:1",
  "C#6:1 E6:1 A6:1.5 r:.5",
  "D6:.5 E6:.5 F6:1 A6:1 F6:1",
  "G6:.5 A6:.5 Bb6:1 D7:1 Bb6:1",
  "C7:1 G6:.5 E6:.5 C6:1 E6:1",
  "F6:1.5 A6:.5 C7:2!",
  "D7:1 Bb6:.5 F6:.5 D6:1 F6:1",
  "G6:1 D6:.5 Bb5:.5 G5:1 Bb5:1",
  "A5:.5 C#6:.5 E6:.5 G6:.5 A6:1 C#7:1",
  "D7:2! A6:1 r:1",
);
export const CANYON_CHORDS =
  "Dm:4 Dm:4 Bb:4 A:4 Dm:4 Gm:4 A7:4 Dm:4 " +
  "F:4 C:4 Dm:4 A:4 Bb:4 F:4 Gm:4 A7:4 " +
  "Dm:4 Bb:4 F:4 C:4 Gm:4 Dm:4 Bb:4 A7:4 " +
  "Dm:4 Gm:4 C:4 F:4 Bb:4 Gm:4 A7:4 Dm:4";

function canyon(): Song {
  const ch = chart(CANYON_CHORDS);
  const mel = seq(CANYON_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const later = ch.filter((c) => c.t >= 32);
  // A galloping bass: root, a skip to the fifth, the octave, a walk into the next bar.
  const gallop: [number, number, string][] = [
    [0, 0.75, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "5"],
    [1.5, 0.5, "8"],
    [2, 0.75, "R"],
    [2.75, 0.25, "R"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "canyon",
    title: "Canyon Dash",
    role: "Desert World",
    bpm: 168,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      // The tune: brass down the canyon wall, the flute over the bridge, strings and
      // brass by the falls, everyone on the mesa.
      part("brass", "base", 0.85, p1),
      part("marimba", "base", 0.35, shift(p1, 0, -12)),
      part("flute", "base", 1, p2),
      part("xylophone", "base", 0.4, p2),
      part("strings", "base", 0.95, p3),
      part("brass", "base", 0.45, shift(p3, 0, -12)),
      part("brass", "base", 0.85, p4),
      part("flute", "base", 0.6, p4),
      part("strings", "base", 0.5, shift(p4, 0, -12)),
      // Strummed pizzicato on the off-beats, a rolling marimba from the bridge on.
      part("pizz", "base", 0.55, stabs(ch, [0.5, 1, 1.5, 2.5, 3, 3.5], 57, 0.15, 0.5)),
      part("marimba", "base", 0.45, arpeggio(later, 0.5, [0, 1, 2, 1, 3, 2, 1, 2], 62, 0.25, 0.45)),
      part("horn", "base", 0.35, pads(ch, 50, 4, 0.4)),
      part("bass", "base", 1, bassLine(ch, gallop, 33, 0.85)),
      // The gallop: woodblock hooves throughout, bongos, a driving kick and snare, a
      // tambourine shake, tom fills and crashes at the top of each section.
      ...drumParts("base", 0.55, drums("w..ww..ww..ww..w", KIT, 0.25, 32)),
      ...drumParts("base", 0.85, drums("K.......K.k.....", KIT, 0.25, 32)),
      ...drumParts("base", 0.7, drums("....S.......S...", KIT, 0.25, 32)),
      ...drumParts("base", 0.4, drums("b.b.bb.bb.b.bb.b", KIT, 0.25, 24, 32)),
      ...drumParts("base", 0.35, drums("..t...t...t...tt", KIT, 0.25, 32)),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("base", 0.8, drums("o.o.O.o.OoOoOOOO", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.85, drums("C", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Oasis Haven"

export const OASIS_MELODY = bars(
  "E5:.5 A5:.5 C#6:1 B5:.5 A5:.5 E5:1",
  "F#5:.5 A5:.5 D6:1 C#6:1 A5:1",
  "B5:.5 C#6:.5 D6:1 B5:.5 G#5:.5 E5:1",
  "A5:1 C#6:1 E6:2",
  "E6:.5 D6:.5 C#6:1 A5:.5 B5:.5 C#6:1",
  "D6:1 F#6:.5 E6:.5 D6:1 B5:1",
  "C#6:.5 E6:.5 A6:1 G#6:.5 F#6:.5 E6:1",
  "D6:1 B5:1 C#6:2!",
  "A5:.5 B5:.5 C#6:.5 E6:.5 F#6:1 E6:1",
  "D6:.5 C#6:.5 B5:1 G#5:1 E5:1",
  "F#5:.5 A5:.5 C#6:1 F#6:1 E6:1",
  "D6:1 C#6:.5 B5:.5 A5:2",
  "B5:.5 D6:.5 F#6:1 A6:1 F#6:1",
  "E6:1 C#6:.5 E6:.5 A6:1 E6:1",
  "D6:.5 E6:.5 F#6:1 E6:.5 D6:.5 B5:1",
  "G#5:1 B5:1 E6:1.5 r:.5",
  "A6:1 G#6:.5 F#6:.5 E6:1 C#6:1",
  "D6:1 F#6:1 A6:2",
  "G#6:.5 F#6:.5 E6:1 B5:1 E6:1",
  "C#6:1 E6:1 A6:1.5 r:.5",
  "F#6:.5 E6:.5 D6:1 A5:1 D6:1",
  "C#6:.5 D6:.5 E6:1 A5:1 C#6:1",
  "B5:.5 C#6:.5 D6:1 F#6:1 B6:1",
  "G#6:1 E6:1 B5:2",
  "A5:.5 C#6:.5 E6:.5 A6:.5 C#7:1 A6:1",
  "B6:1 G#6:.5 E6:.5 B5:1 E6:1",
  "F#6:.5 A6:.5 D7:1 C#7:.5 B6:.5 A6:1",
  "E6:1.5 F#6:.5 G#6:2",
  "A6:1 E6:.5 C#6:.5 A5:1 C#6:1",
  "D6:1 F#6:1 B6:1 A6:1",
  "G#6:.5 B6:.5 E7:1 D7:.5 B6:.5 G#6:1",
  "A6:2! E6:1 r:1",
);
export const OASIS_CHORDS =
  "A:4 D:4 E:4 A:4 F#m:4 D:4 A:4 E:4 " +
  "A:4 E:4 F#m:4 D:4 Bm:4 A:4 Bm:4 E7:4 " +
  "F#m:4 D:4 E:4 A:4 D:4 A:4 Bm:4 E:4 " +
  "A:4 E:4 D:4 E:4 F#m:4 D:4 E7:4 A:4";

function oasis(): Song {
  const ch = chart(OASIS_CHORDS);
  const mel = seq(OASIS_MELODY, 0, 0.82);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  // A bouncy bass: root, a skip up to the fifth, the octave, a walk in.
  const bounce: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "5"],
    [1.5, 0.5, "8"],
    [2, 0.5, "R"],
    [2.75, 0.25, "5"],
    [3, 0.5, "8"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "oasis",
    title: "Oasis Haven",
    role: "Desert World",
    bpm: 150,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      // The tune: steel pan on the promenade, the flute through the market, strings
      // over the falls, and all of them for the palace.
      part("steelpan", "base", 1, p1),
      part("marimba", "base", 0.35, shift(p1, 0, -12)),
      part("flute", "base", 1, p2),
      part("steelpan", "base", 0.4, shift(p2, 0, -12)),
      part("strings", "base", 0.95, p3),
      part("bell", "base", 0.3, shift(p3, 0, 12)),
      part("steelpan", "base", 0.9, p4),
      part("flute", "base", 0.6, p4),
      part("brass", "base", 0.4, shift(p4, 0, -12)),
      // Sparkling water: marimba and bells running up and down the chords.
      part("marimba", "base", 0.5, arpeggio(ch, 0.25, [0, 1, 2, 3, 2, 1, 2, 3], 64, 0.2, 0.42)),
      part("bell", "base", 0.18, arpeggio(ch, 0.5, [3, 2, 1, 2], 79, 0.3, 0.3)),
      part("pizz", "base", 0.45, stabs(ch, [0.5, 1.5, 2.5, 3.5], 57, 0.15, 0.45)),
      part("pad", "base", 0.4, pads(ch, 55, 4, 0.4)),
      part(
        "horn",
        "base",
        0.3,
        pads(
          ch.filter((c) => c.t >= 96),
          52,
          4,
          0.4,
        ),
      ),
      part("bass", "base", 1, bassLine(ch, bounce, 33, 0.85)),
      // A light holiday groove: kick, rimshot snare, shaker, congas (bongos), tambourine.
      ...drumParts("base", 0.85, drums("K.....k.K.......", KIT, 0.25, 32)),
      ...drumParts("base", 0.6, drums("....S.......S...", KIT, 0.25, 32)),
      ...drumParts("base", 0.45, drums("hhHhhhHhhhHhhhHh", KIT, 0.25, 32)),
      ...drumParts("base", 0.5, drums("..b.bb.b..b.b.bb", KIT, 0.25, 32)),
      ...drumParts("base", 0.35, drums("..t...t...t...t.", KIT, 0.25, 24, 32)),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("base", 0.7, drums("o.o.O.o.OoOoOOOO", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.8, drums("C", KIT, 32, 4)),
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

// ---------------------------------------------------------------- "Ember Peak (Classic)"

export const EMBER_CLASSIC_MELODY = bars(
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
export const EMBER_CLASSIC_CHORDS =
  "Am:4 Am:4 F:4 E:4 Am:4 Am:4 Dm:4 E:4 F:4 G:4 Am:4 Em:4 F:4 G:4 E:4 E7:4";

function emberClassic(): Song {
  const ch = chart(EMBER_CLASSIC_CHORDS);
  const mel = seq(EMBER_CLASSIC_MELODY, 0, 0.85);
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
    id: "ember_classic",
    title: "Ember Peak (Classic)",
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

// ---------------------------------------------------------------- "Ember Peak"

// The Volcanic Apocalypse: D minor, 160. A relentless first half (low brass carrying
// the tune over a hammering marimba and heavy toms), then a triumphant second half
// (strings and brass together, soaring) as you escape the eruption.
export const EMBER_MELODY = bars(
  "D5:.5 D5:.5 F5:.5 A5:.5 D6:1 A5:1",
  "C6:.5 A5:.5 F5:.5 A5:.5 D5:2",
  "Bb5:.5 A5:.5 F5:.5 D5:.5 Bb4:1 D5:1",
  "C5:.5 E5:.5 G5:1 E5:1 C5:1",
  "D5:.5 F5:.5 A5:1 D6:.5 C6:.5 A5:1",
  "F5:.5 A5:.5 D6:1 F6:1 D6:1",
  "G5:.5 Bb5:.5 D6:1 Bb5:.5 G5:.5 D5:1",
  "C#5:.5 E5:.5 A5:1 C#6:2",
  "D6:1 A5:.5 F5:.5 D5:1 F5:1",
  "Bb5:1 F5:.5 D5:.5 Bb4:1 D5:1",
  "A5:.5 C6:.5 F6:1 C6:1 A5:1",
  "G5:.5 E5:.5 C5:1 E5:1 G5:1",
  "Bb5:.5 G5:.5 D5:1 G5:1 Bb5:1",
  "A5:.5 C#6:.5 E6:1 C#6:1 A5:1",
  "D6:.5 F6:.5 A6:1 F6:.5 D6:.5 A5:1",
  "E5:.5 G5:.5 C#6:1 A5:2",
  "F5:1 Bb5:.5 D6:.5 F6:1 D6:1",
  "E6:1 C6:.5 G5:.5 E5:1 G5:1",
  "F5:.5 A5:.5 C6:1 F6:1.5 r:.5",
  "D6:.5 C6:.5 A5:1 F5:1 D5:1",
  "Bb5:.5 D6:.5 F6:1 D6:.5 Bb5:.5 F5:1",
  "C6:.5 E6:.5 G6:1 E6:1 C6:1",
  "C#6:1 E6:.5 A6:.5 E6:1 C#6:1",
  "A5:.5 C#6:.5 E6:.5 G6:.5 A6:2",
  "G6:.5 F6:.5 D6:1 Bb5:1 G5:1",
  "Bb5:.5 D6:.5 F6:1 Bb6:1 F6:1",
  "A6:1 F6:.5 C6:.5 A5:1 C6:1",
  "G6:.5 E6:.5 C6:1 G5:1 E5:1",
  "D6:.5 Bb5:.5 G5:1 Bb5:1 D6:1",
  "C#6:.5 E6:.5 A6:1 E6:1 C#6:1",
  "D6:1 A5:.5 F5:.5 D5:1 A5:1",
  "D6:3 r:1",
);
export const EMBER_CHORDS =
  "Dm:4 Dm:4 Bb:4 C:4 Dm:4 Dm:4 Gm:4 A:4 Dm:4 Bb:4 F:4 C:4 Gm:4 A:4 Dm:4 A7:4 " +
  "Bb:4 C:4 F:4 Dm:4 Bb:4 C:4 A:4 A7:4 Gm:4 Bb:4 F:4 C:4 Gm:4 A:4 Dm:4 Dm:4";

function ember(): Song {
  const ch = chart(EMBER_CHORDS);
  const mel = seq(EMBER_MELODY, 0, 0.88);
  const a = mel.filter((n) => n.t < 64);
  const b = mel.filter((n) => n.t >= 64);
  const first = ch.filter((c) => c.t < 64);
  const second = ch.filter((c) => c.t >= 64);
  // A galloping bass, digging in on every beat.
  const gallop: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.25, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "8"],
    [1.5, 0.5, "R"],
    [2, 0.5, "5"],
    [2.5, 0.25, "R"],
    [2.75, 0.25, "R"],
    [3, 0.5, "8"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "ember",
    title: "Ember Peak",
    role: "Prehistoric World",
    bpm: 160,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      // The tune: low brass and horns in the first half; strings and brass soaring
      // together in the second, with square-wave sparks an octave up.
      part("brass", "base", 0.95, a),
      part("horn", "base", 0.55, shift(a, 0, -12)),
      part("strings", "base", 1, b),
      part("brass", "base", 0.6, b),
      part("square", "base", 0.2, shift(b, 0, 12)),
      // The hammering marimba, and fast string stabs pushing every bar.
      part("marimba", "base", 0.6, arpeggio(ch, 0.25, [0, 1, 2, 1, 3, 2, 1, 2], 57, 0.2, 0.55)),
      part("pizz", "base", 0.5, stabs(first, [0, 0.75, 1.5, 2.5, 3], 50, 0.25, 0.6)),
      part("strings", "base", 0.35, pads(first, 50, 4, 0.4)),
      part("horn", "base", 0.5, stabs(second, [0, 1.5, 3], 45, 0.4, 0.6)),
      part("square", "base", 0.16, stabs(second, [0.75, 2.75], 69, 0.15, 0.5)),
      part("drone", "base", 0.3, pads(first, 38, 8, 0.5)),
      part("bass", "base", 1.1, bassLine(ch, gallop, 33, 0.92)),
      // Heavy drums: kick and snare, a storm of toms at the end of every phrase, hats.
      ...drumParts("base", 1, drums("K.k.K.k.K.k.K.kk", KIT, 0.25, 32)),
      ...drumParts("base", 0.85, drums("....S.......S.S.", KIT, 0.25, 32)),
      ...drumParts("base", 0.5, drums("iiIiiiIiiiIiiiIi", KIT, 0.25, 32)),
      ...[12, 28, 44, 60, 76, 92, 108, 124].flatMap((at) =>
        drumParts("base", 0.9, drums("O.o.O.o.OoOoOOOO", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.8, drums("..o...o...o..ooo", KIT, 0.25, 16, 64)),
      ...drumParts("base", 0.9, drums("C", KIT, 16, 8)),
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
// ---------------------------------------------------------------- "Dry Gulch"

export const GHOST_MELODY = bars(
  "E5:1 B4:.5 E5:.5 G5:1 F#5:1",
  "E5:.5 D5:.5 B4:1 r:1 B4:1",
  "C5:1 E5:.5 A5:.5 G5:1 E5:1",
  "F#5:2 D#5:1 B4:1",
  "E5:1 B4:.5 E5:.5 G5:1 B5:1",
  "A5:.5 G5:.5 F#5:1 E5:1 C5:1",
  "B4:1 D#5:1 F#5:1 A5:1",
  "G5:1 F#5:1 E5:2",
  "B5:1.5 A5:.5 G5:1 E5:1",
  "C6:1.5 B5:.5 A5:1 E5:1",
  "D5:1 G5:1 B5:1 D6:1",
  "C6:1 B5:1 A5:2",
  "G5:1.5 F#5:.5 E5:1 C5:1",
  "A5:1 G5:.5 F#5:.5 E5:1 D#5:1",
  "E5:1 F#5:1 G5:1 A5:1",
  "B5:3 r:1",
  "E5:.5 F5:.5 E5:.5 D#5:.5 E5:2",
  "G5:.5 G#5:.5 G5:.5 F#5:.5 G5:2",
  "A5:1 C6:1 B5:1 G5:1",
  "F#5:1 A5:1 D#5:2",
  "E5:.5 F5:.5 E5:.5 D#5:.5 E5:1 B4:1",
  "C5:1 E5:1 A5:1 C6:1",
  "B5:1 A5:1 F#5:1 D#5:1",
  "E5:2 r:2",
  "E5:1 B4:.5 E5:.5 G5:1 F#5:1",
  "E5:.5 D5:.5 B4:1 E5:1 G5:1",
  "C6:1 B5:.5 A5:.5 G5:1 E5:1",
  "F#5:2 B5:2",
  "E6:1 D6:.5 B5:.5 G5:1 E5:1",
  "A5:1 C6:1 B5:1 A5:1",
  "G5:.5 F#5:.5 E5:1 D#5:1 F#5:1",
  "E5:3! r:1",
);
export const GHOST_CHORDS =
  "Em:4 Em:4 Am:4 B7:4 Em:4 Am:4 B7:4 Em:4 " +
  "Em:4 Am:4 G:4 Am:4 Em:4 B7:4 C:4 B7:4 " +
  "Em:4 C:4 Am:4 B7:4 Em:4 Am:4 B7:4 Em:4 " +
  "Em:4 Em:4 Am:4 B7:4 Em:4 Am:4 B7:4 Em:4";

/**
 * "Dry Gulch": a haunted frontier ballad in E minor, 132 BPM. A lonesome whistle (the
 * pan flute) carries the tune down Main Street over a plucked, strummed guitar (the
 * pizzicato) and a galloping bass; eerie strings and a music-box celesta come in by the
 * graveyard; in the mine the celesta and a low clarinet creep round a chromatic turn
 * over a deep drone; the whistle returns for the ride home. Woodblock hooves, a
 * slow kick, a rimshot and the odd tambourine shake. Our own tune.
 */
function ghost(): Song {
  const ch = chart(GHOST_CHORDS);
  const mel = seq(GHOST_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const gallop: [number, number, string][] = [
    [0, 0.75, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "5"],
    [2, 0.75, "R"],
    [2.75, 0.25, "R"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "ghost",
    title: "Dry Gulch",
    role: "Desert World",
    bpm: 132,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      part("panflute", "base", 1, p1),
      part("pizz", "base", 0.3, shift(p1, 0, -12)),
      part("strings", "base", 0.95, p2),
      part("celesta", "base", 0.35, shift(p2, 0, 12)),
      part("celesta", "base", 0.9, p3),
      part("clarinet", "base", 0.5, shift(p3, 0, -12)),
      part("panflute", "base", 0.95, p4),
      part("strings", "base", 0.5, p4),
      part("brass", "base", 0.3, shift(p4, 0, -12)),
      // The strummed guitar, a music box turning, the drone underneath.
      part("pizz", "base", 0.55, stabs(ch, [0, 1.5, 2, 3.5], 52, 0.2, 0.5)),
      part("celesta", "base", 0.28, arpeggio(ch, 0.5, [0, 1, 2, 1, 3, 2, 1, 2], 67, 0.3, 0.3)),
      part("drone", "base", 0.35, pads(ch, 40, 4, 0.5)),
      part(
        "pad",
        "base",
        0.3,
        pads(
          ch.filter((c) => c.t >= 32),
          55,
          4,
          0.4,
        ),
      ),
      part("bass", "base", 1, bassLine(ch, gallop, 28, 0.85)),
      ...drumParts("base", 0.6, drums("w..w.ww.w..w.ww.", KIT, 0.25, 32)),
      ...drumParts("base", 0.8, drums("K.......K.......", KIT, 0.25, 32)),
      ...drumParts("base", 0.55, drums("....S.......S...", KIT, 0.25, 32)),
      ...drumParts("base", 0.3, drums("..............t.", KIT, 0.25, 32)),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("base", 0.7, drums("o...o...o.o.oOoO", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.7, drums("C", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Impact Depths"

export const DEPTHS_MELODY = bars(
  "D5:1 A4:.5 D5:.5 F5:1 E5:1",
  "D5:.5 C5:.5 A4:1 r:1 A4:1",
  "Bb4:1 D5:.5 F5:.5 G5:1 F5:1",
  "E5:2 C#5:1 A4:1",
  "D5:1 A4:.5 D5:.5 F5:1 A5:1",
  "G5:.5 F5:.5 E5:1 D5:1 Bb4:1",
  "A4:1 C#5:1 E5:1 G5:1",
  "F5:1 E5:1 D5:2",
  "A5:1.5 G5:.5 F5:1 D5:1",
  "Bb5:1.5 A5:.5 G5:1 D5:1",
  "C5:1 F5:1 A5:1 C6:1",
  "Bb5:1 A5:1 G5:2",
  "F5:1.5 E5:.5 D5:1 Bb4:1",
  "G5:1 F5:.5 E5:.5 D5:1 C#5:1",
  "D5:1 E5:1 F5:1 G5:1",
  "A5:3 r:1",
  "D4:.5 E4:.5 D4:.5 C#4:.5 D4:2",
  "F4:.5 G4:.5 F4:.5 E4:.5 F4:2",
  "G4:1 Bb4:1 A4:1 F4:1",
  "E4:1 G4:1 C#4:2",
  "D4:.5 E4:.5 D4:.5 C#4:.5 D4:1 A3:1",
  "Bb3:1 D4:1 G4:1 Bb4:1",
  "A4:1 G4:1 E4:1 C#4:1",
  "D4:2 r:2",
  "D5:1 A4:.5 D5:.5 F5:1 E5:1",
  "D5:.5 C5:.5 A4:1 D5:1 F5:1",
  "Bb5:1 A5:.5 G5:.5 F5:1 D5:1",
  "E5:2 A5:2",
  "D6:1 C6:.5 A5:.5 F5:1 D5:1",
  "G5:1 Bb5:1 A5:1 G5:1",
  "F5:.5 E5:.5 D5:1 C#5:1 E5:1",
  "D5:3! r:1",
);
export const DEPTHS_CHORDS =
  "Dm:4 Dm:4 Bb:4 A7:4 Dm:4 Gm:4 A7:4 Dm:4 " +
  "Dm:4 Gm:4 F:4 C:4 Bb:4 Gm:4 Bb:4 A:4 " +
  "Dm:4 Bb:4 Gm:4 A7:4 Dm:4 Bb:4 A7:4 Dm:4 " +
  "Dm:4 Dm:4 Bb:4 A:4 Bb:4 Gm:4 A7:4 Dm:4";

/**
 * "Impact Depths": an expedition going down, D minor, 140 BPM. Bold brass and flute
 * carry the adventure theme over the desert; celesta and bells ring through the crystal
 * halls; down in the Lost World and the lava, a low marimba and horns creep round a
 * chromatic figure over pounding toms; then strings and brass climb the theme back up
 * into the sun. Our own tune.
 */
function depths(): Song {
  const ch = chart(DEPTHS_CHORDS);
  const mel = seq(DEPTHS_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const drive: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.5, "R"],
    [1, 0.5, "5"],
    [1.5, 0.5, "R"],
    [2, 0.5, "R"],
    [2.5, 0.5, "R"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "depths",
    title: "Impact Depths",
    role: "Desert World",
    bpm: 140,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      part("brass", "base", 0.9, p1),
      part("flute", "base", 0.6, shift(p1, 0, 12)),
      part("celesta", "base", 0.95, p2),
      part("bell", "base", 0.35, p2),
      part("marimba", "base", 1, shift(p3, 0, 12)),
      part("horn", "base", 0.8, p3),
      part("strings", "base", 1, p4),
      part("brass", "base", 0.55, shift(p4, 0, -12)),
      part("flute", "base", 0.4, shift(p4, 0, 12)),
      // Plucked strings on the off-beats; crystal arpeggios in the halls; a pad and
      // the drone in the deep; the driving bass.
      part("pizz", "base", 0.5, stabs(ch, [0.5, 1.5, 2.5, 3.5], 57, 0.2, 0.5)),
      part(
        "celesta",
        "base",
        0.3,
        arpeggio(
          ch.filter((c) => c.t >= 32 && c.t < 64),
          0.25,
          [0, 1, 2, 3, 2, 1, 2, 3],
          72,
          0.2,
          0.3,
        ),
      ),
      part(
        "marimba",
        "base",
        0.45,
        arpeggio(
          ch.filter((c) => c.t < 32 || c.t >= 96),
          0.5,
          [0, 2, 1, 2, 0, 2, 1, 3],
          62,
          0.3,
          0.35,
        ),
      ),
      part(
        "drone",
        "base",
        0.4,
        pads(
          ch.filter((c) => c.t >= 64 && c.t < 96),
          38,
          4,
          0.5,
        ),
      ),
      part("pad", "base", 0.35, pads(ch, 55, 4, 0.4)),
      part("bass", "base", 1, bassLine(ch, drive, 26, 0.85)),
      ...drumParts("base", 0.8, drums("k.......k.k.....", KIT, 0.25, 32)),
      ...drumParts("base", 0.6, drums("....s.......s...", KIT, 0.25, 32)),
      ...drumParts("base", 0.35, drums("i.i.i.i.i.i.i.ii", KIT, 0.25, 32)),
      ...[64, 72, 80, 88].flatMap((at) =>
        drumParts("base", 0.8, drums("o..o..o.o..o.oOo", KIT, 0.25, 2, at)),
      ),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("base", 0.7, drums("o.o.o.o.oooooooo", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.7, drums("c", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Dragon Isles"

export const DRAGON_MELODY = bars(
  // The festival (flute)
  "G5:.5 A5:.5 B5:1 D6:1 B5:.5 A5:.5",
  "G5:1 E5:.5 G5:.5 A5:2",
  "B5:.5 D6:.5 E6:1 D6:.5 B5:.5 A5:1",
  "G5:.5 A5:.5 B5:.5 A5:.5 G5:1 E5:1",
  "D5:.5 E5:.5 G5:1 A5:1 B5:.5 D6:.5",
  "E6:1.5 D6:.5 B5:1 A5:1",
  "G5:.5 A5:.5 B5:.5 D6:.5 A5:1 B5:.5 A5:.5",
  "G5:3 r:1",
  // The market (plucked strings and xylophone)
  "D6:.5 D6:.5 B5:.5 D6:.5 E6:1 D6:1",
  "B5:.5 A5:.5 G5:.5 A5:.5 B5:2",
  "A5:.5 A5:.5 G5:.5 A5:.5 B5:1 D6:1",
  "E6:.5 D6:.5 B5:.5 A5:.5 G5:2",
  "G5:.5 B5:.5 D6:.5 E6:.5 G6:1 E6:1",
  "D6:.5 E6:.5 D6:.5 B5:.5 A5:2",
  "B5:.5 A5:.5 G5:.5 E5:.5 D5:1 E5:1",
  "G5:2 A5:1 B5:1",
  // The dragon (bells and celesta, broad)
  "D6:2 B5:1 A5:1",
  "G5:1 A5:1 B5:2",
  "E6:2 D6:1 B5:1",
  "A5:3 r:1",
  "G5:1 B5:1 D6:1 E6:1",
  "G6:2 E6:1 D6:1",
  "B5:1 D6:.5 B5:.5 A5:1 G5:1",
  "A5:3 r:1",
  // The palace (brass and flute)
  "G5:.5 A5:.5 B5:1 D6:1 E6:1",
  "D6:.5 B5:.5 A5:1 G5:2",
  "E5:.5 G5:.5 A5:1 B5:1 D6:1",
  "B5:.5 A5:.5 G5:1 A5:2",
  "G5:.5 A5:.5 B5:1 D6:1 G6:1",
  "E6:.5 D6:.5 B5:1 D6:2",
  "E6:.5 D6:.5 B5:.5 A5:.5 G5:.5 A5:.5 B5:1",
  "G5:3! r:1",
);
export const DRAGON_CHORDS =
  "G:4 Em:4 C:4 D:4 G:4 Em:4 C:2 D:2 G:4 " +
  "G:4 D:4 Am:4 Em:4 C:4 D:4 Em:2 D:2 G:4 " +
  "Em:4 C:4 G:4 D:4 Em:4 C:4 Am:2 D:2 D:4 " +
  "G:4 Em:4 C:4 D:4 G:4 C:4 Am:2 D:2 G:4";

/**
 * "Dragon Isles": a festival lap of the dragon kingdom, G major pentatonic, 152 BPM.
 * A bamboo flute leads through the festival over plucked strings; the market skips
 * along on plucked strings and xylophone; bells and celesta sing the great dragon's
 * broad theme over held strings; brass and flute bring it home to the palace. Festival
 * drums, bongos and a gong-like crash throughout. Our own tune.
 */
function dragon(): Song {
  const ch = chart(DRAGON_CHORDS);
  const mel = seq(DRAGON_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const skip: [number, number, string][] = [
    [0, 1, "R"],
    [1, 0.5, "5"],
    [1.5, 0.5, "R"],
    [2, 1, "5"],
    [3, 0.5, "8"],
    [3.5, 0.5, "5"],
  ];
  return {
    id: "dragon",
    title: "Dragonspire Keep",
    role: "Dragon Kingdom",
    bpm: 152,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      part("flute", "base", 1, p1),
      part("pizz", "base", 0.9, p2),
      part("xylophone", "base", 0.6, shift(p2, 0, 12)),
      part("bell", "base", 0.55, p3),
      part("celesta", "base", 0.9, p3),
      part(
        "strings",
        "base",
        0.5,
        pads(
          ch.filter((c) => c.t >= 64 && c.t < 96),
          55,
          4,
          0.45,
        ),
      ),
      part("brass", "base", 0.85, p4),
      part("flute", "base", 0.5, shift(p4, 0, 12)),
      // Plucked strings rippling under it all; mallets on the off-beats; the bass.
      part(
        "pizz",
        "base",
        0.45,
        arpeggio(
          ch.filter((c) => c.t < 32 || c.t >= 64),
          0.5,
          [0, 1, 2, 1, 0, 2, 1, 2],
          62,
          0.3,
          0.4,
        ),
      ),
      part("marimba", "base", 0.6, stabs(ch, [0.5, 1.5, 2.5, 3.5], 60, 0.2, 0.45)),
      part("pad", "base", 0.3, pads(ch, 55, 4, 0.35)),
      part("bass", "base", 1, bassLine(ch, skip, 31, 0.8)),
      ...drumParts("base", 0.75, drums("o...o.o.o...o.oo", KIT, 0.25, 32)),
      ...drumParts("base", 0.5, drums("..b...b...b.b.b.", KIT, 0.25, 32)),
      ...drumParts("base", 0.35, drums("h.h.h.h.h.h.h.hh", KIT, 0.25, 32)),
      ...drumParts("base", 0.5, drums("k.......k.......", KIT, 0.25, 32)),
      ...[30, 62, 94, 126].flatMap((at) =>
        drumParts("base", 0.7, drums("oooooooo", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.6, drums("c", KIT, 32, 4)),
    ],
  };
}

// ---------------------------------------------------------------- "Dragon Canyon"

export const CANYON_DRAGON_MELODY = bars(
  // The frontier (flute)
  "D5:.5 F5:.5 G5:.5 A5:.5 C6:1 A5:1",
  "G5:.5 A5:.5 G5:.5 F5:.5 D5:2",
  "F5:.5 G5:.5 A5:1 C6:.5 D6:.5 C6:1",
  "A5:.5 G5:.5 F5:.5 G5:.5 A5:2",
  "D6:.5 C6:.5 A5:1 G5:.5 A5:.5 C6:1",
  "A5:1 G5:.5 F5:.5 D5:2",
  "F5:.5 A5:.5 C6:.5 D6:.5 E6:1 C6:1",
  "D6:3 r:1",
  // The quarry (low brass and marimba)
  "D4:1 F4:.5 G4:.5 A4:1 G4:1",
  "F4:.5 E4:.5 D4:1 r:1 A3:1",
  "Bb3:1 D4:.5 F4:.5 G4:1 F4:1",
  "E4:1.5 F4:.5 E4:1 C4:1",
  "D4:1 F4:.5 G4:.5 A4:1 C5:1",
  "Bb4:1 A4:.5 G4:.5 F4:1 E4:1",
  "D4:.5 E4:.5 F4:.5 G4:.5 A4:1 G4:1",
  "A4:3 r:1",
  // The High Bridges (strings, the dragon overhead)
  "A5:2 D6:1 E6:1",
  "F6:2 E6:1 D6:1",
  "C6:2 A5:1 C6:1",
  "D6:3 r:1",
  "Bb5:2 C6:1 D6:1",
  "E6:2 F6:1 E6:1",
  "D6:1 C6:1 A5:1 G5:1",
  "A5:3 r:1",
  // The Final Twist (flute and xylophone)
  "D6:.5 C6:.5 A5:.5 G5:.5 A5:.5 C6:.5 D6:1",
  "F6:.5 E6:.5 D6:.5 C6:.5 A5:2",
  "G5:.5 A5:.5 C6:.5 D6:.5 E6:.5 D6:.5 C6:1",
  "A5:.5 G5:.5 F5:.5 E5:.5 D5:2",
  "D5:.5 F5:.5 A5:.5 D6:.5 F6:1 E6:1",
  "D6:.5 C6:.5 A5:.5 C6:.5 D6:2",
  "E6:.5 D6:.5 C6:.5 A5:.5 G5:.5 A5:.5 C6:1",
  "D6:3! r:1",
);
export const CANYON_DRAGON_CHORDS =
  "Dm:4 C:4 Bb:4 A:4 Dm:4 Gm:2 A:2 F:2 C:2 Dm:4 " +
  "Dm:4 Dm:4 Bb:4 C:4 Dm:4 Bb:4 Gm:4 A:4 " +
  "F:4 Dm:4 C:4 Dm:4 Bb:4 C:4 Gm:4 A:4 " +
  "Dm:4 F:4 C:4 Dm:4 Dm:4 Bb:4 C:4 Dm:4";

/**
 * "Dragon Canyon": the kingdom's desert frontier, D minor, 168 BPM: more driven and
 * restless than Dragon Isles. A galloping flute over plucked strings; the quarry's low
 * brass and marimba over pounding toms; strings soaring over the High Bridges; flute and
 * xylophone racing through the Final Twist. Our own tune.
 */
function canyonDragon(): Song {
  const ch = chart(CANYON_DRAGON_CHORDS);
  const mel = seq(CANYON_DRAGON_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const gallop: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "5"],
    [2, 0.5, "R"],
    [2.75, 0.25, "R"],
    [3, 0.5, "8"],
  ];
  return {
    id: "dragon_canyon",
    title: "Dragon Canyon",
    role: "Dragon Kingdom",
    bpm: 168,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      part("flute", "base", 1, p1),
      part("brass", "base", 0.85, p2),
      part("marimba", "base", 0.7, shift(p2, 0, 12)),
      part("strings", "base", 1, p3),
      part("horn", "base", 0.5, shift(p3, 0, -12)),
      part("flute", "base", 0.9, p4),
      part("xylophone", "base", 0.6, p4),
      part(
        "pizz",
        "base",
        0.5,
        arpeggio(
          ch.filter((c) => c.t < 32 || c.t >= 96),
          0.5,
          [0, 1, 2, 1, 0, 2, 1, 2],
          62,
          0.25,
          0.45,
        ),
      ),
      part(
        "pizz",
        "base",
        0.4,
        stabs(
          ch.filter((c) => c.t >= 32 && c.t < 96),
          [0.5, 1.5, 2.5, 3.5],
          57,
          0.2,
          0.45,
        ),
      ),
      part("pad", "base", 0.3, pads(ch, 50, 4, 0.35)),
      part("bass", "base", 1, bassLine(ch, gallop, 26, 0.85)),
      ...drumParts("base", 0.85, drums("o..oo..oo..oo.oo", KIT, 0.25, 32)),
      ...drumParts("base", 0.55, drums("k...k...k...k...", KIT, 0.25, 32)),
      ...drumParts("base", 0.45, drums("..b..b.b..b..b.b", KIT, 0.25, 32)),
      ...drumParts("base", 0.35, drums("h.hhh.hhh.hhh.hh", KIT, 0.25, 32)),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("base", 0.75, drums("o.o.oooooooooooo", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.6, drums("c", KIT, 32, 4)),
    ],
  };
}

export const SNOW_DRAGON_MELODY = bars(
  // The pass in the storm (bells)
  "B5:1 F#5:.5 A5:.5 B5:1 D6:1",
  "C#6:1 A5:1 F#5:2",
  "G5:1 A5:.5 B5:.5 D6:1 C#6:1",
  "B5:3 r:1",
  "D6:1 C#6:.5 B5:.5 A5:1 F#5:1",
  "G5:1 F#5:.5 E5:.5 F#5:2",
  "B5:1 D6:.5 E6:.5 F#6:1 E6:1",
  "D6:3 r:1",
  // The village and the ration lines (strings, a lament)
  "F#5:2 E5:1 D5:1",
  "B4:2 C#5:1 D5:1",
  "E5:1.5 D5:.5 C#5:1 A4:1",
  "B4:3 r:1",
  "D5:2 E5:1 F#5:1",
  "G5:2 F#5:1 E5:1",
  "F#5:1 E5:1 D5:1 C#5:1",
  "B4:3 r:1",
  // The ice dragon (low horns)
  "B3:1 B3:.5 D4:.5 F#4:2",
  "E4:1 D4:1 C#4:2",
  "G3:1 B3:.5 D4:.5 E4:2",
  "F#4:3 r:1",
  "B3:1 D4:.5 E4:.5 F#4:1 A4:1",
  "G4:1 F#4:1 E4:2",
  "D4:1 E4:1 F#4:1 C#4:1",
  "B3:3! r:1",
  // The climb to the citadel (flute and strings)
  "F#5:.5 B5:.5 C#6:.5 D6:.5 F#6:1 E6:1",
  "D6:.5 C#6:.5 B5:.5 A5:.5 B5:2",
  "G5:.5 A5:.5 B5:.5 D6:.5 E6:1 D6:1",
  "C#6:.5 B5:.5 A5:.5 C#6:.5 F#5:2",
  "B5:.5 D6:.5 F#6:.5 G6:.5 F#6:1 E6:1",
  "D6:.5 E6:.5 F#6:1 E6:.5 D6:.5 C#6:1",
  "B5:.5 C#6:.5 D6:.5 E6:.5 F#6:1 A6:1",
  "B6:3! r:1",
);
export const SNOW_DRAGON_CHORDS =
  "Bm:4 F#m:4 G:4 Bm:4 D:4 Em:4 G:2 A:2 Bm:4 " +
  "Bm:4 G:4 Em:4 Bm:4 D:4 G:4 F#:4 Bm:4 " +
  "Bm:4 Em:4 G:4 F#:4 Bm:4 Em:4 D:2 F#:2 Bm:4 " +
  "Bm:4 G:4 Em:4 F#:4 Bm:4 G:4 A:4 Bm:4";

/**
 * "Snow Dragon Pass": the kingdom in winter, B minor, 150 BPM: beautiful and cold, and
 * sadder than the canyon. Bells and celesta ring out over a pulsing drone in the storm;
 * strings lament through the village and the ration lines; low horns and pounding toms
 * for the ice dragon; flute and strings climb together to the citadel. Our own tune.
 */
function snowDragon(): Song {
  const ch = chart(SNOW_DRAGON_CHORDS);
  const mel = seq(SNOW_DRAGON_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const pulse: [number, number, string][] = [
    [0, 1.5, "R"],
    [1.5, 0.5, "R"],
    [2, 1.5, "5"],
    [3.5, 0.5, "R"],
  ];
  return {
    id: "snow_dragon",
    title: "Emberdeep Hold",
    role: "Dragon Kingdom",
    bpm: 150,
    beats: 128,
    loop: true,
    stems: [],
    parts: [
      part("bell", "base", 0.8, p1),
      part("celesta", "base", 0.6, shift(p1, 0, -12)),
      part("strings", "base", 1, p2),
      part("pizz", "base", 0.35, shift(p2, 0, -12)),
      part("horn", "base", 1, p3),
      part("brass", "base", 0.5, shift(p3, 0, 12)),
      part("flute", "base", 0.9, p4),
      part("strings", "base", 0.7, shift(p4, 0, -12)),
      part("celesta", "base", 0.35, arpeggio(ch, 0.5, [0, 2, 1, 2, 0, 2, 1, 2], 69, 0.2, 0.35)),
      part("pad", "base", 0.4, pads(ch, 50, 4, 0.4)),
      part("drone", "base", 0.3, pads(ch, 38, 8, 0.3)),
      part("bass", "base", 1, bassLine(ch, pulse, 26, 0.8)),
      ...drumParts("base", 0.8, drums("o.....o.o.....o.", KIT, 0.25, 32)),
      ...drumParts("base", 0.5, drums("k.......k.......", KIT, 0.25, 32)),
      ...drumParts("base", 0.3, drums("..h...h...h...hh", KIT, 0.25, 32)),
      ...[60, 92].flatMap((at) =>
        drumParts("base", 0.8, drums("o.o.o.oooooooooo", KIT, 0.25, 1, at)),
      ),
      ...drumParts("base", 0.55, drums("c", KIT, 32, 4)),
    ],
  };
}

export const CELESTIAL_MELODY = bars(
  // The Festival Gate and the market (flute and bells)
  "F#5:1 A5:.5 B5:.5 D6:1 B5:1",
  "A5:1 E5:.5 F#5:.5 E5:2",
  "F#5:1 D5:.5 E5:.5 F#5:1 B5:1",
  "A5:3 r:1",
  "D6:1 B5:.5 A5:.5 F#5:1 A5:1",
  "B5:1 A5:.5 G5:.5 E5:2",
  "G5:1 A5:1 B5:1 C#6:1",
  "D6:3! r:1",
  // The worship of the dragon (strings, solemn)
  "F#5:2 E5:1 D5:1",
  "B4:2 D5:1 E5:1",
  "F#5:1.5 A5:.5 F#5:1 E5:1",
  "E5:3 r:1",
  "D5:2 F#5:1 B5:1",
  "A5:2 G5:1 F#5:1",
  "E5:1 F#5:1 G5:1 E5:1",
  "A5:3 r:1",
  // Above the clouds: the Star Bridge and the observatory (celesta, high)
  "B5:.5 D6:.5 E6:1 D6:.5 B5:.5 A5:1",
  "C#6:1 E6:1 A5:2",
  "A5:.5 C#6:.5 F#6:1 E6:.5 C#6:.5 A5:1",
  "B5:3 r:1",
  "D6:.5 B5:.5 G5:1 B5:.5 D6:.5 E6:1",
  "E6:1 C#6:1 A5:1 E6:1",
  "F#6:1 E6:.5 D6:.5 A5:1 D6:1",
  "D6:3 r:1",
  // The triumph (brass)
  "B5:1 D6:1 G6:1 F#6:1",
  "E6:1 C#6:1 A5:2",
  "F#6:1 E6:.5 D6:.5 B5:1 D6:1",
  "G5:3 r:1",
  "A5:1 D6:1 F#6:1 A6:1",
  "G6:1 F#6:1 E6:2",
  "D6:1 E6:1 F#6:1 E6:1",
  "D6:3! r:1",
);
export const CELESTIAL_CHORDS =
  "D:4 A:4 Bm:4 G:4 D:4 Em:4 G:2 A:2 D:4 " +
  "Bm:4 G:4 D:4 A:4 Bm:4 G:4 Em:4 A:4 " +
  "G:4 A:4 F#m:4 Bm:4 G:4 A:4 D:4 D:4 " +
  "G:4 A:4 Bm:4 G:4 D:4 A:4 G:2 A:2 D:4";

/**
 * "Celestial Dragon Festival": the grand finale, D major, 144 BPM, in three layers that
 * follow the festival lap by lap. The base (the Opening Celebration): flute and bells at
 * the gate, strings for the worship, celesta above the clouds, a bright tune for the
 * triumph, over celesta arpeggios, plucked strings, a warm pad and a light pulse. "rise"
 * (the Ceremony Intensifies) adds horns under the tune, sustained strings, a running
 * marimba, toms, bongos and tambourine. "finale" (the Grand Finale) is all of that and
 * the brass and bells on the tune, a xylophone, snare, more kick and a crash on every
 * phrase. Our own tune.
 */
function celestial(): Song {
  const ch = chart(CELESTIAL_CHORDS);
  const mel = seq(CELESTIAL_MELODY, 0, 0.8);
  const p1 = mel.filter((n) => n.t < 32);
  const p2 = mel.filter((n) => n.t >= 32 && n.t < 64);
  const p3 = mel.filter((n) => n.t >= 64 && n.t < 96);
  const p4 = mel.filter((n) => n.t >= 96);
  const walk: [number, number, string][] = [
    [0, 1, "R"],
    [1, 1, "5"],
    [2, 1, "8"],
    [3, 1, "5"],
  ];
  // The middle layer, which the finale carries too.
  const rise = (stem: string): Part[] => [
    part("horn", stem, 0.45, shift(mel, 0, -12)),
    part("strings", stem, 0.4, pads(ch, 57, 4, 0.35)),
    part("marimba", stem, 0.35, arpeggio(ch, 0.25, [0, 1, 2, 1, 3, 2, 1, 2], 62, 0.2, 0.4)),
    ...drumParts(stem, 0.6, drums("o.....o.o.....o.", KIT, 0.25, 32)),
    ...drumParts(stem, 0.4, drums("..b..b.b..b..b.b", KIT, 0.25, 32)),
    ...drumParts(stem, 0.35, drums("....t.......t...", KIT, 0.25, 32)),
  ];
  return {
    id: "celestial",
    title: "Moonstone Kingdom",
    role: "Dragon Kingdom",
    bpm: 144,
    beats: 128,
    loop: true,
    stems: ["rise", "finale"],
    parts: [
      part("flute", "base", 0.9, p1),
      part("bell", "base", 0.4, shift(p1, 0, 12)),
      part("strings", "base", 0.9, p2),
      part("celesta", "base", 0.8, p3),
      part("bell", "base", 0.35, p3),
      part("flute", "base", 0.8, p4),
      part("celesta", "base", 0.3, arpeggio(ch, 0.5, [0, 2, 1, 2, 3, 2, 1, 2], 69, 0.2, 0.35)),
      part("pizz", "base", 0.35, stabs(ch, [0.5, 1.5, 2.5, 3.5], 57, 0.2, 0.45)),
      part("pad", "base", 0.35, pads(ch, 50, 4, 0.4)),
      part("bass", "base", 1, bassLine(ch, walk, 26, 0.8)),
      ...drumParts("base", 0.5, drums("k...k...k...k...", KIT, 0.25, 32)),
      ...drumParts("base", 0.3, drums("..h...h...h...hh", KIT, 0.25, 32)),
      ...drumParts("base", 0.5, drums("c", KIT, 32, 4)),
      ...rise("rise"),
      ...rise("finale"),
      part("brass", "finale", 0.6, mel),
      part("bell", "finale", 0.3, shift(mel, 0, 12)),
      part("xylophone", "finale", 0.3, arpeggio(ch, 0.25, [0, 1, 2, 3, 2, 1, 2, 3], 74, 0.15, 0.4)),
      ...drumParts("finale", 0.55, drums("....S.......S...", KIT, 0.25, 32)),
      ...drumParts("finale", 0.4, drums("..k.....k.k.....", KIT, 0.25, 32)),
      ...[28, 60, 92, 124].flatMap((at) =>
        drumParts("finale", 0.6, drums("sssssssSsSsSSSSS", KIT, 0.25, 1, at)),
      ),
      ...drumParts("finale", 0.45, drums("c", KIT, 8, 16)),
    ],
  };
}

export const SONGS: Record<string, Song> = {
  title: title(),
  select: select(),
  map: map(),
  race: race(),
  fanfare: fanfare(),
  riverbend: riverbend(),
  riverbend_classic: riverbendClassic(),
  cascade: cascade(),
  cascade_classic: cascadeClassic(),
  frostveil: frostveil(),
  summit: summit(),
  hearthglow: hearthglow(),
  aurora: aurora(),
  canyon: canyon(),
  oasis: oasis(),
  ghost: ghost(),
  depths: depths(),
  dragon: dragon(),
  dragon_canyon: canyonDragon(),
  snow_dragon: snowDragon(),
  celestial: celestial(),
  bonebog: bonebog(),
  ember: ember(),
  ember_classic: emberClassic(),
};

/** The music player's list: composed pieces, then planned ones not written yet. */
export const CATALOG: { id: string; title: string; role: string; available: boolean }[] = [
  ...Object.values(SONGS).map((s) => ({ id: s.id, title: s.title, role: s.role, available: true })),
  // Planned: the Tropic Isles' own pieces (their courses use the title theme for now), the
  // dragons' boss races (they borrow their kingdom's), and Adventure's map.
  { id: "coral_cove", title: "Coral Cove", role: "Tropic Isles", available: false },
  { id: "shipwreck_bay", title: "Shipwreck Bay", role: "Tropic Isles", available: false },
  { id: "volcano_isle", title: "Volcano Isle", role: "Tropic Isles", available: false },
  { id: "splash_lagoon", title: "Splash Lagoon", role: "Tropic Isles", available: false },
  { id: "boss", title: "Dragon Race", role: "Boss races", available: false },
  { id: "adventure", title: "Adventure Map", role: "Adventure mode", available: false },
];
