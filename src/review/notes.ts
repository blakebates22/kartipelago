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

export type NoteKind = "pin" | "box" | "path" | "measure" | "line" | "general";
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

export async function openStore(track: string, trackName: string): Promise<NoteStore> {
  let notes: ReviewNote[] = [];
  const base = `/__review/${encodeURIComponent(track)}`;
  let repo = false;
  if (import.meta.env.DEV) {
    try {
      const r = await fetch(base);
      if (r.ok) {
        const f = (await r.json()) as Partial<ReviewFile>;
        notes = f.notes ?? [];
        repo = true;
      }
    } catch {
      repo = false;
    }
  }
  if (!repo) {
    try {
      notes = (JSON.parse(localStorage.getItem(LOCAL_KEY(track)) ?? "[]") as ReviewNote[]) ?? [];
    } catch {
      notes = [];
    }
  }
  const keepLocal = () => {
    try {
      localStorage.setItem(LOCAL_KEY(track), JSON.stringify(notes));
    } catch {
      // Full or blocked: the notes stay for this visit; EXPORT still works.
    }
  };
  const upsert = (n: ReviewNote) => {
    const i = notes.findIndex((x) => x.id === n.id);
    if (i >= 0) notes[i] = n;
    else notes.push(n);
  };
  return {
    where: repo ? "repo" : "local",
    async load() {
      return notes;
    },
    async save(note, shot) {
      if (repo) {
        const r = await fetch(`${base}/note`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ trackName, note, shot }),
        });
        if (!r.ok) throw new Error(`saving the note failed (${r.status})`);
        const saved = (await r.json()) as ReviewNote;
        upsert(saved);
        Object.assign(note, saved);
      } else {
        if (shot) note.shot = shot;
        upsert(note);
        keepLocal();
      }
    },
    async remove(id) {
      if (repo) await fetch(`${base}/note/${encodeURIComponent(id)}`, { method: "DELETE" });
      notes = notes.filter((n) => n.id !== id);
      if (!repo) keepLocal();
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
