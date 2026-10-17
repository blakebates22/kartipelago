/**
 * Lightweight on-screen readout for frame timing and anything else worth watching.
 * Systems call overlay.set("speed", value) and it shows up; no wiring needed.
 */
export function createOverlay(parent: HTMLElement) {
  const el = document.createElement("pre");
  el.className = "debug-overlay";
  el.hidden = true;
  parent.appendChild(el);

  const values = new Map<string, string>();
  let frames = 0;
  let acc = 0;
  let fps = 0;

  return {
    get visible() {
      return !el.hidden;
    },
    set visible(v: boolean) {
      el.hidden = !v;
    },
    set(label: string, value: unknown) {
      const text =
        typeof value === "number" && !Number.isInteger(value) ? value.toFixed(2) : String(value);
      values.set(label, text);
    },
    frame(frameSeconds: number) {
      frames++;
      acc += frameSeconds;
      if (acc >= 0.5) {
        fps = frames / acc;
        frames = 0;
        acc = 0;
      }
      if (el.hidden) return;
      const lines = [`fps   ${fps.toFixed(0)}`, `frame ${(frameSeconds * 1000).toFixed(1)} ms`];
      for (const [k, v] of values) lines.push(`${k.padEnd(5)} ${v}`);
      el.textContent = lines.join("\n");
    },
  };
}

export type Overlay = ReturnType<typeof createOverlay>;
