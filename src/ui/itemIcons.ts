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
 *   green    1 oil slick (tar)   2 mine (a coconut bomb)            3 bubble trap
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

function sheen(g: G, x: number, y: number, w: number) {
  disc(g, "#8a6ad8", x, y, w, 0.9);
  disc(g, "#5ac8ff", x + w * 0.45, y + 1.1, w * 0.55, 0.7);
}

/** The oil slick: a tar splat, a lumpy blob with drops flung out, a sheen and a glint. */
function tarSplat(g: G) {
  for (const [x, y, r] of [
    [10, 11, 6.2],
    [5.5, 8.5, 3.4],
    [14.5, 8, 3.2],
    [14, 14.5, 3.6],
    [6, 14.5, 3.4],
  ] as const)
    disc(g, "#1e1828", x, y, r);
  for (const [x, y, r] of [
    [2, 3.5, 1.3],
    [18, 3, 1.1],
    [18.6, 17.4, 1.2],
    [1.6, 18, 1],
    [10, 1.6, 1],
  ] as const)
    disc(g, "#1e1828", x, y, r);
  sheen(g, 9, 11.5, 4.6);
  disc(g, "#3a3050", 7, 8, 2, 1.2);
  disc(g, "#ffffff", 6.4, 7.6, 0.9, 0.6);
}

function fuse(g: G, x: number, y: number) {
  g.strokeStyle = "#c8962a";
  g.lineWidth = 1.2;
  g.beginPath();
  g.moveTo(x, y);
  g.quadraticCurveTo(x + 3, y - 1.5, x + 3, y - 3.4);
  g.stroke();
  // The spark: an eight-point star, orange round a white-hot middle.
  const sx = x + 3;
  const sy = y - 4.4;
  const star = (r: number, col: string) => {
    const pts: [number, number][] = [];
    for (let i = 0; i < 16; i++) {
      const a = (i / 16) * Math.PI * 2;
      const rr = i % 2 ? r * 0.42 : i % 4 ? r * 0.75 : r;
      pts.push([sx + Math.cos(a) * rr, sy + Math.sin(a) * rr]);
    }
    poly(g, col, pts);
  };
  star(3.6, "#ffb02a");
  star(2.2, "#fff06a");
  disc(g, "#ffffff", sx, sy, 0.8);
}

/** The mine: a coconut bomb, a hairy brown nut with its three eyes and a lit fuse. */
function coconutBomb(g: G) {
  disc(g, "#5a3a20", 10, 12.4, 7);
  disc(g, "#7a5030", 8.6, 10.6, 4.4);
  g.strokeStyle = "#3a2414";
  g.lineWidth = 0.7;
  for (let i = 0; i < 5; i++) {
    g.beginPath();
    g.moveTo(4.6 + i * 2.6, 8 + (i % 2));
    g.lineTo(5.6 + i * 2.6, 11 + (i % 2));
    g.stroke();
  }
  disc(g, "#3a2414", 8, 14, 1.2);
  disc(g, "#3a2414", 12, 14, 1.2);
  disc(g, "#3a2414", 10, 16.6, 1.2);
  fuse(g, 10, 5.6);
}

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

/**
 * Prototype shield icons (?shield=1|2|3|4; 0 is the original):
 *   1 knight's shield: a steel-rimmed shield, gold field, a raised boss; 1-3 gems above.
 *   2 plasma orb: the in-game shield's globe of light with 1-3 rings round it.
 *   3 turtle shell: a round shell shield of plates with a bone rim; 1-3 gems on the rim.
 *   4 energy crest: a glowing blue shield with a lightning bolt; 1-3 bolts.
 */
export const SHIELD_STYLE = {
  v: (() => {
    const q =
      typeof location !== "undefined" ? new URLSearchParams(location.search).get("shield") : null;
    const n = Number(q);
    return n >= 1 && n <= 4 ? n : 0;
  })(),
};
/** Draw every icon again (after SHIELD_STYLE changes, for the prototype sheet). */
export function clearIconCache() {
  cache.clear();
}

function gems(g: G, level: number, y: number, color: string, gap = 4.2) {
  for (let i = 0; i < level; i++) {
    const x = 10 + (i - (level - 1) / 2) * gap;
    poly(g, color, [
      [x, y - 1.6],
      [x + 1.6, y],
      [x, y + 1.6],
      [x - 1.6, y],
    ]);
    disc(g, "#ffffff", x - 0.4, y - 0.5, 0.45);
  }
}

function shieldStyle(g: G, level: number, v: number) {
  if (v === 1) {
    // A knight's shield: curved top corners, steel rim, gold field split by a bar, a boss.
    const outline: [number, number][] = [
      [10, 4.2],
      [13.5, 3.6],
      [17, 4.6],
      [17, 10],
      [15, 14.6],
      [10, 19],
      [5, 14.6],
      [3, 10],
      [3, 4.6],
      [6.5, 3.6],
    ];
    poly(g, "#c8c8d0", outline);
    poly(
      g,
      "#ffc42a",
      outline.map(([x, y]) => [10 + (x - 10) * 0.78, 11 + (y - 11) * 0.8]),
    );
    poly(g, "#c8962a", [
      [10, 5.6],
      [15.4, 5.2],
      [15.4, 10],
      [13.8, 13.6],
      [10, 17],
    ]);
    g.fillStyle = "#d8d8e0";
    g.fillRect(9.2, 5, 1.6, 12.5);
    disc(g, "#d8d8e0", 10, 10.6, 2.4);
    disc(g, "#ffffff", 9.4, 10, 0.9);
    gems(g, level, 2, "#e8302a");
  } else if (v === 2) {
    // The plasma orb (like the shield you wear): a bright globe with a white-hot middle,
    // little arcs inside, and one ring orbiting round it per level.
    for (let i = 0; i < level; i++) {
      g.save();
      g.translate(10, 10);
      g.rotate(-0.5 + i * 1.05);
      g.strokeStyle = "#ffe88a";
      g.lineWidth = 1.1;
      g.beginPath();
      g.ellipse(0, 0, 9.2, 3.4, 0, 0, Math.PI * 2);
      g.stroke();
      g.restore();
    }
    disc(g, "#ffb02a", 10, 10, 6.4);
    disc(g, "#ffd84a", 10, 10, 5.2);
    disc(g, "#fff06a", 10, 10, 3.4);
    disc(g, "#ffffff", 10, 10, 1.7);
    g.strokeStyle = "#ffffff";
    g.lineWidth = 0.8;
    g.beginPath();
    g.moveTo(10, 10);
    g.lineTo(7.4, 7.6);
    g.lineTo(6.2, 9.4);
    g.moveTo(10, 10);
    g.lineTo(13.4, 11.8);
    g.lineTo(13, 14);
    g.stroke();
    disc(g, "#ffffff", 7.4, 6.4, 1, 0.7);
  } else if (v === 3) {
    // A turtle-shell shield: a domed shell of plates with a bone rim and gems.
    disc(g, "#efe3c4", 10, 10.6, 8.8, 8.2);
    disc(g, "#5a8a3a", 10, 10.6, 7.4, 6.8);
    const hex = (cx: number, cy: number, r: number, col: string) =>
      poly(
        g,
        col,
        Array.from({ length: 6 }, (_, k) => {
          const a = (k / 6) * Math.PI * 2 + Math.PI / 6;
          return [cx + Math.cos(a) * r, cy + Math.sin(a) * r] as [number, number];
        }),
      );
    hex(10, 10.6, 2.6, "#8ac25a");
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2;
      hex(10 + Math.cos(a) * 4.6, 10.6 + Math.sin(a) * 4.4, 1.9, "#7ab24a");
    }
    disc(g, "#d8f0a8", 8.4, 8.6, 1.2, 0.8);
    gems(g, level, 2.4, "#ffd84a", 4.6);
  } else {
    // An energy crest: a glowing blue shield with a lightning bolt, one bolt per level.
    const outline: [number, number][] = [
      [10, 1.6],
      [17.6, 4.4],
      [16.6, 12],
      [10, 18.8],
      [3.4, 12],
      [2.4, 4.4],
    ];
    poly(g, "#bff0ff", outline);
    poly(
      g,
      "#2f7ae8",
      outline.map(([x, y]) => [10 + (x - 10) * 0.8, 9.6 + (y - 9.6) * 0.8]),
    );
    poly(
      g,
      "#5ab4ff",
      outline.map(([x, y]) => [8.8 + (x - 10) * 0.45, 8.4 + (y - 9.6) * 0.5]),
    );
    const bolt = (cx: number, s: number) =>
      poly(g, "#fff06a", [
        [cx + 0.6 * s, 4.4],
        [cx - 2.2 * s, 10.6],
        [cx - 0.2 * s, 10.6],
        [cx - 1 * s, 16],
        [cx + 2.4 * s, 8.8],
        [cx + 0.4 * s, 8.8],
      ]);
    if (level === 1) bolt(10, 1);
    else if (level === 2) {
      bolt(7.6, 0.8);
      bolt(12.4, 0.8);
    } else {
      bolt(6.4, 0.66);
      bolt(10, 0.66);
      bolt(13.6, 0.66);
    }
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
      if (level === 1) tarSplat(g);
      else if (level === 2) coconutBomb(g);
      else {
        // A bubble trap: a shimmering bubble.
        disc(g, "#5ac8ff", 10, 10, 8.6);
        disc(g, "#bff0ff", 10, 10, 7);
        disc(g, "#8fe0ff", 11, 11.5, 5.2);
        disc(g, "#ffffff", 7, 6.5, 2.2, 1.6);
        disc(g, "#ffffff", 13.5, 14.5, 0.9);
      }
      break;
    case "yellow":
      if (SHIELD_STYLE.v) shieldStyle(g, level, SHIELD_STYLE.v);
      else shield(g, level);
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
  "#1e1828",
  "#2a2240",
  "#b8582a",
  "#e07a3a",
  "#7a3418",
  "#fff0d0",
  "#5a3a20",
  "#7a5030",
  "#3a2414",
  "#c8962a",
  "#efe3c4",
  "#5a8a3a",
  "#8ac25a",
  "#7ab24a",
  "#d8f0a8",
  "#e8302a",
  "#ffb02a",
  "#fff06a",
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
