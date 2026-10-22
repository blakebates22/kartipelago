/**
 * More of the "Choose a mode" screen's art (see modeArt.ts): the ancient ruins the
 * terrace is built from, the erupting volcano, and the dinosaurs that live round it.
 *
 * - Ruins: worn, cracked flagstones with moss in the joints, a few broken out, a carved
 *   glyph; a broken temple plinth on the left (a fallen column drum, a standing column
 *   snapped off) and a ruined archway on the right.
 * - The volcano: big and dark, a glowing crater, lava rivers down its flanks; live, a
 *   lava fountain, lava bombs arcing out and a rolling plume of smoke.
 * - Dinosaurs: a triceratops grazing on the right-hand ruins, a pair of pteranodons
 *   gliding across the sky, a small stegosaurus on the cliff top.
 *
 * All painted in code at the UI's low resolution; all original artwork.
 */
type G = CanvasRenderingContext2D;

function hash(x: number, y: number, s = 0) {
  const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453;
  return v - Math.floor(v);
}

const px = (g: G, x: number, y: number, w: number, h: number, c: string) => {
  g.fillStyle = c;
  g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};

/** A filled ellipse, row by row (crisp pixel edges). */
function ell(g: G, cx: number, cy: number, rx: number, ry: number, c: string) {
  for (let y = -Math.ceil(ry); y <= Math.ceil(ry); y++) {
    const k = 1 - (y / ry) ** 2;
    if (k <= 0) continue;
    const half = Math.sqrt(k) * rx;
    px(g, cx - half, cy + y, half * 2, 1, c);
  }
}

const STONE = ["#b8ad94", "#a89c82", "#c4b99e", "#9d917a", "#b0a48b"];
const STONE_LIGHT = "#d6ccb2";
const STONE_DARK = "#6f6552";
const GROUT = "#5f5646";
const MOSS = ["#4f8a3a", "#5f9e44", "#3d7230"];

// ---------------------------------------------------------------- the ruins

/**
 * The terrace floor: big old slabs of uneven size, worn and cracked, grass and moss
 * growing up through the joints, some sunken or broken out, lichen on others.
 */
export function ruinFloor(g: G, W: number, H: number, top: number) {
  px(g, 0, top, W, H - top, GROUT);
  let y = top + 1;
  let row = 0;
  while (y < H) {
    const rh = 6 + row * 3;
    let x = -hash(row, 3) * 30;
    let k = 0;
    while (x < W) {
      const id = k * 31 + row * 7;
      const bw = (24 + row * 10) * (0.6 + hash(k, row, 1) * 0.9);
      // Slabs sit at slightly different heights: some sunken a pixel or two.
      const sink = hash(id, 4) < 0.25 ? 1 : 0;
      const broken = hash(id, 2) < 0.1 && row > 0;
      if (broken) {
        // Broken out: earth, a few fragments, grass growing in the hole.
        px(g, x + 1, y, bw - 2, rh - 1, "#4a3a2a");
        for (let f = 0; f < 3; f++)
          px(
            g,
            x + 2 + hash(id, f) * (bw - 8),
            y + 1 + hash(id, f + 5) * (rh - 4),
            4,
            2,
            STONE[3]!,
          );
        grass(g, x + 2, x + bw - 2, y + rh - 1, id, 4);
      } else {
        const shade = STONE[Math.floor(hash(id, 5) * STONE.length)]!;
        const sy = y + sink;
        px(g, x + 1, sy, bw - 2, rh - 1 - sink, shade);
        px(g, x + 2, sy, bw - 4, 1, sink ? STONE[3]! : STONE_LIGHT);
        px(g, x + 1, y + rh - 2, bw - 2, 1, STONE_DARK);
        // Worn corners, knocked round.
        px(g, x + 1, sy, 2, 1, GROUT);
        px(g, x + bw - 3, sy, 2, 1, GROUT);
        // A crack wandering across.
        if (hash(id, 6) < 0.4) {
          let cx = x + 3 + hash(id, 7) * (bw - 8);
          for (let jj = 0; jj < rh - 2; jj++) {
            px(g, cx, sy + 1 + jj, 1, 1, STONE_DARK);
            cx += hash(id, jj) < 0.5 ? -1 : 1;
          }
        }
        // Lichen: a yellow-green blotch.
        if (hash(id, 13) < 0.25) {
          const lx = x + 3 + hash(id, 14) * (bw - 10);
          const ly = sy + 1 + hash(id, 15) * (rh - 4);
          for (let q = 0; q < 6; q++)
            px(
              g,
              lx + hash(id, 40 + q) * 6,
              ly + hash(id, 50 + q) * 3,
              1,
              1,
              q % 2 ? "#a8b26a" : "#8f9e58",
            );
        }
        if (hash(id, 8) < 0.06 && bw > 22 && rh > 8)
          glyph(g, x + bw / 2, sy + rh / 2 - 1, STONE_DARK);
      }
      // Grass and moss coming up through the joint.
      if (hash(id, 9) < 0.5) grass(g, x - 1, x + 2, y + rh - 1, id + 3, 3);
      if (hash(id, 11) < 0.35) px(g, x + hash(id, 12) * bw, y + rh - 1, 4, 1, MOSS[(k + 1) % 3]!);
      x += bw;
      k++;
    }
    y += rh;
    row++;
  }
  // Rubble: chips of fallen stone here and there.
  for (let i = 0; i < 16; i++) {
    const rx = hash(i, 41) * W;
    const ry = top + 4 + hash(i, 42) * (H - top - 8);
    px(g, rx, ry, 3, 2, STONE[i % STONE.length]!);
    px(g, rx, ry, 3, 1, STONE_LIGHT);
    px(g, rx + 1, ry + 2, 2, 1, GROUT);
  }
}

/** Blades of grass from x0 to x1 standing on `base`, up to `tall` pixels. */
function grass(g: G, x0: number, x1: number, base: number, seed: number, tall: number) {
  for (let x = x0; x < x1; x++)
    if (hash(x, seed, 7) < 0.55) {
      const h = 1 + Math.floor(hash(x, seed, 8) * tall);
      px(g, x, base - h, 1, h, MOSS[Math.floor(hash(x, seed, 9) * 3)]!);
    }
}

/** A carved spiral, a few pixels across. */
function glyph(g: G, cx: number, cy: number, c: string) {
  for (let i = 0; i < 26; i++) {
    const a = i * 0.55;
    const r = 0.4 + i * 0.11;
    px(g, cx + Math.cos(a) * r * 1.4, cy + Math.sin(a) * r, 1, 1, c);
  }
}

/** A block of weathered stone: shaded, chipped, mossy on top. */
function block(g: G, x: number, y: number, w: number, h: number, seed: number) {
  const shade = STONE[Math.floor(hash(seed, 1) * STONE.length)]!;
  px(g, x, y, w, h, shade);
  px(g, x, y, w, 1, STONE_LIGHT);
  px(g, x, y + h - 1, w, 1, STONE_DARK);
  px(g, x + w - 1, y, 1, h, STONE_DARK);
  // A chip off a corner.
  if (hash(seed, 2) < 0.6) px(g, x, y, 2, 2, GROUT);
  for (let i = 0; i < w; i += 2)
    if (hash(i, seed, 3) < 0.4) px(g, x + i, y - 1, 2, 1, MOSS[i % 3]!);
}

/**
 * A ruined wall: big irregular blocks, tumbled and gapped, its top broken (tallest at
 * `tallAt` across it, 0..1), overgrown with moss and creepers; fallen blocks at its foot.
 */
function ruinWall(
  g: G,
  x: number,
  base: number,
  w: number,
  maxH: number,
  tallAt: number,
  seed: number,
) {
  let cx = x;
  let i = 0;
  while (cx < x + w) {
    const bw = Math.min(x + w - cx, 14 + Math.floor(hash(i, seed) * 12));
    const u = (cx - x + bw / 2) / w;
    const height = Math.max(
      4,
      maxH * (1 - Math.abs(u - tallAt) * 1.5) * (0.6 + hash(i, seed, 2) * 0.5),
    );
    let yy = base;
    let r = 0;
    while (base - yy < height) {
      const bh = 5 + Math.floor(hash(i, r, seed) * 4);
      // Courses shift a little, and the odd block is missing.
      const jitter = Math.round((hash(i, r, seed + 1) - 0.5) * 3);
      if (r === 0 || hash(i, r, seed + 2) > 0.12)
        block(g, cx + jitter, yy - bh, bw - 1, bh, seed * 13 + i * 7 + r);
      yy -= bh;
      r++;
    }
    // Creepers hanging over the top.
    if (hash(i, seed, 5) < 0.5)
      for (let v = 0; v < 6 + hash(i, seed, 6) * 8; v++)
        px(g, cx + 2 + Math.sin(v * 0.6 + i) * 1.2, yy + v, 1, 1, MOSS[v % 3]!);
    cx += bw;
    i++;
  }
  // Tumbled blocks at the foot.
  for (let k = 0; k < Math.floor(w / 30); k++)
    block(g, x + hash(k, seed, 9) * (w - 12), base - 4, 9 + hash(k, seed, 10) * 5, 5, seed * 3 + k);
}

/** A column: fluted shaft, a base, and a capital unless it's snapped off. */
function column(g: G, x: number, base: number, h: number, broken: boolean) {
  px(g, x - 5, base - 3, 12, 3, STONE[2]!);
  px(g, x - 5, base - 3, 12, 1, STONE_LIGHT);
  px(g, x - 3, base - h, 8, h - 3, STONE[0]!);
  px(g, x - 3, base - h, 2, h - 3, STONE_LIGHT);
  for (let k = 0; k < 3; k++) px(g, x - 1 + k * 2, base - h, 1, h - 3, STONE_DARK);
  if (broken) {
    // A jagged, snapped-off top.
    for (let k = 0; k < 8; k++)
      px(g, x - 3 + k, base - h - ((hash(k, h) * 3) | 0), 1, 3, STONE[3]!);
  } else {
    px(g, x - 5, base - h - 3, 12, 3, STONE[2]!);
    px(g, x - 5, base - h - 3, 12, 1, STONE_LIGHT);
  }
  // A vine up it.
  for (let y = 0; y < h * 0.6; y++)
    px(g, x + 3 + Math.sin(y * 0.5) * 1.5, base - 3 - y, 1, 1, MOSS[y % 3]!);
}

/**
 * The left ruins: a broken temple plinth for the long-necked dinosaur to stand on, a
 * fallen column drum beside it and a column snapped off behind. `top` is where the
 * plinth's top surface is.
 */
export function ruinsLeft(g: G, top: number, terrace: number) {
  // Behind: a ruined wall along the cliff edge.
  ruinWall(g, 0, terrace + 2, 92, 22, 0.25, 5);
  column(g, 72, terrace + 4, 26, true);
  // The plinth: a slab with a carved frieze along its face, broken at the right end.
  px(g, 4, top, 64, 3, STONE[2]!);
  px(g, 4, top, 64, 1, STONE_LIGHT);
  px(g, 6, top + 3, 60, 9, STONE[1]!);
  px(g, 6, top + 11, 60, 1, STONE_DARK);
  for (let x = 10; x < 60; x += 9) {
    // The frieze: little carved steps.
    px(g, x, top + 5, 6, 1, STONE_DARK);
    px(g, x + 1, top + 6, 4, 1, STONE_DARK);
    px(g, x + 2, top + 7, 2, 2, STONE_DARK);
  }
  for (let k = 0; k < 6; k++) px(g, 62 + k, top + ((hash(k, 3) * 4) | 0), 1, 12, GROUT);
  for (let x = 4; x < 62; x += 3) if (hash(x, 77) < 0.45) px(g, x, top - 1, 3, 1, MOSS[x % 3]!);
  // The fallen column drum, lying in front.
  px(g, 70, top + 6, 16, 7, STONE[0]!);
  px(g, 70, top + 6, 16, 1, STONE_LIGHT);
  for (let k = 0; k < 3; k++) px(g, 70, top + 8 + k * 2, 16, 1, STONE_DARK);
  ell(g, 86, top + 9, 2.5, 3.5, STONE[2]!);
  px(g, 86, top + 8, 1, 2, STONE_DARK);
}

/** The right ruins: a broken archway at the canyon's foot, and a block to stand on. */
export function ruinsRight(g: G, W: number, terrace: number) {
  ruinWall(g, W - 96, terrace + 2, 96, 18, 0.8, 9);
  const ax = W - 52;
  column(g, ax - 18, terrace + 2, 40, false);
  column(g, ax + 18, terrace + 2, 28, true);
  // What's left of the arch: voussoirs from the left column round to the crown.
  for (let i = 0; i < 7; i++) {
    const a = Math.PI - (i / 10) * Math.PI;
    const cx = ax + Math.cos(a) * 18;
    const cy = terrace - 38 - Math.sin(a) * 12;
    px(g, cx - 2, cy - 2, 5, 5, STONE[(i + 1) % STONE.length]!);
    px(g, cx - 2, cy - 2, 5, 1, STONE_LIGHT);
    px(g, cx + 2, cy - 2, 1, 5, STONE_DARK);
  }
  // A low block in front (the triceratops grazes beside it).
  block(g, W - 30, terrace + 1, 22, 8, 31);
  block(g, W - 92, terrace + 3, 14, 6, 33);
}

// ---------------------------------------------------------------- the volcano

/** The volcano's shape: peak height, centre and width (shared by the still and live parts). */
export function volcanoAt(W: number) {
  return { x: Math.round(W * 0.15), peak: 70, base: 133, halfW: 62 };
}

/** The still volcano: dark slopes, a glowing crater, lava rivers. */
export function paintVolcano(g: G, W: number) {
  const v = volcanoAt(W);
  const top = (x: number) => {
    const d = Math.abs(x - v.x);
    // A concave cone, a notched crater at the top.
    return v.peak + (d < 6 ? 2 : 0) + d * 0.55 + (d / v.halfW) ** 2 * 26;
  };
  for (let x = v.x - v.halfW; x < v.x + v.halfW; x++) {
    const y = Math.round(top(x));
    if (y >= v.base) continue;
    const left = x < v.x;
    px(g, x, y, 1, v.base - y, left ? "#5e4d66" : "#4a3c54");
    // Ridges running down the slope.
    if (hash(x, 3) < 0.18) px(g, x, y + 3, 1, (v.base - y) * 0.6, left ? "#6e5c76" : "#3e3248");
  }
  // The crater's glow and the lava rivers down the flanks.
  px(g, v.x - 6, v.peak + 1, 12, 2, "#ffb23a");
  px(g, v.x - 4, v.peak, 8, 1, "#ffe07a");
  const rivers: [number, number][] = [
    [-3, -0.7],
    [2, 0.55],
    [-1, 0.2],
  ];
  rivers.forEach(([sx, drift], r) => {
    let x = v.x + sx;
    for (let y = v.peak + 3; y < v.base - 4; y++) {
      x += drift + Math.sin(y * 0.4 + r * 2) * 0.6;
      const w = 1 + (y - v.peak) / 30;
      px(g, x, y, w, 1, (y + r) % 5 ? "#e8501e" : "#ff9a2a");
    }
  });
  // Green jungle round the volcano's foot.
  for (let x = v.x - v.halfW - 4; x < v.x + v.halfW; x++) {
    const y = 118 + Math.sin(x * 0.12) * 3 + hash(x, 5) * 2;
    px(g, x, y, 1, v.base - y + 1, x % 5 < 3 ? "#5f9a5a" : "#4f8a4a");
  }
}

/** The live volcano: a lava fountain, lava bombs, and a rolling plume of smoke. */
export function volcanoLife(g: G, W: number, t: number, calm: boolean) {
  const v = volcanoAt(W);
  const T = calm ? 2 : t;
  // Smoke: a plume of puffs rising from the crater and leaning out to the right (clear
  // of the jungle tree), growing and darkening as they go.
  for (let i = 0; i < 14; i++) {
    const life = (T * 0.11 + i / 14) % 1;
    const r = 3 + life * 9;
    const sx = v.x + 4 + life * 84 + Math.sin(life * 6 + i) * 3;
    const sy = v.peak - 4 - life * 20 + Math.sin(life * 4 + i) * 2;
    const c = life < 0.3 ? "#7c707a" : life < 0.65 ? "#665a66" : "#574c58";
    ell(g, sx, sy, r, r * 0.75, c);
    ell(g, sx - r * 0.3, sy - r * 0.3, r * 0.5, r * 0.4, life < 0.5 ? "#9a8e96" : "#746a74");
    if (life < 0.35) ell(g, sx, sy + r * 0.4, r * 0.6, r * 0.3, "#c0603a");
  }
  // The crater glows, brighter in pulses.
  const pulse = calm ? 0.5 : 0.5 + 0.5 * Math.sin(t * 3.1);
  px(g, v.x - 7, v.peak - 1, 14, 3, pulse > 0.6 ? "#fff0a0" : "#ffc24a");
  // The fountain: blobs thrown up and falling back.
  if (!calm)
    for (let i = 0; i < 26; i++) {
      const ph = (t * 0.9 + i * 0.137) % 1;
      const vx = (hash(i, 51) - 0.5) * 26;
      const vy = 26 + hash(i, 52) * 20;
      const x = v.x + vx * ph;
      const y = v.peak - (vy * ph - 26 * ph * ph);
      if (y > v.peak + 2) continue;
      px(g, x, y, 2, 2, ph < 0.5 ? "#ffe07a" : "#ff7a2a");
    }
  // Now and then a big lava bomb arcs right out over the slope, trailing sparks.
  if (!calm) {
    const cycle = t % 5.5;
    if (cycle < 1.6) {
      const p = cycle / 1.6;
      const dir = Math.floor(t / 5.5) % 2 ? 1 : -1;
      const bx = v.x + dir * p * 44;
      const by = v.peak - 6 - (40 * p - 34 * p * p);
      for (let k = 1; k < 5; k++) {
        const q = Math.max(0, p - k * 0.03);
        px(g, v.x + dir * q * 44, v.peak - 6 - (40 * q - 34 * q * q), 1, 1, "#ff9a2a");
      }
      px(g, bx - 1, by - 1, 3, 3, "#ff5a1e");
      px(g, bx, by - 1, 1, 1, "#ffe07a");
    }
  }
}

// ---------------------------------------------------------------- dinosaurs

/**
 * A triceratops grazing, facing left (`x`, `y`: between its front feet, on the
 * ground): it dips its head to the grass and lifts it to look about; the tail swishes.
 */
export function triceratops(g: G, x: number, y: number, t: number, calm = false) {
  const body = "#c9773a";
  const shade = "#9c5626";
  const belly = "#e8b47a";
  const frill = "#d9482a";
  const frillDark = "#8f2a18";
  const horn = "#f6efd8";
  const graze = calm ? 0 : Math.max(0, Math.sin(t * 0.8)) ** 3;
  const dip = Math.round(graze * 4);
  // Tail, swishing.
  for (let i = 0; i < 12; i++) {
    const sw = calm ? 0 : Math.sin(t * 2.4 - i * 0.3) * i * 0.12;
    px(g, x + 12 + i, y - 10 + i * 0.4 + sw, 1, Math.max(1, 4 - i * 0.3), body);
  }
  // Back legs, then the body, then the front legs.
  px(g, x + 6, y - 6, 4, 6, shade);
  px(g, x + 6, y - 1, 5, 1, "#5a3014");
  ell(g, x + 3, y - 10, 12, 6.5, body);
  ell(g, x + 4, y - 7, 10, 3, shade);
  px(g, x - 5, y - 6, 18, 2, belly);
  for (let k = 0; k < 4; k++) px(g, x - 2 + k * 5, y - 15 + (k % 2), 2, 1, shade);
  px(g, x - 6, y - 6, 4, 6, body);
  px(g, x + 1, y - 6, 4, 6, body);
  px(g, x - 6, y - 1, 5, 1, "#5a3014");
  px(g, x + 1, y - 1, 5, 1, "#5a3014");
  // The head (dips to graze): the frill behind, a beak, three horns.
  const hx = x - 12;
  const hy = y - 11 + dip;
  ell(g, hx + 4, hy - 3, 6.5, 7, frillDark);
  ell(g, hx + 4, hy - 3, 5.5, 6, frill);
  for (let i = 0; i < 6; i++) {
    const a = -Math.PI * 0.95 + (i / 5) * Math.PI * 0.9;
    px(g, hx + 4 + Math.cos(a) * 7, hy - 3 + Math.sin(a) * 7.5, 1, 1, horn);
  }
  ell(g, hx + 1, hy - 2, 3, 2, "#f2c64a");
  ell(g, hx, hy + 1, 5, 3.5, body);
  ell(g, hx - 4, hy + 2, 2.5, 2.5, belly);
  px(g, hx - 7, hy + 2, 3, 2, "#e8d6a8");
  px(g, hx - 8, hy + 3, 2, 1, "#e8d6a8");
  // Horns: two long brow horns sweeping forward, a short nose horn.
  for (let i = 0; i < 6; i++) px(g, hx - 2 - i, hy - 3 - i * 0.55, 1, 1, horn);
  for (let i = 0; i < 5; i++) px(g, hx + 1 - i, hy - 4 - i * 0.6, 1, 1, "#e0d4b4");
  px(g, hx - 5, hy, 1, 1, horn);
  px(g, hx - 6, hy - 1, 1, 1, horn);
  // The eye.
  const blink = !calm && (t + 1.3) % 3.7 < 0.12;
  px(g, hx - 1, hy - 1, 2, blink ? 1 : 2, "#1a1a1a");
  if (!blink) px(g, hx - 1, hy - 1, 1, 1, "#ffffff");
}

/** One pteranodon gliding (facing left), its wings beating now and then. */
function pteranodon(g: G, x: number, y: number, t: number, seed: number, calm: boolean) {
  const wing = "#e07a3a";
  const wingDark = "#a8502a";
  const body = "#f2b64a";
  // Glide mostly; a few beats every so often.
  const beat = calm ? 0 : Math.sin(t * 9 + seed) * (Math.sin(t * 0.7 + seed) > 0.6 ? 1 : 0.15);
  for (let i = 1; i <= 11; i++) {
    const lift = beat * i * 0.45 + (i > 7 ? (i - 7) * 0.5 : 0);
    const thick = i < 6 ? 2 : 1;
    px(g, x - i * 0.9, y - lift, 1, thick, i % 4 ? wing : wingDark);
    px(g, x + 3 + i * 0.9, y - lift, 1, thick, i % 4 ? wing : wingDark);
  }
  ell(g, x + 1.5, y + 1, 3, 1.5, body);
  // Head, a long beak forward, the crest back.
  px(g, x - 3, y - 1, 3, 2, body);
  px(g, x - 7, y, 4, 1, "#f7cf5a");
  px(g, x - 1, y - 2, 3, 1, "#d9482a");
}

/** A pair of pteranodons crossing the sky, low over the sea. */
export function pteranodons(g: G, W: number, t: number, calm = false) {
  const span = W + 80;
  const k = calm ? 0.35 : (t * 0.022 + 0.4) % 1;
  const x = W + 40 - span * k;
  const y = 52 + Math.sin(t * 0.5) * 4;
  pteranodon(g, x, y, t, 0, calm);
  pteranodon(g, x + 18, y + 7 + Math.sin(t * 0.6 + 1) * 2, t, 2.1, calm);
}

/** A small stegosaurus plodding along the cliff top (facing right), far off. */
export function stegosaurus(g: G, x: number, y: number, t: number, calm = false) {
  const body = "#7a9a4a";
  const plate = "#e07a3a";
  const step = calm ? 0 : Math.floor(t * 3) % 2;
  // Tail with spikes, the body arched, plates along the back, a small low head.
  for (let i = 0; i < 6; i++) px(g, x - 6 - i, y - 4 + i * 0.3, 1, 2, body);
  px(g, x - 12, y - 4, 1, 1, "#f2ead4");
  px(g, x - 11, y - 5, 1, 1, "#f2ead4");
  ell(g, x, y - 4, 6, 3, body);
  for (let i = 0; i < 5; i++) {
    const h = 3 - Math.abs(i - 2) * 0.6;
    px(g, x - 4 + i * 2, y - 7 - h, 1, h + 1, plate);
  }
  px(g, x + 6, y - 3, 3, 2, body);
  px(g, x + 8, y - 3, 1, 1, "#1a1a1a");
  for (const [lx, ph] of [
    [-3, 0],
    [3, 1],
  ] as const)
    px(g, x + lx, y - 2, 2, 2 + ((step + ph) % 2), "#5f7a3a");
}
