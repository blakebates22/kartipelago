/**
 * The audio engine: one AudioContext, four mixing buses, and the music player.
 *
 *   MUSIC ─┐
 *   SFX ───┼─> MASTER ─> (mono fold-down, if chosen) ─> speakers
 *   VOICE ─┘
 *
 * - Browsers only start sound after a click or key press, so the context is resumed on
 *   the first one; until then everything is silent but nothing breaks.
 * - If Web Audio is missing or fails, every method is a harmless no-op.
 * - Music is rendered once per piece (render.ts) and played as looping buffers. Every
 *   stem of a piece starts on the same clock tick, so layers stay in sync; switching
 *   layers only moves their gains.
 * - Changing piece crossfades. Pausing the game ducks the music.
 */
import { play, type InstrumentId } from "./instruments";
import { renderSong, type RenderedSong } from "./render";
import { INTRO } from "./dsp";
import { SONGS } from "./songs";

export interface AudioSettings {
  /** 0..1 */
  master: number;
  music: number;
  sfx: number;
  voice: number;
  musicOn: boolean;
  mono: boolean;
}

export type Bus = "music" | "sfx" | "voice";

interface Playing {
  id: string;
  rendered: RenderedSong;
  sources: AudioBufferSourceNode[];
  /** Fades the whole piece (crossfades). */
  gain: GainNode;
  stems: Record<string, GainNode>;
  startedAt: number;
  /** Offset into the piece when started (resuming in the music player), seconds. */
  offset: number;
  loop: boolean;
  onEnd?: () => void;
}

/** A small loudness curve so sliders feel even (0.5 on the slider ≈ half as loud). */
const curve = (v: number) => Math.max(0, Math.min(1, v)) ** 1.7;

export function createAudioEngine(initial: AudioSettings) {
  let ctx: AudioContext | undefined;
  try {
    ctx = new AudioContext({ latencyHint: "interactive" });
  } catch {
    ctx = undefined;
  }
  let settings = { ...initial };
  const buses: Record<Bus, GainNode> | undefined = ctx
    ? { music: ctx.createGain(), sfx: ctx.createGain(), voice: ctx.createGain() }
    : undefined;
  const master = ctx?.createGain();
  const mono = ctx?.createGain();
  /** Music goes through a little room. */
  const musicIn = ctx?.createGain();
  let duck = 1;

  if (ctx && buses && master && mono && musicIn) {
    // Mono: a gain node with one explicit channel down-mixes whatever comes in.
    mono.channelCount = 1;
    mono.channelCountMode = "explicit";
    mono.channelInterpretation = "speakers";
    mono.connect(ctx.destination);
    for (const b of Object.values(buses)) b.connect(master);
    musicIn.connect(buses.music);
    const verb = ctx.createConvolver();
    verb.buffer = roomImpulse(ctx);
    const send = ctx.createGain();
    send.gain.value = 0.18;
    musicIn.connect(send).connect(verb).connect(buses.music);
  }

  const routeMaster = () => {
    if (!ctx || !master || !mono) return;
    master.disconnect();
    master.connect(settings.mono ? mono : ctx.destination);
  };
  routeMaster();

  const ramp = (p: AudioParam, v: number, sec = 0.08) => {
    if (!ctx) return;
    p.cancelScheduledValues(ctx.currentTime);
    p.setValueAtTime(p.value, ctx.currentTime);
    p.linearRampToValueAtTime(v, ctx.currentTime + sec);
  };

  const applyLevels = (sec = 0.08) => {
    if (!buses || !master) return;
    ramp(master.gain, curve(settings.master), sec);
    ramp(buses.music.gain, settings.musicOn ? curve(settings.music) * 0.8 * duck : 0, sec);
    ramp(buses.sfx.gain, curve(settings.sfx), sec);
    ramp(buses.voice.gain, curve(settings.voice), sec);
  };
  applyLevels(0);

  // Start (resume) on the first press, as browsers require.
  const unlock = () => {
    if (ctx && ctx.state === "suspended") void ctx.resume();
  };
  for (const ev of ["pointerdown", "keydown", "touchstart"])
    window.addEventListener(ev, unlock, { capture: true });
  // Gamepads don't count as a gesture for every browser, but try anyway.
  const padUnlock = setInterval(() => {
    if (!ctx || ctx.state === "running") return clearInterval(padUnlock);
    if ([...(navigator.getGamepads?.() ?? [])].some((p) => p?.buttons.some((b) => b.pressed)))
      unlock();
  }, 250);

  // ---------------------------------------------------------------- music

  const cache = new Map<string, Promise<RenderedSong>>();
  const recent: string[] = [];
  /** Render (once) and keep the last few pieces; older ones are dropped to save memory. */
  function load(id: string): Promise<RenderedSong> {
    let p = cache.get(id);
    if (!p) {
      const song = SONGS[id];
      if (!song) return Promise.reject(new Error(`No song "${id}"`));
      p = renderSong(song);
      cache.set(id, p);
      p.catch(() => cache.delete(id));
    }
    const i = recent.indexOf(id);
    if (i >= 0) recent.splice(i, 1);
    recent.unshift(id);
    // (Six: a cutscene prepares its few cues ahead while another piece plays.)
    for (const old of recent.splice(6)) if (old !== current?.id) cache.delete(old);
    return p;
  }

  let current: Playing | undefined;

  /**
   * The AudioContext time of the next beat of a playing piece (within a beat and at
   * most a second away), so the next piece can come in on it; undefined for none.
   */
  function nextBeat(p: Playing | undefined): number | undefined {
    if (!ctx || !p) return undefined;
    const beat = 60 / p.rendered.song.bpm;
    const now = ctx.currentTime + 0.06;
    const t = now - p.startedAt + p.offset; // seconds into the piece
    if (t < 0) return undefined;
    const wait = Math.ceil(t / beat - 1e-3) * beat - t;
    return wait <= 1 ? now + wait : undefined;
  }
  /** Bumped on every music request, so a slow render can't start a stale piece. */
  let request = 0;

  function start(
    rendered: RenderedSong,
    opts: {
      fade: number;
      layers?: Record<string, number>;
      offset?: number;
      loop?: boolean;
      /** When to start (AudioContext time); soon, by default. */
      at?: number;
    },
  ): Playing | undefined {
    if (!ctx || !musicIn) return undefined;
    const gain = ctx.createGain();
    gain.gain.value = 0;
    gain.connect(musicIn);
    const at = Math.max(ctx.currentTime + 0.06, opts.at ?? 0);
    const loop = opts.loop ?? rendered.song.loop;
    const offset = opts.offset ?? 0;
    const intro = rendered.introSeconds;
    const stems: Record<string, GainNode> = {};
    const sources: AudioBufferSourceNode[] = [];
    for (const [name, buf] of Object.entries(rendered.stems)) {
      if (name === INTRO) continue;
      const g = ctx.createGain();
      g.gain.value = name === "base" ? 1 : (opts.layers?.[name] ?? 0);
      g.connect(gain);
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.loop = loop;
      if (loop) {
        src.loopStart = 0;
        src.loopEnd = rendered.seconds;
      }
      src.connect(g);
      // The loop starts once the intro (if any) has played.
      if (offset < intro) src.start(at + intro - offset, 0);
      else src.start(at, (offset - intro) % buf.duration);
      stems[name] = g;
      sources.push(src);
    }
    const introBuf = rendered.stems[INTRO];
    if (introBuf && offset < intro) {
      // Played once, its tail ringing on over the loop's first bars.
      const src = ctx.createBufferSource();
      src.buffer = introBuf;
      src.connect(stems.base ?? gain);
      src.start(at, offset);
      sources.push(src);
    }
    gain.gain.setValueAtTime(0, at);
    gain.gain.linearRampToValueAtTime(1, at + Math.max(0.01, opts.fade));
    const playing: Playing = {
      id: rendered.song.id,
      rendered,
      sources,
      gain,
      stems,
      startedAt: at,
      offset,
      loop,
    };
    sources[0]!.onended = () => {
      if (current === playing) {
        current = undefined;
        playing.onEnd?.();
      }
    };
    return playing;
  }

  /** Fade a piece out over `sec`, holding its level until `from` (AudioContext time). */
  function fadeOut(p: Playing | undefined, sec: number, from = 0) {
    if (!ctx || !p) return;
    const now = ctx.currentTime;
    const t = Math.max(now, from);
    p.gain.gain.cancelScheduledValues(now);
    p.gain.gain.setValueAtTime(p.gain.gain.value, now);
    if (t > now) p.gain.gain.linearRampToValueAtTime(p.gain.gain.value, t);
    p.gain.gain.linearRampToValueAtTime(0, t + sec);
    for (const s of p.sources) {
      s.onended = null;
      try {
        s.stop(t + sec + 0.05);
      } catch {
        // already stopped
      }
    }
    setTimeout(() => p.gain.disconnect(), (t - now + sec + 0.2) * 1000);
  }

  const music = {
    /**
     * Play a piece (crossfading from whatever's playing). Asking for the piece that's
     * already playing does nothing, so screens can call this freely.
     */
    async play(
      id: string,
      opts: {
        fade?: number;
        layers?: Record<string, number>;
        restart?: boolean;
        loop?: boolean;
        onEnd?: () => void;
      } = {},
    ) {
      if (current?.id === id && !opts.restart) {
        if (opts.layers) for (const [k, v] of Object.entries(opts.layers)) music.layer(k, v);
        return;
      }
      const mine = ++request;
      const fade = opts.fade ?? 0.8;
      let rendered: RenderedSong;
      try {
        rendered = await load(id);
      } catch (err) {
        console.warn("[audio] music unavailable:", err);
        return;
      }
      if (mine !== request) return; // something else was asked for meanwhile
      // A cutscene cue (a piece with an intro) comes in on the next beat of the piece
      // it replaces, quickly, while that one fades out under it from the same moment.
      const at = rendered.introSeconds > 0 ? nextBeat(current) : undefined;
      fadeOut(current, fade, at);
      current = start(rendered, {
        fade: at === undefined ? fade : Math.min(fade, 0.3),
        layers: opts.layers,
        loop: opts.loop,
        at,
      });
      if (current) current.onEnd = opts.onEnd;
    },
    stop(fade = 0.6) {
      request++;
      fadeOut(current, fade);
      current = undefined;
    },
    /** Fade one layer of the playing piece (e.g. a racer's instruments) to `level`. */
    layer(name: string, level: number, sec = 0.5) {
      const g = current?.stems[name];
      if (g) ramp(g.gain, level, sec);
    },
    /** Start rendering a piece in the background (no sound). */
    prepare(id: string) {
      void load(id).catch(() => undefined);
    },
    get playingId() {
      return current?.id;
    },
    /** Is the piece rendered and ready to start instantly? */
    async ready(id: string) {
      try {
        await load(id);
        return true;
      } catch {
        return false;
      }
    },
    /** Seconds into the playing piece (for the music player). */
    position(): number {
      if (!ctx || !current) return 0;
      const t = Math.max(0, ctx.currentTime - current.startedAt) + current.offset;
      const { seconds, introSeconds: intro } = current.rendered;
      if (t < intro) return t;
      return current.loop ? intro + ((t - intro) % seconds) : Math.min(t, intro + seconds);
    },
    length(): number {
      return current ? current.rendered.introSeconds + current.rendered.seconds : 0;
    },
    /** Duck the music (pausing the game) or bring it back. */
    duck(on: boolean) {
      duck = on ? 0.35 : 1;
      applyLevels(0.25);
    },
    /** Restart the current piece from `offset` seconds, e.g. to resume the music player. */
    async seek(id: string, offset: number, loop: boolean, onEnd?: () => void) {
      const mine = ++request;
      let rendered: RenderedSong;
      try {
        rendered = await load(id);
      } catch {
        return;
      }
      if (mine !== request) return;
      fadeOut(current, 0.05);
      current = start(rendered, { fade: 0.05, offset, loop });
      if (current) current.onEnd = onEnd;
    },
  };

  // ---------------------------------------------------------------- one-shots

  /** Play notes live on a bus: [instrument, midi, delay s, length s, velocity]. */
  function notes(bus: Bus, list: [InstrumentId, number, number, number, number?][], level = 1) {
    if (!ctx || !buses || ctx.state !== "running") return;
    const out = ctx.createGain();
    out.gain.value = level;
    out.connect(buses[bus]);
    const t = ctx.currentTime + 0.01;
    let end = 0;
    for (const [inst, m, at, len, vel] of list) {
      play(ctx, out, inst, t + at, len, m, vel ?? 0.8);
      end = Math.max(end, at + len);
    }
    setTimeout(() => out.disconnect(), (end + 2) * 1000);
  }

  /** Recorded sounds (public/audio/), fetched and decoded once. */
  const samples = new Map<string, Promise<AudioBuffer | undefined>>();
  function loadSample(path: string) {
    let p = samples.get(path);
    if (!p) {
      p = ctx
        ? fetch(`${import.meta.env.BASE_URL}${path}`)
            .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(r.statusText))))
            .then((b) => ctx!.decodeAudioData(b))
            .catch(() => undefined)
        : Promise.resolve(undefined);
      samples.set(path, p);
    }
    return p;
  }
  /** Play a recorded sound on a bus (loading it first if it isn't yet). */
  function sample(bus: Bus, path: string, level = 1) {
    if (!ctx || !buses || ctx.state !== "running") return;
    void loadSample(path).then((buf) => {
      if (!buf || !ctx || !buses) return;
      const src = ctx.createBufferSource();
      src.buffer = buf;
      const g = ctx.createGain();
      g.gain.value = level;
      src.connect(g).connect(buses[bus]);
      src.start();
      src.onended = () => g.disconnect();
    });
  }

  let tap: MediaStreamAudioDestinationNode | undefined;

  return {
    get context() {
      return ctx;
    },
    /**
     * Everything you hear (before the master volume), as a stream: for the dev clip
     * recorder (debug/clipRecorder.ts). Made the first time it's asked for.
     */
    recordStream(): MediaStream | undefined {
      if (!ctx || !buses) return undefined;
      if (!tap) {
        tap = ctx.createMediaStreamDestination();
        for (const b of Object.values(buses)) b.connect(tap);
      }
      return tap.stream;
    },
    sample,
    /** Fetch and decode a recorded sound ahead of time. */
    preload: (path: string) => void loadSample(path),
    /** True once the browser lets us make sound. */
    get running() {
      return ctx?.state === "running";
    },
    /** Where sound effects should connect. */
    bus(b: Bus): AudioNode | undefined {
      return buses?.[b];
    },
    settings: () => ({ ...settings }),
    apply(next: AudioSettings) {
      const monoChanged = next.mono !== settings.mono;
      settings = { ...next };
      if (monoChanged) routeMaster();
      applyLevels();
    },
    music,
    notes,
    unlock,
  };
}

export type AudioEngine = ReturnType<typeof createAudioEngine>;

/** A short, soft stereo room (decaying noise), generated rather than recorded. */
function roomImpulse(ctx: BaseAudioContext) {
  const len = Math.floor(ctx.sampleRate * 1.4);
  const b = ctx.createBuffer(2, len, ctx.sampleRate);
  for (let c = 0; c < 2; c++) {
    const d = b.getChannelData(c);
    let seed = 99 + c * 7;
    for (let i = 0; i < len; i++) {
      seed = (seed * 1103515245 + 12345) >>> 0;
      const n = seed / 2147483648 - 1;
      d[i] = n * Math.exp((-4.2 * i) / len) * (i < 200 ? i / 200 : 1);
    }
  }
  return b;
}
