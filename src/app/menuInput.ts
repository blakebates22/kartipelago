/**
 * Menu input: keyboard, gamepad and mouse merged into a few actions.
 *
 * Only the screen manager reads this, once per frame, so there's exactly one place that
 * acts on menu keys. Directions repeat while held (after a pause); Confirm, Back and
 * Pause never repeat, so holding a key can't skip through several screens.
 * Gameplay keeps its own input (core/input.ts), which only the race reads.
 */

export type MenuAction = "up" | "down" | "left" | "right" | "confirm" | "back" | "pause";

const KEYMAP: Record<string, MenuAction> = {
  ArrowUp: "up",
  KeyW: "up",
  ArrowDown: "down",
  KeyS: "down",
  ArrowLeft: "left",
  KeyA: "left",
  ArrowRight: "right",
  KeyD: "right",
  Enter: "confirm",
  NumpadEnter: "confirm",
  Space: "confirm",
  KeyZ: "confirm",
  Escape: "back",
  Backspace: "back",
  KeyX: "back",
  KeyP: "pause",
};

const DIRECTIONS = new Set<MenuAction>(["up", "down", "left", "right"]);

/** Standard gamepad buttons. */
const PAD: [number, MenuAction][] = [
  [0, "confirm"], // A
  [1, "back"], // B
  [9, "pause"], // Start
  [12, "up"],
  [13, "down"],
  [14, "left"],
  [15, "right"],
];

const REPEAT_DELAY = 0.38;
const REPEAT_EVERY = 0.11;

export interface Pointer {
  /** Logical UI coordinates (set by the UI layer). */
  x: number;
  y: number;
  /** Moved since the last frame (mouse focus follows the pointer only when it moves). */
  moved: boolean;
  /** Pressed this frame. */
  clicked: boolean;
  /** Wheel steps this frame (+ = down). */
  wheel: number;
  inside: boolean;
}

export function createMenuInput(target: Window = window) {
  const queue: MenuAction[] = [];
  /** Escape both backs out of menus and pauses a race: the screen decides. */
  let escapePressed = false;
  const held: Partial<Record<string, number>> = {};
  const padHeld = new Map<string, number>();
  const pointer: Pointer = { x: -1, y: -1, moved: false, clicked: false, wheel: 0, inside: false };

  target.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (e.target as { tagName?: string } | null)?.tagName;
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
    const a = KEYMAP[e.code];
    if (!a) return;
    if (e.repeat) {
      // Browser key repeat is too fast for menus; we time repeats ourselves.
      return;
    }
    held[e.code] = 0;
    queue.push(a);
    if (e.code === "Escape") escapePressed = true;
  });
  target.addEventListener("keyup", (e) => delete held[e.code]);
  target.addEventListener("blur", () => {
    for (const k of Object.keys(held)) delete held[k];
    padHeld.clear();
  });

  return {
    pointer,
    /**
     * This frame's actions (each listed once per press or repeat). Call once per frame.
     */
    poll(dt: number): MenuAction[] {
      const out = queue.splice(0);
      // Held directions repeat.
      for (const [code, t] of Object.entries(held)) {
        const a = KEYMAP[code]!;
        if (!DIRECTIONS.has(a)) continue;
        const next = t! + dt;
        held[code] = next;
        if (next > REPEAT_DELAY) {
          out.push(a);
          held[code] = REPEAT_DELAY - REPEAT_EVERY;
        }
      }
      // Gamepads: buttons, d-pad and left stick, with the same repeat.
      const pressed = new Set<MenuAction>();
      for (const pad of navigator.getGamepads?.() ?? []) {
        if (!pad?.connected) continue;
        for (const [i, a] of PAD) if (pad.buttons[i]?.pressed) pressed.add(a);
        const [x = 0, y = 0] = pad.axes;
        if (x < -0.55) pressed.add("left");
        if (x > 0.55) pressed.add("right");
        if (y < -0.55) pressed.add("up");
        if (y > 0.55) pressed.add("down");
      }
      for (const a of pressed) {
        const t = padHeld.get(a);
        if (t === undefined) {
          padHeld.set(a, 0);
          out.push(a);
        } else if (DIRECTIONS.has(a)) {
          const next = t + dt;
          if (next > REPEAT_DELAY) {
            out.push(a);
            padHeld.set(a, REPEAT_DELAY - REPEAT_EVERY);
          } else padHeld.set(a, next);
        }
      }
      for (const a of [...padHeld.keys()]) if (!pressed.has(a as MenuAction)) padHeld.delete(a);
      return out;
    },
    /** Was Escape (rather than another Back key) pressed this frame? */
    takeEscape() {
      const e = escapePressed;
      escapePressed = false;
      return e;
    },
    /** Clear the pointer's per-frame flags (after the UI has read them). */
    endFrame() {
      pointer.moved = false;
      pointer.clicked = false;
      pointer.wheel = 0;
    },
    /** Forget everything held (after a screen change, so nothing carries over). */
    flush() {
      queue.length = 0;
      for (const k of Object.keys(held)) held[k] = -10; // held keys don't repeat into the new screen
      for (const k of padHeld.keys()) padHeld.set(k, -10);
    },
  };
}

export type MenuInput = ReturnType<typeof createMenuInput>;
