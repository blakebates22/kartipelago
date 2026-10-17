/**
 * Fixed-timestep accumulator.
 *
 * Rendering runs at whatever rate the browser gives us, but simulation
 * (physics, AI, race logic) always advances in identical steps. This keeps
 * vehicle handling the same on a 60 Hz laptop and a 144 Hz monitor, and makes
 * bugs reproducible.
 */
export interface FixedStep {
  /** Feed real elapsed seconds; returns how many simulation steps to run now. */
  advance(elapsedSeconds: number): number;
  /** 0..1 progress toward the next step, used to interpolate rendering. */
  readonly alpha: number;
  readonly stepSeconds: number;
  /** Total steps simulated so far. */
  readonly tick: number;
}

export function createFixedStep(hz: number, maxStepsPerFrame: number): FixedStep {
  if (hz <= 0) throw new Error(`physics rate must be positive, got ${hz}`);
  const stepSeconds = 1 / hz;
  let accumulator = 0;
  let tick = 0;

  return {
    advance(elapsedSeconds: number): number {
      accumulator += Math.max(0, elapsedSeconds);
      let steps = Math.floor(accumulator / stepSeconds);
      if (steps > maxStepsPerFrame) {
        // Tab was in the background or a frame hitched: drop the backlog
        // instead of fast-forwarding the race (the "spiral of death").
        steps = maxStepsPerFrame;
        accumulator = 0;
      } else {
        accumulator -= steps * stepSeconds;
      }
      tick += steps;
      return steps;
    },
    get alpha() {
      return accumulator / stepSeconds;
    },
    get tick() {
      return tick;
    },
    stepSeconds,
  };
}
