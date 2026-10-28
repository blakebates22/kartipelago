/**
 * The Adventure's cutscene score: twenty cues written as one film score, all original
 * (MIT, like the code). Staged scenes name them (StagedScene.music, a beat's
 * fx.music); "dread" (songs.ts) stays the cue for a dragon arriving.
 *
 * Three leitmotifs run through it, written into each cue in its own key and voice:
 *
 *   LUMEN   5 ↑ 3 ↑ #4 ↓ 2 ↑ 5   e.g. in D: A4 F#5 G#5 E5 A5. A rising sixth, a step up
 *           to the lydian fourth (the sparkle), a fall and a questioning leap to the
 *           fifth. Celesta when the hooded figure appears; twisted by tritones when the
 *           Heart Stone shatters; minor and falling in the ruins; turning major again
 *           when the shards are found; full and golden in brass for the finale.
 *   PACT    5 ↑ 1 ↑ 2 ↑ 3 ↓ 2 ↓ 1 ↑ 5   e.g. in C: G4 C5 D5 E5 D5 C5 G5. The crews and their
 *   (crew)  Pact: a rising fourth, a climb and a heroic leap up to the fifth. Hinted at
 *           the festival, crushed into minor under the dragons, cheered in the false
 *           victory, sung by the choir as a new Pact Stone rises, confessed slowly and
 *           brokenly on Mossback's horn, and played with Lumen's motif at the end.
 *   DRAGON  1 ↑ b2 ↓ 1 ↑ #4     e.g. C Db C F#. The half-step neighbour and the tritone
 *           of "The Dragon's Shadow" (dread). Each dragon gets their own reading of it:
 *           Rimefang's in cold bells, Scorchwind's as a blues lick, Tidewyrm's as a slither
 *           in the bass, the King's broad and slow in the organ and brass. When a dragon
 *           yields, its tritone finally resolves up a half step.
 *
 * Every cue loops (but "shatter", which plays once and rings away into silence) and has
 * a short intro (beats before 0, played once), so a cue switched in mid-scene comes in
 * on the beat with a pickup rather than mid-phrase (see engine.ts).
 */
import type { InstrumentId } from "./instruments";
import {
  arpeggio,
  above,
  bassLine,
  chart,
  drums,
  dyn,
  pads,
  seq,
  seqLength,
  shift,
  stabs,
  type Chord,
  type Note,
  type Part,
  type Song,
} from "./score";

const part = (inst: InstrumentId, gain: number, notes: Note[]): Part => ({
  inst,
  stem: "base",
  gain,
  notes,
});

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

const beat = (grid: string, step: number, times: number, start = 0, gain = 0.7): Part[] =>
  drums(grid, KIT, step, times, start).map((d) => part(d.inst, gain, d.notes));

/**
 * Bars of melody, each checked to be `len` beats long (a slip in a bar shows up at
 * once rather than as a melody drifting off its chords), joined.
 */
function bars(len: number, ...b: string[]): string {
  b.forEach((bar, i) => {
    const l = seqLength(bar);
    if (Math.abs(l - len) > 1e-6) throw new Error(`Bar ${i + 1} is ${l} beats, not ${len}: ${bar}`);
  });
  return b.join(" ");
}

/** A melody starting at `at` (bars() checked), as notes, its swung and triplet times
 * snapped back onto the grid they drift off by rounding. */
const line = (src: string, at = 0, vel = 0.8) =>
  seq(src, at, vel).map((n) => ({ ...n, t: Math.round(n.t * 1e6) / 1e6 }));

/** Notes in a window [from, to) of beats. */
const between = (notes: Note[], from: number, to: number) =>
  notes.filter((n) => n.t >= from && n.t < to);

/**
 * A roll (timpani, snare): hits every `step` beats, swelling from v0 to v1, each hit
 * softer the closer they come (they ring into one another and would pile up).
 */
function roll(midi: number, start: number, beats: number, step: number, v0: number, v1: number) {
  const out: Note[] = [];
  const n = Math.round(beats / step);
  const damp = Math.min(1, Math.sqrt(step * 2)) * (midi > 0 ? 0.7 : 1);
  for (let i = 0; i < n; i++)
    out.push({
      t: start + i * step,
      d: step,
      m: midi,
      v: (v0 + ((v1 - v0) * i) / Math.max(1, n - 1)) * damp,
    });
  return out;
}

/** A harp's rolled chord on each chord's first beat: the voicing spread upward. */
function rolled(chords: Chord[], floor: number, spread = 0.08, vel = 0.6, octaves = 2): Note[] {
  const out: Note[] = [];
  for (const c of chords) {
    const root = above(c.bass, floor - 12);
    const tones: number[] = [root];
    for (let o = 0; o < octaves; o++)
      for (const i of c.tones) tones.push(above((c.root + i) % 12, floor) + 12 * o);
    tones.sort((a, b) => a - b);
    tones.forEach((m, k) =>
      out.push({ t: c.t + k * spread, d: c.d, m, v: vel * (0.8 + k * 0.03) }),
    );
  }
  return out;
}

/** A figure on each chord's bass note: semitone offsets from it, one every `step` beats. */
function ostinato(
  chords: Chord[],
  offsets: number[],
  step: number,
  floor: number,
  len = step,
  vel = 0.7,
) {
  const out: Note[] = [];
  for (const c of chords) {
    const root = above(c.bass, floor);
    let k = 0;
    for (let t = 0; t < c.d - 1e-6; t += step, k++)
      out.push({
        t: c.t + t,
        d: len,
        m: root + offsets[k % offsets.length]!,
        v: vel * (k % 4 ? 0.82 : 1),
      });
  }
  return out;
}

/** A clock: `hi` on every beat and `lo` between, for `beats` beats from `start`. */
function clock(
  start: number,
  beats: number,
  hi: number,
  lo: number,
  vel = 0.5,
  skip: number[] = [],
) {
  const out: Note[] = [];
  for (let b = 0; b < beats; b++) {
    if (!skip.includes(b)) out.push({ t: start + b, d: 0.25, m: hi, v: vel });
    out.push({ t: start + b + 0.5, d: 0.25, m: lo, v: vel * 0.7 });
  }
  return out;
}

// ================================================================ festival

export const FESTIVAL_CHORDS =
  "C:4 F:4 G:4 C:4 Am:4 F:4 D7:4 G7:4 C:4 G:4 Am:4 Em:4 F:4 C:4 Dm7:2 G7:2 C:4";

export const FESTIVAL_MELODY = bars(
  4,
  "E5:.5 G5:.5 C6:.75 B5:.25 A5:.5 G5:.5 E5:1",
  "F5:.5 A5:.5 C6:1 A5:.5 F5:.5 C5:1",
  "D5:.5 G5:.5 B5:.75 A5:.25 G5:.5 F5:.5 D5:1",
  "E5:1 G5:.5 E5:.5 C5:2",
  "A5:.5 C6:.5 E6:1 D6:.5 C6:.5 A5:1",
  "F5:.5 A5:.5 C6:1 D6:.5 C6:.5 A5:1",
  "F#5:.5 A5:.5 D6:1 C6:.5 A5:.5 F#5:1",
  "G5:1 F5:.5 D5:.5 B4:1 G4:1",
  // The Pact, hinted: the crews' motif, then a skip away from it.
  "G4:.5 C5:.5 D5:.5 E5:1.5 D5:.5 C5:.5",
  "G5:2 r:.5 D5:.5 G5:.5 B5:.5",
  "C6:1 B5:.5 A5:.5 E5:1 A5:1",
  "G5:1.5 F#5:.5 E5:1 B4:1",
  "A5:.5 G5:.5 F5:.5 A5:.5 C6:1 F6:1",
  "E6:1 D6:.5 C6:.5 G5:1 E5:1",
  "F5:.5 E5:.5 D5:.5 F5:.5 B5:.5 A5:.5 G5:.5 F5:.5",
  "E5:1 C5:.5 D5:.5 E5:1 r:1",
);

/** A flute counter-line over the second half of the A section. */
const FESTIVAL_COUNTER = bars(4, "C6:2 B5:2", "A5:4", "A5:2 F#5:2", "G5:2 F5:2");

const bounce: [number, number, string][] = [
  [0, 1, "R"],
  [1, 0.5, "5"],
  [1.5, 0.5, "8"],
  [2, 1, "5"],
  [3, 0.5, "R"],
  [3.5, 0.5, "A"],
];

/** "Summer Festival": Dinosaur Valley in bunting, C major, 136. Steel pan and a whistling
 * flute over an accordion's off-beats, rolling marimba, a bouncing bass, bongos. */
function festival(): Song {
  const ch = chart(FESTIVAL_CHORDS);
  const mel = line(FESTIVAL_MELODY, 0, 0.82);
  return {
    id: "festival",
    title: "Summer Festival",
    role: "Cutscenes",
    bpm: 136,
    beats: 64,
    intro: 2,
    peak: 0.81,
    loop: true,
    stems: [],
    parts: [
      // Intro: a xylophone run up into the tune, over a snare pickup.
      part(
        "xylophone",
        0.7,
        line("G4:.25 A4:.25 B4:.25 C5:.25 D5:.25 E5:.25 F5:.25 G5:.25", -2, 0.7),
      ),
      ...beat("....s.ss", 0.25, 1, -2, 0.55),
      ...beat("S.s.S.SS", 0.25, 1, -1, 0.6),
      part("steelpan", 0.95, mel),
      part("xylophone", 0.3, shift(between(mel, 32, 64), 0, 12)),
      part("flute", 0.85, line(FESTIVAL_COUNTER, 16, 0.7)),
      // The flute doubles the Pact's hint.
      part("flute", 0.7, between(mel, 32, 40)),
      part("accordion", 0.45, stabs(ch, [0.5, 1.5, 2.5, 3.5], 60, 0.3, 0.55)),
      part("marimba", 0.45, dyn(arpeggio(ch, 0.5, [0, 1, 2, 3, 2, 1, 2, 1], 55, 0.4, 0.5), 1)),
      part("bass", 1, bassLine(ch, bounce, 36, 0.85)),
      ...beat("K...k.K.K...k.K.", 0.25, 16, 0, 0.75),
      ...beat("....S.......S..s", 0.25, 16, 0, 0.5),
      ...beat("b.bb..b.b.bb..bb", 0.25, 16, 0, 0.45),
      ...beat("hHhhhHhhhHhhhHhh", 0.25, 16, 0, 0.35),
      ...beat("..t...t...t...t.", 0.25, 16, 0, 0.35),
      ...beat("C", 32, 2, 0, 0.5),
    ],
  };
}

// ================================================================ lumen

export const LUMEN_CHORDS = "D:4 E/D:4 D:4 E/D:4 Bm:4 Gmaj7:4 Em7:4 Asus4:2 A:2";

/** "Lumen": the hooded figure. D lydian, 72: celesta and flute trade the motif over a
 * rolling harp, soft strings and a plucked tick-tock. */
function lumen(): Song {
  const ch = chart(LUMEN_CHORDS);
  const celesta = line(
    bars(
      4,
      // LUMEN
      "A4:.5 F#5:1 G#5:.5 E5:1 A5:1",
      "r:4",
      "A4:.5 F#5:1 G#5:.5 B5:1 A5:1",
      "r:4",
      "F#5:1.5 D5:.5 B4:2",
      "r:1 F#5:1 B5:1 A5:1",
      "G5:1.5 F#5:.5 E5:1 D5:1",
      "E5:3 r:1",
    ),
    0,
    0.8,
  );
  const flute = line(
    bars(
      4,
      "r:4",
      "r:1 G#5:1 F#5:.5 E5:.5 B4:1",
      "r:4",
      "r:1 B5:1 G#5:.5 F#5:.5 E5:1",
      "r:4",
      "D6:2 C#6:2",
      "B5:4",
      "D6:2 C#6:2",
    ),
    0,
    0.6,
  );
  return {
    id: "lumen",
    title: "Lumen",
    role: "Cutscenes",
    bpm: 72,
    beats: 32,
    intro: 1,
    loop: true,
    peak: 0.54,
    stems: [],
    parts: [
      // Intro: a harp glissando up the lydian chord, a bell on top.
      part(
        "harp",
        0.8,
        line("D4:.125 F#4:.125 A4:.125 C#5:.125 E5:.125 G#5:.125 A5:.125 C#6:.125", -1, 0.6),
      ),
      part("bell", 0.4, line("A6:1", -1 + 0.875, 0.5)),
      part("celesta", 1, celesta),
      part("bell", 0.25, shift(celesta, 0, 12)),
      part("flute", 0.75, flute),
      part("harp", 0.55, arpeggio(ch, 0.5, [0, 1, 2, 3, 4, 3, 2, 1], 50, 0.5, 0.5)),
      part("pad", 0.45, pads(ch, 57, 4, 0.4)),
      part("strings", 0.3, bassLine(ch, [[0, 3.9, "R"]], 38, 0.5)),
      part(
        "pizz",
        0.4,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [2, 1, "5"],
          ],
          38,
          0.55,
        ),
      ),
      part("bell", 0.18, arpeggio(ch, 2, [3, 4], 74, 2, 0.35)),
    ],
  };
}

// ================================================================ smugglers

export const SMUGGLERS_CHORDS =
  "Gm:4 Gm:4 Cm:4 Gm:4 Eb:4 D7:4 Gm:4 D7:4 Gm:4 Gm:4 Cm:4 Cm:4 Ab:4 D7:4 Gm:2 D7:2 Gm:4";

/** "Smugglers' Den": tiptoeing through the tunnels, G minor shuffle, 112. Bassoon and
 * clarinet sneaking in swung eighths over a plucked walking bass, brushes and a woodblock. */
function smugglers(): Song {
  const ch = chart(SMUGGLERS_CHORDS);
  const sneak = bars(
    4,
    "G3:.5 r:.5 Bb3:.5 r:.5 D4:.66 Eb4:.34 D4:.5 r:.5",
    "C#4:.66 D4:.34 F4:.66 E4:.34 Eb4:.66 D4:.34 Bb3:1",
    "C4:.5 r:.5 Eb4:.5 r:.5 G4:.66 Ab4:.34 G4:.5 r:.5",
    "F#4:.66 G4:.34 Bb4:.66 A4:.34 G4:.66 D4:.34 r:1",
  );
  // The bassoon sneaks in bars 1-4, and again (under the clarinet) in bars 9-12.
  const bassoon = [...line(sneak, 0, 0.8), ...line(sneak, 32, 0.8)];
  const clarinet = line(
    bars(
      4,
      "r:4",
      "r:4",
      "r:4",
      "r:4",
      "Bb4:.66 G4:.34 Eb4:.66 G4:.34 Bb4:1 Ab4:.66 G4:.34",
      "F#4:.66 A4:.34 C5:.66 A4:.34 F#4:1 D4:1",
      "G4:.66 Bb4:.34 D5:.66 C#5:.34 D5:.66 Bb4:.34 G4:1",
      "r:1 A4:.33 Bb4:.33 B4:.34 C5:.33 C#5:.33 D5:.34 r:.5 D4:.5",
      // Second time: the clarinet shadows the bassoon an octave up.
      "G4:.5 r:.5 Bb4:.5 r:.5 D5:.66 Eb5:.34 D5:.5 r:.5",
      "C#5:.66 D5:.34 F5:.66 E5:.34 Eb5:.66 D5:.34 Bb4:1",
      "C5:.5 r:.5 Eb5:.5 r:.5 G5:.66 Ab5:.34 G5:.5 r:.5",
      "F#5:.66 G5:.34 Bb5:.66 A5:.34 G5:.66 D5:.34 r:1",
      "C5:.66 Eb5:.34 Ab5:.66 G5:.34 F5:.66 Eb5:.34 C5:1",
      "D5:.66 F#5:.34 A5:.66 C6:.34 A5:.66 F#5:.34 D5:1",
      "G5:.66 D5:.34 Bb4:.66 G4:.34 A4:.66 C5:.34 F#4:1",
      "G4:.5 r:.5 D4:.5 r:.5 G3:.5 r:1.5",
    ),
    0,
    0.72,
  );
  // A plucked walking bass on the beat, the woodblock on two and four.
  const walk: [number, number, string][] = [
    [0, 0.5, "R"],
    [1, 0.5, "5"],
    [2, 0.5, "8"],
    [3, 0.5, "A"],
  ];
  return {
    id: "smugglers",
    title: "Smugglers' Den",
    role: "Cutscenes",
    bpm: 112,
    beats: 64,
    intro: 2,
    loop: true,
    peak: 0.67,
    stems: [],
    parts: [
      // Intro: a chromatic creep up to the tonic.
      part("bassoon", 0.9, line("D3:.5 Eb3:.5 E3:.5 F#3:.5", -2, 0.7)),
      part("woodblock", 0.5, line("C6:.5 r:.5 G5:.5 r:.5", -2, 0.5)),
      part("bassoon", 0.95, bassoon),
      part("clarinet", 0.9, clarinet),
      part("bassoon", 0.5, shift(between(clarinet, 48, 64), 0, -12)),
      part("pizz", 0.9, bassLine(ch, walk, 31, 0.8)),
      part("bass", 0.7, bassLine(ch, walk, 31, 0.7)),
      part("pizz", 0.35, stabs(ch, [1.66, 3.66], 55, 0.2, 0.5)),
      part("pad", 0.2, pads(ch, 50, 4, 0.35)),
      // A shuffle: the hat on the swung eighths (triplet grid), brushes on two and four.
      ...beat("I.iI.iI.iI.i", 1 / 3, 16, 0, 0.3),
      ...beat("...s.....s..", 1 / 3, 16, 0, 0.35),
      ...beat("k.....k.....", 1 / 3, 16, 0, 0.45),
      ...beat("...w.....w..", 1 / 3, 16, 0, 0.35),
    ],
  };
}

// ================================================================ conquered

export const CONQUERED_CHORDS = "Cm:4 Db:4 Cm:4 Gb:4 Fm:4 Db:4 G:4 G:4 Cm:4 Ab:4 Db:4 G:4";

/** "Under the Dragon's Heel": the land the dragons rule, C minor march, 84. Low brass
 * stamping out the DRAGON motif over timpani and a military snare; in the strings the
 * crews' PACT motif, in minor, falling short of its leap. */
function conquered(): Song {
  const ch = chart(CONQUERED_CHORDS);
  const brass = line(
    bars(
      4,
      // DRAGON
      "C4:1.5 Db4:.5 C4:1 Gb4:1",
      "F4:.75 Eb4:.25 Db4:1 Ab3:2",
      "C4:1.5 Db4:.5 C4:1 G4:1",
      "Bb4:.75 Ab4:.25 Gb4:1 Db4:2",
      "C5:1.5 Ab4:.5 F4:1 C4:1",
      "Db5:1.5 C5:.5 Ab4:1 F4:1",
      "G4:.75 Ab4:.25 G4:1 F4:.75 Eb4:.25 D4:1",
      "D4:.75 Eb4:.25 D4:1 B3:2",
      "r:4",
      "r:4",
      // DRAGON again, from F
      "F4:1.5 Gb4:.5 F4:1 B4:1",
      "G4:1 Ab4:1 G4:1 D4:1",
    ),
    0,
    0.85,
  );
  // The PACT motif in minor, crushed: it can't make its leap.
  const strings = line(bars(4, "G4:.5 C5:.5 D5:.5 Eb5:1.5 D5:.5 C5:.5", "Ab4:2 G4:1 r:1"), 32, 0.6);
  const march: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "R"],
    [2, 0.5, "5"],
    [2.75, 0.25, "5"],
    [3, 0.5, "R"],
  ];
  return {
    id: "conquered",
    title: "Under the Dragon's Heel",
    role: "Cutscenes",
    bpm: 84,
    beats: 48,
    intro: 2,
    loop: true,
    stems: [],
    parts: [
      // Intro: a snare roll swelling, the timpani on the dominant.
      part("snare", 0.55, roll(0, -2, 2, 0.125, 0.25, 0.85)),
      part("timpani", 0.8, line("G2:1 G2:.5 G2:.5", -2, 0.75)),
      part("brass", 1, brass),
      part("horn", 0.75, shift(brass, 0, -12)),
      part("strings", 0.85, strings),
      part("flute", 0.3, strings),
      part("strings", 0.45, ostinato(ch, [0, 0, 12, 0, 1, 0, 12, 0], 0.5, 36, 0.4, 0.6)),
      part("choir", 0.45, pads(ch, 48, 4, 0.5)),
      part(
        "timpani",
        0.9,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [2, 1, "5"],
          ],
          36,
          0.85,
        ),
      ),
      part("bass", 0.9, bassLine(ch, march, 24, 0.8)),
      part("drone", 0.45, bassLine(ch, [[0, 3.9, "R"]], 24, 0.55)),
      part("bell", 0.3, arpeggio(ch, 4, [0], 60, 3, 0.5)),
      ...beat("S..sS.s.S..sS.ss", 0.25, 12, 0, 0.5),
      ...beat("K.......K.......", 0.25, 12, 0, 0.6),
      ...beat("C", 32, 2, 0, 0.45),
    ],
  };
}

// ================================================================ rimefang

export const RIMEFANG_CHORDS =
  "Bm:4 Bm:4 G:4 F#:4 Bm:4 Bm:4 Em:4 F#:4 G:4 Em:4 Bm:4 F#:4 G:4 C:4 F#:4 F#:4";

/** "Rimefang's Clockwork": the ice dragon's precise cold, B minor, 120. A ticking clock,
 * a music-box ostinato in plucked strings, staccato strings, and the DRAGON motif rung
 * high in bells; a Neapolitan C major glints like frost. */
function rimefang(): Song {
  const ch = chart(RIMEFANG_CHORDS);
  const bells = line(
    bars(
      4,
      // DRAGON, rung cold and high
      "B5:1 C6:1 B5:1 F6:1",
      "r:4",
      "r:4",
      "r:4",
      "B5:1 C6:1 B5:1 F6:1",
      "r:4",
      "r:4",
      "r:4",
    ),
    0,
    0.75,
  );
  const strings = line(
    bars(
      4,
      "r:4",
      "B4:.5 C#5:.5 D5:.5 E5:.5 F#5:1 B4:1",
      "G5:.5 F#5:.5 E5:.5 D5:.5 B4:1 G4:1",
      "A#4:.5 C#5:.5 F#5:.5 E5:.5 C#5:1 A#4:1",
      "r:4",
      "D5:.5 E5:.5 F#5:.5 G5:.5 A5:1 F#5:1",
      "G5:.5 F#5:.5 E5:.5 B4:.5 E5:1 G5:1",
      "F#5:1 E#5:.5 F#5:.5 C#5:2",
    ),
    0,
    0.78,
  );
  // Staccato: every note clipped short.
  const clip = (n: Note[], d = 0.28) => n.map((x) => ({ ...x, d: Math.min(x.d, d) }));
  const celesta = line(
    bars(
      4,
      "B5:.5 D6:.5 G6:1 F#6:.5 D6:.5 B5:1",
      "G5:.5 B5:.5 E6:1 D6:.5 B5:.5 G5:1",
      "F#5:.5 B5:.5 D6:1 C#6:.5 B5:.5 F#5:1",
      "A#5:1 C#6:1 F#6:2",
    ),
    32,
    0.7,
  );
  const late = line(
    bars(
      4,
      // DRAGON, in the strings
      "G4:1 Ab4:1 G4:1 C#5:1",
      "E5:.5 G5:.5 C6:1 B5:.5 G5:.5 E5:1",
      "C#5:.5 E5:.5 F#5:.5 A#5:.5 C#6:1 A#5:1",
      "F#5:.5 r:3.5",
    ),
    48,
    0.78,
  );
  return {
    id: "rimefang",
    title: "Rimefang's Clockwork",
    role: "Cutscenes",
    bpm: 120,
    beats: 64,
    intro: 2,
    peak: 0.74,
    loop: true,
    stems: [],
    parts: [
      // Intro: the clock alone, then a bell.
      part("woodblock", 0.55, clock(-2, 2, 88, 83, 0.55)),
      part("bell", 0.35, line("F#5:1", -1, 0.4)),
      part("bell", 0.9, bells),
      part("celesta", 0.5, bells),
      part("strings", 1, clip(strings)),
      part("pizz", 0.6, strings),
      part("celesta", 0.9, celesta),
      part("bell", 0.3, celesta),
      part("strings", 1, clip(late)),
      part("bell", 0.35, between(late, 48, 52)),
      part("pizz", 0.5, arpeggio(ch, 0.25, [0, 1, 2, 1, 3, 2, 1, 2], 59, 0.12, 0.5)),
      part(
        "bass",
        0.8,
        bassLine(
          ch,
          [
            [0, 0.4, "R"],
            [1, 0.4, "5"],
            [2, 0.4, "R"],
            [3, 0.4, "5"],
          ],
          35,
          0.75,
        ),
      ),
      part("strings", 0.25, pads(ch, 62, 4, 0.35)),
      part("woodblock", 0.4, clock(0, 64, 88, 83, 0.5)),
      part("bell", 0.15, arpeggio(ch, 1, [4, 3, 5, 3], 71, 0.9, 0.3)),
      ...beat("o...............", 0.25, 16, 0, 0.4),
      ...beat("....i.......i...", 0.25, 16, 0, 0.3),
    ],
  };
}

// ================================================================ scorchwind

export const SCORCHWIND_CHORDS =
  "Bb:4 G7:4 Cm7:4 F7:4 Bb:4 G7:4 Cm7:2 F7:2 Bb:4 Eb:4 Edim:4 Bb:4 G7:4 C7:4 F7:4 Bb:2 G7:2 Cm7:2 F7:2";

/** "Scorchwind's Big Show": the showman, Bb swing, 144. Brass shouting the DRAGON motif
 * as a blues lick (Bb B Bb E, the flat fifth resolving up), an accordion and clarinet
 * for the cabaret, a walking bass, a swinging ride and rimshots. */
function scorchwind(): Song {
  const ch = chart(SCORCHWIND_CHORDS);
  const brass = line(
    bars(
      4,
      // DRAGON, as a lick
      "Bb4:.66 B4:.34 Bb4:.66 E5:.34 F5:2",
      "D5:.66 F5:.34 G5:.66 F5:.34 D5:.66 B4:.34 G4:1",
      "Eb5:.66 G5:.34 Bb5:.66 G5:.34 Eb5:1 C5:1",
      "A4:.66 C5:.34 Eb5:.66 F5:.34 A5:1 r:1",
      "Bb5:.66 B5:.34 Bb5:.66 E6:.34 F6:2",
      "F6:.66 D6:.34 B5:.66 G5:.34 F5:1 D5:1",
      "Eb5:.66 D5:.34 C5:.66 Bb4:.34 A4:.66 C5:.34 Eb5:1",
      "D5:.66 Bb4:.34 F4:1 Bb4:1! r:1",
    ),
    0,
    0.85,
  );
  const cabaret = line(
    bars(
      4,
      "G5:.66 F5:.34 Eb5:.66 Bb4:.34 G4:1 Bb4:1",
      "Bb4:.66 Db5:.34 E5:.66 G5:.34 Bb5:1 G5:1",
      "F5:1.5 D5:.5 Bb4:2",
      "B4:.66 D5:.34 F5:.66 G5:.34 B5:1 G5:1",
      "Bb5:.66 G5:.34 E5:.66 C5:.34 Bb4:1 G4:1",
      "A4:.66 C5:.34 F5:.66 A5:.34 C6:1 Eb6:1",
      "D6:.66 C6:.34 Bb5:1 B5:.66 D6:.34 F6:1",
      "Eb6:1 C6:.66 A5:.34 F5:1 r:1",
    ),
    32,
    0.8,
  );
  const walk: [number, number, string][] = [
    [0, 1, "R"],
    [1, 1, "3"],
    [2, 1, "5"],
    [3, 1, "A"],
  ];
  return {
    id: "scorchwind",
    title: "Scorchwind's Big Show",
    role: "Cutscenes",
    bpm: 144,
    beats: 64,
    intro: 2,
    peak: 0.7,
    loop: true,
    stems: [],
    parts: [
      // Intro: a drum roll and a brass "ta-da" climbing to the downbeat.
      part("snare", 0.5, roll(0, -2, 2, 0.125, 0.3, 0.8)),
      part("brass", 0.9, line("F4:.5 Bb4:.5 D5:.5 F5:.5", -2, 0.8)),
      part("brass", 1, brass),
      part("horn", 0.5, shift(brass, 0, -12)),
      part("accordion", 0.95, cabaret),
      part("clarinet", 0.5, shift(cabaret, 0, -12)),
      // Brass stabs answer the cabaret; the accordion vamps behind the brass.
      part(
        "brass",
        0.4,
        stabs(
          ch.filter((c) => c.t >= 32),
          [1.66, 3],
          58,
          0.3,
          0.6,
        ),
      ),
      part(
        "accordion",
        0.35,
        stabs(
          ch.filter((c) => c.t < 32),
          [1, 3],
          58,
          0.4,
          0.5,
        ),
      ),
      part("bass", 1, bassLine(ch, walk, 34, 0.85)),
      part("pizz", 0.3, bassLine(ch, walk, 34, 0.6)),
      ...beat("I.iI.iI.iI.i", 1 / 3, 16, 0, 0.4),
      ...beat("...S.....S..", 1 / 3, 16, 0, 0.45),
      ...beat("k.....k.....", 1 / 3, 16, 0, 0.55),
      ...beat("C", 16, 4, 0, 0.45),
      ...beat("s.s.ssS.", 0.25, 1, 30, 0.55),
      ...beat("s.s.ssS.", 0.25, 1, 62, 0.55),
    ],
  };
}

// ================================================================ tidewyrm

/** 6/8: a beat here is an eighth note, a bar six of them. */
export const TIDEWYRM_CHORDS =
  "Dm:6 Dm:6 C:6 C:6 Dm:6 Am:6 Bb:6 A:6 Dm:6 G:6 Dm:6 C:6 Bb:6 C:6 A:6 Dm:6";

/** "The Tidewyrm's Tune": slinky and sly, a sea shanty in D dorian 6/8. An accordion on
 * the tune, a clarinet sidling up with the DRAGON motif, a wobbling bass that slithers
 * the motif itself, plucked off-beats, shakers like surf and a wave swelling in. */
function tidewyrm(): Song {
  const ch = chart(TIDEWYRM_CHORDS);
  const accordion = line(
    bars(
      6,
      "D5:2 A4:1 D5:2 E5:1",
      "F5:3 E5:2 D5:1",
      "E5:2 C5:1 E5:2 G5:1",
      "E5:2 D5:1 C5:3",
      "D5:2 A4:1 D5:2 F5:1",
      "E5:2 C5:1 A4:3",
      "D5:2 F5:1 Bb5:2 A5:1",
      "G5:1 F5:1 E5:1 C#5:3",
      "A5:2 F5:1 D5:2 F5:1",
      "B5:3 G5:2 D5:1",
      "F5:2 E5:1 D5:2 A4:1",
      "r:6",
      "D5:2 Bb4:1 F5:2 D5:1",
      "E5:2 G5:1 C6:2 G5:1",
      "A5:2 G5:1 E5:2 C#5:1",
      "D5:3 r:3",
    ),
    0,
    0.8,
  );
  // DRAGON, sidling up in the clarinet where the accordion pauses.
  const clarinet = line(bars(6, "G4:2 Ab4:1 G4:2 C#5:1"), 66, 0.8);
  // The bass: dotted-quarter roots and fifths, slithering the motif at the turnarounds.
  const slither = (at: number, root: string, up: string, tri: string) =>
    line(`${root}:2 ${up}:1 ${root}:2 ${tri}:1`, at, 0.85);
  const base = bassLine(
    ch,
    [
      [0, 2.6, "R"],
      [3, 2.6, "5"],
    ],
    38,
    0.85,
  ).filter((n) => !(n.t >= 42 && n.t < 48) && !(n.t >= 90 && n.t < 96));
  const bass = [...base, ...slither(42, "A2", "Bb2", "D#3"), ...slither(90, "A2", "Bb2", "D#3")];
  return {
    id: "tidewyrm",
    title: "The Tidewyrm's Tune",
    role: "Cutscenes",
    bpm: 176,
    beats: 96,
    intro: 3,
    peak: 0.76,
    loop: true,
    stems: [],
    parts: [
      // Intro: a shanty pickup, the bass sliding in under it.
      part("accordion", 0.9, line("A4:1 C5:1 C#5:1", -3, 0.7)),
      part("wobble", 1, line("A2:3", -3, 0.7)),
      part("accordion", 1, accordion),
      part("clarinet", 0.9, clarinet),
      part("clarinet", 0.4, between(accordion, 48, 66)),
      part("wobble", 1, bass),
      part("pizz", 0.55, stabs(ch, [1, 2, 4, 5], 57, 0.25, 0.5)),
      part("marimba", 0.3, stabs(ch, [1, 4], 64, 0.25, 0.45)),
      part("pad", 0.25, pads(ch, 55, 6, 0.35)),
      part("riser", 0.25, line("D4:5.5 r:.5", 42, 0.6)),
      part("riser", 0.25, line("D4:5.5 r:.5", 90, 0.6)),
      ...beat("K..k..", 1, 16, 0, 0.6),
      ...beat("hhhhhh", 1, 16, 0, 0.35),
      ...beat("...t..", 1, 16, 0, 0.35),
      ...beat("b..bb.", 1, 16, 0, 0.4),
      ...beat("C", 48, 2, 0, 0.35),
    ],
  };
}

// ================================================================ king

export const KING_CHORDS = "Cm:4 Gb:4 Fm:4 G:4 Ab:4 Db:4 Fm:2 G:2 Cm:4";

/** "The Dragon King": ancient and vast, C minor, 54. The DRAGON motif broad in low brass,
 * horns and choir over an organ, its tritone set on a full Gb major chord; timpani and a
 * tolling bell. */
function king(): Song {
  const ch = chart(KING_CHORDS);
  const theme = line(
    bars(
      4,
      // DRAGON, majestic
      "C4:2 Db4:1 C4:1",
      "Gb4:4",
      "F4:1.5 Ab4:.5 C5:2",
      "B4:2 D5:1 G4:1",
      "C5:2 Db5:1 C5:1",
      "Ab4:2 F4:2",
      "F4:1 Ab4:1 G4:1 D4:1",
      "Eb4:1 D4:1 C4:2",
    ),
    0,
    0.85,
  );
  return {
    id: "king",
    title: "The Dragon King",
    role: "Cutscenes",
    bpm: 54,
    beats: 32,
    intro: 1,
    peak: 0.83,
    loop: true,
    stems: [],
    parts: [
      // Intro: a timpani roll swelling into the first chord.
      part("timpani", 0.8, roll(36, -1, 1, 0.125, 0.3, 0.9)),
      part("brass", 0.9, theme),
      part("horn", 0.9, shift(theme, 0, -12)),
      part("strings", 0.5, shift(theme, 0, -12)),
      part("choir", 0.8, between(theme, 16, 32)),
      part("organ", 0.95, pads(ch, 48, 4, 0.55)),
      part("organ", 0.6, bassLine(ch, [[0, 3.9, "R"]], 36, 0.6)),
      part("choir", 0.5, pads(ch, 55, 4, 0.45)),
      part("drone", 0.45, bassLine(ch, [[0, 3.9, "R"]], 24, 0.5)),
      part(
        "timpani",
        0.9,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [2, 1, "5"],
          ],
          36,
          0.8,
        ),
      ),
      part("timpani", 0.6, roll(43, 15, 1, 0.125, 0.25, 0.8)),
      part("timpani", 0.6, roll(43, 31, 1, 0.125, 0.25, 0.8)),
      part("bell", 0.45, arpeggio(ch, 4, [0], 48, 3.5, 0.6)),
      ...beat("C", 16, 2, 0, 0.4),
    ],
  };
}

// ================================================================ suspense

/** "Something's Wrong": the cracked stones. No key will settle: a clock that skips a
 * tick, low strings rubbing a half step, a heartbeat, and the first notes of LUMEN's
 * motif on a celesta that never finishes them. Quiet. 90 BPM. */
function suspense(): Song {
  const strings = line("A2:8 Ab2:8 A2:8 G#2:4 G2:4", 0, 0.55);
  const upper = line("E4:8 F4:8 E4:8 Eb4:8", 0, 0.45);
  const high = line("r:4 B5:4 C6:8 r:4 Bb5:4 B5:8", 0, 0.3);
  return {
    id: "suspense",
    title: "Something's Wrong",
    role: "Cutscenes",
    bpm: 90,
    beats: 32,
    intro: 1,
    loop: true,
    peak: 0.5,
    stems: [],
    parts: [
      part("woodblock", 0.4, line("F6:.5", -1, 0.5)),
      part("harp", 0.6, line("A2:1", -1, 0.6)),
      // The clock, missing a tick now and then.
      part("woodblock", 0.35, clock(0, 32, 96, 91, 0.45, [6, 14, 15, 27])),
      part("strings", 0.9, strings),
      part("strings", 0.6, upper),
      part("strings", 0.25, high),
      part("pad", 0.4, line("A3:16 Bb3:16", 0, 0.4)),
      // LUMEN's first notes, unanswered, then sunk a half step.
      part("celesta", 0.9, line("A5:.5 F#6:1 G#6:.5", 8, 0.55)),
      part("celesta", 0.9, line("Ab5:.5 F6:1 G6:.5", 24, 0.5)),
      part("harp", 0.5, line("E3:1 r:7 F3:1 r:7 E3:1 r:7 Eb3:1 r:3 D3:1 r:3", 0, 0.5)),
      part("tom", 0.6, line("A1:.5 A1:.5 r:3", 0, 0.6)),
      part("tom", 0.6, line("A1:.5 A1:.5 r:3", 8, 0.6)),
      part("tom", 0.6, line("A1:.5 A1:.5 r:3", 16, 0.6)),
      part("tom", 0.6, line("A1:.5 A1:.5 r:3", 24, 0.65)),
      part("tom", 0.45, line("A1:.5 A1:.5 r:3", 28, 0.6)),
      part("riser", 0.3, line("A3:3.5", 28, 0.45)),
    ],
  };
}

// ================================================================ court

/** 3/4: a sarabande, the weight on the second beat. */
export const COURT_CHORDS =
  "Dm:3 Dm:3 Bb:3 A:3 Gm:3 Dm:3 Eb:3 A:3 Gm:3 Eb:3 Dm:3 A:3 Bb:3 G:3 A:3 A:3";

/** "The Dragon Court": grand and dangerous, a sarabande in D minor, 84. Strings and a
 * glittering celesta lead the dance; low brass slips the DRAGON motif in beneath it,
 * the second time onto a tritone. Timpani, brass on the heavy second beats. */
function court(): Song {
  const ch = chart(COURT_CHORDS);
  const dance = line(
    bars(
      3,
      "D5:1 F5:1.5 E5:.5",
      "D5:1 A4:2",
      "Bb4:1 D5:1.5 F5:.5",
      "E5:1 C#5:2",
      "G5:1 Bb5:1.5 A5:.5",
      "F5:1 D5:1.5 F5:.5",
      "Eb5:1 G5:1.5 Bb5:.5",
      "A5:1 G5:.5 F5:.5 E5:1",
      "Bb5:1 D6:1.5 C6:.5",
      "Bb5:1 G5:2",
      "A5:1 F5:1.5 D5:.5",
      "E5:1 C#5:1.5 E5:.5",
      "D6:1 Bb5:1.5 F5:.5",
      "G5:1 B5:1.5 D6:.5",
      "C#6:1 E6:1.5 D6:.5",
      "C#6:1 A5:2",
    ),
    0,
    0.8,
  );
  // DRAGON, beneath the dance.
  const brass = line(bars(3, "D4:1 Eb4:1.5 D4:.5", "Ab4:3"), 24, 0.8);
  const brass2 = line(bars(3, "F4:1 Gb4:1.5 F4:.5", "B4:3"), 36, 0.85);
  const sarabande: [number, number, string][] = [
    [0, 1, "R"],
    [1, 1.5, "5"],
    [2.5, 0.5, "R"],
  ];
  return {
    id: "court",
    title: "The Dragon Court",
    role: "Cutscenes",
    bpm: 84,
    beats: 48,
    intro: 3,
    peak: 0.83,
    loop: true,
    stems: [],
    parts: [
      // Intro: a herald's call.
      part("brass", 0.9, line("D4:.33 D4:.33 D4:.34 A4:2", -3, 0.8)),
      part("timpani", 0.8, line("D2:1 A1:1 D2:1", -3, 0.7)),
      part("strings", 1, dance),
      part("celesta", 0.4, dance),
      part("flute", 0.35, between(dance, 24, 48)),
      part("brass", 0.95, [...brass, ...brass2]),
      part("horn", 0.7, shift([...brass, ...brass2], 0, -12)),
      part("brass", 0.4, stabs(ch, [1], 55, 1.3, 0.55)),
      part("horn", 0.45, pads(ch, 50, 3, 0.45)),
      part("pad", 0.35, pads(ch, 57, 3, 0.4)),
      part("pizz", 0.7, bassLine(ch, sarabande, 38, 0.75)),
      part(
        "bass",
        0.7,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [1, 1.5, "R"],
          ],
          26,
          0.7,
        ),
      ),
      part("timpani", 0.75, bassLine(ch, [[0, 1, "R"]], 36, 0.7)),
      part("bell", 0.25, arpeggio(ch, 3, [0], 62, 2.5, 0.45)),
      ...beat("C", 24, 2, 0, 0.4),
    ],
  };
}

// ================================================================ shatter

/** "The Shattering": Lumen strikes the Heart Stone. LUMEN's motif twisted by tritones on
 * the celesta, then again and faster as the DRAGON motif rises under it; a rush, the blast,
 * and a bell left ringing into silence. Plays once. 80 BPM. */
function shatter(): Song {
  const twisted = line(
    bars(
      4,
      // LUMEN, twisted
      "A4:.5 F5:1 G#5:.5 Eb5:1 A5:1",
      "r:4",
      "A4:.5 F5:1 G#5:.5 Eb5:1 A5:1",
      "Ab4:.5 E5:1 G5:.5 D5:.5 Ab5:.5 r:1",
    ),
    0,
    0.75,
  );
  const harp = line(bars(4, "r:4", "A3:.5 F4:1 G#4:.5 Eb4:1 A4:1", "r:4", "r:4"), 0, 0.6);
  // The build: fragments of both motifs piling in, faster.
  const strings = line(
    bars(
      4,
      "A4:.25 F5:.25 G#5:.25 Eb5:.25 A4:.25 F5:.25 G#5:.25 Eb5:.25 A4:.25 F5:.25 G#5:.25 Eb5:.25 Bb4:.25 F#5:.25 A5:.25 E5:.25",
      "Bb4:.25 F#5:.25 A5:.25 E5:.25 B4:.25 G5:.25 Bb5:.25 F5:.25 C5:.25 G#5:.25 B5:.25 F#5:.25 C#5:.25 A5:.25 C6:.25 G5:.25",
    ),
    8,
    0.6,
  );
  // DRAGON, rising underneath.
  const brass = line(bars(4, "D3:1 Eb3:1 D3:1 G#3:1", "E3:1 F3:1 E3:1 A#3:1"), 8, 0.85);
  const hit = 16;
  const cluster = (inst: InstrumentId, gain: number, pitches: string[], d: number, v: number) =>
    part(
      inst,
      gain,
      pitches.map((p) => ({ ...line(`${p}:${d}`, hit, v)[0]! })),
    );
  return {
    id: "shatter",
    title: "The Shattering",
    role: "Cutscenes",
    bpm: 80,
    beats: 40,
    intro: 1,
    loop: false,
    stems: [],
    parts: [
      // Intro: a low harp and a bell, Lumen's note, before the motif.
      part("bell", 0.7, line("A5:1", -1, 0.6)),
      part("harp", 0.9, line("D3:.5 A3:.5", -1, 0.7)),
      part("drone", 0.4, line("D2:16", 0, 0.5)),
      part("pad", 0.6, line("[D3,G#3,D4]:8 [D3,A3,Eb4]:8", 0, 0.45)),
      part("celesta", 1, twisted),
      part("bell", 0.3, twisted),
      part("harp", 0.8, harp),
      part("strings", 0.9, dyn(strings, 1.1, 0)),
      part("brass", 0.8, brass),
      part("horn", 0.7, shift(brass, 0, -12)),
      part("timpani", 0.8, roll(38, 8, 8, 0.125, 0.15, 0.95)),
      part("snare", 0.4, roll(0, 12, 4, 0.125, 0.2, 0.9)),
      part("riser", 0.8, line("D4:8", 8, 0.9)),
      // The blast.
      cluster("brass", 1, ["D3", "G#3", "D4", "Eb4", "A4"], 3, 1),
      cluster("choir", 0.9, ["D4", "G#4", "Eb5", "A5"], 6, 0.9),
      cluster("strings", 0.8, ["D2", "D3", "G#3"], 6, 0.9),
      part("timpani", 1, line("D2:2", hit, 1)),
      part("kick", 1, line("C2:1", hit, 1)),
      part("tom", 0.9, line("D2:1", hit, 1)),
      part("crash", 0.9, line("C4:4", hit, 1)),
      part("crash", 0.6, line("C4:4", hit + 0.06, 0.9)),
      part("drone", 0.5, line("D1:12", hit, 0.7)),
      // Then the ring of it: a bell, high strings, LUMEN's first two notes, alone.
      part("bell", 0.6, line("A6:8", hit + 4, 0.55)),
      part("strings", 0.25, line("A6:12 r:4", hit + 4, 0.35)),
      part("celesta", 0.6, line("A5:.5 F6:3.5", 32, 0.35)),
    ],
  };
}

// ================================================================ false_victory

export const VICTORY_CHORDS =
  "C:4 G:4 Am:4 F:4 C:4 F:4 G:4 G:4 C:4 Em:4 F:4 Gsus4:2 G:2 Am:4 F:4 G:4 C:4";

/** "Victory!": the crews cheer, C major, 120. The PACT motif in triumphant brass, then the
 * horns and strings, over timpani, snare and choir: everything right, a little too bright
 * (the last bar slips a Db into the bass). */
function falseVictory(): Song {
  const ch = chart(VICTORY_CHORDS);
  const brass = line(
    bars(
      4,
      // PACT
      "G4:.5 C5:.5 D5:.5 E5:1.5 D5:.5 C5:.5",
      "G5:2.5 F5:.5 E5:.5 D5:.5",
      "C5:.5 E5:.5 A5:2 G5:.5 E5:.5",
      "F5:1.5 A5:.5 C6:2",
      "G5:.5 C6:.5 D6:.5 E6:1.5 D6:.5 C6:.5",
      "C6:1.5 A5:.5 F5:2",
      "D6:1 B5:.5 G5:.5 D6:1 F6:1",
      "D6:2 B5:1 G5:1",
    ),
    0,
    0.88,
  );
  const second = line(
    bars(
      4,
      // PACT, then again from F, its leap landing on a suspension
      "G4:.5 C5:.5 D5:.5 E5:1.5 D5:.5 C5:.5",
      "G5:2 E5:1 B4:1",
      "C5:.5 F5:.5 G5:.5 A5:1.5 G5:.5 F5:.5",
      "C6:2 B5:2",
      "A5:1 C6:1 E6:1 D6:.5 C6:.5",
      "C6:1 A5:1 F5:1 A5:1",
      "B5:1 D6:1 G6:1 F6:1",
      "E6:3! r:1",
    ),
    32,
    0.88,
  );
  const march: [number, number, string][] = [
    [0, 1, "R"],
    [1, 1, "5"],
    [2, 1, "R"],
    [3, 1, "5"],
  ];
  const bass = bassLine(ch, march, 36, 0.85).map((n) => (n.t === 63 ? { ...n, m: 37 } : n));
  return {
    id: "false_victory",
    title: "Victory!",
    role: "Cutscenes",
    bpm: 120,
    beats: 64,
    intro: 2,
    loop: true,
    stems: [],
    parts: [
      part("snare", 0.5, roll(0, -2, 2, 0.125, 0.3, 0.9)),
      part("timpani", 0.8, line("G2:.5 G2:.5 G2:.5 G2:.5", -2, 0.8)),
      part("brass", 1, brass),
      part("horn", 0.5, shift(brass, 0, -12)),
      part("horn", 1, second),
      part("brass", 0.6, second),
      part("strings", 0.6, shift(second, 0, 12)),
      part("strings", 0.5, arpeggio(ch, 0.5, [0, 1, 2, 3, 2, 1, 2, 1], 55, 0.45, 0.5)),
      part(
        "choir",
        0.5,
        pads(
          ch.filter((c) => c.t >= 32),
          55,
          4,
          0.5,
        ),
      ),
      part("pad", 0.35, pads(ch, 55, 4, 0.4)),
      part("bell", 0.3, arpeggio(ch, 1, [3, 4], 72, 0.8, 0.4)),
      part("bass", 1, bass),
      part(
        "timpani",
        0.7,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [2, 1, "5"],
          ],
          36,
          0.7,
        ),
      ),
      ...beat("S.s.S.ssS.s.S.s.", 0.25, 16, 0, 0.45),
      ...beat("K.......K.......", 0.25, 16, 0, 0.6),
      ...beat("C", 32, 2, 0, 0.6),
      ...beat("C", 16, 4, 0, 0.3),
    ],
  };
}

// ================================================================ rage

export const RAGE_CHORDS =
  "Cm:4 Cm:4 Db:4 Cm:4 Cm:4 Cm:4 Gb:4 G:4 Ab:4 Gb:4 Cm:4 Db:4 Ab:4 Gb:4 G:4 G:4";

/** "Rage": the dragons unleashed, C minor, 152, faster and harder than "The Dragon's
 * Shadow". The DRAGON motif hammered in brass and horns, then screamed up high by the
 * strings, over a sixteenth-note string ostinato that keeps biting a half step, war drums,
 * a galloping bass and a choir. */
function rage(): Song {
  const ch = chart(RAGE_CHORDS);
  const theme = line(
    bars(
      4,
      // DRAGON, hammered
      "C4:1 Db4:1 C4:1 F#4:1",
      "G4:1.5 Ab4:.5 G4:1 C4:1",
      "Db4:1 D4:1 Db4:1 G4:1",
      "Ab4:1.5 G4:.5 Eb4:1 C4:1",
      "C5:.5 Db5:.5 C5:.5 F#5:.5 G5:2",
      "Eb5:.5 D5:.5 C5:.5 G4:.5 Ab4:1 G4:1",
      "Gb4:.5 G4:.5 Gb4:.5 C5:.5 Db5:2",
      "D5:1 B4:1 G4:1 F4:1",
      "C5:2 Eb5:1 Db5:1",
      "Db5:2 C5:1 Bb4:1",
      "C5:1 Db5:1 C5:1 F#5:1",
      "Ab5:2 G5:1 F5:1",
      "Eb5:1 C5:1 Ab4:1 C5:1",
      "Db5:1 Bb4:1 Gb4:1 Bb4:1",
      "B4:1 C5:1 D5:1 F5:1",
      "G5:1 Ab5:1 G5:1 D5:1",
    ),
    0,
    0.9,
  );
  const gallop: [number, number, string][] = [
    [0, 0.5, "R"],
    [0.5, 0.25, "R"],
    [0.75, 0.25, "R"],
    [1, 0.5, "8"],
    [1.5, 0.5, "R"],
    [2, 0.5, "R"],
    [2.5, 0.25, "R"],
    [2.75, 0.25, "R"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "rage",
    title: "Rage",
    role: "Cutscenes",
    bpm: 152,
    beats: 64,
    intro: 2,
    loop: true,
    stems: [],
    parts: [
      ...beat("O.o.OoOoOOOOOOOO", 0.125, 1, -2, 0.75),
      part("brass", 0.9, line("G3:1.5 G3:.5", -2, 0.8)),
      part("brass", 1, theme),
      part("horn", 0.8, shift(theme, 0, -12)),
      part("strings", 0.55, shift(between(theme, 16, 32), 0, 12)),
      part("strings", 0.65, ostinato(ch, [0, 12, 0, 1], 0.25, 48, 0.2, 0.6)),
      part("pizz", 0.35, ostinato(ch, [0, 12, 0, 1], 0.25, 48, 0.2, 0.5)),
      part("choir", 0.5, pads(ch, 55, 4, 0.55)),
      part("drone", 0.5, bassLine(ch, [[0, 3.9, "R"]], 24, 0.6)),
      part("bass", 1, bassLine(ch, gallop, 24, 0.85)),
      part("timpani", 0.8, bassLine(ch, [[0, 1, "R"]], 36, 0.85)),
      part("bell", 0.35, arpeggio(ch, 4, [0], 60, 3, 0.55)),
      part("riser", 0.5, line("C4:8", 56, 0.8)),
      ...beat("K..kK..kK..kK.k.", 0.25, 16, 0, 0.85),
      ...beat("....S.......S.ss", 0.25, 16, 0, 0.6),
      ...beat("O.oOo.oOO.oOo.oo", 0.25, 16, 0, 0.6),
      ...beat("i.i.i.i.i.i.i.i.", 0.25, 16, 0, 0.35),
      ...beat("C", 16, 4, 0, 0.5),
    ],
  };
}

// ================================================================ sorrow

export const SORROW_CHORDS = "Dm:4 Bb:4 Gm:4 A:4 Dm:4 F:4 Gm:4 Asus4:2 A:2";

/** "Ashes": waking in a cage among the ruins, D minor, 60. LUMEN's motif in minor, falling
 * where it used to rise, in low strings, then a fragile broken echo on the celesta, then a
 * clarinet; a harp, a mourning bell, a breath of strings. */
function sorrow(): Song {
  const ch = chart(SORROW_CHORDS);
  const strings = line(
    bars(
      4,
      // LUMEN, in minor, falling
      "A4:.5 F5:1 G5:.5 E5:1 D5:1",
      "D5:3 r:1",
      "r:4",
      "E5:1.5 C#5:.5 A4:2",
      "r:4",
      "r:4",
      "r:4",
      "r:4",
    ),
    0,
    0.7,
  );
  const clarinet = line(
    bars(
      4,
      "A4:.5 F5:1 G5:.5 E5:1 C5:1",
      "A4:2 G4:1 F4:1",
      "Bb4:1.5 A4:.5 G4:1 D5:1",
      "D5:2 C#5:2",
    ),
    16,
    0.65,
  );
  const harp: Note[] = [];
  for (const c of ch) {
    const r = rolled([c], 50, 0.12, 0.5, 1);
    harp.push(...r);
    if (c.d >= 4) harp.push({ t: c.t + 2.5, d: 1, m: r.at(-1)!.m, v: 0.35 });
  }
  return {
    id: "sorrow",
    title: "Ashes",
    role: "Cutscenes",
    bpm: 60,
    beats: 32,
    intro: 1,
    loop: true,
    peak: 0.38,
    stems: [],
    parts: [
      part("harp", 0.8, line("D3:1", -1, 0.5)),
      part("strings", 1, strings),
      part("strings", 0.5, shift(between(strings, 0, 8), 0, -12)),
      // The echo: LUMEN's opening, high, broken off.
      part("celesta", 0.7, line("A5:.5 F6:1 G6:.5", 8, 0.5)),
      part("clarinet", 0.9, clarinet),
      part("harp", 0.7, harp),
      part("pad", 0.35, pads(ch, 50, 4, 0.35)),
      part("strings", 0.25, bassLine(ch, [[0, 3.9, "R"]], 38, 0.45)),
      part("bell", 0.3, line("D4:4 r:12 D4:4 r:12", 0, 0.4)),
    ],
  };
}

// ================================================================ hope

export const HOPE_CHORDS = "D:4 E/D:4 Bm:4 G:4 D/F#:4 G:4 Em7:2 A:2 D:4";

/** "The Shards": Mossback finds the pieces of the Heart Stone. The intro is the turn: LUMEN's
 * motif in D minor; then, in the loop, back in D major with its lydian sparkle restored, on a
 * flute over a harp, the strings, horns and bells gently gathering. 72 BPM. */
function hope(): Song {
  const ch = chart(HOPE_CHORDS);
  const intro = chart("Dm:4 Bb:2 A:2", -8);
  const flute = line(
    bars(
      4,
      // LUMEN, major again
      "A4:.5 F#5:1 G#5:.5 E5:1 A5:1",
      "B5:2 G#5:1 E5:1",
      "F#5:.5 D5:1 E5:.5 F#5:1 B5:1",
      "B5:1.5 A5:.5 G5:2",
      "A4:.5 F#5:1 G#5:.5 E5:1 A5:1",
      "B5:1.5 D6:.5 B5:1 G5:1",
      "G5:1 F#5:1 E5:1 C#5:1",
      "F#5:2 D5:2",
    ),
    0,
    0.75,
  );
  return {
    id: "hope",
    title: "The Shards",
    role: "Cutscenes",
    bpm: 72,
    beats: 32,
    intro: 8,
    loop: true,
    peak: 0.38,
    stems: [],
    parts: [
      // The turn: the motif in minor on the celesta, the harp climbing to the dominant.
      part("celesta", 0.9, line("A4:.5 F5:1 G5:.5 E5:1 D5:1 r:2 A4:.5 C#5:.5 E5:1", -8, 0.6)),
      part("harp", 0.6, arpeggio(intro, 0.5, [0, 1, 2, 3], 50, 0.5, 0.45)),
      part("pad", 0.35, pads(intro, 55, 4, 0.35)),
      part("flute", 1, flute),
      part("strings", 0.6, shift(between(flute, 16, 32), 0, -12)),
      part("celesta", 0.4, shift(between(flute, 16, 32), 0, 12)),
      part(
        "harp",
        0.6,
        arpeggio(
          ch.filter((c) => c.t < 16),
          0.5,
          [0, 1, 2, 3, 4, 3, 2, 1],
          50,
          0.5,
          0.5,
        ),
      ),
      part(
        "harp",
        0.6,
        arpeggio(
          ch.filter((c) => c.t >= 16),
          0.25,
          [0, 1, 2, 3, 4, 5, 4, 3],
          50,
          0.3,
          0.5,
        ),
      ),
      part(
        "strings",
        0.35,
        pads(
          ch.filter((c) => c.t >= 8),
          55,
          4,
          0.4,
        ),
      ),
      part(
        "horn",
        0.4,
        pads(
          ch.filter((c) => c.t >= 16),
          50,
          4,
          0.4,
        ),
      ),
      part("pad", 0.3, pads(ch, 57, 4, 0.35)),
      part(
        "bass",
        0.55,
        bassLine(
          ch.filter((c) => c.t >= 16),
          [
            [0, 2, "R"],
            [2, 2, "5"],
          ],
          38,
          0.6,
        ),
      ),
      part(
        "bell",
        0.25,
        arpeggio(
          ch.filter((c) => c.t >= 16),
          1,
          [3, 4, 5, 4],
          74,
          0.9,
          0.35,
        ),
      ),
      part("timpani", 0.4, roll(38, 30, 2, 0.125, 0.1, 0.5)),
    ],
  };
}

// ================================================================ new_stone

export const STONE_CHORDS = "E:4 C#m:4 A:4 B:4 E/G#:4 A:4 F#m7:2 B:2 E:4";

/** "A New Pact Stone": magic binding the crews' promise into stone, E major, 80. The choir
 * sings the PACT motif, slowly; then LUMEN's motif rings over it on celesta and bells: the
 * two themes bound together. Harp sweeps, a deep organ pedal, a swell into the loop. */
function newStone(): Song {
  const ch = chart(STONE_CHORDS);
  const choir = line(
    bars(
      4,
      // PACT, slowly
      "r:1 B4:1 E5:1 F#5:1",
      "G#5:3 F#5:1",
      "E5:1 B5:3",
      "B5:2 A5:1 F#5:1",
      "G#5:4",
      "A5:2 C#6:2",
      "B5:2 A5:1 F#5:1",
      "G#5:4",
    ),
    0,
    0.75,
  );
  const lumen = line(
    bars(
      4,
      // LUMEN, in E
      "B4:.5 G#5:1 A#5:.5 F#5:1 B5:1",
      "C#6:2 E6:2",
      "B5:.5 G#6:1 A#6:.5 F#6:1 B6:1",
      "G#6:4",
    ),
    16,
    0.7,
  );
  return {
    id: "new_stone",
    title: "A New Pact Stone",
    role: "Cutscenes",
    bpm: 80,
    beats: 32,
    intro: 2,
    loop: true,
    peak: 0.75,
    stems: [],
    parts: [
      part(
        "harp",
        0.8,
        line("E3:.25 B3:.25 E4:.25 G#4:.25 B4:.25 D#5:.25 E5:.25 G#5:.25", -2, 0.6),
      ),
      part("bell", 0.45, line("B5:1", -1, 0.45)),
      part("choir", 1, choir),
      part("choir", 0.55, pads(ch, 52, 4, 0.5)),
      part("strings", 0.35, shift(choir, 0, -12)),
      part("celesta", 1, lumen),
      part("bell", 0.45, lumen),
      part("harp", 0.6, arpeggio(ch, 0.25, [0, 1, 2, 3, 4, 5, 6, 5], 52, 0.4, 0.45)),
      part("organ", 0.5, bassLine(ch, [[0, 3.9, "R"]], 28, 0.5)),
      part("pad", 0.35, pads(ch, 59, 4, 0.4)),
      part("bell", 0.2, arpeggio(ch, 2, [3, 5], 76, 1.8, 0.3)),
      part("timpani", 0.45, roll(40, 28, 4, 0.125, 0.08, 0.6)),
      part("riser", 0.25, line("E4:4", 28, 0.5)),
    ],
  };
}

// ================================================================ yield

export const YIELD_CHORDS = "Cm:4 Bb:4 Ab:4 Eb:4 Eb:4 Bb:4 Ab:2 Bb:2 Eb:4";

/** "The Land Mends": a dragon yields, Eb major, 76. A horn sings the DRAGON motif softly and
 * its tritone at last resolves, up a half step; the strings warm the land; the horns and
 * flute bring in the PACT motif. Harp, a warm pad, bells like new leaves. */
function yieldCue(): Song {
  const ch = chart(YIELD_CHORDS);
  const horn = line(
    bars(
      4,
      // DRAGON, resolving: Eb E Eb A, then up to Bb
      "Eb4:1 E4:1 Eb4:1 A4:1",
      "Bb4:3 r:1",
      "r:4",
      "r:4",
      // PACT
      "Bb4:.5 Eb5:.5 F5:.5 G5:1.5 F5:.5 Eb5:.5",
      "Bb5:3 Ab5:1",
      "G5:1 F5:1 F5:1 D5:1",
      "Eb5:4",
    ),
    0,
    0.75,
  );
  const strings = line(bars(4, "C5:1.5 Bb4:.5 Ab4:1 Eb5:1", "Eb5:2 Bb4:2"), 8, 0.7);
  return {
    id: "yield",
    title: "The Land Mends",
    role: "Cutscenes",
    bpm: 76,
    beats: 32,
    intro: 1,
    loop: true,
    peak: 0.5,
    stems: [],
    parts: [
      part("harp", 0.7, line("Bb3:.25 Eb4:.25 G4:.25 Bb4:.25", -1, 0.55)),
      part("horn", 1, horn),
      part("flute", 0.55, shift(between(horn, 16, 32), 0, 12)),
      part("strings", 0.9, strings),
      part("strings", 0.35, pads(ch, 55, 4, 0.4)),
      part("pad", 0.35, pads(ch, 51, 4, 0.4)),
      part("harp", 0.55, arpeggio(ch, 0.5, [0, 1, 2, 3, 4, 3, 2, 1], 51, 0.5, 0.45)),
      part(
        "bass",
        0.6,
        bassLine(
          ch,
          [
            [0, 2, "R"],
            [2, 2, "5"],
          ],
          39,
          0.6,
        ),
      ),
      part(
        "celesta",
        0.45,
        line("r:12 G6:.5 Bb6:.5 Eb7:1 r:2 r:12 G6:.5 Bb6:.5 Eb7:1 r:2", 0, 0.45),
      ),
      part("timpani", 0.35, roll(39, 30, 2, 0.125, 0.08, 0.45)),
    ],
  };
}

// ================================================================ confession

export const CONFESSION_CHORDS = "Fm:4 Db:4 Bbm:4 C:4 Ab:4 Db:4 Bbm:2 Csus4:2 F:4";

/** "The Confession": Mossback owns up and breaks the horn. F minor, 63. One horn, alone over
 * hushed strings: the PACT motif, slowly and haltingly, in minor, its leap only arriving a
 * bar late; at the end a plain F major, honest. */
function confession(): Song {
  const ch = chart(CONFESSION_CHORDS);
  const horn = line(
    bars(
      4,
      // PACT, in minor, halting
      "C4:1 F4:1 G4:1 Ab4:1",
      "r:1 G4:1 F4:2",
      "r:2 Bb4:1 Db5:1",
      "C5:3 r:1",
      "C5:1.5 Bb4:.5 Ab4:1 Eb4:1",
      "F4:2 Ab4:1 F4:1",
      "Bb3:1 Db4:1 F4:1 G4:1",
      "A4:4",
    ),
    0,
    0.8,
  );
  return {
    id: "confession",
    title: "The Confession",
    role: "Cutscenes",
    bpm: 63,
    beats: 32,
    intro: 1,
    loop: true,
    peak: 0.27,
    stems: [],
    parts: [
      // Intro: the strings breathe in, an F minor chord swelling.
      part("strings", 0.7, line("[F2,C3,Ab3]:1", -1, 0.6)),
      part("horn", 1.1, horn),
      part("strings", 0.55, pads(ch, 48, 4, 0.4)),
      part("strings", 0.35, bassLine(ch, [[0, 3.9, "R"]], 36, 0.45)),
      part("pad", 0.25, pads(ch, 53, 4, 0.3)),
      part(
        "harp",
        0.45,
        arpeggio(
          ch.filter((c) => c.t >= 16),
          4,
          [0],
          53,
          3,
          0.4,
        ),
      ),
    ],
  };
}

// ================================================================ finale

export const FINALE_CHORDS =
  "D:4 E/D:4 Bm:4 G:4 D:4 E:4 A:4 A:4 G:4 A:4 F#m:4 Bm:4 G:4 E/G#:4 A:4 A:4";

/** "Lumen Returns": golden and full-grown, D major, 104. LUMEN's motif in full, in the
 * brass with the strings an octave above, lydian sparkle and all; then the horns sing the
 * PACT motif against it. Choir, harp, timpani, a march snare, bells. */
function finale(): Song {
  const ch = chart(FINALE_CHORDS);
  const brass = line(
    bars(
      4,
      // LUMEN, in full
      "A4:.5 F#5:1 G#5:.5 E5:1 A5:1",
      "B5:1.5 G#5:.5 E5:2",
      "F#5:.5 D5:1 E5:.5 F#5:1 B5:1",
      "D6:2 B5:1 G5:1",
      "A4:.5 F#5:1 G#5:.5 E5:1 A5:1",
      "B5:1.5 G#5:.5 B5:1 E6:1",
      "C#6:2 B5:1 A5:1",
      "A5:3 r:1",
      "B5:4",
      "C#6:4",
      // LUMEN, from C#
      "C#5:.5 A5:1 B5:.5 F#5:1 C#6:1",
      "D6:2 C#6:1 B5:1",
      "B5:4",
      "B5:2 E6:2",
      // LUMEN, over the dominant
      "A4:.5 F#5:1 G#5:.5 E5:1 A5:1",
      "E6:2 C#6:1 A5:1",
    ),
    0,
    0.88,
  );
  const horns = line(
    bars(
      4,
      // PACT, in D, then in G
      "A4:.5 D5:.5 E5:.5 F#5:1.5 E5:.5 D5:.5",
      "A5:4",
      "r:4",
      "r:4",
      "D5:.5 G5:.5 A5:.5 B5:1.5 A5:.5 G5:.5",
      "G#5:4",
      "r:4",
      "r:4",
    ),
    32,
    0.85,
  );
  const march: [number, number, string][] = [
    [0, 1, "R"],
    [1, 0.5, "5"],
    [1.5, 0.5, "R"],
    [2, 1, "8"],
    [3, 0.5, "5"],
    [3.5, 0.5, "A"],
  ];
  return {
    id: "finale",
    title: "Lumen Returns",
    role: "Cutscenes",
    bpm: 104,
    beats: 64,
    intro: 2,
    loop: true,
    stems: [],
    parts: [
      part("timpani", 0.8, roll(45, -2, 2, 0.125, 0.2, 0.9)),
      part(
        "harp",
        0.8,
        line("D4:.25 F#4:.25 A4:.25 C#5:.25 E5:.25 G#5:.25 A5:.25 C#6:.25", -2, 0.6),
      ),
      part("brass", 1, brass),
      part("strings", 0.6, shift(between(brass, 0, 32), 0, 12)),
      part("strings", 0.6, between(brass, 32, 64)),
      part("horn", 1, horns),
      part("flute", 0.4, shift(horns, 0, 12)),
      part("choir", 0.6, pads(ch, 55, 4, 0.5)),
      part("harp", 0.5, arpeggio(ch, 0.25, [0, 1, 2, 3, 4, 3, 2, 1], 50, 0.3, 0.45)),
      part("strings", 0.4, arpeggio(ch, 0.5, [0, 2, 1, 2], 50, 0.45, 0.45)),
      part("bass", 1, bassLine(ch, march, 38, 0.85)),
      part(
        "timpani",
        0.75,
        bassLine(
          ch,
          [
            [0, 1, "R"],
            [2, 1, "5"],
          ],
          38,
          0.75,
        ),
      ),
      part("bell", 0.3, arpeggio(ch, 1, [3, 4], 74, 0.8, 0.4)),
      ...beat("S.s.S.s.S.s.S.ss", 0.25, 16, 0, 0.4),
      ...beat("K.......K.......", 0.25, 16, 0, 0.55),
      ...beat("C", 32, 2, 0, 0.6),
      ...beat("C", 8, 8, 0, 0.25),
    ],
  };
}

// ================================================================ home

/** "Home Again": the ending, back at the festival. The festival's tune, a little slower
 * and warmer: flute and strings on it, the accordion and harp behind, the PACT motif in
 * the horns completed at last, and LUMEN's motif as the last word on the celesta. 124. */
function home(): Song {
  const ch = chart(FESTIVAL_CHORDS);
  const mel = line(FESTIVAL_MELODY, 0, 0.78).filter((n) => n.t < 60);
  return {
    id: "home",
    title: "Home Again",
    role: "Cutscenes",
    bpm: 124,
    beats: 64,
    intro: 2,
    peak: 0.56,
    loop: true,
    stems: [],
    parts: [
      part("harp", 0.8, line("C4:.25 E4:.25 G4:.25 C5:.25 E5:.25 G5:.25 C6:.25 E6:.25", -2, 0.6)),
      part("flute", 1, mel),
      part("strings", 0.55, shift(mel, 0, -12)),
      part("steelpan", 0.35, between(mel, 0, 32)),
      // PACT, whole at last, in the horns with the flute.
      part("horn", 0.9, line(bars(4, "G4:.5 C5:.5 D5:.5 E5:1.5 D5:.5 C5:.5", "G5:4"), 32, 0.75)),
      // LUMEN, in C, the last word.
      part("celesta", 1, line("G4:.5 E5:1 F#5:.5 D5:1 G5:1", 60, 0.7)),
      part("bell", 0.4, line("G4:.5 E5:1 F#5:.5 D5:1 G5:1", 60, 0.5)),
      part("accordion", 0.45, line(FESTIVAL_COUNTER, 16, 0.6)),
      part("accordion", 0.3, stabs(ch, [1, 3], 60, 0.4, 0.5)),
      part("harp", 0.5, arpeggio(ch, 0.5, [0, 1, 2, 3, 2, 1, 2, 1], 55, 0.5, 0.5)),
      part("pad", 0.35, pads(ch, 55, 4, 0.4)),
      part("bass", 0.9, bassLine(ch, bounce, 36, 0.8)),
      ...beat("K.......k.......", 0.25, 16, 0, 0.55),
      ...beat("h.hhh.hhh.hhh.hh", 0.25, 16, 0, 0.3),
      ...beat("..b...b...b.b.b.", 0.25, 16, 0, 0.35),
      ...beat("........t.......", 0.25, 16, 0, 0.3),
      ...beat("C", 64, 1, 0, 0.35),
    ],
  };
}

// ================================================================ the cues

/** Every cutscene cue, by id (the ids the staged scenes use). */
export function cues(): Record<string, Song> {
  const list = [
    festival(),
    lumen(),
    smugglers(),
    conquered(),
    rimefang(),
    scorchwind(),
    tidewyrm(),
    king(),
    suspense(),
    court(),
    shatter(),
    falseVictory(),
    rage(),
    sorrow(),
    hope(),
    newStone(),
    yieldCue(),
    confession(),
    finale(),
    home(),
  ];
  return Object.fromEntries(list.map((s) => [s.id, s]));
}

/** The cue ids, in story order. */
export const CUE_IDS = [
  "festival",
  "lumen",
  "smugglers",
  "conquered",
  "rimefang",
  "scorchwind",
  "tidewyrm",
  "king",
  "suspense",
  "court",
  "shatter",
  "false_victory",
  "rage",
  "sorrow",
  "hope",
  "new_stone",
  "yield",
  "confession",
  "finale",
  "home",
] as const;
