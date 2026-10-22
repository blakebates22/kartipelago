/**
 * Pebble the ankylosaurus: the Shoreline Roller (design D).
 *
 * Silhouette: the thick armoured back, a dome of blue-grey plates with rows of pale ivory
 * spikes, and a thick tail ending in a rounded club over the back of the kart. Rounded,
 * compact and calm: slate-blue skin, cream muzzle and belly, big dark eyes, a friendly
 * relaxed look.
 * Kart: a low, rounded shoreline roller: cream nose with a big turquoise spiral, blue
 * fenders, wooden trim, cyan accents and a broad, stable stance.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import { Build, box, cone, cyl, ellipsoid, gem, loft, taper } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import { emblemMesh } from "../kit/props";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#7891c2",
  skinDark: "#56709e",
  cream: "#f2e4c4",
  plate: "#90a4cc",
  plateDark: "#6b81ab",
  spike: "#f2ead4",
  spikeBase: "#cfc4a6",
  eye: "#1a1418",
  mouth: "#8a2a3a",
  tongue: "#ec7a8c",
  glove: "#2c3346",
  brow: "#3a4766",
  // The kart.
  blue: "#5f9ee0",
  blueDark: "#3f74b8",
  cream2: "#f5ecd6",
  sand: "#dcc79a",
  wood: "#b9895a",
  slate: "#3c4a5e",
  cyan: "#35d0d8",
  seat: "#2f3b52",
  tyre: "#262a33",
};

/** The alternate look: Pebble as a sandy canyon cruiser. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#b07a4a",
  skinDark: "#8a5a32",
  plate: "#c4925a",
  plateDark: "#8f6236",
  blue: "#d9773a",
  blueDark: "#b0552a",
  cyan: "#f2b33a",
};

type P = typeof MAIN;

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return {
    wheel: { tyre: c.tyre, rim: c.blue, cap: c.cream2, ring: c.cyan, sides: 10 },
    steering: c.slate,
    shell(b, detail) {
      b.add(box(1.0, 0.14, 2.2, 0.05), c.slate, { p: [0, 0.28, -0.05] });
      // A low, round tub: cream on top, sandy sides, a cyan stripe.
      b.addColored(
        loft(
          [
            { at: [0, 0.47, -1.04], rx: 0.44, ry: 0.13 },
            { at: [0, 0.48, -0.75], rx: 0.56, ry: 0.18 },
            { at: [0, 0.48, -0.2], rx: 0.58, ry: 0.19 },
            { at: [0, 0.47, 0.4], rx: 0.54, ry: 0.19 },
            { at: [0, 0.45, 0.85], rx: 0.46, ry: 0.17 },
          ],
          {
            sides: 14,
            steps: 2,
            capStart: true,
            capEnd: true,
            paint: (_t, a) =>
              a > 0.25 && a < 2.9 ? c.cream2 : a > -0.1 && a < 3.25 ? c.cyan : c.sand,
          },
        ),
      );
      // The rounded cream nose, its front a big disc for the spiral.
      b.add(cyl(0.3, 0.3, 0.44, 14), c.cream2, {
        p: [0, 0.47, 1.06],
        r: [Math.PI / 2, 0, 0],
        s: [1.25, 1, 0.95],
      });
      b.add(new THREE.TorusGeometry(0.3, 0.035, 5, 16), c.wood, {
        p: [0, 0.47, 1.285],
        s: [1.25, 0.95, 1],
      });
      b.add(box(0.86, 0.08, 0.12, 0.03), c.slate, { p: [0, 0.27, 1.3] });
      // Wooden trim round the cockpit, and a seat.
      b.add(new THREE.TorusGeometry(0.36, 0.05, 4, 14), c.wood, {
        p: [0, 0.67, -0.28],
        r: [Math.PI / 2, 0, 0],
        s: [1, 1.18, 1],
      });
      b.add(box(0.52, 0.1, 0.42, 0.04), c.seat, { p: [0, 0.48, -0.3] });
      b.add(box(0.52, 0.22, 0.1, 0.04), c.seat, { p: [0, 0.64, -0.56], r: [-0.12, 0, 0] });
      for (const s of [1, -1]) {
        // Big rounded blue fenders, wide-set for a stable stance.
        b.add(taper(box(0.5, 0.28, 0.78, 0.13), 0.92, 0.75, 0.05), c.blue, {
          p: [s * 0.8, 0.74, 0.88],
        });
        b.add(box(0.54, 0.32, 0.86, 0.14), c.blueDark, { p: [s * 0.83, 0.72, -0.78] });
        b.add(box(0.05, 0.05, 0.7, 0.012), c.cyan, { p: [s * 1.08, 0.73, -0.78] });
        // Wooden rub-strips along the sides.
        b.add(box(0.06, 0.06, 0.9, 0.015), c.wood, { p: [s * 0.6, 0.46, 0.0] });
        b.add(box(0.22, 0.16, 0.8, 0.05), c.slate, { p: [s * 0.6, 0.36, 0.05] });
        // A little seashell on each back fender.
        if (detail === 0) {
          b.add(cone(0.08, 0.12, 6), "#f6c6b8", {
            p: [s * 0.83, 0.92, -0.95],
            r: [-0.4, 0, s * 0.3],
          });
        }
      }
      b.add(cyl(0.09, 0.11, 0.3, 8), c.slate, { p: [0, 0.4, -1.18], r: [Math.PI / 2, 0, 0] });
      b.add(cyl(0.11, 0.11, 0.05, 8), c.cyan, { p: [0, 0.4, -1.31], r: [Math.PI / 2, 0, 0] });
    },
    decorate(body) {
      const e = emblemMesh("spiral", { disc: c.cream2, ink: c.cyan, rim: c.cream2 }, 0.5);
      e.position.set(0, 0.47, 1.284);
      e.scale.set(1.25, 0.95, 1);
      body.add(e);
    },
  };
}

// ------------------------------------------------------------------ Pebble

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "pebble";
  const torso = new THREE.Group();
  root.add(torso);

  // A round, compact body with a cream belly.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, 0.0, -0.02], rx: 0.25, ry: 0.18 },
        { at: [0, 0.12, -0.02], rx: 0.29, ry: 0.26 },
        { at: [0, 0.28, -0.02], rx: 0.27, ry: 0.24 },
        { at: [0, 0.4, 0.0], rx: 0.2, ry: 0.18 },
        { at: [0, 0.47, 0.02], rx: 0.12, ry: 0.12 },
      ],
      {
        sides: 12,
        steps: 2,
        up: [0, 0, 1],
        capStart: true,
        paint: (_t, a) => (Math.abs(a - Math.PI / 2) < 0.8 ? c.cream : c.skin),
      },
    ),
  );
  // The armoured back: a dome of plates, with rows of ivory spikes.
  body.add(gem(2), (p) => (p.y > 0.55 ? c.plate : c.plateDark), {
    p: [0, 0.27, -0.08],
    s: [0.33, 0.33, 0.28],
  });
  const rows: [number, number, number][] = [
    // [height on the dome (0 low .. 1 top), spikes in the row, spike size]
    [0.24, 7, 0.13],
    [0.45, 6, 0.16],
    [0.8, 4, 0.15],
  ];
  rows.forEach(([hgt, n, size], ri) => {
    for (let k = 0; k < n; k++) {
      // Spread over the back half (and round the sides), facing outward.
      const span = hgt > 0.9 ? 0.6 : 2.6 - hgt * 1.2;
      const a = Math.PI + (n === 1 ? 0 : (k / (n - 1) - 0.5) * span) + (ri % 2 ? 0.12 : 0);
      const el = (hgt * Math.PI) / 2.3;
      const dir = new THREE.Vector3(
        Math.sin(a) * Math.cos(el),
        Math.sin(el),
        Math.cos(a) * Math.cos(el),
      );
      const base = new THREE.Vector3(0, 0.27, -0.08).add(
        dir.clone().multiply(new THREE.Vector3(0.33, 0.33, 0.28)),
      );
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      const e = new THREE.Euler().setFromQuaternion(q);
      body.add(cone(size * 0.55, size * 1.5, 6), (p) => (p.y < -0.25 ? c.spikeBase : c.spike), {
        p: [base.x, base.y, base.z],
        r: [e.x, e.y, e.z],
      });
      // A plate under each spike.
      body.add(gem(1), c.plateDark, {
        p: [base.x * 0.97, base.y, base.z * 0.97],
        r: [e.x, e.y, e.z],
        s: [size * 0.95, size * 0.3, size * 0.95],
      });
    }
  });
  torso.add(new THREE.Mesh(body.build(), mat));

  // The head: broad and friendly, with a cream muzzle and little horns at the back.
  const head = new THREE.Group();
  head.position.set(0, 0.42, 0.12);
  head.rotation.x = -0.05;
  head.scale.setScalar(1.3);
  torso.add(head);
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.1, -0.13], rx: 0.12, ry: 0.1 },
        { at: [0, 0.11, -0.07], rx: 0.19, ry: 0.15 },
        { at: [0, 0.11, 0.03], rx: 0.21, ry: 0.16 },
        { at: [0, 0.09, 0.13], rx: 0.19, ry: 0.13, flat: 0.35 },
        { at: [0, 0.06, 0.21], rx: 0.15, ry: 0.1, flat: 0.4 },
        { at: [0, 0.05, 0.26], rx: 0.1, ry: 0.07, flat: 0.3 },
        { at: [0, 0.05, 0.285], rx: 0.03, ry: 0.025 },
      ],
      {
        sides: 12,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => ((t > 0.55 && a < 0.4) || t > 0.82 ? c.cream : c.skin),
      },
    ),
  );
  for (const s of [1, -1]) {
    skull.add(cone(0.035, 0.09, 5), c.spike, {
      p: [s * 0.17, 0.17, -0.07],
      r: [-0.6, 0, -s * 0.9],
    });
    skull.add(cone(0.03, 0.07, 5), c.spike, { p: [s * 0.19, 0.08, -0.06], r: [0, 0, -s * 1.5] });
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.05, 0.1, 0.27], s: [0.018, 0.012, 0.012] });
  }
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.01, 0.13], s: [0.13, 0.035, 0.13] });
  head.add(new THREE.Mesh(skull.build(), mat));

  const jaw = new THREE.Group();
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, 0.0, -0.03], rx: 0.16, ry: 0.05 },
              { at: [0, -0.02, 0.1], rx: 0.15, ry: 0.05, flat: -0.4 },
              { at: [0, -0.02, 0.21], rx: 0.11, ry: 0.04, flat: -0.4 },
              { at: [0, -0.01, 0.255], rx: 0.03, ry: 0.015 },
            ],
            {
              sides: 10,
              steps: 2,
              capStart: true,
              capEnd: true,
              paint: (_t, a) => (a > 0.5 && a < 2.6 ? c.mouth : c.cream),
            },
          ),
        )
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.006, 0.12], s: [0.08, 0.02, 0.08] })
        .build(),
      mat,
    ),
  );

  const eyes = buildEyes(head, {
    at: [0.11, 0.15, 0.1],
    size: [0.08, 0.09, 0.07],
    yaw: 0.4,
    iris: c.eye,
    lid: c.skin,
    inward: 0.25,
    brow: { color: c.brow, at: [0.11, 0.235, 0.12], size: [0.05, 0.014, 0.022], tilt: 0.1 },
  });

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.23, 0.37, 0.1],
    upper: 0.2,
    fore: 0.19,
    radius: [0.072, 0.062, 0.055],
    color: c.skin,
    hand: c.glove,
    handSize: 0.07,
    hint: [0.85, -0.5, -0.2],
  });

  // The thick tail and its rounded club, resting out over the back of the kart.
  const tail: THREE.Object3D[] = [];
  let parent: THREE.Object3D = torso;
  const segs: [number, number, number][] = [
    [0.14, 0.2, 0.11],
    [0.11, 0.17, 0.085],
    [0.085, 0.13, 0.07],
  ];
  const lift = [0.5, -0.32, -0.12];
  segs.forEach(([r0, len, r1], k) => {
    const j = new THREE.Group();
    if (k === 0) j.position.set(0, 0.09, -0.2);
    else j.position.set(0, 0, -segs[k - 1]![1]);
    j.rotation.x = lift[k]!;
    parent.add(j);
    const tb = new Build().addColored(
      loft(
        [
          { at: [0, 0, r0 * 0.5], rx: r0 * 0.7, ry: r0 * 0.7 },
          { at: [0, 0, 0], rx: r0, ry: r0 },
          { at: [0, 0, -len], rx: r1, ry: r1 },
          { at: [0, 0, -len - r1 * 0.6], rx: r1 * 0.6, ry: r1 * 0.6 },
        ],
        { sides: 9, capStart: true, capEnd: true, paint: (_t, a) => (a < -1.0 ? c.cream : c.skin) },
      ),
    );
    // Small plates down the top of the tail.
    tb.add(gem(0), c.plateDark, {
      p: [0, r0 * 0.85, -len * 0.5],
      s: [r0 * 0.7, r0 * 0.3, len * 0.35],
    });
    if (k === 2) {
      // The club: a heavy rounded knob with ivory bumps.
      tb.add(ellipsoid(10, 7), c.plate, { p: [0, 0, -len - 0.08], s: [0.17, 0.12, 0.13] });
      for (const s of [1, -1])
        tb.add(ellipsoid(6, 4), c.spike, { p: [s * 0.15, 0, -len - 0.08], s: [0.05, 0.06, 0.06] });
      tb.add(ellipsoid(6, 4), c.spike, { p: [0, 0.1, -len - 0.08], s: [0.05, 0.04, 0.05] });
    }
    j.add(new THREE.Mesh(tb.build(), mat));
    tail.push(j);
    parent = j;
  });

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(7, 5), c.plate, { p: [0, 0.22, -0.06], s: [0.34, 0.34, 0.3] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.58, 0.2], s: [0.27, 0.21, 0.32] })
      .add(cone(0.06, 0.12, 4), c.spike, { p: [0.25, 0.4, -0.2] })
      .add(cone(0.06, 0.12, 4), c.spike, { p: [-0.25, 0.4, -0.2] })
      .add(cone(0.06, 0.12, 4), c.spike, { p: [0, 0.55, -0.25] })
      .add(ellipsoid(5, 4), c.plate, { p: [0, 0.32, -0.85], s: [0.17, 0.12, 0.14] })
      .build(),
    mat,
  );

  return {
    root,
    torso,
    neck: null,
    head,
    face: { ...eyes, jaw, jawOpen: 0.38 },
    arms,
    hands,
    tail,
    wings: [],
    wiggles: [],
    low,
    cheer: [new THREE.Vector3(0.36, 0.6, 0.18), new THREE.Vector3(-0.38, 0.62, 0.2)],
    personality: {
      lean: 1.0,
      headTurn: 0.6,
      curiosity: 0.3,
      glanceEvery: 6,
      blinkEvery: 4.5,
      blinkTime: 0.28,
      bob: 0.018,
      bobHz: 1.1,
      steerHands: 0.7,
      boostKick: 1.7,
      boostFace: 1.2,
      grumble: 0.1,
      response: 0.75,
      restJaw: 0.18,
      restBrow: 0.15,
      restLids: 0.22,
      victory: "wave",
    },
  };
}

export const PEBBLE: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
