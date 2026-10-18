/**
 * The speedometer in the bottom-right corner, drawn as pixel art: a wooden barrel dial
 * with metal bands and a palm leaf, a red star needle, a digital readout and a wooden
 * BOOST sign.
 *
 * Every pixel is set by hand on a tiny canvas (W x H) that the page scales up by a whole
 * number with no smoothing, so the pixels stay crisp and square. The still parts are
 * painted once; the coloured blocks, needle, readout and chevrons are repainted only
 * when what they show changes.
 *
 * It only displays what it is given (see speedo.ts for the numbers): the needle and the
 * readout follow the kart's true speed with no smoothing, and the chevrons on the sign
 * show how much of the current boost is left.
 */
import { DIAL_SWEEP_DEG } from "./speedo";

export interface SpeedoFrame {
  /** The unitless number to show. */
  value: number;
  /** Needle angle, degrees clockwise from straight up. */
  needleDeg: number;
  /** The last number on the dial (for lighting the coloured blocks). */
  dialMax: number;
  /** Lit chevrons, 0..4. */
  chevrons: number;
  /** Chevron colour (the exhaust colour of the boost). */
  color: string;
  /** The end of an enhanced boost: chevrons cycle through the rainbow. */
  rainbow: boolean;
  /** An enhanced boost is running: the sign's lettering lights up. */
  enhanced: boolean;
}

/** Art size in pixels. */
const W = 124;
const H = 96;
/** Dial centre, barrel radius, dial-face radius. */
const CX = 48;
const CY = 47;
const R_OUT = 46;
const R_DIAL = 36;
const BLOCKS = 24;
const CHEVRONS = 4;

// ------------------------------------------------------------------ palette

const PAL = {
  ink: "#24140a",
  woodHi: "#c98a4b",
  wood: "#a5662f",
  woodAlt: "#93592a",
  woodLo: "#6f4220",
  grain: "#5a3418",
  metalHi: "#e3e8eb",
  metal: "#a9b1b7",
  metalLo: "#6d757c",
  metalInk: "#2c3136",
  cream: "#fbf0d2",
  creamLo: "#ead6a4",
  creamRim: "#d9bf88",
  navy: "#24305a",
  blockOff: "#e6d3a5",
  red: "#e23b2e",
  redHi: "#ff8f78",
  redInk: "#5a120c",
  blue: "#2f6fd6",
  blueHi: "#6fa5f2",
  star: "#ffd23f",
  starLo: "#d99a1b",
  screen: "#1a1722",
  screenRim: "#3b2412",
  digit: "#ffd23f",
  digitLo: "#e08f17",
  leaf: "#4fb34a",
  leafLo: "#2f8a35",
  leafInk: "#1d4d20",
  chevOff: "#2b3346",
  chevOffHi: "#36405a",
} as const;

/** Coloured blocks round the dial, bottom left to bottom right. */
const BLOCK_COLORS = [
  ["#3fbf3f", "#a6e39a"],
  ["#8fd13a", "#cdeea0"],
  ["#f2c230", "#f7e2a0"],
  ["#f28a22", "#f5c79a"],
  ["#e23b2e", "#f0b0a6"],
] as const;

// ------------------------------------------------------------------ pixel fonts

/** 3x5 digits for the dial numbers. */
const SMALL: Record<string, string[]> = {
  "0": ["111", "101", "101", "101", "111"],
  "1": ["010", "110", "010", "010", "111"],
  "2": ["111", "001", "111", "100", "111"],
  "3": ["111", "001", "111", "001", "111"],
  "4": ["101", "101", "111", "001", "001"],
  "5": ["111", "100", "111", "001", "111"],
  "6": ["111", "100", "111", "101", "111"],
  "7": ["111", "001", "001", "001", "001"],
  "8": ["111", "101", "111", "101", "111"],
  "9": ["111", "101", "111", "001", "111"],
};

/** 5x7 glyphs for the readout (drawn at double size) and the sign. */
const BIG: Record<string, string[]> = {
  "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
  "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
  "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
  "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
  "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
  "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
  "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
  "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
  "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
  "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
  B: ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
  O: ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
  S: ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
  T: ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
};

// ------------------------------------------------------------------ the raster

/** Pack "#rrggbb" into a little-endian RGBA pixel. */
function pack(hex: string, a = 255) {
  const n = parseInt(hex.slice(1), 16);
  return ((a << 24) | ((n & 0xff) << 16) | (n & 0xff00) | ((n >> 16) & 0xff)) >>> 0;
}

class Raster {
  readonly px = new Uint32Array(W * H);
  set(x: number, y: number, color: string) {
    x = Math.round(x);
    y = Math.round(y);
    if (x >= 0 && y >= 0 && x < W && y < H) this.px[y * W + x] = pack(color);
  }
  /** Colour every pixel whose centre passes the test (returning a colour, or nothing). */
  paint(
    x0: number,
    y0: number,
    x1: number,
    y1: number,
    f: (x: number, y: number) => string | undefined,
  ) {
    for (let y = Math.max(0, Math.floor(y0)); y <= Math.min(H - 1, Math.ceil(y1)); y++)
      for (let x = Math.max(0, Math.floor(x0)); x <= Math.min(W - 1, Math.ceil(x1)); x++) {
        const c = f(x + 0.5, y + 0.5);
        if (c) this.px[y * W + x] = pack(c);
      }
  }
  rect(x: number, y: number, w: number, h: number, color: string) {
    this.paint(x, y, x + w - 1, y + h - 1, () => color);
  }
  /** A glyph (rows of 0/1) at (x, y), each bit `scale` pixels square. */
  glyph(rows: string[], x: number, y: number, color: string, scale = 1) {
    rows.forEach((row, j) => {
      for (let i = 0; i < row.length; i++)
        if (row[i] === "1") this.rect(x + i * scale, y + j * scale, scale, scale, color);
    });
  }
  copyFrom(o: Raster) {
    this.px.set(o.px);
  }
}

/** Text width in pixels. */
const textWidth = (font: Record<string, string[]>, text: string, scale: number, gap: number) =>
  [...text].reduce((w, ch) => w + font[ch]![0]!.length * scale, 0) + gap * (text.length - 1);

function text(
  r: Raster,
  font: Record<string, string[]>,
  s: string,
  cx: number,
  y: number,
  color: string,
  opts: {
    scale?: number;
    gap?: number;
    bold?: boolean;
    outline?: string;
    shadow?: string;
    shade?: string;
  } = {},
) {
  const scale = opts.scale ?? 1;
  const gap = opts.gap ?? scale;
  const bold = opts.bold ? 1 : 0;
  const x0 = Math.round(cx - (textWidth(font, s, scale, gap) + bold) / 2);
  const each = (fn: (rows: string[], x: number) => void) => {
    let x = x0;
    for (const ch of s) {
      fn(font[ch]!, x);
      x += font[ch]![0]!.length * scale + gap;
    }
  };
  if (opts.outline)
    for (const [dx, dy] of [
      [-1, 0],
      [1 + bold, 0],
      [0, -1],
      [0, 1],
      [-1, -1],
      [1 + bold, 1],
      [-1, 1],
      [1 + bold, -1],
    ])
      each((g, x) => r.glyph(g, x + dx!, y + dy!, opts.outline!, scale));
  if (opts.shadow)
    each((g, x) => {
      r.glyph(g, x, y + 1, opts.shadow!, scale);
      if (bold) r.glyph(g, x + 1, y + 1, opts.shadow!, scale);
    });
  each((g, x) => {
    r.glyph(g, x, y, color, scale);
    if (bold) r.glyph(g, x + 1, y, color, scale);
    // The lower half of each glyph a shade darker, like lit pixel lettering.
    if (opts.shade) {
      const lower = g.map((row, j) =>
        j >= Math.ceil(g.length / 2) ? row : row.replace(/1/g, "0"),
      );
      r.glyph(lower, x, y, opts.shade, scale);
      if (bold) r.glyph(lower, x + 1, y, opts.shade, scale);
    }
  });
}

/** Angle in degrees, clockwise from straight up, of (x, y) around the dial centre. */
const angleOf = (x: number, y: number) => (Math.atan2(x - CX, CY - y) * 180) / Math.PI;
const rad = (deg: number) => (deg * Math.PI) / 180;

/** Rotate (x, y) into a frame at (ox, oy) pointing `deg` clockwise from up: u along, v across. */
function frame(x: number, y: number, ox: number, oy: number, deg: number) {
  const a = rad(deg);
  const dx = x - ox;
  const dy = y - oy;
  return { u: dx * Math.sin(a) - dy * Math.cos(a), v: dx * Math.cos(a) + dy * Math.sin(a) };
}

// ------------------------------------------------------------------ the still parts

function paintLeaf(r: Raster) {
  const fronds: [number, number, number][] = [
    [22, 30, 13],
    [92, 30, 12],
    [56, 36, 15],
  ];
  for (const [deg, len, width] of fronds) {
    const inside = (x: number, y: number, grow: number) => {
      const { u, v } = frame(x, y, 84, 26, deg);
      if (u < -1 || u > len + grow) return false;
      // Saw-toothed edges: the half-width dips every few pixels.
      const t = Math.max(0, Math.min(1, u / len));
      const half =
        (width / 2) * Math.sin(Math.PI * Math.pow(t, 0.8)) - (Math.floor(u) % 4 < 2 ? 0 : 1.2);
      return Math.abs(v) <= half + grow;
    };
    r.paint(60, 0, W - 1, 50, (x, y) => {
      if (inside(x, y, 0)) {
        const { v } = frame(x, y, 84, 26, deg);
        return Math.abs(v) < 0.7 ? PAL.leafInk : v < 0 ? PAL.leafLo : PAL.leaf;
      }
      return inside(x, y, 1) ? PAL.leafInk : undefined;
    });
  }
}

function paintBarrel(r: Raster) {
  const staves = 14;
  r.paint(CX - R_OUT - 1, CY - R_OUT - 1, CX + R_OUT + 1, CY + R_OUT + 1, (x, y) => {
    const d = Math.hypot(x - CX, y - CY);
    if (d > R_OUT + 0.5) return undefined;
    if (d > R_OUT - 0.7) return PAL.ink;
    if (d < R_DIAL + 1.5) return undefined;
    if (d < R_DIAL + 2.3) return PAL.ink; // the lip round the dial
    const a = angleOf(x, y);
    const k = ((a + 360 + 8) / (360 / staves)) % staves;
    const within = k - Math.floor(k);
    // Seams between staves.
    if (within < 0.09) return PAL.ink;
    // Light from the top left: brighter there, darker bottom right.
    const lit = (-(x - CX) - (y - CY)) / (d * Math.SQRT2);
    if (d > R_OUT - 2 && lit > 0.2) return PAL.woodHi;
    if (lit < -0.55) return PAL.woodLo;
    // A little grain on each stave.
    const g = Math.floor(k);
    if (Math.abs(d - (R_DIAL + 5 + (g % 3) * 1.5)) < 0.5 && within > 0.3 && within < 0.75)
      return PAL.grain;
    return g % 2 ? PAL.woodAlt : PAL.wood;
  });
  // Metal bands with rivets.
  for (const deg of [-118, -62, 82]) {
    r.paint(0, 0, W - 1, H - 1, (x, y) => {
      const { u, v } = frame(x, y, CX, CY, deg);
      if (u < R_DIAL - 0.5 || u > R_OUT + 2.5 || Math.abs(v) > 4.5) return undefined;
      if (u > R_OUT + 1.5 || u < R_DIAL + 0.5 || Math.abs(v) > 3.5) return PAL.metalInk;
      const rivet =
        Math.abs(v) < 1.2 &&
        (Math.abs(u - (R_DIAL + 3)) < 1.2 || Math.abs(u - (R_OUT - 1.5)) < 1.2);
      if (rivet) return PAL.metalHi;
      return v < -1.5 ? PAL.metalHi : v > 1.5 ? PAL.metalLo : PAL.metal;
    });
  }
}

function paintFace(r: Raster, dialMax: number) {
  r.paint(CX - R_DIAL, CY - R_DIAL, CX + R_DIAL, CY + R_DIAL, (x, y) => {
    const d = Math.hypot(x - CX, y - CY);
    if (d > R_DIAL + 1.5) return undefined;
    if (d > R_DIAL + 0.5) return PAL.creamRim;
    const lit = (-(x - CX) - (y - CY)) / (Math.max(1, d) * Math.SQRT2);
    if (d > R_DIAL - 3 && lit < -0.3) return PAL.creamLo;
    return PAL.cream;
  });
  // Major marks and their numbers.
  for (let k = 0; k <= 6; k++) {
    const deg = -DIAL_SWEEP_DEG / 2 + (k / 6) * DIAL_SWEEP_DEG;
    const a = rad(deg);
    const label = String(Math.round((k * dialMax) / 6));
    const lx = CX + 18.5 * Math.sin(a);
    const ly = CY - 18.5 * Math.cos(a);
    text(r, SMALL, label, lx, Math.round(ly - 2.5), PAL.navy);
  }
}

function paintScreen(r: Raster) {
  // Rounded dark screen with a wooden rim.
  const x0 = 28;
  const y0 = 65;
  const w = 41;
  const h = 20;
  r.paint(x0 - 1, y0 - 1, x0 + w, y0 + h, (x, y) => {
    const cx = Math.min(Math.max(x, x0 + 3), x0 + w - 3);
    const cy = Math.min(Math.max(y, y0 + 3), y0 + h - 3);
    const d = Math.hypot(x - cx, y - cy);
    if (d > 3.6) return undefined;
    if (d > 2.4) return PAL.ink;
    if (d > 1.4 && (x < x0 + 2 || y < y0 + 2 || x > x0 + w - 2 || y > y0 + h - 2))
      return PAL.screenRim;
    return PAL.screen;
  });
}

function paintSign(r: Raster) {
  const x0 = 78;
  const y0 = 64;
  const w = 45;
  const h = 31;
  r.paint(x0, y0, x0 + w - 1, y0 + h - 1, (x, y) => {
    const ix = x - x0;
    const iy = y - y0;
    const corner = (ix < 2 || ix > w - 2) && (iy < 2 || iy > h - 2);
    if (corner) return undefined;
    if (ix < 1 || iy < 1 || ix > w - 1 || iy > h - 1) return PAL.ink;
    if (Math.abs(iy - 11.5) < 0.5) return PAL.ink; // plank seam
    if (iy < 2.5) return PAL.woodHi;
    if (iy > h - 3) return PAL.woodLo;
    return iy < 11 ? PAL.wood : PAL.woodAlt;
  });
  for (const [x, y] of [
    [x0 + 3, y0 + 3],
    [x0 + w - 4, y0 + 3],
    [x0 + 3, y0 + h - 4],
    [x0 + w - 4, y0 + h - 4],
  ]) {
    r.set(x!, y!, PAL.metalHi);
  }
  // The dark window the chevrons sit in.
  r.rect(x0 + 4, y0 + 14, w - 8, h - 18, PAL.ink);
  r.rect(x0 + 5, y0 + 15, w - 10, h - 20, PAL.screen);
}

const SIGN_LABEL = { x: 100, y: 66 };

function paintHub(r: Raster) {
  r.paint(CX - 9, CY - 9, CX + 9, CY + 9, (x, y) => {
    const d = Math.hypot(x - CX, y - CY);
    if (d > 8.4) return undefined;
    if (d > 7.4) return PAL.redInk;
    if (d > 5.6) return x - CX + (y - CY) < -3 ? PAL.redHi : PAL.red;
    if (d > 4.8) return PAL.redInk;
    return x - CX + (y - CY) < -3 ? PAL.blueHi : PAL.blue;
  });
  // A yellow star in the middle.
  const star = ["0001000", "0011100", "1111111", "0111110", "0011100", "0110110", "0100010"];
  r.glyph(star, CX - 3, CY - 3, PAL.star);
  r.glyph(
    ["0000000", "0000000", "0000000", "0000000", "0000000", "0100010", "0100010"],
    CX - 3,
    CY - 3,
    PAL.starLo,
  );
}

// ------------------------------------------------------------------ moving parts

/** Each coloured block's pixels, so lighting them is a quick copy. */
function blockPixels() {
  const blocks: number[][] = Array.from({ length: BLOCKS }, () => []);
  const step = DIAL_SWEEP_DEG / BLOCKS;
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const d = Math.hypot(x + 0.5 - CX, y + 0.5 - CY);
      if (d < 27 || d > 32.5) continue;
      const a = angleOf(x + 0.5, y + 0.5) + DIAL_SWEEP_DEG / 2;
      if (a < 0 || a > DIAL_SWEEP_DEG) continue;
      const i = Math.floor(a / step);
      const within = a / step - i;
      if (within < 0.16 || within > 0.92) continue; // gaps between blocks
      blocks[Math.min(BLOCKS - 1, i)]!.push(y * W + x);
    }
  return blocks;
}

function paintNeedle(r: Raster, deg: number) {
  const len = 26;
  const tail = 5;
  const half = (u: number) => (u < 0 ? 2.4 : 3 * (1 - u / (len + 2)));
  const inside = (x: number, y: number, grow: number) => {
    const { u, v } = frame(x, y, CX, CY, deg);
    return u >= -tail - grow && u <= len + grow && Math.abs(v) <= half(u) + grow;
  };
  r.paint(CX - len - 3, CY - len - 3, CX + len + 3, CY + len + 3, (x, y) => {
    if (inside(x, y, 0)) {
      const { u, v } = frame(x, y, CX, CY, deg);
      return v < -0.4 && u > 1 && u < len - 3 ? PAL.redHi : PAL.red;
    }
    return inside(x, y, 1) ? PAL.redInk : undefined;
  });
}

/** A chevron 7 wide and 9 tall at (x, y). */
function paintChevron(r: Raster, x: number, y: number, color: string, hi: string) {
  for (let j = 0; j < 9; j++) {
    const off = 3 - Math.abs(j - 4) * 0.75;
    for (let i = 0; i < 4; i++) r.set(x + Math.round(off) + i, y + j, j < 3 ? hi : color);
  }
}

/** Lighter version of a colour, for the top of a lit chevron. */
function lighten(hex: string, k = 0.45) {
  const n = parseInt(hex.slice(1), 16);
  const c = [n >> 16, (n >> 8) & 0xff, n & 0xff].map((v) => Math.round(v + (255 - v) * k));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function hsl(h: number) {
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const v = 0.6 - 0.4 * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return Math.round(v * 255)
      .toString(16)
      .padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

// ------------------------------------------------------------------ the view

export function createSpeedometer(parent: HTMLElement) {
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  canvas.className = "speedo";
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "Speed");
  parent.appendChild(canvas);
  const g = canvas.getContext("2d")!;
  const image = g.createImageData(W, H);
  const out = new Raster();

  // Scale by a whole number so every art pixel is the same size on screen.
  const fit = () => {
    // About a fifth of the screen width: 2x on a laptop, 3x or 4x on big screens.
    const least = innerWidth < 640 ? 1 : 2;
    const scale = Math.max(least, Math.min(4, Math.round((innerWidth * 0.22) / W)));
    canvas.style.width = `${W * scale}px`;
    canvas.style.height = `${H * scale}px`;
  };
  fit();
  addEventListener("resize", fit);

  const blocks = blockPixels();
  const blockColor = (i: number, lit: boolean) => {
    const c =
      BLOCK_COLORS[
        Math.min(BLOCK_COLORS.length - 1, Math.floor((i / BLOCKS) * BLOCK_COLORS.length))
      ]!;
    return pack(lit ? c[0] : c[1]);
  };

  let under: Raster | undefined; // dial and frame, below the needle
  let over: Raster | undefined; // the hub, above the needle (transparent elsewhere)
  let builtFor = -1;
  const build = (dialMax: number) => {
    under = new Raster();
    paintLeaf(under);
    paintBarrel(under);
    paintFace(under, dialMax);
    paintScreen(under);
    paintSign(under);
    over = new Raster();
    paintHub(over);
    builtFor = dialMax;
  };

  let last = "";
  return {
    element: canvas,
    update(f: SpeedoFrame) {
      if (f.dialMax !== builtFor) build(f.dialMax);
      const lit = Math.min(BLOCKS, Math.ceil((f.value / f.dialMax) * BLOCKS - 1e-9));
      const needle = Math.round(f.needleDeg * 2) / 2;
      const shown = String(Math.round(f.value));
      const rainbowStep = f.rainbow ? Math.floor(performance.now() / 80) : 0;
      const key = `${lit}|${needle}|${shown}|${f.chevrons}|${f.color}|${rainbowStep}|${f.enhanced}`;
      if (key === last) return;
      last = key;

      out.copyFrom(under!);
      blocks.forEach((pixels, i) => {
        const c = blockColor(i, i < lit);
        for (const p of pixels) out.px[p] = c;
      });
      paintNeedle(out, needle);
      for (let i = 0; i < out.px.length; i++) if (over!.px[i]) out.px[i] = over!.px[i]!;

      text(out, BIG, shown, 48.5, 68, PAL.digit, {
        scale: 2,
        gap: 2,
        bold: true,
        shade: PAL.digitLo,
      });
      text(out, BIG, "BOOST", SIGN_LABEL.x, SIGN_LABEL.y, f.enhanced ? PAL.star : PAL.navy, {
        shadow: f.enhanced ? PAL.ink : PAL.woodHi,
      });
      for (let i = 0; i < CHEVRONS; i++) {
        const on = i < f.chevrons;
        const c = !on ? PAL.chevOff : f.rainbow ? hsl((rainbowStep * 40 + i * 70) % 360) : f.color;
        paintChevron(out, 85 + i * 8, 80, c, on ? lighten(c) : PAL.chevOffHi);
      }

      new Uint32Array(image.data.buffer).set(out.px);
      g.putImageData(image, 0, 0);
    },
  };
}

export type Speedometer = ReturnType<typeof createSpeedometer>;
