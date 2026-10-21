/**
 * Impact Depths' life and light (game/depths.ts says where and when): the triceratops
 * grazing, a pack of raptors darting across the road, shooting stars and the great
 * fireball at the start, the asteroid's smoke, the Heart of the Earth's crystal, motes
 * drifting in the air, and coloured light near the camera.
 *
 * All original low-poly designs built in code; purely visual.
 */
import * as THREE from "three";
import type { CoreConfig, MotesConfig, PlumeConfig } from "../game/depths";
import { corePulse } from "../game/depths";
import { createParticles } from "./particles";

const lam = (
  mats: THREE.Material[],
  color: string,
  opts: THREE.MeshLambertMaterialParameters = {},
) => {
  const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
  mats.push(m);
  return m;
};

function shadowDisc(mats: THREE.Material[], geos: THREE.BufferGeometry[], sx: number, sz: number) {
  const g = new THREE.CircleGeometry(1, 20).rotateX(-Math.PI / 2);
  geos.push(g);
  const m = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.28,
    depthWrite: false,
  });
  mats.push(m);
  const mesh = new THREE.Mesh(g, m);
  mesh.scale.set(sx, 1, sz);
  mesh.position.y = 0.06;
  mesh.renderOrder = 1;
  return mesh;
}

// ---------------------------------------------------------------- the triceratops

export interface GrazerView {
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    walk: number,
    graze: number,
    bellow: number,
    t: number,
  ): void;
  dispose(): void;
}

/**
 * A three-horned grazer (faces +z, about 8 m long at scale 1): a heavy barrel body on
 * four stout legs, a short thick tail, a great bony frill edged with knobs, two long
 * brow horns and a short nose horn over a parrot beak.
 */
export function createTriceratopsView(parent: THREE.Object3D, scale = 1): GrazerView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const geo = <G extends THREE.BufferGeometry>(g: G) => (geos.push(g), g);
  const hide = lam(mats, "#7a7a4a");
  const back = lam(mats, "#5a5a36");
  const belly = lam(mats, "#b4a878");
  const frillMat = lam(mats, "#c0602a", { side: THREE.DoubleSide });
  const frillEdge = lam(mats, "#e8b860");
  const horn = lam(mats, "#efe2c0");
  const beak = lam(mats, "#3a3026");
  const eye = lam(mats, "#1a1410");
  const root = new THREE.Group();
  root.scale.setScalar(scale);
  parent.add(root);
  const body = new THREE.Group();
  body.position.y = 2.7;
  root.add(body);
  const torso = new THREE.Mesh(geo(new THREE.SphereGeometry(1, 10, 7)), hide);
  torso.scale.set(1.7, 1.55, 3.4);
  body.add(torso);
  const ridge = new THREE.Mesh(geo(new THREE.SphereGeometry(1, 8, 5)), back);
  ridge.scale.set(1.1, 0.7, 2.8);
  ridge.position.set(0, 0.95, -0.2);
  body.add(ridge);
  const under = new THREE.Mesh(geo(new THREE.SphereGeometry(1, 8, 5)), belly);
  under.scale.set(1.35, 0.8, 2.6);
  under.position.set(0, -0.75, 0.1);
  body.add(under);
  // The tail.
  const tail = new THREE.Group();
  tail.position.set(0, 0.2, -3.0);
  body.add(tail);
  const tailMesh = new THREE.Mesh(
    geo(new THREE.ConeGeometry(0.75, 3.6, 7).rotateX(-Math.PI / 2).translate(0, 0, -1.7)),
    hide,
  );
  tail.add(tailMesh);
  // The legs: thick columns with a knee, pivoting at the hip.
  const legGeo = geo(new THREE.CylinderGeometry(0.42, 0.5, 2.4, 7).translate(0, -1.2, 0));
  const footGeo = geo(new THREE.CylinderGeometry(0.62, 0.66, 0.35, 8));
  const legs: THREE.Group[] = [];
  for (const [x, z] of [
    [-1.05, 1.9],
    [1.05, 1.9],
    [-1.15, -1.7],
    [1.15, -1.7],
  ] as const) {
    const leg = new THREE.Group();
    leg.position.set(x, -0.5, z);
    const m = new THREE.Mesh(legGeo, hide);
    leg.add(m);
    const f = new THREE.Mesh(footGeo, back);
    f.position.y = -2.3;
    leg.add(f);
    body.add(leg);
    legs.push(leg);
  }
  // The head: frill, horns, beak, pivoting at the neck.
  const head = new THREE.Group();
  head.position.set(0, 0.2, 3.1);
  body.add(head);
  const skull = new THREE.Mesh(geo(new THREE.SphereGeometry(1, 8, 6)), hide);
  skull.scale.set(0.95, 0.9, 1.5);
  skull.position.set(0, -0.2, 1.1);
  head.add(skull);
  const snout = new THREE.Mesh(
    geo(new THREE.ConeGeometry(0.62, 1.7, 7).rotateX(Math.PI / 2)),
    hide,
  );
  snout.position.set(0, -0.45, 2.6);
  head.add(snout);
  const beakM = new THREE.Mesh(
    geo(new THREE.ConeGeometry(0.34, 0.8, 6).rotateX(Math.PI / 2 + 0.4)),
    beak,
  );
  beakM.position.set(0, -0.75, 3.45);
  head.add(beakM);
  const frill = new THREE.Mesh(geo(new THREE.CircleGeometry(2.3, 14, 0, Math.PI)), frillMat);
  frill.rotation.set(-0.55, 0, 0);
  frill.position.set(0, 0.25, 0.2);
  head.add(frill);
  for (let k = 0; k <= 8; k++) {
    const a = (k / 8) * Math.PI;
    const knob = new THREE.Mesh(geo(new THREE.ConeGeometry(0.22, 0.6, 5)), frillEdge);
    knob.position.set(Math.cos(a) * 2.35, Math.sin(a) * 2.35, 0);
    knob.rotation.z = a - Math.PI / 2;
    frill.add(knob);
  }
  const hornGeo = geo(new THREE.ConeGeometry(0.2, 2.6, 6).translate(0, 1.3, 0));
  for (const s of [-1, 1]) {
    const h = new THREE.Mesh(hornGeo, horn);
    h.position.set(s * 0.5, 0.35, 1.3);
    h.rotation.set(1.05, 0, -s * 0.18);
    head.add(h);
    const e = new THREE.Mesh(geo(new THREE.SphereGeometry(0.14, 6, 4)), eye);
    e.position.set(s * 0.72, 0.05, 1.55);
    head.add(e);
  }
  const nose = new THREE.Mesh(
    geo(new THREE.ConeGeometry(0.18, 0.9, 6).translate(0, 0.45, 0)),
    horn,
  );
  nose.position.set(0, -0.05, 2.75);
  nose.rotation.x = 0.55;
  head.add(nose);
  const shadow = shadowDisc(mats, geos, 2.4, 4.4);
  root.add(shadow);
  let gait = 0;
  let last = 0;
  return {
    update(x, y, z, heading, walk, graze, bellow, t) {
      const dt = Math.min(0.1, Math.max(0, t - last));
      last = t;
      gait += dt * walk * 3.2;
      root.position.set(x, y, z);
      root.rotation.y = heading;
      legs.forEach((l, k) => {
        l.rotation.x = Math.sin(gait + (k === 0 || k === 3 ? 0 : Math.PI)) * 0.35 * walk;
      });
      body.position.y = 2.7 + Math.abs(Math.sin(gait)) * 0.08 * walk;
      // Head: down to graze (with a little chewing), up and open to bellow.
      head.rotation.x = graze * 0.55 + Math.sin(t * 5) * 0.03 * graze - bellow * 0.35;
      head.rotation.y = Math.sin(t * 0.4 + x) * 0.15 * (1 - graze);
      tail.rotation.y = Math.sin(t * 1.3 + z) * 0.25;
      beakM.rotation.x = bellow * 0.4;
    },
    dispose() {
      root.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- raptors

export interface RaptorPackView {
  /** Place the pack: the leader at (x, y, z) heading `heading`, `run` metres run so far;
   * `shown`: crossing (else they hide in the ferns, `peek` 0..1 while chirping). */
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    run: number,
    shown: boolean,
    peek: number,
    t: number,
  ): void;
  /** Where raptor k is (for the solid circles), relative to the leader. */
  offset(k: number): { along: number; across: number };
  dispose(): void;
}

/** A pack of lean, fast raptors (each ~4 m nose to tail, faces +z): a long stiff tail,
 * a crest of bright quills, sickle-clawed legs pumping. */
export function createRaptorPackView(parent: THREE.Object3D, count = 3): RaptorPackView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const geo = <G extends THREE.BufferGeometry>(g: G) => (geos.push(g), g);
  const skin = lam(mats, "#8a5a2a");
  const stripe = lam(mats, "#4a2a16");
  const pale = lam(mats, "#d8c49a");
  const crestMat = lam(mats, "#2a8aa0", { side: THREE.DoubleSide });
  const eyeMat = lam(mats, "#ffd040", {
    emissive: new THREE.Color("#a07010"),
    emissiveIntensity: 0.6,
  });
  const offs = Array.from({ length: count }, (_, k) => ({
    along: -k * 2.8,
    across: k % 2 ? 1.8 : -1.6 * Math.min(1, k),
  }));
  const pack = new THREE.Group();
  parent.add(pack);
  const bodyGeo = geo(new THREE.SphereGeometry(1, 8, 6));
  const tailGeo = geo(
    new THREE.ConeGeometry(0.32, 2.6, 6).rotateX(-Math.PI / 2).translate(0, 0, -1.3),
  );
  const neckGeo = geo(new THREE.CylinderGeometry(0.2, 0.28, 1.0, 6));
  const headGeo = geo(new THREE.BoxGeometry(0.42, 0.42, 0.95));
  const jawGeo = geo(new THREE.BoxGeometry(0.34, 0.12, 0.7));
  const thighGeo = geo(new THREE.CylinderGeometry(0.2, 0.13, 0.9, 6).translate(0, -0.45, 0));
  const shinGeo = geo(new THREE.CylinderGeometry(0.1, 0.07, 0.9, 5).translate(0, -0.45, 0));
  const footGeo = geo(new THREE.BoxGeometry(0.22, 0.08, 0.5));
  const armGeo = geo(new THREE.BoxGeometry(0.08, 0.08, 0.5));
  const quill = geo(new THREE.PlaneGeometry(0.16, 0.6));
  const shadowG = geo(new THREE.CircleGeometry(1, 14).rotateX(-Math.PI / 2));
  const shadowM = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.25,
    depthWrite: false,
  });
  mats.push(shadowM);
  const raptors = offs.map((_, k) => {
    const root = new THREE.Group();
    const s = 0.9 + 0.15 * ((k * 7) % 3);
    root.scale.setScalar(s);
    pack.add(root);
    const body = new THREE.Group();
    body.position.y = 1.35;
    root.add(body);
    const torso = new THREE.Mesh(bodyGeo, skin);
    torso.scale.set(0.45, 0.5, 1.0);
    body.add(torso);
    const back = new THREE.Mesh(bodyGeo, stripe);
    back.scale.set(0.3, 0.25, 0.8);
    back.position.y = 0.3;
    body.add(back);
    const tail = new THREE.Mesh(tailGeo, skin);
    tail.position.set(0, 0.1, -0.8);
    body.add(tail);
    const neck = new THREE.Group();
    neck.position.set(0, 0.3, 0.85);
    neck.rotation.x = -0.6;
    body.add(neck);
    const nm = new THREE.Mesh(neckGeo, skin);
    nm.position.y = 0.4;
    neck.add(nm);
    const head = new THREE.Group();
    head.position.set(0, 0.9, 0.1);
    head.rotation.x = 0.6;
    neck.add(head);
    const hm = new THREE.Mesh(headGeo, skin);
    hm.position.z = 0.3;
    head.add(hm);
    const jaw = new THREE.Mesh(jawGeo, pale);
    jaw.position.set(0, -0.2, 0.35);
    head.add(jaw);
    for (const sx of [-1, 1]) {
      const e = new THREE.Mesh(geo(new THREE.SphereGeometry(0.06, 5, 4)), eyeMat);
      e.position.set(sx * 0.2, 0.08, 0.38);
      head.add(e);
    }
    for (let q = 0; q < 5; q++) {
      const p = new THREE.Mesh(quill, crestMat);
      p.position.set(0, 0.3 + 0.02 * q, 0.1 - q * 0.22 - (q > 1 ? 0.6 : 0));
      p.rotation.set(-0.5, 0, 0);
      (q < 2 ? head : body).add(p);
      if (q >= 2) p.position.set(0, 0.45, 0.6 - (q - 2) * 0.5);
    }
    const legs: { thigh: THREE.Group; shin: THREE.Group }[] = [];
    for (const sx of [-1, 1]) {
      const thigh = new THREE.Group();
      thigh.position.set(sx * 0.3, -0.15, -0.1);
      body.add(thigh);
      thigh.add(new THREE.Mesh(thighGeo, skin));
      const shin = new THREE.Group();
      shin.position.y = -0.85;
      thigh.add(shin);
      shin.add(new THREE.Mesh(shinGeo, stripe));
      const foot = new THREE.Mesh(footGeo, stripe);
      foot.position.set(0, -0.9, 0.15);
      shin.add(foot);
      legs.push({ thigh, shin });
      const arm = new THREE.Mesh(armGeo, skin);
      arm.position.set(sx * 0.32, 0.0, 0.8);
      arm.rotation.x = 0.8;
      body.add(arm);
    }
    const sh = new THREE.Mesh(shadowG, shadowM);
    sh.scale.set(0.8, 1, 1.6);
    sh.position.y = 0.05;
    root.add(sh);
    return { root, body, tail, head, jaw, legs, phase: k * 1.7 };
  });
  return {
    update(x, y, z, heading, run, shown, peek, t) {
      pack.visible = shown || peek > 0;
      if (!pack.visible) return;
      const fx = Math.sin(heading);
      const fz = Math.cos(heading);
      raptors.forEach((r, k) => {
        const o = offs[k]!;
        const along = shown ? o.along : o.along - 3 + peek * 1.5;
        r.root.position.set(x + fx * along + fz * o.across, y, z + fz * along - fx * o.across);
        r.root.rotation.y = heading;
        const g = shown ? run * 2.2 + r.phase : t * 3 + r.phase;
        const pump = shown ? 1 : 0.15;
        r.legs.forEach((l, j) => {
          const p = g + (j ? Math.PI : 0);
          l.thigh.rotation.x = Math.sin(p) * 0.9 * pump;
          l.shin.rotation.x = (Math.cos(p) * 0.6 - 0.3) * pump;
        });
        r.body.position.y =
          1.35 + Math.abs(Math.sin(g)) * 0.12 * pump - (shown ? 0 : 0.35 * (1 - peek));
        r.body.rotation.x = shown ? 0.12 : 0;
        r.tail.rotation.y = Math.sin(g * 0.5) * 0.15;
        r.head.rotation.y = shown ? 0 : Math.sin(t * 4 + k) * 0.5;
        r.jaw.rotation.x = shown ? 0 : Math.max(0, Math.sin(t * 9 + k * 2)) * 0.5;
      });
    },
    offset(k) {
      return offs[k] ?? { along: 0, across: 0 };
    },
    dispose() {
      pack.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- meteors

export interface MeteorView {
  /** Shooting stars round `cam` (if outdoors) and the intro fireball (u: 0..1 along its
   * fall, or null). Returns true on the frame the fireball lands. */
  update(dt: number, cam: THREE.Vector3, outdoors: number, intro: number | null): boolean;
  dispose(): void;
}

/** Shooting stars streaking across the sky, and the great fireball at the start of the
 * race: from high over the start line down into the crater at `target`. */
export function createMeteorView(
  parent: THREE.Object3D,
  target: THREE.Vector3,
  from: THREE.Vector3,
  rate: number,
): MeteorView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const add = (color: string, opacity = 1) => {
    const m = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      fog: false,
    });
    mats.push(m);
    return m;
  };
  const streakGeo = new THREE.CylinderGeometry(0.02, 1, 1, 6, 1, true).translate(0, -0.5, 0);
  geos.push(streakGeo);
  const streakMat = add("#fff4d0", 0.85);
  const stars: {
    mesh: THREE.Mesh;
    life: number;
    age: number;
    pos: THREE.Vector3;
    vel: THREE.Vector3;
  }[] = [];
  for (let k = 0; k < 6; k++) {
    const mesh = new THREE.Mesh(streakGeo, streakMat);
    mesh.visible = false;
    parent.add(mesh);
    stars.push({ mesh, life: 0, age: 1, pos: new THREE.Vector3(), vel: new THREE.Vector3() });
  }
  // The fireball: a hot core, a glow, a long trail; then a flash where it lands.
  const ball = new THREE.Group();
  ball.visible = false;
  parent.add(ball);
  const coreGeo = new THREE.IcosahedronGeometry(4, 1);
  geos.push(coreGeo);
  ball.add(new THREE.Mesh(coreGeo, add("#fff0c0")));
  const glow = new THREE.Mesh(coreGeo, add("#ff8a3a", 0.5));
  glow.scale.setScalar(2.2);
  ball.add(glow);
  const trailGeo = new THREE.ConeGeometry(5, 1, 8, 1, true).translate(0, -0.5, 0);
  geos.push(trailGeo);
  const trail = new THREE.Mesh(trailGeo, add("#ff6a2a", 0.55));
  ball.add(trail);
  const light = new THREE.PointLight(0xffa060, 0, 900, 1.2);
  parent.add(light);
  const flash = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), add("#ffd890", 0.7));
  geos.push(flash.geometry);
  flash.visible = false;
  parent.add(flash);
  const dir = target.clone().sub(from);
  const up = new THREE.Vector3(0, 1, 0);
  const tailDir = dir.clone().normalize().negate();
  let acc = 0;
  let landed = false;
  let flashT = 0;
  return {
    update(dt, cam, outdoors, intro) {
      // Shooting stars: now and then, high in the sky ahead of the camera.
      acc += dt * rate * outdoors;
      if (acc > 1) {
        acc = 0;
        const s = stars.find((q) => q.age >= q.life);
        if (s) {
          const a = Math.random() * Math.PI * 2;
          s.pos.set(
            cam.x + Math.cos(a) * 500,
            cam.y + 260 + Math.random() * 120,
            cam.z + Math.sin(a) * 500,
          );
          s.vel.set(
            -Math.cos(a) * 400 + (Math.random() - 0.5) * 300,
            -120 - Math.random() * 80,
            -Math.sin(a) * 400 + (Math.random() - 0.5) * 300,
          );
          s.life = 0.8 + Math.random() * 0.6;
          s.age = 0;
        }
      }
      for (const s of stars) {
        s.age += dt;
        const on = s.age < s.life;
        s.mesh.visible = on;
        if (!on) continue;
        s.pos.addScaledVector(s.vel, dt);
        s.mesh.position.copy(s.pos);
        const v = s.vel.clone().normalize();
        s.mesh.quaternion.setFromUnitVectors(up, v.negate());
        const f = Math.sin((s.age / s.life) * Math.PI);
        s.mesh.scale.set(1.6 * f, 90 * f, 1.6 * f);
      }
      // The intro fireball.
      let hit = false;
      if (intro !== null) {
        ball.visible = true;
        landed = false;
        const u = intro * intro;
        ball.position.copy(from).addScaledVector(dir, u);
        ball.quaternion.setFromUnitVectors(up, tailDir);
        trail.scale.set(1, 60 + 220 * intro, 1);
        light.position.copy(ball.position);
        light.intensity = 3;
        glow.scale.setScalar(2.2 + Math.sin(performance.now() * 0.03) * 0.2);
      } else if (ball.visible) {
        ball.visible = false;
        if (!landed) {
          landed = true;
          hit = true;
          flashT = 1.6;
        }
      }
      if (flashT > 0) {
        flashT -= dt;
        const k = Math.max(0, flashT / 1.6);
        flash.visible = true;
        flash.position.copy(target);
        flash.scale.setScalar(20 + 90 * (1 - k));
        (flash.material as THREE.MeshBasicMaterial).opacity = 0.75 * k;
        light.position.copy(target).y += 20;
        light.intensity = 6 * k;
      } else {
        flash.visible = false;
        if (intro === null) light.intensity = 0;
      }
      return hit;
    },
    dispose() {
      for (const s of stars) s.mesh.removeFromParent();
      ball.removeFromParent();
      flash.removeFromParent();
      light.removeFromParent();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- the core

export interface CoreView {
  update(t: number, dt: number, near: number): void;
  dispose(): void;
}

/** The Heart of the Earth: a cluster of great crystals (a gold heart inside a shell of
 * magenta points), three rings of light turning round it on different tilts, motes
 * rising, and a warm light that pulses with it. */
export function createCoreView(parent: THREE.Object3D, cfg: CoreConfig): CoreView {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  const root = new THREE.Group();
  root.position.set(cfg.x, cfg.y, cfg.z);
  root.scale.setScalar(cfg.size / 10);
  parent.add(root);
  const gold = new THREE.MeshLambertMaterial({
    color: "#ffd060",
    emissive: new THREE.Color("#ffb020"),
    emissiveIntensity: 1.2,
    flatShading: true,
  });
  const rose = new THREE.MeshLambertMaterial({
    color: "#ff4aa8",
    emissive: new THREE.Color("#c01a7a"),
    emissiveIntensity: 0.9,
    flatShading: true,
    transparent: true,
    opacity: 0.82,
  });
  const violet = new THREE.MeshLambertMaterial({
    color: "#a050ff",
    emissive: new THREE.Color("#5a1aa0"),
    emissiveIntensity: 0.7,
    flatShading: true,
  });
  mats.push(gold, rose, violet);
  const spike = (r: number, h: number) => {
    const g = new THREE.ConeGeometry(r, h, 6).translate(0, h / 2, 0);
    geos.push(g);
    return g;
  };
  const heart = new THREE.Group();
  root.add(heart);
  // The gold heart: a double point, up and down.
  const up = new THREE.Mesh(spike(2.6, 7.5), gold);
  const down = new THREE.Mesh(spike(2.6, 5.5), gold);
  down.rotation.x = Math.PI;
  heart.add(up, down);
  // The magenta shell: points leaning out all round.
  const shell = new THREE.Group();
  root.add(shell);
  for (let k = 0; k < 9; k++) {
    const a = (k / 9) * Math.PI * 2;
    const m = new THREE.Mesh(
      spike(1.3 + (k % 3) * 0.3, 6 + (k % 4) * 1.6),
      k % 3 === 0 ? violet : rose,
    );
    m.position.set(Math.cos(a) * 1.6, -1.5 + (k % 2), Math.sin(a) * 1.6);
    m.rotation.set(Math.sin(a) * 0.6, 0, -Math.cos(a) * 0.6);
    shell.add(m);
  }
  for (let k = 0; k < 5; k++) {
    const a = (k / 5) * Math.PI * 2 + 0.3;
    const m = new THREE.Mesh(spike(1.1, 4.5), rose);
    m.position.set(Math.cos(a) * 1.2, -1.2, Math.sin(a) * 1.2);
    m.rotation.set(Math.PI - Math.sin(a) * 0.5, 0, Math.cos(a) * 0.5);
    shell.add(m);
  }
  // The rings of light.
  const ringMat = (c: string) => {
    const m = new THREE.MeshBasicMaterial({
      color: c,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    mats.push(m);
    return m;
  };
  const rings = [
    { r: 11, tilt: 0.25, speed: 0.5, c: "#ffd27a" },
    { r: 14, tilt: -0.5, speed: -0.35, c: "#ff6ac8" },
    { r: 17.5, tilt: 1.1, speed: 0.22, c: "#ffe9b0" },
  ].map((q) => {
    const g = new THREE.TorusGeometry(q.r, 0.22, 4, 48);
    geos.push(g);
    const pivot = new THREE.Group();
    pivot.rotation.x = Math.PI / 2 + q.tilt;
    root.add(pivot);
    const mesh = new THREE.Mesh(g, ringMat(q.c));
    pivot.add(mesh);
    // Little sparks riding each ring.
    for (let k = 0; k < 4; k++) {
      const s = new THREE.Mesh(new THREE.OctahedronGeometry(0.55), ringMat("#ffffff"));
      geos.push(s.geometry);
      const a = (k / 4) * Math.PI * 2;
      s.position.set(Math.cos(a) * q.r, Math.sin(a) * q.r, 0);
      mesh.add(s);
    }
    return { pivot, mesh, q };
  });
  // A halo: a soft glowing sphere.
  const haloMat = ringMat("#ff9ad0");
  haloMat.opacity = 0.16;
  const halo = new THREE.Mesh(new THREE.SphereGeometry(9, 16, 10), haloMat);
  geos.push(halo.geometry);
  root.add(halo);
  const light = new THREE.PointLight(0xffb0d0, 3, 200, 1.1);
  light.position.set(0, 2, 0);
  root.add(light);
  const motes = createParticles(parent, { max: 160, size: 0.6, gravity: -1.2, additive: true });
  let acc = 0;
  return {
    update(t, dt, near) {
      const p = corePulse(t);
      gold.emissiveIntensity = 1.0 + 1.4 * p;
      rose.emissiveIntensity = 0.7 + 0.9 * p;
      heart.scale.setScalar(1 + 0.06 * p);
      shell.rotation.y = t * 0.12;
      heart.rotation.y = -t * 0.3;
      for (const r of rings) {
        r.mesh.rotation.z = t * r.q.speed;
        r.pivot.rotation.y = Math.sin(t * 0.2 + r.q.r) * 0.2;
      }
      halo.scale.setScalar(1 + 0.12 * p);
      haloMat.opacity = 0.12 + 0.1 * p;
      light.intensity = 2.2 + 3 * p;
      if (near < 260) {
        acc += dt * 26;
        for (; acc > 1; acc--) {
          const a = Math.random() * Math.PI * 2;
          const r = 4 + Math.random() * 30;
          motes.emit(
            cfg.x + Math.cos(a) * r,
            cfg.y - 20 + Math.random() * 10,
            cfg.z + Math.sin(a) * r,
            (Math.random() - 0.5) * 0.6,
            3 + Math.random() * 3,
            (Math.random() - 0.5) * 0.6,
            4 + Math.random() * 3,
            Math.random() < 0.5 ? 0xffd27a : 0xff6ac8,
          );
        }
      }
      motes.step(dt);
    },
    dispose() {
      root.removeFromParent();
      motes.dispose();
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

// ---------------------------------------------------------------- plumes and motes

export interface DriftView {
  update(dt: number, cam: THREE.Vector3): void;
  dispose(): void;
}

/** A tall column of smoke billowing up and drifting, glowing from below. */
export function createPlumeView(parent: THREE.Object3D, cfg: PlumeConfig): DriftView {
  const smoke = createParticles(parent, {
    max: 220,
    size: cfg.radius * 0.9,
    gravity: -0.6,
    opacity: 0.55,
  });
  const lit = createParticles(parent, {
    max: 60,
    size: cfg.radius * 0.6,
    gravity: -0.8,
    additive: true,
  });
  const col = new THREE.Color(cfg.color);
  const glow = new THREE.Color(cfg.glow);
  let acc = 0;
  return {
    update(dt, cam) {
      const far = Math.hypot(cam.x - cfg.x, cam.z - cfg.z);
      if (far < 2200) {
        acc += dt * cfg.rate;
        for (; acc > 1; acc--) {
          const life = cfg.height / 7;
          smoke.emit(
            cfg.x + (Math.random() - 0.5) * cfg.radius,
            cfg.y,
            cfg.z + (Math.random() - 0.5) * cfg.radius,
            1.5 + Math.random() * 1.5,
            5 + Math.random() * 3,
            (Math.random() - 0.5) * 1.2,
            life,
            col.clone().offsetHSL(0, 0, (Math.random() - 0.5) * 0.06),
          );
          if (Math.random() < 0.35)
            lit.emit(
              cfg.x + (Math.random() - 0.5) * cfg.radius * 0.6,
              cfg.y + 2,
              cfg.z + (Math.random() - 0.5) * cfg.radius * 0.6,
              0.5,
              6,
              0,
              2.2,
              glow,
            );
        }
      }
      smoke.step(dt);
      lit.step(dt);
    },
    dispose() {
      smoke.dispose();
      lit.dispose();
    },
  };
}

/** Little lights drifting in the air near a spot: dust in sunbeams, glints, fireflies,
 * embers (only while the camera is near). */
export function createMotesView(parent: THREE.Object3D, cfg: MotesConfig): DriftView {
  const pool = createParticles(parent, {
    max: Math.ceil(cfg.rate * 6) + 10,
    size: cfg.size,
    gravity: -cfg.rise,
    additive: true,
  });
  const col = new THREE.Color(cfg.color);
  let acc = 0;
  return {
    update(dt, cam) {
      const far = Math.hypot(cam.x - cfg.x, cam.y - cfg.y, cam.z - cfg.z);
      if (far < cfg.radius + 120) {
        acc += dt * cfg.rate;
        for (; acc > 1; acc--) {
          const a = Math.random() * Math.PI * 2;
          const r = Math.sqrt(Math.random()) * cfg.radius;
          const life = cfg.blink ? 1.2 + Math.random() * 1.5 : 3 + Math.random() * 3;
          pool.emit(
            cfg.x + Math.cos(a) * r,
            cfg.y + (Math.random() - 0.3) * Math.min(20, cfg.radius * 0.4),
            cfg.z + Math.sin(a) * r,
            (Math.random() - 0.5) * 0.8,
            cfg.rise * (0.5 + Math.random()),
            (Math.random() - 0.5) * 0.8,
            life,
            col,
          );
        }
      }
      pool.step(dt);
    },
    dispose() {
      pool.dispose();
    },
  };
}
