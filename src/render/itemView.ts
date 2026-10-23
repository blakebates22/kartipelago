/**
 * Drawing for balloons and weapons: balloons to collect, missiles, traps, blasts,
 * shields, bubbles and magnet beams. Purely visual.
 */
import * as THREE from "three";
import type { RacerItems } from "../items/effects";
import type { BalloonColor } from "../items/inventory";
import type { ItemWorld } from "../items/world";

export const BALLOON_COLORS: Record<BalloonColor, string> = {
  red: "#e63946",
  blue: "#2f80ed",
  green: "#2bb24c",
  yellow: "#ffd23f",
  rainbow: "#ffffff",
};

const UP = new THREE.Vector3(0, 1, 0);
const trapUp = new THREE.Vector3();
const trapSpin = new THREE.Quaternion();

let oilTex: THREE.Texture | undefined;
/**
 * A pixel-art oil puddle: a lumpy blob with a couple of splashes beside it, near-black
 * with a purple rim and a band of rainbow sheen, two glints. 24 x 24, nearest-filtered.
 */
function oilTexture(): THREE.Texture {
  if (oilTex) return oilTex;
  const N = 24;
  const c = document.createElement("canvas");
  c.width = c.height = N;
  const g = c.getContext("2d")!;
  const lobes = [
    [12, 12, 7.2],
    [8, 9, 4.6],
    [16, 9.5, 4.4],
    [15, 15.5, 4.8],
    [8.5, 15, 4.2],
    [20.5, 17.5, 1.6],
    [4, 5, 1.4],
    [19.5, 5.5, 1.1],
  ] as const;
  /** Signed "how far inside" the blob (above 0 is inside). */
  const inside = (x: number, y: number) =>
    Math.max(...lobes.map(([cx, cy, r]) => r - Math.hypot(x - cx, y - cy)));
  // A faint oily sheen: muted purple, blue and teal, not a bright rainbow.
  const sheen = ["#33244a", "#2a3a5e", "#2a4a4e", "#3a2a48"];
  for (let y = 0; y < N; y++)
    for (let x = 0; x < N; x++) {
      const d = inside(x + 0.5, y + 0.5);
      if (d <= 0) continue;
      let col = "#121018";
      if (d < 1)
        col = "#2a1838"; // the rim
      else {
        // A wavy band of rainbow across the middle.
        const band = (x - y) * 0.5 + Math.sin(y * 0.9) * 1.2;
        if (band > -1 && band < 3) col = sheen[Math.floor(band + 1)]!;
        else if (d < 2) col = "#1e1828";
      }
      g.fillStyle = col;
      g.fillRect(x, y, 1, 1);
    }
  g.fillStyle = "#e8e4f4";
  g.fillRect(9, 8, 2, 1);
  g.fillRect(9, 9, 1, 1);
  g.fillRect(15, 15, 1, 1);
  oilTex = new THREE.CanvasTexture(c);
  oilTex.colorSpace = THREE.SRGBColorSpace;
  oilTex.magFilter = THREE.NearestFilter;
  oilTex.minFilter = THREE.NearestFilter;
  oilTex.generateMipmaps = false;
  return oilTex;
}

const BLAST_COLORS: Record<string, string> = {
  missile: "#ff7b00",
  mine: "#ff3b1f",
  oil: "#222222",
  bubble: "#8fd3ff",
  blocked: "#ffe066",
  wall: "#ff9f43",
  fizz: "#bbbbbb",
};

/** A pool of meshes that grows on demand; unused ones are hidden. */
function pool(make: () => THREE.Object3D, scene: THREE.Object3D) {
  const items: THREE.Object3D[] = [];
  return {
    get(i: number) {
      while (items.length <= i) {
        const m = make();
        scene.add(m);
        items.push(m);
      }
      const m = items[i]!;
      m.visible = true;
      return m;
    },
    hideFrom(n: number) {
      for (let i = n; i < items.length; i++) items[i]!.visible = false;
    },
  };
}

/**
 * The balloons' painted markings: a carved-stone, cave-painting look (a zigzag band
 * round the middle, rows of dots, little triangles near the top). The texture is a
 * shade of grey that darkens the balloon's own colour, so red stays red.
 */
function markingsTexture() {
  const W = 64;
  const H = 32;
  const data = new Uint8Array(W * H * 4);
  const set = (x: number, y: number, v: number) => {
    const i = ((((y % H) + H) % H) * W + (((x % W) + W) % W)) * 4;
    data[i] = data[i + 1] = data[i + 2] = v;
    data[i + 3] = 255;
  };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) set(x, y, 255);
  const ink = 120;
  // A zigzag band round the middle (v = 0.5 is the equator).
  for (let x = 0; x < W; x++) {
    const z = Math.abs((x % 8) - 4);
    for (let t = 0; t < 2; t++) set(x, 14 + z + t, ink);
    set(x, 12, 170);
    set(x, 21, 170);
  }
  // Dots above and below.
  for (let x = 2; x < W; x += 6) {
    for (const y of [8, 25]) {
      set(x, y, ink);
      set(x + 1, y, ink);
      set(x, y + 1, ink);
      set(x + 1, y + 1, ink);
    }
  }
  // Little triangles near the top, pointing up.
  for (let x = 0; x < W; x += 8)
    for (let r = 0; r < 3; r++) for (let k = -r; k <= r; k++) set(x + 4 + k, 4 - r + 2, 150);
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat);
  tex.wrapS = THREE.RepeatWrapping;
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

/** A twisted leather-and-vine cord: diagonal stripes in two browns and a green. */
function cordTexture() {
  const W = 8;
  const H = 16;
  const data = new Uint8Array(W * H * 4);
  const cols = [
    [122, 84, 48],
    [168, 124, 72],
    [78, 120, 52],
    [168, 124, 72],
  ];
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const c = cols[Math.floor((x + y) / 2) % cols.length]!;
      const i = (y * W + x) * 4;
      data.set([c[0]!, c[1]!, c[2]!, 255], i);
    }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1, 10);
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

/** The string: a wiggly cord hanging from the knot, `len` metres long, top at y = 0. */
function cordGeometry(len: number) {
  const pts: THREE.Vector3[] = [];
  for (let k = 0; k <= 16; k++) {
    const t = k / 16;
    // Squiggles that grow toward the free end, turning round as they go.
    const a = 0.08 + 0.16 * t;
    pts.push(new THREE.Vector3(Math.sin(t * 13) * a, -t * len, Math.cos(t * 9 + 0.5) * a * 0.8));
  }
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, 0.045, 5, false);
}

export function createItemView(scene: THREE.Object3D) {
  const markings = markingsTexture();
  const rainbowMat = new THREE.MeshStandardMaterial({
    color: "#ffffff",
    map: markings,
    emissive: "#ffffff",
    emissiveMap: markings,
    emissiveIntensity: 0.25,
  });
  const balloonMats = Object.fromEntries(
    Object.entries(BALLOON_COLORS).map(([k, c]) => [
      k,
      k === "rainbow"
        ? rainbowMat
        : new THREE.MeshStandardMaterial({
            color: c,
            map: markings,
            emissive: c,
            emissiveMap: markings,
            emissiveIntensity: 0.2,
          }),
    ]),
  ) as Record<BalloonColor, THREE.MeshStandardMaterial>;
  const balloonGeo = new THREE.SphereGeometry(0.9, 16, 12).scale(1, 1.2, 1);
  // The string: a squiggly twisted cord, bound at the knot, with a bone bead at the end.
  const cordMat = new THREE.MeshLambertMaterial({ map: cordTexture() });
  const boneMat = new THREE.MeshLambertMaterial({ color: "#efe3c4", flatShading: true });
  const cordGeo = cordGeometry(1.7);
  const knotGeo = new THREE.ConeGeometry(0.2, 0.32, 6);
  const wrapGeo = new THREE.TorusGeometry(0.11, 0.045, 4, 8).rotateX(Math.PI / 2);
  const boneGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.3, 5).rotateZ(Math.PI / 2);
  const knobGeo = new THREE.SphereGeometry(0.075, 5, 4);
  const balloons = pool(() => {
    const g = new THREE.Group();
    const ball = new THREE.Mesh(balloonGeo, balloonMats.red);
    ball.name = "ball";
    ball.castShadow = true;
    const knot = new THREE.Mesh(knotGeo, cordMat);
    knot.position.y = -1.15;
    knot.rotation.x = Math.PI;
    const wrap = new THREE.Mesh(wrapGeo, cordMat);
    wrap.position.y = -1.26;
    const cord = new THREE.Mesh(cordGeo, cordMat);
    cord.name = "cord";
    cord.position.y = -1.3;
    // A little bone tied on the end.
    const bone = new THREE.Group();
    bone.add(new THREE.Mesh(boneGeo, boneMat));
    for (const s of [-1, 1])
      for (const z of [-0.04, 0.04]) {
        const knob = new THREE.Mesh(knobGeo, boneMat);
        knob.position.set(s * 0.15, 0, z);
        bone.add(knob);
      }
    const end = cordGeo.parameters.path.getPoint(1);
    bone.position.set(end.x, end.y - 0.04, end.z);
    cord.add(bone);
    g.add(ball, knot, wrap, cord);
    return g;
  }, scene);

  const missileMat = new THREE.MeshStandardMaterial({ color: "#d62828", flatShading: true });
  const missileFlame = new THREE.MeshBasicMaterial({ color: "#ffb703" });
  const trailMat = new THREE.MeshBasicMaterial({
    color: "#ffd27a",
    transparent: true,
    opacity: 0.55,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const missiles = pool(() => {
    const g = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.CylinderGeometry(0.3, 0.3, 1.8, 8).rotateX(Math.PI / 2),
      missileMat,
    );
    const nose = new THREE.Mesh(
      new THREE.ConeGeometry(0.3, 0.65, 8).rotateX(Math.PI / 2),
      missileMat,
    );
    nose.position.z = 1.22;
    const flame = new THREE.Mesh(
      new THREE.ConeGeometry(0.28, 0.9, 8).rotateX(-Math.PI / 2),
      missileFlame,
    );
    flame.position.z = -1.3;
    // A bright streak behind, so a fast missile is easy to follow (it's scaled to the
    // missile's speed each frame).
    const trail = new THREE.Mesh(
      new THREE.ConeGeometry(0.26, 1, 8).rotateX(-Math.PI / 2).translate(0, 0, -0.5),
      trailMat,
    );
    trail.name = "trail";
    trail.position.z = -1.5;
    g.add(body, nose, flame, trail);
    return g;
  }, scene);

  // The oil: a chunky pixel-art puddle (24 texels across, unfiltered) with an oily
  // rainbow sheen, so it sits in the world's low-res look.
  const oilMat = new THREE.MeshBasicMaterial({
    map: oilTexture(),
    transparent: true,
    alphaTest: 0.5,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -4,
  });
  const mineMat = new THREE.MeshStandardMaterial({ color: "#2b2b2b", flatShading: true });
  const mineLight = new THREE.MeshBasicMaterial({ color: "#ff2a2a" });
  const bubbleMat = new THREE.MeshStandardMaterial({
    color: "#9fdcff",
    transparent: true,
    opacity: 0.35,
    emissive: "#4fb3ff",
    emissiveIntensity: 0.3,
    depthWrite: false,
  });
  const traps = pool(() => {
    const g = new THREE.Group();
    const oil = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 4.6).rotateX(-Math.PI / 2), oilMat);
    oil.name = "oil";
    oil.position.y = 0.06;
    const mine = new THREE.Group();
    mine.name = "mine";
    mine.add(new THREE.Mesh(new THREE.SphereGeometry(0.6, 10, 8), mineMat));
    const light = new THREE.Mesh(new THREE.SphereGeometry(0.15, 6, 4), mineLight);
    light.name = "light";
    light.position.y = 0.6;
    mine.add(light);
    mine.position.y = 0.5;
    const bubble = new THREE.Mesh(new THREE.SphereGeometry(1.4, 16, 12), bubbleMat);
    bubble.name = "bubble";
    bubble.position.y = 1.4;
    g.add(oil, mine, bubble);
    return g;
  }, scene);

  const blastGeo = new THREE.SphereGeometry(1, 14, 10);
  const blasts = pool(() => {
    const m = new THREE.Mesh(
      blastGeo,
      new THREE.MeshBasicMaterial({ color: "#ff7b00", transparent: true, depthWrite: false }),
    );
    return m;
  }, scene);

  // The shield: a plasma globe. A glass ball round the kart (clear in the middle,
  // glowing violet at its edges), a bright core with a soft halo, and electric tendrils
  // crackling from the core out to the glass, beading where they touch it (more of them
  // at higher levels). Like the toy, the nearest rival draws a tendril toward it.
  const plasmaGlass = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: {
      tint: { value: new THREE.Color("#a070ff") },
      edge: { value: new THREE.Color("#ff9cff") },
    },
    vertexShader: `
      varying vec3 vN;
      varying vec3 vV;
      void main() {
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vN = normalize(normalMatrix * normal);
        vV = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      uniform vec3 tint;
      uniform vec3 edge;
      varying vec3 vN;
      varying vec3 vV;
      void main() {
        float f = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.6);
        gl_FragColor = vec4(mix(tint, edge, f) * (0.06 + f * 0.9), 1.0);
      }`,
  });
  const additive = (color: string, opacity: number) =>
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
  const plasmaCore = additive("#fff0ff", 0.95);
  const plasmaHalo = additive("#d070ff", 0.35);
  const plasmaBead = additive("#ffd8ff", 0.9);
  const boltMat = new THREE.MeshBasicMaterial({
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const BOLTS = 10;
  const SEGS = 7;
  /** Each segment is two crossed quads (so a tendril has width from any angle). */
  const VERTS_PER_SEG = 8;
  const beadGeo = new THREE.SphereGeometry(0.11, 6, 4);
  const shields = pool(() => {
    const g = new THREE.Group();
    const glass = new THREE.Mesh(new THREE.SphereGeometry(2.1, 24, 16), plasmaGlass);
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), plasmaCore);
    core.name = "core";
    const halo = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 8), plasmaHalo);
    halo.name = "halo";
    const geo = new THREE.BufferGeometry();
    const nv = BOLTS * SEGS * VERTS_PER_SEG;
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
    geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
    const idx: number[] = [];
    for (let k = 0; k < BOLTS * SEGS; k++)
      for (const q of [0, 4]) {
        const o = k * VERTS_PER_SEG + q;
        idx.push(o, o + 1, o + 2, o + 1, o + 3, o + 2);
      }
    geo.setIndex(idx);
    const bolts = new THREE.Mesh(geo, boltMat);
    bolts.name = "bolts";
    bolts.frustumCulled = false;
    g.add(glass, halo, core, bolts);
    for (let k = 0; k < BOLTS; k++) {
      const bead = new THREE.Mesh(beadGeo, plasmaBead);
      bead.name = `bead${k}`;
      g.add(bead);
    }
    g.userData = { next: 0 };
    return g;
  }, scene);
  const boltColor = new THREE.Color();
  const toRival = new THREE.Vector3();
  const cA = new THREE.Vector3();
  const cB = new THREE.Vector3();
  const dir = new THREE.Vector3();
  const sideA = new THREE.Vector3();
  const sideB = new THREE.Vector3();
  const WORLD_UP = new THREE.Vector3(0, 1, 0);
  const WORLD_X = new THREE.Vector3(1, 0, 0);

  /** New tendrils: jagged paths from the core to random points on the glass. */
  function crackle(g: THREE.Group, level: number, toward: THREE.Vector3 | null) {
    const n = Math.min(BOLTS, 4 + level * 2);
    const bolts = g.getObjectByName("bolts") as THREE.Mesh;
    const pos = bolts.geometry.getAttribute("position") as THREE.BufferAttribute;
    const col = bolts.geometry.getAttribute("color") as THREE.BufferAttribute;
    const end = new THREE.Vector3();
    for (let k = 0; k < BOLTS; k++) {
      const bead = g.getObjectByName(`bead${k}`)!;
      bead.visible = k < n;
      if (k >= n) {
        for (let q = 0; q < SEGS * VERTS_PER_SEG; q++)
          pos.setXYZ(k * SEGS * VERTS_PER_SEG + q, 0, 0, 0);
        continue;
      }
      // Toward the nearest rival for the first tendril (if one's close), else anywhere
      // (a little more often up and out than down into the kart).
      if (k === 0 && toward) end.copy(toward);
      else end.set(Math.random() * 2 - 1, Math.random() * 1.7 - 0.5, Math.random() * 2 - 1);
      end.normalize().multiplyScalar(2.05);
      bead.position.copy(end);
      boltColor.setHSL(0.76 + Math.random() * 0.14, 1, 0.6 + Math.random() * 0.2);
      cA.set(0, 0, 0);
      for (let q = 0; q < SEGS; q++) {
        const f = (q + 1) / SEGS;
        cB.copy(end).multiplyScalar(f);
        if (q < SEGS - 1) {
          const jag = 0.42 * Math.sin(f * Math.PI);
          cB.x += (Math.random() - 0.5) * jag;
          cB.y += (Math.random() - 0.5) * jag;
          cB.z += (Math.random() - 0.5) * jag;
        }
        // Two quads crossed along the segment; thicker near the core.
        dir.subVectors(cB, cA).normalize();
        sideA.crossVectors(dir, Math.abs(dir.y) > 0.9 ? WORLD_X : WORLD_UP).normalize();
        sideB.crossVectors(dir, sideA).normalize();
        const w0 = 0.07 * (1.3 - (q / SEGS) * 0.7);
        const w1 = 0.07 * (1.3 - f * 0.7);
        const o = (k * SEGS + q) * VERTS_PER_SEG;
        let v = o;
        for (const side of [sideA, sideB]) {
          pos.setXYZ(v++, cA.x + side.x * w0, cA.y + side.y * w0, cA.z + side.z * w0);
          pos.setXYZ(v++, cA.x - side.x * w0, cA.y - side.y * w0, cA.z - side.z * w0);
          pos.setXYZ(v++, cB.x + side.x * w1, cB.y + side.y * w1, cB.z + side.z * w1);
          pos.setXYZ(v++, cB.x - side.x * w1, cB.y - side.y * w1, cB.z - side.z * w1);
        }
        const glow = 1.15 - f * 0.45;
        for (let c = o; c < o + VERTS_PER_SEG; c++)
          col.setXYZ(c, boltColor.r * glow, boltColor.g * glow, boltColor.b * glow);
        cA.copy(cB);
      }
    }
    pos.needsUpdate = true;
    col.needsUpdate = true;
  }

  const held = pool(() => new THREE.Mesh(new THREE.SphereGeometry(2.2, 16, 12), bubbleMat), scene);
  // Grappling arms (the rainbow balloon): segmented mechanical arms of dark steel with
  // brass collars, rising from the back of the grappler's kart, arcing over and clamping
  // three-fingered claws onto the other kart. They shoot out over a quarter of a second,
  // then writhe a little as they reel in.
  const ARM_SEGS = 16;
  const steel = new THREE.MeshStandardMaterial({
    color: "#3a3f4a",
    metalness: 0.7,
    roughness: 0.35,
    flatShading: true,
  });
  const brass = new THREE.MeshStandardMaterial({
    color: "#c8962a",
    metalness: 0.8,
    roughness: 0.3,
    flatShading: true,
  });
  const eyeMat = new THREE.MeshBasicMaterial({ color: "#ff3a2a" });
  const segGeo = new THREE.CylinderGeometry(1, 1, 1, 8).rotateX(Math.PI / 2);
  const collarGeo = new THREE.TorusGeometry(1, 0.28, 5, 10);
  const fingerGeo = new THREE.ConeGeometry(0.07, 0.42, 5).translate(0, 0.21, 0);
  const arms = pool(() => {
    const g = new THREE.Group();
    for (let k = 0; k < ARM_SEGS; k++) {
      const seg = new THREE.Mesh(segGeo, steel);
      seg.name = `seg${k}`;
      const collar = new THREE.Mesh(collarGeo, brass);
      collar.name = `col${k}`;
      g.add(seg, collar);
    }
    // The claw: a brass hub with a red eye, three steel fingers.
    const claw = new THREE.Group();
    claw.name = "claw";
    const hub = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), brass);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.05, 6, 4), eyeMat);
    eye.position.set(0, 0.1, 0.1);
    claw.add(hub, eye);
    for (let f = 0; f < 3; f++) {
      const pivot = new THREE.Group();
      pivot.rotation.z = (f / 3) * Math.PI * 2;
      const finger = new THREE.Mesh(fingerGeo, steel);
      finger.name = "finger";
      finger.position.set(0, 0.1, 0);
      pivot.add(finger);
      claw.add(pivot);
    }
    g.add(claw);
    g.userData = { since: 0, key: "" };
    return g;
  }, scene);
  const armStart = new Map<string, number>();
  const bz = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  const ap = new THREE.Vector3();
  const aq = new THREE.Vector3();
  const tan = new THREE.Vector3();
  const lift = new THREE.Vector3();
  const qArm = new THREE.Quaternion();
  const zAxis = new THREE.Vector3(0, 0, 1);
  const bezier = (t: number, out: THREE.Vector3) => {
    const u = 1 - t;
    return out
      .copy(bz[0]!)
      .multiplyScalar(u * u * u)
      .addScaledVector(bz[1]!, 3 * u * u * t)
      .addScaledVector(bz[2]!, 3 * u * t * t)
      .addScaledVector(bz[3]!, t * t * t);
  };

  /** Pose one arm from `from` (a shoulder) to `to` (where its claw grips). */
  function poseArm(
    g: THREE.Group,
    from: THREE.Vector3,
    to: THREE.Vector3,
    out: THREE.Vector3,
    reach: number,
    seconds: number,
    seed: number,
  ) {
    const span = from.distanceTo(to);
    const h = 1.2 + Math.min(3, span * 0.18);
    bz[0]!.copy(from);
    bz[1]!.copy(from).addScaledVector(out, 0.7).y += h;
    bz[2]!.copy(to).addScaledVector(out, 0.5).y += h * 0.8;
    bz[3]!.copy(to);
    let prev = bezier(0, ap.clone());
    for (let k = 0; k < ARM_SEGS; k++) {
      const t1 = ((k + 1) / ARM_SEGS) * reach;
      bezier(t1, aq);
      // A writhe along the arm, fading out at both ends.
      const w = Math.sin((k / ARM_SEGS) * Math.PI) * 0.18;
      aq.x += Math.sin(seconds * 7 + k * 0.7 + seed) * w;
      aq.y += Math.cos(seconds * 6 + k * 0.9 + seed) * w;
      const seg = g.getObjectByName(`seg${k}`)!;
      const col = g.getObjectByName(`col${k}`)!;
      tan.subVectors(aq, prev);
      const len = tan.length();
      const r = 0.075 - (k / ARM_SEGS) * 0.025;
      seg.position.addVectors(prev, aq).multiplyScalar(0.5);
      qArm.setFromUnitVectors(zAxis, tan.normalize());
      seg.quaternion.copy(qArm);
      seg.scale.set(r, r, Math.max(0.01, len * 0.92));
      col.position.copy(aq);
      col.quaternion.copy(qArm);
      col.scale.setScalar(r * 1.25);
      prev = prev.copy(aq);
    }
    const claw = g.getObjectByName("claw")!;
    claw.position.copy(prev);
    claw.quaternion.copy(qArm);
    // Fingers open as it flies, close to grip once it arrives.
    const grip = reach >= 1 ? 1 : 0;
    claw.children.forEach((c) => {
      const finger = c.getObjectByName("finger");
      if (finger) finger.rotation.x = grip ? 0.25 : -0.7;
    });
  }

  const tmp = new THREE.Vector3();

  return {
    /**
     * Draw this frame. `karts` are the karts' drawn positions (meshes), in racer order;
     * `lift` is how far each one is raised (a kart held in a bubble floats).
     */
    render(
      w: ItemWorld,
      karts: THREE.Vector3[],
      racers: RacerItems[],
      seconds: number,
      /** The karts' roots, for where on them the grappling arms attach. */
      roots?: THREE.Object3D[],
    ) {
      const live = new Set<string>();
      rainbowMat.color.setHSL((seconds * 0.4) % 1, 0.9, 0.6);
      rainbowMat.emissive.copy(rainbowMat.color);

      let n = 0;
      w.balloons.forEach((b, i) => {
        if (!b.active) return;
        const g = balloons.get(n++) as THREE.Group;
        (g.getObjectByName("ball") as THREE.Mesh).material = balloonMats[b.color];
        g.position.set(b.x, b.y + 2.6 + Math.sin(seconds * 2 + i) * 0.2, b.z);
        g.rotation.y = seconds + i;
        // The cord sways a little as the balloon bobs.
        const cord = g.getObjectByName("cord")!;
        cord.rotation.x = Math.sin(seconds * 2.3 + i) * 0.08;
        cord.rotation.z = Math.cos(seconds * 1.9 + i) * 0.08;
        g.scale.setScalar(Math.min(1, 0.2 + b.age * 3));
      });
      balloons.hideFrom(n);

      w.missiles.forEach((m, i) => {
        const g = missiles.get(i);
        g.position.set(m.x, m.y, m.z);
        g.rotation.y = m.heading;
        g.getObjectByName("trail")!.scale.set(1, 1, Math.min(9, m.speed * 0.08));
      });
      missiles.hideFrom(w.missiles.length);

      w.traps.forEach((t, i) => {
        const g = traps.get(i) as THREE.Group;
        g.position.set(t.x, t.y, t.z);
        for (const kind of ["oil", "mine", "bubble"])
          g.getObjectByName(kind)!.visible = t.kind === kind;
        if (t.kind === "oil") {
          // Lie along the ground (banked or sloping road), just above it.
          const oil = g.getObjectByName("oil")!;
          trapUp.set(t.nx ?? 0, t.ny ?? 1, t.nz ?? 0).normalize();
          oil.quaternion.setFromUnitVectors(UP, trapUp);
          // Each puddle turned its own way, so they don't all look stamped.
          oil.quaternion.multiply(trapSpin.setFromAxisAngle(UP, i * 2.39));
          oil.position.copy(trapUp).multiplyScalar(0.06);
        }
        const light = g.getObjectByName("light");
        if (light) light.visible = t.kind === "mine" && Math.floor(seconds * 4) % 2 === 0;
        if (t.kind === "bubble")
          g.getObjectByName("bubble")!.position.y = 1.4 + Math.sin(seconds * 3) * 0.15;
      });
      traps.hideFrom(w.traps.length);

      w.blasts.forEach((b, i) => {
        const m = blasts.get(i) as THREE.Mesh;
        const mat = m.material as THREE.MeshBasicMaterial;
        mat.color.set(BLAST_COLORS[b.kind] ?? "#ffffff");
        const big = b.kind === "missile" || b.kind === "mine" || b.kind === "wall" ? 3.5 : 2;
        const f = Math.min(1, b.age / 0.5);
        m.scale.setScalar(0.5 + f * big);
        mat.opacity = Math.max(0, 0.8 * (1 - b.age / 1.2));
        m.position.set(b.x, b.y + 0.5, b.z);
      });
      blasts.hideFrom(w.blasts.length);

      let s = 0;
      let h = 0;
      let bm = 0;
      racers.forEach((it, i) => {
        const p = karts[i];
        if (!p) return;
        if (it.shieldTime > 0) {
          const g = shields.get(s++) as THREE.Group;
          // Centred on the kart (its origin is on the ground).
          g.position.copy(p).y += 0.9;
          g.scale.setScalar(1 + 0.06 * it.shieldLevel + Math.sin(seconds * 6) * 0.02);
          // In its last second it sputters, so you know it's about to drop.
          const ending = it.shieldTime < 1 && Math.floor(seconds * 12) % 2 === 0;
          g.visible = !ending;
          const u = g.userData as { next: number };
          if (seconds >= u.next) {
            // The nearest rival within reach draws a tendril.
            let best = 7;
            let near: THREE.Vector3 | null = null;
            karts.forEach((q, j) => {
              if (j === i || !q) return;
              const d = q.distanceTo(p);
              if (d < best) {
                best = d;
                near = toRival.copy(q).sub(p);
              }
            });
            crackle(g, it.shieldLevel, near);
            u.next = seconds + 0.045 + Math.random() * 0.04;
          }
          const flick = 1 + Math.sin(seconds * 23) * 0.15 + Math.random() * 0.1;
          g.getObjectByName("core")!.scale.setScalar(flick);
          g.getObjectByName("halo")!.scale.setScalar(0.9 + flick * 0.2);
        }
        if (it.bubbleTime > 0) {
          const m = held.get(h++);
          m.position.copy(p).y += 1.0;
          m.scale.setScalar(1 + Math.sin(seconds * 5) * 0.04);
        }
        // The grappler (a) reaches for the other kart (b): a's own grapple, or a
        // reverse grapple dragging this racer back to its owner.
        const target = it.magnetTime > 0 ? it.magnetTarget : -1;
        const from = it.pullTime > 0 ? it.pullBy : -1;
        for (const [a, b] of [
          [i, target],
          [from, i],
        ] as const) {
          const pa = karts[a];
          const pb = karts[b];
          if (a < 0 || b < 0 || !pa || !pb) continue;
          const key = `${a}>${b}`;
          live.add(key);
          if (!armStart.has(key)) armStart.set(key, seconds);
          const reach = Math.min(1, (seconds - armStart.get(key)!) / 0.25);
          const ra = roots?.[a];
          const rb = roots?.[b];
          for (const side of [1, -1]) {
            const g = arms.get(bm++) as THREE.Group;
            // Shoulders on the back of the grappler, grips on the other kart's sides.
            if (ra) ra.localToWorld(bz[0]!.set(side * 0.42, 0.95, -0.7));
            else bz[0]!.copy(pa).y += 0.95;
            if (rb) rb.localToWorld(tmp.set(side * 0.62, 0.65, 0.1));
            else tmp.copy(pb).y += 0.65;
            lift.set(side, 0, 0);
            if (ra) lift.transformDirection(ra.matrixWorld);
            const shoulder = bz[0]!.clone();
            poseArm(g, shoulder, tmp.clone(), lift.clone(), reach, seconds, side * 1.7 + a);
          }
        }
      });
      shields.hideFrom(s);
      held.hideFrom(h);
      arms.hideFrom(bm);
      for (const k of [...armStart.keys()]) if (!live.has(k)) armStart.delete(k);
    },
  };
}
