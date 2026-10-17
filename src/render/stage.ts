import * as THREE from "three";
import { tuning } from "../core/tuning";

/** Owns the renderer, scene and camera, and keeps them sized to the window. */
export function createStage(container: HTMLElement) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(tuning.camera.fov, 1, 0.1, 2000);

  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(8, 14, 6);
  sun.castShadow = true;
  scene.add(sun, new THREE.HemisphereLight(0xdff6ff, 0x335533, 1.1));

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = container;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
  };
  window.addEventListener("resize", resize);
  resize();

  return { renderer, scene, camera, render: () => renderer.render(scene, camera) };
}

export type Stage = ReturnType<typeof createStage>;
