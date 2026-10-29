/**
 * The valley village's carved and mechanical decor, built like the characters (Blake,
 * Oct 28, review-valley_region 3): the totem poles ("redo these totem poles and make them
 * high resolution like the characters we have") and the kart taken apart in the repair
 * shed ("an actual rendered cart thats dissasembled": the game's own kart, its wheels
 * off).
 *
 * The build places them as entities (tools/blender/prehistoric/valley_village.py):
 *   village_totem { "x", "y", "z", "variant", "heading" }: its carved faces look along
 *     its heading (+Z turned by heading);
 *   kart_wreck    { "x", "y", "z", "heading" }: on its blocks, its nose along heading.
 * Their colliders are in the track; these are only seen.
 */
import * as THREE from "three";
import { buildKart } from "./racers/kit/chassis";
import { sleekKart } from "./racers/kit/sleek";
import {
  Build,
  box,
  card,
  cyl,
  ellipsoid,
  horn,
  loft,
  torus,
  tube,
  type ColorLike,
  type V3,
} from "./racers/kit/shapes";
import { skinMaterial } from "./racers/kit/paint";
import { createFire, type Fire } from "./fire";

const WOOD = "#8a5a34";
const WOOD_DARK = "#5e3a1e";
const WOOD_PALE = "#a87448";
const RED = "#c8402e";
const TEAL = "#2a8fae";
const GOLD = "#e8b83c";
const BONE = "#f0e6cc";
const INK = "#1e1410";

/** A smooth grain over the carving: lighter on the bulges, darker in the cuts. */
const grain =
  (base: ColorLike, seed: number) =>
  (p: THREE.Vector3): ColorLike => {
    const c = new THREE.Color(base);
    const k = 0.9 + 0.12 * Math.sin(p.y * 9 + seed) + 0.05 * Math.sin(p.x * 23 + p.z * 17 + seed);
    return c.multiplyScalar(k);
  };

/** One carved face of a totem, its chin at y = 0, looking along +Z. */
function carvedHead(
  b: Build,
  y: number,
  w: number,
  h: number,
  kind: number,
  paint: [string, string],
  seed: number,
) {
  // The block it's carved from: a rounded, slightly barrel-shaped drum.
  b.addColored(
    loft(
      [
        { at: [0, y, 0], rx: w * 0.92, ry: w * 0.8, sq: 2.8, color: WOOD },
        { at: [0, y + h * 0.3, 0], rx: w, ry: w * 0.86, sq: 2.8, color: WOOD },
        { at: [0, y + h * 0.75, 0], rx: w, ry: w * 0.86, sq: 2.8, color: WOOD },
        { at: [0, y + h, 0], rx: w * 0.9, ry: w * 0.78, sq: 2.8, color: WOOD },
      ],
      {
        sides: 16,
        steps: 2,
        up: [0, 0, 1],
        paint: (t, a, base) => {
          const c = new THREE.Color(base);
          // (Cuts round the drum, and the grain.)
          const cut = Math.abs(((t * 6 + 0.5) % 1) - 0.5) < 0.04 ? 0.7 : 1;
          return c.multiplyScalar(cut * (0.92 + 0.1 * Math.sin(a * 5 + seed)));
        },
      },
    ),
  );
  const fz = w * 0.82; // the front of the face
  // The brow: a heavy ridge over the eyes, painted.
  b.addColored(
    loft(
      [
        { at: [-w * 0.95, y + h * 0.7, fz * 0.75], rx: 0.12, ry: 0.14, color: paint[0] },
        { at: [-w * 0.45, y + h * 0.76, fz + 0.12], rx: 0.16, ry: 0.17, color: paint[0] },
        { at: [0, y + h * 0.7, fz + 0.16], rx: 0.15, ry: 0.15, color: paint[0] },
        { at: [w * 0.45, y + h * 0.76, fz + 0.12], rx: 0.16, ry: 0.17, color: paint[0] },
        { at: [w * 0.95, y + h * 0.7, fz * 0.75], rx: 0.12, ry: 0.14, color: paint[0] },
      ],
      { sides: 8, steps: 3, capStart: true, capEnd: true },
    ),
  );
  // The eyes: a painted ring, a white, a black pupil.
  for (const sx of [-1, 1]) {
    const ex = sx * w * 0.42;
    const ey = y + h * 0.55;
    b.add(torus(0.21, 0.06, 6, 16), paint[1], { p: [ex, ey, fz + 0.03] });
    b.add(ellipsoid(14, 10), BONE, { p: [ex, ey, fz + 0.02], s: [0.19, 0.17, 0.08] });
    b.add(ellipsoid(10, 8), INK, {
      p: [ex + sx * 0.02, ey - 0.01, fz + 0.09],
      s: [0.08, 0.09, 0.04],
    });
  }
  // The nose: a hooked beak, a broad snout, or a long nose.
  if (kind === 0) {
    b.addColored(
      loft(
        [
          { at: [0, y + h * 0.5, fz - 0.05], rx: 0.22, ry: 0.2, color: GOLD },
          { at: [0, y + h * 0.42, fz + 0.45], rx: 0.17, ry: 0.15, color: GOLD },
          { at: [0, y + h * 0.26, fz + 0.72], rx: 0.09, ry: 0.08, color: GOLD },
          { at: [0, y + h * 0.12, fz + 0.66], rx: 0.03, ry: 0.03, color: WOOD_DARK },
        ],
        { sides: 10, steps: 3, capStart: true, capEnd: true },
      ),
    );
  } else if (kind === 1) {
    b.addColored(
      loft(
        [
          { at: [0, y + h * 0.36, fz - 0.05], rx: 0.42, ry: 0.22, sq: 2.6, color: WOOD_PALE },
          { at: [0, y + h * 0.34, fz + 0.3], rx: 0.4, ry: 0.2, sq: 2.6, color: WOOD_PALE },
          { at: [0, y + h * 0.33, fz + 0.42], rx: 0.3, ry: 0.15, sq: 2.6, color: WOOD_PALE },
        ],
        { sides: 12, steps: 2, capStart: true, capEnd: true },
      ),
    );
    for (const sx of [-1, 1])
      b.add(ellipsoid(8, 6), INK, {
        p: [sx * 0.14, y + h * 0.35, fz + 0.43],
        s: [0.06, 0.05, 0.03],
      });
  } else {
    b.addColored(
      tube(
        [
          [0, y + h * 0.62, fz + 0.05],
          [0, y + h * 0.46, fz + 0.2],
          [0, y + h * 0.3, fz + 0.26],
        ],
        [0.13, 0.15, 0.1],
        WOOD_PALE,
        { sides: 10, steps: 2 },
      ),
    );
  }
  // The mouth, wide, bared teeth along it.
  b.addColored(
    loft(
      [
        { at: [-w * 0.55, y + h * 0.2, fz - 0.02], rx: 0.04, ry: 0.06, color: INK },
        { at: [0, y + h * 0.13, fz + 0.04], rx: 0.07, ry: 0.11, color: INK },
        { at: [w * 0.55, y + h * 0.2, fz - 0.02], rx: 0.04, ry: 0.06, color: INK },
      ],
      { sides: 8, steps: 3, capStart: true, capEnd: true },
    ),
  );
  for (let t = 0; t < 6; t++) {
    const x = (t - 2.5) * w * 0.17;
    b.add(box(0.1, 0.13, 0.06, 0.02), BONE, {
      p: [x, y + h * 0.2 - Math.abs(x) * 0.12, fz + 0.07],
    });
  }
  // Ears (or little wings) at its sides.
  for (const sx of [-1, 1]) {
    b.addColored(
      loft(
        [
          { at: [sx * w * 0.85, y + h * 0.5, 0], rx: 0.12, ry: 0.3, color: paint[1] },
          { at: [sx * (w + 0.3), y + h * 0.66, -0.05], rx: 0.1, ry: 0.32, color: paint[1] },
          { at: [sx * (w + 0.55), y + h * 0.9, -0.1], rx: 0.04, ry: 0.12, color: paint[0] },
        ],
        { sides: 8, steps: 2, capEnd: true, up: [0, 0, 1] },
      ),
    );
  }
  // The painted band under its chin, dots round it.
  b.add(cyl(w * 0.97, w * 0.97, 0.16, 18), paint[0], { p: [0, y + 0.02, 0], s: [1, 1, 0.88] });
  for (let k = 0; k < 10; k++) {
    const a = (k / 10) * Math.PI * 2;
    b.add(ellipsoid(8, 6), BONE, {
      p: [Math.sin(a) * w * 0.98, y + 0.02, Math.cos(a) * w * 0.86],
      s: 0.055,
    });
  }
  void grain;
}

/** The great bird on top: its body, a hooked beak, spread wings of painted feathers. */
function thunderbird(b: Build, y: number, variant: number) {
  const c1 = variant % 2 ? TEAL : RED;
  const c2 = variant % 2 ? RED : TEAL;
  b.addColored(
    loft(
      [
        { at: [0, y, -0.1], rx: 0.6, ry: 0.55, color: WOOD },
        { at: [0, y + 0.6, 0], rx: 0.72, ry: 0.65, color: WOOD },
        { at: [0, y + 1.25, 0.15], rx: 0.5, ry: 0.5, color: c1 },
        { at: [0, y + 1.75, 0.3], rx: 0.42, ry: 0.42, color: c1 },
        { at: [0, y + 2.05, 0.35], rx: 0.2, ry: 0.2, color: c1 },
      ],
      { sides: 14, steps: 2, up: [0, 0, 1], capEnd: true },
    ),
  );
  b.addColored(horn([0, y + 1.65, 0.6], [0, y + 1.25, 1.35], 0.2, GOLD, [0, 0.25, 0.1], 10));
  for (const sx of [-1, 1]) {
    b.add(ellipsoid(10, 8), BONE, { p: [sx * 0.26, y + 1.8, 0.55], s: [0.1, 0.1, 0.06] });
    b.add(ellipsoid(8, 6), INK, { p: [sx * 0.28, y + 1.8, 0.6], s: [0.05, 0.05, 0.03] });
    // The wing: an arm of the carving out to the side, rising, with feathers stepping
    // down off its trailing edge.
    const span = 3.0 + 0.3 * (variant % 3);
    const tip: V3 = [sx * span, y + 1.9, -0.05];
    b.addColored(
      loft(
        [
          { at: [sx * 0.55, y + 0.95, 0], rx: 0.26, ry: 0.42, color: WOOD },
          { at: [sx * span * 0.45, y + 1.3, 0], rx: 0.2, ry: 0.4, color: c1 },
          { at: [sx * span * 0.85, y + 1.75, -0.02], rx: 0.12, ry: 0.3, color: c2 },
          { at: tip, rx: 0.04, ry: 0.12, color: c2 },
        ],
        { sides: 10, steps: 3, capEnd: true, up: [0, 0, 1] },
      ),
    );
    for (let f = 0; f < 6; f++) {
      const t = (f + 0.5) / 6;
      const x = sx * (0.7 + (span - 0.7) * t);
      const top = y + 1.0 + 0.8 * t;
      const len = 0.9 - 0.08 * f;
      b.addColored(
        loft(
          [
            { at: [x, top, -0.02], rx: 0.15, ry: 0.06, color: f % 2 ? c2 : BONE },
            {
              at: [x + sx * 0.06, top - len * 0.6, 0],
              rx: 0.13,
              ry: 0.05,
              color: f % 2 ? c2 : BONE,
            },
            { at: [x + sx * 0.1, top - len, 0.02], rx: 0.04, ry: 0.03, color: INK },
          ],
          { sides: 6, steps: 1, capEnd: true, up: [0, 0, 1] },
        ),
      );
    }
  }
  // Its tail fanned behind.
  for (let k = -2; k <= 2; k++)
    b.addColored(
      loft(
        [
          { at: [k * 0.12, y + 0.4, -0.5], rx: 0.1, ry: 0.05, color: c2 },
          { at: [k * 0.3, y + 0.1, -1.1], rx: 0.13, ry: 0.05, color: BONE },
          { at: [k * 0.36, y - 0.05, -1.35], rx: 0.04, ry: 0.03, color: INK },
        ],
        { sides: 6, steps: 1, capEnd: true },
      ),
    );
}

/** A totem pole (about 9 m): a carved plinth, three or four faces stacked, the bird. */
export function buildTotem(variant: number): THREE.Mesh {
  const b = new Build();
  const heads = variant % 2 === 0 ? 4 : 3;
  // The plinth: a squat carved stone, its corners rounded.
  b.addColored(
    loft(
      [
        { at: [0, -0.4, 0], rx: 1.25, ry: 1.25, sq: 3.4, color: "#6e675e" },
        { at: [0, 0.3, 0], rx: 1.2, ry: 1.2, sq: 3.4, color: "#867e72" },
        { at: [0, 0.45, 0], rx: 1.05, ry: 1.05, sq: 3.4, color: "#9a9284" },
      ],
      { sides: 16, steps: 1, up: [0, 0, 1], capEnd: true },
    ),
  );
  const palette: [string, string][] = [
    [RED, TEAL],
    [TEAL, GOLD],
    [GOLD, RED],
    [RED, GOLD],
  ];
  let y = 0.45;
  for (let k = 0; k < heads; k++) {
    const w = 0.95 - 0.05 * k;
    const h = 1.7 - 0.08 * k;
    carvedHead(b, y, w, h, (k + variant) % 3, palette[(k + variant) % 4]!, k * 3 + variant);
    y += h + 0.04;
  }
  thunderbird(b, y, variant);
  const mesh = new THREE.Mesh(b.build(), skinMaterial());
  mesh.castShadow = false;
  return mesh;
}

/** The kart up on its blocks in the repair shed, taken apart: no wheels on it, one
 * leaning on its side, two lying flat one on the other, the last against the blocks. */
export function buildKartWreck(): THREE.Group {
  const kit = sleekKart({
    main: "#b0602e",
    dark: "#7a3e1e",
    stripe: "#e8c060",
    nose: "#8a8478",
    trim: "#5a5650",
    metal: "#7a746c",
    seat: "#4a2e1e",
    glass: "#c8d8d0",
    tyre: "#2a2626",
    rim: "#a09a90",
    cap: "#5a5650",
    tyreLine: "#e8c060",
    front: "blade",
    pods: "intake",
    rear: "wing",
    emblem: { kind: "spiral", disc: "#e8c060", ink: "#7a3e1e", rim: "#5a5650" },
    spokes: 5,
  });
  const kart = buildKart(kit, 0);
  const root = new THREE.Group();
  root.name = "kart wreck";
  // Up on the blocks (no wheels under it): its belly on them.
  kart.body.position.y = 0.12;
  root.add(kart.root);
  const spots: { p: V3; r: V3 }[] = [
    { p: [1.25, 0.4, 0.55], r: [0, 0, 0.32] }, // leaning on its side
    { p: [-1.35, 0.17, -0.55], r: [0, 0, Math.PI / 2] }, // lying flat
    { p: [-1.38, 0.51, -0.5], r: [0, 0.4, Math.PI / 2] }, // and one on it
    { p: [0.95, 0.36, -1.1], r: [0.12, 0.6, 0] }, // propped against the blocks
  ];
  kart.wheels.forEach((w, i) => {
    const s = spots[i]!;
    w.pivot.position.set(...s.p);
    w.pivot.rotation.set(...s.r);
  });
  return root;
}

const BONE_HI = "#efe4c8";
const BONE_LO = "#b8a482";
const CRACK = "#6a5a42";
const MOSS = "#5a7a32";

/** Old bone: ivory, yellowing low down, cracked and stained, moss where rain sits. */
function oldBone(seed: number) {
  const hi = new THREE.Color(BONE_HI);
  const lo = new THREE.Color(BONE_LO);
  const crack = new THREE.Color(CRACK);
  const moss = new THREE.Color(MOSS);
  return (p: THREE.Vector3, n: THREE.Vector3): ColorLike => {
    const c = lo.clone().lerp(hi, Math.min(1, Math.max(0, 0.35 + p.y * 0.18)));
    const w = Math.sin(p.x * 3.1 + p.z * 1.7 + seed) * Math.sin(p.y * 2.3 - p.z * 2.9 + seed * 2);
    if (Math.abs(w) < 0.05) c.lerp(crack, 0.7);
    c.multiplyScalar(0.92 + 0.1 * Math.sin(p.x * 11 + p.y * 7 + p.z * 13));
    if (n.y > 0.6 && Math.sin(p.x * 1.3 + seed) * Math.cos(p.z * 1.1) > 0.35) c.lerp(moss, 0.65);
    return c;
  };
}

/** A great horned skull (about 9 m long at scale 1, facing +Z, lying on the ground): a
 * broad cranium and a deep snout ending in a hooked beak, long brow horns sweeping
 * forward, a short nose horn, a wide frill behind with a scalloped, knobbed edge and two
 * windows through it, dark eye sockets with heavy rims, the lower jaw lying apart. */
export function buildHornedSkull(): THREE.Mesh {
  const b = new Build();
  const bone = oldBone(3);
  const colorise = (g: THREE.BufferGeometry) => {
    const pos = g.getAttribute("position");
    const nor = g.getAttribute("normal");
    const cols = new Float32Array(pos.count * 3);
    const p = new THREE.Vector3();
    const n = new THREE.Vector3();
    for (let i = 0; i < pos.count; i++) {
      const c = new THREE.Color(bone(p.fromBufferAttribute(pos, i), n.fromBufferAttribute(nor, i)));
      cols.set([c.r, c.g, c.b], i * 3);
    }
    g.setAttribute("color", new THREE.BufferAttribute(cols, 3));
    return g;
  };
  // (A triceratops's, unmistakably: Blake, Riverbend note 7, "this is better but it needs
  // to look more like a triceratops skull". A short, deep face; two long brow horns
  // sweeping forward over the eyes; a stubby nose horn; a hooked beak; and the great frill
  // fanned up and back behind it all, spikes all round its edge.)
  // The cranium and face, one loft from the back of the head to the beak's root.
  b.addColored(
    colorise(
      loft(
        [
          { at: [0, 1.6, -1.6], rx: 1.7, ry: 1.35, sq: 2.4 },
          { at: [0, 1.9, -0.7], rx: 2.05, ry: 1.7, sq: 2.5 },
          { at: [0, 1.95, 0.5], rx: 1.9, ry: 1.7, sq: 2.6 },
          { at: [0, 1.75, 1.6], rx: 1.4, ry: 1.55, sq: 2.6, flat: 0.15 },
          { at: [0, 1.45, 2.6], rx: 0.95, ry: 1.3, sq: 2.6, flat: 0.2 },
          { at: [0, 1.2, 3.4], rx: 0.6, ry: 0.95, sq: 2.4, flat: 0.2 },
        ],
        { sides: 18, steps: 3, capStart: true, capEnd: true },
      ),
    ),
  );
  // The beak: deep and hooked down, like a parrot's.
  b.addColored(
    colorise(
      loft(
        [
          { at: [0, 1.25, 3.3], rx: 0.55, ry: 0.85 },
          { at: [0, 1.0, 3.95], rx: 0.36, ry: 0.65 },
          { at: [0, 0.55, 4.35], rx: 0.18, ry: 0.38 },
          { at: [0, 0.12, 4.4], rx: 0.04, ry: 0.08 },
        ],
        { sides: 12, steps: 3, capStart: true, capEnd: true },
      ),
    ),
  );
  // The brow horns: long, thick at the root, curving up and then forward over the beak.
  for (const sx of [-1, 1]) {
    b.addColored(
      colorise(
        loft(
          [
            { at: [sx * 0.9, 2.9, 0.3], rx: 0.55, ry: 0.55 },
            { at: [sx * 1.05, 4.2, 1.0], rx: 0.42, ry: 0.42 },
            { at: [sx * 1.1, 5.2, 2.2], rx: 0.28, ry: 0.28 },
            { at: [sx * 1.0, 5.6, 3.6], rx: 0.14, ry: 0.14 },
            { at: [sx * 0.9, 5.55, 4.6], rx: 0.03, ry: 0.03 },
          ],
          { sides: 12, steps: 3, capStart: true, capEnd: true },
        ),
      ),
    );
    // The eye socket under each horn's root: a heavy rim round a dark hole.
    b.add(torus(0.42, 0.14, 8, 16), BONE_LO, {
      p: [sx * 1.6, 2.2, 0.15],
      r: [0, sx * 1.2, 0],
    });
    b.add(ellipsoid(12, 8), "#1a1410", { p: [sx * 1.55, 2.2, 0.15], s: [0.12, 0.36, 0.36] });
    // The cheek horns, low and out to the sides (the jugals).
    b.addColored(
      colorise(horn([sx * 1.7, 1.15, -0.3], [sx * 2.7, 0.8, 0.0], 0.34, BONE_HI, [0, -0.1, 0], 10)),
    );
  }
  // The nose horn: short and stubby, up from the snout.
  b.addColored(colorise(horn([0, 2.45, 2.4], [0, 3.35, 2.95], 0.36, BONE_HI, [0, 0.05, 0.08], 10)));
  b.add(ellipsoid(10, 8), "#1a1410", { p: [0, 1.75, 3.0], s: [0.3, 0.26, 0.35] });
  // The frill: a broad shield fanned up and back from the back of the skull, its edge
  // scalloped and set with spikes (the epoccipitals), two windows through it.
  const outline: [number, number][] = [];
  const N = 30;
  const R = 4.9;
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * Math.PI;
    const r = R + 0.3 * Math.cos(i * Math.PI); // (scallops)
    outline.push([Math.cos(a) * r * 1.05, Math.sin(a) * r * 1.15]);
  }
  outline.push([-1.8, -0.3], [1.8, -0.3]);
  const LEAN = -0.4; // (back from upright: the fan stands over the head, from in front or the side)
  const frill = colorise(card(outline, 0.38));
  b.addColored(frill, { p: [0, 1.7, -1.5], r: [LEAN, 0, 0] });
  // A ridge up the middle of it.
  b.addColored(
    colorise(
      card(
        [
          [-0.3, 0],
          [0.3, 0],
          [0.18, (R - 0.4) * 1.15],
          [-0.18, (R - 0.4) * 1.15],
        ],
        0.6,
      ),
    ),
    {
      p: [0, 1.7, -1.5],
      r: [LEAN, 0, 0],
    },
  );
  const tilt = new THREE.Matrix4().makeRotationX(LEAN);
  for (let i = 1; i < N; i += 2) {
    const a = (i / N) * Math.PI;
    const r0 = R + 0.15;
    const base = new THREE.Vector3(
      Math.cos(a) * r0 * 1.05,
      Math.sin(a) * r0 * 1.15,
      0,
    ).applyMatrix4(tilt);
    const tip = new THREE.Vector3(
      Math.cos(a) * (r0 + 0.95) * 1.05,
      Math.sin(a) * (r0 + 0.95) * 1.15,
      0,
    ).applyMatrix4(tilt);
    b.addColored(
      colorise(
        horn(
          [base.x, base.y + 1.7, base.z - 1.5],
          [tip.x, tip.y + 1.7, tip.z - 1.5],
          0.3,
          BONE_HI,
          [0, 0, 0],
          8,
        ),
      ),
    );
  }
  for (const sx of [-1, 1]) {
    const v = new THREE.Vector3(sx * 1.9, 3.4, 0).applyMatrix4(tilt);
    for (const off of [0.21, -0.21]) {
      const w = new THREE.Vector3(0, 0, off).applyMatrix4(tilt);
      b.add(ellipsoid(14, 10), "#5a4e3e", {
        p: [v.x, v.y + 1.7 + w.y, v.z - 1.5 + w.z],
        s: [0.6, 0.75, 0.06],
        r: [LEAN, 0, 0],
      });
    }
  }
  // The lower jaw, fallen apart: two bones lying in front.
  for (const sx of [-1, 1])
    b.addColored(
      colorise(
        loft(
          [
            { at: [sx * 1.3, 0.45, -0.4], rx: 0.42, ry: 0.55 },
            { at: [sx * 1.05, 0.38, 1.3], rx: 0.32, ry: 0.45 },
            { at: [sx * 0.55, 0.32, 2.8], rx: 0.22, ry: 0.3 },
            { at: [sx * 0.2, 0.28, 3.5], rx: 0.15, ry: 0.2 },
          ],
          { sides: 10, steps: 2, capStart: true, capEnd: true },
        ),
      ),
      { r: [0, sx * 0.08, sx * 0.1] },
    );
  const mesh = new THREE.Mesh(b.build(), skinMaterial());
  return mesh;
}

/** The decor among a track's entities, added under `parent`: the carved and built pieces,
 * and the living fires (`fire` { "x", "y", "z", "size" }: the fire's base). update(t)
 * plays the fires; dispose() takes it all away. */
/** The flames modelled into the scenery (campfires, braziers, torches), by their
 * materials' names: they give way to the living fire (render/fire.ts). */
const FLAME = /campfire[ _]flame|keep[ _]flame|torch[ _]flame|brazier[ _]fire/i;

/** Where the scenery's own flames stand: each one's foot and height, its faces hidden.
 * (Blake, Oct 29: "now that we have high fidelity torches in the tunnel ... lets replace
 * all fire with this.") */
function modelledFlames(visual: THREE.Object3D) {
  const cells = new Map<string, { x: number; z: number; y0: number; y1: number; n: number }>();
  const v = new THREE.Vector3();
  visual.updateMatrixWorld(true);
  visual.traverse((o) => {
    if (!(o instanceof THREE.Mesh)) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const hit = mats.map((m) => FLAME.test(m?.name ?? "") || FLAME.test(m?.map?.name ?? ""));
    if (!hit.some(Boolean)) return;
    const geo = o.geometry as THREE.BufferGeometry;
    const pos = geo.getAttribute("position");
    const idx = geo.getIndex();
    const groups = geo.groups.length
      ? geo.groups
      : [{ start: 0, count: idx ? idx.count : pos.count, materialIndex: 0 }];
    for (const g of groups) {
      if (!hit[g.materialIndex ?? 0]) continue;
      for (let i = g.start; i < g.start + g.count; i++) {
        v.fromBufferAttribute(pos, idx ? idx.getX(i) : i).applyMatrix4(o.matrixWorld);
        const key = `${Math.round(v.x / 1.6)},${Math.round(v.z / 1.6)}`;
        const c = cells.get(key);
        if (c) {
          c.x += v.x;
          c.z += v.z;
          c.n++;
          c.y0 = Math.min(c.y0, v.y);
          c.y1 = Math.max(c.y1, v.y);
        } else cells.set(key, { x: v.x, z: v.z, y0: v.y, y1: v.y, n: 1 });
      }
    }
    for (let i = 0; i < mats.length; i++) if (hit[i] && mats[i]) mats[i]!.visible = false;
  });
  // (Neighbouring cells of one flame joined: a flame is one fire.)
  const out: { x: number; y: number; z: number; h: number }[] = [];
  for (const c of cells.values()) {
    const x = c.x / c.n;
    const z = c.z / c.n;
    const near = out.find((f) => Math.hypot(f.x - x, f.z - z) < 1.8 && Math.abs(f.y - c.y0) < 2.0);
    if (near) {
      near.h = Math.max(near.h, c.y1 - near.y);
      near.y = Math.min(near.y, c.y0);
      continue;
    }
    out.push({ x, y: c.y0, z, h: c.y1 - c.y0 });
  }
  return out;
}

/** How far off a fire still burns (m), and the most that burn at once. */
const FIRE_RANGE = 90;
const FIRES_MAX = 36;

export function createVillageDecor(
  parent: THREE.Object3D,
  entities: unknown[],
  visual?: THREE.Object3D,
): { update(t: number, eye?: THREE.Vector3): void; dispose(): void } {
  const group = new THREE.Group();
  group.name = "village decor";
  const fires: Fire[] = [];
  const num = (v: unknown, d = 0) => (typeof v === "number" && Number.isFinite(v) ? v : d);
  // Every fire in the world the living one: the scenery's own flames, then the torches'
  // and campfires' where no flame was modelled.
  const spots: { x: number; y: number; z: number; size: number }[] = [];
  if (visual)
    for (const f of modelledFlames(visual))
      spots.push({ x: f.x, y: f.y, z: f.z, size: Math.max(0.35, Math.min(2.2, f.h / 1.7)) });
  for (const e of entities) {
    if (!e || typeof e !== "object") continue;
    const o = e as Record<string, unknown>;
    if (o.type !== "torch" && o.type !== "campfire") continue;
    const x = num(o.x);
    const y = num(o.y);
    const z = num(o.z);
    if (spots.some((s) => Math.hypot(s.x - x, s.z - z) < 1.8 && Math.abs(s.y - y) < 3)) continue;
    spots.push(
      o.type === "torch" ? { x, y: y - 0.45, z, size: 0.5 } : { x, y: y - 0.3, z, size: 1.0 },
    );
  }
  const living: { fire: Fire; x: number; y: number; z: number; d: number }[] = [];
  const near: typeof living = [];
  for (const s of spots) {
    const f = createFire({ size: s.size, seed: living.length * 2.3 });
    f.group.position.set(s.x, s.y, s.z);
    group.add(f.group);
    living.push({ fire: f, x: s.x, y: s.y, z: s.z, d: 0 });
  }
  for (const e of entities) {
    if (!e || typeof e !== "object") continue;
    const o = e as Record<string, unknown>;
    let obj: THREE.Object3D | undefined;
    if (o.type === "village_totem") obj = buildTotem(Math.round(num(o.variant)));
    else if (o.type === "kart_wreck") obj = buildKartWreck();
    else if (o.type === "horned_skull") {
      obj = buildHornedSkull();
      obj.scale.setScalar(num(o.scale, 1));
    } else if (o.type === "fire") {
      const f = createFire({ size: num(o.size, 1), red: o.red === true, seed: fires.length * 1.7 });
      fires.push(f);
      obj = f.group;
    }
    if (!obj) continue;
    obj.position.set(num(o.x), num(o.y), num(o.z));
    obj.rotation.y = num(o.heading);
    group.add(obj);
  }
  if (group.children.length) parent.add(group);
  // The lily pads and lotus flowers ride the water, rising and falling a little and
  // rocking, each in its own time (Blake, Riverbend note 15).
  // (Drawn instanced: one draw for every pad of a kind, not one each, the lag, Oct 29.)
  const floats: {
    o: THREE.Object3D;
    y: number;
    rx: number;
    rz: number;
    ph: number;
    sp: number;
    parts: { inst: THREE.InstancedMesh; i: number; local: THREE.Matrix4 }[];
  }[] = [];
  const insts = new Map<string, { inst?: THREE.InstancedMesh; mesh: THREE.Mesh; n: number }>();
  const FLOAT = /^(Lily_Pad|Lotus)/;
  visual?.traverse((o) => {
    if (!FLOAT.test(o.name) || (o.parent && FLOAT.test(o.parent.name))) return;
    const ph = (o.position.x * 0.37 + o.position.z * 0.23) % (Math.PI * 2);
    floats.push({
      o,
      y: o.position.y,
      rx: o.rotation.x,
      rz: o.rotation.z,
      ph,
      sp: 1.1 + (ph % 0.5),
      parts: [],
    });
    o.traverse((m) => {
      const mesh = m as THREE.Mesh;
      if (!mesh.isMesh || Array.isArray(mesh.material)) return;
      const key = `${mesh.geometry.uuid}|${mesh.material.uuid}`;
      const e = insts.get(key);
      if (e) e.n++;
      else insts.set(key, { mesh, n: 1 });
    });
  });
  const floatRoot = new THREE.Group();
  floatRoot.name = "floating (instanced)";
  const fm = new THREE.Matrix4();
  if (visual && floats.length) {
    visual.updateMatrixWorld(true);
    const invRoot = new THREE.Matrix4().copy(visual.matrixWorld).invert();
    for (const e of insts.values()) {
      e.inst = new THREE.InstancedMesh(e.mesh.geometry, e.mesh.material as THREE.Material, e.n);
      e.inst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      e.inst.frustumCulled = false;
      e.n = 0;
      floatRoot.add(e.inst);
    }
    for (const f of floats) {
      const toFloat = new THREE.Matrix4().copy(f.o.matrixWorld).invert();
      f.o.traverse((m) => {
        const mesh = m as THREE.Mesh;
        if (!mesh.isMesh || Array.isArray(mesh.material)) return;
        const e = insts.get(`${mesh.geometry.uuid}|${mesh.material.uuid}`)!;
        const local = new THREE.Matrix4().multiplyMatrices(toFloat, mesh.matrixWorld);
        f.parts.push({ inst: e.inst!, i: e.n, local });
        e.inst!.setMatrixAt(e.n++, fm.multiplyMatrices(invRoot, mesh.matrixWorld));
      });
      f.o.visible = false;
    }
    visual.add(floatRoot);
    // (The review tool shows the pads themselves, to pick them.)
    visual.userData.floating = {
      off() {
        floatRoot.visible = false;
        for (const f of floats) f.o.visible = true;
      },
    };
  }
  return {
    update(t, eye) {
      const live = floatRoot.visible;
      const touched = new Set<THREE.InstancedMesh>();
      for (const f of floats) {
        if (eye && Math.hypot(f.o.position.x - eye.x, f.o.position.z - eye.z) > 120) continue;
        const a = t * f.sp + f.ph;
        f.o.position.y = f.y + Math.sin(a) * 0.045;
        f.o.rotation.x = f.rx + Math.sin(a * 0.8 + 1.3) * 0.035;
        f.o.rotation.z = f.rz + Math.cos(a * 0.7) * 0.035;
        if (!live) continue;
        // (Each pad hangs right under the track's root: its own matrix is its place.)
        f.o.updateMatrix();
        for (const p of f.parts) {
          p.inst.setMatrixAt(p.i, fm.multiplyMatrices(f.o.matrix, p.local));
          touched.add(p.inst);
        }
      }
      for (const inst of touched) inst.instanceMatrix.needsUpdate = true;
      for (const f of fires) f.update(t);
      // (Only the fires near enough to see are drawn and kept burning, and no more than
      // FIRES_MAX of them, the nearest: Blake, Oct 29, the lag in Ember, where 130 burned
      // at once.)
      near.length = 0;
      for (const l of living) {
        l.d = eye ? Math.hypot(l.x - eye.x, l.y - eye.y, l.z - eye.z) : 0;
        l.fire.group.visible = false;
        if (l.d < FIRE_RANGE) near.push(l);
      }
      if (near.length > FIRES_MAX) near.sort((a, b) => a.d - b.d).length = FIRES_MAX;
      for (const l of near) {
        l.fire.group.visible = true;
        l.fire.update(t);
      }
    },
    dispose() {
      for (const f of fires) f.dispose();
      for (const l of living) l.fire.dispose();
      group.removeFromParent();
      group.traverse((o) => {
        if (o instanceof THREE.Mesh) o.geometry.dispose();
      });
    },
  };
}
