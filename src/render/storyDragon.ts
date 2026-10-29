/**
 * The story dragons of Adventure's cutscenes: Cinderjaw, Rimefang, Scorchwind, Tidewyrm,
 * King Pyrrhax and Lumen (a hatchling, and grown). Each its own design
 * (storyDragons/designs): its own silhouette, head, wings, tail, hide and manner, built
 * by one engine here.
 *
 * The body is one smooth skin from the tail's tip to the back of the skull, lofted round
 * a spine and re-bent every frame (like Riverbend Palms' long-neck): the torso pitches
 * about the hips (rearing, bowing), the neck and the tail bend as chains, the head turns
 * to whatever it's looking at. Legs are skins of their own, placed by two-bone IK (feet
 * planted, raised, tucked in flight, splayed when it's knocked down). Wings fold, spread
 * and beat. The face: eyes that track, blink and narrow, brows, a jaw that talks, roars
 * and breathes (fire, frost, sand, water or light, storyDragons/breath.ts).
 *
 * Poses (adventure/staged.ts StoryPose) blend into each other over about 0.4 s.
 */
import * as THREE from "three";
import type { StoryPose } from "../adventure/staged";
import type { DragonLook } from "./dragon";
import { Breath } from "./storyDragons/breath";
import { poseEyes } from "./storyDragons/face";
import { hideMaps, partBump } from "./storyDragons/hide";
import { LiveLoft, newFrame } from "./storyDragons/liveLoft";
import { Parts, clawGeo, mix } from "./storyDragons/parts";
import { DESIGNS } from "./storyDragons/designs";
import { Wing } from "./storyDragons/wing";
import type { DesignId, DragonDesign, HeadKit, LegDesign } from "./storyDragons/types";

export type { DesignId } from "./storyDragons/types";

/** Which design plays a staged dragon of each look (adventure/staged.ts). */
export function designOf(look: DragonLook | undefined): DesignId {
  switch (look) {
    case "frost":
      return "rimefang";
    case "sand":
      return "scorchwind";
    case "sea":
      return "tidewyrm";
    case "king":
      return "king";
    case "lumen":
      return "lumen";
    case "lumen_grown":
      return "lumen_grown";
    default:
      return "cinderjaw";
  }
}

export { DRAGON_SIZE } from "./storyDragons/headAt";

export interface StoryDragonView {
  readonly root: THREE.Group;
  readonly design: DesignId;
  /**
   * Pose and animate it: `t` seconds into the line, `time` the clock, looking at `look`
   * (world), `talk` while it has the line.
   */
  update(pose: StoryPose, t: number, time: number, look: THREE.Vector3, talk: boolean): void;
  /** The mouth's world position (where its breath comes from). */
  mouth(out: THREE.Vector3): THREE.Vector3;
  /** The head's world position (for cameras). */
  head(out: THREE.Vector3): THREE.Vector3;
  /** The head's world centre and the way it faces (unit). */
  headFrame(centre: THREE.Vector3, facing: THREE.Vector3): void;
  /** The ground's world height under it (for breath, the tail, a flyer's shadow). */
  ground: number | undefined;
  /** Stride length (1 normal): bigger, slower steps for the same ground covered. */
  pace: number;
  /** Its own breath, smoke and glow (off when something else draws the fire). */
  effects: boolean;
  dispose(): void;
}

/** What a pose asks of the body (all blended). */
interface PoseState {
  pitch: number;
  lift: number;
  roll: number;
  neck: number;
  head: number;
  jaw: number;
  spread: number;
  flap: number;
  flapHz: number;
  wingLift: number;
  wingSweep: number;
  droop: number;
  tuck: number;
  reach: number;
  fore: number;
  claw: number;
  splay: number;
  sink: number;
  tail: number;
  swish: number;
  eyes: number;
  wide: number;
  squint: number;
  brow: number;
  breath: number;
  look: number;
  hover: number;
  walk: number;
  turn: number;
  crouch: number;
  shake: number;
  /** The head lolling on its side (knocked out). */
  loll: number;
}

const BASE: PoseState = {
  pitch: 0,
  lift: 0,
  roll: 0,
  neck: 0,
  head: 0,
  jaw: 0.02,
  spread: 0,
  flap: 0,
  flapHz: 0.8,
  wingLift: 0,
  wingSweep: 0,
  droop: 0,
  tuck: 0,
  reach: 0,
  fore: 0,
  claw: 0,
  splay: 0,
  sink: 0,
  tail: 0,
  swish: 1,
  eyes: 1,
  wide: 0,
  squint: 0,
  brow: 0,
  breath: 0,
  look: 1,
  hover: 0,
  walk: 0,
  turn: 0,
  crouch: 0,
  shake: 0,
  loll: 0,
};

function target(pose: StoryPose, d: DragonDesign, pt: number): PoseState {
  const m = d.manner;
  const s: PoseState = { ...BASE, spread: d.wings.rest, brow: m.brow };
  switch (pose) {
    case "rear":
      Object.assign(s, {
        pitch: 0.55,
        lift: 1.2,
        neck: 0.3,
        head: -0.1,
        jaw: 0.4,
        spread: 1,
        flap: 0.12,
        flapHz: 0.55,
        wingLift: 0.35,
        fore: 1,
        wide: 0.4,
        brow: -1,
        look: 0.85,
        tail: -0.1,
        swish: 1.6,
      });
      break;
    case "breathe": {
      // A breath drawn in (head back, chest swelling), then the blast.
      const inhale = pt < 0.7;
      Object.assign(s, {
        pitch: inhale ? 0.22 : 0.06,
        lift: inhale ? 0.6 : 0,
        neck: inhale ? 0.35 : -0.15,
        head: inhale ? 0.25 : 0,
        reach: inhale ? 0 : 1,
        jaw: inhale ? 0.25 : 1,
        spread: 0.7,
        wingLift: 0.25,
        flap: 0.05,
        brow: -0.9,
        squint: 0.35,
        look: inhale ? 0.3 : 1,
        breath: inhale ? 0 : 1,
      });
      break;
    }
    case "fly":
      Object.assign(s, {
        pitch: 0.06,
        tuck: 1,
        spread: 1,
        flap: 1,
        flapHz: 0.85,
        hover: 1,
        tail: 0.12,
        swish: 0.6,
        look: 0.9,
      });
      break;
    case "land":
      Object.assign(s, {
        pitch: 0.42,
        tuck: -0.6,
        spread: 1,
        flap: 0.5,
        flapHz: 1.2,
        wingLift: 0.45,
        wingSweep: 0.25,
        tail: -0.05,
        look: 0.7,
        wide: 0.2,
      });
      break;
    case "roar":
      Object.assign(s, {
        pitch: 0.3,
        lift: 0.6,
        neck: 0.55,
        head: 0.55,
        jaw: 1,
        spread: 0.95,
        wingLift: 0.35,
        flap: 0.06,
        flapHz: 1.5,
        look: 0.12,
        eyes: 0.75,
        squint: 0.6,
        brow: -1,
        shake: 1,
        swish: 1.8,
      });
      break;
    case "bow":
      Object.assign(s, {
        pitch: -0.12,
        crouch: 0.8,
        neck: -0.32,
        head: -0.3,
        jaw: 0,
        spread: 0,
        eyes: 0.5,
        look: 0.25,
        brow: 0.4,
        tail: -0.05,
        swish: 0.3,
      });
      break;
    case "stunned":
      Object.assign(s, {
        sink: 1,
        splay: 1,
        neck: -1.0,
        head: -0.25,
        roll: 0.22,
        spread: 0.55,
        wingLift: -0.5,
        droop: 0.55,
        eyes: 0,
        jaw: 0.22,
        look: 0,
        swish: 0.05,
        tail: -0.3,
        brow: 0.5,
        loll: 1,
      });
      break;
    case "claw":
      Object.assign(s, { pitch: 0.06, claw: 1, neck: -0.2, look: 1 });
      break;
    case "walk":
      Object.assign(s, { walk: 1, spread: d.wings.rest * 0.6, look: 0.8 });
      break;
    case "turn":
      Object.assign(s, { turn: 2.7, walk: 0.7, look: 0.15, spread: d.wings.rest * 0.6 });
      break;
    default:
      break;
  }
  return s;
}

/** The spine's 0..1 position of a control point. */
const uOf = (d: DragonDesign, i: number) => i / (d.spine.length - 1);

export function createStoryDragon(
  parent: THREE.Object3D,
  who: DesignId,
  scale = 1,
): StoryDragonView {
  const d = DESIGNS[who];
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const keep = <M extends THREE.Material>(m: M) => (mats.push(m), m);

  const root = new THREE.Group();
  root.name = `story dragon ${who}`;
  root.scale.setScalar(scale);
  parent.add(root);
  const body = new THREE.Group();
  root.add(body);

  // ------------------------------------------------------------------ materials
  const partMat = keep(
    new THREE.MeshLambertMaterial({
      vertexColors: true,
      bumpMap: partBump(),
      bumpScale: d.bump * 0.6,
    }),
  );
  const eyeMat = keep(new THREE.MeshLambertMaterial({ vertexColors: true }));
  const irisMat = keep(
    new THREE.MeshLambertMaterial({
      vertexColors: true,
      emissive: new THREE.Color("#ffffff"),
      emissiveIntensity: 0.25,
    }),
  );
  const glassMat = keep(
    new THREE.MeshLambertMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.82,
      emissive: new THREE.Color("#9adcff"),
      emissiveIntensity: 0.35,
    }),
  );
  const heatMat = keep(
    new THREE.MeshLambertMaterial({
      color: "#5a1410",
      emissive: new THREE.Color(d.breath === "light" ? "#ffd060" : "#ff6a14"),
      emissiveIntensity: 0,
    }),
  );
  const finMat = keep(
    new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }),
  );
  const kit: HeadKit = {
    skin: partMat,
    eye: eyeMat,
    iris: irisMat,
    glass: glassMat,
    heat: heatMat,
    fin: finMat,
  };

  // ------------------------------------------------------------------ the skin
  const n = d.spine.length;
  const skin = new LiveLoft({
    shape: d.spine.map(([, , rx, ry, sq, keel]) => ({ rx, ry, sq, keel })),
    // (A little under the design's own count: smooth at the game's resolution, and
    // inside the triangle budget.)
    rings: Math.round(d.rings * 0.78),
    sides: Math.min(d.sides, 20),
    cells: d.cells,
    cellAlong: d.cellAlong,
  });
  geos.push(skin.geometry);
  const rest = d.spine.map(([z, y]) => new THREE.Vector3(0, y, z));
  // The skin runs on past the back of the skull, into the head.
  const ctrl = skin.ctrl;
  const extra = new THREE.Vector3();
  // (The first sweep must be the rest pose: the hide is painted from it.)
  const setRest = () => {
    for (let i = 0; i < n; i++) ctrl[i]!.copy(rest[i]!);
  };
  setRest();
  skin.update();
  const hide = hideMaps(d, skin);
  const bodyMat = keep(
    new THREE.MeshLambertMaterial({
      map: hide.color,
      bumpMap: hide.bump,
      bumpScale: d.bump,
      emissiveMap: hide.glow ?? null,
      emissive: new THREE.Color(hide.glow ? "#ffffff" : "#000000"),
      emissiveIntensity: hide.glow ? 1 : 0,
    }),
  );
  const skinMesh = new THREE.Mesh(skin.geometry, bodyMat);
  skinMesh.frustumCulled = false;
  body.add(skinMesh);

  // ------------------------------------------------------------------ the head
  const hp = d.buildHead(kit);
  // (Its box in its own space, before it's scaled and placed.)
  hp.head.updateMatrixWorld(true);
  const headBox = new THREE.Box3().setFromObject(hp.head);
  hp.head.scale.setScalar(d.headScale ?? 1);
  body.add(hp.head);
  hp.head.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh) geos.push(m.geometry);
  });
  const browBase = hp.brows.map((b) => ({ y: b.position.y, rz: b.rotation.z }));
  const mouthPt = new THREE.Object3D();
  mouthPt.position.set(...hp.mouth);
  hp.head.add(mouthPt);
  const nosePt = new THREE.Object3D();
  nosePt.position.set(...hp.nose);
  hp.head.add(nosePt);
  const swayRest = hp.sway.map((s) => s.obj.rotation.clone());

  // ------------------------------------------------------------------ legs
  interface Leg {
    d: LegDesign;
    side: number;
    fore: boolean;
    skin: LiveLoft;
    foot: THREE.Mesh;
    pts: THREE.Vector3[];
    phase: number;
  }
  const legs: Leg[] = [];
  const footGeo = (L: LegDesign) => {
    const p = new Parts();
    const [c0, c1] = L.color;
    p.add(new THREE.SphereGeometry(1, 10, 7), c1, {
      p: [0, L.toeR * 0.9, L.toeLen * 0.1],
      s: [L.toeR * 1.9, L.toeR * 1.05, L.toeR * 1.7],
      rep: [3, 3],
    });
    const spread = L.toes === 3 ? 0.45 : 0.36;
    for (let k = 0; k < L.toes; k++) {
      const a = (k - (L.toes - 1) / 2) * spread;
      const len = L.toeLen * (1 - Math.abs(a) * 0.35);
      const dx = Math.sin(a);
      const dz = Math.cos(a);
      // A toe: thick at the knuckle, then the claw curling down.
      p.add(new THREE.SphereGeometry(1, 8, 6), mix(c1, c0, 0.2), {
        p: [dx * len * 0.55, L.toeR * 0.6, dz * len * 0.55 + L.toeLen * 0.1],
        r: [0, a, 0],
        s: [L.toeR * 0.6, L.toeR * 0.62, len * 0.55],
        rep: [2, 2],
      });
      const tip = new THREE.Vector3(
        dx * len * 1.08,
        L.toeR * 0.5,
        dz * len * 1.08 + L.toeLen * 0.1,
      );
      p.add(clawGeo(L.toeR * 0.42, L.claw), L.clawColor, {
        p: [tip.x, tip.y, tip.z],
        r: [Math.PI / 2 + 0.55, 0, -a],
      });
    }
    // A dew claw at the back.
    p.add(clawGeo(L.toeR * 0.3, L.claw * 0.6), L.clawColor, {
      p: [0, L.toeR * 0.8, -L.toeR * 1.3],
      r: [-Math.PI / 2 - 0.4, 0, 0],
    });
    const g = p.build();
    geos.push(g);
    return g;
  };
  for (const [key, fore] of [
    ["hind", false],
    ["fore", true],
  ] as const) {
    const L = d.legs[key];
    const fg = footGeo(L);
    for (const side of [1, -1]) {
      const r = L.radii;
      const ls = new LiveLoft({
        shape: [
          { rx: r[0], ry: r[0] * 1.15 },
          { rx: r[1], ry: r[1] * 1.12 },
          { rx: r[2], ry: r[2] },
          { rx: r[3], ry: r[3] },
          { rx: r[4], ry: r[4] * 0.9 },
        ],
        rings: 16,
        sides: 10,
        cells: 8,
        paint: (u) => mix(L.color[0], L.color[1], (u - 0.3) / 0.5),
      });
      geos.push(ls.geometry);
      const mesh = new THREE.Mesh(ls.geometry, partMat);
      mesh.frustumCulled = false;
      body.add(mesh);
      const foot = new THREE.Mesh(fg, partMat);
      body.add(foot);
      legs.push({
        d: L,
        side,
        fore,
        skin: ls,
        foot,
        pts: [0, 1, 2, 3, 4].map(() => new THREE.Vector3()),
        phase: (fore ? 0 : Math.PI) + (side > 0 ? 0 : Math.PI),
      });
    }
  }

  // ------------------------------------------------------------------ wings
  const wd = d.wings;
  const boneGeo = new THREE.CylinderGeometry(0.55, 1, 1, 8, 1).translate(0, 0.5, 0);
  const knGeo = new THREE.SphereGeometry(1, 10, 8);
  const thumbGeo = clawGeo(0.35, 1.6);
  const boneG = new Parts().add(boneGeo, wd.bone, { rep: [2, 4] }).build();
  const knG = new Parts().add(knGeo, wd.bone, { rep: [2, 2] }).build();
  const thG = new Parts().add(thumbGeo, d.horn, {}).build();
  geos.push(boneG, knG, thG);
  const wingMat = keep(
    new THREE.MeshLambertMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      transparent: (wd.opacity ?? 1) < 1,
      opacity: wd.opacity ?? 1,
      depthWrite: (wd.opacity ?? 1) >= 1,
      emissive: new THREE.Color(wd.glow ?? "#000000"),
      emissiveIntensity: wd.glow ? 0.35 : 0,
    }),
  );
  const wings = [1, -1].map(
    (side) => new Wing(wd, side, { bone: partMat, membrane: wingMat }, boneG, knG, thG),
  );
  for (const w of wings) body.add(w.group);

  // ------------------------------------------------------------------ spines, sails, tail tip
  const spikeRows = d.spikes.map((row) => {
    const g = spikeGeo(row.shape, row.color, row.tip ?? row.color);
    geos.push(g);
    const count = row.count * (row.pair ? 2 : 1);
    const mesh = new THREE.InstancedMesh(g, row.glass ? glassMat : partMat, count);
    mesh.frustumCulled = false;
    body.add(mesh);
    return { row, mesh };
  });
  const sails = (d.sails ?? []).map((sd) => {
    const K = 36;
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array((K + 1) * 3 * 3);
    const col = new Float32Array((K + 1) * 3 * 3);
    const idx: number[] = [];
    const c = new THREE.Color();
    for (let k = 0; k <= K; k++) {
      const kk = k / K;
      for (let r = 0; r < 3; r++) {
        c.set(sd.color).lerp(new THREE.Color(sd.edge), r === 2 ? 1 : r === 1 ? 0.25 : 0);
        if (sd.paint) c.copy(sd.paint(c, kk, r / 2));
        col.set([c.r, c.g, c.b], (k * 3 + r) * 3);
      }
      if (k < K)
        for (let r = 0; r < 2; r++) {
          const a = k * 3 + r;
          idx.push(a, a + 3, a + 1, a + 1, a + 3, a + 4);
        }
    }
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    geo.setIndex(idx);
    geos.push(geo);
    const mat = keep(
      new THREE.MeshLambertMaterial({
        vertexColors: true,
        side: THREE.DoubleSide,
        transparent: (sd.opacity ?? 1) < 1,
        opacity: sd.opacity ?? 1,
      }),
    );
    const mesh = new THREE.Mesh(geo, mat);
    mesh.frustumCulled = false;
    body.add(mesh);
    return { sd, geo, pos, K };
  });
  const tailTip = d.tailTip?.(kit);
  if (tailTip) {
    body.add(tailTip);
    tailTip.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) geos.push(m.geometry);
    });
  }

  // A soft round shadow on the ground.
  const shadowGeo = new THREE.CircleGeometry(1, 32);
  geos.push(shadowGeo);
  const shadowMat = keep(
    new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.28,
      depthWrite: false,
    }),
  );
  const shadow = new THREE.Mesh(shadowGeo, shadowMat);
  shadow.name = "story dragon shadow";
  shadow.rotation.x = -Math.PI / 2;
  const hipZ = d.spine[d.hip]![0];
  const shZ = d.spine[d.shoulder]![0];
  const bodyHalf = Math.max(
    Math.abs(d.legs.hind.foot[0]),
    Math.abs(d.legs.fore.foot[0]),
    d.spine[d.hip]![2],
  );
  shadow.scale.set(bodyHalf * 1.5, (shZ - hipZ) * 0.5 + bodyHalf * 1.6, 1);
  shadow.position.z = (shZ + hipZ) / 2;
  shadow.renderOrder = 1;
  root.add(shadow);

  // ------------------------------------------------------------------ the breath
  const breath = new Breath(parent, d.breath);

  // ------------------------------------------------------------------ animation state
  const cur: PoseState = { ...target("idle", d, 0) };
  let lastPose: StoryPose = "idle";
  let poseStart = 0;
  let last = -1;
  let flapPhase = 0;
  let walkPhase = 0;
  let lookYaw = 0;
  let lookPitch = 0;
  let blinkAt = 1.5;
  let talkJaw = 0;
  const prevWorld = new THREE.Vector3();
  let hasPrev = false;

  // Scratch.
  const qT = new THREE.Quaternion();
  const qA = new THREE.Quaternion();
  const qB = new THREE.Quaternion();
  const qHead = new THREE.Quaternion();
  const X = new THREE.Vector3(1, 0, 0);
  const Y = new THREE.Vector3(0, 1, 0);
  const Z = new THREE.Vector3(0, 0, 1);
  const pivot = rest[d.hip]!.clone();
  const tv = new THREE.Vector3();
  const tw = new THREE.Vector3();
  const lookLocal = new THREE.Vector3();
  const fr = newFrame();
  const tSide = new THREE.Vector3();
  const tUp = new THREE.Vector3();
  const tFwd = new THREE.Vector3();
  const lift = new THREE.Vector3();
  const neckPts = Array.from({ length: d.neck + 1 }, () => new THREE.Vector3());
  const tailPts = Array.from({ length: d.hip + 1 }, () => new THREE.Vector3());
  const m4 = new THREE.Matrix4();
  let gLocal = 0;
  // Probes round the head (its box, a little inside): to keep it off the ground.
  const probes: THREE.Vector3[] = [];
  {
    const c = headBox.getCenter(new THREE.Vector3());
    const h = headBox.getSize(new THREE.Vector3()).multiplyScalar(0.36);
    for (const x of [-1, 1])
      for (const y of [-1, 1])
        for (const z of [-1, 1])
          probes.push(new THREE.Vector3(c.x + x * h.x, c.y + y * h.y, c.z + z * h.z));
  }
  /** Torso rings (hips to the neck's base) for draping the wings over the body. */
  const ringA = Math.max(0, Math.round(skin.ringAt(uOf(d, Math.max(0, d.hip - 2)))));
  const ringB = Math.round(skin.ringAt(uOf(d, Math.min(n - 1, d.shoulder + 2))));
  const cv = new THREE.Vector3();
  const collideWing = (v: THREE.Vector3) => {
    let best = ringA;
    let bd = Infinity;
    for (let i = ringA; i <= ringB; i++) {
      const q = v.distanceToSquared(skin.P[i]!);
      if (q < bd) {
        bd = q;
        best = i;
      }
    }
    cv.subVectors(v, skin.P[best]!);
    const x = cv.dot(skin.S[best]!);
    const y = cv.dot(skin.U[best]!);
    const rx = skin.rx[best]! * 1.05 + 0.25;
    const ry = skin.ry[best]! * 1.05 + 0.25;
    const e = Math.hypot(x / rx, y / ry);
    if (e < 1 && e > 1e-4) {
      const k = 1 / e - 1;
      v.addScaledVector(skin.S[best]!, x * k).addScaledVector(skin.U[best]!, y * k);
    }
    if (v.y < gLocal + 0.1) v.y = gLocal + 0.1;
  };

  /** The torso's transform of a rest point. */
  const torso = (p: THREE.Vector3, out: THREE.Vector3) =>
    out.copy(p).sub(pivot).applyQuaternion(qT).add(pivot).add(lift);

  /** Run the neck as a chain: yaw and pitch per joint; returns the head's orientation. */
  const runNeck = (raise: number, yaw: number, pitch: number, out: THREE.Vector3[]) => {
    const m = d.neck;
    torso(rest[d.shoulder]!, out[0]!);
    qA.copy(qT);
    for (let j = 1; j <= m; j++) {
      qB.setFromEuler(new THREE.Euler(-raise / m + (pitch * 0.45) / m, (yaw * 0.55) / m, 0, "YXZ"));
      qA.multiply(qB);
      tv.subVectors(rest[d.shoulder + j]!, rest[d.shoulder + j - 1]!).applyQuaternion(qA);
      out[j]!.copy(out[j - 1]!).add(tv);
      const floor = gLocal + d.spine[d.shoulder + j]![3] * 0.9;
      if (out[j]!.y < floor) out[j]!.y = floor;
    }
    qHead
      .copy(qA)
      .multiply(
        qB.setFromEuler(
          new THREE.Euler(d.headTilt - cur.head + pitch * 0.55, yaw * 0.45, 0, "YXZ"),
        ),
      );
    return qHead;
  };

  const update = (pose: StoryPose, t: number, time: number, look: THREE.Vector3, talk: boolean) => {
    const dt = last < 0 ? 0 : Math.min(0.1, Math.max(0, time - last));
    last = time;
    if (pose !== lastPose) {
      lastPose = pose;
      poseStart = time;
    }
    const pt = Math.max(time - poseStart, pose === lastPose ? 0 : t);
    const m = d.manner;
    // Blend toward the pose (about 0.4 s to settle).
    const want = target(pose, d, pt);
    // High in the air whatever it's doing: wings beating, legs tucked.
    const air = d_ground();
    if (air !== undefined && air < -4 && pose !== "land" && pose !== "stunned") {
      want.tuck = Math.max(want.tuck, 1);
      want.flap = Math.max(want.flap, 0.8);
      want.spread = 1;
      want.hover = 1;
      want.fore = 0;
    }
    const k = 1 - Math.exp(-dt * 7.5 * m.speed);
    for (const key of Object.keys(cur) as (keyof PoseState)[])
      cur[key] += (want[key] - cur[key]) * (key === "breath" ? Math.min(1, k * 2) : k);
    if (dt === 0) Object.assign(cur, want);

    root.updateMatrixWorld(true);
    // Where it's moving (to step its feet in time).
    const wp = tv.setFromMatrixPosition(root.matrixWorld);
    const moved = hasPrev ? Math.hypot(wp.x - prevWorld.x, wp.z - prevWorld.z) / scale : 0;
    prevWorld.copy(wp);
    hasPrev = true;
    const stride = Math.abs(d.legs.fore.foot[1] - d.legs.hind.foot[1]) * 0.55;
    walkPhase += (Math.max(moved, cur.walk * dt * stride * 1.1) / (stride * view.pace)) * Math.PI;
    flapPhase += dt * Math.PI * 2 * cur.flapHz;
    const groundLocal = d_ground() ?? 0;
    gLocal = groundLocal;

    // ---- the torso
    const breathe = Math.sin(time * 1.4) * m.breathe;
    const sway = Math.sin(time * 0.37) * m.sway;
    const hover = cur.hover * Math.sin(flapPhase - 0.6) * 0.9;
    const step = cur.walk * Math.abs(Math.sin(walkPhase)) * 0.35;
    const shake = cur.shake * Math.sin(time * 31) * 0.012;
    qT.setFromEuler(
      new THREE.Euler(
        -cur.pitch + cur.crouch * 0.16 + breathe * 0.008 + shake,
        sway * 0.03 + Math.sin(walkPhase) * 0.04 * cur.walk,
        cur.roll + sway * 0.02 + Math.sin(walkPhase) * 0.03 * cur.walk,
        "YXZ",
      ),
    );
    const restHipY = rest[d.hip]!.y;
    const sinkTo = Math.max(0, restHipY - d.spine[d.hip]![3] * 0.95);
    lift.set(
      sway * 0.25,
      cur.lift - cur.sink * sinkTo + hover + step - cur.crouch * 1.2 + breathe * 0.05,
      0,
    );
    body.rotation.y = cur.turn;

    // ---- look: the head's neutral direction, then the turn needed to face the target
    lookLocal.copy(look);
    body.worldToLocal(lookLocal);
    runNeck(cur.neck, 0, 0, neckPts);
    const hx = neckPts[d.neck]!;
    tv.copy(Z).applyQuaternion(qHead);
    tw.subVectors(lookLocal, hx);
    let wantYaw = Math.atan2(tw.x, tw.z) - Math.atan2(tv.x, tv.z);
    wantYaw = Math.atan2(Math.sin(wantYaw), Math.cos(wantYaw));
    const wantPitch =
      -Math.atan2(tw.y, Math.hypot(tw.x, tw.z)) + Math.atan2(tv.y, Math.hypot(tv.x, tv.z));
    const lw = cur.look;
    const yawT = Math.max(-1.25, Math.min(1.25, wantYaw)) * lw;
    // (Not too far down: the head dips, the eyes do the rest, and the face stays seen.)
    const pitchT = Math.max(-0.7, Math.min(0.4, wantPitch)) * lw;
    const kl = 1 - Math.exp(-dt * 4.5);
    lookYaw += (yawT - lookYaw) * (dt === 0 ? 1 : kl);
    lookPitch += (pitchT - lookPitch) * (dt === 0 ? 1 : kl);
    // Personality: a cocked head, little idle glances, a nod while talking.
    const talking = talk ? 1 : 0;
    const nod =
      talking * m.nod * (Math.sin(time * 5.3) * 0.04 + Math.sin(time * 2.1) * 0.03) +
      Math.sin(time * 0.53) * 0.03 * cur.look;
    const reachNeck = cur.reach * 0.2;
    runNeck(
      cur.neck - reachNeck,
      lookYaw + Math.sin(time * 0.31) * 0.05 * cur.look,
      lookPitch + nod + reachNeck * 0.6,
      neckPts,
    );
    // Cock the head.
    qHead.multiply(
      qB.setFromAxisAngle(
        Z,
        m.tilt * (0.6 + 0.4 * Math.sin(time * 0.4)) * cur.look + cur.roll * 0.8,
      ),
    );
    if (cur.shake > 0.01)
      qHead.multiply(qB.setFromAxisAngle(Y, Math.sin(time * 23) * 0.05 * cur.shake));
    if (cur.loll > 0.001) qHead.multiply(qB.setFromAxisAngle(Z, cur.loll * 1.2));

    // ---- the tail: a chain back from the hips, swishing
    tailPts[0]!.copy(torso(rest[d.hip]!, tw));
    qA.copy(qT).slerp(qB.identity(), 0.45);
    const nt = d.hip;
    for (let j = 1; j <= nt; j++) {
      const kk = j / nt;
      const swish =
        m.tail * cur.swish * (0.05 + 0.08 * kk) * Math.sin(time * 0.95 - j * 0.6) +
        m.undulate * 0.12 * Math.sin(time * 1.3 - j * 0.7) +
        d.tailDrape * 0.06 * kk +
        cur.walk * 0.05 * Math.sin(walkPhase + j * 0.4);
      qA.multiply(
        qB.setFromEuler(new THREE.Euler(-cur.tail * 0.12 + cur.sink * 0.02, swish, 0, "YXZ")),
      );
      tv.subVectors(rest[d.hip - j]!, rest[d.hip - j + 1]!).applyQuaternion(qA);
      const p = tailPts[j]!.copy(tailPts[j - 1]!).add(tv);
      const r = d.spine[d.hip - j]![3];
      const floor = groundLocal + r * 0.9 + 0.05;
      if (p.y < floor) p.y = floor;
    }
    // ---- the skin's control points: tail (tip first), torso, neck, into the head
    for (let i = 0; i < nt; i++) ctrl[i]!.copy(tailPts[nt - i]!);
    for (let i = d.hip; i <= d.shoulder; i++) {
      torso(rest[i]!, ctrl[i]!);
      // A serpent's body weaves.
      if (m.undulate) ctrl[i]!.x += Math.sin(time * 1.3 - (d.hip - i) * 0.7) * m.undulate * 0.6;
    }
    for (let j = 1; j <= d.neck; j++) ctrl[d.shoulder + j]!.copy(neckPts[j]!);
    extra.copy(Z).applyQuaternion(qHead).multiplyScalar(d.neckInto);
    // (The last point sits inside the skull: the neck flows into the head.)
    ctrl[n - 1]!.add(extra);
    const swellTo = (i: number, u: number) => {
      // Breathing in: the chest swells; a fire-breather's throat fills.
      const chest = Math.exp(-(((u - uOf(d, d.shoulder - 1)) / 0.1) ** 2));
      const inhale = lastPose === "breathe" && pt < 0.8 ? Math.min(1, pt / 0.5) : 0;
      void i;
      return 1 + chest * (0.015 * (1 + breathe) + 0.06 * inhale);
    };
    // (If the head was lifted off the ground, the neck's end goes with it.)
    {
      const hs = d.headScale ?? 1;
      let low = Infinity;
      for (const pr of probes) {
        tv.copy(pr).multiplyScalar(hs).applyQuaternion(qHead).add(neckPts[d.neck]!);
        low = Math.min(low, tv.y);
      }
      const under = groundLocal + 0.15 - low;
      if (under > 0) {
        neckPts[d.neck]!.y += under;
        ctrl[n - 1]!.y += under;
        ctrl[n - 2]!.y += under * 0.5;
      }
    }
    skin.update(swellTo);
    // The head rides the neck's end (lolling on its side when knocked out), kept off
    // the ground.
    hp.head.position.copy(neckPts[d.neck]!);
    hp.head.quaternion.copy(qHead);

    // ---- legs
    for (const L of legs) {
      const ld = L.d;
      const sd = L.side;
      const hipRest = tv.set(ld.hip[0] * sd, ld.hip[1], ld.hip[2]);
      const H = torso(hipRest, L.pts[1]!);
      // Where the foot goes: planted (stepping when walking), raised, tucked, splayed.
      const ph = walkPhase + L.phase;
      const strideZ = cur.walk * Math.sin(ph) * stride * 0.45;
      const stepUp = cur.walk * Math.max(0, Math.cos(ph)) * stride * 0.25;
      const F = L.pts[4]!;
      F.set(ld.foot[0] * sd * (1 + cur.splay * 1.4), groundLocal + stepUp, ld.foot[1] + strideZ);
      if (cur.splay > 0) F.z += (L.fore ? 1 : -1) * cur.splay * ld.upper * 0.6;
      if (L.fore && cur.crouch > 0) F.z += cur.crouch * ld.upper * 0.35;
      const reachLen = ld.upper + ld.lower;
      // Forelegs raised as it rears: claws up before its chest.
      if (L.fore && cur.fore > 0.001) {
        const raised = tw
          .set(ld.hip[0] * sd * 1.05, ld.hip[1] - reachLen * 0.55, ld.hip[2] + reachLen * 0.55)
          .sub(pivot)
          .applyQuaternion(qT)
          .add(pivot)
          .add(lift);
        raised.y += Math.sin(time * 2.2 + sd) * 0.25 * cur.fore;
        F.lerp(raised, Math.min(1, cur.fore));
      }
      if (L.fore && sd < 0 && cur.claw > 0.001) {
        tw.set(ld.foot[0] * sd * 0.7, groundLocal + reachLen * 0.28, ld.foot[1] + reachLen * 0.7);
        F.lerp(tw, cur.claw);
      }
      if (Math.abs(cur.tuck) > 0.001) {
        // Tucked (flying): up under the body; reaching (landing): hanging down.
        const tk = cur.tuck;
        tw.set(
          ld.hip[0] * sd * 0.9,
          ld.hip[1] - reachLen * (tk > 0 ? 0.45 : 0.98),
          ld.hip[2] + (L.fore ? 0.25 : -0.55) * reachLen * (tk > 0 ? 1 : 0.2),
        )
          .sub(pivot)
          .applyQuaternion(qT)
          .add(pivot)
          .add(lift);
        F.lerp(tw, Math.min(1, Math.abs(tk)));
      }
      if (F.y < groundLocal) F.y = groundLocal;
      // The ankle above the ball of the foot; the knee by two-bone IK.
      const A = L.pts[3]!.set(ld.meta[0] * sd, ld.meta[1], ld.meta[2]).add(F);
      const K = L.pts[2]!;
      const a = ld.upper;
      const b = ld.lower;
      tw.subVectors(A, H);
      let dist = tw.length();
      if (dist > (a + b) * 0.995) {
        // Out of reach: the ankle stops short (and the foot with it).
        tw.multiplyScalar(((a + b) * 0.995) / dist);
        A.copy(H).add(tw);
        F.copy(A).sub(tv.set(ld.meta[0] * sd, ld.meta[1], ld.meta[2]));
        dist = (a + b) * 0.995;
      }
      dist = Math.max(Math.abs(a - b) + 0.01, dist);
      const dir = tw.normalize();
      const pole = tFwd.set(sd * 0.25, 0.1, ld.knee).applyQuaternion(qT);
      pole.addScaledVector(dir, -pole.dot(dir)).normalize();
      const cosA = (a * a + dist * dist - b * b) / (2 * a * dist);
      const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
      K.copy(H)
        .addScaledVector(dir, a * cosA)
        .addScaledVector(pole, a * sinA);
      // The haunch: inside the body above the hip, so the leg grows out of it.
      tUp.set(0, 1, 0).applyQuaternion(qT);
      tSide.set(sd, 0, 0).applyQuaternion(qT);
      L.pts[0]!.copy(H)
        .addScaledVector(tUp, ld.radii[0] * 0.9)
        .addScaledVector(tSide, -ld.radii[0] * 0.5);
      for (let i = 0; i < 5; i++) L.skin.ctrl[i]!.copy(L.pts[i]!);
      L.skin.update();
      // The foot: flat on the ground, or following the shin when it's off it.
      const off = Math.min(1, Math.max(0, (F.y - groundLocal) / (reachLen * 0.15)));
      tUp
        .set(0, 1, 0)
        .lerp(tw.subVectors(A, F).normalize(), off * 0.85)
        .normalize();
      tFwd.set(0, 0, 1).applyQuaternion(qT);
      if (L.fore && sd < 0) tFwd.lerp(tw.set(0, 0, 1), cur.claw);
      tFwd.addScaledVector(tUp, -tFwd.dot(tUp)).normalize();
      tSide.crossVectors(tUp, tFwd);
      m4.makeBasis(tSide, tUp, tFwd);
      L.foot.quaternion.setFromRotationMatrix(m4);
      L.foot.position.copy(F);
      const spreadToes = 1 + cur.splay * 0.1;
      L.foot.scale.setScalar(spreadToes);
    }

    // ---- wings
    tSide.set(1, 0, 0).applyQuaternion(qT);
    tUp.set(0, 1, 0).applyQuaternion(qT);
    tFwd.set(0, 0, 1).applyQuaternion(qT);
    const fl = cur.flap * Math.sin(flapPhase);
    for (const w of wings) {
      const sd = w.side;
      const R = torso(tv.set(wd.root[0] * sd, wd.root[1], wd.root[2]), new THREE.Vector3());
      const Fk = torso(tv.set(wd.flank[0] * sd, wd.flank[1], wd.flank[2]), new THREE.Vector3());
      const restless = Math.sin(time * 0.8 + sd) * 0.03 * (1 - cur.flap);
      w.update(
        R,
        Fk,
        tSide,
        tUp,
        tFwd,
        {
          spread: cur.spread * (1 - 0.22 * cur.flap * Math.max(0, Math.sin(flapPhase + 0.4))),
          lift: cur.wingLift + fl * 0.75 + restless,
          sweep: cur.wingSweep - fl * 0.12,
          droop: cur.droop + cur.flap * 0.15 * Math.cos(flapPhase),
        },
        collideWing,
      );
    }

    // ---- spines and sails along the skin
    for (const { row, mesh } of spikeRows) {
      let i = 0;
      for (let k = 0; k < row.count; k++) {
        const kk = row.count === 1 ? 0.5 : k / (row.count - 1);
        const u = row.from + (row.to - row.from) * kk;
        const { rx, ry } = skin.frame(u, fr);
        const h =
          kk < 0.5
            ? row.size[0] + (row.size[1] - row.size[0]) * (kk * 2)
            : row.size[1] + (row.size[2] - row.size[1]) * (kk * 2 - 1);
        for (const side of row.pair ? [1, -1] : [0]) {
          const a = side * (row.pair ?? 0);
          // Up the body at angle a from the ridge.
          tUp.copy(fr.up).multiplyScalar(Math.cos(a)).addScaledVector(fr.s, Math.sin(a));
          tv.copy(fr.p)
            .addScaledVector(fr.up, Math.cos(a) * ry * 0.9)
            .addScaledVector(fr.s, Math.sin(a) * rx * 0.9);
          tFwd.copy(fr.t);
          tSide.crossVectors(tUp, tFwd).normalize();
          tFwd.crossVectors(tSide, tUp);
          m4.makeBasis(tSide, tUp, tFwd);
          qA.setFromRotationMatrix(m4).multiply(qB.setFromAxisAngle(X, -row.lean));
          m4.compose(tv, qA, tw.set(h * row.width, h, h * row.width));
          mesh.setMatrixAt(i++, m4);
        }
      }
      mesh.instanceMatrix.needsUpdate = true;
    }
    for (const s of sails) {
      const { sd, pos, K, geo } = s;
      const around = sd.around ?? 0;
      for (let k = 0; k <= K; k++) {
        const kk = k / K;
        const u = sd.from + (sd.to - sd.from) * kk;
        const { rx, ry } = skin.frame(u, fr);
        tUp.copy(fr.up).multiplyScalar(Math.cos(around)).addScaledVector(fr.s, Math.sin(around));
        const scal = 0.82 + 0.18 * Math.abs(Math.cos(Math.PI * sd.rays * kk));
        const h = sd.height(kk) * scal * (1 + 0.04 * Math.sin(time * 2 + kk * 9));
        tv.copy(fr.p).addScaledVector(
          tUp,
          (Math.abs(Math.cos(around)) * ry + Math.abs(Math.sin(around)) * rx) * 0.8,
        );
        // Lean back a little.
        tw.copy(tUp).addScaledVector(fr.t, -0.25).normalize();
        for (let r = 0; r < 3; r++) {
          const f = r === 0 ? 0 : r === 1 ? 0.55 : 1;
          const o = (k * 3 + r) * 3;
          pos[o] = tv.x + tw.x * h * f;
          pos[o + 1] = tv.y + tw.y * h * f;
          pos[o + 2] = tv.z + tw.z * h * f;
        }
      }
      geo.attributes.position!.needsUpdate = true;
      geo.computeVertexNormals();
    }
    if (tailTip) {
      skin.frame(0, fr);
      tFwd.copy(fr.t).negate();
      tUp.copy(fr.up);
      tSide.crossVectors(tUp, tFwd).normalize();
      tUp.crossVectors(tFwd, tSide);
      m4.makeBasis(tSide, tUp, tFwd);
      tailTip.quaternion.setFromRotationMatrix(m4);
      tailTip.position.copy(fr.p);
    }

    // ---- the face
    const syll =
      Math.max(0, Math.sin(time * 12.5)) *
      (0.55 + 0.45 * Math.sin(time * 3.7)) *
      (Math.sin(time * 1.25) > -0.75 ? 1 : 0.15);
    talkJaw +=
      ((talking ? m.talk * (0.25 + 0.75 * syll) : 0) - talkJaw) * Math.min(1, dt * 18 || 1);
    hp.jaw.rotation.x = Math.min(1, cur.jaw + talkJaw) * hp.jawOpen;
    // Blinks (and eyes shut when stunned).
    if (time > blinkAt + 0.18)
      blinkAt = time + m.blink * (0.6 + 0.8 * ((Math.sin(time * 91.7) + 1) / 2));
    const blink = time >= blinkAt && time < blinkAt + 0.16 ? 0 : 1;
    const open = cur.eyes * blink;
    poseEyes(
      hp.eyes,
      open,
      cur.squint + talking * m.squint,
      cur.wide,
      cur.look > 0.05 ? look : null,
    );
    const brow = cur.brow + talking * m.talkBrow * (0.6 + 0.4 * Math.sin(time * 2.3));
    hp.brows.forEach((b, i) => {
      const side = i === 0 ? 1 : -1;
      // The showman's one raised brow.
      const q = side > 0 ? m.quirk : -m.quirk * 0.4;
      b.position.y = browBase[i]!.y + (brow + q) * 0.12;
      b.rotation.z = browBase[i]!.rz + side * (brow + q) * 0.18;
    });
    hp.sway.forEach((s, i) => {
      const r = swayRest[i]!;
      s.obj.rotation.x =
        r.x + Math.sin(time * 1.6 + s.phase) * s.amount + cur.hover * 0.2 * s.amount * 3;
      s.obj.rotation.z = r.z + Math.sin(time * 1.1 + s.phase * 1.7) * s.amount * 0.6;
    });
    if (hp.frill) {
      const flare = Math.min(
        1,
        0.35 + talking * 0.65 + (pose === "rear" || pose === "roar" ? 1 : 0),
      );
      hp.frill.scale.setScalar(0.75 + 0.25 * flare + 0.03 * Math.sin(time * 6) * talking);
    }
    // The throat and mouth glow as it draws breath and breathes.
    const inhaling = lastPose === "breathe" && pt < 0.8 ? Math.min(1, pt / 0.6) : 0;
    heatMat.emissiveIntensity = inhaling * 1.6 + cur.breath * (1.6 + 0.4 * Math.sin(time * 25));
    if (d.breath === "fire" || d.breath === "kingfire")
      irisMat.emissiveIntensity = 0.55 + cur.breath * 0.6;

    // ---- the breath
    root.updateMatrixWorld(true);
    const mouthW = mouthPt.getWorldPosition(new THREE.Vector3());
    const dirW = new THREE.Vector3(0, -0.12, 1).normalize().transformDirection(hp.head.matrixWorld);
    const noseW = nosePt.getWorldPosition(new THREE.Vector3());
    const groundW = view.ground ?? root.getWorldPosition(new THREE.Vector3()).y;
    breath.update(
      time,
      view.effects && cur.breath > 0.5 ? cur.breath : 0,
      mouthW,
      dirW,
      scale,
      groundW,
      m.smoke * (pose === "stunned" || !view.effects ? 0 : 1) * (cur.breath > 0.1 ? 0 : 1),
      noseW,
      view.effects ? m.aura : 0,
      tw.copy(neckPts[0]!).applyMatrix4(body.matrixWorld),
    );
    // The shadow stays on the ground under a flyer, fading with height.
    const hUp = Math.max(0, root.position.y - groundW) / scale;
    shadow.position.y = -hUp + 0.06;
    shadowMat.opacity = 0.28 * Math.max(0, 1 - hUp / 60);
  };

  // (The ground in body space.)
  const d_ground = () =>
    view.ground === undefined ? undefined : (view.ground - root.position.y) / scale;

  const view: StoryDragonView = {
    root,
    design: who,
    ground: undefined,
    pace: 1,
    effects: true,
    update,
    mouth(out) {
      return mouthPt.getWorldPosition(out);
    },
    head(out) {
      return hp.head.getWorldPosition(out);
    },
    headFrame(centre, facing) {
      hp.head.updateWorldMatrix(true, false);
      centre.set(0, 0.3, 3.5).applyMatrix4(hp.head.matrixWorld);
      facing.set(0, 0, 1).transformDirection(hp.head.matrixWorld);
    },
    dispose() {
      root.removeFromParent();
      breath.dispose();
      for (const w of wings) w.dispose();
      for (const g of new Set(geos)) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
  // A first pose, so it's never seen unposed.
  update("idle", 0, 0, new THREE.Vector3(0, 10, 100).applyMatrix4(root.matrixWorld), false);
  return view;
}

/** One spine/plate/crystal/ray/nub, built standing up along +y (height 1). */
function spikeGeo(shape: string, color: string, tip: string) {
  const p = new Parts();
  const paint = (q: THREE.Vector3) => mix(color, tip, q.y);
  if (shape === "plate") {
    // A thick blunt plate: wide at the base, rounded.
    const g = new THREE.SphereGeometry(1, 10, 7);
    p.add(g, paint, { p: [0, 0.35, 0], s: [0.18, 0.7, 0.55], rep: [2, 2] });
  } else if (shape === "crystal") {
    // A faceted shard (and a smaller one beside it).
    p.add(new THREE.ConeGeometry(0.28, 1, 5, 1), paint, { p: [0, 0.5, 0] });
    p.add(new THREE.ConeGeometry(0.16, 0.55, 5, 1), paint, {
      p: [0.12, 0.28, -0.15],
      r: [-0.3, 0, -0.5],
    });
  } else if (shape === "ray") {
    p.add(new THREE.CylinderGeometry(0.02, 0.07, 1, 5, 1), paint, { p: [0, 0.5, 0] });
  } else if (shape === "nub") {
    p.add(new THREE.SphereGeometry(1, 10, 8), paint, { p: [0, 0.3, 0], s: [0.45, 0.6, 0.5] });
  } else {
    // A curved spine.
    const g = clawGeo(0.32, 1);
    p.add(g, paint, { r: [0, 0, 0] });
  }
  return p.build();
}
