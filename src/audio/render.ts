/**
 * Turns a Song into AudioBuffers to loop: rendered by the synthesizer in dsp.ts, in a
 * worker when the browser has one (otherwise right here).
 *
 * 32 kHz, like a lot of late-90s console music: plenty for this band, and it keeps
 * the buffers small. Stems are mono; the music bus adds width with its reverb.
 */
import { renderSongData } from "./dsp";
import type { Song } from "./score";

export const MUSIC_RATE = 32000;

export interface RenderedSong {
  song: Song;
  /** Buffer per stem ("base" plus the song's stems). */
  stems: Record<string, AudioBuffer>;
  /** Loop (or piece) length, seconds. */
  seconds: number;
}

type Reply = { id: string; stems?: Record<string, Float32Array>; error?: string };

let worker: Worker | undefined;
let workerFailed = false;
const waiting = new Map<
  string,
  { resolve: (s: Record<string, Float32Array>) => void; reject: (e: Error) => void }[]
>();

function getWorker(): Worker | undefined {
  if (worker || workerFailed || typeof Worker === "undefined") return worker;
  try {
    worker = new Worker(new URL("./musicWorker.ts", import.meta.url), { type: "module" });
    worker.onmessage = (e: MessageEvent<Reply>) => {
      const list = waiting.get(e.data.id) ?? [];
      waiting.delete(e.data.id);
      for (const w of list)
        e.data.stems ? w.resolve(e.data.stems) : w.reject(new Error(e.data.error));
    };
    worker.onerror = () => {
      // Fall back to rendering on this thread from now on.
      workerFailed = true;
      worker = undefined;
      for (const [id, list] of waiting)
        for (const w of list) w.reject(new Error(`worker failed (${id})`));
      waiting.clear();
    };
  } catch {
    workerFailed = true;
  }
  return worker;
}

function stemsFor(song: Song): Promise<Record<string, Float32Array>> {
  const w = getWorker();
  if (!w) return Promise.resolve(renderSongData(song, MUSIC_RATE));
  return new Promise((resolve, reject) => {
    const list = waiting.get(song.id) ?? [];
    list.push({ resolve, reject });
    waiting.set(song.id, list);
    if (list.length === 1) w.postMessage({ id: song.id, rate: MUSIC_RATE });
  }).catch(() => renderSongData(song, MUSIC_RATE)) as Promise<Record<string, Float32Array>>;
}

/** Render every stem of a song into AudioBuffers. */
export async function renderSong(song: Song): Promise<RenderedSong> {
  const data = await stemsFor(song);
  const stems: Record<string, AudioBuffer> = {};
  for (const [name, d] of Object.entries(data)) {
    const buf = new AudioBuffer({ numberOfChannels: 1, length: d.length, sampleRate: MUSIC_RATE });
    buf.copyToChannel(d as Float32Array<ArrayBuffer>, 0);
    stems[name] = buf;
  }
  return { song, stems, seconds: (song.beats * 60) / song.bpm };
}
