/**
 * Debug view of a course's checkpoint gates: translucent rectangles where the invisible
 * gates are, with an arrow showing which way they're crossed, coloured by what they
 * mean to the player right now:
 *
 *   green   the next checkpoint you must cross
 *   blue    the one you passed last (where a respawn puts you)
 *   orange  gates on alternate routes (shortcuts)
 *   white   the rest
 *
 * Shown only in debug mode (G toggles it). Never part of normal play.
 */
import * as THREE from "three";
import type { Checkpoint, Progression } from "../race/checkpoints";

const COLORS = { next: 0x40ff70, last: 0x4aa8ff, alt: 0xffa040, other: 0xffffff };

export interface CheckpointView {
  visible: boolean;
  update(r: Progression): void;
  dispose(): void;
}

export function createCheckpointView(parent: THREE.Object3D, course: Checkpoint[]): CheckpointView {
  const group = new THREE.Group();
  group.name = "checkpoint gates";
  group.visible = false;
  parent.add(group);
  const geos: THREE.BufferGeometry[] = [];
  const meshes: {
    mesh: THREE.Mesh;
    mat: THREE.MeshBasicMaterial;
    edge: THREE.LineBasicMaterial;
    tip: THREE.MeshBasicMaterial;
    index: number;
    alt: boolean;
    id: string;
  }[] = [];
  const arrowGeo = new THREE.ConeGeometry(0.6, 2.4, 4);
  arrowGeo.rotateX(Math.PI / 2); // point along +z
  geos.push(arrowGeo);
  for (const c of course)
    for (const g of c.gates) {
      const w = g.left + g.right;
      const h = g.height + g.below;
      const geo = new THREE.PlaneGeometry(w, h);
      geos.push(geo);
      const mat = new THREE.MeshBasicMaterial({
        color: COLORS.other,
        transparent: true,
        opacity: 0.22,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      // The plane faces +z by default: turn it to face the gate's forward.
      mesh.rotation.y = g.heading;
      const mid = (g.right - g.left) / 2;
      // Right is (-fz, fx).
      mesh.position.set(g.x - g.fz * mid, g.y - g.below + h / 2, g.z + g.fx * mid);
      // A solid outline, so the gate reads clearly even against a bright sky.
      const edgeGeo = new THREE.EdgesGeometry(geo);
      geos.push(edgeGeo);
      const edge = new THREE.LineBasicMaterial({ color: COLORS.other });
      mesh.add(new THREE.LineSegments(edgeGeo, edge));
      const tip = new THREE.MeshBasicMaterial({ color: COLORS.other });
      const arrow = new THREE.Mesh(arrowGeo, tip);
      arrow.position.set(0, -h / 2 + g.below + 1.2, 1.2);
      mesh.add(arrow);
      mesh.renderOrder = 3;
      group.add(mesh);
      meshes.push({ mesh, mat, edge, tip, index: c.index, alt: g.route !== "main", id: g.id });
    }
  return {
    get visible() {
      return group.visible;
    },
    set visible(v: boolean) {
      group.visible = v;
    },
    update(r) {
      if (!group.visible) return;
      for (const m of meshes) {
        const color =
          m.index === r.next
            ? COLORS.next
            : m.id === r.lastGate.id
              ? COLORS.last
              : m.alt
                ? COLORS.alt
                : COLORS.other;
        m.mat.color.setHex(color);
        m.edge.color.setHex(color);
        m.tip.color.setHex(color);
        m.mat.opacity = m.index === r.next ? 0.45 : 0.25;
      }
    },
    dispose() {
      group.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of meshes) {
        m.mat.dispose();
        m.edge.dispose();
        m.tip.dispose();
      }
    },
  };
}
