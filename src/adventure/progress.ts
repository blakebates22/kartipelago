/**
 * Adventure progress: what the player has done (a small saved record) and everything
 * worked out from it (each kingdom's phase on the way out and on the way back, how each
 * region looks now, the next scene due). Plain data and functions, no rendering; the
 * rules read the story data (data.ts). The approved story: claude/kartipelago-story.md.
 *
 * The way out (Acts I-III): a kingdom's four courses (the festival, then the gladiator
 * games), its champion 1 on 1 (they join your crew), its underground mini-game as that
 * champion (the smugglers' key: the tunnel out). Then the King's Games and the King.
 * The way back (Acts IV-V): each ruined kingdom's four ruined courses, each won with all
 * its shard pieces for a light shard; four shards make the new Pact Stone and force the
 * dragon to race; it yields and the kingdom is restored. Then the Dragon Kingdom's four
 * shards, the Heart Stone, and the King's last race.
 *
 * The record only ever gains things, so replaying a race never undoes the story, and a
 * light shard is won only by a race that took all its shard pieces AND was won.
 */
import {
  DRAGON,
  END_CREDITS,
  FAKE_CREDITS,
  KINGDOMS,
  RAGE,
  STORY_ORDER,
  kingdomById,
  prevOf,
  sceneOf,
  type AdventureCourse,
  type Kingdom,
  type KingdomId,
} from "./data";
import type { RacerId } from "../render/racers/designs";
import { regionOfKingdom } from "../overworld/regions";

export interface AdventureSave {
  version: 2;
  /** Standard courses won in Adventure (1st place), by track id: the festival, the
   * gladiator games and the King's Games are made of these (any order). */
  wins: Record<string, boolean>;
  /** The champions beaten 1 on 1 (they've joined your crew). */
  duels: Partial<Record<KingdomId, boolean>>;
  /** The underground games won: the smugglers' key, the tunnel out of the kingdom. */
  games: Partial<Record<KingdomId, boolean>>;
  /** The race for the lands: the King beaten the first time (the Pact shatters). */
  kingRace: boolean;
  /** Light shards won, by the standard course's track id (raced on its ruin). */
  shards: Record<string, boolean>;
  /** Dragons beaten under the new Pact (each yields its kingdom). */
  bosses: Partial<Record<KingdomId, boolean>>;
  /** The King's last race, won. */
  kingWon: boolean;
  /** Scenes already shown (each plays once; the scene list can replay them). */
  seen: string[];
  /** The file's racer: picked when the file starts, "you" for the whole story. */
  racer?: string;
  /** Who's driving now: the file's racer or one of the crew who joined (Your Crew). */
  driver?: string;
  /** Where you were in the overworld (the region, and the mark you last came out of). */
  where?: { region: string; at?: string };
}

export const newSave = (): AdventureSave => ({
  version: 2,
  wins: {},
  duels: {},
  games: {},
  kingRace: false,
  shards: {},
  bosses: {},
  kingWon: false,
  seen: [],
});

/** Save files: three, like the cartridge games. A new key for the new story (the old
 * story's files stay where they were, for the adventure-v1 backup). */
export const SLOTS = 3;
const KEY = "kartipelago.adventure.v2";
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
  s.wins = flags(r.wins);
  s.duels = flags(r.duels);
  s.games = flags(r.games);
  s.shards = flags(r.shards);
  s.bosses = flags(r.bosses);
  s.kingRace = r.kingRace === true;
  s.kingWon = r.kingWon === true;
  s.seen = Array.isArray(r.seen) ? r.seen.filter((x): x is string => typeof x === "string") : [];
  if (typeof r.racer === "string") s.racer = r.racer;
  if (typeof r.driver === "string") s.driver = r.driver;
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

/** A kingdom's step. The way out: locked (not reached), games (its four courses), duel
 * (its champion), underground (the mini-game), escaped (the key won). The way back:
 * waiting (in ruins, not reached yet), shards (its four ruined courses), boss (the new
 * stone's forced race), restored. */
export type KingdomPhase =
  | "locked"
  | "games"
  | "duel"
  | "underground"
  | "escaped"
  | "waiting"
  | "shards"
  | "boss"
  | "restored";
/** The Dragon Kingdom's step: locked, games (the King's Games), king (the race for the
 * lands); after the Pact shatters: waiting (in ruins), shards, final (the King under the
 * new Pact), done. */
export type DragonPhase = "locked" | "games" | "king" | "waiting" | "shards" | "final" | "done";

export const coursesOf = (id: KingdomId): AdventureCourse[] =>
  id === "dragon" ? DRAGON.courses : (kingdomById(id)?.courses ?? []);
/** How many of a kingdom's four standard courses are won (the way out). */
export const winsOf = (s: AdventureSave, id: KingdomId) =>
  coursesOf(id).filter((c) => s.wins[c.track]).length;
/** How many of its light shards are won (the way back). */
export const shardsOf = (s: AdventureSave, id: KingdomId) =>
  coursesOf(id).filter((c) => s.shards[c.track]).length;

/** Reached on the way out: the valley always; each next one once the kingdom before it
 * is escaped (its smugglers' key won). */
export function reachedOut(s: AdventureSave, id: KingdomId): boolean {
  const prev = prevOf(id);
  return !prev || Boolean(s.games[prev]);
}
/** Reached on the way back: the valley once the Pact has shattered; each next one once
 * the dragon before it has yielded. */
export function reachedBack(s: AdventureSave, id: KingdomId): boolean {
  if (!s.kingRace) return false;
  const prev = prevOf(id);
  return !prev || Boolean(s.bosses[prev]);
}

export function kingdomPhase(s: AdventureSave, k: Kingdom): KingdomPhase {
  if (!s.kingRace) {
    if (!reachedOut(s, k.id)) return "locked";
    if (winsOf(s, k.id) < k.courses.length) return "games";
    if (!s.duels[k.id]) return "duel";
    if (!s.games[k.id]) return "underground";
    return "escaped";
  }
  if (s.bosses[k.id]) return "restored";
  if (!reachedBack(s, k.id)) return "waiting";
  if (shardsOf(s, k.id) < k.courses.length) return "shards";
  return "boss";
}

export function dragonPhase(s: AdventureSave): DragonPhase {
  if (!s.kingRace) {
    if (!reachedOut(s, "dragon")) return "locked";
    return winsOf(s, "dragon") < DRAGON.courses.length ? "games" : "king";
  }
  if (s.kingWon) return "done";
  if (!reachedBack(s, "dragon")) return "waiting";
  return shardsOf(s, "dragon") < DRAGON.courses.length ? "shards" : "final";
}

/** How a kingdom's region looks now: free (the valley before Cinderjaw comes; the Dragon
 * Kingdom before the Pact shatters), conquered (a dragon rules it), ruined (after the
 * Rage; the Dragon Kingdom after the blast), restored (its dragon yielded). */
export type RegionLook = "free" | "conquered" | "ruined" | "restored";
export function regionLook(s: AdventureSave, id: KingdomId): RegionLook {
  if (id === "dragon") return !s.kingRace ? "free" : s.kingWon ? "restored" : "ruined";
  if (s.kingRace) return s.bosses[id] ? "restored" : "ruined";
  return id === "valley" && !s.seen.includes(sceneOf("valley", "hundredth")) ? "free" : "conquered";
}

/** Your crew: the champions who've joined you (beaten 1 on 1), as their looks. A file
 * raced as a champion: that champion's cousin joined in their place (you're already
 * them, so they're not listed twice). */
export const crewOf = (s: AdventureSave): RacerId[] =>
  KINGDOMS.filter((k) => s.duels[k.id] && k.champion.look !== s.racer).map((k) => k.champion.look);
/** Who can drive: your own racer, and the crew. */
export const driversOf = (s: AdventureSave): RacerId[] => [
  ...(s.racer ? [s.racer as RacerId] : []),
  ...crewOf(s),
];

/** The ruined version a shard race runs: the ruin if it's built, else the standard
 * course standing in (`standIn`). `exists` says whether a track id is in the game. */
export function shardCourse(c: AdventureCourse, exists: (id: string) => boolean) {
  const ruin = c.ruin && exists(c.ruin) ? c.ruin : undefined;
  return { track: ruin ?? c.track, standIn: !ruin };
}

// ---------------------------------------------------------------- the scenes

/** The scenes that start a race at once (staged where you are, then the race): the
 * champion's challenge, the race for the lands, a new stone's forced race, the King's
 * last. The overworld plays them (screens/overworld.ts raceTrigger), not dueScene. */
export const challengeScene = (k: KingdomId) => sceneOf(k, "challenge");
export const BEFORE_KING = "dragon_before_king";
export const newStoneScene = (k: KingdomId) => sceneOf(k, "new_stone");
export const HEART = "dragon_heart";
export const UNDERGROUND = (k: KingdomId) => sceneOf(k, "underground");

/** The story's scenes in order, each with whether it's due yet (all but the race
 * triggers and the underground's welcome, which play where they happen). `here`: is
 * the file in that kingdom's region (a welcome waits until you've driven there). */
export function storyScenes(
  s: AdventureSave,
  here: (id: KingdomId) => boolean = () => true,
): [string, boolean][] {
  const due: [string, boolean][] = [];
  // Act I: the valley.
  due.push([sceneOf("valley", "festival"), true]);
  if (s.duels.valley)
    due.push(
      [sceneOf("valley", "prize"), true],
      [sceneOf("valley", "hundredth"), true],
      [sceneOf("valley", "way_out"), true],
    );
  if (s.games.valley)
    due.push([sceneOf("valley", "key"), true], [sceneOf("valley", "stone"), true]);
  // Act II: the conquered kingdoms.
  for (const k of KINGDOMS.slice(1)) {
    if (!reachedOut(s, k.id)) break;
    due.push([sceneOf(k.id, "caught"), here(k.id)]);
    if (winsOf(s, k.id) >= 2) due.push([sceneOf(k.id, "stands"), true]);
    if (s.duels[k.id]) due.push([sceneOf(k.id, "prize"), true]);
    if (s.games[k.id]) due.push([sceneOf(k.id, "key"), true], [sceneOf(k.id, "stone"), true]);
  }
  // Act III: the Dragon Kingdom; the Pact shatters, the fake ending, the Rage.
  if (reachedOut(s, "dragon")) due.push(["dragon_challenger", here("dragon")]);
  if (s.kingRace)
    due.push(
      ["dragon_return", true],
      ["dragon_lumen", true],
      ["dragon_horn", true],
      [FAKE_CREDITS, true],
      ...RAGE.map((r): [string, boolean] => [r, true]),
    );
  // Act IV: the ruins.
  if (s.kingRace) {
    due.push([sceneOf("valley", "rescue"), here("valley")]);
    for (const k of KINGDOMS) if (s.bosses[k.id]) due.push([sceneOf(k.id, "yield"), true]);
  }
  // Act V.
  if (s.bosses.beach) due.push(["dragon_court", here("dragon")]);
  if (s.kingWon) due.push(["dragon_lumen_returns", true], ["ending", true], [END_CREDITS, true]);
  return due;
}

/** The next scene due, if any (each once, in story order). */
export function dueScene(
  s: AdventureSave,
  here: (id: KingdomId) => boolean = () => true,
): string | undefined {
  return storyScenes(s, here).find(([id, ok]) => ok && !s.seen.includes(id))?.[0];
}

/**
 * Where a scene puts you when it ends (the file's `where`, for the overworld to load):
 * a kingdom's stone (the way out) through the smugglers' tunnel into the journey on;
 * the Rage into the ruined valley; a dragon's Yield in front of the cave (the tunnel on)
 * in its restored kingdom; the credits home to the valley.
 */
export function afterScene(s: AdventureSave, scene: string) {
  for (const k of KINGDOMS) {
    if (scene === sceneOf(k.id, "stone")) s.where = { region: k.tunnel, at: "start" };
    if (scene === sceneOf(k.id, "yield")) {
      const r = regionOfKingdom(k.id);
      if (r) s.where = { region: r.id, at: "cave:front" };
    }
  }
  if (scene === RAGE[RAGE.length - 1]) s.where = { region: "dinosaur_valley" };
  if (scene === END_CREDITS) s.where = { region: "dinosaur_valley" };
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

/** One of a kingdom's four standard courses raced (the festival, the gladiator games,
 * the King's Games: win all four, in any order). `position` is where you finished. */
export function raceFinished(
  s: AdventureSave,
  id: KingdomId,
  track: string,
  position: number | undefined,
): Outcome {
  if (position !== 1) return { progressed: false, lines: ["WIN IT TO COUNT IT. TRY AGAIN!"] };
  if (s.wins[track]) return { progressed: false, lines: ["WON AGAIN!"] };
  s.wins[track] = true;
  const n = winsOf(s, id);
  const all = coursesOf(id).length;
  if (n < all)
    return { progressed: true, lines: [`${n} OF ${all} COURSES WON!`, "WIN THE REST, ANY ORDER."] };
  return {
    progressed: true,
    lines: [
      "ALL FOUR COURSES WON!",
      id === "dragon" ? "THE KING IS WAITING." : "SOMEONE'S COMING...",
    ],
  };
}

/** The champion's challenge finished (1 on 1 round the kingdom's region). */
export function duelFinished(
  s: AdventureSave,
  id: KingdomId,
  position: number | undefined,
  cousin = false,
): Outcome {
  const c = kingdomById(id)!.champion.name.toUpperCase();
  const champ = cousin ? `${c}'S COUSIN` : c;
  if (position !== 1) return { progressed: false, lines: [`${champ} WINS THIS TIME. TRY AGAIN!`] };
  if (s.duels[id]) return { progressed: false, lines: [`${champ} BEATEN AGAIN!`] };
  s.duels[id] = true;
  return { progressed: true, lines: [`${champ} IS BEATEN!`] };
}

/** The underground games' mini-game finished: won, the smugglers' key. */
export function gamesFinished(s: AdventureSave, id: KingdomId, won: boolean): Outcome {
  if (!won) return { progressed: false, lines: ["NO KEY FOR LOSERS. TRY AGAIN!"] };
  if (s.games[id]) return { progressed: false, lines: ["WON AGAIN!"] };
  s.games[id] = true;
  return { progressed: true, lines: ["THE SMUGGLERS' KEY!"] };
}

/** The race for the lands (the King, the first time). */
export function kingRaceFinished(s: AdventureSave, position: number | undefined): Outcome {
  if (position !== 1) return { progressed: false, lines: ["THE KING WINS THIS TIME. TRY AGAIN!"] };
  if (s.kingRace) return { progressed: false, lines: ["THE KING IS BEATEN AGAIN!"] };
  s.kingRace = true;
  return { progressed: true, lines: ["THE KING IS BEATEN!", "THE LANDS ARE YOURS..."] };
}

/** A shard race on a ruined course: all its shard pieces AND 1st, its light shard. */
export function shardRaceFinished(
  s: AdventureSave,
  track: string,
  pieces: { got: number; total: number },
  position: number | undefined,
): Outcome {
  const all = pieces.total > 0 && pieces.got >= pieces.total;
  const won = position === 1;
  if (all && won) {
    if (s.shards[track]) return { progressed: false, lines: ["YOU ALREADY HAVE THIS SHARD."] };
    s.shards[track] = true;
    return { progressed: true, lines: ["A LIGHT SHARD!"] };
  }
  if (!all && !won)
    return {
      progressed: false,
      lines: [`SHARD PIECES ${pieces.got}/${pieces.total} AND NOT 1ST.`, "GET THEM ALL AND WIN."],
    };
  if (!all)
    return {
      progressed: false,
      lines: [`YOU WON, BUT SHARD PIECES ${pieces.got}/${pieces.total}.`, "GET THEM ALL AND WIN."],
    };
  return { progressed: false, lines: ["EVERY PIECE, BUT YOU HAVE TO WIN TOO."] };
}

/** A dragon's race under its new Pact Stone. */
export function bossFinished(s: AdventureSave, id: KingdomId, position: number | undefined) {
  const name = kingdomById(id)!.boss.name.toUpperCase();
  if (position !== 1) return { progressed: false, lines: [`${name} WINS THIS TIME. TRY AGAIN!`] };
  if (s.bosses[id]) return { progressed: false, lines: [`${name} BEATEN AGAIN!`] };
  s.bosses[id] = true;
  return { progressed: true, lines: [`${name} IS BEATEN!`, "BY THE PACT, HE MUST YIELD."] };
}

/** The King's last race, under the whole new Pact. */
export function finalFinished(s: AdventureSave, position: number | undefined): Outcome {
  if (position !== 1) return { progressed: false, lines: ["THE KING HOLDS ON. TRY AGAIN!"] };
  const first = !s.kingWon;
  s.kingWon = true;
  return { progressed: first, lines: ["THE DRAGON KING IS BEATEN, FAIRLY!"] };
}

/** Where the story stands, in a line (the overworld's goal under the region's name, the
 * file chooser). */
export function objective(s: AdventureSave): string {
  for (const k of KINGDOMS) {
    const ph = kingdomPhase(s, k);
    const name = k.name.toUpperCase();
    const champ = k.champion.name.toUpperCase();
    if (ph === "games") return `${name}: WIN ITS 4 COURSES (${winsOf(s, k.id)}/4 WON)`;
    if (ph === "duel") return `${name}: BEAT ${champ}, 1 ON 1`;
    if (ph === "underground") return `${name}: THE UNDERGROUND GAMES (${k.cave})`;
    if (ph === "shards") return `${name}: WIN ITS LIGHT SHARDS (${shardsOf(s, k.id)}/4)`;
    if (ph === "boss") return `${name}: RACE ${k.boss.name.toUpperCase()}`;
  }
  const kd = KINGDOMS.find((k) => kingdomPhase(s, k) === "escaped");
  switch (dragonPhase(s)) {
    case "locked":
      return kd ? `ON THROUGH THE SMUGGLERS' TUNNEL` : "";
    case "games":
      return `DRAGON KINGDOM: THE KING'S GAMES (${winsOf(s, "dragon")}/4 WON)`;
    case "king":
      return "DRAGON KINGDOM: RACE THE KING FOR THE LANDS";
    case "shards":
      return `DRAGON KINGDOM: THE LAST LIGHT SHARDS (${shardsOf(s, "dragon")}/4)`;
    case "final":
      return "DRAGON KINGDOM: RACE THE KING, UNDER THE NEW PACT";
    case "done":
      return "THE KINGDOMS ARE RESTORED!";
    default:
      return KINGDOMS.some((k) => kingdomPhase(s, k) === "restored")
        ? "ON THROUGH THE SMUGGLERS' TUNNEL"
        : "";
  }
}

/** The kingdom the story is in now (where the next thing to do is). */
export function storyKingdom(s: AdventureSave): KingdomId {
  for (const id of STORY_ORDER) {
    if (id === "dragon") return "dragon";
    const ph = kingdomPhase(s, kingdomById(id)!);
    if (ph !== "escaped" && ph !== "restored" && ph !== "locked" && ph !== "waiting") return id;
  }
  return "dragon";
}
