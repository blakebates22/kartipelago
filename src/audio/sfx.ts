/**
 * Tiny synthesized sound effects (no audio files), played on the audio engine's SFX
 * bus. Until the browser allows sound (the first key or click) they're silent.
 */
import type { AudioEngine } from "./engine";

export function createSfx(engine: AudioEngine) {
  const out = () => engine.bus("sfx")!;
  const ctx: AudioContext | undefined = engine.context;

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
    osc.connect(gain).connect(out());
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
    src.connect(filter).connect(gain).connect(out());
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
    /** Driving into water: a splash, bigger for deep water or a fast entry. */
    splash(volume: number, big = false) {
      noise(0, big ? 0.55 : 0.3, volume * (big ? 0.9 : 0.55), big ? 2600 : 3600, 300);
      note(big ? 180 : 260, 0.02, 0.18, volume * 0.25, big ? 90 : 140, "sine");
    },
    /** Touching lava: a hiss and a yelp-like upward squeak. */
    sizzle(volume: number) {
      noise(0, 0.6, volume * 0.8, 7000, 1800);
      note(500, 0, 0.16, volume * 0.35, 1100, "square");
    },
    /** Fished out of deep water or lava: a cheerful bloop back onto the road. */
    recover(volume: number) {
      note(330, 0, 0.12, volume * 0.6, 660, "sine");
      note(660, 0.1, 0.14, volume * 0.5, 990, "sine");
    },
    /** The long-neck's friendly hoot: two low, round notes. */
    dinoCall(volume: number) {
      note(147, 0, 0.42, volume * 0.7, 165, "sine");
      note(110, 0.36, 0.6, volume * 0.6, 98, "sine");
    },
    /** A pterosaur's cry, high overhead: two harsh falling squawks. */
    screech(volume: number) {
      note(1250, 0, 0.32, volume * 0.22, 760, "sawtooth");
      note(1100, 0.38, 0.45, volume * 0.18, 620, "sawtooth");
    },
    /** The dragon rears up: a deep, rasping roar rising and falling. */
    roar(volume: number) {
      note(95, 0, 0.9, volume * 0.5, 140, "sawtooth");
      note(70, 0.25, 1.1, volume * 0.45, 52, "sawtooth");
      noise(0, 1.2, volume * 0.5, 900, 180);
    },
    /** The dragon's breath: a long, roaring whoosh of fire. */
    flame(volume: number) {
      noise(0, 1.9, volume * 0.9, 2400, 500);
      noise(0.1, 1.6, volume * 0.5, 600, 120);
    },
    /** The volcano: a deep rumble building to a boom. */
    rumble(volume: number) {
      noise(0, 2.4, volume * 0.6, 260, 60);
      noise(1.1, 1.4, volume * 0.8, 900, 70);
      note(48, 1.1, 1.2, volume * 0.5, 30, "sine");
    },
    /** A woolly mammoth's trumpet: a brassy blare rising and falling (higher for a calf). */
    trumpet(volume: number, small = false) {
      const f = small ? 1.7 : 1;
      note(220 * f, 0, 0.35, volume * 0.28, 330 * f, "sawtooth");
      note(330 * f, 0.3, 0.7, volume * 0.3, 260 * f, "sawtooth");
      noise(0.05, 0.8, volume * 0.15, 1800 * f, 600 * f);
    },
    /** A geyser getting ready to blow: a deep gurgle and bubbling. */
    gurgle(volume: number) {
      noise(0, 1.3, volume * 0.45, 500, 120);
      for (let i = 0; i < 5; i++)
        note(120 + i * 30, i * 0.22, 0.12, volume * 0.18, 240 + i * 40, "sine");
    },
    /** A geyser blowing: a great roaring whoosh of water and steam. */
    geyser(volume: number) {
      noise(0, 2.2, volume * 0.85, 5200, 700);
      noise(0, 1.2, volume * 0.5, 900, 140);
    },
    /** Sleigh bells: a bright, jingling shimmer. */
    jingle(volume: number) {
      for (let i = 0; i < 10; i++) {
        const f = [2637, 3136, 2794, 3520][i % 4]!;
        note(f, i * 0.16, 0.14, volume * 0.12, f * 1.02, "square");
        noise(i * 0.16, 0.08, volume * 0.12, 9000, 5000);
      }
    },
    /** The bell tower: two deep, ringing bongs. */
    bell(volume: number) {
      for (const [at, f] of [
        [0, 392],
        [1.1, 330],
      ] as const) {
        note(f, at, 2.2, volume * 0.35, f * 0.995, "sine");
        note(f * 2.4, at, 1.2, volume * 0.12, f * 2.39, "sine");
        note(f * 0.5, at, 2.6, volume * 0.2, f * 0.5, "triangle");
      }
    },
    /** A present smashed open: a papery rip and a cheerful pop. */
    present(volume: number) {
      noise(0, 0.25, volume * 0.6, 6000, 1200);
      note(520, 0.02, 0.12, volume * 0.35, 1040, "triangle");
      note(780, 0.1, 0.16, volume * 0.3, 1170, "triangle");
    },
    /** Onto a loop-the-loop: the booster's surge, a rising whoosh up and over. */
    loop(volume: number) {
      noise(0, 0.5, volume * 0.7, 900, 6000);
      note(220, 0, 1.4, volume * 0.35, 880, "sawtooth");
      note(660, 0.9, 0.9, volume * 0.25, 330, "triangle");
      noise(1.2, 1.2, volume * 0.4, 5000, 500);
    },
    /** Ice cracking underfoot: a sharp snap and a low groan. */
    crack(volume: number) {
      noise(0, 0.08, volume * 0.9, 9000, 2500);
      note(160, 0.02, 0.35, volume * 0.35, 90, "sawtooth");
      noise(0.12, 0.06, volume * 0.5, 7000, 2000);
    },
    /** Ice shattering: a crash of tinkling glass. */
    shatter(volume: number) {
      noise(0, 0.4, volume * 0.8, 10000, 1500);
      for (let i = 0; i < 6; i++)
        note(1800 + i * 430, i * 0.035, 0.18, volume * 0.18, 2600 + i * 300, "triangle");
    },
    /** An icicle about to fall: a creaking groan. */
    creak(volume: number) {
      note(220, 0, 0.5, volume * 0.3, 140, "sawtooth");
      note(300, 0.3, 0.4, volume * 0.22, 180, "square");
    },
    /** A heavy, soft footstep. */
    thud(volume: number) {
      noise(0, 0.12, volume * 0.5, 400, 80);
    },
    /** An ore cart on old rails: a fast iron clatter over the joints and a squeal. */
    rattle(volume: number) {
      for (let i = 0; i < 14; i++) {
        noise(i * 0.11, 0.05, volume * (0.35 + 0.15 * (i % 2)), 5200, 1400);
        if (i % 4 === 0) note(180 + (i % 3) * 30, i * 0.11, 0.06, volume * 0.12, 140, "square");
      }
      note(2400, 0.2, 0.9, volume * 0.06, 2100, "sawtooth");
    },
    /** Ghostly whispering: breathy hisses that rise and fall, like words just out of
     * hearing. */
    whisper(volume: number) {
      for (let i = 0; i < 5; i++) {
        const at = i * 0.32 + Math.random() * 0.12;
        noise(at, 0.28 + Math.random() * 0.2, volume * 0.22, 2600 + Math.random() * 1800, 900);
      }
    },
    /** A ghost's low moan: a hollow tone sliding down, wavering. */
    moan(volume: number) {
      note(330, 0, 1.6, volume * 0.16, 196, "sine");
      note(333, 0.05, 1.5, volume * 0.1, 200, "triangle");
    },
    /** Old timber creaking underfoot. */
    timber(volume: number) {
      note(140 + Math.random() * 60, 0, 0.45, volume * 0.22, 90, "sawtooth");
      noise(0.05, 0.3, volume * 0.12, 700, 200);
    },
    /** A hinge squeaking (the saloon's doors). */
    squeak(volume: number) {
      note(900, 0, 0.35, volume * 0.12, 1300, "square");
      note(1250, 0.32, 0.3, volume * 0.1, 800, "square");
    },
    /**
     * The night wind (a breathy rush whose pitch wanders) or the mine's drone (a low
     * rumble with a hollow hum in it), looping until stopped. Returns a handle to set its
     * volume (0..1) every frame.
     */
    ambience(kind: "wind" | "drone"): { set(volume: number): void; stop(): void } {
      if (!ctx) return { set() {}, stop() {} };
      const frames = ctx.sampleRate * 3;
      const buf = ctx.createBuffer(1, frames, ctx.sampleRate);
      const data = buf.getChannelData(0);
      let last = 0;
      for (let i = 0; i < frames; i++) {
        last = last * 0.92 + (Math.random() * 2 - 1) * 0.08;
        data[i] = last * 3;
      }
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      const filter = ctx.createBiquadFilter();
      filter.type = kind === "wind" ? "bandpass" : "lowpass";
      filter.frequency.value = kind === "wind" ? 500 : 160;
      filter.Q.value = kind === "wind" ? 1.4 : 0.7;
      // The wind's pitch wanders slowly.
      const lfo = ctx.createOscillator();
      const depth = ctx.createGain();
      lfo.frequency.value = kind === "wind" ? 0.11 : 0.05;
      depth.gain.value = kind === "wind" ? 260 : 40;
      lfo.connect(depth).connect(filter.frequency);
      const gain = ctx.createGain();
      gain.gain.value = 0;
      src.connect(filter).connect(gain).connect(out());
      const hums: OscillatorNode[] = [];
      if (kind === "drone")
        for (const f of [55, 82.4]) {
          const o = ctx.createOscillator();
          o.type = "sine";
          o.frequency.value = f;
          const g = ctx.createGain();
          g.gain.value = 0.18;
          o.connect(g).connect(gain);
          o.start();
          hums.push(o);
        }
      src.start();
      lfo.start();
      let stopped = false;
      return {
        set(v: number) {
          if (!stopped)
            gain.gain.setTargetAtTime(Math.max(0, Math.min(1, v)), ctx.currentTime, 0.3);
        },
        stop() {
          if (stopped) return;
          stopped = true;
          gain.gain.setTargetAtTime(0, ctx.currentTime, 0.05);
          src.stop(ctx.currentTime + 0.3);
          lfo.stop(ctx.currentTime + 0.3);
          for (const o of hums) o.stop(ctx.currentTime + 0.3);
        },
      };
    },
    /**
     * A steady rushing noise (waterfalls), looping until stopped. Returns a handle to set
     * its volume (0..1) every frame.
     */
    rush(): { set(volume: number): void; stop(): void } {
      if (!ctx) return { set() {}, stop() {} };
      const frames = ctx.sampleRate * 2;
      const buf = ctx.createBuffer(1, frames, ctx.sampleRate);
      const data = buf.getChannelData(0);
      let last = 0;
      for (let i = 0; i < frames; i++) {
        last = last * 0.6 + (Math.random() * 2 - 1) * 0.4;
        data[i] = last;
      }
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = 1800;
      const gain = ctx.createGain();
      gain.gain.value = 0;
      src.connect(filter).connect(gain).connect(out());
      src.start();
      let stopped = false;
      return {
        set(v: number) {
          if (!stopped)
            gain.gain.setTargetAtTime(Math.max(0, Math.min(1, v)), ctx.currentTime, 0.1);
        },
        stop() {
          if (stopped) return;
          stopped = true;
          gain.gain.setTargetAtTime(0, ctx.currentTime, 0.05);
          src.stop(ctx.currentTime + 0.3);
        },
      };
    },
  };
}
export type Sfx = ReturnType<typeof createSfx>;
