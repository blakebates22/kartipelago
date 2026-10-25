/**
 * Worlds: groups of tracks, picked before the track. Tracks mode goes
 * World Select → Track Select → race.
 *
 * Ids are stable (saved in settings, used in URLs and by Adventure later), so rename a
 * world's `name` freely but never its `id`. A track belongs to exactly one world; the
 * order here is the order on the track select screen. Add a world by adding an entry.
 */
import { trackById, type TrackEntry } from "./tracks";

export interface WorldEntry {
  /** Stable id. */
  id: string;
  name: string;
  /** One line under the name on World Select. */
  tagline: string;
  description: string;
  /** Banner colour on World Select. */
  color: string;
  /** Track ids, in menu order. */
  tracks: string[];
  /** Unfinished worlds are labelled as such. */
  testing?: boolean;
  /** Kept in the game (its tracks still load, e.g. with ?track=) but not shown in the
   * menus. */
  hidden?: boolean;
  /** Names of tracks still to come: shown after the real ones as "Coming Soon". */
  comingSoon?: string[];
}

export const WORLDS: WorldEntry[] = [
  {
    id: "prehistoric",
    name: "Prehistoric World",
    tagline: "A lost valley",
    description:
      "A lost valley of sunny rivers, roaring waterfalls, misty fossil swamps and a smoking volcano.",
    color: "#e8873a",
    tracks: ["riverbend_palms", "cascade_caverns", "bonebog_pyramid", "ember_peak"],
  },
  {
    id: "frostveil",
    name: "Snowy Peaks",
    tagline: "A lost citadel",
    description:
      "Snowbound mountains where an ancient civilization built temples, bridges and fortresses into the peaks.",
    color: "#6f7fd6",
    tracks: ["frostveil_citadel", "snowy_summit", "hearthglow_hollow", "aurora_rift"],
  },
  {
    id: "desert",
    name: "Desert World",
    tagline: "Red rock country",
    description:
      "Sun-baked red-rock country: vast canyons, towering mesas, hidden oases and the ghost towns of the old frontier.",
    color: "#d8703a",
    tracks: ["canyon_dash", "oasis_haven", "dry_gulch", "impact_depths"],
  },
  {
    id: "beach",
    name: "Tropic Isles",
    tagline: "Sun, sea and shipwrecks",
    description:
      "Sunny coves and lagoons: a lighthouse on the rocks, a pirate cove with its wreck, a dormant volcano and a seaside water park.",
    color: "#22b4c8",
    tracks: ["coral_cove", "shipwreck_bay", "volcano_isle", "splash_lagoon"],
  },
  {
    id: "dragon",
    name: "Dragon Kingdom",
    tagline: "Castles and dragons",
    description:
      "A kingdom of castles, ruins and dragons: a keep at sunset, a jungle castle reclaimed by the trees, a fortress in a storm and a moonlit palace.",
    color: "#2fae8f",
    tracks: ["dragon_isles", "dragon_canyon", "snow_dragon_pass", "celestial_dragon_festival"],
  },
  {
    id: "test_world",
    name: "Testing",
    tagline: "Prototypes",
    description:
      "Prototypes and practice: the material demo, the early test circuits and the drift park.",
    color: "#5fb8f0",
    tracks: [
      "dino_demo",
      "drift_loop",
      "ribbon_ridge",
      "meadow_run",
      "bridge_test",
      "loop_lab",
      "drift_park",
      "riverbend_palms_v21",
      "cascade_caverns_v2",
      "cascade_caverns_ruin_v2",
      "ember_peak_v2",
      "bonebog_pyramid_v2",
      "frostveil_citadel_v2",
      "snowy_summit_v2",
      "hearthglow_hollow_v2",
      "oasis_haven_v2",
      "dry_gulch_v2",
      "aurora_rift_v2",
      "impact_depths_v2",
      "dragon_isles_v2",
      "dragon_canyon_v2",
      "snow_dragon_pass_v2",
      "celestial_dragon_festival_v2",
      "riverbend_palms_ruin",
      "cascade_caverns_ruin",
      "bonebog_pyramid_ruin",
      "ember_peak_ruin",
      "frostveil_citadel_ruin",
      "boss_prehistoric",
      "boss_snowy",
      "boss_desert",
      "boss_dragon",
      "boss_tropic",
      "coral_cove_v2",
      "shipwreck_bay_v2",
    ],
    testing: true,
    // Set aside for now: the prototypes stay in the code but out of the menus.
    hidden: true,
  },
];

/** The worlds the menus show. */
export const VISIBLE_WORLDS = WORLDS.filter((w) => !w.hidden);

export const worldById = (id: string) => WORLDS.find((w) => w.id === id);

/** The world a track belongs to. */
export const worldOfTrack = (trackId: string) => WORLDS.find((w) => w.tracks.includes(trackId));

/** A world's tracks, in order. */
export const tracksOf = (w: WorldEntry): TrackEntry[] =>
  w.tracks.map((id) => trackById(id)).filter((t): t is TrackEntry => Boolean(t));

/**
 * What track select lists for a world: its tracks, then a locked "Coming Soon" tile for
 * each planned one (not playable: no picture, no package).
 */
export const trackTilesOf = (w: WorldEntry): TrackEntry[] => {
  const tracks = tracksOf(w);
  const soon = (w.comingSoon ?? []).map((name, i): TrackEntry => ({
    id: `${w.id}_soon_${i + 1}`,
    name,
    description: "Coming soon: still being built.",
    preview: "",
    modes: ["race"],
    music: tracks[0]?.music ?? "map",
    load: { scene: "track" },
    comingSoon: true,
  }));
  return [...tracks, ...soon];
};

/** The world the menus should open on: the one last picked, else the last track's. */
export const currentWorld = (sel: { worldId?: string; trackId: string }): WorldEntry => {
  const shown = (w: WorldEntry | undefined) => (w && !w.hidden ? w : undefined);
  return (
    shown(worldById(sel.worldId ?? "")) ?? shown(worldOfTrack(sel.trackId)) ?? VISIBLE_WORLDS[0]!
  );
};
