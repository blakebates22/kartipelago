/**
 * The King Croc (Blake, Nov 4: "we also need a big king croc on a throne. it can be
 * standing and still not look like king k rool"): the smugglers' king, holding court on
 * his throne over the Smugglers' Docks. One of the smuggler crocs (folk.ts' croc, folk
 * "sump"), only lean, scarred and old, a great deal bigger (the view's scale), standing:
 *
 *   a crown of driftwood spikes, barnacles crusted on it, a sea-glass stone in front;
 *   a cloak cut from an old sail, its hem ragged, over his shoulders and down his back;
 *   gold teeth among the rest, a gold chain of office, rings of gold in his brows;
 *   scars across his snout; a driftwood staff with a gold charm in his hand.
 *
 * Not King K. Rool: no belly plate, no red cape, no bulging eye, no crown of jewels.
 */
import * as THREE from "three";
import { Build, cone, ellipsoid, gem } from "../racers/kit/shapes";
import { buildFolk } from "./folk";
import { staffGeometry } from "./parts";
import { mesh, type PersonRig } from "./rig";
import { createPersonView, type PersonView } from "./view";

export const CROC_KING_SEED = 1;
/** How big he is against his people (the view's scale). */
export const CROC_KING_SCALE = 3.1;

export function buildCrocKing(): PersonRig {
  const rig = buildFolk("sump", CROC_KING_SEED, "croc");
  // The crown: driftwood spikes in a ring, barnacles, a sea-glass stone.
  const crown = new Build();
  const at: [number, number, number] = [0, 0.29, -0.02];
  for (let k = 0; k < 9; k++) {
    const a = (k / 9) * Math.PI * 2;
    const tall = 0.07 + 0.04 * ((k * 5) % 3);
    crown.add(cone(0.022, tall, 5), k % 2 ? "#8a6a44" : "#6e5232", {
      p: [at[0] + Math.sin(a) * 0.11, at[1] + tall / 2, at[2] + Math.cos(a) * 0.11],
      r: [Math.cos(a) * 0.25, 0, -Math.sin(a) * 0.25],
    });
    crown.add(ellipsoid(6, 4), "#d8d0bc", {
      p: [at[0] + Math.sin(a + 0.35) * 0.12, at[1] + 0.012, at[2] + Math.cos(a + 0.35) * 0.12],
      s: [0.018, 0.014, 0.018],
    });
  }
  crown.add(new THREE.TorusGeometry(0.115, 0.02, 5, 18), "#5a4228", {
    p: at,
    r: [Math.PI / 2, 0, 0],
  });
  crown.add(gem(1), "#4ac8a8", {
    p: [at[0], at[1] + 0.03, at[2] + 0.125],
    s: [0.028, 0.034, 0.02],
  });
  // Gold teeth among the others, gold rings in his brows, scars across his snout.
  for (const [x, z] of [
    [0.06, 0.2],
    [-0.07, 0.32],
    [0.075, 0.44],
  ] as const)
    crown.add(cone(0.013, 0.045, 5), "#e8b830", { p: [x, 0.08, z], r: [Math.PI, 0, 0] });
  for (const sd of [1, -1])
    crown.add(new THREE.TorusGeometry(0.018, 0.005, 4, 10), "#e8b830", {
      p: [sd * 0.1, 0.27, 0.1],
      r: [0, Math.PI / 2, 0],
    });
  for (const [z, x, r] of [
    [0.3, 0.0, 0.7],
    [0.42, 0.02, -0.5],
  ] as const)
    crown.add(new THREE.BoxGeometry(0.16, 0.006, 0.012), "#3a2a1e", {
      p: [x, 0.115, z],
      r: [0, r, 0],
    });
  rig.head.add(mesh(crown));
  // The sail-cloth cloak over his shoulders and down his back, and the chain of office.
  const cloak = new Build();
  cloak.add(
    new THREE.CylinderGeometry(0.27, 0.46, 1.15, 14, 3, true, Math.PI / 2, Math.PI),
    "#c8b896",
    { p: [0, -0.06, -0.03] },
  );
  cloak.add(
    new THREE.CylinderGeometry(0.265, 0.455, 1.14, 14, 3, true, Math.PI / 2, Math.PI).scale(
      -1,
      1,
      1,
    ),
    "#9a8a6c",
    { p: [0, -0.06, -0.03], r: [0, Math.PI, 0] },
  );
  // (its ragged hem: patches of darker sail, a red stripe across it)
  cloak.add(
    new THREE.CylinderGeometry(0.42, 0.46, 0.08, 14, 1, true, Math.PI / 2, Math.PI),
    "#8a2a22",
    { p: [0, -0.5, -0.03] },
  );
  for (let k = 0; k < 6; k++) {
    const a = Math.PI / 2 + ((k + 0.5) / 6) * Math.PI;
    cloak.add(new THREE.BoxGeometry(0.08, 0.1, 0.01), "#8a7a5c", {
      p: [Math.sin(a) * 0.46, -0.66, Math.cos(a) * 0.46 - 0.03],
      r: [0, a, 0.2 * (k % 2 ? 1 : -1)],
    });
  }
  cloak.add(new THREE.TorusGeometry(0.17, 0.018, 5, 18), "#e8b830", {
    p: [0, 0.5, 0.1],
    r: [Math.PI / 2 - 0.3, 0, 0],
  });
  cloak.add(ellipsoid(8, 6), "#e8b830", { p: [0, 0.36, 0.25], s: [0.045, 0.055, 0.02] });
  rig.torso.add(mesh(cloak));
  // The staff: driftwood, a gold charm on its crook.
  const staff = new THREE.Group();
  staff.add(
    new THREE.Mesh(
      staffGeometry(0.62, 0.72, {
        wood: "#7a5a3a",
        dark: "#4a3420",
        charm: "#e8b830",
        cord: "#3a2a1c",
      }),
      new THREE.MeshLambertMaterial({ vertexColors: true }),
    ),
  );
  staff.userData.alwaysHeld = { hand: 0, at: [0.0, 0, 0.04], rot: [0.06, 0, -0.05] };
  staff.userData.foot = 0.62;
  rig.root.add(staff);
  rig.props.staff = { obj: staff, restAt: [0.3, 0.1, 0.3], restRot: [0, 0, 0] };
  rig.root.name = "King Croc";
  return rig;
}

export function createCrocKingView(parent: THREE.Object3D): PersonView {
  return createPersonView(parent, "croc-king", buildCrocKing, {
    scale: CROC_KING_SCALE,
    shadow: 0.7,
    seed: CROC_KING_SEED,
    lod: 400,
  });
}

/** What the King Croc is doing at time t: holding court, by turns pointing his staff,
 * raising it, shaking his head, waving his people on; talking (roaring) now and then. */
export function crocKingCue(t: number): {
  gesture: "point" | "raiseStaff" | "shake" | "wave" | null;
  talk: boolean;
} {
  const k = ((t % 24) + 24) % 24;
  const gesture =
    k < 4
      ? "point"
      : k < 7
        ? null
        : k < 11
          ? "raiseStaff"
          : k < 15
            ? null
            : k < 18
              ? "shake"
              : k < 21
                ? "wave"
                : null;
  return { gesture, talk: (k > 0.5 && k < 3.2) || (k > 8 && k < 10.5) || (k > 15.5 && k < 17.5) };
}
