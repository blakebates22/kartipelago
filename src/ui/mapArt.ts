/**
 * Ancient-map art for the track menus, painted in code at the UI's low resolution:
 * aged parchment (mottled, stained, creased, its edges burnt and torn), inked sea curls,
 * a compass rose, little ships, and each world drawn as an island vignette (jungle and
 * volcano, snowy peaks, red mesas, jade hills and pagodas) with an inked route round it.
 *
 * Still parts are painted once and cached. All original artwork (Blake's reference map
 * was mood only).
 */
type G = CanvasRenderingContext2D;

function hash(x: number, y: number, s = 0) {
  const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453;
  return v - Math.floor(v);
}
/** Smooth value noise in 0..1. */
function noise(x: number, y: number, s = 0) {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const fx = x - xi;
  const fy = y - yi;
  const u = fx * fx * (3 - 2 * fx);
  const v = fy * fy * (3 - 2 * fy);
  const a = hash(xi, yi, s);
  const b = hash(xi + 1, yi, s);
  const c = hash(xi, yi + 1, s);
  const d = hash(xi + 1, yi + 1, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}

function canvas(w: number, h: number): [HTMLCanvasElement, G] {
  const c = document.createElement("canvas");
  c.width = Math.max(1, Math.ceil(w));
  c.height = Math.max(1, Math.ceil(h));
  const g = c.getContext("2d")!;
  g.imageSmoothingEnabled = false;
  return [c, g];
}

const px = (g: G, x: number, y: number, w: number, h: number, c: string) => {
  g.fillStyle = c;
  g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};

export const INK = "#4a3220";
export const INK_SOFT = "#7a5a3a";
export const PAPER = "#e9d4a4";

const PAPER_TONES = ["#f0dcae", "#e9d4a4", "#e0c896", "#d6bb86", "#cbae78"];

// ---------------------------------------------------------------- parchment

const paperCache = new Map<string, HTMLCanvasElement>();

/** The whole sheet: aged parchment with burnt edges, sea curls, a compass, ships. */
export function parchment(W: number, H: number, opts: { compass?: boolean; ships?: boolean } = {}) {
  const key = `${W}x${H}:${opts.compass ?? true}:${opts.ships ?? true}`;
  let c = paperCache.get(key);
  if (c) return c;
  const [cv, g] = canvas(W, H);
  c = cv;
  // Mottled paper: two scales of noise.
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const n = noise(x / 22, y / 22, 1) * 0.65 + noise(x / 6, y / 6, 2) * 0.35;
      const k = Math.min(PAPER_TONES.length - 1, Math.floor(n * PAPER_TONES.length));
      px(g, x, y, 1, 1, PAPER_TONES[k]!);
    }
  // Coffee-ring stains.
  for (let i = 0; i < 4; i++) {
    const cx = hash(i, 1, 3) * W;
    const cy = hash(i, 2, 3) * H;
    const r = 10 + hash(i, 3, 3) * 16;
    for (let a = 0; a < Math.PI * 2; a += 0.04) {
      const rr = r + Math.sin(a * 5 + i) * 1.2;
      px(g, cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * 0.8, 1, 1, "#c4a26c");
    }
  }
  // Fold creases: a light line with a darker one beside it.
  for (const fx of [Math.round(W / 3), Math.round((W * 2) / 3)]) {
    px(g, fx, 0, 1, H, "#f4e4bc");
    px(g, fx + 1, 0, 1, H, "#cdb07c");
  }
  px(g, 0, Math.round(H / 2), W, 1, "#f4e4bc");
  px(g, 0, Math.round(H / 2) + 1, W, 1, "#cdb07c");
  // A faint graticule.
  for (let x = 24; x < W; x += 48) for (let y = 0; y < H; y += 3) px(g, x, y, 1, 1, "#d2b783");
  for (let y = 30; y < H; y += 48) for (let x = 0; x < W; x += 3) px(g, x, y, 1, 1, "#d2b783");
  // Sea curls: little inked waves scattered over the open water.
  for (let i = 0; i < Math.floor((W * H) / 2600); i++) {
    const x = hash(i, 7, 4) * W;
    const y = hash(i, 8, 4) * H;
    seaCurl(g, x, y, hash(i, 9) < 0.5 ? INK_SOFT : "#9a7a52");
  }
  if (opts.ships ?? true) {
    ship(g, W * 0.08, H * 0.82);
    ship(g, W * 0.56, H * 0.9);
  }
  if (opts.compass ?? true) compassRose(g, W - 30, H - 34, 16);
  // Burnt, torn edges: a ragged dark border fading into the paper.
  for (let x = 0; x < W; x++)
    for (const [y0, dir] of [
      [0, 1],
      [H - 1, -1],
    ] as const) {
      const d = 2 + noise(x / 7, y0, 5) * 6;
      for (let k = 0; k < d + 3; k++)
        px(g, x, y0 + dir * k, 1, 1, k < d * 0.5 ? "#3a2414" : k < d ? "#7a5030" : "#b8915c");
    }
  for (let y = 0; y < H; y++)
    for (const [x0, dir] of [
      [0, 1],
      [W - 1, -1],
    ] as const) {
      const d = 2 + noise(x0, y / 7, 6) * 6;
      for (let k = 0; k < d + 3; k++)
        px(g, x0 + dir * k, y, 1, 1, k < d * 0.5 ? "#3a2414" : k < d ? "#7a5030" : "#b8915c");
    }
  paperCache.set(key, c);
  return c;
}

/** A little inked wave: two crests. */
function seaCurl(g: G, x: number, y: number, c: string) {
  for (const [dx, dy] of [
    [0, 1],
    [1, 0],
    [2, 0],
    [3, 1],
    [4, 1],
    [5, 0],
    [6, 0],
    [7, 1],
  ] as const)
    px(g, x + dx, y + dy, 1, 1, c);
}

/** A tiny sailing ship. */
function ship(g: G, x: number, y: number) {
  px(g, x - 7, y, 14, 2, INK);
  px(g, x - 5, y + 2, 10, 1, INK);
  px(g, x, y - 12, 1, 12, INK);
  for (let k = 0; k < 9; k++) px(g, x + 1, y - 11 + k, Math.min(k, 8 - k) + 2, 1, "#f4e8cc");
  for (let k = 0; k < 6; k++)
    px(g, x - 1 - Math.min(k, 5 - k) - 1, y - 9 + k, Math.min(k, 5 - k) + 1, 1, "#f4e8cc");
  px(g, x, y - 14, 3, 2, "#b8302a");
  seaCurl(g, x - 10, y + 3, INK_SOFT);
}

/** An inked compass rose with N, E, S, W. */
export function compassRose(g: G, cx: number, cy: number, r: number) {
  for (let a = 0; a < Math.PI * 2; a += 0.05)
    px(g, cx + Math.cos(a) * r, cy + Math.sin(a) * r, 1, 1, INK_SOFT);
  for (let a = 0; a < Math.PI * 2; a += 0.08)
    px(g, cx + Math.cos(a) * (r - 3), cy + Math.sin(a) * (r - 3), 1, 1, INK_SOFT);
  const point = (ang: number, len: number, w: number, c1: string, c2: string) => {
    for (let k = 0; k < len; k++) {
      const half = w * (1 - k / len);
      const x = cx + Math.cos(ang) * k;
      const y = cy + Math.sin(ang) * k;
      const nx = -Math.sin(ang);
      const ny = Math.cos(ang);
      for (let s = -half; s <= half; s += 0.5) px(g, x + nx * s, y + ny * s, 1, 1, s < 0 ? c1 : c2);
    }
  };
  for (let i = 0; i < 4; i++)
    point(Math.PI / 4 + (i * Math.PI) / 2, r * 0.6, 2, "#b8915c", INK_SOFT);
  for (let i = 0; i < 4; i++) point((i * Math.PI) / 2 - Math.PI / 2, r + 2, 3, "#b8302a", INK);
  px(g, cx - 1, cy - 1, 3, 3, "#f0dcae");
  // The letters, in tiny hand-made pixels.
  const letter = (s: string, x: number, y: number) => {
    const L: Record<string, string[]> = {
      N: ["1001", "1101", "1011", "1001"],
      E: ["111", "110", "100", "111"],
      S: ["111", "110", "011", "111"],
      W: ["10001", "10101", "10101", "01010"],
    };
    L[s]!.forEach((row, j) =>
      [...row].forEach((b, i) => b === "1" && px(g, x + i, y + j, 1, 1, INK)),
    );
  };
  letter("N", cx - 2, cy - r - 8);
  letter("S", cx - 1, cy + r + 4);
  letter("E", cx + r + 4, cy - 2);
  letter("W", cx - r - 9, cy - 2);
}

// ---------------------------------------------------------------- islands

export type IslandStyle = "prehistoric" | "frostveil" | "desert" | "dragon";

const islandCache = new Map<string, HTMLCanvasElement>();

/** How far an island's coast reaches at angle `a` (0..1 of its radius). */
function coast(a: number, seed: number) {
  return (
    0.82 +
    noise(Math.cos(a) * 1.6 + 5, Math.sin(a) * 1.6 + 5, seed) * 0.3 +
    Math.sin(a * 3 + seed) * 0.04
  );
}

/**
 * A world's island, `r` across its middle: shallows, a pale beach, an inked coast, and
 * its own land on top. Returned as a canvas (2r + margin square); draw it centred.
 */
export function island(style: IslandStyle, r: number): HTMLCanvasElement {
  const key = `${style}:${r}`;
  let c = islandCache.get(key);
  if (c) return c;
  const S = Math.ceil(r * 2.6);
  const [cv, g] = canvas(S, S);
  c = cv;
  const o = S / 2;
  const seed = { prehistoric: 11, frostveil: 23, desert: 37, dragon: 51 }[style];
  const land = {
    prehistoric: ["#6aa84a", "#5a9a3e", "#7fbc56"],
    frostveil: ["#e8eef4", "#cfdcea", "#f6f9fc"],
    desert: ["#e0a060", "#d48a4e", "#eab478"],
    dragon: ["#7cbc8a", "#68a878", "#94cca0"],
  }[style];
  for (let y = 0; y < S; y++)
    for (let x = 0; x < S; x++) {
      const dx = x - o;
      const dy = (y - o) * 1.25;
      const d = Math.hypot(dx, dy) / r;
      const edge = coast(Math.atan2(dy, dx), seed);
      if (d < edge - 0.08) {
        const n = noise(x / 6, y / 6, seed);
        px(g, x, y, 1, 1, land[Math.min(2, Math.floor(n * 3))]!);
      } else if (d < edge - 0.02) px(g, x, y, 1, 1, style === "frostveil" ? "#b8c8d8" : "#f2e2b0");
      else if (d < edge + 0.02) px(g, x, y, 1, 1, INK);
      else if (d < edge + 0.16 && (x + y) % 3 === 0) px(g, x, y, 1, 1, "#9ab8b0");
    }
  // The land's features.
  const at = (fx: number, fy: number): [number, number] => [o + fx * r, o + fy * r * 0.8];
  if (style === "prehistoric") {
    // A volcano with a lava trickle, jungle clumps, a river.
    const [vx, vy] = at(-0.15, -0.2);
    for (let k = 0; k < 14; k++)
      px(g, vx - k, vy + k, k * 2 + 1, 1, k < 3 ? "#5e4d66" : k % 2 ? "#6e5c76" : "#5e4d66");
    px(g, vx - 1, vy - 1, 3, 2, "#ff7a2a");
    for (let k = 2; k < 12; k++) px(g, vx + Math.sin(k) * 1.2, vy + k, 1, 1, "#e8501e");
    for (let i = 0; i < 4; i++) px(g, vx + 1 + i * 2, vy - 3 - i * 2, 2 + i, 2, "#8a8088");
    for (let i = 0; i < 16; i++) {
      const [tx, ty] = at((hash(i, 1) - 0.5) * 1.3, (hash(i, 2) - 0.2) * 1.1);
      px(g, tx - 1, ty - 1, 3, 3, "#3d7a32");
      px(g, tx - 1, ty - 1, 2, 1, "#5fae46");
    }
    for (let k = 0; k < r * 0.9; k++) {
      const [rx, ry] = at(0.15 + Math.sin(k * 0.2) * 0.06, -0.1 + k / r);
      px(g, rx, ry, 2, 1, "#4fa8d8");
    }
  } else if (style === "frostveil") {
    // A range of snowy peaks and a citadel.
    for (let i = 0; i < 6; i++) {
      const [mx, my] = at(-0.6 + i * 0.24, -0.15 + (i % 2) * 0.25);
      const h = 9 + (i % 3) * 3;
      for (let k = 0; k < h; k++) {
        px(g, mx - k * 0.8, my + k, k * 0.8, 1, "#8a9ab8");
        px(g, mx, my + k, k * 0.8, 1, "#6a7a98");
        if (k < h * 0.4) px(g, mx - k * 0.8, my + k, k * 1.6, 1, "#ffffff");
      }
    }
    const [cx, cy] = at(0.2, 0.35);
    px(g, cx - 4, cy - 4, 9, 5, "#7a86a8");
    px(g, cx - 4, cy - 7, 2, 3, "#7a86a8");
    px(g, cx + 3, cy - 7, 2, 3, "#7a86a8");
    px(g, cx - 1, cy - 2, 2, 3, "#2a3050");
  } else if (style === "desert") {
    // Mesas, a canyon, an oasis with palms.
    for (let i = 0; i < 5; i++) {
      const [mx, my] = at(-0.55 + i * 0.27, -0.25 + (i % 2) * 0.3);
      const w = 8 + (i % 3) * 3;
      px(g, mx - w / 2, my, w, 6, "#b4613a");
      px(g, mx - w / 2, my, w, 1, "#e8a676");
      px(g, mx - w / 2, my + 3, w, 1, "#a3552f");
    }
    for (let k = 0; k < r * 1.1; k++) {
      const [cx, cy] = at(-0.5 + k / r, 0.3 + Math.sin(k * 0.25) * 0.08);
      px(g, cx, cy, 1, 2, "#8a4a2a");
    }
    const [ox, oy] = at(0.35, 0.45);
    for (let y = -2; y <= 2; y++)
      px(g, ox - 4 + Math.abs(y), oy + y, 8 - Math.abs(y) * 2, 1, "#4fb8d8");
    px(g, ox + 4, oy - 5, 1, 5, "#7a5a3a");
    px(g, ox + 2, oy - 6, 5, 1, "#3d8a34");
  } else {
    // Jade hills, a red bridge, pagodas, blossom.
    for (let i = 0; i < 8; i++) {
      const [hx, hy] = at(-0.6 + i * 0.17, -0.2 + (i % 3) * 0.15);
      for (let k = 0; k < 6; k++)
        px(g, hx - k, hy + k, k * 2 + 1, 1, k % 2 ? "#4f9a68" : "#5aa874");
    }
    const pagoda = (x: number, y: number, s: number) => {
      for (let tier = 0; tier < 3; tier++) {
        const w = (9 - tier * 2) * s;
        px(g, x - w / 2 - 1, y - tier * 4 * s, w + 2, 1, "#2a5a9a");
        px(g, x - w / 2 + 1, y - tier * 4 * s + 1, w - 2, 3 * s, "#c8322a");
      }
      px(g, x, y - 12 * s, 1, 2, "#f2c64a");
    };
    pagoda(...at(0.15, -0.05), 1);
    pagoda(...at(-0.35, 0.3), 0.7);
    const [bx, by] = at(0.25, 0.4);
    for (let k = -6; k <= 6; k++)
      px(g, bx + k, by - Math.round(Math.sqrt(36 - k * k) * 0.5), 1, 2, "#d8402a");
    for (let i = 0; i < 6; i++) {
      const [tx, ty] = at((hash(i, 5) - 0.5) * 1.2, (hash(i, 6) - 0.1) * 0.9);
      px(g, tx, ty, 2, 2, "#f2a0c0");
    }
  }
  islandCache.set(key, c);
  return c;
}

/** Points round an island where its tracks sit (an inked route links them). */
export function routeStops(cx: number, cy: number, r: number, n: number): [number, number][] {
  const out: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const a = -Math.PI * 0.85 + (i / Math.max(1, n - 1)) * Math.PI * 1.7;
    out.push([cx + Math.cos(a) * r * 0.62, cy + Math.sin(a) * r * 0.5]);
  }
  return out;
}

/** A dashed inked route through points. */
export function dashedRoute(g: G, pts: [number, number][], color = INK) {
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i]!;
    const [x1, y1] = pts[i + 1]!;
    const n = Math.ceil(Math.hypot(x1 - x0, y1 - y0));
    // A gentle bow between stops.
    const mx = (x0 + x1) / 2 + (y1 - y0) * 0.15;
    const my = (y0 + y1) / 2 - (x1 - x0) * 0.15;
    for (let k = 0; k < n; k++) {
      if (k % 4 > 1) continue;
      const t = k / n;
      const x = (1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * mx + t * t * x1;
      const y = (1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * my + t * t * y1;
      px(g, x, y, 1, 1, color);
    }
  }
}

/** A route stop: an inked ring with a number, filled gold when it's chosen. */
export function stop(g: G, x: number, y: number, label: string, on: boolean, locked = false) {
  const r = on ? 5 : 4;
  for (let yy = -r; yy <= r; yy++) {
    const half = Math.sqrt(r * r - yy * yy);
    px(g, x - half, y + yy, half * 2 + 1, 1, INK);
  }
  const ri = r - 1;
  for (let yy = -ri; yy <= ri; yy++) {
    const half = Math.sqrt(ri * ri - yy * yy);
    px(g, x - half, y + yy, half * 2 + 1, 1, locked ? "#b8a88a" : on ? "#ffd84a" : "#f4e8cc");
  }
  // A tiny numeral.
  const D: Record<string, string[]> = {
    "1": ["010", "110", "010", "111"],
    "2": ["110", "001", "010", "111"],
    "3": ["110", "011", "001", "110"],
    "4": ["101", "101", "111", "001"],
  };
  (D[label] ?? []).forEach((row, j) =>
    [...row].forEach((b, i) => b === "1" && px(g, x - 1 + i, y - 2 + j, 1, 1, INK)),
  );
}

/** A small gold trophy cup (about 12 x 14), for Trophy Race. */
const METALS = {
  gold: ["#f2c64a", "#b8861a", "#fff0a0"],
  silver: ["#d4dae4", "#8a94a8", "#ffffff"],
  bronze: ["#d8904a", "#8a5226", "#f6c08a"],
} as const;
export type Metal = keyof typeof METALS;

export function trophy(g: G, x: number, y: number, s = 1, shine = 0, metal: Metal = "gold") {
  const [gold, dark, lite] = METALS[metal];
  const P = (dx: number, dy: number, w: number, h: number, c: string) =>
    px(g, x + dx * s, y + dy * s, w * s, h * s, c);
  // Outline first, then the cup.
  P(-1, -1, 14, 10, INK);
  P(2, 8, 8, 3, INK);
  P(0, 10, 12, 5, INK);
  P(0, 0, 12, 8, gold);
  P(0, 0, 12, 1, lite);
  P(9, 1, 2, 6, dark);
  P(-3, 1, 3, 1, INK);
  P(-3, 1, 1, 4, INK);
  P(-3, 4, 3, 1, INK);
  P(12, 1, 3, 1, INK);
  P(14, 1, 1, 4, INK);
  P(12, 4, 3, 1, INK);
  P(4, 8, 4, 2, dark);
  P(1, 11, 10, 3, dark);
  P(2, 11, 8, 1, gold);
  P(3, 2, 2, 4, shine > 0.5 ? "#ffffff" : lite);
}
