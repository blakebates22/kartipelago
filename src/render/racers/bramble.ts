/**
 * Bramble the squirrel and his kart, in the faceted, pixel-textured style (like Moss):
 * a chestnut faceted head with a cream face mask, a swooping quiff, round ears and a
 * big bushy tail; and a rounded green kart with a cartoon face on its nose, a yellow
 * "beak" bumper, green fenders and chunky octagonal tyres.
 */
import * as THREE from "three";
import type { CharacterRig } from "./characters";
import { buildToyKart } from "./toykart";
import { Parts } from "./geo";
import { PixelArt, chamferBox, decalMaterial, decalOn, facetMaterial, gem } from "./faceted";

export const BRAMBLE = {
  fur: "#9a4e2c",
  furDark: "#7a3a20",
  cream: "#f2deae",
  nose: "#4a2626",
  kart: "#4fb565",
  kartDark: "#3c9a52",
  trim: "#f4c03c",
  tyre: "#2f2838",
  hub: "#e4d3a2",
  hubCap: "#8eac5b",
  wheel: "#2d2533",
  seat: "#3b2f48",
};

type Mouth = "smile" | "open" | "grin";
type Eyes = "open" | "closed" | "wide" | "determined";

/** Bramble's face at 64x40: a cream mask, big eyes, blush and an open, happy mouth. */
function paintFace(mouth: Mouth, eyes: Eyes) {
  const p = new PixelArt(64, 40);
  const ink = "#2b1d2a";
  const white = "#fffaf0";
  const fur = "#8f4829"; // the fur, as lit through the grain
  // The cream mask: round around both eyes and down over the muzzle, with a brown
  // peak dipping between the eyes.
  p.fill((x, y) => {
    const eyeL = ((x - 20) / 13) ** 2 + ((y - 17) / 13) ** 2 <= 1;
    const eyeR = ((x - 44) / 13) ** 2 + ((y - 17) / 13) ** 2 <= 1;
    const muzzle = ((x - 32) / 19) ** 2 + ((y - 30) / 11) ** 2 <= 1;
    const peak = y < 14 - Math.abs(x - 32) * 0.9 && Math.abs(x - 32) < 7;
    return (eyeL || eyeR || muzzle) && !peak;
  }, BRAMBLE.cream);
  // Blush.
  p.ellipse(9, 26, 3.5, 2.5, "#f29aa5");
  p.ellipse(55, 26, 3.5, 2.5, "#f29aa5");

  for (const side of [-1, 1]) {
    const cx = 32 + side * 12;
    const cy = 17;
    if (eyes === "closed") {
      p.fill((x, y) => {
        const d = ((x - cx) / 8) ** 2 + ((y - cy - 4) / 6) ** 2;
        return d <= 1 && d >= 0.5 && y < cy + 3;
      }, ink);
      continue;
    }
    const wide = eyes === "wide";
    const rx = wide ? 8.5 : 7.5;
    const ry = wide ? 10.5 : 9.5;
    p.ellipse(cx, cy, rx, ry, white);
    const pr = wide ? 4 : 5.2;
    const px = cx - side * 1.5;
    p.ellipse(px, cy + 1.5, pr, pr * 1.25, ink);
    p.rect(px + 1, cy - 3, 3, 3, white);
    if (eyes === "determined") {
      // Brows down toward the middle: a cheeky, competitive look.
      const lid = (x: number) => cy - ry + 3 + ((x - cx) * -side + rx) * 0.45;
      p.fill(
        (x, y) => ((x - cx) / (rx + 1.5)) ** 2 + ((y - cy) / (ry + 1.5)) ** 2 <= 1 && y < lid(x),
        fur,
      );
      p.fill((x, y) => Math.abs(x - cx) <= rx + 1 && y >= lid(x) - 2 && y < lid(x), "#4a2416");
    }
  }

  const cx = 32;
  const top = 30;
  if (mouth === "open") {
    p.ellipse(cx, 33, 4.5, 5, "#4a1f2a");
    p.ellipse(cx, 33.5, 3.2, 3.6, "#a63d4f");
    return p.texture();
  }
  const big = mouth === "grin";
  const rx = big ? 8.5 : 6.5;
  const ry = big ? 8.5 : 6;
  const inMouth = (x: number, y: number, k = 0) =>
    y >= top - k && ((x - cx) / (rx + k)) ** 2 + ((y - top) / (ry + k)) ** 2 <= 1;
  p.fill((x, y) => inMouth(x, y, 1.2), "#4a1f2a");
  p.fill((x, y) => inMouth(x, y), "#a63d4f");
  p.ellipse(cx, top + ry - 2, rx * 0.6, 2.6, "#f08aa0");
  return p.texture();
}

// ------------------------------------------------------------------ the kart

/** Bramble's kart: leaf green with a yellow bill and roll hoop. */
export const buildBrambleKart = (detail: 0 | 1 = 0) =>
  buildToyKart(
    {
      body: BRAMBLE.kart,
      bodyDark: BRAMBLE.kartDark,
      trim: BRAMBLE.trim,
      tyre: BRAMBLE.tyre,
      hub: BRAMBLE.hub,
      hubCap: BRAMBLE.hubCap,
      wheel: BRAMBLE.wheel,
      seat: BRAMBLE.seat,
    },
    detail,
    { bill: 0.45 },
  );

// ------------------------------------------------------------------ Bramble

export function buildBramble(grips: [THREE.Vector3, THREE.Vector3]): CharacterRig {
  const mat = facetMaterial();
  const root = new THREE.Group();
  const torso = new THREE.Group();
  root.add(torso);
  torso.add(
    new THREE.Mesh(
      new Parts()
        .add(gem(1), BRAMBLE.fur, { p: [0, 0.28, 0], s: [0.32, 0.32, 0.27] })
        .add(gem(1), BRAMBLE.cream, { p: [0, 0.24, 0.14], s: [0.2, 0.24, 0.15] })
        .build(),
      mat,
    ),
  );

  const head = new THREE.Group();
  head.position.set(0, 0.52, 0.02);
  torso.add(head);
  const headGeo = new Parts()
    .add(gem(3), BRAMBLE.fur, { p: [0, 0.3, 0.04], s: [0.6, 0.5, 0.5] })
    .build();
  head.add(new THREE.Mesh(headGeo, mat));
  head.add(
    new THREE.Mesh(
      new Parts()
        // A dark button nose.
        .add(gem(1), BRAMBLE.nose, { p: [0, 0.27, 0.53], s: [0.075, 0.055, 0.05] })
        // Round ears with cream insides.
        .add(gem(1), BRAMBLE.fur, { p: [0.43, 0.66, -0.02], s: [0.15, 0.16, 0.09] })
        .add(gem(1), BRAMBLE.fur, { p: [-0.43, 0.66, -0.02], s: [0.15, 0.16, 0.09] })
        .add(gem(1), BRAMBLE.cream, { p: [0.43, 0.65, 0.04], s: [0.08, 0.09, 0.04] })
        .add(gem(1), BRAMBLE.cream, { p: [-0.43, 0.65, 0.04], s: [0.08, 0.09, 0.04] })
        // A big swooping quiff, leaning forward over the brow.
        .add(gem(2), BRAMBLE.furDark, {
          p: [0.04, 0.82, 0.08],
          s: [0.36, 0.11, 0.3],
          r: [0.35, 0.25, 0.18],
        })
        .add(gem(1), BRAMBLE.fur, { p: [0.1, 0.9, 0.0], s: [0.24, 0.08, 0.2], r: [0.3, 0.4, 0.3] })
        .build(),
      mat,
    ),
  );

  // The painted face (swapped for expressions and blinks).
  const faceGeo = decalOn(headGeo, "front", [-0.52, 0.52, -0.02, 0.62], 0.12);
  const faces = new Map<string, THREE.Texture>();
  for (const mouth of ["smile", "open", "grin"] as Mouth[])
    for (const eyes of ["open", "closed", "wide", "determined"] as Eyes[])
      faces.set(`${mouth}/${eyes}`, paintFace(mouth, eyes));
  const faceMat = decalMaterial(faces.get("smile/open")!);
  head.add(new THREE.Mesh(faceGeo, faceMat));
  let current = "";
  const setFace = (mouth: Mouth, eyes: "open" | "closed" | "wide" | "sleepy") => {
    // Bramble's competitive streak: the determined look comes out a lot.
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

  // A big bushy tail curling up behind the seat.
  const tail = new THREE.Mesh(
    new Parts()
      .add(gem(1), BRAMBLE.fur, { p: [0, 0.05, -0.08], s: [0.2, 0.2, 0.2] })
      .add(gem(1), BRAMBLE.fur, { p: [0.02, 0.32, -0.24], s: [0.26, 0.26, 0.24] })
      .add(gem(1), BRAMBLE.furDark, { p: [0.04, 0.62, -0.22], s: [0.25, 0.25, 0.22] })
      .add(gem(1), BRAMBLE.fur, { p: [0.06, 0.86, -0.06], s: [0.19, 0.2, 0.18] })
      .add(gem(1), BRAMBLE.cream, { p: [0.07, 0.98, 0.06], s: [0.11, 0.11, 0.11] })
      .build(),
    mat,
  );
  tail.position.set(0, 0.1, -0.28);
  torso.add(tail);
  const wiggles: CharacterRig["wiggles"] = [{ obj: tail, kind: "tail", side: 0 }];

  const arm = () =>
    new THREE.Mesh(
      new Parts().add(chamferBox(0.14, 0.14, 1, 0.04), BRAMBLE.fur, { p: [0, 0, 0.5] }).build(),
      mat,
    );
  const arms: [THREE.Mesh, THREE.Mesh] = [arm(), arm()];
  const shoulders: [THREE.Vector3, THREE.Vector3] = [
    new THREE.Vector3(0.27, 0.44, 0.06),
    new THREE.Vector3(-0.27, 0.44, 0.06),
  ];
  arms.forEach((a, i) => {
    a.position.copy(shoulders[i]!);
    torso.add(a);
  });
  const paws = new Parts();
  for (const g of grips)
    paws.add(gem(1), BRAMBLE.furDark, { p: [g.x, g.y, g.z - 0.01], s: [0.09, 0.085, 0.09] });
  const hands = new THREE.Mesh(paws.build(), mat);

  const low = new THREE.Mesh(
    new Parts()
      .add(gem(0), BRAMBLE.fur, { p: [0, 0.28, 0], s: [0.32, 0.32, 0.27] })
      .add(gem(1), BRAMBLE.fur, { p: [0, 0.82, 0.06], s: [0.6, 0.5, 0.5] })
      .add(gem(0), BRAMBLE.furDark, { p: [0.04, 1.34, 0.1], s: [0.36, 0.11, 0.3] })
      .add(gem(0), BRAMBLE.fur, { p: [0, 0.75, -0.55], s: [0.26, 0.4, 0.24] })
      .build(),
    mat,
  );

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
      bob: 0.02,
      bobHz: 1.6,
      lean: 1,
      blinkEvery: 2.4,
      boostFace: "grin",
      glanceEvery: 3.5,
    },
  };
}
