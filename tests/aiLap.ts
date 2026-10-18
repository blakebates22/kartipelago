// Shared by the imported-track tests: one AI lap with the race's own driver.
import tuning from "../assets/data/tuning.json";
import { NEUTRAL } from "../src/core/input";
import { createDriver, driveAi } from "../src/ai/driver";
import { buildRacingLine } from "../src/ai/racingLine";
import { stepVertical } from "../src/physics/vertical";
import { stepImpacts, stepMeshWalls } from "../src/physics/walls";
import { createRace, stepRacer, tickRace } from "../src/race/race";
import { createKartState, stepKart, type KartConfig } from "../src/vehicles/kart";
import { createMeshGround } from "../src/world/collisionMesh";
import { buildTrack } from "../src/world/track";
import type { TrackPackage } from "../src/world/trackPackage";

const dt = 1 / 120;
const cfg: KartConfig = { ...tuning.vehicle };
const wallCfg = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

/** Drive one kart round an imported track with the race's own AI driver. */
export async function aiLap(p: TrackPackage) {
  const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
  const line = buildRacingLine(track, {
    margin: tuning.ai.lineMargin,
    span: tuning.ai.lineSpan,
    iterations: tuning.ai.lineIterations,
  });
  const race = createRace(track, tuning.race, 1);
  const driver = createDriver(line, 1, tuning.ai);
  const ground = createMeshGround(p.collision);
  const start = track.start;
  const k = createKartState(start.x, start.z, start.heading, track.samples[0]!.pos.y);
  k.y = ground.at(k.x, k.z, k.y + 0.5).height;
  let lowest = Infinity;
  let worstAbove = 0;
  let walls = 0;
  for (let t = 0; t < 90 && !race.racers[0]!.lapTimes.length; t += dt) {
    tickRace(race, dt);
    const input = driveAi(driver, k, cfg, tuning.ai, {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startTarget: -1,
    });
    stepImpacts(k, tuning.collision, dt);
    stepKart(k, race.phase === "countdown" ? NEUTRAL : input, cfg, dt);
    if (stepMeshWalls(k, p.collision, wallCfg, dt)) walls++;
    stepVertical(k, ground, tuning.physics, dt);
    stepRacer(race, 0, k, ground.at(k.x, k.z, k.y).onRoad, input.throttle, tuning.race, dt);
    lowest = Math.min(lowest, k.y);
    // How far above the nearest route point's height the kart is (wrong layer = ~8 m).
    if (k.grounded) {
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
  return { race, lowest, worstAbove, walls, killY: p.killY };
}
