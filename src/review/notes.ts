/**
 * Review notes: what Blake marks on a track in the review tool (src/review/), for Claude
 * to read and act on. See docs/review-tool.md.
 *
 * Where they live:
 * - Running the dev server (`npm run dev`), each note goes straight into the repo:
 *   reviews/<trackId>/notes.json, and its screenshot in reviews/<trackId>/shots/<id>.jpg
 *   (the dev-only endpoint in vite.config.ts writes them).
 * - Anywhere else (the GitHub Pages build), they're kept in this browser and the panel's
 *   EXPORT button downloads them as one JSON file (screenshots inside).
 */

export type NoteKind = "pin" | "box" | "path" | "measure" | "line" | "general" | "edit";
export type EditOp = "move" | "copy" | "delete";
/** A transform in the world: position, quaternion (x, y, z, w) and scale. */
export interface Transform {
  pos: Vec3;
  quat: [number, number, number, number];
  scale: Vec3;
}
export type NoteTag = "art" | "layout" | "gameplay" | "bug";
export type Vec3 = [number, number, number];

export interface ReviewNote {
  /** Unique, sortable: "n" + creation time + a random suffix. */
  id: string;
  /** Shown on the pin: 1, 2, 3 ... in creation order. */
  number: number;
  kind: NoteKind;
  text: string;
  tags: NoteTag[];
  important: boolean;
  /** "open" until Claude (or Blake) marks it done. */
  status: "open" | "done";
  /** Claude's answer: what was changed, or a question back. */
  reply?: string;
  created: string;
  /** Where the camera was: position, quaternion (x, y, z, w) and field of view. */
  camera: { pos: Vec3; quat: [number, number, number, number]; fov: number };
  /** Pin: the exact point, the surface normal there and what it is. */
  pin?: {
    point: Vec3;
    normal: Vec3;
    /** The object hit, its name and its parents' names, outermost first. */
    object: string;
    path: string[];
    /** For instanced things (trees, rocks): which instance. */
    instance?: number;
  };
  /** Box: an area, centre and size in metres, turned `yaw` radians about the vertical. */
  box?: { center: Vec3; size: Vec3; yaw: number; objects: string[] };
  /** Path (and recorded driving line): points along the ground. */
  path?: Vec3[];
  /** Measure: two points and the distance between them, metres. */
  measure?: { a: Vec3; b: Vec3; metres: number };
  /**
   * Edit (a nudge): a track prop moved / turned / resized, copied or deleted. `node` is
   * the prop's name in the track file (for a copy: the new copy's name, and `copyOf` the
   * prop it was copied from). `from` and `to` are world transforms (three.js: Y up).
   */
  edit?: { op: EditOp; node: string; copyOf?: string; from: Transform; to: Transform };
  /** The screenshot's file name in reviews/<track>/shots/ (or a data URL when local). */
  shot?: string;
}

export interface ReviewFile {
  track: string;
  trackName: string;
  notes: ReviewNote[];
}

export const newNoteId = () =>
  `n${Date.now().toString(36)}${Math.floor(Math.random() * 1296)
    .toString(36)
    .padStart(2, "0")}`;

const LOCAL_KEY = (track: string) => `kp.review.${track}`;

/** Saving and loading: the repo through the dev server if it's there, else this browser. */
export interface NoteStore {
  /** "repo" (saving into reviews/ through the dev server) or "local" (this browser). */
  readonly where: "repo" | "local";
  load(): Promise<ReviewNote[]>;
  /** Save (create or replace) a note; `shot` is a JPEG data URL to store with it. */
  save(note: ReviewNote, shot?: string): Promise<void>;
  remove(id: string): Promise<void>;
  /** URL for a note's screenshot. */
  shotUrl(note: ReviewNote): string | undefined;
  /** Everything as one file (for EXPORT). */
  exportFile(): ReviewFile;
}

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** The notes kept in this browser for a track (when the repo couldn't be reached). */
function readLocal(track: string): ReviewNote[] {
  try {
    return (JSON.parse(localStorage.getItem(LOCAL_KEY(track)) ?? "[]") as ReviewNote[]) ?? [];
  } catch {
    return [];
  }
}
function writeLocal(track: string, notes: ReviewNote[]) {
  try {
    if (notes.length) localStorage.setItem(LOCAL_KEY(track), JSON.stringify(notes));
    else localStorage.removeItem(LOCAL_KEY(track));
  } catch {
    // Full or blocked: the notes stay for this visit; EXPORT still works.
  }
}

/**
 * Open a track's notes. On the dev server they live in the repo: it's asked a few times
 * (it can be restarting for a moment) before falling back to this browser, and any notes
 * that were kept in the browser earlier are sent to the repo as soon as it answers
 * (`synced` says how many).
 */
export async function openStore(
  track: string,
  trackName: string,
): Promise<NoteStore & { synced: number }> {
  let notes: ReviewNote[] = [];
  const base = `/__review/${encodeURIComponent(track)}`;
  let repo = false;
  if (import.meta.env.DEV) {
    for (let attempt = 0; attempt < 5 && !repo; attempt++) {
      try {
        const r = await fetch(base, { cache: "no-store" });
        const type = r.headers.get("content-type") ?? "";
        if (r.ok && type.includes("json")) {
          const f = (await r.json()) as Partial<ReviewFile>;
          notes = f.notes ?? [];
          repo = true;
        }
      } catch {
        // Not answering yet.
      }
      if (!repo) await wait(500 * (attempt + 1));
    }
  }
  const post = async (note: ReviewNote, shot?: string) => {
    const r = await fetch(`${base}/note`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ trackName, note, shot }),
    });
    if (!r.ok) throw new Error(`the dev server said ${r.status}`);
    return (await r.json()) as ReviewNote;
  };
  const upsert = (n: ReviewNote) => {
    const i = notes.findIndex((x) => x.id === n.id);
    if (i >= 0) notes[i] = n;
    else notes.push(n);
  };
  // Send any notes kept in this browser earlier up to the repo.
  let synced = 0;
  if (repo) {
    const backlog = readLocal(track);
    const left: ReviewNote[] = [];
    for (const n of backlog) {
      // Already in the repo (sent before, or added by Claude): the repo's copy wins.
      if (notes.some((x) => x.id === n.id)) continue;
      try {
        const shot = n.shot?.startsWith("data:") ? n.shot : undefined;
        const { shot: _drop, ...rest } = n;
        void _drop;
        upsert(await post(rest as ReviewNote, shot));
        synced++;
      } catch {
        left.push(n);
      }
    }
    writeLocal(track, left);
  } else notes = readLocal(track);
  return {
    where: repo ? "repo" : "local",
    synced,
    async load() {
      return notes;
    },
    async save(note, shot) {
      if (repo) {
        try {
          const saved = await post(note, shot);
          upsert(saved);
          Object.assign(note, saved);
          return;
        } catch (err) {
          // Keep it in the browser so nothing is lost; it goes up next time.
          if (shot) note.shot = shot;
          writeLocal(track, [...readLocal(track).filter((x) => x.id !== note.id), note]);
          upsert(note);
          throw new Error(
            `${(err as Error).message}: kept in this browser, sent to the repo next time`,
          );
        }
      }
      if (shot) note.shot = shot;
      upsert(note);
      writeLocal(track, notes);
    },
    async remove(id) {
      if (repo) await fetch(`${base}/note/${encodeURIComponent(id)}`, { method: "DELETE" });
      notes = notes.filter((n) => n.id !== id);
      if (!repo) writeLocal(track, notes);
    },
    shotUrl(note) {
      if (!note.shot) return undefined;
      if (note.shot.startsWith("data:")) return note.shot;
      return `${base}/shots/${encodeURIComponent(note.shot)}?t=${Date.now()}`;
    },
    exportFile() {
      return { track, trackName, notes };
    },
  };
}
