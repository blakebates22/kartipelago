import * as THREE from "three";
import "./styles.css";
import { tuning } from "./core/tuning";
import { createLoop } from "./core/loop";
import { createInput, NEUTRAL } from "./core/input";
import { createStage } from "./render/stage";
import { createDebug } from "./debug";
import { createStartMeter } from "./debug/startMeter";
import courseData from "../assets/data/course.json";
import driftLoop from "../assets/data/track.json";
import ribbonRidge from "../assets/data/track2.json";
import meadowRun from "../assets/data/track3.json";
import roster from "../assets/data/characters.json";
import { createChaseCamera } from "./render/chaseCamera";
import { createCourseView } from "./render/courseView";
import { createTrackView } from "./render/trackView";
import { createCourse, resetCourse, stepCourse } from "./world/course";
import { buildTrack, type TrackData } from "./world/track";
import { buildZippers, enteredZipper } from "./world/zippers";
import { ZIP, startZipper } from "./vehicles/zipper";
import { bananaMult, bananaScales, effectiveBananas, loseBananas } from "./vehicles/bananas";
import {
  collectBananas,
  createBananaField,
  dropBananas,
  resetBananaField,
  stepBananaField,
  type BananaPickup,
} from "./world/bananas";
import { createBananaView } from "./render/bananaView";
import { createSfx } from "./audio/sfx";
import { createTrackGround, flatGround, type GroundQuery } from "./physics/ground";
import { stepVertical } from "./physics/vertical";
import { stepImpacts, stepSolids, stepWalls } from "./physics/walls";
import { boundarySolids, buildTunnel, placeTrees, tunnelSolids } from "./world/solids";
import { createSceneryView } from "./render/sceneryView";
import { bumpKarts } from "./physics/bump";
import { buildRacingLine } from "./ai/racingLine";
import { createDriver, driveAi, type Driver } from "./ai/driver";
import {
  canDrive,
  createRace,
  formatTime,
  lapClock,
  standings,
  startTarget,
  stepRacer,
  tickRace,
} from "./race/race";
import { gridSlot } from "./race/grid";
import { applyCharacter, type Character } from "./vehicles/character";
import {
  applyBoost,
  createKartState,
  slipAngle,
  stepKart,
  wrapAngle,
  type KartState,
} from "./vehicles/kart";

// Two scenes: a race on a track with seven AI rivals (default; pick the track with
// ?track=1 or ?track=2) and the M1 practice course of pickups and boost pads (open with
// ?scene=practice). Press R to restart.

const PARAMS = new URLSearchParams(location.search);
const SCENE = PARAMS.get("scene") === "practice" ? "practice" : "track";
// The start-boost timing bar is a tuning tool: only shown with ?timing in the URL.
const SHOW_TIMING = PARAMS.has("timing");
// Tracks: ?track=1 (Drift Loop, the default), ?track=2 (Ribbon Ridge) or ?track=3
// (Meadow Run, an open track).
const TRACKS = [driftLoop, ribbonRidge, meadowRun] as TrackData[];
const trackData = TRACKS[Number(PARAMS.get("track") ?? 1) - 1] ?? TRACKS[0]!;
const GROUND_SIZE = 1200;
const GROUND_TILE = 5; // metres per grid square

const app = document.getElementById("app")!;
const stage = createStage(app);
const debug = createDebug(document.body);
const input = createInput();
const chase = createChaseCamera(stage.camera);

// Tiled lines on the ground give the eye something to judge speed and turning against.
function groundTexture() {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const g = canvas.getContext("2d")!;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, size, size);
  g.fillStyle = "#c4c4c4"; // multiplies groundColor, so lines are a darker shade of it
  g.fillRect(0, 0, size, 3);
  g.fillRect(0, 0, 3, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(GROUND_SIZE / GROUND_TILE, GROUND_SIZE / GROUND_TILE);
  tex.anisotropy = 8;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const groundMat = new THREE.MeshStandardMaterial({
  color: tuning.world.groundColor,
  map: groundTexture(),
});
const ground = new THREE.Mesh(new THREE.PlaneGeometry(GROUND_SIZE, GROUND_SIZE), groundMat);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
stage.scene.add(ground);

const course = SCENE === "practice" ? createCourse(courseData) : undefined;
const courseView = course ? createCourseView(stage.scene, course, tuning.course) : undefined;
const track = SCENE === "track" ? buildTrack(trackData, tuning.track.sampleSpacing) : undefined;
const zippers = track ? buildZippers(track, trackData.zippers ?? [], tuning.track) : [];
const trackView = track ? createTrackView(stage.scene, track, tuning.track, zippers) : undefined;
// Open tracks: no road walls; tunnels, the map boundary and trees are what you can hit.
const OPEN = Boolean(track && trackData.open);
const tunnels = track && OPEN ? (trackData.tunnels ?? []).map((t) => buildTunnel(track, t)) : [];
const solids = (() => {
  if (!track || !OPEN) return [];
  const fixed = [
    ...tunnels.flatMap(tunnelSolids),
    ...boundarySolids(track, tuning.scenery.boundaryMargin),
  ];
  return [...fixed, ...placeTrees(track, tuning.scenery, fixed)];
})();
const sceneryView = OPEN
  ? createSceneryView(stage.scene, solids, tunnels, tuning.scenery)
  : undefined;
const bananaField = createBananaField(
  track,
  trackData.bananas ?? [],
  () => (track ? createTrackGround(track) : flatGround),
  !OPEN,
);
const bananaView = createBananaView(stage.scene, tuning.bananas);
const sfx = createSfx();
/** Collected this step, for the render to show (effects run at frame rate). */
const pickupsToShow: BananaPickup[] = [];
const line = track
  ? buildRacingLine(track, {
      margin: trackData.aiLineMargin ?? tuning.ai.lineMargin,
      span: tuning.ai.lineSpan,
      iterations: tuning.ai.lineIterations,
    })
  : undefined;

const characters = roster.characters as Character[];
const findCharacter = (id: string) => characters.find((c) => c.id === id) ?? characters[0]!;

/** A box kart with a darker nose, so you can tell which way is forward. */
function makeKartMesh() {
  const mat = new THREE.MeshStandardMaterial({ flatShading: true });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.8, 2.4), mat);
  mesh.castShadow = true;
  const nose = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, 0.3, 0.4),
    new THREE.MeshStandardMaterial({ color: "#333333", flatShading: true }),
  );
  nose.position.set(0, 0.2, 1.2);
  mesh.add(nose);
  // Exhaust flame at the back: shows zipper boosts, and turns rainbow at the moment to
  // press the throttle again after an enhanced boost.
  const flameMat = new THREE.MeshBasicMaterial({ color: "#ff8c1a", transparent: true });
  const flame = new THREE.Mesh(
    new THREE.ConeGeometry(0.35, 1.4, 10).rotateX(-Math.PI / 2),
    flameMat,
  );
  flame.position.set(0, 0, -1.9);
  flame.visible = false;
  mesh.add(flame);
  stage.scene.add(mesh);
  return { mesh, mat, flame, flameMat };
}

interface Entrant {
  name: string;
  character: Character;
  color: string;
  state: KartState;
  /** State at the previous step, for smooth rendering between steps. */
  prev: { x: number; y: number; z: number; heading: number; velAngle: number };
  mesh: THREE.Mesh;
  mat: THREE.MeshStandardMaterial;
  flame: THREE.Mesh;
  flameMat: THREE.MeshBasicMaterial;
  /** Each kart keeps its own ground lookup (it remembers where on the track it was). */
  ground: GroundQuery;
  driver?: Driver;
}

const player = findCharacter(roster.default);
const rivals = track ? roster.rivals : [];
const entrants: Entrant[] = [
  { name: "You", character: player, color: player.color },
  ...rivals.map((r) => ({ name: r.name, character: findCharacter(r.character), color: r.color })),
].map((e, i) => {
  const { mesh, mat, flame, flameMat } = makeKartMesh();
  const state = createKartState();
  return {
    ...e,
    state,
    prev: { x: 0, y: 0, z: 0, heading: 0, velAngle: 0 },
    mesh,
    mat,
    flame,
    flameMat,
    ground: track ? createTrackGround(track) : flatGround,
    driver: i > 0 && line ? createDriver(line, i, tuning.ai) : undefined,
  };
});
const you = entrants[0]!;

/** Put every kart in its starting spot. The player starts at the front of the grid. */
function placeKarts() {
  entrants.forEach((e, i) => {
    let spot = { x: courseData.start.x, y: 0, z: courseData.start.z, heading: 0 };
    if (track) spot = gridSlot(track, i);
    Object.assign(e.state, createKartState(spot.x, spot.z, spot.heading, spot.y));
    e.state.y = e.ground.at(spot.x, spot.z).height;
    snapPrev(e);
    if (e.driver) e.driver.driftHeld = false;
  });
}
function snapPrev(e: Entrant) {
  const s = e.state;
  Object.assign(e.prev, { x: s.x, y: s.y, z: s.z, heading: s.heading, velAngle: s.velAngle });
}

const newRace = () => (track ? createRace(track, tuning.race, entrants.length) : undefined);
let race = newRace();
placeKarts();

// Always-on readout, plus big centred text for the start and the finish.
const hud = document.createElement("div");
hud.className = "hud";
document.body.appendChild(hud);
const startMeter = createStartMeter(document.body);
const banner = document.createElement("div");
banner.className = "banner";
document.body.appendChild(banner);
// Short message when your banana speed bonus is full.
const toast = document.createElement("div");
toast.className = "toast";
toast.hidden = true;
document.body.appendChild(toast);
let toastUntil = 0;
function showToast(text: string, seconds: number) {
  toast.textContent = text;
  toast.hidden = false;
  toastUntil = performance.now() + seconds * 1000;
}

// Best lap ever on this track, kept in this browser only. Storage can be unavailable
// (private windows, blocked site data), so every access is guarded.
const bestKey = `kartipelago.bestLap.${trackData.name}`;
function loadBest(): number | undefined {
  try {
    const v = Number(localStorage.getItem(bestKey));
    return v > 0 ? v : undefined;
  } catch {
    return undefined;
  }
}
let bestEver = loadBest();
function saveBest(time: number) {
  if (bestEver !== undefined && bestEver <= time) return;
  bestEver = time;
  try {
    localStorage.setItem(bestKey, String(time));
  } catch {
    // Not saved; it still shows for this session.
  }
}

let pathCurvature = 0;
let youAccel = 0;

// Key events only request changes; they're applied on the fixed step, like all gameplay.
let resetRequested = false;
// Number keys pick your character (1 = first in characters.json, and so on).
let pickRequested: Character | undefined;
// Debug only (overlay showing): L loses two bananas as a hit would, K adds one.
let bananaLossRequested = false;
let bananaAddRequested = 0;
window.addEventListener("keydown", (e) => {
  if (e.code === "KeyR") resetRequested = true;
  if (debug.overlay.visible && e.code === "KeyL") bananaLossRequested = true;
  if (debug.overlay.visible && e.code === "KeyK") bananaAddRequested++;
  // M flips between the legacy and offset drift models, for side-by-side comparison.
  if (e.code === "KeyM") tuning.vehicle.driftModel = tuning.vehicle.driftModel >= 1 ? 0 : 1;
  const n = /^Digit([1-9])$/.exec(e.code);
  if (n) pickRequested = characters[Number(n[1]) - 1];
});

const loop = createLoop(tuning.loop.physicsHz, tuning.loop.maxStepsPerFrame, {
  update(dt) {
    if (resetRequested) {
      resetRequested = false;
      race = newRace();
      placeKarts();
      resetBananaField(bananaField);
      if (course) resetCourse(course);
    }
    if (bananaAddRequested) {
      gotBananas(0, bananaAddRequested);
      bananaAddRequested = 0;
    }
    if (bananaLossRequested) {
      bananaLossRequested = false;
      const lost = loseBananas(you.state, "debug", tuning.bananas);
      dropBananas(bananaField, you.state, lost, tuning.bananas);
      if (lost) sfx.bananaLost(tuning.bananas.volume);
    }
    if (pickRequested) {
      you.character = pickRequested;
      you.color = pickRequested.color;
      pickRequested = undefined;
    }
    for (const e of entrants) snapPrev(e);
    const pathBefore = you.state.velAngle;
    const speedBefore = you.state.speed;
    const posBefore = { x: you.state.x, z: you.state.z };
    if (race) tickRace(race, dt);

    // Keyboard steering responds differently while you're drifting (finer taps).
    const held = input.sample(dt, you.state.driftDir !== 0);
    const moment = race && {
      countdown: race.phase === "countdown",
      clock: race.clock,
      startTarget: startTarget(tuning.race),
    };
    const walls = { ...tuning.physics, ...tuning.collision, wallHeight: tuning.track.wallHeight };

    entrants.forEach((e, i) => {
      // Rebuilt each step so live tuning edits apply immediately.
      let cfg = applyCharacter(tuning.vehicle, e.character, tuning.stats);
      if (e.driver) cfg = { ...cfg, topSpeed: cfg.topSpeed * tuning.ai.speedMult };
      const want = e.driver && moment ? driveAi(e.driver, e.state, cfg, tuning.ai, moment) : held;
      // During the countdown every kart sits on the line.
      stepImpacts(e.state, tuning.collision, dt);
      stepKart(e.state, !race || canDrive(race) ? want : NEUTRAL, cfg, dt);
      if (enteredZipper(e.state, zippers)) startZipper(e.state, want.throttle, cfg);
      if (!OPEN) stepWalls(e.state, e.ground, walls, dt);
      stepSolids(e.state, solids, walls, dt);
      stepVertical(e.state, e.ground, tuning.physics, dt);
      const before = e.state.bananas;
      const got = collectBananas(bananaField, i, e.state, tuning.bananas);
      if (got.length) {
        pickupsToShow.push(...got);
        e.state.bananas = before;
        gotBananas(i, got.length);
      }
      if (course && i === 0) stepCourse(course, e.state, tuning.course, cfg, dt);
      if (!race) return;

      const laps = race.racers[i]!.lapTimes.length;
      const onRoad = e.ground.at(e.state.x, e.state.z).onRoad;
      const events = stepRacer(race, i, e.state, onRoad, want.throttle, tuning.race, dt);
      if (i === 0 && race.racers[0]!.lapTimes.length > laps)
        saveBest(race.racers[0]!.lapTimes.at(-1)!);
      if (events.boost) applyBoost(e.state, cfg, events.boost.mult, events.boost.seconds);
      if (events.respawn) {
        const g = events.respawn;
        const bananas = e.state.bananas; // a respawn keeps what you've collected
        Object.assign(e.state, createKartState(g.x, g.z, g.heading, g.y));
        e.state.bananas = bananas;
        snapPrev(e);
      }
    });
    bumpKarts(
      entrants.map((e) => e.state),
      tuning.physics.kartBump,
    );
    stepBananaField(bananaField, tuning.bananas, dt);
    // Telemetry: how sharply the player's path is curving (1/m), for the debug overlay.
    const moved = Math.hypot(you.state.x - posBefore.x, you.state.z - posBefore.z);
    if (moved > 1e-3) pathCurvature = wrapAngle(you.state.velAngle - pathBefore) / moved;
    youAccel = (you.state.speed - speedBefore) / dt;
  },

  render(alpha, frameSeconds) {
    const { camera, world, vehicle } = tuning;
    for (const e of entrants) renderKart(e, alpha, frameSeconds);
    groundMat.color.set(trackData.groundColor ?? world.groundColor);
    sceneryView?.render(tuning.scenery);
    stage.scene.background = new THREE.Color(world.skyColor);

    const s = you.state;
    const p = you.prev;
    const x = p.x + (s.x - p.x) * alpha;
    const y = p.y + (s.y - p.y) * alpha;
    const z = p.z + (s.z - p.z) * alpha;
    const heading = p.heading + wrapAngle(s.heading - p.heading) * alpha;
    const velAngle = p.velAngle + wrapAngle(s.velAngle - p.velAngle) * alpha;
    stage.followSun(x, z);
    stage.camera.fov = camera.fov;
    stage.camera.updateProjectionMatrix();
    chase.update(
      { x, y, z, heading, velAngle, speedFrac: s.speed / vehicle.topSpeed },
      camera,
      frameSeconds,
    );

    courseView?.render(performance.now() / 1000, tuning.course);
    trackView?.render(tuning.track);
    for (const p of pickupsToShow.splice(0)) bananaView.burst(p);
    bananaView.render(bananaField, tuning.bananas, performance.now() / 1000, frameSeconds);
    if (!toast.hidden && performance.now() > toastUntil) toast.hidden = true;
    renderHud();
    startMeter.render(race, tuning.race, SHOW_TIMING);

    debug.overlay.set("speed", `${s.speed.toFixed(1)} m/s`);
    debug.overlay.set("slip", `${((slipAngle(s) * 180) / Math.PI).toFixed(1)}°`);
    debug.overlay.set("thr", input.state.throttle);
    debug.overlay.set("brk", input.state.brake);
    debug.overlay.set("steer", input.state.steer);
    debug.overlay.set("air", s.grounded ? "-" : `${s.y.toFixed(1)} m`);
    debug.overlay.set("tap", `${Math.round(s.tapCharge * 100)}%`);
    const phases = ["normal", "ACTIVE", "ENDING (rainbow)", "recovery"];
    const youCfg = applyCharacter(tuning.vehicle, you.character, tuning.stats);
    debug.overlay.set("max", `${youCfg.topSpeed.toFixed(1)} m/s`);
    debug.overlay.set(
      "zip",
      s.zipPhase ? `${phases[s.zipPhase]} ${s.zipEnhanced ? "enhanced" : "ordinary"}` : "-",
    );
    debug.overlay.set(
      "zipT",
      s.zipPhase === ZIP.ACTIVE || s.zipPhase === ZIP.ENDING
        ? `${s.zipTime.toFixed(2)}s left`
        : "-",
    );
    debug.overlay.set(
      "zipPw",
      `${Math.round(s.zipPower * 100)}%  released ${s.zipReleasedAtStart ? "yes" : "no"}  early ${s.zipPressedEarly ? "yes" : "no"}`,
    );
    debug.overlay.set("accel", `${youAccel.toFixed(1)} m/s²`);
    const bs = bananaScales(s.bananas, tuning.vehicle);
    debug.overlay.set(
      "banana",
      `${s.bananas} held, ${effectiveBananas(s.bananas, tuning.vehicle)} effective, ×${bananaMult(s.bananas, tuning.vehicle).toFixed(3)}  (L lose 2, K add 1)`,
    );
    debug.overlay.set(
      "banTop",
      `${(youCfg.topSpeed * bs.top).toFixed(1)} m/s top, accel ×${bs.accel.toFixed(3)}`,
    );
    debug.overlay.set(
      "boost",
      s.zipPhase
        ? `zipper ${phases[s.zipPhase]}`
        : s.boostTime > 0
          ? `boost ×${s.boostMult.toFixed(2)} ${s.boostTime.toFixed(1)}s`
          : "-",
    );
    debug.overlay.set(
      "lat",
      `${(Math.abs(s.speed) * Math.sin(Math.abs(slipAngle(s)))).toFixed(1)} m/s`,
    );
    const model = tuning.vehicle.driftModel >= 1 ? "offset" : "legacy";
    debug.overlay.set("model", `${model} (M)`);
    debug.overlay.set("stick", s.steerSmooth.toFixed(2));
    const pathRate = Math.abs(s.speed) * Math.abs(pathCurvature);
    debug.overlay.set(
      "arc",
      pathRate > 0.02 ? `${(Math.abs(s.speed) / pathRate).toFixed(0)} m` : "-",
    );
    debug.overlay.set("offs", `${((s.driftOffset * 180) / Math.PI).toFixed(0)}°`);
    debug.overlay.set("spin", s.spinTime > 0 ? "SPIN" : `${s.counterTime.toFixed(2)}s`);
    const tiers = ["-", "light", "moderate", "CRASH"];
    debug.overlay.set(
      "hit",
      s.lastImpactTier ? `${tiers[s.lastImpactTier]} ${s.lastImpactSpeed.toFixed(1)} m/s` : "-",
    );
    debug.overlay.set(
      "drift",
      s.driftDir === 0 ? "-" : `${s.driftDir > 0 ? "R" : "L"} ${s.driftTime.toFixed(1)}s`,
    );
    debug.overlay.frame(frameSeconds);
    stage.render();
  },
});

// Visual tilt: sit flat on the surface when grounded; in the air, pitch with the arc of
// the jump. Smoothed, so bumps and landings don't snap the mesh.
const tilt = { up: new THREE.Vector3(), fwd: new THREE.Vector3(), right: new THREE.Vector3() };
const tiltBasis = new THREE.Matrix4();
const tiltTarget = new THREE.Quaternion();
function renderKart(e: Entrant, alpha: number, frameSeconds: number) {
  const { state: s, prev: p, mesh } = e;
  const heading = p.heading + wrapAngle(s.heading - p.heading) * alpha;
  mesh.position.set(
    p.x + (s.x - p.x) * alpha,
    p.y + (s.y - p.y) * alpha + 0.4,
    p.z + (s.z - p.z) * alpha,
  );
  const { up, fwd, right } = tilt;
  fwd.set(Math.sin(heading), 0, Math.cos(heading));
  if (s.grounded) up.set(s.nx, s.ny, s.nz);
  else
    up.set(0, 1, 0)
      .addScaledVector(fwd, -s.vy / Math.max(8, Math.abs(s.speed)))
      .normalize();
  right.crossVectors(up, fwd).normalize();
  fwd.crossVectors(right, up).normalize();
  tiltBasis.makeBasis(right, up, fwd);
  tiltTarget.setFromRotationMatrix(tiltBasis);
  mesh.quaternion.slerp(tiltTarget, 1 - Math.exp(-14 * frameSeconds));
  e.mat.color.set(e.color);

  const z = s.zipPhase;
  e.flame.visible = z !== ZIP.NORMAL;
  if (z === ZIP.ENDING) {
    // Rainbow: the cue to press the throttle again.
    e.flameMat.color.setHSL((performance.now() / 250) % 1, 1, 0.6);
    e.flame.scale.setScalar(1.5);
  } else if (z === ZIP.ACTIVE) {
    e.flameMat.color.set(s.zipEnhanced ? "#ffd166" : "#ff8c1a");
    e.flame.scale.setScalar(s.zipEnhanced ? 1.3 : 1);
  } else if (z === ZIP.RECOVERY) {
    e.flameMat.color.set("#ff8c1a");
    e.flame.scale.setScalar(0.6);
  }
  e.flameMat.opacity = z === ZIP.RECOVERY ? 0.5 : 0.9;
}

/** Count collected bananas; the player hears each one, and a fanfare at the cap. */
function gotBananas(i: number, n: number) {
  const s = entrants[i]!.state;
  const full = tuning.vehicle.bananaMaxEffective;
  const before = s.bananas;
  s.bananas += n;
  if (i !== 0) return;
  sfx.banana(tuning.bananas.volume);
  if (before < full && s.bananas >= full) {
    sfx.bananaMilestone(tuning.bananas.volume);
    showToast(`${full} bananas! Full speed bonus`, 1.6);
  }
}

const ordinal = (n: number) =>
  `${n}${["th", "st", "nd", "rd"][n % 10 < 4 && Math.floor(n / 10) !== 1 ? n % 10 : 0]}`;

function renderHud() {
  const s = you.state;
  const parts = [you.character.name, `${s.speed.toFixed(0)} m/s`, `Bananas ${s.bananas}`];
  if (course) parts.push(`Pickups ${course.collected}`);
  let order: number[] = [];
  if (race) {
    const r = race.racers[0]!;
    order = standings(
      race,
      entrants.map((e) => e.state),
    );
    parts.unshift(`${ordinal(order.indexOf(0) + 1)} / ${entrants.length}`);
    parts.push(`Lap ${Math.min(r.lap, tuning.race.laps)}/${tuning.race.laps}`);
    parts.push(formatTime(lapClock(race, 0)));
    if (r.bestLap !== undefined) parts.push(`Best ${formatTime(r.bestLap)}`);
    parts.unshift(trackData.name);
    if (bestEver !== undefined) parts.push(`Record ${formatTime(bestEver)}`);
  }
  parts.push(`1–${characters.length} character`, "R restart");
  hud.textContent = parts.join("  ·  ");

  let message = "";
  const r = race?.racers[0];
  if (race?.phase === "countdown") message = "Get ready!";
  else if (race && r?.finished) {
    // Finished racers keep their order; anyone still racing is listed by position.
    const rows = order.map((i, place) => {
      const racer = race!.racers[i]!;
      const time = racer.finished ? formatTime(racer.totalTime ?? 0) : "racing";
      return `${ordinal(place + 1).padEnd(4)} ${entrants[i]!.name.padEnd(8)} ${time}`;
    });
    message = `Finished ${ordinal(order.indexOf(0) + 1)}!\n${rows.join("\n")}\nR to race again`;
  } else if (race && race.clock < tuning.race.goShowSec) {
    const tier = r?.start?.tier;
    message =
      tier === "perfect" ? "GO!\nPerfect start!" : tier === "good" ? "GO!\nGood start" : "GO!";
  }
  banner.textContent = message;
  banner.hidden = message === "";
  banner.classList.toggle("standings", Boolean(r?.finished));
}

loop.start();
