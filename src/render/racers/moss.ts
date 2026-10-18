/**
 * Moss the axolotl and Moss's kart, in the faceted, pixel-textured style:
 * a big faceted head with a painted pixel-art face (swapped for expressions), chunky
 * gem-like gills, blocky arms with dark gloves, and an angular little formula kart with
 * chunky octagonal tyres, teal pods and a cream crown on the nose.
 *
 * Builds the same KartModel / CharacterRig as the other racers, so the same animator
 * drives it.
 */
import * as THREE from "three";
import type { CharacterRig } from "./characters";
import type { KartModel } from "./kart";
import { Parts } from "./geo";
import {
  PixelArt,
  chamferBox,
  decalMaterial,
  decalOn,
  facetMaterial,
  gem,
  octTyre,
  taper,
} from "./faceted";

export const MOSS = {
  skin: "#36b9ad",
  skinDark: "#2a9a90",
  chest: "#b8ece2",
  gill: "#d8467f",
  gillLight: "#ee7193",
  glove: "#3a2d47",
  kart: "#f5c23b",
  pod: "#35b5a8",
  tyre: "#2f2838",
  hub: "#e4d3a2",
  hubCap: "#8eac5b",
  wheel: "#2d2533",
  seat: "#3b2f48",
  cream: "#f7e8c8",
};

// ------------------------------------------------------------------ face textures

type Mouth = "smile" | "open" | "grin";
type Eyes = "open" | "closed" | "wide" | "determined";

/** Moss's face, painted at 64x40: big eyes, a wide mouth and blushing cheeks. */
function paintFace(mouth: Mouth, eyes: Eyes) {
  const W = 64;
  const H = 40;
  const p = new PixelArt(W, H);
  const ink = "#2b1d3a";
  const white = "#fffaf0";
  const skin = "#32ada2"; // the skin, as lit through the grain
  // Cheeks.
  p.ellipse(6.5, 27, 4.5, 3.2, "#f39ab3");
  p.ellipse(57.5, 27, 4.5, 3.2, "#f39ab3");

  for (const side of [-1, 1]) {
    const cx = 32 + side * 14;
    const cy = 15;
    if (eyes === "closed") {
      // Happy closed eyes: a thick dark arc each.
      p.fill((x, y) => {
        const d = ((x - cx) / 9) ** 2 + ((y - cy - 4) / 7) ** 2;
        return d <= 1 && d >= 0.5 && y < cy + 3;
      }, ink);
      continue;
    }
    const wide = eyes === "wide";
    const rx = wide ? 10.5 : 9.5;
    const ry = wide ? 12.5 : 11.5;
    p.ellipse(cx, cy, rx, ry, white);
    // Big dark pupils, looking a little inward (smaller when wide-eyed), with a bright
    // square highlight.
    const pr = wide ? 4.5 : 6;
    const px = cx - side * 1.8;
    p.ellipse(px, cy + 1.5, pr, pr * 1.25, ink);
    p.rect(px + 1, cy - 3.5, 3, 3, white);
    if (eyes === "determined") {
      // A mischievous slant: skin over the top of each eye, lower toward the middle,
      // with a dark brow line along its edge.
      const lid = (x: number) => cy - ry + 3 + ((x - cx) * -side + rx) * 0.42;
      p.fill(
        (x, y) => ((x - cx) / (rx + 1.5)) ** 2 + ((y - cy) / (ry + 1.5)) ** 2 <= 1 && y < lid(x),
        skin,
      );
      p.fill((x, y) => Math.abs(x - cx) <= rx + 1 && y >= lid(x) - 2 && y < lid(x), "#1c5f5a");
    } else {
      // A thin dark line over the top of the eye.
      p.fill((x, y) => {
        const d = ((x - cx) / (rx + 1)) ** 2 + ((y - cy) / (ry + 1)) ** 2;
        return d <= 1 && d > 0.8 && y < cy - ry * 0.4;
      }, "#1c5f5a");
    }
  }

  const cx = 32;
  const top = 27;
  if (mouth === "grin") {
    // A wide open grin with one buck tooth.
    const inMouth = (x: number, y: number, k = 0) =>
      y >= top - k && ((x - cx) / (12 + k)) ** 2 + ((y - top) / (10.5 + k)) ** 2 <= 1;
    p.fill((x, y) => inMouth(x, y, 1.2), "#4d1a45");
    p.fill((x, y) => inMouth(x, y), "#8a2a63");
    p.ellipse(cx + 1, 35.5, 6.5, 3, "#d3577f");
    p.rect(cx - 4, top, 5, 5, white);
  } else if (mouth === "smile") {
    // A happy open smile, smaller than the grin.
    p.fill((x, y) => y >= top && ((x - cx) / 9.5) ** 2 + ((y - top) / 7) ** 2 <= 1, "#4d1a45");
    p.fill((x, y) => y >= top + 1 && ((x - cx) / 8) ** 2 + ((y - top) / 5.8) ** 2 <= 1, "#8a2a63");
    p.ellipse(cx, 32, 4.5, 1.8, "#d3577f");
    p.rect(cx - 3, top + 1, 4, 3, white);
  } else {
    // "Oh!"
    p.ellipse(cx, 31, 5.5, 6, "#4d1a45");
    p.ellipse(cx, 31.5, 4, 4.5, "#8a2a63");
  }
  return p.texture();
}

/** The cream zig-zag on Moss's chest. */
function paintChest() {
  const p = new PixelArt(16, 16);
  p.fill((x, y) => {
    const zig = Math.abs(((x / 4) % 1) - 0.5) * 2; // 0..1 triangle wave
    return y > 4 + zig * 3;
  }, MOSS.chest);
  return p.texture();
}

/** A cream crown on the kart's nose. */
function paintCrown() {
  const p = new PixelArt(24, 16);
  p.fill((x, y) => {
    if (y >= 10 && y <= 14 && x >= 3 && x <= 21) return true;
    // Three spikes.
    for (const sx of [5, 12, 19]) if (y >= 3 + Math.abs(x - sx) * 1.6 && y < 11) return true;
    return false;
  }, MOSS.cream);
  return p.texture();
}

// ------------------------------------------------------------------ the kart

export function buildMossKart(detail: 0 | 1 = 0): KartModel {
  const mat = facetMaterial();
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);

  const p = new Parts();
  // Floor tray.
  p.add(chamferBox(0.9, 0.14, 2.2, 0.04), MOSS.kart, { p: [0, 0.28, 0] });
  // The big wedge nose: tall at the cockpit, sloping down to a narrow tip.
  const nose = taper(chamferBox(0.8, 0.5, 1.12, 0.09), 0.62, 0.45);
  p.add(nose, MOSS.kart, { p: [0, 0.47, 0.92] });
  // A low, wide front wing at the tip.
  p.add(chamferBox(1.2, 0.07, 0.3, 0.03), MOSS.kart, { p: [0, 0.25, 1.5] });
  // Raised cockpit sides.
  for (const side of [-1, 1])
    p.add(chamferBox(0.16, 0.44, 0.92, 0.05), MOSS.kart, { p: [side * 0.38, 0.52, -0.2] });
  // Chunky teal pods over the wheels (the front ones angled like fenders), and teal
  // panels between them.
  for (const side of [-1, 1]) {
    p.add(taper(chamferBox(0.5, 0.36, 0.78, 0.12), 0.88, 0.62, 0.06), MOSS.pod, {
      p: [side * 0.75, 0.72, 0.86],
    });
    p.add(chamferBox(0.56, 0.5, 0.86, 0.12), MOSS.pod, { p: [side * 0.79, 0.66, -0.76] });
    p.add(chamferBox(0.22, 0.24, 0.8, 0.05), MOSS.pod, { p: [side * 0.58, 0.42, 0.05] });
  }
  // Seat.
  p.add(chamferBox(0.5, 0.1, 0.45, 0.03), MOSS.seat, { p: [0, 0.46, -0.32] });
  p.add(chamferBox(0.52, 0.46, 0.1, 0.03), MOSS.seat, { p: [0, 0.68, -0.56] });
  // Roll hoop behind the seat.
  for (const side of [-1, 1])
    p.add(chamferBox(0.09, 0.5, 0.09, 0.02), MOSS.kart, { p: [side * 0.3, 0.86, -0.62] });
  p.add(chamferBox(0.69, 0.09, 0.09, 0.02), MOSS.kart, { p: [0, 1.1, -0.62] });
  // Exhausts.
  for (const side of [-1, 1])
    p.add(new THREE.CylinderGeometry(0.08, 0.09, 0.3, 8), MOSS.tyre, {
      p: [side * 0.2, 0.42, -1.2],
      r: [Math.PI / 2, 0, 0],
    });
  const shellGeo = p.build();
  body.add(new THREE.Mesh(shellGeo, mat));
  if (detail === 0) {
    // The crown, painted on the top of the nose.
    const crownGeo = decalOn(
      nose.clone().translate(0, 0.47, 0.92),
      "top",
      [-0.27, 0.27, -1.28, -0.66],
      0.4,
    );
    body.add(new THREE.Mesh(crownGeo, decalMaterial(paintCrown())));
  }

  // Chunky octagonal tyres, cream hubs, green caps.
  const wheel = (r: number) => {
    const w = new Parts();
    w.add(octTyre(r, 0.34, 0.07), MOSS.tyre);
    w.add(new THREE.CylinderGeometry(r * 0.62, r * 0.62, 0.36, 8), MOSS.hub, {
      r: [0, 0, Math.PI / 2],
    });
    w.add(new THREE.CylinderGeometry(r * 0.22, r * 0.26, 0.42, 8), MOSS.hubCap, {
      r: [0, 0, Math.PI / 2],
    });
    return w.build();
  };
  const spots: [number, number, number, boolean][] = [
    [0.76, 0.88, 0.36, true],
    [-0.76, 0.88, 0.36, true],
    [0.8, -0.78, 0.42, false],
    [-0.8, -0.78, 0.42, false],
  ];
  const wheels: KartModel["wheels"] = [];
  const front = wheel(0.36);
  const rear = wheel(0.42);
  if (detail === 1) {
    const baked = new Parts().addColored(shellGeo);
    for (const [x, z, r, f] of spots) baked.addColored(f ? front : rear, { p: [x, r, z] });
    (body.children[0] as THREE.Mesh).geometry = baked.build();
  } else {
    for (const [x, z, r, f] of spots) {
      const pivot = new THREE.Group();
      pivot.position.set(x, r, z);
      const tyre = new THREE.Mesh(f ? front : rear, mat);
      pivot.add(tyre);
      root.add(pivot);
      wheels.push({ pivot, tyre, radius: r, front: f });
    }
  }

  // A dark octagonal steering wheel on a short column.
  const steering = new THREE.Group();
  steering.position.set(0, 0.9, 0.24);
  steering.rotation.x = -0.5;
  const sw = new Parts()
    .add(new THREE.TorusGeometry(0.17, 0.04, 4, 8), MOSS.wheel, { r: [0, 0, Math.PI / 8] })
    .add(chamferBox(0.3, 0.05, 0.04, 0.01), MOSS.wheel)
    .add(chamferBox(0.05, 0.16, 0.04, 0.01), MOSS.wheel, { p: [0, -0.08, 0] })
    .add(new THREE.CylinderGeometry(0.035, 0.035, 0.34, 6), MOSS.wheel, {
      p: [0, -0.05, 0.17],
      r: [Math.PI / 2 - 0.3, 0, 0],
    });
  steering.add(new THREE.Mesh(sw.build(), mat));
  body.add(steering);

  return {
    root,
    body,
    wheels,
    steering,
    grips: [new THREE.Vector3(0.15, 0.03, -0.02), new THREE.Vector3(-0.15, 0.03, -0.02)],
    seat: new THREE.Vector3(0, 0.5, -0.3),
    exhaust: new THREE.Vector3(0, 0.42, -1.32),
  };
}

// ------------------------------------------------------------------ Moss

export function buildMoss(grips: [THREE.Vector3, THREE.Vector3]): CharacterRig {
  const mat = facetMaterial();
  const root = new THREE.Group();
  const torso = new THREE.Group();
  root.add(torso);

  const torsoGeo = new Parts()
    .add(gem(1), MOSS.skin, { p: [0, 0.28, 0], s: [0.3, 0.32, 0.25] })
    .build();
  torso.add(new THREE.Mesh(torsoGeo, mat));
  torso.add(
    new THREE.Mesh(
      decalOn(torsoGeo, "front", [-0.24, 0.24, 0.0, 0.5], 0.3),
      decalMaterial(paintChest()),
    ),
  );

  const head = new THREE.Group();
  head.position.set(0, 0.52, 0.02);
  torso.add(head);
  // A big, wide faceted head.
  const headGeo = new Parts()
    .add(gem(3), MOSS.skin, { p: [0, 0.3, 0.04], s: [0.64, 0.48, 0.5] })
    .build();
  head.add(new THREE.Mesh(headGeo, mat));

  // The painted face: one decal on the head's own facets, its texture swapped for
  // each expression (and blinks).
  const faceGeo = decalOn(headGeo, "front", [-0.52, 0.52, -0.02, 0.62], 0.12);
  const faces = new Map<string, THREE.Texture>();
  for (const mouth of ["smile", "open", "grin"] as Mouth[])
    for (const eyes of ["open", "closed", "wide", "determined"] as Eyes[])
      faces.set(`${mouth}/${eyes}`, paintFace(mouth, eyes));
  const faceMat = decalMaterial(faces.get("smile/open")!);
  // Freeing the material frees all the expressions painted for it.
  faceMat.addEventListener("dispose", () => {
    for (const t of faces.values()) t.dispose();
  });
  head.add(new THREE.Mesh(faceGeo, faceMat));
  let current = "";
  const setFace = (mouth: Mouth, eyes: "open" | "closed" | "wide" | "sleepy") => {
    // Moss's looks: cheerful toothy smile; a determined, mischievous grin when racing
    // hard; wide-eyed "oh!" when surprised.
    const e: Eyes =
      eyes === "closed"
        ? "closed"
        : mouth === "grin"
          ? "determined"
          : mouth === "open"
            ? "wide"
            : "open";
    const key = `${mouth}/${e}`;
    if (key === current) return;
    current = key;
    faceMat.map = faces.get(key)!;
    faceMat.needsUpdate = true;
  };

  // Gills: three chunky gem fronds a side, fanning up and out.
  const wiggles: CharacterRig["wiggles"] = [];
  for (const side of [-1, 1]) {
    const g = new Parts();
    [0.95, 0.42, -0.08].forEach((angle, k) => {
      const dir = new THREE.Vector3(side * Math.cos(angle), Math.sin(angle), -0.3).normalize();
      [0.12, 0.3, 0.47].forEach((d, j) => {
        const r = 0.14 - j * 0.012;
        g.add(gem(1), (k + j) % 2 ? MOSS.gillLight : MOSS.gill, {
          p: [dir.x * d, dir.y * d, dir.z * d],
          s: [r, r * 0.95, r],
          r: [j, k, 0],
        });
      });
    });
    const m = new THREE.Mesh(g.build(), mat);
    m.position.set(side * 0.5, 0.42, -0.04);
    head.add(m);
    wiggles.push({ obj: m, kind: "gill", side });
  }
  // A little tail fin, seen over the back of the kart.
  const tail = new THREE.Mesh(
    new Parts()
      .add(gem(1), MOSS.skinDark, { p: [0, 0.18, -0.08], s: [0.05, 0.24, 0.16], r: [-0.5, 0, 0] })
      .build(),
    mat,
  );
  tail.position.set(0, 0.08, -0.26);
  torso.add(tail);
  wiggles.push({ obj: tail, kind: "tail", side: 0 });

  // Blocky arms (stretched from shoulder to hand) and dark gloves on the wheel.
  const arm = () => {
    const geo = new Parts()
      .add(chamferBox(0.13, 0.13, 1, 0.035), MOSS.skin, { p: [0, 0, 0.5] })
      .build();
    return new THREE.Mesh(geo, mat);
  };
  const arms: [THREE.Mesh, THREE.Mesh] = [arm(), arm()];
  const shoulders: [THREE.Vector3, THREE.Vector3] = [
    new THREE.Vector3(0.26, 0.44, 0.06),
    new THREE.Vector3(-0.26, 0.44, 0.06),
  ];
  arms.forEach((a, i) => {
    a.position.copy(shoulders[i]!);
    torso.add(a);
  });
  const gloves = new Parts();
  for (const g of grips)
    gloves.add(chamferBox(0.15, 0.14, 0.15, 0.04), MOSS.glove, { p: [g.x, g.y, g.z - 0.01] });
  const hands = new THREE.Mesh(gloves.build(), mat);

  const low = new THREE.Mesh(
    new Parts()
      .add(gem(0), MOSS.skin, { p: [0, 0.28, 0], s: [0.3, 0.32, 0.25] })
      .add(gem(1), MOSS.skin, { p: [0, 0.82, 0.06], s: [0.62, 0.47, 0.5] })
      .add(gem(0), MOSS.gill, { p: [0.62, 0.98, 0], s: [0.22, 0.2, 0.12] })
      .add(gem(0), MOSS.gill, { p: [-0.62, 0.98, 0], s: [0.22, 0.2, 0.12] })
      .build(),
    mat,
  );

  // Unused by the decal face, but part of the shared rig shape.
  const none = () => {
    const m = new THREE.Mesh();
    m.visible = false;
    return m;
  };
  return {
    root,
    torso,
    head,
    eyes: new THREE.Group(),
    mouths: { smile: none(), open: none(), grin: none() },
    brows: null,
    shoulders,
    arms,
    hands,
    wiggles,
    low,
    setFace,
    personality: {
      bob: 0.035,
      bobHz: 2.2,
      lean: 1.15,
      blinkEvery: 3,
      boostFace: "grin",
      glanceEvery: 5,
    },
  };
}
