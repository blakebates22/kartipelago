/**
 * The speedometer in the bottom-right corner: a wooden barrel dial with metal bands
 * and a palm leaf, a red star needle, a digital readout and a wooden BOOST sign.
 *
 * It only displays what it is given (see speedo.ts for the numbers): the needle and
 * the readout follow the kart's true speed every frame with no smoothing, and the
 * chevrons on the sign show how much of the current boost is left.
 */
import { DIAL_SWEEP_DEG } from "./speedo";

const NS = "http://www.w3.org/2000/svg";
const CX = 122;
const CY = 122;
const R_OUT = 110;
const R_DIAL = 86;
const BLOCKS = 30;
const CHEVRONS = 4;

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

/** A point at radius r and angle deg (clockwise from up) around the dial centre. */
const polar = (r: number, deg: number) => {
  const a = (deg * Math.PI) / 180;
  return [CX + r * Math.sin(a), CY - r * Math.cos(a)] as const;
};
const f1 = (n: number) => n.toFixed(1);

function el<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attrs: Record<string, string | number> = {},
  parent?: Element,
): SVGElementTagNameMap[K] {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  parent?.appendChild(e);
  return e;
}

/** A five-pointed star centred at (x, y). */
function starPoints(x: number, y: number, r: number) {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const rr = i % 2 ? r * 0.45 : r;
    const a = (i * Math.PI) / 5;
    pts.push(`${f1(x + rr * Math.sin(a))},${f1(y - rr * Math.cos(a))}`);
  }
  return pts.join(" ");
}

/** Green at the bottom of the dial, through yellow and orange, to red at the top. */
const blockColor = (f: number) => `hsl(${f1(118 - 114 * Math.pow(f, 1.15))} 78% 47%)`;

export function createSpeedometer(parent: HTMLElement) {
  const svg = el("svg", {
    viewBox: "0 0 300 236",
    class: "speedo",
    role: "img",
    "aria-label": "Speed",
  });
  parent.appendChild(svg);

  const defs = el("defs", {}, svg);
  const grad = (id: string, stops: [number, string][], radial = false) => {
    const g = el(
      radial ? "radialGradient" : "linearGradient",
      radial ? { id, cx: "50%", cy: "42%", r: "62%" } : { id, x1: 0, y1: 0, x2: 0, y2: 1 },
      defs,
    );
    for (const [o, c] of stops) el("stop", { offset: o, "stop-color": c }, g);
  };
  grad("spd-wood", [
    [0, "#a46a34"],
    [0.55, "#86532a"],
    [1, "#5e3a1c"],
  ]);
  grad("spd-plank", [
    [0, "#a8703a"],
    [1, "#714522"],
  ]);
  grad("spd-metal", [
    [0, "#c9d0d5"],
    [1, "#7b848b"],
  ]);
  grad(
    "spd-face",
    [
      [0, "#fff8e3"],
      [0.75, "#f4e4bc"],
      [1, "#e2c993"],
    ],
    true,
  );
  const glow = el(
    "filter",
    { id: "spd-glow", x: "-50%", y: "-50%", width: "200%", height: "200%" },
    defs,
  );
  el("feGaussianBlur", { stdDeviation: 2.2, result: "b" }, glow);
  const merge = el("feMerge", {}, glow);
  el("feMergeNode", { in: "b" }, merge);
  el("feMergeNode", { in: "SourceGraphic" }, merge);

  // --- the palm leaf, tucked behind the barrel at the top right
  const leaf = el("g", {}, svg);
  const frond = (deg: number, len: number, w: number, fill: string) => {
    const g = el("g", { transform: `translate(196 74) rotate(${deg})` }, leaf);
    // A pointed leaf with a few chunky notches along each edge.
    const pts: string[] = ["0,0"];
    const n = 5;
    for (let i = 1; i <= n; i++) {
      const t = i / (n + 1);
      const half = w * Math.sin(Math.PI * t) * 0.5;
      pts.push(`${f1(half)},${f1(-len * t + 3)}`, `${f1(half * 0.7)},${f1(-len * t - 4)}`);
    }
    pts.push(`0,${-len}`);
    for (let i = n; i >= 1; i--) {
      const t = i / (n + 1);
      const half = w * Math.sin(Math.PI * t) * 0.5;
      pts.push(`${f1(-half * 0.7)},${f1(-len * t - 4)}`, `${f1(-half)},${f1(-len * t + 3)}`);
    }
    el(
      "polygon",
      {
        points: pts.join(" "),
        fill,
        stroke: "#245a26",
        "stroke-width": 2,
        "stroke-linejoin": "round",
      },
      g,
    );
    el("path", { d: `M0,0 L0,${-len + 6}`, stroke: "#2c6e2f", "stroke-width": 2, fill: "none" }, g);
  };
  frond(18, 74, 34, "#3f9a44");
  frond(88, 70, 32, "#3f9a44");
  frond(52, 84, 38, "#55b94f");

  // --- the barrel ring
  el(
    "circle",
    { cx: CX, cy: CY, r: R_OUT, fill: "url(#spd-wood)", stroke: "#3a2210", "stroke-width": 4 },
    svg,
  );
  el(
    "circle",
    {
      cx: CX,
      cy: CY,
      r: R_OUT - 4,
      fill: "none",
      stroke: "#c08a52",
      "stroke-opacity": 0.35,
      "stroke-width": 2,
    },
    svg,
  );
  // Stave seams, and a little grain on each stave.
  const staves = 16;
  for (let i = 0; i < staves; i++) {
    const deg = (i * 360) / staves + 6;
    const [x0, y0] = polar(R_DIAL + 1, deg);
    const [x1, y1] = polar(R_OUT - 1, deg);
    el("line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: "#3f2410", "stroke-width": 2.5 }, svg);
    const g0 = deg + 6 + ((i * 7) % 5);
    const g1 = g0 + 6 + ((i * 3) % 4);
    const r = 95 + ((i * 5) % 9);
    const [gx0, gy0] = polar(r, g0);
    const [gx1, gy1] = polar(r, g1);
    el(
      "path",
      {
        d: `M${f1(gx0)},${f1(gy0)} A${r},${r} 0 0 1 ${f1(gx1)},${f1(gy1)}`,
        stroke: "#5c3618",
        "stroke-width": 1.6,
        fill: "none",
        "stroke-linecap": "round",
      },
      svg,
    );
  }
  // Metal bands with rivets.
  for (const deg of [-118, -62, 82]) {
    const g = el("g", { transform: `rotate(${deg} ${CX} ${CY})` }, svg);
    el(
      "rect",
      {
        x: CX - 9,
        y: CY - R_OUT - 5,
        width: 18,
        height: 34,
        rx: 3,
        fill: "url(#spd-metal)",
        stroke: "#33383c",
        "stroke-width": 2,
      },
      g,
    );
    for (const dy of [5, 24])
      el(
        "circle",
        {
          cx: CX,
          cy: CY - R_OUT + dy,
          r: 2.6,
          fill: "#eef1f3",
          stroke: "#33383c",
          "stroke-width": 1.2,
        },
        g,
      );
  }

  // --- the dial face
  el(
    "circle",
    { cx: CX, cy: CY, r: R_DIAL, fill: "url(#spd-face)", stroke: "#3a2210", "stroke-width": 4 },
    svg,
  );
  el(
    "circle",
    { cx: CX, cy: CY, r: R_DIAL - 6, fill: "none", stroke: "#d6bb85", "stroke-width": 1.5 },
    svg,
  );

  // Coloured blocks around the dial, lit up to the current speed.
  const blocks: SVGPathElement[] = [];
  const step = DIAL_SWEEP_DEG / BLOCKS;
  const rb = 70;
  for (let i = 0; i < BLOCKS; i++) {
    const a0 = -DIAL_SWEEP_DEG / 2 + i * step + 0.9;
    const a1 = a0 + step - 1.8;
    const [x0, y0] = polar(rb, a0);
    const [x1, y1] = polar(rb, a1);
    blocks.push(
      el(
        "path",
        {
          d: `M${f1(x0)},${f1(y0)} A${rb},${rb} 0 0 1 ${f1(x1)},${f1(y1)}`,
          stroke: blockColor(i / (BLOCKS - 1)),
          "stroke-width": 11,
          fill: "none",
        },
        svg,
      ),
    );
  }
  // Major marks and numbers. They are filled in by `layoutDial` (the dial max is tunable).
  const marks = el("g", {}, svg);
  let laidOutFor = -1;
  function layoutDial(dialMax: number) {
    if (dialMax === laidOutFor) return;
    laidOutFor = dialMax;
    marks.replaceChildren();
    const every = dialMax / 6;
    for (let k = 0; k <= 6; k++) {
      const deg = -DIAL_SWEEP_DEG / 2 + (k / 6) * DIAL_SWEEP_DEG;
      const [x0, y0] = polar(57, deg);
      const [x1, y1] = polar(64, deg);
      el(
        "line",
        {
          x1: x0,
          y1: y0,
          x2: x1,
          y2: y1,
          stroke: "#2a3550",
          "stroke-width": 3,
          "stroke-linecap": "round",
        },
        marks,
      );
      const [tx, ty] = polar(47, deg);
      const t = el("text", { x: f1(tx), y: f1(ty + 5), class: "speedo-num" }, marks);
      t.textContent = String(Math.round(k * every));
    }
  }

  // --- the readout
  el(
    "rect",
    {
      x: CX - 25,
      y: 165,
      width: 50,
      height: 30,
      rx: 6,
      fill: "#18161f",
      stroke: "#4a2c14",
      "stroke-width": 3,
    },
    svg,
  );
  const readout = el(
    "text",
    { x: CX, y: 189, class: "speedo-readout", filter: "url(#spd-glow)" },
    svg,
  );

  // --- the needle and its star hub
  const needle = el("g", {}, svg);
  el(
    "path",
    {
      d: `M${CX - 4},${CY + 3} L${CX},${CY - 68} L${CX + 4},${CY + 3} Z`,
      fill: "#000",
      opacity: 0.22,
      transform: "translate(2.5 3)",
    },
    needle,
  );
  el(
    "path",
    {
      d: `M${CX - 4.5},${CY + 2} L${CX},${CY - 68} L${CX + 4.5},${CY + 2} L${CX + 2.5},${CY + 15} L${CX - 2.5},${CY + 15} Z`,
      fill: "#e23b2e",
      stroke: "#6e1610",
      "stroke-width": 2,
      "stroke-linejoin": "round",
    },
    needle,
  );
  el(
    "path",
    {
      d: `M${CX - 1},${CY - 4} L${CX},${CY - 60}`,
      stroke: "#ff8a7a",
      "stroke-width": 1.4,
      "stroke-linecap": "round",
    },
    needle,
  );
  el(
    "circle",
    { cx: CX, cy: CY, r: 14, fill: "#e23b2e", stroke: "#6e1610", "stroke-width": 2.5 },
    svg,
  );
  el(
    "circle",
    { cx: CX, cy: CY, r: 9.5, fill: "#2a7fa0", stroke: "#123c4d", "stroke-width": 1.5 },
    svg,
  );
  el(
    "polygon",
    {
      points: starPoints(CX, CY + 0.5, 7),
      fill: "#ffd23f",
      stroke: "#8a6100",
      "stroke-width": 1,
      "stroke-linejoin": "round",
    },
    svg,
  );

  // --- the BOOST sign
  const sign = el("g", { transform: "translate(194 160)" }, svg);
  el(
    "rect",
    {
      x: 0,
      y: 0,
      width: 102,
      height: 64,
      rx: 8,
      fill: "url(#spd-plank)",
      stroke: "#3a2210",
      "stroke-width": 3,
    },
    sign,
  );
  el("path", { d: "M3,23 H99", stroke: "#4a2c14", "stroke-width": 2 }, sign);
  el(
    "path",
    {
      d: "M14,12 h20 M64,15 h24 M18,58 h14",
      stroke: "#5c3618",
      "stroke-width": 1.4,
      "stroke-linecap": "round",
    },
    sign,
  );
  for (const [x, y] of [
    [8, 8],
    [94, 8],
    [8, 56],
    [94, 56],
  ])
    el(
      "circle",
      { cx: x!, cy: y!, r: 2.6, fill: "#d3d8dc", stroke: "#33383c", "stroke-width": 1.2 },
      sign,
    );
  const label = el("text", { x: 51, y: 18.5, class: "speedo-boost" }, sign);
  label.textContent = "BOOST";
  el(
    "rect",
    {
      x: 11,
      y: 28,
      width: 80,
      height: 28,
      rx: 5,
      fill: "#16151e",
      stroke: "#2a1a0e",
      "stroke-width": 2,
    },
    sign,
  );
  const chevrons: SVGPathElement[] = [];
  for (let i = 0; i < CHEVRONS; i++)
    chevrons.push(
      el(
        "path",
        {
          d: `M${18 + i * 17},32 h7 l8,10 l-8,10 h-7 l8,-10 z`,
          fill: "#2b3346",
          "stroke-linejoin": "round",
        },
        sign,
      ),
    );

  let shownValue = "";
  let litBlocks = -1;
  let litChevrons = -1;
  let chevronColor = "";
  let wasEnhanced = false;

  return {
    element: svg,
    update(f: SpeedoFrame) {
      layoutDial(f.dialMax);
      needle.setAttribute("transform", `rotate(${f.needleDeg.toFixed(2)} ${CX} ${CY})`);
      const text = String(Math.round(f.value));
      if (text !== shownValue) readout.textContent = shownValue = text;
      const lit = Math.min(BLOCKS, Math.ceil((f.value / f.dialMax) * BLOCKS - 1e-9));
      if (lit !== litBlocks) {
        litBlocks = lit;
        blocks.forEach((b, i) => b.setAttribute("opacity", i < lit ? "1" : "0.3"));
      }
      const t = performance.now() / 1000;
      const color = f.rainbow ? `rainbow${Math.floor(t * 12)}` : f.color;
      if (f.chevrons !== litChevrons || color !== chevronColor) {
        litChevrons = f.chevrons;
        chevronColor = color;
        chevrons.forEach((c, i) => {
          const on = i < f.chevrons;
          const fill = !on
            ? "#2b3346"
            : f.rainbow
              ? `hsl(${Math.round((t * 400 + i * 70) % 360)} 95% 60%)`
              : f.color;
          c.setAttribute("fill", fill);
          if (on) c.setAttribute("filter", "url(#spd-glow)");
          else c.removeAttribute("filter");
        });
      }
      if (f.enhanced !== wasEnhanced) {
        wasEnhanced = f.enhanced;
        label.classList.toggle("lit", f.enhanced);
      }
    },
  };
}

export type Speedometer = ReturnType<typeof createSpeedometer>;
