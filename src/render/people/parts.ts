/**
 * Shared bits for the people: moss and lichen, little flowers, spectacles, woven
 * cloth, tassels, the Founders' Horn, a gnarled staff, a key ring. Built from the
 * racers' kit shapes, so they share the look.
 */
import * as THREE from "three";
import { Build, ellipsoid, gem, loft, tube, type ColorLike, type V3 } from "../racers/kit/shapes";
import { leaf } from "../racers/kit/props";
import { seeded } from "../racers/kit/paint";

const UP = new THREE.Vector3(0, 0, 1);
/** Euler angles turning +Z to `n`. */
export function facing(n: V3): V3 {
  const q = new THREE.Quaternion().setFromUnitVectors(UP, new THREE.Vector3(...n).normalize());
  const e = new THREE.Euler().setFromQuaternion(q);
  return [e.x, e.y, e.z];
}

/**
 * A patch of moss on a surface at `at` (normal `n`): soft lumps in a few greens, a fern
 * frond or two, maybe a tiny flower.
 */
export function moss(
  b: Build,
  at: V3,
  n: V3,
  radius: number,
  seed: number,
  o: { greens?: string[]; fronds?: number; flowers?: number; lump?: number } = {},
) {
  const r = seeded(seed);
  const greens = o.greens ?? ["#5f9a3a", "#76b046", "#8cc455", "#4f8a34", "#a2c860"];
  const nn = new THREE.Vector3(...n).normalize();
  // Two tangents.
  const t1 = new THREE.Vector3(1, 0, 0);
  if (Math.abs(nn.dot(t1)) > 0.9) t1.set(0, 1, 0);
  t1.addScaledVector(nn, -t1.dot(nn)).normalize();
  const t2 = new THREE.Vector3().crossVectors(nn, t1);
  const lump = o.lump ?? radius * 0.32;
  const count = Math.max(4, Math.round((radius / lump) ** 2 * 1.25));
  for (let i = 0; i < count; i++) {
    const a = r() * Math.PI * 2;
    const d = Math.sqrt(r()) * radius;
    const p = new THREE.Vector3(...at)
      .addScaledVector(t1, Math.cos(a) * d)
      .addScaledVector(t2, Math.sin(a) * d)
      .addScaledVector(nn, lump * 0.2 * (1 - d / radius));
    const s = lump * (0.6 + r() * 0.6) * (1 - (d / radius) * 0.45);
    b.add(gem(0), greens[Math.floor(r() * greens.length)]!, {
      p: [p.x, p.y, p.z],
      r: facing([nn.x, nn.y, nn.z]),
      s: [s, s, s * 0.55],
    });
  }
  for (let i = 0; i < (o.fronds ?? 0); i++) {
    const a = r() * Math.PI * 2;
    const p = new THREE.Vector3(...at)
      .addScaledVector(t1, Math.cos(a) * radius * 0.4)
      .addScaledVector(t2, Math.sin(a) * radius * 0.4);
    // A frond standing out of the moss, leaning outward.
    const lean = new THREE.Vector3()
      .copy(nn)
      .addScaledVector(t1, Math.cos(a) * 0.6)
      .addScaledVector(t2, Math.sin(a) * 0.6)
      .normalize();
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), lean);
    const e = new THREE.Euler().setFromQuaternion(q);
    b.addColored(leaf(radius * 0.9, radius * 0.16, "#4f8f30", "#9ad060"), {
      p: [p.x, p.y, p.z],
      r: [e.x, e.y, e.z],
    });
  }
  for (let i = 0; i < (o.flowers ?? 0); i++) {
    const a = r() * Math.PI * 2;
    const p = new THREE.Vector3(...at)
      .addScaledVector(t1, Math.cos(a) * radius * 0.5)
      .addScaledVector(t2, Math.sin(a) * radius * 0.5)
      .addScaledVector(nn, lump * 0.5);
    flower(b, [p.x, p.y, p.z], [nn.x, nn.y, nn.z], lump * 0.75, i % 2 ? "#fff6e8" : "#f4d040");
  }
}

/** A tiny five-petalled flower facing `n`. */
export function flower(b: Build, at: V3, n: V3, size: number, petal: string, middle = "#e89a20") {
  const rot = facing(n);
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot));
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2;
    const off = new THREE.Vector3(
      Math.cos(a) * size * 0.75,
      Math.sin(a) * size * 0.75,
      0,
    ).applyQuaternion(q);
    b.add(ellipsoid(6, 4), petal, {
      p: [at[0] + off.x, at[1] + off.y, at[2] + off.z],
      r: rot,
      s: [size * 0.55, size * 0.55, size * 0.2],
    });
  }
  b.add(ellipsoid(6, 4), middle, { p: at, r: rot, s: [size * 0.4, size * 0.4, size * 0.3] });
}

/** Woven cloth: bands across `t`, with a zigzag in the bands. */
export function woven(main: string, bands: string[], every = 0.18) {
  const m = new THREE.Color(main);
  const cs = bands.map((c) => new THREE.Color(c));
  return (t: number, a: number) => {
    const u = (t / every) % 1;
    const k = Math.floor(t / every);
    const zig = Math.abs((((a * 3) / Math.PI) % 1) - 0.5) * 0.12;
    if (u > 0.62 + zig && u < 0.82 + zig) return cs[k % cs.length]!;
    if (u > 0.86 && u < 0.92) return cs[(k + 1) % cs.length]!;
    return m;
  };
}

/** Round spectacles: two rims at `at` (left; mirrored), a bridge, arms back to the head. */
export function spectacles(
  b: Build,
  o: { at: V3; r: number; yaw: number; bridgeY: number; ear: V3; rim: string },
) {
  for (const s of [1, -1]) {
    const c: V3 = [o.at[0] * s, o.at[1], o.at[2]];
    b.add(new THREE.TorusGeometry(o.r, o.r * 0.13, 5, 16), o.rim, {
      p: c,
      r: [0, o.yaw * s, 0],
    });
    b.addColored(
      tube(
        [
          [
            c[0] + s * o.r * Math.cos(o.yaw),
            c[1] + o.r * 0.2,
            c[2] - s * o.r * Math.sin(o.yaw * s) * s,
          ],
          [o.ear[0] * s, o.ear[1] + 0.01, (c[2] + o.ear[2]) / 2],
          [o.ear[0] * s, o.ear[1], o.ear[2]],
        ],
        o.r * 0.1,
        o.rim,
        { sides: 4 },
      ),
    );
  }
  b.addColored(
    tube(
      [
        [o.at[0] - o.r * Math.cos(o.yaw), o.bridgeY - 0.004, o.at[2] + 0.012],
        [0, o.bridgeY + 0.012, o.at[2] + 0.03],
        [-(o.at[0] - o.r * Math.cos(o.yaw)), o.bridgeY - 0.004, o.at[2] + 0.012],
      ],
      o.r * 0.11,
      o.rim,
      { sides: 4, steps: 3 },
    ),
  );
}

/** A tassel hanging down from `at`. */
export function tassel(b: Build, at: V3, len: number, color: string, knot?: string) {
  b.add(ellipsoid(6, 4), knot ?? color, { p: at, s: [len * 0.16, len * 0.14, len * 0.16] });
  b.add(new THREE.ConeGeometry(len * 0.17, len, 6), color, {
    p: [at[0], at[1] - len * 0.55, at[2]],
    r: [Math.PI, 0, 0],
  });
}

// ---------------------------------------------------------------- the Founders' Horn

const HORN_PATH: V3[] = [
  [0, 0, 0],
  [0, 0.012, 0.09],
  [0, 0.035, 0.18],
  [0, 0.075, 0.26],
  [0, 0.13, 0.32],
  [0, 0.19, 0.345],
];
const HORN_R = [0.017, 0.024, 0.033, 0.045, 0.058, 0.074];

/**
 * The Founders' Horn: an old curved horn, ivory gone honey at the bell, three bronze
 * bands and a bronze mouthpiece; its origin is the mouthpiece and it runs along +Z,
 * curving up to the bell. `part`: the whole horn, or the mouthpiece half (a) or the bell
 * half (b), as it snaps in two.
 */
export function hornGeometry(
  part: "whole" | "a" | "b",
  c: { ivory: string; old: string; band: string; inside: string } = {
    ivory: "#f2e6c4",
    old: "#c8a060",
    band: "#b07a30",
    inside: "#3a2614",
  },
) {
  const iv = new THREE.Color(c.ivory);
  const old = new THREE.Color(c.old);
  const band = new THREE.Color(c.band);
  const cut = 2.55; // (between the third and fourth sections)
  const pts = HORN_PATH.map((p, i) => ({ p, r: HORN_R[i]!, i }));
  const keep =
    part === "whole"
      ? pts
      : part === "a"
        ? [...pts.filter((x) => x.i < cut), mid(cut)]
        : [mid(cut), ...pts.filter((x) => x.i > cut)];
  function mid(f: number) {
    const i = Math.floor(f);
    const k = f - i;
    const a = HORN_PATH[i]!;
    const bb = HORN_PATH[i + 1]!;
    return {
      p: [a[0] + (bb[0] - a[0]) * k, a[1] + (bb[1] - a[1]) * k, a[2] + (bb[2] - a[2]) * k] as V3,
      r: HORN_R[i]! + (HORN_R[i + 1]! - HORN_R[i]!) * k,
      i: f,
    };
  }
  const n = HORN_PATH.length - 1;
  const b = new Build().addColored(
    loft(
      keep.map((x) => ({ at: x.p, rx: x.r, ry: x.r })),
      {
        sides: 10,
        steps: 3,
        capStart: true,
        capEnd: part !== "b" && part !== "whole" ? true : false,
        paint: (t) => {
          // (t along this piece -> along the whole horn.)
          const u = (keep[0]!.i + t * (keep[keep.length - 1]!.i - keep[0]!.i)) / n;
          for (const at of [0.3, 0.55, 0.8]) if (Math.abs(u - at) < 0.03) return band;
          if (u < 0.06) return band;
          return iv.clone().lerp(old, Math.max(0, u - 0.2) * 1.1);
        },
      },
    ),
  );
  // The jagged break.
  if (part !== "whole") {
    const m = mid(cut);
    for (let k = 0; k < 5; k++) {
      const a = (k / 5) * Math.PI * 2;
      b.add(new THREE.ConeGeometry(m.r * 0.35, m.r * 0.9, 4), c.ivory, {
        p: [m.p[0] + Math.cos(a) * m.r * 0.6, m.p[1] + Math.sin(a) * m.r * 0.6, m.p[2]],
        r: [part === "a" ? Math.PI / 2 : -Math.PI / 2, 0, 0],
      });
    }
  }
  if (part !== "a") {
    // The bell's mouth: a rolled rim and the dark inside.
    const e = HORN_PATH[n]!;
    const d = new THREE.Vector3(...e).sub(new THREE.Vector3(...HORN_PATH[n - 1]!)).normalize();
    const rot = facing([d.x, d.y, d.z]);
    b.add(new THREE.TorusGeometry(HORN_R[n]! * 0.95, 0.009, 5, 14), band, { p: e, r: rot });
    b.add(new THREE.CircleGeometry(HORN_R[n]! * 0.92, 12), c.inside, {
      p: [e[0] - d.x * 0.01, e[1] - d.y * 0.01, e[2] - d.z * 0.01],
      r: rot,
    });
  }
  if (part !== "b") {
    b.add(new THREE.CylinderGeometry(0.02, 0.016, 0.03, 8), band, {
      p: [0, 0, -0.01],
      r: [Math.PI / 2, 0, 0],
    });
    // The cord's loop.
    b.add(new THREE.TorusGeometry(0.022, 0.005, 4, 8), "#6a4426", { p: [0, 0.028, 0.06] });
  }
  return b.build();
}

/** A gnarled walking staff, its grip at the origin, `below` down to the ground. */
export function staffGeometry(
  below: number,
  above: number,
  c: { wood: string; dark: string; charm: string; cord: string },
  seed = 3,
) {
  const r = seeded(seed);
  const pts: V3[] = [];
  const rad: number[] = [];
  const n = 9;
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const y = -below + (below + above) * t;
    const wob = i === 0 || i === n ? 0 : 0.018;
    pts.push([(r() - 0.5) * wob, y, (r() - 0.5) * wob]);
    rad.push(0.022 + 0.006 * Math.sin(i * 2.3) + (t > 0.85 ? 0.012 : 0));
  }
  const wood = new THREE.Color(c.wood);
  const dark = new THREE.Color(c.dark);
  const b = new Build().addColored(
    tube(pts, rad, c.wood, {
      sides: 7,
      steps: 2,
      paint: (t, a) =>
        Math.sin(t * 40 + a * 2) > 0.6 ? dark : wood.clone().lerp(dark, Math.max(0, 0.3 - t) * 0.8),
    }),
  );
  // Knots along it.
  for (const k of [0.3, 0.52, 0.7]) {
    const i = Math.round(k * n);
    const p = pts[i]!;
    b.add(ellipsoid(6, 4), c.dark, { p: [p[0] + 0.018, p[1], p[2]], s: [0.016, 0.024, 0.02] });
  }
  // The crook at the top: a curl of root.
  const top = pts[n]!;
  b.addColored(
    tube(
      [
        top,
        [top[0] + 0.02, top[1] + 0.06, top[2] + 0.03],
        [top[0] + 0.07, top[1] + 0.09, top[2] + 0.02],
        [top[0] + 0.1, top[1] + 0.05, top[2] - 0.01],
        [top[0] + 0.08, top[1] + 0.01, top[2] - 0.02],
      ],
      [0.034, 0.03, 0.026, 0.02, 0.014],
      c.wood,
      { sides: 7, steps: 3 },
    ),
  );
  // A charm on a cord under the crook: a carved disc and a feather.
  const hang: V3 = [top[0] + 0.09, top[1] - 0.06, top[2] - 0.02];
  b.addColored(
    tube([[top[0] + 0.085, top[1] + 0.01, top[2] - 0.02], hang], 0.004, c.cord, { sides: 4 }),
  );
  b.add(new THREE.CylinderGeometry(0.024, 0.024, 0.008, 10), c.charm, {
    p: [hang[0], hang[1] - 0.02, hang[2]],
    r: [Math.PI / 2, 0, 0],
  });
  b.add(ellipsoid(6, 4), "#e8e0d0", {
    p: [hang[0] + 0.012, hang[1] - 0.06, hang[2]],
    s: [0.012, 0.04, 0.004],
    r: [0, 0, 0.3],
  });
  // A leather grip wrap.
  b.add(new THREE.CylinderGeometry(0.028, 0.028, 0.09, 8), c.cord, { p: [0, 0, 0] });
  return b.build();
}

/** A ring of old iron keys (the smugglers'), its ring's top at the origin, hanging down. */
export function keyRingGeometry(c: { iron: string; gold: string }) {
  const b = new Build().add(new THREE.TorusGeometry(0.035, 0.006, 5, 12), c.iron, {
    p: [0, -0.035, 0],
  });
  const keys: [number, number, string][] = [
    [-0.5, 0.11, c.iron],
    [0.15, 0.13, c.gold],
    [0.7, 0.1, c.iron],
  ];
  for (const [a, len, col] of keys) {
    const g = new Build()
      .add(new THREE.TorusGeometry(0.016, 0.005, 4, 8), col, { p: [0, -0.016, 0] })
      .add(new THREE.CylinderGeometry(0.005, 0.005, len, 5), col, { p: [0, -0.032 - len / 2, 0] })
      .add(new THREE.BoxGeometry(0.004, 0.022, 0.016), col, { p: [0, -0.032 - len + 0.012, 0.01] })
      .add(new THREE.BoxGeometry(0.004, 0.012, 0.012), col, { p: [0, -0.032 - len + 0.032, 0.008] })
      .build();
    b.addColored(g, {
      p: [Math.sin(a) * 0.035, -0.035 - Math.cos(a) * 0.035, 0],
      r: [0, 0, a * 0.6],
    });
  }
  return b.build();
}

/** Paint for a sleeve: cloth to `end` (0..1 along the bone), then skin, a cuff at the edge. */
export const sleeve =
  (cloth: ColorLike, skin: ColorLike, end: number, cuff?: ColorLike) => (t: number) =>
    t < end - 0.06 ? cloth : t < end ? (cuff ?? cloth) : skin;

/**
 * Cut an opening into a loft (a vest's front): drop the triangles whose middle lies
 * within `half` radians of straight ahead (+Z) round the Y axis, between y0 and y1.
 */
export function cutFront(
  geo: THREE.BufferGeometry,
  half: (y: number) => number,
  y0: number,
  y1: number,
) {
  const g = geo.index ? geo.toNonIndexed() : geo;
  if (g !== geo) geo.dispose();
  const keep: number[] = [];
  const pos = g.getAttribute("position");
  const uv = g.getAttribute("uv");
  for (let i = 0; i < pos.count; i += 3) {
    let x = 0;
    let y = 0;
    let z = 0;
    let u = 0;
    for (let k = 0; k < 3; k++) {
      x += pos.getX(i + k) / 3;
      y += pos.getY(i + k) / 3;
      z += pos.getZ(i + k) / 3;
      u += (uv?.getX(i + k) ?? 0) / 3;
    }
    // (A loft standing up: its columns' angle from the front, so the cut runs cleanly
    // along them; otherwise the triangle's angle round Y.)
    const a = uv
      ? Math.abs(((u * Math.PI * 2 - Math.PI / 2 + Math.PI * 3) % (Math.PI * 2)) - Math.PI)
      : Math.abs(Math.atan2(x, z));
    if (!(y > y0 && y < y1 && a < half(y))) keep.push(i);
  }
  const out = new THREE.BufferGeometry();
  for (const name of Object.keys(g.attributes)) {
    const src = g.getAttribute(name) as THREE.BufferAttribute;
    const n = src.itemSize;
    const arr = new Float32Array(keep.length * 3 * n);
    keep.forEach((i, j) => {
      for (let k = 0; k < 3 * n; k++) arr[j * 3 * n + k] = src.array[i * n + k]!;
    });
    out.setAttribute(name, new THREE.BufferAttribute(arr, n));
  }
  g.dispose();
  return out;
}

/** A patch sewn on (a square of cloth, stitched round the edge), facing `n`. */
export function patch(
  b: Build,
  at: V3,
  n: V3,
  w: number,
  h: number,
  color: string,
  stitch: string,
  tilt = 0,
) {
  const rot = facing(n);
  const q = new THREE.Quaternion()
    .setFromEuler(new THREE.Euler(...rot))
    .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), tilt));
  const e = new THREE.Euler().setFromQuaternion(q);
  b.add(new THREE.BoxGeometry(w, h, 0.008), color, { p: at, r: [e.x, e.y, e.z] });
  // Stitches: little dashes round it.
  const u = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
  const v = new THREE.Vector3(0, 1, 0).applyQuaternion(q);
  const nn = new THREE.Vector3(0, 0, 1).applyQuaternion(q);
  const base = new THREE.Vector3(...at).addScaledVector(nn, 0.005);
  for (const [du, dv, along] of [
    [0, h / 2, "u"],
    [0, -h / 2, "u"],
    [w / 2, 0, "v"],
    [-w / 2, 0, "v"],
  ] as [number, number, "u" | "v"][]) {
    const len = along === "u" ? w : h;
    const nst = Math.max(2, Math.round(len / 0.03));
    for (let i = 0; i < nst; i++) {
      const k = (i + 0.5) / nst - 0.5;
      const p = base
        .clone()
        .addScaledVector(u, du * 0.85 + (along === "u" ? k * len * 0.85 : 0))
        .addScaledVector(v, dv * 0.85 + (along === "v" ? k * len * 0.85 : 0));
      b.add(new THREE.BoxGeometry(0.004, 0.012, 0.004), stitch, {
        p: [p.x, p.y, p.z],
        r: [e.x, e.y, e.z + (along === "u" ? Math.PI / 2 : 0)],
      });
    }
  }
}
