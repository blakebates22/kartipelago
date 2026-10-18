/**
 * One input state for the whole game, merged from keyboard and gamepad.
 *
 * Gameplay code never reads devices directly. It calls input.sample(dt, drifting) once per fixed
 * step and reads the result, so keyboard and gamepad behave identically and the
 * simulation stays deterministic for a given input sequence.
 */
import { tuning } from "./tuning";

export interface InputState {
  /** 0..1 */
  throttle: number;
  /** 0..1. Brakes when moving forward, reverses when stopped. */
  brake: number;
  /** -1 (left) .. 1 (right) */
  steer: number;
  drift: boolean;
}

/** Raw readings from one device, before any smoothing. */
export interface DeviceReading {
  throttle: number;
  brake: number;
  /** Target steering, -1..1. */
  steer: number;
  drift: boolean;
}

export interface InputConfig {
  stickDeadzone: number;
  /** 1 = linear stick response; higher = finer control near centre. */
  stickCurve: number;
  /** Keyboard steering ramp toward full lock, per second. */
  keySteerRate: number;
  /** Keyboard steering ramp back to centre (and through it when reversing), per second. */
  keySteerReturn: number;
  /**
   * While drifting, keys build steering more slowly, so tap length gives fine control:
   * a short tap nudges the arc, holding commits to it.
   */
  driftKeyRate: number;
  /** While drifting, how fast released keys ease steering back to centre, per second. */
  driftKeyReturn: number;
  /** While drifting, how fast steering swings through centre to the other side, per second. */
  driftKeyReverse: number;
}

export const NEUTRAL: Readonly<DeviceReading> = { throttle: 0, brake: 0, steer: 0, drift: false };

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/** Apply a radial-ish deadzone to one stick axis, rescaled so output still reaches ±1. */
export function shapeStick(x: number, deadzone: number, curve: number): number {
  const mag = Math.abs(x);
  if (mag <= deadzone) return 0;
  const t = clamp((mag - deadzone) / (1 - deadzone), 0, 1);
  return Math.sign(x) * Math.pow(t, curve);
}

/**
 * Keys are digital, so steering ramps instead of snapping. This makes small corrections
 * possible on a keyboard. Releasing or switching direction recentres at the return rate.
 * While drifting, a separate, slower build-up makes tap length the fine control, with a
 * fast swing through centre so changes of direction stay responsive.
 */
export function rampKeySteer(
  current: number,
  target: number,
  dt: number,
  cfg: InputConfig,
  drifting = false,
): number {
  const reversing = target !== 0 && current !== 0 && Math.sign(target) !== Math.sign(current);
  const releasing = target === 0 && current !== 0;
  let rate: number;
  if (drifting) {
    rate = reversing ? cfg.driftKeyReverse : releasing ? cfg.driftKeyReturn : cfg.driftKeyRate;
  } else {
    rate = reversing || releasing ? cfg.keySteerReturn : cfg.keySteerRate;
  }
  const step = rate * dt;
  if (Math.abs(target - current) <= step) return target;
  return current + Math.sign(target - current) * step;
}

/** Merge devices: the stronger reading wins on each axis, buttons are OR'd. */
export function mergeReadings(a: DeviceReading, b: DeviceReading): DeviceReading {
  return {
    throttle: Math.max(a.throttle, b.throttle),
    brake: Math.max(a.brake, b.brake),
    steer: Math.abs(b.steer) > Math.abs(a.steer) ? b.steer : a.steer,
    drift: a.drift || b.drift,
  };
}

const KEYS = {
  throttle: ["KeyW", "ArrowUp"],
  brake: ["KeyS", "ArrowDown"],
  left: ["KeyA", "ArrowLeft"],
  right: ["KeyD", "ArrowRight"],
  drift: ["Space", "ShiftLeft", "ShiftRight"],
} as const;

const GAME_KEYS = new Set<string>(Object.values(KEYS).flat());

/** Standard Gamepad API button indices. */
const PAD = { a: 0, b: 1, x: 2, lb: 4, rb: 5, lt: 6, rt: 7, left: 14, right: 15 } as const;

export function readGamepad(pad: Gamepad, cfg: InputConfig): DeviceReading {
  const value = (i: number) => pad.buttons[i]?.value ?? 0;
  const pressed = (i: number) => pad.buttons[i]?.pressed ?? false;
  const stick = shapeStick(pad.axes[0] ?? 0, cfg.stickDeadzone, cfg.stickCurve);
  const dpad = (pressed(PAD.right) ? 1 : 0) - (pressed(PAD.left) ? 1 : 0);
  return {
    throttle: Math.max(value(PAD.rt), pressed(PAD.a) ? 1 : 0),
    brake: Math.max(value(PAD.lt), pressed(PAD.x) ? 1 : 0),
    steer: dpad !== 0 ? dpad : stick,
    drift: pressed(PAD.rb) || pressed(PAD.lb),
  };
}

export function createInput(target: Window = window) {
  const held = new Set<string>();
  let keySteer = 0;
  const state: InputState = { ...NEUTRAL };

  const isTyping = (e: KeyboardEvent) =>
    e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;

  target.addEventListener("keydown", (e) => {
    if (isTyping(e) || !GAME_KEYS.has(e.code)) return;
    held.add(e.code);
    e.preventDefault(); // stop arrows and space scrolling the page
  });
  target.addEventListener("keyup", (e) => held.delete(e.code));
  // Keys released while the tab is unfocused never fire keyup; don't leave them stuck.
  target.addEventListener("blur", () => held.clear());

  const any = (codes: readonly string[]) => codes.some((c) => held.has(c));

  return {
    state: state as Readonly<InputState>,

    /** Read all devices and update state. Call once per fixed step. */
    sample(dt: number, drifting = false): Readonly<InputState> {
      const cfg = tuning.input;
      const steerTarget = (any(KEYS.right) ? 1 : 0) - (any(KEYS.left) ? 1 : 0);
      keySteer = rampKeySteer(keySteer, steerTarget, dt, cfg, drifting);

      let merged: DeviceReading = {
        throttle: any(KEYS.throttle) ? 1 : 0,
        brake: any(KEYS.brake) ? 1 : 0,
        steer: keySteer,
        drift: any(KEYS.drift),
      };
      for (const pad of navigator.getGamepads?.() ?? []) {
        if (pad?.connected) merged = mergeReadings(merged, readGamepad(pad, cfg));
      }

      Object.assign(state, merged);
      return state;
    },
  };
}

export type Input = ReturnType<typeof createInput>;
