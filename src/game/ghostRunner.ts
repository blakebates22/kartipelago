/**
 * The Time Trial's ghost, on the session's side: it records your run as you drive and
 * plays back your saved best beside you (src/game/ghost.ts has the recording itself).
 *
 * The ghost you see is your personal best for this course (its layout and physics
 * version), loaded when the session starts. It sits on the line through the countdown,
 * goes at GO and replays its run by the race clock: paused when you pause, from the top
 * when you restart. It's only something drawn: not an entrant, so it never touches you,
 * the rivals, items, checkpoints or anything on the course.
 *
 * Your run is saved only when it's a finished race (every lap validated by the
 * checkpoints) and faster than the saved one. Restart, leave or use a debug tool on the
 * way and nothing is saved. After a new best, your next attempt races that one.
 */
import * as THREE from "three";
import type { GhostStore } from "../app/ghostStore";
import { Racer as RacerView } from "../render/racers/racer";
import type { RacerMotion } from "../render/racers/animator";
import type { RacerId } from "../render/racers/designs";
import {
  GHOST_FORMAT,
  blankSample,
  createRecorder,
  recordSplit,
  recordStep,
  sampleGhost,
  splitDelta,
  type Ghost,
  type GhostChoice,
  type GhostRecorder,
  type GhostSample,
} from "./ghost";

export interface GhostRunnerOptions {
  root: THREE.Object3D;
  store: GhostStore;
  track: string;
  layout: string;
  physics: string;
  racer: RacerId;
  character: string;
  hz: number;
  /** See-through-ness of the ghost (0 invisible .. 1 solid). */
  opacity: number;
  choice: GhostChoice;
  /** The session's exhaust flame and sharp-turn roll, so the ghost looks like a kart. */
  flames: (racer: RacerView, s: GhostSample, frameSeconds: number) => void;
  rollPivot: number;
}

/** How long a checkpoint's "+0.42" / "-1.07" stays up, seconds. */
const DELTA_SHOW = 3;
/** The ghost fades out over this long after its run ends, seconds. */
const FADE = 0.6;

export function createGhostRunner(o: GhostRunnerOptions) {
  let ghost: Ghost | undefined;
  let view: RacerView | undefined;
  let choice = o.choice;
  let rec: GhostRecorder = createRecorder(o.hz);
  let valid = true;
  let lastBest = 0;
  let delta: { value: number; at: number } | undefined;
  let saving: Promise<boolean> | undefined;
  /** A new best just saved: raced from the next attempt. */
  let pendingBest: Ghost | undefined;
  let disposed = false;
  const tilt = new THREE.Quaternion();
  let tiltReady = false;
  const target = new THREE.Quaternion();
  const rollQ = new THREE.Quaternion();
  const shift = new THREE.Vector3();
  const FORWARD = new THREE.Vector3(0, 0, 1);
  const pose = blankSample();
  const mats: THREE.Material[] = [];

  /** A see-through copy of the racer who set it, a little pale and bluish. */
  function makeView(g: Ghost) {
    view?.root.removeFromParent();
    view = new RacerView((g.meta.racer as RacerId) ?? o.racer, { seed: 91 });
    view.root.traverse((ob: THREE.Object3D) => {
      const m = ob as THREE.Mesh;
      if (!m.isMesh || m === view!.flame || m.parent === view!.flame || m === view!.core) return;
      const list = Array.isArray(m.material) ? m.material : [m.material];
      const ghostly = list.map((mat) => {
        const c = mat.clone();
        c.transparent = true;
        c.opacity = o.opacity;
        c.depthWrite = false;
        const col = (c as THREE.MeshLambertMaterial).color;
        if (col) col.lerp(new THREE.Color("#bfe4ff"), 0.35);
        mats.push(c);
        return c;
      });
      m.material = Array.isArray(m.material) ? ghostly : ghostly[0]!;
      m.renderOrder = 2;
    });
    view.shadow.visible = false;
    view.root.visible = false;
    o.root.add(view.root);
    tiltReady = false;
  }

  function use(g: Ghost | undefined) {
    ghost = g;
    if (g) makeView(g);
    else if (view) view.root.visible = false;
  }

  // The saved best, once storage answers (the countdown hides the wait).
  void o.store.load(o.track, o.layout, o.physics).then((g) => {
    if (!disposed && !ghost) use(g);
  });

  return {
    get ghost() {
      return ghost;
    },
    get choice() {
      return choice;
    },
    /** The see-through racer (tests and debugging). */
    get view() {
      return view;
    },
    /** Personal best ghost, or none (the setting; also the pause menu's switch). */
    setChoice(c: GhostChoice) {
      choice = c;
      if (view && c === "off") view.root.visible = false;
    },
    /** A new attempt: start recording afresh; the ghost replays from the top. */
    reset() {
      rec = createRecorder(o.hz);
      valid = true;
      lastBest = 0;
      delta = undefined;
      tiltReady = false;
    },
    /** Something happened that a fair run can't have (a debug tool): don't save it. */
    invalidate() {
      valid = false;
    },
    /**
     * Each physics step, after the karts moved: a snapshot when one's due, and the
     * checkpoint splits (and the gap to the ghost) as they're validated.
     */
    step(clock: number, best: number, finished: boolean, sample: () => GhostSample) {
      if (finished) return;
      recordStep(rec, clock, sample);
      if (best > lastBest) {
        for (let k = lastBest + 1; k <= best; k++) {
          recordSplit(rec, k, clock);
          const d = ghost && choice !== "off" ? splitDelta(ghost, k, clock) : undefined;
          if (d !== undefined) delta = { value: d, at: clock };
        }
        lastBest = best;
      }
    },
    /** Over the line: keep the run if it's a valid new best. */
    finish(
      clock: number,
      total: number,
      lapTimes: number[],
      laps: number,
      sample: () => GhostSample,
    ) {
      if (rec.stopped) return saving;
      // The last snapshot is the moment you crossed the line.
      rec.next = -Infinity;
      recordStep(rec, clock, sample);
      rec.stopped = true;
      if (!valid || lapTimes.length !== laps || !(total > 0)) return undefined;
      const run: Ghost = {
        meta: {
          format: GHOST_FORMAT,
          track: o.track,
          layout: o.layout,
          physics: o.physics,
          racer: o.racer,
          character: o.character,
          hz: o.hz,
          total,
          lapTimes: [...lapTimes],
          splits: [...rec.splits],
          t0: rec.samples[0]?.t ?? 0,
          recordedAt: Date.now(),
        },
        samples: rec.samples,
      };
      saving = o.store.offer(run).then((kept) => {
        // The next attempt races the new best.
        if (kept && !disposed) pendingBest = run;
        return kept;
      });
      return saving;
    },
    /** A restart after a new best switches to it. */
    takeNewBest() {
      if (pendingBest) {
        use(pendingBest);
        pendingBest = undefined;
      }
    },
    /** Draw the ghost at race clock `t` (the render's moment between physics steps). */
    render(t: number, frameSeconds: number) {
      if (!view || !ghost) return;
      if (choice === "off") {
        view.root.visible = false;
        return;
      }
      const going = sampleGhost(ghost, t, pose);
      const end = ghost.samples[ghost.samples.length - 1]!.t;
      const fade = going ? 1 : Math.max(0, 1 - (t - end) / FADE);
      view.root.visible = fade > 0;
      if (!view.root.visible) return;
      for (const m of mats) m.opacity = o.opacity * fade;
      view.root.position.set(pose.x, pose.y, pose.z);
      target.set(pose.qx, pose.qy, pose.qz, pose.qw);
      // The same smoothing the race gives your kart's tilt (snapped on the first frame).
      if (!tiltReady) tilt.copy(target);
      else tilt.slerp(target, 1 - Math.exp(-14 * frameSeconds));
      tiltReady = true;
      view.root.quaternion.copy(tilt);
      if (pose.roll !== 0) {
        rollQ.setFromAxisAngle(FORWARD, pose.roll);
        view.root.quaternion.multiply(rollQ);
        const px = -Math.sign(pose.roll) * o.rollPivot;
        shift
          .set(px * (1 - Math.cos(pose.roll)), -px * Math.sin(pose.roll), 0)
          .applyQuaternion(tilt);
        view.root.position.add(shift);
      }
      const m: RacerMotion = {
        speed: pose.speed,
        steer: pose.steer,
        driftDir: pose.driftDir,
        slip: pose.slip,
        grounded: pose.grounded,
        throttle: pose.throttle,
        boostPhase: pose.zipPhase,
        boostEnhanced: pose.zipEnhanced,
        boostLeft: pose.zipTime,
        impactTier: 0,
        impactSpeed: 0,
        spinTime: pose.spinTime,
      };
      view.animate(frameSeconds, m, null);
      o.flames(view, pose, frameSeconds);
    },
    /** For the HUD: the gap at the last checkpoint (while it's showing), and the best. */
    hud(clock: number) {
      return {
        on: choice !== "off" && Boolean(ghost),
        best: ghost?.meta.total,
        delta: delta && clock - delta.at < DELTA_SHOW ? delta.value : undefined,
      };
    },
    dispose() {
      disposed = true;
      view?.root.removeFromParent();
      for (const m of mats) m.dispose();
    },
  };
}

export type GhostRunner = ReturnType<typeof createGhostRunner>;
