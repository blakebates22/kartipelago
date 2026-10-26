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
  spawn: { x: number; z: number; heading: number };
  gateways: Gateway[];
}

export const REGIONS: Region[] = [
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

/** Is (x, z) inside the gateway's trigger (by `extra` metres more)? */
export const inGateway = (g: Gateway, x: number, z: number, extra = 0) =>
  Math.hypot(x - g.x, z - g.z) < g.radius + extra;
