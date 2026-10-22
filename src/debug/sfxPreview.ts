/**
 * Render sound effects offline into a WAV, to listen to them outside the game
 * (developer tool). From the browser console on a ?debug page:
 *
 *   const p = await import("/src/debug/sfxPreview.ts");
 *   const url = await p.previewItemsAndSkid();  // a WAV data URL
 */
import { createSfx } from "../audio/sfx";
import type { AudioEngine } from "../audio/engine";

/** An offline context that reports itself as running, so the effects schedule into it. */
function offline(seconds: number) {
  const real = new OfflineAudioContext(1, Math.ceil(44100 * seconds), 44100);
  const ctx = new Proxy(real, {
    get(t, p) {
      if (p === "state") return "running";
      const v = Reflect.get(t, p, t) as unknown;
      return typeof v === "function" ? (v as (...a: unknown[]) => unknown).bind(t) : v;
    },
  });
  const engine = { context: ctx, bus: () => real.destination } as unknown as AudioEngine;
  return { real, sfx: createSfx(engine) };
}

function wav(buf: AudioBuffer): string {
  const d = buf.getChannelData(0);
  let peak = 0;
  for (const v of d) peak = Math.max(peak, Math.abs(v));
  const k = peak > 0 ? 0.9 / peak : 1;
  const out = new DataView(new ArrayBuffer(44 + d.length * 2));
  const str = (o: number, s: string) =>
    [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  str(0, "RIFF");
  out.setUint32(4, 36 + d.length * 2, true);
  str(8, "WAVEfmt ");
  out.setUint32(16, 16, true);
  out.setUint16(20, 1, true);
  out.setUint16(22, 1, true);
  out.setUint32(24, buf.sampleRate, true);
  out.setUint32(28, buf.sampleRate * 2, true);
  out.setUint16(32, 2, true);
  out.setUint16(34, 16, true);
  str(36, "data");
  out.setUint32(40, d.length * 2, true);
  d.forEach((v, i) => out.setInt16(44 + i * 2, Math.max(-1, Math.min(1, v * k)) * 32767, true));
  let bin = "";
  const bytes = new Uint8Array(out.buffer);
  for (let i = 0; i < bytes.length; i += 0x8000)
    bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return `data:audio/wav;base64,${btoa(bin)}`;
}

/** Item pickups (levels 1-3 and a refill, in each colour), then a drift skid. */
export async function previewItemsAndSkid(): Promise<string> {
  const colors = ["red", "blue", "green", "yellow", "rainbow"] as const;
  const seconds = colors.length * 2.2 + 6;
  const { real, sfx } = offline(seconds);
  const at = async (t: number, fn: () => void) => {
    await real.suspend(t);
    fn();
    void real.resume();
  };
  const jobs: Promise<void>[] = [];
  colors.forEach((c, i) => {
    const t0 = 0.2 + i * 2.2;
    jobs.push(at(t0, () => sfx.balloon(0.5, "new", 1, c)));
    jobs.push(at(t0 + 0.55, () => sfx.balloon(0.5, "upgrade", 2, c)));
    jobs.push(at(t0 + 1.1, () => sfx.balloon(0.5, "upgrade", 3, c)));
    jobs.push(at(t0 + 1.75, () => sfx.balloon(0.5, "refill", 3, c)));
  });
  const t1 = colors.length * 2.2 + 0.3;
  let skid: ReturnType<typeof sfx.skid>;
  jobs.push(at(t1, () => sfx.skidChirp(0.5)));
  jobs.push(at(t1 + 0.02, () => (skid = sfx.skid())));
  for (let k = 0; k < 40; k++) {
    const t = t1 + 0.05 + k * 0.1;
    const ph = k / 40;
    jobs.push(
      at(t, () => skid?.set(ph < 0.8 ? 0.55 + 0.45 * Math.sin(ph * 9) ** 2 : 0, 0.4 + ph * 0.5)),
    );
  }
  jobs.push(at(t1 + 4.4, () => skid?.stop()));
  const rendering = real.startRendering();
  await Promise.all(jobs);
  return wav(await rendering);
}

/** Driving: the engine from idle up to speed, two drifts (with their barks), a boost. */
export async function previewDriving(): Promise<string> {
  const seconds = 9;
  const { real, sfx } = offline(seconds);
  const at = async (t: number, fn: () => void) => {
    await real.suspend(t);
    fn();
    void real.resume();
  };
  const jobs: Promise<void>[] = [];
  let engine: ReturnType<typeof sfx.engine>;
  let skid: ReturnType<typeof sfx.skid>;
  jobs.push(at(0.01, () => ((engine = sfx.engine()), (skid = sfx.skid()))));
  for (let k = 0; k < 85; k++) {
    const t = 0.05 + k * 0.1;
    const speed = Math.min(1, t / 2.5);
    const drifting = (t > 2.8 && t < 4.6) || (t > 5.4 && t < 7.2);
    jobs.push(
      at(t, () => {
        engine?.set(0.45 + speed * 0.55, speed + (t > 7.4 ? 0.15 : 0));
        skid?.set(drifting ? 0.7 + 0.3 * Math.sin(t * 5) ** 2 : 0, 0.6 + 0.3 * Math.sin(t));
      }),
    );
  }
  for (const t of [2.8, 5.4]) jobs.push(at(t, () => sfx.skidChirp(0.3)));
  jobs.push(at(7.4, () => sfx.blueBoost(0.3, 2, 0.3)));
  jobs.push(at(8.7, () => (engine?.stop(), skid?.stop())));
  const rendering = real.startRendering();
  await Promise.all(jobs);
  return wav(await rendering);
}
