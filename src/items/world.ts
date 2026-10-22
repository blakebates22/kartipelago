/**
 * Everything item-related that lives in the world rather than on a kart: balloons to
 * pick up, missiles in flight, traps on the road, and short-lived blasts (for effects).
 *
 * Missiles and traps move and collide here, separately from vehicle physics. When they
 * hit a racer they call hitRacer (effects.ts), which only sets state the handling
 * already understands.
 */
import type { GroundQuery } from "../physics/ground";
import type { BananaLossConfig } from "../vehicles/bananas";
import { insideBox, type Solid } from "../world/solids";
import type { Track } from "../world/track";
import { activateBlue } from "./boosts";
import type { ItemsConfig } from "./config";
import {
  activateMagnet,
  activateShield,
  hitRacer,
  magnetTarget,
  type HitKind,
  type Racer,
} from "./effects";
import { collectBalloon, useAmmo, type BalloonColor } from "./inventory";

export interface BalloonSpot {
  at: number;
  across?: number;
  color: BalloonColor;
  /** Branching courses: `at` is along this whole-lap route (TrackMeta.lapRoutes). */
  route?: string;
}

export interface BalloonPickup {
  x: number;
  y: number;
  z: number;
  color: BalloonColor;
  active: boolean;
  respawnIn: number;
  /** Seconds since it (re)appeared, for the pop-in. */
  age: number;
}

export interface Missile {
  x: number;
  y: number;
  z: number;
  heading: number;
  speed: number;
  life: number;
  owner: number;
  homing: boolean;
  /** Index of the racer it's chasing, or -1. */
  target: number;
  /** Nearest track sample, for following the road. */
  sample: number;
  ground: GroundQuery;
}

export type TrapKind = "oil" | "mine" | "bubble";

export interface Trap {
  kind: TrapKind;
  x: number;
  y: number;
  z: number;
  owner: number;
  age: number;
}

/** A moment worth showing or hearing: an explosion, a blocked hit, a fizzled shot. */
export interface Blast {
  kind: HitKind | "blocked" | "wall" | "fizz";
  x: number;
  y: number;
  z: number;
  age: number;
}

export interface ItemWorld {
  balloons: BalloonPickup[];
  missiles: Missile[];
  traps: Trap[];
  blasts: Blast[];
  track: Track | undefined;
  solids: Solid[];
  /** Walled track: missiles explode at the road edge. */
  walled: boolean;
  makeGround: () => GroundQuery;
}

/** Something that happened this step, for sound and feedback. */
export type ItemEvent =
  | { type: "pickup"; racer: number; color: BalloonColor; result: "new" | "upgrade" | "refill" }
  | {
      type: "fire";
      racer: number;
      color: BalloonColor;
      level: number;
      /** Blue only: activated with the throttle released. */
      enhanced?: boolean;
    }
  | { type: "noTarget"; racer: number }
  | { type: "hit"; racer: number; kind: HitKind; blocked: boolean; lost: number };

const sampleAt = (track: Track, at: number) => {
  const n = track.samples.length;
  return track.samples[((Math.round((at / track.length) * n) % n) + n) % n]!;
};

export function createItemWorld(
  track: Track | undefined,
  spots: BalloonSpot[],
  makeGround: () => GroundQuery,
  solids: Solid[] = [],
  walled = true,
): ItemWorld {
  const balloons: BalloonPickup[] = [];
  if (track) {
    for (const spot of spots) {
      const s = sampleAt(track, spot.at);
      const rh = Math.hypot(s.right.x, s.right.z);
      const across = spot.across ?? 0;
      balloons.push({
        x: s.pos.x + (s.right.x / rh) * across,
        y: s.pos.y + s.right.y * (across / rh),
        z: s.pos.z + (s.right.z / rh) * across,
        color: spot.color,
        active: true,
        respawnIn: 0,
        age: 1,
      });
    }
  }
  return { balloons, missiles: [], traps: [], blasts: [], track, solids, walled, makeGround };
}

/** A restart: every balloon back, nothing in flight or on the road. */
export function resetItemWorld(w: ItemWorld) {
  for (const b of w.balloons) Object.assign(b, { active: true, respawnIn: 0, age: 1 });
  w.missiles = [];
  w.traps = [];
  w.blasts = [];
}

/** Items fire when the button is released. Returns true on the release. */
export function itemReleased(r: Racer, down: boolean): boolean {
  const released = r.items.buttonDown && !down;
  r.items.buttonDown = down;
  return released;
}

/** Pick up any balloon a racer is touching. */
export function collectBalloons(
  w: ItemWorld,
  racers: Racer[],
  cfg: ItemsConfig,
  canCollect: (i: number) => boolean,
): ItemEvent[] {
  const events: ItemEvent[] = [];
  for (const b of w.balloons) {
    if (!b.active) continue;
    racers.forEach((r, i) => {
      if (!b.active || !canCollect(i) || r.items.bubbleTime > 0) return;
      const k = r.kart;
      if (Math.hypot(k.x - b.x, k.z - b.z) > cfg.balloonRadius || Math.abs(k.y - b.y) > 3) return;
      b.active = false;
      b.respawnIn = cfg.balloonRespawnSec;
      const result = collectBalloon(r.items.held, b.color, cfg);
      events.push({ type: "pickup", racer: i, color: b.color, result });
    });
  }
  return events;
}

/** The nearest racer ahead within range, for a homing missile. */
function homingTarget(
  racers: Racer[],
  i: number,
  cfg: ItemsConfig,
  progress: (j: number) => number,
) {
  return magnetTarget(racers, i, cfg.homingRange, progress);
}

function nearestSample(track: Track, x: number, z: number, hint: number) {
  const n = track.samples.length;
  let best = hint;
  let bestD = Infinity;
  const look = (i: number) => {
    const p = track.samples[((i % n) + n) % n]!.pos;
    const d = (p.x - x) ** 2 + (p.z - z) ** 2;
    if (d < bestD) {
      bestD = d;
      best = ((i % n) + n) % n;
    }
  };
  for (let k = -30; k <= 30; k++) look(hint + k);
  if (bestD > 40 * 40) for (let i = 0; i < n; i++) look(i);
  return best;
}

function launchMissile(
  w: ItemWorld,
  racers: Racer[],
  i: number,
  homing: boolean,
  cfg: ItemsConfig,
  progress: (j: number) => number,
) {
  const k = racers[i]!.kart;
  // Launched along the nose, plus the kart's own movement.
  const fx =
    Math.sin(k.heading) * cfg.missileSpeed + Math.sin(k.velAngle) * k.speed * cfg.missileCarry;
  const fz =
    Math.cos(k.heading) * cfg.missileSpeed + Math.cos(k.velAngle) * k.speed * cfg.missileCarry;
  const ground = w.makeGround();
  w.missiles.push({
    x: k.x + Math.sin(k.heading) * 2,
    y: k.y + 0.7,
    z: k.z + Math.cos(k.heading) * 2,
    heading: Math.atan2(fx, fz),
    speed: Math.max(cfg.missileSpeed, Math.hypot(fx, fz)),
    life: cfg.missileLife,
    owner: i,
    homing,
    target: homing ? homingTarget(racers, i, cfg, progress) : -1,
    sample: w.track ? nearestSample(w.track, k.x, k.z, 0) : 0,
    ground,
  });
}

function dropTrap(w: ItemWorld, r: Racer, i: number, kind: TrapKind, cfg: ItemsConfig) {
  const k = r.kart;
  const x = k.x - Math.sin(k.heading) * cfg.trapBehind;
  const z = k.z - Math.cos(k.heading) * cfg.trapBehind;
  w.traps.push({ kind, x, y: w.makeGround().at(x, z).height, z, owner: i, age: 0 });
}

/**
 * Use the held balloon (called on the item button's release). `throttle` is the
 * throttle at this moment: it decides whether a blue boost is enhanced.
 */
export function fireItem(
  w: ItemWorld,
  racers: Racer[],
  i: number,
  throttle: number,
  cfg: ItemsConfig,
  progress: (j: number) => number,
): ItemEvent | null {
  const r = racers[i]!;
  const h = r.items.held;
  if (!h.color || h.ammo <= 0 || r.items.bubbleTime > 0) return null;
  const { color, level } = h;
  let enhanced: boolean | undefined;
  switch (color) {
    case "blue":
      activateBlue(r.kart, level, throttle, r.cfg, cfg);
      enhanced = r.kart.zipEnhanced;
      break;
    case "red":
      launchMissile(w, racers, i, level === 2, cfg, progress);
      break;
    case "green":
      dropTrap(w, r, i, level === 1 ? "oil" : level === 2 ? "mine" : "bubble", cfg);
      break;
    case "yellow":
      activateShield(r.items, level, cfg);
      break;
    case "rainbow":
      if (!activateMagnet(racers, i, level, cfg, progress)) return { type: "noTarget", racer: i };
      break;
  }
  useAmmo(h);
  return { type: "fire", racer: i, color, level, enhanced };
}

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

/** Is this point blocked: outside a walled road, or inside a solid? */
function blocked(w: ItemWorld, m: Missile): boolean {
  if (w.walled && w.track) {
    const road = m.ground.at(m.x, m.z).road;
    if (road && Math.abs(road.across) > road.halfWidth) return true;
  }
  for (const s of w.solids) {
    if (m.y > s.height) continue;
    if (s.kind === "circle" ? Math.hypot(m.x - s.x, m.z - s.z) < s.radius : insideBox(s, m.x, m.z))
      return true;
  }
  return false;
}

/** Move missiles, check traps, respawn balloons, age blasts. Returns the hits. */
export function stepItemWorld(
  w: ItemWorld,
  racers: Racer[],
  cfg: ItemsConfig,
  loss: BananaLossConfig,
  dt: number,
  progress: (j: number) => number,
): ItemEvent[] {
  const events: ItemEvent[] = [];
  const hit = (j: number, kind: HitKind, x: number, y: number, z: number) => {
    const r = racers[j]!;
    const res = hitRacer(r.kart, r.items, kind, cfg, loss);
    w.blasts.push({ kind: res.blocked ? "blocked" : kind, x, y, z, age: 0 });
    events.push({ type: "hit", racer: j, kind, blocked: res.blocked, lost: res.lost });
  };

  for (const b of w.balloons) {
    b.age += dt;
    if (!b.active && (b.respawnIn -= dt) <= 0) {
      b.active = true;
      b.age = 0;
    }
  }

  w.missiles = w.missiles.filter((m) => {
    m.life -= dt;
    if (m.life <= 0) {
      w.blasts.push({ kind: "fizz", x: m.x, y: m.y, z: m.z, age: 0 });
      return false;
    }
    if (m.homing) {
      if (m.target < 0) m.target = homingTarget(racers, m.owner, cfg, progress);
      const t = racers[m.target]?.kart;
      if (t) {
        // Close: aim at the target. Further: follow the road ahead toward it.
        let ax = t.x;
        let az = t.z;
        const d = Math.hypot(t.x - m.x, t.z - m.z);
        if (d > cfg.homingDirect && w.track) {
          const n = w.track.samples.length;
          m.sample = nearestSample(w.track, m.x, m.z, m.sample);
          const ahead = Math.round((cfg.homingLookAhead / w.track.length) * n);
          const p = w.track.samples[(m.sample + ahead) % n]!.pos;
          ax = p.x;
          az = p.z;
        }
        const want = Math.atan2(ax - m.x, az - m.z);
        const turn = cfg.homingTurn * dt;
        m.heading = wrap(m.heading + Math.max(-turn, Math.min(turn, wrap(want - m.heading))));
      }
    }
    m.x += Math.sin(m.heading) * m.speed * dt;
    m.z += Math.cos(m.heading) * m.speed * dt;
    m.y = m.ground.at(m.x, m.z).height + 0.7;
    if (blocked(w, m)) {
      w.blasts.push({ kind: "wall", x: m.x, y: m.y, z: m.z, age: 0 });
      return false;
    }
    for (let j = 0; j < racers.length; j++) {
      if (j === m.owner) continue;
      const k = racers[j]!.kart;
      if (
        Math.hypot(k.x - m.x, k.z - m.z) < cfg.missileHitRadius &&
        Math.abs(k.y + 0.5 - m.y) < 2
      ) {
        hit(j, "missile", m.x, m.y, m.z);
        return false;
      }
    }
    return true;
  });

  w.traps = w.traps.filter((t) => {
    t.age += dt;
    if (t.age > cfg.trapLife) return false;
    const radius =
      t.kind === "oil" ? cfg.oilRadius : t.kind === "mine" ? cfg.mineRadius : cfg.bubbleRadius;
    for (let j = 0; j < racers.length; j++) {
      if (j === t.owner && t.age < cfg.trapOwnerGrace) continue;
      const k = racers[j]!.kart;
      if (Math.hypot(k.x - t.x, k.z - t.z) < radius && Math.abs(k.y - t.y) < 2) {
        if (racers[j]!.items.immuneTime > 0 && racers[j]!.items.shieldTime <= 0) continue;
        hit(j, t.kind, t.x, t.y, t.z);
        return false;
      }
    }
    return true;
  });

  w.blasts = w.blasts.filter((b) => (b.age += dt) < 1.2);
  return events;
}
