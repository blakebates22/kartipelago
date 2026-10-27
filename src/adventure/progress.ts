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
  farewellSceneOf,
  kingdomById,
  type AdventureCourse,
  type Kingdom,
  type KingdomId,
} from "./data";
import { regionOfKingdom } from "../overworld/regions";

export interface AdventureSave {
  version: 1;
  /** Championships won: every one of the kingdom's four courses won (Blake, Oct 26: in
   * any order, no Trophy Race cup); the Dragon Kingdom's is its first visit. */
  cups: Partial<Record<KingdomId, boolean>>;
  /** Courses won in Adventure (1st place), by track id: the championships are made of
   * these. */
  wins: Record<string, boolean>;
  /** Map pieces earned, by the standard course's track id. */
  pieces: Record<string, boolean>;
  /** Demi-bosses beaten. */
  bosses: Partial<Record<KingdomId, boolean>>;
  /** The champions' challenges won (the 1v1 race round a kingdom's overworld region). */
  duels: Partial<Record<KingdomId, boolean>>;
  /** Act V: return objectives done. */
  returns: Partial<Record<KingdomId, boolean>>;
  /** The overworld's puzzles solved ("<region>.<puzzle>": src/overworld/puzzles.ts). */
  puzzles: Record<string, boolean>;
  /** The kingdoms' hidden keys found (each opens its mini-game slot one day). */
  keys: Partial<Record<KingdomId, boolean>>;
  /** The regions' secrets found (treasure chests behind later tools' obstacles), by
   * region id. */
  secrets: Record<string, boolean>;
  /** Where you were in the overworld (the region, and the gateway you last came out of):
   * opening the file takes you back there. */
  where?: { region: string; at?: string };
  /** The second visit to the Dragon Kingdom: its ruined courses' cup. */
  finalCup: boolean;
  /** The scripted first race against the King (always lost), then the Chosen One's. */
  kingLost: boolean;
  kingWon: boolean;
  /** Scenes already shown (each plays once; the scene list can replay them). */
  seen: string[];
  /** The file's racer: picked when the file starts; any of your crew can take over from
   * the overworld's pause menu (Blake, Oct 26: never locked to one racer till the end).
   * Missing in files from before files had one: picked on opening. */
  racer?: string;
}

export const newSave = (): AdventureSave => ({
  version: 1,
  cups: {},
  wins: {},
  pieces: {},
  bosses: {},
  duels: {},
  returns: {},
  puzzles: {},
  keys: {},
  secrets: {},
  finalCup: false,
  kingLost: false,
  kingWon: false,
  seen: [],
});

/** Save files: three, like the cartridge games. File 1 keeps the original key, so a save
 * from before files existed opens as file 1. */
export const SLOTS = 3;
const KEY = "kartipelago.adventure.v1";
const slotKey = (slot: number) => (slot === 0 ? KEY : `${KEY}.${slot + 1}`);
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
  s.wins = flags(r.wins);
  s.pieces = flags(r.pieces);
  s.bosses = flags(r.bosses);
  s.duels = flags(r.duels);
  s.returns = flags(r.returns);
  s.puzzles = flags(r.puzzles);
  s.keys = flags(r.keys);
  s.secrets = flags(r.secrets);
  s.finalCup = r.finalCup === true;
  s.kingLost = r.kingLost === true;
  s.kingWon = r.kingWon === true;
  s.seen = Array.isArray(r.seen) ? r.seen.filter((x): x is string => typeof x === "string") : [];
  if (typeof r.racer === "string") s.racer = r.racer;
  const w = r.where as Record<string, unknown> | undefined;
  if (w && typeof w === "object" && typeof w.region === "string")
    s.where = { region: w.region, ...(typeof w.at === "string" ? { at: w.at } : {}) };
  return s;
}

export function loadAdventure(
  storage: Pick<Store, "getItem"> | undefined,
  slot = 0,
): AdventureSave | undefined {
  try {
    const raw = storage?.getItem(slotKey(slot));
    return raw ? sanitizeSave(JSON.parse(raw)) : undefined;
  } catch {
    return undefined;
  }
}

export function saveAdventure(
  s: AdventureSave,
  storage: Pick<Store, "setItem"> | undefined,
  slot = 0,
) {
  try {
    storage?.setItem(slotKey(slot), JSON.stringify(s));
  } catch {
    // Storage full or blocked: progress still counts for this visit.
  }
}

export function eraseAdventure(storage: Pick<Store, "removeItem"> | undefined, slot = 0) {
  try {
    storage?.removeItem(slotKey(slot));
  } catch {
    // Nothing to erase.
  }
}

// ---------------------------------------------------------------- what follows from it

export type KingdomPhase = "locked" | "championship" | "duel" | "coins" | "boss" | "done";
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

/** A kingdom with its overworld region built has the champion's challenge after its
 * championship (the overworld doc): the champion joins you when you win it. */
export const hasDuel = (k: Kingdom) => Boolean(k.champion && regionOfKingdom(k.id));
/** Has the kingdom's champion joined you (their challenge won, or the cup where there's
 * no challenge)? */
export const championWon = (s: AdventureSave, k: Kingdom) =>
  hasDuel(k) ? Boolean(s.duels[k.id]) : Boolean(s.cups[k.id]);

export function kingdomPhase(s: AdventureSave, k: Kingdom): KingdomPhase {
  if (!unlocked(s, k.id)) return "locked";
  if (s.bosses[k.id]) return "done";
  if (!s.cups[k.id]) return "championship";
  if (hasDuel(k) && !s.duels[k.id]) return "duel";
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
  KINGDOMS.filter((k) => k.champion && championWon(s, k)).map((k) => k.champion!);

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
  // A kingdom's welcome waits until you've driven there (Blake, Oct 26: no hopping to the
  // next world from a map): its region is where you are (the first is where you start).
  const here = (id: KingdomId | "dragon", first: boolean) => {
    const r = regionOfKingdom(id);
    return !r || first || s.where?.region === r.id;
  };
  for (const k of KINGDOMS) {
    const ph = kingdomPhase(s, k);
    if (ph === "locked") continue;
    due.push([k.scenes.arrive, here(k.id, k === KINGDOMS[0])]);
    // (The dragons strike at the champion's welcome: after the challenge, where there is one.)
    if (championWon(s, k)) due.push([k.scenes.catastrophe, true]);
    if (piecesOf(s, k) >= k.courses.length) due.push([k.scenes.mapDone, true]);
    if (s.bosses[k.id]) due.push([k.scenes.bossWon, true]);
    // (The farewell, on the way out: not for a file already in the next world.)
    const next = k.next === "dragon" ? DRAGON : KINGDOMS.find((x) => x.id === k.next);
    if (s.bosses[k.id] && k.champion && next && !s.seen.includes(next.scenes.arrive))
      due.push([farewellSceneOf(k.id), true]);
  }
  const dp = dragonPhase(s);
  if (dp !== "locked") {
    due.push([DRAGON.scenes.arrive, here("dragon", false)]);
    if (s.cups.dragon) due.push([DRAGON.scenes.sacrifice, true]);
    if (allReturned(s)) due.push([DRAGON.scenes.resurrection, true]);
    if (allReturned(s)) due.push([DRAGON.scenes.finalArrive, here("dragon", false)]);
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

/** The tracks of a kingdom's championship (the Dragon Kingdom's last one: its ruins). */
export function championshipTracks(
  id: KingdomId | "dragon_final",
  exists: (id: string) => boolean = () => true,
): string[] {
  if (id === "dragon_final") return DRAGON.courses.map((c) => coinCourse(c, exists).track);
  const courses = id === "dragon" ? DRAGON.courses : (kingdomById(id)?.courses ?? []);
  return courses.map((c) => c.track);
}

/** How many of a championship's courses are won. */
export const winsOf = (s: AdventureSave, id: KingdomId | "dragon_final") =>
  championshipTracks(id).filter((t) => s.wins[t]).length;

/** One of a championship's courses raced (Blake, Oct 26: win all four, in any order, and
 * the championship is yours): `position` is where you finished. */
export function raceFinished(
  s: AdventureSave,
  id: KingdomId | "dragon_final",
  track: string,
  position: number | undefined,
): Outcome {
  const tracks = championshipTracks(id);
  if (position !== 1) return { progressed: false, lines: ["WIN IT TO COUNT IT. TRY AGAIN!"] };
  if (s.wins[track]) return { progressed: false, lines: ["WON AGAIN!"] };
  s.wins[track] = true;
  const n = tracks.filter((t) => s.wins[t]).length;
  if (n < tracks.length)
    return {
      progressed: true,
      lines: [`${n} OF ${tracks.length} COURSES WON!`, "WIN THE REST, IN ANY ORDER."],
    };
  const out = cupFinished(s, id, 1);
  return { ...out, lines: ["ALL FOUR COURSES WON!", ...out.lines.slice(1)] };
}

/** A championship won (all its courses: raceFinished), or not: `place` 1 is won. */
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
    const k = kingdomById(id);
    const champ = k?.champion;
    if (k && hasDuel(k))
      return {
        progressed: true,
        lines: ["CHAMPIONS!", `${champ!.name.toUpperCase()} CHALLENGES YOU: 1 ON 1!`],
      };
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
      lines: [`FRAGMENTS ${coins.got}/${coins.total} AND NOT 1ST.`, "GET ALL 4 AND WIN."],
    };
  if (!all)
    return {
      progressed: false,
      lines: [`YOU WON, BUT FRAGMENTS ${coins.got}/${coins.total}.`, "GET ALL 4 AND WIN."],
    };
  return { progressed: false, lines: ["ALL 4 FRAGMENTS, BUT YOU HAVE TO WIN TOO."] };
}

/** The champion's challenge finished (the 1v1 round the kingdom's region). */
export function duelFinished(
  s: AdventureSave,
  id: KingdomId,
  position: number | undefined,
): Outcome {
  const champ = kingdomById(id)!.champion!.name.toUpperCase();
  if (position !== 1) return { progressed: false, lines: [`${champ} WINS THIS TIME. TRY AGAIN!`] };
  if (s.duels[id]) return { progressed: false, lines: [`${champ} BEATEN AGAIN!`] };
  s.duels[id] = true;
  return { progressed: true, lines: [`${champ} IS BEATEN!`, `${champ} JOINS YOUR CREW!`] };
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
    if (ph === "championship")
      return `${k.name.toUpperCase()}: WIN ITS 4 COURSES (${winsOf(s, k.id)}/4 WON)`;
    if (ph === "duel")
      return `${k.name.toUpperCase()}: RACE ${k.champion!.name.toUpperCase()}, 1 ON 1`;
    if (ph === "coins") return `${k.name.toUpperCase()}: FIND THE MAP (${piecesOf(s, k)}/4 PIECES)`;
    if (ph === "boss") return `${k.name.toUpperCase()}: RACE ${k.boss!.name.toUpperCase()}`;
  }
  switch (dragonPhase(s)) {
    case "first":
      return `DRAGON KINGDOM: WIN ITS 4 COURSES (${winsOf(s, "dragon")}/4 WON)`;
    case "return": {
      const left = KINGDOMS.filter((k) => !s.returns[k.id]).length;
      return `RETURN HOME: ${left} TASK${left === 1 ? "" : "S"} LEFT IN THE FOUR KINGDOMS`;
    }
    case "final":
      return `DRAGON KINGDOM: WIN ITS 4 RUINED COURSES (${winsOf(s, "dragon_final")}/4 WON)`;
    case "king":
      return "DRAGON KINGDOM: RACE THE DRAGON KING";
    case "done":
      return "THE KINGDOMS ARE FREE!";
    default:
      return "";
  }
}
