/**
 * The overworlds' villagers (Blake, Oct 26): dinosaur folk who live in each kingdom,
 * walking about round their homes. Their own cast, not the racers: eight kinds, each a
 * chunky low-poly toon in the game's style, in the colours and clothes of their kingdom.
 *
 *   ankylo    a low, wide quadruped: an armoured back of knobs, a club on its tail
 *   parasaur  a duck-billed biped with a long crest swept back
 *   trike     a quadruped with a frill and three horns
 *   pachy     a biped with a bony dome of a head ringed with knobs
 *   compy     a small, quick biped (the villages' children)
 *   iggy      a tall biped with thumb spikes
 *   ovi       a feathered biped with a crest and a beak
 *   sauro     a small long-neck on four legs
 *
 * The folk (their kingdom) dress them: the valley's leaf collars and shell beads, the
 * snow's scarves and bobble hats, the desert's straw hats and ponchos, the islands' leis
 * and sun hats, the Dragon Kingdom's hooded tunics.
 *
 * Each villager is a body mesh (torso, head, tail, clothes) and two or four leg meshes
 * that swing from the hips as it walks, with vertex colours and one shared material.
 * Purely visual: src/overworld/villagers.ts walks them about.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export type Species =
  "ankylo" | "parasaur" | "trike" | "pachy" | "compy" | "iggy" | "ovi" | "sauro";
export const SPECIES: readonly Species[] = [
  "ankylo",
  "parasaur",
  "trike",
  "pachy",
  "compy",
  "iggy",
  "ovi",
  "sauro",
];
export type Folk = "valley" | "snow" | "desert" | "beach" | "dragon" | "road";

/** Four-legged kinds (the rest walk on two). */
const FOURS = new Set<Species>(["ankylo", "trike", "sauro"]);

/** How big each kind is (metres to the top of the head, about) and how fast it walks. */
export const SIZE: Record<Species, { scale: number; speed: number; radius: number }> = {
  ankylo: { scale: 1.25, speed: 0.9, radius: 1.5 },
  parasaur: { scale: 1.2, speed: 1.3, radius: 0.9 },
  trike: { scale: 1.3, speed: 0.95, radius: 1.6 },
  pachy: { scale: 1.05, speed: 1.2, radius: 0.8 },
  compy: { scale: 0.65, speed: 2.0, radius: 0.5 },
  iggy: { scale: 1.35, speed: 1.15, radius: 0.9 },
  ovi: { scale: 0.95, speed: 1.6, radius: 0.7 },
  sauro: { scale: 1.2, speed: 0.85, radius: 1.5 },
};

/** Skin colours each kingdom's folk come in (picked by the villager's seed). */
const SKINS: Record<Folk, string[]> = {
  valley: ["#6fae4a", "#9a7b4f", "#c98a3a", "#4f8f7a", "#b5a046"],
  snow: ["#8aa6c9", "#b7b1d8", "#6f8f9e", "#c9c2b0", "#7d9b8a"],
  desert: ["#d09a5b", "#b8743e", "#d8b878", "#a86a4a", "#c99a6a"],
  beach: ["#3fb8a0", "#ff9a6a", "#6fc06a", "#e0b040", "#5aa0e0"],
  dragon: ["#7a6aa0", "#5f8a6a", "#9a5a5a", "#6a7a9a", "#a08a5a"],
  road: ["#8a9a6a", "#a08060", "#7a8aa0", "#b0906a", "#6a8a7a"],
};
/** Clothes colours (main, trim) per folk. */
const CLOTH: Record<Folk, [string, string][]> = {
  valley: [
    ["#3f7a2a", "#f0e0b0"],
    ["#7a4a2a", "#e0d0a0"],
  ],
  snow: [
    ["#d83a3a", "#ffffff"],
    ["#2f6fd0", "#ffe060"],
    ["#3a9a5a", "#ffffff"],
  ],
  desert: [
    ["#c8402a", "#f0c040"],
    ["#2a8a9a", "#f0e0c0"],
    ["#8a3a8a", "#f0c040"],
  ],
  beach: [
    ["#ff4f8a", "#ffe040"],
    ["#ffffff", "#2fb0e0"],
    ["#ff8a20", "#ffffff"],
  ],
  dragon: [
    ["#5a3a8a", "#d8b040"],
    ["#8a2a2a", "#d8b040"],
    ["#2a5a8a", "#e0e0e0"],
  ],
  road: [
    ["#8a6a3a", "#e0d0a0"],
    ["#4a6a8a", "#e0d0a0"],
  ],
};

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
const sphere = (r: number, w = 9, h = 6) => new THREE.SphereGeometry(r, w, h);
const cone = (r: number, h: number, n = 6) => new THREE.ConeGeometry(r, h, n);
const cyl = (r0: number, r1: number, h: number, n = 7) => new THREE.CylinderGeometry(r1, r0, h, n);
const box = (x: number, y: number, z: number) => new THREE.BoxGeometry(x, y, z);

function merge(parts: THREE.BufferGeometry[]) {
  const g = mergeGeometries(parts, false)!;
  for (const p of parts) p.dispose();
  g.computeVertexNormals();
  return g;
}

/** A shade of a colour (k < 1 darker, > 1 lighter). */
function shade(hex: string, k: number) {
  const c = new THREE.Color(hex);
  if (k < 1) c.multiplyScalar(k);
  else c.lerp(new THREE.Color("#ffffff"), k - 1);
  return `#${c.getHexString()}`;
}

/** Where a kind's head sits (its neck), the hips, and how long its legs are. */
interface Frame {
  head: [number, number, number];
  hips: [number, number, number][];
  leg: number;
  legR: number;
}
const FRAMES: Record<Species, Frame> = {
  ankylo: {
    head: [0, 0.85, 1.05],
    hips: [
      [-0.45, 0.55, 0.55],
      [0.45, 0.55, 0.55],
      [-0.45, 0.55, -0.5],
      [0.45, 0.55, -0.5],
    ],
    leg: 0.55,
    legR: 0.17,
  },
  trike: {
    head: [0, 1.0, 1.05],
    hips: [
      [-0.42, 0.65, 0.55],
      [0.42, 0.65, 0.55],
      [-0.42, 0.65, -0.5],
      [0.42, 0.65, -0.5],
    ],
    leg: 0.65,
    legR: 0.18,
  },
  sauro: {
    head: [0, 2.05, 1.25],
    hips: [
      [-0.36, 0.7, 0.45],
      [0.36, 0.7, 0.45],
      [-0.36, 0.7, -0.45],
      [0.36, 0.7, -0.45],
    ],
    leg: 0.7,
    legR: 0.17,
  },
  parasaur: {
    head: [0, 1.75, 0.35],
    hips: [
      [-0.25, 0.8, -0.05],
      [0.25, 0.8, -0.05],
    ],
    leg: 0.8,
    legR: 0.16,
  },
  pachy: {
    head: [0, 1.5, 0.25],
    hips: [
      [-0.24, 0.7, -0.05],
      [0.24, 0.7, -0.05],
    ],
    leg: 0.7,
    legR: 0.16,
  },
  compy: {
    head: [0, 1.45, 0.45],
    hips: [
      [-0.2, 0.72, -0.1],
      [0.2, 0.72, -0.1],
    ],
    leg: 0.72,
    legR: 0.12,
  },
  iggy: {
    head: [0, 1.95, 0.3],
    hips: [
      [-0.28, 0.9, -0.05],
      [0.28, 0.9, -0.05],
    ],
    leg: 0.9,
    legR: 0.18,
  },
  ovi: {
    head: [0, 1.45, 0.4],
    hips: [
      [-0.22, 0.72, -0.05],
      [0.22, 0.72, -0.05],
    ],
    leg: 0.72,
    legR: 0.13,
  },
};

/** The body (with head, tail and clothes) of one villager, feet at the origin, facing +z. */
function bodyFor(
  species: Species,
  folk: Folk,
  skin: string,
  cloth: [string, string],
  seed: number,
) {
  const belly = shade(skin, 1.45);
  const dark = shade(skin, 0.62);
  const p: THREE.BufferGeometry[] = [];
  const f = FRAMES[species];
  const [hx, hy, hz] = f.head;
  const eyes = (x: number, y: number, z: number, r = 0.11) => {
    for (const s of [-1, 1]) {
      p.push(part(sphere(r, 7, 5), "#ffffff", M([x + s * r * 1.5, y, z])));
      p.push(part(sphere(r * 0.5, 5, 4), "#1d1a18", M([x + s * r * 1.5, y + 0.01, z + r * 0.7])));
    }
  };
  if (FOURS.has(species)) {
    // A barrel of a body, level, the tail out behind.
    const len = species === "sauro" ? 1.0 : 1.2;
    p.push(part(sphere(0.62), skin, M([0, 0.95, 0], [0, 0, 0], [1.05, 0.82, len * 1.25])));
    p.push(part(sphere(0.5), belly, M([0, 0.78, 0.05], [0, 0, 0], [0.95, 0.6, len * 1.1])));
    p.push(part(cone(0.32, 1.5), skin, M([0, 0.85, -1.35], [-Math.PI / 2 - 0.12, 0, 0])));
    if (species === "ankylo") {
      // The armour: rows of knobs down the back, the club on the tail.
      for (let i = 0; i < 4; i++)
        for (const s of [-1, 0, 1])
          p.push(
            part(
              cone(0.13, 0.24, 5),
              dark,
              M([s * 0.38, 1.42 - Math.abs(s) * 0.12, 0.55 - i * 0.36]),
            ),
          );
      p.push(part(sphere(0.3, 7, 5), dark, M([0, 0.72, -2.05], [0, 0, 0], [1.3, 0.8, 1])));
      p.push(part(sphere(0.34), skin, M([hx, hy, hz], [0, 0, 0], [1.1, 0.8, 1.1])));
      eyes(hx, hy + 0.15, hz + 0.25, 0.08);
    } else if (species === "trike") {
      p.push(part(sphere(0.42), skin, M([hx, hy, hz], [0, 0, 0], [1, 0.9, 1.15])));
      p.push(part(cyl(0.68, 0.55, 0.12, 10), dark, M([hx, hy + 0.3, hz - 0.25], [-1.1, 0, 0])));
      for (const s of [-1, 1])
        p.push(
          part(
            cone(0.07, 0.55, 5),
            "#f4ead0",
            M([hx + s * 0.2, hy + 0.42, hz + 0.25], [1.0, 0, 0]),
          ),
        );
      p.push(part(cone(0.06, 0.3, 5), "#f4ead0", M([hx, hy + 0.05, hz + 0.5], [1.3, 0, 0])));
      p.push(part(cone(0.11, 0.2, 5), "#e8c070", M([hx, hy - 0.1, hz + 0.5], [Math.PI / 2, 0, 0])));
      eyes(hx, hy + 0.15, hz + 0.32, 0.08);
    } else {
      // The long neck up to a small head.
      p.push(part(cyl(0.26, 0.17, 1.4, 8), skin, M([0, 1.45, 0.75], [0.62, 0, 0])));
      p.push(part(sphere(0.27), skin, M([hx, hy, hz], [0, 0, 0], [1, 0.85, 1.3])));
      eyes(hx, hy + 0.1, hz + 0.2, 0.07);
    }
  } else {
    // Upright: a round torso leaning forward a little, the tail behind for balance.
    const lean = species === "iggy" || species === "parasaur" ? 0.3 : 0.2;
    const tall = species === "compy" ? 0.8 : 1;
    p.push(part(sphere(0.5), skin, M([0, 1.15 * tall, 0], [lean, 0, 0], [1, 1.2, 0.95])));
    p.push(part(sphere(0.38), belly, M([0, 1.1 * tall, 0.17], [lean, 0, 0], [0.92, 1.1, 0.7])));
    p.push(
      part(cone(0.27, 1.3 * tall), skin, M([0, 0.95 * tall, -0.85], [-Math.PI / 2 - 0.55, 0, 0])),
    );
    // Arms, held a little out.
    for (const s of [-1, 1]) {
      p.push(part(cyl(0.09, 0.07, 0.5), skin, M([s * 0.42, 1.2 * tall, 0.25], [0.9, 0, s * 0.35])));
      if (species === "iggy")
        p.push(part(cone(0.05, 0.2, 4), "#f4ead0", M([s * 0.5, 1.02 * tall, 0.47], [1.5, 0, 0])));
    }
    // Head.
    p.push(part(cyl(0.18, 0.14, 0.5, 7), skin, M([0, hy - 0.25, hz - 0.12], [0.3, 0, 0])));
    p.push(part(sphere(0.33), skin, M([hx, hy, hz], [0, 0, 0], [1, 0.92, 1.05])));
    eyes(hx, hy + 0.13, hz + 0.25, 0.09);
    if (species === "parasaur") {
      p.push(part(sphere(0.22), belly, M([hx, hy - 0.08, hz + 0.32], [0, 0, 0], [1.1, 0.45, 1.2])));
      p.push(part(cyl(0.1, 0.05, 0.9, 6), dark, M([hx, hy + 0.35, hz - 0.35], [-1.0, 0, 0])));
    } else if (species === "pachy") {
      p.push(
        part(
          sphere(0.3, 9, 6),
          shade(skin, 1.2),
          M([hx, hy + 0.2, hz - 0.03], [0, 0, 0], [1, 0.8, 1]),
        ),
      );
      for (let k = 0; k < 7; k++) {
        const a = (k / 7) * Math.PI * 2;
        p.push(
          part(
            cone(0.05, 0.12, 4),
            dark,
            M([hx + Math.sin(a) * 0.3, hy + 0.08, hz + Math.cos(a) * 0.28]),
          ),
        );
      }
    } else if (species === "ovi") {
      p.push(
        part(cone(0.12, 0.25, 5), "#f0b040", M([hx, hy - 0.04, hz + 0.36], [Math.PI / 2, 0, 0])),
      );
      p.push(part(box(0.06, 0.32, 0.26), cloth[1], M([hx, hy + 0.36, hz])));
      // A fan of tail feathers.
      for (let k = -2; k <= 2; k++)
        p.push(
          part(
            cone(0.08, 0.55, 4),
            shade(skin, 0.8),
            M([k * 0.1, 0.95, -1.5], [-Math.PI / 2 + 0.3, 0, k * 0.25]),
          ),
        );
    } else {
      p.push(part(sphere(0.2), belly, M([hx, hy - 0.06, hz + 0.28], [0, 0, 0], [1, 0.6, 1])));
    }
  }
  // The clothes, by kingdom.
  const [main, trim] = cloth;
  const neck: [number, number, number] = FOURS.has(species)
    ? [hx, hy - 0.25, hz - 0.35]
    : [0, hy - 0.42, hz - 0.12];
  const crown: [number, number, number] = [hx, hy + (species === "pachy" ? 0.42 : 0.3), hz - 0.02];
  const v = seed % 2;
  if (folk === "snow") {
    p.push(
      part(new THREE.TorusGeometry(0.24, 0.09, 5, 10), main, M(neck, [Math.PI / 2 - 0.3, 0, 0])),
    );
    p.push(
      part(
        box(0.14, 0.5, 0.06),
        main,
        M([neck[0] + 0.15, neck[1] - 0.25, neck[2] + 0.15], [0.2, 0, 0.2]),
      ),
    );
    if (v === 0) {
      p.push(part(sphere(0.27, 8, 5), main, M(crown, [0, 0, 0], [1, 0.7, 1])));
      p.push(part(sphere(0.1, 6, 4), trim, M([crown[0], crown[1] + 0.22, crown[2]])));
    }
  } else if (folk === "desert") {
    p.push(part(cyl(0.48, 0.48, 0.04, 12), "#e8c870", M(crown)));
    p.push(part(cyl(0.22, 0.18, 0.2, 10), "#e8c870", M([crown[0], crown[1] + 0.1, crown[2]])));
    p.push(part(cyl(0.22, 0.22, 0.05, 10), main, M([crown[0], crown[1] + 0.05, crown[2]])));
    if (!FOURS.has(species) && v === 1)
      p.push(part(cone(0.62, 0.7, 8), main, M([0, 1.35, 0.05], [0.2, 0, 0])));
  } else if (folk === "beach") {
    for (let k = 0; k < 8; k++) {
      const a = (k / 8) * Math.PI * 2;
      p.push(
        part(
          sphere(0.08, 5, 4),
          k % 2 ? main : trim,
          M([neck[0] + Math.sin(a) * 0.26, neck[1], neck[2] + Math.cos(a) * 0.22]),
        ),
      );
    }
    if (v === 1)
      p.push(part(sphere(0.1, 6, 4), main, M([crown[0] + 0.2, crown[1] - 0.05, crown[2] + 0.05])));
  } else if (folk === "dragon") {
    if (!FOURS.has(species)) {
      p.push(part(cyl(0.5, 0.42, 0.75, 9), main, M([0, 1.05, 0.02], [0.2, 0, 0])));
      p.push(part(cyl(0.52, 0.52, 0.08, 9), trim, M([0, 0.7, 0.0], [0.2, 0, 0])));
    } else p.push(part(box(0.9, 0.06, 1.0), main, M([0, 1.5, 0.1])));
    p.push(part(cone(0.3, 0.45, 8), main, M([crown[0], crown[1] + 0.05, crown[2] - 0.1])));
  } else if (folk === "valley") {
    for (let k = 0; k < 7; k++) {
      const a = (k / 7) * Math.PI * 2;
      p.push(
        part(
          cone(0.09, 0.22, 4),
          k % 2 ? main : shade(main, 1.3),
          M(
            [neck[0] + Math.sin(a) * 0.27, neck[1] - 0.05, neck[2] + Math.cos(a) * 0.23],
            [Math.PI, 0, 0],
          ),
        ),
      );
    }
    if (v === 1)
      p.push(part(sphere(0.07, 5, 4), trim, M([neck[0], neck[1] - 0.12, neck[2] + 0.25])));
  } else {
    // On the road: a traveller's pack.
    p.push(part(box(0.5, 0.55, 0.3), main, M([0, FOURS.has(species) ? 1.5 : 1.25, -0.45])));
    p.push(
      part(
        cyl(0.12, 0.12, 0.55, 6),
        trim,
        M([0, FOURS.has(species) ? 1.85 : 1.6, -0.45], [0, 0, Math.PI / 2]),
      ),
    );
  }
  return merge(p);
}

function legFor(species: Species, skin: string) {
  const f = FRAMES[species];
  const dark = shade(skin, 0.75);
  return merge([
    part(cyl(f.legR, f.legR * 0.8, f.leg, 7), skin, M([0, -f.leg / 2, 0])),
    part(
      sphere(f.legR * 1.15, 7, 5),
      dark,
      M([0, -f.leg + 0.04, f.legR * 0.5], [0, 0, 0], [1, 0.5, 1.4]),
    ),
  ]);
}

let shared: THREE.MeshLambertMaterial | undefined;
const bodies = new Map<string, THREE.BufferGeometry>();
const legs = new Map<string, THREE.BufferGeometry>();

export interface VillagerView {
  readonly root: THREE.Group;
  /** Place it; `walk` 0..1 how fast it's walking (its stride), `t` seconds, `look` the
   * head's turn (radians, a glance at you). */
  update(x: number, y: number, z: number, heading: number, walk: number, t: number): void;
  dispose(): void;
}

/** A villager's look, all picked by its seed. */
export function villagerLook(folk: Folk, seed: number, kind?: Species) {
  const species = kind ?? SPECIES[seed % SPECIES.length]!;
  const skins = SKINS[folk];
  const cloths = CLOTH[folk];
  return {
    species,
    skin: skins[Math.floor(seed / 8) % skins.length]!,
    cloth: cloths[Math.floor(seed / 3) % cloths.length]!,
  };
}

export function createVillagerView(
  parent: THREE.Object3D,
  folk: Folk,
  seed: number,
  kind?: Species,
): VillagerView {
  shared ??= new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });
  const { species, skin, cloth } = villagerLook(folk, seed, kind);
  const key = `${species}|${folk}|${skin}|${cloth.join()}|${seed % 2}`;
  let bg = bodies.get(key);
  if (!bg) bodies.set(key, (bg = bodyFor(species, folk, skin, cloth, seed)));
  const lk = `${species}|${skin}`;
  let lg = legs.get(lk);
  if (!lg) legs.set(lk, (lg = legFor(species, skin)));
  const root = new THREE.Group();
  root.name = `Villager ${species}`;
  const inner = new THREE.Group();
  const s = SIZE[species].scale;
  inner.scale.setScalar(s);
  root.add(inner);
  const body = new THREE.Mesh(bg, shared);
  body.castShadow = false;
  inner.add(body);
  const f = FRAMES[species];
  const legMeshes = f.hips.map((h) => {
    const pivot = new THREE.Group();
    pivot.position.set(...h);
    pivot.add(new THREE.Mesh(lg, shared));
    inner.add(pivot);
    return pivot;
  });
  // A soft round shadow under it.
  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(FOURS.has(species) ? 1.1 : 0.6, 12),
    new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.25,
      depthWrite: false,
    }),
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = 0.04;
  shadow.scale.setScalar(s);
  root.add(shadow);
  parent.add(root);
  const phase = (seed * 0.731) % (Math.PI * 2);
  return {
    root,
    update(x, y, z, heading, walk, t) {
      root.position.set(x, y, z);
      root.rotation.y = heading;
      const stride = Math.min(1, walk);
      const cadence = (FOURS.has(species) ? 5 : 7) / Math.sqrt(s);
      const a = t * cadence + phase;
      legMeshes.forEach((l, i) => {
        // (Two legs: opposite. Four: the diagonal pairs together.)
        const opp = FOURS.has(species) ? (i === 0 || i === 3 ? 0 : Math.PI) : i * Math.PI;
        l.rotation.x = Math.sin(a + opp) * 0.55 * stride;
      });
      body.position.y = Math.abs(Math.sin(a)) * 0.06 * stride + Math.sin(t * 1.7 + phase) * 0.015;
      body.rotation.z = Math.sin(a) * 0.04 * stride;
    },
    dispose() {
      parent.remove(root);
      (shadow.material as THREE.Material).dispose();
      shadow.geometry.dispose();
    },
  };
}
