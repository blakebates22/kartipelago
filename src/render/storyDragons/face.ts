/**
 * The story dragons' eyes and brows. Each eye is a ball with an iris and a pupil that
 * slide over it to look about (round, a slit, or a goat's bar), bright highlights, an
 * upper lid that blinks and can rest half-closed (bored, sly, sleepy), slanted for anger
 * or worry, and a lower lid that pushes up into a squint. The irises can glow.
 */
import * as THREE from "three";
import { Parts, type V3 } from "./parts";

export interface EyeDesign {
  /** The left eye's centre in head space (the right is mirrored), and its half-sizes. */
  at: V3;
  size: V3;
  /** Turn outward, and tilt (radians). */
  yaw: number;
  pitch?: number;
  sclera: string;
  iris: string;
  /** A second iris colour toward the rim. */
  irisRim?: string;
  /** Iris radius as a fraction of the eye. */
  irisSize: number;
  pupil: "round" | "slit" | "bar";
  /** Pupil width (fraction of the iris). */
  pupilSize?: number;
  /** The skin of the lids. */
  lid: string;
  /** A dark line along the lids' edges (eyeliner markings). */
  liner?: string;
  /** Upper lid at rest (0 open .. 1 shut), lower lid (0 .. 1 up), the upper lid's slant
   * (>0 drops its front end: a glare; <0 lifts it: worry). */
  rest: number;
  lower?: number;
  slant?: number;
}

export interface EyeRig {
  group: THREE.Group;
  look: THREE.Group;
  upper: THREE.Group;
  lower: THREE.Group;
  side: number;
  d: EyeDesign;
}

/** Lid angles: open (folded away behind the ball), and shut over the front. */
const UP_OPEN = -1.75;
const UP_SHUT = 1.4;
const LO_OPEN = 1.9;
const LO_UP = 0.25;

export function buildEyes(
  head: THREE.Object3D,
  d: EyeDesign,
  mats: { eye: THREE.Material; iris: THREE.Material; skin: THREE.Material },
): EyeRig[] {
  const out: EyeRig[] = [];
  const [rx, ry, rz] = d.size;
  for (const side of [1, -1]) {
    const g = new THREE.Group();
    g.position.set(d.at[0] * side, d.at[1], d.at[2]);
    g.rotation.set(d.pitch ?? 0, d.yaw * side, 0, "YXZ");
    const ball = new Parts().add(new THREE.SphereGeometry(1, 16, 12), d.sclera, {
      s: [rx, ry, rz],
    });
    g.add(new THREE.Mesh(ball.build(), mats.eye));
    // The iris, pupil and highlights: a group that turns in the socket.
    const look = new THREE.Group();
    const ir = d.irisSize;
    const iris = new Parts().add(
      new THREE.SphereGeometry(1, 14, 8, 0, Math.PI * 2, 0, Math.PI * 0.6),
      (p) => {
        const r = Math.min(1, Math.hypot(p.x, p.z));
        return new THREE.Color(d.iris).lerp(new THREE.Color(d.irisRim ?? d.iris), r * r);
      },
      { p: [0, 0, rz * 0.64], s: [rx * ir, rz * 0.42, ry * ir], r: [Math.PI / 2, 0, 0] },
    );
    look.add(new THREE.Mesh(iris.build(), mats.iris));
    const pw = d.pupilSize ?? (d.pupil === "round" ? 0.55 : 0.2);
    const pupil = new Parts().add(
      new THREE.SphereGeometry(1, 12, 6, 0, Math.PI * 2, 0, Math.PI * 0.5),
      "#0c0808",
      {
        p: [0, 0, rz * 0.8],
        r: [Math.PI / 2, 0, 0],
        s:
          d.pupil === "bar"
            ? [rx * ir * 0.8, rz * 0.27, ry * ir * pw]
            : d.pupil === "slit"
              ? [rx * ir * pw, rz * 0.27, ry * ir * 0.9]
              : [rx * ir * pw, rz * 0.27, ry * ir * pw],
      },
    );
    // Highlights: a big one up and toward the front, a small one below.
    pupil.add(new THREE.SphereGeometry(1, 8, 5), "#ffffff", {
      p: [rx * 0.26 * side, ry * 0.3, rz * 1.03],
      s: [rx * 0.16, ry * 0.18, rz * 0.06],
    });
    pupil.add(new THREE.SphereGeometry(1, 6, 4), "#ffffff", {
      p: [-rx * 0.2 * side, -ry * 0.24, rz * 1.0],
      s: [rx * 0.07, ry * 0.07, rz * 0.04],
    });
    look.add(new THREE.Mesh(pupil.build(), mats.eye));
    g.add(look);
    // Lids: caps over the top and bottom halves, a hair bigger than the ball.
    const cap = (top: boolean) => {
      const p = new Parts().add(
        new THREE.SphereGeometry(1, 16, 6, 0, Math.PI * 2, top ? 0 : Math.PI / 2, Math.PI / 2),
        (q) => new THREE.Color(d.liner && Math.abs(q.y) < 0.2 ? d.liner : d.lid),
        { s: [rx * 1.1, ry * 1.1, rz * 1.1] },
      );
      const grp = new THREE.Group();
      grp.add(new THREE.Mesh(p.build(), mats.skin));
      return grp;
    };
    const upper = cap(true);
    const lower = cap(false);
    const slant = new THREE.Group();
    slant.rotation.z = -(d.slant ?? 0) * side;
    slant.add(upper);
    g.add(slant, lower);
    head.add(g);
    out.push({ group: g, look, upper, lower, side, d });
  }
  return out;
}

const tmp = new THREE.Vector3();
/**
 * Pose the eyes: `open` 0..1 (1 = as designed, 0 = shut), `squint` lifts the lower lids,
 * `wide` opens them past their rest; the pupils turn toward `target` (world space).
 */
export function poseEyes(
  eyes: EyeRig[],
  open: number,
  squint: number,
  wide: number,
  target: THREE.Vector3 | null,
) {
  for (const e of eyes) {
    const rest = Math.max(0, e.d.rest - wide * 0.45);
    const shut = Math.min(1, 1 - (1 - rest) * open);
    e.upper.rotation.x = UP_OPEN + (UP_SHUT - UP_OPEN) * shut;
    const lo = Math.min(1, (e.d.lower ?? 0) + squint) * Math.min(1, 0.3 + open);
    e.lower.rotation.x = LO_OPEN + (LO_UP - LO_OPEN) * lo;
    let yaw = 0;
    let pitch = 0;
    if (target) {
      e.group.worldToLocal(tmp.copy(target));
      yaw = Math.atan2(tmp.x, Math.max(0.01, tmp.z));
      pitch = -Math.atan2(tmp.y, Math.hypot(tmp.x, tmp.z));
    }
    const lim = 0.42;
    e.look.rotation.set(
      Math.max(-lim * 0.7, Math.min(lim * 0.7, pitch)),
      Math.max(-lim, Math.min(lim, yaw)),
      0,
    );
  }
}
