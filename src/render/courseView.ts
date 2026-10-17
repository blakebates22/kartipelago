import * as THREE from "three";
import type { Course, CourseConfig } from "../world/course";

/** Chevrons pointing along the pad (toward +Z once laid flat). */
function chevronTexture() {
  const w = 64;
  const h = 128;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const g = canvas.getContext("2d")!;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, w, h);
  g.strokeStyle = "#e85d04";
  g.lineWidth = 9;
  g.lineJoin = "round";
  for (let i = 0; i < 3; i++) {
    const y = 18 + i * 38;
    g.beginPath();
    g.moveTo(10, y);
    g.lineTo(w / 2, y + 22);
    g.lineTo(w - 10, y);
    g.stroke();
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return tex;
}

/** Meshes for the practice course. Reads course state each frame; never changes it. */
export function createCourseView(scene: THREE.Scene, course: Course, cfg: CourseConfig) {
  const padMat = new THREE.MeshStandardMaterial({ map: chevronTexture(), roughness: 0.6 });
  const padGeo = new THREE.PlaneGeometry(cfg.padWidth, cfg.padLength).rotateX(-Math.PI / 2);
  for (const pad of course.data.pads) {
    const mesh = new THREE.Mesh(padGeo, padMat);
    mesh.position.set(pad.x, 0.02, pad.z);
    mesh.rotation.y = pad.heading;
    mesh.receiveShadow = true;
    scene.add(mesh);
  }

  const orbMat = new THREE.MeshStandardMaterial({
    flatShading: true,
    emissiveIntensity: 0.35,
  });
  const orbGeo = new THREE.IcosahedronGeometry(0.75, 1);
  const orbs = course.pickups.map((p) => {
    const mesh = new THREE.Mesh(orbGeo, orbMat);
    mesh.position.set(p.x, 1.4, p.z);
    mesh.castShadow = true;
    scene.add(mesh);
    return mesh;
  });

  return {
    render(time: number, colors: { pickupColor: string; padColor: string }) {
      orbMat.color.set(colors.pickupColor);
      orbMat.emissive.set(colors.pickupColor);
      padMat.color.set(colors.padColor);
      course.pickups.forEach((p, i) => {
        const orb = orbs[i]!;
        orb.visible = p.respawnIn === 0;
        orb.position.y = 1.4 + Math.sin(time * 2 + i) * 0.2;
        orb.rotation.y = time + i;
      });
    },
  };
}
