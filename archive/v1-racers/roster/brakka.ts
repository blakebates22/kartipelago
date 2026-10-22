/**
 * Brakka the triceratops: the Rocky Roader (design D).
 *
 * Silhouette: a broad, angular frill covered in rocky plates, framing the head from
 * behind, and three big ivory horns; a compact, muscular body sitting low. Warm
 * golden-brown skin, cream muzzle and belly, big eyes under heavy, determined brows.
 * Gear: utility straps and a small rugged pack.
 * Kart: a sturdy stone-and-timber roader: a broad sandstone nose with a dark footprint
 * emblem, chunky charcoal stone fenders, timber sides, green leaf tufts and a log on the
 * back.
 */
import * as THREE from "three";
import type { BodyKit } from "../kit/chassis";
import { buildArms, buildEyes, type RiderRig } from "../kit/rig";
import {
  Build,
  box,
  card,
  cone,
  cyl,
  ellipsoid,
  gem,
  horn,
  loft,
  taper,
  tube,
} from "../kit/shapes";
import { seeded, skinMaterial } from "../kit/paint";
import { backpack, emblemMesh, leaf, strap } from "../kit/props";
import type { RacerBuild } from "./types";

const MAIN = {
  skin: "#d38a3a",
  skinDark: "#a9652a",
  cream: "#f3e1b6",
  horn: "#f3ead2",
  hornBase: "#d8c9a4",
  rock1: "#9a948b",
  rock2: "#b8a990",
  rock3: "#8a7862",
  rockLight: "#d6caae",
  eye: "#2a1a10",
  brow: "#5a3518",
  mouth: "#8f2a30",
  tongue: "#e8707c",
  glove: "#3a2b24",
  strap: "#5e3c22",
  buckle: "#c9a24a",
  pack: "#8a6a44",
  packDark: "#6a4e30",
  // The kart.
  sand: "#e6d2a2",
  sandDark: "#c7ae7c",
  wood: "#8a5a34",
  woodDark: "#5f3c22",
  stone: "#625d58",
  stoneLight: "#87817a",
  orange: "#e07a2e",
  green: "#5d9e3a",
  greenLight: "#9ccf62",
  seat: "#4a3426",
  tyre: "#2b2626",
  ink: "#3a2a20",
};

/** The alternate look: Brakka in classic explorer red. */
const ALT: typeof MAIN = {
  ...MAIN,
  skin: "#d9533a",
  skinDark: "#a83a2a",
  rock1: "#e8a030",
  rock2: "#f2c050",
  rock3: "#c97a2a",
  rockLight: "#ffd86a",
  sand: "#f2d7a8",
  stone: "#9c3a2e",
  stoneLight: "#c4553e",
  orange: "#f2b33a",
};

type P = typeof MAIN;

/** A cluster of faceted rocks on a surface (grid of `n` x `m` over w x h, facing +Z). */
function rocks(
  b: Build,
  c: P,
  w: number,
  h: number,
  n: number,
  m: number,
  at: [number, number, number],
  seed: number,
  size = 1,
) {
  const r = seeded(seed);
  const cols = [c.rock1, c.rock2, c.rock3, c.rockLight];
  for (let i = 0; i < n; i++)
    for (let j = 0; j < m; j++) {
      const x = (i / Math.max(1, n - 1) - 0.5) * w + (r() - 0.5) * 0.03;
      const y = (j / Math.max(1, m - 1) - 0.5) * h + (r() - 0.5) * 0.03;
      const s = (0.05 + r() * 0.025) * size;
      b.add(gem(0), cols[Math.floor(r() * cols.length)]!, {
        p: [at[0] + x, at[1] + y, at[2]],
        s: [s * 1.3, s * 1.05, s * 0.2],
        r: [r() * 0.25, r() * 0.25, r() * 3],
      });
    }
}

// ------------------------------------------------------------------ the kart

function kart(c: P): BodyKit {
  return {
    wheel: { tyre: c.tyre, rim: c.orange, cap: "#f0b44a", ring: c.stoneLight, sides: 9 },
    steering: "#352a24",
    shell(b, detail) {
      b.add(box(1.0, 0.14, 2.2, 0.05), c.woodDark, { p: [0, 0.28, -0.05] });
      // A boxy tub: sandstone on top, timber sides.
      b.addColored(
        loft(
          [
            { at: [0, 0.5, -1.02], rx: 0.44, ry: 0.15, sq: 3.2 },
            { at: [0, 0.5, -0.7], rx: 0.54, ry: 0.2, sq: 3.4 },
            { at: [0, 0.5, 0.2], rx: 0.54, ry: 0.21, sq: 3.4 },
            { at: [0, 0.49, 0.8], rx: 0.5, ry: 0.2, sq: 3.2 },
          ],
          {
            sides: 12,
            steps: 2,
            capStart: true,
            capEnd: true,
            paint: (_t, a) =>
              a > 0.35 && a < 2.8 ? c.sand : a > -0.2 && a < 3.35 ? c.wood : c.woodDark,
          },
        ),
      );
      // The broad sandstone nose, flat at the front for the emblem, with stone teeth.
      b.add(taper(box(0.98, 0.4, 0.5, 0.1), 0.94, 0.9), c.sand, { p: [0, 0.48, 1.06] });
      b.add(box(1.02, 0.08, 0.52, 0.03), c.sandDark, { p: [0, 0.68, 1.04] });
      b.add(box(0.5, 0.1, 0.14, 0.04), c.woodDark, { p: [0, 0.3, 1.33] });
      // Cockpit rim: timber.
      b.add(new THREE.TorusGeometry(0.35, 0.06, 4, 12), c.wood, {
        p: [0, 0.7, -0.28],
        r: [Math.PI / 2, 0, Math.PI / 12],
        s: [1, 1.2, 1],
      });
      b.add(box(0.52, 0.1, 0.42, 0.04), c.seat, { p: [0, 0.48, -0.3] });
      b.add(box(0.52, 0.24, 0.1, 0.04), c.seat, { p: [0, 0.66, -0.56], r: [-0.12, 0, 0] });
      for (const s of [1, -1]) {
        // Chunky stone fenders: faceted slabs, lighter on top.
        b.add(gem(0), (p) => (p.y > 0.3 ? c.stoneLight : c.stone), {
          p: [s * 0.77, 0.76, 0.88],
          s: [0.27, 0.13, 0.44],
          r: [0, s * 0.3, 0],
        });
        b.add(gem(0), (p) => (p.y > 0.3 ? c.stoneLight : c.stone), {
          p: [s * 0.81, 0.76, -0.78],
          s: [0.3, 0.15, 0.5],
          r: [0, -s * 0.25, 0],
        });
        // Timber planks down the sides, with orange pegs.
        for (const k of [0, 1])
          b.add(box(0.06, 0.08, 0.84, 0.015), k ? c.wood : c.woodDark, {
            p: [s * 0.57, 0.44 + k * 0.1, 0.02],
          });
        b.add(cyl(0.025, 0.025, 0.06, 6), c.orange, {
          p: [s * 0.6, 0.49, 0.35],
          r: [0, 0, Math.PI / 2],
        });
        b.add(cyl(0.025, 0.025, 0.06, 6), c.orange, {
          p: [s * 0.6, 0.49, -0.3],
          r: [0, 0, Math.PI / 2],
        });
        b.add(box(0.2, 0.16, 0.8, 0.05), c.woodDark, { p: [s * 0.6, 0.36, 0.05] });
      }
      // The log on the back, strapped down, and stone exhaust.
      b.add(cyl(0.13, 0.13, 0.9, 9), c.wood, { p: [0, 0.78, -0.98], r: [0, 0, Math.PI / 2] });
      for (const s of [1, -1])
        b.add(cyl(0.1, 0.1, 0.02, 9), "#c49a64", {
          p: [s * 0.455, 0.78, -0.98],
          r: [0, 0, Math.PI / 2],
        });
      for (const x of [-0.25, 0.25])
        b.add(cyl(0.135, 0.135, 0.04, 9), c.strap, { p: [x, 0.78, -0.98], r: [0, 0, Math.PI / 2] });
      b.add(cyl(0.1, 0.12, 0.3, 7), c.stone, { p: [0, 0.42, -1.18], r: [Math.PI / 2, 0, 0] });
      if (detail === 0) {
        // Leaf tufts behind the log and on the nose corners.
        for (const s of [1, -1]) {
          b.addColored(leaf(0.42, 0.13, c.green, c.greenLight), {
            p: [s * 0.5, 0.82, -1.08],
            r: [-1.1, s * 0.4, s * 0.6],
          });
          b.addColored(leaf(0.34, 0.11, c.green, c.greenLight), {
            p: [s * 0.3, 0.84, -1.1],
            r: [-1.3, s * 0.2, s * 0.25],
          });
          b.addColored(leaf(0.3, 0.1, c.green, c.greenLight), {
            p: [s * 0.47, 0.66, 1.25],
            r: [-0.4, s * 0.2, s * 1.3],
          });
        }
      }
    },
    decorate(body) {
      const e = emblemMesh("footprint", { disc: c.sand, ink: c.ink, rim: c.sandDark }, 0.32);
      e.position.set(0, 0.47, 1.315);
      body.add(e);
    },
  };
}

// ------------------------------------------------------------------ Brakka

function rider(c: P): RiderRig {
  const mat = skinMaterial();
  const root = new THREE.Group();
  root.name = "brakka";
  const torso = new THREE.Group();
  root.add(torso);

  // A compact, muscular body: broad shoulders, cream belly.
  const body = new Build().addColored(
    loft(
      [
        { at: [0, -0.04, -0.01], rx: 0.22, ry: 0.19 },
        { at: [0, 0.12, 0.0], rx: 0.26, ry: 0.22 },
        { at: [0, 0.3, 0.01], rx: 0.28, ry: 0.21 },
        { at: [0, 0.43, 0.02], rx: 0.24, ry: 0.17 },
        { at: [0, 0.52, 0.03], rx: 0.16, ry: 0.14 },
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
  // Utility straps crossing the chest, and a little pack on the back.
  for (const s of [1, -1])
    body.addColored(
      strap(
        [
          [s * 0.2, 0.45, 0.13],
          [0, 0.27, 0.235],
          [-s * 0.21, 0.08, 0.2],
        ],
        0.024,
        0.01,
        c.strap,
      ),
    );
  body.add(box(0.06, 0.05, 0.03, 0.01), c.buckle, { p: [0, 0.27, 0.24] });
  body.addColored(backpack(0.26, 0.22, 0.12, { bag: c.pack, flap: c.packDark, buckle: c.buckle }), {
    p: [0, 0.3, -0.24],
  });
  torso.add(new THREE.Mesh(body.build(), mat));

  // The head: big skull, cream muzzle, a hooked beak.
  const head = new THREE.Group();
  head.position.set(0, 0.5, 0.06);
  head.rotation.x = -0.12;
  head.scale.setScalar(1.32);
  torso.add(head);
  const cream = new THREE.Color(c.cream);
  const skin = new THREE.Color(c.skin);
  const skull = new Build().addColored(
    loft(
      [
        { at: [0, 0.12, -0.17], rx: 0.11, ry: 0.11 },
        { at: [0, 0.13, -0.11], rx: 0.18, ry: 0.17 },
        { at: [0, 0.13, -0.01], rx: 0.21, ry: 0.19 },
        { at: [0, 0.11, 0.09], rx: 0.19, ry: 0.17, flat: 0.3 },
        { at: [0, 0.07, 0.18], rx: 0.15, ry: 0.13, flat: 0.4 },
        { at: [0, 0.04, 0.26], rx: 0.11, ry: 0.1, flat: 0.3 },
        { at: [0, 0.0, 0.31], rx: 0.07, ry: 0.075 },
        { at: [0, -0.04, 0.33], rx: 0.02, ry: 0.02 },
      ],
      {
        sides: 12,
        steps: 2,
        capStart: true,
        capEnd: true,
        paint: (t, a) => (t > 0.5 && a < 0.3 ? cream : t > 0.78 ? cream : skin),
      },
    ),
  );
  for (const s of [1, -1])
    skull.add(ellipsoid(6, 4), c.skinDark, { p: [s * 0.05, 0.1, 0.27], s: [0.02, 0.014, 0.014] });
  skull.add(ellipsoid(10, 6), c.mouth, { p: [0, 0.0, 0.15], s: [0.12, 0.04, 0.15] });
  // Three ivory horns: two long brow horns sweeping forward, a short nose horn.
  for (const s of [1, -1])
    skull.addColored(
      horn([s * 0.1, 0.24, 0.02], [s * 0.15, 0.39, 0.27], 0.05, c.horn, [s * 0.02, 0.05, -0.06], 7),
    );
  skull.addColored(horn([0, 0.15, 0.2], [0, 0.24, 0.27], 0.04, c.horn, [0, 0.02, -0.02], 6));
  head.add(new THREE.Mesh(skull.build(), mat));

  // The frill: a broad, angular shield behind the head, covered with rocky plates and
  // knobs round the edge. It lags a little behind the head's motion.
  const frill = new THREE.Group();
  frill.position.set(0, 0.2, -0.1);
  frill.rotation.x = -0.45;
  head.add(frill);
  const outline: [number, number][] = [];
  const N = 9;
  for (let i = 0; i <= N; i++) {
    const a = Math.PI * (0.06 + 0.88 * (i / N));
    const r = i % 2 ? 0.38 : 0.42;
    outline.push([Math.cos(a) * r * 1.15, Math.sin(a) * r * 0.85 - 0.04]);
  }
  outline.push([-0.2, -0.12], [0.2, -0.12]);
  const fb = new Build().add(card(outline, 0.05), (p) => (p.y > 0.24 ? c.skinDark : c.skin));
  // Rocky plates on the front and back faces, knobs round the edge.
  rocks(fb, c, 0.7, 0.24, 6, 3, [0, 0.13, -0.035], 11, 1.15);
  rocks(fb, c, 0.4, 0.06, 4, 1, [0, 0.31, -0.035], 12, 1.1);
  rocks(fb, c, 0.62, 0.2, 5, 2, [0, 0.16, 0.035], 13, 1.0);
  for (let i = 0; i <= N; i += 1) {
    const a = Math.PI * (0.06 + 0.88 * (i / N));
    const r = i % 2 ? 0.38 : 0.42;
    fb.add(cone(0.035, 0.08, 4), c.hornBase, {
      p: [Math.cos(a) * r * 1.15, Math.sin(a) * r * 0.85 - 0.04, 0],
      r: [0, 0, a - Math.PI / 2],
    });
  }
  frill.add(new THREE.Mesh(fb.build(), mat));

  // Lower jaw: the beak's lower half.
  const jaw = new THREE.Group();
  jaw.position.set(0, 0.0, 0.0);
  head.add(jaw);
  jaw.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          loft(
            [
              { at: [0, 0.0, -0.02], rx: 0.15, ry: 0.06 },
              { at: [0, -0.03, 0.12], rx: 0.13, ry: 0.055, flat: -0.4 },
              { at: [0, -0.03, 0.24], rx: 0.09, ry: 0.045, flat: -0.4 },
              { at: [0, -0.02, 0.3], rx: 0.03, ry: 0.02 },
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
        .add(ellipsoid(8, 5), c.tongue, { p: [0, -0.008, 0.13], s: [0.075, 0.022, 0.09] })
        .build(),
      mat,
    ),
  );

  const eyes = buildEyes(head, {
    at: [0.115, 0.165, 0.15],
    size: [0.074, 0.088, 0.066],
    yaw: 0.36,
    iris: c.eye,
    lid: c.skin,
    inward: 0.3,
    brow: { color: c.brow, at: [0.11, 0.255, 0.17], size: [0.066, 0.022, 0.03], tilt: -0.32 },
  });

  const { arms, hands } = buildArms(torso, {
    shoulder: [0.21, 0.41, 0.08],
    upper: 0.21,
    fore: 0.19,
    radius: [0.075, 0.065, 0.055],
    color: c.skin,
    hand: c.glove,
    handSize: 0.075,
    hint: [0.9, -0.4, -0.2],
  });

  // A short, thick tail behind the seat.
  const tailJ = new THREE.Group();
  tailJ.position.set(0, 0.06, -0.16);
  tailJ.rotation.x = 0.35;
  torso.add(tailJ);
  tailJ.add(
    new THREE.Mesh(
      new Build()
        .addColored(
          tube(
            [
              [0, 0, 0.04],
              [0, 0, -0.18],
              [0, -0.02, -0.34],
            ],
            [0.13, 0.09, 0.03],
            c.skin,
            { sides: 8 },
          ),
        )
        .build(),
      mat,
    ),
  );

  const low = new THREE.Mesh(
    new Build()
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.2, 0], s: [0.26, 0.26, 0.21] })
      .add(ellipsoid(6, 4), c.skin, { p: [0, 0.6, 0.12], s: [0.27, 0.23, 0.32] })
      .add(cyl(0.42, 0.5, 0.06, 6), c.rock1, { p: [0, 0.82, -0.05], r: [1.1, 0, 0] })
      .add(cone(0.06, 0.3, 4), c.horn, { p: [0.15, 0.85, 0.35], r: [1.0, 0, 0] })
      .add(cone(0.06, 0.3, 4), c.horn, { p: [-0.15, 0.85, 0.35], r: [1.0, 0, 0] })
      .build(),
    mat,
  );

  return {
    root,
    torso,
    neck: null,
    head,
    face: { ...eyes, jaw, jawOpen: 0.4 },
    arms,
    hands,
    tail: [tailJ],
    wings: [],
    wiggles: [{ obj: frill, kind: "crest", side: 0, amount: 0.6 }],
    low,
    cheer: [new THREE.Vector3(0.36, 0.66, 0.16), new THREE.Vector3(-0.36, 0.66, 0.16)],
    personality: {
      lean: 1.2,
      headTurn: 0.9,
      curiosity: 0.2,
      glanceEvery: 5,
      blinkEvery: 3.6,
      blinkTime: 0.12,
      bob: 0.02,
      bobHz: 1.6,
      steerHands: 1.0,
      boostKick: 0.9,
      boostFace: 0.55,
      grumble: 1,
      response: 1,
      restJaw: 0.24,
      restBrow: -0.35,
      restLids: 0.08,
      victory: "nod",
    },
  };
}

export const BRAKKA: RacerBuild<P> = {
  palettes: { main: MAIN, alt: ALT },
  kart,
  rider,
};
