/**
 * What every screen can reach: the renderer, audio, settings, records, the menu picks,
 * and the screen manager. Built once in main.ts.
 */
import type { AudioEngine } from "../audio/engine";
import type { UiSounds } from "../audio/uiSounds";
import type { Input } from "../core/input";
import type { RacerId } from "../render/racers/designs";
import type { Stage } from "../render/stage";
import type { UiLayer } from "../ui/layer";
import type { MenuInput } from "./menuInput";
import type { ScreenManager } from "./app";
import type { Settings } from "./settings";
import type { SessionContext, SessionOptions, Session } from "../game/session";
import type { TrackMode } from "../game/tracks";

export interface Selection {
  racer: RacerId;
  trackId: string;
  mode: TrackMode;
}

export interface Game {
  stage: Stage;
  ui: UiLayer;
  menuInput: MenuInput;
  gameInput: Input;
  audio: AudioEngine;
  sounds: UiSounds;
  screens: ScreenManager;
  settings: Settings;
  /** Save settings and apply them everywhere (audio, video). */
  applySettings(): void;
  selection: Selection;
  /** Build a race session (throws if its track can't load). */
  createSession(opts: Omit<SessionOptions, "lookMode">): Promise<Session>;
  sessionContext: SessionContext;
  /** The open race, if any (for the dev server's track reload). */
  session?: Session;
  /** ?debug: developer extras. */
  debugMode: boolean;
}
