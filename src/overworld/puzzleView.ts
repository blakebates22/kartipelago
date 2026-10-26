/**
 * The overworld puzzles' things in the scene (src/overworld/puzzles.ts): the switch
 * stones, each with a beam of light over it until it's pressed; the gate, which sinks
 * into the ground once the puzzle's solved; and the prize behind it, turning in the air.
 */
import * as THREE from "three";
import type { Puzzle, PuzzleState } from "./puzzles";

export interface PuzzleView {
  /** Show the state (call each frame; `t` is seconds, for the animation). */
  update(st: PuzzleState, prizeTaken: boolean, prizeShown: boolean, t: number, dt: number): void;
  dispose(): void;
}

const GOLD = 0xf0c040;
const DIM = 0x8a6a30;

/** A key out of primitives: a ring for its bow, a shaft and two teeth. */
function keyMesh(mat: THREE.Material, geos: THREE.BufferGeometry[]) {
  const g = new THREE.Group();
  const bow = new THREE.TorusGeometry(0.9, 0.28, 8, 18);
  const shaft = new THREE.BoxGeometry(0.34, 2.6, 0.34);
  const tooth = new THREE.BoxGeometry(0.7, 0.3, 0.3);
  geos.push(bow, shaft, tooth);
  const b = new THREE.Mesh(bow, mat);
  b.position.y = 1.2;
  g.add(b);
  const s = new THREE.Mesh(shaft, mat);
  s.position.y = -0.8;
  g.add(s);
  for (const y of [-1.7, -1.2]) {
    const t = new THREE.Mesh(tooth, mat);
    t.position.set(0.45, y, 0);
    g.add(t);
  }
  return g;
}

export function createPuzzleView(
  root: THREE.Object3D,
  p: Puzzle,
  groundAt: (x: number, z: number) => number,
): PuzzleView {
  const group = new THREE.Group();
  group.name = `Puzzle ${p.id}`;
  const geos: THREE.BufferGeometry[] = [];
  const mats: THREE.Material[] = [];
  const mat = <M extends THREE.Material>(m: M) => (mats.push(m), m);
  const stoneM = mat(new THREE.MeshLambertMaterial({ color: 0xb09870 }));
  const plateG = new THREE.CylinderGeometry(p.radius, p.radius + 0.4, 0.8, 20);
  const runeG = new THREE.CircleGeometry(p.radius * 0.6, 3);
  const beamG = new THREE.CylinderGeometry(1.1, 1.1, 40, 12, 1, true);
  geos.push(plateG, runeG, beamG);
  const switches = p.switches.map((s) => {
    const y = groundAt(s.x, s.z);
    const plate = new THREE.Group();
    plate.position.set(s.x, y, s.z);
    plate.add(new THREE.Mesh(plateG, stoneM));
    const runeM = mat(new THREE.MeshBasicMaterial({ color: DIM }));
    const rune = new THREE.Mesh(runeG, runeM);
    rune.rotation.x = -Math.PI / 2;
    rune.position.y = 0.42;
    plate.add(rune);
    const beamM = mat(
      new THREE.MeshBasicMaterial({
        color: GOLD,
        transparent: true,
        opacity: 0.22,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    );
    const beam = new THREE.Mesh(beamG, beamM);
    beam.position.set(s.x, y + 20, s.z);
    group.add(plate, beam);
    return { plate, runeM, beam, y };
  });
  // The gate: a slab of stone across the gateway, the puzzle's rune on it.
  const gy = groundAt(p.gate.x, p.gate.z);
  const slabG = new THREE.BoxGeometry(p.gate.width + 0.4, 7, 1.2);
  geos.push(slabG);
  const gate = new THREE.Group();
  gate.position.set(p.gate.x, gy, p.gate.z);
  gate.rotation.y = p.gate.heading;
  const slab = new THREE.Mesh(slabG, mat(new THREE.MeshLambertMaterial({ color: 0x9a8058 })));
  slab.position.y = 3.5 - 1.5;
  gate.add(slab);
  const gateRune = new THREE.Mesh(
    runeG,
    mat(new THREE.MeshBasicMaterial({ color: GOLD, side: THREE.DoubleSide })),
  );
  gateRune.position.set(0, 3.2, 0.62);
  gate.add(gateRune);
  group.add(gate);
  let sink = 0;
  // The prize.
  const keyM = mat(new THREE.MeshLambertMaterial({ color: GOLD, emissive: 0x604010 }));
  const prize = p.prize ? keyMesh(keyM, geos) : undefined;
  const py = p.prize ? groundAt(p.prize.x, p.prize.z) : 0;
  if (prize && p.prize) {
    prize.position.set(p.prize.x, py + 3.2, p.prize.z);
    group.add(prize);
  }
  root.add(group);

  return {
    update(st, taken, shown, t, dt) {
      switches.forEach((s, i) => {
        const down = st.pressed[i]!;
        s.plate.position.y = s.y - (down ? 0.45 : 0);
        s.runeM.color.setHex(down ? GOLD : DIM);
        // The beam over each stone still to press; it flickers as the drums run out.
        const hurry = st.left > 0 && st.left < 4 && Math.sin(t * 18) > 0;
        s.beam.visible = !down && !st.solved && !hurry;
      });
      sink = st.solved ? Math.min(1, sink + dt / 1.6) : 0;
      gate.position.y = gy - sink * 7.2;
      gate.visible = sink < 1;
      if (prize) {
        prize.visible = shown && !taken;
        prize.rotation.y = t * 1.6;
        prize.position.y = py + 3.2 + Math.sin(t * 2.2) * 0.3;
      }
    },
    dispose() {
      root.remove(group);
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
