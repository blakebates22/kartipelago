/**
 * The soundtrack's synthesizer, in plain number crunching: every note is computed
 * straight into a Float32Array (no audio graph), so a whole piece renders in a moment,
 * the same everywhere, in a worker or in a test.
 *
 * The instruments match instruments.ts (which plays live menu sounds through Web
 * Audio): struck bars as decaying sines, plucks and winds as band-limited
 * oscillators through a swept low-pass, drums from tuned sines and filtered noise.
 */
import type { InstrumentId } from "./instruments";
import type { Note, Song } from "./score";

const TAU = Math.PI * 2;
export const midiHz = (m: number) => 440 * Math.pow(2, (m - 69) / 12);

/** A resonant RBJ biquad, recomputed as its cutoff moves. */
class Biquad {
  private b0 = 1;
  private b1 = 0;
  private b2 = 0;
  private a1 = 0;
  private a2 = 0;
  private x1 = 0;
  private x2 = 0;
  private y1 = 0;
  private y2 = 0;
  constructor(
    private type: "lp" | "hp" | "bp",
    private rate: number,
  ) {}
  set(freq: number, q: number) {
    const f = Math.min(freq, this.rate * 0.45);
    const w = (TAU * f) / this.rate;
    const cos = Math.cos(w);
    const alpha = Math.sin(w) / (2 * Math.max(0.1, q));
    const a0 = 1 + alpha;
    if (this.type === "lp") {
      this.b0 = (1 - cos) / 2 / a0;
      this.b1 = (1 - cos) / a0;
      this.b2 = this.b0;
    } else if (this.type === "hp") {
      this.b0 = (1 + cos) / 2 / a0;
      this.b1 = -(1 + cos) / a0;
      this.b2 = this.b0;
    } else {
      this.b0 = alpha / a0;
      this.b1 = 0;
      this.b2 = -alpha / a0;
    }
    this.a1 = (-2 * cos) / a0;
    this.a2 = (1 - alpha) / a0;
  }
  run(x: number) {
    const y =
      this.b0 * x + this.b1 * this.x1 + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2;
    this.x2 = this.x1;
    this.x1 = x;
    this.y2 = this.y1;
    this.y1 = y;
    return y;
  }
}

/** PolyBLEP: smooths the jump in a saw or square so it doesn't alias. */
function blep(t: number, dt: number) {
  if (t < dt) {
    const x = t / dt;
    return x + x - x * x - 1;
  }
  if (t > 1 - dt) {
    const x = (t - 1) / dt;
    return x * x + x + x + 1;
  }
  return 0;
}

class Osc {
  phase: number;
  constructor(phase = 0) {
    this.phase = phase;
  }
  /** Advance by `inc` cycles and return the waveform. */
  saw(inc: number) {
    const v = 2 * this.phase - 1 - blep(this.phase, inc);
    this.phase = (this.phase + inc) % 1;
    return v;
  }
  square(inc: number) {
    let v = this.phase < 0.5 ? 1 : -1;
    v += blep(this.phase, inc) - blep((this.phase + 0.5) % 1, inc);
    this.phase = (this.phase + inc) % 1;
    return v;
  }
  tri(inc: number) {
    const v = 1 - 4 * Math.abs(this.phase - 0.5);
    this.phase = (this.phase + inc) % 1;
    return v;
  }
  sine(inc: number) {
    const v = Math.sin(TAU * this.phase);
    this.phase = (this.phase + inc) % 1;
    return v;
  }
}

let noiseSeed = 0x2545f491;
const noise = () => {
  noiseSeed ^= noiseSeed << 13;
  noiseSeed ^= noiseSeed >>> 17;
  noiseSeed ^= noiseSeed << 5;
  return (noiseSeed >>> 0) / 2147483648 - 1;
};

interface Ctx {
  out: Float32Array;
  rate: number;
  /** Sample index the note starts at. */
  start: number;
  /** Held length, seconds. */
  dur: number;
  freq: number;
  vel: number;
  gain: number;
}

const add = (c: Ctx, i: number, v: number) => {
  const k = c.start + i;
  if (k >= 0 && k < c.out.length) c.out[k]! += v * c.gain;
};

/** Struck bar: decaying sine partials [ratio, amp, decay-multiplier]. */
function bar(c: Ctx, partials: [number, number, number][], decay: number, level: number) {
  const ring = decay * Math.min(1.8, Math.max(0.6, 400 / c.freq));
  const len = Math.ceil(ring * 6 * c.rate);
  for (const [mult, amp, d] of partials) {
    const f = c.freq * mult;
    if (f > c.rate * 0.45) continue;
    const k = Math.exp(-1 / (ring * d * c.rate));
    const inc = (TAU * f) / c.rate;
    let a = amp * level * c.vel;
    const n = Math.min(len, Math.ceil(ring * d * 7 * c.rate));
    for (let i = 0; i < n; i++) {
      const atk = i < 0.003 * c.rate ? i / (0.003 * c.rate) : 1;
      add(c, i, a * atk * Math.sin(inc * i));
      a *= k;
    }
  }
}

/** Attack/hold/release envelope value at sample i. */
function ahr(i: number, rate: number, a: number, hold: number, release: number) {
  const t = i / rate;
  if (t < a) return t / a;
  if (t < hold) return 1;
  return Math.exp(-(t - hold) / (release / 4));
}

interface SustainSpec {
  layers: { wave: "saw" | "square" | "tri" | "sine"; mult: number; amp: number; detune?: number }[];
  filter: { from: number; to: number; time: number; q: number };
  attack: number;
  release: number;
  level: number;
  vibrato?: { delay: number; rate: number; depth: number };
  breath?: number;
}

function sustained(c: Ctx, s: SustainSpec) {
  const hold = Math.max(s.attack, c.dur);
  const n = Math.ceil((hold + s.release * 2) * c.rate);
  const lp = new Biquad("lp", c.rate);
  const oscs = s.layers.map((_, i) => new Osc(i * 0.37));
  const incs = s.layers.map(
    (l) => (c.freq * l.mult * Math.pow(2, (l.detune ?? 0) / 1200)) / c.rate,
  );
  const air = s.breath ? new Biquad("bp", c.rate) : undefined;
  air?.set(Math.min(8000, c.freq * 2), 2);
  for (let i = 0; i < n; i++) {
    if (i % 16 === 0) {
      const t = i / c.rate;
      const f =
        t < s.filter.time
          ? s.filter.from + (s.filter.to - s.filter.from) * (t / s.filter.time)
          : s.filter.to;
      lp.set(f, s.filter.q);
    }
    let vib = 1;
    if (s.vibrato) {
      const t = i / c.rate;
      const depth =
        t < s.vibrato.delay ? 0 : Math.min(1, (t - s.vibrato.delay) / 0.25) * s.vibrato.depth;
      vib = 1 + depth * Math.sin(TAU * s.vibrato.rate * t);
    }
    let x = 0;
    for (let k = 0; k < oscs.length; k++) {
      const l = s.layers[k]!;
      const o = oscs[k]!;
      const inc = incs[k]! * vib;
      x +=
        l.amp *
        (l.wave === "saw"
          ? o.saw(inc)
          : l.wave === "square"
            ? o.square(inc)
            : l.wave === "tri"
              ? o.tri(inc)
              : o.sine(inc));
    }
    let y = lp.run(x) * ahr(i, c.rate, s.attack, hold, s.release) * s.level * c.vel;
    if (air && i < 0.14 * c.rate) y += air.run(noise()) * 0.05 * c.vel * (1 - i / (0.14 * c.rate));
    add(c, i, y);
  }
}

/** A filtered noise burst (drums). */
function noiseHit(
  c: Ctx,
  type: "lp" | "hp" | "bp",
  freq: number,
  q: number,
  len: number,
  level: number,
  attack = 0.001,
) {
  const f = new Biquad(type, c.rate);
  f.set(freq, q);
  const n = Math.ceil(len * 2.5 * c.rate);
  const tau = len / 3;
  for (let i = 0; i < n; i++) {
    const t = i / c.rate;
    const e = t < attack ? t / attack : Math.exp(-(t - attack) / tau);
    add(c, i, f.run(noise()) * e * level * c.vel);
  }
}

/** A sine with a pitch drop (kick, bongo, the snare's body). */
function thump(
  c: Ctx,
  from: number,
  to: number,
  drop: number,
  tau: number,
  level: number,
  wave: "sine" | "tri" = "sine",
) {
  const n = Math.ceil(tau * 7 * c.rate);
  const o = new Osc();
  for (let i = 0; i < n; i++) {
    const t = i / c.rate;
    const f = to + (from - to) * Math.exp(-t / (drop / 3));
    const v = wave === "sine" ? o.sine(f / c.rate) : o.tri(f / c.rate);
    add(c, i, v * Math.exp(-t / tau) * level * c.vel);
  }
}

/** Write one note of an instrument into `out` (mono), `gain` scaling it. */
export function renderNote(
  out: Float32Array,
  rate: number,
  inst: InstrumentId,
  timeSec: number,
  durSec: number,
  midi: number,
  vel: number,
  gain: number,
) {
  const c: Ctx = {
    out,
    rate,
    start: Math.round(timeSec * rate),
    dur: durSec,
    freq: midiHz(midi),
    vel,
    gain,
  };
  switch (inst) {
    case "marimba":
      return bar(
        c,
        [
          [1, 1, 1],
          [4, 0.22, 0.18],
          [9.8, 0.06, 0.05],
        ],
        0.28,
        0.5,
      );
    case "xylophone":
      return bar(
        c,
        [
          [1, 1, 1],
          [3, 0.35, 0.3],
          [6.2, 0.1, 0.1],
        ],
        0.12,
        0.42,
      );
    case "celesta":
      return bar(
        c,
        [
          [1, 1, 1],
          [2, 0.25, 0.6],
          [4.1, 0.12, 0.15],
        ],
        0.55,
        0.32,
      );
    case "woodblock":
      c.freq = midi > 0 ? c.freq : 1300;
      return bar(
        c,
        [
          [1, 1, 1],
          [2.7, 0.4, 0.5],
        ],
        0.035,
        0.5,
      );
    case "pizz": {
      const lp = new Biquad("lp", rate);
      const a = new Osc();
      const b = new Osc(0.3);
      const n = Math.ceil(0.6 * rate);
      const inc = c.freq / rate;
      for (let i = 0; i < n; i++) {
        const t = i / rate;
        if (i % 16 === 0)
          lp.set(
            c.freq * 1.5 + (Math.min(6000, c.freq * 7) - c.freq * 1.5) * Math.exp(-t / 0.05),
            1.5,
          );
        const x = a.saw(inc * 0.997) + b.tri(inc * 1.003);
        const e = t < 0.004 ? t / 0.004 : Math.exp(-(t - 0.004) / 0.09);
        add(c, i, lp.run(x) * e * 0.42 * vel);
      }
      return;
    }
    case "bass": {
      const lp = new Biquad("lp", rate);
      const a = new Osc();
      const b = new Osc(0.2);
      const len = Math.min(durSec, 0.9);
      const n = Math.ceil((len + 0.3) * rate);
      const inc = c.freq / rate;
      for (let i = 0; i < n; i++) {
        const t = i / rate;
        if (i % 16 === 0) lp.set(380 + 520 * Math.exp(-t / 0.12), 0.7);
        const x = a.tri(inc) + 0.35 * b.saw(inc);
        let e = t < 0.006 ? t / 0.006 : 0.35 + 0.4 * Math.exp(-(t - 0.006) / 0.12);
        if (t > len) e *= Math.exp(-(t - len) / 0.05);
        add(c, i, lp.run(x) * e * 0.75 * vel);
      }
      return;
    }
    case "flute":
      return sustained(c, {
        layers: [
          { wave: "sine", mult: 1, amp: 1 },
          { wave: "tri", mult: 1, amp: 0.25 },
          { wave: "sine", mult: 2, amp: 0.08 },
        ],
        filter: { from: 3000, to: 3000, time: 0.01, q: 0.5 },
        attack: 0.05,
        release: 0.09,
        level: 0.32,
        vibrato: { delay: 0.18, rate: 5.2, depth: 0.006 },
        breath: 1,
      });
    case "clarinet":
      return sustained(c, {
        layers: [
          { wave: "square", mult: 1, amp: 0.55 },
          { wave: "sine", mult: 1, amp: 0.6 },
        ],
        filter: { from: 1200, to: Math.min(3200, c.freq * 5), time: 0.05, q: 0.7 },
        attack: 0.04,
        release: 0.07,
        level: 0.3,
        vibrato: { delay: 0.3, rate: 4.6, depth: 0.003 },
      });
    case "brass":
      return sustained(c, {
        layers: [
          { wave: "saw", mult: 1, amp: 0.5, detune: -6 },
          { wave: "saw", mult: 1, amp: 0.5, detune: 6 },
        ],
        filter: { from: 400, to: Math.min(4200, c.freq * 6), time: 0.07, q: 1.2 },
        attack: 0.03,
        release: 0.1,
        level: 0.26,
        vibrato: { delay: 0.25, rate: 5, depth: 0.003 },
      });
    case "horn":
      return sustained(c, {
        layers: [
          { wave: "saw", mult: 1, amp: 0.45, detune: -4 },
          { wave: "tri", mult: 1, amp: 0.6, detune: 4 },
        ],
        filter: { from: 300, to: Math.min(1400, c.freq * 3), time: 0.12, q: 0.8 },
        attack: 0.09,
        release: 0.2,
        level: 0.24,
      });
    case "bassoon":
      return sustained(c, {
        layers: [
          { wave: "saw", mult: 1, amp: 0.6 },
          { wave: "square", mult: 1, amp: 0.25 },
        ],
        filter: { from: 500, to: Math.min(1100, c.freq * 4), time: 0.06, q: 3 },
        attack: 0.05,
        release: 0.08,
        level: 0.3,
        vibrato: { delay: 0.3, rate: 4.4, depth: 0.003 },
      });
    case "pad":
      return sustained(c, {
        layers: [
          { wave: "saw", mult: 1, amp: 0.4, detune: -9 },
          { wave: "saw", mult: 1, amp: 0.4, detune: 9 },
          { wave: "tri", mult: 0.5, amp: 0.3 },
        ],
        filter: { from: 900, to: 1500, time: 0.4, q: 0.5 },
        attack: 0.25,
        release: 0.45,
        level: 0.11,
      });
    case "square":
      return sustained(c, {
        layers: [{ wave: "square", mult: 1, amp: 1 }],
        filter: { from: 2600, to: 1800, time: 0.08, q: 0.5 },
        attack: 0.005,
        release: 0.05,
        level: 0.11,
      });
    case "steelpan":
      // A pan's ring: a strong fundamental, its octave and a slightly sharp twelfth,
      // with the soft "boing" of a quick pitch settle at the start.
      return bar(
        c,
        [
          [1, 1, 1],
          [2.005, 0.55, 0.7],
          [3.02, 0.22, 0.4],
          [4.1, 0.08, 0.2],
        ],
        0.42,
        0.36,
      );
    case "bell":
      // Small bells and chimes: bright, inharmonic and long.
      return bar(
        c,
        [
          [1, 1, 1],
          [2.76, 0.45, 0.6],
          [5.4, 0.22, 0.35],
          [8.9, 0.08, 0.2],
        ],
        1.1,
        0.22,
      );
    case "strings":
      return sustained(c, {
        layers: [
          { wave: "saw", mult: 1, amp: 0.45, detune: -7 },
          { wave: "saw", mult: 1, amp: 0.45, detune: 7 },
          { wave: "saw", mult: 2, amp: 0.12 },
        ],
        filter: { from: 700, to: Math.min(3600, c.freq * 4), time: 0.12, q: 0.6 },
        attack: 0.08,
        release: 0.16,
        level: 0.17,
        vibrato: { delay: 0.2, rate: 5.5, depth: 0.004 },
      });
    case "panflute": {
      // A wooden pan pipe: a soft, hollow tone with air all through it (not just at the
      // start), a little scoop up into each note and a slow, shy vibrato.
      sustained(c, {
        layers: [
          { wave: "sine", mult: 1, amp: 1 },
          { wave: "sine", mult: 2, amp: 0.12 },
          { wave: "tri", mult: 1, amp: 0.12, detune: -12 },
        ],
        filter: { from: 1800, to: 2600, time: 0.06, q: 0.4 },
        attack: 0.06,
        release: 0.12,
        level: 0.3,
        vibrato: { delay: 0.28, rate: 4.4, depth: 0.005 },
        breath: 1,
      });
      return noiseHit(c, "bp", Math.min(7000, c.freq * 1.01), 9, Math.max(0.25, c.dur), 0.07, 0.04);
    }
    case "logdrum":
      // A hollow log (slit) drum: a woody, quickly-damped tone and a knock.
      bar(
        c,
        [
          [1, 1, 1],
          [2.32, 0.3, 0.35],
          [4.95, 0.08, 0.12],
        ],
        0.2,
        0.5,
      );
      return noiseHit(c, "bp", Math.min(5000, c.freq * 3), 1.2, 0.012, 0.14);
    case "drone": {
      // A deep, buzzing drone (a long horn blown with the lips): a sawtooth through a
      // resonant filter that "talks", opening and closing in a slow rhythm.
      const n = Math.ceil((c.dur + 0.4) * c.rate);
      const o = new Osc();
      const o2 = new Osc(0.3);
      const lp = new Biquad("lp", c.rate);
      const inc = c.freq / c.rate;
      for (let i = 0; i < n; i++) {
        const t = i / c.rate;
        if (i % 16 === 0) lp.set(380 + 520 * (0.5 + 0.5 * Math.sin(TAU * 2 * t - 1.2)) ** 2, 4.5);
        const x = o.saw(inc) * 0.7 + o2.saw(inc * 1.004) * 0.4;
        const e = t < 0.15 ? t / 0.15 : t > c.dur ? Math.exp(-(t - c.dur) / 0.08) : 1;
        add(c, i, lp.run(x) * e * 0.2 * c.vel);
      }
      return;
    }
    case "djembe": {
      // A hand drum: a deep bass tone with a soft palm slap on top.
      const f = midi > 0 ? c.freq : 92;
      thump(c, f * 1.5, f, 0.04, 0.11, 0.62);
      return noiseHit(c, "bp", 1700, 0.9, 0.03, 0.2);
    }
    case "tom": {
      const f = midi > 0 ? c.freq : 110;
      thump(c, f * 1.6, f, 0.06, 0.14, 0.75);
      return noiseHit(c, "lp", 900, 0.7, 0.04, 0.12);
    }
    case "kick":
      return thump(c, 140, 48, 0.12, 0.06, 0.9);
    case "snare":
      noiseHit(c, "bp", 1900, 0.8, 0.13, 0.55);
      return thump(c, 240, 160, 0.06, 0.03, 0.4, "tri");
    case "hat":
      return noiseHit(c, "hp", 7500, 0.7, 0.035, 0.22);
    case "shaker":
      return noiseHit(c, "bp", 6500, 1.2, 0.05, 0.16, 0.012);
    case "tamb":
      return noiseHit(c, "hp", 8500, 1, 0.1, 0.18);
    case "crash":
      return noiseHit(c, "hp", 5000, 0.5, 1.1, 0.25);
    case "bongo": {
      const f = midi > 0 ? c.freq : 330;
      return thump(c, f * 1.25, f, 0.03, 0.05, 0.5);
    }
  }
}

const TAIL_SEC = 2.5;

/**
 * Render one stem of a song (mono). Loops come out exactly one loop long, with the
 * notes still ringing at the end wrapped onto the start.
 */
export function renderStem(song: Song, stem: string, rate: number): Float32Array {
  const spb = 60 / song.bpm;
  const seconds = song.beats * spb;
  const len = Math.round(seconds * rate);
  const work = new Float32Array(Math.ceil((seconds + TAIL_SEC) * rate));
  for (const p of song.parts) {
    if (p.stem !== stem) continue;
    for (const n of p.notes as Note[])
      renderNote(work, rate, p.inst, n.t * spb + 0.005, n.d * spb, n.m, n.v, p.gain);
  }
  if (!song.loop) return work;
  const out = work.slice(0, len);
  for (let i = len; i < work.length; i++) out[i - len]! += work[i]!;
  return out;
}

/** Scale stems together so the loudest mix (base + any one layer) peaks at `peak`. */
export function normalise(stems: Record<string, Float32Array>, peak = 0.85) {
  const base = stems.base!;
  const layers = Object.keys(stems).filter((k) => k !== "base");
  let max = 1e-6;
  const sets = layers.length ? layers.map((l) => stems[l]!) : [undefined];
  for (const layer of sets)
    for (let i = 0; i < base.length; i++) {
      const s = Math.abs(base[i]! + (layer?.[i] ?? 0));
      if (s > max) max = s;
    }
  const k = peak / max;
  for (const b of Object.values(stems)) for (let i = 0; i < b.length; i++) b[i]! *= k;
}

/** Every stem of a song, normalised together. */
export function renderSongData(song: Song, rate: number): Record<string, Float32Array> {
  const stems: Record<string, Float32Array> = {};
  for (const s of ["base", ...song.stems]) stems[s] = renderStem(song, s, rate);
  normalise(stems);
  return stems;
}
