/**
 * A duck, in detail (Blake, Nov 6: "high fidelity ducks swimming in the river"): a mallard
 * drake (bottle-green head, white collar, chestnut breast, grey flanks, the blue speculum
 * on his folded wing, the curl on his tail), the hen (mottled browns, her speculum too),
 * or a duckling (yellow and brown fluff); smooth shaded, a flattened bill with its nail,
 * glossy eyes. Floating at the waterline: it bobs, paddles (a ripple of the tail), dabbles
 * (tips forward, tail up, head under) and looks about. game/ducks.ts moves it.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import type { DuckAct, DuckKind } from "../game/ducks";

export interface DuckView {
  readonly root: THREE.Group;
  update(x: number, y: number, z: number, heading: number, act: DuckAct, t: number): void;
  dispose(): void;
}

const M = (x: number, y: number, z: number, sx = 1, sy = 1, sz = 1, rx = 0, ry = 0, rz = 0) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)),
    new THREE.Vector3(sx, sy, sz),
  );

const tmp = new THREE.Color();

/** A piece placed and coloured: `color(x, y, z, ny)` per vertex (its own space after
 * placing), shaded a little lighter on top. */
function piece(
  g: THREE.BufferGeometry,
  m: THREE.Matrix4,
  color: string | ((x: number, y: number, z: number, ny: number) => string),
) {
  if (!g.attributes.normal) g.computeVertexNormals();
  g.applyMatrix4(m);
  const geo = g.index ? g.toNonIndexed() : g;
  const pos = geo.attributes.position!;
  const nor = geo.attributes.normal!;
  const col = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) {
    const ny = nor.getY(i);
    tmp.set(typeof color === "string" ? color : color(pos.getX(i), pos.getY(i), pos.getZ(i), ny));
    tmp.multiplyScalar(0.9 + 0.14 * Math.max(0, ny));
    col.set([tmp.r, tmp.g, tmp.b], i * 3);
  }
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  geo.deleteAttribute("uv");
  return geo;
}

const ball = (r = 1, w = 20, h = 14) => new THREE.SphereGeometry(r, w, h);
const speck = (x: number, y: number, z: number) => {
  const v = Math.sin(x * 91.7 + y * 47.3 + z * 63.1) * 43758.5453;
  return v - Math.floor(v);
};

interface Parts {
  body: THREE.BufferGeometry;
  head: THREE.BufferGeometry;
  tail: THREE.BufferGeometry;
  neck: THREE.Vector3;
  scale: number;
}

const cache = new Map<DuckKind, Parts>();

function build(kind: DuckKind): Parts {
  const hit = cache.get(kind);
  if (hit) return hit;
  const drake = kind === "drake";
  const chick = kind === "duckling";
  // (the hen's mottle: two browns and a buff, in flecks)
  const mottle = (x: number, y: number, z: number) => {
    const s = speck(Math.round(x * 30), Math.round(y * 30), Math.round(z * 30));
    return s < 0.33 ? "#6a4a2c" : s < 0.7 ? "#8a6a44" : "#b8986a";
  };
  const body: THREE.BufferGeometry[] = [];
  const head: THREE.BufferGeometry[] = [];
  if (chick) {
    body.push(
      piece(ball(), M(0, 0.05, 0, 0.09, 0.075, 0.12), (_x, y) =>
        y > 0.07 ? "#7a5a2a" : "#f0d060",
      ),
    );
    head.push(
      piece(ball(), M(0, 0.03, 0.02, 0.06, 0.06, 0.065), (_x, y) =>
        y > 0.06 ? "#7a5a2a" : "#f2d868",
      ),
      piece(ball(), M(0, 0.015, 0.075, 0.025, 0.012, 0.035), "#3a3020"),
    );
    for (const sd of [-1, 1])
      head.push(
        piece(ball(0.012, 8, 6), M(sd * 0.05, 0.045, 0.045), "#14100c"),
        piece(ball(0.004, 6, 4), M(sd * 0.058, 0.05, 0.052), "#ffffff"),
      );
  } else {
    // The body: a long boat of a breast and flanks, the back, the folded wings over it.
    body.push(
      piece(ball(), M(0, 0.07, 0, 0.16, 0.12, 0.27), (x, y, z) =>
        drake
          ? z > 0.12 && y > 0.02
            ? "#7a3a22"
            : y > 0.12
              ? "#5a5a52"
              : "#c8c8c0"
          : mottle(x, y, z),
      ),
      piece(ball(), M(0, 0.15, -0.03, 0.12, 0.06, 0.2), (x, y, z) =>
        drake ? "#4a4a44" : mottle(x, y, z),
      ),
    );
    for (const sd of [-1, 1]) {
      body.push(
        piece(ball(), M(sd * 0.11, 0.14, -0.05, 0.045, 0.06, 0.2, 0.15, 0, sd * 0.2), (x, y, z) =>
          z < -0.08 && z > -0.16 && y > 0.12 ? "#2a4ab8" : drake ? "#7a7a70" : mottle(x, y, z),
        ),
        // (the white bars either side of the speculum)
        piece(
          new THREE.BoxGeometry(0.012, 0.03, 0.01),
          M(sd * 0.155, 0.16, -0.075, 1, 1, 1, 0, 0, sd * 0.2),
          "#f0f0e8",
        ),
        piece(
          new THREE.BoxGeometry(0.012, 0.03, 0.01),
          M(sd * 0.155, 0.16, -0.17, 1, 1, 1, 0, 0, sd * 0.2),
          "#f0f0e8",
        ),
      );
    }
    // (the neck, the drake's white collar)
    body.push(
      piece(
        new THREE.CylinderGeometry(0.05, 0.075, 0.12, 14),
        M(0, 0.2, 0.17, 1, 1, 1, 0.5),
        (x, y, z) => (drake ? (y < 0.19 ? "#7a3a22" : "#2a6a3a") : mottle(x, y, z)),
      ),
    );
    if (drake)
      body.push(
        piece(
          new THREE.TorusGeometry(0.058, 0.009, 6, 18),
          M(0, 0.235, 0.19, 1, 1, 1, Math.PI / 2 - 0.5),
          "#f4f4ee",
        ),
      );
    // The head: round, a little flat at the crown; the bill long and flat with its nail;
    // the eyes; the hen's eye-stripe.
    head.push(
      piece(ball(), M(0, 0.03, 0.02, 0.07, 0.07, 0.085), (x, y, z) =>
        drake ? "#1e5a34" : y > 0.03 && y < 0.05 && z < 0.07 ? "#3a2a1a" : mottle(x, y, z),
      ),
      piece(ball(), M(0, 0.005, 0.11, 0.032, 0.014, 0.07), drake ? "#e8c838" : "#c87a30"),
      piece(ball(), M(0, 0.0, 0.11, 0.03, 0.008, 0.066), drake ? "#d0b030" : "#a86020"),
      piece(ball(0.01, 8, 6), M(0, 0.012, 0.176), "#2a2018"),
    );
    for (const sd of [-1, 1])
      head.push(
        piece(ball(0.013, 10, 8), M(sd * 0.055, 0.045, 0.05), "#14100c"),
        piece(ball(0.004, 6, 4), M(sd * 0.064, 0.05, 0.058), "#ffffff"),
      );
  }
  // The tail: short, tipped up; the drake's black-and-white with its curl.
  const tail = chick
    ? [piece(ball(), M(0, 0.07, -0.11, 0.04, 0.03, 0.04, -0.4), "#7a5a2a")]
    : [
        piece(
          new THREE.ConeGeometry(0.07, 0.14, 10),
          M(0, 0.11, -0.28, 1, 0.5, 1, -2.0),
          (_x, y) => (drake ? (y > 0.11 ? "#1a1a1a" : "#f0f0ea") : "#8a6a44"),
        ),
        ...(drake
          ? [
              piece(
                new THREE.TorusGeometry(0.025, 0.006, 5, 12, Math.PI * 1.4),
                M(0, 0.17, -0.27, 1, 1, 1, 0, Math.PI / 2, 0),
                "#1a1a1a",
              ),
            ]
          : []),
      ];
  const p: Parts = {
    body: mergeGeometries(body)!,
    head: mergeGeometries(head)!,
    tail: mergeGeometries(tail)!,
    neck: chick ? new THREE.Vector3(0, 0.1, 0.09) : new THREE.Vector3(0, 0.26, 0.21),
    scale: chick ? 1.1 : 1.35,
  };
  cache.set(kind, p);
  return p;
}

let shared: THREE.MeshLambertMaterial | undefined;
let users = 0;

export function createDuckView(parent: THREE.Object3D, kind: DuckKind, seed = 0): DuckView {
  shared ??= new THREE.MeshLambertMaterial({ vertexColors: true });
  users++;
  const p = build(kind);
  const root = new THREE.Group();
  root.name = `duck ${kind}`;
  root.scale.setScalar(p.scale);
  const body = new THREE.Group();
  root.add(body);
  body.add(new THREE.Mesh(p.body, shared));
  const tail = new THREE.Mesh(p.tail, shared);
  body.add(tail);
  const neck = new THREE.Group();
  neck.position.copy(p.neck);
  body.add(neck);
  neck.add(new THREE.Mesh(p.head, shared));
  root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) o.castShadow = true;
  });
  parent.add(root);
  let dabble = 0;
  let last = 0;
  return {
    root,
    update(x, y, z, heading, act, t) {
      const dt = Math.min(0.1, Math.max(0, t - last));
      last = t;
      dabble += ((act === "dabble" ? 1 : 0) - dabble) * (1 - Math.exp(-5 * dt));
      root.position.set(x, y - 0.06 + 0.015 * Math.sin(t * 2.3 + seed) - 0.05 * dabble, z);
      root.rotation.y = heading;
      // (bobbing, the tail's paddle-wag; tipping forward to dabble)
      body.rotation.x = 0.03 * Math.sin(t * 1.9 + seed) + 1.15 * dabble;
      body.rotation.z = 0.04 * Math.sin(t * 1.3 + seed * 2);
      tail.rotation.y = 0.18 * Math.sin(t * 5.5 + seed);
      neck.rotation.x = 0.1 * Math.sin(t * 2.3 + seed) + 0.6 * dabble;
      neck.rotation.y =
        act === "look" ? 0.9 * Math.sin(t * 1.4 + seed) : 0.12 * Math.sin(t * 0.6 + seed);
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
