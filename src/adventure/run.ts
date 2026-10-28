/**
 * The Adventure race being run (on `game.adventure.run`): what kind it is, and what the
 * race session needs for it (shard pieces, the field, the names). The screens set it
 * before loading a race and read it back when the race ends.
 */
import type { SessionOptions } from "../game/session";
import { RACER_IDS, type RacerId } from "../render/racers/designs";
import { STARTERS } from "../app/unlocks";
import { DRAGON, kingdomById, type KingdomId } from "./data";
import type { AdventureSave } from "./progress";

export type AdventureRun =
  /** One of a kingdom's four standard courses (the festival, the gladiator games, the
   * King's Games): win all four, any order. */
  | { kind: "race"; kingdom: KingdomId; track: string }
  /** A shard race on a ruined course (or its stand-in): every shard piece and 1st. */
  | { kind: "shards"; kingdom: KingdomId; course: string; track: string; standIn: boolean }
  /** A dragon's race under its new Pact Stone. */
  | { kind: "boss"; kingdom: KingdomId }
  /** The champion's challenge: 1 on 1, once round the kingdom's overworld region. */
  | { kind: "duel"; kingdom: KingdomId }
  /** The King: the race for the lands (`final` false), or the last, under the new Pact. */
  | { kind: "king"; final: boolean };

export interface AdventureState {
  save: AdventureSave;
  /** Which save file (0-2) it is. */
  slot: number;
  run?: AdventureRun;
}

/**
 * Who you race in a kingdom (Blake, Oct 27: the other starters are just other racers;
 * the captives race each other): the kingdom's own champion while they haven't joined
 * you (racing as them yourself: their cousin), the other starters, your crew, and local
 * racers in the alternate paints to fill the grid.
 */
export function kingdomField(
  kingdom: KingdomId,
  player: RacerId,
  crew: ReadonlySet<RacerId>,
): { id: RacerId; alt: boolean }[] {
  const champ = kingdom === "dragon" ? undefined : kingdomById(kingdom)?.champion.look;
  const out: { id: RacerId; alt: boolean }[] = [];
  if (champ && champ === player) out.push({ id: champ, alt: true });
  else if (champ && !crew.has(champ)) out.push({ id: champ, alt: false });
  for (const r of STARTERS) if (r !== player && r !== champ) out.push({ id: r, alt: false });
  for (const r of RACER_IDS)
    if (crew.has(r) && r !== player && !out.some((o) => o.id === r && !o.alt))
      out.push({ id: r, alt: false });
  // Locals: alternate paints (new local racers come later).
  const kin = RACER_IDS.filter((r) => r !== player);
  for (let i = 0; out.length < 7; i++) out.push({ id: kin[i % kin.length]!, alt: true });
  return out.slice(0, 7);
}

/**
 * A boss waits for you (Blake couldn't beat them): well ahead it eases right off, so a
 * clean lap with your boosts always catches it; behind, it pushes a little harder.
 */
export const BOSS_CATCH_UP = {
  catchupBand: 25,
  catchupRamp: 90,
  catchupMaxHold: 0.12,
  catchupMaxHelp: 0.03,
};

/** What a race needs from Adventure (merged into the session's options). `player` is
 * who's driving; `racer` the file's own racer (a champion's cousin stands in for them). */
export function sessionExtras(
  run: AdventureRun | undefined,
  player: RacerId,
  crew: ReadonlySet<RacerId>,
  racer: RacerId = player,
): Partial<SessionOptions> {
  if (!run) return {};
  if (run.kind === "shards")
    return { coins: "auto", field: { looks: kingdomField(run.kingdom, player, crew) } };
  if (run.kind === "race") return { field: { looks: kingdomField(run.kingdom, player, crew) } };
  if (run.kind === "duel") {
    const ch = kingdomById(run.kingdom)!.champion;
    // (A file raced as the champion: their cousin takes the challenge.)
    const cousin = ch.look === racer || ch.look === player;
    return {
      field: {
        count: 1,
        names: [cousin ? `${ch.name}'s Cousin` : ch.name],
        looks: [{ id: ch.look, alt: cousin }],
      },
    };
  }
  if (run.kind === "boss") {
    const b = kingdomById(run.kingdom)!.boss;
    return {
      field: {
        count: 1,
        names: [b.name],
        speed: b.speed,
        looks: [{ id: "dragon", alt: false, palette: b.name.toLowerCase(), boss: true }],
        catchUp: BOSS_CATCH_UP,
      },
    };
  }
  if (run.kind === "king")
    return {
      field: {
        count: 1,
        names: [DRAGON.king.name],
        looks: [{ id: "dragon", alt: false, palette: "king", boss: true }],
        catchUp: BOSS_CATCH_UP,
        speed: DRAGON.king.speed,
      },
      // The race for the lands: his wall of fire; the last race: his fireballs and the
      // gauntlet (the course's other mechanic).
      bossVariant: run.final ? "alt" : "main",
    };
  return {};
}

/** A line for the top of the race screen. */
export function runLabel(run: AdventureRun | undefined): string | undefined {
  if (!run) return undefined;
  switch (run.kind) {
    case "shards":
      return run.standIn ? "LIGHT SHARD · STAND-IN COURSE" : "LIGHT SHARD";
    case "boss":
      return `VS ${kingdomById(run.kingdom)!.boss.name.toUpperCase()}`;
    case "duel":
      return `1 ON 1 VS ${kingdomById(run.kingdom)!.champion.name.toUpperCase()}`;
    case "king":
      return run.final ? "VS THE DRAGON KING · UNDER THE NEW PACT" : "VS THE DRAGON KING";
    default:
      return undefined;
  }
}
