/**
 * Adventure mode's story, as data (the approved story, Blake, Oct 27: "The Shattered
 * Pact", claude/kartipelago-story.md in the project): the four kingdoms in story order,
 * each one's courses (raced standard on the way out, ruined on the way back), its dragon,
 * its champion, its underground mini-game; and the Dragon Kingdom. The progress rules
 * (progress.ts) and the screens read only this.
 *
 * The journey runs twice: out through the four conquered kingdoms to the Dragon King
 * (the gladiator games, the champions, the underground games and the smugglers' keys),
 * then back through them in ruins (the light shards, the new Pact Stones, the dragons'
 * boss races and the Yield), and to the King once more.
 */
import type { CoinSpot } from "../game/coins";
import type { MiniGameId } from "../game/minigames";
import type { RacerId } from "../render/racers/designs";

export type KingdomId = "valley" | "snow" | "desert" | "beach" | "dragon";

export interface AdventureCourse {
  /** The standard course (track id): the festival, the gladiator games, the King's Games. */
  track: string;
  /** Its ruined version (track id): its light shard is won on it. */
  ruin?: string;
  /** Shard piece spots on the ruin (default: four spread round the lap). */
  coins?: CoinSpot[];
}

export interface Kingdom {
  id: Exclude<KingdomId, "dragon">;
  name: string;
  /** The game world its courses come from (game/worlds.ts). */
  worldId: string;
  courses: AdventureCourse[];
  /** The demi-boss: its race on the way back (forced by the new Pact Stone). */
  boss: { name: string; track: string; speed: number };
  /** The kingdom's champion: beaten 1 on 1 after its four courses, they join your crew. */
  champion: { name: string; look: RacerId };
  /** The smugglers' underground games: the mini-game, and the cave's name. */
  minigame: MiniGameId;
  cave: string;
  /** The kingdom the smugglers' tunnel leads on to, and the journey region it comes out in. */
  next: KingdomId;
  tunnel: string;
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
    champion: { name: "Rex", look: "rex" },
    minigame: "eggs",
    cave: "THE LOOKOUT CAVE",
    next: "snow",
    tunnel: "journey_gorge",
  },
  {
    id: "snow",
    name: "Snow Kingdom",
    worldId: "frostveil",
    courses: [
      { track: "frostveil_citadel", ruin: "frostveil_citadel_ruin" },
      { track: "snowy_summit", ruin: "snowy_summit_ruin" },
      { track: "hearthglow_hollow", ruin: "hearthglow_hollow_ruin" },
      { track: "aurora_rift", ruin: "aurora_rift_ruin" },
    ],
    boss: { name: "Rimefang", track: "boss_snowy", speed: 1.0 },
    champion: { name: "Brachio", look: "brachio" },
    minigame: "crown",
    cave: "THE ICE CAVE",
    next: "desert",
    tunnel: "journey_pass",
  },
  {
    id: "desert",
    name: "Desert World",
    worldId: "desert",
    courses: [
      { track: "canyon_dash", ruin: "canyon_dash_ruin" },
      { track: "oasis_haven", ruin: "oasis_haven_ruin" },
      { track: "dry_gulch", ruin: "dry_gulch_ruin" },
      { track: "impact_depths", ruin: "impact_depths_ruin" },
    ],
    boss: { name: "Scorchwind", track: "boss_desert", speed: 1.0 },
    champion: { name: "Stego", look: "stego" },
    minigame: "stars",
    cave: "THE DRIFT CAVE",
    next: "beach",
    tunnel: "journey_dust",
  },
  {
    id: "beach",
    name: "Tropic Isles",
    worldId: "beach",
    courses: [
      { track: "coral_cove", ruin: "coral_cove_ruin" },
      { track: "shipwreck_bay", ruin: "shipwreck_bay_ruin" },
      { track: "volcano_isle", ruin: "volcano_isle_ruin" },
      { track: "splash_lagoon", ruin: "splash_lagoon_ruin" },
    ],
    boss: { name: "Tidewyrm", track: "boss_tropic", speed: 1.0 },
    champion: { name: "Raptor", look: "raptor" },
    minigame: "balloons",
    cave: "THE SEA CAVE",
    next: "dragon",
    tunnel: "journey_cause",
  },
];

/** The Dragon Kingdom: the King's Games and the race for the lands; in ruins after the
 * Pact shatters, its last four shards; then the King once more, under the new Pact. */
export const DRAGON = {
  id: "dragon" as const,
  name: "Dragon Kingdom",
  worldId: "dragon",
  courses: [
    { track: "dragon_isles", ruin: "dragon_isles_ruin" },
    { track: "dragon_canyon", ruin: "dragon_canyon_ruin" },
    { track: "snow_dragon_pass", ruin: "snow_dragon_pass_ruin" },
    { track: "celestial_dragon_festival", ruin: "celestial_dragon_festival_ruin" },
  ] as AdventureCourse[],
  /** Both races are raced to be won: the first for the lands (his wall of fire), the last
   * under the new Pact (his fireballs and the gauntlet: the course's other mechanic). */
  king: { name: "King Pyrrhax", track: "boss_dragon", speed: 1.0 },
};

/** Every kingdom in story order, the Dragon Kingdom last. */
export const STORY_ORDER: KingdomId[] = ["valley", "snow", "desert", "beach", "dragon"];

export const kingdomById = (id: KingdomId | string) => KINGDOMS.find((k) => k.id === id);
export const nameOf = (id: KingdomId) => (id === "dragon" ? DRAGON.name : kingdomById(id)!.name);
/** The kingdom before this one in the story (the valley: none). */
export const prevOf = (id: KingdomId): KingdomId | undefined =>
  STORY_ORDER[STORY_ORDER.indexOf(id) - 1];

/** A kingdom's scene for a step of its story (scenes.ts): "<kingdom>_<step>". Steps:
 * caught, stands, challenge, prize, underground, key, stone (the way out); new_stone,
 * yield (the way back). The valley's own: festival, hundredth, way_out, rescue. */
export const sceneOf = (k: KingdomId, step: string) => `${k}_${step}`;

/** The scenes that aren't scenes: the credits, rolled (screens/credits.ts). */
export const FAKE_CREDITS = "fake_credits";
export const END_CREDITS = "end_credits";
/** The opening, before you pick your racer (a new file). */
export const OPENING = "first_race";
/** The Rage, kingdom by kingdom (each staged in its own ruins). */
export const RAGE = [
  "dragon_rage",
  "rage_valley",
  "rage_snow",
  "rage_desert",
  "rage_beach",
  "rage_shards",
] as const;
