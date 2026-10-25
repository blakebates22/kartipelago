/**
 * How well a rival drives, and how it likes to race: a skill set per racer.
 *
 * Every number here changes what the rival does with the same controls and the same
 * kart a player has (src/ai/driver.ts, src/ai/items.ts); none of them adds speed by
 * itself, apart from `pace`, a small trim kept close to 1. A strong rival is fast
 * because it drifts the corners that reward a drift, taps the throttle on the
 * straights, takes the zippers and lets the throttle go to enhance them, picks its
 * moments with items and makes few mistakes. A weak one does less of all that.
 *
 * Values are 0..1 unless noted. Defaults for the field come from assets/data/tuning.json
 * ("ai": "rivals", by roster name) on top of a tier ("strong", "good", "weak").
 */

export interface AiSkill {
  /** Top-speed trim, kept very close to 1 (0.98-1.0): the only direct speed knob. */
  pace: number;
  /** Steering accuracy: 1 holds its line exactly; lower wanders a little. */
  precision: number;
  /** How far ahead it reads the road (scales the lookahead), about 0.85-1.15. */
  vision: number;
  /** Drifting: how many of the corners that reward a drift it drifts, and how cleanly. */
  drift: number;
  /** Throttle tapping on the straights (the tap charge raises top speed). */
  tapping: number;
  /** Boost sense: steering for zippers and letting the throttle go to enhance them and
   * blue boosts, firing blue balloons on straights. */
  boosting: number;
  /** Reaction time to other racers, traps and incoming missiles, seconds. */
  reaction: number;
  /** Overtaking and defending: how readily it pulls out to pass, how close it follows,
   * and how often it blocks a racer behind. */
  aggression: number;
  /** Item sense: picking good moments and targets (and not wasting items). */
  items: number;
  /** Mistakes a minute: a missed drift, a wide line, a late lift. */
  mistakes: number;
  /** Where on the road it likes to be, -1 (inside of corners) .. 1 (wide), metres scale. */
  lineBias: number;
  /** Starts: 1 nails the window more often; 0 is an ordinary start. */
  start: number;
}

export type AiTier = "strong" | "good" | "weak";

export const TIERS: Record<AiTier, AiSkill> = {
  strong: {
    pace: 1,
    precision: 0.95,
    vision: 1.08,
    drift: 0.95,
    tapping: 0.6,
    boosting: 0.9,
    reaction: 0.25,
    aggression: 0.7,
    items: 0.85,
    mistakes: 0.4,
    lineBias: 0,
    start: 0.8,
  },
  good: {
    pace: 1,
    precision: 0.86,
    vision: 1,
    drift: 0.75,
    tapping: 0.25,
    boosting: 0.6,
    reaction: 0.4,
    aggression: 0.5,
    items: 0.6,
    mistakes: 0.9,
    lineBias: 0,
    start: 0.5,
  },
  weak: {
    pace: 0.985,
    precision: 0.74,
    vision: 0.9,
    drift: 0.45,
    tapping: 0,
    boosting: 0.3,
    reaction: 0.6,
    aggression: 0.3,
    items: 0.35,
    mistakes: 1.6,
    lineBias: 0,
    start: 0.25,
  },
};

/** A rival's skill: its tier, with any of its own tendencies on top. */
export function skillFor(tier: AiTier, own: Partial<AiSkill> = {}): AiSkill {
  return { ...TIERS[tier], ...own };
}

/** One rival's entry in the field (tuning.ai.rivals). */
export interface RivalSetup {
  tier: AiTier;
  /** Personal tendencies on top of the tier. */
  skill?: Partial<AiSkill>;
  /** A word for the debug view: what kind of racer this is. */
  style?: string;
}

export interface SkillConfig {
  /** Field difficulty: a whole-field nudge of every skill (-1 easier .. 1 harder). */
  difficulty: number;
  /** The field, by roster name; anyone missing is "good". */
  rivals: Record<string, RivalSetup>;
}

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/**
 * The skill a rival races with: its setup, then the field difficulty (which moves every
 * ability a little toward or away from perfect, and mistakes the other way).
 */
export function rivalSkill(
  name: string,
  cfg: SkillConfig,
): { skill: AiSkill; tier: AiTier; style: string } {
  const setup = cfg.rivals[name] ?? { tier: "good" as AiTier };
  const s = skillFor(setup.tier, setup.skill);
  const d = Math.max(-1, Math.min(1, cfg.difficulty));
  const toward = (v: number) => clamp01(v + (d > 0 ? (1 - v) * d * 0.5 : v * d * 0.5));
  return {
    tier: setup.tier,
    style: setup.style ?? setup.tier,
    skill: {
      ...s,
      precision: toward(s.precision),
      drift: toward(s.drift),
      // Throttle tapping (up to +10% top speed) only on the harder settings: a new
      // player can't see it or learn it from the rivals, so at Normal nobody taps.
      tapping: d > 0 ? clamp01(s.tapping * d * 1.5) : 0,
      boosting: toward(s.boosting),
      items: toward(s.items),
      aggression: toward(s.aggression),
      start: toward(s.start),
      reaction: Math.max(0.1, s.reaction * (1 - d * 0.35)),
      mistakes: Math.max(0, s.mistakes * (1 - d * 0.6)),
      pace: Math.min(1.01, s.pace + d * 0.01),
    },
  };
}
