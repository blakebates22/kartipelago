/**
 * The overworld (Claude Doc "Kartipelago Overworld: Concept & Layout"): one drivable
 * region per kingdom, with gateways into its courses at matching landmarks. Blake, Oct 26:
 * regions with passages (we're in the browser), gateways at landmarks, ~800-900 m
 * across, the champion flow, tools that open one kind of obstacle each, and Banjo-style
 * switches and puzzles.
 *
 * Step 1 of the doc's build order: free roam on an existing course's land with two test
 * gateways. The test region drives on Riverbend Palms' valley (its bowl of grassland is
 * close to the doc's Dinosaur Valley sketch); its own greybox region comes next.
 *
 * Positions are game coordinates (x, z; heading 0 faces +z, the kart's convention).
 */
import type { KingdomId } from "../adventure/data";

export interface Gateway {
  id: string;
  /** The standard course it opens (its ruin, when there is one, is offered too). */
  track: string;
  x: number;
  z: number;
  /** Drive within this of the middle to open its card. */
  radius: number;
  /** Which way the arch faces: you come back out of it this way after a race. */
  heading: number;
  /** The kingdom's dragon's lair (its boss race), not one of its four courses. */
  boss?: boolean;
  /** The name on its board, when it isn't the course's. */
  label?: string;
}

/** A way on to another region (the doc's passages): a gorge, a pass, a causeway. */
export interface Passage {
  id: string;
  label: string;
  /** The region it leads to, and the passage there you come out of. */
  to: string;
  toPassage: string;
  x: number;
  z: number;
  radius: number;
  /** Which way you face coming out of it into this region. */
  heading: number;
  /** Adventure: it opens once this kingdom's dragon has fallen (dev free roam: always). */
  opensAfter?: KingdomId;
  /** What's in the way until then. */
  locked?: string;
}

export interface Region {
  id: string;
  name: string;
  /** The track package whose land the region drives on. */
  packageId: string;
  /** Its music (game/tracks.ts music ids). */
  music: string;
  /** The kingdom's world, for the colours (game/worlds.ts). */
  worldId: string;
  /** The Adventure kingdom it is (src/adventure/data.ts): the story runs through it. */
  kingdom?: KingdomId;
  spawn: { x: number; z: number; heading: number };
  gateways: Gateway[];
  passages?: Passage[];
  /** Adventure: where the champion waits to race you 1 on 1 once round the ring (beside
   * its start line; game/tracks.ts has the region as a race under its package's id). */
  challenge?: { x: number; z: number; heading: number };
}

export const REGIONS: Region[] = [
  {
    // The doc's first region (tools/blender/prehistoric/valley_region.py, a greybox): a
    // cliff-ringed bowl, a ring road round it and spokes in to Elder Mossback's camp.
    id: "dinosaur_valley",
    name: "Dinosaur Valley",
    packageId: "valley_region",
    music: "riverbend",
    worldId: "prehistoric",
    kingdom: "valley",
    challenge: { x: 250, z: 0, heading: -Math.PI / 2 },
    // At the camp, facing north up the north spoke.
    spawn: { x: 0, z: 8, heading: Math.PI },
    gateways: [
      // By the ford where the west spoke crosses the river.
      {
        id: "riverbend",
        track: "riverbend_palms",
        x: -128,
        z: 24,
        radius: 6,
        heading: Math.PI,
      },
      // In the cave mouth beside the falls, north-east, at the end of the cave road.
      {
        id: "cascade",
        track: "cascade_caverns",
        x: 252,
        z: -211.5,
        radius: 6,
        heading: Math.atan2(-0.766, 0.643),
      },
      // On the bog's shore, the pyramid's tip out in the water, south-west.
      {
        id: "bonebog",
        track: "bonebog_pyramid",
        x: -196.6,
        z: 196.6,
        radius: 6,
        heading: Math.atan2(0.707, -0.707),
      },
      // At the lava-lit tunnel in the south-east cliff, the volcano beyond.
      {
        id: "ember",
        track: "ember_peak",
        x: 252,
        z: 211.5,
        radius: 6,
        heading: Math.atan2(-0.766, -0.643),
      },
      // Cinderjaw's Scar, up the burnt trench in the south: the dragon's race.
      {
        id: "scar",
        track: "boss_prehistoric",
        x: 0,
        z: 318,
        radius: 6,
        heading: Math.PI,
        boss: true,
        label: "CINDERJAW'S SCAR",
      },
    ],
    passages: [
      // The Burnt Gorge, through the north cliff: on to the Snow Kingdom.
      {
        id: "burnt_gorge",
        label: "THE BURNT GORGE · TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        toPassage: "burnt_gorge",
        x: -6.8,
        z: -440,
        radius: 8,
        heading: 0,
        opensAfter: "valley",
        locked: "CINDERJAW'S FIRE SPLIT THE CLIFF, BUT THE GORGE STILL BURNS: BEAT HIM FIRST",
      },
    ],
  },
  {
    // The doc's second region (tools/blender/prehistoric/snow_region.py, a greybox): a
    // basin ringed by peaks, a frozen lake in the middle, Hearthglow's village by the gorge.
    id: "snow_kingdom",
    name: "Snow Kingdom",
    packageId: "snow_region",
    music: "hearthglow",
    worldId: "frostveil",
    kingdom: "snow",
    challenge: { x: 238, z: 14, heading: -Math.PI / 2 },
    // In the village square, facing north up to the ring.
    spawn: { x: 0, z: 290, heading: Math.PI },
    gateways: [
      // By the village's great tree (the town square).
      {
        id: "hearthglow",
        track: "hearthglow_hollow",
        x: 20,
        z: 275,
        radius: 6,
        heading: -Math.PI / 2,
      },
      // At the citadel's gate in the west cliff.
      {
        id: "frostveil",
        track: "frostveil_citadel",
        x: -331,
        z: 0,
        radius: 6,
        heading: Math.PI / 2,
      },
      // At the foot of the giant tree, north.
      { id: "summit", track: "snowy_summit", x: 0, z: -285, radius: 6, heading: 0 },
      // At the crack in the glacier, east.
      { id: "aurora", track: "aurora_rift", x: 331, z: 0, radius: 6, heading: -Math.PI / 2 },
      // Rimefang's lair, an ice cave in the north-west cliff: the dragon's race.
      {
        id: "lair",
        track: "boss_snowy",
        x: -232.6,
        z: -232.6,
        radius: 6,
        heading: Math.PI / 4,
        boss: true,
        label: "RIMEFANG'S LAIR",
      },
    ],
    passages: [
      // Back down the Burnt Gorge to the valley.
      {
        id: "burnt_gorge",
        label: "THE BURNT GORGE · BACK TO DINOSAUR VALLEY",
        to: "dinosaur_valley",
        toPassage: "burnt_gorge",
        x: -2.8,
        z: 440,
        radius: 8,
        heading: Math.PI,
      },
    ],
  },
  {
    id: "test_valley",
    name: "Dinosaur Valley (test)",
    packageId: "riverbend_palms",
    music: "riverbend",
    worldId: "prehistoric",
    // Riverbend's start straight, facing up it.
    spawn: { x: 150, z: 5, heading: Math.PI },
    gateways: [
      // In the meadow inside the east bend, facing the east straight.
      { id: "cascade", track: "cascade_caverns", x: 62, z: -69, radius: 6, heading: Math.PI / 2 },
      // In the meadow inside the west bends, facing the west straight.
      {
        id: "bonebog",
        track: "bonebog_pyramid",
        x: -96,
        z: 22,
        radius: 6,
        heading: -Math.PI / 2,
      },
    ],
  },
];

export const regionById = (id: string) => REGIONS.find((r) => r.id === id);

/** The region an Adventure kingdom is driven in, once it's built. */
export const regionOfKingdom = (k: KingdomId) => REGIONS.find((r) => r.kingdom === k);

/** Is (x, z) inside the gateway's trigger (by `extra` metres more)? */
export const inGateway = (
  g: { x: number; z: number; radius: number },
  x: number,
  z: number,
  extra = 0,
) => Math.hypot(x - g.x, z - g.z) < g.radius + extra;
