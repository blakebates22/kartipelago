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
import type { StagedScene, Shot, V3 } from "../adventure/staged";
import { regionById } from "../overworld/regions";
import { Racer as RacerView } from "../render/racers/racer";
import { DRAGON_PALETTES } from "../render/racers/roster/dragon";
import type { RacerId } from "../render/racers/designs";
import { createVillagerView, type VillagerView } from "../render/villager";
import {
  createDragonFire,
  createDragonView,
  type DragonFireView,
  type DragonView,
} from "../render/dragon";
import { createPixelPortraits, type PixelPortraits } from "../ui/pixelPortraits";
import { wrap } from "../ui/font";
import { PAL } from "../ui/textures";
import { hints } from "./common";
import { portrait } from "./adventure";

const INK = "#3a2412";
const ease = (t: number) => t * t * (3 - 2 * t);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerp3 = (a: V3, b: V3, t: number): V3 => [
  lerp(a[0], b[0], t),
  lerp(a[1], b[1], t),
  lerp(a[2], b[2], t),
];

interface Actor {
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
    toUp: number;
    toHeading: number;
  };
  racer?: RacerView;
  villager?: VillagerView;
  dragon?: DragonView;
  fire?: DragonFireView;
}

export function stagedSceneScreen(
  game: Game,
  staged: StagedScene,
  title: string,
  beats: Beat[],
  finish: () => void,
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

  const startBeat = (k: number) => {
    const b = staged.beats[k];
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
        toUp: m.y ?? a.up,
        toHeading: m.heading ?? Math.atan2(m.to[0] - a.x, m.to[1] - a.z),
      };
    }
  };
  const next = () => {
    i++;
    t = 0;
    if (i >= beats.length) return done();
    startBeat(i);
  };
  const done = () => {
    alive = false;
    finish();
  };

  const build = (s: Session) => {
    land = s.makeGround();
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
      };
      if (spec.kind === "racer") {
        const look = (spec.look === "you" ? game.selection.racer : spec.look) as RacerId;
        a.racer = new RacerView(look, { seed: name.length * 7 });
        s.root.add(a.racer.root, a.racer.shadow);
      } else if (spec.kind === "villager") {
        a.villager = createVillagerView(s.root, spec.folk, spec.seed, spec.species);
      } else {
        a.dragon = createDragonView(
          s.root,
          { x, y: a.y + a.up, z },
          spec.heading,
          spec.scale ?? 2,
          spec.look ?? "ember",
        );
        // (Its fire's made where it is when it breathes: it may fly in first.)
      }
      actors.set(name, a);
    }
    void DRAGON_PALETTES;
    startBeat(0);
  };

  const place = (frameSeconds: number) => {
    const b = beatOf(i);
    const mouth = new THREE.Vector3();
    for (const a of actors.values()) {
      if (a.from) {
        const k = ease(Math.min(1, (clock - a.from.t0) / Math.max(0.01, a.from.dur)));
        a.x = lerp(a.from.x, a.from.to[0], k);
        a.z = lerp(a.from.z, a.from.to[1], k);
        a.up = lerp(a.from.up, a.from.toUp, k);
        const dh = Math.atan2(
          Math.sin(a.from.toHeading - a.from.heading),
          Math.cos(a.from.toHeading - a.from.heading),
        );
        a.heading = a.from.heading + dh * Math.min(1, k * 2);
        if (k >= 1) a.from = undefined;
      }
      a.y = groundAt(a.x, a.z);
      if (a.racer) {
        a.racer.root.position.set(a.x, a.y, a.z);
        a.racer.root.rotation.y = a.heading;
        a.racer.placeShadow(a.x, a.y, a.z, a.heading, 0);
      }
      a.villager?.update(a.x, a.y, a.z, a.heading, a.from ? 1 : 0, clock);
      if (a.dragon) {
        a.dragon.root.position.set(a.x, a.y + a.up, a.z);
        a.dragon.root.rotation.y = a.heading;
        const name = [...actors.entries()].find(([, v]) => v === a)?.[0];
        const rear = b?.fx?.rear === name;
        const fire = b?.fx?.fire === name;
        const target = new THREE.Vector3(
          a.x + Math.sin(a.heading) * 20,
          a.y,
          a.z + Math.cos(a.heading) * 20,
        );
        const tt = Math.min(1, t / 1.5);
        a.dragon.update(
          fire ? "breathing" : rear ? "warning" : a.up > 2 ? "warning" : "idle",
          fire ? (t % 2) / 2 : tt,
          clock,
          target,
        );
        a.dragon.mouth(mouth);
        if (fire && !a.fire && session)
          a.fire = createDragonFire(session.root, {
            x: a.x + Math.sin(a.heading) * 22,
            y: a.y,
            z: a.z + Math.cos(a.heading) * 22,
            heading: a.heading,
            length: 26,
            width: 14,
            height: 6,
          });
        a.fire?.update(fire ? "breathing" : "idle", (t % 2) / 2, clock, mouth);
      }
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
    const sh = shake * Math.max(0, 1 - t / 2.5);
    cam.position.set(
      from[0] + Math.sin(clock * 37) * sh,
      groundAt(from[0], from[2]) + from[1] + Math.sin(clock * 41) * sh,
      from[2] + Math.cos(clock * 33) * sh,
    );
    cam.lookAt(look[0], groundAt(look[0], look[2]) + look[1], look[2]);
  };

  return {
    id: "ADVENTURE_SCENE",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      pp = createPixelPortraits(game.stage.renderer);
      if (staged.music) void game.audio.music.play(staged.music, { fade: 1 });
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
        a.villager?.dispose();
        a.dragon?.dispose();
        a.fire?.dispose();
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
      if (game.menuInput.pointer.clicked && t > 0.3) next();
    },
    render3d(alpha, frameSeconds) {
      if (!session) return false;
      session.render(alpha, frameSeconds);
      place(frameSeconds);
      shoot(beatOf(i)?.cam);
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
        portrait(
          ui,
          pp,
          who,
          beat.who === "you" ? game.selection.racer : who.look,
          bx + 6,
          by - 22,
          ui.time,
        );
        tx = bx + 64;
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
}
