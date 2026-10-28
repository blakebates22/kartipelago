/**
 * Dev-build switches kept between visits (the dev menu's TESTING TOOLS). Off, and inert,
 * in the published game.
 */
import { safeStorage } from "../app/settings";

const INSTA_WIN = "kartipelago.dev.instaWin";

/** Insta-win (Blake, Oct 27: to get through Adventure faster): every race you enter is
 * won the moment it starts, every shard piece taken, the rivals behind you. */
export function instaWin(): boolean {
  if (!import.meta.env.DEV) return false;
  try {
    return safeStorage()?.getItem(INSTA_WIN) === "on";
  } catch {
    return false;
  }
}

export function setInstaWin(on: boolean) {
  try {
    safeStorage()?.setItem(INSTA_WIN, on ? "on" : "off");
  } catch {
    // (no storage: stays as it was)
  }
}

const BOOST = "kartipelago.dev.infiniteBoost";

/** Infinite boost (Blake, Oct 27: to get round the overworlds faster): while it's on,
 * holding the item key (E) keeps your kart on a zipper boost; it fires no items. */
export function infiniteBoost(): boolean {
  if (!import.meta.env.DEV) return false;
  try {
    return safeStorage()?.getItem(BOOST) === "on";
  } catch {
    return false;
  }
}

export function setInfiniteBoost(on: boolean) {
  try {
    safeStorage()?.setItem(BOOST, on ? "on" : "off");
  } catch {
    // (no storage: stays as it was)
  }
}
