/**
 * Kartipelago starts here: it builds the long-lived pieces once (renderer, audio,
 * input, settings, the UI layer and the screen manager) and hands over to the screens.
 *
 * Normally you get the full frontend: title, racer, mode and track select, then the
 * race. The old developer URLs still jump straight into a race:
 *
 *   ?track=1|2|3 or ?track=<blender id>   race on that track (live reload for Blender tracks)
 *   ?scene=drift | ?scene=practice        the Drift Park or the pickup practice course
 *   ?racer=tiko|brakka|pebble|zephyr       who you drive
 *   ?solo                                 no AI rivals
 *   ?look=authentic|enhanced              texture look
 *   ?timing                               start-boost timing bar
 *   ?debug                                developer keys and window.kp
 */
import { adventureHub } from "./screens/adventure";
import { overworldLoading } from "./screens/overworld";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";
import { createBoostLab } from "./debug/boostLab";
import { createClipRecorder } from "./debug/clipRecorder";
import { createAudioEngine } from "./audio/engine";
import { createSfx } from "./audio/sfx";
import { createUiSounds } from "./audio/uiSounds";
import { createMenuInput } from "./app/menuInput";
import { createScreenManager, type Screen } from "./app/app";
import { loadSettings, saveSettings, safeStorage, sanitize } from "./app/settings";
import type { Game } from "./app/game";
import { createSession, type SessionContext } from "./game/session";
import { TITLE_TRACK, TRACKS, trackById, type TrackEntry } from "./game/tracks";
import { createUiLayer } from "./ui/layer";
import { RACER_IDS, type RacerId } from "./render/racers/designs";
import type { LookMode } from "./render/trackMaterials";
import { bootScreen } from "./screens/title";
import { loadingScreen } from "./screens/loading";

const PARAMS = new URLSearchParams(location.search);
// ?debug (dev keys, the debug overlay, window.kp): only on the dev server.
const debugMode = import.meta.env.DEV && PARAMS.has("debug");

// ---------------------------------------------------------------- settings

const storage = safeStorage();
const settings = (() => {
  const s = loadSettings(storage);
  // First visit since settings existed: keep the racer and look picked the old way.
  if (!storage?.getItem("kartipelago.settings.v1")) {
    const racer = storage?.getItem("kartipelago.racer");
    if (racer && (RACER_IDS as string[]).includes(racer)) s.last.racer = racer as RacerId;
    if (storage?.getItem("kartipelago.look") === "enhanced") {
      s.video.filtering = "sharp";
      s.video.resolution = 0;
    }
  }
  return sanitize(s);
})();
const lookParam = PARAMS.get("look");
if (lookParam === "enhanced") Object.assign(settings.video, { filtering: "sharp", resolution: 0 });
if (lookParam === "authentic")
  Object.assign(settings.video, { filtering: "soft", resolution: 360 });
const lookMode = (): LookMode => (settings.video.filtering === "soft" ? "authentic" : "enhanced");

// ---------------------------------------------------------------- the long-lived pieces

const app = document.getElementById("app")!;
const stage = createStage(app);
const debug = createDebug(document.body);
const boostLab = createBoostLab(debug.panel, document.body, () => debug.overlay.visible);
const gameInput = createInput();
const menuInput = createMenuInput();
const ui = createUiLayer(app, menuInput);
const audio = createAudioEngine(settings.audio);
const sfx = createSfx(audio);
const sounds = createUiSounds(audio);
const scanlines = document.createElement("div");
scanlines.className = "scanlines";
app.appendChild(scanlines);

const sessionContext: SessionContext = {
  stage,
  input: gameInput,
  sfx,
  debug,
  boostLab,
  hudParent: app,
  devKeys: debugMode,
  showTiming: PARAMS.has("timing"),
};

function applyVideo() {
  const v = settings.video;
  stage.setResolution(v.resolution);
  game.session?.setLookMode(lookMode());
  app.classList.toggle("aspect-43", v.aspect === "4:3");
  scanlines.hidden = !v.scanlines;
  stage.resize();
  ui.resize();
}

const screens = createScreenManager(ui, menuInput, {
  reduceMotion: () => settings.general.reduceMotion,
});

const game: Game = {
  stage,
  ui,
  menuInput,
  gameInput,
  audio,
  sounds,
  screens,
  settings,
  applySettings() {
    audio.apply(settings.audio);
    applyVideo();
    saveSettings(settings, storage);
  },
  selection: { racer: settings.last.racer, trackId: settings.last.track, mode: settings.last.mode },
  createSession: (opts) => createSession(sessionContext, { ...opts, lookMode: lookMode() }),
  sessionContext,
  debugMode,
};
applyVideo();

// ---------------------------------------------------------------- where to start

/** The track a developer URL asks for, if any. */
function urlTrack(): { entry: TrackEntry; mode: Game["selection"]["mode"] } | undefined {
  const scene = PARAMS.get("scene");
  const trackParam = PARAMS.get("track");
  if (scene === "drift") return { entry: trackById("drift_park")!, mode: "practice" };
  if (scene === "practice")
    return {
      entry: {
        id: "practice",
        name: "Practice Course",
        description: "",
        preview: "",
        modes: ["practice"],
        music: "map",
        load: { scene: "practice" },
      },
      mode: "practice",
    };
  if (!trackParam) return undefined;
  const byNumber = /^\d+$/.test(trackParam)
    ? TRACKS.find((t) => t.legacyNumber === Number(trackParam))
    : undefined;
  const entry = byNumber ??
    trackById(trackParam) ?? {
      id: trackParam,
      name: trackParam,
      description: "",
      preview: "",
      modes: ["race", "timeTrial"],
      music: "race",
      load: { scene: "track" as const, packageId: trackParam },
    };
  return { entry, mode: PARAMS.has("solo") ? "timeTrial" : "race" };
}

const fromUrl = urlTrack();
const racerParam = PARAMS.get("racer");
if (racerParam && (RACER_IDS as string[]).includes(racerParam))
  game.selection.racer = racerParam as RacerId;

/** ?shot=<track>[&skip=<s>]: the title demo on a track with no UI, for preview pictures. */
function shotScreen(id: string): Screen {
  let session: Awaited<ReturnType<Game["createSession"]>> | undefined;
  const entry =
    trackById(id) ?? (id === TITLE_TRACK.id ? TITLE_TRACK : undefined) ?? trackById("drift_loop")!;
  return {
    id: "TITLE",
    enter() {
      void game
        .createSession({
          ...entry.load,
          rivals: entry.load.scene === "track",
          racer: game.selection.racer,
          demo: true,
        })
        .then((s) => {
          // &skip=<seconds>: fast-forward the demo to a better spot for the picture.
          const skip = Number(PARAMS.get("skip") ?? 0);
          for (let i = 0; i < skip * 120; i++) s.update(1 / 120);
          session = s;
        });
    },
    step: (dt) => session?.update(dt),
    render3d(alpha, fs) {
      if (!session) return false;
      session.render(alpha, fs);
      stage.render();
      return true;
    },
    frame() {},
    draw() {},
  };
}

if (PARAMS.get("shot")) screens.go(shotScreen(PARAMS.get("shot")!));
// ?adventure (dev server only): straight to the Adventure world map.
else if (import.meta.env.DEV && PARAMS.has("adventure")) screens.go(adventureHub(game));
// ?overworld (dev server only): free roam in the overworld's test region.
else if (import.meta.env.DEV && PARAMS.has("overworld"))
  screens.go(overworldLoading(game, PARAMS.get("overworld") || "test_valley"));
else if (fromUrl) {
  // Straight into a race: the frontend is one Escape (pause) away.
  game.selection.trackId = fromUrl.entry.id;
  game.selection.mode = fromUrl.mode;
  if (!trackById(fromUrl.entry.id)) {
    // An unlisted Blender track: register it for this visit so the loader can find it.
    TRACKS.push(fromUrl.entry);
  }
  screens.go(loadingScreen(game));
} else screens.go(bootScreen(game));

// F4 saves the last 20-40 s of play as a video (dev server only; ?noclips turns it off).
const clips =
  import.meta.env.DEV && !PARAMS.has("noclips")
    ? createClipRecorder({
        view: stage.renderer.domElement,
        hud: app.querySelector("canvas.ui-layer"),
        audio: () => audio.recordStream(),
        session: () => game.session,
        trackId: () => game.session && game.selection.trackId,
      })
    : undefined;

// ---------------------------------------------------------------- the loop

const loop = createLoop(tuning.loop.physicsHz, tuning.loop.maxStepsPerFrame, {
  update(dt, _tick, at) {
    // Throttle presses only count from the step they happened in (core/input.ts).
    gameInput.setStepTime(at);
    screens.step(dt);
  },
  render(alpha, frameSeconds) {
    const dt = Math.min(frameSeconds, 0.1);
    screens.frame(dt);
    screens.render3d(alpha, frameSeconds);
    screens.draw(dt);
    clips?.frame();
  },
});

// Developer conveniences that work in any race.
window.addEventListener("keydown", (e) => {
  if (e.repeat || screens.top?.id !== "RACING") return;
  // V: the two looks, soft 360 lines or sharp full resolution.
  if (e.code === "KeyV") {
    const soft = settings.video.filtering !== "soft";
    Object.assign(
      settings.video,
      soft ? { filtering: "soft", resolution: 360 } : { filtering: "sharp", resolution: 0 },
    );
    game.applySettings();
    game.session?.showToast(soft ? "Look: soft (V)" : "Look: sharp (V)", 1.5);
  }
});
// The dev server says a Blender track was re-exported: reload it in place.
if (import.meta.hot)
  import.meta.hot.on("kp:track-changed", (data: { id: string }) => {
    if (game.session && data.id === game.session.packageId) void game.session.reloadTrack();
  });
if (debugMode)
  Object.assign(window, {
    kp: {
      game,
      stage,
      tuning,
      get session() {
        return game.session;
      },
    },
  });

loop.start();
