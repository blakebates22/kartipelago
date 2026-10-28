/**
 * Ember Peak's dragon: an original, low-poly prehistoric fire-breather perched on a
 * crag. A massive dark red-brown body on clawed legs gripping the rock, a long neck in
 * two joints, a horned head with glowing eyes and a hinged jaw, a throat that glows
 * orange as it draws breath, great leathery wings and a spined tail draped down the
 * crag.
 *
 * Built in code (well under 2k triangles). It only shows the attack the game's clock
 * says (game/dragon.ts): turning its head to the road, rearing up with its wings
 * spread and its throat glowing, then lunging forward with its jaws open.
 */
import * as THREE from "three";
import type { DragonPhase } from "../game/dragon";

export interface DragonView {
  readonly root: THREE.Group;
  /** Pose it for the attack phase (t: 0..1 through it), looking at `target` (world). */
  update(phase: DragonPhase, t: number, time: number, target: THREE.Vector3): void;
  /** The mouth's world position (where the fire comes from). */
  mouth(out: THREE.Vector3): THREE.Vector3;
  dispose(): void;
}

const SCALES = "#5a2216";
const DARK = "#3a140e";
const BELLY = "#b2683a";
const WING = "#7a2a18";
const HORN = "#e0d2b0";
const SPINE = "#2a0e0a";

const ease = (t: number) => t * t * (3 - 2 * t);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** The dragons' colours: Cinderjaw's ember (and Impact Depths' obsidian), Rimefang's
 * frost, Scorchwind's sand, Tidewyrm's sea, the King's, and Lumen's gold (a hatchling;
 * `lumen_grown` full-grown). The cutscenes give each its own design
 * (render/storyDragon.ts). */
export type DragonLook =
  "ember" | "obsidian" | "frost" | "sand" | "sea" | "king" | "lumen" | "lumen_grown";

export function createDragonView(
  parent: THREE.Object3D,
  pos: { x: number; y: number; z: number },
  heading: number,
  scale = 1,
  look: DragonLook = "ember",
): DragonView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const mat = (color: string, opts: THREE.MeshLambertMaterialParameters = {}) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
    mats.push(m);
    return m;
  };
  const geo = <G extends THREE.BufferGeometry>(g: G) => (geos.push(g), g);
  // Impact Depths' dragon is obsidian-black with molten spines and a crimson membrane.
  const ob = look === "obsidian";
  // The other dragons' colours (the staged scenes: Rimefang, Scorchwind, Tidewyrm, the
  // King): scales, dark, belly, wing.
  const TINT: Record<string, [string, string, string, string]> = {
    frost: ["#8ab4d8", "#3a5a7a", "#e0f0ff", "#6a9ac8"],
    sand: ["#c89a5a", "#6a4a2a", "#f0d8a0", "#a8743a"],
    sea: ["#2a7a7a", "#0f3a3a", "#8ad8c8", "#1f5a6a"],
    king: ["#5a2a8a", "#2a0f3a", "#c8a040", "#7a3aa0"],
    // Lumen, out of his robe: pale gold.
    lumen: ["#f0d890", "#8a6a30", "#fff6d8", "#f4e0a0"],
    lumen_grown: ["#f4d070", "#9a7020", "#fff8e0", "#ffe8a0"],
  };
  const tint = TINT[look === "lumen_grown" ? "lumen" : look];
  const scales = mat(tint ? tint[0] : ob ? "#26202a" : SCALES);
  const dark = mat(tint ? tint[1] : ob ? "#120e14" : DARK);
  const belly = mat(tint ? tint[2] : ob ? "#6a3a2a" : BELLY);
  const horn = mat(ob ? "#e8dcc0" : HORN);
  const spine = ob
    ? mat("#ff6a1a", { emissive: new THREE.Color("#ff4a10"), emissiveIntensity: 0.9 })
    : mat(SPINE);
  const wingMat = mat(tint ? tint[3] : ob ? "#5a1418" : WING, { side: THREE.DoubleSide });
  const eyeMat = mat("#ffd040", { emissive: new THREE.Color("#ffb020"), emissiveIntensity: 1.4 });
  const throatMat = mat("#c04010", {
    emissive: new THREE.Color("#ff6a10"),
    emissiveIntensity: 0.2,
  });
  const mouthMat = mat("#ff8a20", { emissive: new THREE.Color("#ff5a10"), emissiveIntensity: 0.3 });

  const blob = (m: THREE.Material, r: number, sx: number, sy: number, sz: number, detail = 1) => {
    const mesh = new THREE.Mesh(geo(new THREE.IcosahedronGeometry(r, detail)), m);
    mesh.scale.set(sx, sy, sz);
    return mesh;
  };
  /** A tapered limb from a to b (local points). */
  const limb = (
    m: THREE.Material,
    a: THREE.Vector3,
    b: THREE.Vector3,
    r0: number,
    r1: number,
    sides = 6,
  ) => {
    const len = a.distanceTo(b);
    const mesh = new THREE.Mesh(geo(new THREE.CylinderGeometry(r1, r0, len, sides)), m);
    mesh.position.copy(a).add(b).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    return mesh;
  };
  const cone = (m: THREE.Material, r: number, h: number, sides = 5) =>
    new THREE.Mesh(geo(new THREE.ConeGeometry(r, h, sides)), m);
  const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);

  const root = new THREE.Group();
  root.name = "dragon";
  root.position.set(pos.x, pos.y, pos.z);
  root.rotation.y = heading;
  root.scale.setScalar(scale);
  parent.add(root);

  // The body: a deep chest, a paler belly, a ridge of spines.
  const body = new THREE.Group();
  root.add(body);
  const torso = blob(scales, 1, 5, 4.6, 9.5);
  torso.position.set(0, 7, -1);
  const chest = blob(scales, 1, 4.6, 4.8, 4.6);
  chest.position.set(0, 8.5, 5);
  const under = blob(belly, 1, 4.0, 3.2, 8.0);
  under.position.set(0, 5.2, 0.5);
  body.add(torso, chest, under);
  for (let k = 0; k < 6; k++) {
    const sp = cone(spine, 0.8, 3.0 - k * 0.2, 4);
    sp.position.set(0, 12 - k * 0.5, 4 - k * 3);
    sp.rotation.x = -0.4;
    body.add(sp);
  }
  // Legs gripping the crag, with claws.
  for (const sd of [-1, 1]) {
    const hip = V(sd * 3.6, 6, -5);
    const knee = V(sd * 5.2, 3.4, -2.5);
    const foot = V(sd * 4.8, 0, -4.5);
    body.add(limb(scales, hip, knee, 2.2, 1.6), limb(dark, knee, foot, 1.5, 1.0));
    const shoulder = V(sd * 3.6, 7, 6);
    const elbow = V(sd * 4.6, 3.2, 8.5);
    const paw = V(sd * 4.2, 0.2, 10.5);
    body.add(limb(scales, shoulder, elbow, 1.8, 1.3), limb(dark, elbow, paw, 1.2, 0.9));
    for (const [f, p] of [
      [0, foot],
      [1, paw],
    ] as const) {
      for (let c = -1; c <= 1; c++) {
        const claw = cone(horn, 0.35, 2.0, 4);
        claw.position.set(p.x + c * 0.8, p.y - 0.3, p.z + (f ? 1.4 : 1.2));
        claw.rotation.x = Math.PI / 2 + 0.6;
        body.add(claw);
      }
    }
  }
  // The tail, draped back and down the crag, with a spiked tip (it swishes slowly).
  const tail = new THREE.Group();
  tail.position.set(0, 6, -9);
  body.add(tail);
  const tailPts = [
    V(0, 6, -9),
    V(1.5, 4.5, -14),
    V(4, 1, -18),
    V(6, -4, -21),
    V(6.5, -10, -22),
    V(5.5, -15, -21),
  ];
  for (const p of tailPts) p.sub(tail.position);
  for (let k = 0; k < tailPts.length - 1; k++)
    tail.add(
      limb(k % 2 ? dark : scales, tailPts[k]!, tailPts[k + 1]!, 2.4 - k * 0.42, 2.0 - k * 0.38),
    );
  const tip = cone(spine, 0.9, 3.5, 4);
  tip.position.copy(tailPts.at(-1)!).add(V(0, -1.5, 0));
  tip.rotation.x = Math.PI;
  tail.add(tip);

  // The wings: an arm and three long fingers, with membrane between.
  const wings: THREE.Group[] = [];
  for (const sd of [-1, 1]) {
    const w = new THREE.Group();
    w.position.set(sd * 3.4, 11, 2);
    body.add(w);
    wings.push(w);
    const elbow = V(sd * 9, 6, -3);
    const tips = [V(sd * 26, 10, -2), V(sd * 24, 2, -10), V(sd * 17, -3, -15)];
    w.add(limb(dark, V(0, 0, 0), elbow, 1.0, 0.7, 5));
    for (const tp of tips) w.add(limb(dark, elbow, tp, 0.6, 0.15, 4));
    const g = new THREE.BufferGeometry();
    const pts = [
      V(0, 0, 0),
      elbow,
      tips[0]!,
      elbow,
      tips[0]!,
      tips[1]!,
      elbow,
      tips[1]!,
      tips[2]!,
      V(0, 0, 0),
      elbow,
      tips[2]!,
      V(0, 0, 0),
      tips[2]!,
      V(sd * 2, -2, -9),
    ];
    g.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(
        pts.flatMap((p) => [p.x, p.y, p.z]),
        3,
      ),
    );
    g.computeVertexNormals();
    geos.push(g);
    w.add(new THREE.Mesh(g, wingMat));
  }

  // The neck in two joints, and the head.
  const neckA = new THREE.Group();
  neckA.position.set(0, 10, 7.5);
  body.add(neckA);
  neckA.add(limb(scales, V(0, 0, 0), V(0, 5.5, 5), 2.6, 2.0));
  const throat = blob(throatMat, 1, 1.7, 1.5, 3.2, 1);
  throat.position.set(0, 1.8, 3.4);
  neckA.add(throat);
  const neckB = new THREE.Group();
  neckB.position.set(0, 5.5, 5);
  neckA.add(neckB);
  neckB.add(limb(scales, V(0, 0, 0), V(0, 4.5, 4.5), 2.0, 1.6));
  const throat2 = blob(throatMat, 1, 1.4, 1.2, 2.6, 1);
  throat2.position.set(0, 1.4, 2.6);
  neckB.add(throat2);
  for (let k = 0; k < 4; k++) {
    const sp = cone(spine, 0.55, 2.0, 4);
    sp.position.set(0, (k < 2 ? 2.2 : 1.8) + k * 1.2, (k < 2 ? 1 : 0.6) + k * 1.1);
    sp.rotation.x = -0.6;
    (k < 2 ? neckA : neckB).add(sp);
  }
  const eyes: THREE.Mesh[] = [];
  const head = new THREE.Group();
  head.position.set(0, 4.5, 4.5);
  neckB.add(head);
  const skull = blob(scales, 1, 2.3, 1.9, 3.0);
  skull.position.set(0, 0.6, 1.2);
  const snout = blob(scales, 1, 1.6, 1.1, 2.6);
  snout.position.set(0, 0.2, 4.2);
  head.add(skull, snout);
  for (const sd of [-1, 1]) {
    const brow = blob(dark, 1, 0.9, 0.5, 1.4, 0);
    brow.position.set(sd * 1.3, 1.9, 2.4);
    const eye = blob(eyeMat, 0.5, 1.2, 0.8, 1.0, 1);
    eye.position.set(sd * 1.55, 1.35, 2.6);
    eyes.push(eye);
    const hornA = cone(horn, 0.7, 5.5, 5);
    hornA.position.set(sd * 1.4, 2.6, -1.0);
    hornA.rotation.set(-1.9, 0, sd * 0.35);
    const hornB = cone(horn, 0.4, 2.6, 4);
    hornB.position.set(sd * 2.1, 0.9, -0.8);
    hornB.rotation.set(-1.6, 0, sd * 0.9);
    const nose = cone(horn, 0.3, 1.2, 4);
    nose.position.set(sd * 0.5, 1.2, 5.6);
    nose.rotation.x = -0.4;
    head.add(brow, eye, hornA, hornB, nose);
  }
  const glowMouth = blob(mouthMat, 1, 1.1, 0.4, 2.2, 0);
  glowMouth.position.set(0, -0.4, 3.6);
  head.add(glowMouth);
  const jaw = new THREE.Group();
  jaw.position.set(0, -0.4, 0.6);
  head.add(jaw);
  const jawBone = blob(dark, 1, 1.5, 0.6, 2.8);
  jawBone.position.set(0, -0.3, 2.8);
  jaw.add(jawBone);
  for (let k = 0; k < 6; k++) {
    for (const sd of [-1, 1]) {
      const tooth = cone(horn, 0.18, 0.7, 3);
      tooth.position.set(sd * (1.0 - k * 0.1), 0.3, 1.8 + k * 0.6);
      jaw.add(tooth);
    }
  }
  const mouthPoint = new THREE.Object3D();
  mouthPoint.position.set(0, -0.3, 6.5);
  head.add(mouthPoint);

  const local = new THREE.Vector3();
  let yaw = 0;
  let pitch = 0;
  return {
    root,
    update(phase, t, time, target) {
      // Head toward the road (yaw), with a little idle sway.
      local.copy(target);
      root.worldToLocal(local);
      const want = Math.max(-1.2, Math.min(1.2, Math.atan2(local.x, local.z - 7.5)));
      const aimed = phase === "idle" ? 0.25 * Math.sin(time * 0.4) : want;
      yaw += (aimed - yaw) * Math.min(1, 0.06 + (phase === "aiming" ? 0.08 : 0.02));
      // Rear up while warning, lunge down at the road while breathing.
      const down = Math.atan2(-(local.y - 18), Math.hypot(local.x, local.z));
      let p = 0.05 * Math.sin(time * 0.7);
      let jawOpen = 0.05 + 0.05 * Math.sin(time * 1.3);
      let glow = 0.2;
      let spread = 0.15 + 0.08 * Math.sin(time * 0.6);
      if (phase === "aiming") p = lerp(0, -0.15, ease(t));
      if (phase === "warning") {
        p = lerp(-0.15, -0.65, ease(Math.min(1, t * 1.6)));
        glow = 0.4 + 2.6 * t + 0.5 * Math.sin(time * 18);
        spread = lerp(0.2, 0.9, ease(Math.min(1, t * 1.5)));
        jawOpen = 0.15;
      }
      if (phase === "breathing") {
        p = lerp(-0.65, down * 0.55, ease(Math.min(1, t * 4)));
        jawOpen = 0.7;
        glow = 3.2 + 0.6 * Math.sin(time * 25);
        spread = 0.9;
      }
      if (phase === "cooldown") {
        p = lerp(down * 0.55, 0, ease(t));
        jawOpen = lerp(0.7, 0.05, ease(t));
        glow = lerp(2.5, 0.2, t);
        spread = lerp(0.9, 0.2, ease(t));
      }
      pitch += (p - pitch) * 0.15;
      neckA.rotation.set(-0.25 + pitch * 0.5, yaw * 0.5, 0);
      neckB.rotation.set(-0.2 + pitch * 0.4, yaw * 0.5, 0);
      head.rotation.set(0.45 + pitch * 0.3, 0, 0);
      jaw.rotation.x = jawOpen;
      throatMat.emissiveIntensity = glow;
      mouthMat.emissiveIntensity = phase === "breathing" ? 2.5 : glow * 0.4;
      // Wings: a slow restless flex at rest, a great beat as it rears up.
      const flap =
        0.06 * Math.sin(time * 1.1) + (phase === "warning" ? 0.25 * Math.sin(time * 6) * t : 0);
      wings[0]!.rotation.set(0, -spread * 0.6, spread * 0.5 + flap);
      wings[1]!.rotation.set(0, spread * 0.6, -spread * 0.5 - flap);
      body.position.y = 0.25 * Math.sin(time * 0.9);
      tail.rotation.y =
        0.18 * Math.sin(time * 0.7) + (phase === "warning" ? 0.15 * Math.sin(time * 4) : 0);
      // It blinks every few seconds (never while breathing fire).
      const b = (time + heading * 3) % 4.3;
      const lid = phase !== "breathing" && b < 0.16 ? 0.1 : 1;
      for (const e of eyes) e.scale.y = 0.8 * lid;
    },
    mouth(out) {
      return mouthPoint.getWorldPosition(out);
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

export interface DragonFireView {
  /** Show the fire for this phase: the stream from `mouth`, and the flames that fill
   * the burn zone (exactly the box that burns). */
  update(phase: DragonPhase, t: number, time: number, mouth: THREE.Vector3): void;
  dispose(): void;
}

/**
 * The dragon's fire as low-poly flame geometry: a roaring cone of fire from its jaws to
 * the road, and a grid of flickering flame tongues standing over the burn zone (a box
 * `length` along the road and `width` across it, centred at x, y, z, the road running
 * along `heading`).
 */
export function createDragonFire(
  parent: THREE.Object3D,
  zone: {
    x: number;
    y: number;
    z: number;
    heading: number;
    length: number;
    width: number;
    height: number;
  },
): DragonFireView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const glow = (color: string, opacity: number) => {
    const m = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    mats.push(m);
    return m;
  };
  const outer = glow("#ff5a14", 0.75);
  const inner = glow("#ffd860", 0.85);
  const group = new THREE.Group();
  group.name = "dragon fire";
  group.visible = false;
  parent.add(group);
  // The stream: two nested cones, base at the road, tip at the mouth.
  const coneGeo = new THREE.ConeGeometry(1, 1, 7, 1, true);
  coneGeo.translate(0, -0.5, 0); // tip at the origin, opening along -y
  geos.push(coneGeo);
  const stream = new THREE.Group();
  stream.add(new THREE.Mesh(coneGeo, outer));
  const core = new THREE.Mesh(coneGeo, inner);
  core.scale.set(0.5, 1, 0.5);
  stream.add(core);
  group.add(stream);
  // The flames over the zone.
  const tongue = new THREE.ConeGeometry(1, 1, 5);
  tongue.translate(0, 0.5, 0);
  geos.push(tongue);
  const flames: { mesh: THREE.Mesh; phase: number; size: number }[] = [];
  const zoneGroup = new THREE.Group();
  zoneGroup.position.set(zone.x, zone.y, zone.z);
  zoneGroup.rotation.y = zone.heading;
  group.add(zoneGroup);
  const nx = Math.max(2, Math.round(zone.width / 3.5));
  const nz = Math.max(2, Math.round(zone.length / 3.5));
  for (let i = 0; i < nx; i++)
    for (let j = 0; j < nz; j++) {
      const m = new THREE.Mesh(tongue, (i + j) % 3 === 0 ? inner : outer);
      m.position.set(((i + 0.5) / nx - 0.5) * zone.width, 0, ((j + 0.5) / nz - 0.5) * zone.length);
      zoneGroup.add(m);
      flames.push({
        mesh: m,
        phase: (i * 7 + j * 13) % 10,
        size: 1.4 + ((i * 5 + j * 3) % 4) * 0.25,
      });
    }
  const base = new THREE.Vector3(zone.x, zone.y + 1, zone.z);
  const up = new THREE.Vector3(0, 1, 0);
  const dir = new THREE.Vector3();
  return {
    update(phase, t, time, mouth) {
      const on = phase === "breathing" || (phase === "cooldown" && t < 0.35);
      group.visible = on;
      if (!on) return;
      const grow = phase === "breathing" ? Math.min(1, t * 6) : 1 - t / 0.35;
      // The stream from the jaws to the middle of the zone.
      dir.copy(base).sub(mouth);
      const len = dir.length();
      stream.position.copy(mouth);
      stream.quaternion.setFromUnitVectors(up, dir.normalize().negate());
      const w = 3.2 * grow * (1 + 0.12 * Math.sin(time * 31));
      stream.scale.set(w, len * Math.min(1, grow * 1.5), w);
      for (const f of flames) {
        const flick = 0.75 + 0.25 * Math.sin(time * 19 + f.phase * 2.1);
        const h = zone.height * grow * flick;
        f.mesh.scale.set(f.size * grow, h, f.size * grow);
      }
    },
    dispose() {
      group.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}
