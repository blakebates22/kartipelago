/**
 * Baby dinosaurs for the Beast Market's pens (Blake, Nov 4: "the animals look bad"; he
 * picked "baby dinos in pens"): hatchling raptors, triceratops and stegosaurs, chunky and
 * big-eyed, each a few meshes (body, head, legs, tail) in vertex colours with one shared
 * material; in detail (Nov 5, review note 3: "we need to increase the fidelity of these
 * dinsouars"): smooth, shaded to the belly, striped or spotted, glossy eyes with lids,
 * nostrils, little teeth, toes and claws; the raptor's down and tail fan, the trike's
 * scalloped frill and horns, the stegosaur's plates and spikes. Animated: a waddling walk with the tail swinging and the head bobbing, a peck
 * at the hay, a look round, a sit, a squeak with the mouth open.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export type HatchlingKind = "raptor" | "trike" | "stego";
export const HATCHLING_KINDS: readonly HatchlingKind[] = ["raptor", "trike", "stego"];

/** What it's doing: walking (0..1, how fast), or one of its idles. */
export type HatchlingAct = "walk" | "peck" | "look" | "sit" | "squeak";

export interface HatchlingView {
  readonly root: THREE.Group;
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    act: HatchlingAct,
    pace: number,
    t: number,
  ): void;
  dispose(): void;
}

const LOOKS: Record<HatchlingKind, [string, string, string][]> = {
  // (skin, belly, markings: stripes, spots or plates)
  raptor: [
    ["#4f9a6e", "#efe2b8", "#c8622c"],
    ["#b8692e", "#f4dcae", "#4a2e6a"],
    ["#6e8a3c", "#ece8c0", "#2a4a6a"],
  ],
  trike: [
    ["#6f8cb8", "#ece8e0", "#d0a83a"],
    ["#a87648", "#f2e2c8", "#6a3424"],
    ["#86a85a", "#eef0d0", "#c45e34"],
  ],
  stego: [
    ["#7a9a46", "#eceabe", "#c8582e"],
    ["#a88e4c", "#f2e8c8", "#3a6a7a"],
    ["#8a6aa8", "#ece2f0", "#e0942a"],
  ],
};

const tc = new THREE.Color();
const tb = new THREE.Color();
const tm = new THREE.Color();

/**
 * Paint a piece (after placing it): its colour shaded toward the belly underneath and
 * darker along the back, and its markings by `mark(x, y, z)` (body space; 0..1, how much).
 */
function painted(
  g: THREE.BufferGeometry,
  color: string,
  m?: THREE.Matrix4,
  shade?: { belly?: string; mark?: string; at?: (x: number, y: number, z: number) => number },
) {
  // (smooth: normals from the indexed shape, carried through the placing)
  if (!g.attributes.normal) g.computeVertexNormals();
  if (m) g.applyMatrix4(m);
  const geo = g.index ? g.toNonIndexed() : g;
  const pos = geo.attributes.position!;
  const nor = geo.attributes.normal!;
  const n = pos.count;
  const col = new Float32Array(n * 3);
  tc.set(color);
  if (shade?.belly) tb.set(shade.belly);
  if (shade?.mark) tm.set(shade.mark);
  const c = new THREE.Color();
  for (let i = 0; i < n; i++) {
    c.copy(tc);
    const ny = nor.getY(i);
    if (shade?.belly && ny < -0.15) c.lerp(tb, Math.min(1, (-ny - 0.15) * 1.6));
    if (shade?.mark && shade.at) {
      const k = shade.at(pos.getX(i), pos.getY(i), pos.getZ(i));
      if (k > 0 && ny > -0.2) c.lerp(tm, Math.min(1, k));
    }
    // (a little darker along the back, lighter in the light)
    c.multiplyScalar(0.92 + 0.12 * Math.max(0, ny) - (ny > 0.7 ? 0.06 : 0));
    col.set([c.r, c.g, c.b], i * 3);
  }
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  geo.deleteAttribute("uv");
  return geo;
}
const colored = (g: THREE.BufferGeometry, color: string, m?: THREE.Matrix4) => painted(g, color, m);

const M = (x: number, y: number, z: number, sx = 1, sy = 1, sz = 1, rx = 0, ry = 0, rz = 0) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
    new THREE.Vector3(sx, sy, sz),
  );
const ball = (r = 1, w = 18, h = 12) => new THREE.SphereGeometry(r, w, h);
/** A tapered limb or neck along +z, r0 at z 0 to r1 at z len. */
const taper = (r0: number, r1: number, len: number, seg = 12) =>
  new THREE.CylinderGeometry(r1, r0, len, seg, 2).rotateX(Math.PI / 2).translate(0, 0, len / 2);
const cone = (r: number, h: number, seg = 8) => new THREE.ConeGeometry(r, h, seg);
const hash = (x: number, y: number, z: number) => {
  const v = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
  return v - Math.floor(v);
};
/** Spots, roughly round, scattered (0..1 inside one). */
const spots = (cell: number, size: number) => (x: number, y: number, z: number) => {
  const ix = Math.floor(x / cell);
  const iy = Math.floor(y / cell);
  const iz = Math.floor(z / cell);
  const h = hash(ix, iy, iz);
  if (h < 0.45) return 0;
  const cx = (ix + 0.25 + 0.5 * hash(iz, ix, iy)) * cell;
  const cy = (iy + 0.25 + 0.5 * hash(iy, iz, ix)) * cell;
  const cz = (iz + 0.25 + 0.5 * h) * cell;
  const d = Math.hypot(x - cx, y - cy, z - cz) / (cell * size);
  return d < 1 ? 1 - d * d * 0.5 : 0;
};

interface Parts {
  body: THREE.BufferGeometry;
  head: THREE.BufferGeometry;
  jaw: THREE.BufferGeometry;
  leg: THREE.BufferGeometry;
  /** Hind legs, where they differ from the front (the stegosaur's longer ones). */
  hind?: THREE.BufferGeometry;
  arm?: THREE.BufferGeometry;
  tail: THREE.BufferGeometry[];
  /** Where things hang off the body (body space). */
  neck: THREE.Vector3;
  hips: { x: number; z: number }[];
  hipY: number;
  tailAt: THREE.Vector3;
  quad: boolean;
}

const cache = new Map<string, Parts>();

/** A big glossy eye: the white, the iris, the pupil, a catchlight, a lid over its top. */
function eye(sd: number, x: number, y: number, z: number, r: number, skin: string, iris: string) {
  return [
    colored(ball(r, 14, 10), "#f6f2e6", M(sd * x, y, z)),
    colored(
      ball(r * 0.7, 12, 8),
      iris,
      M(sd * (x + r * 0.32), y + r * 0.02, z + r * 0.45, 1, 1, 0.6),
    ),
    colored(
      ball(r * 0.42, 10, 6),
      "#14100c",
      M(sd * (x + r * 0.42), y + r * 0.04, z + r * 0.6, 1, 1, 0.6),
    ),
    colored(ball(r * 0.14, 6, 4), "#ffffff", M(sd * (x + r * 0.55), y + r * 0.32, z + r * 0.78)),
    // (the lid, half over the top, and a brow ridge)
    colored(
      new THREE.SphereGeometry(r * 1.08, 14, 8, 0, Math.PI * 2, 0, Math.PI * 0.42),
      skin,
      M(sd * x, y, z, 1, 1, 1, -0.35),
    ),
  ];
}

function build(kind: HatchlingKind, look: number): Parts {
  const key = `${kind}|${look}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const [skin, belly, mark] = LOOKS[kind][look % LOOKS[kind].length]!;
  const iris = ["#d8a020", "#7aa030", "#c86a20"][look % 3]!;
  let p: Parts;
  if (kind === "raptor") {
    // (stripes across its back; downy feathers in a crest down its neck and back, and a fan
    // at the tail's tip; a hooked claw on each foot)
    const stripes = (_x: number, y: number, z: number) =>
      y > 0.05 && Math.sin(z * 34) > 0.35 ? 1 : 0;
    const sk = { belly, mark, at: stripes };
    const body = [
      painted(ball(), skin, M(0, 0, 0.02, 0.21, 0.2, 0.34, -0.15), sk),
      painted(ball(), skin, M(0, -0.01, -0.14, 0.2, 0.19, 0.2), sk),
      // (the neck, up and forward)
      painted(taper(0.13, 0.085, 0.24), skin, M(0, 0.06, 0.22, 1, 1, 1, -0.75), { belly }),
    ];
    for (let k = 0; k < 6; k++)
      body.push(
        colored(
          cone(0.035, 0.12, 5),
          k % 2 ? mark : skin,
          M(0, 0.21 - Math.abs(k - 2) * 0.012, 0.16 - k * 0.075, 0.6, 1, 1.4, -0.9),
        ),
      );
    const head = [
      painted(ball(), skin, M(0, 0.06, 0.02, 0.13, 0.13, 0.15), { belly }),
      // (the snout, long and a little flat, nostrils at its end)
      painted(taper(0.1, 0.045, 0.22), skin, M(0, 0.02, 0.06, 1, 0.68, 1), { belly }),
      colored(ball(0.012, 6, 4), "#2a1a12", M(0.025, 0.04, 0.27)),
      colored(ball(0.012, 6, 4), "#2a1a12", M(-0.025, 0.04, 0.27)),
      // (its mouth's line, little teeth showing)
      colored(new THREE.BoxGeometry(0.1, 0.006, 0.17), "#3a2418", M(0, 0.0, 0.18)),
      ...[-1, 1].flatMap((sd) =>
        [0, 1, 2].map((k) =>
          colored(
            cone(0.007, 0.018, 4),
            "#f8f4e8",
            M(sd * (0.042 - k * 0.006), -0.008, 0.2 + k * 0.03, 1, 1, 1, Math.PI),
          ),
        ),
      ),
      ...eye(-1, 0.08, 0.1, 0.06, 0.058, skin, iris),
      ...eye(1, 0.08, 0.1, 0.06, 0.058, skin, iris),
      // (its crest of down)
      ...[0, 1, 2].map((k) =>
        colored(
          cone(0.025, 0.1 - k * 0.02, 5),
          mark,
          M(0, 0.19 - k * 0.01, 0.0 - k * 0.055, 0.6, 1, 1.3, -0.9),
        ),
      ),
    ];
    p = {
      body: mergeGeometries(body)!,
      head: mergeGeometries(head)!,
      jaw: mergeGeometries([
        painted(taper(0.075, 0.035, 0.18), belly, M(0, -0.035, 0.06, 1, 0.45, 1)),
        ...[-1, 1].map((sd) =>
          colored(cone(0.006, 0.016, 4), "#f8f4e8", M(sd * 0.03, -0.018, 0.2)),
        ),
      ])!,
      leg: mergeGeometries([
        painted(ball(), skin, M(0, -0.04, 0.0, 0.09, 0.13, 0.11), { belly }),
        painted(taper(0.04, 0.03, 0.15), skin, M(0, -0.12, 0.02, 1, 1, 1, Math.PI / 2 + 0.3)),
        // (three toes forward, the hooked claw held up off the ground)
        ...[-1, 0, 1].map((k) =>
          colored(
            taper(0.018, 0.01, 0.08),
            skin,
            M(k * 0.025, -0.26, 0.03, 1, 1, 1, 0, k * 0.25, 0),
          ),
        ),
        ...[-1, 0, 1].map((k) =>
          colored(
            cone(0.009, 0.03, 4),
            "#2a2018",
            M(k * 0.027 + k * 0.01, -0.26, 0.12, 1, 1, 1, Math.PI / 2),
          ),
        ),
        colored(cone(0.014, 0.06, 5), "#2a2018", M(0.02, -0.22, 0.03, 1, 1, 1, 0.6)),
      ])!,
      arm: mergeGeometries([
        painted(taper(0.03, 0.02, 0.1), skin, M(0, -0.02, 0.0, 1, 1, 1, 0.9)),
        // (three little clawed fingers; a tuft of down off the arm)
        ...[-1, 0, 1].map((k) =>
          colored(cone(0.007, 0.035, 4), "#f4f0e0", M(k * 0.012, -0.075, 0.08, 1, 1, 1, 1.9)),
        ),
        colored(cone(0.02, 0.08, 4), mark, M(0, 0.0, -0.03, 0.4, 1, 1, -2.2)),
      ])!,
      tail: [0, 1, 2].map((k) =>
        mergeGeometries([
          painted(
            taper(0.11 - k * 0.032, 0.08 - k * 0.03, 0.22),
            skin,
            M(0, 0, 0.01, 1, 0.9, 1, 0, Math.PI, 0),
            sk,
          ),
          ...(k === 2
            ? [-1, 0, 1].map((q) =>
                colored(
                  cone(0.03, 0.14, 4),
                  q ? mark : skin,
                  M(q * 0.035, 0.0, -0.26, 0.5, 1, 1, -Math.PI / 2, 0, q * 0.3),
                ),
              )
            : []),
        ])!,
      ),
      neck: new THREE.Vector3(0, 0.2, 0.36),
      hips: [
        { x: -0.13, z: -0.08 },
        { x: 0.13, z: -0.08 },
      ],
      hipY: 0.29,
      tailAt: new THREE.Vector3(0, 0.04, -0.3),
      quad: false,
    };
  } else if (kind === "trike") {
    // (spotted; the frill scalloped round its edge with little knobs, a hooked beak, the
    // nose horn and the two brow horns still stubby)
    const sk = { belly, mark, at: spots(0.11, 0.45) };
    const body = [
      painted(ball(), skin, M(0, 0, 0, 0.3, 0.25, 0.4), sk),
      painted(ball(), skin, M(0, 0.02, -0.18, 0.27, 0.23, 0.24), sk),
      // (a ridge of bumps down its back)
      ...[0, 1, 2, 3, 4].map((k) =>
        colored(ball(0.04, 8, 6), mark, M(0, 0.24 - Math.abs(k - 2) * 0.015, 0.2 - k * 0.1)),
      ),
    ];
    const frill = new THREE.CircleGeometry(0.25, 20, 0, Math.PI);
    const head: THREE.BufferGeometry[] = [
      painted(ball(), skin, M(0, 0.04, 0.05, 0.16, 0.15, 0.17), { belly }),
      painted(taper(0.11, 0.07, 0.14), skin, M(0, -0.01, 0.1, 1, 0.9, 1), { belly }),
      // (the beak, hooked)
      colored(cone(0.055, 0.1, 8), "#d8c890", M(0, -0.03, 0.27, 1, 1.1, 1, Math.PI / 2 + 0.35)),
      ...eye(-1, 0.095, 0.1, 0.09, 0.056, skin, iris),
      ...eye(1, 0.095, 0.1, 0.09, 0.056, skin, iris),
      // (the frill, both faces, its knobs)
      colored(frill.clone(), mark, M(0, 0.12, -0.07, 1, 1, 1, -1.05)),
      colored(frill, skin, M(0, 0.12, -0.075, 1, 1, 1, -1.05 + Math.PI, Math.PI, 0)),
      ...Array.from({ length: 9 }, (_, k) => {
        const a = (k / 8) * Math.PI;
        const ex = Math.cos(a) * 0.25;
        const ey = Math.sin(a) * 0.25;
        return colored(
          cone(0.025, 0.05, 5),
          "#f0e4c4",
          M(ex, 0.12 + ey * 0.5, -0.07 - ey * 0.86, 1, 1, 1, -1.05 + 0.0, 0, -a + Math.PI / 2),
        );
      }),
      colored(cone(0.022, 0.07, 6), "#f4ecd8", M(0, 0.09, 0.22, 1, 1, 1, 0.5)),
      ...[-1, 1].map((sd) =>
        colored(
          cone(0.025, 0.11, 6),
          "#f4ecd8",
          M(sd * 0.07, 0.19, 0.08, 1, 1, 1, 0.6, 0, -sd * 0.25),
        ),
      ),
      // (the cheek knobs)
      ...[-1, 1].map((sd) =>
        colored(cone(0.02, 0.05, 5), "#e8dcc0", M(sd * 0.13, -0.0, 0.08, 1, 1, 1, 0, 0, -sd * 1.4)),
      ),
    ];
    p = {
      body: mergeGeometries(body)!,
      head: mergeGeometries(head)!,
      jaw: painted(taper(0.07, 0.03, 0.14), belly, M(0, -0.07, 0.12, 1, 0.5, 1)),
      leg: mergeGeometries([
        painted(taper(0.075, 0.06, 0.2), skin, M(0, 0.0, 0, 1, 1, 1, Math.PI / 2), { belly }),
        painted(ball(), skin, M(0, -0.2, 0.02, 0.07, 0.035, 0.08)),
        ...[-1, 0, 1].map((k) => colored(ball(0.018, 6, 4), "#e8dcc0", M(k * 0.035, -0.2, 0.085))),
      ])!,
      tail: [0, 1, 2].map((k) =>
        painted(
          taper(0.13 - k * 0.04, 0.09 - k * 0.035, 0.22),
          skin,
          M(0, 0, 0.01, 1, 0.85, 1, 0, Math.PI, 0),
          sk,
        ),
      ),
      neck: new THREE.Vector3(0, 0.08, 0.38),
      hips: [
        { x: -0.16, z: 0.2 },
        { x: 0.16, z: 0.2 },
        { x: -0.16, z: -0.2 },
        { x: 0.16, z: -0.2 },
      ],
      hipY: 0.22,
      tailAt: new THREE.Vector3(0, 0.03, -0.36),
      quad: true,
    };
  } else {
    // (dappled; two staggered rows of plates up its arched back, little ones on its neck;
    // four spikes at its tail; a small head carried low; longer hind legs)
    const sk = { belly, mark: skin === "#8a6aa8" ? "#6a4a88" : "#4a5a2a", at: spots(0.07, 0.4) };
    const body = [
      painted(ball(), skin, M(0, 0.02, 0, 0.29, 0.27, 0.42), sk),
      painted(ball(), skin, M(0, 0.06, -0.12, 0.26, 0.26, 0.26), sk),
    ];
    for (let k = 0; k < 7; k++)
      for (const sd of [-1, 1]) {
        if (sd > 0 && k === 6) continue;
        const z = 0.3 - k * 0.1 - (sd > 0 ? 0.05 : 0);
        const big = 1 - Math.abs(k - 3) / 4;
        const h = 0.06 + 0.11 * big;
        body.push(
          colored(
            new THREE.OctahedronGeometry(1, 0),
            k % 2 ? mark : "#e8a050",
            M(
              sd * 0.04,
              0.25 + 0.05 * big + h * 0.5,
              z,
              0.018,
              h,
              0.045 + 0.03 * big,
              0,
              0,
              sd * 0.12,
            ),
          ),
        );
      }
    const head: THREE.BufferGeometry[] = [
      painted(ball(), skin, M(0, 0.0, 0.05, 0.12, 0.1, 0.15), { belly }),
      painted(taper(0.08, 0.05, 0.12), skin, M(0, -0.02, 0.1, 1, 0.8, 1), { belly }),
      colored(cone(0.04, 0.05, 6), "#d8c890", M(0, -0.03, 0.24, 1, 0.8, 1, Math.PI / 2)),
      ...eye(-1, 0.075, 0.05, 0.08, 0.048, skin, iris),
      ...eye(1, 0.075, 0.05, 0.08, 0.048, skin, iris),
      ...[0, 1].map((k) =>
        colored(
          new THREE.OctahedronGeometry(1, 0),
          "#e8a050",
          M(0, 0.12, -0.04 - k * 0.07, 0.012, 0.04, 0.03),
        ),
      ),
    ];
    const leg = (len: number) =>
      mergeGeometries([
        painted(taper(0.075, 0.055, len), skin, M(0, 0.0, 0, 1, 1, 1, Math.PI / 2), { belly }),
        painted(ball(), skin, M(0, -len, 0.02, 0.065, 0.03, 0.075)),
        ...[-1, 0, 1].map((k) => colored(ball(0.016, 6, 4), "#e8dcc0", M(k * 0.03, -len, 0.08))),
      ])!;
    p = {
      body: mergeGeometries(body)!,
      head: mergeGeometries(head)!,
      jaw: painted(taper(0.055, 0.03, 0.12), belly, M(0, -0.06, 0.1, 1, 0.5, 1)),
      leg: leg(0.22),
      hind: leg(0.25),
      tail: [0, 1, 2].map((k) => {
        const parts = [
          painted(
            taper(0.13 - k * 0.04, 0.09 - k * 0.035, 0.22),
            skin,
            M(0, 0, 0.01, 1, 0.9, 1, 0, Math.PI, 0),
            sk,
          ),
        ];
        if (k < 2)
          parts.push(
            colored(
              new THREE.OctahedronGeometry(1, 0),
              mark,
              M(0, 0.11 - k * 0.03, -0.1, 0.014, 0.05, 0.035),
            ),
          );
        if (k === 2)
          for (const sd of [-1, 1])
            for (const q of [0, 1])
              parts.push(
                colored(
                  cone(0.016, 0.13, 5),
                  "#f4ecd8",
                  M(sd * 0.05, 0.04, -0.12 - q * 0.08, 1, 1, 1, -0.5, 0, -sd * 1.0),
                ),
              );
        return mergeGeometries(parts)!;
      }),
      neck: new THREE.Vector3(0, 0.0, 0.42),
      hips: [
        { x: -0.16, z: 0.22 },
        { x: 0.16, z: 0.22 },
        { x: -0.16, z: -0.2 },
        { x: 0.16, z: -0.2 },
      ],
      hipY: 0.27,
      tailAt: new THREE.Vector3(0, 0.06, -0.38),
      quad: true,
    };
  }
  cache.set(key, p);
  return p;
}

let shared: THREE.MeshLambertMaterial | undefined;
let users = 0;

export function createHatchlingView(
  parent: THREE.Object3D,
  kind: HatchlingKind,
  look: number,
  scale = 1,
): HatchlingView {
  shared ??= new THREE.MeshLambertMaterial({ vertexColors: true });
  users++;
  const mat = shared;
  const p = build(kind, look);
  const root = new THREE.Group();
  root.name = `hatchling ${kind}`;
  root.scale.setScalar(scale);
  const body = new THREE.Group();
  body.position.y = p.hipY;
  root.add(body);
  body.add(new THREE.Mesh(p.body, mat));
  const neck = new THREE.Group();
  neck.position.copy(p.neck);
  body.add(neck);
  neck.add(new THREE.Mesh(p.head, mat));
  const jaw = new THREE.Mesh(p.jaw, mat);
  neck.add(jaw);
  const legs = p.hips.map((h, k) => {
    const g = new THREE.Group();
    g.position.set(h.x, 0, h.z);
    g.add(new THREE.Mesh(p.hind && k >= 2 ? p.hind : p.leg, mat));
    body.add(g);
    return g;
  });
  const arms = p.arm
    ? [-1, 1].map((sd) => {
        const g = new THREE.Group();
        g.position.set(sd * 0.14, 0.02, 0.22);
        g.add(new THREE.Mesh(p.arm!, mat));
        body.add(g);
        return g;
      })
    : [];
  const tail: THREE.Group[] = [];
  let parentT: THREE.Object3D = body;
  p.tail.forEach((g, k) => {
    const seg = new THREE.Group();
    seg.position.copy(k === 0 ? p.tailAt : new THREE.Vector3(0, 0, -0.2));
    seg.add(new THREE.Mesh(g, mat));
    parentT.add(seg);
    tail.push(seg);
    parentT = seg;
  });
  root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) o.castShadow = true;
  });
  parent.add(root);
  let step = 0;
  let last = 0;
  return {
    root,
    update(x, y, z, heading, act, pace, t) {
      const dt = Math.min(0.1, Math.max(0, t - last));
      last = t;
      root.position.set(x, y, z);
      root.rotation.y = heading;
      const walking = act === "walk" ? Math.min(1, pace) : 0;
      step += dt * (6 + 6 * walking) * walking;
      const s = Math.sin(step);
      // (the waddle: legs in pairs, the body rolling and bobbing)
      legs.forEach((g, k) => {
        const ph = p.quad ? (k === 0 || k === 3 ? s : -s) : k === 0 ? s : -s;
        g.rotation.x = ph * 0.6 * walking;
      });
      const sit = act === "sit" ? 1 : 0;
      body.position.y = p.hipY + Math.abs(Math.cos(step)) * 0.03 * walking - sit * p.hipY * 0.45;
      body.rotation.z = s * 0.08 * walking;
      body.rotation.x = (act === "peck" ? 0.25 : 0) + (sit ? -0.15 : 0);
      for (const g of legs)
        if (sit) g.rotation.x = p.quad ? 1.2 * (g.position.z > 0 ? -1 : 1) : -1.2;
      // (the head: bobbing as it walks, pecking, looking round, squeaking)
      const peck = act === "peck" ? Math.max(0, Math.sin(t * 7)) : 0;
      neck.rotation.x =
        walking * Math.sin(step * 2) * 0.08 + peck * 0.7 - (act === "squeak" ? 0.4 : 0);
      neck.rotation.y = act === "look" ? Math.sin(t * 1.6) * 0.8 : Math.sin(t * 0.7 + x) * 0.15;
      jaw.rotation.x = act === "squeak" ? 0.35 + Math.sin(t * 18) * 0.1 : peck * 0.2;
      jaw.position.y = act === "squeak" ? -0.02 : 0;
      for (const a of arms)
        a.rotation.x = Math.sin(step + 1) * 0.3 * walking + (act === "squeak" ? -0.6 : 0);
      tail.forEach((g, k) => {
        g.rotation.y = Math.sin(t * (2 + 3 * walking) - k * 0.7) * (0.18 + 0.12 * walking);
        g.rotation.x = 0.05 * k - sit * 0.1;
      });
    },
    dispose() {
      root.removeFromParent();
      users--;
      if (users === 0) {
        shared?.dispose();
        shared = undefined;
      }
    },
  };
}
