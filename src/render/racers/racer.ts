/**
 * A complete racer for the screen: kart + rider + exhaust flame + blob shadow, a cheaper
 * far-away version, and the animator that brings it to life.
 *
 * Everything here is visual. The racer follows the kart's physics state (position,
 * heading, speed, drift, boosts, hits) and adds motion on top through child transforms.
 * It never writes back to the physics.
 */
import * as THREE from "three";
import type { RacerId } from "./designs";
import { BUILDS } from "./roster";
import { BUILDS_V2 } from "./roster/v2";
import { CHASSIS, buildKart, type KartModel } from "./kit/chassis";
import type { RiderRig } from "./kit/rig";
import { shadowTexture } from "./kit/paint";
import { Animator, type RacerMotion } from "./animator";

export { motionOf, type RacerMotion, type AnimState } from "./animator";

/**
 * The redesigned racers and karts (prototype): on with ?racers=v2 in the address, or
 * per racer with the `v2` option.
 */
export function racerV2(): boolean {
  return typeof location !== "undefined" && new URLSearchParams(location.search).get("racers") === "v2";
}

/** Distance beyond which the cheap version is drawn, metres. */
export const LOD_DISTANCE = 45;

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

  constructor(id: RacerId, opts: { alt?: boolean; seed?: number; v2?: boolean } = {}) {
    this.id = id;
    const build = ((opts.v2 ?? racerV2()) && BUILDS_V2[id]) || BUILDS[id];
    const palette = opts.alt ? build.palettes.alt : build.palettes.main;
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
    this.root.add(this.lod);

    // Exhaust flame: shows boosts (the session colours it by boost source and phase).
    this.flameMat = new THREE.MeshBasicMaterial({ color: "#ff8c1a", transparent: true });
    this.flame = new THREE.Mesh(
      new THREE.ConeGeometry(0.3, 1.2, 10).rotateX(-Math.PI / 2),
      this.flameMat,
    );
    this.flame.position.copy(this.kart.exhaust).add(new THREE.Vector3(0, 0, -0.5));
    this.flame.visible = false;
    this.core = new THREE.Mesh(
      new THREE.ConeGeometry(0.15, 0.95, 8).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: "#3ddc84" }),
    );
    this.core.position.copy(this.flame.position).add(new THREE.Vector3(0, 0, 0.12));
    this.core.visible = false;
    this.root.add(this.flame, this.core);

    this.shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(2.2, 3).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false }),
    );
    this.shadow.renderOrder = 1;
  }

  /** Put the blob shadow on the ground under the kart (it stays flat on the road). */
  placeShadow(x: number, groundY: number, z: number, heading: number, above: number) {
    this.shadow.position.set(x, groundY + 0.05, z);
    this.shadow.rotation.y = heading;
    this.shadow.scale.setScalar(Math.max(0.4, 1 - above * 0.12));
    (this.shadow.material as THREE.MeshBasicMaterial).opacity = Math.max(0.25, 1 - above * 0.15);
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
    this.anim.react(kind);
  }

  /** The race is over: `place` 1..n celebrates or slumps; null clears it. */
  setResult(place: number | null, of?: number) {
    this.anim.setResult(place, of);
  }

  /**
   * Animate one rendered frame. `rival` is the nearest other racer's position in this
   * racer's local frame (x across, z forward), if one is close enough to glance at.
   */
  animate(dt: number, m: RacerMotion, rival: { x: number; z: number } | null) {
    if (this.lod.getCurrentLevel() !== 0) {
      // Far away: the wheels are baked in; nothing to do.
      return;
    }
    this.anim.step(dt, m, this.kart, rival);
  }
}
