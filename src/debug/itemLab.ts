/**
 * The item lab (developer tool): prototype sheets for item art. On a ?debug page:
 *
 *   const lab = await import("/src/debug/itemLab.ts");
 *   lab.balloonSheet(kp.stage.renderer); // a PNG data URL: every balloon in every wrap
 *   lab.iconSheet(); // the oil slick and mine icon styles, big and in the item box
 */
import * as THREE from "three";
import type { BalloonColor } from "../items/inventory";
import { wrapMaterial, type WrapStyle } from "../render/balloonWraps";
import { BALLOON_COLORS, markingsTexture } from "../render/itemView";
import { ICON_STYLE, clearIconCache, itemIcon } from "../ui/itemIcons";
import { drawText } from "../ui/font";

const COLORS: BalloonColor[] = ["red", "blue", "green", "yellow", "rainbow"];
const STYLES: [WrapStyle, string][] = [
  [0, "NOW"],
  [1, "1 PAINTED BANDS"],
  [2, "2 HOT-AIR GORES"],
  [3, "3 CAVE GLYPHS"],
  [4, "4 SUNBURST"],
];

function classic(color: BalloonColor) {
  const map = markingsTexture();
  const c = color === "rainbow" ? "#ffffff" : BALLOON_COLORS[color];
  return new THREE.MeshStandardMaterial({
    color: c,
    map,
    emissive: c,
    emissiveMap: map,
    emissiveIntensity: 0.2,
  });
}

/** Rows: wrap styles. Columns: balloon colours. Each balloon seen twice (turned). */
export function balloonSheet(renderer: THREE.WebGLRenderer, cell = 120): string {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#9fd8ff");
  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(3, 5, 4);
  scene.add(sun, new THREE.HemisphereLight(0xdff6ff, 0x335533, 1.1));
  const geo = new THREE.SphereGeometry(0.9, 16, 12).scale(1, 1.2, 1);
  const ball = new THREE.Mesh(geo);
  scene.add(ball);
  const cam = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  cam.position.set(0, 0.6, 4.6);
  cam.lookAt(0, 0, 0);
  const rt = new THREE.WebGLRenderTarget(cell, cell);
  const label = 200;
  const out = document.createElement("canvas");
  out.width = label + COLORS.length * 2 * cell;
  out.height = STYLES.length * cell;
  const g = out.getContext("2d")!;
  g.fillStyle = "#2b1b14";
  g.fillRect(0, 0, out.width, out.height);
  const px = new Uint8Array(cell * cell * 4);
  const tmp = document.createElement("canvas");
  tmp.width = tmp.height = cell;
  const tg = tmp.getContext("2d")!;
  STYLES.forEach(([style, name], row) => {
    g.save();
    g.scale(2, 2);
    drawText(g, name, 6, row * (cell / 2) + cell / 4 - 4, { color: "#ffd84a" });
    g.restore();
    COLORS.forEach((color, col) => {
      ball.material = style ? wrapMaterial(style, color) : classic(color);
      for (let k = 0; k < 2; k++) {
        ball.rotation.y = k * 1.9 + 0.3;
        renderer.setRenderTarget(rt);
        renderer.render(scene, cam);
        renderer.readRenderTargetPixels(rt, 0, 0, cell, cell, px);
        const img = tg.createImageData(cell, cell);
        for (let y = 0; y < cell; y++)
          img.data.set(px.subarray((cell - 1 - y) * cell * 4, (cell - y) * cell * 4), y * cell * 4);
        tg.putImageData(img, 0, 0);
        g.drawImage(tmp, label + (col * 2 + k) * cell, row * cell);
      }
    });
  });
  renderer.setRenderTarget(null);
  rt.dispose();
  return out.toDataURL();
}

/** The oil slick and mine icons in every style: big (x6) and in a mock item box (x3). */
export function iconSheet(): string {
  const n = 4;
  const cw = 170;
  const out = document.createElement("canvas");
  out.width = n * cw + 20;
  out.height = 2 * 200 + 20;
  const g = out.getContext("2d")!;
  g.imageSmoothingEnabled = false;
  g.fillStyle = "#2b1b14";
  g.fillRect(0, 0, out.width, out.height);
  const was = { ...ICON_STYLE };
  (["oil", "mine"] as const).forEach((kind, row) => {
    for (let v = 0; v < n; v++) {
      ICON_STYLE.oil = kind === "oil" ? v : 0;
      ICON_STYLE.mine = kind === "mine" ? v : 0;
      clearIconCache();
      const icon = itemIcon("green", kind === "oil" ? 1 : 2);
      const x = 10 + v * cw;
      const y = 10 + row * 200;
      g.drawImage(icon, x, y + 20, 120, 120);
      // The item box: a green-framed dark square, as in the HUD.
      g.fillStyle = "#1f8a32";
      g.fillRect(x + 124, y + 74, 44, 44);
      g.fillStyle = "#14281a";
      g.fillRect(x + 127, y + 77, 38, 38);
      g.drawImage(icon, x + 129, y + 79, 34, 34);
      g.save();
      g.scale(2, 2);
      drawText(g, `${kind.toUpperCase()} ${v === 0 ? "NOW" : v}`, x / 2, y / 2 + 75, {
        color: "#ffd84a",
      });
      g.restore();
    }
  });
  Object.assign(ICON_STYLE, was);
  clearIconCache();
  return out.toDataURL();
}
