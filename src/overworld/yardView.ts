/**
 * The overworld's yard things in the scene: the obstacles across a yard's way in or a
 * passage (a rockfall, ice, a drift, deep water, fire) and the secrets' treasure chests.
 * (Once the puzzles' switches too: Blake cut the puzzles, Oct 27.)
 */
import * as THREE from "three";

const GOLD = 0xf0c040;

/** A tool obstacle across a yard's way in (regions.ts ReturnSpot): a rockfall, a wall of
 * ice, a sand drift or a deep channel. Shown while it's still shut. */
export function createObstacleView(
  root: THREE.Object3D,
  kind: "rockfall" | "ice" | "drift" | "water" | "fire",
  gate: { x: number; z: number; heading: number; width: number },
  groundAt: (x: number, z: number) => number,
) {
  const group = new THREE.Group();
  group.position.set(gate.x, groundAt(gate.x, gate.z), gate.z);
  group.rotation.y = gate.heading;
  const geos: THREE.BufferGeometry[] = [];
  const mats: THREE.Material[] = [];
  const w = gate.width + 1;
  if (kind === "rockfall") {
    const g = new THREE.IcosahedronGeometry(1, 0);
    const m = new THREE.MeshLambertMaterial({ color: 0x8a7a6a, flatShading: true });
    geos.push(g);
    mats.push(m);
    for (let k = 0; k < 9; k++) {
      const b = new THREE.Mesh(g, m);
      const s = 1.3 + ((k * 37) % 10) / 10;
      b.scale.setScalar(s);
      b.position.set(-w / 2 + (k % 5) * (w / 4), s * 0.7 + (k >= 5 ? 1.6 : 0), (k % 2) - 0.5);
      b.rotation.set(k, k * 2, k * 3);
      group.add(b);
    }
  } else {
    const look = {
      fire: { color: 0xff6a20, opacity: 0.55, h: 5, d: 1.2 },
      ice: { color: 0xbfe6ff, opacity: 0.85, h: 7, d: 1.6 },
      drift: { color: 0xe0b27a, opacity: 1, h: 3.5, d: 6 },
      water: { color: 0x2a7ab8, opacity: 0.8, h: 0.4, d: 8 },
    }[kind];
    const g =
      kind === "drift"
        ? new THREE.SphereGeometry(1, 12, 8)
        : new THREE.BoxGeometry(w, look.h, look.d);
    const m =
      kind === "fire"
        ? new THREE.MeshBasicMaterial({
            color: look.color,
            transparent: true,
            opacity: look.opacity,
            depthWrite: false,
          })
        : new THREE.MeshLambertMaterial({
            color: look.color,
            transparent: look.opacity < 1,
            opacity: look.opacity,
          });
    geos.push(g);
    mats.push(m);
    const mesh = new THREE.Mesh(g, m);
    if (kind === "drift") mesh.scale.set(w / 2 + 1, look.h, look.d / 2);
    else mesh.position.y = kind === "water" ? 0.1 : look.h / 2 - 0.5;
    group.add(mesh);
  }
  root.add(group);
  const y0 = group.position.y;
  return {
    set shown(v: boolean) {
      group.visible = v;
    },
    /** 0 standing .. 1 gone into the ground (breaking open). */
    set sunk(t: number) {
      group.position.y = y0 - t * 8;
      group.visible = t < 1;
    },
    /** Flames flicker. */
    flicker(t: number) {
      if (kind === "fire") group.scale.y = 1 + 0.15 * Math.sin(t * 13) + 0.1 * Math.sin(t * 7.3);
    },
    dispose() {
      root.remove(group);
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

/** A treasure chest (a region's secret): shut and gleaming until found, then open. */
export function createChestView(
  root: THREE.Object3D,
  spot: { x: number; z: number },
  heading: number,
  groundAt: (x: number, z: number) => number,
) {
  const group = new THREE.Group();
  group.position.set(spot.x, groundAt(spot.x, spot.z), spot.z);
  group.rotation.y = heading;
  const wood = new THREE.MeshLambertMaterial({ color: 0x7a4a24 });
  const gold = new THREE.MeshLambertMaterial({ color: GOLD, emissive: 0x503008 });
  const bodyG = new THREE.BoxGeometry(2.4, 1.3, 1.6);
  const lidG = new THREE.BoxGeometry(2.5, 0.5, 1.7);
  const bandG = new THREE.BoxGeometry(0.25, 1.9, 1.75);
  const body = new THREE.Mesh(bodyG, wood);
  body.position.y = 0.65 + 1.2;
  const lid = new THREE.Group();
  lid.position.set(0, 1.3 + 1.2, -0.8);
  const lidM = new THREE.Mesh(lidG, wood);
  lidM.position.set(0, 0.25, 0.8);
  lid.add(lidM);
  for (const x of [-0.8, 0.8]) {
    const b = new THREE.Mesh(bandG, gold);
    b.position.set(x, 0.95 + 1.2, 0);
    group.add(b);
  }
  group.add(body, lid);
  root.add(group);
  return {
    set open(v: boolean) {
      lid.rotation.x = v ? -1.9 : 0;
    },
    dispose() {
      root.remove(group);
      for (const g of [bodyG, lidG, bandG]) g.dispose();
      wood.dispose();
      gold.dispose();
    },
  };
}
