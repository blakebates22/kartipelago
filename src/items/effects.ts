/**
 * What weapons do to racers, and the effects that last a while: shields, bubbles and
 * magnets. Kept apart from the kart's handling: these only set state the handling
 * already understands (spin-out, speed, a crash ending a boost) or nudge velocity
 * smoothly, never teleporting a kart.
 */
import { removeBananas, type BananaLossConfig } from "../vehicles/bananas";
import type { KartConfig, KartState } from "../vehicles/kart";
import type { ItemsConfig } from "./config";
import { emptyHeld, type Held } from "./inventory";

/** What hit a racer. "shield": rammed by a kart with its shield up. */
export type HitKind = "missile" | "oil" | "mine" | "bubble" | "shield";

export interface RacerItems {
  held: Held;
  /** Item button down last step (weapons fire on release). */
  buttonDown: boolean;
  shieldTime: number;
  shieldLevel: number;
  /** Seconds left trapped in a bubble. */
  bubbleTime: number;
  /** Magnet pulling this racer toward magnetTarget (an index), seconds left. */
  magnetTime: number;
  magnetTarget: number;
  /** A reverse magnet dragging this racer toward pullBy (an index), seconds left. */
  pullTime: number;
  pullBy: number;
  /** Can't be hit again until this runs out. */
  immuneTime: number;
  /** Last thing that hit this racer and how long ago, for effects. */
  lastHit: HitKind | "blocked" | null;
  lastHitAge: number;
}

export interface Racer {
  kart: KartState;
  items: RacerItems;
  cfg: KartConfig;
}

export function racerItems(): RacerItems {
  return {
    held: emptyHeld(),
    buttonDown: false,
    shieldTime: 0,
    shieldLevel: 0,
    bubbleTime: 0,
    magnetTime: 0,
    magnetTarget: -1,
    pullTime: 0,
    pullBy: -1,
    immuneTime: 0,
    lastHit: null,
    lastHitAge: Infinity,
  };
}

/** Bananas lost per hit: missiles and mines are weapon hits; oil is a spin (none). */
const LOSS: Record<HitKind, keyof BananaLossConfig | null> = {
  missile: "lossWeapon",
  mine: "lossWeapon",
  oil: "lossSpin",
  bubble: null,
  shield: null,
};

export interface HitResult {
  blocked: boolean;
  /** Bananas knocked loose (the caller drops them). */
  lost: number;
}

/** Spin the kart out (reusing the handling's own spin-out). */
function spinOut(k: KartState, seconds: number, keep: number) {
  k.spinTime = Math.max(k.spinTime, seconds);
  k.spinDir = Math.sin(k.heading * 7 + k.x) >= 0 ? 1 : -1;
  k.speed *= keep;
  k.counterTime = 0;
  if (k.driftDir !== 0) {
    k.driftDir = 0;
    k.recovering = true;
  }
  // Like a crash, a hit ends any boost (keeping a little of its extra speed).
  k.zipCrashed = true;
}

/** Something hit this racer. A shield blocks it; immunity after a hit ignores it. */
export function hitRacer(
  k: KartState,
  it: RacerItems,
  kind: HitKind,
  cfg: ItemsConfig,
  loss: BananaLossConfig,
): HitResult {
  if (it.immuneTime > 0) return { blocked: true, lost: 0 };
  if (it.shieldTime > 0) {
    it.lastHit = "blocked";
    it.lastHitAge = 0;
    return { blocked: true, lost: 0 };
  }
  it.immuneTime = cfg.hitImmuneSec;
  it.lastHit = kind;
  it.lastHitAge = 0;
  const key = LOSS[kind];
  const lost = key ? removeBananas(k, loss[key]) : 0;
  if (kind === "missile") {
    spinOut(k, cfg.missileSpinSec, cfg.missileSpeedKeep);
    k.vy = cfg.missilePop;
    k.grounded = false;
  } else if (kind === "mine") {
    spinOut(k, cfg.mineSpinSec, cfg.mineSpeedKeep);
    k.vy = cfg.minePop;
    k.grounded = false;
  } else if (kind === "oil") {
    spinOut(k, cfg.oilSpinSec, cfg.oilSpeedKeep);
  } else if (kind === "shield") {
    spinOut(k, cfg.shieldSpinSec, cfg.shieldSpeedKeep);
  } else {
    it.bubbleTime = cfg.bubbleSec;
    it.immuneTime = Math.max(it.immuneTime, cfg.bubbleSec + cfg.hitImmuneSec);
    if (k.driftDir !== 0) {
      k.driftDir = 0;
      k.recovering = true;
    }
    k.zipCrashed = true;
  }
  return { blocked: false, lost };
}

/**
 * Two karts touched. If exactly one has its shield up, the other spins out (unless it's
 * immune from a hit a moment ago). Returns the racer who spun, or -1.
 */
export function shieldRam(
  a: Racer,
  b: Racer,
  ia: number,
  ib: number,
  cfg: ItemsConfig,
  loss: BananaLossConfig,
): { victim: number; lost: number } | null {
  const sa = a.items.shieldTime > 0;
  const sb = b.items.shieldTime > 0;
  if (sa === sb) return null;
  const [v, iv] = sa ? [b, ib] : [a, ia];
  const res = hitRacer(v.kart, v.items, "shield", cfg, loss);
  return res.blocked ? null : { victim: iv, lost: res.lost };
}

export function activateShield(it: RacerItems, level: number, cfg: ItemsConfig) {
  it.shieldLevel = level;
  it.shieldTime = [0, cfg.shield1Sec, cfg.shield2Sec, cfg.shield3Sec][level] ?? cfg.shield1Sec;
}

/** Magnet range for a level, metres. */
export function magnetRange(level: number, cfg: ItemsConfig): number {
  const units = [0, cfg.magnet1Range, cfg.magnet2Range, cfg.magnet3Range][level] ?? 0;
  return units * cfg.magnetUnit;
}

/** How far round from the nose a grapple target can be (cosine of 75 degrees). */
const IN_FRONT = Math.cos((75 * Math.PI) / 180);

/** Is `t` in front of kart `k` (within 75 degrees of where it's facing)? */
function inFront(k: KartState, t: KartState, cosLimit = IN_FRONT) {
  const dx = t.x - k.x;
  const dz = t.z - k.z;
  const d = Math.hypot(dx, dz);
  if (d < 1e-6) return false;
  return (dx * Math.sin(k.heading) + dz * Math.cos(k.heading)) / d >= cosLimit;
}

/**
 * Pick a target: the nearest rival within range ahead of you. For a grapple (`front`)
 * "ahead" is physical: in front of your nose (within 75 degrees) and at about your
 * height, whatever lap they're on, so you can grab a backmarker you're about to lap
 * but never someone beside or behind you. For a homing missile it's race order (it
 * follows the road round corners to reach them). Returns its index, or -1.
 */
export function magnetTarget(
  racers: Racer[],
  i: number,
  range: number,
  progress: (index: number) => number,
  /** Only karts in front of you (grapples). Homing missiles follow the road to anyone ahead. */
  front = true,
): number {
  const me = racers[i]!.kart;
  const mine = progress(i);
  let best = -1;
  let bestD = range;
  racers.forEach((r, j) => {
    if (j === i) return;
    if (front ? !inFront(me, r.kart) || Math.abs(r.kart.y - me.y) > 4 : progress(j) <= mine) return;
    const d = Math.hypot(r.kart.x - me.x, r.kart.z - me.z);
    if (d <= bestD) {
      bestD = d;
      best = j;
    }
  });
  return best;
}

/** Fire a magnet. Returns false (and keeps the balloon) if there's no target. */
export function activateMagnet(
  racers: Racer[],
  i: number,
  level: number,
  cfg: ItemsConfig,
  progress: (index: number) => number,
): boolean {
  const target = magnetTarget(racers, i, magnetRange(level, cfg), progress);
  if (target < 0) return false;
  if (level >= 3) {
    // Reverse magnet: drag the rival back toward you.
    const t = racers[target]!.items;
    t.pullTime = cfg.reverseMagnetSec;
    t.pullBy = i;
  } else {
    const me = racers[i]!.items;
    me.magnetTime = cfg.magnetSec;
    me.magnetTarget = target;
  }
  return true;
}

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
const moveToward = (v: number, target: number, maxDelta: number) =>
  Math.abs(target - v) <= maxDelta ? target : v + Math.sign(target - v) * maxDelta;

/**
 * Advance timed effects for every racer. Call once per step, after the karts move.
 * Bubbles stop the kart; magnets steer and speed it toward its target; a reverse
 * magnet brakes its victim and drags it toward the magnet's owner.
 */
export function stepEffects(racers: Racer[], cfg: ItemsConfig, dt: number) {
  racers.forEach((r, i) => {
    const it = r.items;
    const k = r.kart;
    it.immuneTime = Math.max(0, it.immuneTime - dt);
    it.lastHitAge += dt;
    if (it.shieldTime > 0 && (it.shieldTime -= dt) <= 0) {
      it.shieldTime = 0;
      it.shieldLevel = 0;
    }
    if (it.bubbleTime > 0) {
      it.bubbleTime = Math.max(0, it.bubbleTime - dt);
      k.speed *= Math.exp(-6 * dt);
    }

    if (it.magnetTime > 0) {
      it.magnetTime = Math.max(0, it.magnetTime - dt);
      const t = racers[it.magnetTarget]?.kart;
      const d = t ? Math.hypot(t.x - k.x, t.z - k.z) : 0;
      // It lets go on arrival, in a bubble, or if you've got past them (so it never
      // drags you backwards).
      if (!t || d < cfg.magnetReach || it.bubbleTime > 0 || !inFront(k, t, 0)) {
        it.magnetTime = 0;
      } else {
        // Turn the path (and the nose with it) toward the target, and speed up.
        const want = Math.atan2(t.x - k.x, t.z - k.z);
        const turn = Math.max(
          -cfg.magnetTurn * dt,
          Math.min(cfg.magnetTurn * dt, wrap(want - k.velAngle)),
        );
        k.velAngle = wrap(k.velAngle + turn);
        k.heading = wrap(k.heading + turn);
        const pullTo = r.cfg.topSpeed * cfg.magnetSpeedMult;
        if (k.speed < pullTo) k.speed = Math.min(pullTo, k.speed + cfg.magnetAccel * dt);
      }
    }

    if (it.pullTime > 0) {
      it.pullTime = Math.max(0, it.pullTime - dt);
      const by = racers[it.pullBy]?.kart;
      const d = by ? Math.hypot(by.x - k.x, by.z - k.z) : 0;
      if (!by || d < cfg.magnetReach || i === it.pullBy) {
        it.pullTime = 0;
      } else {
        k.speed = moveToward(k.speed, 0, cfg.reverseDecel * dt);
        const step = Math.min(d - cfg.magnetReach, cfg.reversePull * dt);
        k.x += ((by.x - k.x) / d) * step;
        k.z += ((by.z - k.z) / d) * step;
      }
    }
  });
}

/** Bump weight: a shielded kart shoves others aside without being pushed itself. */
export const bumpMass = (it: RacerItems, cfg: ItemsConfig) =>
  it.shieldTime > 0 ? cfg.shieldMass : 1;
