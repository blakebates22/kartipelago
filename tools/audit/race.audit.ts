import { readFile, writeFile } from "node:fs/promises";
import { it } from "vitest";
import { loadTrackPackage, type PackageReader } from "../../src/world/trackPackage";
import { PLAYERS, raceSim } from "../../tests/raceSim";
import rivalSetups from "../../assets/data/rivals.json";
import type { SkillConfig } from "../../src/ai/skill";
// RIVALS: a JSON file of the field (rivals.json's shape) to race instead, for balancing.
const rivalsFile = process.env.RIVALS;

const ids = (process.env.TRACKS ?? "riverbend_palms").split(",");
const seeds = Number(process.env.SEEDS ?? 1);
const who = process.env.PLAYER;
it("races", async () => {
  const rivals = rivalsFile
    ? (JSON.parse(await readFile(rivalsFile, "utf8")) as SkillConfig)
    : (rivalSetups as SkillConfig);
  const dump: unknown[] = [];
  for (const id of ids) {
    const reader: PackageReader = async (file) => {
      const b = await readFile(new URL(`../../public/tracks/${id}/${file}`, import.meta.url));
      return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) as ArrayBuffer;
    };
    const p = await loadTrackPackage(reader, { visual: false });
    const wins: Record<string, number> = {};
    const places: Record<string, number[]> = {};
    for (let s = 1; s <= seeds; s++) {
      const r = raceSim(p, {
        seed: s,
        rivals,
        ai: process.env.AI ? JSON.parse(process.env.AI) : undefined,
        kartClass: process.env.CLASS || undefined,
        shuffleGrid: process.env.SHUFFLE === "1",
        items: process.env.ITEMS !== "0",
        catchUp: process.env.CATCHUP !== "0",
        player: who ? PLAYERS[who] : undefined,
        trace: process.env.TRACE ? Number(process.env.TRACE) : undefined,
        traceEvery: process.env.TRACE_EVERY ? Number(process.env.TRACE_EVERY) : undefined,
        maxSeconds: process.env.MAXS ? Number(process.env.MAXS) : undefined,
      });
      dump.push({ track: id, seed: s, stats: r.stats });
      const order = [...r.stats].sort((a, b) => a.place - b.place);
      wins[order[0]!.name] = (wins[order[0]!.name] ?? 0) + 1;
      for (const k of r.stats) (places[k.name] ??= []).push(k.place);
      if (seeds <= 3 || s === 1)
        console.log(
          id,
          "seed",
          s,
          order
            .map(
              (k) =>
                `${k.place}.${k.name}(${k.tier}) ${k.finished ? k.time.toFixed(1) : "DNF"} best ${Math.min(...k.lapTimes).toFixed(1)} resp ${k.respawns} rec ${k.recoveries} drift ${k.drifting.toFixed(0)}s items ${k.itemsFired} hit ${k.hitsTaken} walls ${k.walls}`,
            )
            .join("\n  "),
        );
    }
    console.log(
      id,
      "wins",
      JSON.stringify(wins),
      "avg place",
      JSON.stringify(
        Object.fromEntries(
          Object.entries(places).map(([k, v]) => [
            k,
            +(v.reduce((a, b) => a + b, 0) / v.length).toFixed(2),
          ]),
        ),
      ),
    );
  }
  if (process.env.OUT) await writeFile(process.env.OUT, JSON.stringify(dump));
}, 3_600_000);
