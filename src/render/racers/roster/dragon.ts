/**
 * The dragons (Adventure's bosses): a PLACEHOLDER racer, not playable. Blake's "Wildbolt"
 * sheet is the direction (one stocky horned dragon with a pale belly in bold colour
 * variants); until the real model is built, this is Rex's body in dragon colours with
 * horns, a ridge of spikes and folded wings (they spread in the air, like Zephyr's), on
 * Rex's kart.
 *
 * One palette per dragon (DRAGON_PALETTES), picked by the session (`palette`).
 */
import * as THREE from "three";
import { Build, card, horn, loft } from "../kit/shapes";
import { skinMaterial } from "../kit/paint";
import type { RiderRig } from "../kit/rig";
import type { BodyKit } from "../kit/chassis";
import { REX } from "./rex";
import type { RacerBuild } from "./types";

type RexPalette = (typeof REX.palettes)["main"];

type DragonPalette = RexPalette & { wing: string; wingDark: string; horn: string };

/** A dragon's colours: body, darker body, belly, wing membrane, horns, kart accent. */
function dragon(
  skin: string,
  dark: string,
  belly: string,
  wing: string,
  hornC: string,
  accent: string,
): DragonPalette {
  const m = REX.palettes.main;
  return {
    ...m,
    skin,
    skinDark: dark,
    spot: dark,
    belly,
    // Rex's leaf wreath and lei become a frill of the dragon's own scales; the goggles,
    // scarf and straps take the dragon's colours.
    leaf: dark,
    leafRib: skin,
    scarf: accent,
    gold: hornC,
    lens: "#ffd84a",
    leather: dark,
    leatherDark: "#1a1014",
    // The kart: a low racer in the dragon's colours.
    char: dark,
    charLight: skin,
    banner: accent,
    lava: "#ffb040",
    bone: belly,
    boneDark: hornC,
    wing,
    wingDark: dark,
    horn: hornC,
  };
}

export const DRAGON_PALETTES: Record<string, DragonPalette> = {
  cinderjaw: dragon("#c8282a", "#6a1416", "#f2d6a8", "#f0c890", "#2a1a1a", "#f0c890"),
  rimefang: dragon("#e8eef6", "#5a7aa8", "#f8f4ec", "#9ab8e0", "#2a3a5a", "#3a6ac8"),
  scorchwind: dragon("#c8a070", "#6a4a2a", "#f0dcb0", "#e0c898", "#3a2a1a", "#e0b060"),
  tidewyrm: dragon("#1f6a6a", "#0e3a40", "#9ad8c8", "#5ab8a0", "#0e2a2a", "#3ad0c0"),
  king: dragon("#3a2a4a", "#16101e", "#b89ad8", "#7a4ac8", "#e8b030", "#9a5ae8"),
};

function wings(c: DragonPalette, torso: THREE.Object3D): THREE.Object3D[] {
  const mat = skinMaterial();
  const outline: [number, number][] = [
    [0, 0.08],
    [0.3, 0.16],
    [0.62, 0.12],
    [0.9, -0.1],
    [0.62, -0.08],
    [0.48, -0.22],
    [0.3, -0.12],
    [0.14, -0.26],
    [0, -0.16],
  ];
  const wing = new THREE.Color(c.wing);
  const dark = new THREE.Color(c.wingDark);
  const geo = new Build()
    .add(card(outline), (p) => wing.clone().lerp(dark, Math.min(1, Math.max(0, -p.y * 2.5 + 0.2))))
    .addColored(
      loft(
        [
          { at: [0, 0.08, 0], rx: 0.035, ry: 0.035, color: c.skinDark },
          { at: [0.3, 0.16, 0], rx: 0.03, ry: 0.03, color: c.skinDark },
          { at: [0.62, 0.12, 0], rx: 0.022, ry: 0.022, color: c.skinDark },
          { at: [0.9, -0.1, 0], rx: 0.006, ry: 0.006, color: c.horn },
        ],
        { sides: 5, capStart: true, capEnd: true, up: [0, 0, 1] },
      ),
    )
    .build();
  const out: THREE.Object3D[] = [];
  for (const side of [1, -1]) {
    const w = new THREE.Group();
    w.position.set(side * 0.16, 0.4, -0.12);
    const m = new THREE.Mesh(
      side === 1 ? geo : new Build().addColored(geo.clone(), { mirror: true }).build(),
      mat,
    );
    w.add(m);
    w.userData.fold = new THREE.Euler(0.2, side * 1.25, side * 0.75);
    w.userData.open = new THREE.Euler(-0.45, side * 0.2, side * 0.45);
    w.rotation.copy(w.userData.fold as THREE.Euler);
    torso.add(w);
    out.push(w);
  }
  return out;
}

function rider(c: DragonPalette): RiderRig {
  const rig = REX.rider(c);
  rig.root.name = "dragon";
  const mat = skinMaterial();
  // Swept-back horns, a smaller pair beside them, and a ridge of spikes down the back.
  const h = new Build();
  for (const s of [1, -1]) {
    h.addColored(
      horn([s * 0.12, 0.33, 0.02], [s * 0.2, 0.52, -0.22], 0.05, c.horn, [0, 0.03, -0.02], 6),
    );
    h.addColored(horn([s * 0.2, 0.26, 0.06], [s * 0.3, 0.34, -0.1], 0.03, c.horn, [0, 0, 0], 5));
  }
  rig.head.add(new THREE.Mesh(h.build(), mat));
  const spikes = new Build();
  for (let k = 0; k < 4; k++)
    spikes.addColored(
      horn(
        [0, 0.44 - k * 0.11, -0.12 - k * 0.03],
        [0, 0.5 - k * 0.11, -0.24 - k * 0.03],
        0.035,
        c.horn,
        [0, 0, 0],
        4,
      ),
    );
  rig.torso.add(new THREE.Mesh(spikes.build(), mat));
  rig.wings = wings(c, rig.torso);
  return rig;
}

function kart(c: DragonPalette): BodyKit {
  return REX.kart(c);
}

export const DRAGON: RacerBuild<DragonPalette> = {
  palettes: { main: DRAGON_PALETTES.cinderjaw!, alt: DRAGON_PALETTES.king! },
  kart,
  rider,
};
