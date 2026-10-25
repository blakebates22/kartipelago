// Shared by the imported-track tests: one AI lap with the race's own driver.
import tuning from "../assets/data/tuning.json";
import { NEUTRAL } from "../src/core/input";
import { createDriver, driveAi } from "../src/ai/driver";
import type { AiSkill } from "../src/ai/skill";
import { createLoops } from "../src/game/loops";
import { buildRacingLine } from "../src/ai/racingLine";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../src/physics/walls";
import { createRace, respawnSpot, stepRacer, teleported, tickRace } from "../src/race/race";
import { createKartState, stepKart, type KartConfig } from "../src/vehicles/kart";
import { applySurface, createMeshGround } from "../src/world/collisionMesh";
import { buildTrack } from "../src/world/track";
import { buildZippers, enteredZipper } from "../src/world/zippers";
import { startZipper } from "../src/vehicles/zipper";
import { SURFACES, type TrackPackage } from "../src/world/trackPackage";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

export interface LapOptions {
  /** Laps to drive (default 1). */
  laps?: number;
  /** Apply each surface's speed and grip, and its respawn, like a race does. */
  surfaces?: boolean;
  /** Record the kart's position every this many seconds. */
  trace?: number;
  /** Give up after this many seconds a lap (default 90). */
  lapSeconds?: number;
  /** Override the AI's settings (e.g. { drift: 0 }: steer every corner, never drift). */
  ai?: Partial<typeof tuning.ai>;
  /** Branching courses: drive this whole-lap route (TrackMeta.lapRoutes) instead of main. */
  route?: string;
  /** Fire zipper pads (main route's and every lap route's) as a race does. */
  zippers?: boolean;
  /** The driver's skill (src/ai/skill.ts); absent: the steady test driver. */
  skill?: AiSkill;
}

/** Drive one kart round an imported track with the race's own AI driver. */
export async function aiLap(p: TrackPackage, opts: LapOptions = {}) {
  const laps = opts.laps ?? 1;
  const ai = { ...tuning.ai, ...opts.ai };
  let respawns = 0;
  const visited = new Set<string>();
  const path: {
    t: number;
    x: number;
    y: number;
    z: number;
    v: number;
    gate: number;
    drift?: number;
    steer?: number;
    h?: number;
    va?: number;
  }[] = [];
  let nextTrace = 0;
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const alt = opts.route ? p.lapRoutes.find((r) => r.id === opts.route) : undefined;
  if (opts.route && !alt) throw new Error(`no lap route ${opts.route}`);
  const line = buildRacingLine(
    alt ? buildTrack(alt.trackData, tuning.track.sampleSpacing) : track,
    {
      margin: tuning.ai.lineMargin,
      span: tuning.ai.lineSpan,
      iterations: tuning.ai.lineIterations,
    },
  );
  const race = createRace(track, tuning.race, 1);
  const pads = opts.zippers
    ? [
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
      ]
    : [];
  let zips = 0;
  const driver = createDriver(line, 1, ai, opts.skill);
  const ground = createMeshGround(p.collision);
  const start = track.start;
  const k = createKartState(start.x, start.z, start.heading, track.samples[0]!.pos.y);
  k.y = ground.at(k.x, k.z, k.y + 0.5).height;
  // Loop-the-loops ride the kart round themselves (src/game/loops.ts), as in a race.
  const loops = createLoops(p.meta.entities ?? [], 1);
  let loopsRidden = 0;
  let inverted = 0;
  let lowest = Infinity;
  let worstAbove = 0;
  let walls = 0;
  const wallHits: { x: number; y: number; z: number }[] = [];
  for (
    let t = 0;
    t < (opts.lapSeconds ?? 90) * laps && race.racers[0]!.lapTimes.length < laps;
    t += dt
  ) {
    tickRace(race, dt);
    const riding = loops?.riding(0) ?? false;
    const input = driveAi(
      driver,
      riding ? { ...k, ...loops!.racePos(0, k) } : k,
      cfg,
      ai,
      {
        countdown: race.phase === "countdown",
        clock: race.clock,
        startRefHz: tuning.race.startRefHz,
      },
      loops?.aim(0, k),
    );
    if (riding) input.steer = loops!.aiSteer(0);
    stepImpacts(k, tuning.collision, dt);
    let c = cfg;
    const here = ground.at(k.x, k.z, k.y);
    if (opts.surfaces && k.grounded && here.surface && !riding) {
      visited.add(here.surface);
      c = applySurface(cfg, SURFACES[here.surface]);
    }
    const before = { x: k.x, y: k.y, z: k.z };
    const want = race.phase === "countdown" ? NEUTRAL : input;
    stepKart(k, loops ? loops.input(0, k, want) : want, c, dt);
    if (!riding && enteredZipper(k, pads)) {
      startZipper(k, input.throttle, c);
      zips++;
    }
    if (!riding) {
      if (stepMeshWalls(k, p.collision, wallCfg, dt)) {
        walls++;
        wallHits.push({ x: k.x, y: k.y, z: k.z, t, drift: k.driftDir, v: k.speed } as {
          x: number;
          y: number;
          z: number;
        });
      }
      stepVertical(k, ground, tuning.physics, dt);
    }
    if (loops) {
      const lp = loops.step(0, k, before, input.steer, c, dt);
      if (lp.entered) loopsRidden++;
      if (loops.riding(0) && k.ny < -0.9) inverted++;
    }
    const at = loops?.riding(0) ? { ...k, ...loops.racePos(0, k) } : k;
    const ev = stepRacer(
      race,
      0,
      at,
      loops?.riding(0) ? true : ground.at(k.x, k.z, k.y).onRoad,
      input.throttle,
      tuning.race,
      dt,
    );
    const under = k.grounded ? ground.at(k.x, k.z, k.y).surface : undefined;
    const fell =
      !loops?.riding(0) && (k.y < p.killY || (opts.surfaces && under && SURFACES[under]?.respawn));
    if (ev.respawn || fell) {
      const g = ev.respawn ?? respawnSpot(race, 0);
      Object.assign(k, createKartState(g.x, g.z, g.heading, g.y));
      loops?.reset(0);
      teleported(race, 0, k);
      respawns++;
    }
    if (opts.trace && t >= nextTrace) {
      nextTrace += opts.trace;
      path.push({
        t,
        x: k.x,
        y: k.y,
        z: k.z,
        v: k.speed,
        gate: race.racers[0]!.last,
        drift: k.driftDir,
        steer: input.steer,
        h: k.heading,
        va: k.velAngle,
      });
    }
    lowest = Math.min(lowest, k.y);
    // How far above the nearest route point's height the kart is (wrong layer = ~8 m).
    if (k.grounded && !loops?.riding(0)) {
      let near = track.samples[0]!;
      let nd = Infinity;
      for (const s of track.samples) {
        const d = (s.pos.x - k.x) ** 2 + (s.pos.z - k.z) ** 2 + ((s.pos.y - k.y) * 3) ** 2;
        if (d < nd) {
          nd = d;
          near = s;
        }
      }
      worstAbove = Math.max(worstAbove, Math.abs(k.y - near.pos.y));
    }
  }
  return {
    race,
    lowest,
    worstAbove,
    walls,
    /** Where the kart touched a wall. */
    wallHits,
    killY: p.killY,
    respawns,
    /** Zipper pads fired. */
    zips,
    /** Loops driven onto, and steps spent upside down on one. */
    loopsRidden,
    inverted,
    surfaces: visited,
    kart: k,
    path,
  };
}
