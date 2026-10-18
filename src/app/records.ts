/**
 * Personal bests, kept in this browser: best lap and best race time per track and
 * mode. Like settings, unreadable storage just means no records yet.
 */
import { safeStorage } from "./settings";

export type RaceMode = "race" | "timeTrial";

export interface TrackRecord {
  bestLap?: number;
  /** Best total time, by mode. */
  best: Partial<Record<RaceMode, number>>;
}

const KEY = "kartipelago.records.v1";

type Store = Pick<Storage, "getItem" | "setItem">;

export function loadRecords(
  storage: Store | undefined = safeStorage(),
): Record<string, TrackRecord> {
  try {
    const raw = JSON.parse(storage?.getItem(KEY) ?? "{}") as unknown;
    if (typeof raw !== "object" || raw === null) return {};
    const out: Record<string, TrackRecord> = {};
    for (const [id, r] of Object.entries(raw as Record<string, Partial<TrackRecord>>)) {
      const ok = (v: unknown) =>
        typeof v === "number" && v > 0 && Number.isFinite(v) ? v : undefined;
      out[id] = {
        bestLap: ok(r?.bestLap),
        best: { race: ok(r?.best?.race), timeTrial: ok(r?.best?.timeTrial) },
      };
    }
    return out;
  } catch {
    return {};
  }
}

export interface NewRecords {
  lap: boolean;
  race: boolean;
  /** The previous bests, for "beat it by…". */
  previousLap?: number;
  previousRace?: number;
}

/** Record a finished race; says which bests it beat. */
export function submitResult(
  trackId: string,
  mode: RaceMode,
  totalTime: number,
  bestLap: number,
  storage: Store | undefined = safeStorage(),
): NewRecords {
  const all = loadRecords(storage);
  const rec = all[trackId] ?? { best: {} };
  const previousLap = rec.bestLap;
  const previousRace = rec.best[mode];
  const lap = previousLap === undefined || bestLap < previousLap;
  const race = previousRace === undefined || totalTime < previousRace;
  if (lap) rec.bestLap = bestLap;
  if (race) rec.best[mode] = totalTime;
  all[trackId] = rec;
  try {
    storage?.setItem(KEY, JSON.stringify(all));
  } catch {
    // not saved
  }
  return { lap, race, previousLap, previousRace };
}
