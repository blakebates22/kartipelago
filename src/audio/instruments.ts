/**
 * A small synthesized "sample palette" for the soundtrack and menu sounds: marimba,
 * xylophone, celesta, pizzicato strings, acoustic bass, flute, clarinet, brass, a low
 * woodwind, a soft pad, a square-wave accent, and hand percussion.
 *
 * Every instrument is a few Web Audio nodes scheduled at a time: the same code plays
 * live (menu blips) and in an OfflineAudioContext (music, rendered once into loops).
 * All original; no recorded samples.
 */

export type InstrumentId =
  | "marimba"
  | "xylophone"
  | "celesta"
  | "pizz"
  | "bass"
  | "flute"
  | "clarinet"
  | "brass"
  | "horn"
  | "bassoon"
  | "pad"
  | "square"
  | "steelpan"
  | "bell"
  | "strings"
  | "kick"
  | "snare"
  | "hat"
  | "shaker"
  | "woodblock"
  | "bongo"
  | "tamb"
  | "crash"
  | "tom";

export const DRUMS: ReadonlySet<InstrumentId> = new Set([
  "kick",
  "snare",
  "hat",
  "shaker",
  "woodblock",
  "bongo",
  "tamb",
  "crash",
  "tom",
]);

export const midiToFreq = (m: number) => 440 * Math.pow(2, (m - 69) / 12);

const noiseCache = new WeakMap<BaseAudioContext, AudioBuffer>();
function noiseBuffer(ctx: BaseAudioContext) {
  let b = noiseCache.get(ctx);
  if (!b) {
    b = ctx.createBuffer(1, Math.floor(ctx.sampleRate * 1.5), ctx.sampleRate);
    const d = b.getChannelData(0);
    let seed = 12345;
    for (let i = 0; i < d.length; i++) {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      d[i] = seed / 2147483648 - 1;
    }
    noiseCache.set(ctx, b);
  }
  return b;
}

interface Voice {
  ctx: BaseAudioContext;
  out: AudioNode;
  /** Start time, seconds. */
  t: number;
  /** Held length, seconds. */
  dur: number;
  freq: number;
  /** 0..1 */
  vel: number;
}

/** An envelope on a gain node: attack to `peak`, hold, then release; or a decay. */
function env(
  g: GainNode,
  t: number,
  a: number,
  peak: number,
  hold: number,
  release: number,
  sustain = 1,
) {
  const p = g.gain;
  p.setValueAtTime(0, t);
  p.linearRampToValueAtTime(peak, t + a);
  if (sustain < 1) p.setTargetAtTime(peak * sustain, t + a, 0.15);
  p.setValueAtTime(peak * sustain, t + Math.max(a, hold));
  p.setTargetAtTime(0, t + Math.max(a, hold), release / 4);
}

function osc(v: Voice, type: OscillatorType, mult: number, detuneCents = 0) {
  const o = v.ctx.createOscillator();
  o.type = type;
  o.frequency.value = v.freq * mult;
  o.detune.value = detuneCents;
  return o;
}

/** A struck bar: a fundamental plus decaying overtones (marimba, xylophone, celesta). */
function bar(v: Voice, partials: [number, number, number][], decay: number, level: number) {
  const end = v.t + decay * 5;
  // Lower notes ring longer.
  const ring = decay * Math.min(1.8, Math.max(0.6, 400 / v.freq));
  for (const [mult, amp, d] of partials) {
    if (v.freq * mult > v.ctx.sampleRate * 0.45) continue; // above what this rate can hold
    const o = osc(v, "sine", mult);
    const g = v.ctx.createGain();
    g.gain.setValueAtTime(0, v.t);
    g.gain.linearRampToValueAtTime(amp * level * v.vel, v.t + 0.003);
    g.gain.setTargetAtTime(0, v.t + 0.003, ring * d);
    o.connect(g).connect(v.out);
    o.start(v.t);
    o.stop(end);
  }
}

function noiseHit(
  v: Voice,
  type: BiquadFilterType,
  freq: number,
  q: number,
  len: number,
  level: number,
  attack = 0.001,
) {
  const src = v.ctx.createBufferSource();
  src.buffer = noiseBuffer(v.ctx);
  const f = v.ctx.createBiquadFilter();
  f.type = type;
  f.frequency.value = freq;
  f.Q.value = q;
  const g = v.ctx.createGain();
  g.gain.setValueAtTime(0, v.t);
  g.gain.linearRampToValueAtTime(level * v.vel, v.t + attack);
  g.gain.setTargetAtTime(0, v.t + attack, len / 3);
  src.connect(f).connect(g).connect(v.out);
  // Start somewhere different in the noise each time, so hits don't sound identical.
  const offset = ((v.t * 7.31) % 1) * 0.5;
  src.start(v.t, offset);
  src.stop(v.t + len * 2 + 0.05);
}

function vibrato(v: Voice, o: OscillatorNode, delay: number, rate: number, depth: number) {
  const lfo = v.ctx.createOscillator();
  lfo.frequency.value = rate;
  const g = v.ctx.createGain();
  g.gain.setValueAtTime(0, v.t);
  g.gain.linearRampToValueAtTime(0, v.t + delay);
  g.gain.linearRampToValueAtTime(v.freq * depth, v.t + delay + 0.25);
  lfo.connect(g).connect(o.frequency);
  lfo.start(v.t);
  lfo.stop(v.t + v.dur + 0.5);
}

/** A sustained voice through a low-pass filter (winds, brass, pad). */
function sustained(
  v: Voice,
  layers: { type: OscillatorType; mult: number; amp: number; detune?: number }[],
  filter: { from: number; to: number; time: number; q: number },
  a: number,
  release: number,
  level: number,
  vib?: { delay: number; rate: number; depth: number },
) {
  const f = v.ctx.createBiquadFilter();
  f.type = "lowpass";
  f.Q.value = filter.q;
  f.frequency.setValueAtTime(filter.from, v.t);
  f.frequency.linearRampToValueAtTime(filter.to, v.t + filter.time);
  const g = v.ctx.createGain();
  env(g, v.t, a, level * v.vel, v.dur, release);
  f.connect(g).connect(v.out);
  const end = v.t + v.dur + release * 2 + 0.05;
  for (const l of layers) {
    const o = osc(v, l.type, l.mult, l.detune ?? 0);
    const lg = v.ctx.createGain();
    lg.gain.value = l.amp;
    o.connect(lg).connect(f);
    if (vib) vibrato(v, o, vib.delay, vib.rate, vib.depth);
    o.start(v.t);
    o.stop(end);
  }
}

/** Play one note (or drum hit) of an instrument at time t (seconds) into `out`. */
export function play(
  ctx: BaseAudioContext,
  out: AudioNode,
  inst: InstrumentId,
  t: number,
  dur: number,
  midi: number,
  vel = 0.8,
) {
  const v: Voice = { ctx, out, t, dur, freq: midiToFreq(midi), vel };
  // The newer track-theme instruments live only in the music renderer (dsp.ts); live
  // sounds use their nearest relative.
  if (inst === "steelpan" || inst === "bell") inst = "celesta";
  else if (inst === "strings") inst = "pad";
  else if (inst === "tom") inst = "bongo";
  switch (inst) {
    case "marimba":
      bar(
        v,
        [
          [1, 1, 1],
          [4, 0.22, 0.18],
          [9.8, 0.06, 0.05],
        ],
        0.28,
        0.5,
      );
      break;
    case "xylophone":
      bar(
        v,
        [
          [1, 1, 1],
          [3, 0.35, 0.3],
          [6.2, 0.1, 0.1],
        ],
        0.12,
        0.42,
      );
      break;
    case "celesta":
      bar(
        v,
        [
          [1, 1, 1],
          [2, 0.25, 0.6],
          [4.1, 0.12, 0.15],
        ],
        0.55,
        0.32,
      );
      break;
    case "pizz": {
      const f = ctx.createBiquadFilter();
      f.type = "lowpass";
      f.Q.value = 1.5;
      f.frequency.setValueAtTime(Math.min(6000, v.freq * 7), t);
      f.frequency.setTargetAtTime(v.freq * 1.5, t + 0.005, 0.05);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.42 * vel, t + 0.004);
      g.gain.setTargetAtTime(0, t + 0.004, 0.09);
      f.connect(g).connect(out);
      for (const [type, d] of [
        ["sawtooth", -5],
        ["triangle", 5],
      ] as const) {
        const o = osc(v, type, 1, d);
        o.connect(f);
        o.start(t);
        o.stop(t + 0.6);
      }
      break;
    }
    case "bass": {
      // A plucked upright: round, with a short thumpy attack.
      const f = ctx.createBiquadFilter();
      f.type = "lowpass";
      f.frequency.setValueAtTime(900, t);
      f.frequency.setTargetAtTime(380, t + 0.01, 0.12);
      const g = ctx.createGain();
      const len = Math.min(dur, 0.9);
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.75 * vel, t + 0.006);
      g.gain.setTargetAtTime(0.35 * vel, t + 0.01, 0.12);
      g.gain.setTargetAtTime(0, t + len, 0.05);
      f.connect(g).connect(out);
      const o1 = osc(v, "triangle", 1);
      const o2 = osc(v, "sawtooth", 1);
      const g2 = ctx.createGain();
      g2.gain.value = 0.35;
      o1.connect(f);
      o2.connect(g2).connect(f);
      for (const o of [o1, o2]) {
        o.start(t);
        o.stop(t + len + 0.4);
      }
      break;
    }
    case "flute": {
      sustained(
        v,
        [
          { type: "sine", mult: 1, amp: 1 },
          { type: "triangle", mult: 1, amp: 0.25 },
          { type: "sine", mult: 2, amp: 0.08 },
        ],
        { from: 3000, to: 3000, time: 0.01, q: 0.5 },
        0.05,
        0.09,
        0.32,
        { delay: 0.18, rate: 5.2, depth: 0.006 },
      );
      // A breath of air at the start.
      noiseHit(v, "bandpass", Math.min(8000, v.freq * 2), 2, 0.12, 0.05, 0.02);
      break;
    }
    case "clarinet":
      sustained(
        v,
        [
          { type: "square", mult: 1, amp: 0.55 },
          { type: "sine", mult: 1, amp: 0.6 },
        ],
        { from: 1200, to: Math.min(3200, v.freq * 5), time: 0.05, q: 0.7 },
        0.04,
        0.07,
        0.3,
        { delay: 0.3, rate: 4.6, depth: 0.003 },
      );
      break;
    case "brass":
      sustained(
        v,
        [
          { type: "sawtooth", mult: 1, amp: 0.5, detune: -6 },
          { type: "sawtooth", mult: 1, amp: 0.5, detune: 6 },
        ],
        { from: 400, to: Math.min(4200, v.freq * 6), time: 0.07, q: 1.2 },
        0.03,
        0.1,
        0.26,
        { delay: 0.25, rate: 5, depth: 0.003 },
      );
      break;
    case "horn":
      sustained(
        v,
        [
          { type: "sawtooth", mult: 1, amp: 0.45, detune: -4 },
          { type: "triangle", mult: 1, amp: 0.6, detune: 4 },
        ],
        { from: 300, to: Math.min(1400, v.freq * 3), time: 0.12, q: 0.8 },
        0.09,
        0.2,
        0.24,
      );
      break;
    case "bassoon":
      sustained(
        v,
        [
          { type: "sawtooth", mult: 1, amp: 0.6 },
          { type: "square", mult: 1, amp: 0.25 },
        ],
        { from: 500, to: Math.min(1100, v.freq * 4), time: 0.06, q: 3 },
        0.05,
        0.08,
        0.3,
        { delay: 0.3, rate: 4.4, depth: 0.003 },
      );
      break;
    case "pad":
      sustained(
        v,
        [
          { type: "sawtooth", mult: 1, amp: 0.4, detune: -9 },
          { type: "sawtooth", mult: 1, amp: 0.4, detune: 9 },
          { type: "triangle", mult: 0.5, amp: 0.3 },
        ],
        { from: 900, to: 1500, time: 0.4, q: 0.5 },
        0.25,
        0.45,
        0.11,
      );
      break;
    case "square":
      sustained(
        v,
        [{ type: "square", mult: 1, amp: 1 }],
        { from: 2600, to: 1800, time: 0.08, q: 0.5 },
        0.005,
        0.05,
        0.11,
      );
      break;
    case "kick": {
      const o = ctx.createOscillator();
      o.frequency.setValueAtTime(140, t);
      o.frequency.exponentialRampToValueAtTime(48, t + 0.12);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.9 * vel, t);
      g.gain.setTargetAtTime(0, t + 0.01, 0.06);
      o.connect(g).connect(out);
      o.start(t);
      o.stop(t + 0.4);
      break;
    }
    case "snare":
      noiseHit(v, "bandpass", 1900, 0.8, 0.13, 0.55);
      {
        const o = ctx.createOscillator();
        o.type = "triangle";
        o.frequency.setValueAtTime(240, t);
        o.frequency.exponentialRampToValueAtTime(160, t + 0.06);
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.4 * vel, t);
        g.gain.setTargetAtTime(0, t + 0.005, 0.03);
        o.connect(g).connect(out);
        o.start(t);
        o.stop(t + 0.2);
      }
      break;
    case "hat":
      noiseHit(v, "highpass", 7500, 0.7, 0.035, 0.22);
      break;
    case "shaker":
      noiseHit(v, "bandpass", 6500, 1.2, 0.05, 0.16, 0.012);
      break;
    case "tamb":
      noiseHit(v, "highpass", 8500, 1, 0.1, 0.18);
      break;
    case "crash":
      noiseHit(v, "highpass", 5000, 0.5, 1.1, 0.25);
      break;
    case "woodblock":
      bar(
        { ...v, freq: midi > 0 ? v.freq : 1300 },
        [
          [1, 1, 1],
          [2.7, 0.4, 0.5],
        ],
        0.035,
        0.5,
      );
      break;
    case "bongo": {
      const o = ctx.createOscillator();
      const f = midi > 0 ? v.freq : 330;
      o.frequency.setValueAtTime(f * 1.25, t);
      o.frequency.exponentialRampToValueAtTime(f, t + 0.03);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.5 * vel, t);
      g.gain.setTargetAtTime(0, t + 0.004, 0.05);
      o.connect(g).connect(out);
      o.start(t);
      o.stop(t + 0.3);
      break;
    }
  }
}
