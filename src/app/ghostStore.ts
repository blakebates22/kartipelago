/**
 * Saved Time Trial ghosts: one personal best per course (and per layout and physics
 * version, so a ghost set on an older version of a course never races a newer one).
 *
 * Kept in this browser's IndexedDB (ghosts are tens of kilobytes each, too big to pile
 * into localStorage beside the settings and records), gzipped where the browser can.
 * Nothing here can stop the game: blocked or broken storage just means no ghosts, and a
 * bad entry is skipped. A ghost is only ever replaced by a faster valid run.
 */
import { decodeGhost, encodeGhost, ghostKey, type Ghost } from "../game/ghost";

/** Where the bytes live: IndexedDB in the browser, a Map in tests. */
export interface GhostBackend {
  get(key: string): Promise<Uint8Array | undefined>;
  put(key: string, bytes: Uint8Array): Promise<void>;
  remove(key: string): Promise<void>;
}

export function memoryBackend(map = new Map<string, Uint8Array>()): GhostBackend {
  return {
    get: async (k) => map.get(k),
    put: async (k, b) => void map.set(k, b),
    remove: async (k) => void map.delete(k),
  };
}

const DB = "kartipelago";
const STORE = "ghosts";

export function indexedDbBackend(): GhostBackend | undefined {
  if (typeof indexedDB === "undefined") return undefined;
  let opening: Promise<IDBDatabase> | undefined;
  const open = () =>
    (opening ??= new Promise<IDBDatabase>((resolve, reject) => {
      const req = indexedDB.open(DB, 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    }));
  const run = async <T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>) => {
    const db = await open();
    return new Promise<T>((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const req = fn(tx.objectStore(STORE));
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  };
  return {
    get: async (k) => {
      const v = await run("readonly", (s) => s.get(k) as IDBRequest<unknown>);
      return v instanceof Uint8Array ? v : v instanceof ArrayBuffer ? new Uint8Array(v) : undefined;
    },
    put: async (k, b) => void (await run("readwrite", (s) => s.put(b, k))),
    remove: async (k) => void (await run("readwrite", (s) => s.delete(k))),
  };
}

// ---- gzip, where the browser has it (first byte tells: 1 = gzipped, 0 = plain)

async function pipe(bytes: Uint8Array, stream: GenericTransformStream): Promise<Uint8Array> {
  const out = new Blob([bytes as BlobPart])
    .stream()
    .pipeThrough(stream as ReadableWritablePair<Uint8Array, Uint8Array>);
  return new Uint8Array(await new Response(out).arrayBuffer());
}

async function pack(bytes: Uint8Array): Promise<Uint8Array> {
  try {
    if (typeof CompressionStream !== "undefined") {
      const z = await pipe(bytes, new CompressionStream("gzip"));
      const out = new Uint8Array(z.length + 1);
      out[0] = 1;
      out.set(z, 1);
      return out;
    }
  } catch {
    // fall through: stored plain
  }
  const out = new Uint8Array(bytes.length + 1);
  out.set(bytes, 1);
  return out;
}

async function unpack(bytes: Uint8Array): Promise<Uint8Array | undefined> {
  if (bytes[0] === 0) return bytes.subarray(1);
  if (bytes[0] === 1 && typeof DecompressionStream !== "undefined")
    return pipe(bytes.subarray(1), new DecompressionStream("gzip"));
  return undefined;
}

// ---- the store

export interface GhostStore {
  /** The saved ghost for this course, layout and physics, if any. */
  load(track: string, layout: string, physics: string): Promise<Ghost | undefined>;
  /**
   * Keep this run if it's the first, or faster than the saved one. Says whether it was
   * kept. Never replaces a faster ghost with a slower one.
   */
  offer(g: Ghost): Promise<boolean>;
  forget(track: string, layout: string, physics: string): Promise<void>;
}

export function createGhostStore(
  backend: GhostBackend | undefined = indexedDbBackend(),
): GhostStore {
  const b = backend ?? memoryBackend();
  // Saves one at a time, so a quick restart can't interleave two writes to one course.
  let queue: Promise<unknown> = Promise.resolve();
  const load = async (track: string, layout: string, physics: string) => {
    try {
      const raw = await b.get(ghostKey(track, layout, physics));
      if (!raw) return undefined;
      const bytes = await unpack(raw);
      return bytes ? decodeGhost(bytes) : undefined;
    } catch {
      return undefined;
    }
  };
  return {
    load,
    offer(g) {
      const job = queue.then(async () => {
        const m = g.meta;
        if (!(m.total > 0) || !Number.isFinite(m.total) || g.samples.length < 2) return false;
        const old = await load(m.track, m.layout, m.physics);
        if (old && old.meta.total <= m.total) return false;
        try {
          await b.put(ghostKey(m.track, m.layout, m.physics), await pack(encodeGhost(g)));
          return true;
        } catch {
          return false;
        }
      });
      queue = job.catch(() => undefined);
      return job;
    },
    forget: async (track, layout, physics) => {
      try {
        await b.remove(ghostKey(track, layout, physics));
      } catch {
        // nothing to forget
      }
    },
  };
}
