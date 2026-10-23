#!/usr/bin/env node
/**
 * Bake a track's open review edits (nudges) into the track:
 *
 *   node tools/bakeEdits.mjs <trackId> [noteNumber ...]
 *
 * Every open "edit" note in reviews/<trackId>/notes.json (or just the numbers given) is
 * written into public/tracks/<trackId>/edits.json, which the game applies when the track
 * loads (src/world/trackEdits.ts), to the visual and the collision. Each baked note is
 * marked done, with a reply saying so. Run it from the repo root.
 */
import fs from "node:fs";
import path from "node:path";

const [track, ...nums] = process.argv.slice(2);
if (!track || !/^[A-Za-z0-9_-]+$/.test(track)) {
  console.error("usage: node tools/bakeEdits.mjs <trackId> [noteNumber ...]");
  process.exit(1);
}
const notesFile = path.join("reviews", track, "notes.json");
const editsFile = path.join("public", "tracks", track, "edits.json");
const review = JSON.parse(fs.readFileSync(notesFile, "utf8"));
const baked = fs.existsSync(editsFile)
  ? JSON.parse(fs.readFileSync(editsFile, "utf8"))
  : { schemaVersion: 1, edits: [] };
const want = new Set(nums.map(Number));
let count = 0;
for (const n of review.notes) {
  if (n.kind !== "edit" || n.status !== "open" || !n.edit) continue;
  if (want.size && !want.has(n.number)) continue;
  const e = n.edit;
  // One entry per prop: a later edit of the same prop replaces the earlier one.
  baked.edits = baked.edits.filter((x) => x.node !== e.node);
  baked.edits.push({
    op: e.op,
    node: e.node,
    ...(e.copyOf ? { copyOf: e.copyOf } : {}),
    ...(e.op === "delete" ? {} : { to: e.to }),
    note: `#${n.number}${n.text ? `: ${n.text}` : ""}`,
  });
  n.status = "done";
  n.reply = `Baked into the track (edits.json): ${e.op} ${e.node}.`;
  count++;
}
fs.writeFileSync(editsFile, JSON.stringify(baked, null, 2) + "\n");
fs.writeFileSync(notesFile, JSON.stringify(review, null, 2) + "\n");
console.log(`baked ${count} edit(s) into ${editsFile}`);
