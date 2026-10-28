/**
 * A tiny notation for writing the soundtrack in code.
 *
 * Melodies are written as note:length tokens, lengths in beats:
 *
 *   seq("C5:.5 F5:.5 A5:1 r:1 [F4,A4,C5]:2 G5:1!")
 *
 * `r` is a rest, `[..]` a chord, and a trailing `!` accents a note. Chord charts
 * ("F:4 Am:4 Bb:2 C7:2") drive generated bass lines, arpeggios and pads, and drum
 * patterns are a step grid ("k.h.s.h."). Everything comes out as plain note events
 * (time and length in beats, MIDI pitch, velocity) that the renderer plays.
 */
import type { InstrumentId } from "./instruments";

export interface Note {
  /** Start, beats from the start of the song. */
  t: number;
  /** Length, beats. */
  d: number;
  /** MIDI note number (drums: 0 = the drum's own pitch). */
  m: number;
  /** 0..1 */
  v: number;
}

export interface Part {
  inst: InstrumentId;
  /** Which stem (layer) it belongs to. "base" always plays. */
  stem: string;
  gain: number;
  notes: Note[];
}

export interface Song {
  id: string;
  title: string;
  /** What it's for, shown in the music player. */
  role: string;
  bpm: number;
  /** Length of the loop (or the whole piece), beats. */
  beats: number;
  loop: boolean;
  /** Stems other than "base" start silent and are faded in by the game. */
  stems: string[];
  parts: Part[];
  /**
   * Beats of lead-in played once before the loop (cutscene cues): notes at negative
   * times (-intro..0, "base" stem) are the intro, and the loop is beats 0..`beats`.
   * A piece with an intro enters on the beat of the piece it replaces.
   */
  intro?: number;
  /** Loudest sample after rendering (default 0.85): quiet cues stay quiet. */
  peak?: number;
}

const NAMES: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

/** "C4" = 60, "F#5" = 78, "Bb3" = 58. */
export function midi(name: string): number {
  const m = /^([A-G])(#|b)?(-?\d)$/.exec(name.trim());
  if (!m) throw new Error(`Bad note "${name}"`);
  const acc = m[2] === "#" ? 1 : m[2] === "b" ? -1 : 0;
  return 12 * (Number(m[3]) + 1) + NAMES[m[1]!]! + acc;
}

/** Parse a melody into notes, starting at beat `start`. */
export function seq(src: string, start = 0, vel = 0.78): Note[] {
  const out: Note[] = [];
  let t = start;
  for (const tok of src.trim().split(/\s+/)) {
    if (!tok) continue;
    const accent = tok.endsWith("!");
    const body = accent ? tok.slice(0, -1) : tok;
    const i = body.lastIndexOf(":");
    if (i < 0) throw new Error(`Missing length in "${tok}"`);
    const what = body.slice(0, i);
    const d = Number(body.slice(i + 1));
    if (!(d > 0)) throw new Error(`Bad length in "${tok}"`);
    if (what !== "r") {
      const pitches = what.startsWith("[") ? what.slice(1, -1).split(",") : [what];
      for (const p of pitches)
        out.push({ t, d, m: midi(p), v: Math.min(1, vel + (accent ? 0.15 : 0)) });
    }
    t += d;
  }
  return out;
}

/** Total length of a melody string, beats. */
export function seqLength(src: string): number {
  return src
    .trim()
    .split(/\s+/)
    .reduce((s, tok) => s + Number(tok.replace(/!$/, "").split(":").at(-1)), 0);
}

const QUALITY: Record<string, number[]> = {
  "": [0, 4, 7],
  m: [0, 3, 7],
  "7": [0, 4, 7, 10],
  m7: [0, 3, 7, 10],
  maj7: [0, 4, 7, 11],
  sus4: [0, 5, 7],
  dim: [0, 3, 6],
  "6": [0, 4, 7, 9],
};

export interface Chord {
  /** Pitch class of the root, 0..11. */
  root: number;
  /** Bass pitch class (slash chords), 0..11. */
  bass: number;
  /** Intervals above the root. */
  tones: number[];
  t: number;
  d: number;
}

function pitchClass(s: string) {
  const acc = s[1] === "#" ? 1 : s[1] === "b" ? -1 : 0;
  return (NAMES[s[0]!]! + acc + 12) % 12;
}

/** A chord chart, "F:4 Am:4 Bb:2 C7:2 G/B:4", from beat `start`. */
export function chart(src: string, start = 0): Chord[] {
  const out: Chord[] = [];
  let t = start;
  for (const tok of src.trim().split(/\s+/)) {
    const [name, len] = tok.split(":");
    const m = /^([A-G][#b]?)(m7|maj7|sus4|dim|m|7|6)?(?:\/([A-G][#b]?))?$/.exec(name!);
    if (!m) throw new Error(`Bad chord "${tok}"`);
    const root = pitchClass(m[1]!);
    const d = Number(len);
    out.push({ root, bass: m[3] ? pitchClass(m[3]) : root, tones: QUALITY[m[2] ?? ""]!, t, d });
    t += d;
  }
  return out;
}

/** The chord's notes as MIDI pitches, voiced upward from the lowest pitch >= `floor`. */
export function voicing(c: Chord, floor: number): number[] {
  let base = floor + ((((c.root - floor) % 12) + 12) % 12);
  if (base - floor > 7) base -= 12; // keep voicings close to the floor
  if (base < floor - 2) base += 12;
  return c.tones.map((i) => base + i);
}

/** Lowest MIDI pitch of a pitch class at or above `floor`. */
export function above(pc: number, floor: number) {
  return floor + ((((pc - floor) % 12) + 12) % 12);
}

/**
 * A bass line: per chord, a pattern of [beat offset, length, degree] where degree is
 * "R" (the bass note), "5" (fifth), "8" (octave), "3" (third), "A" (approach: a step
 * below the next chord's root).
 */
export function bassLine(
  chords: Chord[],
  pattern: [number, number, string][],
  floor: number,
  vel = 0.8,
): Note[] {
  const out: Note[] = [];
  chords.forEach((c, i) => {
    const root = above(c.bass, floor);
    const next = chords[(i + 1) % chords.length]!;
    for (const [off, d, deg] of pattern) {
      if (off >= c.d) continue;
      let m = root;
      if (deg === "5") m = above((c.root + 7) % 12, floor);
      if (deg === "8") m = root + 12;
      if (deg === "3") m = above((c.root + c.tones[1]!) % 12, floor);
      if (deg === "A") m = above(next.bass, floor) - 1;
      out.push({ t: c.t + off, d: Math.min(d, c.d - off), m, v: vel });
    }
  });
  return out;
}

/**
 * Arpeggios over a chart: a note every `step` beats, walking the voicing by `order`
 * (indices into the voicing; 3 and up wrap an octave higher).
 */
export function arpeggio(
  chords: Chord[],
  step: number,
  order: number[],
  floor: number,
  length = step,
  vel = 0.7,
): Note[] {
  const out: Note[] = [];
  for (const c of chords) {
    const v = voicing(c, floor);
    let k = 0;
    for (let t = 0; t < c.d - 1e-6; t += step, k++) {
      const idx = order[k % order.length]!;
      const m = v[idx % v.length]! + 12 * Math.floor(idx / v.length);
      out.push({ t: c.t + t, d: length, m, v: vel * (k % 2 ? 0.85 : 1) });
    }
  }
  return out;
}

/** Sustained chords (pads, held brass), each re-struck every `every` beats. */
export function pads(chords: Chord[], floor: number, every = 4, vel = 0.6): Note[] {
  const out: Note[] = [];
  for (const c of chords) {
    for (let t = 0; t < c.d - 1e-6; t += every) {
      for (const m of voicing(c, floor))
        out.push({ t: c.t + t, d: Math.min(every, c.d - t), m, v: vel });
    }
  }
  return out;
}

/** Off-beat chord stabs: the voicing struck at each listed beat offset within every chord. */
export function stabs(chords: Chord[], offsets: number[], floor: number, d = 0.4, vel = 0.6) {
  const out: Note[] = [];
  for (const c of chords)
    for (const off of offsets)
      if (off < c.d) for (const m of voicing(c, floor)) out.push({ t: c.t + off, d, m, v: vel });
  return out;
}

/**
 * A drum part from a step grid, repeated `times`: one character per `step` beats;
 * "." is a rest, a letter plays that drum (see `kit`), upper case is accented.
 */
export function drums(
  grid: string,
  kit: Record<string, InstrumentId>,
  step: number,
  times: number,
  start = 0,
): { inst: InstrumentId; notes: Note[] }[] {
  const byInst = new Map<InstrumentId, Note[]>();
  const len = grid.length * step;
  for (let r = 0; r < times; r++) {
    [...grid].forEach((ch, i) => {
      if (ch === "." || ch === " ") return;
      const inst = kit[ch.toLowerCase()];
      if (!inst) throw new Error(`No drum for "${ch}"`);
      const list = byInst.get(inst) ?? [];
      list.push({
        t: start + r * len + i * step,
        d: step,
        m: 0,
        v: ch === ch.toUpperCase() ? 0.95 : 0.6,
      });
      byInst.set(inst, list);
    });
  }
  return [...byInst].map(([inst, notes]) => ({ inst, notes }));
}

/** Move notes later by `beats` (and optionally transpose). */
export function shift(notes: Note[], beats: number, semis = 0): Note[] {
  return notes.map((n) => ({ ...n, t: n.t + beats, m: n.m + semis }));
}

/** Repeat a passage `times`, each `length` beats long. */
export function repeat(notes: Note[], times: number, length: number): Note[] {
  const out: Note[] = [];
  for (let i = 0; i < times; i++) out.push(...shift(notes, i * length));
  return out;
}

/** Scale velocities (and add a tiny deterministic humanising wobble). */
export function dyn(notes: Note[], scale: number, wobble = 0.06): Note[] {
  return notes.map((n, i) => ({
    ...n,
    v: Math.min(1, Math.max(0.05, n.v * scale * (1 + wobble * Math.sin(i * 12.9898)))),
  }));
}
