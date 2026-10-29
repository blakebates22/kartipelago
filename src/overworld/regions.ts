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
  /** A journey between two kingdoms, its own section (Blake, Oct 26: a loading zone at a
   * kingdom's edge, the connecting stretch driven to the next one's): no gateways, a way
   * in at each end (its passages "start", from `from`, and "end", to `to`). `road`: the
   * stretch of its route that's road (the rest goes round out of sight). */
  journey?: { from: KingdomId; to: KingdomId; road: [number, number] };
  spawn: { x: number; z: number; heading: number };
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
    passages: [
      // The Burnt Gorge, through Riverbend's north cliff: on to the Snow Kingdom.
      {
        id: "burnt_gorge",
        label: "THE BURNT GORGE · TO THE SNOW KINGDOM",
        to: "journey_gorge",
        toPassage: "start",
        x: -96.8,
        z: -270,
        radius: 8,
        heading: 0,
        ruinOnly: true,
        blocker: { kind: "fire", width: 30 },
        opensAfter: "valley",
        locked: "CINDERJAW'S FIRE SPLIT THE CLIFF, BUT THE GORGE STILL BURNS: BEAT HIM FIRST",
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
      gate: { x: -126.71, z: 70.07, heading: -0.7017, width: 9 },
      spot: { x: -120.9, z: 63.2 },
    },
    // The smugglers' Ice Cave: a walled yard in the summit meadow, round Brachio's old hot spring.
    cave: {
      gate: { x: -52.56, z: -163.42, heading: 1.315, width: 9 },
      spot: { x: -63.2, z: -166.2 },
    },
    music: "hearthglow",
    worldId: "frostveil",
    kingdom: "snow",
    // The main road's start line, on the village's north side (the 1-on-1 is raced from it).
    challenge: { x: 16, z: 127, heading: -1.7226 },
    // In the village square, facing north to the road.
    spawn: { x: 0, z: 155, heading: Math.PI },
    gateways: [
      // In the hollow's west wall, at the end of the lane out of the square.
      {
        id: "hearthglow",
        track: "hearthglow_hollow",
        x: -45.0,
        z: 150.72,
        radius: 6,
        heading: 1.5484,
      },
      // At the keep's gate in the bailey's west wall.
      {
        id: "frostveil",
        track: "frostveil_citadel",
        x: -201.95,
        z: 31.84,
        radius: 6,
        heading: 2.149,
      },
      // At the foot of the giant tree in the summit meadow.
      { id: "summit", track: "snowy_summit", x: -148.63, z: -168.43, radius: 6, heading: 0.5596 },
      // At the rift in the glacier.
      { id: "aurora", track: "aurora_rift", x: 187.09, z: -58.03, radius: 6, heading: -1.0015 },
      // Rimefang's lair, an ice cave in the summit's north wall: the dragon's race.
      {
        id: "lair",
        track: "boss_snowy",
        x: -107.6,
        z: -184.28,
        radius: 6,
        heading: -0.218,
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
        x: 0,
        z: 283,
        radius: 8,
        heading: Math.PI,
      },
      // The Frozen Pass, east out of the lake: on to Desert World.
      {
        id: "frozen_pass",
        label: "THE FROZEN PASS · TO DESERT WORLD",
        to: "journey_pass",
        toPassage: "start",
        x: 244,
        z: 117.8,
        radius: 8,
        heading: -1.692, // (along the Frozen Pass Road, west down to the lake)
        ruinOnly: true,
        blocker: { kind: "ice", width: 13 },
        opensAfter: "snow",
        locked: "RIMEFANG'S ICE WALLS THE PASS SHUT: BEAT HIM FIRST",
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
    // A secret, for the way back: a sunken garden in the oasis, cut off by deep water the Beach Tool gets you over.
    secret: {
      obstacle: "water",
      tool: "beach",
      gate: { x: 168.74, z: -126.04, heading: -0.7382, width: 9 },
      spot: { x: 174.8, z: -132.7 },
    },
    // The smugglers' Drift Cave: a walled yard behind the trading post, round Stego's old well.
    cave: {
      gate: { x: -172.5, z: 17.5, heading: 1.5621, width: 9 },
      spot: { x: -183.5, z: 17.4 },
    },
    music: "canyon",
    worldId: "desert",
    kingdom: "desert",
    // The main road's start line, on the post's east side (the 1-on-1 is raced from it).
    challenge: { x: -146, z: 6, heading: 3.0636 },
    // In the trading post's square, facing east to the road.
    spawn: { x: -167.4, z: 0, heading: Math.PI / 2 },
    gateways: [
      // At the slot canyon's mouth in the canyon's north wall.
      { id: "canyon", track: "canyon_dash", x: -40.75, z: -188.14, radius: 6, heading: -0.3006 },
      // In the palm grove by the spring.
      { id: "oasis", track: "oasis_haven", x: 183.97, z: -99.17, radius: 6, heading: -0.9034 },
      // At the end of the ghost town's false-front street.
      { id: "gulch", track: "dry_gulch", x: 137.23, z: 135.37, radius: 6, heading: -2.0975 },
      // By the meteorite in the crater's floor.
      { id: "impact", track: "impact_depths", x: -12.97, z: 149.31, radius: 6, heading: 1.737 },
      // Scorchwind's lair: a rock arch in the canyon's west wall.
      {
        id: "lair",
        track: "boss_desert",
        x: -109.01,
        z: -159.23,
        radius: 6,
        heading: 0.822,
        boss: true,
        label: "SCORCHWIND'S LAIR",
      },
    ],
    passages: [
      // Back up the Frozen Pass to the Snow Kingdom.
      {
        id: "frozen_pass",
        label: "THE FROZEN PASS · BACK TO THE SNOW KINGDOM",
        to: "journey_pass",
        toPassage: "end",
        x: -279,
        z: 0,
        radius: 8,
        heading: Math.PI / 2,
      },
      // The Dust Road south out of the crater, under Scorchwind's drifts: on to Tropic Isles.
      {
        id: "dust_road",
        label: "THE DUST ROAD · TO TROPIC ISLES",
        to: "journey_dust",
        toPassage: "start",
        x: 0,
        z: 270,
        radius: 8,
        heading: Math.PI,
        ruinOnly: true,
        blocker: { kind: "drift", width: 13 },
        opensAfter: "desert",
        locked: "SCORCHWIND'S DRIFTS BURY THE DUST ROAD: BEAT HIM FIRST",
      },
    ],
  },
  {
    // Tropic Isles (tools/blender/prehistoric/beach_region.py), v3: a pocket for each of
    // its worlds walled off by jungle hills and rocky headlands, the main road one loop
    // through them (Raptor's 1-on-1) by a threshold each time: Raptor's village on its
    // plateau (the hub, the Dust Road down into it from the desert), the Vine Tunnel to
    // the water park, behind the Falls to the shipwreck cove, through the Hull to the
    // pier's cove, the Sea Arch to the coral cove, the Mangroves to the lagoon, up the
    // Tiki Steps back to the village. (The positions below are the build's entities.)
    id: "tropic_isles",
    name: "Tropic Isles",
    packageId: "beach_region",
    ruinPackageId: "beach_region_ruin",
    // A secret, for the way back: a smugglers' cave in the pier's cove, behind a rockfall the Valley Tool shifts.
    secret: {
      obstacle: "rockfall",
      tool: "valley",
      gate: { x: -31.58, z: 149.91, heading: 2.9267, width: 9 },
      spot: { x: -33.5, z: 158.7 },
    },
    // The smugglers' Sea Cave: a walled yard in the shipwreck cove, Raptor's old haunt.
    cave: {
      gate: { x: -153.54, z: 60.27, heading: 1.9653, width: 9 },
      spot: { x: -163.7, z: 64.5 },
    },
    music: "coral_cove",
    worldId: "beach",
    kingdom: "beach",
    // The main road's start line, south of the village square (the 1-on-1 is raced from it).
    challenge: { x: 16, z: -140, heading: -1.8809 },
    // On the village square's boardwalk, facing south to the road.
    spawn: { x: 0, z: -155, heading: 0 },
    gateways: [
      // At the water park's slide tower, north-west.
      { id: "splash", track: "splash_lagoon", x: -174.0, z: -77.08, radius: 6, heading: 1.5858 },
      // By the wrecked hull up the shipwreck cove's beach, south-west.
      { id: "wreck", track: "shipwreck_bay", x: -150.56, z: 91.07, radius: 6, heading: 1.7321 },
      // At the end of the pier, Volcano Isle smoking offshore.
      { id: "volcano", track: "volcano_isle", x: 1.98, z: 186.23, radius: 6, heading: 2.6233 },
      // By the coral heads in the shallows, south-east.
      { id: "coral", track: "coral_cove", x: 123.77, z: 117.75, radius: 6, heading: -2.5955 },
      // Tidewyrm's lair: a sea cave in the coral cove's east headland.
      {
        id: "lair",
        track: "boss_tropic",
        x: 178.19,
        z: 58.01,
        radius: 6,
        heading: -1.2828,
        boss: true,
        label: "TIDEWYRM'S LAIR",
      },
    ],
    passages: [
      // Back up the Dust Road to Desert World.
      {
        id: "dust_road",
        label: "THE DUST ROAD · BACK TO DESERT WORLD",
        to: "journey_dust",
        toPassage: "end",
        x: 0,
        z: -279.4,
        radius: 8,
        heading: 0,
      },
      // Tidewyrm's Causeway, on from the pier's end over the sea: to the Dragon Kingdom.
      {
        id: "causeway",
        label: "TIDEWYRM'S CAUSEWAY · TO THE DRAGON KINGDOM",
        to: "journey_cause",
        toPassage: "start",
        x: 0,
        z: 285.2,
        radius: 8,
        heading: -2.861, // (along the Causeway, back to the beach west of the pier)
        ruinOnly: true,
        blocker: { kind: "water", width: 14 },
        opensAfter: "beach",
        locked: "THE REEF LIES UNDER DEEP WATER, HELD DOWN BY TIDEWYRM: BEAT HIM FIRST",
      },
    ],
  },
  {
    // The last region (tools/blender/prehistoric/dragon_region.py), v3: far over the
    // horizon at the end of Tidewyrm's Causeway. A pocket for each of its worlds walled
    // off by dark crags, the main road one loop through them: the Harbour and Dragonfire
    // Square (the hub, the Causeway in over the sea), the Dragon Gate to Moonstone, the
    // Climb to Dragonspire, the Keep Gate onto the Citadel's approach, the Lava Tube to
    // Emberdeep, the Storm Pass to the Emerald Canyon, the Root Tunnel back to the
    // harbour. Ruined after the sacrifice (the end of its first championship).
    id: "dragon_kingdom",
    name: "Dragon Kingdom",
    packageId: "dragon_region",
    ruinPackageId: "dragon_region_ruin",
    music: "dragon",
    worldId: "dragon",
    kingdom: "dragon",
    // On Dragonfire Square's north side, facing north to the road.
    spawn: { x: 0, z: 138.8, heading: Math.PI },
    gateways: [
      // Under Dragonspire Keep's tower on its crag, north-west.
      { id: "keep", track: "dragon_isles", x: -126.54, z: -154.6, radius: 6, heading: 0.5389 },
      // At the overgrown jungle castle's gate, east.
      { id: "canyon", track: "dragon_canyon", x: 192.68, z: 68.02, radius: 6, heading: -1.6862 },
      // At Emberdeep Hold's fortress gate under its storm, north-east.
      { id: "hold", track: "snow_dragon_pass", x: 125.26, z: -138.19, radius: 6, heading: -0.6693 },
      // Before the moon gate among the violet lanterns, west.
      {
        id: "moon",
        track: "celestial_dragon_festival",
        x: -197.93,
        z: -14.01,
        radius: 6,
        heading: 1.8073,
      },
      // King Pyrrhax's Citadel's gate in the north wall: the King's race.
      {
        id: "citadel",
        track: "boss_dragon",
        x: 7.24,
        z: -198.14,
        radius: 6,
        heading: 0.2998,
        king: true,
        label: "KING PYRRHAX'S CITADEL",
      },
    ],
    passages: [
      // Back along Tidewyrm's Causeway to Tropic Isles.
      {
        id: "causeway",
        label: "TIDEWYRM'S CAUSEWAY · BACK TO TROPIC ISLES",
        to: "journey_cause",
        toPassage: "end",
        x: 0,
        z: 283,
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
    journey: { from: "valley", to: "snow", road: [35, 1492] },
    spawn: { x: -380.3, z: 331.8, heading: 2.796 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE BURNT GORGE · BACK TO DINOSAUR VALLEY",
        to: "dinosaur_valley",
        toPassage: "burnt_gorge",
        x: -385,
        z: 345,
        radius: 8,
        heading: 2.796,
      },
      {
        id: "end",
        label: "THE BURNT GORGE · ON TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        toPassage: "burnt_gorge",
        x: 362,
        z: -394,
        radius: 8,
        heading: -0.4613,
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
    journey: { from: "snow", to: "desert", road: [58, 1367] },
    spawn: { x: -361.0, z: -351.2, heading: 0.6936 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE FROZEN PASS · BACK TO THE SNOW KINGDOM",
        to: "snow_kingdom",
        toPassage: "frozen_pass",
        x: -370,
        z: -362,
        radius: 8,
        heading: 0.6936,
      },
      {
        id: "end",
        label: "THE FROZEN PASS · ON TO DESERT WORLD",
        to: "desert_world",
        toPassage: "frozen_pass",
        x: 368,
        z: 368,
        radius: 8,
        heading: -2.634,
      },
    ],
  },
  {
    // Out of the sand into the jungle: the Dunes, the Mesa Tunnel, the Scrub, the Ford's river and bridge, the Vine Gorge, the Jungle.
    // (tools/blender/prehistoric/journey_region.py dust; the positions are the build's.)
    id: "journey_dust",
    name: "The Dust Road",
    packageId: "journey_dust",
    music: "journey_dust",
    worldId: "desert",
    journey: { from: "desert", to: "beach", road: [43, 1292] },
    spawn: { x: -358.3, z: 54.8, heading: 1.3713 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "THE DUST ROAD · BACK TO DESERT WORLD",
        to: "desert_world",
        toPassage: "dust_road",
        x: -372,
        z: 52,
        radius: 8,
        heading: 1.3713,
      },
      {
        id: "end",
        label: "THE DUST ROAD · ON TO TROPIC ISLES",
        to: "tropic_isles",
        toPassage: "dust_road",
        x: 380,
        z: -322,
        radius: 8,
        heading: -1.1288,
      },
    ],
  },
  {
    // Over the sea on the reef Tidewyrm raised: the Reef, the Sea Cave, the Stacks, the Isle and its lighthouse, the serpent's Ribs over the strait, the Crags up to the Dragon Kingdom's gate.
    // (tools/blender/prehistoric/journey_region.py cause; the positions are the build's.)
    id: "journey_cause",
    name: "Tidewyrm's Causeway",
    packageId: "journey_cause",
    music: "journey_cause",
    worldId: "beach",
    journey: { from: "beach", to: "dragon", road: [50, 1158] },
    spawn: { x: -1.1, z: -386.4, heading: -0.2245 },
    gateways: [],
    passages: [
      {
        id: "start",
        label: "TIDEWYRM'S CAUSEWAY · BACK TO TROPIC ISLES",
        to: "tropic_isles",
        toPassage: "causeway",
        x: 2,
        z: -400,
        radius: 8,
        heading: -0.2245,
      },
      {
        id: "end",
        label: "TIDEWYRM'S CAUSEWAY · ON TO THE DRAGON KINGDOM",
        to: "dragon_kingdom",
        toPassage: "causeway",
        x: 70,
        z: 390,
        radius: 8,
        heading: -2.7008,
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
