/**
 * The whole Adventure script, as an actor would get it (Blake, Oct 27): every scene in
 * the order it plays, when it plays, where it's staged, who's in it, every line, and the
 * stage directions (from the stagings: who flies in, rears up, breathes fire; the flashes,
 * the horn, the blackout). Made from the story's own data (scenes.ts, staged.ts), so it
 * can't drift from the game: docs/adventure-script.txt is this, written out
 * (tools/audit/script.audit.ts writes it; tests/script.test.ts checks it's up to date).
 */
import { END_CREDITS, FAKE_CREDITS, KINGDOMS, OPENING, RAGE, sceneOf } from "./data";
import { CAST, SCENES, type Beat } from "./scenes";
import { STAGED, type StagedBeat, type StagedScene } from "./staged";
import { regionById } from "../overworld/regions";

/** The story's scenes in the order they play (the dev list too), the credits among them. */
export function sceneOrder(): string[] {
  const all = Object.keys(SCENES);
  const act2 = (k: string) =>
    ["caught", "stands", "challenge", "prize", "underground", "key", "stone"].map(
      (x) => `${k}_${x}`,
    );
  const order = [
    OPENING,
    ...[
      "festival",
      "challenge",
      "prize",
      "hundredth",
      "way_out",
      "underground",
      "key",
      "stone",
    ].map((x) => sceneOf("valley", x)),
    ...act2("snow"),
    ...act2("desert"),
    ...act2("beach"),
    "dragon_challenger",
    "dragon_before_king",
    "dragon_return",
    "dragon_lumen",
    "dragon_horn",
    FAKE_CREDITS,
    ...RAGE,
    sceneOf("valley", "rescue"),
    ...KINGDOMS.flatMap((k) => [sceneOf(k.id, "new_stone"), sceneOf(k.id, "yield")]),
    "dragon_court",
    "dragon_heart",
    "dragon_lumen_returns",
    "ending",
    END_CREDITS,
  ];
  return [
    ...new Set([
      ...order.filter((x) => x in SCENES || x === FAKE_CREDITS || x === END_CREDITS),
      ...all,
    ]),
  ];
}

/** The lands as a sentence names them. */
const THE: Record<string, string> = {
  valley: "Dinosaur Valley",
  snow: "the Snow Kingdom",
  desert: "Desert World",
  beach: "the Tropic Isles",
};
const of = (k: string) => (k.endsWith("s") ? `${k}'` : `${k}'s`);

/** When each scene plays (what you've just done). */
function when(id: string): string {
  const k = KINGDOMS.find((x) => id.startsWith(`${x.id}_`));
  const step = k ? id.slice(k.id.length + 1) : "";
  const K = k ? THE[k.id]! : "";
  switch (id) {
    case OPENING:
      return "A new file is started, before you pick your racer.";
    case FAKE_CREDITS:
      return "Straight after The Horn: the credits start to roll... and break off.";
    case END_CREDITS:
      return "After the ending.";
    case "dragon_challenger":
      return "Arriving in the Dragon Kingdom through the last smugglers' tunnel.";
    case "dragon_before_king":
      return "The King's four courses won; the race for the lands starts straight after.";
    case "dragon_return":
      return "The King beaten in the race for the lands.";
    case "dragon_lumen":
      return "Straight after The Return.";
    case "dragon_horn":
      return "Straight after Lumen (the Dragon Kingdom now in ruins).";
    case RAGE[0]:
      return "Straight after the fake credits. The Rage plays on through every kingdom.";
    case "dragon_court":
      return "Arriving in the ruined Dragon Kingdom, every demi-boss yielded.";
    case "dragon_heart":
      return "The last four light shards won; the King's last race starts straight after.";
    case "dragon_lumen_returns":
      return "The King beaten under the new Pact.";
    case "ending":
      return "Straight after Lumen Returns.";
  }
  if ((RAGE as readonly string[]).includes(id)) return "The Rage, kingdom by kingdom.";
  switch (step) {
    case "festival":
      return "Your racer picked: the first thing you see in Dinosaur Valley.";
    case "challenge":
      return `Coming out of the gateway of the last of ${of(K)} four courses; the 1 on 1 starts straight after.`;
    case "prize":
      return `${k!.champion.name} beaten 1 on 1.`;
    case "hundredth":
      return "Straight after A Crew of Two, at sunset.";
    case "way_out":
      return "Straight after The Hundredth Summer.";
    case "underground":
      return `Driving into ${k!.cave} as ${k!.champion.name}; the mini-game starts straight after.`;
    case "key":
      return `The underground games' mini-game won.`;
    case "stone":
      return `Straight after the key; then you're through the smugglers' tunnel.`;
    case "caught":
      return `Arriving in ${K} out of the smugglers' tunnel.`;
    case "stands":
      return `Two of ${of(K)} four courses won.`;
    case "rescue":
      return "After the Rage: you wake in the ruined valley.";
    case "new_stone":
      return `All four of ${of(K)} light shards won; the dragon's race starts straight after.`;
    case "yield":
      return `${k!.boss.name} beaten under the new Pact Stone.`;
  }
  return "";
}

const name = (who: string) => (who ? (CAST[who]?.name ?? who).toUpperCase() : "NARRATOR (CAPTION)");

/** The score's cues, as the script names them. */
const CUE_NAME: Record<string, string> = {
  festival: "the festival",
  lumen: "Lumen's theme",
  smugglers: "the smugglers",
  conquered: "the conquered lands",
  rimefang: "Rimefang's theme",
  scorchwind: "Scorchwind's theme",
  tidewyrm: "Tidewyrm's theme",
  king: "the King's theme",
  suspense: "suspense",
  court: "the dragon court",
  shatter: "the shattering",
  false_victory: "victory (too soon)",
  rage: "the Rage",
  sorrow: "sorrow",
  hope: "hope",
  new_stone: "the new stone",
  yield: "the yield",
  confession: "the confession",
  finale: "the finale",
  home: "home",
  dread: "the Dragon's Shadow (Cinderjaw's theme)",
};
/** A dragon's pose, in words ("idle" says nothing). */
const POSE: Record<string, string> = {
  rear: "rears up",
  breathe: "breathes",
  fly: "takes to the air",
  land: "lands",
  roar: "roars",
  bow: "bows low",
  stunned: "lies stunned",
  claw: "lays a claw on the stone",
  walk: "walks",
  turn: "turns",
};
/** What each dragon breathes. */
const BREATH: Record<string, string> = {
  cinderjaw: "fire",
  rimefang: "frost",
  scorchwind: "a sandstorm",
  tidewyrm: "a flood",
  king: "fire",
  lumen_dragon: "light",
};
/** A gesture, in words. */
const GESTURE: Record<string, string> = {
  wave: "waves",
  point: "points",
  cheer: "cheers",
  nod: "nods",
  shake: "shakes his head",
  shrug: "shrugs",
  bow: "bows",
  cower: "cowers",
  think: "stops to think",
  raiseStaff: "raises his staff",
  blowHorn: "blows the Founders' Horn",
  breakHorn: "breaks the horn",
  holdOut: "holds it out",
  kneel: "sinks to his knees",
};

/** The townsfolk's gestures, all together. */
const FOLK_DO: Record<string, string> = { cheer: "cheer", cower: "cower", point: "point" };

/** A staged line's stage directions, in words. */
function directions(
  st: StagedScene,
  b: StagedBeat | undefined,
  prev: StagedBeat | undefined,
): string[] {
  if (!b) return [];
  const who = (k: string) => {
    const a = st.actors[k];
    const base = k.replace(/\d+$/, "");
    if (a?.kind === "stone") {
      const what = a.big ? "Heart Stone" : "Pact Stone";
      return a.state === "broken"
        ? `the broken ${what}`
        : a.state === "new" && !a.big
          ? "the new Pact Stone"
          : `the ${what}`;
    }
    if (k === "lumen_dragon") return "Lumen the dragon";
    if (k === "you") return "you";
    if (a?.kind === "villager") return CAST[base]?.name ?? "a townsperson";
    const name = CAST[base]?.name ?? base;
    return base !== k && k.endsWith("2") ? "the other guard" : name;
  };
  const out: string[] = [];
  const fx = b.fx ?? {};
  for (const m of b.moves ?? []) {
    const a = st.actors[m.actor];
    const flying = a?.kind === "dragon" && (m.y ?? 0) > 2;
    const landing = a?.kind === "dragon" && m.y === 0;
    const you = m.actor === "you";
    out.push(
      `${who(m.actor)} ${flying ? "flies" : landing ? "comes down to land" : a?.kind === "racer" ? (you ? "drive" : "drives") : you ? "move" : "moves"}${flying ? " overhead" : ""}.`,
    );
  }
  for (const k of fx.hide ?? []) out.push(`${who(k)} is gone.`);
  for (const k of fx.show ?? []) out.push(`${who(k)} appears.`);
  // A pose is said when it changes (a line without one is back to standing).
  for (const [k, p] of Object.entries(fx.pose ?? {})) {
    const moving = (b.moves ?? []).some((m) => m.actor === k) || (fx.show ?? []).includes(k);
    const fire = fx.fire === k && p === "breathe";
    if (POSE[p] && !moving && !fire && prev?.fx?.pose?.[k] !== p)
      out.push(`${who(k)} ${p === "breathe" ? `breathes ${BREATH[k] ?? "fire"}` : POSE[p]}.`);
  }
  if (fx.fire) out.push(`${who(fx.fire)} breathes ${BREATH[fx.fire] ?? "fire"}.`);
  for (const [k, g] of Object.entries(fx.gesture ?? {})) {
    const a = st.actors[k];
    // (Townsfolk are summed up once below.)
    if (a?.kind !== "villager" && GESTURE[g]) out.push(`${who(k)} ${GESTURE[g]}.`);
  }
  const folk = Object.entries(fx.gesture ?? {}).filter(
    ([k]) => st.actors[k]?.kind === "villager" && !CAST[k.replace(/\d+$/, "")],
  );
  if (folk.length) out.push(`The townsfolk ${FOLK_DO[folk[0]![1]] ?? "react"}.`);
  for (const [k, g] of Object.entries(fx.gesture ?? {}))
    if (st.actors[k]?.kind === "villager" && CAST[k.replace(/\d+$/, "")] && GESTURE[g])
      out.push(`${who(k)} ${FOLK_DO[g] ?? GESTURE[g]}.`);
  if (fx.rear) out.push(`${who(fx.rear)} rears up.`);
  if (fx.horn) out.push("The Founders' Horn sounds.");
  if (fx.flash) out.push("A flash.");
  if (fx.shake && fx.shake >= 1) out.push("The ground shakes.");
  if (fx.black) out.push("Blackout.");
  if (fx.music) out.push(`Music: ${CUE_NAME[fx.music] ?? fx.music}.`);
  return out.map((d) => d[0]!.toUpperCase() + d.slice(1));
}

const indent = (text: string, n: number, width = 72) => {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let line = "";
  for (const w of words) {
    if (line && line.length + 1 + w.length > width - n) {
      lines.push(line);
      line = w;
    } else line = line ? `${line} ${w}` : w;
  }
  if (line) lines.push(line);
  return lines.map((l) => " ".repeat(n) + l).join("\n");
};

/** The script, as plain text. */
export function scriptText(): string {
  const out: string[] = [];
  out.push("KARTIPELAGO: THE SHATTERED PACT");
  out.push("The Adventure mode script: every cutscene, in the order it plays.");
  out.push("");
  out.push(
    indent(
      "Made from the game's own scene data (src/adventure/scenes.ts and staged.ts): change a line there and this script changes with it. Lines are as they appear on screen. Captions are read by the narrator. Stage directions, in brackets, come from the 3D staging of each scene.",
      0,
    ),
  );
  out.push("");
  out.push("CAST");
  const cast: [string, string][] = [
    [
      "YOU",
      "Your racer (Tiko, Brakka, Pebble or Zephyr; a champion's cousin plays a champion's part).",
    ],
    [
      "ELDER MOSSBACK",
      "Keeper of the Pact: he sends the champion. Wears the Founders' Horn at his hip, and its secret.",
    ],
    [
      "LUMEN",
      "Mossback's ward, raised from an egg found in the river. Always hooded, always asking. Really a dragon, his wings hidden under the robe.",
    ],
    ["REX", "Dinosaur Valley's champion. A cocky lone racer, no crew. Your first."],
    ["BRACHIO", "The Snow Kingdom's champion, Rimefang's captive."],
    ["STEGO", "Desert World's champion, Scorchwind's star act."],
    ["RAPTOR", "Tropic Isles' champion, Tidewyrm's 'treasure'."],
    ["CINDERJAW", "Dragon of the valley: the brute. All fire, no patience."],
    ["RIMEFANG", "Dragon of the snow: the lawyer. Cold, precise, never breaks a rule."],
    ["SCORCHWIND", "Dragon of the desert: the showman. Vain, theatrical."],
    ["TIDEWYRM", "Dragon of the isles: the trickster. Greedy, sly, charming."],
    [
      "KING PYRRHAX",
      "The Dragon King. He lost the First Race young, stunned by the horn, and has beaten every champion since.",
    ],
    ["SKETCHY GUARD", "The smugglers' guards at the underground games. They sell tunnels."],
    ["GUARD", "The dragons' own guards: Dragon Kingdom folk in hooded tunics."],
    ["THE CROWD", "The Tropic Isles' captives and townsfolk."],
  ];
  for (const [n, d] of cast) out.push(`  ${n.padEnd(15)} ${d}`);
  const acts: [string, string][] = [
    [OPENING, "THE OPENING"],
    [sceneOf("valley", "festival"), "ACT I: DINOSAUR VALLEY"],
    [sceneOf("snow", "caught"), "ACT II: THE CONQUERED KINGDOMS"],
    ["dragon_challenger", "ACT III: THE DRAGON KINGDOM"],
    [sceneOf("valley", "rescue"), "ACT IV: THE RUINS"],
    ["dragon_court", "ACT V: THE NEW PACT"],
  ];
  let n = 0;
  for (const id of sceneOrder()) {
    const act = acts.find(([a]) => a === id);
    if (act) {
      out.push("", "", "=".repeat(72), act[1], "=".repeat(72));
    }
    n++;
    const sc = SCENES[id];
    const title =
      id === FAKE_CREDITS
        ? "The Fake Ending"
        : id === END_CREDITS
          ? "The Credits"
          : (sc?.title ?? id);
    out.push("", "", `SCENE ${n}. ${title.toUpperCase()}   [${id}]`, "-".repeat(72));
    out.push(indent(`WHEN: ${when(id)}`, 0));
    const st = STAGED.find((s) => s.scene === id);
    const where = st
      ? `${regionById(st.region)?.name ?? st.region}${st.ruined ? " (in ruins)" : ""}, staged in 3D.`
      : id === OPENING
        ? "A storybook page, inked pictures turning with each line."
        : "Full screen: the credits roll.";
    out.push(indent(`WHERE: ${where}`, 0));
    if (st) {
      const who = [
        ...new Set(
          Object.entries(st.actors).map(([k, a]) =>
            a.kind === "stone"
              ? a.big
                ? "the Heart Stone"
                : "a Pact Stone"
              : k === "you"
                ? "you"
                : k === "lumen_dragon"
                  ? "Lumen (as a dragon)"
                  : (CAST[k.replace(/\d+$/, "")]?.name ??
                    (a.kind === "villager" ? "townsfolk" : k)),
          ),
        ),
      ];
      out.push(indent(`ON STAGE: ${who.join(", ")}.`, 0));
    }
    if (id === FAKE_CREDITS) {
      out.push(
        "",
        indent(
          '[THE END. The credits begin to roll over a dark screen... and stop dead. The screen shakes and turns red. A low gong. "..."]',
          4,
        ),
      );
      continue;
    }
    if (id === END_CREDITS) {
      out.push("", indent("[The real credits roll. Thanks for playing.]", 4));
      continue;
    }
    const beats: Beat[] = sc?.beats ?? [];
    beats.forEach((b, i) => {
      const page = {
        dragons: "Dragons sweep across the page.",
        horn: "A horn blasts.",
        flash: "A flash.",
        light: "Golden light.",
      };
      const dir = st ? directions(st, st.beats[i], st.beats[i - 1]) : b.fx ? [page[b.fx]] : [];
      out.push("");
      if (dir.length) out.push(indent(`[${dir.join(" ")}]`, 4));
      // (Lumen's voice out of the light, with no Lumen on stage.)
      const vo =
        st && b.who === "lumen" && !st.actors.lumen ? " (HIS VOICE, OUT OF THE LIGHT)" : "";
      out.push(`    ${name(b.who)}${vo}`);
      out.push(indent(b.text, 8));
    });
  }
  out.push("", "", "END OF SCRIPT", "");
  return out.join("\n");
}
