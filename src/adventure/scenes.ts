/**
 * Adventure's story scenes, as data: who speaks and what they say (the approved story,
 * Blake, Oct 27: claude/kartipelago-story.md). Almost every scene is staged in the 3D
 * world (staged.ts says where everyone stands and what the camera does for each line);
 * the opening is a storybook, over a picture.
 *
 * A scene is a list of beats: a line from someone, or a caption (who: "").
 */
import type { RacerId } from "../render/racers/designs";
import { KINGDOMS, OPENING, sceneOf, type KingdomId } from "./data";

export interface Speaker {
  name: string;
  /** A racer's look for the portrait (the racers), or a drawn head. */
  look?: RacerId;
  shape?: "dragon" | "elder" | "robed" | "guard" | "crowd";
  color: string;
}

export const CAST: Record<string, Speaker> = {
  elder: { name: "Elder Mossback", shape: "elder", color: "#6a994e" },
  lumen: { name: "Lumen", shape: "robed", color: "#d8c890" },
  // Lumen once the robe comes off: a dragon hatchling (and grown, at the end).
  lumen_dragon: { name: "Lumen", shape: "dragon", color: "#f0d890" },
  you: { name: "You", color: "#5ab4ff" },
  // The champions: the four racers who join your crew.
  rex: { name: "Rex", look: "rex", color: "#e8873a" },
  brachio: { name: "Brachio", look: "brachio", color: "#bfe4ff" },
  stego: { name: "Stego", look: "stego", color: "#e8b060" },
  raptor: { name: "Raptor", look: "raptor", color: "#22b4c8" },
  // The dragons.
  cinderjaw: { name: "Cinderjaw", shape: "dragon", color: "#c8402a" },
  rimefang: { name: "Rimefang", shape: "dragon", color: "#bfd8f0" },
  scorchwind: { name: "Scorchwind", shape: "dragon", color: "#d8b070" },
  tidewyrm: { name: "Tidewyrm", shape: "dragon", color: "#1f6a6a" },
  king: { name: "King Pyrrhax", shape: "dragon", color: "#5a2a8a" },
  // The underground's sketchy guards, and a crowd.
  guard: { name: "Sketchy Guard", shape: "guard", color: "#7a6a5a" },
  // The dragons' own guards (Dragon Kingdom folk).
  sentry: { name: "Guard", shape: "guard", color: "#5a3a6a" },
  crowd: { name: "The Crowd", shape: "crowd", color: "#a87a4a" },
};

export interface Beat {
  /** A CAST key, or "" for a caption. */
  who: string;
  text: string;
  /** The picture scenes' effects (the opening). */
  fx?: "dragons" | "flash" | "light" | "horn";
  /** A caption about a champion joining your crew, or switching to them for the
   * underground: a file raced as that champion reads it differently (beatsFor). */
  crew?: RacerId;
  switchTo?: RacerId;
}

export interface Scene {
  id: string;
  title: string;
  /** The picture behind it, when it isn't staged: a course's preview, or a colour
   * (`storybook`: old parchment). */
  backdrop: { track?: string; color: string; storybook?: boolean };
  beats: Beat[];
}

const S = (id: string, title: string, backdrop: Scene["backdrop"], beats: Beat[]): Scene => ({
  id,
  title,
  backdrop,
  beats,
});
const say = (who: string, text: string, more: Partial<Beat> = {}): Beat => ({ who, text, ...more });
const cap = (text: string, more: Partial<Beat> = {}): Beat => ({ who: "", text, ...more });

/** Each kingdom's dragon and champion, as CAST keys. */
export const DRAGON_OF: Record<string, string> = {
  valley: "cinderjaw",
  snow: "rimefang",
  desert: "scorchwind",
  beach: "tidewyrm",
};
export const CHAMP_OF: Record<string, RacerId> = {
  valley: "rex",
  snow: "brachio",
  desert: "stego",
  beach: "raptor",
};

/** A land's name as the lines say it ("THE SNOW KINGDOM", "DESERT WORLD"). */
export const LAND: Record<KingdomId, string> = {
  valley: "DINOSAUR VALLEY",
  snow: "THE SNOW KINGDOM",
  desert: "DESERT WORLD",
  beach: "THE TROPIC ISLES",
  dragon: "THE DRAGON KINGDOM",
};

const scenes: Scene[] = [
  // ---------------------------------------------------------------- the opening
  // Every rule the story stands on is in here: the war, the oath sworn before the race,
  // its terms (the border, the peace, the hundred-year champion, the forfeit and how the
  // lands are won back), the horn, and the five stones that hold it.
  S(OPENING, "The First Race", { color: "#e8d6a8", storybook: true }, [
    cap(
      "A THOUSAND YEARS AGO, THE DRAGONS, RULED BY THEIR KING, AND THE FIRST RACING CREWS, RULED BY THEIR KEEPER, WENT TO WAR OVER THE FOUR LANDS.",
      { fx: "dragons" },
    ),
    cap(
      "AT LAST THEY AGREED: ONE RACE WOULD END THE WAR. BEFORE IT BEGAN, BOTH SIDES SWORE TO ITS RULES. THEY CALLED THAT OATH THE DRAGON PACT.",
    ),
    cap(
      "RULE ONE: WHOEVER LOST THE RACE WOULD LEAVE THE FOUR LANDS AND LIVE BEHIND A BORDER. AND NEITHER SIDE WOULD EVER HARM THE OTHER AGAIN.",
    ),
    cap(
      "RULE TWO: EVERY HUNDRED YEARS, THE WINNERS MUST SEND THEIR BEST RACER, A CHAMPION, TO RACE THE LOSERS' RULER. IF THAT RULER WINS, THE LANDS GO BACK TO THE ONES WHO WERE DEFEATED.",
    ),
    cap(
      "RULE THREE: IF A HUNDRED YEARS PASS AND NO CHAMPION COMES, THE LOSERS' RULER WINS WITHOUT A RACE, UNTIL A CHAMPION BEATS THAT RULER AND WINS THE LANDS BACK.",
    ),
    cap("WITH THE OATH SWORN, THE RACE BEGAN: DRAGONS AND CREWS, SIDE BY SIDE."),
    cap("THE DRAGONS FLEW FASTER THAN ANYTHING ALIVE. BUT AT THE LAST TURN, A HORN SOUNDED...", {
      fx: "horn",
    }),
    cap(
      "...THE DRAGONS FALTERED, AND THE CREWS CROSSED THE LINE FIRST. NO DRAGON SAW WHO BLEW THE HORN.",
    ),
    cap(
      "THE DRAGON KING SUSPECTED A TRICK, BUT HE COULD NOT PROVE IT, AND HE HAD SWORN. SO THE DRAGONS KEPT THEIR OATH, AND WITHDREW BEHIND THE BORDER, TO THE DRAGON KINGDOM.",
      { fx: "light" },
    ),
    cap(
      "THE PACT WAS CARVED INTO FIVE STONES MADE OF DRAGON LIGHT: ONE IN EACH LAND, AND THE HEART STONE IN THE DRAGON KINGDOM. WHILE THEY STAND, THE BORDER AND THE PEACE HOLD.",
    ),
  ]),

  // ---------------------------------------------------------------- Act I: the valley
  S(
    sceneOf("valley", "festival"),
    "The Summer Festival",
    { track: "riverbend_palms", color: "#3a7a3a" },
    [
      cap(
        "DINOSAUR VALLEY. THE SUMMER FESTIVAL, HELD AT THE VALLEY'S PACT STONE EVERY SUMMER FOR A THOUSAND YEARS.",
      ),
      say("elder", "A NEW FACE! NO CREW COLOURS? THEN YOU RACE FOR YOURSELF. WELCOME, STRANGER!"),
      say("elder", "I'M MOSSBACK, THE CREWS' KEEPER. AND THIS IS LUMEN, WHO I RAISED."),
      say(
        "elder",
        "I FOUND HIM AS A BABY, ASLEEP IN THE RIVER REEDS, GLOWING LIKE A LANTERN. SAY HELLO, LUMEN.",
      ),
      say("lumen", "HI! GOOD LUCK. YOU'LL NEED IT IF REX IS RACING."),
      say(
        "elder",
        "FOUR COURSES, ONE FESTIVAL CUP. WIN ALL FOUR AND THE WHOLE VALLEY WILL KNOW YOUR NAME.",
      ),
      say("elder", "AND WHO KNOWS? ONE DAY THE PACT MIGHT EVEN CALL ON YOU TO......"),
      say(
        "lumen",
        "ELDER! IN THE OLD STORY A HORN SOUNDED AT THE LAST TURN, AND THE DRAGONS FALTERED. WHOSE HORN WAS IT?",
      ),
      say("elder", "NOT NOW, LUMEN. IT'S A FESTIVAL STORY, THAT'S ALL. GO AND WATCH THE RACES."),
      cap("MOSSBACK'S HAND GOES TO THE OLD HORN AT HIS HIP."),
      say("lumen", "THEN ONE DAY I'LL ASK THE DRAGONS MYSELF."),
    ],
  ),
  S(sceneOf("valley", "challenge"), "The Lone Racer", { track: "ember_peak", color: "#7a5a1a" }, [
    say("rex", "SO YOU'RE THE ONE WHO TOOK ALL FOUR RACES. NOT BAD, FOR A NOBODY WITH NO CREW."),
    say("rex", "I'M REX. NO CREW EITHER. NEVER NEEDED ONE. I'M THE BEST RACER IN THIS VALLEY."),
    say("rex", "YOU WANT TO BE THE BEST? BEAT ME. ONCE ROUND THE VALLEY, YOU AND ME. RIGHT NOW!"),
  ]),
  S(sceneOf("valley", "prize"), "A Crew of Two", { track: "riverbend_palms", color: "#3a7a3a" }, [
    say("rex", "...YOU ACTUALLY BEAT ME. NOBODY BEATS ME."),
    say("rex", "FINE. TWO LONERS WITH NO CREW. I SUPPOSE THAT MAKES US A CREW."),
    cap("REX JOINS YOUR CREW!", { crew: "rex" }),
    say("elder", "A NEW CREW, BORN ON FESTIVAL DAY! NOW THAT'S A GOOD OMEN."),
  ]),
  S(
    sceneOf("valley", "hundredth"),
    "The Hundredth Summer",
    { track: "ember_peak", color: "#7a2618" },
    [
      say("elder", "THE STONE... IT'S GLOWING. IT ONLY DOES THAT ON THE HUNDREDTH SUMMER. TODAY?"),
      say(
        "elder",
        "A CHAMPION MUST RACE THE KING EVERY HUNDRED YEARS. THE LAST ONE WENT A HUNDRED SUMMERS AGO, BEFORE I WAS BORN.",
      ),
      say("elder", "SENDING THE CHAMPION IS THE KEEPER'S JOB. MY JOB. AND I LOST COUNT."),
      cap("A SHADOW CROSSES THE SUN."),
      say(
        "cinderjaw",
        "NOBODY CAME. A HUNDRED YEARS, AND NO CHAMPION. BY THE PACT, YOUR LANDS ARE OURS NOW.",
      ),
      say(
        "cinderjaw",
        "I AM CINDERJAW. A THOUSAND YEARS WE WAITED BEHIND YOUR BORDER. NOW FOUR DRAGONS TAKE THE FOUR LANDS, AND THIS VALLEY IS MINE.",
      ),
      say("cinderjaw", "THE PACT STILL SAYS I MAY NOT HARM YOU. SO I WON'T. FOR NOW."),
      say("cinderjaw", "SEAL THE BORDERS! ROUND UP EVERY RACER! THE RACES BELONG TO ME NOW."),
      cap("CINDERJAW'S GUARDS SPREAD THROUGH THE VALLEY."),
    ],
  ),
  S(sceneOf("valley", "way_out"), "One Way Out", { track: "ember_peak", color: "#4a2a1a" }, [
    say(
      "elder",
      "THIS IS MY FAULT. I KNEW THE PACT BY HEART, AND STILL I LOST COUNT OF THE SUMMERS.",
    ),
    say(
      "elder",
      "BUT THE PACT ALSO SAYS THIS: IF A CHAMPION BEATS THE KING, HE MUST GIVE ALL FOUR LANDS BACK.",
    ),
    say("elder", "YOU WON THE FESTIVAL AND BEAT REX. THAT MAKES YOU THE VALLEY'S CHAMPION."),
    say("you", "THEN I'LL GO TO THE KING."),
    say(
      "elder",
      "WITH THE BORDERS SEALED, THE ONLY WAY OUT IS UNDER THEM: THE SMUGGLERS' TUNNELS.",
    ),
    say(
      "elder",
      "EACH TUNNEL COMES OUT IN AN OLD PASS, AND THE PASS LEADS ON TO THE NEXT LAND: SNOW, THEN DESERT, THEN THE ISLES. ONLY FROM THE ISLES DOES A TUNNEL REACH THE DRAGON KINGDOM.",
    ),
    say(
      "elder",
      "AND I'M COMING WITH YOU. SENDING A CHAMPION WAS MY JOB. THE LEAST I CAN DO IS GO WITH ONE.",
    ),
    // (He tags along: so in The Smugglers' Key, "he was right behind us".)
    say("lumen", "ME TOO! YOU ALWAYS TOLD ME TO KEEP AWAY FROM DRAGONS."),
    say(
      "rex",
      "THE SMUGGLERS ONLY OPEN UP FOR RACERS THEY KNOW. THEY KNOW ME. I CAN GET US THROUGH.",
    ),
    cap(
      "THEIR CAVE IS UP ON EMBER'S LOWER SLOPE. (REX IS IN YOUR CREW NOW: TO DRIVE AS HIM, PAUSE AND CHOOSE YOUR CREW.)",
      { switchTo: "rex" },
    ),
  ]),
  S(
    sceneOf("valley", "underground"),
    "The Underground",
    { track: "ember_peak", color: "#2a1a10" },
    [
      cap(
        "A CAVE BEHIND A ROCKFALL. TWO GUARDS ARE COUNTING A PILE OF KART PARTS THAT ISN'T THEIRS.",
      ),
      say("guard", "WELL, WELL. REX. WE HEARD YOU LOST TODAY."),
      say(
        "rex",
        "YEAH. THIS RACER BEAT ME FAIR. THAT'S HOW GOOD THEY ARE. WE NEED THE TUNNEL OUT TO THE SNOW KINGDOM'S PASS.",
      ),
      say("guard", "THE TUNNEL'S FOR WINNERS. WIN OUR GAME, AND THE KEY IS YOURS."),
    ],
  ),
  S(sceneOf("valley", "key"), "The Smugglers' Key", { track: "ember_peak", color: "#2a1a10" }, [
    say("guard", "HUH. YOU ACTUALLY WON. A DEAL'S A DEAL."),
    say(
      "guard",
      "THE SMUGGLERS' KEY. THE TUNNEL COMES OUT IN THE BURNT GORGE, ON THE SNOW KINGDOM'S SIDE.",
    ),
    say("elder", "WHERE'S LUMEN? HE WAS RIGHT BEHIND US."),
    say("elder", "...HE'LL FIND US. HE ALWAYS DOES."),
  ]),
  S(sceneOf("valley", "stone"), "The Cracked Stone", { track: "ember_peak", color: "#1a0a0a" }, [
    cap("MEANWHILE, AT THE VALLEY'S PACT STONE..."),
    say("cinderjaw", "A CRACK. RIGHT THROUGH THE OLD STONE. WHO DARED TOUCH IT?"),
    say(
      "cinderjaw",
      "NO TOOL CAN CRACK A PACT STONE. ONLY DRAGON LIGHT COULD, AND EVERY DRAGON IS ACCOUNTED FOR.",
    ),
  ]),

  // ---------------------------------------------------------------- Act III
  S("dragon_challenger", "The Challenger", { track: "dragon_isles", color: "#3a1a2a" }, [
    cap("THE DRAGON KINGDOM. THE FIRST CREW TO DRIVE HERE IN A HUNDRED YEARS."),
    cap("THE KING COMES DOWN TO MEET YOU."),
    say("king", "I AM PYRRHAX, KING OF THE DRAGONS. A CHAMPION, A HUNDRED YEARS LATE."),
    say(
      "king",
      "NINE CHAMPIONS HAVE RACED ME, ONE EVERY HUNDRED YEARS. NINE TIMES I LOST, AND MY PEOPLE STAYED BEHIND THE BORDER, DIMMING.",
    ),
    say("king", "THIS TIME THE LANDS ARE MINE. BEAT ME, AND BY THE PACT I MUST GIVE THEM BACK."),
    say("king", "THE PACT SAYS I MUST RACE YOU. IT DOESN'T SAY WHEN. WIN MY FOUR RACES FIRST."),
    cap(
      "FOUR DRAGONS SETTLE ON THE ROOFTOPS TO WATCH: CINDERJAW, RIMEFANG, SCORCHWIND AND TIDEWYRM.",
    ),
    say("lumen", "YOU CAME. I KNEW YOU WOULD."),
    say("elder", "LUMEN! HOW DID YOU GET PAST THE BORDERS?"),
    say("lumen", "I HAVE MY WAYS. GO ON. HE'S WAITING."),
  ]),
  S("dragon_before_king", "Before the King", { track: "dragon_isles", color: "#1a0a0a" }, [
    say("cinderjaw", "FOUR WINS. IN OUR OWN KINGDOM."),
    say("rimefang", "BY THE LAW, THE CHAMPION HAS EARNED THE RACE."),
    say("scorchwind", "AND WHAT A RACE IT'LL BE! I'D SELL TICKETS, IF ANYONE HAD ANY MONEY LEFT."),
    say("tidewyrm", "MY KING, A WORD FIRST. THE PACT STONES, ALL FOUR OF THEM. THEY'RE CRACKED..."),
    say("king", "ENOUGH. TO THE LINE."),
  ]),
  S("dragon_return", "The Return", { track: "dragon_isles", color: "#1a0a1a" }, [
    cap("THE KING IS BEATEN. AND FOR THE FIRST TIME EVER, HE HOLDS THE LANDS TO GIVE BACK."),
    say(
      "king",
      "...BEATEN. AND A DRAGON KEEPS HIS OATH. BY THE PACT, THE FOUR LANDS GO BACK TO THE CREWS.",
    ),
    cap("HE LAYS HIS CLAW ON THE HEART STONE TO GIVE THE LANDS BACK."),
    cap("THE HEART STONE WAKES, FOR THE FIRST TIME SINCE IT WAS RAISED."),
  ]),
  S("dragon_lumen", "Lumen", { track: "dragon_isles", color: "#1a0a1a" }, [
    say("lumen", "NOW."),
    cap("LUMEN THROWS BACK HIS ROBE. HIS WINGS UNFOLD."),
    say(
      "elder",
      "LUMEN, NO! I HID WHAT YOU ARE ALL THESE YEARS, SO THE STONES WOULD NEVER DIM YOU!",
    ),
    say(
      "lumen_dragon",
      "THE STONES ARE MADE OF DRAGON LIGHT, AND THEY FEED ON IT. I HATCHED ON YOUR SIDE OF THE BORDER, SO THEY NEVER TOOK MINE.",
    ),
    say("king", "A HATCHLING? STEP AWAY FROM THE STONE!"),
    say(
      "lumen_dragon",
      "FOR A THOUSAND YEARS THEY'VE DIMMED MY PEOPLE. I NEEDED A CHAMPION TO BEAT YOU, SO THE HEART STONE WOULD WAKE. AWAKE, IT CAN BE BROKEN.",
    ),
    say(
      "lumen_dragon",
      "I CRACKED THE OTHER FOUR SO THEY'D FALL WITH IT. NO STONES, NO BORDER. OUR LIGHT COMES HOME.",
    ),
    say(
      "lumen_dragon",
      "I'M SORRY, ELDER. WE'LL KEEP THE PEACE WITHOUT THE STONES. AND BREAKING IT TAKES ALL MY LIGHT.",
    ),
    cap("LUMEN STRIKES THE WAKING STONE. FAR AWAY, FOUR CRACKED STONES ANSWER."),
    cap("THE DRAGON PACT SHATTERS."),
    cap("THE BLAST TEARS THROUGH THE DRAGON KINGDOM. WHEN THE LIGHT FADES, LUMEN IS GONE."),
  ]),
  S("dragon_horn", "The Horn", { track: "dragon_isles_ruin", color: "#1a0a0a" }, [
    cap("SMOKE. RUBBLE. THE HEART STONE IN PIECES."),
    say("king", "NO PACT. NO OATH. NOTHING HOLDS ME NOW."),
    say("king", "AND YOU WILL BURN FIRST."),
    say("elder", "NO PACT? THEN NOTHING HOLDS ME EITHER."),
    cap("MOSSBACK RAISES THE OLD HORN, AND BLOWS. THE KING DROPS LIKE A STONE."),
    say("rex", "HE'S DOWN! THE KING IS DOWN!"),
    cap("THE CREWS CHEER. THE PACT IS GONE AND THE KING IS BEATEN. IT'S OVER."),
  ]),
  S("dragon_rage", "The Rage", { track: "dragon_isles_ruin", color: "#1a0a0a" }, [
    cap("...BUT A HORN ONLY EVER STUNNED A DRAGON."),
    cap("THE KING WAKES IN THE RUINS, BLAZING. FREE OF THE STONES, HIS LIGHT HAS COME HOME."),
    say("king", "MY HOME, IN RUINS. BROKEN BY A HATCHLING RAISED BY YOUR KIND."),
    say(
      "king",
      "A THOUSAND YEARS AGO, THAT HORN STOLE THE FIRST RACE. NOW YOUR KIND HAS TAKEN THE REST.",
    ),
    say("king", "THE PACT IS GONE. NO BORDER, NO OATH, NO PEACE. DRAGONS! TAKE IT ALL!"),
  ]),
  S("rage_valley", "The Rage", { track: "ember_peak_ruin", color: "#3a0a00" }, [
    cap("CINDERJAW BURNS DINOSAUR VALLEY. NO PACT STOPS HIM NOW."),
  ]),
  S("rage_snow", "The Rage", { track: "frostveil_citadel_ruin", color: "#0a1a2a" }, [
    cap("RIMEFANG FREEZES THE SNOW KINGDOM SOLID, AS CALMLY AS FILING PAPERWORK."),
  ]),
  S("rage_desert", "The Rage", { track: "canyon_dash_ruin", color: "#3a2a0a" }, [
    cap("SCORCHWIND BURIES DESERT WORLD IN SAND, THEN SULKS THAT THERE'S NOBODY LEFT TO WATCH."),
  ]),
  S("rage_beach", "The Rage", { track: "coral_cove_ruin", color: "#0a2a2a" }, [
    cap("TIDEWYRM DROWNS THE TROPIC ISLES, AND KEEPS EVERYTHING THAT FLOATS."),
  ]),
  S("rage_shards", "The Rage", { track: "dragon_isles_ruin", color: "#000000" }, [
    cap("IN THE RUINS OF THE CITADEL, THE BROKEN HEART STONE STILL GLOWS."),
    cap("LUMEN'S LIGHT BURSTS OUT OF IT AND SCATTERS OVER ALL FIVE LANDS: A RAIN OF LIGHT SHARDS."),
    cap("THEN THE KING'S TAIL COMES DOWN FROM ABOVE, AND EVERYTHING GOES DARK."),
  ]),

  // ---------------------------------------------------------------- Act IV
  S(sceneOf("valley", "rescue"), "Rex", { track: "ember_peak_ruin", color: "#2a1a10" }, [
    cap(
      "THE KING SENDS YOU TO CINDERJAW AS A PRIZE. YOU WAKE IN HIS CAGE, IN THE RUINS OF THE VALLEY.",
    ),
    say("rex", "PSST. HOLD STILL. THESE LOCKS ARE OLDER THAN I AM."),
    say("rex", "THEY DRAGGED US ALL HOME. NOBODY BOTHERED LOCKING UP THE LOSER. GOT IT! COME ON!"),
    say("elder", "YOU'RE ALIVE, THANK THE STONES. LOOK WHAT FELL IN THE ASHES: LUMEN'S LIGHT."),
    cap("THE SHARD BURNS MOSSBACK'S HAND. A VOICE SPEAKS OUT OF THE LIGHT. LUMEN'S VOICE."),
    say("lumen", "ONLY A FAIR WINNER MAY HOLD ME."),
    say("elder", "THE PACT STONES WERE MADE OF DRAGON LIGHT. AND HERE IS LUMEN'S, FREELY GIVEN."),
    say(
      "elder",
      "FOUR SHARDS MAKE A NEW STONE, AND A NEW STONE MAKES NEW LAWS. LAWS EVERY DRAGON MUST OBEY.",
    ),
    say(
      "elder",
      "A SHARD FELL ON EACH OF THE VALLEY'S COURSES. WIN ALL FOUR, THEN TAKE THEM TO CINDERJAW.",
    ),
    cap(
      "(EACH RUINED COURSE HIDES SHARD PIECES: COLLECT THEM ALL AND FINISH 1ST TO WIN ITS LIGHT SHARD.)",
    ),
  ]),

  // ---------------------------------------------------------------- Act V
  S("dragon_court", "The Ruined Court", { track: "dragon_isles_ruin", color: "#1a0a1a" }, [
    cap("THE DRAGON KINGDOM, STILL IN RUINS FROM THE BLAST."),
    cap(
      "THE FOUR DRAGONS HAVE COME HOME, AS THE NEW STONES' LAW SAID. THE KING SITS ON A BROKEN THRONE.",
    ),
    say("king", "YOU AGAIN. CARRYING THE HATCHLING'S LIGHT."),
    say("cinderjaw", "LET ME BURN THEM, MY KING."),
    say(
      "king",
      "NO. THE LAST FOUR SHARDS FELL ON MY OWN COURSES. THAT LIGHT ONLY GOES TO A FAIR WINNER.",
    ),
    say("king", "LET THEM WIN IT. THEN WE'LL SEE WHAT KIND OF PACT THE HATCHLING LEFT US."),
  ]),
  S("dragon_heart", "The Heart Stone", { track: "dragon_isles_ruin", color: "#2a1a0a" }, [
    cap("THE LAST FOUR SHARDS FLY TO THE CITADEL. THE HEART STONE RISES AGAIN, WHOLE AND SHINING."),
    say(
      "lumen",
      "THE NEW PACT HAS NO BORDER, NO FORFEIT, AND IT FEEDS ON NOBODY'S LIGHT. ONLY ITS TWO LAWS, FOR DRAGONS AND CREWS ALIKE.",
    ),
    say(
      "lumen",
      "IT HOLDS BY MY LIGHT, UNTIL BOTH SIDES ACCEPT IT. THEN IT WON'T NEED ME ANY MORE.",
    ),
    say("elder", "BEFORE IT BINDS YOU, KING PYRRHAX, YOU SHOULD HEAR SOMETHING. FROM ONE OF US."),
    say(
      "elder",
      "THE FIRST RACE. THIS HORN STUNNED YOUR KIND AT THE LAST TURN. THE FOUNDERS CHEATED.",
    ),
    say(
      "elder",
      "THE KEEPERS HID IT FOR A THOUSAND YEARS. THAT'S WHY LUMEN'S LIGHT WOULDN'T LET ME HOLD IT.",
    ),
    cap(
      "MOSSBACK BREAKS THE FOUNDERS' HORN ACROSS HIS KNEE. NO MORE HORNS: THE CREWS ACCEPT THE NEW PACT.",
    ),
    say("king", "...A THOUSAND YEARS I WAITED FOR ONE OF YOU TO SAY IT."),
    say("you", "KING PYRRHAX. I CHALLENGE YOU."),
    say("king", "THEN WE RACE. NO HORN. NO LIES."),
  ]),
  S("dragon_lumen_returns", "Lumen Returns", { track: "dragon_isles", color: "#f4e8cc" }, [
    say("king", "...BEATEN. FAIRLY. UNDER A LAW MADE BY ONE OF MY OWN."),
    say("king", "I GIVE UP MY CLAIM TO THE LANDS. AND THE GRUDGE WITH IT. I ACCEPT THE NEW PACT."),
    cap("BOTH SIDES HAVE ACCEPTED THE PACT. IT NO LONGER NEEDS LUMEN'S LIGHT TO HOLD."),
    cap("THE HEART STONE OPENS, AND A DRAGON STEPS OUT OF THE LIGHT: FULL-GROWN, AND GOLDEN."),
    say("lumen_dragon", "HELLO, ELDER. YOU SAID I'D ALWAYS FIND YOU."),
    say("elder", "A THOUSAND YEARS OF DIMMING, AND LOOK AT YOU SHINE."),
    say("lumen_dragon", "AND YOU TOLD HIM THE TRUTH. THAT'S ALL I EVER WANTED FROM YOU."),
    say("king", "YOU GAVE YOURSELF UP, HATCHLING. FOR US. FOR ALL OF US."),
    say(
      "lumen_dragon",
      "THE BORDER IS GONE, MY KING, AND NO STONE TAKES OUR LIGHT. WE'RE FREE TOO.",
    ),
    cap(
      "THE DRAGON KINGDOM MENDS IN THE LIGHT. RIMEFANG, SCORCHWIND AND TIDEWYRM BOW TO THE NEW PACT.",
    ),
    say(
      "cinderjaw",
      "NOT ME. THE KING ACCEPTED FOR THE DRAGONS OF THESE LANDS. SO I'M LEAVING THEM!",
    ),
    cap(
      "CINDERJAW FLIES OFF, PAST THE EDGE OF THE WORLD, WHERE NO PACT CAN REACH. NOBODY KNOWS WHERE.",
    ),
  ]),
  S("ending", "Home", { track: "riverbend_palms", color: "#3a7a3a" }, [
    cap("AND SO THE FOUR LANDS WERE RESTORED, AND THE DRAGON KINGDOM WITH THEM."),
    cap(
      "THAT SUMMER, THE FESTIVAL HAD NEW RACERS: DRAGONS, RACING FOR FUN, WINNING AND LOSING HONESTLY.",
    ),
    say("elder", "YOU CAME HERE WITH NO CREW. LOOK AT YOU NOW."),
    say("rex", "BEST CREW IN THE WORLD. OBVIOUSLY."),
    say("lumen_dragon", "SEE YOU AT THE NEXT FESTIVAL. I'M ENTERING THIS TIME."),
  ]),
];

// ---------------------------------------------------------------- Act II, kingdom by kingdom

interface Kingdom2 {
  caught: Beat[];
  stands: Beat[];
  challenge: [string, Beat[]];
  prize: [string, Beat[]];
  underground: Beat[];
  key: [string, Beat[]];
  stone: Beat[];
}

const ACT2: Record<"snow" | "desert" | "beach", Kingdom2> = {
  snow: {
    caught: [
      cap(
        "THE SNOW KINGDOM. YOU AND YOUR CREW COME OUT OF THE GORGE STRAIGHT INTO A WALL OF GUARDS.",
      ),
      say("rimefang", "TRAVELLERS. FROM A SEALED LAND, NO LESS. HOW IRREGULAR."),
      say(
        "rimefang",
        "I AM RIMEFANG. THIS LAND IS MINE BY THE PACT. HERE, EVERY STRANGER IS A CAPTIVE.",
      ),
      say(
        "rimefang",
        "THE KING'S LAW: A CAPTIVE RACES. WIN FOUR, THEN BEAT MY CHAMPION, AND YOUR CREW GOES FREE.",
      ),
      say("rimefang", "AND MY CHAMPION GOES FREE WITH YOU. LOSE, AND YOU RACE AGAIN. AND AGAIN."),
      cap("IN THE CROWD, A HOODED FIGURE WATCHES. THEN IT IS GONE."),
    ],
    stands: [
      say("rimefang", "THE CAPTIVES RACE WELL. THAT IS NOT WHAT TROUBLES ME."),
      say(
        "rimefang",
        "SOMEONE HAS BEEN IN MY LIBRARY, READING THE PACT'S OLDEST PAGE: HOW ITS STONES FEED ON OUR LIGHT, AND HOW THE HEART STONE WAKES.",
      ),
      say("sentry", "HOW DOES IT WAKE, LORD RIMEFANG?"),
      say("rimefang", "ONLY WHEN A KING GIVES THE LANDS BACK. NO KING EVER HAS. FIND THE READER."),
      say("sentry", "YES, LORD RIMEFANG."),
    ],
    challenge: [
      "The Prized Racer",
      [
        say("rimefang", "FOUR WINS. NOW, BY THE KING'S LAW, ONE MORE RACE: AGAINST MY CHAMPION."),
        say(
          "brachio",
          "I'M BRACHIO. THE BEST RACER IN THIS KINGDOM, SO HE MADE ME HIS. I DON'T WANT THIS.",
        ),
        say(
          "brachio",
          "BUT IF I LOSE ON PURPOSE, HE'LL KNOW. SO GIVE IT EVERYTHING. ONCE ROUND THE KINGDOM!",
        ),
      ],
    ],
    prize: [
      "The Winner's Prize",
      [
        say(
          "rimefang",
          "AND YOU HAVE WON. BY THE KING'S LAW, YOUR CREW GOES FREE, AND BRACHIO WITH IT.",
        ),
        say(
          "rimefang",
          "FREE FROM MY GAMES. NOT FREE TO LEAVE. MY BORDER STAYS SHUT. THE LAW IS SATISFIED.",
        ),
        say(
          "brachio",
          "...HE'S RIGHT, AND HE KNOWS IT. BUT A FREE RACER CAN GO WHERE A CAPTIVE CAN'T.",
        ),
        say("brachio", "THE SMUGGLERS' ICE CAVE. THEY KNOW MY NAME THERE. I'M WITH YOU."),
        cap("BRACHIO JOINS YOUR CREW! (SWITCH TO BRACHIO TO GET PAST THE ICE CAVE'S GUARDS.)", {
          crew: "brachio",
          switchTo: "brachio",
        }),
      ],
    ],
    underground: [
      cap("A CAVE IN THE ICE. THE GUARDS HERE ARE BIGGER, AND SKETCHIER."),
      say("guard", "BRACHIO! RIMEFANG LET YOU GO? HE NEVER LETS ANYTHING GO."),
      say("brachio", "HE DIDN'T. THE LAW DID. WE WANT THE TUNNEL TO DESERT WORLD."),
      say("guard", "WIN THE GAME, GET THE KEY. SAME AS ALWAYS."),
    ],
    key: [
      "The Frozen Pass",
      [
        say(
          "guard",
          "A WIN'S A WIN. THE KEY: THE TUNNEL COMES OUT ON THE FROZEN PASS, ON DESERT WORLD'S SIDE.",
        ),
        say("you", "HAS ANYONE SEEN A HOODED KID? ABOUT THIS TALL?"),
        say("guard", "SEEN NOTHING. HEARD NOTHING. THAT'S HOW WE STAY IN BUSINESS."),
      ],
    ],
    stone: [
      cap("MEANWHILE, AT THE SNOW KINGDOM'S PACT STONE..."),
      say("rimefang", "CRACKED. BY NO TOOL I KNOW. BY A CLAW, PERHAPS."),
      say("rimefang", "FIRST MY LIBRARY, NOW MY STONE. SOMEONE IS PLANNING SOMETHING."),
    ],
  },
  desert: {
    caught: [
      cap("DESERT WORLD. A SANDSTORM ROLLS IN OVER THE DUNES, AND IT HAS A VOICE."),
      say(
        "scorchwind",
        "LADIES AND GENTLE-LIZARDS! FRESH FROM THE FROZEN PASS: NEW PERFORMERS FOR MY GAMES!",
      ),
      say(
        "scorchwind",
        "I AM SCORCHWIND! RACE WELL AND THE CROWD LOVES YOU. RACE BADLY, AND THEY STILL LOVE ME.",
      ),
      say(
        "scorchwind",
        "THE KING'S LAW, DARLINGS: WIN FOUR, BEAT MY STAR, AND YOU'RE FREE. AND SO IS MY STAR!",
      ),
      cap("UP ON A ROOFTOP, A HOODED FIGURE. WHEN YOU LOOK AGAIN, IT IS GONE."),
    ],
    stands: [
      say("scorchwind", "WHAT A SHOW! WHAT A CROWD! WHAT A... WAIT. WHO LEFT?"),
      say(
        "scorchwind",
        "THE HOODED ONE! RAN OFF THE ROOF AND NEVER LANDED. IT FLEW! NOBODY UPSTAGES ME!",
      ),
    ],
    challenge: [
      "The Star Act",
      [
        say(
          "scorchwind",
          "AND NOW, THE MOMENT YOU'VE ALL BEEN WAITING FOR: MY STAR, MY HEADLINER... STEGO!",
        ),
        say(
          "stego",
          "EVERY NIGHT THE SAME SHOW. EVERY NIGHT I WIN. EVERY NIGHT I GO BACK IN MY CAGE.",
        ),
        say("stego", "BEAT ME, NEWCOMER. THEN WE BOTH WALK OUT OF HERE."),
      ],
    ],
    prize: [
      "The Winner's Prize",
      [
        cap("THE CROWD GOES SILENT. THE STAR HAS LOST."),
        say(
          "scorchwind",
          "...BY THE KING'S LAW, YOUR CREW GOES FREE, AND MY STAR WITH IT. I ALWAYS KEEP MY WORD.",
        ),
        say("scorchwind", "WHAT A TWIST! WHO WROTE THIS SHOW? I DID! APPLAUD ME!"),
        say(
          "stego",
          "HE'LL SPIN ANYTHING. BUT FREE IS FREE. THE SMUGGLERS IN THE DRIFT CAVE OWE ME A FAVOUR.",
        ),
        cap("STEGO JOINS YOUR CREW! (SWITCH TO STEGO TO GET PAST THE DRIFT CAVE'S GUARDS.)", {
          crew: "stego",
          switchTo: "stego",
        }),
      ],
    ],
    underground: [
      cap("A CAVE UNDER A DRIFT. THE GUARDS ARE COUNTING SOMEBODY ELSE'S COINS."),
      say("guard", "STEGO! THE STAR HIMSELF! DOES SCORCHWIND KNOW YOU'RE OUT?"),
      say(
        "stego",
        "HE KNOWS. HE'S TELLING EVERYONE IT WAS HIS IDEA. WE NEED THE TUNNEL TO THE ISLES.",
      ),
      say("guard", "THE GAME FIRST. THE STAR SHOULD LIKE THAT."),
    ],
    key: [
      "The Dust Road",
      [
        say(
          "guard",
          "A FINE PERFORMANCE. THE KEY: THE TUNNEL COMES OUT ON THE DUST ROAD, BY THE TROPIC ISLES.",
        ),
        say("stego", "THE TROPIC ISLES. TIDEWYRM'S. WATCH YOUR POCKETS."),
      ],
    ],
    stone: [
      cap("MEANWHILE, AT DESERT WORLD'S PACT STONE..."),
      say("scorchwind", "A CRACK! IN MY STONE! IN MY KINGDOM! DURING MY SHOW!"),
      say("scorchwind", "SOMEBODY'S STAGING THEIR OWN ACT. I HATE A RIVAL ACT."),
    ],
  },
  beach: {
    caught: [
      cap("THE TROPIC ISLES. THE TIDE IS HIGH OVER THE BOARDWALKS, AND IT ISN'T GOING DOWN."),
      say(
        "tidewyrm",
        "WELCOME, WELCOME! I'M TIDEWYRM. THE WATER? MY TOLL. YOU'LL PAY IT IN RACES.",
      ),
      say(
        "tidewyrm",
        "THE KING'S LAW, YES, YES: WIN FOUR, BEAT MY TREASURE, AND YOU BOTH GO FREE. ROUGHLY.",
      ),
      cap("ON THE PIER, A HOODED FIGURE. A WAVE BREAKS, AND THE PIER IS EMPTY."),
    ],
    stands: [
      say("tidewyrm", "LOVELY RACING. LOVELY. NOW, WHAT'S ALL THIS ABOUT MY STONE?"),
      say(
        "tidewyrm",
        "SOMETHING'S BEEN SWIMMING ROUND MY STONE. NOTHING SWIMS IN MY WATER WITHOUT PAYING.",
      ),
    ],
    challenge: [
      "The Treasure",
      [
        say(
          "tidewyrm",
          "AND NOW, MY TREASURE. THE FASTEST THING IN THE ISLES, AND ALL MINE. RAPTOR!",
        ),
        say("raptor", "HE CALLS ME HIS TREASURE. HE KEEPS ME IN A CHEST WHEN I'M NOT RACING."),
        say("raptor", "SO DON'T YOU DARE GO EASY ON ME. ONCE ROUND THE ISLES. GO!"),
      ],
    ],
    prize: [
      "The Fine Print",
      [
        say("tidewyrm", "OH, WELL DONE! YES, YES, FREEDOM. HERE'S THE CONTRACT."),
        say(
          "tidewyrm",
          "AND IF YOU READ THE FINE PRINT: FREEDOM BEGINS AFTER A HUNDRED MORE RACES.",
        ),
        say(
          "crowd",
          "THAT'S NOT THE KING'S LAW! THE WINNER'S CREW GOES FREE! AND THE CHAMPION WITH THEM!",
        ),
        say(
          "tidewyrm",
          "...EVERYONE'S A LAWYER. FINE. FINE! TAKE HER. FREE FROM MY GAMES. NOT ONE BIT MORE.",
        ),
        say("raptor", "I KNOW EVERY SMUGGLER ON THESE ISLANDS. AND THEY ALL OWE ME."),
        cap("RAPTOR JOINS YOUR CREW! (SWITCH TO RAPTOR TO GET PAST THE SEA CAVE'S GUARDS.)", {
          crew: "raptor",
          switchTo: "raptor",
        }),
      ],
    ],
    underground: [
      cap("A SEA CAVE AT LOW TIDE. THE GUARDS ARE SITTING ON A CHEST THAT ISN'T THEIRS."),
      say("guard", "RAPTOR? OUT OF THE CHEST AT LAST! WHAT'S IT TO BE?"),
      say("raptor", "THE LAST TUNNEL. THE ONE UNDER THE BORDER, INTO THE DRAGON KINGDOM."),
      say("guard", "NOBODY USES THAT ONE. NOBODY COMES BACK. WIN THE GAME AND IT'S YOURS ANYWAY."),
    ],
    key: [
      "The Last Key",
      [
        say(
          "guard",
          "THERE. THE LAST KEY. THE TUNNEL COMES UP ON THE OLD CAUSEWAY, PAST THE BORDER.",
        ),
        say("elder", "THE DRAGON KINGDOM. A CHAMPION IS GOING TO THE KING AFTER ALL."),
        say("rex", "A CHAMPION AND A CREW."),
      ],
    ],
    stone: [
      cap("MEANWHILE, AT THE TROPIC ISLES' PACT STONE..."),
      say("tidewyrm", "CRACKED. THAT'S FOUR. ALL FOUR STONES, ALL CRACKED."),
      say("tidewyrm", "THE KING WILL WANT TO KNOW. AND HE'LL PAY TO KNOW IT."),
    ],
  },
};

for (const [k, d] of Object.entries(ACT2) as [KingdomId, Kingdom2][]) {
  const track = KINGDOMS.find((x) => x.id === k)!.courses[0]!.track;
  const bd = { track, color: "#3a5a7a" };
  scenes.push(
    S(sceneOf(k, "caught"), "Caught", bd, d.caught),
    S(sceneOf(k, "stands"), "In the Stands", bd, d.stands),
    S(sceneOf(k, "challenge"), d.challenge[0], bd, d.challenge[1]),
    S(sceneOf(k, "prize"), d.prize[0], bd, d.prize[1]),
    S(sceneOf(k, "underground"), "The Underground", { ...bd, color: "#1a1a2a" }, d.underground),
    S(sceneOf(k, "key"), d.key[0], { ...bd, color: "#1a1a2a" }, d.key[1]),
    S(sceneOf(k, "stone"), "The Cracked Stone", { ...bd, color: "#0a0a1a" }, d.stone),
  );
}

// ---------------------------------------------------------------- Act IV, kingdom by kingdom

/** The dragon's answer when the new stone forces its race. */
const STONE_LINE: Record<string, string> = {
  valley: "I DON'T HAVE TO... I... I HAVE TO RACE YOU?",
  snow: "A NEW LAW. THEN I AM BOUND BY IT. I ACCEPT YOUR CHALLENGE.",
  desert: "A RACE? NOW? I HAVEN'T EVEN DONE MY HAIR. FINE! THE SHOW MUST GO ON.",
  beach: "BOUND? ME? THERE'S ALWAYS A WAY OUT OF A CONTRACT. RIGHT AFTER THIS RACE.",
};
/** The dragon's last word, and how it goes. */
const YIELD_LINE: Record<string, [string, string]> = {
  valley: [
    "THIS ISN'T OVER. YOU HEAR ME? THIS ISN'T OVER!",
    "CINDERJAW WON'T EVEN LOOK AT YOU. HE FLIES HOME TO THE DRAGON KINGDOM.",
  ],
  snow: [
    "THIS IS NOT THE PACT I KNEW. BUT IT IS A PACT. I GO.",
    "RIMEFANG BOWS, AND FLIES HOME TO THE DRAGON KINGDOM.",
  ],
  desert: [
    "A BAD ACT, THIS RAGE. TERRIBLE REVIEWS. I'M LEAVING.",
    "SCORCHWIND MAKES A GRAND EXIT, INTO HIS OWN STORM, HOME TO THE DRAGON KINGDOM.",
  ],
  beach: [
    "FINE. A FREE TIP, SINCE YOU NEVER PAY: THE LAST FOUR SHARDS FELL ON THE KING'S OWN COURSES.",
    "TIDEWYRM SLINKS HOME TO THE DRAGON KINGDOM.",
  ],
};

for (const k of KINGDOMS) {
  const d = DRAGON_OF[k.id]!;
  const D = k.boss.name.toUpperCase();
  const ruin = k.courses[0]!.ruin ?? k.courses[0]!.track;
  // The first new stone says its laws in full; the others are the same stone again.
  const first = k.id === "valley";
  scenes.push(
    S(sceneOf(k.id, "new_stone"), "A New Stone", { track: ruin, color: "#2a1a0a" }, [
      ...(first
        ? [
            cap("THE FOUR SHARDS RISE FROM YOUR HANDS AND FLY TO CINDERJAW'S LAIR."),
            cap("THEY JOIN INTO A STONE: A NEW PACT STONE, GLOWING WITH LUMEN'S LIGHT."),
            cap("TWO LAWS BURN INTO IT. ONE: A CHALLENGE MADE AT THIS STONE MUST BE ANSWERED."),
            cap(
              "TWO: IF THE CHALLENGER WINS, THE ONE THEY CHALLENGED GIVES UP ALL CLAIM TO THE CREWS' LANDS, AND GOES HOME.",
            ),
          ]
        : [cap(`FOUR SHARDS. A NEW STONE RISES AT ${D}'S LAIR, WITH THE SAME TWO LAWS.`)]),
      say("you", `${D}. I CHALLENGE YOU.`),
      say(d, STONE_LINE[k.id]!),
    ]),
    S(sceneOf(k.id, "yield"), "The Yield", { track: ruin, color: "#3a6a9a" }, [
      cap(`YOU WIN. BY THE STONE'S SECOND LAW, ${D} GIVES UP ${LAND[k.id]} AND GOES HOME.`),
      say(d, YIELD_LINE[k.id]![0]),
      cap(YIELD_LINE[k.id]![1]),
      cap(
        `THE NEW STONE'S LIGHT SPREADS, AND THE RUINS MEND. ${LAND[k.id]} ${k.id === "beach" ? "ARE" : "IS"} RESTORED!`,
      ),
      cap(`(THE SMUGGLERS' TUNNEL LEADS ON TO ${LAND[k.next]}.)`),
    ]),
  );
}

// Racing Adventure as a kingdom's own champion (an unlocked racer), their cousin takes
// their part (Blake, Oct 27): every line of theirs is the cousin's, and the cousin joins
// your crew in their place.
for (const champ of Object.values(CHAMP_OF))
  CAST[`${champ}_cousin`] = { ...CAST[champ]!, name: `${CAST[champ]!.name}'s Cousin` };

/** A scene's lines as they play for a file raced as `racer`. */
export function beatsFor(scene: Scene, racer: string): Beat[] {
  const champ = Object.values(CHAMP_OF).find((c) => c === racer);
  if (!champ) return scene.beats;
  const NAME = CAST[champ]!.name.toUpperCase();
  const cousin = `${champ}_cousin`;
  const named = new RegExp(`\\b${NAME}\\b(?!'S COUSIN)`, "g");
  return scene.beats.map((b) => {
    if (b.crew === champ)
      return {
        ...b,
        text: `${NAME}'S COUSIN JOINS YOUR CREW IN ${NAME}'S PLACE.${b.switchTo ? " (THE CAVE'S GUARDS WILL KNOW YOUR FACE.)" : ""}`,
      };
    if (b.switchTo === champ)
      return { ...b, text: "(THE CAVE'S GUARDS WILL KNOW YOUR FACE: DRIVE STRAIGHT ON IN.)" };
    const text = b.text.replace(named, `${NAME}'S COUSIN`);
    return { ...b, who: b.who === champ ? cousin : b.who, text };
  });
}

export const SCENES: Record<string, Scene> = Object.fromEntries(scenes.map((s) => [s.id, s]));
export const sceneById = (id: string) => SCENES[id];
