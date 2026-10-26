/**
 * Shared menu pieces: a vertical button list with keyboard/gamepad/mouse focus, a
 * wooden title sign, and the hint bar along the bottom.
 */
import type { MenuAction } from "../app/menuInput";
import type { Game } from "../app/game";
import type { UiLayer } from "../ui/layer";
import { PAL } from "../ui/textures";

export interface MenuItem {
  label: string;
  sub?: string;
  disabled?: boolean;
  action: () => void;
}

/**
 * A column of buttons. Keyboard and gamepad move the focus; the mouse moves it too
 * when it moves onto a button. A click is acted on at the next frame (never in the
 * middle of drawing).
 */
export class VMenu {
  focus = 0;
  private clicked = -1;
  constructor(
    private game: Game,
    public items: MenuItem[],
    private backAction?: () => void,
  ) {
    this.focus = Math.max(
      0,
      items.findIndex((i) => !i.disabled),
    );
  }

  private moveTo(i: number) {
    if (i !== this.focus) {
      this.focus = i;
      this.game.sounds.move();
    }
  }

  private step(d: number) {
    const n = this.items.length;
    for (let k = 1; k <= n; k++) {
      const i = (this.focus + d * k + n * 4) % n;
      if (!this.items[i]!.disabled) return this.moveTo(i);
    }
  }

  /** Handle this frame's actions. Returns true if one was used. */
  handle(actions: MenuAction[]): boolean {
    let used = false;
    if (this.clicked >= 0) {
      const it = this.items[this.clicked];
      this.clicked = -1;
      if (it && !it.disabled) {
        this.game.sounds.confirm();
        it.action();
        return true;
      }
    }
    for (const a of actions) {
      if (a === "up") this.step(-1);
      else if (a === "down") this.step(1);
      else if (a === "confirm") {
        const it = this.items[this.focus];
        if (it && !it.disabled) {
          this.game.sounds.confirm();
          it.action();
        } else this.game.sounds.error();
      } else if (a === "back" && this.backAction) {
        this.game.sounds.back();
        this.backAction();
      } else continue;
      used = true;
    }
    return used;
  }

  /** The first row shown, when only `rows` of them fit (the list scrolls to the focus). */
  top = 0;

  draw(ui: UiLayer, x: number, y: number, w: number, h: number, gap = 4, scale = 1, rows?: number) {
    if (rows !== undefined) {
      this.top = Math.min(Math.max(this.top, this.focus - rows + 1), this.focus);
      this.top = Math.max(0, Math.min(this.top, this.items.length - rows));
    }
    this.items.forEach((it, i) => {
      if (rows !== undefined && (i < this.top || i >= this.top + rows)) return;
      const by = y + (i - (rows !== undefined ? this.top : 0)) * (h + gap);
      const r = ui.button(x, by, w, h, it.label, {
        focused: i === this.focus,
        disabled: it.disabled,
        sub: it.sub,
        scale,
      });
      if (r.hover && this.game.menuInput.pointer.moved) this.moveTo(i);
      if (r.clicked) this.clicked = i;
    });
  }
}

/** A wooden sign with a title, top centre. */
export function titleSign(ui: UiLayer, text: string, y = 8, scale = 2) {
  const w = ui.textWidth(text) * scale + 28;
  const x = Math.round(ui.W / 2 - w / 2);
  // Two posts.
  ui.rect(x + 10, y + 7 * scale + 10, 4, 6, "#5a3318");
  ui.rect(x + w - 14, y + 7 * scale + 10, 4, 6, "#5a3318");
  ui.panel(x, y, w, 7 * scale + 12, "wood", "gold");
  ui.text(text, ui.W / 2, y + 6, { scale, color: PAL.gold, outline: PAL.shadow, align: "center" });
}

/** Button hints along the bottom: [key, meaning] pairs. */
export function hints(ui: UiLayer, list: [string, string][]) {
  const parts = list.map(([k, v]) => `${k} ${v}`);
  const text = parts.join("   ");
  ui.rect(0, ui.H - 12, ui.W, 12, "#1a1210");
  ui.rect(0, ui.H - 12, ui.W, 1, "#3a2a1e");
  ui.text(text, ui.W / 2, ui.H - 10, { color: "#e8d5b0", align: "center" });
}

export const CONFIRM_HINT: [string, string] = ["ENTER", "SELECT"];
export const BACK_HINT: [string, string] = ["ESC", "BACK"];
