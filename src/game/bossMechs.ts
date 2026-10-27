/**
 * The other bosses' mechanics (game/bossMech.ts has Cinderjaw's and the frame they all
 * share), each from track.json entities, each acting on you only:
 *
 *   Rimefang (main)  ice_wall { x, y, z, heading, width, across, period, offset, warn }:
 *                    a wall of ice rising across one lane of a divided straight on a beat,
 *                    the frost cracking across it first: be in the other lane. avalanche
 *                    { from, to, gap, speed }: from `from` round the lap, a wall of snow
 *                    chases you downhill; it catches you and you're buried (stopped,
 *                    dug out), the HUD shows how close it is.
 *   Rimefang (alt)   thin_lake { x, y, z, r }: a frozen lake that cracks under you if you
 *                    linger (slow, or stopped): keep moving or go through.
 *   Scorchwind (main) gust { x, y, z, r, dx, dz, period, offset, warn, strength }: a
 *                    crosswind on a beat, sand streaming across first, shoving you toward
 *                    the quicksand at the road's edge; shelter { x, z, r } (rock pillars):
 *                    out of the wind behind them. Sail ramps: a jump in a tailwind goes
 *                    further (a boost as you leave it: tailwind { x, z, r }).
 *   Scorchwind (alt) sandstorm { density }: the whole course in a sandstorm: you see a few
 *                    metres; the beacon fires mark the way (the build's torches).
 *   Tidewyrm (main)  tide { period, low, high, offset }: the sea rising and falling as he
 *                    thrashes; sandbar { x, y, z, r }: a shortcut only above water at low
 *                    tide, buoys at its ends green / amber / red (caught on it flooded,
 *                    you swim slowly); coil { from, to, period, offset }: his back
 *                    breaching from the road there, hump by hump, a swirl first: hit one
 *                    as it rises for a boost, once it's up it knocks you back.
 *   Tidewyrm (alt)   whirlpool { x, y, z, r, spin, fling }: a whirlpool that swings you
 *                    round it and flings you out (a boost, if you leave it facing out).
 *   King Pyrrhax     firewall { from, to, gap, speed }: race 1, a wall of fire chasing you
 *                    (the avalanche's twin). fireball { period, speed }: the rematch: the
 *                    King throws fireballs; press the item button as one reaches you and
 *                    AURIN'S LIGHT sends it back into him.
 */
import * as THREE from "three";

const num = (v: unknown, d: number) => (typeof v === "number" && Number.isFinite(v) ? v : d);

export interface MechKart {
  x: number;
  y: number;
  z: number;
  speed: number;
  heading: number;
  spinTime: number;
  spinDir: number;
}

export interface MechCtx {
  t: number;
  dt: number;
  /** Your distance round the race (metres, counting laps), the leader's, a lap's length. */
  lap: number;
  lead: number;
  lapLength: number;
  roadAt: (s: number) => { x: number; y: number; z: number; heading: number; width: number };
  /** The boss (the King's fireballs come from him). */
  boss?: { x: number; y: number; z: number };
  /** The item button just pressed (AURIN'S LIGHT). */
  item?: boolean;
  /** Your kart's in the air. */
  airborne?: boolean;
}

export interface MechEvents {
  burnt?: boolean;
  overheated?: boolean;
  vented?: boolean;
  /** Put back on the road here (metres round the lap). */
  dropAt?: number;
  buried?: boolean;
  bumped?: boolean;
  splashed?: boolean;
  boosted?: boolean;
  reflected?: boolean;
  /** The boss hit by its own reflected fireball. */
  bossHit?: boolean;
}

export interface Mechanic {
  step(k: MechKart, c: MechCtx, ev: MechEvents): void;
  render(t: number): void;
  gauge?(): { label: string; value: number } | undefined;
  /** How thick the air is (a sandstorm: 0..1). */
  fog?(): number;
  /** The sea's height now (the tide). */
  sea?(): number | undefined;
  dispose(): void;
}

const wrapL = (s: number, L: number) => ((s % L) + L) % L;
/** Where in its beat a timed thing is: 0..1, and its phase. */
function beat(t: number, period: number, offset: number, warn: number, on: number) {
  if (t < 0) return { phase: "off" as const, k: 0 };
  const u = (((t - offset) % period) + period) % period;
  const onAt = period - on;
  if (u >= onAt) return { phase: "on" as const, k: (u - onAt) / on };
  if (u >= onAt - warn) return { phase: "warn" as const, k: (u - (onAt - warn)) / warn };
  return { phase: "off" as const, k: 0 };
}

/** The local coordinates of (x, z) in a frame at (ox, oz) turned to `heading`: along it
 * and across it (positive to the right). */
function local(ox: number, oz: number, heading: number, x: number, z: number) {
  const dx = x - ox;
  const dz = z - oz;
  return {
    along: dx * Math.sin(heading) + dz * Math.cos(heading),
    across: dx * Math.cos(heading) - dz * Math.sin(heading),
  };
}

function kit(root: THREE.Object3D | undefined) {
  const group = new THREE.Group();
  group.name = "Boss mechanic";
  root?.add(group);
  const made: (THREE.Material | THREE.BufferGeometry)[] = [];
  const mat = (color: number, opacity = 1, additive = false) => {
    const m = new THREE.MeshBasicMaterial({
      color,
      transparent: opacity < 1 || additive,
      opacity,
      depthWrite: !additive && opacity >= 1,
      blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
      side: THREE.DoubleSide,
    });
    made.push(m);
    return m;
  };
  const lambert = (color: number) => {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true });
    made.push(m);
    return m;
  };
  const geo = <G extends THREE.BufferGeometry>(g: G) => (made.push(g), g);
  return {
    group,
    mat,
    lambert,
    geo,
    dispose() {
      root?.remove(group);
      for (const m of made) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- Rimefang

function iceWalls(list: Record<string, unknown>[], root?: THREE.Object3D): Mechanic {
  const K = kit(root);
  const walls = list.map((o) => ({
    x: num(o.x, 0),
    y: num(o.y, 0),
    z: num(o.z, 0),
    heading: num(o.heading, 0),
    width: num(o.width, 7),
    across: num(o.across, 3.5),
    period: num(o.period, 4),
    offset: num(o.offset, 0),
    warn: num(o.warn, 1.2),
    up: num(o.up, 1.8),
  }));
  const iceM = K.lambert(0xa8dcff);
  const crackM = K.mat(0xffffff, 0.8, true);
  const views = walls.map((w) => {
    const g = K.geo(new THREE.BoxGeometry(w.width, 3.2, 1.2));
    const m = new THREE.Mesh(g, iceM);
    const cx = w.x + Math.cos(w.heading) * w.across;
    const cz = w.z - Math.sin(w.heading) * w.across;
    m.position.set(cx, w.y - 3, cz);
    m.rotation.y = w.heading;
    const cg = K.geo(new THREE.PlaneGeometry(w.width, 0.6));
    cg.rotateX(-Math.PI / 2);
    const crack = new THREE.Mesh(cg, crackM);
    crack.position.set(cx, w.y + 0.1, cz);
    crack.rotation.y = w.heading;
    K.group.add(m, crack);
    return { m, crack, cx, cz };
  });
  let clock = 0;
  return {
    step(k, c, ev) {
      clock = c.t;
      walls.forEach((w, i) => {
        const b = beat(c.t, w.period, w.offset, w.warn, w.up);
        if (b.phase !== "on") return;
        const v = views[i]!;
        const l = local(v.cx, v.cz, w.heading, k.x, k.z);
        if (
          Math.abs(l.along) < 1.6 &&
          Math.abs(l.across) < w.width / 2 &&
          Math.abs(k.y - w.y) < 3
        ) {
          // Into the ice: stopped dead, bounced back the way you came.
          const back = 1.8 - Math.abs(l.along);
          k.x -= Math.sin(k.heading) * back;
          k.z -= Math.cos(k.heading) * back;
          k.speed = -Math.abs(k.speed) * 0.2;
          ev.bumped = true;
        }
      });
    },
    render(t) {
      walls.forEach((w, i) => {
        const b = beat(t, w.period, w.offset, w.warn, w.up);
        const v = views[i]!;
        const rise = b.phase === "on" ? Math.min(1, b.k * 8) * Math.min(1, (1 - b.k) * 8) : 0;
        v.m.position.y = w.y - 3.4 + rise * 4.9;
        v.crack.visible = b.phase === "warn";
        v.crack.scale.set(0.3 + 0.7 * b.k, 1, 1);
      });
      void clock;
    },
    dispose: K.dispose,
  };
}

/** A wall chasing you round the lap (Rimefang's avalanche, the King's fire). */
function chase(
  o: Record<string, unknown>,
  root: THREE.Object3D | undefined,
  fire: boolean,
): Mechanic {
  const K = kit(root);
  const from = num(o.from, 0);
  const to = num(o.to, 0);
  const gap = num(o.gap, 60);
  const speed = num(o.speed, 24);
  let front = -1;
  let you = 0;
  let hold = 0;
  let road: MechCtx["roadAt"] | undefined;
  const wallM = fire ? K.mat(0xff5a14, 0.85, true) : K.lambert(0xf4f8ff);
  const g = K.geo(new THREE.BoxGeometry(1, 1, 1));
  const wall = new THREE.Group();
  for (let k = 0; k < 7; k++) {
    const m = new THREE.Mesh(g, wallM);
    m.position.set((k - 3) * 3.2, 0, 0);
    wall.add(m);
  }
  wall.visible = false;
  K.group.add(wall);
  return {
    step(k, c, ev) {
      road = c.roadAt;
      you = c.lap;
      hold = Math.max(0, hold - c.dt);
      const at = wrapL(c.lap, c.lapLength);
      if (front < 0) {
        // It starts when you pass `from`.
        if (at >= from && at <= to) front = c.lap - gap;
        return;
      }
      front += speed * c.dt;
      const ahead = wrapL(front, c.lapLength);
      if (ahead > to || at > to + 5 || at < from - 5) {
        front = -1;
        return;
      }
      if (front >= c.lap && hold <= 0) {
        // Caught: buried in the snow (or burnt), dug out; it falls back.
        k.speed = 0;
        k.spinTime = 0.9;
        k.spinDir = 1;
        hold = 1.6;
        front = c.lap - gap * 0.6;
        ev.buried = true;
        if (fire) ev.burnt = true;
      }
      if (hold > 0) k.speed = Math.min(k.speed, 2);
    },
    render(t) {
      wall.visible = front >= 0 && Boolean(road);
      if (!wall.visible || !road) return;
      const p = road(front);
      wall.position.set(p.x, p.y, p.z);
      wall.rotation.y = p.heading;
      wall.children.forEach((m, i) => {
        const h = (fire ? 7 : 9) + Math.sin(t * (fire ? 13 : 4) + i * 1.3) * (fire ? 2 : 1.2);
        m.scale.set(3.6, h, fire ? 2 : 6);
        m.position.y = h / 2 - 0.5;
      });
    },
    gauge() {
      if (front < 0) return undefined;
      return {
        label: fire ? "FIRE!" : "AVALANCHE!",
        value: Math.max(0, Math.min(1, 1 - (you - front) / gap)),
      };
    },
    dispose: K.dispose,
  };
}

function thinLake(list: Record<string, unknown>[], root?: THREE.Object3D): Mechanic {
  const K = kit(root);
  const lakes = list.map((o) => ({
    x: num(o.x, 0),
    y: num(o.y, 0),
    z: num(o.z, 0),
    r: num(o.r, 40),
  }));
  let crack = 0;
  let on = false;
  const cm = K.mat(0xffffff, 0.7, true);
  const cg = K.geo(new THREE.RingGeometry(0.5, 1.0, 8, 1));
  cg.rotateX(-Math.PI / 2);
  const ring = new THREE.Mesh(cg, cm);
  ring.visible = false;
  K.group.add(ring);
  return {
    step(k, c, ev) {
      on = lakes.some((l) => Math.hypot(k.x - l.x, k.z - l.z) < l.r && Math.abs(k.y - l.y) < 2);
      if (!on) {
        crack = Math.max(0, crack - c.dt * 2);
        return;
      }
      // Slow on the ice and it cracks under you; fast and it holds (just).
      const speed = Math.abs(k.speed);
      crack += c.dt * (speed < 8 ? 0.9 : speed < 14 ? 0.25 : -0.4);
      crack = Math.max(0, crack);
      ring.position.set(k.x, k.y + 0.08, k.z);
      if (crack >= 1) {
        crack = 0;
        ev.splashed = true;
        ev.dropAt = wrapL(c.lap, c.lapLength) + 25;
      }
    },
    render() {
      ring.visible = on && crack > 0.05;
      ring.scale.setScalar(1 + crack * 6);
    },
    gauge() {
      return on ? { label: "ICE", value: Math.min(1, crack) } : undefined;
    },
    dispose: K.dispose,
  };
}

// ---------------------------------------------------------------- Scorchwind

function winds(
  gusts: Record<string, unknown>[],
  shelters: Record<string, unknown>[],
  tails: Record<string, unknown>[],
  root?: THREE.Object3D,
): Mechanic {
  const K = kit(root);
  const gs = gusts.map((o) => {
    const dx = num(o.dx, 1);
    const dz = num(o.dz, 0);
    const n = Math.hypot(dx, dz) || 1;
    return {
      x: num(o.x, 0),
      y: num(o.y, 0),
      z: num(o.z, 0),
      r: num(o.r, 30),
      dx: dx / n,
      dz: dz / n,
      period: num(o.period, 6),
      offset: num(o.offset, 0),
      warn: num(o.warn, 1.2),
      on: num(o.on, 2.4),
      strength: num(o.strength, 7),
    };
  });
  const sh = shelters.map((o) => ({ x: num(o.x, 0), z: num(o.z, 0), r: num(o.r, 6) }));
  const tw = tails.map((o) => ({ x: num(o.x, 0), z: num(o.z, 0), r: num(o.r, 8) }));
  let tailCool = 0;
  // The sand streaming across: thin strips flying along the wind.
  const sm = K.mat(0xf0d8a0, 0.7, false);
  const sg = K.geo(new THREE.PlaneGeometry(9, 0.5));
  const streams = gs.map((g) => {
    const list: THREE.Mesh[] = [];
    for (let k = 0; k < 36; k++) {
      const m = new THREE.Mesh(sg, sm);
      m.rotation.y = Math.atan2(g.dx, g.dz) + Math.PI / 2;
      K.group.add(m);
      list.push(m);
    }
    return list;
  });
  return {
    step(k, c, ev) {
      tailCool = Math.max(0, tailCool - c.dt);
      for (const g of gs) {
        if (Math.hypot(k.x - g.x, k.z - g.z) > g.r) continue;
        const b = beat(c.t, g.period, g.offset, g.warn, g.on);
        if (b.phase !== "on") continue;
        // Behind a pillar (upwind of you): out of the wind.
        const cover = sh.some((p) => {
          const px = k.x - g.dx * 4;
          const pz = k.z - g.dz * 4;
          return (
            Math.hypot(px - p.x, pz - p.z) < p.r || Math.hypot(k.x - p.x, k.z - p.z) < p.r * 0.8
          );
        });
        if (cover) continue;
        const f = g.strength * Math.sin(Math.PI * Math.min(1, b.k * 1.2));
        k.x += g.dx * f * c.dt;
        k.z += g.dz * f * c.dt;
        // Leaving a sail ramp into the wind's tail: carried further.
        if (c.airborne && tailCool <= 0 && tw.some((p) => Math.hypot(k.x - p.x, k.z - p.z) < p.r)) {
          ev.boosted = true;
          tailCool = 3;
        }
      }
    },
    render(t) {
      gs.forEach((g, i) => {
        const b = beat(t, g.period, g.offset, g.warn, g.on);
        const live = b.phase !== "off";
        streams[i]!.forEach((m, j) => {
          m.visible = live;
          if (!live) return;
          const u = ((t * (b.phase === "on" ? 30 : 12) + j * 13.7) % (g.r * 2)) - g.r;
          const side = ((j * 7.3) % (g.r * 1.6)) - g.r * 0.8;
          m.position.set(
            g.x + g.dx * u - g.dz * side,
            g.y + 0.6 + (j % 3) * 0.7,
            g.z + g.dz * u + g.dx * side,
          );
        });
      });
    },
    dispose: K.dispose,
  };
}

function sandstorm(o: Record<string, unknown>): Mechanic {
  const d = num(o.density, 0.8);
  return { step() {}, render() {}, fog: () => d, dispose() {} };
}

// ---------------------------------------------------------------- Tidewyrm

function tides(
  tide: Record<string, unknown> | undefined,
  bars: Record<string, unknown>[],
  coils: Record<string, unknown>[],
  root?: THREE.Object3D,
): Mechanic {
  // (Blake, Oct 27: the tide was jank, a meter nobody could read and splashes out of
  // nowhere. Reworked: you see everything coming.)
  //  - The sandbar shortcut is signposted: buoys at each end, green while it stays dry,
  //    amber when the sea's coming in (under SANDBAR_WARN s), red when it's under water.
  //    Caught on it under water you swim (slowly), you're not put back.
  //  - His coils on the causeway (coil from..to round the lap) are always a road now;
  //    his back breaches from it in turn, one hump at a time on one half of the road: a
  //    dark swirl on the road first (HUMP_WARN s), then the hump. Hit it just as it rises
  //    and it throws you on (a boost); once it's up, it knocks you back.
  const K = kit(root);
  const period = num(tide?.period, 16);
  const low = num(tide?.low, -1.6);
  const high = num(tide?.high, 1.2);
  const offset = num(tide?.offset, 0);
  const sb = bars.map((o) => ({ x: num(o.x, 0), y: num(o.y, 0), z: num(o.z, 0), r: num(o.r, 12) }));
  const cs = coils.map((o) => ({
    from: num(o.from, 0),
    to: num(o.to, 0),
    period: num(o.period, 8),
    offset: num(o.offset, 0),
  }));
  const levelAt = (t: number) =>
    (low + high) / 2 + ((high - low) / 2) * Math.sin(((t - offset) / period) * Math.PI * 2);
  /** Under water from this level (a sandbar's top plus a little). */
  const wet = sb.length ? Math.min(...sb.map((b) => b.y)) + 0.4 : Infinity;
  const stateAt = (t: number): "open" | "closing" | "flooded" =>
    levelAt(t) >= wet ? "flooded" : levelAt(t + SANDBAR_WARN) >= wet ? "closing" : "open";
  let level = low;
  let now = 0;
  let swimming = false;
  let road: MechCtx["roadAt"] | undefined;
  const seaM = K.mat(0x2aa8c8, 0.6, false);
  const seaG = K.geo(new THREE.CircleGeometry(900, 40));
  seaG.rotateX(-Math.PI / 2);
  const sea = new THREE.Mesh(seaG, seaM);
  K.group.add(sea);
  // The buoys: two at each end of the sandbar.
  const buoyLit = {
    open: K.mat(0x30e050),
    closing: K.mat(0xffb020),
    flooded: K.mat(0xe03020),
  };
  const postM = K.lambert(0xf4f0e0);
  const postG = K.geo(new THREE.CylinderGeometry(0.5, 0.7, 4.6, 8));
  const lampG = K.geo(new THREE.SphereGeometry(1.2, 10, 8));
  const buoys: THREE.Mesh[] = [];
  if (sb.length) {
    const ends = [sb[0]!, sb[sb.length - 1]!];
    const dir = sb.length > 1 ? Math.atan2(ends[1]!.x - ends[0]!.x, ends[1]!.z - ends[0]!.z) : 0;
    for (const e of ends)
      for (const side of [-1, 1]) {
        const x = e.x + Math.cos(dir) * side * (e.r + 1.5);
        const z = e.z - Math.sin(dir) * side * (e.r + 1.5);
        const post = new THREE.Mesh(postG, postM);
        post.position.set(x, e.y + 1.6, z);
        K.group.add(post);
        const lamp = new THREE.Mesh(lampG, buoyLit.open);
        lamp.position.set(x, e.y + 4.4, z);
        K.group.add(lamp);
        buoys.push(lamp);
      }
  }
  // His humps: four spots along each coil stretch, breaching in turn.
  const coilM = K.lambert(0x1f6a6a);
  const swirlM = K.mat(0x0a2a3a, 0.7, false);
  const humpG = K.geo(new THREE.TorusGeometry(2.6, 1.2, 6, 10, Math.PI));
  const swirlG = K.geo(new THREE.CircleGeometry(3.2, 16));
  swirlG.rotateX(-Math.PI / 2);
  const humps = cs.flatMap((c, ci) =>
    [0, 1, 2, 3].map((j) => {
      const hump = new THREE.Mesh(humpG, coilM);
      const swirl = new THREE.Mesh(swirlG, swirlM);
      hump.visible = swirl.visible = false;
      K.group.add(hump, swirl);
      return {
        ci,
        at: c.from + ((c.to - c.from) * (j + 0.5)) / 4,
        side: j % 2 ? 1 : -1,
        offset: c.offset + (c.period * j) / 4,
        period: c.period,
        hump,
        swirl,
        lastHit: -Infinity,
      };
    }),
  );
  const humpBeat = (h: (typeof humps)[number], t: number) =>
    beat(t, h.period, h.offset, HUMP_WARN, HUMP_UP);
  const humpSpot = (h: (typeof humps)[number]) => {
    if (!road) return undefined;
    const p = road(h.at);
    const across = h.side * (p.width / 4);
    return {
      x: p.x + Math.cos(p.heading) * across,
      y: p.y,
      z: p.z - Math.sin(p.heading) * across,
      heading: p.heading,
      half: p.width / 4,
    };
  };
  return {
    step(k, c, ev) {
      road = c.roadAt;
      now = c.t;
      level = levelAt(c.t);
      // On the sandbar under water: swimming, slowly.
      let wetNow = false;
      for (const b of sb)
        if (Math.hypot(k.x - b.x, k.z - b.z) < b.r && level > b.y + 0.4 && k.y < level + 0.5)
          wetNow = true;
      if (wetNow) {
        k.speed = Math.min(k.speed, SWIM_SPEED);
        if (!swimming) ev.splashed = true;
      }
      swimming = wetNow;
      // His humps.
      for (const h of humps) {
        const b = humpBeat(h, c.t);
        if (b.phase !== "on" || c.t - h.lastHit < 1) continue;
        const p = humpSpot(h);
        if (!p) continue;
        const l = local(p.x, p.z, p.heading, k.x, k.z);
        if (Math.abs(l.along) > 2.6 || Math.abs(l.across) > p.half + 0.6 || Math.abs(k.y - p.y) > 3)
          continue;
        h.lastHit = c.t;
        if (b.k < HUMP_RAMP) ev.boosted = true;
        else {
          k.speed *= 0.4;
          k.spinTime = 0.5;
          k.spinDir = h.side;
          ev.bumped = true;
        }
      }
    },
    render(t) {
      sea.position.y = level;
      const st = stateAt(now);
      for (const lamp of buoys) {
        lamp.material = buoyLit[st];
        // (Amber flashes.)
        lamp.visible = st !== "closing" || Math.sin(t * 12) > -0.3;
      }
      for (const h of humps) {
        const b = humpBeat(h, t);
        const p = humpSpot(h);
        if (!p) continue;
        h.swirl.visible = b.phase === "warn";
        h.swirl.position.set(p.x, p.y + 0.06, p.z);
        h.swirl.scale.setScalar(0.4 + 0.6 * b.k);
        h.hump.visible = b.phase === "on";
        if (b.phase === "on") {
          const rise = Math.min(1, b.k / HUMP_RAMP) * Math.min(1, (1 - b.k) * 5);
          h.hump.position.set(p.x, p.y - 2.6 + 2.6 * rise, p.z);
          h.hump.rotation.y = p.heading + Math.PI / 2;
        }
      }
    },
    sea: () => level,
    gauge() {
      if (!sb.length) return undefined;
      const st = stateAt(now);
      return {
        label:
          st === "open"
            ? "SANDBAR: OPEN"
            : st === "closing"
              ? "SANDBAR: CLOSING!"
              : "SANDBAR: FLOODED",
        value: (level - low) / Math.max(0.01, high - low),
      };
    },
    dispose: K.dispose,
  };
}

/** Seconds of warning before the sandbar floods (the buoys go amber). */
const SANDBAR_WARN = 3;
/** Caught on the sandbar under water: swimming at most this fast, m/s. */
const SWIM_SPEED = 9;
/** A hump's swirl before it breaches, how long it's up, and the first part of that
 * (as it rises) when hitting it throws you on. */
const HUMP_WARN = 1.6;
const HUMP_UP = 2.2;
const HUMP_RAMP = 0.25;

function whirlpools(list: Record<string, unknown>[], root?: THREE.Object3D): Mechanic {
  const K = kit(root);
  const ws = list.map((o) => ({
    x: num(o.x, 0),
    y: num(o.y, 0),
    z: num(o.z, 0),
    r: num(o.r, 12),
    spin: num(o.spin, 1.4),
  }));
  const inside = ws.map(() => false);
  const rm = K.mat(0xbff0ff, 0.5, true);
  const rings = ws.map((w) => {
    const list: THREE.Mesh[] = [];
    for (let k = 1; k <= 4; k++) {
      const g = K.geo(
        new THREE.RingGeometry(w.r * (k / 4) - 0.4, w.r * (k / 4), 24, 1, 0, Math.PI * 1.4),
      );
      g.rotateX(-Math.PI / 2);
      const m = new THREE.Mesh(g, rm);
      m.position.set(w.x, w.y + 0.1, w.z);
      K.group.add(m);
      list.push(m);
    }
    return list;
  });
  return {
    step(k, c, ev) {
      ws.forEach((w, i) => {
        const d = Math.hypot(k.x - w.x, k.z - w.z);
        const now = d < w.r && Math.abs(k.y - w.y) < 3;
        if (now) {
          // Swung round it: your path turned with the current.
          const a = Math.atan2(k.x - w.x, k.z - w.z) + w.spin * c.dt * (1 + (w.r - d) / w.r);
          const r = Math.max(1.5, d - 0.5 * c.dt);
          k.x = w.x + Math.sin(a) * r;
          k.z = w.z + Math.cos(a) * r;
          k.heading += w.spin * c.dt;
        } else if (inside[i]) {
          // Out of it facing away from the middle: flung, a boost.
          const out = Math.atan2(k.x - w.x, k.z - w.z);
          const err = Math.abs(Math.atan2(Math.sin(k.heading - out), Math.cos(k.heading - out)));
          if (err < 1.2) ev.boosted = true;
        }
        inside[i] = now;
      });
    },
    render(t) {
      ws.forEach((w, i) =>
        rings[i]!.forEach((m, j) => (m.rotation.y = -t * w.spin * (1 + j * 0.3))),
      );
    },
    dispose: K.dispose,
  };
}

// ---------------------------------------------------------------- the King

function fireballs(o: Record<string, unknown>, root?: THREE.Object3D): Mechanic {
  const K = kit(root);
  const period = num(o.period, 5);
  const speed = num(o.speed, 28);
  let next = 4;
  const balls: { x: number; y: number; z: number; back: boolean; age: number; m: THREE.Mesh }[] =
    [];
  const bm = K.mat(0xff7a20, 0.9, true);
  const lm = K.mat(0xfff0a0, 0.9, true);
  const bg = K.geo(new THREE.SphereGeometry(1.2, 10, 8));
  let flash = 0;
  return {
    step(k, c, ev) {
      flash = Math.max(0, flash - c.dt);
      if (!c.boss || c.t < 0) return;
      next -= c.dt;
      if (next <= 0) {
        next = period;
        const m = new THREE.Mesh(bg, bm);
        K.group.add(m);
        balls.push({ x: c.boss.x, y: c.boss.y + 4, z: c.boss.z, back: false, age: 0, m });
      }
      for (let i = balls.length - 1; i >= 0; i--) {
        const b = balls[i]!;
        b.age += c.dt;
        const tx = b.back ? c.boss.x : k.x;
        const ty = b.back ? c.boss.y + 3 : k.y + 1;
        const tz = b.back ? c.boss.z : k.z;
        const d = Math.hypot(tx - b.x, ty - b.y, tz - b.z);
        const step = Math.min(d, (speed + (b.back ? 20 : 0)) * c.dt);
        b.x += ((tx - b.x) / (d || 1)) * step;
        b.y += ((ty - b.y) / (d || 1)) * step;
        b.z += ((tz - b.z) / (d || 1)) * step;
        if (!b.back && d < 7 && c.item) {
          // AURIN'S LIGHT: back at him.
          b.back = true;
          b.m.material = lm;
          ev.reflected = true;
          flash = 0.3;
        } else if (d < 1.6 || b.age > 9) {
          if (b.back) ev.bossHit = true;
          else if (b.age <= 9) {
            ev.burnt = true;
            k.spinTime = 0.8;
            k.spinDir = 1;
            k.speed *= 0.4;
          }
          K.group.remove(b.m);
          balls.splice(i, 1);
        }
      }
    },
    render(t) {
      for (const b of balls) {
        b.m.position.set(b.x, b.y, b.z);
        b.m.scale.setScalar(1 + Math.sin(t * 20) * 0.15 + flash);
      }
    },
    dispose: K.dispose,
  };
}

/** Every mechanic among a course's entities, for its main version or its alternative. */
export function createMechanics(
  entities: unknown[],
  variant: "main" | "alt",
  root?: THREE.Object3D,
): Mechanic[] {
  const by = (type: string) =>
    entities.filter((e): e is Record<string, unknown> => {
      if (!e || typeof e !== "object") return false;
      const o = e as Record<string, unknown>;
      return o.type === type && (o.variant === "alt" ? "alt" : "main") === variant;
    });
  const out: Mechanic[] = [];
  const walls = by("ice_wall");
  if (walls.length) out.push(iceWalls(walls, root));
  for (const a of by("avalanche")) out.push(chase(a, root, false));
  for (const a of by("firewall")) out.push(chase(a, root, true));
  const lakes = by("thin_lake");
  if (lakes.length) out.push(thinLake(lakes, root));
  const gusts = by("gust");
  if (gusts.length) out.push(winds(gusts, by("shelter"), by("tailwind"), root));
  for (const s of by("sandstorm")) out.push(sandstorm(s));
  const tide = by("tide")[0];
  const coils = by("coil");
  if (tide || coils.length) out.push(tides(tide, by("sandbar"), coils, root));
  const pools = by("whirlpool");
  if (pools.length) out.push(whirlpools(pools, root));
  for (const f of by("fireball")) out.push(fireballs(f, root));
  return out;
}
