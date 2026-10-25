/**
 * Personal bests, kept in this browser: per track, the best Time Trial and the best lap
 * driven in a Time Trial. Only Time Trials count: a race against the rivals is never a
 * record (items, bumps and the field make its times something else). Like settings,
 * unreadable storage just means no records yet.
 */
import { safeStorage } from "./settings";

export type RaceMode = "race" | "timeTrial";

export interface TrackRecord {
  /** Best lap, Time Trials only. */
  bestLap?: number;
  /** Best total time: Time Trials only (`race` is never kept). */
  best: { timeTrial?: number };
}

const KEY = "kartipelago.records.v2";
/** The first store, which also kept races (and their laps) as records. */
const OLD_KEY = "kartipelago.records.v1";

type Store = Pick<Storage, "getItem" | "setItem">;

const ok = (v: unknown) => (typeof v === "number" && v > 0 && Number.isFinite(v) ? v : undefined);

function parse(raw: string | null | undefined) {
  const v = JSON.parse(raw ?? "{}") as unknown;
  return typeof v === "object" && v !== null
    ? (v as Record<string, { bestLap?: unknown; best?: { race?: unknown; timeTrial?: unknown } }>)
    : {};
}

export function loadRecords(
  storage: Store | undefined = safeStorage(),
): Record<string, TrackRecord> {
  try {
    const now = storage?.getItem(KEY);
    const out: Record<string, TrackRecord> = {};
    if (now !== null && now !== undefined) {
      for (const [id, r] of Object.entries(parse(now)))
        out[id] = { bestLap: ok(r?.bestLap), best: { timeTrial: ok(r?.best?.timeTrial) } };
      return out;
    }
    // From the first store: the Time Trial bests, and the best lap only where no race was
    // ever kept (then every lap it knew was a Time Trial's).
    for (const [id, r] of Object.entries(parse(storage?.getItem(OLD_KEY)))) {
      const trial = ok(r?.best?.timeTrial);
      const lap = ok(r?.best?.race) === undefined ? ok(r?.bestLap) : undefined;
      if (trial !== undefined || lap !== undefined)
        out[id] = { bestLap: lap, best: { timeTrial: trial } };
    }
    return out;
  } catch {
    return {};
  }
}

export interface NewRecords {
  lap: boolean;
  race: boolean;
  /** The previous bests, for "beat it by…" (a race shows the Time Trial lap record). */
  previousLap?: number;
  previousRace?: number;
}

/** Record a finished race; says which bests it beat (a race against rivals: none). */
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
  if (mode !== "timeTrial") return { lap: false, race: false, previousLap };
  const previousRace = rec.best.timeTrial;
  const lap = previousLap === undefined || bestLap < previousLap;
  const race = previousRace === undefined || totalTime < previousRace;
  if (lap) rec.bestLap = bestLap;
  if (race) rec.best.timeTrial = totalTime;
  all[trackId] = rec;
  try {
    storage?.setItem(KEY, JSON.stringify(all));
  } catch {
    // not saved
  }
  return { lap, race, previousLap, previousRace };
}
