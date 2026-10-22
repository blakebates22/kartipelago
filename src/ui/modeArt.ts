/**
 * The "Choose a mode" screen's art, painted in code at the UI's low resolution:
 *
 * - a vista from a stone terrace: the Prehistoric island on the left (volcano,
 *   waterfalls off green cliffs, a palm islet), open sea in the middle, and the desert
 *   mesas and a Dragon Kingdom pagoda with an arched bridge on the right, a serpent
 *   dragon gliding through the sky above it;
 * - a jungle tree with hanging vines framing the top left, and a friendly long-necked
 *   dinosaur on a ledge below it;
 * - a title plank hung on chains between two red dragon banners;
 * - the mode signboards: planks on posts with stone footings, vines over the corners,
 *   a checkered flag (Tracks) or a treasure map (Adventure) on top.
 *
 * The still parts are painted once into offscreen canvases; only the clouds, sea
 * glints, waterfall shimmer, dragon, banners and flag move. All original artwork.
 */
import { drawText, textWidth } from "./font";
import { PAL } from "./textures";

type G = CanvasRenderingContext2D;

/** Small deterministic hash in [0, 1). */
function hash(x: number, y: number, s = 0) {
  const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453;
  return v - Math.floor(v);
}

function canvas(w: number, h: number): [HTMLCanvasElement, G] {
  const c = document.createElement("canvas");
  c.width = Math.max(1, w);
  c.height = Math.max(1, h);
  const g = c.getContext("2d")!;
  g.imageSmoothingEnabled = false;
  return [c, g];
}

const px = (g: G, x: number, y: number, w: number, h: number, c: string) => {
  g.fillStyle = c;
  g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};

/** A horizontal span filled under a profile function, from `top(x)` down to `bottom`. */
function ridge(
  g: G,
  x0: number,
  x1: number,
  top: (x: number) => number,
  bottom: number,
  c: string,
) {
  g.fillStyle = c;
  for (let x = Math.floor(x0); x < x1; x++) {
    const y = Math.round(top(x));
    if (y < bottom) g.fillRect(x, y, 1, bottom - y);
  }
}

// ---------------------------------------------------------------- the vista

const SKY = ["#3f9be6", "#4ea6ea", "#5fb2ee", "#72bef1", "#88c9f3", "#a0d5f5", "#bce2f7"];

/** Where the horizon (the sea's far edge) sits. */
const HORIZON = 132;
/** The terrace's top edge. */
const TERRACE = 186;

function paintSky(W: number): HTMLCanvasElement {
  const [c, g] = canvas(W, HORIZON + 2);
  const band = Math.ceil(HORIZON / SKY.length);
  SKY.forEach((col, i) => px(g, 0, i * band, W, band + 1, col));
  // A pale sun low over the sea.
  px(g, W * 0.5 - 9, 70, 18, 18, "#fff6c2");
  px(g, W * 0.5 - 11, 74, 22, 10, "#fff6c2");
  return c;
}

/** Everything but the sky (transparent above the land). */
function paintVista(W: number, H: number): HTMLCanvasElement {
  const [c, g] = canvas(W, H);
  // Sea.
  px(g, 0, HORIZON, W, TERRACE - HORIZON, "#2f8fd0");
  px(g, 0, HORIZON, W, 2, "#8fd0f2");
  px(g, 0, HORIZON + 2, W, 6, "#3fa0dc");
  for (let i = 0; i < 70; i++) {
    const x = hash(i, 1) * W;
    const y = HORIZON + 6 + hash(i, 2) * (TERRACE - HORIZON - 8);
    px(g, x, y, 3 + hash(i, 3) * 6, 1, "#5db6e6");
  }

  // ---- left: the Prehistoric island
  const L = W * 0.3;
  // Distant volcano.
  const vx = W * 0.14;
  ridge(
    g,
    vx - 46,
    vx + 46,
    (x) => 92 + Math.abs(x - vx) * 0.85 - (Math.abs(x - vx) < 6 ? 0 : 0),
    HORIZON + 2,
    "#8e7d9c",
  );
  ridge(g, vx - 46, vx, (x) => 92 + Math.abs(x - vx) * 0.85 + 2, HORIZON + 2, "#a191ae");
  px(g, vx - 5, 91, 10, 2, "#e8613a");
  px(g, vx - 3, 93, 2, 6, "#e8613a");
  px(g, vx + 2, 93, 1, 9, "#d24a2e");
  // Green slopes on the volcano's foot.
  ridge(g, vx - 50, vx + 40, (x) => 118 + Math.sin(x * 0.12) * 3, HORIZON + 2, "#5f9a5a");
  // Cliffs with waterfalls, nearer.
  const cliffTop = (x: number) =>
    134 + Math.sin(x * 0.09) * 4 + (x > L - 20 ? (x - (L - 20)) * 1.2 : 0);
  ridge(g, 0, L + 10, cliffTop, TERRACE, "#7d6a52");
  for (let x = 0; x < L + 10; x++) {
    const y = Math.round(cliffTop(x));
    px(g, x, y, 1, 5, x % 7 < 4 ? "#4f9a3c" : "#5fae46");
    px(g, x, y + 5, 1, 2, "#3d7a32");
    if (hash(x, 9) < 0.25) px(g, x, y + 9 + hash(x, 8) * 20, 1, 3, "#66553f");
  }
  // Rock strata.
  for (let y = 0; y < 6; y++)
    for (let x = 0; x < L; x += 2)
      if (hash(x, y, 4) < 0.35) px(g, x, cliffTop(x) + 12 + y * 7, 2, 1, "#6a5944");
  // Palms along the cliff top.
  for (const [pxs, s] of [
    [0.06, 1.2],
    [0.11, 1],
    [0.2, 1.1],
  ] as const)
    palm(g, W * pxs, cliffTop(W * pxs) + 1, s);
  // A palm islet in the sea.
  const ix = W * 0.36;
  ridge(g, ix - 16, ix + 18, (x) => 150 + ((x - ix) / 17) ** 2 * 6, 158, "#e6cf8c");
  ridge(g, ix - 10, ix + 12, (x) => 146 + ((x - ix) / 11) ** 2 * 5, 154, "#4f9a3c");
  palm(g, ix - 3, 148, 0.9);
  palm(g, ix + 5, 149, 0.7);

  // ---- right: desert mesas and the Dragon Kingdom
  const R = W * 0.6;
  // Far mesas.
  const mesa = (x0: number, w: number, top: number, col: string, cap: string) => {
    ridge(
      g,
      x0,
      x0 + w,
      (x) =>
        top + (x < x0 + 4 ? (x0 + 4 - x) * 3 : 0) + (x > x0 + w - 4 ? (x - (x0 + w - 4)) * 3 : 0),
      HORIZON + 2,
      col,
    );
    px(g, x0 + 3, top, w - 6, 2, cap);
  };
  mesa(R + 6, 18, 104, "#d88a5a", "#e8a676");
  mesa(R + 34, 12, 96, "#cf7d50", "#e8a676");
  mesa(R + 56, 22, 108, "#d88a5a", "#eab07e");
  // Spires.
  for (const [sx, sh] of [
    [R + 28, 30],
    [R + 50, 40],
    [R + 84, 34],
  ] as const) {
    ridge(g, sx - 5, sx + 6, (x) => HORIZON - sh + Math.abs(x - sx) * 2.4, HORIZON + 2, "#c26e44");
    px(g, sx - 1, HORIZON - sh, 2, 2, "#e09468");
  }
  // Near red canyon wall with terraces, stepping up to the right.
  // Stepped terraces climbing to the right.
  const wallTop = (x: number) =>
    150 - Math.floor(Math.max(0, x - (W - 132)) / 30) * 11 + Math.round(Math.sin(x * 0.2) * 1.5);
  ridge(g, R - 10, W, wallTop, TERRACE, "#b4613a");
  for (let x = Math.floor(R - 10); x < W; x++) {
    const y = Math.round(wallTop(x));
    px(g, x, y, 1, 2, "#e09468");
    for (let k = 1; k < 9; k++) {
      // Strata: soft darker bands with lighter ledges, and a few cracks.
      px(
        g,
        x,
        y + k * 9 + Math.round(Math.sin(x * 0.05 + k) * 1.5),
        1,
        2,
        k % 2 ? "#a3552f" : "#c06c42",
      );
      if (hash(x, k, 7) < 0.2) px(g, x, y + k * 9 + 4, 1, 3, "#94502f");
    }
  }
  // A waterfall down the red wall.
  px(g, W - 70, wallTop(W - 70), 5, TERRACE - wallTop(W - 70), "#bfe6f7");
  px(g, W - 69, wallTop(W - 70), 1, TERRACE - wallTop(W - 70), "#ffffff");
  // Pagodas on the high terraces.
  pagoda(g, W - 16, wallTop(W - 16), 1.3);
  pagoda(g, W - 46, wallTop(W - 46), 0.95);
  pagoda(g, W - 76, wallTop(W - 76), 0.75);
  pagoda(g, W - 108, wallTop(W - 108), 0.6);
  // An arched bridge from the lowest terrace to the cliff.
  arches(g, W - 132, W - 104, wallTop(W - 104) + 4);

  // ---- the jungle tree, top left
  const tx = 14;
  px(g, tx - 6, 0, 13, TERRACE + 4, "#6b4424");
  px(g, tx - 6, 0, 3, TERRACE + 4, "#835632");
  px(g, tx + 4, 0, 3, TERRACE + 4, "#4f301a");
  for (let y = 10; y < TERRACE; y += 9) px(g, tx - 4 + (y % 3), y, 5, 1, "#4f301a");
  // Roots.
  for (let k = -3; k <= 3; k++) px(g, tx + k * 3, TERRACE - 2 + Math.abs(k), 3, 6, "#5a3a1e");
  // Canopy blobs.
  const leaves = ["#2f6e2c", "#3d8a34", "#4fa23e", "#64b84a"];
  for (let i = 0; i < 46; i++) {
    const cx = -6 + hash(i, 21) * 92;
    const cy = -8 + hash(i, 22) * 42 + (cx > 60 ? (cx - 60) * 0.2 : 0);
    const r = 7 + hash(i, 23) * 9;
    for (let y = -r; y < r; y++) {
      const half = Math.sqrt(r * r - y * y);
      const shade =
        leaves[Math.min(3, Math.max(0, Math.floor(((-y / r + 1) / 2) * 3 + hash(i, 24))))]!;
      px(g, cx - half, cy + y, half * 2, 1, shade);
    }
  }
  // Hanging vines.
  for (let i = 0; i < 9; i++) {
    const vx2 = 6 + i * 9 + hash(i, 31) * 4;
    const len = 18 + hash(i, 32) * 34;
    for (let y = 0; y < len; y++) {
      px(g, vx2 + Math.sin(y * 0.3 + i) * 1.2, 30 + y, 1, 1, "#2f6e2c");
      if (y % 5 === 2) px(g, vx2 + 1 + Math.sin(y * 0.3 + i) * 1.2, 30 + y, 2, 1, "#4fa23e");
    }
  }

  // ---- the terrace
  px(g, 0, TERRACE, W, H - TERRACE, "#b9a27e");
  // Flagstones in rows that widen towards the viewer.
  let y = TERRACE + 2;
  let row = 0;
  while (y < H) {
    const rh = 5 + row * 2;
    const bw = 20 + row * 7;
    const off = (row % 2) * (bw / 2);
    for (let x = -off; x < W; x += bw) {
      const shade = ["#c4ae88", "#b49c76", "#cbb791", "#ab946f"][Math.floor(hash(x, row, 5) * 4)]!;
      px(g, x + 1, y, bw - 2, rh - 1, shade);
      px(g, x + 1, y, bw - 2, 1, "#d8c6a2");
    }
    px(g, 0, y + rh - 1, W, 1, "#8a7556");
    y += rh;
    row++;
  }
  // Low stone walls at both ends, ferns.
  stoneWall(g, 0, TERRACE - 14, 74, 20);
  stoneWall(g, W - 70, TERRACE - 10, 70, 16);
  for (const fx of [70, 92, W * 0.5 - 90, W * 0.5 + 84, W - 80, W - 30]) fern(g, fx, TERRACE + 3);
  return c;
}

function palm(g: G, x: number, y: number, s: number) {
  for (let i = 0; i < 16 * s; i++)
    px(g, x + Math.sin(i / 7) * 2, y - i, 2, 1, i % 4 ? "#7a4f2a" : "#94643a");
  const top = y - 16 * s;
  for (const [dx, dy] of [
    [-9, 3],
    [9, 3],
    [-6, -2],
    [6, -2],
    [0, -5],
    [-3, 5],
  ] as const)
    for (let k = 0; k <= 8; k++) {
      const t = k / 8;
      px(
        g,
        x + 1 + dx * t * s,
        top + dy * t * s + 4 * t * t * s,
        2,
        1,
        k > 5 ? "#3d8a34" : "#2f7a2c",
      );
    }
}

function pagoda(g: G, x: number, y: number, s: number) {
  const tiers = 3;
  let w = 22 * s;
  let yy = y;
  // Base wall.
  px(g, x - w / 2, yy - 4 * s, w, 6 * s, "#e8dcc4");
  px(g, x - w / 2, yy - 4 * s, w, 1, "#ffffff");
  yy -= 4 * s;
  for (let t = 0; t < tiers; t++) {
    const bodyH = 6 * s;
    px(g, x - w / 2 + 3 * s, yy - bodyH, w - 6 * s, bodyH, "#b8322a");
    for (let k = 0; k < 3; k++)
      px(
        g,
        x - w / 2 + 5 * s + k * ((w - 10 * s) / 2),
        yy - bodyH + 2 * s,
        2 * s,
        2 * s,
        "#ffd36a",
      );
    yy -= bodyH;
    // Upturned roof.
    const rw = w + 6 * s;
    px(g, x - rw / 2, yy - 2 * s, rw, 2 * s, "#2f4f7a");
    px(g, x - rw / 2 - 1, yy - 3 * s, 2 * s, 1 * s + 1, "#2f4f7a");
    px(g, x + rw / 2 - 2 * s + 1, yy - 3 * s, 2 * s, 1 * s + 1, "#2f4f7a");
    px(g, x - rw / 2 + 2 * s, yy - 4 * s, rw - 4 * s, 2 * s, "#3d6496");
    px(g, x - rw / 2, yy, rw, 1, "#f7c948");
    yy -= 4 * s;
    w *= 0.75;
  }
  px(g, x - 1, yy - 4 * s, 2, 4 * s, "#f7c948");
}

function arches(g: G, x0: number, x1: number, y: number) {
  px(g, x0, y - 3, x1 - x0, 2, "#7a6c5a");
  px(g, x0, y - 1, x1 - x0, 5, "#a89a86");
  const n = 2;
  const span = (x1 - x0) / n;
  for (let a = 0; a < n; a++)
    for (let x = Math.floor(x0 + a * span); x < x0 + (a + 1) * span; x++) {
      const k = (x - x0 - a * span) / span;
      const open = Math.sin(k * Math.PI);
      if (k < 0.2 || k > 0.8) px(g, x, y + 4, 1, TERRACE - y - 4, "#968874");
      else px(g, x, y + 4, 1, 3 + (1 - open) * 8, "#968874");
    }
}

function stoneWall(g: G, x: number, y: number, w: number, h: number) {
  for (let r = 0; r * 6 < h; r++)
    for (let k = -(r % 2) * 5; k < w; k += 10) {
      const shade = ["#8f8a7c", "#a19c8d", "#7d786b"][Math.floor(hash(k + x, r, 3) * 3)]!;
      px(g, x + Math.max(0, k) + 1, y + r * 6, Math.min(9, w - Math.max(0, k) - 1), 5, shade);
      px(g, x + Math.max(0, k) + 1, y + r * 6, Math.min(9, w - Math.max(0, k) - 1), 1, "#bdb8a8");
    }
  for (let k = 0; k < w; k += 3) if (hash(k, x, 9) < 0.5) px(g, x + k, y - 1, 3, 2, "#4f9a3c");
}

function fern(g: G, x: number, y: number) {
  for (let a = -3; a <= 3; a++)
    for (let k = 0; k < 7; k++)
      px(
        g,
        x + a * k * 0.9,
        y - k * (1.4 - Math.abs(a) * 0.25),
        1,
        1,
        k > 3 ? "#5fae46" : "#3d8a34",
      );
}

// ---------------------------------------------------------------- moving bits

/** A serpent dragon gliding through the sky: a sine-wave body behind its head. */
function skyDragon(g: G, W: number, t: number, calm: boolean) {
  // Glides right to left across the right half of the sky, below the title.
  const x0 = W * 0.42;
  const span = W + 110 - x0;
  const k = calm ? 0.6 : (t * 0.035) % 1;
  const hx = W + 10 - span * k;
  const hy = 64 + Math.sin(t * 0.7) * 3;
  // Body: segments trailing to the right of the head.
  for (let i = 40; i >= 0; i--) {
    const sx = hx + 6 + i * 2.2;
    const sy = hy + 4 + Math.sin(i * 0.32 - t * 2.2) * 6 + i * 0.12;
    const r = i < 3 ? 3 : Math.max(1.2, 3.4 - i * 0.05);
    px(g, sx, sy - r, 3, r * 2, i % 3 ? "#5fb89a" : "#4aa086");
    px(g, sx, sy - r, 3, 1, "#f2d36a"); // golden crest
    px(g, sx, sy + r - 1, 3, 1, "#e8f4d8");
  }
  // Head.
  px(g, hx - 6, hy, 14, 7, "#5fb89a");
  px(g, hx - 9, hy + 3, 5, 4, "#5fb89a");
  px(g, hx - 9, hy + 6, 6, 1, "#e8f4d8");
  px(g, hx - 3, hy + 1, 2, 2, "#ffd36a");
  px(g, hx + 2, hy - 4, 2, 5, "#f2d36a"); // horns
  px(g, hx + 5, hy - 3, 2, 4, "#f2d36a");
  // Whiskers.
  for (let i = 0; i < 8; i++)
    px(g, hx - 10 - i, hy + 6 + Math.sin(i * 0.8 + t * 3) * 1.5, 1, 1, "#f2d36a");
}

function clouds(g: G, W: number, t: number, calm: boolean) {
  const drift = calm ? 0 : t * 3;
  for (let i = 0; i < 6; i++) {
    const w = 24 + (i % 3) * 12;
    const x = ((i * 89 + drift * (0.5 + i * 0.12)) % (W + 80)) - 40;
    const y = 14 + ((i * 29) % 58);
    px(g, x, y + 3, w, 4, "#ffffff");
    px(g, x + 3, y, w * 0.45, 4, "#ffffff");
    px(g, x + w * 0.4, y - 2, w * 0.35, 5, "#ffffff");
    px(g, x, y + 6, w, 1, "#d6ecf8");
  }
}

function waterfalls(g: G, W: number, t: number, calm: boolean) {
  const shift = calm ? 0 : Math.floor(t * 30);
  for (const fx of [W * 0.08, W * 0.17, W * 0.25]) {
    const top = 134 + Math.sin(fx * 0.09) * 4 + 4;
    const h = TERRACE - top;
    px(g, fx, top, 4, h, "#bfe6f7");
    for (let y = 0; y < h; y += 2)
      if ((y + shift) % 7 < 2) px(g, fx + ((y >> 1) % 3), top + y, 1, 2, "#ffffff");
    // Mist where it lands.
    px(g, fx - 3, TERRACE - 4, 10, 3, "#e6f6fd");
  }
}

function seaGlints(g: G, W: number, t: number, calm: boolean) {
  for (let i = 0; i < 16; i++) {
    const x = ((i * 61 + (calm ? 0 : t * 6)) % (W + 20)) - 10;
    const y = HORIZON + 10 + ((i * 13) % (TERRACE - HORIZON - 16));
    px(g, x, y, 5, 1, "#c4ecfb");
  }
}

let vistaCache:
  { W: number; H: number; sky: HTMLCanvasElement; land: HTMLCanvasElement } | undefined;

/** The whole background vista. */
export function modeVista(g: G, W: number, H: number, t: number, calm = false) {
  if (!vistaCache || vistaCache.W !== W || vistaCache.H !== H)
    vistaCache = { W, H, sky: paintSky(W), land: paintVista(W, H) };
  // Sky, then the clouds and the dragon, then the land in front of them.
  g.drawImage(vistaCache.sky, 0, 0);
  clouds(g, W, t, calm);
  skyDragon(g, W, t, calm);
  g.drawImage(vistaCache.land, 0, 0);
  waterfalls(g, W, t, calm);
  seaGlints(g, W, t, calm);
}

/** The friendly long-necked dinosaur on the ledge: blinks and bobs its head. */
export function terraceDino(g: G, x: number, y: number, t: number, calm = false) {
  const bob = calm ? 0 : Math.round(Math.sin(t * 1.6) * 1);
  const body = "#3f9a8a";
  const dark = "#2c7468";
  const belly = "#9fd8b8";
  // Tail.
  for (let i = 0; i < 18; i++)
    px(g, x - 18 - i, y + 6 + i * 0.35, 2, Math.max(1, 5 - i * 0.25), body);
  // Body.
  for (let k = -12; k <= 12; k++) {
    const hgt = Math.sqrt(1 - (k / 13) ** 2) * 11;
    px(g, x + k, y + 10 - hgt, 1, hgt * 2 - 4, body);
  }
  px(g, x - 10, y + 12, 20, 2, belly);
  // Legs.
  for (const lx of [-9, -4, 4, 9]) {
    px(g, x + lx, y + 12, 4, 10, lx < 0 ? dark : body);
    px(g, x + lx, y + 21, 5, 1, "#1f5a50");
  }
  // Neck up and forward, head.
  for (let i = 0; i < 20; i++)
    px(g, x + 8 + i * 0.55, y + 2 - i * 1.1 + (i > 14 ? bob : 0), 4, 4, body);
  const hx = x + 19;
  const hy = y - 22 + bob;
  px(g, hx - 1, hy, 10, 6, body);
  px(g, hx + 6, hy + 2, 5, 4, body);
  px(g, hx + 6, hy + 5, 5, 1, belly);
  const blink = !calm && t % 4 < 0.12;
  px(g, hx + 4, hy + 1, 2, blink ? 1 : 2, "#1a1a1a");
  if (!blink) px(g, hx + 4, hy + 1, 1, 1, "#ffffff");
  px(g, hx + 9, hy + 4, 2, 1, "#2a6a5c"); // smile
  // Spots.
  for (const [sx, sy] of [
    [-5, 2],
    [1, 0],
    [6, 3],
  ] as const)
    px(g, x + sx, y + sy, 2, 2, dark);
}

// ---------------------------------------------------------------- signs

/** A gold coiled-dragon emblem (the Dragon Kingdom's), about 9 px across. */
function emblem(g: G, cx: number, cy: number, col: string) {
  for (let a = 0; a < Math.PI * 3.2; a += 0.12) {
    const r = 1 + a * 0.42;
    px(g, cx + Math.cos(a) * r, cy + Math.sin(a) * r, 1, 1, col);
  }
  px(g, cx + 3, cy - 5, 2, 2, col);
}

/** A red banner hanging from a little crossbar, its tail swaying. */
export function banner(g: G, cx: number, y: number, h: number, t: number, calm = false) {
  const w = 18;
  px(g, cx - w / 2 - 4, y, w + 8, 3, "#6b4424");
  px(g, cx - w / 2 - 5, y - 1, 2, 5, "#c9a24a");
  px(g, cx + w / 2 + 3, y - 1, 2, 5, "#c9a24a");
  for (let yy = 0; yy < h; yy++) {
    const sway = calm ? 0 : Math.sin(t * 2 + yy * 0.12) * (yy / h) * 1.6;
    const tail = yy > h - 8 ? yy - (h - 8) : 0;
    const x0 = cx - w / 2 + sway;
    // A notched tail: two points.
    if (tail) {
      px(g, x0, y + 3 + yy, w / 2 - tail * 0.9, 1, "#b8322a");
      px(g, x0 + w / 2 + tail * 0.9, y + 3 + yy, w / 2 - tail * 0.9, 1, "#b8322a");
    } else {
      px(g, x0, y + 3 + yy, w, 1, yy % 9 === 0 ? "#a02a24" : "#c63a30");
      px(g, x0, y + 3 + yy, 1, 1, "#e8c45a");
      px(g, x0 + w - 1, y + 3 + yy, 1, 1, "#e8c45a");
    }
  }
  const sway = calm ? 0 : Math.sin(t * 2 + 3) * 0.6;
  emblem(g, cx + sway, y + 3 + h * 0.42, "#f2c94c");
}

/** Vines draped over a corner. */
function vines(g: G, x: number, y: number, dir: 1 | -1, len: number, seed: number) {
  for (let i = 0; i < len; i++) {
    const vx = x + dir * i * 0.9;
    const vy = y + Math.sin(i * 0.35 + seed) * 2;
    px(g, vx, vy, 2, 2, "#3d8a34");
    if (i % 3 === 0) px(g, vx + dir, vy - 2, 2, 2, "#5fae46");
  }
  for (let k = 0; k < 3; k++) {
    const dx = x + dir * (3 + k * 6);
    const dl = 5 + hash(k, seed) * 10;
    for (let yy = 0; yy < dl; yy++) px(g, dx + Math.sin(yy * 0.5) * 0.8, y + yy, 1, 1, "#2f6e2c");
    px(g, dx - 1, y + dl, 3, 2, "#5fae46");
  }
}

const boardCache = new Map<string, HTMLCanvasElement>();

/** A plank board, w × h, painted once: warm gold-brown when lit, grey-brown when not. */
function plankBoard(w: number, h: number, lit: boolean) {
  const key = `${w}x${h}${lit ? "L" : "D"}`;
  const hit = boardCache.get(key);
  if (hit) return hit;
  const [c, g] = canvas(w, h);
  const shades = lit
    ? ["#8a5428", "#a9692f", "#c27f3a", "#d69445", "#e3a654"]
    : ["#4f4436", "#5e5243", "#6d604f", "#7b6d5a", "#887a65"];
  const frame = lit ? ["#4a2a12", "#f2b733", "#ffe7a0"] : ["#2b241c", "#4f4436", "#7b6d5a"];
  const plank = Math.max(8, Math.floor((h - 8) / 4));
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const p = Math.floor((y - 4) / plank);
      const grain = Math.sin(x * 0.18 + p * 7 + Math.sin(x * 0.05 + p) * 2 + y * 0.9) * 0.5 + 0.5;
      const v = 0.2 + grain * 0.45 + hash(x >> 1, y, p) * 0.25 + ((y - 4) % plank < 2 ? 0.12 : 0);
      g.fillStyle = shades[Math.min(4, Math.floor(v * 5))]!;
      if ((y - 4) % plank === plank - 1) g.fillStyle = shades[0]!;
      g.fillRect(x, y, 1, 1);
    }
  // The frame: dark outer edge, a coloured rail, a bright inner line.
  g.fillStyle = frame[0]!;
  g.fillRect(0, 0, w, 2);
  g.fillRect(0, h - 2, w, 2);
  g.fillRect(0, 0, 2, h);
  g.fillRect(w - 2, 0, 2, h);
  g.fillStyle = frame[1]!;
  g.fillRect(2, 2, w - 4, 2);
  g.fillRect(2, h - 4, w - 4, 2);
  g.fillRect(2, 2, 2, h - 4);
  g.fillRect(w - 4, 2, 2, h - 4);
  g.fillStyle = frame[2]!;
  g.fillRect(4, 4, w - 8, 1);
  g.fillRect(4, 4, 1, h - 8);
  // Corner bolts.
  for (const [bx, by] of [
    [6, 6],
    [w - 9, 6],
    [6, h - 9],
    [w - 9, h - 9],
  ] as const) {
    g.fillStyle = "#2b241c";
    g.fillRect(bx, by, 3, 3);
    g.fillStyle = lit ? "#ffe7a0" : "#a8a090";
    g.fillRect(bx, by, 1, 1);
  }
  boardCache.set(key, c);
  return c;
}

/** The checkered flag on its pole, rippling. */
function checkeredFlag(g: G, x: number, y: number, t: number, calm: boolean) {
  // Pole, leaning.
  for (let i = 0; i < 28; i++) px(g, x + i * 0.3, y + 28 - i, 2, 1, "#5a3318");
  px(g, x + 7, y - 1, 3, 3, "#f2c94c");
  const fx = x + 9;
  const fy = y + 1;
  for (let cx = 0; cx < 24; cx++) {
    const wave = calm ? 0 : Math.sin(t * 5 - cx * 0.35) * 1.6;
    const droop = cx * 0.12;
    for (let cy = 0; cy < 16; cy++) {
      const dark = ((cx >> 2) + (cy >> 2)) % 2 === 0;
      px(g, fx + cx, fy + cy + wave + droop, 1, 1, dark ? "#1d1d1d" : "#f4f4f4");
    }
    px(g, fx + cx, fy + 16 + wave + droop, 1, 1, "#00000055");
  }
}

/** A rolled treasure map: parchment, a dotted trail and a red X. */
function mapScroll(g: G, x: number, y: number, t: number, dim: boolean) {
  const w = 34;
  const h = 22;
  px(g, x + 1, y + 2, w, h, "#00000040");
  px(g, x, y, w, h, dim ? "#d8c6a0" : "#efdcae");
  for (let i = 0; i < 18; i++)
    px(g, x + hash(i, 61) * w, y + hash(i, 62) * h, 2, 1, dim ? "#c8b48c" : "#dcc493");
  // Rolled ends.
  px(g, x - 3, y - 1, 4, h + 2, dim ? "#c9b48a" : "#e0c890");
  px(g, x - 3, y - 1, 1, h + 2, "#9c7f50");
  px(g, x + w - 1, y - 1, 4, h + 2, dim ? "#c9b48a" : "#e0c890");
  px(g, x + w + 2, y - 1, 1, h + 2, "#9c7f50");
  // Land blobs.
  px(g, x + 5, y + 5, 10, 6, "#a8c47a");
  px(g, x + 8, y + 10, 8, 5, "#a8c47a");
  px(g, x + 20, y + 12, 9, 6, "#a8c47a");
  // Mountains.
  for (const mx of [9, 14])
    for (let i = 0; i < 4; i++) px(g, x + mx - i, y + 4 + i, 2 * i + 1, 1, "#8a6a40");
  // A dotted trail to the X.
  const n = 9;
  const shown = Math.floor(((t * 0.8) % 1.5) * n);
  for (let i = 0; i <= Math.min(n, shown); i++)
    px(g, x + 8 + i * 2, y + 15 - Math.sin((i / n) * Math.PI) * 6, 1, 1, "#c0392b");
  const xx = x + 27;
  const xy = y + 13;
  for (let i = -2; i <= 2; i++) {
    px(g, xx + i, xy + i, 1, 1, "#c0392b");
    px(g, xx + i, xy - i, 1, 1, "#c0392b");
  }
}

export interface ModeBoard {
  label: string;
  sub: string;
  icon: "flag" | "map";
  focused: boolean;
  /** Not available yet: drawn weathered. */
  dim?: boolean;
}

/** One mode signboard with its posts, footings, vines and icon. */
export function modeBoard(
  g: G,
  x: number,
  y: number,
  w: number,
  h: number,
  b: ModeBoard,
  t: number,
  calm = false,
  ground = TERRACE + 12,
) {
  const lit = b.focused;
  // Posts and footings.
  for (const ox of [12, w - 20]) {
    px(g, x + ox, y - 6, 8, ground - y + 6, "#5a3318");
    px(g, x + ox, y - 6, 2, ground - y + 6, "#7a4522");
    px(g, x + ox - 1, y - 8, 10, 3, "#6b4424");
    stoneFooting(g, x + ox - 5, ground - 3);
  }
  // A soft glow behind the lit board.
  if (lit) {
    g.globalAlpha = 0.25 + (calm ? 0 : Math.sin(t * 4) * 0.08);
    px(g, x - 4, y - 4, w + 8, h + 8, "#ffe7a0");
    g.globalAlpha = 1;
  }
  g.drawImage(plankBoard(w, h, lit), Math.round(x), Math.round(y));
  vines(g, x + 2, y + 1, 1, 14, 1);
  vines(g, x + w - 4, y + 1, -1, 12, 2);
  // Icon.
  if (b.icon === "flag") checkeredFlag(g, x + w / 2 - 18, y + 4, t, calm);
  else mapScroll(g, x + w / 2 - 17, y + 8, t, Boolean(b.dim));
  // Words.
  const scale = textWidth(b.label) * 2 > w - 16 ? 1 : 2;
  drawText(g, b.label, x + w / 2, y + h - 30, {
    scale,
    color: lit ? "#fff4d6" : b.dim ? "#e6dccb" : PAL.cream,
    outline: PAL.shadow,
    align: "center",
  });
  drawText(g, b.sub, x + w / 2, y + h - 13, {
    color: lit ? "#fff4d6" : "#d8ccb4",
    shadow: PAL.shadow,
    align: "center",
  });
}

function stoneFooting(g: G, x: number, y: number) {
  px(g, x, y, 18, 9, "#7d786b");
  px(g, x + 1, y, 8, 4, "#a19c8d");
  px(g, x + 10, y, 7, 4, "#8f8a7c");
  px(g, x + 1, y + 5, 6, 3, "#8f8a7c");
  px(g, x + 8, y + 5, 9, 3, "#a19c8d");
  px(g, x, y, 18, 1, "#bdb8a8");
}

/** The title plank, hung on two chains, with a dragon banner either side. */
export function titlePlank(g: G, W: number, text: string, t: number, calm = false) {
  const scale = 3;
  const tw = textWidth(text) * scale;
  const w = tw + 36;
  const h = 34;
  const x = Math.round(W / 2 - w / 2);
  const y = 20 + (calm ? 0 : Math.round(Math.sin(t * 1.3) * 1));
  // Chains from the top of the screen.
  for (const cx of [x + 26, x + w - 30])
    for (let k = 0; k < y + 2; k += 4) {
      px(g, cx, k, 4, 3, "#8a8578");
      px(g, cx + 1, k + 1, 2, 1, "#4a463e");
      px(g, cx, k, 4, 1, "#c9c4b4");
    }
  // Banners.
  banner(g, x - 16, 8, 50, t, calm);
  banner(g, x + w + 16, 8, 50, t + 1.3, calm);
  // The plank (lit wood) and its words.
  g.drawImage(plankBoard(w, h, true), x, y);
  vines(g, x + 4, y + h - 3, 1, 10, 3);
  vines(g, x + w - 6, y + h - 3, -1, 16, 4);
  drawText(g, text, W / 2, y + 7, { scale, color: "#ffd84a", outline: "#3a1c08", align: "center" });
}
