/**
 * Player settings, saved in this browser (localStorage) and loaded at startup.
 *
 * Settings are separate from what's being picked in the menus (app/state.ts) and from
 * the race itself (game/session.ts). Anything missing or broken in storage falls back
 * to the default, so a bad value can never stop the game starting.
 */
import type { AudioSettings } from "../audio/engine";
import type { RacerId } from "../render/racers/designs";
import { RACER_IDS } from "../render/racers/designs";

export type Resolution = 240 | 360 | 480 | 0; // lines; 0 = full screen resolution
export type Filtering = "soft" | "sharp";
export type Aspect = "fill" | "4:3";

export interface Settings {
  version: 1;
  audio: AudioSettings;
  video: {
    /** Texture filtering: soft (bilinear, N64-like) or sharp (crisp texels). */
    filtering: Filtering;
    resolution: Resolution;
    aspect: Aspect;
    scanlines: boolean;
  };
  general: {
    /** Calmer menus: no bouncing, sliding or camera swoops. */
    reduceMotion: boolean;
  };
  /** Last picks, so the menus start where you left them. */
  last: { racer: RacerId; track: string; mode: "race" | "timeTrial" };
}

export const DEFAULT_SETTINGS: Settings = {
  version: 1,
  audio: { master: 0.8, music: 0.7, sfx: 0.8, voice: 0.8, musicOn: true, mono: false },
  video: { filtering: "soft", resolution: 360, aspect: "fill", scanlines: false },
  general: { reduceMotion: false },
  last: { racer: "moss", track: "dino_demo", mode: "race" },
};

const KEY = "kartipelago.settings.v1";

const num = (v: unknown, d: number) =>
  typeof v === "number" && Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : d;
const bool = (v: unknown, d: boolean) => (typeof v === "boolean" ? v : d);
const oneOf = <T>(v: unknown, list: readonly T[], d: T): T =>
  list.includes(v as T) ? (v as T) : d;
const obj = (v: unknown): Record<string, unknown> =>
  typeof v === "object" && v !== null ? (v as Record<string, unknown>) : {};

/** Make a full, valid Settings from whatever was stored (or nothing). */
export function sanitize(raw: unknown): Settings {
  const r = obj(raw);
  const a = obj(r.audio);
  const v = obj(r.video);
  const g = obj(r.general);
  const l = obj(r.last);
  const D = DEFAULT_SETTINGS;
  return {
    version: 1,
    audio: {
      master: num(a.master, D.audio.master),
      music: num(a.music, D.audio.music),
      sfx: num(a.sfx, D.audio.sfx),
      voice: num(a.voice, D.audio.voice),
      musicOn: bool(a.musicOn, D.audio.musicOn),
      mono: bool(a.mono, D.audio.mono),
    },
    video: {
      filtering: oneOf(v.filtering, ["soft", "sharp"] as const, D.video.filtering),
      resolution: oneOf(v.resolution, [240, 360, 480, 0] as const, D.video.resolution),
      aspect: oneOf(v.aspect, ["fill", "4:3"] as const, D.video.aspect),
      scanlines: bool(v.scanlines, D.video.scanlines),
    },
    general: { reduceMotion: bool(g.reduceMotion, D.general.reduceMotion) },
    last: {
      racer: oneOf(l.racer, RACER_IDS, D.last.racer),
      track: typeof l.track === "string" ? l.track : D.last.track,
      mode: oneOf(l.mode, ["race", "timeTrial"] as const, D.last.mode),
    },
  };
}

export function loadSettings(
  storage: Pick<Storage, "getItem"> | undefined = safeStorage(),
): Settings {
  try {
    const raw = storage?.getItem(KEY);
    return sanitize(raw ? JSON.parse(raw) : undefined);
  } catch {
    return sanitize(undefined);
  }
}

export function saveSettings(
  s: Settings,
  storage: Pick<Storage, "setItem"> | undefined = safeStorage(),
) {
  try {
    storage?.setItem(KEY, JSON.stringify(s));
  } catch {
    // Storage full or blocked: the settings still apply for this visit.
  }
}

export function safeStorage(): Storage | undefined {
  try {
    return typeof localStorage === "undefined" ? undefined : localStorage;
  } catch {
    return undefined;
  }
}
