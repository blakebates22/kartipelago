/**
 * Tunable game parameters.
 *
 * All "feel" values live in assets/data/tuning.json, never hardcoded in game code.
 * In dev, editing the JSON hot-reloads it. The debug panel (backtick key) edits the
 * same object live, and "Copy tuning JSON" lets you paste good values back into the file.
 */
import defaults from "../../assets/data/tuning.json";

export type Tuning = typeof defaults;

/** Deep copy so live edits never mutate the imported module. */
export const tuning: Tuning = structuredClone(defaults);

/** Replace all values in place, keeping object identity so references stay valid. */
export function applyTuning(next: Tuning): void {
  for (const key of Object.keys(next) as (keyof Tuning)[]) {
    Object.assign(tuning[key], next[key]);
  }
}

export function tuningAsJson(): string {
  return JSON.stringify(tuning, null, 2) + "\n";
}

if (import.meta.hot) {
  import.meta.hot.accept("../../assets/data/tuning.json", (mod) => {
    if (mod) applyTuning(mod.default as Tuning);
  });
}
