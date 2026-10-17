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
  scene.add(sun, sun.target, new THREE.HemisphereLight(0xdff6ff, 0x335533, 1.1));
  const sunOffset = sun.position.clone();

  /** Keep the sun's small shadow area centred on the action. */
  const followSun = (x: number, z: number) => {
    sun.position.set(x + sunOffset.x, sunOffset.y, z + sunOffset.z);
    sun.target.position.set(x, 0, z);
  };

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = container;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
  };
  window.addEventListener("resize", resize);
  resize();

  return { renderer, scene, camera, followSun, render: () => renderer.render(scene, camera) };
}

export type Stage = ReturnType<typeof createStage>;
