/**
 * Art for the racer select screen, painted in code at the UI's low resolution: the
 * mystery eggs in the locked roster slots (racers still to hatch), and the background
 * backgrounds. The select screen uses dawn (Blake's pick); the others stay as options
 * (?selectbg=ruins|vista).
 *
 *   dawn   a jungle at sunrise: a clear sky going gold at the horizon, the sun just up,
 *          hills in the morning haze and mist, backlit palms, birds and drifting pollen.
 *   ruins  an old temple wall: carved stone, a dinosaur frieze, glyphs, vines and two
 *          flickering torches.
 *   vista  the Choose a Mode scene, dimmed behind the roster.
 *
 * All original artwork.
 */
import { modeVista } from "./modeArt";

type G = CanvasRenderingContext2D;

function hash(x: number, y: number, s = 0) {
  const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453;
  return v - Math.floor(v);
}

const px = (g: G, x: number, y: number, w: number, h: number, c: string) => {
  g.fillStyle = c;
  g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};

function canvas(w: number, h: number): [HTMLCanvasElement, G] {
  const c = document.createElement("canvas");
  c.width = Math.max(1, w);
  c.height = Math.max(1, h);
  const g = c.getContext("2d")!;
  g.imageSmoothingEnabled = false;
  return [c, g];
}

// ---------------------------------------------------------------- mystery eggs

const SPECKLES = ["#3fb8a8", "#8a5ad8", "#e8603a", "#5aae3a"];

/**
 * A mystery egg (a racer still to hatch): speckled, cracked, and now and then it
 * wobbles. `size` is its height in pixels; `seed` picks its speckle colour.
 */
export function mysteryEgg(
  g: G,
  cx: number,
  cy: number,
  size: number,
  t: number,
  seed: number,
  calm = false,
) {
  const h = size / 2;
  const w = size * 0.38;
  // A wobble every few seconds (different for each egg).
  const ph = (t + seed * 1.7) % 4.2;
  const wob = calm || ph > 0.6 ? 0 : Math.sin(ph * 30) * (1 - ph / 0.6);
  const tilt = (y: number) => Math.round(wob * 2 * ((y + h) / (2 * h)));
  const speck = SPECKLES[seed % SPECKLES.length]!;
  // Egg shape: rounder at the bottom, narrower at the top.
  const half = (y: number) => {
    const u = y / h; // -1 top .. 1 bottom
    const k = 1 - u * u;
    return k <= 0 ? 0 : Math.sqrt(k) * w * (1 + u * 0.18);
  };
  for (let y = -h - 1; y <= h + 1; y++) {
    const hw = half(Math.max(-h, Math.min(h, y)));
    if (hw <= 0) continue;
    px(g, cx - hw - 1 + tilt(y), cy + y, hw * 2 + 2, 1, "#2a1e14");
  }
  for (let y = -h; y <= h; y++) {
    const hw = half(y);
    if (hw <= 0.5) continue;
    const shade = y > h * 0.45 ? "#c9b48e" : "#ecdfbe";
    px(g, cx - hw + tilt(y), cy + y, hw * 2, 1, shade);
    // A light highlight on the upper left.
    if (y < -h * 0.2 && y > -h * 0.75)
      px(g, cx - hw * 0.6 + tilt(y), cy + y, Math.max(1, hw * 0.25), 1, "#fbf4e0");
  }
  // Speckles.
  for (let i = 0; i < 10; i++) {
    const sy = -h * 0.8 + hash(i, seed) * h * 1.6;
    const hw = half(sy);
    const sx = (hash(i, seed, 2) * 2 - 1) * hw * 0.8;
    px(g, cx + sx + tilt(sy), cy + sy, i % 3 ? 1 : 2, i % 3 ? 1 : 2, speck);
  }
  // A zigzag crack across the middle, and a "?" glowing through it.
  const cyc = cy - h * 0.05;
  for (let x = -w * 0.8; x < w * 0.8; x++) {
    const zz = Math.abs(((x + 100) % 4) - 2) - 1;
    px(g, cx + x + tilt(0), cyc + zz, 1, 1, "#4a3220");
  }
  const glow = calm ? 0.8 : 0.6 + 0.4 * Math.sin(t * 3 + seed);
  g.globalAlpha = glow;
  const q = ["0110", "1001", "0010", "0100", "0000", "0100"];
  q.forEach((row, j) =>
    [...row].forEach(
      (b, i) => b === "1" && px(g, cx - 2 + i + tilt(j), cy - h * 0.55 + j, 1, 1, "#ffd84a"),
    ),
  );
  g.globalAlpha = 1;
}

// ---------------------------------------------------------------- backgrounds

export type SelectBackdrop = "dawn" | "ruins" | "vista";

const cache = new Map<string, HTMLCanvasElement>();

function paintDawn(W: number, H: number) {
  const [c, g] = canvas(W, H);
  // A clear morning sky: blue overhead, gold and peach at the horizon.
  const sky = [
    "#5aa8e8",
    "#6ab4ec",
    "#82c2ee",
    "#9ecff0",
    "#bcdcec",
    "#dce2d8",
    "#f2dcb4",
    "#fad49a",
  ];
  const horizon = Math.round(H * 0.6);
  const band = Math.ceil(horizon / sky.length);
  sky.forEach((col, i) => px(g, 0, i * band, W, band + 1, col));
  // The sun just up over the hills, with soft rays.
  const sx = W * 0.68;
  const sy = horizon - 22;
  g.globalAlpha = 0.18;
  for (let k = 0; k < 9; k++) {
    const a = -Math.PI + (k / 8) * Math.PI;
    g.fillStyle = "#fff6d0";
    g.beginPath();
    g.moveTo(sx, sy);
    g.lineTo(sx + Math.cos(a - 0.05) * W, sy + Math.sin(a - 0.05) * W);
    g.lineTo(sx + Math.cos(a + 0.05) * W, sy + Math.sin(a + 0.05) * W);
    g.fill();
  }
  g.globalAlpha = 1;
  for (let y = -16; y <= 16; y++) {
    const hw = Math.sqrt(256 - y * y);
    px(g, sx - hw, sy + y, hw * 2, 1, "#fff2b8");
  }
  for (let y = -11; y <= 11; y++) {
    const hw = Math.sqrt(121 - y * y);
    px(g, sx - hw, sy + y, hw * 2, 1, "#fffbe8");
  }
  // A few morning clouds, lit gold from below.
  for (const [cx, cy, w] of [
    [W * 0.18, 34, 46],
    [W * 0.48, 22, 34],
    [W * 0.86, 44, 40],
  ] as const) {
    px(g, cx, cy + 3, w, 5, "#ffffff");
    px(g, cx + 5, cy, w * 0.5, 5, "#ffffff");
    px(g, cx + w * 0.45, cy - 2, w * 0.35, 6, "#ffffff");
    px(g, cx, cy + 8, w, 2, "#ffd9a0");
  }
  // Hills in the haze: far blue-green, the volcano (a wisp of smoke), nearer greens.
  const ridge = (base: number, amp: number, freq: number, seed: number, col: string) => {
    for (let x = 0; x < W; x++) {
      const y =
        base -
        Math.abs(Math.sin(x * freq + seed)) * amp -
        Math.sin(x * freq * 2.7 + seed) * amp * 0.3;
      px(g, x, y, 1, H - y, col);
    }
  };
  ridge(horizon + 4, 14, 0.03, 1, "#8fb4b0");
  const vx = W * 0.24;
  for (let x = vx - 70; x < vx + 70; x++) {
    const d = Math.abs(x - vx);
    const y = horizon - 62 + (d < 7 ? 2 : 0) + d * 0.8;
    px(g, x, y, 1, H - y, x < vx ? "#7e8c9e" : "#6e7c90");
  }
  for (let k = 0; k < 7; k++) {
    const r = 3 + k * 1.6;
    const cx2 = vx + 4 + k * 5;
    const cy2 = horizon - 66 - k * 6;
    for (let y = -r; y <= r; y++) {
      const hw = Math.sqrt(r * r - y * y);
      px(g, cx2 - hw, cy2 + y, hw * 2, 1, "#e6e2e0");
    }
  }
  // Morning mist in the valley.
  g.globalAlpha = 0.55;
  px(g, 0, horizon + 6, W, 6, "#f4f0e4");
  g.globalAlpha = 0.3;
  px(g, 0, horizon + 12, W, 8, "#f4f0e4");
  g.globalAlpha = 1;
  ridge(horizon + 22, 10, 0.05, 4, "#5f9a5a");
  ridge(horizon + 34, 8, 0.07, 7, "#4a8a46");
  // The jungle floor and palms, backlit by the sun (deep green, not black).
  px(g, 0, horizon + 40, W, H, "#3a7a3a");
  const palm = (x: number, base: number, h: number, lean: number) => {
    for (let k = 0; k < h; k++)
      px(g, x + lean * (k / h) ** 2 * h * 0.3, base - k, 3, 1, k % 6 < 3 ? "#5a4028" : "#4a3420");
    const tx = x + lean * h * 0.3;
    const ty = base - h;
    for (const [dx, dy] of [
      [-1, 0.2],
      [-0.7, -0.5],
      [0, -0.8],
      [0.7, -0.5],
      [1, 0.2],
    ] as const)
      for (let k = 0; k < 14; k++) {
        px(g, tx + dx * k, ty + dy * k + (k / 14) ** 2 * 6, 2, 2, "#2f6a2c");
        px(g, tx + dx * k, ty + dy * k + (k / 14) ** 2 * 6, 1, 1, "#5aa848");
      }
  };
  palm(18, H, 120, 1);
  palm(W - 30, H, 132, -1);
  palm(W - 70, H, 90, -0.6);
  palm(60, H, 80, 0.7);
  for (let x = 0; x < W; x += 9)
    for (let k = 0; k < 8; k++)
      px(g, x + k, H - 10 + Math.abs(k - 4), 1, 10, k % 2 ? "#2f6a2c" : "#3d8a34");
  return c;
}

function paintRuins(W: number, H: number) {
  const [c, g] = canvas(W, H);
  px(g, 0, 0, W, H, "#2a2420");
  // Big stone blocks in rough courses.
  const stones = ["#6a5f52", "#5e544a", "#75695a", "#544a40"];
  let y = 0;
  let row = 0;
  while (y < H) {
    const bh = 22 + Math.floor(hash(row, 3) * 10);
    let x = -hash(row, 4) * 30;
    let k = 0;
    while (x < W) {
      const bw = 34 + Math.floor(hash(k, row, 5) * 30);
      const col = stones[Math.floor(hash(k, row, 6) * stones.length)]!;
      px(g, x + 1, y + 1, bw - 2, bh - 2, col);
      px(g, x + 1, y + 1, bw - 2, 1, "#8a7e6c");
      px(g, x + 1, y + bh - 2, bw - 2, 1, "#3e362e");
      // Chips and cracks.
      if (hash(k, row, 7) < 0.4) {
        let cx = x + 4 + hash(k, row, 8) * (bw - 8);
        for (let j = 0; j < bh - 3; j++) {
          px(g, cx, y + 2 + j, 1, 1, "#3e362e");
          cx += hash(j, k, row) < 0.5 ? -1 : 1;
        }
      }
      // A carved glyph on some.
      if (hash(k, row, 9) < 0.2 && bw > 40) {
        const gx = x + bw / 2;
        const gy = y + bh / 2;
        for (let i = 0; i < 30; i++) {
          const a = i * 0.5;
          const r = 0.5 + i * 0.25;
          px(g, gx + Math.cos(a) * r * 1.3, gy + Math.sin(a) * r, 1, 1, "#3e362e");
        }
      }
      x += bw;
      k++;
    }
    y += bh;
    row++;
  }
  // A frieze of marching dinosaurs carved along a band.
  const fy = Math.round(H * 0.18);
  px(g, 0, fy, W, 20, "#7a6e5e");
  px(g, 0, fy, W, 1, "#9a8e7a");
  px(g, 0, fy + 19, W, 1, "#3e362e");
  for (let x = 6; x < W; x += 34) {
    // A little long-neck in relief.
    for (let k = -5; k <= 5; k++)
      px(g, x + 10 + k, fy + 12 - Math.sqrt(30 - k * k) * 0.8, 1, 4, "#4e463c");
    for (let k = 0; k < 6; k++) px(g, x + 15 + k * 0.6, fy + 9 - k, 2, 2, "#4e463c");
    px(g, x + 18, fy + 2, 4, 2, "#4e463c");
    for (const lx of [6, 9, 12, 14]) px(g, x + lx, fy + 14, 1, 4, "#4e463c");
    for (let k = 0; k < 6; k++) px(g, x + 4 - k, fy + 12 + k * 0.3, 1, 1, "#4e463c");
  }
  // Vines down from the top.
  for (let i = 0; i < 12; i++) {
    const vx = hash(i, 11) * W;
    const len = 20 + hash(i, 12) * 70;
    for (let k = 0; k < len; k++) {
      px(g, vx + Math.sin(k * 0.25 + i) * 2, k, 1, 1, "#3d6a2c");
      if (k % 6 === 3) px(g, vx + 1 + Math.sin(k * 0.25 + i) * 2, k, 3, 2, "#4f8a3a");
    }
  }
  // Darker toward the edges (the torches light the middle).
  for (let x = 0; x < W; x += 2) {
    const d = Math.abs(x - W / 2) / (W / 2);
    if (d > 0.55) {
      g.globalAlpha = (d - 0.55) * 0.9;
      px(g, x, 0, 2, H, "#0e0a08");
    }
  }
  g.globalAlpha = 1;
  return c;
}

/** Torches either side, flickering (drawn each frame over the ruins). */
function torches(g: G, W: number, H: number, t: number, calm: boolean) {
  for (const tx of [10, W - 16]) {
    const ty = Math.round(H * 0.42);
    px(g, tx, ty, 6, 26, "#4a3220");
    px(g, tx - 2, ty - 3, 10, 4, "#6a4a2a");
    const f = calm ? 1 : 0.85 + Math.sin(t * 17 + tx) * 0.1 + Math.sin(t * 29) * 0.06;
    for (let k = 0; k < 14; k++) {
      const w = (1 - k / 14) * 8 * f;
      px(
        g,
        tx + 3 - w / 2 + Math.sin(t * 9 + k) * (calm ? 0 : 0.8),
        ty - 4 - k,
        w,
        1,
        k < 4 ? "#ffe07a" : k < 9 ? "#ff9a2a" : "#d8401e",
      );
    }
    // A warm glow on the wall round it.
    g.globalAlpha = 0.12 * f;
    for (let r = 30; r > 6; r -= 6) {
      g.fillStyle = "#ff9a3a";
      g.beginPath();
      g.arc(tx + 3, ty - 8, r, 0, Math.PI * 2);
      g.fill();
    }
    g.globalAlpha = 1;
  }
}

/** Birds crossing the morning sky, and specks of pollen drifting in the light. */
function morning(g: G, W: number, H: number, t: number, calm: boolean) {
  for (let i = 0; i < 4; i++) {
    const k = calm ? 0.3 + i * 0.15 : (t * (0.03 + i * 0.006) + i * 0.27) % 1;
    const x = -20 + k * (W + 40);
    const y = 40 + i * 14 + Math.sin(t * 0.8 + i) * 4;
    const flap = calm ? 0 : Math.sin(t * 9 + i * 2) > 0 ? 1 : 0;
    px(g, x, y, 1, 1, "#3a4a5a");
    px(g, x - 2, y - flap, 2, 1, "#3a4a5a");
    px(g, x + 1, y - flap, 2, 1, "#3a4a5a");
  }
  for (let i = 0; i < 16; i++) {
    const x = (hash(i, 21) * W + (calm ? 0 : t * (4 + (i % 3)))) % W;
    const y = H * 0.45 + hash(i, 22) * H * 0.45 + (calm ? 0 : Math.sin(t * 0.7 + i * 2) * 6);
    px(g, x, y, 1, 1, i % 3 ? "#fff6c8" : "#ffffff");
  }
}

/** Paint the chosen background. */
export function selectBackdrop(
  g: G,
  W: number,
  H: number,
  kind: SelectBackdrop,
  t: number,
  calm = false,
) {
  if (kind === "vista") {
    modeVista(g, W, H, t, calm);
    g.globalAlpha = 0.5;
    px(g, 0, 0, W, H, "#0e1024");
    g.globalAlpha = 1;
    return;
  }
  const key = `${kind}:${W}x${H}`;
  let c = cache.get(key);
  if (!c) {
    c = kind === "dawn" ? paintDawn(W, H) : paintRuins(W, H);
    cache.set(key, c);
  }
  g.drawImage(c, 0, 0);
  if (kind === "dawn") morning(g, W, H, t, calm);
  else torches(g, W, H, t, calm);
}
