/**
 * Pixel portraits of the racers for the 2D menus: the real 3D racer (kart and rider)
 * rendered small into an offscreen target, then turned into a pixel-art sprite: colours
 * stepped down to a few levels a channel, hard-edged (no half-transparent pixels) and
 * outlined in a dark line one pixel wide. Drawn on the UI layer at 2x or 3x with no
 * smoothing, they read as hand-placed pixels and always match the models.
 *
 *   const pp = createPixelPortraits(renderer);
 *   const img = pp.draw("tiko", { w: 48, h: 48, view: "head", yaw: 0.4 }, motion);
 *   ui.image(img, x, y, 96, 96, false);
 *
 * Each (racer, size, view) keeps its own canvas, so a menu can show several at once.
 */
import type { Folk } from "../render/villager";
import * as THREE from "three";
import { Racer, type RacerMotion } from "../render/racers/racer";
import type { RacerId } from "../render/racers/designs";
import { createElderView, createGuardView, createLumenView } from "../render/people";
import type { PersonView } from "../render/people/view";
import { createStoryDragon, type DesignId, type StoryDragonView } from "../render/storyDragon";

/** The story's cast who aren't racers, by CAST key (adventure/scenes.ts), and what plays
 * each: a person (Mossback, Lumen in his robe, a guard) or a story dragon. */
const CAST_MODELS: Record<
  string,
  { person?: () => "elder" | "lumen" | "guard" | "sentry"; dragon?: DesignId }
> = {
  elder: { person: () => "elder" },
  lumen: { person: () => "lumen" },
  guard: { person: () => "guard" },
  sentry: { person: () => "sentry" },
  lumen_dragon: { dragon: "lumen" },
  cinderjaw: { dragon: "cinderjaw" },
  rimefang: { dragon: "rimefang" },
  scorchwind: { dragon: "scorchwind" },
  tidewyrm: { dragon: "tidewyrm" },
  king: { dragon: "king" },
};

/** How far back a dragon's portrait stands (its head's size, about: metres at scale 1). */
const HEAD_SIZE: Partial<Record<DesignId, number>> = {
  cinderjaw: 18,
  king: 21,
  lumen: 13,
  lumen_grown: 12,
};

/** Dragons whose faces read best from the front (a broad, short face: Cinderjaw's). */
const FRONTAL = new Set<DesignId>(["cinderjaw"]);

/** Whether a CAST key has a 3D model to portray (the rest are drawn). */
export const hasCastModel = (key: string) => key in CAST_MODELS;

export type PortraitView = "kart" | "head" | "front";

export interface PortraitOpts {
  w: number;
  h: number;
  view: PortraitView;
  /** Turn of the racer about its vertical axis (radians; 0 faces the camera). */
  yaw?: number;
  /** The racer's alternate paint (a champion's cousin). */
  alt?: boolean;
  /** Outline colour ("" for none). */
  outline?: string;
  /** Colour levels a channel (fewer: chunkier pixel art). */
  levels?: number;
  /** Dim it (unselected roster tiles): 0..1. */
  dim?: number;
  /** Fill it with one colour (a locked silhouette). */
  silhouette?: string;
}

interface Slot {
  rt: THREE.WebGLRenderTarget;
  buf: Uint8Array;
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  img: ImageData;
}

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

function hexRgb(h: string): [number, number, number] {
  const m = /^#?([0-9a-f]{6})$/i.exec(h);
  const n = m ? parseInt(m[1]!, 16) : 0;
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export function createPixelPortraits(renderer: THREE.WebGLRenderer) {
  const scene = new THREE.Scene();
  const sun = new THREE.DirectionalLight("#fff4e0", 2.6);
  sun.position.set(3, 6, 5);
  const rim = new THREE.DirectionalLight("#bfe0ff", 1.1);
  rim.position.set(-4, 3, -3);
  // (A light from the camera for the dragons: their hides are dark, their heads big.)
  const fill = new THREE.DirectionalLight("#fff0dc", 0);
  scene.add(sun, rim, fill, fill.target, new THREE.HemisphereLight("#eaf4ff", "#6a5a48", 1.25));
  const camera = new THREE.PerspectiveCamera(28, 1, 0.05, 60);
  const racers = new Map<string, Racer>();
  const people = new Map<string, PersonView>();
  const dragons = new Map<string, StoryDragonView>();
  const slots = new Map<string, Slot>();
  const at = new THREE.Vector3();
  const fwd = new THREE.Vector3();
  const side = new THREE.Vector3();
  const motion = still();
  const head = new THREE.Vector3();
  const clear = new THREE.Color();

  function racerOf(id: RacerId, alt = false) {
    const key = alt ? `${id}:alt` : id;
    let r = racers.get(key);
    if (!r) {
      r = new Racer(id, { seed: id.length * 7 + 3, alt });
      // Close up: always the detailed model.
      r.lod.autoUpdate = false;
      r.lod.levels.forEach((l, i) => (l.object.visible = i === 0));
      scene.add(r.root);
      racers.set(key, r);
    }
    return r;
  }

  function slotOf(key: string, w: number, h: number): Slot {
    let s = slots.get(key);
    if (!s) {
      const rt = new THREE.WebGLRenderTarget(w, h, {
        minFilter: THREE.NearestFilter,
        magFilter: THREE.NearestFilter,
      });
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d")!;
      s = { rt, buf: new Uint8Array(w * h * 4), canvas, ctx, img: ctx.createImageData(w, h) };
      slots.set(key, s);
    }
    return s;
  }

  /** Render the one visible model into a slot and make it pixel art. */
  function shoot(s: Slot, o: PortraitOpts): HTMLCanvasElement {
    // Render small, transparent behind.
    const prevTarget = renderer.getRenderTarget();
    renderer.getClearColor(clear);
    const prevAlpha = renderer.getClearAlpha();
    renderer.setRenderTarget(s.rt);
    renderer.setClearColor(0x000000, 0);
    renderer.clear();
    renderer.render(scene, camera);
    renderer.readRenderTargetPixels(s.rt, 0, 0, o.w, o.h, s.buf);
    renderer.setRenderTarget(prevTarget);
    renderer.setClearColor(clear, prevAlpha);
    // Into pixel art: flip, step the colours, hard alpha, outline.
    const { w, h } = o;
    const d = s.img.data;
    const lv = Math.max(2, o.levels ?? 6);
    const step = 255 / (lv - 1);
    const dim = 1 - Math.min(1, Math.max(0, o.dim ?? 0)) * 0.6;
    const sil = o.silhouette ? hexRgb(o.silhouette) : undefined;
    const line = o.outline === "" ? undefined : hexRgb(o.outline ?? "#1d120a");
    const solid = new Uint8Array(w * h);
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++) {
        const src = ((h - 1 - y) * w + x) * 4;
        const dst = (y * w + x) * 4;
        if (s.buf[src + 3]! < 110) {
          d[dst + 3] = 0;
          continue;
        }
        solid[y * w + x] = 1;
        for (let c = 0; c < 3; c++) {
          const v = sil ? sil[c]! : Math.round(s.buf[src + c]! / step) * step * dim;
          d[dst + c] = Math.max(0, Math.min(255, v));
        }
        d[dst + 3] = 255;
      }
    if (line)
      for (let y = 0; y < h; y++)
        for (let x = 0; x < w; x++) {
          if (solid[y * w + x]) continue;
          const near =
            (x > 0 && solid[y * w + x - 1]) ||
            (x < w - 1 && solid[y * w + x + 1]) ||
            (y > 0 && solid[(y - 1) * w + x]) ||
            (y < h - 1 && solid[(y + 1) * w + x]);
          if (!near) continue;
          const dst = (y * w + x) * 4;
          d[dst] = line[0];
          d[dst + 1] = line[1];
          d[dst + 2] = line[2];
          d[dst + 3] = 255;
        }
    s.ctx.putImageData(s.img, 0, 0);
    return s.canvas;
  }

  /** Only `root` shows. */
  function solo(root: THREE.Object3D) {
    for (const r of racers.values()) r.root.visible = r.root === root;
    for (const p of people.values()) p.root.visible = p.root === root;
    for (const d of dragons.values()) d.root.visible = d.root === root;
  }

  return {
    /**
     * The racer's portrait now (call each frame for a turning, breathing one). `pose`
     * drives the rider's animation (steering, hops, the victory pose).
     */
    draw(
      id: RacerId,
      o: PortraitOpts,
      pose?: Partial<RacerMotion>,
      dt = 0,
      result: number | null = null,
    ): HTMLCanvasElement {
      const s = slotOf(`${id}${o.alt ? ":alt" : ""}:${o.w}x${o.h}:${o.view}`, o.w, o.h);
      const r = racerOf(id, o.alt);
      solo(r.root);
      fill.intensity = 0;
      Object.assign(motion, still(), pose ?? {});
      r.setResult(result, 8);
      r.animate(dt, motion, { x: 0, z: 6 });
      r.flame.visible = (pose?.boostPhase ?? 0) > 0;
      r.core.visible = r.flame.visible;
      r.root.rotation.y = o.yaw ?? 0;
      r.root.updateMatrixWorld(true);
      // Frame it.
      camera.aspect = o.w / o.h;
      if (o.view === "head") {
        // The face, not the neck joint: up and forward from the head's pivot.
        r.rig.head.localToWorld(head.set(0, 0.14, 0.12));
        camera.fov = 24;
        camera.position.set(head.x + 0.5, head.y + 0.14, head.z + 2.65);
        camera.lookAt(head.x, head.y, head.z);
      } else if (o.view === "front") {
        camera.fov = 30;
        camera.position.set(0.0, 2.1, 6.4);
        camera.lookAt(0, 0.85, 0);
      } else {
        camera.fov = 30;
        camera.position.set(3.6, 2.9, 5.0);
        camera.lookAt(0, 0.75, 0);
      }
      camera.updateProjectionMatrix();
      return shoot(s, o);
    },
    /**
     * A story character who isn't a racer (Mossback, Lumen, a guard, a dragon): their
     * head and shoulders, turning a little, blinking and breathing with `t`.
     */
    cast(
      key: string,
      o: { w: number; h: number; levels?: number },
      t: number,
      /** A guard as the scene dressed them (their kingdom's folk and look), so the face
       * in the box is the one on stage. */
      guard?: { folk: Folk; seed: number },
    ): HTMLCanvasElement {
      const m = CAST_MODELS[key];
      const gk = guard ? `${key}|${guard.folk}|${guard.seed}` : key;
      const s = slotOf(`cast:${gk}:${o.w}x${o.h}`, o.w, o.h);
      camera.aspect = o.w / o.h;
      fill.intensity = 0;
      if (m?.person) {
        let p = people.get(gk);
        if (!p) {
          const kind = m.person();
          p =
            kind === "elder"
              ? createElderView(scene)
              : kind === "lumen"
                ? createLumenView(scene)
                : guard
                  ? createGuardView(scene, guard.folk, guard.seed)
                  : createGuardView(scene, kind === "sentry" ? "dragon" : "road", 4);
          people.set(gk, p);
        }
        solo(p.root);
        const yaw = 0.35 + Math.sin(t * 0.7) * 0.12;
        p.update(0, 0, 0, yaw, { look: camera.position }, t);
        p.root.updateMatrixWorld(true);
        p.headPosition(at);
        camera.fov = 26;
        camera.position.set(at.x + 0.45, at.y + 0.08, at.z + 1.75);
        camera.lookAt(at.x, at.y - 0.12, at.z);
      } else if (m?.dragon) {
        let d = dragons.get(key);
        if (!d) {
          d = createStoryDragon(scene, m.dragon, 1);
          d.ground = 0;
          d.effects = false;
          dragons.set(key, d);
        }
        solo(d.root);
        d.root.rotation.y = 0.5 + Math.sin(t * 0.6) * 0.1;
        // (Looking ahead, a little our way: not at wherever the camera was last.)
        const ry = d.root.rotation.y + 0.35;
        d.update("idle", t, t, side.set(Math.sin(ry) * 60, 12, Math.cos(ry) * 60), false);
        d.root.updateMatrixWorld(true);
        d.headFrame(at, fwd);
        side.set(0, 1, 0).cross(fwd).normalize();
        const size = HEAD_SIZE[m.dragon] ?? 10;
        camera.fov = 26;
        // Three-quarters on, a little above: the snout, the horns and an eye (framed a
        // little toward the snout, the head's long that way).
        at.addScaledVector(fwd, size * 0.06);
        camera.position
          .copy(at)
          .addScaledVector(fwd, size * (FRONTAL.has(m.dragon) ? 1.6 : 1.25))
          .addScaledVector(side, size * (FRONTAL.has(m.dragon) ? 0.55 : 1.15))
          .add(new THREE.Vector3(0, size * 0.3, 0));
        camera.lookAt(at);
        fill.position.copy(camera.position);
        fill.target.position.copy(at);
        fill.intensity = 2.1;
      }
      camera.near = 0.05;
      camera.far = 400;
      camera.updateProjectionMatrix();
      return shoot(s, { w: o.w, h: o.h, view: "head", levels: o.levels ?? 8 });
    },
    dispose() {
      for (const p of people.values()) p.dispose();
      people.clear();
      for (const d of dragons.values()) d.dispose();
      dragons.clear();
      for (const s of slots.values()) s.rt.dispose();
      slots.clear();
      for (const r of racers.values()) r.root.removeFromParent();
      racers.clear();
    },
  };
}

export type PixelPortraits = ReturnType<typeof createPixelPortraits>;
