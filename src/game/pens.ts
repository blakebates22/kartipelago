/**
 * The Beast Market's pens (Blake, Nov 4: "the animals look bad"; he picked "baby dinos in
 * pens"): a few hatchlings (render/hatchling.ts) in each, waddling about inside its fence,
 * pecking at the hay, looking round, sitting down, squeaking.
 *
 *   pen  { "type": "pen", "x", "y", "z", "w", "d", "heading", "species": "raptor"|"trike"|"stego",
 *          "count": 3, "seed": 1 }   (w across, d deep: the inside of its fence, m)
 */
import { HATCHLING_KINDS, type HatchlingAct, type HatchlingKind } from "../render/hatchling";

export interface PenConfig {
  x: number;
  y: number;
  z: number;
  w: number;
  d: number;
  heading: number;
  kind: HatchlingKind;
  count: number;
  seed: number;
}

export interface Baby {
  /** Where in the pen (its own space: u across, v deep, from its middle). */
  u: number;
  v: number;
  heading: number;
  to: { u: number; v: number } | null;
  act: HatchlingAct;
  /** How long it keeps at what it's doing (s). */
  left: number;
  pace: number;
}

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export function parsePen(e: Record<string, unknown>): PenConfig {
  return {
    x: num(e.x, 0),
    y: num(e.y, 0),
    z: num(e.z, 0),
    w: Math.max(1, num(e.w, 4)),
    d: Math.max(1, num(e.d, 3)),
    heading: num(e.heading, 0),
    kind: HATCHLING_KINDS.includes(e.species as HatchlingKind)
      ? (e.species as HatchlingKind)
      : "raptor",
    count: Math.max(1, Math.min(6, Math.round(num(e.count, 3)))),
    seed: Math.round(num(e.seed, 1)),
  };
}

/** A small repeatable random sequence per pen. */
export function penRng(seed: number) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return ((s >>> 0) % 100000) / 100000;
  };
}

/** The pen's babies, spread about it. */
export function penBabies(c: PenConfig, rnd: () => number): Baby[] {
  return Array.from({ length: c.count }, () => ({
    u: (rnd() - 0.5) * (c.w - 0.8),
    v: (rnd() - 0.5) * (c.d - 0.8),
    heading: rnd() * Math.PI * 2,
    to: null,
    act: "look" as HatchlingAct,
    left: rnd() * 2,
    pace: 0,
  }));
}

const IDLES: HatchlingAct[] = ["peck", "peck", "look", "sit", "squeak"];
const SPEED = 0.7;

/**
 * One step for a pen's babies: walk to where it's going (inside the fence, keeping off
 * the others), then an idle for a while, then off somewhere else.
 */
export function stepPen(c: PenConfig, babies: Baby[], dt: number, rnd: () => number) {
  const mu = c.w / 2 - 0.4;
  const mv = c.d / 2 - 0.4;
  for (const b of babies) {
    b.left -= dt;
    if (b.to) {
      const du = b.to.u - b.u;
      const dv = b.to.v - b.v;
      const dist = Math.hypot(du, dv);
      if (dist < 0.1 || b.left <= 0) {
        b.to = null;
        b.act = IDLES[Math.floor(rnd() * IDLES.length)]!;
        b.left = b.act === "sit" ? 3 + rnd() * 4 : 1 + rnd() * 2.5;
        b.pace = 0;
      } else {
        const want = Math.atan2(du, dv);
        let turn = want - b.heading;
        while (turn > Math.PI) turn -= Math.PI * 2;
        while (turn < -Math.PI) turn += Math.PI * 2;
        b.heading += Math.max(-dt * 4, Math.min(dt * 4, turn));
        const go = Math.min(dist, SPEED * dt) * Math.max(0, Math.cos(turn));
        b.u = Math.max(-mu, Math.min(mu, b.u + Math.sin(b.heading) * go));
        b.v = Math.max(-mv, Math.min(mv, b.v + Math.cos(b.heading) * go));
        b.act = "walk";
        b.pace = 1;
      }
    } else if (b.left <= 0) {
      b.to = { u: (rnd() * 2 - 1) * mu, v: (rnd() * 2 - 1) * mv };
      b.left = 6;
    }
  }
  // (keep off each other)
  for (let i = 0; i < babies.length; i++)
    for (let j = i + 1; j < babies.length; j++) {
      const a = babies[i]!;
      const b = babies[j]!;
      const du = b.u - a.u;
      const dv = b.v - a.v;
      const d = Math.hypot(du, dv);
      if (d > 0 && d < 0.55) {
        const k = (0.55 - d) / 2 / d;
        a.u -= du * k;
        a.v -= dv * k;
        b.u += du * k;
        b.v += dv * k;
      }
    }
}

/** A baby's place in the world (x, z) and its heading. */
export function babyAt(c: PenConfig, b: Baby) {
  const ca = Math.cos(c.heading);
  const sa = Math.sin(c.heading);
  // (u across, v deep: v along the pen's heading)
  return {
    x: c.x + b.u * ca + b.v * sa,
    z: c.z - b.u * sa + b.v * ca,
    heading: c.heading + b.heading,
  };
}
