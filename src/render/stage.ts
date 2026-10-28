import * as THREE from "three";
import { tuning } from "../core/tuning";
import type { TrackLook } from "../world/trackPackage";
import { applyRetroLook } from "./retro";
import { createSkyDome, type SkyDome, type SkyDomeSpec } from "./skyDome";
import type { Air } from "../overworld/air";

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
  /** The overworld's air, blended from its areas' looks (overworld/air.ts): over the
   * track's own sun, light, sky colour and fog while it's set. */
  let air: Air | undefined;
  /** The overworld's areas' painted skies: the nearer one, the other faded over it. */
  const skies = new Map<SkyDomeSpec, SkyDome>();
  let skiesOn = false;

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

  const applyAir = () => {
    if (!air) return;
    (scene.background as THREE.Color).setRGB(...air.sky);
    if (scene.fog instanceof THREE.Fog) {
      scene.fog.color.setRGB(...air.fog.color);
      scene.fog.near = air.fog.near;
      scene.fog.far = air.fog.far;
    }
    sun.color.setRGB(...air.sun.color);
    sun.intensity = air.sun.intensity;
    sunOffset
      .set(...air.sun.direction)
      .normalize()
      .multiplyScalar(defaults.sunOffset.length());
    hemi.color.setRGB(...air.ambient.sky);
    hemi.groundColor.setRGB(...air.ambient.ground);
    hemi.intensity = air.ambient.intensity;
  };
  const clearSkies = () => {
    for (const d of skies.values()) d.dispose();
    skies.clear();
    skiesOn = false;
    if (dome) dome.group.visible = true;
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
      air = undefined;
      clearSkies();
      lookKey = "";
      applyEnvironment();
      resize();
    },
    /** The overworld's blended air (undefined: the track's own look again). */
    setAir(next: Air | undefined) {
      air = next;
      if (!air) {
        lookKey = "";
        applyEnvironment();
        updateLook();
      } else applyAir();
    },
    /**
     * The overworld's painted skies: `under` (the nearer area's) and `over` faded over it
     * by `t`. Each is made once and kept until the track changes (or `clear`).
     */
    setSkies(
      under: { spec: SkyDomeSpec; sun?: [number, number, number] } | undefined,
      over?: { spec: SkyDomeSpec; sun?: [number, number, number]; t: number },
    ) {
      const get = (x: { spec: SkyDomeSpec; sun?: [number, number, number] }) => {
        let d = skies.get(x.spec);
        if (!d) {
          d = createSkyDome(x.spec, x.sun);
          skies.set(x.spec, d);
          scene.add(d.group);
        }
        return d;
      };
      if (!under) return clearSkies();
      skiesOn = true;
      if (dome) dome.group.visible = false;
      const a = get(under);
      const b = over && over.spec !== under.spec && over.t > 0.002 ? get(over) : undefined;
      for (const d of skies.values()) d.group.visible = d === a || d === b;
      a.fade(1, false);
      b?.fade(over!.t, true);
    },
    render: () => {
      // Live tuning edits to the look apply at once.
      if (updateLook()) {
        resize();
        applyAir();
      }
      const now = performance.now();
      const step = Math.min(0.1, (now - lastFrame) / 1000);
      if (skiesOn) for (const d of skies.values()) if (d.group.visible) d.update(camera, step);
      dome?.update(camera, Math.min(0.1, (now - lastFrame) / 1000));
      lastFrame = now;
      renderer.render(scene, camera);
    },
  };
}

export type Stage = ReturnType<typeof createStage>;
