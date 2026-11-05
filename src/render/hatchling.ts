/**
 * Baby dinosaurs for the Beast Market's pens (Blake, Nov 4: "the animals look bad"; he
 * picked "baby dinos in pens"): hatchling raptors, triceratops and stegosaurs, chunky and
 * big-eyed, each a few meshes (body, head, legs, tail) in vertex colours with one shared
 * material. Animated: a waddling walk with the tail swinging and the head bobbing, a peck
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
  // (skin, belly, stripes or plates)
  raptor: [
    ["#3fa88a", "#f2e4b8", "#e8763a"],
    ["#c96a2e", "#f6dcae", "#5a3a8a"],
    ["#6a8a3a", "#eaf0c0", "#2a5a8a"],
  ],
  trike: [
    ["#7a9ad0", "#eef0f8", "#e8c040"],
    ["#c08050", "#f8e8d0", "#7a3a2a"],
    ["#9ac060", "#f2f8d8", "#d86a3a"],
  ],
  stego: [
    ["#8ab04a", "#f0f2c8", "#d8603a"],
    ["#c0a050", "#f8f0d0", "#3a7a8a"],
    ["#a07ac0", "#f0e8f8", "#f0a030"],
  ],
};

function colored(g: THREE.BufferGeometry, color: string, m?: THREE.Matrix4) {
  const geo = g.index ? g.toNonIndexed() : g;
  if (m) geo.applyMatrix4(m);
  const c = new THREE.Color(color);
  const n = geo.attributes.position!.count;
  const col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) col.set([c.r, c.g, c.b], i * 3);
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  geo.deleteAttribute("uv");
  return geo;
}

const M = (x: number, y: number, z: number, sx = 1, sy = 1, sz = 1, rx = 0, ry = 0, rz = 0) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
    new THREE.Vector3(sx, sy, sz),
  );
const ball = (r = 1, w = 10, h = 8) => new THREE.SphereGeometry(r, w, h);

interface Parts {
  body: THREE.BufferGeometry;
  head: THREE.BufferGeometry;
  jaw: THREE.BufferGeometry;
  leg: THREE.BufferGeometry;
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

function build(kind: HatchlingKind, look: number): Parts {
  const key = `${kind}|${look}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const [skin, belly, mark] = LOOKS[kind][look % LOOKS[kind].length]!;
  const eye = (sd: number, x: number, y: number, z: number, r: number) => [
    colored(ball(r, 10, 8), "#ffffff", M(sd * x, y, z)),
    colored(ball(r * 0.55, 8, 6), "#1a1410", M(sd * (x + r * 0.35), y + r * 0.08, z + r * 0.55)),
    colored(ball(r * 0.18, 6, 4), "#ffffff", M(sd * (x + r * 0.5), y + r * 0.3, z + r * 0.85)),
  ];
  let p: Parts;
  if (kind === "raptor") {
    const body = [
      colored(ball(), skin, M(0, 0, 0, 0.26, 0.24, 0.36)),
      colored(ball(), belly, M(0, -0.07, 0.04, 0.2, 0.17, 0.3)),
      // (stripes down its back)
      ...[-0.12, 0.0, 0.12].map((z) => colored(ball(), mark, M(0, 0.17, z, 0.12, 0.06, 0.05))),
      // (a tuft of down on its back)
      colored(new THREE.ConeGeometry(0.06, 0.14, 5), mark, M(0, 0.25, 0.08, 1, 1, 1, -0.5)),
    ];
    const head = [
      colored(ball(), skin, M(0, 0.06, 0.04, 0.17, 0.16, 0.18)),
      colored(ball(), skin, M(0, 0.0, 0.17, 0.11, 0.08, 0.13)),
      colored(ball(), belly, M(0, -0.04, 0.17, 0.09, 0.04, 0.11)),
      ...eye(-1, 0.09, 0.11, 0.1, 0.06),
      ...eye(1, 0.09, 0.11, 0.1, 0.06),
      colored(new THREE.ConeGeometry(0.03, 0.09, 4), mark, M(0, 0.21, 0.0, 1, 1, 1, -0.6)),
    ];
    p = {
      body: mergeGeometries(body)!,
      head: mergeGeometries(head)!,
      jaw: colored(ball(), belly, M(0, -0.05, 0.13, 0.08, 0.03, 0.1)),
      leg: mergeGeometries([
        colored(ball(), skin, M(0, -0.06, 0, 0.08, 0.12, 0.09)),
        colored(new THREE.CylinderGeometry(0.035, 0.03, 0.14, 6), skin, M(0, -0.18, 0.02)),
        colored(ball(), mark, M(0, -0.25, 0.05, 0.06, 0.03, 0.09)),
      ])!,
      arm: mergeGeometries([
        colored(
          new THREE.CylinderGeometry(0.025, 0.02, 0.1, 5),
          skin,
          M(0, -0.04, 0.03, 1, 1, 1, 0.9),
        ),
        colored(new THREE.ConeGeometry(0.015, 0.04, 4), "#f4f0e0", M(0, -0.07, 0.08, 1, 1, 1, 1.6)),
      ])!,
      tail: [0, 1, 2].map((k) =>
        colored(
          new THREE.ConeGeometry(0.12 - k * 0.035, 0.24, 7),
          k === 1 ? mark : skin,
          M(0, 0, -0.1, 1, 1, 1, -Math.PI / 2),
        ),
      ),
      neck: new THREE.Vector3(0, 0.16, 0.3),
      hips: [
        { x: -0.12, z: -0.04 },
        { x: 0.12, z: -0.04 },
      ],
      hipY: 0.3,
      tailAt: new THREE.Vector3(0, 0.04, -0.32),
      quad: false,
    };
  } else {
    const trike = kind === "trike";
    const body = [
      colored(ball(), skin, M(0, 0, 0, 0.3, 0.24, 0.4)),
      colored(ball(), belly, M(0, -0.08, 0.02, 0.24, 0.16, 0.34)),
    ];
    if (!trike)
      for (let k = 0; k < 5; k++)
        for (const sd of [-1, 1])
          body.push(
            colored(
              new THREE.ConeGeometry(
                0.07 - Math.abs(k - 2) * 0.012,
                0.18 - Math.abs(k - 2) * 0.03,
                4,
              ),
              mark,
              M(
                sd * 0.05,
                0.25 - Math.abs(k - 2) * 0.02,
                -0.2 + k * 0.1,
                0.4,
                1,
                1,
                0,
                0,
                sd * 0.18,
              ),
            ),
          );
    const head: THREE.BufferGeometry[] = [
      colored(ball(), skin, M(0, 0.04, 0.06, 0.16, 0.15, 0.17)),
      colored(ball(), skin, M(0, -0.02, 0.18, 0.11, 0.09, 0.11)),
      colored(
        new THREE.ConeGeometry(0.06, 0.08, 6),
        "#e8d8a0",
        M(0, -0.03, 0.29, 1, 1, 1, Math.PI / 2),
      ),
      ...eye(-1, 0.1, 0.1, 0.1, 0.055),
      ...eye(1, 0.1, 0.1, 0.1, 0.055),
    ];
    if (trike) {
      head.push(
        colored(
          new THREE.CylinderGeometry(0.24, 0.2, 0.04, 12),
          mark,
          M(0, 0.14, -0.06, 1, 1, 1, -1.1),
        ),
      );
      head.push(
        colored(new THREE.ConeGeometry(0.025, 0.12, 5), "#f4ecd8", M(0, 0.06, 0.25, 1, 1, 1, 1.1)),
      );
      for (const sd of [-1, 1])
        head.push(
          colored(
            new THREE.ConeGeometry(0.03, 0.16, 5),
            "#f4ecd8",
            M(sd * 0.08, 0.17, 0.08, 1, 1, 1, 0.9, 0, -sd * 0.2),
          ),
        );
    }
    p = {
      body: mergeGeometries(body)!,
      head: mergeGeometries(head)!,
      jaw: colored(ball(), belly, M(0, -0.08, 0.16, 0.08, 0.03, 0.09)),
      leg: mergeGeometries([
        colored(new THREE.CylinderGeometry(0.06, 0.055, 0.2, 7), skin, M(0, -0.1, 0)),
        colored(ball(), mark, M(0, -0.2, 0.02, 0.07, 0.03, 0.08)),
      ])!,
      tail: [0, 1, 2].map((k) => {
        const parts = [
          colored(
            new THREE.ConeGeometry(0.13 - k * 0.04, 0.24, 7),
            skin,
            M(0, 0, -0.1, 1, 1, 1, -Math.PI / 2),
          ),
        ];
        if (!trike && k === 2)
          for (const sd of [-1, 1])
            parts.push(
              colored(
                new THREE.ConeGeometry(0.02, 0.12, 4),
                "#f4ecd8",
                M(sd * 0.05, 0.03, -0.14, 1, 1, 1, 0, 0, -sd * 1.1),
              ),
            );
        return mergeGeometries(parts)!;
      }),
      neck: new THREE.Vector3(0, 0.08, 0.36),
      hips: [
        { x: -0.15, z: 0.2 },
        { x: 0.15, z: 0.2 },
        { x: -0.15, z: -0.2 },
        { x: 0.15, z: -0.2 },
      ],
      hipY: 0.22,
      tailAt: new THREE.Vector3(0, 0.02, -0.36),
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
  shared ??= new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });
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
  const legs = p.hips.map((h) => {
    const g = new THREE.Group();
    g.position.set(h.x, 0, h.z);
    g.add(new THREE.Mesh(p.leg, mat));
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
