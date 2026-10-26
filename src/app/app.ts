/**
 * The screen manager: which screen is showing, the transitions between them, and the
 * frame/step loop that drives them.
 *
 * Screens live on a stack. Most transitions replace the whole stack (`go`); pause
 * menus, options and dialogs are pushed on top of the screen they belong to (`push`)
 * and popped off again. Only the top screen gets menu input. The 3D view is drawn by
 * the highest screen that has one (the race under its pause menu, the title demo under
 * the options).
 *
 * Every `go` bumps a token. Anything that finishes loading later checks its token and
 * throws its result away if you've moved on, so a slow track load can never yank you
 * out of a menu you went back to.
 */
import type { MenuAction, MenuInput } from "./menuInput";
import type { UiLayer } from "../ui/layer";

export type ScreenId =
  | "BOOT"
  | "TITLE"
  | "CHARACTER_SELECT"
  | "MODE_SELECT"
  | "TRACK_SELECT"
  | "TROPHY_STANDINGS"
  | "TROPHY_PODIUM"
  | "LOADING"
  | "LOAD_ERROR"
  | "RACING"
  | "REVIEW"
  | "PAUSED"
  | "CONFIRM"
  | "RESULTS"
  | "OPTIONS"
  | "AUDIO_SETTINGS"
  | "VIDEO_SETTINGS"
  | "CONTROLS"
  | "GENERAL_SETTINGS"
  | "MUSIC_PLAYER"
  | "CREDITS"
  | "ADVENTURE_FILES"
  | "ADVENTURE_HUB"
  | "ADVENTURE_KINGDOM"
  | "ADVENTURE_MAP"
  | "ADVENTURE_SCENE"
  | "ADVENTURE_RESULT"
  | "ADVENTURE_DEV"
  | "ADVENTURE_SCENES"
  | "OVERWORLD_LOADING"
  | "OVERWORLD"
  | "GATEWAY";

export interface Screen {
  readonly id: ScreenId;
  /** Called once when the screen becomes part of the stack. */
  enter?(): void;
  /** Called once when it leaves the stack: free everything it made. */
  exit?(): void;
  /** A screen above it was popped: it's on top again. */
  resume?(): void;
  /** Fixed-rate simulation step (the race, the title demo). `top`: nothing is over it. */
  step?(dt: number, top: boolean): void;
  /** Once per frame. Only the top screen gets actions. */
  frame(dt: number, actions: MenuAction[], top: boolean): void;
  /** Draw this screen's UI (screens below are drawn first). */
  draw(ui: UiLayer): void;
  /** Draw the 3D view, if this screen has one. Returns false to let a lower one draw. */
  render3d?(alpha: number, frameSeconds: number): boolean;
  /** Draw the screens below this one as well (pause over the race). Default: true. */
  seeThrough?: boolean;
}

const FADE_OUT = 0.16;
const FADE_IN = 0.22;

export function createScreenManager(
  ui: UiLayer,
  input: MenuInput,
  opts: { reduceMotion: () => boolean },
) {
  const stack: Screen[] = [];
  let token = 0;
  /** A pending replace: fading out, then swap, then fading in. */
  let pending: { next: () => Screen[]; t: number } | undefined;
  let fadeIn = 0;
  /** Ignore input briefly after a change, so one press can't land on two screens. */
  let cooldown = 0;

  const top = () => stack[stack.length - 1];

  function swap(next: Screen[]) {
    for (const s of stack.splice(0).reverse()) s.exit?.();
    for (const s of next) {
      stack.push(s);
      s.enter?.();
    }
    input.flush();
    cooldown = 0.12;
  }

  const mgr = {
    get token() {
      return token;
    },
    get top() {
      return top();
    },
    get stack(): readonly Screen[] {
      return stack;
    },
    get transitioning() {
      return pending !== undefined;
    },
    /** Replace every screen with `screens` (bottom first), with a quick fade. */
    go(...screens: Screen[]) {
      token++;
      const instant = opts.reduceMotion() || stack.length === 0;
      if (instant) {
        pending = undefined;
        swap(screens);
        fadeIn = stack.length ? 0 : FADE_IN;
        return;
      }
      // Asked again mid-fade: the newest request wins, the fade carries on.
      pending = { next: () => screens, t: pending?.t ?? 0 };
    },
    /** Put a screen on top (menus over the race or the title). */
    push(s: Screen) {
      stack.push(s);
      s.enter?.();
      input.flush();
      cooldown = 0.08;
    },
    /** Remove the top screen. */
    pop() {
      const s = stack.pop();
      s?.exit?.();
      top()?.resume?.();
      input.flush();
      cooldown = 0.08;
    },
    /** Fixed step: simulation for every screen that has one. */
    step(dt: number) {
      const t = top();
      for (const s of stack) s.step?.(dt, s === t && !pending);
    },
    /** Per frame: input to the top screen, animation for all, then the UI drawing. */
    frame(dt: number) {
      let actions = input.poll(dt);
      if (pending) {
        pending.t += dt;
        actions = [];
        if (pending.t >= FADE_OUT) {
          const next = pending.next();
          pending = undefined;
          swap(next);
          fadeIn = FADE_IN;
        }
      }
      if (cooldown > 0) {
        cooldown -= dt;
        actions = [];
        input.pointer.clicked = false;
      }
      const t = top();
      for (const s of [...stack]) s.frame(dt, s === t ? actions : [], s === t);
    },
    render3d(alpha: number, frameSeconds: number) {
      for (let i = stack.length - 1; i >= 0; i--)
        if (stack[i]!.render3d?.(alpha, frameSeconds)) return true;
      return false;
    },
    draw(dt: number) {
      ui.begin(dt);
      // Draw from the lowest screen that's still visible.
      let from = stack.length - 1;
      while (from > 0 && stack[from]!.seeThrough !== false) from--;
      for (let i = Math.max(0, from); i < stack.length; i++) stack[i]!.draw(ui);
      // Fade to and from black between screens.
      let a = 0;
      if (pending) a = Math.min(1, pending.t / FADE_OUT);
      else if (fadeIn > 0) {
        fadeIn = Math.max(0, fadeIn - dt);
        a = fadeIn / FADE_IN;
      }
      if (a > 0) ui.rect(0, 0, ui.W, ui.H, "#0b0710", a);
      input.endFrame();
    },
  };
  return mgr;
}

export type ScreenManager = ReturnType<typeof createScreenManager>;
