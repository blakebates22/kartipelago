/**
 * The soft late-90s console look, applied to the whole picture:
 * - render at a reduced resolution and let the browser scale it up with smoothing, for
 *   the gently filtered image of the era (and it's cheaper to draw);
 * - distance fog in the sky colour, so the far world fades softly instead of ending.
 */
import * as THREE from "three";

export interface RetroLook {
  /** Fraction of the screen's resolution to render at (1 = full, sharp). */
  resolutionScale: number;
  fogNear: number;
  fogFar: number;
}

export function applyRetroLook(renderer: THREE.WebGLRenderer, scene: THREE.Scene, look: RetroLook) {
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2) * look.resolutionScale);
  renderer.domElement.style.imageRendering = "auto";
  const sky =
    scene.background instanceof THREE.Color ? scene.background : new THREE.Color("#8ecae6");
  if (scene.fog instanceof THREE.Fog) {
    scene.fog.color.copy(sky);
    scene.fog.near = look.fogNear;
    scene.fog.far = look.fogFar;
  } else {
    scene.fog = new THREE.Fog(sky.clone(), look.fogNear, look.fogFar);
  }
}
