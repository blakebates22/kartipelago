/**
 * Shared bits for the v2 racers: each keeps its v1 body, arms and tail (the rig the
 * animator knows), and gets a new head and a sleek kart.
 */
import * as THREE from "three";
import type { RiderRig } from "../../kit/rig";

/** Empty the rig's head (skull, crest, eyes, brows, jaw) and drop wiggles that lived in it. */
export function clearHead(rig: RiderRig) {
  const inHead = (o: THREE.Object3D) => {
    for (let p: THREE.Object3D | null = o; p; p = p.parent) if (p === rig.head) return true;
    return false;
  };
  rig.wiggles = rig.wiggles.filter((w) => !inHead(w.obj));
  for (const c of [...rig.head.children]) {
    rig.head.remove(c);
    c.traverse((o) => {
      if (o instanceof THREE.Mesh) o.geometry.dispose();
    });
  }
  rig.face.jaw = null;
  rig.face.eyes = [];
  rig.face.brows = [];
}

/** Remove the torso's direct meshes that match (to swap out a body part). */
export function dropMeshes(parent: THREE.Object3D, keep: (m: THREE.Mesh, i: number) => boolean) {
  parent.children
    .filter((c): c is THREE.Mesh => c instanceof THREE.Mesh)
    .forEach((m, i) => {
      if (!keep(m, i)) parent.remove(m);
    });
}
