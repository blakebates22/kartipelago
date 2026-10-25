/**
 * Every track you can pick in the menus, with what the track select screen shows and
 * how to load it. Built-in tracks come from assets/data; Blender tracks load from
 * public/tracks/<id>/ (docs/track-pipeline.md). Add a track here to list it.
 */
import driftLoop from "../../assets/data/track.json";
import ribbonRidge from "../../assets/data/track2.json";
import meadowRun from "../../assets/data/track3.json";
import type { TrackData } from "../world/track";
import type { SessionScene } from "./session";

export type TrackMode = "race" | "timeTrial" | "practice";

export interface TrackEntry {
  /** Stable id: used for records, settings and ?track=. */
  id: string;
  name: string;
  description: string;
  /** Unfinished tracks are labelled as prototypes. */
  prototype?: boolean;
  /** Preview picture (public/previews/). */
  preview: string;
  modes: TrackMode[];
  /** Environment theme (Blender material library themes), if it has one. */
  theme?: string;
  /** Music while racing. */
  music: string;
  load: { scene: SessionScene; trackData?: TrackData; packageId?: string };
  /** Old ?track= numbers that open it directly. */
  legacyNumber?: number;
  /** A planned track: shown in track select as "Coming Soon", not playable yet. */
  comingSoon?: boolean;
}

export const TRACKS: TrackEntry[] = [
  // Prehistoric World (src/game/worlds.ts), built by tools/blender/prehistoric/.
  {
    id: "riverbend_palms",
    name: "Riverbend Palms",
    description:
      "Palm-shaded S-bends, a creaky bridge and a splashy ford. Mind the long-neck strolling across the road.",
    preview: "previews/riverbend_palms.jpg",
    modes: ["race", "timeTrial"],
    theme: "jungle_cascade",
    music: "riverbend",
    load: { scene: "track", packageId: "riverbend_palms" },
  },
  // The previous Riverbend Palms (v2.1, before Blake's first review round), kept
  // playable with ?track=riverbend_palms_v21. Not in any world's menu.
  {
    id: "riverbend_palms_v21",
    name: "Riverbend Palms (v2.1)",
    description: "The version before the first review round.",
    preview: "previews/riverbend_palms.jpg",
    modes: ["race", "timeTrial"],
    theme: "jungle_cascade",
    music: "riverbend",
    load: { scene: "track", packageId: "riverbend_palms_v21" },
  },
  {
    id: "cascade_caverns",
    name: "Cascade Caverns",
    description:
      "Punch straight through the waterfall, rattle through the caves, then hug the canyon ledges high above.",
    preview: "previews/cascade_caverns.jpg",
    modes: ["race", "timeTrial"],
    theme: "jungle_cascade",
    music: "cascade",
    load: { scene: "track", packageId: "cascade_caverns" },
  },
  // The previous Cascade Caverns (v2, before Blake's first review round), kept
  // playable with ?track=cascade_caverns_v2. Not in any world's menu.
  {
    id: "cascade_caverns_v2",
    name: "Cascade Caverns (v2)",
    description: "The version before the first review round.",
    preview: "previews/cascade_caverns.jpg",
    modes: ["race", "timeTrial"],
    theme: "jungle_cascade",
    music: "cascade",
    load: { scene: "track", packageId: "cascade_caverns_v2" },
  },
  {
    id: "bonebog_pyramid",
    name: "Bonebog Pyramid",
    description:
      "Rickety boardwalks over a steaming swamp, through a giant's ribcage and right through the pyramid.",
    preview: "previews/bonebog_pyramid.jpg",
    modes: ["race", "timeTrial"],
    theme: "bonebog_swamp",
    music: "bonebog",
    load: { scene: "track", packageId: "bonebog_pyramid" },
  },
  {
    id: "ember_peak",
    name: "Ember Peak",
    description:
      "Across a smouldering volcanic field: a jump over the lava river and a cave through the volcano.",
    preview: "previews/ember_peak.jpg",
    modes: ["race", "timeTrial"],
    theme: "volcanic_apocalypse",
    music: "ember",
    load: { scene: "track", packageId: "ember_peak" },
  },
  // The first Dry Gulch (round Boot Hill, the long mine), replaced by the new lap on
  // Oct 24, kept playable with ?track=dry_gulch_v2. Not in any world's menu.
  {
    id: "dry_gulch_v2",
    name: "Dry Gulch Ghost Town (v2)",
    description:
      "The first Dry Gulch: round Boot Hill, the Rickety Trestle and the long haunted mine.",
    preview: "previews/dry_gulch_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "dry_gulch",
    music: "ghost",
    load: { scene: "track", packageId: "dry_gulch_v2" },
  },
  // The first Aurora Rift (the new lap replaced it on 2026-10-24): ?track=aurora_rift_v2.
  {
    id: "aurora_rift_v2",
    name: "Aurora Rift (v2)",
    description:
      "Inside a cracked glacier: a crystal cathedral, a loop over the abyss, a bridge under the northern lights.",
    preview: "previews/aurora_rift_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "aurora_rift",
    music: "aurora",
    load: { scene: "track", packageId: "aurora_rift_v2" },
  },
  // The first Impact Depths (the new lap replaced it on 2026-10-24): ?track=impact_depths_v2.
  {
    id: "impact_depths_v2",
    name: "Impact Depths (v2)",
    description:
      "Dive into a smoking crater, down through crystal caves, a lost jungle and lava, to the Earth's core.",
    preview: "previews/impact_depths_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "impact_depths",
    music: "depths",
    load: { scene: "track", packageId: "impact_depths_v2" },
  },
  // The beach world's first course, painted (the Tropic Isles, Oct 25): the greybox's lap
  // exactly, a bright tropical cove. A really short lap, all three under a minute.
  // ?track=coral_cove.
  {
    id: "coral_cove",
    name: "Coral Cove",
    description:
      "A sunny cove: over the boardwalk's jump across the channel, round the lighthouse on its rock, down the palm avenue to the beach.",
    preview: "previews/coral_cove.jpg",
    modes: ["race", "timeTrial"],
    theme: "coral_cove",
    music: "title",
    load: { scene: "track", packageId: "coral_cove" },
  },
  // The Coral Cove greybox (the painted course replaced it on 2026-10-25; the same lap):
  // ?track=coral_cove_v2.
  {
    id: "coral_cove_v2",
    name: "Coral Cove (greybox, v2)",
    description:
      "A short beach lap: the boardwalk jump over the channel, the lighthouse hairpin and back down to the sand.",
    preview: "previews/coral_cove_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "beach_party",
    music: "title",
    load: { scene: "track", packageId: "coral_cove_v2" },
  },
  // The beach world's second course (working name), a greybox: a pirate cove, through a
  // wrecked galleon and off its fallen mast. ?track=shipwreck_bay.
  {
    id: "shipwreck_bay",
    name: "Shipwreck Bay (greybox)",
    description:
      "Over the rolling pier, through the wrecked galleon's hold, up its fallen mast and off it over the river mouth.",
    preview: "previews/shipwreck_bay.jpg",
    modes: ["race", "timeTrial"],
    theme: "beach_party",
    music: "title",
    load: { scene: "track", packageId: "shipwreck_bay" },
  },
  // The first Dragonspire Keep (the old Dragon Isles; the painted v3 lap replaced it on
  // 2026-10-25): ?track=dragon_isles_v2.
  {
    id: "dragon_isles_v2",
    name: "Dragonspire Keep (v2)",
    description:
      "Festival day on the karst isles: market streets, cliff roads, a huge waterfall bridge, a jade dragon above.",
    preview: "previews/dragon_isles_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "dragon_isles",
    music: "dragon",
    load: { scene: "track", packageId: "dragon_isles_v2" },
  },
  // The beach world's third course (working name), a greybox: a tropical island, the
  // volcano dormant behind it. ?track=volcano_isle.
  {
    id: "volcano_isle",
    name: "Volcano Isle (greybox)",
    description:
      "Geysers on the hot-spring flats, jungle switchbacks, through the old lava tube and off the cliff over the lagoon.",
    preview: "previews/volcano_isle.jpg",
    modes: ["race", "timeTrial"],
    theme: "beach_party",
    music: "title",
    load: { scene: "track", packageId: "volcano_isle" },
  },
  // The beach world's fourth course (working name), a greybox: a seaside water park, the
  // wave loop, the slide tower and its flume, the lazy river. ?track=splash_lagoon.
  {
    id: "splash_lagoon",
    name: "Splash Lagoon (greybox)",
    description:
      "Round the Big Curl wave loop, up the slide tower and down the flume, then the lazy river's bend or its plank.",
    preview: "previews/splash_lagoon.jpg",
    modes: ["race", "timeTrial"],
    theme: "beach_party",
    music: "title",
    load: { scene: "track", packageId: "splash_lagoon" },
  },
  // The first Dragon Canyon paint (the desert frontier; the Emerald Kingdom repaint replaced
  // it on 2026-10-25): ?track=dragon_canyon_v2.
  {
    id: "dragon_canyon_v2",
    name: "Dragon Canyon (v2)",
    description:
      "Golden-hour hairpins stacked up the cliffs. The most technical drifting course in the game.",
    preview: "previews/dragon_canyon_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "dragon_canyon",
    music: "dragon_canyon",
    load: { scene: "track", packageId: "dragon_canyon_v2" },
  },
  // The first Snow Dragon Pass (the painted v3 lap, Emberdeep Hold, replaced it on
  // 2026-10-25): ?track=snow_dragon_pass_v2.
  {
    id: "snow_dragon_pass_v2",
    name: "Snow Dragon Pass (v2)",
    description:
      "A blizzard over the highest peaks. Pick your road twice, then climb to the citadel under the ice dragon.",
    preview: "previews/snow_dragon_pass_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "snow_dragon_pass",
    music: "snow_dragon",
    load: { scene: "track", packageId: "snow_dragon_pass_v2" },
  },
  // The first Celestial Dragon Festival (the painted v3 lap, the Moonstone Kingdom,
  // replaced it on 2026-10-25): ?track=celestial_dragon_festival_v2.
  {
    id: "celestial_dragon_festival_v2",
    name: "Celestial Dragon Festival (v2)",
    description:
      "The grand finale on festival night: leap among the stars while fireworks fill the sky, more every lap.",
    preview: "previews/celestial_dragon_festival_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "celestial_dragon_festival",
    music: "celestial",
    load: { scene: "track", packageId: "celestial_dragon_festival_v2" },
  },
  // The previous Oasis Haven (v2, the lakeside resort, before the redo back in the
  // desert), kept playable with ?track=oasis_haven_v2. Not in any world's menu.
  {
    id: "oasis_haven_v2",
    name: "Oasis Haven (v2)",
    description: "The version before the redo.",
    preview: "previews/oasis_haven_v2.jpg",
    modes: ["race", "timeTrial"],
    theme: "oasis_haven",
    music: "oasis",
    load: { scene: "track", packageId: "oasis_haven_v2" },
  },
  // The previous Bonebog Pyramid (v2, before Blake's driving notes), kept playable
  // with ?track=bonebog_pyramid_v2. Not in any world's menu.
  {
    id: "bonebog_pyramid_v2",
    name: "Bonebog Pyramid (v2)",
    description: "The version before the new lap.",
    preview: "previews/bonebog_pyramid.jpg",
    modes: ["race", "timeTrial"],
    theme: "bonebog_swamp",
    music: "bonebog",
    load: { scene: "track", packageId: "bonebog_pyramid_v2" },
  },
  // The previous Frostveil Citadel (before the shorter bridge and the quicker run home),
  // kept playable with ?track=frostveil_citadel_v2. Not in any world's menu.
  {
    id: "frostveil_citadel_v2",
    name: "Frostveil Citadel (v2)",
    description: "The version before the shorter lap.",
    preview: "previews/frostveil_citadel.jpg",
    modes: ["race", "timeTrial"],
    theme: "frost_citadel",
    music: "frostveil",
    load: { scene: "track", packageId: "frostveil_citadel_v2" },
  },
  // The previous Snowy Summit Pass (before the shorter, twistier lap), kept playable with
  // ?track=snowy_summit_v2. Not in any world's menu.
  {
    id: "snowy_summit_v2",
    name: "Snowy Summit Pass (v2)",
    description: "The version before the shorter lap.",
    preview: "previews/snowy_summit.jpg",
    modes: ["race", "timeTrial"],
    theme: "summit_pass",
    music: "summit",
    load: { scene: "track", packageId: "snowy_summit_v2" },
  },
  // The previous Hearthglow Hollow (the long climb and sleigh run, before the shorter
  // lap and the shortcut), kept playable with ?track=hearthglow_hollow_v2.
  {
    id: "hearthglow_hollow_v2",
    name: "Hearthglow Hollow (v2)",
    description: "The version before the shorter lap.",
    preview: "previews/hearthglow_hollow.jpg",
    modes: ["race", "timeTrial"],
    theme: "hearthglow",
    music: "hearthglow",
    load: { scene: "track", packageId: "hearthglow_hollow_v2" },
  },
  // The previous Ember Peak (v2, the long climb up the volcano, before the redo), kept
  // playable with ?track=ember_peak_v2. Not in any world's menu.
  {
    id: "ember_peak_v2",
    name: "Ember Peak (v2)",
    description: "The version before the redo.",
    preview: "previews/ember_peak.jpg",
    modes: ["race", "timeTrial"],
    theme: "volcanic_apocalypse",
    music: "ember",
    load: { scene: "track", packageId: "ember_peak_v2" },
  },
  // Snowy Peaks (src/game/worlds.ts), built by tools/blender/prehistoric/frostveil_*.py.
  {
    id: "frostveil_citadel",
    name: "Frostveil Citadel",
    description:
      "Cloud-high bridges to a lost citadel, through a stone serpent's jaws and down a frozen slide.",
    preview: "previews/frostveil_citadel.jpg",
    modes: ["race", "timeTrial"],
    theme: "frost_citadel",
    music: "frostveil",
    load: { scene: "track", packageId: "frostveil_citadel" },
  },
  {
    id: "snowy_summit",
    name: "Snowy Summit Pass",
    description:
      "Round a frozen lake past geysers and an ice cave, then spiral up a giant tree to the treetop bridges.",
    preview: "previews/snowy_summit.jpg",
    modes: ["race", "timeTrial"],
    theme: "summit_pass",
    music: "summit",
    load: { scene: "track", packageId: "snowy_summit" },
  },
  {
    id: "hearthglow_hollow",
    name: "Hearthglow Hollow",
    description:
      "A snowy village at dusk: round the big tree, up the winding mountain road, down the sleigh run and home through the old town (or its hidden back alley).",
    preview: "previews/hearthglow_hollow.jpg",
    modes: ["race", "timeTrial"],
    theme: "hearthglow",
    music: "hearthglow",
    load: { scene: "track", packageId: "hearthglow_hollow" },
  },
  {
    id: "aurora_rift",
    name: "Aurora Rift",
    description:
      "Into a cracked glacier: round the crystal Monolith, jump the broken bridge, loop the loop, out over the Rift.",
    preview: "previews/aurora_rift.jpg",
    modes: ["race", "timeTrial"],
    theme: "aurora_rift",
    music: "aurora",
    load: { scene: "track", packageId: "aurora_rift" },
  },
  // Desert World (src/game/worlds.ts), built by tools/blender/prehistoric/canyon_*.py.
  {
    id: "canyon_dash",
    name: "Canyon Dash",
    description:
      "Flat out round a red-rock canyon: down the cliffs, under the great arch and over the gorge.",
    preview: "previews/canyon_dash.jpg",
    modes: ["race", "timeTrial"],
    theme: "canyon_dash",
    music: "canyon",
    load: { scene: "track", packageId: "canyon_dash" },
  },
  {
    id: "oasis_haven",
    name: "Oasis Haven",
    description:
      "A green pool in the deep desert: a nomad camp, a wind-carved arch, the dune sea and a spiral up the old watchtower.",
    preview: "previews/oasis_haven.jpg",
    modes: ["race", "timeTrial"],
    theme: "oasis_haven",
    music: "oasis",
    load: { scene: "track", packageId: "oasis_haven" },
  },
  {
    id: "dry_gulch",
    name: "Dry Gulch Ghost Town",
    description:
      "A moonlit ghost town where the lanterns still burn. The haunted mine is a shortcut, if you dare.",
    preview: "previews/dry_gulch.jpg",
    modes: ["race", "timeTrial"],
    theme: "dry_gulch",
    music: "ghost",
    load: { scene: "track", packageId: "dry_gulch" },
  },
  {
    id: "impact_depths",
    name: "Impact Depths",
    description:
      "Down the great pit under the cracked cave roof to the core, and the updraft back up.",
    preview: "previews/impact_depths.jpg",
    modes: ["race", "timeTrial"],
    theme: "impact_depths",
    music: "depths",
    load: { scene: "track", packageId: "impact_depths" },
  },
  {
    id: "dragon_isles",
    // Blake, Oct 24-25: Dragonspire Keep, the v3 greybox's lap painted as a castle at
    // sunset (it keeps the id, so its records carry on; ghosts are kept per layout).
    name: "Dragonspire Keep",
    description:
      "Through the castle gate and town, up the cliff road, over the broken waterfall viaduct, round the keep and its red dragon, down the beacon tower to the docks.",
    preview: "previews/dragon_isles.jpg",
    modes: ["race", "timeTrial"],
    theme: "dragonspire_keep",
    music: "dragon",
    load: { scene: "track", packageId: "dragon_isles" },
  },
  {
    id: "dragon_canyon",
    // Blake, Oct 25: repainted as the Emerald Kingdom, an overgrown jungle castle and its
    // ruins (the same lap; the first paint is dragon_canyon_v2).
    name: "Dragon Canyon",
    description:
      "Hairpins stacked up the jungle cliffs, through the ruins and the crystal caverns, under the green dragon's tower. The most technical drifting course in the game.",
    preview: "previews/dragon_canyon.jpg",
    modes: ["race", "timeTrial"],
    theme: "emerald_kingdom",
    music: "dragon_canyon",
    load: { scene: "track", packageId: "dragon_canyon" },
  },
  {
    id: "snow_dragon_pass",
    // Blake, Oct 25: Emberdeep Hold, the v3 greybox's lap painted as a fortress built
    // into a dark mountain on a stormy night (it keeps the id, so its records carry on;
    // ghosts are kept per layout).
    name: "Emberdeep Hold",
    description:
      "Out of the Outer Gate, up the mountain or through the Hall of Pillars, along the ramparts, over the broken bridge, down past the falls and up round the dragon on its gold.",
    preview: "previews/snow_dragon_pass.jpg",
    modes: ["race", "timeTrial"],
    theme: "emberdeep_hold",
    music: "snow_dragon",
    load: { scene: "track", packageId: "snow_dragon_pass" },
  },
  {
    id: "celestial_dragon_festival",
    // Blake, Oct 25: the v3 greybox's lap painted as the Moonstone Kingdom, a moonlit
    // violet kingdom (the first lap is celestial_dragon_festival_v2).
    name: "Celestial Dragon Festival",
    description:
      "A moonlit kingdom: over the glowing lake, round the winged dragon's fountain, up through the crystals and off the Star Leap, past the observatory to the palace.",
    preview: "previews/celestial_dragon_festival.jpg",
    modes: ["race", "timeTrial"],
    theme: "moonstone_kingdom",
    music: "celestial",
    load: { scene: "track", packageId: "celestial_dragon_festival" },
  },
  // Test World.
  {
    id: "dino_demo",
    name: "Dino Demo",
    description:
      "A dusty lakeside road through grassy hills, a layered cliff and a dark tunnel through the rock.",
    preview: "previews/dino_demo.jpg",
    modes: ["race", "timeTrial"],
    theme: "mirror_lake",
    music: "race",
    load: { scene: "track", packageId: "dino_demo" },
  },
  {
    id: "drift_loop",
    name: "Drift Loop",
    description: "A simple flowing circuit. Learn your lines and your drifts.",
    preview: "previews/drift_loop.jpg",
    modes: ["race", "timeTrial"],
    music: "race",
    load: { scene: "track", trackData: driftLoop as TrackData },
    legacyNumber: 1,
  },
  {
    id: "ribbon_ridge",
    name: "Ribbon Ridge",
    description: "Hills, dips and banked bends along a winding ridge.",
    preview: "previews/ribbon_ridge.jpg",
    prototype: true,
    modes: ["race", "timeTrial"],
    music: "race",
    load: { scene: "track", trackData: ribbonRidge as TrackData },
    legacyNumber: 2,
  },
  {
    id: "meadow_run",
    name: "Meadow Run",
    description: "An open road through the meadow. No walls: just trees, rocks and a tunnel.",
    preview: "previews/meadow_run.jpg",
    prototype: true,
    modes: ["race", "timeTrial"],
    music: "race",
    load: { scene: "track", trackData: meadowRun as TrackData },
    legacyNumber: 3,
  },
  {
    id: "bridge_test",
    name: "Bridge Test",
    description: "A banked figure-eight that crosses itself on a bridge. Made in Blender.",
    preview: "previews/bridge_test.jpg",
    prototype: true,
    modes: ["race", "timeTrial"],
    music: "race",
    load: { scene: "track", packageId: "bridge_test" },
  },
  {
    id: "loop_lab",
    name: "Loop Lab",
    description:
      "A plain test circuit: a boost pad into one giant loop-the-loop, then round again.",
    preview: "previews/loop_lab.jpg",
    prototype: true,
    modes: ["race", "timeTrial"],
    theme: "summit_pass",
    music: "race",
    load: { scene: "track", packageId: "loop_lab" },
  },
  {
    id: "drift_park",
    name: "Drift Park",
    description:
      "Twelve practice loops for learning to drift. [ and ] change loop, F flips direction.",
    preview: "previews/drift_park.jpg",
    modes: ["practice"],
    music: "map",
    load: { scene: "drift" },
  },
];

export const trackById = (id: string) => TRACKS.find((t) => t.id === id);

/**
 * The title screen's course: Party Beach, a dinosaur beach party (built by
 * tools/blender/prehistoric/beach_party.py). It isn't in any world, so it never shows
 * in track select; the title demo races on it.
 */
export const TITLE_TRACK: TrackEntry = {
  id: "beach_party",
  name: "Party Beach",
  description: "A dinosaur beach party: palms, sand, a turquoise sea and a dance floor.",
  preview: "previews/dino_demo.jpg",
  modes: ["race"],
  theme: "beach_party",
  music: "title",
  load: { scene: "track", packageId: "beach_party" },
};

export const MODE_LABELS: Record<TrackMode, { name: string; sub: string }> = {
  race: { name: "RACE", sub: "8 KARTS · 3 LAPS" },
  timeTrial: { name: "TIME TRIAL", sub: "SOLO · 3 LAPS" },
  practice: { name: "PRACTICE", sub: "FREE DRIVE" },
};
