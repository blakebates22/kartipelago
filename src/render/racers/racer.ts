/**
 * A complete racer for the screen: kart + rider + exhaust flame + blob shadow, a cheaper
 * far-away version, and the animator that brings it to life.
 *
 * Everything here is visual. The racer follows the kart's physics state (position,
 * heading, speed, drift, boosts, hits) and adds motion on top through child transforms.
 * It never writes back to the physics.
 */
import { BOSS_SHADOW, BossDragon, type BossPalette } from "./bossDragon";
import * as THREE from "three";
import type { RacerId } from "./designs";
import type { Palette } from "./roster/types";
import { BUILDS } from "./roster";
import { CHASSIS, buildKart, type KartModel } from "./kit/chassis";
import type { RiderRig } from "./kit/rig";
import { shadowTexture } from "./kit/paint";
import { Animator, type RacerMotion } from "./animator";

export { motionOf, type RacerMotion, type AnimState } from "./animator";

/** Distance beyond which the cheap version is drawn, metres. */
export const LOD_DISTANCE = 45;

let rainbowTex: THREE.Texture | undefined;
/** Six bold bands of colour (red to violet), repeated twice along the flame. */
function rainbowTexture() {
  if (rainbowTex) return rainbowTex;
  const c = document.createElement("canvas");
  c.width = 2;
  c.height = 12;
  const g = c.getContext("2d")!;
  ["#ff2a2a", "#ff9a1a", "#ffe82a", "#3ade3a", "#2a8aff", "#a84aff"].forEach((col, i) => {
    g.fillStyle = col;
    g.fillRect(0, i * 2, 2, 2);
  });
  rainbowTex = new THREE.CanvasTexture(c);
  rainbowTex.wrapS = rainbowTex.wrapT = THREE.RepeatWrapping;
  rainbowTex.repeat.set(1, 2);
  rainbowTex.magFilter = THREE.NearestFilter;
  rainbowTex.minFilter = THREE.NearestFilter;
  rainbowTex.colorSpace = THREE.SRGBColorSpace;
  return rainbowTex;
}

const SH_UP = new THREE.Vector3(0, 1, 0);
const SH_N = new THREE.Vector3();
const SH_Q = new THREE.Quaternion();

export class Racer {
  readonly root = new THREE.Group();
  readonly lod = new THREE.LOD();
  readonly high = new THREE.Group();
  readonly lowGroup = new THREE.Group();
  readonly kart: KartModel;
  readonly rig: RiderRig;
  readonly anim: Animator;
  readonly flame: THREE.Mesh;
  readonly flameMat: THREE.MeshBasicMaterial;
  readonly core: THREE.Mesh;
  readonly shadow: THREE.Mesh;
  readonly id: RacerId;
  private lowKart: KartModel;

  /** A boss (Adventure): a huge dragon on foot instead of the kart and rider. */
  readonly boss?: BossDragon;

  constructor(
    id: RacerId,
    opts: { alt?: boolean; seed?: number; palette?: Palette; boss?: boolean } = {},
  ) {
    this.id = id;
    const build = BUILDS[id];
    const palette = opts.palette ?? (opts.alt ? build.palettes.alt : build.palettes.main);
    const kit = build.kart(palette);
    this.kart = buildKart(kit, 0);
    this.rig = build.rider(palette);
    this.rig.root.position.copy(this.kart.seat);
    this.rig.root.scale.setScalar(CHASSIS.riderScale);
    this.kart.body.add(this.rig.root, this.rig.hands);
    this.high.add(this.kart.root);
    this.anim = new Animator(this.rig, opts.seed ?? 7);

    // Far away: the baked kart and the rider's one-piece stand-in.
    this.lowKart = buildKart(kit, 1);
    this.lowKart.steering.visible = false;
    this.rig.low.position.copy(this.lowKart.seat);
    this.rig.low.scale.setScalar(CHASSIS.riderScale);
    this.lowKart.body.add(this.rig.low);
    this.lowGroup.add(this.lowKart.root);

    this.lod.addLevel(this.high, 0);
    this.lod.addLevel(this.lowGroup, LOD_DISTANCE);
    if (opts.boss) {
      this.boss = new BossDragon(palette as unknown as BossPalette);
      this.root.add(this.boss.root);
    } else this.root.add(this.lod);

    // Exhaust flame: shows boosts (the session colours it by boost source and phase). A
    // jet: the coloured outer flame (glowing, additive), a hot yellow-white flame inside
    // it, a white-hot core, a glow at the nozzle and shock diamonds rippling down it
    // (see animateFlame). Its origin is at the nozzle; it points back along -Z.
    this.flameMat = new THREE.MeshBasicMaterial({
      color: "#ff8c1a",
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const jet = (r: number, len: number, color: string, opacity: number) =>
      new THREE.Mesh(
        new THREE.ConeGeometry(r, len, 12).rotateX(-Math.PI / 2).translate(0, 0, -len / 2),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
    this.flame = new THREE.Mesh(
      new THREE.ConeGeometry(0.34, 1.7, 12).rotateX(-Math.PI / 2).translate(0, 0, -0.85),
      this.flameMat,
    );
    const hot = jet(0.2, 1.15, "#ffe08a", 0.85);
    hot.name = "hot";
    const white = jet(0.1, 0.7, "#ffffff", 0.95);
    white.name = "white";
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.32, 10, 8),
      new THREE.MeshBasicMaterial({
        color: "#fff4c8",
        transparent: true,
        opacity: 0.55,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    );
    glow.name = "glow";
    this.flame.add(hot, white, glow);
    for (let k = 0; k < 3; k++) {
      const d = new THREE.Mesh(
        new THREE.SphereGeometry(1, 8, 6),
        new THREE.MeshBasicMaterial({
          color: "#ffffff",
          transparent: true,
          opacity: 0.8,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      );
      d.name = `diamond${k}`;
      d.scale.set(0.12, 0.12, 0.2);
      this.flame.add(d);
    }
    this.flame.position.copy(this.kart.exhaust);
    this.flame.visible = false;
    this.core = new THREE.Mesh(
      new THREE.ConeGeometry(0.15, 0.95, 8).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: "#fff4c0" }),
    );
    this.core.position.copy(this.flame.position).add(new THREE.Vector3(0, 0, -0.38));
    this.core.visible = false;
    if (this.boss) {
      // A boss's boosts are fire out of its mouth: the flame turned to point forward.
      const breath = new THREE.Group();
      breath.rotation.y = Math.PI;
      breath.scale.setScalar(2.4);
      this.flame.position.set(0, 0, 0);
      this.core.position.set(0, 0, -0.38);
      breath.add(this.flame, this.core);
      this.boss.mouth.add(breath);
    } else this.root.add(this.flame, this.core);

    this.shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(2.2, 3).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({
        map: shadowTexture(),
        transparent: true,
        depthWrite: false,
        // Drawn just in front of the ground so it never sinks into bumps.
        polygonOffset: true,
        polygonOffsetFactor: -2,
        polygonOffsetUnits: -4,
      }),
    );
    this.shadow.renderOrder = 1;
  }

  /**
   * The rainbow window's flame (on), or back to normal (off): the outer flame painted in
   * bands of every colour that stream back along it (drawn solid, not added, so the
   * colours stay strong instead of washing out to white), its hot inner flame, white
   * core and shock diamonds hidden, and the nozzle glow cycling through the colours.
   */
  rainbowFlame(on: boolean, seconds: number) {
    const glow = this.flame.getObjectByName("glow") as THREE.Mesh;
    const glowMat = glow.material as THREE.MeshBasicMaterial;
    const inner = ["hot", "white", "diamond0", "diamond1", "diamond2"].map((n) =>
      this.flame.getObjectByName(n)!,
    );
    const m = this.flameMat;
    if (on) {
      if (!this.rainbowOn) {
        m.map = rainbowTexture();
        m.blending = THREE.NormalBlending;
        m.needsUpdate = true;
        this.rainbowOn = true;
      }
      m.color.set("#ffffff");
      m.map!.offset.y = (seconds * 3) % 1;
      for (const o of inner) o.visible = false;
      glowMat.color.setHSL((seconds * 2.6) % 1, 1, 0.6);
      glowMat.opacity = 0.9;
    } else if (this.rainbowOn) {
      m.map = null;
      m.blending = THREE.AdditiveBlending;
      m.needsUpdate = true;
      for (const o of inner) o.visible = true;
      glowMat.color.set("#fff4c8");
      glowMat.opacity = 0.55;
      this.rainbowOn = false;
    }
  }
  private rainbowOn = false;

  /**
   * Bring the boost flame to life this frame: it flickers and pulses, and shock diamonds
   * ripple back down it (faster and brighter the hotter it burns, 0..1).
   */
  animateFlame(seconds: number, heat: number) {
    const f = this.flame;
    const flick = 1 + Math.sin(seconds * 47) * 0.06 + Math.sin(seconds * 31 + 1) * 0.05;
    f.scale.z *= flick * (1 + heat * 0.25);
    const hot = f.getObjectByName("hot")!;
    hot.scale.set(1, 1, 0.9 + Math.sin(seconds * 53) * 0.12);
    const glow = f.getObjectByName("glow")!;
    glow.scale.setScalar(0.85 + heat * 0.35 + Math.sin(seconds * 40) * 0.08);
    for (let k = 0; k < 3; k++) {
      const d = f.getObjectByName(`diamond${k}`)!;
      const ph = (seconds * (2.6 + heat * 2) + k / 3) % 1;
      d.position.set(0, 0, -0.2 - ph * 1.15);
      const s = (1 - ph) * (0.9 + heat * 0.5);
      d.scale.set(0.12 * s, 0.12 * s, 0.22 * s);
      d.visible = heat > 0.15;
    }
  }

  /**
   * Put the blob shadow on the ground under the kart, lying along the slope (normal
   * nx, ny, nz), smaller and fainter the higher the kart flies; gone if it's far above.
   */
  placeShadow(
    x: number,
    groundY: number,
    z: number,
    heading: number,
    above: number,
    nx = 0,
    ny = 1,
    nz = 0,
  ) {
    const sh = this.shadow;
    sh.visible = above < 12;
    sh.position.set(x + nx * 0.04, groundY + ny * 0.04, z + nz * 0.04);
    SH_N.set(nx, ny, nz);
    sh.quaternion.setFromUnitVectors(SH_UP, SH_N);
    SH_Q.setFromAxisAngle(SH_UP, heading);
    sh.quaternion.multiply(SH_Q);
    sh.scale.setScalar(
      Math.max(0.4, 1 - Math.max(0, above) * 0.08) * (this.boss ? BOSS_SHADOW : 1),
    );
    (sh.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 1 - Math.max(0, above) / 12);
  }

  /** Remove from the scene and free the geometry. */
  dispose(scene: THREE.Object3D) {
    scene.remove(this.root, this.shadow);
    this.root.traverse((o) => {
      if (o instanceof THREE.Mesh) o.geometry.dispose();
    });
    this.shadow.geometry.dispose();
  }

  /** React to a course hazard: a yelp and a jolt (burn) or a big-eyed bob (splash). */
  react(kind: "burn" | "splash") {
    this.boss?.react();
    this.anim.react(kind);
  }

  /** The race is over: `place` 1..n celebrates or slumps; null clears it. */
  setResult(place: number | null, of?: number) {
    this.boss?.setResult(place);
    this.anim.setResult(place, of);
  }

  /**
   * Animate one rendered frame. `rival` is the nearest other racer's position in this
   * racer's local frame (x across, z forward), if one is close enough to glance at.
   */
  animate(dt: number, m: RacerMotion, rival: { x: number; z: number } | null) {
    if (this.boss) {
      this.boss.step(dt, m);
      return;
    }
    if (this.lod.getCurrentLevel() !== 0) {
      // Far away: the wheels are baked in; nothing to do.
      return;
    }
    this.anim.step(dt, m, this.kart, rival);
  }
}
