/**
 * The places audit: races a 1-on-1 (or a bigger field) headless and watches the places
 * the HUD would show, step by step, against who is really ahead by metres along the
 * road. Reports every spell (longer than the HUD's 0.25 s hold) where the places came
 * out the wrong way round with a clear gap between the two karts.
 *
 *   AUDIT_FILE=tools/audit/places.audit.ts TRACKS=valley_region,boss_prehistoric \
 *     [SEEDS=4 COUNT=2 GAP=4] npx vitest run --config tools/audit/vitest.config.ts --silent=false
 */
import { readFile } from "node:fs/promises";
import { it } from "vitest";
import tuning from "../../assets/data/tuning.json";
import { progress, standings } from "../../src/race/race";
import { segmentProgress } from "../../src/race/checkpoints";
import { buildTrack } from "../../src/world/track";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { PLAYERS, raceSim } from "../../tests/raceSim";

const ids = (process.env.TRACKS ?? "valley_region").split(",");
const seeds = Number(process.env.SEEDS ?? 4);
const count = Number(process.env.COUNT ?? 2);
const minGap = Number(process.env.GAP ?? 4);

it("places", async () => {
  for (const id of ids) {
    const reader: PackageReader = async (file) => {
      const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
      return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
    };
    const p = await loadTrackPackage(reader, { visual: false });
    const track = buildTrack(p.trackData, tuning.track.sampleSpacing);
    const sm = track.samples;
    const L = track.length;
    let spells = 0;
    let steps = 0;
    for (let seed = 1; seed <= seeds; seed++) {
      // Each kart's metres along the race (unwrapped), followed sample to sample.
      let along: number[] = [];
      let idx: number[] = [];
      let wrong: { since: number; worst: number; log: string } | undefined;
      raceSim(p, {
        seed,
        count,
        player: PLAYERS[seed % 2 ? "expert" : "competent"],
        items: process.env.ITEMS === "1",
        onStep(race, karts, t) {
          steps++;
          karts.forEach((k, i) => {
            const near = (j: number) => {
              const q = sm[((j % sm.length) + sm.length) % sm.length]!.pos;
              return (q.x - k.x) ** 2 + (q.z - k.z) ** 2 + 4 * (q.y - k.y) ** 2;
            };
            if (idx[i] === undefined) {
              let b = 0;
              for (let j = 1; j < sm.length; j++) if (near(j) < near(b)) b = j;
              idx[i] = b;
              along[i] = sm[b]!.dist - (sm[b]!.dist > L / 2 ? L : 0);
              return;
            }
            let b = idx[i]!;
            for (let j = idx[i]! - 15; j <= idx[i]! + 15; j++) if (near(j) < near(b)) b = j;
            const prev = sm[((idx[i]! % sm.length) + sm.length) % sm.length]!.dist;
            const now = sm[((b % sm.length) + sm.length) % sm.length]!.dist;
            let d = now - prev;
            if (d > L / 2) d -= L;
            if (d < -L / 2) d += L;
            along[i]! += d;
            idx[i] = b;
          });
          if (race.phase === "countdown" || race.racers.some((r) => r.finished)) {
            wrong = undefined;
            return;
          }
          const order = standings(race, karts);
          const truth = karts.map((_, i) => i).sort((a, b) => along[b]! - along[a]!);
          const gap = along[truth[0]!]! - along[truth[1]!]!;
          if (order[0] !== truth[0] && gap > minGap) {
            const desc = karts
              .map((k, i) => {
                const r = race.racers[i]!;
                return `#${i} (${k.x.toFixed(1)},${k.y.toFixed(1)},${k.z.toFixed(1)}) along ${along[i]!.toFixed(1)} value ${progress(race, i, k.x, k.z, k.y).toFixed(3)} passed ${r.passed} best ${r.best} last ${r.lastGate.id} next ${race.course[r.next]!.gates.map((g) => g.id).join("|")} route ${r.activeRoute} seg ${segmentProgress(race.course, r, k).toFixed(3)} v ${k.speed.toFixed(1)} grounded ${k.grounded} ev ${r.lastEvent ? `${r.lastEvent.kind}:${r.lastEvent.gate}${r.lastEvent.why ? ` (${r.lastEvent.why})` : ""}` : "-"}`;
              })
              .join("\n      ");
            if (!wrong) wrong = { since: t, worst: gap, log: `t ${t.toFixed(2)}\n      ${desc}` };
            wrong.worst = Math.max(wrong.worst, gap);
          } else if (wrong) {
            const held = t - wrong.since;
            if (held > 0.25) {
              spells++;
              console.log(
                `  ${id} seed ${seed}: wrong places for ${held.toFixed(2)} s, gap up to ${wrong.worst.toFixed(1)} m\n    at ${wrong.log}`,
              );
            }
            wrong = undefined;
          }
        },
      });
      along = [];
      idx = [];
    }
    console.log(`${id}: ${seeds} races, ${spells} spells of wrong places (${steps} steps)`);
  }
}, 3_600_000);
