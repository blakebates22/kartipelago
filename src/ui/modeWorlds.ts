/**
 * The other worlds in the "Choose a mode" vista (see modeArt.ts), so all four can be seen
 * from the terrace: Frostveil's snowy peaks, the Desert's red-rock canyon with a natural
 * arch, the Dragon Kingdom's jade cliffs (or a floating island with a pagoda).
 *
 * Arrangements (prototypes, ?vista=1|2|3):
 *   1  peaks on the horizon: a snowy range behind the sea in the middle; the canyon on
 *      the right with the pagodas on its high terraces.
 *   2  side by side: a snow peak beside the volcano on the left; on the right the red
 *      canyon and its arch, then jade cliffs with the pagodas.
 *   3  four corners: volcano left, snowy range behind the sea, canyon and arch right, a
 *      floating Dragon Kingdom island high in the sky.
 *
 * All original artwork.
 */
type G = CanvasRenderingContext2D;

export type VistaLayout = 0 | 1 | 2 | 3;

/** The arrangement to show (0: the original, before all four worlds were in it). */
export function vistaLayout(): VistaLayout {
  const v =
    typeof location !== "undefined" ? new URLSearchParams(location.search).get("vista") : null;
  return v === "1" || v === "2" || v === "3" ? (Number(v) as VistaLayout) : 0;
}

function hash(x: number, y: number, s = 0) {
  const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453;
  return v - Math.floor(v);
}

const px = (g: G, x: number, y: number, w: number, h: number, c: string) => {
  g.fillStyle = c;
  g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};

/**
 * One snowy peak: shaded rock (lit side and shadow side) under a jagged snow cap that
 * runs down the gullies. `base` is where it meets the horizon.
 */
export function snowPeak(
  g: G,
  cx: number,
  base: number,
  halfW: number,
  height: number,
  seed: number,
) {
  const top = base - height;
  for (let x = Math.floor(cx - halfW); x <= cx + halfW; x++) {
    const d = Math.abs(x - cx) / halfW;
    const jag = (hash(x, seed) - 0.5) * 2 + Math.sin(x * 0.7 + seed) * 1.5;
    const y = Math.round(top + d * height * (0.85 + d * 0.15) + jag);
    if (y >= base) continue;
    const lit = x < cx;
    px(g, x, y, 1, base - y, lit ? "#8a96b8" : "#68749a");
    // The snow: deep at the top, fingers running down the gullies.
    const snow = height * (0.38 - d * 0.18) + Math.sin(x * 0.9 + seed) * 5 + hash(x, seed, 3) * 4;
    if (snow > 0) px(g, x, y, 1, snow, lit ? "#ffffff" : "#d4def0");
  }
}

/** A snowy range: a big peak and its shoulders. */
export function snowRange(g: G, cx: number, base: number, scale: number) {
  snowPeak(g, cx - 46 * scale, base, 30 * scale, 34 * scale, 3);
  snowPeak(g, cx + 44 * scale, base, 34 * scale, 40 * scale, 5);
  snowPeak(g, cx, base, 42 * scale, 62 * scale, 7);
}

/** A natural arch of red rock: two legs and a span, banded with strata. */
export function naturalArch(g: G, x: number, base: number, w: number, h: number) {
  const leg = Math.max(5, Math.round(w * 0.2));
  const span = Math.max(5, Math.round(h * 0.22));
  const top = base - h;
  const rock = (x0: number, y0: number, ww: number, hh: number) => {
    for (let yy = 0; yy < hh; yy++) {
      const col = (y0 + yy) % 7 < 2 ? "#a3552f" : (y0 + yy) % 7 < 5 ? "#c06c42" : "#b4613a";
      px(g, x0, y0 + yy, ww, 1, col);
    }
    px(g, x0, y0, ww, 1, "#e09468");
  };
  rock(x, top + span - 2, leg, h - span + 2);
  rock(x + w - leg, top + span, leg, h - span);
  // The span, thinner in the middle, sagging a touch.
  for (let k = 0; k < w; k++) {
    const u = k / (w - 1);
    const sag = Math.sin(u * Math.PI) * 2;
    const thick = span - Math.sin(u * Math.PI) * span * 0.35;
    rock(x + k, top + sag, 1, thick);
  }
  // The sky seen through it is the land behind: just a shadow under the span.
  px(g, x + leg, top + span, w - leg * 2, 1, "#8a4026");
}

/** A floating island of the Dragon Kingdom: jade turf, a hanging rock root, a pagoda. */
export function floatingIsland(
  g: G,
  cx: number,
  cy: number,
  r: number,
  pagoda: (g: G, x: number, y: number, s: number) => void,
) {
  // The rock underneath, tapering to a point, with roots and a waterfall.
  for (let y = 0; y < r * 1.4; y++) {
    const hw = r * (1 - y / (r * 1.4)) ** 0.8;
    px(g, cx - hw, cy + y, hw * 2, 1, y % 4 < 2 ? "#7a6a5a" : "#6a5a4c");
  }
  for (let k = 0; k < 3; k++)
    for (let y = 0; y < 8 + k * 3; y++)
      px(g, cx - r * 0.5 + k * r * 0.5, cy + r * 0.4 + y, 1, 1, "#4f8a3a");
  px(g, cx + r * 0.55, cy + 2, 2, r * 1.6, "#bfe6f7");
  // Jade turf on top.
  for (let x = -r; x <= r; x++) {
    const hgt = 3 + Math.round(Math.sin(x * 0.4) * 1);
    px(g, cx + x, cy - hgt, 1, hgt + 1, Math.abs(x) % 5 < 3 ? "#5aa874" : "#4f9a68");
  }
  // Blossom trees and the pagoda.
  for (const tx of [-r * 0.7, r * 0.75]) {
    px(g, cx + tx, cy - 7, 1, 4, "#5a3a22");
    px(g, cx + tx - 3, cy - 11, 7, 4, "#f2a0c0");
    px(g, cx + tx - 2, cy - 12, 5, 1, "#f8c0d8");
  }
  pagoda(g, cx - 2, cy - 2, 0.85);
}

/** Recolour part of the canyon wall as jade cliffs (the Dragon Kingdom's), with strata. */
export function jadeCliff(
  g: G,
  x0: number,
  x1: number,
  top: (x: number) => number,
  bottom: number,
) {
  for (let x = Math.floor(x0); x < x1; x++) {
    const y = Math.round(top(x));
    px(g, x, y, 1, bottom - y, "#4f8a72");
    px(g, x, y, 1, 2, "#8fd0a8");
    for (let k = 1; k < 9; k++)
      px(
        g,
        x,
        y + k * 9 + Math.round(Math.sin(x * 0.05 + k) * 1.5),
        1,
        2,
        k % 2 ? "#3e7460" : "#5a9a80",
      );
    if (hash(x, 5) < 0.3) px(g, x, y + 2, 1, 4 + hash(x, 6) * 10, "#3d7a32");
  }
}
