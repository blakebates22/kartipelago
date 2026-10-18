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
  const note = (freq: number, at: number, length: number, volume: number, to = freq) => {
    if (!ctx || ctx.state !== "running") return;
    const t = ctx.currentTime + at;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "triangle";
    osc.frequency.setValueAtTime(freq, t);
    osc.frequency.exponentialRampToValueAtTime(to, t + length);
    gain.gain.setValueAtTime(volume, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + length);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t);
    osc.stop(t + length + 0.02);
  };

  return {
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
