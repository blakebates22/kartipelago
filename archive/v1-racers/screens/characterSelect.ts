/**
 * CHARACTER_SELECT ("Select Racer"): a jungle clearing with your highlighted racer turning
 * on a big stone pedestal, the others waiting on small pedestals in front, and an info
 * board with their name, title, a line about them and their motto.
 *
 * Left and right cycle the racers (or click one); each one hops when highlighted, and
 * boosts then celebrates when picked. Looks don't change driving, so there are no stat
 * bars here: driving stats are chosen separately. The music is "Pick Your Racer": the same piece throughout,
 * with the highlighted racer's instruments faded up (no restart).
 *
 * This scene is only a picture: the racer is the real 3D model, driven by a made-up
 * motion state, with no physics or race behind it.
 */
import * as THREE from "three";
import type { Game } from "../app/game";
import type { Screen } from "../app/app";
import { saveSettings } from "../app/settings";
import { RACER_STEMS } from "../audio/songs";
import { Racer, type RacerMotion } from "../render/racers/racer";
import { DESIGNS, RACER_IDS, type RacerId } from "../render/racers/designs";
import { disposeObject } from "../world/trackPackage";
import { PAL } from "../ui/textures";
import { wrap } from "../ui/font";
import { hints, titleSign } from "./common";
import { modeSelect } from "./modeSelect";
import { titleScreen } from "./title";

/** Where the other racers wait, on lower pedestals in front (x, z). */
const BENCH: [number, number][] = [
  [-3.6, 3.5],
  [0, 4.1],
  [3.6, 3.5],
];

function stoneMat(color: string) {
  return new THREE.MeshLambertMaterial({ color, flatShading: true });
}

/** A carved stone pedestal with a mossy rim. */
function pedestal(r: number, h: number) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.CylinderGeometry(r, r * 1.08, h, 10), stoneMat("#9d978a"));
  base.position.y = h / 2;
  const top = new THREE.Mesh(
    new THREE.CylinderGeometry(r * 1.04, r * 1.02, 0.12, 10),
    stoneMat("#b9b3a4"),
  );
  top.position.y = h + 0.02;
  const moss = new THREE.Mesh(
    new THREE.TorusGeometry(r * 1.02, 0.07, 3, 10).rotateX(Math.PI / 2),
    stoneMat("#5f9a3a"),
  );
  moss.position.y = h + 0.06;
  g.add(base, top, moss);
  return g;
}

function buildScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#7cc5f2");
  scene.fog = new THREE.Fog("#a9dcf5", 26, 80);
  const sun = new THREE.DirectionalLight("#fff0d2", 2.3);
  sun.position.set(4, 8, 7);
  scene.add(sun, new THREE.HemisphereLight("#e2f4ff", "#5d7a3a", 1.2));
  // A jungle clearing on an island: sea, sand, grass, cliffs and a far volcano.
  const sea = new THREE.Mesh(
    new THREE.CircleGeometry(90, 32).rotateX(-Math.PI / 2),
    new THREE.MeshLambertMaterial({ color: "#2ec4b6" }),
  );
  sea.position.y = -1.2;
  const sand = new THREE.Mesh(new THREE.CylinderGeometry(15, 16.5, 1.2, 18), stoneMat("#e6cf98"));
  sand.position.y = -0.85;
  const grass = new THREE.Mesh(
    new THREE.CylinderGeometry(12.5, 13.5, 1.2, 18),
    stoneMat("#62b03a"),
  );
  grass.position.y = -0.62;
  scene.add(sea, sand, grass);
  // Cliffs behind, with waterfalls, and the volcano beyond.
  for (const [x, z, w, h] of [
    [-10, -9, 6, 7],
    [-3, -12, 7, 9],
    [5, -11, 6, 8],
    [11, -8, 5, 6],
  ] as const) {
    const cliff = new THREE.Mesh(
      new THREE.CylinderGeometry(w * 0.45, w * 0.55, h, 7),
      stoneMat("#8e8070"),
    );
    cliff.position.set(x, h / 2 - 0.5, z);
    const cap = new THREE.Mesh(
      new THREE.CylinderGeometry(w * 0.47, w * 0.45, 0.6, 7),
      stoneMat("#4f9a35"),
    );
    cap.position.set(x, h - 0.4, z);
    scene.add(cliff, cap);
  }
  for (const [x, z, h] of [
    [-4.6, -9.4, 7.2],
    [7.2, -8.6, 6.2],
  ] as const) {
    const fall = new THREE.Mesh(
      new THREE.PlaneGeometry(1.1, h),
      new THREE.MeshLambertMaterial({ color: "#bfe9fb", emissive: "#3a7a9a" }),
    );
    fall.position.set(x, h / 2 - 0.6, z);
    scene.add(fall);
  }
  const volcano = new THREE.Mesh(new THREE.ConeGeometry(14, 16, 9), stoneMat("#6a5a56"));
  volcano.position.set(20, 4, -40);
  const lava = new THREE.Mesh(
    new THREE.ConeGeometry(3.2, 3.4, 9),
    new THREE.MeshBasicMaterial({ color: "#ff6a2a" }),
  );
  lava.position.set(20, 10.6, -40);
  scene.add(volcano, lava);
  // Palms and tiki torches round the clearing.
  const palm = (x: number, z: number, h: number, lean: number) => {
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.22, h, 6), stoneMat("#8a5a32"));
    trunk.position.set(x, h / 2, z);
    trunk.rotation.z = lean;
    const top = new THREE.Group();
    top.position.set(x - Math.sin(lean) * h * 0.5, h, z);
    for (let i = 0; i < 6; i++) {
      const leaf = new THREE.Mesh(
        new THREE.ConeGeometry(0.35, 2.2, 3),
        stoneMat(i % 2 ? "#2f8a32" : "#3fa83a"),
      );
      leaf.rotation.set(0, (i / 6) * Math.PI * 2, 1.9);
      leaf.position.set(
        Math.cos((i / 6) * Math.PI * 2) * 0.9,
        -0.3,
        -Math.sin((i / 6) * Math.PI * 2) * 0.9,
      );
      leaf.lookAt(
        top.position
          .clone()
          .add(
            new THREE.Vector3(
              Math.cos((i / 6) * Math.PI * 2) * 3,
              -1.6,
              -Math.sin((i / 6) * Math.PI * 2) * 3,
            ),
          ),
      );
      top.add(leaf);
    }
    scene.add(trunk, top);
  };
  palm(-7.5, -3.5, 5.5, 0.12);
  palm(-9, 0.5, 4.6, -0.1);
  palm(7.8, -3, 5.2, -0.14);
  palm(9.4, 1.2, 4.2, 0.1);
  const flames: THREE.Mesh[] = [];
  for (const x of [-6.2, 6.2]) {
    const post = new THREE.Mesh(
      new THREE.CylinderGeometry(0.14, 0.18, 2.2, 6),
      stoneMat("#6a4426"),
    );
    post.position.set(x, 1.1, 1.6);
    const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.2, 0.3, 7), stoneMat("#4a2f1c"));
    bowl.position.set(x, 2.3, 1.6);
    const flame = new THREE.Mesh(
      new THREE.ConeGeometry(0.26, 0.7, 6),
      new THREE.MeshBasicMaterial({ color: "#ffb02a" }),
    );
    flame.position.set(x, 2.75, 1.6);
    flames.push(flame);
    scene.add(post, bowl, flame);
  }
  // The big pedestal (with a turntable top) and three small ones in front.
  const stage = pedestal(2.1, 1.9);
  stage.position.z = -1.4;
  const turntable = new THREE.Group();
  turntable.position.y = 2.02;
  stage.add(turntable);
  scene.add(stage);
  const bench = BENCH.map(([x, z]) => {
    const p = pedestal(1.25, 0.5);
    p.position.set(x, 0, z);
    scene.add(p);
    const spot = new THREE.Group();
    spot.position.set(x, 0.62, z);
    scene.add(spot);
    return spot;
  });
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);
  camera.position.set(0, 6.2, 14.5);
  camera.lookAt(0, 1.9, 0);
  return { scene, camera, turntable, bench, flames };
}

export function characterSelect(game: Game): Screen {
  let index = Math.max(0, RACER_IDS.indexOf(game.settings.last.racer));
  let built: ReturnType<typeof buildScene> | undefined;
  let racer: Racer | undefined;
  /** The others, waiting on the small pedestals. */
  let waiting: { racer: Racer; id: RacerId }[] = [];
  let t = 0;
  let spin = 0;
  /** Reaction timers. */
  let hop = 0;
  let cheer = 0;
  let picked = -1;
  let clicked: "left" | "right" | "confirm" | number | undefined;
  const still = (): RacerMotion => ({
    speed: 0,
    steer: 0,
    driftDir: 0,
    slip: 0,
    grounded: true,
    throttle: false,
    boostPhase: 0,
    boostEnhanced: false,
    boostLeft: 0,
    impactTier: 0,
    impactSpeed: 0,
    spinTime: 0,
  });
  const motion = still();
  const idle = still();
  const id = () => RACER_IDS[index]!;
  const others = () => RACER_IDS.filter((r) => r !== id());

  const drop = (r: Racer) => {
    r.root.removeFromParent();
    r.shadow.removeFromParent();
    disposeObject(r.root);
    disposeObject(r.shadow);
  };

  function showRacers() {
    if (!built) return;
    if (racer) drop(racer);
    for (const w of waiting) drop(w.racer);
    racer = new Racer(id(), { seed: index * 11 + 3 });
    racer.root.scale.setScalar(1.6);
    racer.placeShadow(0, 0, 0, 0, 0);
    built.turntable.add(racer.root, racer.shadow);
    // The others, a little smaller, each turned toward the middle.
    waiting = others().map((rid, i) => {
      const r = new Racer(rid, { seed: i * 7 + 1 });
      r.root.scale.setScalar(0.9);
      r.root.rotation.y = -BENCH[i]![0] * 0.12;
      r.placeShadow(0, 0, 0, 0, 0);
      built!.bench[i]!.add(r.root, r.shadow);
      return { racer: r, id: rid };
    });
    hop = 0.32;
  }

  function highlight(d: number) {
    if (picked >= 0) return;
    const before = id();
    index = (index + d + RACER_IDS.length) % RACER_IDS.length;
    game.audio.music.layer(before, 0, 0.5);
    game.audio.music.layer(id(), 1, 0.5);
    game.sounds.racer(id());
    showRacers();
  }

  function choose() {
    if (picked >= 0) return;
    picked = 0;
    cheer = 1.2;
    game.sounds.racerPicked(id());
    game.selection.racer = id();
    game.settings.last.racer = id();
    saveSettings(game.settings);
  }

  return {
    id: "CHARACTER_SELECT",
    seeThrough: false,
    enter() {
      built = buildScene();
      showRacers();
      const layers = Object.fromEntries(RACER_STEMS.map((s) => [s, s === id() ? 1 : 0]));
      void game.audio.music.play("select", { fade: 0.8, layers });
      game.audio.music.prepare("map");
    },
    exit() {
      if (built) disposeObject(built.scene);
      built = undefined;
      racer = undefined;
      waiting = [];
    },
    frame(dt, actions) {
      t += dt;
      spin += dt * (game.settings.general.reduceMotion ? 0.15 : 0.5);
      const act: (string | number)[] = [...actions];
      if (clicked !== undefined) act.push(clicked);
      clicked = undefined;
      for (const a of act) {
        if (typeof a === "number") {
          // Clicked one of the waiting racers: bring them up.
          const target = RACER_IDS.indexOf(others()[a]!);
          if (target >= 0) highlight(target - index);
        } else if (a === "left") highlight(-1);
        else if (a === "right") highlight(1);
        else if (a === "confirm") choose();
        else if (a === "back" && picked < 0) {
          game.sounds.back();
          game.screens.go(titleScreen(game, true));
        }
      }
      if (picked >= 0) {
        picked += dt;
        if (picked > 1.4) game.screens.go(modeSelect(game));
      }
      // Reactions: a hop when highlighted; picked, a boost and their victory pose.
      hop = Math.max(0, hop - dt);
      cheer = Math.max(0, cheer - dt);
      motion.grounded = !(hop > 0 && hop < 0.26);
      motion.speed = cheer > 0.6 ? 6 : 0;
      motion.boostPhase = cheer > 0.6 ? 1 : 0;
      motion.boostEnhanced = cheer > 0.6;
      motion.boostLeft = cheer;
      motion.steer = Math.sin(t * 1.3) * 0.25;
      if (racer) {
        racer.setResult(picked >= 0 && cheer < 0.7 ? 1 : null, 8);
        racer.animate(dt, motion, { x: 2, z: 3 });
        racer.flame.visible = cheer > 0.6;
        racer.core.visible = cheer > 0.6;
        racer.root.position.y = hop > 0 ? Math.sin((hop / 0.32) * Math.PI) * 0.55 : 0;
      }
      waiting.forEach((w, i) => {
        idle.steer = Math.sin(t * 0.7 + i * 2) * 0.15;
        w.racer.animate(dt, idle, { x: -BENCH[i]![0], z: 2 });
      });
      if (built) {
        built.turntable.rotation.y = game.settings.general.reduceMotion ? 0.5 : spin;
        built.flames.forEach((f, i) => f.scale.set(1, 0.85 + Math.sin(t * 13 + i * 2) * 0.15, 1));
      }
    },
    render3d() {
      if (!built) return false;
      game.stage.renderOther(built.scene, built.camera);
      return true;
    },
    draw(ui) {
      titleSign(ui, "SELECT RACER");
      const d = DESIGNS[id()];
      // Arrows either side of the big pedestal.
      const bob = Math.round(Math.sin(t * 5) * 2);
      const lx = ui.W / 2 - 70 - bob;
      const rx = ui.W / 2 + 54 + bob;
      ui.text("◀", lx, 88, { scale: 2, color: "#7ee05a", outline: PAL.shadow });
      ui.text("▶", rx, 88, { scale: 2, color: "#7ee05a", outline: PAL.shadow });
      const click = game.menuInput.pointer.clicked;
      if (click) {
        if (ui.hover(lx - 6, 84, 22, 34)) clicked = "left";
        else if (ui.hover(rx - 6, 84, 22, 34)) clicked = "right";
        else if (ui.hover(ui.W / 2 - 55, 44, 110, 100)) clicked = "confirm";
      }
      // The info board, to the right: name, title, a line about them, their motto.
      const bw = 112;
      const bx = Math.max(ui.W / 2 + 64, ui.W - bw - 8);
      const by = 34;
      const bio = wrap(d.bio, bw - 10);
      const quote = wrap(`"${d.quote}"`, bw - 14);
      const bh = 40 + bio.length * 9 + quote.length * 9 + 8;
      ui.panel(bx, by, bw, bh, "parchment", "ink");
      ui.panel(bx + 6, by + 4, bw - 12, 18, "wood", "gold");
      ui.text(d.name.toUpperCase(), bx + bw / 2, by + 7, {
        scale: 2,
        color: d.color,
        outline: PAL.ink,
        align: "center",
      });
      ui.text(d.title.toUpperCase(), bx + bw / 2, by + 26, { color: PAL.inkSoft, align: "center" });
      bio.forEach((line, i) =>
        ui.text(line, bx + bw / 2, by + 38 + i * 9, { color: PAL.ink, align: "center" }),
      );
      const qy = by + 42 + bio.length * 9;
      ui.rect(bx + 8, qy - 3, bw - 16, 1, "#b08a5a");
      quote.forEach((line, i) =>
        ui.text(line, bx + bw / 2, qy + 1 + i * 9, { color: "#a8402a", align: "center" }),
      );
      // Name plates under the waiting racers (click one to bring them up).
      others().forEach((r, i) => {
        const px = Math.round(ui.W / 2 + BENCH[i]![0] * 25 - 30);
        const py = 206 - (i === 1 ? 0 : 6);
        ui.panel(px, py, 60, 14, "wood", "dark");
        ui.text(DESIGNS[r].name.toUpperCase(), px + 30, py + 4, {
          color: DESIGNS[r].color,
          outline: PAL.shadow,
          align: "center",
        });
        if (click && ui.hover(px, py - 50, 60, 64)) clicked = i;
      });
      if (picked >= 0)
        ui.text(`${d.name.toUpperCase()}!`, ui.W / 2, 64, {
          scale: 3,
          color: PAL.gold,
          outline: PAL.shadow,
          align: "center",
        });
      hints(ui, [
        ["◀▶", "CHOOSE"],
        ["ENTER", "CONFIRM"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
