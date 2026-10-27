/**
 * The boss races' mechanics (Blake, Oct 26: "every boss level should have a crazy
 * mechanic that needs to be mastered"; "lets try all of them": each boss's main pitch and
 * its alternative). They act on you (the boss is their master: it's immune), driven by
 * track.json entities the boss course's build places, on the race clock.
 *
 *   Cinderjaw (Tyrant's Gorge)
 *     heat     fire_sweep { x, y, z, heading, width, depth, period, offset, warn, burn }:
 *              a line of fire across the road on a beat, its glow showing first; drive
 *              through it burning and you take heat. crust_vent { x, y, z, r }: cooled
 *              crust that vents your heat and fires a zipper. A full gauge overheats you
 *              (a spin and most of your speed gone). The HUD shows HEAT.
 *     crumble  crumble { from, to, gap }: the road between `from` and `to` (metres round
 *              the lap) crumbles into lava `gap` metres behind whoever's leading: fall
 *              behind there and you drop into the lava, put back on the edge.
 *
 * Nothing here changes how the kart drives: it only reacts to where the kart is, the way
 * an item hit does (a spin, a slower speed, a boost, a respawn).
 */
import * as THREE from "three";
import {
  createMechanics,
  type MechCtx,
  type Mechanic,
  type MechEvents as Events,
} from "./bossMechs";

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export interface Sweep {
  x: number;
  y: number;
  z: number;
  heading: number;
  width: number;
  depth: number;
  period: number;
  offset: number;
  warn: number;
  burn: number;
}
export interface Vent {
  x: number;
  y: number;
  z: number;
  r: number;
}
export interface Crumble {
  from: number;
  to: number;
  gap: number;
}

export interface BossMechConfig {
  sweeps: Sweep[];
  vents: Vent[];
  crumbles: Crumble[];
  /** The other bosses' mechanics (game/bossMechs.ts), made from these. */
  entities: unknown[];
  variant: "main" | "alt";
}

export function parseBossMech(
  entities: unknown[],
  variant: "main" | "alt" = "main",
): BossMechConfig {
  const c: BossMechConfig = { sweeps: [], vents: [], crumbles: [], entities, variant };
  for (const e of entities) {
    if (!e || typeof e !== "object") continue;
    const o = e as Record<string, unknown>;
    // (Each mechanic is either the course's main one or its alternative.)
    const v = o.variant === "alt" ? "alt" : "main";
    if (v !== variant) continue;
    if (o.type === "fire_sweep")
      c.sweeps.push({
        x: num(o.x, 0),
        y: num(o.y, 0),
        z: num(o.z, 0),
        heading: num(o.heading, 0),
        width: num(o.width, 18),
        depth: num(o.depth, 4),
        period: num(o.period, 5),
        offset: num(o.offset, 0),
        warn: num(o.warn, 1.4),
        burn: num(o.burn, 1.2),
      });
    else if (o.type === "crust_vent")
      c.vents.push({ x: num(o.x, 0), y: num(o.y, 0), z: num(o.z, 0), r: num(o.r, 3) });
    else if (o.type === "crumble")
      c.crumbles.push({ from: num(o.from, 0), to: num(o.to, 0), gap: num(o.gap, 40) });
  }
  return c;
}

const OTHERS = new Set([
  "ice_wall",
  "avalanche",
  "firewall",
  "thin_lake",
  "gust",
  "sandstorm",
  "tide",
  "coil",
  "whirlpool",
  "fireball",
]);
export const hasBossMech = (c: BossMechConfig) =>
  c.sweeps.length + c.vents.length + c.crumbles.length > 0 ||
  c.entities.some((e) => {
    const o = e as Record<string, unknown> | null;
    return Boolean(
      o && OTHERS.has(String(o.type)) && (o.variant === "alt" ? "alt" : "main") === c.variant,
    );
  });

export const HEAT = {
  /** Heat from one pass through a burning sweep. */
  sweep: 38,
  /** Heat a vent takes away. */
  vent: 45,
  /** Heat lost a second, by itself. */
  cool: 3,
  /** Overheated: spin for this long, and keep this much of your speed. */
  spinSec: 1.1,
  keep: 0.35,
  /** After overheating, the gauge starts here. */
  after: 30,
};

export type SweepPhase = "off" | "warn" | "burn";

/** Where a sweep is in its beat at race time `t`. */
export function sweepPhase(s: Sweep, t: number): { phase: SweepPhase; k: number } {
  if (t < 0) return { phase: "off", k: 0 };
  const u = (((t - s.offset) % s.period) + s.period) % s.period;
  const burnAt = s.period - s.burn;
  if (u >= burnAt) return { phase: "burn", k: (u - burnAt) / s.burn };
  if (u >= burnAt - s.warn) return { phase: "warn", k: (u - (burnAt - s.warn)) / s.warn };
  return { phase: "off", k: 0 };
}

/** Is (x, z) in the sweep's strip across the road? */
export function inSweep(s: Sweep, x: number, z: number) {
  const dx = x - s.x;
  const dz = z - s.z;
  // Along the road (the sweep's heading) and across it.
  const along = dx * Math.sin(s.heading) + dz * Math.cos(s.heading);
  const across = dx * Math.cos(s.heading) - dz * Math.sin(s.heading);
  return Math.abs(along) < s.depth / 2 && Math.abs(across) < s.width / 2;
}

export interface MechKart {
  x: number;
  y: number;
  z: number;
  speed: number;
  heading: number;
  spinTime: number;
  spinDir: number;
}

export type MechEvents = Events;

export interface BossMech {
  readonly heat: number;
  /** The crumble's front (metres round the lap behind which the road's gone), or -1. */
  readonly front: number;
  /** Once a physics step, for your kart: `lap` your distance round the race (metres,
   * counting laps), `lead` the leader's. */
  step(
    k: MechKart,
    t: number,
    dt: number,
    lap: number,
    lead: number,
    lapLength: number,
    /** What the other mechanics need (the boss, the item button, in the air). */
    more?: Pick<MechCtx, "boss" | "item" | "airborne">,
  ): MechEvents;
  /** The HUD's gauge, if the course has one. */
  gauge(): { label: string; value: number } | undefined;
  /** A sandstorm's thickness (0..1), or 0. */
  fog(): number;
  /** The tide's sea level, if there's a tide. */
  sea(): number | undefined;
  render(t: number): void;
  dispose(): void;
}

export function createBossMech(opts: {
  cfg: BossMechConfig;
  root?: THREE.Object3D;
  /** The road's centre at a distance round the lap (for the crumble's lava). */
  roadAt?: (s: number) => { x: number; y: number; z: number; heading: number; width: number };
}): BossMech {
  const { cfg } = opts;
  const others: Mechanic[] = createMechanics(cfg.entities, cfg.variant, opts.root);
  let heat = 0;
  const inSweepLast = cfg.sweeps.map(() => false);
  let ventCool = 0;
  let front = -1;
  let dropHold = 0;
  // The sweeps' look: a glowing strip that brightens as it warns, then a wall of flame.
  const group = new THREE.Group();
  group.name = "Boss mechanics";
  opts.root?.add(group);
  const made: (THREE.Material | THREE.BufferGeometry)[] = [];
  const strips = cfg.sweeps.map((s) => {
    const g = new THREE.PlaneGeometry(s.width, s.depth);
    g.rotateX(-Math.PI / 2);
    const m = new THREE.MeshBasicMaterial({
      color: 0xff3a10,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    made.push(g, m);
    const strip = new THREE.Mesh(g, m);
    strip.position.set(s.x, s.y + 0.12, s.z);
    strip.rotation.y = s.heading;
    group.add(strip);
    // The flames: cones along the strip.
    const fg = new THREE.ConeGeometry(0.9, 1, 5);
    fg.translate(0, 0.5, 0);
    const fm = new THREE.MeshBasicMaterial({
      color: 0xffa020,
      transparent: true,
      opacity: 0.85,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    made.push(fg, fm);
    const flames: THREE.Mesh[] = [];
    const n = Math.max(3, Math.round(s.width / 1.6));
    for (let k = 0; k < n; k++) {
      const f = new THREE.Mesh(fg, fm);
      const across = ((k + 0.5) / n - 0.5) * s.width;
      f.position.set(s.x + Math.cos(s.heading) * across, s.y, s.z - Math.sin(s.heading) * across);
      group.add(f);
      flames.push(f);
    }
    return { strip, m, flames };
  });
  const vents = cfg.vents.map((v) => {
    const g = new THREE.CircleGeometry(v.r, 14);
    g.rotateX(-Math.PI / 2);
    const m = new THREE.MeshBasicMaterial({
      color: 0x5fc8ff,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
    });
    made.push(g, m);
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set(v.x, v.y + 0.1, v.z);
    group.add(mesh);
    return { mesh, m };
  });
  // The crumble: the road behind the front shown as lava (a glowing strip over it).
  let lava: { mesh: THREE.Mesh; s0: number; s1: number }[] = [];
  if (opts.roadAt && cfg.crumbles.length) {
    const lm = new THREE.MeshBasicMaterial({ color: 0xff4a10, transparent: true, opacity: 0.92 });
    made.push(lm);
    for (const c of cfg.crumbles)
      for (let s = c.from; s < c.to; s += 6) {
        const p = opts.roadAt(s + 3);
        const g = new THREE.PlaneGeometry(p.width + 1, 6.4);
        g.rotateX(-Math.PI / 2);
        made.push(g);
        const mesh = new THREE.Mesh(g, lm);
        mesh.position.set(p.x, p.y + 0.15, p.z);
        mesh.rotation.y = p.heading;
        mesh.visible = false;
        group.add(mesh);
        lava.push({ mesh, s0: s, s1: s + 6 });
      }
  }
  const mech: BossMech = {
    get heat() {
      return heat;
    },
    get front() {
      return front;
    },
    step(k, t, dt, lap, lead, lapLength, more) {
      const ev: MechEvents = {};
      heat = Math.max(0, heat - HEAT.cool * dt);
      ventCool = Math.max(0, ventCool - dt);
      cfg.sweeps.forEach((s, i) => {
        const inside = inSweep(s, k.x, k.z) && Math.abs(k.y - s.y) < 4;
        const ph = sweepPhase(s, t).phase;
        if (inside && !inSweepLast[i] && ph === "burn") {
          heat += HEAT.sweep;
          ev.burnt = true;
        }
        inSweepLast[i] = inside && ph === "burn" ? true : inside ? inSweepLast[i]! : false;
      });
      if (ventCool <= 0)
        for (const v of cfg.vents)
          if (Math.hypot(k.x - v.x, k.z - v.z) < v.r && Math.abs(k.y - v.y) < 3) {
            heat = Math.max(0, heat - HEAT.vent);
            ventCool = 2.5;
            ev.vented = true;
            break;
          }
      if (heat >= 100) {
        heat = HEAT.after;
        k.spinTime = HEAT.spinSec;
        k.spinDir = Math.random() < 0.5 ? -1 : 1;
        k.speed *= HEAT.keep;
        ev.overheated = true;
      }
      // The crumble: its front follows the leader, `gap` behind; behind it, in a
      // crumbling stretch, the road's gone.
      front = -1;
      dropHold = Math.max(0, dropHold - dt);
      for (const c of cfg.crumbles) {
        const f = lead - c.gap;
        const fl = ((f % lapLength) + lapLength) % lapLength;
        const yl = ((lap % lapLength) + lapLength) % lapLength;
        if (fl >= c.from && fl <= c.to) front = fl;
        // You're in the stretch, behind the front (on the same lap as it), and it's gone.
        if (dropHold <= 0 && yl >= c.from && yl <= c.to && lap < f && f - lap < c.to - c.from) {
          ev.dropAt = Math.min(c.to + 4, fl + 10);
          dropHold = 2;
        }
      }
      if (others.length && opts.roadAt) {
        const ctx: MechCtx = { t, dt, lap, lead, lapLength, roadAt: opts.roadAt, ...more };
        for (const m of others) m.step(k, ctx, ev);
      }
      return ev;
    },
    gauge() {
      if (cfg.sweeps.length || cfg.vents.length)
        return { label: "HEAT", value: Math.min(1, heat / 100) };
      for (const m of others) {
        const g = m.gauge?.();
        if (g) return g;
      }
      return undefined;
    },
    fog() {
      return Math.max(0, ...others.map((m) => m.fog?.() ?? 0));
    },
    sea() {
      for (const m of others) {
        const v = m.sea?.();
        if (v !== undefined) return v;
      }
      return undefined;
    },
    render(t) {
      cfg.sweeps.forEach((s, i) => {
        const { phase, k } = sweepPhase(s, t);
        const v = strips[i]!;
        v.m.opacity =
          phase === "warn"
            ? 0.2 + 0.5 * k + 0.15 * Math.sin(t * 30)
            : phase === "burn"
              ? 0.8
              : 0.06;
        const h = phase === "burn" ? (k < 0.15 ? k / 0.15 : k > 0.85 ? (1 - k) / 0.15 : 1) : 0;
        v.flames.forEach((f, j) => {
          f.visible = h > 0.02;
          f.scale.set(1.2, h * (5.0 + Math.sin(t * 17 + j * 1.7) * 1.4), 1.2);
        });
      });
      vents.forEach((v, i) => (v.m.opacity = 0.3 + 0.2 * Math.sin(t * 3 + i)));
      for (const l of lava) l.mesh.visible = front >= 0 && l.s1 <= front;
      for (const m of others) m.render(t);
    },
    dispose() {
      for (const m of others) m.dispose();
      opts.root?.remove(group);
      for (const m of made) m.dispose();
      lava = [];
    },
  };
  return mech;
}
