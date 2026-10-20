/**
 * The partygoers on the title screen's beach: little cartoon dinosaurs dancing. Each is
 * a chunky toon biped (round body, big head and eyes, stubby arms, a tail) with its own
 * look by variant: a duck-bill crest, back plates, a horned frill, a bony dome, a spiky
 * frill or a plain round one, in bright colours, with party extras (sunglasses, a lei,
 * a party hat, a flower).
 *
 * Every dinosaur is four meshes (body, head, two arms) with vertex colours and one
 * shared material, so a crowd costs a few dozen draw calls. Dances, all on the beat of
 * the title music: bounce, sway, wave, hop, chill (at the bar), dj (at the decks) and
 * conga (walking in a line, hands on the one in front). Purely visual.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export type Dance = "bounce" | "sway" | "wave" | "hop" | "chill" | "dj" | "conga";
export const DANCES: readonly Dance[] = ["bounce", "sway", "wave", "hop", "chill", "dj", "conga"];

export interface PartyDinoView {
  readonly root: THREE.Group;
  /** Place it and dance: `t` seconds, `phase` offsets its moves from the others. */
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    dance: Dance,
    t: number,
    phase: number,
  ): void;
  dispose(): void;
}

/** The title music's tempo: everyone dances on the beat. */
const BEAT = 132 / 60;

/** Skin, belly and accent colour per variant. */
const LOOKS: [string, string, string][] = [
  ["#ff8a3d", "#ffe1b0", "#2f80ed"], // orange, duck-bill crest
  ["#3fbf6a", "#e8f7c0", "#ff6fb1"], // green, back plates
  ["#a77bff", "#efe0ff", "#ffd23f"], // purple, horned frill
  ["#2bb8e0", "#d9f6ff", "#ff5a4f"], // blue, bony dome
  ["#ffd23f", "#fff4cc", "#19c3b0"], // yellow, spiky frill
  ["#ff6f8e", "#ffe0e8", "#3fbf6a"], // pink, round
];

/** A shape with one colour, as a non-indexed geometry with a colour attribute. */
function part(g: THREE.BufferGeometry, color: string, m?: THREE.Matrix4) {
  const geo = g.index ? g.toNonIndexed() : g;
  if (g !== geo) g.dispose();
  if (m) geo.applyMatrix4(m);
  const c = new THREE.Color(color);
  const n = geo.getAttribute("position").count;
  const col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) col.set([c.r, c.g, c.b], i * 3);
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  geo.deleteAttribute("uv");
  return geo;
}

const M = (
  p: [number, number, number],
  r: [number, number, number] = [0, 0, 0],
  s: [number, number, number] = [1, 1, 1],
) =>
  new THREE.Matrix4().compose(
    new THREE.Vector3(...p),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(...r)),
    new THREE.Vector3(...s),
  );

const sphere = (r: number, w = 10, h = 7) => new THREE.SphereGeometry(r, w, h);
const cone = (r: number, h: number, n = 6) => new THREE.ConeGeometry(r, h, n);
const cyl = (r0: number, r1: number, h: number, n = 7) => new THREE.CylinderGeometry(r1, r0, h, n);

function merge(parts: THREE.BufferGeometry[]) {
  const g = mergeGeometries(parts, false)!;
  for (const p of parts) p.dispose();
  g.computeVertexNormals();
  return g;
}

/** Build the four meshes' geometry for a variant (cached: every dino of a variant shares them). */
const cache = new Map<
  number,
  { body: THREE.BufferGeometry; head: THREE.BufferGeometry; arm: THREE.BufferGeometry }
>();
function geometryFor(variant: number) {
  const v = ((variant % LOOKS.length) + LOOKS.length) % LOOKS.length;
  const hit = cache.get(v);
  if (hit) return hit;
  const [skin, belly, accent] = LOOKS[v]!;
  // Body (origin at the feet): a round, upright torso, a tail behind, two legs.
  const body: THREE.BufferGeometry[] = [
    part(sphere(0.55), skin, M([0, 1.05, -0.05], [0.25, 0, 0], [1, 1.15, 0.95])),
    part(sphere(0.42), belly, M([0, 1.0, 0.18], [0.25, 0, 0], [0.95, 1.1, 0.7])),
    part(cone(0.3, 1.3), skin, M([0, 0.75, -0.85], [-Math.PI / 2 - 0.5, 0, 0])),
  ];
  for (const s of [-1, 1]) {
    body.push(part(cyl(0.18, 0.15, 0.55), skin, M([s * 0.24, 0.33, 0])));
    body.push(part(sphere(0.18, 8, 5), belly, M([s * 0.24, 0.07, 0.1], [0, 0, 0], [1, 0.5, 1.5])));
  }
  if (v === 1)
    // Back plates.
    for (let k = 0; k < 4; k++)
      body.push(
        part(
          cone(0.16, 0.38, 4),
          accent,
          M([0, 1.55 - k * 0.2, -0.45 - k * 0.16], [-0.5 - k * 0.2, 0, 0], [0.4, 1, 1]),
        ),
      );
  // A lei round the neck: a ring of bright flowers.
  if (v % 2 === 0)
    for (let k = 0; k < 9; k++) {
      const a = (k / 9) * Math.PI * 2;
      body.push(
        part(
          sphere(0.09, 6, 4),
          k % 2 ? accent : "#ffffff",
          M([Math.sin(a) * 0.38, 1.52 - Math.cos(a) * 0.04, Math.cos(a) * 0.3 + 0.03]),
        ),
      );
    }

  // Head (origin at the neck): a big round head, a snout, eyes and the variant's feature.
  const head: THREE.BufferGeometry[] = [
    part(sphere(0.42), skin, M([0, 0.38, 0.12], [0, 0, 0], [1, 0.95, 1])),
    part(sphere(0.3), skin, M([0, 0.27, 0.48], [0.1, 0, 0], [0.95, 0.75, 1.1])),
    part(sphere(0.06, 5, 4), "#3a2418", M([-0.12, 0.33, 0.78])),
    part(sphere(0.06, 5, 4), "#3a2418", M([0.12, 0.33, 0.78])),
  ];
  for (const s of [-1, 1]) {
    head.push(part(sphere(0.14, 8, 6), "#ffffff", M([s * 0.2, 0.55, 0.38])));
    head.push(part(sphere(0.075, 6, 4), "#1d1a18", M([s * 0.21, 0.56, 0.5])));
  }
  if (v === 3 || v === 5)
    // Sunglasses.
    head.push(part(new THREE.BoxGeometry(0.62, 0.16, 0.08), "#1d1a18", M([0, 0.56, 0.52])));
  if (v === 0)
    // The duck-bill's crest: a thick horn sweeping back over the head.
    head.push(part(cone(0.17, 1.0, 7), accent, M([0, 0.85, -0.3], [-1.05, 0, 0], [0.75, 1, 1])));
  if (v === 2) {
    head.push(part(cyl(0.05, 0.6, 0.12, 10), accent, M([0, 0.55, -0.15], [-1.1, 0, 0])));
    for (const s of [-1, 1])
      head.push(part(cone(0.06, 0.4), "#fff4dc", M([s * 0.18, 0.8, 0.3], [0.5, 0, -s * 0.3])));
    head.push(part(cone(0.07, 0.3), "#fff4dc", M([0, 0.42, 0.78], [1.1, 0, 0])));
  }
  if (v === 3)
    head.push(part(sphere(0.33, 10, 6), accent, M([0, 0.62, 0.05], [0, 0, 0], [1, 0.7, 1])));
  if (v === 4)
    for (let k = 0; k < 5; k++) {
      const a = (k / 4 - 0.5) * 1.8;
      head.push(
        part(
          cone(0.08, 0.42, 4),
          accent,
          M([Math.sin(a) * 0.35, 0.55 + Math.cos(a) * 0.25, -0.2], [-0.6, 0, -a]),
        ),
      );
    }
  if (v === 1 || v === 4)
    // A party hat.
    head.push(
      part(
        cone(0.16, 0.45, 8),
        v === 1 ? "#ffd23f" : "#ff6fb1",
        M([0.08, 0.98, 0.1], [0, 0, -0.2]),
      ),
    );
  if (v === 5) head.push(part(sphere(0.1, 6, 4), "#ffd23f", M([0.36, 0.7, 0.05])));

  // Arm (origin at the shoulder): an upper arm and a three-fingered hand.
  const arm = [
    part(cyl(0.09, 0.07, 0.42, 6), skin, M([0, -0.21, 0])),
    part(sphere(0.11, 6, 5), belly, M([0, -0.45, 0])),
  ];
  const out = { body: merge(body), head: merge(head), arm: merge(arm) };
  cache.set(v, out);
  return out;
}

let shared: THREE.MeshLambertMaterial | undefined;
let users = 0;

export function createPartyDinoView(
  parent: THREE.Object3D,
  variant: number,
  scale = 1,
): PartyDinoView {
  shared ??= new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });
  users++;
  const mat = shared;
  const g = geometryFor(variant);
  const root = new THREE.Group();
  root.name = "partygoer";
  root.scale.setScalar(scale);
  const hips = new THREE.Group(); // bob, lean and twist
  root.add(hips);
  const body = new THREE.Mesh(g.body, mat);
  hips.add(body);
  const neck = new THREE.Group();
  neck.position.set(0, 1.55, 0.05);
  hips.add(neck);
  neck.add(new THREE.Mesh(g.head, mat));
  const arms = [-1, 1].map((s) => {
    const a = new THREE.Group();
    a.position.set(s * 0.48, 1.3, 0.15);
    a.add(new THREE.Mesh(g.arm, mat));
    hips.add(a);
    return a;
  });
  root.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) o.castShadow = true;
  });
  parent.add(root);

  return {
    root,
    update(x, y, z, heading, dance, t, phase) {
      root.position.set(x, y, z);
      root.rotation.y = heading;
      const b = (t * BEAT + phase) * Math.PI * 2; // one cycle per beat
      const s = Math.sin(b);
      const half = Math.sin(b / 2);
      let bob = 0;
      let lean = 0;
      let twist = 0;
      let nod = 0;
      let tilt = 0;
      // Arm rotations: [x (forward/up), z (out)] for left and right.
      let l: [number, number] = [0.2, 0.3];
      let r: [number, number] = [0.2, -0.3];
      switch (dance) {
        case "bounce":
          bob = Math.abs(s) * 0.28;
          nod = 0.15 * s;
          l = [-2.6 + 0.5 * half, 0.3];
          r = [-2.6 - 0.5 * half, -0.3];
          break;
        case "sway":
          lean = 0.22 * half;
          bob = 0.06 * Math.abs(s);
          tilt = -0.2 * half;
          // Clap on the beat.
          l = [-1.2, 0.5 - 0.45 * Math.abs(s)];
          r = [-1.2, -0.5 + 0.45 * Math.abs(s)];
          break;
        case "wave":
          twist = 0.3 * half;
          bob = 0.1 * Math.abs(s);
          l = [-2.9, 0.5 + 0.5 * s];
          r = [-2.9, -0.5 + 0.5 * s];
          nod = 0.1 * s;
          break;
        case "hop":
          bob = Math.max(0, Math.sin(b / 2)) * 0.5;
          l = [-1.0 - 0.8 * Math.max(0, half), 0.2];
          r = [-1.0 - 0.8 * Math.max(0, half), -0.2];
          break;
        case "chill":
          nod = 0.12 * Math.max(0, s);
          bob = 0.03 * Math.abs(s);
          l = [-1.3, 0.15];
          r = [0.15 + 0.1 * half, -0.25];
          break;
        case "dj":
          nod = 0.25 * Math.max(0, s);
          bob = 0.05 * Math.abs(s);
          l = [-1.1 + 0.25 * s, 0.2];
          r = [b % (Math.PI * 8) < Math.PI * 2 ? -3.0 : -1.1 - 0.25 * s, -0.2];
          break;
        case "conga":
          // Step on the beat, hands forward on the shoulders of the one in front, and a
          // kick out on every fourth.
          bob = Math.abs(s) * 0.12;
          lean = 0.12 * half;
          l = [-1.4, 0.1];
          r = [-1.4, -0.1];
          nod = 0.1 * s;
          break;
      }
      hips.position.y = bob;
      hips.rotation.set(0, twist, lean);
      neck.rotation.set(nod, 0, tilt);
      // (Out from the body is -z for the arm on -x, +z for the one on +x.)
      arms[0]!.rotation.set(l[0], 0, -l[1]);
      arms[1]!.rotation.set(r[0], 0, -r[1]);
    },
    dispose() {
      root.removeFromParent();
      users--;
      if (users === 0) {
        shared?.dispose();
        shared = undefined;
        for (const c of cache.values()) for (const geo of Object.values(c)) geo.dispose();
        cache.clear();
      }
    },
  };
}
