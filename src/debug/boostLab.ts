/**
 * Speedrunning calibration tools (debug only):
 *
 * - "Balloon test" panel: pick any balloon and level, equip it instantly (button or
 *   B key), and choose a scripted throttle timing that takes over the throttle from
 *   the moment the balloon fires (or a zipper is hit) for a few seconds.
 * - A speed-versus-time graph of the player's last boost (with the previous one as a
 *   ghost), marking when the push ended and when the rainbow window opened, and the
 *   distance gained over ordinary driving.
 */
import type GUI from "lil-gui";
import { COLORS, type BalloonColor, type Held } from "../items/inventory";
import { ZIP } from "../vehicles/zipper";

export const SCRIPTS = {
  manual: "manual (you drive)",
  hold: "hold throttle",
  released: "released, stay released",
  r02: "resume after 0.2 s",
  r04: "resume after 0.4 s",
  r06: "resume after 0.6 s",
  rainbow: "resume at the rainbow",
} as const;
type Script = keyof typeof SCRIPTS;

const SCRIPT_SEC = 3;
const GRAPH_SEC = 3.5;

interface Run {
  speeds: number[];
  dist: number[];
  pushEnd: number | null;
  rainbowAt: number | null;
  normalTop: number;
  initial: number;
  label: string;
}

export function createBoostLab(gui: GUI, parent: HTMLElement, isOn: () => boolean) {
  const state = {
    color: "blue" as BalloonColor,
    level: 3,
    script: "rainbow" as Script,
    graph: true,
  };
  let equipRequested = false;
  const folder = gui.addFolder("Balloon test");
  folder.add(state, "color", [...COLORS]).name("balloon");
  folder.add(state, "level", [1, 2, 3]).name("level");
  folder
    .add(state, "script", Object.fromEntries(Object.entries(SCRIPTS).map(([k, v]) => [v, k])))
    .name("throttle after firing");
  folder.add(state, "graph").name("speed graph");
  folder.add({ equip: () => (equipRequested = true) }, "equip").name("Equip (or press B)");
  folder.close();

  window.addEventListener("keydown", (e) => {
    if (e.code === "KeyB" && isOn()) equipRequested = true;
  });

  // The graph.
  const canvas = document.createElement("canvas");
  canvas.width = 420;
  canvas.height = 200;
  canvas.className = "speed-graph";
  canvas.hidden = true;
  parent.appendChild(canvas);
  const g = canvas.getContext("2d")!;

  let since = Infinity; // seconds since the scripted run started
  let current: Run | null = null;
  let ghost: Run | null = null;

  function draw() {
    const W = canvas.width;
    const H = canvas.height;
    const L = 34;
    const B = 22;
    const maxV = 60;
    const x = (t: number) => L + (t / GRAPH_SEC) * (W - L - 8);
    const y = (v: number) => H - B - (v / maxV) * (H - B - 8);
    g.clearRect(0, 0, W, H);
    g.fillStyle = "rgba(0,0,0,0.6)";
    g.fillRect(0, 0, W, H);
    g.font = "10px ui-monospace, Menlo, monospace";
    g.fillStyle = "#cccccc";
    g.strokeStyle = "rgba(255,255,255,0.15)";
    for (let v = 0; v <= maxV; v += 10) {
      g.beginPath();
      g.moveTo(L, y(v));
      g.lineTo(W - 8, y(v));
      g.stroke();
      g.fillText(String(v), 6, y(v) + 3);
    }
    for (let t = 0; t <= GRAPH_SEC; t += 0.5) g.fillText(`${t}`, x(t) - 6, H - 8);
    const run = current;
    if (run) {
      if (run.rainbowAt !== null && run.pushEnd !== null) {
        g.fillStyle = "rgba(255,0,255,0.15)";
        g.fillRect(x(run.rainbowAt), 8, x(run.pushEnd) - x(run.rainbowAt), H - B - 8);
      }
      if (run.pushEnd !== null) {
        g.strokeStyle = "#ffffff";
        g.setLineDash([4, 3]);
        g.beginPath();
        g.moveTo(x(run.pushEnd), 8);
        g.lineTo(x(run.pushEnd), H - B);
        g.stroke();
        g.setLineDash([]);
      }
      g.strokeStyle = "#8ecae6";
      g.setLineDash([2, 3]);
      g.beginPath();
      g.moveTo(L, y(run.normalTop));
      g.lineTo(W - 8, y(run.normalTop));
      g.stroke();
      g.setLineDash([]);
    }
    const line = (r: Run, color: string) => {
      g.strokeStyle = color;
      g.lineWidth = 2;
      g.beginPath();
      r.speeds.forEach((v, i) => {
        const t = i / 120;
        if (i === 0) g.moveTo(x(t), y(v));
        else g.lineTo(x(t), y(v));
      });
      g.stroke();
      g.lineWidth = 1;
    };
    if (ghost) line(ghost, "rgba(255,255,255,0.35)");
    if (run) {
      line(run, "#ffd166");
      const peak = Math.max(...run.speeds);
      const tPeak = run.speeds.indexOf(peak) / 120;
      const at = (s: number) => run.dist[Math.min(run.dist.length - 1, Math.round(s * 120))] ?? 0;
      // Ordinary driving: holding the throttle from the same speed, at normal top speed.
      const ordinary = run.normalTop * Math.min(3, (run.dist.length - 1) / 120);
      const gained = at(3) - ordinary;
      g.fillStyle = "#ffffff";
      g.fillText(run.label, L + 4, 18);
      g.fillText(
        `peak ${peak.toFixed(1)} @ ${tPeak.toFixed(2)}s  push ${run.pushEnd?.toFixed(2) ?? "-"}s  ` +
          `d1 ${at(1).toFixed(0)} d2 ${at(2).toFixed(0)} d3 ${at(3).toFixed(0)}m  +${gained.toFixed(0)}m`,
        L + 4,
        31,
      );
    }
  }

  return {
    /** Equip the chosen balloon this step, if asked. */
    equip(held: Held) {
      if (!equipRequested) return false;
      equipRequested = false;
      held.color = state.color;
      held.level = state.level;
      held.ammo = state.color === "red" && state.level === 3 ? 10 : 1;
      return true;
    },

    /** A boost started for the player: begin the script and a new graph run. */
    started(label: string, initial: number, normalTop: number) {
      since = 0;
      ghost = current;
      current = {
        speeds: [initial],
        dist: [0],
        pushEnd: null,
        rainbowAt: null,
        normalTop,
        initial,
        label,
      };
    },

    /**
     * The throttle the script wants right now (undefined = the player's). `phase` is the
     * boost phase, for "resume at the rainbow".
     */
    throttle(phase: number): number | undefined {
      if (state.script === "manual" || since > SCRIPT_SEC) return undefined;
      switch (state.script) {
        case "hold":
          return 1;
        case "released":
          return 0;
        case "r02":
          return since >= 0.2 ? 1 : 0;
        case "r04":
          return since >= 0.4 ? 1 : 0;
        case "r06":
          return since >= 0.6 ? 1 : 0;
        case "rainbow":
          return phase === ZIP.ACTIVE ? 0 : 1;
      }
    },

    /** Whether a script is set (then the throttle at the moment of firing is scripted too). */
    get scripted() {
      return state.script !== "manual";
    },

    /** Record one physics step of the player's run. */
    record(dt: number, speed: number, moved: number, phase: number) {
      since += dt;
      const run = current;
      if (!run || since > GRAPH_SEC) return;
      const t = since;
      run.speeds.push(speed);
      run.dist.push((run.dist.at(-1) ?? 0) + moved);
      if (phase === ZIP.ENDING && run.rainbowAt === null) run.rainbowAt = t;
      if ((phase === ZIP.RECOVERY || phase === ZIP.NORMAL) && run.pushEnd === null) run.pushEnd = t;
    },

    render(visible: boolean) {
      canvas.hidden = !visible || !state.graph || !current;
      if (!canvas.hidden) draw();
    },
  };
}
