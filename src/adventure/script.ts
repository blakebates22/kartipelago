/**
 * The whole Adventure script, as an actor would get it (Blake, Oct 27): every scene in
 * the order it plays, when it plays, where it's staged, who's in it, every line, and the
 * stage directions (from the stagings: who flies in, rears up, breathes fire; the flashes,
 * the horn, the blackout). Made from the story's own data (scenes.ts, staged.ts), so it
 * can't drift from the game: docs/adventure-script.txt is this, written out
 * (tools/audit/script.audit.ts writes it; tests/script.test.ts checks it's up to date).
 */
import { END_CREDITS, FAKE_CREDITS, KINGDOMS, OPENING, RAGE, nameOf, sceneOf } from "./data";
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

/** When each scene plays (what you've just done). */
function when(id: string): string {
  const k = KINGDOMS.find((x) => id.startsWith(`${x.id}_`));
  const step = k ? id.slice(k.id.length + 1) : "";
  const K = k ? nameOf(k.id) : "";
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
      return `Coming out of the gateway of the last of ${K}'s four courses; the 1 on 1 starts straight after.`;
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
      return `Two of ${K}'s four courses won.`;
    case "rescue":
      return "After the Rage: you wake in the ruined valley.";
    case "new_stone":
      return `All four of ${K}'s light shards won; the dragon's race starts straight after.`;
    case "yield":
      return `${k!.boss.name} beaten under the new Pact Stone.`;
  }
  return "";
}

const name = (who: string) => (who ? (CAST[who]?.name ?? who).toUpperCase() : "NARRATOR (CAPTION)");

/** A staged line's stage directions, in words. */
function directions(st: StagedScene, b: StagedBeat | undefined): string[] {
  if (!b) return [];
  const who = (k: string) => {
    const a = st.actors[k];
    const base = k.replace(/\d+$/, "");
    if (a?.kind === "stone") return a.big ? "the Heart Stone" : "the Pact Stone";
    if (k === "lumen_dragon") return "Lumen, the dragon";
    if (k === "you") return "you";
    return CAST[base]?.name ?? base;
  };
  const out: string[] = [];
  for (const m of b.moves ?? []) {
    const a = st.actors[m.actor];
    const flying = a?.kind === "dragon" && (m.y ?? 0) > 2;
    const landing = a?.kind === "dragon" && m.y === 0;
    out.push(
      `${who(m.actor)} ${flying ? "flies" : landing ? "comes down to land" : a?.kind === "racer" ? "drives" : "moves"}${flying ? " overhead" : ""}.`,
    );
  }
  const fx = b.fx ?? {};
  for (const k of fx.show ?? []) out.push(`${who(k)} appears.`);
  for (const k of fx.hide ?? []) out.push(`${who(k)} is gone.`);
  if (fx.rear) out.push(`${who(fx.rear)} rears up.`);
  if (fx.fire) out.push(`${who(fx.fire)} breathes fire.`);
  if (fx.horn) out.push("The Founders' Horn sounds.");
  if (fx.flash) out.push("A flash.");
  if (fx.shake && fx.shake >= 1) out.push("The ground shakes.");
  if (fx.black) out.push("Blackout.");
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
      "Keeper of the Pact and of the Founders' Horn. Kind, old, a secret on his shoulders.",
    ],
    ["LUMEN", "A hooded figure in a long robe, his wings hidden under it: a dragon hatchling."],
    ["REX", "Dinosaur Valley's champion. A cocky lone racer, no crew. Your first."],
    ["BRACHIO", "The Snow Kingdom's champion, Rimefang's captive."],
    ["STEGO", "Desert World's champion, Scorchwind's star act."],
    ["RAPTOR", "Tropic Isles' champion, Tidewyrm's 'treasure'."],
    ["CINDERJAW", "Dragon of the valley: the brute. All fire, no patience."],
    ["RIMEFANG", "Dragon of the snow: the lawyer. Cold, precise, never breaks a rule."],
    ["SCORCHWIND", "Dragon of the desert: the showman. Vain, theatrical."],
    ["TIDEWYRM", "Dragon of the isles: the trickster. Greedy, sly, charming."],
    ["KING PYRRHAX", "The Dragon King. He lost the First Race young, and remembers."],
    ["SKETCHY GUARD", "The smugglers' guards at the underground games."],
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
      const dir = st ? directions(st, st.beats[i]) : b.fx ? [page[b.fx]] : [];
      out.push("");
      if (dir.length) out.push(indent(`[${dir.join(" ")}]`, 4));
      out.push(`    ${name(b.who)}`);
      out.push(indent(b.text, 8));
    });
  }
  out.push("", "", "END OF SCRIPT", "");
  return out.join("\n");
}
