/**
 * Painted backgrounds and the logo, drawn in code at the UI's low resolution:
 *
 * - a sunny island landscape (sky bands, drifting clouds, three rows of hills, palms
 *   and a smoking volcano) behind the mode and loading screens;
 * - a treasure-map style island for Adventure's "Coming soon" page;
 * - the KARTIPELAGO logo: chunky outlined letters in the accent colours, bouncing in.
 *
 * All original artwork.
 */
import { drawText, textWidth } from "./font";
import { ACCENTS, PAL } from "./textures";

type G = CanvasRenderingContext2D;

const SKY = ["#4aa7e8", "#62b6ee", "#7cc5f2", "#98d3f5", "#b6e1f7", "#d3edf8"];

function hill(
  g: G,
  W: number,
  base: number,
  amp: number,
  freq: number,
  phase: number,
  color: string,
  H: number,
) {
  g.fillStyle = color;
  for (let x = 0; x < W; x++) {
    const y =
      base -
      amp * (0.6 * Math.sin(x * freq + phase) + 0.4 * Math.sin(x * freq * 2.3 + phase * 1.7));
    g.fillRect(x, Math.round(y), 1, H - Math.round(y));
  }
}

function palm(g: G, x: number, y: number, s: number, trunk: string, leaf: string) {
  g.fillStyle = trunk;
  for (let i = 0; i < 14 * s; i++)
    g.fillRect(Math.round(x + Math.sin(i / 6) * 2), Math.round(y - i), 2, 1);
  const top = y - 14 * s;
  g.fillStyle = leaf;
  for (const [dx, dy] of [
    [-7, 2],
    [7, 2],
    [-5, -2],
    [5, -2],
    [0, -4],
  ] as const) {
    for (let k = 0; k <= 6; k++) {
      const t = k / 6;
      g.fillRect(
        Math.round(x + 1 + dx * t * s),
        Math.round(top + dy * t * s + 3 * t * t * s),
        2,
        1,
      );
    }
  }
}

function cloud(g: G, x: number, y: number, w: number) {
  g.fillStyle = "#ffffff";
  g.fillRect(x, y + 3, w, 4);
  g.fillRect(x + 3, y, w * 0.45, 4);
  g.fillRect(x + w * 0.4, y - 2, w * 0.35, 5);
  g.fillStyle = "#dceff8";
  g.fillRect(x, y + 6, w, 1);
}

/** The island landscape. `t` (seconds) drifts the clouds and the volcano's smoke. */
export function landscape(g: G, W: number, H: number, t: number, calm = false) {
  const band = Math.ceil((H * 0.62) / SKY.length);
  SKY.forEach((c, i) => {
    g.fillStyle = c;
    g.fillRect(0, i * band, W, band + 1);
  });
  // Sun.
  g.fillStyle = "#fff6c2";
  g.fillRect(W - 70, 22, 18, 18);
  g.fillRect(W - 72, 26, 22, 10);
  g.fillRect(W - 66, 20, 10, 22);
  const drift = calm ? 0 : t * 4;
  for (let i = 0; i < 5; i++) {
    const w = 26 + (i % 3) * 10;
    const x = ((i * 97 + drift * (0.6 + i * 0.15)) % (W + 80)) - 40;
    cloud(g, Math.round(x), 18 + ((i * 23) % 50), w);
  }
  // Volcano with smoke.
  const vx = Math.round(W * 0.72);
  g.fillStyle = "#7d6a8a";
  for (let y = 0; y < 60; y++) g.fillRect(vx - 8 - y, 104 + y, 16 + 2 * y, 1);
  g.fillStyle = "#e85d3a";
  g.fillRect(vx - 6, 104, 12, 2);
  g.fillStyle = "#cfc6d6";
  for (let i = 0; i < 4; i++) {
    const k = (t * 0.25 + i / 4) % 1;
    const r = 3 + k * 6;
    g.globalAlpha = 1 - k;
    g.fillRect(
      Math.round(vx - r + Math.sin(k * 6 + i) * 4),
      Math.round(100 - k * 46),
      Math.round(r * 2),
      Math.round(r),
    );
  }
  g.globalAlpha = 1;
  hill(g, W, H * 0.66, 10, 0.021, 0.5, "#5aa64a", H);
  hill(g, W, H * 0.76, 9, 0.03, 2.1, "#47923c", H);
  palm(g, Math.round(W * 0.18), Math.round(H * 0.74), 1.4, "#7a4f2a", "#2f7a32");
  palm(g, Math.round(W * 0.86), Math.round(H * 0.8), 1.2, "#7a4f2a", "#2f7a32");
  hill(g, W, H * 0.88, 6, 0.045, 4.2, "#3a7d34", H);
  // Sea glints along the bottom.
  g.fillStyle = "#2f9ad8";
  g.fillRect(0, H - 14, W, 14);
  g.fillStyle = "#8fd3f5";
  for (let i = 0; i < 18; i++) {
    const x = ((i * 53 + (calm ? 0 : t * 10)) % (W + 20)) - 10;
    g.fillRect(Math.round(x), H - 10 + (i % 3) * 3, 6, 1);
  }
}

let mapCache: { w: number; h: number; c: HTMLCanvasElement } | undefined;

/** A treasure-map island, for Adventure's "Coming soon". */
export function treasureMap(g: G, x0: number, y0: number, w: number, h: number, t: number) {
  if (!mapCache || mapCache.w !== w || mapCache.h !== h) {
    const c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    islandArt(c.getContext("2d")!, 0, 0, w, h);
    mapCache = { w, h, c };
  }
  g.drawImage(mapCache.c, x0, y0);
  const cx = x0 + w / 2;
  const cy = y0 + h / 2 + 4;
  const rx = w * 0.36;
  const ry = h * 0.34;
  // A dotted route to an X, drawing itself.
  const path: [number, number][] = [];
  for (let k = 0; k <= 40; k++) {
    const s = k / 40;
    path.push([
      cx - rx * 0.7 + s * rx * 1.2,
      cy + ry * 0.55 - Math.sin(s * Math.PI) * ry * 0.9 + s * ry * 0.2,
    ]);
  }
  const shown = Math.floor(((t * 0.6) % 1.4) * path.length);
  g.fillStyle = PAL.coral;
  path.forEach(([px, py], i) => {
    if (i % 3 === 0 && i <= shown) g.fillRect(Math.round(px), Math.round(py), 2, 2);
  });
  const [ex, ey] = path[path.length - 1]!;
  drawText(g, "×", ex - 2, ey - 3, { color: PAL.coral, outline: PAL.ink });
}

function islandArt(g: G, x0: number, y0: number, w: number, h: number) {
  // Sea hatching.
  g.fillStyle = "#c9b27c";
  for (let y = y0 + 4; y < y0 + h; y += 6)
    for (let x = x0 + ((y / 6) % 2) * 6; x < x0 + w; x += 12) g.fillRect(x, y, 4, 1);
  // The island: a blobby outline, filled.
  const cx = x0 + w / 2;
  const cy = y0 + h / 2 + 4;
  const rx = w * 0.36;
  const ry = h * 0.34;
  const r = (a: number) => 1 + 0.16 * Math.sin(a * 3 + 1) + 0.09 * Math.sin(a * 7 + 2);
  for (let y = Math.floor(cy - ry * 1.4); y < cy + ry * 1.4; y++)
    for (let x = Math.floor(cx - rx * 1.4); x < cx + rx * 1.4; x++) {
      const dx = (x - cx) / rx;
      const dy = (y - cy) / ry;
      const d = Math.hypot(dx, dy);
      const a = Math.atan2(dy, dx);
      const edge = r(a);
      if (d < edge - 0.08) {
        g.fillStyle = d < edge * 0.55 ? "#9fc46b" : "#b9d486";
        g.fillRect(x, y, 1, 1);
      } else if (d < edge) {
        g.fillStyle = PAL.inkSoft;
        g.fillRect(x, y, 1, 1);
      }
    }
  // Mountains, palms, a lagoon.
  for (const [mx, my] of [
    [-0.25, -0.2],
    [-0.05, -0.32],
    [0.18, -0.18],
  ] as const) {
    const px = Math.round(cx + mx * rx * 2);
    const py = Math.round(cy + my * ry * 2);
    g.fillStyle = PAL.inkSoft;
    for (let i = 0; i < 9; i++) g.fillRect(px - i, py + i, 2 * i + 1, 1);
    g.fillStyle = "#f4e4bc";
    g.fillRect(px - 1, py + 1, 3, 1);
  }
  g.fillStyle = "#7cc0d8";
  g.fillRect(Math.round(cx + rx * 0.35), Math.round(cy + ry * 0.2), 14, 6);
  g.fillRect(Math.round(cx + rx * 0.35) + 2, Math.round(cy + ry * 0.2) - 1, 10, 8);
  // A compass rose.
  const kx = x0 + w - 26;
  const ky = y0 + 22;
  g.fillStyle = PAL.inkSoft;
  g.fillRect(kx, ky - 10, 1, 21);
  g.fillRect(kx - 10, ky, 21, 1);
  drawText(g, "N", kx - 2, ky - 19, { color: PAL.ink });
}

const LOGO = "KARTIPELAGO";

/**
 * The logo, letters dropping in one after another with a bounce, then bobbing gently.
 * `t` = seconds since it started; `calm` skips the motion.
 */
export function logo(g: G, cx: number, y: number, t: number, scale = 3, calm = false) {
  const gap = 1;
  const widths = [...LOGO].map((c) => textWidth(c) * scale);
  const total = widths.reduce((a, b) => a + b, 0) + gap * scale * (LOGO.length - 1);
  let x = Math.round(cx - total / 2);
  [...LOGO].forEach((ch, i) => {
    const start = i * 0.07;
    let dy = 0;
    if (!calm) {
      const k = Math.max(0, t - start);
      if (k < 0.5) {
        // Falls in, bounces twice.
        const p = k / 0.5;
        dy = -Math.abs(Math.cos(p * Math.PI * 1.5)) * (1 - p) * 60 - (k === 0 ? 200 : 0);
      } else dy = Math.sin(t * 2.4 + i * 0.6) * 1.5;
      if (t < start) dy = -300;
    }
    const color = ACCENTS[i % ACCENTS.length]!;
    drawText(g, ch, x, Math.round(y + dy), { color, scale, outline: PAL.shadow });
    // A bright top edge on each letter: the "painted plastic" shine.
    g.save();
    g.beginPath();
    g.rect(x - 1, Math.round(y + dy), widths[i]! + 2, scale);
    g.clip();
    g.globalAlpha = 0.55;
    drawText(g, ch, x, Math.round(y + dy), { color: "#ffffff", scale });
    g.restore();
    x += widths[i]! + gap * scale;
  });
  return total;
}

/** A tyre rolling along (the loading screen). */
export function rollingTyre(g: G, x: number, y: number, t: number) {
  const r = 9;
  g.fillStyle = PAL.shadow;
  g.fillRect(x - r, y + r + 1, r * 2, 2);
  for (let a = 0; a < Math.PI * 2; a += 0.05) {
    const px = Math.round(x + Math.cos(a) * r);
    const py = Math.round(y + Math.sin(a) * r);
    g.fillStyle = "#2b2b2b";
    g.fillRect(px, py, 2, 2);
  }
  g.fillStyle = "#3b3b3b";
  for (let rr = 2; rr < r - 1; rr++)
    for (let a = 0; a < Math.PI * 2; a += 0.12)
      g.fillRect(Math.round(x + Math.cos(a) * rr), Math.round(y + Math.sin(a) * rr), 1, 1);
  g.fillStyle = PAL.gold;
  for (let k = 0; k < 5; k++) {
    const a = t * 8 + (k * Math.PI * 2) / 5;
    for (let rr = 1; rr < 5; rr++)
      g.fillRect(Math.round(x + Math.cos(a) * rr), Math.round(y + Math.sin(a) * rr), 1, 1);
  }
  g.fillStyle = "#d8d8d8";
  g.fillRect(x - 1, y - 1, 3, 3);
}
