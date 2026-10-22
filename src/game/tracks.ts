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
      "Palm-lined S-bends, a wooden bridge, a stone ford and a gentle giant strolling by the river.",
    preview: "previews/riverbend_palms.jpg",
    modes: ["race", "timeTrial"],
    theme: "jungle_falls",
    music: "riverbend",
    load: { scene: "track", packageId: "riverbend_palms" },
  },
  {
    id: "cascade_caverns",
    name: "Cascade Caverns",
    description:
      "Leap through a thundering waterfall, roar through the caves and race the high canyon ledges.",
    preview: "previews/cascade_caverns.jpg",
    modes: ["race", "timeTrial"],
    theme: "jungle_falls",
    music: "cascade",
    load: { scene: "track", packageId: "cascade_caverns" },
  },
  {
    id: "bonebog_pyramid",
    name: "Bonebog Pyramid",
    description:
      "Race the raised boardwalks of a living swamp, through a giant's ribs and straight through a colossal pyramid.",
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
      "Climb an erupting volcano past a fire-breathing dragon, race through its lava caverns and escape the eruption.",
    preview: "previews/ember_peak.jpg",
    modes: ["race", "timeTrial"],
    theme: "volcanic_apocalypse",
    music: "ember",
    load: { scene: "track", packageId: "ember_peak" },
  },
  // Frostveil Peaks (src/game/worlds.ts), built by tools/blender/prehistoric/frostveil_*.py.
  {
    id: "frostveil_citadel",
    name: "Frostveil Citadel",
    description:
      "Climb to a lost citadel in the moonlit mountains: giant bridges over clouds, a serpent's mouth, a temple of gold and a frozen descent.",
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
      "A sunny race round a frozen lake: geysers, a glowing ice cave, jumps over gorges and a spiral up inside a giant tree to bridges in the treetops.",
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
      "Race through a Christmas village on a snowy evening: round the giant tree, over the frozen river, past rolling snowballs, up to the bell tower and down the sleigh run.",
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
      "Plunge into a fractured glacier: a crystal cathedral, a giant loop-the-loop over the abyss, a mirror lake and a bridge beneath the northern lights.",
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
      "A flat-out dash round a great red-rock canyon: down the cliffs, under a giant sandstone arch, over the gorge and past a thundering waterfall.",
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
      "Race round a sun-drenched oasis resort: a turquoise lake, a waterfront market, a great arched bridge, a domed pavilion, cascading terraces and the palace above.",
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
      "Race by moonlight through an abandoned frontier town where the lanterns still burn, past the graveyard and over the glowing chasm. Dare you take the shortcut through the haunted mine?",
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
      "Plunge into a smoking asteroid crater and race down through the world beneath the desert: crystal caverns, a lost jungle full of dinosaurs, rivers of lava, a dragon's lair and the glowing heart of the Earth. Then climb back into the sun.",
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
      "Race the festival lap of a sunlit kingdom of karst islands ruled by dragons: through the riverside market, up the cliffs, over the Great Waterfall Bridge, through the temple gardens and along the sky paths as the great jade dragon flies overhead.",
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
      "The dragon kingdom's desert frontier at golden hour: stacked cliffside hairpins, a bridge over the falls, a dragon's bones, the imperial quarry, the High Bridges and the Final Twist. The most technical drifting course in the game.",
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
      "The kingdom's highest mountains in a blizzard. Half the lap is a choice of roads: the High Cliff Road or the Frozen Supply Road, the Monastery Ridge or the Frozen Aqueduct. Past ration lines and full storehouses, up to the blazing citadel under the ice dragon.",
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
      "The grand finale: the dragon kingdom's sacred heart on the night of its greatest festival. Over the Waterfall Bridge, up to the Star Bridge above the clouds, round the great golden rings of the observatory and down to the palace, while the sky fills with fireworks, more every lap, until the whole kingdom erupts on the last.",
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
    theme: "ancient_lake",
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
