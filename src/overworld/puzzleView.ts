/**
 * The overworld puzzles' things in the scene (src/overworld/puzzles.ts): the switch
 * stones, each with a beam of light over it until it's pressed; the gate, which sinks
 * into the ground once the puzzle's solved; and the prize behind it, turning in the air.
 */
import * as THREE from "three";
import { BELL_HALF_SPAN, bellHeading, type Puzzle, type PuzzleState } from "./puzzles";

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
  // Bells: a frame over the way (two posts and a beam), the bell hanging in it, and
  // the clue behind it: its lanterns.
  const postG = new THREE.BoxGeometry(0.9, 8, 0.9);
  const beamBarG = new THREE.BoxGeometry(BELL_HALF_SPAN * 2 + 1, 0.8, 0.9);
  const bellG = new THREE.CylinderGeometry(0.5, 1.6, 2.2, 14, 1, true);
  const lampPostG = new THREE.BoxGeometry(0.3, 3.2, 0.3);
  const lampG = new THREE.BoxGeometry(0.7, 0.8, 0.7);
  const gongG = new THREE.CylinderGeometry(1.9, 1.9, 0.3, 20);
  geos.push(postG, beamBarG, bellG, gongG, lampPostG, lampG);
  const woodM = mat(new THREE.MeshLambertMaterial({ color: 0x6a4a2a }));
  const lampM = mat(new THREE.MeshBasicMaterial({ color: 0xffd070 }));
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
    let bell: THREE.Object3D | undefined;
    let bellM: THREE.MeshLambertMaterial | undefined;
    if (p.look !== "stone") {
      const frame = new THREE.Group();
      frame.position.set(s.x, y, s.z);
      frame.rotation.y = bellHeading(s);
      for (const side of [-1, 1]) {
        const post = new THREE.Mesh(postG, woodM);
        post.position.set(side * BELL_HALF_SPAN, 4, 0);
        frame.add(post);
      }
      const bar = new THREE.Mesh(beamBarG, woodM);
      bar.position.y = 8;
      frame.add(bar);
      bellM = mat(new THREE.MeshLambertMaterial({ color: 0x8a6a3a, side: THREE.DoubleSide }));
      const pivot = new THREE.Group();
      pivot.position.y = 7.6;
      const b = new THREE.Mesh(p.look === "gong" ? gongG : bellG, bellM);
      if (p.look === "gong") b.rotation.x = Math.PI / 2;
      b.position.y = -1.3;
      pivot.add(b);
      frame.add(pivot);
      bell = pivot;
      // The lanterns: behind the frame (away from the middle), in a row.
      const n = s.lanterns ?? 0;
      for (let k = 0; k < n; k++) {
        const lx = (k - (n - 1) / 2) * 2.2;
        const lp = new THREE.Mesh(lampPostG, woodM);
        lp.position.set(lx, 1.6, -4);
        const lamp = new THREE.Mesh(lampG, lampM);
        lamp.position.set(lx, 3.5, -4);
        frame.add(lp, lamp);
      }
      group.add(frame);
    }
    return { plate, runeM, beam, y, bell, bellM, rung: -1 };
  });
  // The gate: a slab of stone across the gateway, the puzzle's rune on it.
  const gy = groundAt(p.gate.x, p.gate.z);
  const slabG = new THREE.BoxGeometry(p.gate.width + 0.4, 7, 1.2);
  geos.push(slabG);
  const gate = new THREE.Group();
  gate.position.set(p.gate.x, gy, p.gate.z);
  gate.rotation.y = p.gate.heading;
  const slab = new THREE.Mesh(
    slabG,
    mat(
      p.look === "bell"
        ? new THREE.MeshLambertMaterial({ color: 0xbfe6ff, transparent: true, opacity: 0.85 })
        : new THREE.MeshLambertMaterial({ color: 0x9a8058 }),
    ),
  );
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
        // A rung bell glows and swings a while.
        if (s.bell && s.bellM) {
          if (down && s.rung < 0) s.rung = t;
          if (!down) s.rung = -1;
          s.bellM.color.setHex(down ? GOLD : 0x8a6a3a);
          const since = s.rung < 0 ? 99 : t - s.rung;
          s.bell.rotation.x = Math.sin(since * 6) * 0.5 * Math.exp(-since * 0.5);
        }
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
