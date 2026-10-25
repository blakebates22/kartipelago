/**
 * The clip recorder (dev server only): press F4 and the last 20-40 seconds of play are
 * saved as a video, with the sound, and beside it a JSON file of your kart's state every
 * frame, so a bug can be watched and then replayed exactly.
 *
 * Two recorders run all the time, half a cycle apart, each restarting every CYCLE
 * seconds; F4 takes whichever has been running longer. Each frame the game's 3D view and
 * the HUD are drawn into one canvas with a line of readings under it (time, speed,
 * height, vertical speed, on the ground, zipper, boost), and that canvas is what's filmed.
 *
 * Files go to reviews/<track>/clips/ (tools/reviewStore.mjs); the folder is git-ignored.
 * Without the dev server they're downloaded instead. Turn it off with ?noclips.
 */
import type { Session } from "../game/session";

const CYCLE = 40;
const FPS = 60;
/** Kart readings kept, seconds (a little more than the longest clip). */
const KEEP = CYCLE + 5;
const MAX_W = 1280;
const MIN_W = 960;
const STRIP = 22;

type Sample = Record<string, number | boolean | string>;

export interface ClipSources {
  view: HTMLCanvasElement;
  hud: HTMLCanvasElement | null;
  audio: () => MediaStream | undefined;
  session: () => Session | undefined;
  trackId: () => string | undefined;
}

function pickType() {
  const types = [
    "video/mp4;codecs=avc1.640028,mp4a.40.2",
    "video/mp4",
    "video/webm;codecs=vp9,opus",
    "video/webm",
  ];
  return types.find((t) => MediaRecorder.isTypeSupported(t)) ?? "";
}

export function createClipRecorder(src: ClipSources) {
  const comp = document.createElement("canvas");
  const g = comp.getContext("2d")!;
  const type = pickType();
  const ext = type.startsWith("video/mp4") ? "mp4" : "webm";
  let stream: MediaStream | undefined;
  const samples: { t: number; s: Sample }[] = [];
  const start = performance.now();
  const now = () => (performance.now() - start) / 1000;

  const toast = document.createElement("div");
  toast.style.cssText =
    "position:fixed;left:12px;top:12px;z-index:200;padding:6px 10px;background:rgba(20,12,8,.9);" +
    "color:#ffd84a;font:13px ui-monospace,Menlo,monospace;border:2px solid #8a5a32;display:none";
  document.body.appendChild(toast);
  let toastTimer: ReturnType<typeof setTimeout> | undefined;
  const say = (text: string, sec = 4) => {
    toast.textContent = text;
    toast.style.display = "block";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toast.style.display = "none"), sec * 1000);
  };

  interface Rec {
    mr: MediaRecorder;
    since: number;
    chunks: Blob[];
    onStop?: (b: Blob) => void;
  }
  const recs: Rec[] = [];

  const begin = (r: Rec) => {
    r.chunks = [];
    r.since = now();
    r.mr.start(1000);
  };
  const makeRec = (): Rec | undefined => {
    if (!stream) return undefined;
    const mr = new MediaRecorder(stream, {
      mimeType: type || undefined,
      videoBitsPerSecond: 6_000_000,
    });
    const r: Rec = { mr, since: now(), chunks: [] };
    mr.ondataavailable = (e) => {
      if (e.data.size) r.chunks.push(e.data);
    };
    mr.onstop = () => {
      const blob = new Blob(r.chunks, { type: type || "video/webm" });
      const done = r.onStop;
      r.onStop = undefined;
      begin(r);
      done?.(blob);
    };
    return r;
  };

  /** Browsers only allow sound after a key or click, so filming starts on the first one. */
  let gestured = false;
  const ensureStarted = () => {
    if (stream || !gestured || !comp.width || typeof MediaRecorder === "undefined") return;
    stream = comp.captureStream(FPS);
    const a = src.audio();
    if (a) for (const t of a.getAudioTracks()) stream.addTrack(t);
    const first = makeRec();
    if (first) {
      recs.push(first);
      begin(first);
    }
    // The second starts half a cycle later.
    setTimeout(
      () => {
        const second = makeRec();
        if (second) {
          recs.push(second);
          begin(second);
        }
      },
      (CYCLE / 2) * 1000,
    );
  };

  // Restart any recorder that has run a whole cycle (unless it's being saved).
  setInterval(() => {
    for (const r of recs)
      if (!r.onStop && r.mr.state === "recording" && now() - r.since > CYCLE) {
        r.onStop = () => {};
        r.mr.stop();
      }
  }, 500);

  const upload = async (track: string, file: string, body: Blob) => {
    try {
      const res = await fetch(`/__clips/${track}/${file}`, { method: "POST", body });
      if (!res.ok) throw new Error(String(res.status));
      return `reviews/${track}/clips/${file}`;
    } catch {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(body);
      a.download = file;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 10_000);
      return `Downloads/${file}`;
    }
  };

  const save = () => {
    const r = recs
      .filter((q) => q.mr.state === "recording" && !q.onStop)
      .sort((a, b) => a.since - b.since)[0];
    if (!r) {
      say("Clip recorder isn't running yet");
      return;
    }
    const from = r.since;
    const to = now();
    const track = src.trackId() ?? "menu";
    const d = new Date();
    const p = (n: number) => String(n).padStart(2, "0");
    const name = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
    say(`Saving the last ${Math.round(to - from)} s...`, 10);
    r.onStop = (blob) => {
      const log = {
        track,
        seconds: to - from,
        video: `${name}.${ext}`,
        note: "t is seconds from the start of the video; s is your kart's state that frame.",
        frames: samples
          .filter((q) => q.t >= from)
          .map((q) => ({ t: +(q.t - from).toFixed(3), s: q.s })),
      };
      void Promise.all([
        upload(track, `${name}.${ext}`, blob),
        upload(
          track,
          `${name}.json`,
          new Blob([JSON.stringify(log)], { type: "application/json" }),
        ),
      ]).then(([where]) => say(`Clip saved: ${where}`, 6));
    };
    r.mr.stop();
  };

  window.addEventListener("keydown", (e) => {
    if (e.code === "F4" && !e.repeat) {
      e.preventDefault();
      save();
    }
  });
  const kick = () => (gestured = true);
  window.addEventListener("keydown", kick);
  window.addEventListener("pointerdown", kick);

  const fmt = (v: unknown, n = 1) => (typeof v === "number" ? v.toFixed(n) : String(v ?? "-"));

  return {
    /** Call after the frame is drawn (3D view and HUD). */
    frame() {
      const vw = src.view.width;
      const vh = src.view.height;
      if (!vw || !vh) return;
      // The game draws at a low resolution: film it at least MIN_W wide, in sharp pixels.
      const scale = Math.min(MAX_W, Math.max(MIN_W, vw)) / vw;
      const w = Math.round((vw * scale) / 2) * 2;
      const h = Math.round((vh * scale) / 2) * 2;
      if (comp.width !== w || comp.height !== h + STRIP) {
        comp.width = w;
        comp.height = h + STRIP;
      }
      g.imageSmoothingEnabled = false;
      g.drawImage(src.view, 0, 0, w, h);
      if (src.hud) g.drawImage(src.hud, 0, 0, w, h);

      const t = now();
      const k = src.session()?.entrants[0]?.state as unknown as Sample | undefined;
      g.fillStyle = "#140c08";
      g.fillRect(0, h, w, STRIP);
      g.fillStyle = "#ffd84a";
      g.font = "14px ui-monospace, Menlo, monospace";
      g.fillText(
        k
          ? `t ${t.toFixed(2)}  v ${fmt(k.speed)}  y ${fmt(k.y, 2)}  vy ${fmt(k.vy)}  ${k.grounded ? "GND" : "AIR"}  zip ${fmt(k.zipPhase, 0)}  boost ${fmt(k.boostTime, 2)}x${fmt(k.boostMult, 2)}  xz ${fmt(k.x)},${fmt(k.z)}`
          : `t ${t.toFixed(2)}`,
        6,
        h + 16,
      );

      if (k) {
        const s: Sample = {};
        for (const [key, v] of Object.entries(k))
          if (typeof v === "number") s[key] = Number.isFinite(v) ? +v.toFixed(4) : String(v);
          else if (typeof v === "boolean" || typeof v === "string") s[key] = v;
        samples.push({ t, s });
      }
      while (samples.length && samples[0]!.t < t - KEEP) samples.shift();
      ensureStarted();
    },
  };
}
