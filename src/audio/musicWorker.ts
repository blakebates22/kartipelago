/**
 * Renders the soundtrack off the main thread, so the menus never stutter while a
 * piece is being prepared. Receives { id, rate }, answers { id, stems } (mono
 * Float32Arrays, transferred).
 */
import { renderSongData } from "./dsp";
import { SONGS } from "./songs";

self.onmessage = (e: MessageEvent<{ id: string; rate: number }>) => {
  const { id, rate } = e.data;
  const song = SONGS[id];
  if (!song) {
    self.postMessage({ id, error: `No song "${id}"` });
    return;
  }
  try {
    const stems = renderSongData(song, rate);
    self.postMessage({ id, stems }, { transfer: Object.values(stems).map((s) => s.buffer) });
  } catch (err) {
    self.postMessage({ id, error: String(err) });
  }
};
