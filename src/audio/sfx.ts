/**
 * Tiny synthesized sound effects (no audio files). Browsers only allow sound after the
 * player has pressed something, so the audio context starts on the first key or click.
 */
export function createSfx() {
  let ctx: AudioContext | undefined;
  const start = () => {
    if (ctx) {
      if (ctx.state === "suspended") void ctx.resume();
      return;
    }
    try {
      ctx = new AudioContext();
    } catch {
      ctx = undefined; // no audio available; effects stay silent
    }
  };
  window.addEventListener("keydown", start);
  window.addEventListener("pointerdown", start);

  /** One short note: a frequency glide with a quick fade. */
  const note = (
    freq: number,
    at: number,
    length: number,
    volume: number,
    to = freq,
    type: OscillatorType = "triangle",
  ) => {
    if (!ctx || ctx.state !== "running") return;
    const t = ctx.currentTime + at;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t);
    osc.frequency.exponentialRampToValueAtTime(to, t + length);
    gain.gain.setValueAtTime(volume, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + length);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t);
    osc.stop(t + length + 0.02);
  };

  /** A burst of filtered noise: whooshes and explosions. */
  const noise = (at: number, length: number, volume: number, from: number, to: number) => {
    if (!ctx || ctx.state !== "running") return;
    const t = ctx.currentTime + at;
    const frames = Math.ceil(ctx.sampleRate * length);
    const buf = ctx.createBuffer(1, frames, ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < frames; i++) data[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(from, t);
    filter.frequency.exponentialRampToValueAtTime(to, t + length);
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(volume, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + length);
    src.connect(filter).connect(gain).connect(ctx.destination);
    src.start(t);
    src.stop(t + length + 0.02);
  };

  return {
    /** Balloon popped: a new one, an upgrade (higher), or a refill. */
    balloon(volume: number, result: "new" | "upgrade" | "refill") {
      const f = result === "new" ? 520 : result === "upgrade" ? 780 : 660;
      noise(0, 0.08, volume * 0.8, 4000, 800);
      note(f, 0.02, 0.15, volume, f * 1.5);
      if (result === "upgrade") note(f * 1.5, 0.12, 0.15, volume, f * 2);
    },
    /**
     * A blue boost firing. Level 3 charges (a rising tone) and then booms after
     * `chargeSec`: sound only, the boost itself started at once.
     */
    blueBoost(volume: number, level: number, chargeSec: number) {
      if (level >= 3) {
        note(200, 0, chargeSec, volume * 0.7, 900, "sawtooth");
        noise(chargeSec, 0.6, volume, 6000, 300);
        note(140, chargeSec, 0.5, volume, 70, "square");
      } else {
        noise(0, 0.25 + level * 0.15, volume, 5000, 400);
        note(level === 1 ? 300 : 240, 0, 0.3, volume * 0.6, 120, "square");
      }
    },
    /** The enhanced (released-throttle) boost took: a bright double chime. */
    enhanced(volume: number) {
      note(1320, 0.03, 0.12, volume * 0.8);
      note(1760, 0.1, 0.16, volume * 0.8);
    },
    /** The rainbow window opened: press the throttle now. */
    rainbow(volume: number) {
      note(1046, 0, 0.09, volume, 1568);
    },
    /** The boost stopped pushing. */
    boostEnd(volume: number) {
      noise(0, 0.15, volume * 0.4, 1200, 200);
    },
    missile(volume: number) {
      noise(0, 0.35, volume * 0.8, 3000, 600);
      note(600, 0, 0.3, volume * 0.5, 300, "sawtooth");
    },
    explosion(volume: number) {
      noise(0, 0.7, volume, 2500, 80);
      note(90, 0, 0.5, volume, 40, "square");
    },
    shieldBlock(volume: number) {
      note(1200, 0, 0.2, volume, 900, "sine");
      note(1800, 0.05, 0.2, volume * 0.6, 1400, "sine");
    },
    shield(volume: number) {
      note(440, 0, 0.35, volume, 880, "sine");
      note(660, 0.08, 0.35, volume * 0.7, 1320, "sine");
    },
    drop(volume: number) {
      note(300, 0, 0.12, volume, 180);
    },
    oil(volume: number) {
      noise(0, 0.3, volume * 0.8, 900, 150);
      note(260, 0, 0.6, volume * 0.6, 520, "sine");
    },
    bubble(volume: number) {
      [400, 520, 660].forEach((f, i) => note(f, i * 0.07, 0.12, volume * 0.7, f * 1.3, "sine"));
    },
    magnet(volume: number) {
      note(300, 0, 0.5, volume * 0.7, 600, "square");
      note(306, 0, 0.5, volume * 0.5, 612, "square");
    },
    fizz(volume: number) {
      note(220, 0, 0.2, volume * 0.6, 110);
    },
    /** A bright upward blip. */
    banana(volume: number) {
      note(880, 0, 0.12, volume, 1320);
    },
    /** A rising little fanfare: the speed bonus is full. */
    bananaMilestone(volume: number) {
      [660, 830, 990, 1320].forEach((f, i) => note(f, 0.1 + i * 0.09, 0.2, volume));
    },
    /** A falling wobble when bananas are knocked loose. */
    bananaLost(volume: number) {
      note(520, 0, 0.25, volume, 220);
    },
  };
}
