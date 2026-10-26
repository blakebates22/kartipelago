/**
 * Adventure mode's story, as data: the five kingdoms in story order, each one's courses
 * and their ruined versions, its dragon, the tool and the champion it gives, where its
 * map leads, its return objective and its (still empty) mini-game slot; and the Dragon
 * Kingdom's own steps. The progress rules (progress.ts) and the screens read only this,
 * so the story changes here, not in code.
 *
 * Everything with a name here is a PLACEHOLDER from the story doc ("Kartipelago Adventure
 * Mode: Story & Progression"): names, lines and objectives are meant to be replaced.
 */
import type { CoinSpot } from "../game/coins";
import type { RacerId } from "../render/racers/designs";

export type KingdomId = "valley" | "snow" | "desert" | "beach" | "dragon";

export interface AdventureCourse {
  /** The standard course (track id). */
  track: string;
  /** Its ruined version (track id), once built. Until then the standard course stands in. */
  ruin?: string;
  /** Map fragment spots on the ruin (default: four spread round the lap). */
  coins?: CoinSpot[];
}

export interface Kingdom {
  id: KingdomId;
  name: string;
  /** The game world its courses come from (game/worlds.ts). */
  worldId: string;
  courses: AdventureCourse[];
  /** The demi-boss race: the dragon, its course, and its edge (a top-speed multiplier). */
  boss?: { name: string; track: string; speed: number };
  /** What beating the dragon gives (placeholder names). */
  tool?: { id: string; name: string };
  /** The kingdom's champion: beaten in its championship, they join your crew and become
   * a racer you can pick everywhere (app/unlocks.ts). */
  champion?: { name: string; look: RacerId };
  /** The kingdom the finished map leads to. */
  next?: KingdomId;
  /** Act V: one placeholder task per kingdom (talk to someone, use the tool). */
  returnTask?: { who: string; label: string; scene: string };
  /** Room for a mini-game (open, not committed): null until one exists. */
  minigame: null;
  /** Scenes (scenes.ts) at each turn of the kingdom's story. */
  scenes: { arrive: string; catastrophe: string; mapDone: string; boss: string; bossWon: string };
}

export const KINGDOMS: Kingdom[] = [
  {
    id: "valley",
    name: "Dinosaur Valley",
    worldId: "prehistoric",
    courses: [
      { track: "riverbend_palms", ruin: "riverbend_palms_ruin" },
      { track: "cascade_caverns", ruin: "cascade_caverns_ruin" },
      { track: "bonebog_pyramid", ruin: "bonebog_pyramid_ruin" },
      { track: "ember_peak", ruin: "ember_peak_ruin" },
    ],
    boss: { name: "Cinderjaw", track: "boss_prehistoric", speed: 1.0 },
    tool: { id: "valley_tool", name: "Valley Tool" },
    champion: { name: "Rex", look: "rex" },
    next: "snow",
    returnTask: { who: "Elder Mossback", label: "TALK TO THE ELDER", scene: "valley_return" },
    minigame: null,
    scenes: {
      arrive: "valley_arrive",
      catastrophe: "valley_catastrophe",
      mapDone: "valley_map",
      boss: "valley_boss",
      bossWon: "valley_boss_won",
    },
  },
  {
    id: "snow",
    name: "Snow Kingdom",
    worldId: "frostveil",
    courses: [
      { track: "frostveil_citadel", ruin: "frostveil_citadel_ruin" },
      { track: "snowy_summit", ruin: "snowy_summit_ruin" },
      { track: "hearthglow_hollow", ruin: "hearthglow_hollow_ruin" },
      { track: "aurora_rift" },
    ],
    boss: { name: "Rimefang", track: "boss_snowy", speed: 1.0 },
    tool: { id: "snow_tool", name: "Snow Tool" },
    champion: { name: "Brachio", look: "brachio" },
    next: "desert",
    returnTask: { who: "Brachio", label: "HELP BRACHIO", scene: "snow_return" },
    minigame: null,
    scenes: {
      arrive: "snow_arrive",
      catastrophe: "snow_catastrophe",
      mapDone: "snow_map",
      boss: "snow_boss",
      bossWon: "snow_boss_won",
    },
  },
  {
    id: "desert",
    name: "Desert Kingdom",
    worldId: "desert",
    courses: [
      { track: "canyon_dash" },
      { track: "oasis_haven" },
      { track: "dry_gulch" },
      { track: "impact_depths" },
    ],
    boss: { name: "Scorchwind", track: "boss_desert", speed: 1.0 },
    tool: { id: "desert_tool", name: "Desert Tool" },
    champion: { name: "Stego", look: "stego" },
    next: "beach",
    returnTask: { who: "Stego", label: "HELP STEGO", scene: "desert_return" },
    minigame: null,
    scenes: {
      arrive: "desert_arrive",
      catastrophe: "desert_catastrophe",
      mapDone: "desert_map",
      boss: "desert_boss",
      bossWon: "desert_boss_won",
    },
  },
  {
    id: "beach",
    name: "Beach Kingdom",
    worldId: "beach",
    courses: [
      { track: "coral_cove" },
      { track: "shipwreck_bay" },
      { track: "volcano_isle" },
      { track: "splash_lagoon" },
    ],
    boss: { name: "Tidewyrm", track: "boss_tropic", speed: 1.0 },
    tool: { id: "beach_tool", name: "Beach Tool" },
    champion: { name: "Raptor", look: "raptor" },
    next: "dragon",
    returnTask: { who: "Raptor", label: "HELP RAPTOR", scene: "beach_return" },
    minigame: null,
    scenes: {
      arrive: "beach_arrive",
      catastrophe: "beach_catastrophe",
      mapDone: "beach_map",
      boss: "beach_boss",
      bossWon: "beach_boss_won",
    },
  },
];

/** The Dragon Kingdom: two visits with the journey home between, and the Dragon King. */
export const DRAGON = {
  id: "dragon" as const,
  name: "Dragon Kingdom",
  worldId: "dragon",
  courses: [
    { track: "dragon_isles" },
    { track: "dragon_canyon" },
    { track: "snow_dragon_pass" },
    { track: "celestial_dragon_festival" },
  ] as AdventureCourse[],
  /** The final race. In the first, scripted race his advantage can't be beaten
   * (`speed`); as the Chosen One, the placeholder ability cancels it (`chosenSpeed`). */
  king: { name: "King Pyrrhax", track: "boss_dragon", speed: 1.45, chosenSpeed: 1.0 },
  chosen: { name: "Aurin", ability: "AURIN'S LIGHT" },
  minigame: null,
  scenes: {
    arrive: "dragon_arrive",
    sacrifice: "dragon_sacrifice",
    resurrection: "resurrection",
    finalArrive: "dragon_final_arrive",
    king: "king_intro",
    kingLost: "king_lost",
    ending: "ending",
  },
};

/** Every kingdom in story order, the Dragon Kingdom last. */
export const STORY_ORDER: KingdomId[] = ["valley", "snow", "desert", "beach", "dragon"];

export const kingdomById = (id: KingdomId) => KINGDOMS.find((k) => k.id === id);
