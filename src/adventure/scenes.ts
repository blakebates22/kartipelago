/**
 * Adventure's story scenes, as data: who speaks and what they say, over which picture.
 * ALL PLACEHOLDER: first-pass lines that say what happens, to be rewritten (and turned
 * into real cinematics) later. The cast is the story doc's placeholder cast.
 *
 * A scene is a list of beats: a line from someone, or a caption (who: "") over the
 * backdrop. `fx` marks the big moments for the player to show (a dragon flying over,
 * the world map opening); for now they're a flash and a caption.
 */
import type { RacerId } from "../render/racers/designs";
import { DRAGON, KINGDOMS } from "./data";

export interface Speaker {
  name: string;
  /** A racer's look for the portrait (the racers), or a drawn placeholder head. */
  look?: RacerId;
  shape?: "dragon" | "elder" | "chosen";
  color: string;
}

export const CAST: Record<string, Speaker> = {
  elder: { name: "Elder Mossback", shape: "elder", color: "#6a994e" },
  chosen: { name: "Aurin", shape: "chosen", color: "#f2c64a" },
  you: { name: "You", color: "#5ab4ff" },
  // The champions: the four racers who join your crew.
  rex: { name: "Rex", look: "rex", color: "#e8873a" },
  brachio: { name: "Brachio", look: "brachio", color: "#bfe4ff" },
  stego: { name: "Stego", look: "stego", color: "#e8b060" },
  raptor: { name: "Raptor", look: "raptor", color: "#22b4c8" },
  // The dragons (placeholder heads; Blake's "Wildbolt" sheet is the look to aim for).
  cinderjaw: { name: "Cinderjaw", shape: "dragon", color: "#c8402a" },
  rimefang: { name: "Rimefang", shape: "dragon", color: "#bfd8f0" },
  scorchwind: { name: "Scorchwind", shape: "dragon", color: "#d8b070" },
  tidewyrm: { name: "Tidewyrm", shape: "dragon", color: "#1f6a6a" },
  king: { name: "King Pyrrhax", shape: "dragon", color: "#5a2a8a" },
};

export interface Beat {
  /** A CAST key, or "" for a caption. */
  who: string;
  text: string;
  fx?: "dragons" | "worldmap" | "flash" | "light";
}

export interface Scene {
  id: string;
  title: string;
  /** The picture behind it: a course's preview (track id), or a colour. */
  backdrop: { track?: string; color: string };
  beats: Beat[];
}

const S = (id: string, title: string, backdrop: Scene["backdrop"], beats: Beat[]): Scene => ({
  id,
  title,
  backdrop,
  beats,
});

const DRAGON_OF: Record<string, string> = {
  valley: "cinderjaw",
  snow: "rimefang",
  desert: "scorchwind",
  beach: "tidewyrm",
};
const CHAMP_OF: Record<string, string> = {
  valley: "rex",
  snow: "brachio",
  desert: "stego",
  beach: "raptor",
};

const scenes: Scene[] = [
  S("intro", "The Annual Valley Championship", { track: "riverbend_palms", color: "#3a7a3a" }, [
    { who: "", text: "A HIDDEN VALLEY. FOR THE DINOSAURS WHO LIVE HERE, IT IS THE WHOLE WORLD." },
    {
      who: "elder",
      text: "THE ANNUAL VALLEY CHAMPIONSHIP BEGINS! FOUR RACES. THE BEST RACER TAKES THE CUP.",
    },
    { who: "rex", text: "SAME AS EVERY YEAR, THEN. THE CUP STAYS WITH ME." },
    { who: "chosen", text: "GOOD LUCK OUT THERE. RACE YOUR BEST AND HAVE FUN." },
    { who: "elder", text: "(QUIETLY) WATCH THAT ONE. HE IS NOT LIKE THE REST OF US." },
  ]),
  S("valley_catastrophe", "Dragons Over the Valley", { track: "ember_peak", color: "#7a2618" }, [
    { who: "rex", text: "YOU BEAT ME FAIR AND SQUARE. WHEREVER YOU GO NEXT, I'M COMING TOO." },
    { who: "", text: "(REX JOINS YOUR CREW: YOU CAN RACE AS REX NOW, IN EVERY MODE.)" },
    {
      who: "",
      text: "THE CELEBRATION IS IN FULL SWING WHEN SHADOWS CROSS THE SUN.",
      fx: "dragons",
    },
    {
      who: "cinderjaw",
      text: "SO THIS IS WHERE THE LITTLE LIZARDS HIDE. BURN IT. BURN ALL OF IT.",
    },
    {
      who: "",
      text: "FIRE FALLS ON THE VALLEY. BRIDGES BREAK, THE GREAT TREE FALLS, THE VOLCANO WAKES.",
      fx: "flash",
    },
    { who: "elder", text: "THE CHOSEN ONE IS GONE. THE PROPHECY... IT HAS BEGUN." },
    { who: "elder", text: "HE WENT TO FACE THEM ALONE. BUT HE LEFT US A WAY TO FOLLOW." },
    {
      who: "elder",
      text: "A MAP, TORN TO PIECES, SCATTERED OVER OUR RUINED COURSES. GATHER EVERY FRAGMENT AND WIN.",
    },
  ]),
  S("valley_map", "The Map Is Whole", { color: "#c8a060" }, [
    { who: "elder", text: "ALL FOUR PIECES! THE MAP SHOWS A LAND OF SNOW BEYOND THE MOUNTAINS." },
    { who: "elder", text: "BUT CINDERJAW STILL CIRCLES THE VALLEY. YOU MUST BEAT HIM FIRST." },
  ]),
  S("valley_boss_won", "Beyond the Valley", { color: "#3a6a9a" }, [
    { who: "cinderjaw", text: "IMPOSSIBLE! OUTRUN BY A LIZARD! THE KING WILL HEAR OF THIS!" },
    { who: "", text: "IN THE ASHES WHERE HE FELL LIES A STRANGE OBJECT: THE VALLEY TOOL." },
    {
      who: "",
      text: "YOU CLIMB THE RIDGE AND SEE IT FOR THE FIRST TIME: THE WORLD.",
      fx: "worldmap",
    },
    { who: "you", text: "IT'S... HUGE. THE VALLEY IS JUST A TINY CORNER OF IT!" },
    { who: "elder", text: "THERE ARE KINGDOMS OUT THERE. THE DRAGONS WANT ALL OF THEM. GO." },
  ]),
  S("valley_return", "The Elder's Task", { track: "riverbend_palms", color: "#3a7a3a" }, [
    {
      who: "elder",
      text: "(PLACEHOLDER TASK) THE VALLEY TOOL. BRING IT TO THE OLD STONE. YES, THERE.",
    },
    { who: "", text: "THE TOOL GLOWS, AND SOMETHING FAR AWAY ANSWERS.", fx: "light" },
  ]),
  S("dragon_arrive", "The Dragon Kingdom", { track: "dragon_isles", color: "#3a1a2a" }, [
    { who: "", text: "THE HOME OF THE DRAGONS. CASTLES ON EVERY PEAK, FIRE IN EVERY WINDOW." },
    { who: "chosen", text: "YOU CAME ALL THIS WAY? I HOPED YOU WOULD." },
    {
      who: "chosen",
      text: "THE KING IS GATHERING A POWER THAT COULD BURN THE WHOLE WORLD. WIN HIS RACES AND GET ME TO HIM.",
    },
  ]),
  S("dragon_sacrifice", "The Sacrifice", { track: "celestial_dragon_festival", color: "#1a0a1a" }, [
    { who: "king", text: "YOU ARE TOO LATE. WITNESS THE END OF EVERY KINGDOM." },
    { who: "chosen", text: "NOT WHILE I'M HERE. STAND BACK, ALL OF YOU." },
    {
      who: "",
      text: "(PLACEHOLDER) A LIGHT BRIGHTER THAN ANY FIRE. THE KING'S POWER BREAKS.",
      fx: "light",
    },
    {
      who: "",
      text: "THE WHOLE KINGDOM IS TORN APART AND REMADE. THE CHOSEN ONE IS GONE.",
      fx: "flash",
    },
    { who: "king", text: "HE THREW HIMSELF AWAY. AND I AM STILL HERE." },
    { who: "", text: "THE HEROES FLEE. THE FOUR TOOLS GROW WARM IN THEIR BAG." },
  ]),
  S("resurrection", "The Return of the Chosen One", { color: "#f4e8cc" }, [
    {
      who: "",
      text: "(PLACEHOLDER) THE FOUR TOOLS RISE TOGETHER AND BLAZE WITH LIGHT.",
      fx: "light",
    },
    { who: "chosen", text: "...YOU DIDN'T GIVE UP ON ME. THANK YOU." },
    { who: "chosen", text: "THE KING IS STILL OUT THERE. LET'S FINISH THIS. TOGETHER." },
  ]),
  S("dragon_final_arrive", "The Remade Kingdom", { track: "dragon_canyon", color: "#2a1a3a" }, [
    { who: "", text: "THE DRAGON KINGDOM, REMADE BY THE SACRIFICE. NOTHING IS WHERE IT WAS." },
    { who: "chosen", text: "WIN THE LAST CHAMPIONSHIP AND THE KING WILL HAVE TO FACE US." },
  ]),
  S("king_intro", "The Dragon King", { track: "dragon_isles", color: "#1a0a0a" }, [
    { who: "king", text: "SO. THE LIZARD WHO WON EVERY CUP. RACE ME, IF YOU DARE." },
  ]),
  S("king_lost", "The Chosen One Steps Forward", { color: "#2a2a4a" }, [
    { who: "you", text: "HE'S TOO FAST. NOBODY CAN KEEP UP WITH HIM." },
    { who: "chosen", text: "THAT'S HIS FIRE. IT FEEDS ON FEAR. LET ME DRIVE THIS ONE." },
    {
      who: "",
      text: `YOU ARE NOW ${DRAGON.chosen.name.toUpperCase()}. (PLACEHOLDER ABILITY: ${DRAGON.chosen.ability} CANCELS THE KING'S ADVANTAGE.)`,
    },
  ]),
  S("ending", "The Kingdoms Are Free", { track: "riverbend_palms", color: "#3a7a3a" }, [
    { who: "king", text: "BEATEN... BY THE LIGHT AND A HANDFUL OF LIZARDS." },
    { who: "", text: "THE DRAGONS' CONQUEST IS OVER. EVERY KINGDOM IS FREE.", fx: "light" },
    { who: "elder", text: "YOU LEFT AS CHILDREN. YOU COME HOME AS HEROES." },
    { who: "", text: "THE END (FOR NOW). THANK YOU FOR PLAYING THE ADVENTURE SKELETON!" },
  ]),
];

// The other kingdoms' scenes: the same shape, placeholder lines that name what happens.
for (const k of KINGDOMS) {
  const d = DRAGON_OF[k.id]!;
  const champ = CHAMP_OF[k.id];
  const track = k.courses[0]!.track;
  if (k.id !== "valley") {
    scenes.push(
      S(k.scenes.arrive, k.name, { track, color: "#3a5a7a" }, [
        {
          who: "",
          text: `THE ${k.name.toUpperCase()}. NOTHING LIKE THE VALLEY. (PLACEHOLDER: ITS PEOPLE AND THEIR RACING WAYS.)`,
        },
        {
          who: champ ?? "elder",
          text: "STRANGERS? THEN RACE OUR CHAMPIONSHIP. HERE, THAT'S HOW TRUST IS EARNED.",
        },
      ]),
      S(
        k.scenes.catastrophe,
        `Dragons Over the ${k.name}`,
        { track: k.courses[1]!.track, color: "#7a2618" },
        [
          { who: champ!, text: "YOU BEAT ME IN MY OWN CHAMPIONSHIP. I'M WITH YOU NOW." },
          { who: "", text: `(${CAST[champ!]!.name.toUpperCase()} JOINS YOUR CREW.)` },
          { who: "", text: "(PLACEHOLDER CATASTROPHE) THE DRAGONS STRIKE.", fx: "dragons" },
          { who: d, text: "THIS KINGDOM BELONGS TO THE DRAGON KING NOW." },
          {
            who: champ ?? "elder",
            text: "OUR COURSES ARE IN RUINS... BUT LOOK: SCRAPS OF A MAP. THE CHOSEN ONE WAS HERE.",
          },
        ],
      ),
      S(k.scenes.mapDone, "The Map Is Whole", { color: "#c8a060" }, [
        { who: champ ?? "elder", text: "THE MAP POINTS ONWARD. BUT FIRST, THE DRAGON." },
      ]),
      S(k.scenes.bossWon, `${k.name} Is Free`, { track, color: "#3a6a9a" }, [
        { who: d, text: "THE KING WILL NOT FORGIVE THIS." },
        { who: "", text: `YOU FIND THE ${k.tool!.name.toUpperCase()}.` },
      ]),
      S(k.returnTask!.scene, `${k.name}: A Task`, { track, color: "#3a5a7a" }, [
        {
          who: champ ?? "elder",
          text: `(PLACEHOLDER TASK) THE ${k.tool!.name.toUpperCase()}... IT WANTS TO GO HOME. LET IT.`,
        },
        { who: "", text: "THE TOOL GLOWS, AND SOMETHING FAR AWAY ANSWERS.", fx: "light" },
      ]),
    );
  }
  // The champion's challenge (Blake, Oct 27): out of the gateway of the last of the four
  // courses, the champion drives up and you race at once (screens/overworld.ts).
  if (champ)
    scenes.push(
      S(challengeSceneOf(k.id), `${CAST[champ]!.name}'s Challenge`, { track, color: "#7a5a1a" }, [
        { who: champ, text: "HOLD IT RIGHT THERE! ALL FOUR OF MY COURSES? NOT BAD AT ALL." },
        {
          who: champ,
          text: `BUT NOBODY TAKES THE ${k.name.toUpperCase()} CUP WITHOUT BEATING ME. ONCE ROUND, YOU AND ME.`,
        },
        { who: "", text: "(THE CHAMPION'S CHALLENGE: 1 ON 1, ONCE ROUND THE KINGDOM.)" },
        { who: champ, text: "NO WAITING AROUND. WE GO RIGHT NOW!" },
      ]),
    );
  scenes.push(
    S(k.scenes.boss, `${k.boss!.name}`, { track: k.boss!.track, color: "#5a1a1a" }, [
      { who: d, text: "RACE ME, LITTLE LIZARD. LOSE, AND YOU BURN WITH THE REST." },
    ]),
  );
}
scenes.push(
  S("valley_arrive", "Dinosaur Valley", { track: "riverbend_palms", color: "#3a7a3a" }, []),
);

/** The scene of a kingdom's champion's challenge (where it has a champion). */
export function challengeSceneOf(kingdom: string) {
  return `${kingdom}_challenge`;
}

export const SCENES: Record<string, Scene> = Object.fromEntries(scenes.map((s) => [s.id, s]));
export const sceneById = (id: string) => SCENES[id];
