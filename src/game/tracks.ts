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
      "Slither through slick mud and over wooden causeways, under giant ribs and through a pyramid.",
    preview: "previews/bonebog_pyramid.jpg",
    modes: ["race", "timeTrial"],
    theme: "fossil_canyon",
    music: "bonebog",
    load: { scene: "track", packageId: "bonebog_pyramid" },
  },
  {
    id: "ember_peak",
    name: "Ember Peak",
    description:
      "Spiral up a rumbling volcano over rivers of lava, then plunge down the side. Mind the lava!",
    preview: "previews/ember_peak.jpg",
    modes: ["race", "timeTrial"],
    theme: "hot_top_volcano",
    music: "ember",
    load: { scene: "track", packageId: "ember_peak" },
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
