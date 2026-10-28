/**
 * Lumen in his robe: a small hooded figure in a long, heavy, too-big robe that pools on
 * the ground and swallows his hands, the hood so deep his face is only shadow and two
 * softly glowing gold eyes. Mysterious, gentle, curious (his head tilts as he listens).
 *
 * He's a dragon hatchling in disguise, and it shows if you look: two humps on his back
 * where his wings are folded under the robe, the gold tip of a tail at the hem behind
 * him, little gold claws at the ends of his sleeves and peeking out under the hem when
 * he walks. (Thrown back, the robe swaps for the dragon: render/dragon.ts.)
 */
import * as THREE from "three";
import { Build, ellipsoid, loft, tube, type V3 } from "../racers/kit/shapes";
import { skinMaterial } from "../racers/kit/paint";
import { buildTail, mesh, mottle, shade, skeleton, type PersonRig } from "./rig";
import { tassel } from "./parts";

const C = {
  robe: "#4d5a80",
  robeDark: "#323b5c",
  robeLight: "#6c79a0",
  trim: "#e2c26a",
  patch: "#7a5a8a",
  rope: "#e8d8b0",
  shadow: "#0e0a08",
  gold: "#e8c060",
  goldDark: "#b8862e",
  eye: "#ffe08a",
};

/** Keep a geometry's triangles that face away from `dir` (cut a hole facing it). */
function cutFacing(geo: THREE.BufferGeometry, dir: V3, cos: number) {
  const g = geo.index ? geo.toNonIndexed() : geo;
  const d = new THREE.Vector3(...dir).normalize();
  const pos = g.getAttribute("position");
  const keep: number[] = [];
  const c = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 3) {
    c.set(0, 0, 0);
    for (let k = 0; k < 3; k++) c.x += pos.getX(i + k) / 3;
    for (let k = 0; k < 3; k++) c.y += pos.getY(i + k) / 3;
    for (let k = 0; k < 3; k++) c.z += pos.getZ(i + k) / 3;
    if (c.normalize().dot(d) < cos) keep.push(i);
  }
  const out = new THREE.BufferGeometry();
  for (const name of Object.keys(g.attributes)) {
    const src = g.getAttribute(name) as THREE.BufferAttribute;
    const n = src.itemSize;
    const arr = new Float32Array(keep.length * 3 * n);
    keep.forEach((i, j) => {
      for (let k = 0; k < 3 * n; k++) arr[j * 3 * n + k] = src.array[i * n + k]!;
    });
    out.setAttribute(name, new THREE.BufferAttribute(arr, n));
  }
  return out;
}

let eyeMat: THREE.MeshBasicMaterial | undefined;
let glowTex: THREE.Texture | undefined;

export function buildLumen(): PersonRig {
  const robe = new THREE.Color(C.robe);
  const robeDark = new THREE.Color(C.robeDark);
  const robeLight = new THREE.Color(C.robeLight);
  // Heavy wool: folds running down it, worn darker toward the hem.
  const wool = (t: number, a: number) => {
    const fold = Math.sin(a * 7 + Math.sin(t * 3) * 0.6);
    const k = robe.clone().lerp(fold > 0.55 ? robeLight : robeDark, Math.abs(fold) * 0.35);
    return k.lerp(robeDark, Math.max(0, t - 0.7) * 0.8 + mottle(t * 4, a, 3) * 0.1);
  };
  const rig = skeleton({
    name: "Lumen (robed)",
    stance: {
      hipY: 0.34,
      stride: 0.22,
      lift: 0.05,
      stoop: 0.05,
      handRest: [0.2, 0.06, 0.2],
      mouth: [0, 0.12, 0.22],
      breath: 0.9,
      sway: 0.8,
      blinkEvery: 3.8,
      glance: 3,
      curious: 1,
      restJaw: 0,
      restLids: 0.08,
      restBrow: 0,
      response: 0.85,
      lookReach: 1.15,
    },
    neckAt: [0, 0.44, 0.04],
    headAt: [0, 0.06, 0.02],
    arms: {
      shoulder: [0.17, 0.38, 0.03],
      upper: 0.17,
      fore: 0.17,
      radius: [0.065, 0.07, 0.085],
      upperColor: C.robe,
      foreColor: (t) => (t > 0.86 ? C.trim : C.robe),
      hand: C.gold,
      handSize: 0.045,
      claws: C.goldDark,
      hint: [0.5, -0.5, -0.6],
    },
    legs: {
      hip: [0.09, -0.02, 0],
      thigh: 0.17,
      shin: 0.15,
      radius: [0.06, 0.05, 0.045],
      thighColor: C.robeDark,
      shinColor: C.gold,
      foot: { len: 0.15, width: 0.1, color: C.gold, claw: C.goldDark },
      ankleH: 0.05,
    },
  });

  // ------------------------------------------------------------ the robe
  const body = new Build();
  // The robe: the top on his body (it bows with him), the skirt from the belt down to
  // the ground, flaring, a little too long (it pools at the hem), standing still.
  body.addColored(
    loft(
      [
        { at: [0, 0.47, 0.03], rx: 0.1, ry: 0.1 },
        { at: [0, 0.43, 0.02], rx: 0.2, ry: 0.15 },
        { at: [0, 0.32, 0.01], rx: 0.23, ry: 0.18 },
        { at: [0, 0.15, 0.0], rx: 0.24, ry: 0.2 },
        { at: [0, 0.04, -0.005], rx: 0.25, ry: 0.215 },
      ],
      { sides: 18, steps: 2, up: [0, 0, 1], capStart: true, capEnd: true, paint: wool },
    ),
  );
  const skirt = new Build();
  skirt.addColored(
    loft(
      [
        { at: [0, 0.17, 0.0], rx: 0.225, ry: 0.19 },
        { at: [0, 0.1, 0.0], rx: 0.245, ry: 0.21 },
        { at: [0, -0.05, -0.01], rx: 0.28, ry: 0.25 },
        { at: [0, -0.22, -0.02], rx: 0.33, ry: 0.3 },
        { at: [0, -0.33, -0.03], rx: 0.38, ry: 0.35, sq: 2.3 },
        { at: [0, -0.355, -0.03], rx: 0.39, ry: 0.36, sq: 2.3 },
      ],
      {
        sides: 18,
        steps: 2,
        up: [0, 0, 1],
        capStart: true,
        capEnd: true,
        paint: (t, a) => wool(0.35 + t * 0.65, a),
      },
    ),
  );
  // The hem's pale trim, frayed, and a mended patch.
  skirt.addColored(
    loft(
      Array.from({ length: 19 }, (_, i) => {
        const a = (i / 18) * Math.PI * 2;
        return {
          at: [
            Math.sin(a) * 0.385,
            -0.33 + Math.sin(a * 5) * 0.006,
            -0.03 + Math.cos(a) * 0.355,
          ] as V3,
          rx: 0.016,
          ry: 0.025,
        };
      }),
      { sides: 6, steps: 2, paint: (t) => (Math.sin(t * 90) > 0.6 ? shade(C.trim, 0.85) : C.trim) },
    ),
  );
  // Gold suns stitched round the hem (he's Lumen: the light).
  for (let k = 0; k < 7; k++) {
    const a = ((k - 3) / 7) * Math.PI * 1.25;
    const p: V3 = [Math.sin(a) * 0.35, -0.25, -0.03 + Math.cos(a) * 0.322];
    const rot: V3 = [0.15, a, 0];
    skirt.add(new THREE.CircleGeometry(0.026, 10), C.trim, { p, r: rot });
    for (let j = 0; j < 8; j++) {
      const b = (j / 8) * Math.PI * 2;
      const off = new THREE.Vector3(Math.cos(b) * 0.04, Math.sin(b) * 0.04, 0.001).applyEuler(
        new THREE.Euler(...rot),
      );
      skirt.add(new THREE.PlaneGeometry(0.008, 0.02), C.trim, {
        p: [p[0] + off.x, p[1] + off.y, p[2] + off.z],
        r: [rot[0], rot[1], b - Math.PI / 2],
      });
    }
  }
  skirt.add(new THREE.BoxGeometry(0.1, 0.09, 0.01), C.patch, {
    p: [0.17, -0.12, 0.215],
    r: [-0.25, 0.6, 0.12],
  });
  // Folded wings under the cloth: two soft humps on his back.
  for (const s of [1, -1])
    body.add(ellipsoid(12, 9), (p) => wool(0.3 + p.y, Math.atan2(p.y, p.x)), {
      p: [s * 0.11, 0.3, -0.13],
      s: [0.15, 0.2, 0.12],
      r: [0.25, s * 0.35, s * 0.25],
    });
  // A rope belt, its ends hanging with tassels.
  body.addColored(
    loft(
      Array.from({ length: 15 }, (_, i) => {
        const a = (i / 14) * Math.PI * 2;
        return {
          at: [Math.sin(a) * 0.245, 0.12, 0.0 + Math.cos(a) * 0.205] as V3,
          rx: 0.016,
          ry: 0.016,
        };
      }),
      { sides: 6, steps: 2, paint: (t) => (Math.sin(t * 120) > 0 ? C.rope : shade(C.rope, 0.8)) },
    ),
  );
  body.addColored(
    tube(
      [
        [0.06, 0.12, 0.2],
        [0.075, 0.02, 0.22],
        [0.07, -0.07, 0.225],
      ],
      0.012,
      C.rope,
      { sides: 5 },
    ),
  );
  tassel(body, [0.07, -0.08, 0.225], 0.07, C.rope);
  // A heavy cowl round his shoulders, under the hood.
  body.addColored(
    loft(
      Array.from({ length: 15 }, (_, i) => {
        const a = (i / 14) * Math.PI * 2;
        return {
          at: [Math.sin(a) * 0.17, 0.44 - Math.cos(a) * 0.02, 0.02 + Math.cos(a) * 0.13] as V3,
          rx: 0.06,
          ry: 0.055,
        };
      }),
      { sides: 8, steps: 2, paint: (t, a) => wool(0.2, a + t * 9) },
    ),
  );
  rig.torso.add(mesh(body));
  const sk = mesh(skirt);
  sk.position.y = rig.stance.hipY;
  rig.body.add(sk);

  // Wide sleeves, too long: they hang over his hands.
  for (const arm of rig.arms)
    arm.fore.add(
      mesh(
        new Build()
          .addColored(
            loft(
              [
                { at: [0, 0, 0.08], rx: 0.075, ry: 0.075 },
                { at: [0, -0.01, 0.17], rx: 0.1, ry: 0.105 },
                { at: [0, -0.02, 0.21], rx: 0.11, ry: 0.115 },
              ],
              { sides: 12, steps: 2, paint: (t, a) => wool(0.4 + t * 0.2, a) },
            ),
          )
          .add(new THREE.TorusGeometry(0.108, 0.014, 5, 14), C.trim, { p: [0, -0.02, 0.21] })
          .add(new THREE.CircleGeometry(0.1, 12), C.shadow, { p: [0, -0.02, 0.2] }),
      ),
    );

  // The tail: under the robe, only its gold tip curling out behind at the hem.
  rig.tail = buildTail(
    rig.hips,
    [0, -0.18, -0.15],
    [
      [0.055, 0.12, 0.05],
      [0.05, 0.25, 0.035],
      [0.035, 0.15, 0.012],
    ],
    [-1.2, 1.3, 0.9],
    (k, t) =>
      k === 0 ? C.robeDark : new THREE.Color(C.gold).lerp(new THREE.Color(C.goldDark), t * 0.4),
  );
  // Its spade tip.
  const tip = rig.tail[2]!;
  rig.tail[1]!.rotation.y = 0.5;
  tip.rotation.y = 0.6;
  tip.add(
    mesh(
      new Build().add(ellipsoid(10, 6), C.gold, {
        p: [0, 0.0, -0.14],
        s: [0.055, 0.016, 0.06],
        r: [0, Math.PI / 4, 0],
      }),
    ),
  );

  // ------------------------------------------------------------ the hood
  const head = rig.head;
  const hood = new Build();
  const hoodC: V3 = [0, 0.15, -0.01];
  const hoodS: V3 = [0.2, 0.22, 0.21];
  // The outside: a deep cowl, open at the front, drooping to a soft point behind.
  hood.addColored(
    cutFacing(
      new Build()
        .add(new THREE.SphereGeometry(1, 26, 18), (p, n) =>
          wool(0.3 - p.y * 0.2, Math.atan2(n.y, n.x)),
        )
        .build(),
      [0, 0.02, 1],
      0.42,
    ),
    { p: hoodC, s: hoodS },
  );
  // The inside (the same shape, a little smaller, turned inward: dark).
  const inner = cutFacing(new THREE.SphereGeometry(1, 26, 18).toNonIndexed(), [0, 0.02, 1], 0.42);
  {
    // (Flip it inside out.)
    const pos = inner.getAttribute("position") as THREE.BufferAttribute;
    const nor = inner.getAttribute("normal") as THREE.BufferAttribute;
    for (let i = 0; i < pos.count; i += 3)
      for (const a of [pos, nor]) {
        for (let k = 0; k < 3; k++) {
          const t = a.getComponent(i + 1, k);
          a.setComponent(i + 1, k, a.getComponent(i + 2, k));
          a.setComponent(i + 2, k, t);
        }
      }
    for (let i = 0; i < nor.count; i++) nor.setXYZ(i, -nor.getX(i), -nor.getY(i), -nor.getZ(i));
  }
  hood.add(inner, C.shadow, { p: hoodC, s: [hoodS[0] * 0.94, hoodS[1] * 0.94, hoodS[2] * 0.94] });
  // The shadowed face deep inside, the faintest snout.
  hood.add(ellipsoid(14, 10), C.shadow, { p: [0, 0.13, 0.02], s: [0.15, 0.16, 0.14] });
  hood.add(ellipsoid(10, 7), "#1c140c", { p: [0, 0.09, 0.12], s: [0.07, 0.055, 0.07] });
  // The hood's rim: thick, pale-edged.
  hood.add(new THREE.TorusGeometry(1, 0.11, 7, 22), (p) => (p.y > 0.7 ? C.trim : C.robeLight), {
    p: [0, hoodC[1] + 0.02 * 0.42 * 0.22, hoodC[2] + 0.21 * 0.42],
    s: [0.2 * 0.9, 0.22 * 0.9, 0.2 * 0.9],
    r: [0.02, 0, 0],
  });
  // The droop of the hood behind.
  hood.addColored(
    loft(
      [
        { at: [0, 0.28, -0.08], rx: 0.11, ry: 0.09 },
        { at: [0, 0.27, -0.2], rx: 0.07, ry: 0.06 },
        { at: [0.02, 0.2, -0.3], rx: 0.045, ry: 0.04 },
        { at: [0.05, 0.08, -0.33], rx: 0.025, ry: 0.025 },
        { at: [0.06, 0.0, -0.31], rx: 0.008, ry: 0.008 },
      ],
      {
        sides: 8,
        steps: 3,
        capEnd: true,
        paint: (t, a) => (t > 0.92 ? C.trim : wool(0.3 + t * 0.2, a)),
      },
    ),
  );
  head.add(mesh(hood));

  // Two soft gold eyes in the dark, glowing (and a faint glow round each).
  eyeMat ??= new THREE.MeshBasicMaterial({ color: C.eye });
  if (!glowTex) {
    const size = 32;
    const data = new Uint8Array(size * size * 4);
    for (let y = 0; y < size; y++)
      for (let x = 0; x < size; x++) {
        const d = Math.hypot(x - size / 2 + 0.5, y - size / 2 + 0.5) / (size / 2);
        const a = Math.max(0, 1 - d) ** 2;
        data.set([255, 214, 120, Math.round(a * 200)], (y * size + x) * 4);
      }
    glowTex = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
    glowTex.needsUpdate = true;
  }
  const eyes = [1, -1].map((side) => {
    const group = new THREE.Group();
    group.position.set(side * 0.062, 0.165, 0.155);
    const lid = new THREE.Group();
    lid.userData.squash = true;
    const look = new THREE.Group();
    const e = new THREE.Mesh(
      new Build()
        .add(ellipsoid(10, 8), "#ffffff", {
          s: [0.026, 0.032, 0.012],
          r: [0, side * 0.2, side * -0.25],
        })
        .build(),
      eyeMat,
    );
    look.add(e);
    lid.add(look);
    const glow = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: glowTex,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        opacity: 0.55,
      }),
    );
    glow.scale.setScalar(0.13);
    glow.position.z = 0.01;
    lid.add(glow);
    group.add(lid);
    head.add(group);
    rig.glow.push(e);
    return { group, lid, look, side };
  });
  rig.face = { eyes, brows: [], jaw: null, jawOpen: 0, lidOpen: 0, lidClosed: 0 };
  void skinMaterial;
  return rig;
}
