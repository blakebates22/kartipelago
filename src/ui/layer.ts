/**
 * The UI layer: one canvas over the 3D view, drawn at a low logical resolution (240
 * lines; 320 wide at 4:3, up to 480 for widescreen) and scaled up to the window, so
 * menus and HUD share one chunky, pixel-aware look.
 *
 * Drawing is immediate-mode: each frame, screens draw their panels, text and buttons.
 * `button()` also does the mouse: it reports hover and click, and screens move their
 * keyboard focus to whatever the mouse moves onto, so the two never disagree.
 */
import type { MenuInput } from "../app/menuInput";
import { drawText, textWidth, type TextStyle } from "./font";
import { focusRing, panel, PAL, type FillKind, type FrameKind } from "./textures";

export const UI_H = 240;
export const SAFE_W = 320;

export interface ButtonOpts {
  focused?: boolean;
  disabled?: boolean;
  fill?: FillKind;
  frame?: FrameKind;
  color?: string;
  outline?: string;
  scale?: number;
  /** Small text under the label. */
  sub?: string;
}

export function createUiLayer(parent: HTMLElement, input: MenuInput) {
  const canvas = document.createElement("canvas");
  canvas.className = "ui-layer";
  parent.appendChild(canvas);
  const g = canvas.getContext("2d")!;
  let W = SAFE_W;
  let scale = 1;
  let time = 0;

  const resize = () => {
    const cw = parent.clientWidth || window.innerWidth;
    const ch = parent.clientHeight || window.innerHeight;
    W = Math.max(SAFE_W, Math.min(480, Math.round((UI_H * cw) / Math.max(1, ch))));
    // Draw at a whole multiple of the logical size, then let the browser smooth the rest.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    scale = Math.max(1, Math.floor((ch * dpr) / UI_H));
    canvas.width = W * scale;
    canvas.height = UI_H * scale;
  };
  resize();
  window.addEventListener("resize", resize);

  // Mouse, in logical coordinates.
  const toLogical = (e: PointerEvent | WheelEvent) => {
    const r = canvas.getBoundingClientRect();
    input.pointer.x = ((e.clientX - r.left) / Math.max(1, r.width)) * W;
    input.pointer.y = ((e.clientY - r.top) / Math.max(1, r.height)) * UI_H;
  };
  canvas.addEventListener("pointermove", (e) => {
    toLogical(e);
    input.pointer.moved = true;
    input.pointer.inside = true;
  });
  canvas.addEventListener("pointerleave", () => (input.pointer.inside = false));
  canvas.addEventListener("pointerdown", (e) => {
    toLogical(e);
    input.pointer.clicked = true;
    input.pointer.inside = true;
  });
  canvas.addEventListener(
    "wheel",
    (e) => {
      toLogical(e);
      input.pointer.wheel += Math.sign(e.deltaY);
      e.preventDefault();
    },
    { passive: false },
  );
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());

  const hit = (x: number, y: number, w: number, h: number) => {
    const p = input.pointer;
    return p.inside && p.x >= x && p.x < x + w && p.y >= y && p.y < y + h;
  };

  const ui = {
    g,
    canvas,
    get W() {
      return W;
    },
    H: UI_H,
    /** Left edge of the centred 4:3 safe area. */
    get safeX() {
      return Math.floor((W - SAFE_W) / 2);
    },
    get time() {
      return time;
    },
    begin(dt: number) {
      time += dt;
      g.setTransform(scale, 0, 0, scale, 0, 0);
      g.imageSmoothingEnabled = false;
      g.clearRect(0, 0, W, UI_H);
      g.globalAlpha = 1;
    },
    /** Hide the layer's pointer events (the race doesn't need the mouse). */
    set interactive(on: boolean) {
      canvas.style.pointerEvents = on ? "auto" : "none";
      canvas.style.cursor = on ? "pointer" : "none";
    },
    text(t: string, x: number, y: number, s?: TextStyle) {
      return drawText(g, t, x, y, s);
    },
    textWidth,
    panel(
      x: number,
      y: number,
      w: number,
      h: number,
      fill: FillKind = "wood",
      frame: FrameKind = "gold",
    ) {
      panel(g, x, y, w, h, fill, frame);
    },
    rect(x: number, y: number, w: number, h: number, color: string, alpha = 1) {
      g.globalAlpha = alpha;
      g.fillStyle = color;
      g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
      g.globalAlpha = 1;
    },
    /** Darken everything drawn so far (under pause menus and dialogs). */
    dim(alpha = 0.5) {
      ui.rect(0, 0, W, UI_H, "#0b0710", alpha);
    },
    hover: hit,
    /**
     * A button. Returns whether the mouse is over it (`hover`) and was clicked on it
     * this frame (`clicked`).
     */
    button(x: number, y: number, w: number, h: number, label: string, o: ButtonOpts = {}) {
      const over = !o.disabled && hit(x, y, w, h);
      const press = o.focused ? Math.round(Math.sin(time * 9) * 0.6) : 0;
      ui.panel(x, y, w, h, o.fill ?? "wood", o.focused ? "gold" : (o.frame ?? "dark"));
      if (o.focused) focusRing(g, x, y, w, h, time);
      const scale = o.scale ?? 1;
      const color = o.disabled ? "#9a8a78" : (o.color ?? (o.focused ? PAL.gold : PAL.cream));
      const ty = y + Math.floor((h - 7 * scale) / 2) - (o.sub ? 4 : 0) + press;
      drawText(g, label, x + w / 2, ty, {
        color,
        align: "center",
        scale,
        outline: o.outline ?? PAL.shadow,
      });
      if (o.sub)
        drawText(g, o.sub, x + w / 2, ty + 7 * scale + 3, {
          color: o.disabled ? "#8a7a68" : "#e8d5b0",
          align: "center",
          shadow: PAL.shadow,
        });
      if (o.focused) {
        // A little pointing arrow that bobs.
        const bob = Math.round(Math.sin(time * 6) * 1.5);
        drawText(g, "▶", x - 8 + bob, y + Math.floor((h - 7) / 2), {
          color: PAL.gold,
          outline: PAL.shadow,
        });
      }
      return { hover: over, clicked: over && input.pointer.clicked };
    },
    image(img: CanvasImageSource, x: number, y: number, w: number, h: number, smooth = true) {
      g.imageSmoothingEnabled = smooth;
      g.drawImage(img, Math.round(x), Math.round(y), Math.round(w), Math.round(h));
      g.imageSmoothingEnabled = false;
    },
    /** A left/right value picker: "◀ VALUE ▶". Returns -1/0/1 clicks on the arrows. */
    arrows(x: number, y: number, w: number, value: string, focused: boolean) {
      const color = focused ? PAL.gold : PAL.cream;
      drawText(g, value, x + w / 2, y, { color, align: "center", outline: PAL.shadow });
      drawText(g, "◀", x, y, { color, outline: PAL.shadow });
      drawText(g, "▶", x + w - 4, y, { color, outline: PAL.shadow });
      if (input.pointer.clicked) {
        if (hit(x - 4, y - 3, 12, 13)) return -1;
        if (hit(x + w - 8, y - 3, 12, 13)) return 1;
      }
      return 0;
    },
    /** A slider bar for 0..1. Returns a new value if dragged/clicked. */
    slider(x: number, y: number, w: number, value: number, focused: boolean): number | undefined {
      ui.rect(x, y + 2, w, 4, PAL.shadow);
      ui.rect(x + 1, y + 3, Math.max(0, (w - 2) * value), 2, focused ? PAL.gold : PAL.leaf);
      const kx = x + (w - 4) * value;
      ui.rect(kx - 1, y - 1, 6, 10, PAL.shadow);
      ui.rect(kx, y, 4, 8, focused ? "#fff3c4" : PAL.cream);
      if (input.pointer.clicked && hit(x - 3, y - 3, w + 6, 14))
        return Math.max(0, Math.min(1, (input.pointer.x - x) / w));
      return undefined;
    },
    resize,
  };
  return ui;
}

export type UiLayer = ReturnType<typeof createUiLayer>;
