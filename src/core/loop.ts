import { createFixedStep, type FixedStep } from "./fixedStep";

export interface LoopCallbacks {
  /**
   * Advance the simulation by exactly one fixed step. `at` is the moment (ms, page time)
   * the step stands for: a frame's steps run together, the last one at "now".
   */
  update(stepSeconds: number, tick: number, at: number): void;
  /** Draw the current state. alpha is 0..1 between the last two steps. */
  render(alpha: number, frameSeconds: number): void;
}

export interface Loop {
  start(): void;
  stop(): void;
  readonly clock: FixedStep;
}

export function createLoop(hz: number, maxSteps: number, callbacks: LoopCallbacks): Loop {
  const clock = createFixedStep(hz, maxSteps);
  let last = 0;
  let handle = 0;
  let running = false;

  const frame = (now: number) => {
    if (!running) return;
    const frameSeconds = last === 0 ? 0 : (now - last) / 1000;
    last = now;
    const steps = clock.advance(frameSeconds);
    for (let i = 0; i < steps; i++) {
      const at = now - (steps - 1 - i + clock.alpha) * clock.stepSeconds * 1000;
      callbacks.update(clock.stepSeconds, clock.tick - steps + i + 1, at);
    }
    callbacks.render(clock.alpha, frameSeconds);
    handle = requestAnimationFrame(frame);
  };

  return {
    start() {
      if (running) return;
      running = true;
      last = 0;
      handle = requestAnimationFrame(frame);
    },
    stop() {
      running = false;
      cancelAnimationFrame(handle);
    },
    clock,
  };
}
