import { createOverlay } from "./overlay";
import { createTuningPanel } from "./tuningPanel";

/**
 * Debug tools. Toggle with the backtick (`) key, or open the page with ?debug
 * to start with them visible.
 */
export function createDebug(parent: HTMLElement) {
  const overlay = createOverlay(parent);
  const panel = createTuningPanel();

  const setVisible = (v: boolean) => {
    overlay.visible = v;
    panel.show(v);
  };

  window.addEventListener("keydown", (e) => {
    if (e.code === "Backquote") setVisible(!overlay.visible);
  });

  if (new URLSearchParams(location.search).has("debug")) setVisible(true);

  return { overlay, panel };
}
