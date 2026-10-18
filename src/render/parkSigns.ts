/**
 * Signposts for the Drift Park: a wooden board beside each loop's start line with its
 * number and name. Purely visual.
 */
import * as THREE from "three";
import type { DriftPark } from "../world/driftPark";

function signTexture(number: string, name: string, detail: string) {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 128;
  const g = c.getContext("2d")!;
  g.fillStyle = "#7a4a22";
  g.beginPath();
  g.roundRect(4, 4, 248, 120, 16);
  g.fill();
  g.lineWidth = 6;
  g.strokeStyle = "#3a2210";
  g.stroke();
  g.fillStyle = "#5c3618";
  g.fillRect(10, 62, 236, 3);
  g.textAlign = "center";
  g.fillStyle = "#ffd23f";
  g.font = "900 44px 'Arial Rounded MT Bold', 'Trebuchet MS', sans-serif";
  g.fillText(`${number} · ${name}`, 128, 52);
  g.fillStyle = "#f4e4bc";
  g.font = "800 30px 'Arial Rounded MT Bold', 'Trebuchet MS', sans-serif";
  g.fillText(detail, 128, 104);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

const DETAIL = { plain: "drift it all", bananas: "+ bananas", zipper: "+ zipper" } as const;

export function createParkSigns(scene: THREE.Object3D, park: DriftPark) {
  const group = new THREE.Group();
  const postMat = new THREE.MeshLambertMaterial({ color: "#5c3618" });
  const postGeo = new THREE.CylinderGeometry(0.18, 0.22, 3.2, 6);
  for (const loop of park.loops) {
    const s = loop.track.samples[0]!;
    // Outside the start line (the loops turn left, so the outside is to the right).
    const out = s.width / 2 + 4;
    const x = s.pos.x + s.right.x * out;
    const z = s.pos.z + s.right.z * out;
    const sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: signTexture(String(loop.index + 1), loop.size.name, DETAIL[loop.variant]),
      }),
    );
    sprite.scale.set(6, 3, 1);
    sprite.position.set(x, 4.4, z);
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(x, 1.6, z);
    group.add(sprite, post);
  }
  scene.add(group);
  return group;
}
