/**
 * Which racers you can pick. Four from the start; the other four join your crew in
 * Adventure (each kingdom's champion, once you've beaten them in its championship) and
 * stay unlocked everywhere, in Tracks mode and in every new adventure. Kept in this
 * browser, apart from the Adventure save, so starting a new adventure keeps them.
 */
import { RACER_IDS, type RacerId } from "../render/racers/designs";
import { safeStorage } from "./settings";

export const STARTERS: RacerId[] = ["tiko", "brakka", "pebble", "zephyr"];
const KEY = "kartipelago.unlocks.v1";

type Store = Pick<Storage, "getItem" | "setItem">;

export function loadUnlocked(
  storage: Pick<Store, "getItem"> | undefined = safeStorage(),
): Set<RacerId> {
  const out = new Set<RacerId>(STARTERS);
  try {
    const raw = JSON.parse(storage?.getItem(KEY) ?? "{}") as { racers?: unknown };
    if (Array.isArray(raw.racers))
      for (const r of raw.racers) if ((RACER_IDS as unknown[]).includes(r)) out.add(r as RacerId);
  } catch {
    // Unreadable: just the starters.
  }
  return out;
}

function save(racers: Set<RacerId>, storage: Pick<Store, "setItem"> | undefined) {
  try {
    storage?.setItem(
      KEY,
      JSON.stringify({ racers: [...racers].filter((r) => !STARTERS.includes(r)) }),
    );
  } catch {
    // Storage blocked: unlocked for this visit only.
  }
}

/** A racer joins the crew. Returns true if they're new. */
export function unlockRacer(id: RacerId, storage: Store | undefined = safeStorage()): boolean {
  const have = loadUnlocked(storage);
  if (have.has(id)) return false;
  have.add(id);
  save(have, storage);
  return true;
}

/** Dev tools: everyone, or back to the starters. */
export function setAllUnlocked(on: boolean, storage: Store | undefined = safeStorage()) {
  save(on ? new Set(RACER_IDS) : new Set(STARTERS), storage);
}
