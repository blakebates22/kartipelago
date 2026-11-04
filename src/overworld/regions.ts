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
  /** The kingdom's dragon's lair (its boss race), not one of its four courses: only in
   * the ruined region (it appears with the attack). */
  boss?: boolean;
  /** The name on its board, when it isn't the course's. */
  label?: string;
  /** The Dragon King's Citadel (his race), in the Dragon Kingdom. */
  king?: boolean;
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
  /** It's only there in the ruined region (what the dragon's attack broke open). */
  ruinOnly?: boolean;
  /** Underground (Oct 31: the Edge of the World's tunnel): the ground is looked for down
   * from this height, not from the sky (which finds the land over the tunnel). */
  y?: number;
  /** Adventure: it opens once this kingdom's dragon has fallen (dev free roam: always). */
  opensAfter?: KingdomId;
  /** Adventure: or once this kingdom's smugglers' key is won (its underground games). */
  keyOf?: KingdomId;
  /** What's in the way until then. */
  locked?: string;
  /** What stands across the way on until then, on the passage itself (shown, solid, and
   * the passage won't open; it breaks open the first time you come back after the dragon
   * falls). */
  blocker?: { kind: ObstacleKind | "fire"; width: number };
  /** How the way on looks (Blake, Nov 1: "No portals"): "tunnel", the mouth of the
   * smugglers' tunnel in the rock (the default), or "open", the road just runs on out of
   * sight (a pier, a bridge), its loading zone unmarked. */
  look?: "tunnel" | "open";
}

export interface Region {
  id: string;
  name: string;
  /** The track package whose land the region drives on. */
  packageId: string;
  /** The region after its dragon's attack (the overworld doc's two states, like the
   * courses): the same land wrecked, with the dragon's lair and the way on it broke
   * open. Built by the same script (`--ruin`). */
  ruinPackageId?: string;
  /** Its music (game/tracks.ts music ids). */
  music: string;
  /** The kingdom's world, for the colours (game/worlds.ts). */
  worldId: string;
  /** The Adventure kingdom it is (src/adventure/data.ts): the story runs through it. */
  kingdom?: KingdomId;
  /** A journey between two kingdoms, its own section (Blake, Oct 26: a loading zone at a
   * kingdom's edge, the connecting stretch driven to the next one's): no gateways, a way
   * in at each end (its passages "start", from `from`, and "end", to `to`). `road`: the
   * stretch of its route that's road (the rest goes round out of sight). */
  journey?: { from: KingdomId; to: KingdomId; road: [number, number] };
  /** Where you start; `y`: look for the ground down from here (an underground spawn). */
  spawn: { x: number; z: number; heading: number; y?: number };
  gateways: Gateway[];
  passages?: Passage[];
  /** Adventure: where the champion waits to race you 1 on 1 once round the ring (beside
   * its start line; game/tracks.ts has the region as a race under its package's id). */
  /** The kingdom's Pact Stone, where the story stands it (old, glowing on the hundredth
   * summer, cracked, broken after the Rage): its spot and the way it faces. */
  pactStone?: { x: number; z: number; heading: number };
  challenge?: { x: number; z: number; heading: number };
  /** Adventure: the smugglers' cave (the underground games and their tunnel out), in a
   * walled yard whose way in the sketchy guards keep (the build's puzzle_gate
   * "return"): its gate, and the cave's mouth inside. */
  cave?: { gate: ReturnSpot["gate"]; spot: ReturnSpot["spot"] };
  /** A secret (Banjo-style backtracking): a walled yard you can see on the way out, its
   * way in blocked by an obstacle a later kingdom's tool clears, a treasure chest
   * inside. */
  secret?: ReturnSpot & { tool: KingdomId };
}

export type ObstacleKind = "rockfall" | "ice" | "drift" | "water";

export interface ReturnSpot {
  /** What's in the way (the kingdom's tool clears it). */
  obstacle: ObstacleKind;
  /** The yard's way in (the build's puzzle_gate "return"). */
  gate: { x: number; z: number; heading: number; width: number };
  /** Where the task waits, inside. */
  spot: { x: number; z: number };
}

/** What each obstacle is, on screen. */
export const OBSTACLE_TEXT: Record<ObstacleKind, string> = {
  rockfall: "A ROCKFALL BLOCKS THE WAY IN",
  ice: "THE WAY IN IS FROZEN SHUT",
  drift: "A SAND DRIFT BURIES THE WAY IN",
  water: "A DEEP CHANNEL CUTS OFF THE WAY IN",
};

export const REGIONS: Region[] = [
  {
    // The doc's first region (tools/blender/prehistoric/valley_region.py, a greybox): a
    // cliff-ringed bowl, a ring road round it and spokes in to Elder Mossback's camp.
    id: "dinosaur_valley",
    name: "Dinosaur Valley",
    packageId: "valley_region",
    ruinPackageId: "valley_region_ruin",
    // (tools/blender/prehistoric/valley_layout.py: walled pockets, one world each, round
    // the camp's plateau; the main road one loop through them by a threshold each time.
    // The positions below are the build's entities.)
    // A secret, for the way back: a grotto in the Cascade's woods, walled with ice the Snow Tool melts.
    secret: {
      obstacle: "ice",
      tool: "snow",
      gate: { x: 137.48, z: -94.99, heading: 1.2297, width: 9 },
      spot: { x: 129, z: -98 },
    },
    // The smugglers' Lookout Cave: the Elder's old lookout, a walled hollow on Ember's lower slope.
    cave: {
      gate: { x: 77.89, z: 119.0, heading: -0.01, width: 9 },
      spot: { x: 78, z: 108 },
    },
    music: "riverbend",
    worldId: "prehistoric",
    kingdom: "valley",
    // The valley's Pact Stone, at the camp's east side: the festival's held round it.
    pactStone: { x: 15, z: 6, heading: -2.11 },
    // The main road's start line, on the camp's south side (the 1-on-1 is raced from it).
    challenge: { x: 22, z: 19, heading: -0.9365 },
    // In the camp's square, facing east to the way out onto the road.
    spawn: { x: -6, z: -3, heading: Math.PI / 2 },
    gateways: [
      // Riverbend: the palms on the bend's far bank, by the falls out of the north cliff.
      {
        id: "riverbend",
        track: "riverbend_palms",
        x: -193.68,
        z: -71.01,
        radius: 6,
        heading: 1.2318,
      },
      // Cascade: the cave mouth in the canyon wall, by the falls.
      {
        id: "cascade",
        track: "cascade_caverns",
        x: 176.27,
        z: -162.55,
        radius: 6,
        heading: -1.7847,
      },
      // Bonebog: the pyramid's tip, out in the swamp's far corner.
      {
        id: "bonebog",
        track: "bonebog_pyramid",
        x: -161.68,
        z: 178.49,
        radius: 6,
        heading: 2.4856,
      },
      // Ember: the lava-lit cave in the volcano's foot.
      {
        id: "ember",
        track: "ember_peak",
        x: 175.46,
        z: 180.26,
        radius: 6,
        heading: -2.0693,
      },
      // Cinderjaw's Scar, up the burnt trench in Ember's south wall: the dragon's race.
      {
        id: "scar",
        track: "boss_prehistoric",
        x: 93,
        z: 187,
        radius: 6,
        heading: Math.PI,
        boss: true,
        label: "CINDERJAW'S SCAR",
      },
    ],
    // (No way out but the smugglers' tunnel, from the Lookout Cave: Blake, Nov 1. The Burnt
    // Gorge Cinderjaw split open is gone.)
    passages: [],
  },
  {
    // The second region (tools/blender/prehistoric/snow_layout.py, snow_region.py): walled
    // pockets like the valley's, the main road one loop through them, a threshold each
    // time: Hearthglow's village (the hub, the Burnt Gorge up into it from the valley), the
    // Gatehouse into Frostveil's bailey, the Climb to the summit meadow, the Ice Cave to the
    // glacier, the Snowshed down to the frozen lake, the Frozen Falls back up to the village.
    // (The positions below are the build's entities.)
    id: "snow_kingdom",
    name: "Snow Kingdom",
    packageId: "snow_region",
    ruinPackageId: "snow_region_ruin",
    // (No secret any more: the Old Store in Frostveil's bailey is gone, Blake, review-snow_region 8:
    // "we arent going to be using it".)
    // The smugglers' Ice Cave: its mouth in the north wall of Aurora's bay, left of the crystal
    // spires (review-snow_region 14 notes 5, 7: it was in the summit meadow).
    cave: {
      gate: { x: 194.0, z: -75.5, heading: 0.0, width: 9 },
      spot: { x: 194.0, z: -86.5 },
    },
    music: "hearthglow",
    worldId: "frostveil",
    kingdom: "snow",
    // The main road's start line, on the village's north side (the 1-on-1 is raced from it).
    challenge: { x: 18, z: 150, heading: -1.7226 },
    // In the ice carvers' village, in the Ice Hollow over the pass, facing in to the Frost
    // Spire.
    spawn: { x: 12, z: 140, heading: Math.PI },
    gateways: [
      // In the village's basin's east wall, at the end of the lane out of the square.
      {
        id: "hearthglow",
        track: "hearthglow_hollow",
        x: -140.74,
        z: 158.23,
        radius: 6,
        heading: 1.9577,
      },
      // At the keep's gate in the bailey's west wall.
      {
        id: "frostveil",
        track: "frostveil_citadel",
        x: -204.12,
        z: -5.66,
        radius: 6,
        heading: 1.7099,
      },
      // At the foot of the giant tree in the summit meadow.
      { id: "summit", track: "snowy_summit", x: -144.08, z: -178.59, radius: 6, heading: 1.4533 },
      // At the rift in the glacier.
      { id: "aurora", track: "aurora_rift", x: 121.83, z: -166.0, radius: 6, heading: -0.0138 },
      // Rimefang's lair, an ice cave in the summit's north wall: the dragon's race.
      {
        id: "lair",
        track: "boss_snowy",
        x: -91.1,
        z: -210.05,
        radius: 6,
        heading: -0.092,
        boss: true,
        label: "RIMEFANG'S LAIR",
      },
    ],
    passages: [
      // Back down the Burnt Gorge to the valley.
      {
        id: "burnt_gorge",
        label: "THE BURNT GORGE · BACK TO DINOSAUR VALLEY",
        to: "journey_gorge",
        toPassage: "end",
        x: -5,
        z: 412,
        radius: 8,
        heading: 1.711,
      },
    ],
  },
  {
    // The third region (tools/blender/prehistoric/desert_layout.py, desert_region.py): walled
    // pockets, the main road one loop through them by a threshold each time: Stego's
    // trading post (the hub, the Frozen Pass down into it from the snow), the Slot (a narrow
    // canyon) to the red canyon, the Arch (a sandstone fin) to the oasis, the Mine to the
    // ghost town, over the Rim into the crater, the Wash back to the post.
    // (The positions below are the build's entities.)
    id: "desert_world",
    name: "Desert World",
    packageId: "desert_region",
    ruinPackageId: "desert_region_ruin",
    // v4, the open Southwest (Blake, Oct 31; tools/blender/prehistoric/mesa_region.py): one
    // open desert floor, its mesas and buttes on it. v4b (Blake, Nov 1: "spread the levels
    // ... further apart", each its own region): the road down into the Grand Canyon onto
    // its terrace, up to Havasu at its head, south over the open floor to the boomtown,
    // down round Meteor Crater's spiral and out, by Scorchwind's rodeo arena, up the Ledge
    // Road and over Sun Arch; zippers on the drives between. (The positions are the build's.)
    // A secret, for the way back: a sunken garden below Havasu, cut off by deep water the Beach Tool gets you over.
    secret: {
      obstacle: "water",
      tool: "beach",
      gate: { x: 431.01, z: -200.42, heading: -1.6172, width: 9 },
      spot: { x: 440, z: -200 },
    },
    // The smugglers' Drift Cave: its mouth in Meteor Crater's inner wall, low on the spiral road,
    // its yard a ledge (review-desert_region note 3: it was behind the trading post).
    cave: {
      gate: { x: 66.96, z: 325.85, heading: 1.3614, width: 9 },
      spot: { x: 62.56, z: 324.92 },
    },
    music: "canyon",
    worldId: "desert",
    kingdom: "desert",
    // The main road's start line, by the frontier town (the 1-on-1 is raced from it).
    challenge: { x: -320, z: 40, heading: -3.0853 },
    // In the frontier town, where the road from the Frozen Pass crosses Main Street, facing east.
    spawn: { x: -360, z: 40, heading: Math.PI / 2 },
    gateways: [
      // Down in the Grand Canyon, in its south wall off the terrace.
      { id: "canyon", track: "canyon_dash", x: 48.63, z: -272.73, radius: 6, heading: -2.6779 },
      // On Havasu's rim over the falls' pool, at the canyon's head.
      { id: "oasis", track: "oasis_haven", x: 370.66, z: -262.07, radius: 6, heading: -0.1116 },
      // Off the boomtown's Main Street, west.
      { id: "gulch", track: "dry_gulch", x: 262, z: 122.17, radius: 6, heading: 1.5565 },
      // Down on Meteor Crater's floor, by the core.
      { id: "impact", track: "impact_depths", x: 113.66, z: 333.92, radius: 6, heading: -2.1026 },
      // Scorchwind's lair: east of where his rodeo stood (review-desert_region 3: the rodeo is gone).
      {
        id: "lair",
        track: "boss_desert",
        x: 157.79,
        z: 171.77,
        radius: 6,
        heading: 1.7579,
        boss: true,
        label: "SCORCHWIND'S LAIR",
      },
    ],
    passages: [
      // Back up the Frozen Pass to the Snow Kingdom (west, through the rim).
      {
        id: "frozen_pass",
        label: "THE FROZEN PASS · BACK TO THE SNOW KINGDOM",
        to: "journey_pass",
        toPassage: "end",
        x: -444,
        z: 40,
        radius: 8,
        heading: Math.PI / 2,
      },
    ],
  },
  {
    // Tropic Isles.
    id: "tropic_isles",
    name: "Tropic Isles",
    // v5 (Blake, Nov 1: "i want to also travel through the island. not just around it ...
    // homeomorphic to a figure 8"; "all of the areas containing the levels need to be their
    // own sub world"): the island (tools/blender/prehistoric/isle_layout.py, isle_region.py),
    // the road a figure eight through it, crossing at the High Bridge over the river gorge;
    // each part its own basin walled by jungle ridges. The island hop comes in over the east
    // bay to Raptor's stilt village. (The positions below are the build's entities.)
    packageId: "beach_region",
    ruinPackageId: "beach_region_ruin",
    // A secret, for the way back: a hidden cove behind the Black Shore, behind a rockfall the Valley Tool shifts.
    secret: {
      obstacle: "rockfall",
      tool: "valley",
      gate: { x: 81.7, z: -297.22, heading: -0.3051, width: 9 },
      spot: { x: 84.4, z: -305.8 },
    },
    // The smugglers' Sea Cave, Raptor's old haunt: its yard on the beach under Smugglers'
    // Point, on the west coast.
    cave: {
      gate: { x: -272.01, z: 90.27, heading: 2.1386, width: 9 },
      spot: { x: -281.28, z: 96.19 },
    },
    music: "coral_cove",
    worldId: "beach",
    kingdom: "beach",
    // The main road's start line, west of the village square (the 1-on-1 is raced from it).
    challenge: { x: 204.0, z: -40.0, heading: 0.0015 },
    // On the village square's boardwalk, facing west to the road.
    spawn: { x: 252, z: -30, heading: -1.5708 },
    gateways: [
      // Coral Cove: on the cove's beach, a short path off the road, the reef off it.
      { id: "coral", track: "coral_cove", x: 148.61, z: 187.11, radius: 6, heading: -2.852 },
      // Shipwreck Bay: down its beach toward the galleon.
      { id: "wreck", track: "shipwreck_bay", x: -264.5, z: -135.71, radius: 6, heading: 0.995 },
      // The Black Shore: under the obsidian arch, toward Volcano Isle smoking offshore.
      { id: "volcano", track: "volcano_isle", x: 30.97, z: -300.29, radius: 6, heading: -0.0029 },
      // The Jungle Heart: at the foot of the old temple's steps.
      {
        id: "rainforest",
        track: "rainforest_rush",
        x: 54.21,
        z: 22.96,
        radius: 6,
        heading: -2.9592,
      },
      // Tidewyrm's lair: his sea cave in the Head's south cliff, off Coral Cove.
      {
        id: "lair",
        track: "boss_tropic",
        x: 198.79,
        z: 163.57,
        radius: 6,
        heading: -2.4494,
        boss: true,
        label: "TIDEWYRM'S LAIR",
      },
    ],
    passages: [
      // Back over the island hop to Desert World: the pier's end, east over the bay (the
      // pier just runs on: no arch over it).
      {
        id: "dust_road",
        label: "THE ISLAND HOP · BACK TO DESERT WORLD",
        to: "journey_dust",
        toPassage: "end",
        x: 442,
        z: -26,
        radius: 8,
        heading: -1.5923,
        look: "open",
      },
      // (No sea door to the last tunnel any more: to the Dragon Kingdom and back through the
      // smugglers' Sea Cave, like every kingdom; review-beach_region notes 1, 2.)
    ],
  },
  {
    // The last region, v4 (Blake, Oct 31: "the most breathtaking kingdom by far"; built for
    // dragons, floating isles and sky bridges; tools/blender/prehistoric/sky_layout.py,
    // sky_region.py): isles of rock hanging over a sea of cloud on chains of dragon light,
    // round the Citadel's spire. In through the Sky Gate onto the Gate isle, over its bridge
    // to the Crown (Dragonfire Square, the avenue of giant steps up to the Citadel's door);
    // the road climbs the isles round the spire on sky bridges. Ruined after the sacrifice
    // (the end of its first championship). (The positions below are the build's.)
    id: "dragon_kingdom",
    name: "Dragon Kingdom",
    packageId: "dragon_region",
    ruinPackageId: "dragon_region_ruin",
    music: "dragon",
    worldId: "dragon",
    kingdom: "dragon",
    // On the road just south of Dragonfire Square, westbound (Blake, Oct 31: the old spot,
    // on the square, was inside the great dragon's statue).
    spawn: { x: 0, z: 132, heading: -Math.PI / 2 },
    gateways: [
      // In the castle's Dragonspire wing, a great door in its hall's wall, west.
      { id: "keep", track: "dragon_isles", x: -340.97, z: 27.89, radius: 6, heading: -0.5225 },
      // In the jungle-swallowed wing's hall (trees through its roof), east.
      { id: "canyon", track: "dragon_canyon", x: 357.05, z: 44.58, radius: 6, heading: 1.4449 },
      // In Emberdeep's forge hall, furnaces glowing, lava running, north-east.
      { id: "hold", track: "snow_dragon_pass", x: 195.62, z: -313.63, radius: 6, heading: -0.5677 },
      // In the moon temple's court, open to the stars, the highest wing, north-west.
      {
        id: "moon",
        track: "celestial_dragon_festival",
        x: -180.56,
        z: -315.23,
        radius: 6,
        heading: -2.6608,
      },
      // King Pyrrhax's Citadel: its forty-metre door in the spire's foot, up the avenue.
      {
        id: "citadel",
        track: "boss_dragon",
        x: 1.95,
        z: -14.12,
        radius: 6,
        heading: 0.1223,
        king: true,
        label: "KING PYRRHAX'S CITADEL",
      },
    ],
    passages: [
      // Back over the Sky Bridge, the edge of the world and the smugglers' tunnel to Tropic Isles.
      {
        id: "causeway",
        label: "THE SKY BRIDGE · BACK TO TROPIC ISLES",
        to: "journey_cause",
        toPassage: "end",
        look: "open",
        x: 0,
        z: 424,
        radius: 8,
        heading: Math.PI,
      },
    ],
  },
  {
    // Cinderjaw's burnt trench out of the valley, up out of the heat into the first snow: the scorched gorge and its lava pools, the Ash Tube, the Stair's switchbacks, the frosty Frostline and Frost Creek, the Snow Arch, the Snowgate.
    // (tools/blender/prehistoric/journey_region.py gorge; the positions are the build's.)
    id: "journey_gorge",
    name: "The Burnt Gorge",
    packageId: "journey_gorge",
    music: "journey_gorge",
    worldId: "prehistoric",
    journey: { from: "valley", to: "snow", road: [35, 1595] },
    spawn: { x: -381.1, z: 332.6, heading: 2.8418 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE BURNT GORGE · BACK TO DINOSAUR VALLEY",
        to: "dinosaur_valley",
        // (Back through the smugglers' tunnel: out of its cave, Blake, Nov 1.)
        toPassage: "cave",
        x: -385,
        z: 345,
        radius: 8,
        heading: 2.8418,
      },
      {
        id: "end",
        label: "THE BURNT GORGE · ON TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        toPassage: "burnt_gorge",
        x: 330,
        z: -448,
        radius: 8,
        heading: 0.3844,
      },
    ],
  },
  {
    // Down out of the snow into the heat: the Col, the Ice Cave, the Glacier's seracs, the Melt's switchbacks and falls, the Red Cut's slot, the desert's Edge.
    // (tools/blender/prehistoric/journey_region.py pass; the positions are the build's.)
    id: "journey_pass",
    name: "The Frozen Pass",
    packageId: "journey_pass",
    music: "journey_pass",
    worldId: "frostveil",
    journey: { from: "snow", to: "desert", road: [59, 1344] },
    spawn: { x: -361.1, z: -348.7, heading: 0.5877 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE FROZEN PASS · BACK TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        // (Back through the smugglers' tunnel: out of its cave, Blake, Nov 1.)
        toPassage: "cave",
        x: -370,
        z: -362,
        radius: 8,
        heading: 0.5877,
      },
      {
        id: "end",
        label: "THE FROZEN PASS · ON TO DESERT WORLD",
        to: "desert_world",
        toPassage: "frozen_pass",
        x: 368,
        z: 368,
        radius: 8,
        heading: -2.6324,
      },
    ],
  },
  {
    // The island hop (Blake, Nov 1): out of the desert's smugglers' tunnel at a sea cave dock, over Sandbar Key, the causeway, Mangrove Cay, Fishers' Isle, Turtle Rocks and Palm Cay, the long pier to Tropic Isles.
    // (tools/blender/prehistoric/journey_region.py hop (its package keeps the Dust Road's id); the positions are the build's.)
    id: "journey_dust",
    name: "The Island Hop",
    packageId: "journey_dust",
    music: "journey_dust",
    worldId: "beach",
    journey: { from: "desert", to: "beach", road: [35, 1864] },
    spawn: { x: -398.2, z: 391.2, heading: 2.3153 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE SMUGGLERS' TUNNEL · BACK TO DESERT WORLD",
        to: "desert_world",
        // (Back through the smugglers' tunnel: out of its cave, Blake, Nov 1.)
        toPassage: "cave",
        x: -410,
        z: 402,
        radius: 8,
        heading: 2.3153,
      },
      {
        id: "end",
        label: "THE ISLAND HOP · ON TO TROPIC ISLES",
        to: "tropic_isles",
        toPassage: "dust_road",
        look: "open",
        x: 430,
        z: -262,
        radius: 8,
        heading: -1.4599,
      },
    ],
  },
  {
    // The last smugglers' tunnel, driven (v4, Blake, Nov 2: "completely rework it. it should
    // be crawling with black market activity"; a chain of districts): in from the isles' sea
    // door, the Smugglers' Docks (over the canal's hump-backed bridge), Smugglers' Alley and
    // the Stair down into the Night Bazaar (the Broker's ship over it), the corkscrew down
    // the Fighting Pits' stands, the Lucky Bone (the gambling den), the Long Bore out through
    // the sea falling off the world's edge onto the Edge Bridge, then the Sky Islands'
    // chained bridges to the Dragon Kingdom's Sky Gate. No jumps (Nov 3: it drives both
    // ways).
    // (tools/blender/prehistoric/jedge_region.py; the positions are the build's.)
    id: "journey_cause",
    name: "The Edge of the World",
    packageId: "journey_cause",
    music: "journey_cause",
    worldId: "beach",
    journey: { from: "beach", to: "dragon", road: [53, 1462] },
    // (Underground: the ground's looked for from just over the tunnel's floor, not the sky.)
    spawn: { x: -52.1, z: 415, heading: 2.7919, y: -12 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE SMUGGLERS' TUNNEL · BACK TO TROPIC ISLES",
        to: "tropic_isles",
        // (Back out of the smugglers' Sea Cave.)
        toPassage: "cave",
        x: -60,
        z: 440,
        radius: 8,
        heading: 2.9115,
        y: -12,
      },
      {
        id: "end",
        label: "THE SKY GATE · ON TO THE DRAGON KINGDOM",
        to: "dragon_kingdom",
        toPassage: "causeway",
        look: "open",
        x: 0,
        z: -445,
        radius: 8,
        heading: 0.4029,
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

/** Where a region sits in the story's order (src/adventure/data.ts STORY_ORDER, as an
 * index): a kingdom's, or halfway between for a journey. */
export function storyPlace(r: Region, order: readonly KingdomId[]): number {
  if (r.kingdom) return order.indexOf(r.kingdom);
  if (r.journey) return (order.indexOf(r.journey.from) + order.indexOf(r.journey.to)) / 2;
  return -1;
}

/** What of the region is there in its standard or ruined state: the lairs and the ways
 * the dragons broke open only after the attack. */
export const regionAsIs = (r: Region, ruined: boolean): Region => ({
  ...r,
  gateways: r.gateways.filter((g) => ruined || !g.boss),
  passages: (r.passages ?? []).filter((p) => ruined || !p.ruinOnly),
});

/** The region an Adventure kingdom is driven in, once it's built. */
export const regionOfKingdom = (k: KingdomId) => REGIONS.find((r) => r.kingdom === k);

/** Is (x, z) inside the gateway's trigger (by `extra` metres more)? */
export const inGateway = (
  g: { x: number; z: number; radius: number },
  x: number,
  z: number,
  extra = 0,
) => Math.hypot(x - g.x, z - g.z) < g.radius + extra;
