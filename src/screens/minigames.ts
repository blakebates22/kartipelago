/**
 * The mini-games (src/game/minigames.ts): the menu (pick one of the four), the arena's
 * loading, the game itself (four karts, the rules' things drawn in the arena: balloons
 * over the karts, eggs and nests, the crown's ring, falling stars and their shadows; the
 * scores on screen) and the result. They unlock nothing yet (Blake, Oct 26).
 */
import * as THREE from "three";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import type { Session } from "../game/session";
import type { TrackEntry } from "../game/tracks";
import {
  MINIGAMES,
  RULES,
  createMiniGame,
  newMind,
  iceDrive,
  waypoint,
  clearLine,
  parseArena,
  seek,
  shouldFire,
  type MiniGame,
  type MiniGameInfo,
  type Mind,
} from "../game/minigames";
import { wrap } from "../ui/font";
import { PAL } from "../ui/textures";
import { VMenu, hints } from "./common";
import { drawHud } from "./race";
import { titleScreen } from "./title";

const entryOf = (m: MiniGameInfo): TrackEntry => ({
  id: m.arena,
  name: m.name,
  description: m.blurb,
  preview: "previews/coral_cove.jpg",
  modes: ["race"],
  music: m.kind === "battle" ? "boss" : "race",
  load: { scene: "track", packageId: m.arena },
});

/** The menu: the four games, each with what it's about. */
/** The four mini-games' list. `back`: where ESC goes (the Tracks menu's DEV tab, where
 * they live for now: Blake, Oct 27). */
export function minigameMenu(
  game: Game,
  back: () => void = () => game.screens.go(titleScreen(game, true)),
): Screen {
  const menu = new VMenu(
    game,
    MINIGAMES.map((m) => ({
      label: `${m.name.toUpperCase()}  ${m.kind === "battle" ? "(BATTLE)" : ""}`,
      action: () => game.screens.go(minigameLoading(game, m)),
    })),
    back,
  );
  return {
    id: "MINIGAMES",
    seeThrough: false,
    enter() {
      game.ui.interactive = true;
      void game.audio.music.play("map", { fade: 1 });
    },
    frame(_dt, actions) {
      menu.handle(actions);
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#1c2a1c");
      const w = Math.min(300, ui.W - 20);
      const x = Math.round(ui.W / 2 - w / 2);
      ui.panel(x, 14, w, ui.H - 50, "wood", "gold");
      ui.text("MINI-GAMES", ui.W / 2, 22, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text("JUST FOR FUN, FOR NOW", ui.W / 2, 42, {
        color: PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      menu.draw(ui, x + 16, 58, w - 32, 16, 4);
      const m = MINIGAMES[menu.focus]!;
      wrap(m.blurb, w - 32)
        .slice(0, 3)
        .forEach((l, i) =>
          ui.text(l, ui.W / 2, 150 + i * 10, {
            color: PAL.cream,
            outline: PAL.shadow,
            align: "center",
          }),
        );
      hints(ui, [
        ["▲▼", "CHOOSE"],
        ["ENTER", "PLAY"],
        ["ESC", "BACK"],
      ]);
    },
  };
}

/** Adventure's underground games (the smugglers' mini-game): how it ends goes back to the
 * story (`finish(won)`), and its menus are the story's (play again, or give up). */
export interface MiniGameStory {
  finish(won: boolean): void;
  /** The caption over the scores (the cave's name). */
  title?: string;
}

/** Load the arena (four karts: you and three rivals), then play. */
export function minigameLoading(game: Game, info: MiniGameInfo, story?: MiniGameStory): Screen {
  let ready: Session | undefined;
  /** The session the game's playing in (the rivals' minds read it). */
  let live: Session | undefined;
  let failed = false;
  let alive = true;
  let t = 0;
  // (The rules are made once the arena's loaded; the session asks them how the rivals
  // drive from its first step, so they're looked up late.)
  const box: { g?: MiniGame; minds: Mind[] } = {
    minds: [newMind(), newMind(), newMind(), newMind()],
  };
  return {
    id: "OVERWORLD_LOADING",
    seeThrough: false,
    enter() {
      game.ui.interactive = false;
      game.audio.music.stop(0.6);
      const token = game.screens.token;
      game
        .createSession({
          scene: "track",
          packageId: info.arena,
          rivals: true,
          racer: game.selection.racer,
          field: { count: 3 },
          arena: {
            drive(i, k, dt) {
              const g = box.g;
              if (!g || !live) return undefined;
              const ks = live.entrants.map((e) => e.state);
              if (g.out[i] || g.winner !== undefined)
                return { throttle: 0, brake: 1, steer: 0, drift: false, item: false };
              const tg = g.target(i, ks);
              if (g.ice) return iceDrive(box.minds[i]!, k, g, tg, dt);
              // By the levels (up a ramp to the deck, round it, off it), round what's in
              // the way.
              const w = waypoint(g.arena, k, tg);
              const c = clearLine(k, w.x, w.z, (x, z, y) => live!.kartFits(x, z, y));
              return seek(box.minds[i]!, k, c.x, c.z, dt);
            },
            fire(i, k) {
              const g = box.g;
              if (!g || !live || g.out[i]) return false;
              const ks = live.entrants.map((e) => e.state);
              return shouldFire(i, k, ks, live.entrants[i]!.items.held.color, g.out);
            },
            onItem(ev) {
              if (ev.type === "hit" && !ev.blocked) box.g?.hit(ev.racer);
            },
            topSpeed(i) {
              return box.g?.carrying(i) ? RULES.carrySpeed : undefined;
            },
          },
        })
        .then((s) => {
          if (!alive || token !== game.screens.token) return s.dispose();
          ready = s;
        })
        .catch((e: Error) => {
          console.error(e);
          failed = true;
        });
    },
    exit() {
      alive = false;
    },
    frame(dt) {
      t += dt;
      if (failed) return story ? story.finish(false) : game.screens.go(minigameMenu(game));
      if (ready && t > 0.6) {
        const s = ready;
        ready = undefined;
        alive = false;
        const arena = parseArena(s.entities);
        arena.spawns.slice(0, s.entrants.length).forEach((p, i) => s.place(i, p.x, p.z, p.heading));
        box.g = createMiniGame(info, arena, s.entrants.length, Math.floor(Math.random() * 1e6));
        if (import.meta.env.DEV) (window as unknown as { kpMini?: MiniGame }).kpMini = box.g;
        live = s;
        game.screens.go(minigamePlay(game, s, box.g, info, () => (live = undefined), story));
      }
    },
    draw(ui) {
      ui.rect(0, 0, ui.W, ui.H, "#1a1210");
      ui.text(info.name.toUpperCase(), ui.W / 2, ui.H / 2 - 12, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      ui.text(
        `GETTING THE ARENA READY${".".repeat(1 + (Math.floor(t * 3) % 3))}`,
        ui.W / 2,
        ui.H / 2 + 8,
        {
          color: PAL.cream,
          align: "center",
        },
      );
    },
  };
}

const KART_COLORS = ["#ffd23f", "#ff5a4f", "#2f80ed", "#3fbf6a"];
const CRACKED = new THREE.Color("#7d98ad");
const BREAKING = new THREE.Color("#2a4258");

/** The rules' things in the arena. */
function arenaView(session: Session, g: MiniGame) {
  const group = new THREE.Group();
  group.name = "Mini-game";
  session.root.add(group);
  const made: (THREE.Material | THREE.BufferGeometry)[] = [];
  const mat = (color: string, emissive = 0.25) => {
    const m = new THREE.MeshLambertMaterial({
      color,
      emissive: new THREE.Color(color).multiplyScalar(emissive),
    });
    made.push(m);
    return m;
  };
  const geo = <T extends THREE.BufferGeometry>(x: T) => (made.push(x), x);
  const you = session.entrants[0]!;
  const groundAt = (x: number, z: number) => you.ground.at(x, z, 200).height;
  const shadowGeo = geo(new THREE.CircleGeometry(1.6, 16));
  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.35,
    depthWrite: false,
  });
  made.push(shadowMat);
  // Balloons over each kart (Balloon Brawl): one per life.
  const balloonGeo = geo(new THREE.SphereGeometry(0.45, 10, 8));
  const lives = session.entrants.map((_, i) => {
    const m = mat(KART_COLORS[i % 4]!, 0.3);
    return [0, 1, 2].map(() => {
      const b = new THREE.Mesh(balloonGeo, m);
      group.add(b);
      return b;
    });
  });
  // Docks (Smugglers' Run): a glowing ring of the crew's colour at each.
  const ringGeo = geo(new THREE.TorusGeometry(RULES.dockRadius, 0.35, 6, 28));
  g.arena.docks.forEach((n, i) => {
    const r = new THREE.Mesh(ringGeo, mat(KART_COLORS[i % 4]!, 0.6));
    r.rotation.x = Math.PI / 2;
    r.position.set(n.x, n.y + 0.3, n.z);
    group.add(r);
  });
  // The crates: planks with dark iron bands.
  const crateGeo = geo(new THREE.BoxGeometry(1.5, 1.2, 1.5));
  const bandGeo = geo(new THREE.BoxGeometry(1.56, 0.18, 1.56));
  const crateMat = mat("#a8743a", 0.1);
  const bandMat = mat("#3a2a1c", 0.05);
  const crates: { g: THREE.Group; s: THREE.Mesh }[] = [];
  // The ice (Crumble Rink): a hexagonal slab per tile; cracking ones shiver and darken,
  // gone ones drop away into the crevasse.
  let tiles: THREE.InstancedMesh | undefined;
  const ice = g.ice;
  const tileColor = new THREE.Color();
  const m4 = new THREE.Matrix4();
  if (ice) {
    const hex = geo(new THREE.CylinderGeometry(ice.size * 0.96, ice.size * 0.9, 0.9, 6));
    hex.rotateY(Math.PI / 6);
    hex.translate(0, -0.45, 0);
    const iceMat = new THREE.MeshLambertMaterial({ color: 0xffffff });
    made.push(iceMat);
    tiles = new THREE.InstancedMesh(hex, iceMat, ice.state.length);
    for (let t = 0; t < ice.state.length; t++) {
      // (A little variety: blue-white ice, some frostier.)
      const v = ((t * 7919) % 100) / 100;
      tiles.setColorAt(t, tileColor.setHSL(0.55, 0.45 + v * 0.2, 0.78 + v * 0.08));
    }
    group.add(tiles);
  }
  const base = ice
    ? Array.from({ length: ice.state.length }, (_, t) =>
        tiles!.instanceColor!.array.slice(t * 3, t * 3 + 3),
      )
    : [];
  // Stars and their shadows (Star Fall).
  const starGeo = geo(new THREE.OctahedronGeometry(1.0));
  const starMat = mat("#ffe060", 0.7);
  const goldMat = mat("#ff9a20", 0.8);
  const stars: { m: THREE.Mesh; s: THREE.Mesh }[] = [];
  // Out of Crumble Rink: the kart's gone through the ice.
  const gone = session.entrants.map(() => false);
  return {
    update(t: number) {
      session.entrants.forEach((e, i) => {
        const k = e.state;
        lives[i]!.forEach((b, j) => {
          b.visible = g.info.id === "balloons" && j < g.score[i]!;
          b.position.set(
            k.x + Math.sin(t * 2 + j * 2.1) * 0.5 + (j - 1) * 0.6,
            k.y + 3.2 + j * 0.25 + Math.sin(t * 3 + j) * 0.1,
            k.z + Math.cos(t * 2 + j * 2.1) * 0.5,
          );
        });
        if (ice && g.out[i] && !gone[i]) {
          gone[i] = true;
          e.mesh.visible = false;
          e.racer.shadow.visible = false;
        }
      });
      while (crates.length < g.crates.length) {
        const c = new THREE.Group();
        c.add(new THREE.Mesh(crateGeo, crateMat));
        for (const y of [-0.38, 0.38]) {
          const b = new THREE.Mesh(bandGeo, bandMat);
          b.position.y = y;
          c.add(b);
        }
        const s = new THREE.Mesh(shadowGeo, shadowMat);
        s.rotation.x = -Math.PI / 2;
        group.add(c, s);
        crates.push({ g: c, s });
      }
      crates.forEach((v, i) => {
        const c = g.crates[i];
        v.g.visible = v.s.visible = Boolean(c);
        if (!c) return;
        const carried = c.carrier >= 0;
        const k = carried ? session.entrants[c.carrier]!.state : undefined;
        const y = k ? k.y : groundAt(c.x, c.z);
        v.g.position.set(c.x, (k ? y + 2.4 : y + 0.6) + Math.max(0, c.fall) * 20, c.z);
        v.g.rotation.y = carried ? k!.heading : i * 1.3;
        v.s.visible = c.fall > 0;
        v.s.position.set(c.x, groundAt(c.x, c.z) + 0.08, c.z);
        v.s.scale.setScalar(1.2 - Math.max(0, c.fall) * 0.3);
      });
      if (ice && tiles) {
        for (let n = 0; n < ice.state.length; n++) {
          const st = ice.state[n];
          let y = ice.y;
          let dx = 0;
          let dz = 0;
          let scale = 1;
          const c = base[n]!;
          tileColor.setRGB(c[0]!, c[1]!, c[2]!);
          if (st === 1) {
            // Cracked: greyer, a little sunk.
            tileColor.lerp(CRACKED, 0.35);
            y -= 0.04;
          } else if (st === 3) {
            // Breaking: shivering, darker as it goes.
            const k = Math.max(0, Math.min(1, 1 - ice.timer[n]! / RULES.breakSec));
            dx = Math.sin(t * 61 + n) * 0.08 * (0.4 + k);
            dz = Math.cos(t * 53 + n) * 0.08 * (0.4 + k);
            tileColor.lerp(BREAKING, 0.45 + k * 0.4);
            y -= 0.1;
          } else if (st === 2) {
            const f = ice.timer[n]!;
            y -= 9 * f * f;
            scale = f > 1.6 ? 0 : 1;
            tileColor.lerp(BREAKING, 0.8);
          }
          m4.makeScale(scale, scale, scale).setPosition(ice.x[n]! + dx, y, ice.z[n]! + dz);
          tiles.setMatrixAt(n, m4);
          tiles.setColorAt(n, tileColor);
        }
        tiles.instanceMatrix.needsUpdate = true;
        tiles.instanceColor!.needsUpdate = true;
      }
      while (stars.length < g.stars.length) {
        const m = new THREE.Mesh(starGeo, starMat);
        const s = new THREE.Mesh(shadowGeo, shadowMat);
        s.rotation.x = -Math.PI / 2;
        group.add(m, s);
        stars.push({ m, s });
      }
      stars.forEach((v, i) => {
        const st = g.stars[i];
        v.m.visible = v.s.visible = Boolean(st);
        if (!st) return;
        const y = groundAt(st.x, st.z);
        v.m.material = st.gold ? goldMat : starMat;
        v.m.scale.setScalar(st.gold ? 1.4 : 1);
        v.m.position.set(st.x, y + 1.4 + Math.max(0, st.fall) * 22, st.z);
        v.m.rotation.y = t * 3;
        v.s.position.set(st.x, y + 0.08, st.z);
        v.s.scale.setScalar(st.fall > 0 ? 1.2 - st.fall * 0.3 : 1);
      });
    },
    dispose() {
      session.root.remove(group);
      tiles?.dispose();
      for (const m of made) m.dispose();
    },
  };
}

function minigamePlay(
  game: Game,
  session: Session,
  g: MiniGame,
  info: MiniGameInfo,
  release: () => void,
  story?: MiniGameStory,
): Screen {
  const entry = entryOf(info);
  let clock = 0;
  let view: ReturnType<typeof arenaView> | undefined;
  let over: VMenu | undefined;
  const names = session.entrants.map((e, i) => (i === 0 ? "YOU" : e.name.toUpperCase()));
  const label = (v: number) =>
    info.id === "balloons" ? `${v} LEFT` : info.id === "crumble" ? "ON THE ICE" : `${v}`;
  const finish = () => {
    const won = g.winner === 0;
    over = new VMenu(
      game,
      story
        ? [
            { label: "CONTINUE", action: () => story.finish(won) },
            ...(won
              ? []
              : [
                  {
                    label: "PLAY AGAIN",
                    action: () => game.screens.go(minigameLoading(game, info, story)),
                  },
                ]),
          ]
        : [
            { label: "PLAY AGAIN", action: () => game.screens.go(minigameLoading(game, info)) },
            { label: "OTHER GAMES", action: () => game.screens.go(minigameMenu(game)) },
            { label: "MAIN MENU", action: () => game.screens.go(titleScreen(game, true)) },
          ],
    );
    game.ui.interactive = true;
    game.sounds.confirm();
  };
  return {
    id: "MINIGAME",
    enter() {
      game.session = session;
      game.ui.interactive = false;
      view = arenaView(session, g);
      void game.audio.music.play(entry.music, { fade: 1.2, restart: true });
    },
    exit() {
      release();
      view?.dispose();
      session.dispose();
      if (game.session === session) game.session = undefined;
    },
    step(dt, top) {
      if (!top) return;
      session.update(dt);
      const ks = session.entrants.map((e) => e.state);
      const before = g.winner;
      g.step(ks, dt);
      // (Out of Balloon Brawl: your kart stops.)
      if (g.out[0]) ks[0]!.speed *= 0.9;
      for (const n of g.news) {
        if (n.what === "pop" && n.who === 0) game.sounds.error();
        if (n.what === "drop" && n.who === 0) game.sounds.error();
        if (n.what === "fall" && n.who === 0) game.sounds.error();
        if ((n.what === "star" || n.what === "dock" || n.what === "grab") && n.who === 0)
          game.sounds.confirm();
      }
      if (before === undefined && g.winner !== undefined) finish();
    },
    frame(dt, actions, top) {
      clock += dt;
      view?.update(clock);
      if (!top) return;
      if (over) {
        over.handle(actions);
        return;
      }
      if (actions.some((a) => a === "pause" || a === "back"))
        game.screens.push(minigamePause(game, info, story));
    },
    render3d(alpha, frameSeconds) {
      session.render(alpha, frameSeconds);
      game.stage.render();
      return true;
    },
    draw(ui) {
      drawHud(ui, session, entry, true, undefined, clock);
      // The scores, top left: everyone's, in their colours.
      const w = 150;
      ui.panel(6, 6, w, 18 + names.length * 11, "wood", "gold");
      ui.text((story?.title ?? info.name).toUpperCase(), 6 + w / 2, 10, {
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      names.forEach((n, i) => {
        const dead = g.out[i];
        ui.text(n, 14, 22 + i * 11, {
          color: dead ? "#8a8a8a" : KART_COLORS[i % 4],
          outline: PAL.shadow,
        });
        ui.text(dead ? "OUT" : label(g.score[i]!), 6 + w - 10, 22 + i * 11, {
          color: dead ? "#8a8a8a" : PAL.cream,
          outline: PAL.shadow,
          align: "right",
        });
      });
      const c = Math.max(0, g.clock);
      ui.text(`${Math.floor(c / 60)}:${String(Math.floor(c % 60)).padStart(2, "0")}`, ui.W / 2, 8, {
        scale: 2,
        color: c < 15 ? PAL.coral : PAL.cream,
        outline: PAL.shadow,
        align: "center",
      });
      if (g.out[0] && g.winner === undefined)
        ui.text(
          info.id === "crumble"
            ? "THROUGH THE ICE! WATCH THE REST..."
            : "YOU'RE OUT! WATCH THE REST...",
          ui.W / 2,
          30,
          {
            color: PAL.coral,
            outline: PAL.shadow,
            align: "center",
          },
        );
      if (over && g.winner !== undefined) {
        const pw = 220;
        const px = Math.round(ui.W / 2 - pw / 2);
        const py = 50;
        ui.panel(px, py, pw, 150, "parchment", "ink");
        const won = g.winner === 0;
        ui.text(won ? "YOU WIN!" : `${names[g.winner]} WINS!`, ui.W / 2, py + 10, {
          scale: 2,
          color: won ? PAL.gold : PAL.coral,
          outline: PAL.ink,
          align: "center",
        });
        g.standings().forEach((i, r) =>
          ui.text(
            `${r + 1}. ${names[i]}  ${g.out[i] ? "OUT" : label(g.score[i]!)}`,
            ui.W / 2,
            py + 34 + r * 10,
            {
              color: PAL.ink,
              align: "center",
            },
          ),
        );
        over.draw(ui, px + 40, py + 84, pw - 80, 16, 4);
      }
    },
  };
}

function minigamePause(game: Game, info: MiniGameInfo, story?: MiniGameStory): Screen {
  const menu = new VMenu(
    game,
    story
      ? [
          { label: "RESUME", action: () => game.screens.pop() },
          {
            label: "START AGAIN",
            action: () => game.screens.go(minigameLoading(game, info, story)),
          },
          { label: "GIVE UP", action: () => story.finish(false) },
        ]
      : [
          { label: "RESUME", action: () => game.screens.pop() },
          { label: "START AGAIN", action: () => game.screens.go(minigameLoading(game, info)) },
          { label: "OTHER GAMES", action: () => game.screens.go(minigameMenu(game)) },
          { label: "MAIN MENU", action: () => game.screens.go(titleScreen(game, true)) },
        ],
    () => game.screens.pop(),
  );
  return {
    id: "PAUSED",
    enter() {
      game.ui.interactive = true;
    },
    frame(_dt, actions) {
      if (actions.includes("pause")) return game.screens.pop();
      menu.handle(actions);
    },
    draw(ui) {
      ui.dim(0.45);
      const w = 140;
      const x = ui.W / 2 - w / 2;
      ui.panel(x, 60, w, 120, "wood", "gold");
      ui.text("PAUSED", ui.W / 2, 70, {
        scale: 2,
        color: PAL.gold,
        outline: PAL.shadow,
        align: "center",
      });
      menu.draw(ui, x + 14, 96, w - 28, 16, 4);
    },
  };
}
