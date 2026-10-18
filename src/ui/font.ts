/**
 * Kartipelago's pixel font: an original 5×7 capital alphabet with numbers, punctuation
 * and a few symbols (arrows, a star, a note). Lower case is drawn as capitals, as on
 * many cartridge games of the era.
 *
 * Glyphs are drawn once into a per-colour atlas and then copied, so text is cheap to
 * redraw every frame.
 */

const G: Record<string, string> = {
  A: ".###. #...# #...# ##### #...# #...# #...#",
  B: "####. #...# #...# ####. #...# #...# ####.",
  C: ".###. #...# #.... #.... #.... #...# .###.",
  D: "####. #...# #...# #...# #...# #...# ####.",
  E: "##### #.... #.... ####. #.... #.... #####",
  F: "##### #.... #.... ####. #.... #.... #....",
  G: ".###. #...# #.... #.### #...# #...# .####",
  H: "#...# #...# #...# ##### #...# #...# #...#",
  I: "### .#. .#. .#. .#. .#. ###",
  J: "..### ...#. ...#. ...#. #..#. #..#. .##..",
  K: "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
  L: "#.... #.... #.... #.... #.... #.... #####",
  M: "#...# ##.## #.#.# #.#.# #...# #...# #...#",
  N: "#...# #...# ##..# #.#.# #..## #...# #...#",
  O: ".###. #...# #...# #...# #...# #...# .###.",
  P: "####. #...# #...# ####. #.... #.... #....",
  Q: ".###. #...# #...# #...# #.#.# #..#. .##.#",
  R: "####. #...# #...# ####. #.#.. #..#. #...#",
  S: ".#### #.... #.... .###. ....# ....# ####.",
  T: "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
  U: "#...# #...# #...# #...# #...# #...# .###.",
  V: "#...# #...# #...# #...# #...# .#.#. ..#..",
  W: "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
  X: "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
  Y: "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
  Z: "##### ....# ...#. ..#.. .#... #.... #####",
  "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
  "1": ".#. ##. .#. .#. .#. .#. ###",
  "2": ".###. #...# ....# ...#. ..#.. .#... #####",
  "3": "####. ....# ....# .###. ....# ....# ####.",
  "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
  "5": "##### #.... ####. ....# ....# #...# .###.",
  "6": "..##. .#... #.... ####. #...# #...# .###.",
  "7": "##### ....# ...#. ..#.. .#... .#... .#...",
  "8": ".###. #...# #...# .###. #...# #...# .###.",
  "9": ".###. #...# #...# .#### ....# ...#. .##..",
  ".": ". . . . . . #",
  ",": ".. .. .. .. .. .# #.",
  "!": "# # # # # . #",
  "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
  "'": "# # . . . . .",
  '"': "#.# #.# ... ... ... ... ...",
  ":": ". . # . . # .",
  ";": ".. .. .# .. .. .# #.",
  "-": ".... .... .... #### .... .... ....",
  "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
  "/": "....# ....# ...#. ..#.. .#... #.... #....",
  "(": ".# #. #. #. #. #. .#",
  "[": "## #. #. #. #. #. ##",
  "]": "## .# .# .# .# .# ##",
  ")": "#. .# .# .# .# .# #.",
  "%": "##..# ##..# ...#. ..#.. .#... #..## #..##",
  "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
  "#": ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
  "*": "..... #.#.# .###. ##### .###. #.#.# .....",
  "<": "...# ..#. .#.. #... .#.. ..#. ...#",
  ">": "#... .#.. ..#. ...# ..#. .#.. #...",
  "=": ".... .... #### .... #### .... ....",
  _: "..... ..... ..... ..... ..... ..... #####",
  "×": "..... #...# .#.#. ..#.. .#.#. #...# .....",
  "·": ". . . # . . .",
  "▲": "..... ..#.. .###. ##### ..... ..... .....",
  "▼": "..... ##### .###. ..#.. ..... ..... .....",
  "◀": "...# ..## .### #### .### ..## ...#",
  "▶": "#... ##.. ###. #### ###. ##.. #...",
  "★": "..#.. ..#.. ##### .###. .###. .#.#. #...#",
  "♪": "..##. ..#.# ..#.. ..#.. .##.. ###.. .#...",
  " ": "... ... ... ... ... ... ...",
};

export const GLYPH_H = 7;
const GAP = 1;

interface Glyph {
  w: number;
  rows: string[];
  /** x in the atlas */
  ax: number;
}

const glyphs = new Map<string, Glyph>();
let atlasW = 0;
for (const [ch, def] of Object.entries(G)) {
  const rows = def.split(" ");
  const w = rows[0]!.length;
  glyphs.set(ch, { w, rows, ax: atlasW });
  atlasW += w + 1;
}

const glyphOf = (ch: string) => glyphs.get(ch) ?? glyphs.get(ch.toUpperCase()) ?? glyphs.get("?")!;

/** Width of `text` in pixels at scale 1. */
export function textWidth(text: string): number {
  let w = 0;
  for (const ch of text) w += glyphOf(ch).w + GAP;
  return Math.max(0, w - GAP);
}

const atlases = new Map<string, HTMLCanvasElement>();
/** The whole alphabet drawn in one colour. */
function atlas(color: string): HTMLCanvasElement {
  let a = atlases.get(color);
  if (a) return a;
  a = document.createElement("canvas");
  a.width = atlasW;
  a.height = GLYPH_H;
  const g = a.getContext("2d")!;
  g.fillStyle = color;
  for (const gl of glyphs.values())
    gl.rows.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) if (row[x] === "#") g.fillRect(gl.ax + x, y, 1, 1);
    });
  atlases.set(color, a);
  return a;
}

export interface TextStyle {
  color?: string;
  /** Integer pixel scale. */
  scale?: number;
  align?: "left" | "center" | "right";
  /** A dark outline all round (chunky titles). */
  outline?: string;
  /** A drop shadow one pixel down-right. */
  shadow?: string;
}

/** Draw text with its top-left (or top-centre / top-right) at x, y. Returns its width. */
export function drawText(
  g: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  s: TextStyle = {},
) {
  const scale = s.scale ?? 1;
  const w = textWidth(text) * scale;
  let left = s.align === "center" ? x - w / 2 : s.align === "right" ? x - w : x;
  left = Math.round(left);
  y = Math.round(y);
  const run = (color: string, dx: number, dy: number) => {
    const a = atlas(color);
    let cx = left + dx;
    for (const ch of text) {
      const gl = glyphOf(ch);
      g.drawImage(a, gl.ax, 0, gl.w, GLYPH_H, cx, y + dy, gl.w * scale, GLYPH_H * scale);
      cx += (gl.w + GAP) * scale;
    }
  };
  if (s.outline) {
    const o = Math.max(1, Math.floor(scale / 2));
    for (const [dx, dy] of [
      [-o, 0],
      [o, 0],
      [0, -o],
      [0, o],
      [-o, -o],
      [o, -o],
      [-o, o],
      [o, o],
    ] as const)
      run(s.outline, dx, dy);
    run(s.outline, o, o + Math.max(1, Math.floor(scale / 2))); // a deeper drop under the outline
  }
  if (s.shadow) run(s.shadow, scale, scale);
  run(s.color ?? "#ffffff", 0, 0);
  return w;
}

/** Split text into lines no wider than `maxW` pixels (scale 1). */
export function wrap(text: string, maxW: number): string[] {
  const out: string[] = [];
  for (const para of text.split("\n")) {
    let line = "";
    for (const word of para.split(" ")) {
      const next = line ? `${line} ${word}` : word;
      if (textWidth(next) > maxW && line) {
        out.push(line);
        line = word;
      } else line = next;
    }
    out.push(line);
  }
  return out;
}

/** Every character the font draws (for tests). */
export const FONT_CHARS = [...glyphs.keys()];
export const FONT_ROWS = (ch: string) => glyphOf(ch).rows;
