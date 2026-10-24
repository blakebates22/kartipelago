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
      "A fast run across a smouldering volcanic field: a big jump over the lava river, a cave through the volcano, and a dragon from beyond the valley.",
    preview: "previews/ember_peak.jpg",
    modes: ["race", "timeTrial"],
    theme: "volcanic_apocalypse",
    music: "ember",
    load: { scene: "track", packageId: "ember_peak" },
  },
  // The greybox of Dry Gulch's new lap (v3: through the graveyard, drifting between the
  // buildings, a wilder mine), to drive before it's dressed: ?track=dry_gulch_v3.
  {
    id: "dry_gulch_v3",
    name: "Dry Gulch Ghost Town (v3 greybox)",
    description:
      "The new lap in plain shapes: the chicane, the graveyard, the broken trestle, the ravine and the mine.",
    preview: "previews/dry_gulch.jpg",
    modes: ["race", "timeTrial"],
    theme: "dry_gulch",
    music: "ghost",
    load: { scene: "track", packageId: "dry_gulch_v3" },
  },
  // The greybox of Oasis Haven's new lap (v3: back in the desert, nearly all bends), to
  // drive before it's dressed: ?track=oasis_haven_v3. Not in any world's menu.
  {
    id: "oasis_haven_v3",
    name: "Oasis Haven (v3 greybox)",
    description:
      "The new lap in plain shapes: the pool, the camp, the butte, the dune sea and the watchtower.",
    preview: "previews/oasis_haven.jpg",
    modes: ["race", "timeTrial"],
    theme: "oasis_haven",
    music: "oasis",
    load: { scene: "track", packageId: "oasis_haven_v3" },
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
      "Inside a cracked glacier: a crystal cathedral, a loop over the abyss, a bridge under the northern lights.",
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
      "A turquoise lake, a waterfront market, terraces of fountains and a palace on top. Very fancy. Very fast.",
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
      "Dive into a smoking crater, down through crystal caves, a lost jungle and lava, to the Earth's core.",
    preview: "previews/impact_depths.jpg",
    modes: ["race", "timeTrial"],
    theme: "impact_depths",
    music: "depths",
    load: { scene: "track", packageId: "impact_depths" },
  },
  {
    id: "dragon_isles",
    name: "Dragon Isles",
    description:
      "Festival day on the karst isles: market streets, cliff roads, a huge waterfall bridge, a jade dragon above.",
    preview: "previews/dragon_isles.jpg",
    modes: ["race", "timeTrial"],
    theme: "dragon_isles",
    music: "dragon",
    load: { scene: "track", packageId: "dragon_isles" },
  },
  {
    id: "dragon_canyon",
    name: "Dragon Canyon",
    description:
      "Golden-hour hairpins stacked up the cliffs. The most technical drifting course in the game.",
    preview: "previews/dragon_canyon.jpg",
    modes: ["race", "timeTrial"],
    theme: "dragon_canyon",
    music: "dragon_canyon",
    load: { scene: "track", packageId: "dragon_canyon" },
  },
  {
    id: "snow_dragon_pass",
    name: "Snow Dragon Pass",
    description:
      "A blizzard over the highest peaks. Pick your road twice, then climb to the citadel under the ice dragon.",
    preview: "previews/snow_dragon_pass.jpg",
    modes: ["race", "timeTrial"],
    theme: "snow_dragon_pass",
    music: "snow_dragon",
    load: { scene: "track", packageId: "snow_dragon_pass" },
  },
  {
    id: "celestial_dragon_festival",
    name: "Celestial Dragon Festival",
    description:
      "The grand finale on festival night: leap among the stars while fireworks fill the sky, more every lap.",
    preview: "previews/celestial_dragon_festival.jpg",
    modes: ["race", "timeTrial"],
    theme: "celestial_dragon_festival",
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
