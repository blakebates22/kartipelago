// A whole race with every kart driven by the AI, headless: the same physics, items,
// bumps, zippers, loops and race rules as the game's session (src/game/session.ts),
// minus the rendering, sound and hazards. For checking that rivals finish, don't get
// stuck, race each other, use their items, and come out in a believable order, and for
// balancing the skills (slot 0 can stand in for a player of a given skill).
import tuning from "../assets/data/tuning.json";
import roster from "../assets/data/characters.json";
import rivalSetups from "../assets/data/rivals.json";
import { NEUTRAL } from "../src/core/input";
import { catchUp, type CatchUpConfig } from "../src/ai/catchup";
import { createDriver, driveAi, type AiWorld, type Driver } from "../src/ai/driver";
import { aiItem } from "../src/ai/items";
import { buildRacingLine } from "../src/ai/racingLine";
import { rivalSkill, skillFor, type AiSkill, type SkillConfig } from "../src/ai/skill";
import { createLoops } from "../src/game/loops";
import type { ItemsConfig } from "../src/items/config";
import { racerItems, shieldRam, stepEffects, type Racer } from "../src/items/effects";
import { collectBalloons, createItemWorld, fireItem, stepItemWorld } from "../src/items/world";
import { bumpKarts } from "../src/physics/bump";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../src/physics/walls";
import { gridSlot } from "../src/race/grid";
import {
  createRace,
  progress,
  respawnSpot,
  stepRacer,
  teleported,
  tickRace,
} from "../src/race/race";
import { applyCharacter, type Character } from "../src/vehicles/character";
import { applyBoost, createKartState, stepKart, type KartConfig } from "../src/vehicles/kart";
import { startZipper } from "../src/vehicles/zipper";
import { applySurface, createMeshGround } from "../src/world/collisionMesh";
import { buildTrack } from "../src/world/track";
import { SURFACES, type TrackPackage } from "../src/world/trackPackage";
import { buildZippers, enteredZipper } from "../src/world/zippers";

const dt = 1 / 120;
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };
const itemsCfg = tuning.items as unknown as ItemsConfig;

/** A stand-in for a player, by how good they are. */
export const PLAYERS: Record<string, AiSkill> = {
  novice: {
    ...skillFor("weak"),
    // (A player's kart is never trimmed: pace is the rivals' knob.)
    pace: 1,
    drift: 0.25,
    tapping: 0,
    boosting: 0.15,
    mistakes: 3,
    precision: 0.68,
    items: 0.3,
    start: 0.1,
  },
  competent: {
    ...skillFor("good"),
    drift: 0.85,
    tapping: 0.35,
    boosting: 0.7,
    mistakes: 0.8,
    items: 0.65,
    start: 0.6,
  },
  expert: {
    ...skillFor("strong"),
    drift: 1,
    tapping: 0.85,
    boosting: 1,
    mistakes: 0.25,
    items: 0.9,
    precision: 0.97,
    start: 0.9,
  },
};

export interface SimOptions {
  laps?: number;
  /** Varies everything a seed decides (starts, drift choices, mistakes, item moments). */
  seed?: number;
  /** Slot 0: a player stand-in of this skill (absent: rival 0's roster skill). */
  player?: AiSkill;
  /** Give up after this many seconds. */
  maxSeconds?: number;
  /** Rivals use items (default on). */
  items?: boolean;
  /** Use the catch-up (default on). */
  catchUp?: boolean;
  /** Log this kart's state every second. */
  trace?: number;
  /** Every kart on this kart class (characters.json id) instead of its own. */
  kartClass?: string;
  /** Shuffle the starting grid by the seed (else entrant order, the player on pole). */
  shuffleGrid?: boolean;
  /** tuning.json's "ai" settings to change (for balancing). */
  ai?: Partial<typeof tuning.ai>;
  /** The field's setups instead of assets/data/rivals.json (for balancing). */
  rivals?: SkillConfig;
  /** Log every this many physics steps (120 = a second). */
  traceEvery?: number;
}

export interface SimKart {
  name: string;
  tier: string;
  finished: boolean;
  place: number;
  time: number;
  lapTimes: number[];
  respawns: number;
  recoveries: number;
  drifting: number;
  itemsFired: number;
  hitsTaken: number;
  walls: number;
  /** Where each respawn happened (x, z, why: off = below killY / respawn surface, race = the race's own reset). */
  respawnAt: { x: number; z: number; why: string }[];
  /** Where it made under 10 m of progress in 6 s (once per spell), with the race time. */
  stuckAt: { x: number; z: number; t: number }[];
}

export function raceSim(p: TrackPackage, opts: SimOptions = {}) {
  const laps = opts.laps ?? 3;
  const ai = { ...tuning.ai, ...opts.ai };
  const seed = opts.seed ?? 1;
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const lineCfg = {
    margin: p.trackData.aiLineMargin ?? tuning.ai.lineMargin,
    span: tuning.ai.lineSpan,
    iterations: tuning.ai.lineIterations,
  };
  const lines = [
    buildRacingLine(track, lineCfg),
    ...p.lapRoutes.map((r) =>
      buildRacingLine(buildTrack(r.trackData, tuning.track.sampleSpacing), lineCfg),
    ),
  ];
  const pads = [
    ...buildZippers(
      track,
      (p.trackData.zippers ?? []).filter((z) => !z.route),
      tuning.track,
    ),
    ...p.lapRoutes.flatMap((r) =>
      buildZippers(
        buildTrack(r.trackData, tuning.track.sampleSpacing),
        (p.trackData.zippers ?? []).filter((z) => z.route === r.id),
        tuning.track,
      ),
    ),
  ];
  const padsSeen = pads.map((z) => ({ x: z.x, y: z.y, z: z.z }));
  const rivals = roster.rivals;
  const n = rivals.length + 1;
  const find = (id: string) => roster.characters.find((c) => c.id === id) as Character;
  const entrants = Array.from({ length: n }, (_, i) => {
    const r = rivals[(i + rivals.length - 1) % rivals.length]!;
    const s = rivalSkill(r.name, opts.rivals ?? (rivalSetups as SkillConfig));
    const isPlayer = i === 0 && opts.player;
    return {
      name: isPlayer ? "player" : r.name,
      tier: isPlayer ? "player" : s.tier,
      character: find(opts.kartClass ?? roster.default),
      skill: isPlayer ? opts.player! : s.skill,
    };
  });
  // Grid slots: in entrant order (the player on pole), or shuffled by the seed.
  const gridOrder = Array.from({ length: n }, (_, i) => i);
  if (opts.shuffleGrid)
    for (let i = n - 1; i > 0; i--) {
      const j = Math.floor(
        ((((Math.sin(seed * 97.13 + i * 13.7) * 43758.5453) % 1) + 1) % 1) * (i + 1),
      );
      [gridOrder[i], gridOrder[j]] = [gridOrder[j]!, gridOrder[i]!];
    }
  const race = createRace(track, tuning.race, n);
  const ground = entrants.map(() => createMeshGround(p.collision));
  const karts = entrants.map((_, i) => {
    const g = gridSlot(track, gridOrder[i]!);
    const k = createKartState(g.x, g.z, g.heading, g.y);
    k.y = ground[i]!.at(k.x, k.z, k.y + 1).height;
    return k;
  });
  const drivers: Driver[] = entrants.map((e, i) =>
    createDriver(lines[i % lines.length]!, i * 101 + seed * 7919, ai, e.skill),
  );
  const items = entrants.map(() => racerItems());
  const world = createItemWorld(track, p.trackData.balloons ?? [], () =>
    createMeshGround(p.collision),
  );
  const loops = createLoops(p.meta.entities ?? [], n);
  // The course's respawn zones (as src/game/hazards.ts): a fall inside one is put back
  // at its spot (past a jump's gap, say) instead of at the last gate.
  const zones = (p.meta.entities ?? []).flatMap((e) => {
    const o = e as { type?: string; from?: number; to?: number; at?: number };
    return o.type === "respawn" ? [{ from: o.from ?? 0, to: o.to ?? 0, at: o.at ?? 0 }] : [];
  });
  /** Each kart's last spot on the road, grounded (a fall's zone is looked up from here too). */
  const lastRoad = Array.from({ length: n }, () => ({ x: NaN, y: NaN, z: NaN }));
  const zoneSpot = (x: number, y: number, z: number) => {
    if (!Number.isFinite(x)) return undefined;
    if (!zones.length) return undefined;
    let near = track.samples[0]!;
    let nd = Infinity;
    for (const q of track.samples) {
      const d = (q.pos.x - x) ** 2 + (q.pos.z - z) ** 2 + ((q.pos.y - y) * 2) ** 2;
      if (d < nd) [nd, near] = [d, q];
    }
    const zn = zones.find((zn) => near.dist >= zn.from && near.dist <= zn.to);
    if (!zn) return undefined;
    const L = track.length;
    const d = ((zn.at % L) + L) % L;
    let best = track.samples[0]!;
    for (const q of track.samples) if (q.dist <= d + 1e-6) best = q;
    return {
      x: best.pos.x,
      y: best.pos.y,
      z: best.pos.z,
      heading: Math.atan2(best.forward.x, best.forward.z),
    };
  };
  const onBoost = entrants.map(() => false);
  const stuckHist: number[][] = [];
  const stuckNow: boolean[] = [];
  const stats: SimKart[] = entrants.map((e) => ({
    name: e.name,
    tier: e.tier,
    finished: false,
    place: 0,
    time: 0,
    lapTimes: [],
    respawns: 0,
    recoveries: 0,
    drifting: 0,
    itemsFired: 0,
    hitsTaken: 0,
    walls: 0,
    respawnAt: [],
    stuckAt: [],
  }));
  const posOf = (j: number) => (loops?.riding(j) ? loops.racePos(j, karts[j]!) : karts[j]!);
  const progressOf = (j: number) => {
    const at = posOf(j);
    // Roughly metres along the race (the catch-up and the rivals' item sense count metres).
    return progress(race, j, at.x, at.z, at.y) * race.metresPerCheckpoint;
  };
  const base = entrants.map((e) =>
    applyCharacter(tuning.vehicle as KartConfig, e.character, tuning.stats),
  );
  let t = 0;
  const maxT = opts.maxSeconds ?? 140 * laps;
  const useItems = opts.items ?? true;
  for (; t < maxT && !race.racers.every((r) => r.finished); t += dt) {
    tickRace(race, dt);
    const moment = {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startRefHz: tuning.race.startRefHz,
    };
    const racers: Racer[] = entrants.map((e, i) => {
      const gap = i > 0 && race.phase !== "countdown" ? progressOf(i) - progressOf(0) : 0;
      const assist = opts.catchUp === false || i === 0 ? 1 : catchUp(gap, ai as CatchUpConfig);
      let cfg = {
        ...base[i]!,
        topSpeed: base[i]!.topSpeed * ai.speedMult * e.skill.pace * assist,
      };
      const k = karts[i]!;
      if (k.grounded && !loops?.riding(i)) {
        const s = ground[i]!.at(k.x, k.z, k.y).surface;
        cfg = applySurface(cfg, s ? SURFACES[s] : undefined);
      }
      return { kart: k, items: items[i]!, cfg };
    });
    for (let i = 0; i < n; i++) {
      const k = karts[i]!;
      const cfg = racers[i]!.cfg;
      const riding = loops?.riding(i) ?? false;
      const aiWorld: AiWorld = {
        others: karts
          .filter((_, j) => j !== i)
          .map((o) => ({ x: o.x, y: o.y, z: o.z, speed: o.speed, heading: o.heading })),
        pads: padsSeen,
        traps: world.traps,
      };
      const input = driveAi(
        drivers[i]!,
        riding ? { ...k, ...loops!.racePos(i, k) } : k,
        cfg,
        ai,
        moment,
        loops?.aim(i, k),
        aiWorld,
        dt,
      );
      if (riding) input.steer = loops!.aiSteer(i);
      if (drivers[i]!.state === "recover" && drivers[i]!.reversing > 0.88) stats[i]!.recoveries++;
      if (useItems && race.phase !== "countdown") {
        const it = aiItem(drivers[i]!, i, racers, world, itemsCfg, progressOf, dt);
        if (it.fire) {
          const ev = fireItem(world, racers, i, it.lift ? 0 : input.throttle, itemsCfg, progressOf);
          if (ev?.type === "fire") {
            stats[i]!.itemsFired++;
            if (ev.color === "blue") drivers[i]!.boostTechnique = it.lift;
          }
        }
      }
      if (items[i]!.bubbleTime > 0) Object.assign(input, NEUTRAL);
      stepImpacts(k, tuning.collision, dt);
      const before = { x: k.x, y: k.y, z: k.z };
      const want = race.phase === "countdown" ? NEUTRAL : input;
      stepKart(k, loops ? loops.input(i, k, want) : want, cfg, dt);
      if (k.driftDir !== 0) stats[i]!.drifting += dt;
      if (!riding && enteredZipper(k, pads)) startZipper(k, input.throttle, cfg);
      if (!riding) {
        if (stepMeshWalls(k, p.collision, wallCfg, dt)) stats[i]!.walls++;
        stepVertical(k, ground[i]!, tuning.physics, dt);
      }
      loops?.step(i, k, before, input.steer, cfg, dt);
      if (!loops?.riding(i)) {
        const s = ground[i]!.at(k.x, k.z, k.y).surface;
        const boost = Boolean(k.grounded && s && SURFACES[s]?.boost);
        if (boost && !onBoost[i]) startZipper(k, input.throttle, cfg);
        onBoost[i] = boost;
      }
      const ridingNow = loops?.riding(i) ?? false;
      const at = ridingNow ? { ...k, ...loops!.racePos(i, k) } : k;
      const ev = stepRacer(
        race,
        i,
        at,
        ridingNow || ground[i]!.at(k.x, k.z, k.y).onRoad,
        input.throttle,
        tuning.race,
        dt,
      );
      if (ev.boost) applyBoost(k, cfg, ev.boost.mult, ev.boost.seconds);
      const under = k.grounded ? ground[i]!.at(k.x, k.z, k.y).surface : undefined;
      if (k.grounded && !ridingNow && ground[i]!.at(k.x, k.z, k.y).onRoad)
        Object.assign(lastRoad[i]!, { x: k.x, y: k.y, z: k.z });
      const lr = lastRoad[i]!;
      const zoned = () => zoneSpot(k.x, k.y, k.z) ?? zoneSpot(lr.x, lr.y, lr.z);
      const fell = !ridingNow && (k.y < p.killY || (under && SURFACES[under]?.respawn));
      const lost = drivers[i]!.wantsRespawn && !ridingNow;
      drivers[i]!.wantsRespawn = false;
      if (ev.respawn || fell || lost) {
        stats[i]!.respawnAt.push({
          x: +k.x.toFixed(0),
          z: +k.z.toFixed(0),
          why:
            !fell && !ev.respawn
              ? "lost"
              : fell
                ? (k.y < p.killY ? "killY" : String(under)) + (zoned() ? "+zone" : "")
                : "race",
        });
        const g = ev.respawn ?? zoned() ?? respawnSpot(race, i);
        const bananas = k.bananas;
        Object.assign(k, createKartState(g.x, g.z, g.heading, g.y));
        k.bananas = bananas;
        loops?.reset(i);
        teleported(race, i, k);
        stats[i]!.respawns++;
      }
    }
    if (race.phase !== "countdown" && Math.round(t * 120) % 120 === 0) {
      for (let i = 0; i < n; i++) {
        if (race.racers[i]!.finished) continue;
        const h = (stuckHist[i] ??= []);
        h.push(progressOf(i));
        if (h.length > 6) {
          const moved = h[h.length - 1]! - h[h.length - 7]!;
          if (moved < 10 && !stuckNow[i] && t > 15) {
            stuckNow[i] = true;
            stats[i]!.stuckAt.push({
              x: +karts[i]!.x.toFixed(0),
              z: +karts[i]!.z.toFixed(0),
              t: +t.toFixed(0),
            });
          } else if (moved >= 10) stuckNow[i] = false;
        }
      }
    }
    if (opts.trace !== undefined && Math.round(t * 120) % (opts.traceEvery ?? 120) === 0) {
      const k = karts[opts.trace]!;
      const d = drivers[opts.trace]!;
      console.log(
        `t ${t.toFixed(0)} (${k.x.toFixed(1)},${k.y.toFixed(1)},${k.z.toFixed(1)}) v ${k.speed.toFixed(1)} h ${k.heading.toFixed(2)} idx ${d.index} line(${d.line.x[d.index]!.toFixed(0)},${d.line.y[d.index]!.toFixed(0)},${d.line.z[d.index]!.toFixed(0)}) ${d.state} off ${d.offset.toFixed(1)} gnd ${k.grounded}`,
      );
    }
    const free = karts.map((_, i) => i).filter((i) => !loops?.riding(i));
    bumpKarts(
      free.map((i) => karts[i]!),
      tuning.physics.kartBump,
      free.map(() => 1),
      (a, b) => {
        shieldRam(
          racers[free[a]!]!,
          racers[free[b]!]!,
          free[a]!,
          free[b]!,
          itemsCfg,
          tuning.bananas,
        );
      },
    );
    loops?.contacts(karts);
    stepEffects(racers, itemsCfg, dt);
    collectBalloons(world, racers, itemsCfg, () => itemsCfg.aiCollect);
    for (const ev of stepItemWorld(world, racers, itemsCfg, tuning.bananas, dt, progressOf))
      if (ev.type === "hit" && !ev.blocked) stats[ev.racer]!.hitsTaken++;
  }
  race.racers.forEach((r, i) => {
    stats[i]!.finished = r.finished;
    stats[i]!.lapTimes = r.lapTimes;
    stats[i]!.time = r.totalTime ?? Infinity;
  });
  race.finishOrder.forEach((i, place) => (stats[i]!.place = place + 1));
  let next = race.finishOrder.length + 1;
  stats.forEach((s) => {
    if (!s.place) s.place = next++;
  });
  return { stats, seconds: t };
}
