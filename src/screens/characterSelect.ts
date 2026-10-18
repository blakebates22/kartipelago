/**
 * CHARACTER_SELECT: your racer, in their kart, on a little turntable island.
 *
 * Left and right cycle the racers; each one hops when highlighted and gives a big grin
 * and a boost when picked. The music is "Pick Your Racer": the same piece throughout,
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

/** A line about each racer (personality only: looks never change how a kart drives). */
export const BIOS: Record<RacerId, string> = {
  moss: "ALWAYS SMILING, NEVER IN A HURRY... UNTIL THE LIGHTS GO GREEN.",
  bramble: "STASHES SHORTCUTS LIKE ACORNS. KNOWS EVERY CORNER BY HEART.",
  poppy: "CHASES BRIGHT LIGHTS AT FULL THROTTLE. LOVES A SUNSET RACE.",
  otto: "CALM AS A HOT SPRING. SOMEHOW ALWAYS FIRST TO THE SNACKS.",
};

function buildScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#7cc5f2");
  scene.fog = new THREE.Fog("#a9dcf5", 18, 60);
  const sun = new THREE.DirectionalLight("#fff0d2", 2.2);
  sun.position.set(4, 8, 6);
  scene.add(sun, new THREE.HemisphereLight("#e2f4ff", "#5d7a3a", 1.2));
  // A grassy island on a turquoise sea, with a stone turntable.
  const sea = new THREE.Mesh(
    new THREE.CircleGeometry(60, 32).rotateX(-Math.PI / 2),
    new THREE.MeshLambertMaterial({ color: "#2ec4b6" }),
  );
  sea.position.y = -1.2;
  const island = new THREE.Mesh(
    new THREE.CylinderGeometry(7, 8.5, 1.4, 14),
    new THREE.MeshLambertMaterial({ color: "#6abe30", flatShading: true }),
  );
  island.position.y = -0.7;
  const turntable = new THREE.Group();
  const disc = new THREE.Mesh(
    new THREE.CylinderGeometry(2.9, 3.1, 0.35, 16),
    new THREE.MeshLambertMaterial({ color: "#a9a59a", flatShading: true }),
  );
  disc.position.y = 0.15;
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(3, 0.12, 4, 24).rotateX(Math.PI / 2),
    new THREE.MeshLambertMaterial({ color: "#f7c948" }),
  );
  ring.position.y = 0.33;
  turntable.add(disc, ring);
  scene.add(sea, island, turntable);
  // A few low-poly palms and rocks round the edge.
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2 + 0.4;
    const r = 5.4 + (i % 2) * 0.8;
    const x = Math.cos(a) * r;
    const z = Math.sin(a) * r;
    if (z > 2.5) continue; // keep the camera's view clear
    if (i % 3 === 0) {
      const rock = new THREE.Mesh(
        new THREE.IcosahedronGeometry(0.7, 0),
        new THREE.MeshLambertMaterial({ color: "#8d8a80", flatShading: true }),
      );
      rock.position.set(x, 0.2, z);
      scene.add(rock);
    } else {
      const trunk = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.18, 2.4, 6),
        new THREE.MeshLambertMaterial({ color: "#7a4f2a", flatShading: true }),
      );
      trunk.position.set(x, 1.2, z);
      trunk.rotation.z = 0.15;
      const leaves = new THREE.Mesh(
        new THREE.ConeGeometry(1.2, 0.8, 6),
        new THREE.MeshLambertMaterial({ color: "#2f7a32", flatShading: true }),
      );
      leaves.position.set(x + 0.18, 2.5, z);
      scene.add(trunk, leaves);
    }
  }
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 200);
  camera.position.set(0, 3.1, 10.5);
  camera.lookAt(0, 1.05, 0);
  return { scene, camera, turntable };
}

export function characterSelect(game: Game): Screen {
  let index = Math.max(0, RACER_IDS.indexOf(game.settings.last.racer));
  let built: ReturnType<typeof buildScene> | undefined;
  let racer: Racer | undefined;
  let t = 0;
  let spin = 0;
  /** Reaction timers. */
  let hop = 0;
  let cheer = 0;
  let picked = -1;
  let clicked: "left" | "right" | "confirm" | undefined;
  const motion: RacerMotion = {
    speed: 0,
    steer: 0,
    driftDir: 0,
    slip: 0,
    grounded: true,
    boostPhase: 0,
    boostEnhanced: false,
    boostLeft: 0,
    impactTier: 0,
    impactSpeed: 0,
    spinTime: 0,
  };
  const id = () => RACER_IDS[index]!;

  function showRacer() {
    if (!built) return;
    if (racer) {
      built.turntable.remove(racer.root, racer.shadow);
      disposeObject(racer.root);
      disposeObject(racer.shadow);
    }
    racer = new Racer(id(), { seed: index * 11 + 3 });
    racer.root.position.y = 0.72;
    racer.root.scale.setScalar(1.15);
    racer.placeShadow(0, 0.33, 0, 0, 0);
    built.turntable.add(racer.root, racer.shadow);
    hop = 0.32;
  }

  function highlight(d: number) {
    if (picked >= 0) return;
    const before = id();
    index = (index + d + RACER_IDS.length) % RACER_IDS.length;
    game.audio.music.layer(before, 0, 0.5);
    game.audio.music.layer(id(), 1, 0.5);
    game.sounds.racer(id());
    showRacer();
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
      showRacer();
      const layers = Object.fromEntries(RACER_STEMS.map((s) => [s, s === id() ? 1 : 0]));
      void game.audio.music.play("select", { fade: 0.8, layers });
      game.audio.music.prepare("map");
    },
    exit() {
      if (built) disposeObject(built.scene);
      built = undefined;
      racer = undefined;
    },
    frame(dt, actions) {
      t += dt;
      spin += dt * (game.settings.general.reduceMotion ? 0.15 : 0.45);
      const act = [...actions];
      if (clicked) act.push(clicked);
      clicked = undefined;
      for (const a of act) {
        if (a === "left") highlight(-1);
        else if (a === "right") highlight(1);
        else if (a === "confirm") choose();
        else if (a === "back" && picked < 0) {
          game.sounds.back();
          game.screens.go(titleScreen(game, true));
        }
      }
      if (picked >= 0) {
        picked += dt;
        if (picked > 1.1) game.screens.go(modeSelect(game));
      }
      // Reactions: a hop when highlighted, a boost and a grin when picked.
      hop = Math.max(0, hop - dt);
      cheer = Math.max(0, cheer - dt);
      motion.grounded = !(hop > 0 && hop < 0.26);
      motion.speed = cheer > 0 ? 6 : 0;
      motion.boostPhase = cheer > 0 ? 1 : 0;
      motion.boostEnhanced = cheer > 0;
      motion.boostLeft = cheer;
      motion.steer = Math.sin(t * 1.3) * 0.25;
      if (racer) {
        racer.animate(dt, motion, { x: 2, z: 3 });
        racer.flame.visible = cheer > 0;
        racer.core.visible = cheer > 0;
        racer.root.position.y = 0.72 + (hop > 0 ? Math.sin((hop / 0.32) * Math.PI) * 0.55 : 0);
      }
      if (built) built.turntable.rotation.y = Math.sin(spin) * 0.9 + 0.35;
    },
    render3d() {
      if (!built) return false;
      game.stage.renderOther(built.scene, built.camera);
      return true;
    },
    draw(ui) {
      titleSign(ui, "CHOOSE YOUR RACER");
      const d = DESIGNS[id()];
      // Arrows either side of the racer.
      const bob = Math.round(Math.sin(t * 5) * 2);
      const lx = ui.W / 2 - 92 - bob;
      const rx = ui.W / 2 + 84 + bob;
      ui.text("◀", lx, 112, { scale: 2, color: PAL.gold, outline: PAL.shadow });
      ui.text("▶", rx, 112, { scale: 2, color: PAL.gold, outline: PAL.shadow });
      if (game.menuInput.pointer.clicked) {
        if (ui.hover(lx - 6, 100, 22, 34)) clicked = "left";
        else if (ui.hover(rx - 6, 100, 22, 34)) clicked = "right";
        else if (ui.hover(ui.W / 2 - 60, 60, 120, 110)) clicked = "confirm";
      }
      // Name plate.
      const py = 160;
      ui.panel(ui.W / 2 - 112, py, 224, 56, "parchment", "ink");
      ui.text(d.name.toUpperCase(), ui.W / 2, py + 7, {
        scale: 2,
        color: d.kart.body,
        outline: PAL.ink,
        align: "center",
      });
      ui.text(`THE ${d.species.toUpperCase()}`, ui.W / 2, py + 24, {
        color: PAL.inkSoft,
        align: "center",
      });
      wrap(BIOS[id()], 200).forEach((line, i) =>
        ui.text(line, ui.W / 2, py + 35 + i * 9, { color: PAL.ink, align: "center" }),
      );
      // Little tiles: one per racer, in their kart colour.
      RACER_IDS.forEach((r, i) => {
        const tx = ui.W / 2 - 46 + i * 24;
        const ty = 40;
        const sel = i === index;
        ui.panel(tx, ty, 20, 16, DESIGNS[r].kart.body, sel ? "gold" : "dark");
        ui.text(DESIGNS[r].name[0]!, tx + 10, ty + 5, {
          align: "center",
          color: PAL.cream,
          outline: PAL.shadow,
        });
        if (game.menuInput.pointer.clicked && ui.hover(tx, ty, 20, 16) && i !== index) {
          highlight(i - index);
        }
      });
      if (picked >= 0)
        ui.text(`${d.name.toUpperCase()}!`, ui.W / 2, 72, {
          scale: 3,
          color: PAL.gold,
          outline: PAL.shadow,
          align: "center",
        });
      hints(ui, [
        ["◀▶", "CHOOSE"],
        ["ENTER", "PICK"],
        ["ESC", "BACK"],
      ]);
    },
  };
}
