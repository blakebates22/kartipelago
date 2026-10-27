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
import type { Puzzle } from "./puzzles";

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
  /** Adventure: it opens once this kingdom's dragon has fallen (dev free roam: always). */
  opensAfter?: KingdomId;
  /** What's in the way until then. */
  locked?: string;
  /** What stands across the way on until then, on the passage itself (shown, solid, and
   * the passage won't open; it breaks open the first time you come back after the dragon
   * falls). */
  blocker?: { kind: ObstacleKind | "fire"; width: number };
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
  spawn: { x: number; z: number; heading: number };
  gateways: Gateway[];
  passages?: Passage[];
  /** Adventure: where the champion waits to race you 1 on 1 once round the ring (beside
   * its start line; game/tracks.ts has the region as a race under its package's id). */
  challenge?: { x: number; z: number; heading: number };
  /** Its switches and puzzles (src/overworld/puzzles.ts). */
  puzzles?: Puzzle[];
  /** Act V: where the kingdom's return task happens, in a walled yard whose way in is
   * blocked by an obstacle the kingdom's own tool clears (the overworld doc's tool
   * gates: each tool opens one kind of obstacle). */
  returnTask?: ReturnSpot;
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
      gate: { x: 216.5, z: -155.04, heading: 1.2356, width: 9 },
      spot: { x: 208, z: -158 },
    },
    // Act V's return task: The Elder's lookout, a walled hollow on Ember's lower slope: a rockfall blocks its way in.
    returnTask: {
      obstacle: "rockfall",
      gate: { x: 136.84, z: 172.15, heading: 1.7395, width: 9 },
      spot: { x: 126, z: 174 },
    },
    music: "riverbend",
    worldId: "prehistoric",
    kingdom: "valley",
    // The main road's start line, on the camp's south side (the 1-on-1 is raced from it).
    challenge: { x: 36, z: 30, heading: -0.9043 },
    // In the camp's square, facing east to the way out onto the road.
    spawn: { x: -6, z: -4, heading: Math.PI / 2 },
    gateways: [
      // Riverbend: the palms on the bend's far bank, by the falls out of the north cliff.
      {
        id: "riverbend",
        track: "riverbend_palms",
        x: -318.58,
        z: -116.31,
        radius: 6,
        heading: 1.2584,
      },
      // Cascade: the cave mouth beside the falls, at the canyon's head.
      {
        id: "cascade",
        track: "cascade_caverns",
        x: 288.78,
        z: -295.76,
        radius: 6,
        heading: -1.2093,
      },
      // Bonebog: the pyramid's tip, out in the swamp's far corner.
      {
        id: "bonebog",
        track: "bonebog_pyramid",
        x: -264.69,
        z: 292.49,
        radius: 6,
        heading: 2.4864,
      },
      // Ember: the lava-lit cave in the volcano's foot.
      {
        id: "ember",
        track: "ember_peak",
        x: 289.42,
        z: 294.33,
        radius: 6,
        heading: -2.0626,
      },
      // Cinderjaw's Scar, up the burnt trench in Ember's south wall: the dragon's race.
      {
        id: "scar",
        track: "boss_prehistoric",
        x: 150,
        z: 312,
        radius: 6,
        heading: Math.PI,
        boss: true,
        label: "CINDERJAW'S SCAR",
      },
    ],
    passages: [
      // The Burnt Gorge, through Riverbend's north cliff: on to the Snow Kingdom.
      {
        id: "burnt_gorge",
        label: "THE BURNT GORGE · TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        toPassage: "burnt_gorge",
        x: -155.4,
        z: -420,
        radius: 8,
        heading: 0,
        ruinOnly: true,
        blocker: { kind: "fire", width: 30 },
        opensAfter: "valley",
        locked: "CINDERJAW'S FIRE SPLIT THE CLIFF, BUT THE GORGE STILL BURNS: BEAT HIM FIRST",
      },
    ],
    puzzles: [
      // The Three Stones: an old stone pen in the camp's north meadow, its gate shut. Press
      // the three switch stones round the camp before the drums stop and the gate sinks.
      // Behind it: the valley's hidden key. (The build's puzzle_gate and puzzle_switch
      // entities are checked against these in tests/overworld.test.ts.)
      {
        id: "three_stones",
        label: "THE THREE STONES",
        look: "stone",
        hint: "THE THREE STONES! PRESS THE OTHER 2 BEFORE THE DRUMS STOP",
        switches: [
          { x: -58, z: -34 },
          { x: 22, z: -54 },
          { x: -36, z: -14 },
        ],
        radius: 3.5,
        seconds: 30,
        gate: { x: -12.14, z: -58.34, heading: 1.4042, width: 9 },
        prize: { kind: "key", x: -22, z: -60 },
      },
    ],
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
    // A secret, for the way back: an old store in Frostveil's bailey, buried under a drift the Desert Tool blows away.
    secret: {
      obstacle: "drift",
      tool: "desert",
      gate: { x: -203.43, z: 98.85, heading: -1.929, width: 9 },
      spot: { x: -195, z: 102 },
    },
    // Act V's return task: Brachio's hot spring, a walled yard in the summit meadow: its way in is frozen shut.
    returnTask: {
      obstacle: "ice",
      gate: { x: -91.36, z: -265.22, heading: 1.315, width: 9 },
      spot: { x: -102, z: -268 },
    },
    music: "hearthglow",
    worldId: "frostveil",
    kingdom: "snow",
    // The main road's start line, on the village's north side (the 1-on-1 is raced from it).
    challenge: { x: 25, z: 205, heading: -1.7204 },
    // In the village square, facing north to the road.
    spawn: { x: 0, z: 250, heading: Math.PI },
    gateways: [
      // By the village's great tree.
      {
        id: "hearthglow",
        track: "hearthglow_hollow",
        x: -59.53,
        z: 193.14,
        radius: 6,
        heading: 0.382,
      },
      // At the keep's gate in the bailey's west wall.
      {
        id: "frostveil",
        track: "frostveil_citadel",
        x: -332.64,
        z: 54.5,
        radius: 6,
        heading: 2.246,
      },
      // At the foot of the giant tree in the summit meadow.
      { id: "summit", track: "snowy_summit", x: -243.28, z: -278.06, radius: 6, heading: 0.595 },
      // At the rift in the glacier.
      { id: "aurora", track: "aurora_rift", x: 306.8, z: -99.69, radius: 6, heading: -1.203 },
      // Rimefang's lair, an ice cave in the summit's north wall: the dragon's race.
      {
        id: "lair",
        track: "boss_snowy",
        x: -118.43,
        z: -309.46,
        radius: 6,
        heading: -0.779,
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
        x: 0,
        z: 462,
        radius: 8,
        heading: Math.PI,
      },
      // The Frozen Pass, east out of the lake: on to Desert World.
      {
        id: "frozen_pass",
        label: "THE FROZEN PASS · TO DESERT WORLD",
        to: "desert_world",
        toPassage: "frozen_pass",
        x: 400,
        z: 190,
        radius: 8,
        heading: -Math.PI / 2,
        ruinOnly: true,
        blocker: { kind: "ice", width: 13 },
        opensAfter: "snow",
        locked: "RIMEFANG'S ICE WALLS THE PASS SHUT: BEAT HIM FIRST",
      },
    ],

    puzzles: [
      // The Ice Bells: a frost-stone hut on an island in the frozen lake, its ice door shut.
      // Ring the three bells out on the ice in order; the clue is their lanterns (one, two,
      // three). A wrong bell and they all go quiet. Behind the door: the kingdom's hidden key.
      {
        id: "ice_bells",
        label: "THE ICE BELLS",
        look: "bell",
        hint: "RING THE BELLS FROM THE FEWEST LANTERNS TO THE MOST",
        ordered: true,
        switches: [
          { x: 90, z: 60, lanterns: 1 },
          { x: 150, z: 112, lanterns: 2 },
          { x: 104, z: 132, lanterns: 3 },
        ],
        radius: 3.5,
        seconds: 0,
        gate: { x: 127.89, z: 90.5, heading: 1.722, width: 9 },
        prize: { kind: "key", x: 118, z: 92 },
      },
    ],
  },
  {
    // The doc's third region (tools/blender/prehistoric/desert_region.py, a greybox): a
    // red-rock basin ringed by mesas, a meteor crater in the middle, Stego's trading post
    // by the Frozen Pass.
    id: "desert_world",
    name: "Desert World",
    packageId: "desert_region",
    ruinPackageId: "desert_region_ruin",
    // A secret, for the way back: a sunken garden in the north, cut off by deep water the Beach Tool gets you over.
    secret: {
      obstacle: "water",
      tool: "beach",
      gate: { x: 75.32, z: -281.08, heading: -0.2618, width: 9 },
      spot: { x: 77.65, z: -289.78 },
    },
    // Act V's return task: Stego's old well, a walled yard in the north-west: a drift buries its way in.
    returnTask: {
      obstacle: "drift",
      gate: { x: -236.73, z: -165.76, heading: 0.9599, width: 9 },
      spot: { x: -245.75, z: -172.07 },
    },
    music: "canyon",
    worldId: "desert",
    kingdom: "desert",
    challenge: { x: 250, z: 0, heading: -Math.PI / 2 },
    // At the trading post, facing east to the ring.
    spawn: { x: -290, z: 0, heading: Math.PI / 2 },
    gateways: [
      // At the slot canyon in the north cliff.
      {
        id: "canyon",
        track: "canyon_dash",
        x: -56.8,
        z: -322.0,
        radius: 6,
        heading: Math.atan2(-Math.cos((100 * Math.PI) / 180), Math.sin((100 * Math.PI) / 180)),
      },
      // On the lawn by the palm-ringed pool, north-east.
      {
        id: "oasis",
        track: "oasis_haven",
        x: 200.7,
        z: -168.4,
        radius: 6,
        heading: Math.atan2(-Math.cos((40 * Math.PI) / 180), Math.sin((40 * Math.PI) / 180)),
      },
      // At the end of the ghost town's false-front street, south-east.
      {
        id: "gulch",
        track: "dry_gulch",
        x: 222.9,
        z: 187.1,
        radius: 6,
        heading: Math.atan2(-Math.cos((-40 * Math.PI) / 180), Math.sin((-40 * Math.PI) / 180)),
      },
      // On the crater's rim in the middle of the basin.
      { id: "impact", track: "impact_depths", x: -60, z: 0, radius: 6, heading: -Math.PI / 2 },
      // Scorchwind's lair: a rock arch in the south-west cliff, the dust devil before it.
      {
        id: "lair",
        track: "boss_desert",
        x: -231.2,
        z: 231.2,
        radius: 6,
        heading: Math.atan2(-Math.cos((-135 * Math.PI) / 180), Math.sin((-135 * Math.PI) / 180)),
        boss: true,
        label: "SCORCHWIND'S LAIR",
      },
    ],
    passages: [
      // Back up the Frozen Pass to the Snow Kingdom.
      {
        id: "frozen_pass",
        label: "THE FROZEN PASS · BACK TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        toPassage: "frozen_pass",
        x: -445,
        z: 0,
        radius: 8,
        heading: Math.PI / 2,
      },
      // The Dust Road south, under Scorchwind's drifts: on to Tropic Isles.
      {
        id: "dust_road",
        label: "THE DUST ROAD · TO TROPIC ISLES",
        to: "tropic_isles",
        toPassage: "dust_road",
        x: 0,
        z: 327,
        radius: 8,
        heading: Math.PI,
        ruinOnly: true,
        blocker: { kind: "drift", width: 13 },
        opensAfter: "desert",
        locked: "SCORCHWIND'S DRIFTS BURY THE DUST ROAD: BEAT HIM FIRST",
      },
    ],
    puzzles: [
      // The Crater Stones: a sandstone vault on the crater's floor, its gate looking west
      // up the road in. Press the four stones round the crater within 30 seconds.
      {
        id: "crater_stones",
        label: "THE CRATER STONES",
        look: "stone",
        hint: "THE CRATER STONES! PRESS THE OTHER 3 BEFORE THE DRUMS STOP",
        switches: [
          { x: -52.33, z: -52.33 },
          { x: 52.33, z: -52.33 },
          { x: 52.33, z: 52.33 },
          { x: -52.33, z: 52.33 },
        ],
        radius: 3.5,
        seconds: 30,
        gate: { x: -8, z: 0, heading: -Math.PI / 2, width: 9 },
        prize: { kind: "key", x: 0, z: 0 },
      },
    ],
  },
  {
    // The doc's fourth region (tools/blender/prehistoric/beach_region.py, a greybox): an
    // island, jungle hills round the north, a long beach round the south into the
    // shallows, a lagoon in the middle, Raptor's boardwalk village where the Dust Road
    // comes in.
    id: "tropic_isles",
    name: "Tropic Isles",
    packageId: "beach_region",
    ruinPackageId: "beach_region_ruin",
    // A secret, for the way back: a smugglers' cave in the north, behind a rockfall the Valley Tool shifts.
    secret: {
      obstacle: "rockfall",
      tool: "valley",
      gate: { x: -89.92, z: -276.76, heading: 0.3142, width: 9 },
      spot: { x: -92.71, z: -285.32 },
    },
    // Act V's return task: Raptor's cove, a walled yard in the west: a deep channel cuts off its way in.
    returnTask: {
      obstacle: "water",
      gate: { x: -287.9, z: -25.19, heading: 1.4835, width: 9 },
      spot: { x: -298.86, z: -26.15 },
    },
    music: "coral_cove",
    worldId: "beach",
    kingdom: "beach",
    challenge: { x: 250, z: 0, heading: -Math.PI / 2 },
    // In the village, facing south to the ring.
    spawn: { x: 0, z: -290, heading: 0 },
    gateways: [
      // On the beach by the coral heads, south-east.
      {
        id: "coral",
        track: "coral_cove",
        x: 224.4,
        z: 157.2,
        radius: 6,
        heading: Math.atan2(-Math.cos((-35 * Math.PI) / 180), Math.sin((-35 * Math.PI) / 180)),
      },
      // At the end of the pier, pointing out to the smoking island offshore.
      { id: "volcano", track: "volcano_isle", x: 0, z: 343, radius: 6, heading: Math.PI },
      // By the wrecked hull on the beach, south-west.
      {
        id: "wreck",
        track: "shipwreck_bay",
        x: -226.1,
        z: 158.3,
        radius: 6,
        heading: Math.atan2(-Math.cos((-145 * Math.PI) / 180), Math.sin((-145 * Math.PI) / 180)),
      },
      // At the water park's slide tower against the hills, north-west.
      {
        id: "splash",
        track: "splash_lagoon",
        x: -252.0,
        z: -145.5,
        radius: 6,
        heading: Math.atan2(-Math.cos((150 * Math.PI) / 180), Math.sin((150 * Math.PI) / 180)),
      },
      // Tidewyrm's lair: a sea cave in the east headland.
      {
        id: "lair",
        track: "boss_tropic",
        x: 323.8,
        z: -45.5,
        radius: 6,
        heading: Math.atan2(-Math.cos((8 * Math.PI) / 180), Math.sin((8 * Math.PI) / 180)),
        boss: true,
        label: "TIDEWYRM'S LAIR",
      },
    ],
    passages: [
      // Back up the Dust Road to Desert World.
      {
        id: "dust_road",
        label: "THE DUST ROAD · BACK TO DESERT WORLD",
        to: "desert_world",
        toPassage: "dust_road",
        x: 0,
        z: -445,
        radius: 8,
        heading: 0,
      },
      // Tidewyrm's Causeway, out through the sea stacks: on to the Dragon Kingdom.
      {
        id: "causeway",
        label: "TIDEWYRM'S CAUSEWAY · TO THE DRAGON KINGDOM",
        to: "dragon_kingdom",
        toPassage: "causeway",
        x: 199.0,
        z: 344.7,
        radius: 8,
        heading: Math.atan2(-0.5, -0.866),
        ruinOnly: true,
        blocker: { kind: "water", width: 14 },
        opensAfter: "beach",
        locked: "THE REEF LIES UNDER DEEP WATER, HELD DOWN BY TIDEWYRM: BEAT HIM FIRST",
      },
    ],
    puzzles: [
      // The Tiki Gongs: a tiki hut in the north-east, its door shut. Strike the three
      // gongs in order; the clue is their torches (one in the north-west, two on the east
      // beach, three on the south-west beach). A wrong gong and they all go quiet.
      {
        id: "tiki_gongs",
        label: "THE TIKI GONGS",
        look: "gong",
        hint: "STRIKE THE GONGS FROM THE FEWEST TORCHES TO THE MOST",
        ordered: true,
        switches: [
          { x: -127.5, z: -220.84, lanterns: 1 },
          { x: 246.2, z: 43.41, lanterns: 2 },
          { x: -122.5, z: 212.18, lanterns: 3 },
        ],
        radius: 3.5,
        seconds: 0,
        gate: { x: 205.06, z: -205.06, heading: -Math.PI / 4, width: 9 },
        prize: { kind: "key", x: 212.13, z: -212.13 },
      },
    ],
  },
  {
    // The last region (tools/blender/prehistoric/dragon_region.py, a greybox): far over
    // the horizon at the end of Tidewyrm's Causeway. A green basin ringed by dark crags,
    // Dragonfire Square in the middle, King Pyrrhax's Citadel on the north cliff. Ruined
    // after the sacrifice (the end of its first championship).
    id: "dragon_kingdom",
    name: "Dragon Kingdom",
    packageId: "dragon_region",
    ruinPackageId: "dragon_region_ruin",
    music: "dragon",
    worldId: "dragon",
    kingdom: "dragon",
    // At the harbour where the Causeway comes in, facing north to the ring.
    spawn: { x: 0, z: 285, heading: Math.PI },
    gateways: [
      // At the gate under Dragonspire Keep's tower on its crag, north-west.
      {
        id: "keep",
        track: "dragon_isles",
        x: -219.1,
        z: -183.8,
        radius: 6,
        heading: Math.atan2(-Math.cos((140 * Math.PI) / 180), Math.sin((140 * Math.PI) / 180)),
      },
      // At the overgrown jungle castle's gate in the east cliff.
      {
        id: "canyon",
        track: "dragon_canyon",
        x: 322.0,
        z: -56.8,
        radius: 6,
        heading: Math.atan2(-Math.cos((10 * Math.PI) / 180), Math.sin((10 * Math.PI) / 180)),
      },
      // At Emberdeep Hold's fortress gate cut into the mountain, north-east.
      {
        id: "hold",
        track: "snow_dragon_pass",
        x: 187.6,
        z: -267.9,
        radius: 6,
        heading: Math.atan2(-Math.cos((55 * Math.PI) / 180), Math.sin((55 * Math.PI) / 180)),
      },
      // Before the moon gate among the violet lanterns, west.
      {
        id: "moon",
        track: "celestial_dragon_festival",
        x: -259.4,
        z: 94.4,
        radius: 6,
        heading: Math.atan2(-Math.cos((200 * Math.PI) / 180), Math.sin((200 * Math.PI) / 180)),
      },
      // King Pyrrhax's Citadel on the north cliff: the King's race.
      {
        id: "citadel",
        track: "boss_dragon",
        x: -56.8,
        z: -322.0,
        radius: 6,
        heading: Math.atan2(-Math.cos((100 * Math.PI) / 180), Math.sin((100 * Math.PI) / 180)),
        king: true,
        label: "KING PYRRHAX'S CITADEL",
      },
    ],
    passages: [
      // Back along Tidewyrm's Causeway to Tropic Isles.
      {
        id: "causeway",
        label: "TIDEWYRM'S CAUSEWAY · BACK TO TROPIC ISLES",
        to: "tropic_isles",
        toPassage: "causeway",
        x: 0,
        z: 445,
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
