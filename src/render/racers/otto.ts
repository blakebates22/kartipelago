/**
 * Otto the capybara, in the faceted, pixel-textured style: a big round caramel head
 * with a broad snout, tiny ears and an orange balanced on top; wide-set eyes (sleepy
 * when relaxed, determined when racing), dark paws; in a royal-blue toy kart with an
 * orange bill and roll hoop.
 */
import * as THREE from "three";
import type { CharacterRig } from "./characters";
import { Parts } from "./geo";
import { PixelArt, chamferBox, facetMaterial, gem, paintedFace } from "./faceted";
import { buildToyKart } from "./toykart";

export const OTTO = {
  fur: "#c8873f",
  furDark: "#a96d2e",
  paw: "#5a3a2c",
  orange: "#f39a2b",
  leaf: "#4caf50",
  stem: "#6b4a2b",
  kart: "#2f6fd6",
  kartDark: "#285fbb",
  trim: "#f4a62a",
  tyre: "#2f2838",
  hub: "#e4d3a2",
  hubCap: "#9aa58f",
  wheel: "#2d2533",
  seat: "#3b2f48",
};

/** Otto's face at 64x40: wide-set eyes, nostrils on the snout, and a big happy mouth. */
function paintFace(key: string) {
  const [mouth, eyes] = key.split("/");
  const p = new PixelArt(64, 40);
  const ink = "#241a20";
  const white = "#fffaf0";
  const fur = "#b8793a"; // the fur, as lit through the grain
  for (const side of [-1, 1]) {
    const cx = 32 + side * 17;
    const cy = 11;
    if (eyes === "closed") {
      p.fill((x, y) => {
        const d = ((x - cx) / 7) ** 2 + ((y - cy - 3) / 5) ** 2;
        return d <= 1 && d >= 0.5 && y < cy + 2;
      }, ink);
      continue;
    }
    const wide = eyes === "wide";
    const rx = wide ? 7.5 : 7;
    const ry = wide ? 8.5 : 7.5;
    p.ellipse(cx, cy, rx, ry, white);
    const pr = wide ? 3.6 : 4.6;
    const px = cx - side * 1.5;
    p.ellipse(px, cy + 1.2, pr, pr * 1.2, ink);
    p.rect(px + 1, cy - 2.5, 2, 2, white);
    if (eyes === "determined" || eyes === "sleepy") {
      // Determined: a slanted brow toward the middle. Sleepy: heavy level lids.
      const lid =
        eyes === "sleepy"
          ? () => cy - 1
          : (x: number) => cy - ry + 2.5 + ((x - cx) * -side + rx) * 0.42;
      p.fill(
        (x, y) => ((x - cx) / (rx + 1.5)) ** 2 + ((y - cy) / (ry + 1.5)) ** 2 <= 1 && y < lid(x),
        fur,
      );
      p.fill((x, y) => Math.abs(x - cx) <= rx + 1 && y >= lid(x) - 1.6 && y < lid(x), "#4a2a16");
    }
  }
  // Nostrils.
  p.ellipse(26, 22, 2.2, 1.8, ink);
  p.ellipse(38, 22, 2.2, 1.8, ink);
  const cx = 32;
  const top = 28;
  if (mouth === "open") {
    p.ellipse(cx, 31, 4, 4.5, "#5a1820");
    p.ellipse(cx, 31.5, 2.8, 3.2, "#b8323c");
    return p.texture();
  }
  const big = mouth === "grin";
  const rx = big ? 9 : 7;
  const ry = big ? 8 : 6;
  const inMouth = (x: number, y: number, k = 0) =>
    y >= top - k && ((x - cx) / (rx + k)) ** 2 + ((y - top) / (ry + k)) ** 2 <= 1;
  p.fill((x, y) => inMouth(x, y, 1.2), "#5a1820");
  p.fill((x, y) => inMouth(x, y), "#b8323c");
  p.ellipse(cx + 1, top + ry - 2, rx * 0.55, 2.4, "#e06b74");
  return p.texture();
}

/** Otto's kart: royal blue with an orange bill and roll hoop. */
export const buildOttoKart = (detail: 0 | 1 = 0) =>
  buildToyKart(
    {
      body: OTTO.kart,
      bodyDark: OTTO.kartDark,
      trim: OTTO.trim,
      tyre: OTTO.tyre,
      hub: OTTO.hub,
      hubCap: OTTO.hubCap,
      wheel: OTTO.wheel,
      seat: OTTO.seat,
    },
    detail,
    { bill: 0.7 },
  );

export function buildOtto(grips: [THREE.Vector3, THREE.Vector3]): CharacterRig {
  const mat = facetMaterial();
  const root = new THREE.Group();
  const torso = new THREE.Group();
  root.add(torso);
  torso.add(
    new THREE.Mesh(
      new Parts()
        // A big, solid body.
        .add(gem(1), OTTO.fur, { p: [0, 0.3, -0.02], s: [0.38, 0.36, 0.32] })
        .build(),
      mat,
    ),
  );

  const head = new THREE.Group();
  head.position.set(0, 0.56, 0.02);
  torso.add(head);
  // A big round head with a broad, blunt snout (one surface for the painted face).
  const headGeo = new Parts()
    .add(gem(3), OTTO.fur, { p: [0, 0.32, 0], s: [0.56, 0.5, 0.52] })
    .add(gem(2), OTTO.fur, { p: [0, 0.18, 0.28], s: [0.44, 0.3, 0.3] })
    .build();
  head.add(new THREE.Mesh(headGeo, mat));
  head.add(
    new THREE.Mesh(
      new Parts()
        // Tiny round ears.
        .add(gem(1), OTTO.furDark, { p: [0.36, 0.76, -0.08], s: [0.1, 0.09, 0.06] })
        .add(gem(1), OTTO.furDark, { p: [-0.36, 0.76, -0.08], s: [0.1, 0.09, 0.06] })
        .build(),
      mat,
    ),
  );
  const show = paintedFace(head, headGeo, [-0.5, 0.5, -0.06, 0.62], paintFace);
  // Otto's moods: content and sleepy-eyed normally, determined when racing hard.
  const setFace: CharacterRig["setFace"] = (mouth, eyes) =>
    show(
      `${mouth}/${eyes === "closed" ? "closed" : mouth === "grin" ? "determined" : mouth === "open" ? "wide" : "sleepy"}`,
    );

  // The orange.
  const orange = new THREE.Mesh(
    new Parts()
      .add(gem(2), OTTO.orange, { p: [0, 0.11, 0], s: [0.15, 0.13, 0.15] })
      .add(new THREE.CylinderGeometry(0.015, 0.02, 0.07, 5), OTTO.stem, { p: [0, 0.26, 0] })
      .add(gem(0), OTTO.leaf, { p: [0.07, 0.28, 0], s: [0.08, 0.015, 0.04], r: [0, 0, 0.35] })
      .build(),
    mat,
  );
  orange.position.set(0, 0.8, -0.02);
  head.add(orange);
  const wiggles: CharacterRig["wiggles"] = [{ obj: orange, kind: "orange", side: 0 }];

  const arm = () =>
    new THREE.Mesh(
      new Parts().add(chamferBox(0.16, 0.16, 1, 0.045), OTTO.fur, { p: [0, 0, 0.5] }).build(),
      mat,
    );
  const arms: [THREE.Mesh, THREE.Mesh] = [arm(), arm()];
  const shoulders: [THREE.Vector3, THREE.Vector3] = [
    new THREE.Vector3(0.32, 0.48, 0.06),
    new THREE.Vector3(-0.32, 0.48, 0.06),
  ];
  arms.forEach((a, i) => {
    a.position.copy(shoulders[i]!);
    torso.add(a);
  });
  const paws = new Parts();
  for (const g of grips)
    paws.add(gem(1), OTTO.paw, { p: [g.x, g.y, g.z - 0.01], s: [0.1, 0.09, 0.1] });
  const hands = new THREE.Mesh(paws.build(), mat);

  const low = new THREE.Mesh(
    new Parts()
      .add(gem(0), OTTO.fur, { p: [0, 0.3, -0.02], s: [0.38, 0.36, 0.32] })
      .add(gem(1), OTTO.fur, { p: [0, 0.88, 0.02], s: [0.56, 0.5, 0.52] })
      .add(gem(0), OTTO.orange, { p: [0, 1.48, 0], s: 0.15 })
      .build(),
    mat,
  );
  const none = () => Object.assign(new THREE.Mesh(), { visible: false });
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
      bob: 0.015,
      bobHz: 0.9,
      lean: 0.7,
      blinkEvery: 4.5,
      boostFace: "grin",
      glanceEvery: 7,
    },
  };
}
