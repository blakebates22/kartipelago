import { startTarget, type Race, type RaceConfig } from "../race/race";

/**
 * Start-boost timing bar: a tuning tool, shown only with ?timing in the URL. Shows the
 * countdown as a timeline from "Get ready!" to just after GO, with the good (early) and
 * perfect windows, a moving cursor for now, and a mark where you pressed. Tune the
 * windows live in the tuning panel's `race` folder, then copy the JSON.
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
      const target = startTarget(cfg);
      const pStart = target - cfg.perfectWindowSec;
      const gStart = pStart - cfg.earlyWindowSec;
      good.style.left = pct(gStart);
      good.style.width = pct(t0 + cfg.earlyWindowSec);
      perfect.style.left = pct(pStart);
      perfect.style.width = pct(t0 + cfg.perfectWindowSec * 2);
      go.style.left = pct(0);
      now.style.left = pct(Math.min(race.clock, AFTER));
      const you = race.racers[0]!;
      press.hidden = you.pressAt === undefined;
      if (you.pressAt !== undefined) press.style.left = pct(you.pressAt);

      const ms = (s: number) => `${s >= 0 ? "+" : ""}${Math.round(s * 1000)} ms`;
      if (you.start) {
        const off = you.start.offset;
        text.textContent = `${you.start.tier.toUpperCase()}${off !== undefined ? `  ·  ${ms(off)} from perfect` : ""}`;
      } else {
        text.textContent =
          you.pressAt !== undefined
            ? `pressed ${ms(you.pressAt - target)} from perfect`
            : "press the throttle in the green window";
      }
    },
  };
}
