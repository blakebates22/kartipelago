/**
 * Menu sounds and racer calls, played live through the audio engine.
 *
 * Each racer has a three-note call in their own instrument from "Pick Your Racer"
 * (Tiko marimba, Brakka bassoon, Pebble clarinet, Zephyr flute; see designs.ts), on the voice
 * bus when you highlight them, and a happier version when you pick them.
 */
import type { AudioEngine } from "./engine";
import type { InstrumentId } from "./instruments";
import { DESIGNS, RACER_IDS, type RacerId } from "../render/racers/designs";

const CALLS: Record<RacerId, { inst: InstrumentId; notes: number[] }> = Object.fromEntries(
  RACER_IDS.map((id) => [id, DESIGNS[id].call]),
) as Record<RacerId, { inst: InstrumentId; notes: number[] }>;

/**
 * The race announcer: a friendly, playful voice, no rasp (made for this game: synthesised
 * speech, pitched down a little; tools/voice/make_announcer.py). Three voices to choose
 * from, ?voice=a|b|c: a friendly dino, b a big gentle one, c a bright little one.
 */
/** The announcer is off for now (Blake: it threw him off; to revisit). */
const ANNOUNCER_ON = false;
const announcer = () => {
  const v =
    typeof location !== "undefined" ? new URLSearchParams(location.search).get("voice") : null;
  return v === "b" || v === "c" ? v : "a";
};

export function createUiSounds(audio: AudioEngine) {
  return {
    move: () => audio.notes("sfx", [["woodblock", 84, 0, 0.05, 0.55]], 0.8),
    confirm: () =>
      audio.notes("sfx", [
        ["marimba", 79, 0, 0.15],
        ["marimba", 86, 0.07, 0.3],
      ]),
    back: () =>
      audio.notes("sfx", [
        ["marimba", 79, 0, 0.15, 0.7],
        ["marimba", 72, 0.07, 0.3, 0.7],
      ]),
    error: () =>
      audio.notes("sfx", [
        ["bassoon", 43, 0, 0.12, 0.7],
        ["bassoon", 42, 0.12, 0.2, 0.7],
      ]),
    tick: () => audio.notes("sfx", [["woodblock", 91, 0, 0.03, 0.4]], 0.6),
    start: () =>
      audio.notes("sfx", [
        ["xylophone", 72, 0, 0.1],
        ["xylophone", 76, 0.06, 0.1],
        ["xylophone", 79, 0.12, 0.1],
        ["xylophone", 84, 0.18, 0.4],
        ["crash", 0, 0.18, 0.6, 0.4],
      ]),
    pause: () =>
      audio.notes("sfx", [
        ["celesta", 84, 0, 0.2],
        ["celesta", 79, 0.09, 0.4],
      ]),
    unpause: () =>
      audio.notes("sfx", [
        ["celesta", 79, 0, 0.2],
        ["celesta", 84, 0.09, 0.4],
      ]),
    /** Highlighting a racer: their call. */
    racer(id: RacerId) {
      const c = CALLS[id];
      audio.notes(
        "voice",
        c.notes.map(
          (m, i) =>
            [c.inst, m, i * 0.09, 0.16, 0.75] as [InstrumentId, number, number, number, number],
        ),
      );
    },
    /** Picking a racer: their call, up and back down, with a cheer. */
    racerPicked(id: RacerId) {
      const c = CALLS[id];
      const [a, b, d] = c.notes as [number, number, number];
      audio.notes("voice", [
        [c.inst, a, 0, 0.12, 0.85],
        [c.inst, b, 0.08, 0.12, 0.85],
        [c.inst, d, 0.16, 0.12, 0.9],
        [c.inst, d + 5, 0.24, 0.45, 0.95],
        ["tamb", 0, 0.24, 0.2, 0.7],
      ]);
    },
    /** Countdown: a wood knock and the announcer's "Get ready!", then a bright GO. */
    count: () => {
      audio.notes("sfx", [["woodblock", 79, 0, 0.08, 0.9]]);
      if (ANNOUNCER_ON) audio.sample("voice", `audio/voice/${announcer()}_ready.mp3`, 0.9);
    },
    go: () => {
      audio.notes("sfx", [
        ["xylophone", 84, 0, 0.3, 0.9],
        ["xylophone", 91, 0, 0.3, 0.7],
      ]);
      if (ANNOUNCER_ON) audio.sample("voice", `audio/voice/${announcer()}_go.mp3`, 0.95);
    },
    /** Load the announcer's lines before a race starts. */
    preloadAnnouncer() {
      if (!ANNOUNCER_ON) return;
      audio.preload(`audio/voice/${announcer()}_ready.mp3`);
      audio.preload(`audio/voice/${announcer()}_go.mp3`);
    },
    lap: () =>
      audio.notes("sfx", [
        ["celesta", 79, 0, 0.12],
        ["celesta", 84, 0.1, 0.12],
        ["celesta", 88, 0.2, 0.3],
      ]),
    finalLap: () =>
      audio.notes("sfx", [
        ["brass", 72, 0, 0.12, 0.8],
        ["brass", 72, 0.14, 0.12, 0.8],
        ["brass", 79, 0.28, 0.45, 0.9],
      ]),
    /** The overworld's puzzles (src/overworld/puzzles.ts): a switch stone pressed (each
     * one higher), the drums beating while they run, the stones popping back up, the
     * puzzle solved, and its prize. */
    stone: (n: number) =>
      audio.notes("sfx", [
        ["tom", 45 + n * 5, 0, 0.2, 0.9],
        ["marimba", 67 + n * 5, 0, 0.12],
        ["marimba", 74 + n * 5, 0.08, 0.3],
      ]),
    bell: (n: number) =>
      audio.notes("sfx", [
        ["bell", 67 + [0, 4, 7, 12][Math.min(3, n - 1)]!, 0, 1.2, 0.9],
        ["celesta", 79 + [0, 4, 7, 12][Math.min(3, n - 1)]!, 0, 0.6, 0.6],
      ]),
    drum: (hurry: boolean) =>
      audio.notes("sfx", [["tom", hurry ? 52 : 45, 0, 0.12, hurry ? 0.75 : 0.55]], 0.7),
    stonesReset: () =>
      audio.notes("sfx", [
        ["bassoon", 50, 0, 0.15, 0.8],
        ["bassoon", 46, 0.15, 0.15, 0.8],
        ["bassoon", 41, 0.3, 0.4, 0.8],
      ]),
    solved: () =>
      audio.notes("sfx", [
        ["tom", 40, 0, 0.6, 1],
        ["brass", 67, 0.1, 0.15, 0.8],
        ["brass", 72, 0.25, 0.15, 0.8],
        ["brass", 76, 0.4, 0.15, 0.8],
        ["brass", 79, 0.55, 0.6, 0.9],
        ["crash", 0, 0.55, 0.8, 0.5],
      ]),
    keyFound: () =>
      audio.notes("sfx", [
        ["celesta", 84, 0, 0.12],
        ["celesta", 88, 0.08, 0.12],
        ["celesta", 91, 0.16, 0.12],
        ["celesta", 96, 0.24, 0.5],
        ["xylophone", 96, 0.24, 0.5, 0.6],
      ]),
  };
}

export type UiSounds = ReturnType<typeof createUiSounds>;
