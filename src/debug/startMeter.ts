import { framesBeforeGo, type Race, type RaceConfig } from "../race/race";

/**
 * Start-boost timing bar: a tuning tool, shown only with ?timing in the URL. Shows the
 * countdown as a timeline from "GET READY..." to just after GO, with the weak and strong
 * windows (counted in reference frames before GO, race.ts), a moving cursor for now,
 * and a mark where you first pressed.
 */
export function createStartMeter(parent: HTMLElement) {
  const el = document.createElement("div");
  el.className = "start-meter";
  el.innerHTML = `
    <div class="sm-bar">
      <div class="sm-zone sm-good"></div>
      <div class="sm-zone sm-perfect"></div>
      <div class="sm-tick sm-go"></div>
      <div class="sm-tick sm-press"></div>
      <div class="sm-tick sm-now"></div>
    </div>
    <div class="sm-text"></div>`;
  el.hidden = true;
  parent.appendChild(el);
  const q = (c: string) => el.querySelector<HTMLElement>(c)!;
  const good = q(".sm-good");
  const perfect = q(".sm-perfect");
  const go = q(".sm-go");
  const press = q(".sm-press");
  const now = q(".sm-now");
  const text = q(".sm-text");

  /** Timeline runs from "Get ready!" to a little after GO. */
  const AFTER = 0.4;

  return {
    render(race: Race | undefined, cfg: RaceConfig, visible: boolean) {
      const show = visible && race !== undefined && race.clock < 3;
      el.hidden = !show;
      if (!show || !race) return;
      const t0 = -cfg.readySec;
      const span = cfg.readySec + AFTER;
      const pct = (t: number) => `${(((t - t0) / span) * 100).toFixed(2)}%`;
      const hz = cfg.startRefHz;
      const strong0 = -cfg.startStrongFrames / hz;
      const weak0 = -cfg.startWeakFrames / hz;
      good.style.left = pct(weak0);
      good.style.width = `${(((strong0 - weak0) / span) * 100).toFixed(2)}%`;
      perfect.style.left = pct(strong0);
      perfect.style.width = `${((-strong0 / span) * 100).toFixed(2)}%`;
      go.style.left = pct(0);
      now.style.left = pct(Math.min(race.clock, AFTER));
      const you = race.racers[0]!;
      press.hidden = you.pressAt === undefined;
      if (you.pressAt !== undefined) press.style.left = pct(you.pressAt);
      const frames = (n: number) => `${n} frame${n === 1 ? "" : "s"} before GO`;
      if (you.start) {
        const f = you.start.frames;
        text.textContent = `${you.start.tier.toUpperCase()}${f !== undefined ? `  ·  ${frames(f)}` : ""}`;
      } else {
        text.textContent =
          you.pressAt !== undefined
            ? `pressed ${frames(framesBeforeGo(you.pressAt, cfg))}${you.releasedEarly ? " (let go)" : ""}`
            : `press 1-${cfg.startStrongFrames} frames before GO and hold`;
      }
    },
  };
}
