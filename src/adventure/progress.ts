/**
 * Adventure progress: what the player has done (a small saved record) and everything
 * worked out from it (which kingdoms are open, each one's phase, the next scene due).
 * Plain data and functions, no rendering; the rules read the story data (data.ts).
 *
 * The record only ever gains things, so replaying a race never undoes the story, and a
 * map piece is earned only by a race that took all four coins AND was won: coins taken
 * in a lost race are not kept.
 */
import {
  DRAGON,
  KINGDOMS,
  STORY_ORDER,
  kingdomById,
  type AdventureCourse,
  type Kingdom,
  type KingdomId,
} from "./data";

export interface AdventureSave {
  version: 1;
  /** Championships (Trophy Race cups) won; the Dragon Kingdom's is its first visit. */
  cups: Partial<Record<KingdomId, boolean>>;
  /** Map pieces earned, by the standard course's track id. */
  pieces: Record<string, boolean>;
  /** Demi-bosses beaten. */
  bosses: Partial<Record<KingdomId, boolean>>;
  /** Act V: return objectives done. */
  returns: Partial<Record<KingdomId, boolean>>;
  /** The second visit to the Dragon Kingdom: its ruined courses' cup. */
  finalCup: boolean;
  /** The scripted first race against the King (always lost), then the Chosen One's. */
  kingLost: boolean;
  kingWon: boolean;
  /** Scenes already shown (each plays once; the scene list can replay them). */
  seen: string[];
}

export const newSave = (): AdventureSave => ({
  version: 1,
  cups: {},
  pieces: {},
  bosses: {},
  returns: {},
  finalCup: false,
  kingLost: false,
  kingWon: false,
  seen: [],
});

const KEY = "kartipelago.adventure.v1";
type Store = Pick<Storage, "getItem" | "setItem" | "removeItem">;

const flags = (v: unknown): Record<string, boolean> => {
  const out: Record<string, boolean> = {};
  if (v && typeof v === "object")
    for (const [k, x] of Object.entries(v as Record<string, unknown>))
      if (x === true) out[k] = true;
  return out;
};

/** Anything read from storage, made safe (unknown keys dropped, wrong types reset). */
export function sanitizeSave(raw: unknown): AdventureSave {
  const r = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  const s = newSave();
  s.cups = flags(r.cups);
  s.pieces = flags(r.pieces);
  s.bosses = flags(r.bosses);
  s.returns = flags(r.returns);
  s.finalCup = r.finalCup === true;
  s.kingLost = r.kingLost === true;
  s.kingWon = r.kingWon === true;
  s.seen = Array.isArray(r.seen) ? r.seen.filter((x): x is string => typeof x === "string") : [];
  return s;
}

export function loadAdventure(
  storage: Pick<Store, "getItem"> | undefined,
): AdventureSave | undefined {
  try {
    const raw = storage?.getItem(KEY);
    return raw ? sanitizeSave(JSON.parse(raw)) : undefined;
  } catch {
    return undefined;
  }
}

export function saveAdventure(s: AdventureSave, storage: Pick<Store, "setItem"> | undefined) {
  try {
    storage?.setItem(KEY, JSON.stringify(s));
  } catch {
    // Storage full or blocked: progress still counts for this visit.
  }
}

export function eraseAdventure(storage: Pick<Store, "removeItem"> | undefined) {
  try {
    storage?.removeItem(KEY);
  } catch {
    // Nothing to erase.
  }
}

// ---------------------------------------------------------------- what follows from it

export type KingdomPhase = "locked" | "championship" | "coins" | "boss" | "done";
export type DragonPhase =
  | "locked"
  | "first" // its four standard courses, as a cup
  | "return" // the sacrifice is over: back to the four kingdoms
  | "final" // the Chosen One is back: its four ruined courses, as a cup
  | "king" // the Dragon King (first the scripted race, then as the Chosen One)
  | "done";

export const piecesOf = (s: AdventureSave, k: Kingdom) =>
  k.courses.filter((c) => s.pieces[c.track]).length;

/** Open once the kingdom before it in the story has been freed (the valley always). */
export function unlocked(s: AdventureSave, id: KingdomId): boolean {
  const i = STORY_ORDER.indexOf(id);
  if (i <= 0) return true;
  return Boolean(s.bosses[STORY_ORDER[i - 1]!]);
}

export function kingdomPhase(s: AdventureSave, k: Kingdom): KingdomPhase {
  if (!unlocked(s, k.id)) return "locked";
  if (s.bosses[k.id]) return "done";
  if (!s.cups[k.id]) return "championship";
  if (piecesOf(s, k) < k.courses.length) return "coins";
  if (!s.bosses[k.id]) return "boss";
  return "done";
}

export const allReturned = (s: AdventureSave) => KINGDOMS.every((k) => s.returns[k.id]);

export function dragonPhase(s: AdventureSave): DragonPhase {
  if (!unlocked(s, "dragon")) return "locked";
  if (!s.cups.dragon) return "first";
  if (!allReturned(s)) return "return";
  if (!s.finalCup) return "final";
  if (!s.kingWon) return "king";
  return "done";
}

/** The tools in the bag: one from each freed kingdom. */
export const toolsOf = (s: AdventureSave) =>
  KINGDOMS.filter((k) => s.bosses[k.id] && k.tool).map((k) => k.tool!);
/** Champions who've joined your crew: each one beaten in their kingdom's championship. */
export const championsOf = (s: AdventureSave) =>
  KINGDOMS.filter((k) => s.cups[k.id] && k.champion).map((k) => k.champion!);

/** The return objective is open in a kingdom during Act V, until done. */
export const returnOpen = (s: AdventureSave, k: Kingdom) =>
  dragonPhase(s) === "return" && !s.returns[k.id];

/** The ruined version a coin race runs: the ruin if it's built, else the standard course
 * standing in (`standIn`). `exists` says whether a track id is in the game. */
export function coinCourse(c: AdventureCourse, exists: (id: string) => boolean) {
  const ruin = c.ruin && exists(c.ruin) ? c.ruin : undefined;
  return { track: ruin ?? c.track, standIn: !ruin };
}

/**
 * The next scene due, if any: the story's turns in order, each once. The hub plays it
 * before showing anything else.
 */
export function dueScene(s: AdventureSave): string | undefined {
  const due: [string, boolean][] = [["intro", true]];
  for (const k of KINGDOMS) {
    const ph = kingdomPhase(s, k);
    if (ph === "locked") continue;
    due.push([k.scenes.arrive, true]);
    if (s.cups[k.id]) due.push([k.scenes.catastrophe, true]);
    if (piecesOf(s, k) >= k.courses.length) due.push([k.scenes.mapDone, true]);
    if (s.bosses[k.id]) due.push([k.scenes.bossWon, true]);
  }
  const dp = dragonPhase(s);
  if (dp !== "locked") {
    due.push([DRAGON.scenes.arrive, true]);
    if (s.cups.dragon) due.push([DRAGON.scenes.sacrifice, true]);
    if (allReturned(s)) due.push([DRAGON.scenes.resurrection, true]);
    if (allReturned(s)) due.push([DRAGON.scenes.finalArrive, true]);
    if (s.finalCup) due.push([DRAGON.scenes.king, true]);
    if (s.kingLost) due.push([DRAGON.scenes.kingLost, true]);
    if (s.kingWon) due.push([DRAGON.scenes.ending, true]);
  }
  return due.find(([id, ok]) => ok && !s.seen.includes(id))?.[0];
}

export function markSeen(s: AdventureSave, scene: string) {
  if (!s.seen.includes(scene)) s.seen.push(scene);
}

// ---------------------------------------------------------------- results

export interface Outcome {
  /** Did the story move on. */
  progressed: boolean;
  /** One or two lines for the result card. */
  lines: string[];
}

/** A championship (cup) finished: `place` is your place in the cup's final table. */
export function cupFinished(
  s: AdventureSave,
  id: KingdomId | "dragon_final",
  place: number,
): Outcome {
  const won = place === 1;
  if (id === "dragon_final") {
    if (won && !s.finalCup) s.finalCup = true;
    return won
      ? { progressed: true, lines: ["THE LAST CHAMPIONSHIP IS YOURS.", "THE DRAGON KING AWAITS."] }
      : { progressed: false, lines: ["WIN THE CUP TO FACE THE DRAGON KING."] };
  }
  if (won && !s.cups[id]) {
    s.cups[id] = true;
    const champ = kingdomById(id)?.champion;
    return {
      progressed: true,
      lines: ["CHAMPIONS!", ...(champ ? [`${champ.name.toUpperCase()} JOINS YOUR CREW!`] : [])],
    };
  }
  return won
    ? { progressed: false, lines: ["CHAMPIONS AGAIN!"] }
    : { progressed: false, lines: ["WIN THE CUP TO GO ON. TRY AGAIN!"] };
}

/** A treasure map race finished. */
export function coinRaceFinished(
  s: AdventureSave,
  track: string,
  coins: { got: number; total: number },
  position: number | undefined,
): Outcome {
  const all = coins.total > 0 && coins.got >= coins.total;
  const won = position === 1;
  if (all && won) {
    if (s.pieces[track]) return { progressed: false, lines: ["YOU ALREADY HAVE THIS PIECE."] };
    s.pieces[track] = true;
    return { progressed: true, lines: ["A PIECE OF THE MAP!"] };
  }
  if (!all && !won)
    return {
      progressed: false,
      lines: [`COINS ${coins.got}/${coins.total} AND NOT 1ST.`, "GET ALL 4 AND WIN."],
    };
  if (!all)
    return {
      progressed: false,
      lines: [`YOU WON, BUT COINS ${coins.got}/${coins.total}.`, "GET ALL 4 AND WIN."],
    };
  return { progressed: false, lines: ["ALL 4 COINS, BUT YOU HAVE TO WIN TOO."] };
}

export function bossFinished(
  s: AdventureSave,
  id: KingdomId,
  position: number | undefined,
): Outcome {
  const k = kingdomById(id)!;
  if (position !== 1)
    return { progressed: false, lines: [`${k.boss!.name.toUpperCase()} WINS THIS TIME.`] };
  if (s.bosses[id])
    return { progressed: false, lines: [`${k.boss!.name.toUpperCase()} BEATEN AGAIN!`] };
  s.bosses[id] = true;
  const lines = [
    `${k.boss!.name.toUpperCase()} IS BEATEN!`,
    `YOU GET THE ${k.tool!.name.toUpperCase()}.`,
  ];
  return { progressed: true, lines };
}

/** The Dragon King's races: the first is scripted (lost whatever happens), the second
 * is raced as the Chosen One and has to be won. */
export function kingFinished(s: AdventureSave, position: number | undefined): Outcome {
  if (!s.kingLost) {
    s.kingLost = true;
    return { progressed: true, lines: ["NOBODY CAN CATCH THE DRAGON KING..."] };
  }
  if (position !== 1) return { progressed: false, lines: ["THE KING HOLDS ON. TRY AGAIN!"] };
  const first = !s.kingWon;
  s.kingWon = true;
  return { progressed: first, lines: ["THE DRAGON KING IS BEATEN!"] };
}

export function completeReturn(s: AdventureSave, id: KingdomId): Outcome {
  if (s.returns[id]) return { progressed: false, lines: [] };
  s.returns[id] = true;
  return { progressed: true, lines: [] };
}

/** Where the story stands, in a line (the hub's banner). */
export function objective(s: AdventureSave): string {
  for (const k of KINGDOMS) {
    const ph = kingdomPhase(s, k);
    if (ph === "championship") return `${k.name.toUpperCase()}: WIN THE CHAMPIONSHIP`;
    if (ph === "coins") return `${k.name.toUpperCase()}: FIND THE MAP (${piecesOf(s, k)}/4 PIECES)`;
    if (ph === "boss") return `${k.name.toUpperCase()}: RACE ${k.boss!.name.toUpperCase()}`;
  }
  switch (dragonPhase(s)) {
    case "first":
      return "DRAGON KINGDOM: FIND THE CHOSEN ONE";
    case "return": {
      const left = KINGDOMS.filter((k) => !s.returns[k.id]).length;
      return `RETURN HOME: ${left} TASK${left === 1 ? "" : "S"} LEFT IN THE FOUR KINGDOMS`;
    }
    case "final":
      return "DRAGON KINGDOM: THE LAST CHAMPIONSHIP";
    case "king":
      return "DRAGON KINGDOM: RACE THE DRAGON KING";
    case "done":
      return "THE KINGDOMS ARE FREE!";
    default:
      return "";
  }
}
