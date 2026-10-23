/**
 * The icon lab (developer tool): prototype sheets for item icons. On a ?debug page:
 *
 *   const lab = await import("/src/debug/iconLab.ts");
 *   lab.shieldSheet(); // a PNG data URL: every shield style at levels 1-3
 */
import { SHIELD_STYLE, clearIconCache, itemIcon } from "../ui/itemIcons";
import { drawText } from "../ui/font";

export function shieldSheet(styles = [0, 1, 2, 3, 4]): string {
  const cw = 3 * 104 + 70;
  const out = document.createElement("canvas");
  out.width = cw * Math.min(styles.length, 3) + 20;
  out.height = Math.ceil(styles.length / 3) * 170 + 20;
  const g = out.getContext("2d")!;
  g.imageSmoothingEnabled = false;
  g.fillStyle = "#2b1b14";
  g.fillRect(0, 0, out.width, out.height);
  const was = SHIELD_STYLE.v;
  styles.forEach((v, k) => {
    SHIELD_STYLE.v = v;
    clearIconCache();
    const x0 = 10 + (k % 3) * cw;
    const y0 = 10 + Math.floor(k / 3) * 170;
    const names = ["NOW", "1 KNIGHT", "2 PLASMA ORB", "3 TURTLE SHELL", "4 ENERGY CREST"];
    g.save();
    g.scale(2, 2);
    drawText(g, names[v]!, x0 / 2, y0 / 2, { color: "#ffd84a" });
    g.restore();
    for (let lv = 1; lv <= 3; lv++) {
      const icon = itemIcon("yellow", lv);
      const x = x0 + (lv - 1) * 104;
      g.drawImage(icon, x, y0 + 24, 80, 80);
      // In the HUD's item box (yellow frame), actual size x2.
      g.fillStyle = "#c08a14";
      g.fillRect(x + 18, y0 + 112, 44, 44);
      g.fillStyle = "#14281a";
      g.fillRect(x + 21, y0 + 115, 38, 38);
      g.drawImage(icon, x + 20, y0 + 114, 40, 40);
    }
  });
  SHIELD_STYLE.v = was;
  clearIconCache();
  return out.toDataURL();
}
