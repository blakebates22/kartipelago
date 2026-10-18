/**
 * The menu art kit: small hand-made pixel textures, painted in code (original; nothing
 * traced or extracted), and the nine-slice frames that turn them into panels and
 * buttons of any size.
 *
 *   wood       64×32  carved, grained sign wood (buttons, signs, the pause menu)
 *   parchment  64×64  warm cream paper (maps, results, track info)
 *   stone      32×32  weathered blocks with carved grooves (options, music player)
 *   frames     16×16  gold / ink / mossy-stone borders, sliced 5 px from each edge
 *
 * Palette: coral, turquoise, leaf, gold, sky and violet accents over warm woods.
 */

export const PAL = {
  coral: "#f0645a",
  turquoise: "#2ec4b6",
  leaf: "#6abe30",
  gold: "#f7c948",
  sky: "#5fb8f0",
  violet: "#9b7ede",
  ink: "#3a2414",
  inkSoft: "#6b4a2a",
  cream: "#fff4d6",
  white: "#ffffff",
  shadow: "#1d120a",
  night: "#14213d",
} as const;

/** The accent colours in a fixed order (track tiles, logo letters...). */
export const ACCENTS = [PAL.coral, PAL.gold, PAL.leaf, PAL.turquoise, PAL.sky, PAL.violet];

function rng(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };
}

function canvas(w: number, h: number) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return { c, g: c.getContext("2d")! };
}

function paint(w: number, h: number, shade: (x: number, y: number) => string) {
  const { c, g } = canvas(w, h);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      g.fillStyle = shade(x, y);
      g.fillRect(x, y, 1, 1);
    }
  return c;
}

/** Value noise that tiles over w×h. */
function tilingNoise(w: number, h: number, cells: number, seed: number) {
  const r = rng(seed);
  const grid = Array.from({ length: cells * cells }, () => r());
  const at = (i: number, j: number) =>
    grid[(((j % cells) + cells) % cells) * cells + (((i % cells) + cells) % cells)]!;
  return (x: number, y: number) => {
    const fx = (x / w) * cells;
    const fy = (y / h) * cells;
    const i = Math.floor(fx);
    const j = Math.floor(fy);
    const u = fx - i;
    const v = fy - j;
    const s = (t: number) => t * t * (3 - 2 * t);
    const a = at(i, j) + (at(i + 1, j) - at(i, j)) * s(u);
    const b = at(i, j + 1) + (at(i + 1, j + 1) - at(i, j + 1)) * s(u);
    return a + (b - a) * s(v);
  };
}

const pick = (list: string[], v: number) =>
  list[Math.max(0, Math.min(list.length - 1, Math.floor(v * list.length)))]!;

let cache: ReturnType<typeof build> | undefined;
/** The textures, made on first use. */
export function uiTextures() {
  return (cache ??= build());
}

function build() {
  // Wood: long wavy grain, a knot, four shades.
  const woodShades = ["#5a3318", "#7a4522", "#93592c", "#a96a36", "#bb7b40"];
  const wn = tilingNoise(64, 32, 4, 11);
  const wood = paint(64, 32, (x, y) => {
    const grain =
      Math.sin(y * 1.15 + Math.sin(x * (Math.PI / 16)) * 1.6 + wn(x, y) * 3) * 0.5 + 0.5;
    const kx = x - 44;
    const ky = (y - 14) * 2.2;
    const knot = Math.hypot(kx, ky);
    let v = 0.25 + grain * 0.5 + wn(x * 2, y * 2) * 0.2;
    if (knot < 9) v = 0.18 + 0.5 * ((Math.sin(knot * 1.3) + 1) / 2) * 0.6;
    if (y % 16 === 0) v = 0.02; // a plank seam
    return pick(woodShades, v);
  });

  // Parchment: warm cream, faint blotches and fibres.
  const pShades = ["#e2c88f", "#ead5a2", "#f1e1b8", "#f6e9c8"];
  const pn = tilingNoise(64, 64, 5, 23);
  const pr = rng(5);
  const fibres = new Set<number>();
  for (let i = 0; i < 26; i++) {
    const x0 = Math.floor(pr() * 64);
    const y0 = Math.floor(pr() * 64);
    for (let k = 0; k < 3 + pr() * 4; k++)
      fibres.add(((y0 + Math.floor(k * 0.4)) % 64) * 64 + ((x0 + k) % 64));
  }
  const parchment = paint(64, 64, (x, y) => {
    if (fibres.has(y * 64 + x)) return "#d9bd84";
    return pick(pShades, 0.15 + pn(x, y) * 0.7 + pn(x * 3, y * 3) * 0.15);
  });

  // Stone: offset blocks with carved grooves, speckles.
  const sShades = ["#6f6b62", "#837f74", "#959185", "#a8a497"];
  const sn = tilingNoise(32, 32, 4, 31);
  const stone = paint(32, 32, (x, y) => {
    const row = Math.floor(y / 16);
    const bx = (x + (row % 2) * 8) % 16;
    const by = y % 16;
    if (by === 0 || bx === 0) return "#4c4943"; // groove
    if (by === 1 || bx === 1) return "#b8b4a6"; // its lit edge
    if (by === 15 || bx === 15) return "#5e5a52";
    return pick(sShades, 0.2 + sn(x, y) * 0.55 + sn(x * 4, y * 4) * 0.25);
  });

  return {
    wood,
    parchment,
    stone,
    frames: {
      gold: frame(["#2a1606", "#ffe7a0", "#f2b733", "#a8701a", "#4a2a12"], "rivets"),
      ink: frame(["#3a2414", "#fff4d6", "#d9bd84", "#c4a26a", "#e6cf9c"], "curls"),
      stone: frame(["#2e2c28", "#c9c5b6", "#8f8b7f", "#5e5a52", "#3d3a34"], "moss"),
      dark: frame(["#0b0806", "#6a5a48", "#3a2f25", "#241c15", "#1a140f"], "plain"),
    },
  };
}

/**
 * A 16×16 frame for nine-slicing (5 px borders): outline, light bevel, mid, dark
 * bevel, inner edge; plus a corner decoration.
 */
function frame(
  c: [string, string, string, string, string],
  deco: "rivets" | "curls" | "moss" | "plain",
) {
  const { c: cv, g } = canvas(16, 16);
  const [outline, light, mid, dark, inner] = c;
  const rect = (x: number, y: number, w: number, h: number, col: string) => {
    g.fillStyle = col;
    g.fillRect(x, y, w, h);
  };
  rect(0, 0, 16, 16, outline);
  rect(1, 1, 14, 14, mid);
  rect(1, 1, 14, 1, light);
  rect(1, 1, 1, 14, light);
  rect(1, 14, 14, 1, dark);
  rect(14, 1, 1, 14, dark);
  rect(3, 3, 10, 10, outline);
  rect(4, 4, 8, 8, inner);
  g.clearRect(5, 5, 6, 6); // the centre is filled by the panel's own texture
  // Round the outer corners.
  for (const [x, y] of [
    [0, 0],
    [15, 0],
    [0, 15],
    [15, 15],
  ] as const)
    g.clearRect(x, y, 1, 1);
  if (deco === "rivets")
    for (const [x, y] of [
      [1, 1],
      [13, 1],
      [1, 13],
      [13, 13],
    ] as const) {
      rect(x, y, 2, 2, "#fff3c4");
      rect(x + 1, y + 1, 1, 1, "#b8811e");
    }
  if (deco === "curls")
    for (const [x, y] of [
      [1, 1],
      [12, 1],
      [1, 12],
      [12, 12],
    ] as const) {
      rect(x, y, 3, 3, outline);
      rect(x + 1, y + 1, 1, 1, light);
    }
  if (deco === "moss") {
    rect(1, 1, 4, 1, "#6aa63a");
    rect(1, 2, 2, 1, "#4f8a2c");
    rect(1, 3, 1, 1, "#4f8a2c");
    rect(11, 1, 4, 1, "#7fbe4a");
    rect(13, 2, 2, 1, "#5a9634");
  }
  return cv;
}

export type FrameKind = "gold" | "ink" | "stone" | "dark";
export type FillKind = "wood" | "parchment" | "stone" | "none" | string;

/**
 * A panel: fill (tiled texture or a colour) with a nine-sliced frame. Coordinates in
 * logical pixels.
 */
export function panel(
  g: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  fill: FillKind,
  frameKind: FrameKind = "gold",
) {
  const t = uiTextures();
  x = Math.round(x);
  y = Math.round(y);
  w = Math.round(w);
  h = Math.round(h);
  if (fill !== "none") {
    const tex =
      fill === "wood"
        ? t.wood
        : fill === "parchment"
          ? t.parchment
          : fill === "stone"
            ? t.stone
            : undefined;
    if (tex) {
      const pat = g.createPattern(tex, "repeat")!;
      pat.setTransform(new DOMMatrix().translate(x, y));
      g.fillStyle = pat;
    } else g.fillStyle = fill;
    g.fillRect(x + 3, y + 3, w - 6, h - 6);
  }
  nineSlice(g, t.frames[frameKind], 5, x, y, w, h);
}

/** Draw `src` stretched to w×h keeping its `b`-pixel borders unscaled. */
export function nineSlice(
  g: CanvasRenderingContext2D,
  src: HTMLCanvasElement,
  b: number,
  x: number,
  y: number,
  w: number,
  h: number,
) {
  const sw = src.width;
  const sh = src.height;
  const cw = sw - 2 * b;
  const ch = sh - 2 * b;
  const iw = Math.max(0, w - 2 * b);
  const ih = Math.max(0, h - 2 * b);
  // corners
  g.drawImage(src, 0, 0, b, b, x, y, b, b);
  g.drawImage(src, sw - b, 0, b, b, x + w - b, y, b, b);
  g.drawImage(src, 0, sh - b, b, b, x, y + h - b, b, b);
  g.drawImage(src, sw - b, sh - b, b, b, x + w - b, y + h - b, b, b);
  // edges (stretched: they're uniform along their length)
  if (iw > 0) {
    g.drawImage(src, b, 0, cw, b, x + b, y, iw, b);
    g.drawImage(src, b, sh - b, cw, b, x + b, y + h - b, iw, b);
  }
  if (ih > 0) {
    g.drawImage(src, 0, b, b, ch, x, y + b, b, ih);
    g.drawImage(src, sw - b, b, b, ch, x + w - b, y + b, b, ih);
  }
}

/** A pulsing highlight round something focused. */
export function focusRing(
  g: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  t: number,
) {
  const pulse = 0.55 + 0.45 * Math.sin(t * 7);
  g.globalAlpha = pulse;
  g.fillStyle = "#fffbe0";
  g.fillRect(Math.round(x) - 2, Math.round(y) - 2, Math.round(w) + 4, 1);
  g.fillRect(Math.round(x) - 2, Math.round(y + h) + 1, Math.round(w) + 4, 1);
  g.fillRect(Math.round(x) - 2, Math.round(y) - 2, 1, Math.round(h) + 4);
  g.fillRect(Math.round(x + w) + 1, Math.round(y) - 2, 1, Math.round(h) + 4);
  g.globalAlpha = 1;
}
