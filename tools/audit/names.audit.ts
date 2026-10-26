/** Consistency audit: dumps every name players see (worlds, kingdoms, courses, songs). */
import { test } from "vitest";
import { existsSync } from "node:fs";
import { TRACKS } from "../../src/game/tracks";
import { WORLDS } from "../../src/game/worlds";
import { KINGDOMS, DRAGON } from "../../src/adventure/data";
import { CATALOG, SONGS } from "../../src/audio/songs";

test("names", () => {
  const out: string[] = [];
  const byId = new Map(TRACKS.map((t) => [t.id, t]));
  for (const w of WORLDS.filter((w) => !w.hidden)) {
    out.push(`\n## WORLD ${w.id} "${w.name}" :: ${(w as any).description ?? ""}`);
    for (const id of w.tracks) {
      for (const tid of [id, byId.get(id)?.ruin].filter(Boolean) as string[]) {
        const t = byId.get(tid)!;
        const prev = existsSync(`public/${t.preview}`) ? "" : " [NO PREVIEW]";
        out.push(
          `- ${t.id} "${t.name}" music=${t.music} theme=${t.theme}${prev}${t.prototype ? " PROTO" : ""}\n    ${t.description}`,
        );
      }
    }
  }
  out.push("\n## KINGDOMS");
  for (const k of KINGDOMS)
    out.push(
      `- ${k.id} "${k.name}" world=${k.worldId} boss=${k.boss?.name} champ=${k.champion?.name}`,
    );
  out.push(`- dragon "${DRAGON.name}"`);
  out.push("\n## SONGS");
  for (const c of CATALOG)
    out.push(`- ${c.id} "${c.title}" [${c.role}] ${c.available ? "" : "(planned)"}`);
  const used = new Set(TRACKS.map((t) => t.music));
  out.push(
    `\nmusic ids used by tracks but not in SONGS: ${[...used].filter((m) => !(m in SONGS)).join(", ")}`,
  );
  console.log(out.join("\n"));
});
