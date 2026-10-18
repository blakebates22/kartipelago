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

export const MODE_LABELS: Record<TrackMode, { name: string; sub: string }> = {
  race: { name: "RACE", sub: "8 KARTS · 3 LAPS" },
  timeTrial: { name: "TIME TRIAL", sub: "SOLO · 3 LAPS" },
  practice: { name: "PRACTICE", sub: "FREE DRIVE" },
};
