/**
 * Rivals' items: when to fire what they're holding. Only what a player could see from
 * the driving seat (who's ahead and behind, and near them; missiles coming; the road
 * ahead), and the same balloons, ammo, targeting and cooldowns a player has: the
 * session fires the item through the same fireItem.
 *
 * A rival thinks about its item a few times a second, and its choice waits out its
 * reaction time. Item sense (skill.items) decides how good its moments are: a sharp
 * one saves a blue boost for a straight, fires a missile at someone it can actually
 * hit, drops a trap with a racer right behind, and raises its shield when a missile's
 * coming; a careless one fires at the first chance, or sits on an item too long.
 */
import { magnetRange, magnetTarget, type Racer } from "../items/effects";
import type { ItemsConfig } from "../items/config";
import type { ItemWorld } from "../items/world";
import { ZIP } from "../vehicles/zipper";
import { noise, type Driver } from "./driver";

const chance = (seed: number) => (noise(seed) + 1) / 2;

/** How much the road bends in the next stretch (largest curvature, 1/m). */
function bendAhead(d: Driver, metres: number) {
  const { line } = d;
  let best = 0;
  const steps = Math.round(metres / line.spacing);
  for (let k = 0; k <= steps; k++)
    best = Math.max(best, Math.abs(line.curvature[(d.index + k) % line.n]!));
  return best;
}

/** Is target t within `cos` of straight ahead of kart k, and within range? */
function inSights(k: Racer["kart"], t: Racer["kart"], range: number, cos: number) {
  const dx = t.x - k.x;
  const dz = t.z - k.z;
  const dist = Math.hypot(dx, dz);
  if (dist < 3 || dist > range || Math.abs(t.y - k.y) > 3) return false;
  return (dx * Math.sin(k.heading) + dz * Math.cos(k.heading)) / dist >= cos;
}

/**
 * Should rival i fire its held balloon now? Returns true to fire, and for a blue boost
 * whether to fire it with the throttle released (an enhanced boost).
 */
export function aiItem(
  d: Driver,
  i: number,
  racers: Racer[],
  world: ItemWorld,
  cfg: ItemsConfig,
  progress: (j: number) => number,
  dt: number,
): { fire: boolean; lift: boolean } {
  const none = { fire: false, lift: false };
  const me = racers[i]!;
  const held = me.items.held;
  if (!held.color || held.ammo <= 0 || me.items.bubbleTime > 0) {
    d.itemHeld = 0;
    return none;
  }
  d.itemHeld += dt;
  d.itemThink -= dt;
  if (d.itemThink > 0) return none;
  // Think again after a beat (slower for a slower thinker).
  d.itemThink = 0.2 + d.skill.reaction * 0.5;
  const sense = d.skill.items;
  const k = me.kart;
  const mine = progress(i);
  const roll = chance(d.seed * 19.1 + d.clock * 3.7);
  // A careless racer fires sooner or later at random; a sharp one waits for a moment.
  const careless = roll > 0.5 + sense * 0.5 && d.itemHeld > 1.5;
  // Racers close behind (by race order, within metres of road).
  const behindClose = racers.some((r, j) => {
    if (j === i) return false;
    const gap = mine - progress(j);
    return gap > 3 && gap < 28 && Math.abs(r.kart.y - k.y) < 3;
  });

  switch (held.color) {
    case "blue": {
      // A boost: on a straight, at speed, not already boosting (or to get going again).
      // (Long enough for the whole boost: a level 3 runs a long way at speed.)
      const straight = bendAhead(d, 60 + 45 * held.level) < 1 / 70;
      const slow = k.speed < me.cfg.topSpeed * 0.5 && d.clock > 3;
      const good = k.zipPhase === ZIP.NORMAL && k.grounded && (straight || slow);
      if (good || careless)
        return { fire: true, lift: chance(d.seed * 23 + d.clock) < d.skill.boosting };
      return none;
    }
    case "red": {
      if (held.level === 2) {
        // Homing: anyone ahead in range (it follows the road to them).
        const t = magnetTarget(racers, i, cfg.homingRange * (0.6 + 0.4 * sense), progress, false);
        if (t >= 0 || careless) return { fire: true, lift: false };
        return none;
      }
      // Straight missiles: someone in its sights on a straight bit of road (a sharp
      // shot lines up tighter, so it hits more often).
      const cos = Math.cos(((4 + (1 - sense) * 10) * Math.PI) / 180);
      const aimed = racers.some((r, j) => j !== i && inSights(k, r.kart, 45, cos));
      if ((aimed && bendAhead(d, 30) < 1 / 50) || careless) return { fire: true, lift: false };
      return none;
    }
    case "green": {
      // Traps: with a racer right behind, or, leading and sitting on one, before a
      // corner (where the line narrows to the apex).
      const corner = bendAhead(d, 25) > 1 / 45;
      if (behindClose || (d.itemHeld > 12 && corner) || (careless && d.itemHeld > 6))
        return { fire: true, lift: false };
      return none;
    }
    case "yellow": {
      // Shields: a missile coming (or a homing one after us), or a trap on our road ahead.
      const threat = world.missiles.some(
        (m) =>
          m.owner !== i &&
          ((m.homing && m.target === i) ||
            (Math.hypot(m.x - k.x, m.z - k.z) < 25 &&
              Math.cos(Math.atan2(k.x - m.x, k.z - m.z) - m.heading) > 0.9)),
      );
      const trap = world.traps.some((t) => {
        const dx = t.x - k.x;
        const dz = t.z - k.z;
        const dist = Math.hypot(dx, dz);
        return dist < 14 && (dx * Math.sin(k.heading) + dz * Math.cos(k.heading)) / dist > 0.9;
      });
      const reacts = chance(d.seed * 29 + d.clock * 1.3) < 0.35 + 0.65 * sense;
      if (((threat || trap) && reacts) || (careless && d.itemHeld > 8))
        return { fire: true, lift: false };
      return none;
    }
    case "rainbow": {
      // Magnets: someone ahead in grapple range.
      const t = magnetTarget(racers, i, magnetRange(held.level, cfg), progress);
      if (t >= 0) return { fire: true, lift: false };
      return none;
    }
  }
  return none;
}
