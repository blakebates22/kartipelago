/**
 * Scenery for open tracks: tunnel rock and roof, the cliffs round the map boundary,
 * trees, and low hills beyond the boundary. Purely visual; collision is in
 * physics/walls.ts (stepSolids) from the same solids.
 */
import * as THREE from "three";
import type { Solid, SolidBox, Tunnel } from "../world/solids";

export interface SceneryLook {
  rockColor: string;
  treeColor: string;
  trunkColor: string;
  hillColor: string;
}

/** Deterministic pseudo-random 0..1 from a number, for varied but stable shapes. */
const hash = (n: number) => {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
};

export function createSceneryView(
  scene: THREE.Object3D,
  solids: Solid[],
  tunnels: Tunnel[],
  look: SceneryLook,
) {
  const rockMat = new THREE.MeshStandardMaterial({ color: look.rockColor, flatShading: true });
  const cliffMat = new THREE.MeshStandardMaterial({ color: look.rockColor, flatShading: true });
  const trunkMat = new THREE.MeshStandardMaterial({ color: look.trunkColor, flatShading: true });
  const leafMat = new THREE.MeshStandardMaterial({ color: look.treeColor, flatShading: true });
  const hillMat = new THREE.MeshStandardMaterial({ color: look.hillColor, flatShading: true });
  const group = new THREE.Group();

  const boxMesh = (b: SolidBox, mat: THREE.Material) => {
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(b.halfWidth * 2, b.height, b.halfLength * 2),
      mat,
    );
    m.position.set(b.x, b.height / 2, b.z);
    m.rotation.y = b.heading;
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  };

  for (const b of solids) {
    if (b.kind === "box") group.add(boxMesh(b, b.look === "rock" ? rockMat : cliffMat));
  }

  // Tunnel roofs, with rocky lumps on top so the tunnel reads as a hill, not a box.
  tunnels.forEach((t, k) => {
    const span = (t.roadHalfWidth + t.thickness) * 2;
    const roof = new THREE.Mesh(new THREE.BoxGeometry(span, 3, t.halfLength * 2), rockMat);
    roof.position.set(t.x, t.y + t.height + 1.5, t.z);
    roof.rotation.y = t.heading;
    roof.castShadow = true;
    roof.receiveShadow = true;
    group.add(roof);
    const fx = Math.sin(t.heading);
    const fz = Math.cos(t.heading);
    // Lumps sit on the roof (sunk a little into its 3 m slab), never hanging into the
    // tunnel, and stay within the rock's footprint.
    const roofTop = t.y + t.height + 3;
    for (let i = 0; i < 10; i++) {
      const size = 7 + hash(k * 7 + i * 5) * 9;
      const along = (hash(k * 31 + i) - 0.5) * Math.max(0, t.halfLength * 2 - size * 1.2);
      const across = (hash(k * 17 + i * 3) - 0.5) * Math.max(0, span - size * 1.2);
      const lump = new THREE.Mesh(new THREE.DodecahedronGeometry(size, 0), rockMat);
      lump.scale.y = 0.55;
      lump.position.set(
        t.x + fx * along + fz * across,
        roofTop + size * 0.55 - 2.5,
        t.z + fz * along - fx * across,
      );
      lump.rotation.y = hash(i + 9) * 3;
      lump.castShadow = true;
      group.add(lump);
    }
  });

  // Trees: a trunk and two stacked cones, instanced (there are many of them).
  const trees = solids.filter((s) => s.kind === "circle");
  if (trees.length) {
    const trunk = new THREE.InstancedMesh(
      new THREE.CylinderGeometry(0.6, 0.8, 3, 7),
      trunkMat,
      trees.length,
    );
    const lower = new THREE.InstancedMesh(new THREE.ConeGeometry(3.4, 5, 8), leafMat, trees.length);
    const upper = new THREE.InstancedMesh(new THREE.ConeGeometry(2.4, 4, 8), leafMat, trees.length);
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const v = new THREE.Vector3();
    const sc = new THREE.Vector3();
    trees.forEach((t, i) => {
      const s = 0.8 + hash(i) * 0.6;
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), hash(i + 50) * Math.PI);
      sc.set(s, s, s);
      trunk.setMatrixAt(i, m.compose(v.set(t.x, 1.5 * s, t.z), q, sc));
      lower.setMatrixAt(i, m.compose(v.set(t.x, 5 * s, t.z), q, sc));
      upper.setMatrixAt(i, m.compose(v.set(t.x, 8 * s, t.z), q, sc));
    });
    for (const im of [trunk, lower, upper]) {
      im.castShadow = true;
      group.add(im);
    }
  }

  // Rolling hills just beyond the boundary, so the edge of the map is a landscape.
  const edges = solids.filter((s): s is SolidBox => s.kind === "box" && s.look === "boundary");
  edges.forEach((e, k) => {
    const fx = Math.sin(e.heading);
    const fz = Math.cos(e.heading);
    // Outward: away from the middle of the map.
    const mid = edges.reduce((a, b) => ({ x: a.x + b.x / 4, z: a.z + b.z / 4 }), { x: 0, z: 0 });
    let ox = fz;
    let oz = -fx;
    if ((e.x - mid.x) * ox + (e.z - mid.z) * oz < 0) {
      ox = -ox;
      oz = -oz;
    }
    const count = Math.max(3, Math.round(e.halfLength / 22));
    for (let i = 0; i < count; i++) {
      const along = (i / (count - 1) - 0.5) * 2 * e.halfLength;
      const r = 26 + hash(k * 13 + i) * 22;
      const hill = new THREE.Mesh(new THREE.SphereGeometry(r, 9, 6), hillMat);
      const out = r * 0.55 + hash(k * 5 + i * 7) * 15;
      hill.position.set(e.x + fx * along + ox * out, -r * 0.45, e.z + fz * along + oz * out);
      hill.scale.y = 0.8;
      group.add(hill);
    }
  });

  scene.add(group);
  return {
    render(colors: SceneryLook) {
      rockMat.color.set(colors.rockColor);
      cliffMat.color.set(colors.rockColor);
      trunkMat.color.set(colors.trunkColor);
      leafMat.color.set(colors.treeColor);
      hillMat.color.set(colors.hillColor);
    },
  };
}
