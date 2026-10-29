/**
 * Adventure's bosses as they race: a huge dragon on foot, no kart (Blake: "an actual
 * large dragon, like in DKR the bosses are very intimidating"). A PLACEHOLDER built from
 * the racer kit, in the boss's own colours (DRAGON_PALETTES): a stocky horned dragon with
 * a pale belly (the direction of Blake's Wildbolt sheet), several karts long. It bounds
 * along on all fours, wings half folded, spreads them and beats them in the air, turns
 * its head into the corners, lashes its tail, and breathes fire when it boosts (the
 * session's boost flame comes out of its mouth: `mouth`).
 *
 * It's only what you see: the boss still races with a kart's physics underneath.
 * All original.
 */
import * as THREE from "three";
import { Build, card, horn, loft, tube, type V3 } from "./kit/shapes";
import { skinMaterial } from "./kit/paint";
import type { RacerMotion } from "./animator";
import {
  DRAGON_SIZE,
  createStoryDragon,
  type DesignId,
  type StoryDragonView,
} from "../storyDragon";

export interface BossPalette {
  skin: string;
  skinDark: string;
  belly: string;
  wing: string;
  wingDark: string;
  horn: string;
  lens: string;
}

/** How big it stands: the model is built about 2.6 m at the shoulder, then scaled. */
export const BOSS_SCALE = 1.0;
/** Its shadow, in kart shadows. */
export const BOSS_SHADOW = 4.2;

const BODY_Y = 2.3;
const STRIDE = 5.2;

interface Leg {
  hip: THREE.Group;
  knee: THREE.Group;
  front: boolean;
  side: number;
}

export class BossDragon {
  readonly root = new THREE.Group();
  /** The boost flame goes here (it points out of the mouth). */
  readonly mouth = new THREE.Group();
  private body = new THREE.Group();
  private neck = new THREE.Group();
  private head = new THREE.Group();
  private jaw = new THREE.Group();
  private tail: THREE.Group[] = [];
  private wings: { g: THREE.Group; side: number }[] = [];
  private legs: Leg[] = [];
  private phase = 0;
  private flap = 0;
  private air = 0;
  private time = 0;
  private boost = 0;
  private lastBoostLeft = 0;
  private jolt = 0;
  private lastImpact = 0;
  private result: number | null = null;
  /** The dragon's own design (as in the cutscenes), when it has one. */
  private story?: StoryDragonView;

  constructor(c: BossPalette, design?: DesignId) {
    if (design) {
      this.initStory(design);
      return;
    }
    const mat = skinMaterial();
    const skin = new THREE.Color(c.skin);
    const dark = new THREE.Color(c.skinDark);
    const belly = new THREE.Color(c.belly);
    // Belly pale underneath, back darker on top.
    const shade = (_t: number, a: number, base: THREE.Color) =>
      a < -0.7 && a > -2.45
        ? base.clone().lerp(belly, 0.85)
        : a > 0.9 && a < 2.25
          ? base.clone().lerp(dark, 0.35)
          : base;
    const mesh = (b: Build) => new THREE.Mesh(b.build(), mat);

    // The body: a deep chest, a heavy rump.
    this.body.position.y = BODY_Y;
    this.root.add(this.body);
    this.body.add(
      mesh(
        new Build()
          .addColored(
            loft(
              [
                { at: [0, 0.2, -2.9], rx: 0.9, ry: 0.85, color: skin },
                { at: [0, 0.1, -1.7], rx: 1.3, ry: 1.2, color: skin },
                { at: [0, 0.0, -0.2], rx: 1.35, ry: 1.3, color: skin },
                { at: [0, 0.15, 1.0], rx: 1.35, ry: 1.35, color: skin },
                { at: [0, 0.5, 1.9], rx: 0.95, ry: 1.0, color: skin },
              ],
              { sides: 12, steps: 2, capStart: true, capEnd: true, paint: shade },
            ),
          )
          .addColored(spikes([0, 1.3, 1.4], [0, 1.0, -2.9], 6, 0.22, c.horn)),
      ),
    );

    // The neck, and the head on it.
    this.neck.position.set(0, 0.6, 1.8);
    this.body.add(this.neck);
    this.neck.add(
      mesh(
        new Build()
          .addColored(
            loft(
              [
                { at: [0, 0, 0], rx: 0.85, ry: 0.85, color: skin },
                { at: [0, 0.8, 0.8], rx: 0.62, ry: 0.65, color: skin },
                { at: [0, 1.5, 1.45], rx: 0.5, ry: 0.52, color: skin },
              ],
              { sides: 10, steps: 2, paint: shade },
            ),
          )
          .addColored(spikes([0, 1.95, 1.2], [0, 0.85, 0.1], 3, 0.18, c.horn)),
      ),
    );
    this.head.position.set(0, 1.55, 1.5);
    this.neck.add(this.head);
    const hb = new Build().addColored(
      loft(
        [
          { at: [0, 0.05, -0.4], rx: 0.55, ry: 0.5, color: skin },
          { at: [0, 0.1, 0.3], rx: 0.6, ry: 0.5, color: skin },
          { at: [0, -0.02, 1.0], rx: 0.42, ry: 0.32, color: skin },
          { at: [0, -0.08, 1.65], rx: 0.34, ry: 0.24, color: dark },
        ],
        { sides: 10, steps: 2, capEnd: true, paint: shade },
      ),
    );
    for (const s of [1, -1]) {
      // The great swept-back horns, a smaller pair, a heavy brow.
      hb.addColored(
        horn([s * 0.32, 0.35, -0.15], [s * 0.75, 0.95, -1.5], 0.2, c.horn, [s * 0.1, 0.25, 0], 7),
      );
      hb.addColored(
        horn([s * 0.5, 0.05, -0.1], [s * 0.95, 0.15, -0.8], 0.11, c.horn, [0, 0.1, 0], 5),
      );
      hb.addColored(
        loft(
          [
            { at: [s * 0.18, 0.42, 0.15], rx: 0.14, ry: 0.08, color: dark },
            { at: [s * 0.42, 0.36, 0.55], rx: 0.12, ry: 0.07, color: dark },
          ],
          { sides: 6, capStart: true, capEnd: true },
        ),
      );
      // Teeth along the upper jaw.
      for (let k = 0; k < 4; k++)
        hb.addColored(
          horn(
            [s * 0.27, -0.2, 0.75 + k * 0.22],
            [s * 0.27, -0.42, 0.8 + k * 0.22],
            0.05,
            "#f4ecd8",
            [0, 0, 0],
            4,
          ),
        );
    }
    this.head.add(new THREE.Mesh(hb.build(), mat));
    // Glowing eyes.
    const eyeMat = new THREE.MeshBasicMaterial({ color: c.lens });
    for (const s of [1, -1]) {
      const eye = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 6), eyeMat);
      eye.position.set(s * 0.38, 0.24, 0.55);
      eye.scale.set(1, 0.7, 1.4);
      this.head.add(eye);
    }
    this.jaw.position.set(0, -0.2, -0.05);
    this.head.add(this.jaw);
    this.jaw.add(
      mesh(
        new Build().addColored(
          loft(
            [
              { at: [0, 0, 0], rx: 0.42, ry: 0.18, color: belly },
              { at: [0, -0.06, 0.8], rx: 0.34, ry: 0.14, color: belly },
              { at: [0, -0.04, 1.5], rx: 0.26, ry: 0.1, color: belly },
            ],
            { sides: 8, capEnd: true },
          ),
        ),
      ),
    );
    this.mouth.position.set(0, -0.15, 1.75);
    this.head.add(this.mouth);

    // Four legs, thick and clawed.
    for (const [x, y, z, front] of [
      [1.0, -0.45, 1.0, true],
      [-1.0, -0.45, 1.0, true],
      [1.0, -0.35, -1.9, false],
      [-1.0, -0.35, -1.9, false],
    ] as [number, number, number, boolean][]) {
      const hip = new THREE.Group();
      hip.position.set(x, y, z);
      this.body.add(hip);
      const up = front ? 1.0 : 1.05;
      hip.add(
        mesh(
          new Build().addColored(
            tube(
              [
                [0, 0.2, 0],
                [0, -up * 0.5, front ? 0.1 : -0.15],
                [0, -up, 0.15],
              ],
              [0.55, 0.45, 0.33],
              [skin, skin, dark],
            ),
          ),
        ),
      );
      const knee = new THREE.Group();
      knee.position.set(0, -up, 0.15);
      hip.add(knee);
      const lo = BODY_Y + y - up - 0.05;
      const lb = new Build().addColored(
        tube(
          [
            [0, 0, 0],
            [0, -lo * 0.55, front ? -0.05 : -0.2],
            [0, -lo, 0],
          ],
          [0.32, 0.27, 0.24],
          [dark, dark, dark],
        ),
      );
      for (let k = -1; k <= 1; k++)
        lb.addColored(
          horn(
            [k * 0.18, -lo + 0.08, 0.15],
            [k * 0.26, -lo - 0.02, 0.6],
            0.08,
            c.horn,
            [0, 0.05, 0],
            4,
          ),
        );
      knee.add(mesh(lb));
      this.legs.push({ hip, knee, front, side: Math.sign(x) });
    }

    // The tail: a chain that lashes, with a spade at the end.
    let parent: THREE.Object3D = this.body;
    let at: V3 = [0, 0.2, -2.8];
    const radii = [0.75, 0.6, 0.48, 0.37, 0.27, 0.18, 0.11];
    for (let k = 0; k < 6; k++) {
      const seg = new THREE.Group();
      seg.position.set(...at);
      parent.add(seg);
      const tb = new Build().addColored(
        loft(
          [
            { at: [0, 0, 0.1], rx: radii[k]!, ry: radii[k]!, color: skin },
            { at: [0, -0.08, -1.0], rx: radii[k + 1]!, ry: radii[k + 1]!, color: skin },
          ],
          { sides: 8, paint: shade },
        ),
      );
      tb.addColored(
        horn(
          [0, radii[k]! * 0.9, -0.4],
          [0, radii[k]! * 0.9 + 0.35, -0.75],
          0.12,
          c.horn,
          [0, 0, 0],
          4,
        ),
      );
      if (k === 5)
        tb.add(
          card(
            [
              [0, 0],
              [0.5, -0.4],
              [0, -1.2],
              [-0.5, -0.4],
            ],
            0.06,
          ),
          c.horn,
          { p: [0, -0.08, -0.95], r: [-Math.PI / 2, 0, 0] },
        );
      seg.add(mesh(tb));
      this.tail.push(seg);
      parent = seg;
      at = [0, -0.08, -1.0];
    }

    // The wings: bony fingers and membranes, folded along the back on the ground.
    const outline: [number, number][] = [
      [0, 0],
      [2.0, -0.4],
      [4.2, -0.6],
      [6.2, -0.2],
      [5.3, 0.9],
      [4.5, 2.3],
      [3.5, 1.4],
      [2.5, 2.9],
      [1.5, 1.9],
      [0.5, 2.6],
      [0, 1.5],
    ];
    const wing = new THREE.Color(c.wing);
    const wdark = new THREE.Color(c.wingDark);
    const wg = new Build()
      .add(card(outline), (p) => wing.clone().lerp(wdark, Math.min(1, Math.max(0, p.y / 3))), {
        r: [-Math.PI / 2, 0, 0],
      })
      .addColored(
        tube(
          [
            [0, 0, 0],
            [2.0, 0.08, 0.4],
            [4.2, 0.1, 0.6],
            [6.2, 0.05, 0.2],
          ],
          [0.22, 0.17, 0.12, 0.04],
          c.skinDark,
        ),
      )
      .addColored(
        tube(
          [
            [4.2, 0.08, 0.6],
            [4.5, 0.04, -2.3],
          ],
          [0.08, 0.03],
          c.skinDark,
        ),
      )
      .addColored(
        tube(
          [
            [4.2, 0.08, 0.6],
            [2.5, 0.04, -2.9],
          ],
          [0.08, 0.03],
          c.skinDark,
        ),
      )
      .addColored(
        tube(
          [
            [4.2, 0.08, 0.6],
            [0.5, 0.04, -2.6],
          ],
          [0.07, 0.03],
          c.skinDark,
        ),
      )
      .addColored(horn([4.2, 0.1, 0.6], [4.3, 0.15, 1.1], 0.09, c.horn))
      .build();
    for (const side of [1, -1]) {
      const g = new THREE.Group();
      g.position.set(side * 0.9, 1.05, 0.7);
      g.add(
        new THREE.Mesh(
          side === 1 ? wg : new Build().addColored(wg.clone(), { mirror: true }).build(),
          mat,
        ),
      );
      this.body.add(g);
      this.wings.push({ g, side });
    }
    this.root.scale.setScalar(BOSS_SCALE);
  }

  /**
   * The cutscenes' dragon (render/storyDragon.ts), scaled to race: it walks along with
   * the kart beneath it, flies when it's airborne, opens its jaws for the boost's fire
   * (the flame rides `mouth`), and roars or bows at the finish.
   */
  private initStory(design: DesignId) {
    const s = DRAGON_SIZE[design] ?? (design === "king" ? 0.22 : 0.2);
    this.story = createStoryDragon(this.root, design, s);
    // (Its legs step at a stride for its size, not a scurry.)
    this.story.pace = 3;
    // (The race draws its fire, out of `mouth`, and its shadow.)
    this.story.effects = false;
    const own = this.story.root.getObjectByName("story dragon shadow");
    if (own) own.visible = false;
    this.root.add(this.mouth);
  }

  private storyStep(dt: number, m: RacerMotion) {
    const v = this.story!;
    this.time += dt;
    this.air += ((m.grounded ? 0 : 1) - this.air) * Math.min(1, dt * 6);
    if (m.boostLeft > this.lastBoostLeft + 0.05) this.boost = 1;
    this.lastBoostLeft = m.boostLeft;
    this.boost = Math.max(m.boostPhase > 0 ? 0.6 : 0, this.boost - dt * 0.8);
    const won = this.result === 1;
    const pose =
      this.result !== null
        ? won
          ? "roar"
          : "bow"
        : this.air > 0.4
          ? "fly"
          : this.boost > 0.3
            ? "breathe"
            : Math.abs(m.speed) > 1.5
              ? "walk"
              : "idle";
    this.root.updateMatrixWorld(true);
    const look = new THREE.Vector3(-m.steer * 30, 8, 60).applyMatrix4(this.root.matrixWorld);
    v.update(pose, 0, this.time, look, false);
    // The boost's flame comes out of its jaws, the way its head faces.
    const at = new THREE.Vector3();
    const facing = new THREE.Vector3();
    v.mouth(at);
    v.headFrame(new THREE.Vector3(), facing);
    this.root.worldToLocal(at);
    const inv = new THREE.Quaternion();
    this.root.getWorldQuaternion(inv).invert();
    facing.applyQuaternion(inv).normalize();
    this.mouth.position.copy(at);
    this.mouth.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), facing);
  }

  setResult(place: number | null) {
    this.result = place;
  }

  react() {
    this.jolt = 1;
  }

  /** One rendered frame, from the kart underneath (never changes it). */
  step(dt: number, m: RacerMotion) {
    if (this.story) return this.storyStep(dt, m);
    this.time += dt;
    const speed = Math.max(0, m.speed);
    const k = Math.min(1, speed / 9);
    this.air += ((m.grounded ? 0 : 1) - this.air) * Math.min(1, dt * 6);
    if (m.boostLeft > this.lastBoostLeft + 0.05) this.boost = 1;
    this.lastBoostLeft = m.boostLeft;
    this.boost = Math.max(m.boostPhase > 0 ? 0.6 : 0, this.boost - dt * 0.8);
    if (m.impactTier > 0 && m.impactSpeed !== this.lastImpact) this.jolt = 1;
    this.lastImpact = m.impactSpeed;
    this.jolt = Math.max(0, this.jolt - dt * 2.5);
    if (m.grounded) this.phase += ((dt * speed) / STRIDE) * Math.PI * 2;
    this.flap += dt * (this.air > 0.3 ? 5.5 : 2 + 3 * k);
    const p = this.phase;
    const ground = 1 - this.air;

    // The bound: front legs together, hind legs together, half a stride apart.
    for (const leg of this.legs) {
      const off = (leg.front ? 0 : Math.PI) + (leg.side > 0 ? 0 : 0.35);
      const swing = Math.sin(p + off) * 0.75 * k;
      const lift = Math.max(0, -Math.cos(p + off)) * 0.9 * k;
      const tuck = this.air * (leg.front ? -0.7 : 0.6);
      leg.hip.rotation.x = (swing + tuck) * ground + tuck;
      leg.knee.rotation.x =
        (leg.front ? -lift : lift) * ground + this.air * (leg.front ? 1.1 : -1.0);
    }
    const breathe = Math.sin(this.time * 2.2) * 0.04 * (1 - k);
    this.body.position.y = BODY_Y + Math.abs(Math.sin(p)) * 0.22 * k * ground + breathe;
    this.body.rotation.x = Math.sin(p) * 0.07 * k * ground - this.air * 0.12 - this.jolt * 0.15;
    this.body.rotation.z = -m.steer * 0.08;

    // The head: into the corners, bobbing with the stride, jaw wide when it breathes fire.
    this.neck.rotation.y = -m.steer * 0.35 + (1 - k) * Math.sin(this.time * 0.7) * 0.3;
    this.neck.rotation.x = Math.sin(p * 2) * 0.05 * k - this.jolt * 0.3;
    this.head.rotation.x = -this.boost * 0.2;
    this.jaw.rotation.x =
      0.08 + this.boost * 0.55 + Math.max(0, Math.sin(this.time * 0.9)) * 0.06 * (1 - k);

    // The tail lashes, and swings out of the corners.
    const sway = Math.sin(this.time * 1.6 + p * 0.5) * (0.08 + 0.06 * k);
    this.tail.forEach((seg, i) => {
      seg.rotation.y = sway * (0.6 + i * 0.25) + m.steer * 0.12;
      seg.rotation.x = 0.04 + this.air * 0.05 - (i === 0 ? 0.1 : 0);
    });

    // The wings: folded on the ground (stirring at speed), spread and beating in the air.
    for (const { g, side } of this.wings) {
      const beat = Math.sin(this.flap);
      const foldZ = side * (0.32 + 0.06 * beat * k);
      const openZ = side * (0.1 + 0.55 * beat);
      g.rotation.set(0, side * (1.35 * ground + 0.1 * this.air), foldZ * ground + openZ * this.air);
    }

    // The race is over: it rears up and roars, or slumps.
    if (this.result !== null) {
      const won = this.result === 1;
      this.body.rotation.x = won ? -0.35 : 0.15;
      this.jaw.rotation.x = won ? 0.7 : 0.05;
      this.neck.rotation.x = won ? -0.3 : 0.5;
    }
  }
}

/** A ridge of spikes from a to b (biggest first). */
function spikes(a: V3, b: V3, n: number, r: number, color: string) {
  const out = new Build();
  for (let k = 0; k < n; k++) {
    const t = k / Math.max(1, n - 1);
    const x = a[0] + (b[0] - a[0]) * t;
    const y = a[1] + (b[1] - a[1]) * t;
    const z = a[2] + (b[2] - a[2]) * t;
    const s = r * (1 - 0.45 * t);
    out.addColored(horn([x, y - s, z], [x, y + s * 2.4, z - s * 1.6], s, color, [0, 0, 0], 5));
  }
  return out.build();
}
