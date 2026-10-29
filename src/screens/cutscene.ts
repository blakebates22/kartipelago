/**
 * Staged scenes (src/adventure/staged.ts): a story scene played out in the 3D world. The
 * region loads, the cast take their marks, and each line has its shot: the camera moving
 * between two spots, actors walking (or flying) to their marks, the dragon rearing and
 * breathing fire, a flash, the screen shaking. Letterboxed; ENTER for the next line, ESC
 * skips the scene. Its lines are the scene's own (scenes.ts), so the text box is the
 * same as the picture scenes'.
 */
import * as THREE from "three";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import type { Session } from "../game/session";
import { CAST, type Beat } from "../adventure/scenes";
import type { StagedScene, Shot, StoryPose, V3 } from "../adventure/staged";
import { regionById } from "../overworld/regions";
import { Racer as RacerView } from "../render/racers/racer";
import { DRAGON_PALETTES } from "../render/racers/roster/dragon";
import type { RacerId } from "../render/racers/designs";
import { createVillagerView } from "../render/villager";
import { createPactStoneView, type PropView } from "../render/storyProps";
import {
  createElderView,
  createGuardView,
  createLumenView,
  type PersonView,
} from "../render/people";
import { actRacer, type RacerActing } from "../render/people/racerActing";
import { facePoint } from "../render/people/view";
import { createStoryDragon, designOf, type StoryDragonView } from "../render/storyDragon";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { wrap } from "../ui/font";
import { PAL } from "../ui/textures";
import { hints } from "./common";
import { portrait, portraitSlot } from "./adventure";

const INK = "#3a2412";
const ease = (t: number) => t * t * (3 - 2 * t);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerp3 = (a: V3, b: V3, t: number): V3 => [
  lerp(a[0], b[0], t),
  lerp(a[1], b[1], t),
  lerp(a[2], b[2], t),
];

interface Actor {
  /** A dragon's pose already settled (its first frame shows it posed, not mid-blend from
   * its rest pose: Blake, Oct 28, "something black pops into the frame"). */
  settled?: boolean;
  x: number;
  y: number;
  z: number;
  heading: number;
  /** Metres up (a flyer). */
  up: number;
  from?: {
    x: number;
    z: number;
    up: number;
    heading: number;
    t0: number;
    dur: number;
    to: [number, number];
    /** The whole way, start to end (a move with bends). */
    path?: [number, number][];
    /** A flyer landing (its own glide and flare). */
    land?: boolean;
    toUp: number;
    toHeading: number;
    /** A flyer's ground at the start and the end (its height is measured between them). */
    y0?: number;
    y1?: number;
  };
  racer?: RacerView;
  /** A racer's acting (looking about, talking) in their kart. */
  acting?: RacerActing;
  /** Someone on foot: the Elder, Lumen in his robe, a guard, the townsfolk. */
  person?: PersonView;
  prop?: PropView;
  shown: boolean;
  /** A dragon (render/storyDragon.ts: each its own design), and its name on stage. */
  dragon?: StoryDragonView;
  name: string;
}

/** A point `k` (0..1) of the way along a path of straight stretches, and the heading
 * there (0 = +z). */
function alongPath(path: [number, number][], k: number): [number, number, number] {
  const lens = path.slice(1).map((p, i) => Math.hypot(p[0] - path[i]![0], p[1] - path[i]![1]));
  const total = lens.reduce((a, b) => a + b, 0) || 1;
  let d = k * total;
  for (let i = 0; i < lens.length; i++) {
    const a = path[i]!;
    const b = path[i + 1]!;
    if (d <= lens[i]! || i === lens.length - 1) {
      const t = lens[i]! ? Math.min(1, d / lens[i]!) : 1;
      return [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        Math.atan2(b[0] - a[0], b[1] - a[1]),
      ];
    }
    d -= lens[i]!;
  }
  const p = path[path.length - 1]!;
  return [p[0], p[1], 0];
}

export function stagedSceneScreen(
  game: Game,
  staged: StagedScene,
  title: string,
  beats: Beat[],
  finish: () => void,
  /** The file's racer: "you" in the scene (and a champion who's you: their cousin). */
  me: RacerId = game.selection.racer,
): Screen {
  const region = regionById(staged.region)!;
  const pkg = (staged.ruined && region.ruinPackageId) || region.packageId;
  let session: Session | undefined;
  let failed = false;
  let alive = true;
  let i = 0;
  let t = 0;
  let clock = 0;
  let pp: PixelPortraits | undefined;
  const actors = new Map<string, Actor>();
  let land: ReturnType<Session["makeGround"]> | undefined;
  const groundAt = (x: number, z: number) => land?.at(x, z, 200).height ?? 0;
  const beatOf = (k: number) => staged.beats[Math.min(k, staged.beats.length - 1)];

  const show = (a: Actor, on: boolean) => {
    a.shown = on;
    if (a.racer) {
      a.racer.root.visible = on;
      a.racer.shadow.visible = on;
    }
    if (a.person) a.person.root.visible = on;
    if (a.prop) a.prop.root.visible = on;
    if (a.dragon) a.dragon.root.visible = on;
  };
  /**
   * The main road's way in to `stop` from ahead of "you": its centre line from about 45 m
   * ahead (the way you face) back to `stop`. Undefined with no road near you.
   */
  const roadPath = (stop: [number, number]): [number, number][] | undefined => {
    const samples = session?.track?.samples;
    const me = actors.get("you");
    if (!samples?.length || !me) return undefined;
    let i0 = 0;
    let bd = Infinity;
    samples.forEach((s, i) => {
      const d = (s.pos.x - me.x) ** 2 + (s.pos.z - me.z) ** 2;
      if (d < bd) {
        bd = d;
        i0 = i;
      }
    });
    if (bd > 25 * 25) return undefined;
    const f0 = samples[i0]!.forward;
    const dir = f0.x * Math.sin(me.heading) + f0.z * Math.cos(me.heading) >= 0 ? 1 : -1;
    const n = samples.length;
    const pts: [number, number][] = [];
    let run = 0;
    let prev = samples[i0]!.pos;
    for (let k = 1; k < n && run < 52; k++) {
      const p = samples[(((i0 + dir * k) % n) + n) % n]!.pos;
      run += Math.hypot(p.x - prev.x, p.z - prev.z);
      prev = p;
      // (Only beyond where they'll stop: no doubling back.)
      if (run > Math.hypot(stop[0] - me.x, stop[1] - me.z) + 6) pts.push([p.x, p.z]);
    }
    return pts.length ? [...pts.reverse(), stop] : undefined;
  };
  /**
   * Someone walking from `from` to `to` (Blake, Oct 28: "the character in the background
   * walks through the hut... we always need to be aware of this"): the straight way if
   * nothing's in it, otherwise round whatever is (a hut, a wall: anything the ground
   * jumps up to under a walker's feet), by the smallest step aside that clears it.
   * Undefined for the straight way; null when there's no way at all.
   */
  const walkAround = (from: [number, number], to: [number, number]) => {
    const clear = (a: [number, number], b: [number, number]) => {
      const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const n = Math.max(2, Math.ceil(d / 0.75));
      // (Not the ends: someone may stand by a wall to start with.)
      for (let i = 1; i < n; i++) {
        const x = a[0] + ((b[0] - a[0]) * i) / n;
        const z = a[1] + ((b[1] - a[1]) * i) / n;
        // (A wall a kart's width away: a hut, a fence, a rock face.)
        if (session && !session.kartFits(x, z, groundAt(x, z) + 3)) return false;
      }
      return true;
    };
    if (clear(from, to)) return undefined;
    const mx = (from[0] + to[0]) / 2;
    const mz = (from[1] + to[1]) / 2;
    const d = Math.hypot(to[0] - from[0], to[1] - from[1]) || 1;
    const px = -(to[1] - from[1]) / d;
    const pz = (to[0] - from[0]) / d;
    for (const off of [3, 5, 7, 9, 12, 15])
      for (const sd of [1, -1]) {
        const mid: [number, number] = [mx + px * off * sd, mz + pz * off * sd];
        if (roomy(mid[0], mid[1]) && clear(from, mid) && clear(mid, to))
          return [from, mid, to] as [number, number][];
      }
    return findWay(from, to, clear);
  };
  /** The way round when one step aside won't do (huts in a row, a hut by a wall): a
   * search over a 1.5 m grid, then pulled straight wherever the way is clear. */
  /** Room to walk: clear here and a step each way (so not in a doorway, not inside). */
  const roomy = (x: number, z: number) =>
    !!session &&
    [
      [0, 0],
      [1.2, 0],
      [-1.2, 0],
      [0, 1.2],
      [0, -1.2],
    ].every(([dx, dz]) => session!.kartFits(x + dx!, z + dz!, groundAt(x + dx!, z + dz!) + 3));
  const findWay = (
    from: [number, number],
    to: [number, number],
    clear: (a: [number, number], b: [number, number]) => boolean,
  ): [number, number][] | null => {
    if (!session) return null;
    const S = 1.5;
    const pad = 20;
    const x0 = Math.min(from[0], to[0]) - pad;
    const z0 = Math.min(from[1], to[1]) - pad;
    const nx = Math.ceil((Math.abs(to[0] - from[0]) + 2 * pad) / S) + 1;
    const nz = Math.ceil((Math.abs(to[1] - from[1]) + 2 * pad) / S) + 1;
    const cell = (x: number, z: number) =>
      Math.max(0, Math.min(nx - 1, Math.round((x - x0) / S))) +
      nx * Math.max(0, Math.min(nz - 1, Math.round((z - z0) / S)));
    const at = (c: number): [number, number] => [x0 + (c % nx) * S, z0 + Math.floor(c / nx) * S];
    const open = new Map<number, boolean>();
    const s0 = cell(...from);
    const s1 = cell(...to);
    const fits = (c: number) => {
      if (c === s0 || c === s1) return true;
      let o = open.get(c);
      if (o === undefined) {
        // (Wide: a doorway isn't a way through a hut.)
        const [x, z] = at(c);
        o = roomy(x, z);
        open.set(c, o);
      }
      return o;
    };
    const cost = new Map<number, number>([[s0, 0]]);
    const back = new Map<number, number>();
    const h = (c: number) => {
      const [x, z] = at(c);
      return Math.hypot(x - to[0], z - to[1]);
    };
    const queue: [number, number][] = [[h(s0), s0]];
    let found = false;
    for (let n = 0; queue.length && n < 20000; n++) {
      let bi = 0;
      for (let k = 1; k < queue.length; k++) if (queue[k]![0] < queue[bi]![0]) bi = k;
      const [, c] = queue.splice(bi, 1)[0]!;
      if (c === s1) {
        found = true;
        break;
      }
      const cx = c % nx;
      const cz = Math.floor(c / nx);
      for (let dz = -1; dz <= 1; dz++)
        for (let dx = -1; dx <= 1; dx++) {
          if (!dx && !dz) continue;
          const x = cx + dx;
          const z = cz + dz;
          if (x < 0 || z < 0 || x >= nx || z >= nz) continue;
          const d = z * nx + x;
          if (!fits(d)) continue;
          const g = cost.get(c)! + Math.hypot(dx, dz) * S;
          if (g >= (cost.get(d) ?? Infinity)) continue;
          cost.set(d, g);
          back.set(d, c);
          queue.push([g + h(d), d]);
        }
    }
    if (!found) return null;
    const cells: [number, number][] = [];
    for (let c: number | undefined = s1; c !== undefined && c !== s0; c = back.get(c))
      cells.unshift(at(c));
    cells[cells.length - 1] = to;
    // Pulled straight: from each point, on to the furthest one it can see.
    const way: [number, number][] = [from];
    let k = -1;
    while (k < cells.length - 1) {
      let j = cells.length - 1;
      const here = k < 0 ? from : cells[k]!;
      while (j > k + 1 && !clear(here, cells[j]!)) j--;
      way.push(cells[j]!);
      k = j;
    }
    return way;
  };
  /** A walk along bends, each stretch taken round anything in its way (a curving path
   * swinging into a hut: Blake, Oct 28). */
  const routeThrough = (all: [number, number][]) => {
    // (A bend that lands in a wall is dropped: the way goes round instead.)
    const pts = all.filter((p, k) => k === 0 || k === all.length - 1 || roomy(p[0], p[1]));
    const out: [number, number][] = [pts[0]!];
    for (let k = 1; k < pts.length; k++) {
      const last = k === pts.length - 1;
      const leg = walkAround(out[out.length - 1]!, pts[k]!);
      // (No way to a bend, from where we are: it's inside something. Skip it.)
      if (leg === null && !last) continue;
      if (leg) out.push(...leg.slice(1));
      else out.push(pts[k]!);
    }
    return out;
  };
  const startBeat = (k: number) => {
    const b = staged.beats[k];
    for (const n of b?.fx?.show ?? []) {
      const a = actors.get(n);
      if (a) show(a, true);
    }
    for (const n of b?.fx?.hide ?? []) {
      const a = actors.get(n);
      if (a) show(a, false);
    }
    if (b?.fx?.horn) game.sounds.gong(3);
    if (b?.fx?.music) void game.audio.music.play(b.fx.music, { fade: 0.8 });
    for (const m of b?.moves ?? []) {
      const a = actors.get(m.actor);
      if (!a) continue;
      a.from = {
        x: a.x,
        z: a.z,
        up: a.up,
        heading: a.heading,
        t0: clock,
        dur: m.dur,
        to: m.to,
        ...(a.person && !m.road && !m.via?.length
          ? (() => {
              const path = walkAround([a.x, a.z], m.to);
              return path ? { path } : {};
            })()
          : m.road
            ? (() => {
                const path = roadPath(m.to);
                if (path) {
                  a.x = path[0]![0];
                  a.z = path[0]![1];
                }
                return path ? { path } : {};
              })()
            : m.via?.length
              ? {
                  path: a.person
                    ? routeThrough([[a.x, a.z], ...m.via, m.to])
                    : [[a.x, a.z], ...m.via, m.to],
                }
              : {}),
        toUp: m.y ?? a.up,
        toHeading: m.heading ?? Math.atan2(m.to[0] - a.x, m.to[1] - a.z),
        ...(m.land ? { land: true } : {}),
      };
    }
  };
  const next = () => {
    // (The last line stays up, whole, until whatever comes next takes over.)
    if (i + 1 >= beats.length) return done();
    i++;
    t = 0;
    startBeat(i);
  };
  const done = () => {
    alive = false;
    finish();
  };

  const build = (s: Session) => {
    land = s.makeGround();
    s.showHud(false);
    // (The geysers rest while a scene plays: nothing erupts behind the speaker.)
    if (s.hazards) s.hazards.calm = true;
    // Your kart isn't driven here: you're one of the cast.
    const you = s.entrants[0]!;
    you.mesh.visible = false;
    you.racer.shadow.visible = false;
    for (const [name, spec] of Object.entries(staged.actors)) {
      const [x, z] = spec.at;
      const a: Actor = {
        x,
        z,
        y: groundAt(x, z),
        heading: spec.heading,
        up: spec.kind === "dragon" ? (spec.y ?? 0) : 0,
        shown: true,
        name,
      };
      if (spec.kind === "racer") {
        const look = (spec.look === "you" ? me : spec.look) as RacerId;
        // (A champion who's also your file's racer: their cousin, in the other paint.)
        const cousin = spec.look !== "you" && look === me;
        a.racer = new RacerView(look, { seed: name.length * 7, alt: cousin });
        a.acting = actRacer(a.racer);
        s.root.add(a.racer.root, a.racer.shadow);
      } else if (spec.kind === "villager") {
        a.person = createVillagerView(s.root, spec.folk, spec.seed, spec.species);
      } else if (spec.kind === "elder") {
        a.person = createElderView(s.root);
        if (spec.horn === "broken") a.person.anim.hornBroken = true;
      } else if (spec.kind === "guard") {
        a.person = createGuardView(s.root, spec.folk, spec.seed);
      } else if (spec.kind === "robed") {
        a.person = createLumenView(s.root);
      } else if (spec.kind === "stone") {
        a.prop = createPactStoneView(s.root, spec.state, spec.big);
      } else {
        a.dragon = createStoryDragon(s.root, designOf(spec.look), spec.scale ?? 2);
      }
      actors.set(name, a);
      if (spec.hidden) show(a, false);
    }
    void DRAGON_PALETTES;
    startBeat(0);
  };

  const look = new THREE.Vector3();
  /** A dragon's pose on this line (the scene's cue, or what it's doing), who it's
   * looking at (whoever's speaking; when it speaks, you), and its jaw while it talks. */
  const placeDragon = (a: Actor, d: StoryDragonView, b: ReturnType<typeof beatOf>) => {
    d.root.position.set(a.x, a.y + a.up, a.z);
    d.root.rotation.y = a.heading;
    const name = a.name;
    const cue = b?.fx?.pose?.[name];
    const moving = a.from !== undefined;
    let pose: StoryPose = "idle";
    if (cue) pose = cue;
    else if (b?.fx?.fire === name) pose = "breathe";
    else if (b?.fx?.rear === name) pose = "rear";
    else if (moving && (a.up > 2 || a.from!.toUp > 2))
      pose = a.from!.toUp < a.up && a.up < 30 ? "land" : "fly";
    else if (moving) pose = "walk";
    // High up and still, it's flying; a little up (a rooftop), it's perched there.
    else if (a.up > 30) pose = "fly";
    const perched = !moving && a.up > 2 && pose !== "fly" && pose !== "land";
    d.ground = perched ? a.y + a.up : a.y;
    const who = beats[Math.min(i, beats.length - 1)]?.who ?? "";
    const talk = who === name || (name === "lumen_dragon" && who === "lumen");
    // Look at the speaker; when it's the one speaking, at you (or ahead).
    const at = (k: string) => {
      const o = actors.get(k);
      return o && o !== a && o.shown ? o : undefined;
    };
    const other = talk ? (at("you") ?? at("elder")) : at(who);
    if (other) {
      if (other.dragon) other.dragon.head(look);
      else look.set(other.x, other.y + other.up + 1.4, other.z);
    } else look.set(a.x + Math.sin(a.heading) * 60, a.y + 4, a.z + Math.cos(a.heading) * 60);
    // Speaking, it plays to the camera a little (a face, not the top of a head).
    if (talk) look.lerp(game.stage.camera.position, 0.55);
    if (!a.settled) {
      for (let k = 0; k < 30; k++) d.update(pose, t, clock - 1.5 + k * 0.05, look, talk);
      a.settled = true;
    }
    d.update(pose, t, clock, look, talk);
  };

  // Who's speaking this line (on stage), and where their face is.
  const speakerOf = (k: number) => {
    const who = beats[k]?.who;
    if (!who) return undefined;
    for (const n of [who, who === "lumen_dragon" ? "lumen" : "", `${who}1`]) {
      const a = n ? actors.get(n) : undefined;
      if (a?.shown && (a.person || a.racer)) return { name: n, a };
    }
    return undefined;
  };
  const faceOf = (a: Actor, out: THREE.Vector3) =>
    a.person
      ? a.person.headPosition(out)
      : a.racer
        ? facePoint(a.racer.rig, out)
        : out.set(a.x, a.y + 1.4, a.z);
  const speakerFace = new THREE.Vector3();
  const camAt = new THREE.Vector3();
  let lastClock = 0;
  const place = (frameSeconds: number) => {
    const b = beatOf(i);
    const dt = Math.max(0, Math.min(0.1, clock - lastClock));
    lastClock = clock;
    for (const a of actors.values()) {
      if (a.from) {
        const k = ease(Math.min(1, (clock - a.from.t0) / Math.max(0.01, a.from.dur)));
        a.up = lerp(a.from.up, a.from.toUp, k);
        if (a.from.land) {
          // A landing (Blake, Oct 28: not floating, turning stiffly, then sinking): it
          // glides in facing the way it flies, slowing, dropping steeply at first and
          // flaring out over the ground; only once down does it turn to face its mark.
          const u = Math.min(1, (clock - a.from.t0) / Math.max(0.01, a.from.dur));
          const kh = 1 - (1 - Math.min(1, u / 0.85)) ** 2;
          a.x = lerp(a.from.x, a.from.to[0], kh);
          a.z = lerp(a.from.z, a.from.to[1], kh);
          const ku = Math.min(1, u / 0.85);
          a.up = a.from.toUp + (a.from.up - a.from.toUp) * (1 - ku) ** 2;
          const fly = Math.atan2(a.from.to[0] - a.from.x, a.from.to[1] - a.from.z);
          const turn = Math.max(0, (u - 0.85) / 0.15);
          const dh = Math.atan2(Math.sin(a.from.toHeading - fly), Math.cos(a.from.toHeading - fly));
          const dh0 = Math.atan2(Math.sin(fly - a.from.heading), Math.cos(fly - a.from.heading));
          a.heading =
            u < 0.15 ? a.from.heading + dh0 * (u / 0.15) : fly + dh * turn * turn * (3 - 2 * turn);
          if (u >= 1) a.from = undefined;
        } else if (a.from.path) {
          // Along the bends at an even speed, facing the way it goes; turning to its last
          // heading over the last stretch.
          const [x, z, h] = alongPath(a.from.path, k);
          a.x = x;
          a.z = z;
          const end = Math.max(0, (k - 0.85) / 0.15);
          const dh = Math.atan2(Math.sin(a.from.toHeading - h), Math.cos(a.from.toHeading - h));
          a.heading = h + dh * end;
        } else {
          a.x = lerp(a.from.x, a.from.to[0], k);
          a.z = lerp(a.from.z, a.from.to[1], k);
          const dh = Math.atan2(
            Math.sin(a.from.toHeading - a.from.heading),
            Math.cos(a.from.toHeading - a.from.heading),
          );
          // (Someone on foot turns to go before they set off, not walking backwards while
          // they come round; the rest turn over the first half of the move.)
          const turn = a.person ? Math.min(1, (clock - a.from.t0) / 0.5) : Math.min(1, k * 2);
          a.heading = a.from.heading + dh * turn;
        }
        if (k >= 1) a.from = undefined;
      }
      // (A dragon in the air flies level, not lifting and dropping with every cliff and
      // tree under it: Blake, Oct 28, "incredibly choppy". Its height is measured from
      // the ground it left blended into the ground it's making for.)
      const flight = a.from;
      if (a.dragon && flight && (flight.up > 2 || flight.toUp > 2)) {
        const u = Math.min(1, (clock - flight.t0) / Math.max(0.01, flight.dur));
        // (Landing, the same curve as its drop, so it never dips below where it lands.)
        const ku = flight.land ? 1 - (1 - Math.min(1, u / 0.85)) ** 2 : ease(u);
        flight.y0 ??= groundAt(flight.x, flight.z);
        flight.y1 ??= groundAt(flight.to[0], flight.to[1]);
        a.y = lerp(flight.y0, flight.y1, ku);
      } else a.y = groundAt(a.x, a.z);
      if (a.racer) {
        a.racer.root.position.set(a.x, a.y, a.z);
        a.racer.root.rotation.y = a.heading;
        a.racer.placeShadow(a.x, a.y, a.z, a.heading, 0);
      }
      a.prop?.update(a.x, a.y, a.z, a.heading, clock, a.from ? 1 : 0);
      if (a.dragon && a.shown) placeDragon(a, a.dragon, b);
    }
    // Acting: the speaker talks (about as long as it takes to say the line) and looks
    // at the camera (whoever they're talking to); everyone else looks at the speaker.
    const sp = speakerOf(i);
    if (sp) faceOf(sp.a, speakerFace);
    camAt.copy(game.stage.camera.position);
    const talking = (beats[i]?.text.length ?? 0) / 14 + 0.3;
    for (const [name, a] of actors) {
      if (!a.shown || (!a.person && !a.acting)) continue;
      const me = sp?.a === a;
      const cue = {
        talk: me && t < talking,
        gesture: b?.fx?.gesture?.[name] ?? null,
        look: me || !sp ? (me ? camAt : null) : speakerFace,
      };
      a.acting?.update(dt, cue);
      a.person?.update(a.x, a.y, a.z, a.heading, cue, clock);
    }
    void frameSeconds;
  };

  const shoot = (shot: Shot | undefined) => {
    if (!shot) return;
    const k = ease(Math.min(1, t / 5));
    const from = lerp3(shot.from, shot.to ?? shot.from, k);
    const look = lerp3(shot.look, shot.lookTo ?? shot.look, k);
    const cam = game.stage.camera;
    const shake = beatOf(i)?.fx?.shake ?? 0;
    // (From `shakeAt` seconds into the line: a landing's thud, not its approach.)
    const ts = t - (beatOf(i)?.fx?.shakeAt ?? 0);
    const sh = ts < 0 ? 0 : shake * Math.max(0, 1 - ts / 2.5);
    // (Heights over the ground under the camera, or under what it looks at: rel.)
    // (The ground under the shot's two ends, blended: a camera gliding in over the land
    // shouldn't ride every bump and treetop under it.)
    const g0 = shot.rel
      ? groundAt(shot.look[0], shot.look[2])
      : groundAt(shot.from[0], shot.from[2]);
    const end = shot.rel ? (shot.lookTo ?? shot.look) : (shot.to ?? shot.from);
    const gy = g0 + (groundAt(end[0], end[2]) - g0) * k;
    cam.position.set(
      from[0] + Math.sin(clock * 37) * sh,
      gy + from[1] + Math.sin(clock * 41) * sh,
      from[2] + Math.cos(clock * 33) * sh,
    );
    // (Likewise what it looks at: a look sweeping across the sky mustn't bob with every
    // cliff and treetop under it: Blake, Oct 28, "very shaky".)
    const lookEnd = shot.lookTo ?? shot.look;
    const l0 = groundAt(shot.look[0], shot.look[2]);
    const ly = l0 + (groundAt(lookEnd[0], lookEnd[2]) - l0) * k;
    // Following someone: their position, eased (a steady pan, not a jitter).
    const who = shot.follow ? actors.get(shot.follow) : undefined;
    if (who) {
      followAt.set(who.x, who.y + who.up + (shot.followUp ?? 0), who.z);
      if (!following) followLook.copy(followAt);
      else followLook.lerp(followAt, 1 - Math.exp(-6 * lastDt));
      following = true;
      cam.lookAt(followLook);
    } else {
      following = false;
      cam.lookAt(look[0], ly + look[1], look[2]);
    }
  };
  const followAt = new THREE.Vector3();
  const followLook = new THREE.Vector3();
  let following = false;
  let lastDt = 1 / 60;

  const screen: Screen & { readonly beat: number; readonly cast: Map<string, Actor> } = {
    id: "ADVENTURE_SCENE",
    seeThrough: false,
    /** The line it's on (for the screenshot tools). */
    get beat() {
      return i;
    },
    /** (For the tools: where everyone is, x/y/up/z.) */
    get cast() {
      return actors;
    },
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
      if (staged.music) void game.audio.music.play(staged.music, { fade: 1 });
      // Render the scene's later cues now, so a switch mid-scene comes in on the beat.
      for (const b of staged.beats) if (b.fx?.music) game.audio.music.prepare(b.fx.music);
      const token = game.screens.token;
      game
        .createSession({
          scene: "track",
          packageId: pkg,
          rivals: false,
          racer: game.selection.racer,
          freeRoam: true,
        })
        .then((s) => {
          if (!alive || token !== game.screens.token) return s.dispose();
          session = s;
          game.session = s;
          build(s);
        })
        .catch((e: Error) => {
          console.error(e);
          failed = true;
        });
    },
    exit() {
      alive = false;
      for (const a of actors.values()) {
        a.person?.dispose();
        a.prop?.dispose();
        a.dragon?.dispose();
        if (a.racer && session) a.racer.dispose(session.root);
      }
      if (session) {
        session.dispose();
        if (game.session === session) game.session = undefined;
      }
      pp?.dispose();
    },
    frame(dt, actions) {
      if (failed) return done();
      if (!session) return;
      t += dt;
      clock += dt;
      for (const act of actions) {
        if (act === "back") {
          game.sounds.back();
          return done();
        }
        if (act === "confirm") {
          const full = (beats[i]?.text.length ?? 0) <= Math.floor(t * 50);
          if (!full) {
            t = Math.max(t, 99 / 50 + (beats[i]?.text.length ?? 0) / 50);
            continue;
          }
          game.sounds.move();
          return next();
        }
      }
      if (game.menuInput.pointer.clicked && t > 0.3 && alive) next();
    },
    render3d(alpha, frameSeconds) {
      if (!session) return false;
      session.render(alpha, frameSeconds);
      // (The shot first: the cast look at the camera.)
      lastDt = Math.min(0.1, Math.max(0, frameSeconds));
      shoot(beatOf(i)?.cam);
      place(frameSeconds);
      game.stage.render();
      return true;
    },
    draw(ui) {
      if (!session) {
        ui.rect(0, 0, ui.W, ui.H, "#0c0a08");
        ui.text(title.toUpperCase(), ui.W / 2, ui.H / 2 - 4, {
          color: PAL.gold,
          outline: PAL.shadow,
          align: "center",
        });
        return;
      }
      const b = beatOf(i);
      if (b?.fx?.darken) ui.rect(0, 0, ui.W, ui.H, "#3a0c00", 0.35);
      if (b?.fx?.night) ui.rect(0, 0, ui.W, ui.H, "#0a0a2a", 0.45);
      if (b?.fx?.light)
        ui.rect(
          0,
          0,
          ui.W,
          ui.H,
          "#fff2c0",
          Math.min(0.55, t * 0.4) * (0.8 + 0.2 * Math.sin(clock * 3)),
        );
      if (b?.fx?.fire && t > 0.2)
        ui.rect(0, 0, ui.W, ui.H, "#ff6a10", 0.12 + 0.06 * Math.sin(clock * 9));
      if (b?.fx?.flash && t < 0.6) ui.rect(0, 0, ui.W, ui.H, "#fff2d0", 1 - t / 0.6);
      // The blackout: everything goes dark (a moment of the picture first).
      if (b?.fx?.black) ui.rect(0, 0, ui.W, ui.H, "#000000", Math.min(1, t / 1.2));
      // Fading in from black at the start.
      if (i === 0 && t < 1) ui.rect(0, 0, ui.W, ui.H, "#000000", 1 - t);
      // Letterbox.
      ui.rect(0, 0, ui.W, 22, "#000000");
      ui.rect(0, ui.H - 22, ui.W, 22, "#000000");
      ui.text(title.toUpperCase(), ui.W / 2, 7, { color: PAL.gold, align: "center" });
      const beat = beats[Math.min(i, beats.length - 1)];
      if (!beat) return;
      const bx = 10;
      const bh = 54;
      const by = ui.H - bh - 26;
      const bw = ui.W - 20;
      ui.panel(bx, by, bw, bh, "parchment", "ink");
      const who = beat.who ? CAST[beat.who] : undefined;
      let tx = bx + 10;
      if (who) {
        const slot = portraitSlot(bx, by, bh);
        // (A guard's face is the one on stage: the same folk, the same look.)
        const spec = beat.who ? staged.actors[beat.who] : undefined;
        portrait(
          ui,
          pp,
          who,
          beat.who === "you" ? me : who.look,
          slot.x,
          slot.y,
          ui.time,
          slot.size,
          spec?.kind === "guard" ? { folk: spec.folk, seed: spec.seed } : undefined,
        );
        tx = slot.tx;
        ui.text((beat.who === "you" ? "YOU" : who.name).toUpperCase(), tx, by + 6, {
          color: "#8a2a1a",
        });
      }
      const shown = beat.text.slice(0, Math.floor(t * 50));
      wrap(shown, bw - (tx - bx) - 10)
        .slice(0, 3)
        .forEach((line, j) => ui.text(line, tx, by + (who ? 18 : 10) + j * 10, { color: INK }));
      hints(ui, [
        ["ENTER", "NEXT"],
        ["ESC", "SKIP"],
      ]);
    },
  };
  return screen;
}
