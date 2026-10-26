// Render songs to WAV files (SONGS=<id,id> OUT=<dir>), to listen to them outside the game.
import { test } from "vitest";
import { writeFileSync } from "node:fs";
import { SONGS } from "../../src/audio/songs";
import { normalise, renderSongData } from "../../src/audio/dsp";

test("wav", () => {
  const rate = 32000;
  for (const id of (process.env.SONGS ?? "").split(",")) {
    const song = SONGS[id]!;
    const stems = renderSongData(song, rate);
    normalise(stems, 0.8);
    const mix = new Float32Array(stems.base!.length);
    for (const d of Object.values(stems)) for (let i = 0; i < mix.length; i++) mix[i]! += d[i] ?? 0;
    const n = mix.length * 2; // two loops' worth would be nice, one is enough
    const buf = Buffer.alloc(44 + n);
    buf.write("RIFF", 0);
    buf.writeUInt32LE(36 + n, 4);
    buf.write("WAVEfmt ", 8);
    buf.writeUInt32LE(16, 16);
    buf.writeUInt16LE(1, 20);
    buf.writeUInt16LE(1, 22);
    buf.writeUInt32LE(rate, 24);
    buf.writeUInt32LE(rate * 2, 28);
    buf.writeUInt16LE(2, 32);
    buf.writeUInt16LE(16, 34);
    buf.write("data", 36);
    buf.writeUInt32LE(n, 40);
    for (let i = 0; i < mix.length; i++)
      buf.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(mix[i]! * 32767))), 44 + i * 2);
    writeFileSync(`${process.env.OUT}/${id}.wav`, buf);
  }
}, 600000);
