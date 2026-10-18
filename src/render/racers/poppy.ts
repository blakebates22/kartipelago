/**
 * Poppy the moth, in the faceted, pixel-textured style: a round lavender head with
 * huge eyes, a little pink nose, long striped club-tipped antennae, a cream bib and
 * dark gloves; in a cherry-red toy kart with a big cream bill and blue tyres.
 */
import * as THREE from "three";
import type { CharacterRig } from "./characters";
import { Parts } from "./geo";
import { PixelArt, chamferBox, facetMaterial, gem, paintedFace } from "./faceted";
import { buildToyKart } from "./toykart";

export const POPPY = {
  skin: "#a585e0",
  skinDark: "#8466c4",
  bib: "#f4ead6",
  nose: "#e0457f",
  glove: "#3a2d47",
  stripe: "#2b2235",
  band: "#8b5fd0",
  kart: "#e9483f",
  kartDark: "#cf3b33",
  trim: "#f2e6c8",
  tyre: "#24607d",
  hub: "#efe4c4",
  hubCap: "#a8a8a8",
  wheel: "#2d2533",
  seat: "#3b2f48",
};

/** Poppy's face at 64x40: huge eyes, round blush and an open happy mouth. */
function paintFace(key: string) {
  const [mouth, eyes] = key.split("/");
  const p = new PixelArt(64, 40);
  const ink = "#241a33";
  const white = "#fffaf0";
  p.ellipse(7.5, 28, 3.6, 3.2, "#f07aa0");
  p.ellipse(56.5, 28, 3.6, 3.2, "#f07aa0");
  for (const side of [-1, 1]) {
    const cx = 32 + side * 13.5;
    const cy = 15;
    if (eyes === "closed") {
      p.fill((x, y) => {
        const d = ((x - cx) / 9) ** 2 + ((y - cy - 4) / 7) ** 2;
        return d <= 1 && d >= 0.5 && y < cy + 3;
      }, ink);
      continue;
    }
    const wide = eyes === "wide";
    const rx = wide ? 11.5 : 10.5;
    const ry = wide ? 13.5 : 12.5;
    p.ellipse(cx, cy, rx, ry, white);
    // Huge dark pupils, the moth's big dark eyes.
    const pr = wide ? 5.5 : 7.2;
    const px = cx - side * 2;
    p.ellipse(px, cy + 1.5, pr, pr * 1.25, ink);
    p.rect(px + 1, cy - 4, 3, 3, white);
    if (eyes === "determined") {
      const lid = (x: number) => cy - ry + 3 + ((x - cx) * -side + rx) * 0.32;
      p.fill(
        (x, y) => ((x - cx) / (rx + 1.5)) ** 2 + ((y - cy) / (ry + 1.5)) ** 2 <= 1 && y < lid(x),
        "#9a7bd2",
      );
      p.fill((x, y) => Math.abs(x - cx) <= rx + 1 && y >= lid(x) - 1.6 && y < lid(x), "#4a3478");
    }
  }
  const cx = 32;
  const top = 30;
  if (mouth === "open") {
    p.ellipse(cx, 33, 4, 4.5, "#5a1838");
    p.ellipse(cx, 33.5, 2.8, 3.2, "#b02c66");
    return p.texture();
  }
  const big = mouth === "grin";
  const rx = big ? 7.5 : 6;
  const ry = big ? 8 : 6;
  const inMouth = (x: number, y: number, k = 0) =>
    y >= top - k && ((x - cx) / (rx + k)) ** 2 + ((y - top) / (ry + k)) ** 2 <= 1;
  p.fill((x, y) => inMouth(x, y, 1.2), "#5a1838");
  p.fill((x, y) => inMouth(x, y), "#b02c66");
  p.ellipse(cx, top + ry - 2, rx * 0.55, 2.4, "#f07aa0");
  return p.texture();
}

/** Poppy's kart: cherry red with a cream bill and roll hoop, on blue tyres. */
export const buildPoppyKart = (detail: 0 | 1 = 0) =>
  buildToyKart(
    {
      body: POPPY.kart,
      bodyDark: POPPY.kartDark,
      trim: POPPY.trim,
      tyre: POPPY.tyre,
      hub: POPPY.hub,
      hubCap: POPPY.hubCap,
      wheel: POPPY.wheel,
      seat: POPPY.seat,
    },
    detail,
    { round: 0.18, bill: 0.6 },
  );

export function buildPoppy(grips: [THREE.Vector3, THREE.Vector3]): CharacterRig {
  const mat = facetMaterial();
  const root = new THREE.Group();
  const torso = new THREE.Group();
  root.add(torso);
  torso.add(
    new THREE.Mesh(
      new Parts()
        .add(gem(1), POPPY.skin, { p: [0, 0.27, 0], s: [0.27, 0.3, 0.24] })
        // A cream bib with a small dark emblem.
        .add(gem(1), POPPY.bib, { p: [0, 0.3, 0.12], s: [0.2, 0.22, 0.14] })
        .add(gem(0), POPPY.stripe, { p: [0, 0.34, 0.255], s: [0.05, 0.035, 0.015] })
        .build(),
      mat,
    ),
  );

  const head = new THREE.Group();
  head.position.set(0, 0.5, 0.02);
  torso.add(head);
  // A big round head.
  const headGeo = new Parts()
    .add(gem(3), POPPY.skin, { p: [0, 0.34, 0.03], s: [0.5, 0.52, 0.47] })
    .build();
  head.add(new THREE.Mesh(headGeo, mat));
  head.add(
    new THREE.Mesh(
      new Parts().add(gem(1), POPPY.nose, { p: [0, 0.26, 0.49], s: 0.055 }).build(),
      mat,
    ),
  );
  const show = paintedFace(head, headGeo, [-0.46, 0.46, 0.02, 0.66], paintFace);
  const setFace: CharacterRig["setFace"] = (mouth, eyes) =>
    show(
      `${mouth}/${eyes === "closed" ? "closed" : mouth === "grin" ? "determined" : mouth === "open" ? "wide" : "open"}`,
    );

  // Long antennae striped purple and black, thickening to club tips.
  const wiggles: CharacterRig["wiggles"] = [];
  for (const side of [-1, 1]) {
    const a = new Parts();
    const bands = 6;
    for (let k = 0; k < bands; k++) {
      const r0 = 0.04 + k * 0.009;
      a.add(new THREE.CylinderGeometry(r0 + 0.009, r0, 0.1, 8), k % 2 ? POPPY.stripe : POPPY.band, {
        p: [0, 0.05 + k * 0.1, 0],
      });
    }
    a.add(gem(1), POPPY.band, { p: [0, 0.68, 0], s: [0.1, 0.14, 0.1] });
    // A tilted mount, so the wiggle (which sets the antenna's own rotation) keeps the
    // outward lean.
    const mount = new THREE.Group();
    mount.position.set(side * 0.2, 0.78, 0);
    mount.rotation.z = -side * 0.28;
    head.add(mount);
    const m = new THREE.Mesh(a.build(), mat);
    mount.add(m);
    wiggles.push({ obj: m, kind: "antenna", side });
  }

  const arm = () =>
    new THREE.Mesh(
      new Parts().add(chamferBox(0.12, 0.12, 1, 0.035), POPPY.skin, { p: [0, 0, 0.5] }).build(),
      mat,
    );
  const arms: [THREE.Mesh, THREE.Mesh] = [arm(), arm()];
  const shoulders: [THREE.Vector3, THREE.Vector3] = [
    new THREE.Vector3(0.23, 0.42, 0.05),
    new THREE.Vector3(-0.23, 0.42, 0.05),
  ];
  arms.forEach((a, i) => {
    a.position.copy(shoulders[i]!);
    torso.add(a);
  });
  const gloves = new Parts();
  for (const g of grips)
    gloves.add(gem(1), POPPY.glove, { p: [g.x, g.y, g.z - 0.01], s: [0.085, 0.08, 0.085] });
  const hands = new THREE.Mesh(gloves.build(), mat);

  const low = new THREE.Mesh(
    new Parts()
      .add(gem(0), POPPY.skin, { p: [0, 0.27, 0], s: [0.27, 0.3, 0.24] })
      .add(gem(1), POPPY.skin, { p: [0, 0.84, 0.05], s: [0.5, 0.52, 0.47] })
      .add(gem(0), POPPY.band, { p: [0.28, 1.6, 0], s: [0.06, 0.34, 0.06], r: [0, 0, -0.28] })
      .add(gem(0), POPPY.band, { p: [-0.28, 1.6, 0], s: [0.06, 0.34, 0.06], r: [0, 0, 0.28] })
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
      bob: 0.03,
      bobHz: 2.8,
      lean: 1.25,
      blinkEvery: 2.2,
      boostFace: "open",
      glanceEvery: 4,
    },
  };
}
