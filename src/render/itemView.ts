/**
 * Drawing for balloons and weapons: balloons to collect, missiles, traps, blasts,
 * shields, bubbles and magnet beams. Purely visual.
 */
import * as THREE from "three";
import type { RacerItems } from "../items/effects";
import type { BalloonColor } from "../items/inventory";
import type { ItemWorld } from "../items/world";

export const BALLOON_COLORS: Record<BalloonColor, string> = {
  red: "#e63946",
  blue: "#2f80ed",
  green: "#2bb24c",
  yellow: "#ffd23f",
  rainbow: "#ffffff",
};

/** Shield colour by level: brighter and warmer as it gets longer. */
const SHIELD_COLORS = ["#ffffff", "#fff3a0", "#ffc94a", "#ff9f1c"];

const BLAST_COLORS: Record<string, string> = {
  missile: "#ff7b00",
  mine: "#ff3b1f",
  oil: "#222222",
  bubble: "#8fd3ff",
  blocked: "#ffe066",
  wall: "#ff9f43",
  fizz: "#bbbbbb",
};

/** A pool of meshes that grows on demand; unused ones are hidden. */
function pool(make: () => THREE.Object3D, scene: THREE.Scene) {
  const items: THREE.Object3D[] = [];
  return {
    get(i: number) {
      while (items.length <= i) {
        const m = make();
        scene.add(m);
        items.push(m);
      }
      const m = items[i]!;
      m.visible = true;
      return m;
    },
    hideFrom(n: number) {
      for (let i = n; i < items.length; i++) items[i]!.visible = false;
    },
  };
}

export function createItemView(scene: THREE.Scene) {
  const rainbowMat = new THREE.MeshStandardMaterial({
    color: "#ffffff",
    emissive: "#ffffff",
    emissiveIntensity: 0.25,
  });
  const balloonMats = Object.fromEntries(
    Object.entries(BALLOON_COLORS).map(([k, c]) => [
      k,
      k === "rainbow"
        ? rainbowMat
        : new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.2 }),
    ]),
  ) as Record<BalloonColor, THREE.MeshStandardMaterial>;
  const balloonGeo = new THREE.SphereGeometry(0.9, 16, 12).scale(1, 1.2, 1);
  const stringMat = new THREE.MeshBasicMaterial({ color: "#eeeeee" });
  const balloons = pool(() => {
    const g = new THREE.Group();
    const ball = new THREE.Mesh(balloonGeo, balloonMats.red);
    ball.name = "ball";
    ball.castShadow = true;
    const knot = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.3, 6), stringMat);
    knot.position.y = -1.15;
    knot.rotation.x = Math.PI;
    const string = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.2, 4), stringMat);
    string.position.y = -1.8;
    g.add(ball, knot, string);
    return g;
  }, scene);

  const missileMat = new THREE.MeshStandardMaterial({ color: "#d62828", flatShading: true });
  const missileFlame = new THREE.MeshBasicMaterial({ color: "#ffb703" });
  const missiles = pool(() => {
    const g = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.CylinderGeometry(0.22, 0.22, 1.4, 8).rotateX(Math.PI / 2),
      missileMat,
    );
    const nose = new THREE.Mesh(
      new THREE.ConeGeometry(0.22, 0.5, 8).rotateX(Math.PI / 2),
      missileMat,
    );
    nose.position.z = 0.95;
    const flame = new THREE.Mesh(
      new THREE.ConeGeometry(0.2, 0.7, 8).rotateX(-Math.PI / 2),
      missileFlame,
    );
    flame.position.z = -1;
    g.add(body, nose, flame);
    return g;
  }, scene);

  const oilMat = new THREE.MeshStandardMaterial({
    color: "#151515",
    roughness: 0.2,
    metalness: 0.4,
  });
  const mineMat = new THREE.MeshStandardMaterial({ color: "#2b2b2b", flatShading: true });
  const mineLight = new THREE.MeshBasicMaterial({ color: "#ff2a2a" });
  const bubbleMat = new THREE.MeshStandardMaterial({
    color: "#9fdcff",
    transparent: true,
    opacity: 0.35,
    emissive: "#4fb3ff",
    emissiveIntensity: 0.3,
    depthWrite: false,
  });
  const traps = pool(() => {
    const g = new THREE.Group();
    const oil = new THREE.Mesh(new THREE.CircleGeometry(2.2, 20).rotateX(-Math.PI / 2), oilMat);
    oil.name = "oil";
    oil.position.y = 0.06;
    const mine = new THREE.Group();
    mine.name = "mine";
    mine.add(new THREE.Mesh(new THREE.SphereGeometry(0.6, 10, 8), mineMat));
    const light = new THREE.Mesh(new THREE.SphereGeometry(0.15, 6, 4), mineLight);
    light.name = "light";
    light.position.y = 0.6;
    mine.add(light);
    mine.position.y = 0.5;
    const bubble = new THREE.Mesh(new THREE.SphereGeometry(1.4, 16, 12), bubbleMat);
    bubble.name = "bubble";
    bubble.position.y = 1.4;
    g.add(oil, mine, bubble);
    return g;
  }, scene);

  const blastGeo = new THREE.SphereGeometry(1, 14, 10);
  const blasts = pool(() => {
    const m = new THREE.Mesh(
      blastGeo,
      new THREE.MeshBasicMaterial({ color: "#ff7b00", transparent: true, depthWrite: false }),
    );
    return m;
  }, scene);

  const shields = pool(
    () =>
      new THREE.Mesh(
        new THREE.SphereGeometry(2.1, 18, 14),
        new THREE.MeshStandardMaterial({
          color: "#ffd23f",
          emissive: "#ffd23f",
          emissiveIntensity: 0.5,
          transparent: true,
          opacity: 0.3,
          depthWrite: false,
        }),
      ),
    scene,
  );
  const held = pool(() => new THREE.Mesh(new THREE.SphereGeometry(2.2, 16, 12), bubbleMat), scene);
  const beams = pool(
    () =>
      new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.12, 1, 6).translate(0, 0.5, 0).rotateX(Math.PI / 2),
        new THREE.MeshBasicMaterial({ color: "#ff00ff", transparent: true, opacity: 0.7 }),
      ),
    scene,
  );

  const tmp = new THREE.Vector3();

  return {
    /**
     * Draw this frame. `karts` are the karts' drawn positions (meshes), in racer order;
     * `lift` is how far each one is raised (a kart held in a bubble floats).
     */
    render(w: ItemWorld, karts: THREE.Vector3[], racers: RacerItems[], seconds: number) {
      rainbowMat.color.setHSL((seconds * 0.4) % 1, 0.9, 0.6);
      rainbowMat.emissive.copy(rainbowMat.color);

      let n = 0;
      w.balloons.forEach((b, i) => {
        if (!b.active) return;
        const g = balloons.get(n++) as THREE.Group;
        (g.getObjectByName("ball") as THREE.Mesh).material = balloonMats[b.color];
        g.position.set(b.x, b.y + 2.6 + Math.sin(seconds * 2 + i) * 0.2, b.z);
        g.rotation.y = seconds + i;
        g.scale.setScalar(Math.min(1, 0.2 + b.age * 3));
      });
      balloons.hideFrom(n);

      w.missiles.forEach((m, i) => {
        const g = missiles.get(i);
        g.position.set(m.x, m.y, m.z);
        g.rotation.y = m.heading;
      });
      missiles.hideFrom(w.missiles.length);

      w.traps.forEach((t, i) => {
        const g = traps.get(i) as THREE.Group;
        g.position.set(t.x, t.y, t.z);
        for (const kind of ["oil", "mine", "bubble"])
          g.getObjectByName(kind)!.visible = t.kind === kind;
        const light = g.getObjectByName("light");
        if (light) light.visible = t.kind === "mine" && Math.floor(seconds * 4) % 2 === 0;
        if (t.kind === "bubble")
          g.getObjectByName("bubble")!.position.y = 1.4 + Math.sin(seconds * 3) * 0.15;
      });
      traps.hideFrom(w.traps.length);

      w.blasts.forEach((b, i) => {
        const m = blasts.get(i) as THREE.Mesh;
        const mat = m.material as THREE.MeshBasicMaterial;
        mat.color.set(BLAST_COLORS[b.kind] ?? "#ffffff");
        const big = b.kind === "missile" || b.kind === "mine" || b.kind === "wall" ? 3.5 : 2;
        const f = Math.min(1, b.age / 0.5);
        m.scale.setScalar(0.5 + f * big);
        mat.opacity = Math.max(0, 0.8 * (1 - b.age / 1.2));
        m.position.set(b.x, b.y + 0.5, b.z);
      });
      blasts.hideFrom(w.blasts.length);

      let s = 0;
      let h = 0;
      let bm = 0;
      racers.forEach((it, i) => {
        const p = karts[i];
        if (!p) return;
        if (it.shieldTime > 0) {
          const m = shields.get(s++) as THREE.Mesh;
          const mat = m.material as THREE.MeshStandardMaterial;
          mat.color.set(SHIELD_COLORS[it.shieldLevel] ?? "#ffd23f");
          mat.emissive.copy(mat.color);
          // Flickers in its last second, so you know it's about to drop.
          const ending = it.shieldTime < 1 && Math.floor(seconds * 12) % 2 === 0;
          mat.opacity = ending ? 0.08 : 0.22 + 0.08 * it.shieldLevel;
          m.scale.setScalar(1 + 0.08 * it.shieldLevel + Math.sin(seconds * 6) * 0.03);
          m.position.copy(p);
        }
        if (it.bubbleTime > 0) {
          const m = held.get(h++);
          m.position.copy(p).y += 0.6;
          m.scale.setScalar(1 + Math.sin(seconds * 5) * 0.04);
        }
        const target = it.magnetTime > 0 ? it.magnetTarget : -1;
        const from = it.pullTime > 0 ? it.pullBy : -1;
        for (const [a, b] of [
          [i, target],
          [from, i],
        ] as const) {
          const pa = karts[a];
          const pb = karts[b];
          if (a < 0 || b < 0 || !pa || !pb) continue;
          const m = beams.get(bm++) as THREE.Mesh;
          (m.material as THREE.MeshBasicMaterial).color.setHSL((seconds * 1.5) % 1, 1, 0.6);
          m.position.copy(pa).y += 0.6;
          tmp.copy(pb).y += 0.6;
          m.lookAt(tmp);
          m.scale.set(1, 1, pa.distanceTo(pb));
        }
      });
      shields.hideFrom(s);
      held.hideFrom(h);
      beams.hideFrom(bm);
    },
  };
}
