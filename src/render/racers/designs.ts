/**
 * Who the racers are: names, species, titles, lines for the select screen, menu colours
 * and their voice call. Plain data (no 3D), so menus, settings and audio can use it.
 *
 * How each one is built (model, kart, colours, personality) lives in roster/<id>.ts.
 * Looks never change how a kart drives: driving stats are chosen separately
 * (characters.json), and every look uses the same kart chassis and physics.
 */

export type RacerId = "tiko" | "brakka" | "pebble" | "zephyr";

export interface RacerDesign {
  id: RacerId;
  name: string;
  species: string;
  /** The design's title ("Tropical Explorer"). */
  title: string;
  /** A short line about them (upper case for the pixel font). */
  bio: string;
  /** Their catchphrase. */
  quote: string;
  /** Menu colours: the name, and the plate behind it. */
  color: string;
  plate: string;
  /** The highlight call: an instrument from "Pick Your Racer" and three notes. */
  call: {
    inst: "marimba" | "pizz" | "flute" | "clarinet" | "bassoon" | "xylophone";
    notes: number[];
  };
}

export const DESIGNS: Record<RacerId, RacerDesign> = {
  tiko: {
    id: "tiko",
    name: "Tiko",
    species: "parasaurolophus",
    title: "Tropical Explorer",
    bio: "KEEPS A JOURNAL OF EVERY WRONG TURN THAT TURNED OUT RIGHT. IT'S MOSTLY DOODLES. AND MUD.",
    quote: "OOPS. NEW SHORTCUT!",
    color: "#3cc8d2",
    plate: "#f39a2b",
    call: { inst: "marimba", notes: [79, 83, 86] },
  },
  brakka: {
    id: "brakka",
    name: "Brakka",
    species: "triceratops",
    title: "Rocky Roader",
    bio: "HEADBUTTS THE STARTING GATE FOR LUCK. THE GATE HAS ASKED HIM TO STOP.",
    quote: "MOVE OR GET MOVED.",
    color: "#e2733a",
    plate: "#8d6e52",
    call: { inst: "bassoon", notes: [55, 59, 62] },
  },
  pebble: {
    id: "pebble",
    name: "Pebble",
    species: "ankylosaurus",
    title: "Shoreline Roller",
    bio: "NAPS ON THE GRID UNTIL THE LAST SECOND, THEN LEADS LAP ONE. NOBODY KNOWS HOW. PEBBLE DOESN'T EITHER.",
    quote: "OH. ARE WE GOING?",
    color: "#5d8fd6",
    plate: "#3fb8c4",
    call: { inst: "clarinet", notes: [62, 66, 69] },
  },
  zephyr: {
    id: "zephyr",
    name: "Zephyr",
    species: "pteranodon",
    title: "Sky Scout",
    bio: "CAN'T FLY WITH A KART STRAPPED ON, AND KEEPS TRYING. THE SMIRK SAYS IT'S GOING TO WORK THIS TIME.",
    quote: "GROUND IS OPTIONAL.",
    color: "#f5a524",
    plate: "#c8402c",
    call: { inst: "flute", notes: [83, 86, 91] },
  },
};

/** The racers in menu order. */
export const RACER_IDS: RacerId[] = ["tiko", "brakka", "pebble", "zephyr"];
