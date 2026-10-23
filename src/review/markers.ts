/**
 * The review notes drawn in the world: pins (an arrow pointing at the exact spot, with
 * its number above), boxes (a glowing outline round an area), paths and driving lines
 * (a ribbon of dots just above the ground) and measures (a line with its length).
 *
 * Colours: open notes magenta (important ones red), done ones green, the note being
 * placed or picked yellow. Numbers and lengths are drawn through walls so you can
 * always find them.
 */
import * as THREE from "three";
import type { ReviewNote, Vec3 } from "./notes";

const COLORS = { open: "#ff4ad8", important: "#ff3a2a", done: "#4ade5a", active: "#ffd84a" };

const v3 = (p: Vec3) => new THREE.Vector3(p[0], p[1], p[2]);

/** A label sprite: text on a dark rounded tag. */
function label(text: string, color: string, scale = 1) {
  const c = document.createElement("canvas");
  const g = c.getContext("2d")!;
  g.font = "bold 40px monospace";
  const w = Math.ceil(g.measureText(text).width) + 28;
  c.width = w;
  c.height = 60;
  g.font = "bold 40px monospace";
  g.fillStyle = "rgba(20, 12, 8, 0.85)";
  g.beginPath();
  g.roundRect(0, 0, w, 60, 14);
  g.fill();
  g.strokeStyle = color;
  g.lineWidth = 5;
  g.stroke();
  g.fillStyle = "#ffffff";
  g.textBaseline = "middle";
  g.fillText(text, 14, 32);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true }),
  );
  s.renderOrder = 20;
  const h = 0.9 * scale;
  s.scale.set((h * w) / 60, h, 1);
  return s;
}

function colorOf(n: ReviewNote, active: boolean) {
  if (active) return COLORS.active;
  if (n.status === "done") return COLORS.done;
  return n.important ? COLORS.important : COLORS.open;
}

/** One note's marker. */
export function noteMarker(n: ReviewNote, active = false): THREE.Object3D {
  const g = new THREE.Group();
  g.name = `review-note-${n.id}`;
  const color = colorOf(n, active);
  const mat = new THREE.MeshBasicMaterial({ color });
  const tag = `${n.status === "done" ? "✓" : ""}${n.number}`;
  if (n.pin) {
    // An arrow standing off the surface along its normal, its tip on the spot.
    const p = v3(n.pin.point);
    const nrm = v3(n.pin.normal).normalize();
    if (nrm.lengthSq() < 0.5) nrm.set(0, 1, 0);
    const arrow = new THREE.Group();
    // The cone's point at the spot (0), its base 0.9 m out; the stick beyond.
    const tip = new THREE.Mesh(
      new THREE.ConeGeometry(0.35, 0.9, 10).rotateX(Math.PI).translate(0, 0.45, 0),
      mat,
    );
    const shaft = new THREE.Mesh(
      new THREE.CylinderGeometry(0.1, 0.1, 1.8, 6).translate(0, 1.8, 0),
      mat,
    );
    arrow.add(tip, shaft);
    arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), nrm);
    arrow.position.copy(p);
    arrow.name = "bob";
    arrow.userData.base = p.clone();
    arrow.userData.normal = nrm.clone();
    // A ring on the surface round the spot.
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.35, 0.5, 20),
      new THREE.MeshBasicMaterial({
        color,
        side: THREE.DoubleSide,
        depthTest: false,
        transparent: true,
        opacity: 0.9,
      }),
    );
    ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), nrm);
    ring.position.copy(p).addScaledVector(nrm, 0.05);
    ring.renderOrder = 19;
    const l = label(tag, color);
    l.position.copy(p).addScaledVector(nrm, 3.4);
    g.add(arrow, ring, l);
  } else if (n.box) {
    const b = n.box;
    const box = new THREE.BoxGeometry(b.size[0], b.size[1], b.size[2]);
    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(box),
      new THREE.LineBasicMaterial({ color, depthTest: false, transparent: true }),
    );
    edges.renderOrder = 19;
    const fill = new THREE.Mesh(
      box,
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.12, depthWrite: false }),
    );
    const holder = new THREE.Group();
    holder.add(edges, fill);
    holder.position.copy(v3(b.center));
    holder.rotation.y = b.yaw;
    const l = label(tag, color);
    l.position.copy(v3(b.center)).add(new THREE.Vector3(0, b.size[1] / 2 + 1, 0));
    g.add(holder, l);
  } else if (n.edit) {
    // A moved, copied or deleted prop: its number over where it now is.
    const at = v3(n.edit.to.pos);
    const verb = n.edit.op === "delete" ? "DELETED" : n.edit.op === "copy" ? "COPY" : "MOVED";
    const l = label(`${tag} ${verb}`, color);
    l.position.copy(at).y += 4;
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 3, 5), mat);
    stick.position.copy(at).y += 2.2;
    g.add(l, stick);
  } else if ((n.path && n.path.length) || n.measure) {
    const pts = n.measure ? [n.measure.a, n.measure.b] : n.path!;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(
        pts.map((p) => v3(p).add(new THREE.Vector3(0, 0.35, 0))),
      ),
      new THREE.LineBasicMaterial({ color, depthTest: false, transparent: true }),
    );
    line.renderOrder = 19;
    g.add(line);
    const dot = new THREE.SphereGeometry(n.kind === "line" ? 0.12 : 0.22, 8, 6);
    const step = n.kind === "line" ? Math.max(1, Math.floor(pts.length / 60)) : 1;
    pts.forEach((p, i) => {
      if (i % step && i !== pts.length - 1) return;
      const d = new THREE.Mesh(dot, mat);
      d.position.copy(v3(p)).y += 0.35;
      g.add(d);
    });
    if (n.kind === "path" && pts.length > 1) {
      // An arrowhead at the end, showing which way it runs.
      const a = v3(pts[pts.length - 2]!);
      const b = v3(pts[pts.length - 1]!);
      const head = new THREE.Mesh(new THREE.ConeGeometry(0.4, 1, 10), mat);
      head.position.copy(b).y += 0.35;
      head.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
      g.add(head);
    }
    const mid = v3(pts[Math.floor(pts.length / 2)]!);
    if (n.measure) mid.copy(v3(n.measure.a).lerp(v3(n.measure.b), 0.5));
    const l = label(n.measure ? `${n.number} · ${n.measure.metres.toFixed(1)} M` : tag, color);
    l.position.copy(mid).y += 1.6;
    g.add(l);
  }
  return g;
}

/** Bob the pins' arrows gently along their normals. */
export function animateMarkers(root: THREE.Object3D, seconds: number) {
  root.traverse((o) => {
    if (o.name !== "bob") return;
    const b = o.userData.base as THREE.Vector3;
    const n = o.userData.normal as THREE.Vector3;
    o.position.copy(b).addScaledVector(n, Math.abs(Math.sin(seconds * 3)) * 0.25);
  });
}

/** Free a marker's GPU resources. */
export function disposeMarker(o: THREE.Object3D) {
  o.traverse((x) => {
    const m = x as THREE.Mesh;
    m.geometry?.dispose();
    const mats = Array.isArray(m.material) ? m.material : m.material ? [m.material] : [];
    for (const mt of mats) {
      (mt as THREE.SpriteMaterial).map?.dispose();
      mt.dispose();
    }
  });
}
