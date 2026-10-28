/**
 * Adventure's story scenes, as data: who speaks and what they say (the approved story,
 * Blake, Oct 27: claude/kartipelago-story.md). Almost every scene is staged in the 3D
 * world (staged.ts says where everyone stands and what the camera does for each line);
 * the opening is a storybook, over a picture.
 *
 * A scene is a list of beats: a line from someone, or a caption (who: "").
 */
import type { RacerId } from "../render/racers/designs";
import { KINGDOMS, OPENING, nameOf, sceneOf, type KingdomId } from "./data";

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

const scenes: Scene[] = [
  // ---------------------------------------------------------------- the opening
  S(OPENING, "The First Race", { color: "#e8d6a8", storybook: true }, [
    cap("LONG AGO, THE DRAGONS AND THE FIRST RACING CREWS WENT TO WAR OVER THE LANDS.", {
      fx: "dragons",
    }),
    cap(
      "THE WAR BURNED FOR YEARS. AT LAST BOTH SIDES AGREED TO SETTLE IT WITH ONE RACE: THE WINNER WOULD KEEP THE LAND.",
    ),
    cap("THE DRAGONS FLEW FASTER THAN ANYTHING ALIVE. BUT AT THE LAST TURN, A HORN SOUNDED...", {
      fx: "horn",
    }),
    cap("...AND THE CREWS CROSSED THE LINE FIRST."),
    cap(
      "THE DRAGONS SWORE THE DRAGON PACT. ITS FIVE STONES WERE RAISED: ONE IN EACH KINGDOM, AND THE HEART STONE IN THEIR OWN.",
      {
        fx: "light",
      },
    ),
    cap("THE DRAGONS WITHDREW BEHIND THE BORDER. AND THE PACT SAID ONE THING MORE:"),
    cap("EVERY HUNDRED YEARS, A CHAMPION GOES TO THE KING."),
  ]),

  // ---------------------------------------------------------------- Act I: the valley
  S(
    sceneOf("valley", "festival"),
    "The Summer Festival",
    { track: "riverbend_palms", color: "#3a7a3a" },
    [
      cap(
        "DINOSAUR VALLEY. THE SUMMER FESTIVAL IS IN FULL SWING, AND EVERY CREW IN THE VALLEY IS HERE.",
      ),
      say(
        "elder",
        "A NEW FACE! AND NO CREW COLOURS? THEN YOU RACE FOR YOURSELF. WELCOME, STRANGER.",
      ),
      say(
        "elder",
        "FOUR COURSES, ONE FESTIVAL CUP. WIN ALL FOUR AND THE WHOLE VALLEY WILL KNOW YOUR NAME.",
      ),
      say("lumen", "ELDER, TELL IT AGAIN. THE FIRST RACE. WHAT DID THE HORN SOUND FOR?"),
      say("elder", "NOT NOW, LUMEN. IT'S A FESTIVAL STORY, THAT'S ALL. GO AND WATCH THE RACES."),
      say("lumen", "...IT'S ALWAYS JUST A STORY."),
    ],
  ),
  S(sceneOf("valley", "challenge"), "The Lone Racer", { track: "ember_peak", color: "#7a5a1a" }, [
    say("rex", "SO YOU'RE THE ONE WHO TOOK ALL FOUR. NOT BAD, FOR A NOBODY WITH NO CREW."),
    say(
      "rex",
      "I DON'T HAVE A CREW EITHER. NEVER NEEDED ONE. I'M REX, AND I'M THE BEST IN THIS VALLEY.",
    ),
    say("rex", "YOU WANT TO BE THE BEST? BEAT ME. ONCE ROUND THE VALLEY, YOU AND ME. RIGHT NOW!"),
  ]),
  S(sceneOf("valley", "prize"), "A Crew of Two", { track: "riverbend_palms", color: "#3a7a3a" }, [
    say("rex", "...YOU ACTUALLY BEAT ME. NOBODY BEATS ME."),
    say(
      "rex",
      "FINE. A LONER WITH NO CREW, AND NOW THERE'S TWO OF US. I SUPPOSE THAT MAKES US A CREW.",
    ),
    cap("REX JOINS YOUR CREW! (YOU CAN RACE AS REX IN EVERY MODE NOW.)", { crew: "rex" }),
    say("elder", "A NEW CREW, BORN ON FESTIVAL DAY! NOW THAT'S A GOOD OMEN."),
  ]),
  S(
    sceneOf("valley", "hundredth"),
    "The Hundredth Summer",
    { track: "ember_peak", color: "#7a2618" },
    [
      say(
        "elder",
        "FESTIVAL DAY... THE HUNDREDTH SUMMER. A HUNDRED SUMMERS SINCE THE LAST CHAMPION WENT TO THE KING.",
      ),
      say("elder", "NO. NO, NO. SOMEBODY HAD TO GO. DID ANYONE GO? DID ANYONE EVEN REMEMBER?"),
      cap("A SHADOW CROSSES THE SUN."),
      say(
        "cinderjaw",
        "NOBODY CAME. A HUNDRED YEARS, AND NOT ONE CHAMPION. BY THE PACT, THIS VALLEY IS MINE.",
      ),
      say("cinderjaw", "THE LAW SAYS I RULE IT, NOT BURN IT. FOR NOW."),
      say("cinderjaw", "SEAL THE BORDERS! ROUND THEM UP! THE RACES BELONG TO ME NOW."),
      cap("CINDERJAW'S GUARDS SPREAD THROUGH THE VALLEY."),
    ],
  ),
  S(sceneOf("valley", "way_out"), "One Way Out", { track: "ember_peak", color: "#4a2a1a" }, [
    say(
      "elder",
      "THIS IS MY FAULT. I KEPT ALL THE OLD STORIES, AND I FORGOT THE ONE THAT MATTERED.",
    ),
    say("elder", "BUT THE PACT CUTS BOTH WAYS. A CHAMPION WHO BEATS THE KING WINS THE LANDS BACK."),
    say("you", "THEN WE GO TO THE KING."),
    say(
      "elder",
      "WITH THE BORDERS SEALED? A SEALED KINGDOM HAS ONE WAY OUT: THE SMUGGLERS' TUNNEL.",
    ),
    say(
      "elder",
      "THE SMUGGLERS RUN THE UNDERGROUND GAMES, AND THEY ONLY LET IN RACERS THEY RESPECT.",
    ),
    say(
      "rex",
      "LUCKY FOR YOU, THEY RESPECT ME. THEIR CAVE'S UP ON EMBER'S LOWER SLOPE. LET ME DRIVE.",
    ),
    cap("(SWITCH TO REX: PAUSE, THEN YOUR CREW. THEN FIND THE LOOKOUT CAVE.)", { switchTo: "rex" }),
  ]),
  S(
    sceneOf("valley", "underground"),
    "The Underground",
    { track: "ember_peak", color: "#2a1a10" },
    [
      cap("A CAVE BEHIND A ROCKFALL, AND TWO GUARDS WHO LOOK LIKE THEY'D SELL THEIR OWN TAILS."),
      say("guard", "WELL, WELL. REX. WE HEARD YOU LOST TODAY."),
      say("rex", "TO THIS ONE. THAT'S WHY THEY'RE WITH ME. WE WANT IN, AND WE WANT THE TUNNEL."),
      say("guard", "THE TUNNEL'S FOR WINNERS. WIN OUR GAME, AND IT'S YOURS."),
    ],
  ),
  S(sceneOf("valley", "key"), "The Smugglers' Key", { track: "ember_peak", color: "#2a1a10" }, [
    say("guard", "HUH. YOU ACTUALLY WON. A DEAL'S A DEAL."),
    say(
      "guard",
      "HERE: THE SMUGGLERS' KEY. THE TUNNEL COMES OUT IN THE BURNT GORGE, PAST CINDERJAW'S BORDER.",
    ),
    say("elder", "WHERE IS LUMEN? HE WAS RIGHT BEHIND US."),
    say("elder", "...HE'LL FIND US. HE ALWAYS DOES."),
  ]),
  S(
    sceneOf("valley", "stone"),
    "Who's Been at the Stone?",
    { track: "ember_peak", color: "#1a0a0a" },
    [
      cap("AT THE VALLEY'S PACT STONE, IN THE DARK..."),
      say("cinderjaw", "A CRACK. RIGHT THROUGH THE OLD STONE. WHO'S BEEN AT IT?"),
      say(
        "cinderjaw",
        "SOMEBODY IN MY VALLEY IS PLAYING GAMES. I DON'T LIKE GAMES I DIDN'T START.",
      ),
    ],
  ),

  // ---------------------------------------------------------------- Act III
  S("dragon_challenger", "The Challenger", { track: "dragon_isles", color: "#3a1a2a" }, [
    cap("THE DRAGON KINGDOM. NO CREW HAS DRIVEN HERE IN A HUNDRED YEARS."),
    cap("THE KING COMES DOWN TO MEET YOU."),
    say("king", "A CHALLENGER. A HUNDRED YEARS LATE, BUT A CHALLENGER."),
    say("king", "THE PACT SAYS I CANNOT REFUSE YOU. VERY WELL. WIN MY GAMES, AND YOU MAY RACE ME."),
    cap(
      "FOUR DRAGONS SETTLE ON THE ROOFTOPS TO WATCH: CINDERJAW, RIMEFANG, SCORCHWIND AND TIDEWYRM.",
    ),
    say("lumen", "YOU CAME. I KNEW YOU WOULD."),
    say("elder", "LUMEN! WHERE HAVE YOU BEEN?"),
    say("lumen", "CLOSE BY. ALWAYS CLOSE BY. GO ON. HE'S WAITING."),
  ]),
  S("dragon_before_king", "Before the King", { track: "dragon_isles", color: "#1a0a0a" }, [
    say("cinderjaw", "FOUR WINS. IN OUR OWN KINGDOM."),
    say("rimefang", "BY THE LAW, THE CHALLENGER HAS EARNED THE RACE."),
    say("scorchwind", "AND WHAT A RACE IT'LL BE! I'D SELL TICKETS, IF ANYONE HAD ANY MONEY LEFT."),
    say("tidewyrm", "MY MONEY'S ON THE KING. MY MONEY'S ALWAYS ON THE KING."),
    say("king", "ENOUGH. TO THE LINE."),
  ]),
  S("dragon_return", "The Return", { track: "dragon_isles", color: "#1a0a1a" }, [
    cap(
      "THE KING IS BEATEN. FOR THE FIRST TIME IN A THOUSAND YEARS, A DRAGON MUST KEEP THE RETURN.",
    ),
    say("king", "BY THE PACT... THE LANDS GO BACK TO THE CREWS."),
    cap("HE WALKS TO THE HEART STONE AND LAYS HIS CLAW ON IT."),
    cap("THE STONE WAKES."),
  ]),
  S("dragon_lumen", "Lumen", { track: "dragon_isles", color: "#1a0a1a" }, [
    say("lumen", "NOW."),
    cap("LUMEN THROWS BACK HIS ROBE. HIS WINGS UNFOLD."),
    say("elder", "LUMEN... YOU'RE A DRAGON."),
    say("king", "A HATCHLING? WHAT ARE YOU DOING? STEP AWAY FROM THE STONE!"),
    say("lumen_dragon", "I'M SORRY, ELDER. THIS IS THE ONLY WAY ANY OF US GET FREE."),
    cap("LUMEN STRIKES THE WAKING STONE. FAR AWAY, FOUR CRACKED STONES ANSWER."),
    cap("THE DRAGON PACT SHATTERS."),
    cap("THE BLAST TEARS THROUGH THE DRAGON KINGDOM. WHEN THE LIGHT FADES, LUMEN IS GONE."),
  ]),
  S("dragon_horn", "The Horn", { track: "dragon_isles_ruin", color: "#1a0a0a" }, [
    cap("SMOKE. RUBBLE. THE HEART STONE IN PIECES."),
    say("king", "NOTHING HOLDS ME NOW. NO PACT. NO LAW. NOTHING."),
    say("king", "AND YOU WILL BURN FIRST."),
    say("elder", "NOT TODAY."),
    cap("THE OLD HORN SOUNDS. THE KING DROPS LIKE A STONE."),
    say("rex", "HE'S DOWN! THE KING IS DOWN!"),
    cap("THE CREWS CHEER. THE PACT IS GONE AND THE KING IS BEATEN. IT'S OVER."),
  ]),
  S("dragon_rage", "The Rage", { track: "dragon_isles_ruin", color: "#1a0a0a" }, [
    cap("...BUT A HORN ONLY EVER STUNNED A DRAGON."),
    cap("THE KING WAKES IN THE RUINS OF HIS KINGDOM."),
    say("king", "MY KINGDOM. MY HOME. YOUR CREWS DID THIS. YOUR CREWS ALWAYS DO THIS."),
    say("king", "THE PACT IS GONE. THERE IS NO LAW LEFT TO STOP US. DRAGONS! TAKE IT ALL!"),
  ]),
  S("rage_valley", "The Rage", { track: "ember_peak_ruin", color: "#3a0a00" }, [
    cap("CINDERJAW BURNS THE VALLEY HE WAS TOLD NOT TO."),
  ]),
  S("rage_snow", "The Rage", { track: "frostveil_citadel_ruin", color: "#0a1a2a" }, [
    cap("RIMEFANG FREEZES THE SNOW KINGDOM SOLID, AS CALMLY AS FILING PAPERWORK."),
  ]),
  S("rage_desert", "The Rage", { track: "canyon_dash_ruin", color: "#3a2a0a" }, [
    cap("SCORCHWIND BURIES DESERT WORLD IN SAND, THEN SULKS THAT THERE'S NOBODY LEFT TO WATCH."),
  ]),
  S("rage_beach", "The Rage", { track: "coral_cove_ruin", color: "#0a2a2a" }, [
    cap("TIDEWYRM DROWNS THE TROPIC ISLES."),
  ]),
  S("rage_shards", "The Rage", { track: "dragon_isles_ruin", color: "#000000" }, [
    cap("IN THE RUINS OF THE CITADEL, THE BROKEN HEART STONE STILL GLOWS."),
    cap(
      "LUMEN'S LIGHT BURSTS OUT OF IT AND SCATTERS ACROSS ALL FIVE KINGDOMS: A RAIN OF LIGHT SHARDS.",
    ),
    cap("THEN A BLOW YOU NEVER SEE COMING, AND EVERYTHING GOES DARK."),
  ]),

  // ---------------------------------------------------------------- Act IV
  S(sceneOf("valley", "rescue"), "Rex", { track: "ember_peak_ruin", color: "#2a1a10" }, [
    cap("YOU WAKE IN A CAGE IN THE RUINS OF DINOSAUR VALLEY. CINDERJAW'S CAGE."),
    say("rex", "PSST. HOLD STILL. THESE LOCKS ARE OLDER THAN I AM."),
    say("rex", "GOT IT! COME ON, BEFORE HIS GUARDS COME BACK."),
    say("elder", "YOU'RE ALIVE, THANK THE STONES. NOW LOOK WHAT I FOUND IN THE ASHES."),
    say(
      "elder",
      "LUMEN'S LIGHT. I'D KNOW IT ANYWHERE. A PIECE OF IT FELL ON EVERY COURSE IN THE VALLEY.",
    ),
    say(
      "elder",
      "A SHARD COMES ONLY TO SOMEONE WHO WINS A RACE FAIRLY. WIN ENOUGH OF THEM, AND...",
    ),
    say("elder", "...AND WE COULD MAKE A NEW PACT. A FAIR ONE."),
    cap(
      "(EACH RUINED COURSE HOLDS SHARD PIECES: COLLECT THEM ALL AND FINISH 1ST TO WIN ITS LIGHT SHARD.)",
    ),
  ]),

  // ---------------------------------------------------------------- Act V
  S("dragon_court", "The Ruined Court", { track: "dragon_isles_ruin", color: "#1a0a1a" }, [
    cap("THE DRAGON KINGDOM, STILL IN RUINS FROM THE BLAST."),
    cap(
      "THE FOUR DRAGONS STAND AT COURT, SENT HOME BY THE YIELD. THE KING SITS ON A BROKEN THRONE.",
    ),
    say("king", "YOU AGAIN. STILL PLAYING WITH THE HATCHLING'S LIGHT."),
    say("cinderjaw", "LET ME BURN THEM, MY KING."),
    say("king", "...NO. LET THEM TRY. THE LAST FOUR SHARDS FELL ON MY OWN COURSES."),
  ]),
  S("dragon_heart", "The Heart Stone", { track: "dragon_isles_ruin", color: "#2a1a0a" }, [
    cap("THE LAST FOUR SHARDS FLY TO THE CITADEL. THE HEART STONE RISES AGAIN, WHOLE AND SHINING."),
    cap("THE NEW PACT IS WHOLE."),
    say("elder", "BEFORE IT BINDS YOU, KING PYRRHAX, THERE IS SOMETHING YOU SHOULD HEAR. FROM US."),
    say(
      "elder",
      "THE FIRST RACE. THIS HORN SOUNDED AT THE LAST TURN AND STUNNED YOUR KIND. THE FOUNDERS CHEATED.",
    ),
    say("elder", "THE ELDERS KEPT THAT SECRET FOR A THOUSAND YEARS. NO MORE."),
    cap("MOSSBACK BREAKS THE FOUNDERS' HORN ACROSS HIS KNEE."),
    say("king", "...A THOUSAND YEARS I WAITED FOR ONE OF YOU TO SAY IT."),
    cap("THE HEART STONE BURNS WITH ITS FIRST LAW: A CHALLENGE MUST BE ANSWERED."),
    say("king", "THEN RACE ME. HONESTLY, THIS TIME. BOTH OF US."),
  ]),
  S("dragon_lumen_returns", "Lumen Returns", { track: "dragon_isles", color: "#f4e8cc" }, [
    say("king", "...BEATEN. FAIRLY. UNDER A LAW MADE BY ONE OF MY OWN."),
    say("king", "I GIVE UP MY CLAIM TO THE LANDS. AND THE GRUDGE WITH IT."),
    cap("BOTH SIDES HAVE ACCEPTED THE PACT. IT NO LONGER NEEDS LUMEN'S LIGHT TO HOLD."),
    cap("THE HEART STONE OPENS, AND A DRAGON STEPS OUT OF THE LIGHT: FULL-GROWN, AND GOLDEN."),
    say("lumen_dragon", "HELLO, ELDER. I TOLD YOU I'D FIND YOU."),
    say("king", "YOU GAVE YOURSELF UP. FOR US. FOR ALL OF US."),
    say("lumen_dragon", "THE BORDER IS GONE, MY KING. WE'RE FREE TOO."),
    cap(
      "THE DRAGON KINGDOM MENDS IN THE LIGHT. RIMEFANG, SCORCHWIND AND TIDEWYRM BOW TO THE NEW PACT.",
    ),
    say("cinderjaw", "NOT ME. NO PACT HOLDS ME. NOT THIS ONE, NOT ANY!"),
    cap("CINDERJAW FLIES OFF, PAST THE EDGE OF THE WORLD. NOBODY KNOWS WHERE."),
  ]),
  S("ending", "Home", { track: "riverbend_palms", color: "#3a7a3a" }, [
    cap("AND SO THE KINGDOMS WERE RESTORED."),
    cap("THAT SUMMER, THE FESTIVAL HAD NEW RACERS: DRAGONS, RACING FOR FUN, AND LOSING HONESTLY."),
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
      cap("THE SNOW KINGDOM. YOU COME OUT OF THE GORGE STRAIGHT INTO A WALL OF GUARDS."),
      say("rimefang", "TRAVELLERS. FROM A SEALED KINGDOM, NO LESS. HOW IRREGULAR."),
      say(
        "rimefang",
        "THE LAW IS CLEAR. WE RULE, SO THE GAMES GO ON, AND EVERY STRANGER IS A CAPTIVE. YOU WILL RACE.",
      ),
      cap("IN THE CROWD, A HOODED FIGURE WATCHES. THEN IT IS GONE."),
    ],
    stands: [
      say("rimefang", "THE CAPTIVES RACE WELL. BUT THAT IS NOT WHAT TROUBLES ME."),
      say("rimefang", "SOMEONE HAS BEEN READING WHERE THEY SHOULDN'T. FIND OUT WHO."),
      say("guard", "YES, LORD RIMEFANG."),
    ],
    challenge: [
      "The Prized Racer",
      [
        say("rimefang", "FOUR WINS. THEN THE LAW ALLOWS YOU ONE MORE RACE: AGAINST MY CHAMPION."),
        say("brachio", "I DON'T WANT TO DO THIS. BUT IF I LOSE ON PURPOSE, HE'LL KNOW."),
        say("brachio", "SO I WON'T. ONCE ROUND THE KINGDOM. GIVE IT EVERYTHING."),
      ],
    ],
    prize: [
      "The Winner's Prize",
      [
        cap("BY THE PACT, A RACER WHO WINS A DRAGON'S GAMES WINS THEIR CREW'S FREEDOM."),
        say("rimefang", "AND YOU HAVE WON. YOU AND BRACHIO ARE FREE, AS THE LAW REQUIRES."),
        say(
          "rimefang",
          "FREE FROM MY GAMES. NOT FROM MY KINGDOM. THE BORDER STAYS SHUT. THE LAW IS SATISFIED.",
        ),
        say(
          "brachio",
          "...HE'S RIGHT, AND HE KNOWS IT. BUT A FREE RACER CAN GO WHERE A CAPTIVE CAN'T.",
        ),
        say("brachio", "THE UNDERGROUND. THE SMUGGLERS HERE KNOW MY NAME. I'M WITH YOU."),
        cap("BRACHIO JOINS YOUR CREW! (SWITCH TO BRACHIO TO GET PAST THE ICE CAVE'S GUARDS.)", {
          crew: "brachio",
          switchTo: "brachio",
        }),
      ],
    ],
    underground: [
      cap("A CAVE IN THE ICE. THE GUARDS HERE ARE BIGGER, AND SKETCHIER."),
      say("guard", "BRACHIO! RIMEFANG LET YOU GO? HE NEVER LETS ANYTHING GO."),
      say("brachio", "HE DIDN'T. THE LAW DID. WE WANT THE TUNNEL."),
      say("guard", "WIN THE GAME, GET THE KEY. SAME AS ALWAYS."),
    ],
    key: [
      "The Frozen Pass",
      [
        say("guard", "A WIN'S A WIN. HERE'S THE KEY: THE TUNNEL COMES OUT ON THE FROZEN PASS."),
        say("you", "HAS ANYONE SEEN A HOODED KID? ABOUT THIS TALL?"),
        say("guard", "SEEN NOTHING. HEARD NOTHING. THAT'S HOW WE STAY IN BUSINESS."),
      ],
    ],
    stone: [
      cap("THE SNOW KINGDOM'S PACT STONE, AT THE EDGE OF THE FROZEN LAKE."),
      say("rimefang", "CRACKED. BY NO TOOL I KNOW."),
      say("rimefang", "THE LAW HAS NO WORD FOR THIS. I WILL HAVE TO WRITE ONE."),
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
        "RACE WELL AND THE CROWD LOVES YOU. RACE BADLY AND, WELL, THE CROWD STILL LOVES ME.",
      ),
      cap("UP ON A ROOFTOP, A HOODED FIGURE. WHEN YOU LOOK AGAIN, IT IS GONE."),
    ],
    stands: [
      say("scorchwind", "WHAT A SHOW! WHAT A CROWD! WHAT A... WAIT. WHO LEFT?"),
      say("scorchwind", "SOMEBODY WALKED OUT ON MY SHOW. NOBODY WALKS OUT ON MY SHOW!"),
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
        say("stego", "BEAT ME, NEWCOMER. I'D LIKE TO SEE WHAT HAPPENS THEN."),
      ],
    ],
    prize: [
      "The Winner's Prize",
      [
        cap("THE CROWD GOES SILENT. THE STAR HAS LOST."),
        say(
          "scorchwind",
          "...BY THE PACT, THE WINNER'S CREW GOES FREE. AND I ALWAYS KEEP MY WORD. IN PUBLIC.",
        ),
        say(
          "scorchwind",
          "WHAT A TWIST! A CHAMPION FREED! WHO WROTE THIS SHOW? I DID! APPLAUD ME!",
        ),
        say(
          "stego",
          "HE'LL SPIN ANYTHING. BUT FREE IS FREE. THE SMUGGLERS UNDER THE SAND OWE ME A FAVOUR.",
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
      say("stego", "HE KNOWS. HE'S TELLING EVERYONE IT WAS HIS IDEA. WE NEED THE TUNNEL."),
      say("guard", "THE GAME FIRST. THE STAR SHOULD LIKE THAT."),
    ],
    key: [
      "The Dust Road",
      [
        say("guard", "A FINE PERFORMANCE. THE KEY: THE TUNNEL COMES OUT ON THE DUST ROAD."),
        say("stego", "THE DUST ROAD GOES TO THE TROPIC ISLES. TIDEWYRM'S. WATCH YOUR POCKETS."),
      ],
    ],
    stone: [
      cap("DESERT WORLD'S PACT STONE, HALF BURIED IN THE DUNES."),
      say("scorchwind", "A CRACK! IN MY STONE! IN MY KINGDOM! DURING MY SHOW!"),
      say("scorchwind", "SOMEBODY'S STAGING THEIR OWN ACT. I HATE A RIVAL ACT."),
    ],
  },
  beach: {
    caught: [
      cap("THE TROPIC ISLES. THE TIDE IS HIGH OVER THE BOARDWALKS, AND IT ISN'T GOING DOWN."),
      say(
        "tidewyrm",
        "WELCOME, WELCOME! THE WATER? THAT'S MY TOLL. EVERYONE PAYS IT. YOU'LL PAY IT IN RACES.",
      ),
      say(
        "tidewyrm",
        "WIN ENOUGH AND WHO KNOWS? MAYBE I'LL LET YOU OFF. I'M VERY GENEROUS. ASK ANYONE.",
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
        say(
          "tidewyrm",
          "OH, WELL DONE! YES, YES, THE WINNER'S PRIZE. FREEDOM. HERE'S THE CONTRACT.",
        ),
        say(
          "tidewyrm",
          "AND IF YOU READ THE FINE PRINT, IT SAYS: FREEDOM BEGINS AFTER A HUNDRED MORE RACES.",
        ),
        say(
          "crowd",
          "THAT'S NOT THE PACT! THE WINNER'S CREW GOES FREE! THE WINNER'S CREW GOES FREE!",
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
      say("raptor", "THE LAST TUNNEL. THE ONE TO THE DRAGON KINGDOM."),
      say("guard", "NOBODY USES THAT ONE. NOBODY COMES BACK. WIN THE GAME AND IT'S YOURS ANYWAY."),
    ],
    key: [
      "The Last Key",
      [
        say("guard", "THERE. THE LAST KEY. THE TUNNEL COMES UP ON TIDEWYRM'S OLD CAUSEWAY."),
        say(
          "elder",
          "THE DRAGON KINGDOM. A HUNDRED YEARS LATE, BUT A CHAMPION IS GOING TO THE KING.",
        ),
        say("rex", "A CHAMPION AND A CREW."),
      ],
    ],
    stone: [
      cap("THE TROPIC ISLES' PACT STONE, OUT ON THE REEF."),
      say("tidewyrm", "CRACKED. THAT'S FOUR. FOUR STONES, FOUR CRACKS."),
      say("tidewyrm", "THE KING SHOULD HEAR ABOUT THIS. FOR A PRICE."),
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
    S(sceneOf(k, "stone"), "Who's Been at the Stone?", { ...bd, color: "#0a0a1a" }, d.stone),
  );
}

// ---------------------------------------------------------------- Act IV, kingdom by kingdom

const STONE_LINE: Record<string, string> = {
  valley: "WHAT IS THIS? I DON'T WANT TO RACE YOU. I... I HAVE TO RACE YOU?",
  snow: "A NEW LAW. THEN I AM BOUND BY IT. I ACCEPT YOUR CHALLENGE.",
  desert: "A RACE? NOW? I HAVEN'T EVEN DONE MY HAIR. FINE! THE SHOW MUST GO ON.",
  beach: "BOUND? ME? THERE'S ALWAYS A WAY OUT OF A CONTRACT. RIGHT AFTER THIS RACE.",
};
const YIELD_LINE: Record<string, Beat[]> = {
  valley: [
    say("cinderjaw", "THIS ISN'T OVER. YOU HEAR ME? THIS ISN'T OVER!"),
    cap("CINDERJAW WON'T EVEN LOOK AT YOU. HE FLIES OFF TO THE DRAGON KINGDOM."),
  ],
  snow: [
    say("rimefang", "THIS IS NOT THE PACT I KNEW."),
    cap("RIMEFANG BOWS, AND FLIES OFF TO THE DRAGON KINGDOM."),
  ],
  desert: [
    say("scorchwind", "THE KING'S RAGE? A BAD ACT. TERRIBLE REVIEWS. I'M LEAVING."),
    cap("SCORCHWIND MAKES A GRAND EXIT, INTO HIS OWN STORM."),
  ],
  beach: [
    say("tidewyrm", "FINE. BUT BETWEEN YOU AND ME, THE KING IS AFRAID. OF WHAT, I WONDER?"),
    cap("TIDEWYRM TRIES ONE LAST TRICK, IT FAILS, AND HE SLINKS OFF TO THE DRAGON KINGDOM."),
  ],
};

for (const k of KINGDOMS) {
  const d = DRAGON_OF[k.id]!;
  const ruin = k.courses[0]!.ruin ?? k.courses[0]!.track;
  const next = nameOf(k.next).toUpperCase();
  scenes.push(
    S(sceneOf(k.id, "new_stone"), "A New Stone", { track: ruin, color: "#2a1a0a" }, [
      cap(`FOUR LIGHT SHARDS RISE FROM YOUR HANDS AND FLY TO ${k.boss.name.toUpperCase()}'S LAIR.`),
      cap("THEY BUILD A STONE: NEW, AND GLOWING WITH LUMEN'S LIGHT."),
      cap("ITS FIRST LAW BURNS INTO THE STONE: A CHALLENGE MUST BE ANSWERED."),
      say(d, STONE_LINE[k.id]!),
    ]),
    S(sceneOf(k.id, "yield"), "The Yield", { track: ruin, color: "#3a6a9a" }, [
      cap("THE STONE SPEAKS ITS SECOND LAW: WHOEVER LOSES GIVES UP THEIR CLAIM, AND LEAVES."),
      ...YIELD_LINE[k.id]!,
      cap(`THE NEW STONE'S LIGHT SPREADS ACROSS ${k.name.toUpperCase()}. THE RUINS MEND.`),
      cap(
        `${k.name.toUpperCase()} IS RESTORED! THE SMUGGLERS' TUNNEL IS OPEN AGAIN: ON TO THE ${next}.`,
      ),
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
