/**
 * The racer lab (developer tool): every racer from a few angles in one picture, for
 * comparing designs. Load it from the browser console on a ?debug page:
 *
 *   const lab = await import("/src/debug/racerLab.ts");
 *   const url = lab.racerSheet(kp.stage.renderer, { v2: true });  // a PNG data URL
 *
 * Each row is a racer: front three-quarter, side, from behind (the race camera), a close
 * look at the face, and the select screen's pixel tile and pixel kart.
 */
import * as THREE from "three";
import { Racer, type RacerMotion } from "../render/racers/racer";
import { DESIGNS, RACER_IDS, type RacerId } from "../render/racers/designs";
import { createPixelPortraits } from "../ui/pixelPortraits";

const still = (): RacerMotion => ({
  speed: 0,
  steer: 0,
  driftDir: 0,
  slip: 0,
  grounded: true,
  throttle: false,
  boostPhase: 0,
  boostEnhanced: false,
  boostLeft: 0,
  impactTier: 0,
  impactSpeed: 0,
  spinTime: 0,
});

type View = { label: string; cam: [number, number, number]; look: [number, number, number]; fov: number; face?: boolean };
// Face views: `cam` is the offset from the head.

const ALL_VIEWS: View[] = [
  { label: "3/4 FRONT", cam: [3.4, 2.4, 4.6], look: [0, 0.9, 0], fov: 32 },
  { label: "SIDE", cam: [6.2, 1.5, 0], look: [0, 0.85, 0], fov: 30 },
  { label: "RACE CAMERA", cam: [0, 2.6, -6.4], look: [0, 1.0, 1.5], fov: 40 },
  { label: "FACE 3/4", cam: [1.3, 0.25, 2.6], look: [0, 0, 0], fov: 26, face: true },
  { label: "FACE", cam: [0, 0.15, 3.0], look: [0, 0, 0], fov: 26, face: true },
];

export function racerSheet(
  renderer: THREE.WebGLRenderer,
  opts: {
    v2?: boolean;
    ids?: RacerId[];
    cell?: [number, number];
    pose?: Partial<RacerMotion>;
    /** Only these views (by label), e.g. ["FACE 3/4", "FACE"]. */
    views?: string[];
    /** Leave out the pixel column. */
    noPixels?: boolean;
  } = {},
): string {
  const VIEWS = opts.views ? ALL_VIEWS.filter((v) => opts.views!.includes(v.label)) : ALL_VIEWS;
  const ids = opts.ids ?? [...RACER_IDS];
  const [cw, ch] = opts.cell ?? [300, 220];
  const pix = opts.noPixels ? 0 : 150;
  const out = document.createElement("canvas");
  out.width = VIEWS.length * cw + pix;
  out.height = ids.length * ch;
  const g = out.getContext("2d")!;
  g.fillStyle = "#20243a";
  g.fillRect(0, 0, out.width, out.height);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#8fc6e8");
  const sun = new THREE.DirectionalLight("#fff0d2", 2.4);
  sun.position.set(4, 8, 6);
  scene.add(sun, new THREE.HemisphereLight("#e2f4ff", "#6a7a4a", 1.25));
  const floor = new THREE.Mesh(new THREE.CircleGeometry(6, 32).rotateX(-Math.PI / 2), new THREE.MeshLambertMaterial({ color: "#7fae5a" }));
  scene.add(floor);
  const camera = new THREE.PerspectiveCamera(30, cw / ch, 0.05, 80);
  const rt = new THREE.WebGLRenderTarget(cw, ch);
  const buf = new Uint8Array(cw * ch * 4);
  const img = g.createImageData(cw, ch);
  const head = new THREE.Vector3();
  const pp = createPixelPortraits(renderer);
  const prev = renderer.getRenderTarget();
  ids.forEach((id, row) => {
    const r = new Racer(id, { seed: 5, v2: opts.v2 });
    r.lod.autoUpdate = false;
    r.lod.levels.forEach((l, i) => (l.object.visible = i === 0));
    scene.add(r.root);
    const m = { ...still(), ...(opts.pose ?? {}) };
    for (let k = 0; k < 30; k++) r.animate(1 / 30, m, { x: 0, z: 6 });
    // Face the camera squarely (no idle glances) for a fair comparison.
    for (const o of [r.rig.head, r.rig.neck, r.rig.torso]) {
      const base = o?.userData.base as THREE.Euler | undefined;
      if (o && base) o.rotation.copy(base);
      else if (o === r.rig.torso) o.rotation.set(0, 0, 0);
    }
    r.root.updateMatrixWorld(true);
    VIEWS.forEach((v, col) => {
      if (v.face) {
        r.rig.head.getWorldPosition(head);
        head.y += 0.12;
        head.z += 0.12;
        camera.position.set(head.x + v.cam[0], head.y + v.cam[1], head.z + v.cam[2]);
        camera.lookAt(head.x, head.y, head.z);
      } else {
        camera.position.set(...v.cam);
        camera.lookAt(...v.look);
      }
      camera.fov = v.fov;
      camera.updateProjectionMatrix();
      renderer.setRenderTarget(rt);
      renderer.render(scene, camera);
      renderer.readRenderTargetPixels(rt, 0, 0, cw, ch, buf);
      for (let y = 0; y < ch; y++) img.data.set(buf.subarray((ch - 1 - y) * cw * 4, (ch - y) * cw * 4), y * cw * 4);
      g.putImageData(img, col * cw, row * ch);
      g.fillStyle = "#ffffff";
      g.font = "12px monospace";
      g.fillText(`${DESIGNS[id].name} ${opts.v2 ? "v2" : "now"} - ${v.label}`, col * cw + 6, row * ch + 14);
    });
    renderer.setRenderTarget(prev);
    r.root.removeFromParent();
    if (opts.noPixels) return;
    // The pixel tile and kart, as the select screen draws them.
    g.imageSmoothingEnabled = false;
    const tile = pp.draw(id, { w: 40, h: 40, view: "head", yaw: 0.35, levels: 8 }, undefined, 0, null, opts.v2);
    g.drawImage(tile, VIEWS.length * cw + 15, row * ch + 10, 120, 120);
    const kart = pp.draw(id, { w: 72, h: 60, view: "kart", yaw: 0.6, levels: 8 }, undefined, 0, null, opts.v2);
    g.drawImage(kart, VIEWS.length * cw + 15, row * ch + 132, 96, 80);
  });
  pp.dispose();
  rt.dispose();
  return out.toDataURL("image/png");
}
