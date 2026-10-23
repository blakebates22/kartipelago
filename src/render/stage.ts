import * as THREE from "three";
import { tuning } from "../core/tuning";
import type { TrackLook } from "../world/trackPackage";
import { applyRetroLook } from "./retro";
import { createSkyDome, type SkyDome } from "./skyDome";

/**
 * Render resolution: a fixed number of lines (the soft, low-resolution picture of the
 * era, smoothed up to the window), or 0 for the screen's own resolution.
 */
export function resolutionScale(lines: number, cssHeight: number, dpr: number) {
  if (!lines) return 1;
  const full = Math.max(1, cssHeight) * Math.min(dpr, 2);
  return Math.min(1, lines / full);
}

/** Owns the renderer, scene and camera, and keeps them sized to the window. */
export function createStage(container: HTMLElement) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  // No shadow maps: karts and creatures carry simple blob shadows instead, like the
  // era's games. (A sun shadow map over a small area round the kart swam, popped in at
  // its edges and broke on high ground; blobs stay steady and cost nothing.)
  renderer.shadowMap.enabled = false;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(tuning.camera.fov, 1, 0.1, 2000);

  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(8, 14, 6);
  const hemi = new THREE.HemisphereLight(0xdff6ff, 0x335533, 1.1);
  scene.add(sun, sun.target, hemi);
  const defaults = {
    sun: sun.color.clone(),
    sunIntensity: sun.intensity,
    sunOffset: sun.position.clone(),
    hemiSky: hemi.color.clone(),
    hemiGround: hemi.groundColor.clone(),
    hemiIntensity: hemi.intensity,
  };
  const sunOffset = defaults.sunOffset.clone();

  /** Keep the sun's small shadow area centred on the action. */
  const followSun = (x: number, z: number) => {
    sun.position.set(x + sunOffset.x, sunOffset.y, z + sunOffset.z);
    sun.target.position.set(x, 0, z);
  };

  let lines = 360;
  let env: TrackLook = {};
  let dome: SkyDome | undefined;
  let lastFrame = performance.now();

  /** A track's sky, sun and fog; an empty look is the game's default. */
  const applyEnvironment = () => {
    const s = env.sun;
    sun.color.set(s ? s.color : defaults.sun);
    sun.intensity = s ? s.intensity : defaults.sunIntensity;
    if (s) {
      sunOffset
        .set(...s.direction)
        .normalize()
        .multiplyScalar(defaults.sunOffset.length());
    } else sunOffset.copy(defaults.sunOffset);
    const a = env.ambient;
    hemi.color.set(a ? a.sky : defaults.hemiSky);
    hemi.groundColor.set(a ? a.ground : defaults.hemiGround);
    hemi.intensity = a ? a.intensity : defaults.hemiIntensity;
    // A painted sky (sun and clouds) if the track has one.
    dome?.dispose();
    dome = undefined;
    if (env.skyDome) {
      dome = createSkyDome(env.skyDome, s?.direction);
      scene.add(dome.group);
    }
  };

  // The late-90s look: authentic or enhanced resolution, sky colour and distance fog.
  scene.background = new THREE.Color(tuning.world.skyColor);
  let lookKey = "";
  const updateLook = () => {
    const l = tuning.look;
    const scale = resolutionScale(lines, container.clientHeight, window.devicePixelRatio);
    const sky = env.sky ?? tuning.world.skyColor;
    const key = `${scale}|${l.fogNear}|${l.fogFar}|${sky}|${JSON.stringify(env.fog)}`;
    if (key === lookKey) return false;
    lookKey = key;
    (scene.background as THREE.Color).set(sky);
    const fog = env.fog;
    applyRetroLook(renderer, scene, {
      resolutionScale: scale,
      fogNear: fog ? fog.near : l.fogNear,
      fogFar: fog ? fog.far : l.fogFar,
    });
    if (fog && scene.fog instanceof THREE.Fog) {
      if (fog.enabled) scene.fog.color.set(fog.color);
      else scene.fog = null;
    }
    return true;
  };

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = container;
    updateLook();
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
  };
  window.addEventListener("resize", resize);
  resize();

  return {
    renderer,
    scene,
    camera,
    followSun,
    get lines() {
      return lines;
    },
    /** Lines to render (240, 360, 480), or 0 for full resolution. */
    setResolution(next: number) {
      lines = next;
      resize();
    },
    resize,
    /** Draw some other scene (a menu's) with this renderer and the same look. */
    renderOther(other: THREE.Scene, cam: THREE.PerspectiveCamera) {
      if (updateLook()) resize();
      const a = container.clientWidth / Math.max(1, container.clientHeight);
      if (Math.abs(cam.aspect - a) > 1e-3) {
        cam.aspect = a;
        cam.updateProjectionMatrix();
      }
      renderer.render(other, cam);
    },
    setEnvironment(look: TrackLook | undefined) {
      env = look ?? {};
      applyEnvironment();
      resize();
    },
    render: () => {
      // Live tuning edits to the look apply at once.
      if (updateLook()) resize();
      const now = performance.now();
      dome?.update(camera, Math.min(0.1, (now - lastFrame) / 1000));
      lastFrame = now;
      renderer.render(scene, camera);
    },
  };
}

export type Stage = ReturnType<typeof createStage>;
