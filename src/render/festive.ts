/**
 * Hearthglow Hollow's moving and breakable bits, built in code (original, chunky, a few
 * hundred triangles each): giant rolling snowballs, wrapped presents you can smash, the
 * bell in the bell tower, spinning baubles, and the sleigh with its two reindeer and its
 * snowman driver. Purely visual: what they do is game/hazards.ts.
 */
import * as THREE from "three";

interface Kit {
  mats: THREE.Material[];
  geos: THREE.BufferGeometry[];
  mat(
    color: string | number,
    opts?: THREE.MeshLambertMaterialParameters,
  ): THREE.MeshLambertMaterial;
  geo<T extends THREE.BufferGeometry>(g: T): T;
  add(
    g: THREE.BufferGeometry,
    m: THREE.Material,
    to: THREE.Object3D,
    at?: [number, number, number],
    s?: [number, number, number],
    rot?: [number, number, number],
  ): THREE.Mesh;
  dispose(): void;
}

function kit(): Kit {
  const mats: THREE.Material[] = [];
  const geos: THREE.BufferGeometry[] = [];
  return {
    mats,
    geos,
    mat(color, opts = {}) {
      const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
      mats.push(m);
      return m;
    },
    geo(g) {
      geos.push(g);
      return g;
    },
    add(g, m, to, at = [0, 0, 0], s = [1, 1, 1], rot) {
      const mesh = new THREE.Mesh(g, m);
      mesh.position.set(...at);
      mesh.scale.set(...s);
      if (rot) mesh.rotation.set(...rot);
      mesh.castShadow = true;
      to.add(mesh);
      return mesh;
    },
    dispose() {
      for (const g of geos) g.dispose();
      for (const m of mats) m.dispose();
    },
  };
}

function shadowDisc(k: Kit, to: THREE.Object3D, sx: number, sz: number) {
  const m = new THREE.MeshBasicMaterial({
    color: 0,
    transparent: true,
    opacity: 0.28,
    depthWrite: false,
  });
  k.mats.push(m);
  const s = new THREE.Mesh(k.geo(new THREE.CircleGeometry(1, 20)), m);
  s.rotation.x = -Math.PI / 2;
  s.scale.set(sx, sz, 1);
  s.renderOrder = 1;
  to.add(s);
  return s;
}

export interface MoverView {
  readonly root: THREE.Group;
  dispose(): void;
}

// ---------------------------------------------------------------- the snowball

export interface SnowballView extends MoverView {
  /** Place it (ground point under it), rolling `rolled` metres along `heading`. */
  update(
    x: number,
    ground: number,
    z: number,
    heading: number,
    rolled: number,
    shown: boolean,
  ): void;
}

export function createSnowballView(parent: THREE.Object3D, r: number): SnowballView {
  const k = kit();
  const root = new THREE.Group();
  root.name = "snowball";
  const ball = new THREE.Group();
  root.add(ball);
  const white = k.mat("#f4f8ff");
  const blue = k.mat("#cfdcf4");
  k.add(k.geo(new THREE.IcosahedronGeometry(1, 2)), white, ball, [0, 0, 0], [r, r, r]);
  // Lumps of packed snow stuck to it, so you can see it roll.
  const lump = k.geo(new THREE.IcosahedronGeometry(1, 0));
  for (let i = 0; i < 9; i++) {
    const a = i * 2.39996;
    const y = 1 - (2 * (i + 0.5)) / 9;
    const rr = Math.sqrt(1 - y * y);
    k.add(
      lump,
      i % 2 ? blue : white,
      ball,
      [Math.cos(a) * rr * r, y * r, Math.sin(a) * rr * r],
      [r * 0.32, r * 0.26, r * 0.3],
    );
  }
  const shadow = shadowDisc(k, root, r * 1.1, r * 1.1);
  parent.add(root);
  return {
    root,
    update(x, ground, z, heading, rolled, shown) {
      root.visible = shown;
      if (!shown) return;
      root.position.set(x, ground, z);
      ball.position.y = r * 0.95;
      // Roll about the axis across its path.
      ball.rotation.set(0, 0, 0);
      ball.rotateY(heading);
      ball.rotateX(rolled / r);
      shadow.position.y = 0.06;
    },
    dispose() {
      root.removeFromParent();
      k.dispose();
    },
  };
}

// ---------------------------------------------------------------- presents

const WRAPS = ["#d8263a", "#2e9a4a", "#2f6fd8", "#9a3ad0", "#f0b020"];
const RIBBONS = ["#f6d040", "#f6f0e0", "#e8302e", "#f6d040", "#d8263a"];

export interface PresentView extends MoverView {
  /** Show it at `scale` (0 hidden .. 1 full size); `wobble` jiggles it after a near miss. */
  update(scale: number, t: number): void;
}

export function createPresentView(
  parent: THREE.Object3D,
  x: number,
  y: number,
  z: number,
  size: number,
  variant: number,
  heading: number,
): PresentView {
  const k = kit();
  const root = new THREE.Group();
  root.name = "present";
  root.position.set(x, y, z);
  root.rotation.y = heading;
  const box = new THREE.Group();
  root.add(box);
  const wrap = k.mat(WRAPS[variant % WRAPS.length]!);
  const ribbon = k.mat(RIBBONS[variant % RIBBONS.length]!, { emissive: 0x201000 });
  const cube = k.geo(new THREE.BoxGeometry(1, 1, 1));
  const h = size * (0.8 + 0.2 * (variant % 3));
  k.add(cube, wrap, box, [0, h / 2, 0], [size, h, size]);
  k.add(cube, ribbon, box, [0, h / 2, 0], [size * 1.02, h * 1.02, size * 0.16]);
  k.add(cube, ribbon, box, [0, h / 2, 0], [size * 0.16, h * 1.02, size * 1.02]);
  const loop = k.geo(new THREE.TorusGeometry(size * 0.18, size * 0.06, 5, 10));
  k.add(loop, ribbon, box, [size * 0.14, h + size * 0.12, 0], [1, 1, 1], [0, 0, 0.6]);
  k.add(loop, ribbon, box, [-size * 0.14, h + size * 0.12, 0], [1, 1, 1], [0, 0, -0.6]);
  parent.add(root);
  return {
    root,
    update(scale, t) {
      root.visible = scale > 0.01;
      box.scale.setScalar(Math.max(0.01, scale));
      box.rotation.z = 0.03 * Math.sin(t * 2 + variant);
    },
    dispose() {
      root.removeFromParent();
      k.dispose();
    },
  };
}

// ---------------------------------------------------------------- the bell

export interface BellView extends MoverView {
  update(angle: number): void;
}

export function createBellView(
  parent: THREE.Object3D,
  x: number,
  y: number,
  z: number,
  heading: number,
  scale = 1,
): BellView {
  const k = kit();
  const root = new THREE.Group();
  root.name = "bell";
  root.position.set(x, y, z);
  root.rotation.y = heading;
  root.scale.setScalar(scale);
  const swing = new THREE.Group();
  root.add(swing);
  const bronze = k.mat("#d8a032", { emissive: 0x3a2008 });
  const dark = k.mat("#4a2e18");
  const prof = [
    [0.0, -2.2],
    [1.55, -2.2],
    [1.5, -1.9],
    [1.2, -1.4],
    [0.95, -0.6],
    [0.85, 0.2],
    [0.6, 0.6],
    [0.0, 0.7],
  ].map(([a, b]) => new THREE.Vector2(a!, b!));
  k.add(k.geo(new THREE.LatheGeometry(prof, 14)), bronze, swing);
  k.add(k.geo(new THREE.SphereGeometry(0.35, 8, 6)), dark, swing, [0, -2.0, 0]);
  k.add(k.geo(new THREE.BoxGeometry(3.6, 0.4, 0.4)), dark, root, [0, 0.9, 0]);
  parent.add(root);
  return {
    root,
    update(angle) {
      swing.rotation.x = angle;
    },
    dispose() {
      root.removeFromParent();
      k.dispose();
    },
  };
}

// ---------------------------------------------------------------- baubles

export interface OrnamentView extends MoverView {
  update(t: number): void;
}

export function createOrnamentView(
  parent: THREE.Object3D,
  x: number,
  y: number,
  z: number,
  r: number,
  color: string,
): OrnamentView {
  const k = kit();
  const root = new THREE.Group();
  root.position.set(x, y, z);
  const spin = new THREE.Group();
  root.add(spin);
  const main = k.mat(color, { emissive: new THREE.Color(color).multiplyScalar(0.35) });
  const gold = k.mat("#f4c440", { emissive: 0x403010 });
  k.add(k.geo(new THREE.IcosahedronGeometry(1, 2)), main, spin, [0, 0, 0], [r, r, r]);
  k.add(
    k.geo(new THREE.TorusGeometry(1, 0.08, 4, 18)),
    gold,
    spin,
    [0, 0, 0],
    [r * 1.01, r * 1.01, r * 1.01],
    [Math.PI / 2, 0, 0],
  );
  k.add(
    k.geo(new THREE.CylinderGeometry(0.22, 0.22, 0.3, 8)),
    gold,
    spin,
    [0, r * 1.02, 0],
    [r, r, r],
  );
  const phase = (x * 7 + z * 3) % 6.28;
  parent.add(root);
  return {
    root,
    update(t) {
      spin.rotation.y = t * 0.6 + phase;
      spin.position.y = 0.25 * r * Math.sin(t * 0.9 + phase);
    },
    dispose() {
      root.removeFromParent();
      k.dispose();
    },
  };
}

// ---------------------------------------------------------------- the sleigh

export interface SleighView extends MoverView {
  /** Place it (on the ground), facing `heading`; `run` is metres travelled (for the
   * reindeer's gallop). */
  update(
    x: number,
    y: number,
    z: number,
    heading: number,
    run: number,
    shown: boolean,
    t: number,
  ): void;
}

export function createSleighView(parent: THREE.Object3D): SleighView {
  const k = kit();
  const root = new THREE.Group();
  root.name = "sleigh";
  const red = k.mat("#d02a30");
  const gold = k.mat("#f2c040", { emissive: 0x3a2806 });
  const brown = k.mat("#8a5432");
  const tan = k.mat("#d8b48a");
  const dark = k.mat("#2a1a14");
  const snow = k.mat("#f6faff");
  const green = k.mat("#2e9a4a");
  const box = k.geo(new THREE.BoxGeometry(1, 1, 1));
  const ball = k.geo(new THREE.IcosahedronGeometry(1, 1));
  const rod = k.geo(new THREE.CylinderGeometry(1, 1, 1, 6));

  // The sleigh (behind the reindeer, which run ahead along +z).
  const sleigh = new THREE.Group();
  sleigh.position.z = -3.5;
  root.add(sleigh);
  k.add(box, red, sleigh, [0, 1.6, 0], [2.6, 1.4, 4.2]);
  k.add(box, red, sleigh, [0, 2.6, -1.6], [2.6, 1.6, 1.0]); // the high back
  k.add(box, gold, sleigh, [0, 2.32, 0], [2.7, 0.14, 4.3]);
  // A curled front.
  const curl = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 1.0, 2.0),
    new THREE.Vector3(0, 1.4, 2.9),
    new THREE.Vector3(0, 2.4, 3.1),
    new THREE.Vector3(0, 2.7, 2.6),
  ]);
  for (const sd of [-1, 1]) {
    // Runners, curling up at the front.
    const runner = new THREE.CatmullRomCurve3([
      new THREE.Vector3(sd * 1.1, 0.2, -2.4),
      new THREE.Vector3(sd * 1.1, 0.15, 1.8),
      new THREE.Vector3(sd * 1.1, 0.6, 2.9),
      new THREE.Vector3(sd * 1.1, 1.3, 3.0),
    ]);
    k.add(k.geo(new THREE.TubeGeometry(runner, 12, 0.13, 5, false)), gold, sleigh);
    for (const zz of [-1.4, 1.2]) k.add(rod, gold, sleigh, [sd * 1.1, 0.55, zz], [0.08, 0.8, 0.08]);
  }
  k.add(k.geo(new THREE.TubeGeometry(curl, 10, 0.18, 5, false)), gold, sleigh);
  // A heap of presents in the back.
  for (const [px, py, pz, s, c] of [
    [-0.5, 2.6, -0.8, 1.0, red],
    [0.55, 2.55, -0.6, 0.9, green],
    [0.0, 3.3, -1.0, 0.8, gold],
  ] as const)
    k.add(box, c, sleigh, [px, py, pz], [s, s, s], [0, px, 0]);
  // The driver: a cheery snowman in a top hat and scarf, holding the reins.
  const driver = new THREE.Group();
  driver.position.set(0, 2.3, 0.6);
  sleigh.add(driver);
  k.add(ball, snow, driver, [0, 0.7, 0], [0.9, 0.85, 0.9]);
  k.add(ball, snow, driver, [0, 1.9, 0], [0.62, 0.6, 0.62]);
  k.add(box, green, driver, [0, 1.42, 0], [1.1, 0.25, 1.1]);
  k.add(rod, dark, driver, [0, 2.65, 0], [0.62, 0.12, 0.62]);
  k.add(rod, dark, driver, [0, 3.05, 0], [0.42, 0.8, 0.42]);
  k.add(
    k.geo(new THREE.ConeGeometry(0.12, 0.6, 6)),
    k.mat("#f08a20"),
    driver,
    [0, 1.9, 0.75],
    [1, 1, 1],
    [Math.PI / 2, 0, 0],
  );
  for (const sd of [-1, 1]) k.add(ball, dark, driver, [sd * 0.22, 2.05, 0.52], [0.08, 0.08, 0.08]);

  // Two reindeer, side by side, galloping.
  const deer: { body: THREE.Group; legs: THREE.Group[]; head: THREE.Group }[] = [];
  for (const sd of [-1, 1]) {
    const body = new THREE.Group();
    body.position.set(sd * 1.0, 0, 2.5);
    root.add(body);
    k.add(ball, brown, body, [0, 2.2, 0], [0.75, 0.7, 1.45]);
    k.add(ball, tan, body, [0, 1.85, 0.1], [0.55, 0.4, 1.1]);
    k.add(ball, tan, body, [0, 2.3, -1.35], [0.25, 0.3, 0.2]); // the tail
    const head = new THREE.Group();
    head.position.set(0, 2.9, 1.25);
    body.add(head);
    k.add(rod, brown, head, [0, -0.2, -0.1], [0.32, 0.9, 0.32], [0.5, 0, 0]);
    k.add(ball, brown, head, [0, 0.45, 0.25], [0.42, 0.42, 0.55]);
    k.add(ball, tan, head, [0, 0.32, 0.72], [0.28, 0.25, 0.3]);
    k.add(ball, dark, head, [0, 0.38, 0.98], [0.1, 0.09, 0.08]); // a dark button nose
    for (const e of [-1, 1]) {
      k.add(ball, dark, head, [e * 0.26, 0.6, 0.55], [0.07, 0.08, 0.06]);
      k.add(ball, brown, head, [e * 0.4, 0.75, 0.05], [0.1, 0.25, 0.14], [0, 0, e * 0.7]);
      // Antlers: a beam with three tines.
      const a = new THREE.Group();
      a.position.set(e * 0.22, 0.8, 0.2);
      a.rotation.z = e * -0.35;
      head.add(a);
      k.add(rod, tan, a, [0, 0.45, 0], [0.06, 0.9, 0.06]);
      for (const [ty, tz, tl] of [
        [0.35, 0.15, 0.35],
        [0.65, 0.12, 0.3],
        [0.85, -0.05, 0.25],
      ] as const)
        k.add(rod, tan, a, [e * 0.12, ty, tz], [0.05, tl, 0.05], [0.9, 0, e * -0.6]);
    }
    const legs: THREE.Group[] = [];
    for (const [lx, lz] of [
      [0.35, 0.9],
      [-0.35, 0.9],
      [0.35, -0.9],
      [-0.35, -0.9],
    ] as const) {
      const hip = new THREE.Group();
      hip.position.set(lx, 1.9, lz);
      body.add(hip);
      k.add(rod, brown, hip, [0, -0.85, 0], [0.13, 1.7, 0.13]);
      k.add(box, dark, hip, [0, -1.75, 0.05], [0.2, 0.16, 0.26]);
      legs.push(hip);
    }
    // A collar of golden bells.
    for (let i = 0; i < 5; i++)
      k.add(
        ball,
        gold,
        body,
        [Math.cos(i * 0.8 - 1.6) * 0.55, 2.6 + Math.sin(i * 0.8 - 1.6) * 0.2, 1.05],
        [0.13, 0.13, 0.13],
      );
    deer.push({ body, legs, head });
  }
  // The harness poles from the sleigh to the reindeer.
  for (const sd of [-1.6, 1.6])
    k.add(rod, dark, root, [sd, 1.6, 0], [0.06, 4.0, 0.06], [Math.PI / 2, 0, 0]);
  shadowDisc(k, root, 2.6, 6.5).position.y = 0.08;
  parent.add(root);
  return {
    root,
    update(x, y, z, heading, run, shown, t) {
      root.visible = shown;
      if (!shown) return;
      root.position.set(x, y, z);
      root.rotation.y = heading;
      const ph = run * 0.55;
      deer.forEach((d, i) => {
        const p = ph + i * 0.7;
        d.body.position.y = 0.25 * Math.abs(Math.sin(p));
        d.head.rotation.x = 0.12 * Math.sin(p * 2);
        d.legs.forEach((l, j) => {
          l.rotation.x = Math.sin(p + (j < 2 ? 0 : Math.PI * 0.8)) * 0.75;
        });
      });
      sleigh.position.y = 0.06 * Math.sin(t * 9);
    },
    dispose() {
      root.removeFromParent();
      k.dispose();
    },
  };
}
