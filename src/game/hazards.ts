/**
 * Course hazards and creatures for Blender tracks, driven by track.json entities and
 * the collision surfaces under the wheels:
 *
 *   lava        a burning bounce (think of a cartoon hop off a hot stove): an upward
 *               kick, a push back towards the road, a sizzle and a yelp, and a speed
 *               penalty. You keep steering in the air, and you're immune for a moment
 *               after. Burn yourself three times in a few seconds and you're put back
 *               at the last checkpoint, held still briefly (the time penalty).
 *   deep water  a splash, then you bob in the water, slow, and are fished out at the
 *               last checkpoint after a moment. Shallow water is just a slow surface
 *               (with a splash going in).
 *   respawn     { "type": "respawn", "from": 820, "to": 845, "at": 852 }: falling in
 *               while between `from` and `to` along the lap (a jump's gap) puts you
 *               back at `at` instead of the last checkpoint, so a missed jump never
 *               loops.
 *   dinosaur    { "type": "dinosaur", "route": "Dino Path", "speed": 2.2 }: a friendly
 *               long-neck that walks round a path from route.json (draw it in Blender
 *               as a curve and mark it as a route). It stops when a kart comes close,
 *               nudges karts aside (it never traps them) and never jumps about.
 *   waterfall   { "type": "waterfall", "x", "y", "z", "top", "width", "heading" }:
 *               spray at its foot and its roar nearby; driving through it splashes.
 *   campfire    { "type": "campfire", "x", "y", "z" }: smoke and embers rising from a
 *               little bonfire (the fire itself is scenery). Purely visual.
 *   torch       { "type": "torch", "x", "y", "z" }: a torch flame (the torch is scenery).
 *               The few torches nearest the camera cast flickering warm light on the
 *               road, the walls and the karts, and drop the odd ember. Purely visual.
 *   bubbles     { "type": "bubbles", "x", "y", "z", "r" }: a bubbling pool: glowing
 *               bubbles rising and popping over it, and now and then a big burp of
 *               swamp gas. Purely visual.
 *   fireflies   { "type": "fireflies", "rate": 40, "radius": 36 }: little glowing
 *               motes drifting in the air round the camera. Purely visual.
 *   dragon      { "type": "dragon", ... } (see game/dragon.ts): a fire-breathing dragon on
 *               a fixed schedule from the race clock. Its fire burns exactly like
 *               lava (the same bounce, immunity and three-strikes respawn).
 *   eruption    { "type": "eruption", "x", "y", "z", "period": 12, "offset": 0 }: a
 *               volcano erupting on a fixed beat of the race clock: a rumble, then a
 *               blast of glowing lava bombs and a flash of red light, with a fountain
 *               of fire between. Purely visual.
 *   ashfall     { "type": "ashfall", "rate": 60, "radius": 40 }: grey ash drifting down
 *               and embers floating up round the camera. Purely visual.
 *   steam       { "type": "steam", "x", "y", "z" }: a vent puffing steam. Purely visual.
 *   pterosaur   { "type": "pterosaur", "route": "Flyer Path", "speed": 13, "scale": 1.6 }:
 *               a pterosaur circling high over the course along a route (its height
 *               comes from the route), flapping and gliding, banking into turns, with
 *               a cry now and then. Purely visual: it never comes down to the karts.
 *
 * Nothing here changes how the kart drives: it only reacts to where the kart is, the
 * way an item hit does (a vertical kick, a slower speed, a respawn).
 */
import * as THREE from "three";
import type { Sfx } from "../audio/sfx";
import { createKartState, type KartState } from "../vehicles/kart";
import type { GroundQuery } from "../physics/ground";
import type { Track } from "../world/track";
import type { SolidCircle } from "../world/solids";
import type { RouteFile } from "../world/trackPackage";
import { createDinoView, type DinoView } from "../render/dinosaur";
import { createPterosaurView, type PterosaurView } from "../render/pterosaur";
import { createPartyDinoView, DANCES, type Dance, type PartyDinoView } from "../render/partyDino";
import { createParticles } from "../render/particles";
import {
  createDragonFire,
  createDragonView,
  type DragonFireView,
  type DragonView,
} from "../render/dragon";
import {
  dragonBurns,
  dragonPhase,
  parseDragon,
  type DragonConfig,
  type DragonPhase,
} from "./dragon";

export interface HazardConfig {
  lavaBounce: number;
  lavaPush: number;
  lavaKeep: number;
  lavaImmuneSec: number;
  lavaStrikes: number;
  lavaStrikeWindowSec: number;
  lavaPenaltySec: number;
  deepWaterSec: number;
  deepWaterSink: number;
  splashSpeed: number;
  recoverImmuneSec: number;
  dinoSpeed: number;
  dinoYieldRadius: number;
  dinoBodyRadius: number;
  dinoSlow: number;
  waterfallRadius: number;
  volume: number;
}

/** Where to put a kart back: a point on the road and the way to face. */
export interface Spot {
  x: number;
  y: number;
  z: number;
  heading: number;
}

interface KartHazard {
  immune: number;
  strikes: number[];
  hold: number;
  holdAt?: Spot;
  deep: number;
  lastSurface?: string;
  /** How far the kart model sinks into water (visual). */
  sink: number;
  /** Burnt: a little smoke trail while it lasts. */
  smoking: number;
}

interface Dino {
  path: { x: number; z: number; d: number }[];
  length: number;
  d: number;
  speed: number;
  pace: number;
  x: number;
  y: number;
  z: number;
  heading: number;
  look: number;
  solids: SolidCircle[];
  view?: DinoView;
  callIn: number;
  stepIn: number;
}

interface Campfire {
  x: number;
  y: number;
  z: number;
  /** Time banked towards the next puff. */
  acc: number;
}

interface Flyer {
  path: { x: number; y: number; z: number; d: number }[];
  length: number;
  d: number;
  speed: number;
  heading: number;
  bank: number;
  view?: PterosaurView;
  callIn: number;
}

/** How many torches light the scene at once (the ones nearest the camera). */
export const TORCH_LIGHTS = 4;

interface Fall {
  x: number;
  y: number;
  z: number;
  top: number;
  width: number;
  heading: number;
}

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export interface HazardEvents {
  /** The kart was burnt by lava (index). */
  burnt?: boolean;
  /** Splashed into water. */
  splashed?: "shallow" | "deep";
  /** Put back on the road. */
  respawned?: Spot;
}

export interface Hazards {
  /** Called once per kart per physics step, after it has moved. */
  stepKart(
    i: number,
    s: KartState,
    surface: string | undefined,
    lastGate: Spot,
    dt: number,
  ): HazardEvents;
  /** Once per physics step, after the karts: creatures walk. */
  step(karts: KartState[], dt: number): void;
  /** Solid circles of anything that walks about (for the usual solid collision). */
  readonly solids: SolidCircle[];
  /** Surfaces this module looks after (the session shouldn't respawn on them). */
  handles(surface: string | undefined): boolean;
  /** The kart's visual sink into water, metres. */
  sinkOf(i: number): number;
  /** Where a kart here should be put back, if a respawn zone says (else undefined). */
  respawnSpot(x: number, y: number, z: number): Spot | undefined;
  render(t: number, dt: number, listener: { x: number; y: number; z: number }): void;
  readonly dinos: { x: number; y: number; z: number }[];
  /** Where the flyers are (for tests and the camera). */
  readonly flyers: { x: number; y: number; z: number }[];
  dispose(): void;
}

export function createHazards(opts: {
  root: THREE.Object3D;
  track: Track;
  entities: unknown[];
  routes: RouteFile["routes"];
  makeGround: () => GroundQuery;
  sfx?: Sfx;
  cfg: HazardConfig;
  karts: number;
  /** Demo / headless: no sound. */
  quiet?: boolean;
  /** No 3D (tests). */
  headless?: boolean;
  /** The race clock (seconds; negative in the countdown). Timed hazards (the dragon)
   * follow it, so every race sees the same attacks. Defaults to the hazards' own. */
  clock?: () => number;
}): Hazards {
  const { cfg, track } = opts;
  const vol = () => (opts.quiet ? 0 : cfg.volume);
  const per: KartHazard[] = Array.from({ length: opts.karts }, () => ({
    immune: 0,
    strikes: [],
    hold: 0,
    deep: 0,
    sink: 0,
    smoking: 0,
  }));
  const group = new THREE.Group();
  group.name = "hazards";
  if (!opts.headless) opts.root.add(group);
  const spray = opts.headless ? undefined : createParticles(group, { max: 400, size: 0.55 });
  const smoke = opts.headless
    ? undefined
    : createParticles(group, { max: 200, size: 0.8, gravity: 2.5, opacity: 0.8 });
  const sparks = opts.headless
    ? undefined
    : createParticles(group, { max: 160, size: 0.4, gravity: -6, additive: true });
  // Snow: created only on tracks that ask for it (see the snowfall entity).
  let snow: ReturnType<typeof createParticles> | undefined;

  // ---------------------------------------------------------------- entities
  const zones: { from: number; to: number; at: number }[] = [];
  const dinos: Dino[] = [];
  const falls: Fall[] = [];
  const fires: Campfire[] = [];
  const torches: { x: number; y: number; z: number; acc: number }[] = [];
  let snowfall: { rate: number; radius: number; acc: number } | undefined;
  /** Bubbling pools, and fireflies (see the bubbles and fireflies entities). */
  const pools: { x: number; y: number; z: number; r: number; acc: number; burp: number }[] = [];
  let fireflies: { rate: number; radius: number; acc: number } | undefined;
  /** Dragons, and what they were doing last frame (for their cues). */
  const dragons: {
    cfg: DragonConfig;
    view?: DragonView;
    flames?: DragonFireView;
    marker?: THREE.Mesh;
    last: DragonPhase;
    acc: number;
  }[] = [];
  let fire: ReturnType<typeof createParticles> | undefined;
  const eruptions: {
    x: number;
    y: number;
    z: number;
    period: number;
    offset: number;
    last: number;
    light?: THREE.PointLight;
  }[] = [];
  let ashfall: { rate: number; radius: number; acc: number } | undefined;
  const vents: { x: number; y: number; z: number; acc: number }[] = [];
  let bombs: ReturnType<typeof createParticles> | undefined;
  let ash: ReturnType<typeof createParticles> | undefined;
  let glowing: ReturnType<typeof createParticles> | undefined;
  const flyers: (Flyer & { x: number; y: number; z: number })[] = [];
  /** Partygoers: dancing on the spot, or round a conga circle (`ring`). */
  const party: {
    x: number;
    y: number;
    z: number;
    heading: number;
    dance: Dance;
    phase: number;
    ring?: { x: number; y: number; z: number; r: number; speed: number; at: number };
    view?: PartyDinoView;
  }[] = [];
  const ground = opts.makeGround();
  for (const e of opts.entities) {
    if (!isObj(e)) continue;
    if (e.type === "respawn")
      zones.push({ from: num(e.from, 0), to: num(e.to, 0), at: num(e.at, 0) });
    else if (e.type === "campfire")
      fires.push({ x: num(e.x, 0), y: num(e.y, 0), z: num(e.z, 0), acc: 0 });
    else if (e.type === "snowfall")
      snowfall = {
        rate: Math.max(0, num(e.rate, 100)),
        radius: Math.max(5, num(e.radius, 40)),
        acc: 0,
      };
    else if (e.type === "bubbles")
      pools.push({
        x: num(e.x, 0),
        y: num(e.y, 0),
        z: num(e.z, 0),
        r: Math.max(0.5, num(e.r, 3)),
        acc: 0,
        burp: 2 + Math.random() * 6,
      });
    else if (e.type === "eruption") {
      const er = {
        x: num(e.x, 0),
        y: num(e.y, 0),
        z: num(e.z, 0),
        period: Math.max(4, num(e.period, 12)),
        offset: num(e.offset, 0),
        last: -1,
        light: undefined as THREE.PointLight | undefined,
      };
      if (!opts.headless) {
        er.light = new THREE.PointLight(0xff5a20, 0, 1400, 1.1);
        er.light.position.set(er.x, er.y + 40, er.z);
        group.add(er.light);
      }
      eruptions.push(er);
    } else if (e.type === "ashfall")
      ashfall = {
        rate: Math.max(0, num(e.rate, 60)),
        radius: Math.max(5, num(e.radius, 40)),
        acc: 0,
      };
    else if (e.type === "steam")
      vents.push({ x: num(e.x, 0), y: num(e.y, 0), z: num(e.z, 0), acc: 0 });
    else if (e.type === "dragon") {
      const cfg = parseDragon(e);
      let marker: THREE.Mesh | undefined;
      if (!opts.headless) {
        // The burn zone, glowing on the road while the dragon draws breath.
        marker = new THREE.Mesh(
          new THREE.PlaneGeometry(cfg.fire.width, cfg.fire.length),
          new THREE.MeshBasicMaterial({
            color: 0xff3a10,
            transparent: true,
            opacity: 0,
            depthWrite: false,
            side: THREE.DoubleSide,
          }),
        );
        marker.rotation.order = "YXZ";
        marker.rotation.set(-Math.PI / 2, cfg.fire.heading, 0);
        marker.position.set(cfg.fire.x, cfg.fire.y + 0.25, cfg.fire.z);
        marker.renderOrder = 3;
        group.add(marker);
      }
      dragons.push({
        cfg,
        view: opts.headless
          ? undefined
          : createDragonView(group, { x: cfg.x, y: cfg.y, z: cfg.z }, cfg.heading, cfg.scale),
        marker,
        flames: opts.headless ? undefined : createDragonFire(group, cfg.fire),
        last: "idle",
        acc: 0,
      });
    } else if (e.type === "fireflies")
      fireflies = {
        rate: Math.max(0, num(e.rate, 30)),
        radius: Math.max(5, num(e.radius, 30)),
        acc: 0,
      };
    else if (e.type === "torch")
      torches.push({ x: num(e.x, 0), y: num(e.y, 0), z: num(e.z, 0), acc: Math.random() });
    else if (e.type === "partygoer") {
      const dance = (DANCES as readonly string[]).includes(String(e.dance))
        ? (e.dance as Dance)
        : "bounce";
      party.push({
        x: num(e.x, 0),
        y: num(e.y, 0),
        z: num(e.z, 0),
        heading: num(e.heading, 0),
        dance,
        phase: party.length * 0.37,
        view: opts.headless ? undefined : createPartyDinoView(group, num(e.variant, party.length)),
      });
    } else if (e.type === "conga") {
      const count = Math.max(1, Math.min(16, Math.round(num(e.count, 6))));
      const r = Math.max(2, num(e.radius, 6));
      for (let k = 0; k < count; k++)
        party.push({
          x: num(e.x, 0),
          y: num(e.y, 0),
          z: num(e.z, 0),
          heading: 0,
          dance: "conga",
          // In step: the whole line dances together.
          phase: 0,
          ring: {
            x: num(e.x, 0),
            y: num(e.y, 0),
            z: num(e.z, 0),
            r,
            speed: num(e.speed, 1.4),
            at: (k / count) * Math.PI * 2 * 0.8,
          },
          view: opts.headless ? undefined : createPartyDinoView(group, k + 2, 0.95),
        });
    } else if (e.type === "pterosaur") {
      const r = opts.routes.find((q) => q.id === e.route);
      if (!r || r.points.length < 3) continue;
      let d = 0;
      const path = r.points.map((p, k) => {
        if (k) d += Math.hypot(p.x - r.points[k - 1]!.x, p.z - r.points[k - 1]!.z);
        return { x: p.x, y: p.y, z: p.z, d };
      });
      const first = r.points[0]!;
      const last = r.points[r.points.length - 1]!;
      flyers.push({
        path,
        length: d + Math.hypot(first.x - last.x, first.z - last.z),
        d: num(e.start, 0),
        speed: num(e.speed, 12),
        heading: 0,
        bank: 0,
        x: first.x,
        y: first.y,
        z: first.z,
        view: opts.headless ? undefined : createPterosaurView(group, num(e.scale, 1)),
        callIn: 5,
      });
    } else if (e.type === "waterfall")
      falls.push({
        x: num(e.x, 0),
        y: num(e.y, 0),
        z: num(e.z, 0),
        top: num(e.top, 10),
        width: num(e.width, 10),
        heading: num(e.heading, 0),
      });
    else if (e.type === "dinosaur") {
      const r = opts.routes.find((q) => q.id === e.route);
      if (!r || r.points.length < 3) continue;
      const path: Dino["path"] = [];
      let d = 0;
      r.points.forEach((p, k) => {
        if (k) d += Math.hypot(p.x - r.points[k - 1]!.x, p.z - r.points[k - 1]!.z);
        path.push({ x: p.x, z: p.z, d });
      });
      const first = r.points[0]!;
      const last = r.points[r.points.length - 1]!;
      const length = d + Math.hypot(first.x - last.x, first.z - last.z);
      const scale = num(e.scale, 1);
      const dino: Dino = {
        path,
        length,
        d: num(e.start, 0),
        speed: num(e.speed, cfg.dinoSpeed),
        pace: 1,
        x: first.x,
        y: first.y,
        z: first.z,
        heading: 0,
        look: 0,
        solids: [0, 1].map(() => ({
          kind: "circle" as const,
          look: "creature" as const,
          x: 0,
          z: 0,
          radius: cfg.dinoBodyRadius * scale,
          height: 1e3,
        })),
        view: opts.headless ? undefined : createDinoView(group, scale),
        callIn: 6,
        stepIn: 0,
      };
      dinos.push(dino);
    }
  }
  const solids: SolidCircle[] = dinos.flatMap((d) => d.solids);

  function pathAt(dn: Dino, d: number) {
    d = ((d % dn.length) + dn.length) % dn.length;
    const p = dn.path;
    let i = p.length - 1;
    for (let k = 1; k < p.length; k++)
      if (p[k]!.d > d) {
        i = k - 1;
        break;
      }
    const a = p[i]!;
    const b = p[(i + 1) % p.length]!;
    const span = (i + 1 < p.length ? b.d : dn.length) - a.d;
    const f = span > 0 ? (d - a.d) / span : 0;
    return { x: a.x + (b.x - a.x) * f, z: a.z + (b.z - a.z) * f };
  }

  function placeDino(dn: Dino) {
    const a = pathAt(dn, dn.d);
    const b = pathAt(dn, dn.d + 2);
    dn.x = a.x;
    dn.z = a.z;
    dn.heading = Math.atan2(b.x - a.x, b.z - a.z);
    dn.y = ground.at(dn.x, dn.z, dn.y + 2).height;
    // Two circles: chest and hips, along the body.
    const fx = Math.sin(dn.heading);
    const fz = Math.cos(dn.heading);
    const s = dn.solids[0]!.radius / cfg.dinoBodyRadius;
    dn.solids[0]!.x = dn.x + fx * 2.2 * s;
    dn.solids[0]!.z = dn.z + fz * 2.2 * s;
    dn.solids[1]!.x = dn.x - fx * 1.6 * s;
    dn.solids[1]!.z = dn.z - fz * 1.6 * s;
  }
  for (const d of dinos) {
    d.y = ground.at(d.x, d.z, d.y + 50).height;
    placeDino(d);
  }

  /** A smooth point on a flyer's loop (Catmull-Rom through the route's points). */
  function flyAt(f: Flyer, d: number) {
    d = ((d % f.length) + f.length) % f.length;
    const p = f.path;
    const n = p.length;
    let i = n - 1;
    for (let k = 1; k < n; k++)
      if (p[k]!.d > d) {
        i = k - 1;
        break;
      }
    const span = (i + 1 < n ? p[i + 1]!.d : f.length) - p[i]!.d;
    const u = span > 0 ? (d - p[i]!.d) / span : 0;
    const P = (k: number) => p[(((i + k) % n) + n) % n]!;
    const cr = (a: number, b: number, c: number, e: number) =>
      0.5 *
      (2 * b +
        (-a + c) * u +
        (2 * a - 5 * b + 4 * c - e) * u * u +
        (-a + 3 * b - 3 * c + e) * u * u * u);
    const [a, b, c, e] = [P(-1), P(0), P(1), P(2)];
    return {
      x: cr(a.x, b.x, c.x, e.x),
      y: cr(a.y, b.y, c.y, e.y),
      z: cr(a.z, b.z, c.z, e.z),
    };
  }
  function placeFlyer(f: (typeof flyers)[number], dt: number) {
    const a = flyAt(f, f.d);
    const b = flyAt(f, f.d + 4);
    const heading = Math.atan2(b.x - a.x, b.z - a.z);
    if (dt > 0) {
      // Bank into the turn: how fast the heading is changing.
      const turn = (((heading - f.heading + 3 * Math.PI) % (2 * Math.PI)) - Math.PI) / dt;
      const want = Math.max(-0.7, Math.min(0.7, turn * 0.9));
      f.bank += (want - f.bank) * (1 - Math.exp(-2 * dt));
    }
    f.heading = heading;
    f.x = a.x;
    f.y = a.y;
    f.z = a.z;
  }
  for (const f of flyers) placeFlyer(f, 0);

  // The torchlight: a few warm point lights, moved to the torches nearest the camera.
  const torchLights: THREE.PointLight[] = [];
  if (torches.length && !opts.headless)
    for (let k = 0; k < Math.min(TORCH_LIGHTS, torches.length); k++) {
      const l = new THREE.PointLight(0xffa04a, 0, 20, 1.4);
      l.castShadow = false;
      group.add(l);
      torchLights.push(l);
    }

  /** The route position `at` metres along the lap, as a respawn spot. */
  function spotAt(at: number): Spot {
    const ss = track.samples;
    const L = track.length;
    const d = ((at % L) + L) % L;
    let best = ss[0]!;
    // A hair of slack: (at % L + L) % L can land a rounding error short of a sample's
    // own distance (it differs between JavaScript engines), which picked the one before.
    for (const q of ss) if (q.dist <= d + 1e-6) best = q;
    return {
      x: best.pos.x,
      y: best.pos.y,
      z: best.pos.z,
      heading: Math.atan2(best.forward.x, best.forward.z),
    };
  }

  /** The route sample nearest a point (height counts, for layered tracks). */
  function nearestSample(x: number, y: number, z: number) {
    let near = track.samples[0]!;
    let nd = Infinity;
    for (const q of track.samples) {
      const d = (q.pos.x - x) ** 2 + (q.pos.z - z) ** 2 + ((q.pos.y - y) * 2) ** 2;
      if (d < nd) {
        nd = d;
        near = q;
      }
    }
    return near;
  }

  function respawnSpot(x: number, y: number, z: number): Spot | undefined {
    if (!zones.length) return undefined;
    const p = nearestSample(x, y, z).dist;
    for (const zn of zones) if (p >= zn.from && p <= zn.to) return spotAt(zn.at);
    return undefined;
  }

  function putBack(s: KartState, at: Spot) {
    const bananas = s.bananas;
    Object.assign(s, createKartState(at.x, at.z, at.heading, at.y));
    s.bananas = bananas;
  }

  let rush: ReturnType<Sfx["rush"]> | undefined;
  /** Seconds of racing so far (for counting burns), advanced by step(). */
  let clock = 0;
  const lastPos = per.map(() => ({ x: NaN, z: NaN }));

  const tmpTarget = new THREE.Vector3();
  const tmpMouth = new THREE.Vector3();
  /** The race clock the timed hazards follow. */
  const raceClock = () => (opts.clock ? opts.clock() : clock);

  /**
   * The burning bounce, shared by lava and dragon fire: up, back towards the road and
   * slower, with a sizzle; three in a few seconds and you're put back at the last
   * checkpoint, held still a moment.
   */
  function burn(i: number, s: KartState, h: KartHazard, ev: HazardEvents, back: () => Spot) {
    h.strikes = h.strikes.filter((t) => clock - t < cfg.lavaStrikeWindowSec);
    h.strikes.push(clock);
    ev.burnt = true;
    if (h.strikes.length >= cfg.lavaStrikes) {
      // Too many: back to the checkpoint, held still for a moment.
      const at = back();
      putBack(s, at);
      h.hold = cfg.lavaPenaltySec;
      h.holdAt = at;
      h.strikes = [];
      h.immune = cfg.recoverImmuneSec + cfg.lavaPenaltySec;
      ev.respawned = at;
      if (i === 0) opts.sfx?.recover(vol());
    } else {
      // Up, and back towards the road, slower.
      const near = nearestSample(s.x, s.y, s.z);
      const dx = near.pos.x - s.x;
      const dz = near.pos.z - s.z;
      const dl = Math.hypot(dx, dz) || 1;
      const vx = Math.sin(s.velAngle) * s.speed * cfg.lavaKeep + (dx / dl) * cfg.lavaPush;
      const vz = Math.cos(s.velAngle) * s.speed * cfg.lavaKeep + (dz / dl) * cfg.lavaPush;
      s.speed = Math.hypot(vx, vz);
      s.velAngle = Math.atan2(vx, vz);
      s.vy = cfg.lavaBounce;
      s.y += 0.05;
      s.grounded = false;
      h.immune = cfg.lavaImmuneSec;
      h.smoking = 1.4;
      if (i === 0) opts.sfx?.sizzle(vol());
    }
    sparks?.burst(s.x, s.y + 0.4, s.z, 18, 4, 7, 0.7, 0xffa030);
    smoke?.burst(s.x, s.y + 0.6, s.z, 8, 1.5, 1.5, 1.1, 0x5a4a48);
  }

  const hazards: Hazards = {
    solids,
    dinos,
    flyers,
    handles: (surface) => surface === "lava" || surface === "deep_water",
    sinkOf: (i) => per[i]?.sink ?? 0,
    respawnSpot,
    stepKart(i, s, surface, lastGate, dt) {
      const h = per[i]!;
      const ev: HazardEvents = {};
      h.immune = Math.max(0, h.immune - dt);
      h.smoking = Math.max(0, h.smoking - dt);
      // Held at a checkpoint (the penalty after too many burns).
      if (h.hold > 0) {
        h.hold -= dt;
        if (h.holdAt) putBack(s, h.holdAt);
        return ev;
      }
      const ground = s.grounded ? surface : undefined;
      const back = () => respawnSpot(s.x, s.y, s.z) ?? lastGate;
      // ---- lava, and dragon fire: the burning bounce
      const t = raceClock();
      const scorched = ground === "lava";
      const flamed = dragons.some((d) => dragonBurns(d.cfg, t, s.x, s.y, s.z));
      if ((scorched || flamed) && h.immune <= 0) burn(i, s, h, ev, back);
      // ---- water
      const wet = ground === "water" || ground === "deep_water";
      if (
        wet &&
        h.lastSurface !== ground &&
        h.lastSurface !== "water" &&
        h.lastSurface !== "deep_water"
      ) {
        const big = ground === "deep_water" || Math.abs(s.speed) > 15;
        ev.splashed = ground === "deep_water" ? "deep" : "shallow";
        spray?.burst(s.x, s.y + 0.2, s.z, big ? 28 : 14, big ? 5 : 3, big ? 7 : 4.5, 0.9, 0xd8f4ff);
        if (i === 0) opts.sfx?.splash(vol(), big);
      }
      if (wet && Math.abs(s.speed) > cfg.splashSpeed && Math.random() < 0.5) {
        // The wake.
        const side = Math.random() < 0.5 ? -1 : 1;
        spray?.emit(
          s.x + Math.cos(s.heading) * side * 0.9,
          s.y + 0.1,
          s.z - Math.sin(s.heading) * side * 0.9,
          Math.cos(s.heading) * side * 2,
          2.5 + Math.random() * 2,
          -Math.sin(s.heading) * side * 2,
          0.5,
          0xe8fbff,
        );
      }
      if (ground === "deep_water") {
        h.deep += dt;
        if (h.deep > cfg.deepWaterSec) {
          const at = back();
          putBack(s, at);
          h.deep = 0;
          h.immune = cfg.recoverImmuneSec;
          ev.respawned = at;
          if (i === 0) opts.sfx?.recover(vol());
        }
      } else if (s.grounded) h.deep = 0;
      const sinkTo = ground === "deep_water" ? cfg.deepWaterSink : ground === "water" ? 0.12 : 0;
      h.sink += (sinkTo - h.sink) * (1 - Math.exp(-8 * dt));
      if (h.smoking > 0 && Math.random() < 0.25)
        smoke?.emit(s.x, s.y + 1, s.z, 0, 1.5, 0, 0.8, 0x6a5a58);
      if (s.grounded) h.lastSurface = surface;
      // Driving through a waterfall: a drenching splash.
      const lp = lastPos[i]!;
      for (const f of falls)
        if (!Number.isNaN(lp.x) && throughFall(f, lp.x, lp.z, s.x, s.z, s.y)) {
          spray?.burst(s.x, s.y + 1.2, s.z, 30, 4, 3, 0.8, 0xe8fbff);
          if (i === 0) opts.sfx?.splash(vol(), true);
          ev.splashed = "shallow";
        }
      lp.x = s.x;
      lp.z = s.z;
      return ev;
    },
    step(karts, dt) {
      clock += dt;
      for (const f of flyers) {
        f.d += f.speed * dt;
        placeFlyer(f, dt);
        f.callIn -= dt;
        if (f.callIn <= 0) {
          f.callIn = 7 + Math.random() * 6;
          const k = karts[0];
          const near = k ? Math.hypot(k.x - f.x, k.y - f.y, k.z - f.z) : Infinity;
          if (near < 110) opts.sfx?.screech(vol() * Math.max(0.15, 1 - near / 110));
        }
      }
      for (const dn of dinos) {
        // Stop for anything close; set off again gently once it's clear.
        let close = Infinity;
        let lookX = 0;
        let lookZ = 0;
        for (const k of karts) {
          const d = Math.hypot(k.x - dn.x, k.z - dn.z);
          if (d < close) {
            close = d;
            lookX = k.x;
            lookZ = k.z;
          }
        }
        const goal = close < cfg.dinoYieldRadius ? 0 : 1;
        dn.pace += (goal - dn.pace) * (1 - Math.exp(-(goal ? 0.8 : 4) * dt));
        dn.d += dn.speed * dn.pace * dt;
        placeDino(dn);
        // Turn its head towards a nearby kart.
        const want =
          close < 40
            ? Math.max(
                -1,
                Math.min(
                  1,
                  ((Math.atan2(lookX - dn.x, lookZ - dn.z) - dn.heading + 3 * Math.PI) %
                    (2 * Math.PI)) -
                    Math.PI,
                ),
              )
            : 0;
        dn.look += (want - dn.look) * (1 - Math.exp(-2 * dt));
        // Bumping into it slows you a little more than a tree would.
        for (const k of karts)
          for (const c of dn.solids)
            if (Math.hypot(k.x - c.x, k.z - c.z) < c.radius + 1.2 && k.y < dn.y + 4)
              k.speed *= Math.pow(cfg.dinoSlow, dt * 4);
        dn.callIn -= dt;
        if (dn.callIn <= 0) {
          dn.callIn = 9 + (dn.d % 5);
          if (close < 60) opts.sfx?.dinoCall(vol() * Math.max(0.2, 1 - close / 60));
        }
        dn.stepIn -= dt * dn.pace;
        if (dn.stepIn <= 0) {
          dn.stepIn = 0.7;
          if (close < 30 && dn.pace > 0.3) opts.sfx?.thud(vol() * (1 - close / 30));
        }
      }
    },
    render(t, dt, listener) {
      for (const dn of dinos)
        dn.view?.update(dn.x, dn.y, dn.z, dn.heading, dn.d, dn.pace, dn.look, t);
      for (const p of party) {
        if (p.ring) {
          // Round the circle, counter-clockwise, facing the way they go.
          const a = p.ring.at + (t * p.ring.speed) / p.ring.r;
          p.x = p.ring.x + Math.cos(a) * p.ring.r;
          p.z = p.ring.z + Math.sin(a) * p.ring.r;
          p.heading = Math.atan2(-Math.sin(a), Math.cos(a));
          p.y = ground.at(p.x, p.z, p.ring.y + 2).height;
        }
        p.view?.update(p.x, p.y, p.z, p.heading, p.dance, t, p.phase);
      }
      for (const f of flyers) {
        // Flap for a while, then glide: the beat comes and goes along the loop.
        const flap = Math.max(0, Math.min(1, 0.5 + 1.6 * Math.sin(f.d / 38)));
        f.view?.update(f.x, f.y, f.z, f.heading, f.bank, flap, t);
      }
      if (torchLights.length) {
        // The nearest torches (a partial sort: there are only a few lights).
        const near = torches
          .map((q) => ({
            q,
            d: (q.x - listener.x) ** 2 + (q.y - listener.y) ** 2 + (q.z - listener.z) ** 2,
          }))
          .sort((a, b) => a.d - b.d)
          .slice(0, torchLights.length);
        near.forEach(({ q, d }, k) => {
          const l = torchLights[k]!;
          l.position.set(q.x, q.y, q.z);
          const fade = Math.max(0, Math.min(1, (60 - Math.sqrt(d)) / 20));
          const flick =
            0.82 + 0.12 * Math.sin(t * 13 + q.acc * 40) + 0.08 * Math.sin(t * 29 + q.acc * 7);
          l.intensity = 34 * fade * flick;
          // The odd ember drifting up from the flame.
          q.acc = (q.acc + dt * 0.9) % 1e3;
          if (fade > 0 && Math.random() < dt * 3)
            sparks?.emit(
              q.x,
              q.y + 0.3,
              q.z,
              (Math.random() - 0.5) * 0.6,
              1.5 + Math.random(),
              (Math.random() - 0.5) * 0.6,
              0.9,
              Math.random() < 0.5 ? 0xffc040 : 0xff7a20,
            );
        });
      }
      // Spray at the foot of each waterfall, and its roar when you're near.
      let nearest = Infinity;
      for (const f of falls) {
        const d = Math.hypot(listener.x - f.x, listener.z - f.z);
        nearest = Math.min(nearest, d);
        if (d > 160 || !spray) continue;
        for (let k = 0; k < 2; k++) {
          const u = (Math.random() - 0.5) * f.width;
          const cx = f.x + Math.cos(f.heading) * u;
          const cz = f.z - Math.sin(f.heading) * u;
          spray.emit(
            cx,
            f.y + 0.2,
            cz,
            (Math.random() - 0.5) * 3,
            3 + Math.random() * 3,
            (Math.random() - 0.5) * 3,
            0.8,
            0xffffff,
          );
        }
      }
      if (falls.length && !opts.quiet) {
        rush ??= opts.sfx?.rush();
        rush?.set(
          nearest < cfg.waterfallRadius
            ? (1 - nearest / cfg.waterfallRadius) * cfg.volume * 0.5
            : 0,
        );
      }
      // Smoke and embers over the campfires you're near.
      for (const f of fires) {
        if (!smoke || Math.hypot(listener.x - f.x, listener.z - f.z) > 140) continue;
        f.acc = Math.min(1, f.acc + dt);
        for (; f.acc > 0.16; f.acc -= 0.16) {
          const j = () => Math.random() - 0.5;
          smoke.emit(
            f.x + j() * 0.6,
            f.y + 1.8,
            f.z + j() * 0.6,
            j() * 0.5,
            1 + Math.random(),
            j() * 0.5,
            2.4,
            0xd2ccc4,
          );
          if (Math.random() < 0.7)
            sparks?.emit(
              f.x + j() * 0.8,
              f.y + 0.9,
              f.z + j() * 0.8,
              j() * 1.4,
              3.2 + Math.random() * 2.5,
              j() * 1.4,
              0.8,
              Math.random() < 0.5 ? 0xffc040 : 0xff6a20,
            );
        }
      }
      // Snow drifting down round the camera, swaying a little in the wind.
      if (snowfall && !opts.headless) {
        snow ??= createParticles(group, { max: 900, size: 0.22, gravity: 0, opacity: 0.95 });
        snowfall.acc = Math.min(2, snowfall.acc + dt * snowfall.rate);
        const r = snowfall.radius;
        for (; snowfall.acc >= 1; snowfall.acc -= 1)
          snow.emit(
            listener.x + (Math.random() - 0.5) * 2 * r,
            listener.y + 6 + Math.random() * 18,
            listener.z + (Math.random() - 0.5) * 2 * r,
            0.8 + Math.sin(t * 0.3) * 0.6 + (Math.random() - 0.5) * 0.6,
            -2.2 - Math.random() * 1.2,
            0.3 + (Math.random() - 0.5) * 0.6,
            8,
            Math.random() < 0.8 ? 0xffffff : 0xdfe6ff,
          );
        snow.step(dt);
      }
      // The dragons: posed for their attack, the burn zone glowing on the road as they
      // draw breath, then the fire (the flames fill exactly the zone that burns).
      if (dragons.length && !opts.headless) {
        fire ??= createParticles(group, { max: 1400, size: 2.2, gravity: 3.5, additive: true });
        const rc = raceClock();
        for (const d of dragons) {
          const { phase, t: pt } = dragonPhase(d.cfg, rc);
          const f = d.cfg.fire;
          tmpTarget.set(f.x, f.y, f.z);
          d.view?.update(phase, pt, t, tmpTarget);
          const far = Math.hypot(listener.x - d.cfg.x, listener.z - d.cfg.z);
          const loud = vol() * Math.max(0, 1 - far / 320);
          if (phase !== d.last) {
            if (phase === "warning" && loud > 0) opts.sfx?.roar(loud);
            if (phase === "breathing" && loud > 0) opts.sfx?.flame(loud);
            d.last = phase;
          }
          if (d.marker) {
            const m = d.marker.material as THREE.MeshBasicMaterial;
            m.opacity =
              phase === "warning"
                ? 0.18 + 0.22 * pt + 0.15 * Math.sin(t * 14)
                : phase === "breathing"
                  ? 0.35
                  : phase === "cooldown"
                    ? 0.35 * (1 - pt)
                    : 0;
          }
          d.view?.mouth(tmpMouth);
          d.flames?.update(phase, pt, t, tmpMouth);
          if (phase !== "breathing" || far > 400) continue;
          d.acc = Math.min(40, d.acc + dt * 420);
          const ca = Math.cos(f.heading);
          const sa = Math.sin(f.heading);
          for (; d.acc >= 1; d.acc -= 1) {
            // A point in the zone: along and across the road.
            const along = (Math.random() - 0.5) * f.length;
            const across = (Math.random() - 0.5) * f.width;
            const px = f.x + sa * along + ca * across;
            const pz = f.z + ca * along - sa * across;
            const col = Math.random() < 0.35 ? 0xffe070 : Math.random() < 0.6 ? 0xff8a20 : 0xff4a10;
            if (Math.random() < 0.3) {
              // The stream from the jaws to the road.
              const life = 0.35;
              fire.emit(
                tmpMouth.x,
                tmpMouth.y,
                tmpMouth.z,
                (px - tmpMouth.x) / life,
                (f.y + 1 - tmpMouth.y) / life - 0.5 * 3.5 * life,
                (pz - tmpMouth.z) / life,
                life,
                col,
              );
            } else {
              fire.emit(
                px,
                f.y + 0.3 + Math.random() * 0.8,
                pz,
                (Math.random() - 0.5) * 1.5,
                2 + Math.random() * 3,
                (Math.random() - 0.5) * 1.5,
                0.45 + Math.random() * 0.45,
                col,
              );
            }
          }
        }
      }
      fire?.step(dt);
      // Eruptions: on their beat of the race clock, a rumble, then a blast of lava bombs
      // arcing out of the crater and a red flash; a fountain of fire in between.
      if (eruptions.length && !opts.headless) {
        bombs ??= createParticles(group, { max: 900, size: 11, gravity: -16, additive: true });
        const rc = raceClock();
        for (const er of eruptions) {
          const beat = Math.floor((rc - er.offset) / er.period);
          const u = rc - er.offset - beat * er.period;
          const far = Math.hypot(listener.x - er.x, listener.z - er.z);
          if (beat !== er.last) {
            er.last = beat;
            if (far < 1500) opts.sfx?.rumble(vol() * Math.max(0.25, 1 - far / 1500));
          }
          // The blast, 1.2 s after the rumble.
          const blast = u - 1.2;
          if (blast >= 0 && blast < dt + 1e-6)
            for (let k = 0; k < 220; k++) {
              const a = Math.random() * Math.PI * 2;
              const sp = 12 + Math.random() * 30;
              bombs.emit(
                er.x,
                er.y + 5,
                er.z,
                Math.cos(a) * sp,
                55 + Math.random() * 55,
                Math.sin(a) * sp,
                4 + Math.random() * 3,
                Math.random() < 0.5 ? 0xffb030 : 0xff5a14,
              );
            }
          if (er.light)
            er.light.intensity = blast >= 0 && blast < 2.5 ? 9000 * Math.exp(-blast * 1.8) : 0;
          // The fountain, always going.
          const n = Math.min(6, Math.floor(Math.random() + dt * 40));
          for (let k = 0; k < n; k++)
            bombs.emit(
              er.x + (Math.random() - 0.5) * 20,
              er.y,
              er.z + (Math.random() - 0.5) * 20,
              (Math.random() - 0.5) * 8,
              35 + Math.random() * 25,
              (Math.random() - 0.5) * 8,
              3.2,
              Math.random() < 0.5 ? 0xff7a20 : 0xffc040,
            );
        }
        bombs.step(dt);
      }
      // Ash drifting down and embers floating up round the camera; steam from vents.
      if ((ashfall || vents.length) && !opts.headless) {
        ash ??= createParticles(group, { max: 700, size: 0.3, gravity: 0, opacity: 0.9 });
        if (ashfall) {
          ashfall.acc = Math.min(3, ashfall.acc + dt * ashfall.rate);
          const r = ashfall.radius;
          for (; ashfall.acc >= 1; ashfall.acc -= 1) {
            const ember = Math.random() < 0.35;
            ash.emit(
              listener.x + (Math.random() - 0.5) * 2 * r,
              listener.y + (ember ? -2 + Math.random() * 6 : 4 + Math.random() * 16),
              listener.z + (Math.random() - 0.5) * 2 * r,
              (Math.random() - 0.5) * 1.6,
              ember ? 1 + Math.random() * 1.5 : -1.5 - Math.random(),
              (Math.random() - 0.5) * 1.6,
              ember ? 2.5 : 7,
              ember
                ? Math.random() < 0.5
                  ? 0xff8a20
                  : 0xffc040
                : Math.random() < 0.5
                  ? 0x7a6e6a
                  : 0x9a8e88,
            );
          }
        }
        for (const v of vents) {
          if (!smoke || Math.hypot(listener.x - v.x, listener.z - v.z) > 140) continue;
          v.acc = Math.min(1, v.acc + dt);
          for (; v.acc > 0.09; v.acc -= 0.09)
            smoke.emit(
              v.x + (Math.random() - 0.5) * 1.5,
              v.y + 0.5,
              v.z + (Math.random() - 0.5) * 1.5,
              (Math.random() - 0.5) * 0.8,
              4 + Math.random() * 3,
              (Math.random() - 0.5) * 0.8,
              1.6,
              0xe8e2dc,
            );
        }
        ash.step(dt);
      }
      // Glowing bubbles over the pools you're near, the odd burp of swamp gas, and
      // fireflies drifting round the camera.
      if ((pools.length || fireflies) && !opts.headless) {
        glowing ??= createParticles(group, { max: 500, size: 0.45, gravity: 0.8, additive: true });
        for (const b of pools) {
          if (Math.hypot(listener.x - b.x, listener.z - b.z) > 130) continue;
          b.acc = Math.min(2, b.acc + dt * (3 + b.r));
          for (; b.acc >= 1; b.acc -= 1) {
            const a = Math.random() * Math.PI * 2;
            const r = Math.sqrt(Math.random()) * b.r * 0.85;
            glowing.emit(
              b.x + Math.cos(a) * r,
              b.y,
              b.z + Math.sin(a) * r,
              0,
              0.6 + Math.random() * 0.8,
              0,
              0.7 + Math.random() * 0.6,
              Math.random() < 0.6 ? 0xa8ff70 : 0xd8ffb0,
            );
          }
          b.burp -= dt;
          if (b.burp <= 0) {
            b.burp = 3 + Math.random() * 7;
            glowing.burst(b.x, b.y + 0.3, b.z, 14, 1.2, 2.2, 1.4, 0x7aff5a);
          }
        }
        if (fireflies) {
          fireflies.acc = Math.min(2, fireflies.acc + dt * fireflies.rate);
          const r = fireflies.radius;
          for (; fireflies.acc >= 1; fireflies.acc -= 1)
            glowing.emit(
              listener.x + (Math.random() - 0.5) * 2 * r,
              listener.y + 0.5 + Math.random() * 9,
              listener.z + (Math.random() - 0.5) * 2 * r,
              (Math.random() - 0.5) * 1.2,
              -0.4 + Math.random() * 0.3,
              (Math.random() - 0.5) * 1.2,
              2.5 + Math.random() * 2.5,
              Math.random() < 0.7 ? 0xeaff7a : 0xfff2a0,
            );
        }
        glowing.step(dt);
      }
      spray?.step(dt);
      smoke?.step(dt);
      sparks?.step(dt);
    },
    dispose() {
      rush?.stop();
      for (const d of dinos) d.view?.dispose();
      for (const f of flyers) f.view?.dispose();
      for (const p of party) p.view?.dispose();
      spray?.dispose();
      snow?.dispose();
      glowing?.dispose();
      fire?.dispose();
      bombs?.dispose();
      ash?.dispose();
      for (const d of dragons) {
        d.view?.dispose();
        d.flames?.dispose();
        if (d.marker) {
          d.marker.geometry.dispose();
          (d.marker.material as THREE.Material).dispose();
        }
      }
      smoke?.dispose();
      sparks?.dispose();
      group.removeFromParent();
    },
  };
  return hazards;
}

/** Does a kart cross a waterfall's sheet this step? (For the splash as you drive through.) */
export function throughFall(f: Fall, ax: number, az: number, bx: number, bz: number, y: number) {
  const nx = Math.sin(f.heading);
  const nz = Math.cos(f.heading);
  const da = (ax - f.x) * nx + (az - f.z) * nz;
  const db = (bx - f.x) * nx + (bz - f.z) * nz;
  if (da * db > 0) return false;
  const u = (bx - f.x) * Math.cos(f.heading) - (bz - f.z) * Math.sin(f.heading);
  return Math.abs(u) < f.width / 2 && y > f.y - 1 && y < f.top;
}
