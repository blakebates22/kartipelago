/**
 * Time Trial ghosts: a recorded run, replayed as a see-through racer.
 *
 * A ghost is a recording of what was drawn, not of the buttons pressed: timestamped
 * snapshots of the kart's pose (where it was, which way its body faced, its sharp-turn
 * roll) and its animation state (speed, steering, drifting, airborne, boosts), taken on
 * the fixed physics step at about 30 a second. Playback interpolates between snapshots
 * by the race clock, so it stays in step whatever the frame rate, stops while the game is
 * paused and starts again on a restart. It never resimulates anything, so it can't drift
 * off its line, and it's never a racer: it has no collisions, no items, no checkpoints.
 *
 * Positions use a (uniform) Catmull-Rom curve through the snapshots (the
 * curve passes through every one, so there's no drift); rotations slerp the shortest way.
 * A respawn (a jump between snapshots no kart could make) is shown as the cut it was.
 *
 * Stored compactly: positions to the millimetre, rotations and the rest quantised, about
 * 35 bytes a snapshot (a 2-minute run is about 120 KB, less once compressed).
 */
import * as THREE from "three";

/** Bump when the stored layout changes: older ghosts are then ignored, not misread. */
export const GHOST_FORMAT = 1;

/** One snapshot, as plain numbers (see FIELDS for the order). */
export interface GhostSample {
  t: number;
  x: number;
  y: number;
  z: number;
  /** The body's tilt (before the sharp turn's roll): a quaternion. */
  qx: number;
  qy: number;
  qz: number;
  qw: number;
  /** The sharp turn's roll, radians. */
  roll: number;
  speed: number;
  steer: number;
  driftDir: number;
  /** Nose minus travel direction, radians. */
  slip: number;
  grounded: boolean;
  throttle: boolean;
  zipPhase: number;
  zipEnhanced: boolean;
  zipTime: number;
  zipSource: number;
  spinTime: number;
}

export interface GhostMeta {
  format: number;
  /** Course id, and fingerprints of its layout and of the driving physics it was set on. */
  track: string;
  layout: string;
  physics: string;
  /** Who drove it: the racer's look and their kart class. */
  racer: string;
  character: string;
  /** Snapshots a second. */
  hz: number;
  /** The run: total time, each lap, and the race clock at each checkpoint passed. */
  total: number;
  lapTimes: number[];
  splits: number[];
  /** Race clock of the first snapshot (negative: during the countdown). */
  t0: number;
  /** When it was set (ms since 1970), for a later "set on..." line. */
  recordedAt: number;
}

export interface Ghost {
  meta: GhostMeta;
  samples: GhostSample[];
}

// ---------------------------------------------------------------- recording

export interface GhostRecorder {
  hz: number;
  samples: GhostSample[];
  splits: number[];
  /** Race clock of the next snapshot due. */
  next: number;
  stopped: boolean;
}

export function createRecorder(hz: number): GhostRecorder {
  return { hz, samples: [], splits: [], next: -Infinity, stopped: false };
}

/**
 * Called every physics step with the race clock and the kart's pose: takes a snapshot
 * when one is due. The first snapshot is taken at once; then one every 1/hz seconds of
 * race clock (on the nearest step, keeping the true clock as its timestamp).
 */
export function recordStep(rec: GhostRecorder, clock: number, sample: () => GhostSample) {
  if (rec.stopped || clock < rec.next) return;
  const s = sample();
  s.t = clock;
  rec.samples.push(s);
  rec.next = (rec.samples.length === 1 ? clock : rec.next) + 1 / rec.hz;
}

/** A checkpoint validated for the first time this run, at this race clock. */
export function recordSplit(rec: GhostRecorder, checkpoint: number, clock: number) {
  if (rec.stopped) return;
  while (rec.splits.length < checkpoint) rec.splits.push(clock);
}

// ---------------------------------------------------------------- the body's tilt

const _up = new THREE.Vector3();
const _fwd = new THREE.Vector3();
const _right = new THREE.Vector3();
const _m = new THREE.Matrix4();

/**
 * The kart's tilt as the race draws it (session.renderKart): sat on the surface normal
 * when grounded; in the air, pitched with the arc of the jump.
 */
export function tiltOf(
  s: {
    heading: number;
    grounded: boolean;
    nx: number;
    ny: number;
    nz: number;
    vy: number;
    speed: number;
  },
  out: THREE.Quaternion,
): THREE.Quaternion {
  _fwd.set(Math.sin(s.heading), 0, Math.cos(s.heading));
  if (s.grounded) _up.set(s.nx, s.ny, s.nz);
  else
    _up
      .set(0, 1, 0)
      .addScaledVector(_fwd, -s.vy / Math.max(8, Math.abs(s.speed)))
      .normalize();
  _right.crossVectors(_up, _fwd).normalize();
  _fwd.crossVectors(_right, _up).normalize();
  _m.makeBasis(_right, _up, _fwd);
  return out.setFromRotationMatrix(_m);
}

/** The same from an up and a forward vector (a kart riding a loop). */
export function basisOf(
  ux: number,
  uy: number,
  uz: number,
  fx: number,
  fy: number,
  fz: number,
  out: THREE.Quaternion,
): THREE.Quaternion {
  _up.set(ux, uy, uz);
  _fwd.set(fx, fy, fz);
  _right.crossVectors(_up, _fwd).normalize();
  _fwd.crossVectors(_right, _up).normalize();
  _m.makeBasis(_right, _up, _fwd);
  return out.setFromRotationMatrix(_m);
}

// ---------------------------------------------------------------- playback

/** Faster than any kart could go between two snapshots: a respawn, shown as a cut. */
const CUT_SPEED = 90;

const _qa = new THREE.Quaternion();
const _qb = new THREE.Quaternion();

/** Where the ghost is at race clock `t`, interpolated, into `out`; false once it's done. */
export function sampleGhost(g: Ghost, t: number, out: GhostSample): boolean {
  const S = g.samples;
  if (!S.length) return false;
  const last = S[S.length - 1]!;
  if (t >= last.t) {
    Object.assign(out, last);
    out.t = t;
    return t <= last.t + 0.001;
  }
  if (t <= S[0]!.t) {
    Object.assign(out, S[0]!);
    out.t = t;
    return true;
  }
  // The snapshot at or before t (they're about evenly spaced: start from the estimate).
  let i = Math.min(S.length - 2, Math.max(0, Math.floor((t - S[0]!.t) * g.meta.hz)));
  while (i > 0 && S[i]!.t > t) i--;
  while (i < S.length - 2 && S[i + 1]!.t <= t) i++;
  const a = S[i]!;
  const b = S[i + 1]!;
  const u = (t - a.t) / Math.max(1e-6, b.t - a.t);
  const gap = Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
  if (gap > CUT_SPEED * (b.t - a.t) + 1) {
    // A respawn: stay where it was until the moment it's put back.
    Object.assign(out, u < 1 ? a : b);
    out.t = t;
    return true;
  }
  // Catmull-Rom through the neighbours (the ends, or across a cut, repeat their point).
  const p0 = i > 0 && !cut(S[i - 1]!, a) ? S[i - 1]! : a;
  const p3 = i + 2 < S.length && !cut(b, S[i + 2]!) ? S[i + 2]! : b;
  const cr = (q0: number, q1: number, q2: number, q3: number) =>
    0.5 *
    (2 * q1 +
      (-q0 + q2) * u +
      (2 * q0 - 5 * q1 + 4 * q2 - q3) * u * u +
      (-q0 + 3 * q1 - 3 * q2 + q3) * u * u * u);
  out.t = t;
  out.x = cr(p0.x, a.x, b.x, p3.x);
  out.y = cr(p0.y, a.y, b.y, p3.y);
  out.z = cr(p0.z, a.z, b.z, p3.z);
  _qa.set(a.qx, a.qy, a.qz, a.qw);
  _qb.set(b.qx, b.qy, b.qz, b.qw);
  _qa.slerp(_qb, u);
  out.qx = _qa.x;
  out.qy = _qa.y;
  out.qz = _qa.z;
  out.qw = _qa.w;
  const mix = (p: number, q: number) => p + (q - p) * u;
  out.roll = mix(a.roll, b.roll);
  out.speed = mix(a.speed, b.speed);
  out.steer = mix(a.steer, b.steer);
  out.slip = Math.atan2(
    Math.sin(a.slip + wrap(b.slip - a.slip) * u),
    Math.cos(a.slip + wrap(b.slip - a.slip) * u),
  );
  out.zipTime = mix(a.zipTime, b.zipTime);
  out.spinTime = mix(a.spinTime, b.spinTime);
  // The on/off things: as they were at the nearer snapshot.
  const n = u < 0.5 ? a : b;
  out.driftDir = n.driftDir;
  out.grounded = n.grounded;
  out.throttle = n.throttle;
  out.zipPhase = n.zipPhase;
  out.zipEnhanced = n.zipEnhanced;
  out.zipSource = n.zipSource;
  return true;
}

const cut = (a: GhostSample, b: GhostSample) =>
  Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z) > CUT_SPEED * (b.t - a.t) + 1;
const wrap = (v: number) => Math.atan2(Math.sin(v), Math.cos(v));

export const blankSample = (): GhostSample => ({
  t: 0,
  x: 0,
  y: 0,
  z: 0,
  qx: 0,
  qy: 0,
  qz: 0,
  qw: 1,
  roll: 0,
  speed: 0,
  steer: 0,
  driftDir: 0,
  slip: 0,
  grounded: true,
  throttle: false,
  zipPhase: 0,
  zipEnhanced: false,
  zipTime: 0,
  zipSource: 0,
  spinTime: 0,
});

/**
 * Time against the ghost at checkpoint `k` (1-based, as validated): negative when ahead.
 * Undefined when the ghost has no split there.
 */
export function splitDelta(g: Ghost, k: number, clock: number): number | undefined {
  const s = g.meta.splits[k - 1];
  return s === undefined ? undefined : clock - s;
}

// ---------------------------------------------------------------- packing

/** Bytes per snapshot (see pack()). */
const BYTES = 36;

/** The ghost as bytes: a JSON header, then the quantised snapshots. */
export function encodeGhost(g: Ghost): Uint8Array {
  const head = new TextEncoder().encode(JSON.stringify(g.meta));
  const n = g.samples.length;
  const out = new Uint8Array(4 + head.length + n * BYTES);
  const dv = new DataView(out.buffer);
  dv.setUint32(0, head.length, true);
  out.set(head, 4);
  let o = 4 + head.length;
  for (const s of g.samples) {
    dv.setFloat32(o, s.t, true);
    dv.setInt32(o + 4, Math.round(s.x * 1000), true);
    dv.setInt32(o + 8, Math.round(s.y * 1000), true);
    dv.setInt32(o + 12, Math.round(s.z * 1000), true);
    const sign = s.qw < 0 ? -1 : 1; // q and -q are the same rotation: store w >= 0
    dv.setInt16(o + 16, Math.round(s.qx * sign * 32767), true);
    dv.setInt16(o + 18, Math.round(s.qy * sign * 32767), true);
    dv.setInt16(o + 20, Math.round(s.qz * sign * 32767), true);
    dv.setInt16(o + 22, Math.round(s.qw * sign * 32767), true);
    dv.setInt16(o + 24, Math.round(s.roll * 10000), true);
    dv.setInt16(o + 26, Math.round(clamp(s.speed, -320, 320) * 100), true);
    dv.setInt8(o + 28, Math.round(clamp(s.steer, -1, 1) * 127));
    dv.setInt8(o + 29, Math.sign(s.driftDir));
    dv.setInt16(o + 30, Math.round(wrap(s.slip) * 10000), true);
    dv.setUint8(
      o + 32,
      (s.grounded ? 1 : 0) |
        (s.throttle ? 2 : 0) |
        (s.zipEnhanced ? 4 : 0) |
        ((s.zipPhase & 7) << 3),
    );
    dv.setUint8(o + 33, s.zipSource & 255);
    dv.setUint8(o + 34, Math.round(clamp(s.zipTime, 0, 25.5) * 10));
    dv.setUint8(o + 35, Math.round(clamp(s.spinTime, 0, 2.55) * 100));
    o += BYTES;
  }
  return out;
}

export function decodeGhost(bytes: Uint8Array): Ghost | undefined {
  try {
    const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const hl = dv.getUint32(0, true);
    const meta = JSON.parse(new TextDecoder().decode(bytes.subarray(4, 4 + hl))) as GhostMeta;
    if (meta.format !== GHOST_FORMAT) return undefined;
    const samples: GhostSample[] = [];
    for (let o = 4 + hl; o + BYTES <= bytes.byteLength; o += BYTES) {
      const qx = dv.getInt16(o + 16, true) / 32767;
      const qy = dv.getInt16(o + 18, true) / 32767;
      const qz = dv.getInt16(o + 20, true) / 32767;
      const qw = dv.getInt16(o + 22, true) / 32767;
      const ql = Math.hypot(qx, qy, qz, qw) || 1;
      const f = dv.getUint8(o + 32);
      samples.push({
        t: dv.getFloat32(o, true),
        x: dv.getInt32(o + 4, true) / 1000,
        y: dv.getInt32(o + 8, true) / 1000,
        z: dv.getInt32(o + 12, true) / 1000,
        qx: qx / ql,
        qy: qy / ql,
        qz: qz / ql,
        qw: qw / ql,
        roll: dv.getInt16(o + 24, true) / 10000,
        speed: dv.getInt16(o + 26, true) / 100,
        steer: dv.getInt8(o + 28) / 127,
        driftDir: dv.getInt8(o + 29),
        slip: dv.getInt16(o + 30, true) / 10000,
        grounded: (f & 1) !== 0,
        throttle: (f & 2) !== 0,
        zipEnhanced: (f & 4) !== 0,
        zipPhase: (f >> 3) & 7,
        zipSource: dv.getUint8(o + 33),
        zipTime: dv.getUint8(o + 34) / 10,
        spinTime: dv.getUint8(o + 35) / 100,
      });
    }
    return { meta, samples };
  } catch {
    return undefined;
  }
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

// ---------------------------------------------------------------- fingerprints

/** A short, stable fingerprint of some data (FNV-1a over its JSON). */
export function fingerprint(data: unknown): string {
  const s = JSON.stringify(data);
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(36);
}

/** Which ghost a Time Trial races against. ("best" for now; later "dev", challenges.) */
export type GhostChoice = "best" | "off";

/** Storage key: a course, its layout and the physics it was set on. */
export const ghostKey = (track: string, layout: string, physics: string) =>
  `${track}|${layout}|${physics}`;
