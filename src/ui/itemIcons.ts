/**
 * Pixel icons for the balloon power-ups: one for every colour and level (15 in all),
 * shown in the race HUD's item box.
 *
 * Each is drawn with simple shapes at 3x, shrunk to 20x20, snapped to a few colours and
 * outlined in a dark line one pixel wide: the same pixel-art look as the select screen's
 * sprites. Built once and kept (they never change).
 *
 *   red      1 missile           2 homing missile (a target lock)   3 a pack of missiles
 *   blue     1-3 boost flames, bigger and hotter, with 1-3 chevrons
 *   green    1 oil slick         2 mine                             3 bubble trap
 *   yellow   1-3 shields, with 1-3 rank chevrons
 *   rainbow  1 grappling arm     2 long-reach grapple               3 reverse grapple
 */
import type { BalloonColor } from "../items/inventory";

export const ICON = 20;
const SS = 3;
const OUTLINE: [number, number, number] = [29, 18, 10];

/** The balloon colours, for the item box's frame. */
export const BALLOON_HUES: Record<BalloonColor, { light: string; dark: string }> = {
  red: { light: "#ff6a4a", dark: "#a8241c" },
  blue: { light: "#5ab4ff", dark: "#1f56b8" },
  green: { light: "#6ade5a", dark: "#1f8a32" },
  yellow: { light: "#ffd84a", dark: "#c08a14" },
  rainbow: { light: "#e86ae0", dark: "#6a3ab8" },
};

type G = CanvasRenderingContext2D;

function poly(g: G, color: string, pts: [number, number][]) {
  g.fillStyle = color;
  g.beginPath();
  g.moveTo(pts[0]![0], pts[0]![1]);
  for (const [x, y] of pts.slice(1)) g.lineTo(x, y);
  g.closePath();
  g.fill();
}
function disc(g: G, color: string, x: number, y: number, rx: number, ry = rx) {
  g.fillStyle = color;
  g.beginPath();
  g.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
  g.fill();
}
function ring(
  g: G,
  color: string,
  x: number,
  y: number,
  r: number,
  w: number,
  a0 = 0,
  a1 = Math.PI * 2,
) {
  g.strokeStyle = color;
  g.lineWidth = w;
  g.beginPath();
  g.arc(x, y, r, a0, a1);
  g.stroke();
}
// All shapes below are in icon pixels (0..20); the canvas is scaled by SS.

/** A missile pointing right, centred on (x, y), `s` its scale. */
function missile(g: G, x: number, y: number, s: number, nose = "#f2f2f6") {
  g.save();
  g.translate(x, y);
  g.scale(s, s);
  // Flame out of the back.
  poly(g, "#ffb02a", [
    [-8.5, 0],
    [-5, -1.8],
    [-5, 1.8],
  ]);
  poly(g, "#fff06a", [
    [-7, 0],
    [-5, -0.9],
    [-5, 0.9],
  ]);
  // Fins.
  poly(g, "#a8241c", [
    [-5, -1.6],
    [-2, -1.6],
    [-4.5, -4.2],
    [-6, -4.2],
  ]);
  poly(g, "#a8241c", [
    [-5, 1.6],
    [-2, 1.6],
    [-4.5, 4.2],
    [-6, 4.2],
  ]);
  // Body, a light stripe along the top, and the nose.
  g.fillStyle = "#e8402a";
  g.fillRect(-5.2, -2, 9, 4);
  g.fillStyle = "#ff8a6a";
  g.fillRect(-4.6, -1.8, 8, 1);
  poly(g, nose, [
    [3.8, -2],
    [7.6, 0],
    [3.8, 2],
  ]);
  g.restore();
}

function flame(g: G, level: number) {
  const k = 0.72 + level * 0.1;
  const cx = 12;
  const by = 17.5;
  const outer = level === 3 ? "#8a5af0" : "#2f7ae8";
  poly(g, outer, [
    [cx, by - 15.5 * k],
    [cx + 6 * k, by - 6 * k],
    [cx + 5 * k, by - 1],
    [cx, by + 0.5],
    [cx - 5 * k, by - 1],
    [cx - 6 * k, by - 6 * k],
  ]);
  poly(g, "#5ab4ff", [
    [cx, by - 11 * k],
    [cx + 3.8 * k, by - 4.5 * k],
    [cx + 3 * k, by - 0.5],
    [cx, by],
    [cx - 3 * k, by - 0.5],
    [cx - 3.8 * k, by - 4.5 * k],
  ]);
  disc(g, "#e8f8ff", cx, by - 3 * k, 2 * k, 3 * k);
  // Speed chevrons up the left side, one per level.
  for (let i = 0; i < level; i++) {
    const y = 16.5 - i * 5;
    poly(g, "#ffffff", [
      [1.5, y + 1],
      [4, y - 1.6],
      [6.5, y + 1],
      [6.5, y + 3.4],
      [4, y + 0.8],
      [1.5, y + 3.4],
    ]);
  }
}

function shield(g: G, level: number) {
  const pts: [number, number][] = [
    [10, 1.5],
    [17.5, 4],
    [17, 11],
    [10, 18.5],
    [3, 11],
    [2.5, 4],
  ];
  poly(g, "#ffffff", pts);
  poly(
    g,
    "#ffc42a",
    pts.map(([x, y]) => [10 + (x - 10) * 0.8, 9.5 + (y - 9.5) * 0.8]),
  );
  // Rank chevrons down the shield, one per level.
  for (let i = 0; i < level; i++) {
    const y = (level === 3 ? 4.6 : level === 2 ? 6 : 8) + i * 3.6;
    poly(g, "#e85a14", [
      [5, y],
      [10, y + 3],
      [15, y],
      [15, y + 2],
      [10, y + 5],
      [5, y + 2],
    ]);
  }
}

/** A grappling arm: a segmented steel arm with brass joints, a three-fingered claw. */
function grapple(g: G, level: number) {
  const joints: [number, number][] =
    level === 2
      ? [
          [1.5, 18],
          [4, 15],
          [5, 11],
          [8, 8.5],
          [11.5, 7.5],
          [14, 5],
        ]
      : [
          [3, 18],
          [5.5, 15],
          [7, 11.5],
          [10, 9],
          [13, 7],
        ];
  // The arm: steel links between brass joints.
  for (let k = 0; k < joints.length - 1; k++) {
    const [x0, y0] = joints[k]!;
    const [x1, y1] = joints[k + 1]!;
    const n = 6;
    for (let s = 0; s <= n; s++)
      disc(g, "#6a7080", x0 + ((x1 - x0) * s) / n, y0 + ((y1 - y0) * s) / n, 1.5);
  }
  for (const [x, y] of joints) disc(g, "#c8962a", x, y, 1.5);
  // The claw at the end: a hub with a red eye and three fingers.
  const [cx, cy] = joints[joints.length - 1]!;
  const open = level === 3 ? 0.45 : 0.75;
  for (const a of [-open - 0.75, -0.75, open - 0.75]) {
    // A hooked finger: out along the arm, then curling in at the tip.
    poly(g, "#d8d8e0", [
      [cx + Math.cos(a - 0.5) * 1.4, cy + Math.sin(a - 0.5) * 1.4],
      [cx + Math.cos(a - 0.12) * 6.2, cy + Math.sin(a - 0.12) * 6.2],
      [cx + Math.cos(a + 0.25) * 6.6, cy + Math.sin(a + 0.25) * 6.6],
      [cx + Math.cos(a + 0.5) * 1.4, cy + Math.sin(a + 0.5) * 1.4],
    ]);
  }
  disc(g, "#c8962a", cx, cy, 1.8);
  disc(g, "#ff2a2a", cx, cy, 0.8);
  if (level === 2)
    // Long reach: motion marks along the arm.
    for (const [x, y] of [
      [13, 15],
      [16, 12],
    ] as const) {
      g.fillStyle = "#ffffff";
      g.fillRect(x, y, 3, 1.2);
    }
  if (level === 3) {
    // Reverse: an arrow curling back down toward you.
    ring(g, "#ff6ae8", 10, 13, 5.4, 1.6, Math.PI * 0.05, Math.PI * 0.9);
    poly(g, "#ff6ae8", [
      [2.4, 11],
      [6.2, 12.2],
      [3.4, 15],
    ]);
  }
}

function draw(g: G, color: BalloonColor, level: number) {
  switch (color) {
    case "red":
      if (level === 1) missile(g, 10, 10, 1.15);
      else if (level === 2) {
        // Homing: a target lock round a missile with a glowing seeker nose.
        ring(g, "#ffd84a", 10, 10, 8, 1.3);
        g.fillStyle = "#ffd84a";
        for (const [x, y, w, h] of [
          [9.3, 0.5, 1.4, 3.5],
          [9.3, 16, 1.4, 3.5],
          [0.5, 9.3, 3.5, 1.4],
          [16, 9.3, 3.5, 1.4],
        ] as const)
          g.fillRect(x, y, w, h);
        missile(g, 10.5, 10, 0.95, "#6affd8");
      } else {
        missile(g, 9, 5, 0.8);
        missile(g, 12, 10.5, 0.8);
        missile(g, 9, 16, 0.8);
      }
      break;
    case "blue":
      flame(g, level);
      break;
    case "green":
      if (level === 1) {
        // An oil slick: a dark puddle with a rainbow sheen, and a drip falling into it.
        disc(g, "#3a3050", 10, 14, 8.6, 4.4);
        disc(g, "#3a3050", 4.6, 12, 3.4, 2.6);
        disc(g, "#8a6ad8", 11, 13, 4.2, 1.3);
        disc(g, "#5ac8ff", 7.2, 15.2, 2.6, 0.9);
        disc(g, "#ffd84a", 14.5, 15, 1.6, 0.7);
        poly(g, "#3a3050", [
          [10, 0.8],
          [12.8, 5.6],
          [10, 8.4],
          [7.2, 5.6],
        ]);
        disc(g, "#3a3050", 10, 6, 2.8);
        disc(g, "#bff0ff", 9, 5.4, 0.9);
      } else if (level === 2) {
        // A mine: a spiked ball with a red light.
        for (let i = 0; i < 8; i++) {
          const a = (i / 8) * Math.PI * 2;
          poly(g, "#8a8a98", [
            [11 + Math.cos(a) * 8.8, 11 + Math.sin(a) * 8.8],
            [11 + Math.cos(a + 0.32) * 5, 11 + Math.sin(a + 0.32) * 5],
            [11 + Math.cos(a - 0.32) * 5, 11 + Math.sin(a - 0.32) * 5],
          ]);
        }
        disc(g, "#4a4a58", 11, 11, 6);
        disc(g, "#6a6a7a", 9.4, 9.2, 2.4);
        disc(g, "#ff2a2a", 11, 11, 1.8);
        disc(g, "#ffd0c0", 10.6, 10.5, 0.6);
      } else {
        // A bubble trap: a shimmering bubble.
        disc(g, "#5ac8ff", 10, 10, 8.6);
        disc(g, "#bff0ff", 10, 10, 7);
        disc(g, "#8fe0ff", 11, 11.5, 5.2);
        disc(g, "#ffffff", 7, 6.5, 2.2, 1.6);
        disc(g, "#ffffff", 13.5, 14.5, 0.9);
      }
      break;
    case "yellow":
      shield(g, level);
      break;
    case "rainbow":
      grapple(g, level);
      break;
  }
}

function rgbOf(c: string): [number, number, number] {
  const n = parseInt(c.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/** Every colour any icon uses: shrunk pixels snap back to these. */
const SNAP = [
  "#ffffff",
  "#f2f2f6",
  "#ffb02a",
  "#fff06a",
  "#a8241c",
  "#e8402a",
  "#ff8a6a",
  "#6affd8",
  "#ffd84a",
  "#8a5af0",
  "#2f7ae8",
  "#5ab4ff",
  "#e8f8ff",
  "#ffc42a",
  "#ffe88a",
  "#e86a14",
  "#e8302a",
  "#ff6ae8",
  "#6a7080",
  "#c8962a",
  "#c8c8d0",
  "#d8d8e0",
  "#3a3050",
  "#e85a14",
  "#8a6ad8",
  "#8a8a98",
  "#4a4a58",
  "#6a6a7a",
  "#ff2a2a",
  "#ffd0c0",
  "#5ac8ff",
  "#bff0ff",
  "#8fe0ff",
].map(rgbOf);

function snap(r: number, g: number, b: number) {
  let best = SNAP[0]!;
  let d = Infinity;
  for (const c of SNAP) {
    const e = (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2;
    if (e < d) {
      d = e;
      best = c;
    }
  }
  return best;
}

/** Turn a 3x drawing into a 20x20 pixel icon: average, hard alpha, snap, outline. */
function pixelate(big: HTMLCanvasElement): HTMLCanvasElement {
  const src = big.getContext("2d")!.getImageData(0, 0, ICON * SS, ICON * SS).data;
  const out = document.createElement("canvas");
  out.width = ICON;
  out.height = ICON;
  const g = out.getContext("2d")!;
  const img = g.createImageData(ICON, ICON);
  const d = img.data;
  const solid = new Uint8Array(ICON * ICON);
  for (let y = 0; y < ICON; y++)
    for (let x = 0; x < ICON; x++) {
      let r = 0;
      let gg = 0;
      let b = 0;
      let a = 0;
      for (let j = 0; j < SS; j++)
        for (let i = 0; i < SS; i++) {
          const k = ((y * SS + j) * ICON * SS + x * SS + i) * 4;
          const w = src[k + 3]! / 255;
          r += src[k]! * w;
          gg += src[k + 1]! * w;
          b += src[k + 2]! * w;
          a += w;
        }
      if (a < (SS * SS) / 2) continue;
      const [cr, cg, cb] = snap(r / a, gg / a, b / a);
      const o = (y * ICON + x) * 4;
      d[o] = cr;
      d[o + 1] = cg;
      d[o + 2] = cb;
      d[o + 3] = 255;
      solid[y * ICON + x] = 1;
    }
  for (let y = 0; y < ICON; y++)
    for (let x = 0; x < ICON; x++) {
      if (solid[y * ICON + x]) continue;
      const near =
        (x > 0 && solid[y * ICON + x - 1]) ||
        (x < ICON - 1 && solid[y * ICON + x + 1]) ||
        (y > 0 && solid[(y - 1) * ICON + x]) ||
        (y < ICON - 1 && solid[(y + 1) * ICON + x]);
      if (!near) continue;
      const o = (y * ICON + x) * 4;
      d[o] = OUTLINE[0];
      d[o + 1] = OUTLINE[1];
      d[o + 2] = OUTLINE[2];
      d[o + 3] = 255;
    }
  g.putImageData(img, 0, 0);
  return out;
}

const cache = new Map<string, HTMLCanvasElement>();

/** The icon for a balloon colour and level (1-3), a 20x20 canvas. */
export function itemIcon(color: BalloonColor, level: number): HTMLCanvasElement {
  const lv = Math.max(1, Math.min(3, Math.round(level)));
  const key = `${color}${lv}`;
  let c = cache.get(key);
  if (!c) {
    const big = document.createElement("canvas");
    big.width = ICON * SS;
    big.height = ICON * SS;
    const g = big.getContext("2d")!;
    g.scale(SS, SS);
    draw(g, color, lv);
    c = pixelate(big);
    cache.set(key, c);
  }
  return c;
}
