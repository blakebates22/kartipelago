import * as THREE from "three";
import type { Driver } from "../ai/driver";

/**
 * The rivals' minds, drawn in the world (`?aidebug`, dev server only): over each rival
 * a tag with its name, what it's doing (racing, overtake, defend, dodge, pad, recover...),
 * its speed and whether it's drifting, and a line from the kart to the point it's
 * steering for, coloured by what it's doing.
 */
export function createAiDebug(parent: THREE.Object3D) {
  const root = new THREE.Group();
  root.name = "ai debug";
  parent.add(root);
  const tags = new Map<
    number,
    {
      sprite: THREE.Sprite;
      ctx: CanvasRenderingContext2D;
      tex: THREE.CanvasTexture;
      line: THREE.Line;
      text: string;
    }
  >();

  const COLORS: Record<string, string> = {
    racing: "#9fe870",
    overtake: "#ffb347",
    follow: "#ffe066",
    defend: "#ff6b6b",
    dodge: "#c77dff",
    pad: "#4dd2ff",
    recover: "#ff4d4d",
    turnaround: "#ff4d4d",
    grid: "#cccccc",
  };

  function tagFor(i: number) {
    let t = tags.get(i);
    if (t) return t;
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext("2d")!;
    const tex = new THREE.CanvasTexture(canvas);
    tex.magFilter = THREE.NearestFilter;
    const sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true }),
    );
    sprite.scale.set(4, 1, 1);
    sprite.renderOrder = 999;
    const geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(),
      new THREE.Vector3(),
    ]);
    const line = new THREE.Line(
      geo,
      new THREE.LineBasicMaterial({ color: "#ffffff", depthTest: false }),
    );
    line.renderOrder = 998;
    root.add(sprite, line);
    t = { sprite, ctx, tex, line, text: "" };
    tags.set(i, t);
    return t;
  }

  return {
    /** Each rival: index, name, its driver, and where its kart is drawn. */
    update(
      rivals: {
        i: number;
        name: string;
        driver: Driver;
        at: THREE.Vector3;
        speed: number;
        drifting: boolean;
      }[],
    ) {
      for (const r of rivals) {
        const t = tagFor(r.i);
        const state = r.driver.state;
        const text = `${r.name} ${state}${r.drifting ? " ~drift" : ""} ${(r.speed * 3.6).toFixed(0)}`;
        if (text !== t.text) {
          t.text = text;
          const c = t.ctx;
          c.clearRect(0, 0, 256, 64);
          c.fillStyle = "rgba(0,0,0,0.6)";
          c.fillRect(0, 8, 256, 48);
          c.fillStyle = COLORS[state] ?? "#ffffff";
          c.font = "bold 22px monospace";
          c.textAlign = "center";
          c.fillText(text, 128, 40);
          t.tex.needsUpdate = true;
        }
        t.sprite.position.set(r.at.x, r.at.y + 3.2, r.at.z);
        const pos = t.line.geometry.getAttribute("position") as THREE.BufferAttribute;
        pos.setXYZ(0, r.at.x, r.at.y + 0.8, r.at.z);
        pos.setXYZ(1, r.driver.debug.tx, r.at.y + 0.8, r.driver.debug.tz);
        pos.needsUpdate = true;
        (t.line.material as THREE.LineBasicMaterial).color.set(COLORS[state] ?? "#ffffff");
      }
    },
    dispose() {
      parent.remove(root);
      for (const t of tags.values()) {
        t.tex.dispose();
        (t.sprite.material as THREE.SpriteMaterial).dispose();
        t.line.geometry.dispose();
        (t.line.material as THREE.Material).dispose();
      }
    },
  };
}
