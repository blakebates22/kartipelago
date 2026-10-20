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
    name: "Frostveil Peaks",
    tagline: "A lost citadel",
    description:
      "Snowbound mountains where an ancient civilization built temples, bridges and fortresses into the peaks.",
    color: "#6f7fd6",
    tracks: ["frostveil_citadel", "snowy_summit", "hearthglow_hollow"],
    // One more course is planned; rename this once it has a name.
    comingSoon: ["Coming Soon"],
  },
  {
    id: "test_world",
    name: "Test World",
    tagline: "Prototypes",
    description:
      "Prototypes and practice: the material demo, the early test circuits and the drift park.",
    color: "#5fb8f0",
    tracks: ["dino_demo", "drift_loop", "ribbon_ridge", "meadow_run", "bridge_test", "drift_park"],
    testing: true,
  },
];

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
export const currentWorld = (sel: { worldId?: string; trackId: string }): WorldEntry =>
  worldById(sel.worldId ?? "") ?? worldOfTrack(sel.trackId) ?? WORLDS[0]!;
