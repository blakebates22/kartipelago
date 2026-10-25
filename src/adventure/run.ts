/**
 * The Adventure race being run (on `game.adventure.run`): what kind it is, and what the
 * race session needs for it (coins, the field, the player's name). The screens set it
 * before loading a race and read it back when the race ends.
 */
import type { SessionOptions } from "../game/session";
import { RACER_IDS, type RacerId } from "../render/racers/designs";
import { DRAGON, kingdomById, type KingdomId } from "./data";
import type { AdventureSave } from "./progress";

export type AdventureRun =
  /** A championship: the kingdom's Trophy Race cup (game.trophy carries the races). */
  | { kind: "cup"; kingdom: KingdomId | "dragon_final" }
  /** A treasure map race on a ruined course (or its stand-in). */
  | { kind: "coins"; kingdom: KingdomId; course: string; track: string; standIn: boolean }
  | { kind: "boss"; kingdom: KingdomId }
  /** The Dragon King: `chosen` once the Chosen One races him. */
  | { kind: "king"; chosen: boolean };

export interface AdventureState {
  save: AdventureSave;
  run?: AdventureRun;
  /** The kingdom the hub last showed. */
  at?: KingdomId;
}

/**
 * Who you race in a kingdom: your crew (the racers who've joined), that kingdom's own
 * champion if they haven't joined yet (you're there to beat them), and local racers in
 * the alternate paints to fill the grid. Never a racer you haven't met.
 */
export function kingdomField(
  kingdom: KingdomId | "dragon_final",
  player: RacerId,
  crew: ReadonlySet<RacerId>,
): { id: RacerId; alt: boolean }[] {
  const champ =
    kingdom === "dragon" || kingdom === "dragon_final"
      ? undefined
      : kingdomById(kingdom)?.champion?.look;
  const out: { id: RacerId; alt: boolean }[] = [];
  if (champ && champ !== player && !crew.has(champ)) out.push({ id: champ, alt: false });
  for (const r of RACER_IDS) if (crew.has(r) && r !== player) out.push({ id: r, alt: false });
  // Locals: the crew's cousins, in their alternate paints.
  const kin = [player, ...RACER_IDS.filter((r) => crew.has(r) && r !== player)];
  for (let i = 0; out.length < 7; i++) out.push({ id: kin[i % kin.length]!, alt: true });
  return out.slice(0, 7);
}

/** What a race needs from Adventure (merged into the session's options). */
export function sessionExtras(
  run: AdventureRun | undefined,
  player: RacerId,
  crew: ReadonlySet<RacerId>,
): Partial<SessionOptions> {
  if (!run) return {};
  if (run.kind === "coins")
    return { coins: "auto", field: { looks: kingdomField(run.kingdom, player, crew) } };
  if (run.kind === "cup") return { field: { looks: kingdomField(run.kingdom, player, crew) } };
  if (run.kind === "boss") {
    const b = kingdomById(run.kingdom)!.boss!;
    return { field: { count: 1, names: [b.name], speed: b.speed } };
  }
  if (run.kind === "king")
    return {
      field: {
        count: 1,
        names: [DRAGON.king.name],
        speed: run.chosen ? DRAGON.king.chosenSpeed : DRAGON.king.speed,
      },
      ...(run.chosen && { playerName: DRAGON.chosen.name }),
    };
  return {};
}

/** A line for the top of the race screen. */
export function runLabel(run: AdventureRun | undefined): string | undefined {
  if (!run) return undefined;
  switch (run.kind) {
    case "coins":
      return run.standIn ? "TREASURE MAP · STAND-IN COURSE" : "TREASURE MAP";
    case "boss":
      return `VS ${kingdomById(run.kingdom)!.boss!.name.toUpperCase()}`;
    case "king":
      return run.chosen ? `${DRAGON.chosen.ability} VS THE DRAGON KING` : "VS THE DRAGON KING";
    default:
      return undefined;
  }
}
