// 3D load test of a part: the part is loaded until it breaks. Colours show stress / strength from
// beam theory; bending is exaggerated so it is visible; broken pieces fall at lunar gravity (slowed).
// Part geometry is built in millimetres and scaled into the scene.
import * as THREE from 'three';
import { sound } from '../../../lib/sound';
import { mulberry32 } from './stage';
import { STRESS_STOPS } from './palette';

const LOAD_SECONDS = 5.5;
const SETTLE_SECONDS = 3.2;
export const SLOW_MOTION = 0.6; // falls are shown at 60% speed
const G_MM = 1620 * SLOW_MOTION; // lunar gravity in mm/s², slowed
const STAGE_FLOOR = -1.3;

const LUT = (() => {
  const out = new Float32Array(256 * 3);
  const a = new THREE.Color();
  const b = new THREE.Color();
  const c = new THREE.Color();
  for (let i = 0; i < 256; i += 1) {
    const t = i / 255;
    let k = 1;
    while (k < STRESS_STOPS.length - 1 && STRESS_STOPS[k][0] < t) k += 1;
    const [t0, c0] = STRESS_STOPS[k - 1];
    const [t1, c1] = STRESS_STOPS[k];
    c.lerpColors(a.set(c0), b.set(c1), (t - t0) / (t1 - t0));
    out.set([c.r, c.g, c.b], i * 3);
  }
  return out;
})();

const smoothstep = (e0, e1, x) => {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
};

// Standard material whose vertex colours also glow (so high stress blooms).
function stressMaterial() {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.42, metalness: 0.12 });
  const uGlow = { value: 0 };
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uGlow = uGlow;
    shader.fragmentShader = `uniform float uGlow;\n${shader.fragmentShader.replace(
      '#include <emissivemap_fragment>',
      '#include <emissivemap_fragment>\n\ttotalEmissiveRadiance += vColor.rgb * uGlow;',
    )}`;
  };
  mat.userData.uGlow = uGlow;
  return mat;
}

const metal = (color = 0x8a96a6) => new THREE.MeshStandardMaterial({ color, metalness: 0.85, roughness: 0.32 });
const panel = () => new THREE.MeshStandardMaterial({ color: 0x2c3748, metalness: 0.6, roughness: 0.5 });
const glowLines = (geo, color = 0x5fd4ff, k = 1.6) => {
  const lines = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), new THREE.LineBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), toneMapped: false, transparent: true, opacity: 0.7 }));
  // Slightly larger than the box, so the outline does not flicker against its faces.
  lines.scale.setScalar(1.004);
  return lines;
};

// A mesh whose vertices carry stress (r0 = stress / strength at the failure load) and can bend.
function piece(geometry, material, r0Fn) {
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, material);
  const pos = geometry.attributes.position;
  const base = Float32Array.from(pos.array);
  const r0 = new Float32Array(pos.count);
  for (let i = 0; i < pos.count; i += 1) r0[i] = Math.max(0, r0Fn(base[i * 3], base[i * 3 + 1], base[i * 3 + 2]));
  geometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(pos.count * 3), 3));
  return { mesh, base, r0 };
}

function paint(p, f, heat, baseColor) {
  const col = p.mesh.geometry.attributes.color;
  for (let i = 0; i < p.r0.length; i += 1) {
    const r = Math.min(1, f * p.r0[i]);
    const j = Math.round(r * 255) * 3;
    col.array[i * 3] = baseColor.r + (LUT[j] - baseColor.r) * heat;
    col.array[i * 3 + 1] = baseColor.g + (LUT[j + 1] - baseColor.g) * heat;
    col.array[i * 3 + 2] = baseColor.b + (LUT[j + 2] - baseColor.b) * heat;
  }
  col.needsUpdate = true;
}

// Cantilever deflection shape, 0 at the root and 1 at the load point, straight beyond it.
const cantilever = (rootX, L) => (x) => {
  const a = x - rootX;
  if (a <= 0) return 0;
  if (a <= L) return (a * a * (3 * L - a)) / (2 * L ** 3);
  return 1 + (1.5 * (a - L)) / L;
};

function bendPieces(pieces, profile, dy) {
  for (const p of pieces) {
    const pos = p.mesh.geometry.attributes.position;
    for (let i = 0; i < p.r0.length; i += 1) pos.array[i * 3 + 1] = p.base[i * 3 + 1] - dy * profile(p.base[i * 3]);
    pos.needsUpdate = true;
  }
}

function restore(p) {
  const pos = p.mesh.geometry.attributes.position;
  pos.array.set(p.base);
  pos.needsUpdate = true;
}

// Load arrow: glowing shaft and head, tip at the origin, pointing down.
function loadArrow() {
  const g = new THREE.Group();
  const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xff9a4d).multiplyScalar(2.2), toneMapped: false });
  const head = new THREE.Mesh(new THREE.ConeGeometry(4.5, 10, 20), mat);
  head.rotation.x = Math.PI;
  head.position.y = 5;
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 1, 12), mat);
  g.add(head, shaft);
  g.userData.setLength = (len) => {
    shaft.scale.y = Math.max(1, len - 10);
    shaft.position.y = 10 + (len - 10) / 2;
  };
  g.userData.setLength(30);
  return g;
}

// ---- Parts -------------------------------------------------------------------------------------

function buildWrench(mat) {
  const xr = 18;
  const xh = 138;
  const L = xh - xr;
  const half = 10;
  const R = 17;
  const w = 5.2;
  const g = new THREE.Group();

  // Fixed open-end head, around a bolt sticking out of a wall panel.
  const jaw = Math.sqrt(R * R - w * w);
  const neckX = Math.sqrt(R * R - half * half);
  const s = new THREE.Shape();
  s.moveTo(xr, -half);
  s.lineTo(xr, half);
  s.lineTo(neckX, half);
  s.absarc(0, 0, R, Math.asin(half / R), Math.PI - Math.asin(w / R), false);
  s.lineTo(4, w);
  s.lineTo(4, -w);
  s.lineTo(-jaw, -w);
  s.absarc(0, 0, R, Math.PI + Math.asin(w / R), 2 * Math.PI - Math.asin(half / R), false);
  s.lineTo(xr, -half);
  const headGeo = new THREE.ExtrudeGeometry(s, { depth: 6, bevelEnabled: true, bevelThickness: 0.8, bevelSize: 0.8, bevelSegments: 2, curveSegments: 36 });
  headGeo.translate(0, 0, -3);
  const head = piece(headGeo, mat, (x, y) => ((xh - x) / L) * (Math.min(Math.abs(y), half) / half) * (x < neckX ? Math.exp(-(neckX - x) / 5) : 1));

  // Handle (breaks off at the root): a bar plus a ring end.
  const barGeo = new THREE.BoxGeometry(132, 2 * half, 6, 66, 8, 1);
  barGeo.translate(xr + 66, 0, 0);
  const bar = piece(barGeo, mat, (x, y) => (x < xh ? ((xh - x) / L) * (Math.abs(y) / half) : 0));
  const ringShape = new THREE.Shape();
  ringShape.absarc(156, 0, 12, 0, Math.PI * 2, false);
  const hole = new THREE.Path();
  hole.absarc(156, 0, 6.5, 0, Math.PI * 2, true);
  ringShape.holes.push(hole);
  const ringGeo = new THREE.ExtrudeGeometry(ringShape, { depth: 6, bevelEnabled: true, bevelThickness: 0.8, bevelSize: 0.8, bevelSegments: 2, curveSegments: 40 });
  ringGeo.translate(0, 0, -3);
  const ring = piece(ringGeo, mat, () => 0);

  const pivot = new THREE.Group();
  pivot.position.set(xr, -half, 0);
  bar.mesh.position.set(-xr, half, 0);
  ring.mesh.position.set(-xr, half, 0);
  pivot.add(bar.mesh, ring.mesh);

  const bolt = new THREE.Mesh(new THREE.CylinderGeometry(5.6, 5.6, 16, 6), metal(0xb4bdc8));
  bolt.rotation.x = Math.PI / 2;
  bolt.position.z = 1;
  // A small mounting plate holds the bolt.
  const wallGeo = new THREE.BoxGeometry(46, 46, 5);
  const wall = new THREE.Mesh(wallGeo, new THREE.MeshStandardMaterial({ color: 0x3a4558, metalness: 0.7, roughness: 0.4 }));
  wall.position.set(0, 0, -8);
  const wallEdges = glowLines(wallGeo);
  wallEdges.position.copy(wall.position);
  g.add(head.mesh, pivot, bolt, wall, wallEdges);

  const profile = cantilever(xr, L);
  return {
    group: g,
    scale: 1 / 45,
    center: [75, -8],
    floor: -62,
    camera: [[1.1, 1.2, 6.4], [0, -0.05, 0]],
    fixed: [head],
    moving: [bar, ring],
    pivot,
    hull: [[xr, -half], [xr, half], [168, -12], [168, 12], [xh, -half], [xh, half]],
    crack: { x: [xr - 1, xr + 2], y: [-half, half], z: [-3, 3], size: [1.2, 3.2], count: 26 },
    profile,
    tipSpan: 30, // largest drawn deflection, mm
    loadPoint: (dy) => [xh, half + 1 - dy],
  };
}

function buildBracket(mat) {
  const xr = 8;
  const L = 100;
  const yMid = 16;
  const half = 4;
  const g = new THREE.Group();

  const wallGeo = new THREE.BoxGeometry(6, 110, 80);
  const wall = new THREE.Mesh(wallGeo, new THREE.MeshStandardMaterial({ color: 0x3a4558, metalness: 0.7, roughness: 0.4 }));
  wall.position.set(-3, -15, 0);
  const wallEdges = glowLines(wallGeo);
  wallEdges.position.copy(wall.position);

  const plateGeo = new THREE.BoxGeometry(8, 70, 30, 2, 14, 3);
  plateGeo.translate(4, -15, 0);
  const plate = piece(plateGeo, mat, (x, y) => (y > 0 ? 0.55 * smoothstep(-10, 20, y) * (x / 8) : 0.1));
  const bolts = [5, -35].map((y) => {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.2, 4, 6), metal(0xb4bdc8));
    b.rotation.z = Math.PI / 2;
    b.position.set(10, y, 0);
    return b;
  });

  const armGeo = new THREE.BoxGeometry(L, 2 * half, 30, 60, 6, 3);
  armGeo.translate(xr + L / 2, yMid, 0);
  const arm = piece(armGeo, mat, (x, y) => ((xr + L - x) / L) * (Math.abs(y - yMid) / half));

  const crateGeo = new THREE.BoxGeometry(26, 22, 26);
  const crate = new THREE.Group();
  const crateBox = new THREE.Mesh(crateGeo, new THREE.MeshStandardMaterial({ color: 0x2c3646, metalness: 0.6, roughness: 0.45 }));
  const crateEdges = glowLines(crateGeo, 0xffb36b, 2);
  crate.add(crateBox, crateEdges);
  const crateX = 94;
  const crateY = yMid + half + 11;

  const pivot = new THREE.Group();
  pivot.position.set(xr, yMid - half, 0);
  arm.mesh.position.set(-xr, -(yMid - half), 0);
  crate.position.set(crateX - xr, crateY - (yMid - half), 0);
  pivot.add(arm.mesh, crate);
  g.add(wall, wallEdges, plate.mesh, ...bolts, pivot);

  const profile = cantilever(xr, L);
  return {
    group: g,
    scale: 1 / 42,
    center: [48, -10],
    floor: -93,
    camera: [[2.8, 2.1, 5.8], [0.1, 0.45, 0]],
    fixed: [plate],
    moving: [arm],
    pivot,
    hull: [[xr, yMid - half], [xr + L, yMid - half], [xr + L, crateY + 11], [crateX - 13, crateY + 11]],
    crack: { x: [xr - 1, xr + 2], y: [yMid - half, yMid + half], z: [-15, 15], size: [1.2, 3.5], count: 30 },
    profile,
    tipSpan: 26,
    // The crate rides on the bending arm.
    onBend(dy) {
      const slope = (profile(crateX + 1) - profile(crateX - 1)) / 2;
      crate.position.y = crateY - (yMid - half) - dy * profile(crateX);
      crate.rotation.z = -Math.atan(dy * slope);
    },
    loadPoint: (dy) => [crateX, crateY + 12 - dy * profile(crateX)],
  };
}

function buildBrick(mat) {
  const g = new THREE.Group();
  const brickGeo = new THREE.BoxGeometry(200, 60, 100, 24, 8, 12);
  const brick = piece(brickGeo, mat, () => 1);

  const steel = metal();
  const base = new THREE.Mesh(new THREE.BoxGeometry(320, 16, 150), panel());
  base.position.y = -52;
  const bottom = new THREE.Mesh(new THREE.BoxGeometry(240, 14, 130), steel);
  bottom.position.y = -37;
  const top = new THREE.Group();
  const topPlate = new THREE.Mesh(new THREE.BoxGeometry(240, 14, 130), steel);
  const ram = new THREE.Mesh(new THREE.CylinderGeometry(22, 22, 70, 32), metal(0xc3ccd6));
  ram.position.y = 42;
  top.add(topPlate, ram);
  top.position.y = 37;
  const columns = [-145, 145].map((x) => {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(9, 9, 190, 24), steel);
    c.position.set(x, 35, 0);
    return c;
  });
  const crossGeo = new THREE.BoxGeometry(320, 24, 64);
  const cross = new THREE.Mesh(crossGeo, panel());
  cross.position.y = 132;
  const crossEdges = glowLines(crossGeo);
  crossEdges.position.copy(cross.position);
  const baseEdges = glowLines(base.geometry);
  baseEdges.position.copy(base.position);
  g.add(base, baseEdges, bottom, top, ...columns, cross, crossEdges, brick.mesh);

  return {
    group: g,
    scale: 1 / 72,
    center: [0, 30],
    floor: -60,
    camera: [[3.3, 2.2, 7.4], [0, 0.3, 0]],
    fixed: [brick],
    moving: [],
    pivot: null,
    // Rubble lands on the lower platen, or on the base beyond it.
    floorAt: (x, z) => (Math.abs(x) < 120 && Math.abs(z) < 65 ? -30 : -44),
    crush: { x: [-100, 100], y: [-30, 30], z: [-50, 50], size: [4, 13], count: 110 },
    tipSpan: 8,
    top,
    brick,
  };
}

const BUILDERS = { wrench: buildWrench, bracket: buildBracket, brick: buildBrick };

// ---- Scene -------------------------------------------------------------------------------------

export function createPartScene(stage, { onPhase, hud }) {
  const { scene } = stage;
  const root = new THREE.Group();
  scene.add(root);
  const baseColor = new THREE.Color(0xd8c9a8);
  const rand = mulberry32(99);

  // Fragments (shared pool).
  const MAX_FRAG = 140;
  const fragMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.75, flatShading: true });
  const frags = new THREE.InstancedMesh(new THREE.TetrahedronGeometry(1), fragMat, MAX_FRAG);
  frags.count = 0;
  frags.frustumCulled = false;
  const fragState = Array.from({ length: MAX_FRAG }, () => ({ p: new THREE.Vector3(), v: new THREE.Vector3(), r: new THREE.Euler(), w: new THREE.Vector3(), s: 1, rest: false }));

  let part = null;
  let test = null;
  let arrow = null;
  let phase = 'idle';
  let t = 0;
  let designPassed = false;
  const fall = { v: new THREE.Vector2(), w: 0 };

  const m4 = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const sv = new THREE.Vector3();

  function setPhase(p) {
    phase = p;
    onPhase?.(p);
  }

  function disposeGroup(group) {
    group.traverse((o) => {
      o.geometry?.dispose();
      if (o.material && o.material !== fragMat) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose());
    });
  }

  function pieces() {
    return [...part.fixed, ...part.moving];
  }

  function paintAll(f, heat) {
    pieces().forEach((p) => paint(p, f, heat, baseColor));
    part.mat.userData.uGlow.value = heat * (0.15 + 0.85 * f ** 2);
  }

  function drawnDeflection(f) {
    if (!test) return 0;
    const real = test.deflectionAtFailure * f;
    const exag = part.id === 'brick' ? 12 : 4;
    let dy = part.tipSpan * Math.tanh((real * exag) / part.tipSpan);
    // Tough mixes bend visibly before they break; brittle ones snap.
    if (!test.brittle && part.id !== 'brick') dy += smoothstep(0.82, 1, f) * Math.min(part.tipSpan * 0.6, test.elongation * 1.6);
    return dy;
  }

  function applyLoad(f) {
    const dy = drawnDeflection(f);
    if (part.id === 'brick') {
      const shorten = dy / 60;
      const bulge = 0.45 * shorten;
      const pos = part.brick.mesh.geometry.attributes.position;
      const b = part.brick.base;
      for (let i = 0; i < pos.count; i += 1) {
        const y = b[i * 3 + 1];
        const k = 1 + bulge * (1 - (y / 30) ** 2);
        pos.array[i * 3] = b[i * 3] * k;
        pos.array[i * 3 + 1] = y * (1 - shorten) - 30 * shorten;
        pos.array[i * 3 + 2] = b[i * 3 + 2] * k;
      }
      pos.needsUpdate = true;
      part.top.position.y = 37 - dy;
      // The press itself shows the load, so the brick gets no arrow.
      arrow.visible = false;
      return;
    }
    bendPieces(part.moving, part.profile, dy);
    part.onBend?.(dy);
    const [x, y] = part.loadPoint(dy);
    arrow.position.set(x, y, 0);
    arrow.userData.setLength(16 + 24 * f);
    arrow.visible = true;
  }

  function spawn(region, count) {
    const start = frags.count;
    const n = Math.min(count, MAX_FRAG - start);
    for (let k = 0; k < n; k += 1) {
      const st = fragState[start + k];
      const x = region.x[0] + rand() * (region.x[1] - region.x[0]);
      const y = region.y[0] + rand() * (region.y[1] - region.y[0]);
      const z = region.z[0] + rand() * (region.z[1] - region.z[0]);
      st.p.set(x, y, z);
      const out = part.id === 'brick' ? 1 : 0.4;
      st.v.set(x * 2.2 * out + (rand() - 0.5) * 120, 60 + rand() * 160, z * 2.2 * out + (rand() - 0.5) * 120);
      st.r.set(rand() * 6, rand() * 6, rand() * 6);
      st.w.set((rand() - 0.5) * 14, (rand() - 0.5) * 14, (rand() - 0.5) * 14);
      st.s = region.size[0] + rand() ** 2 * (region.size[1] - region.size[0]);
      st.rest = false;
    }
    frags.count = start + n;
    fragMat.color.copy(baseColor);
  }

  function stepFragments(dt) {
    const floorAt = part.floorAt ?? (() => part.floor);
    for (let i = 0; i < frags.count; i += 1) {
      const st = fragState[i];
      if (!st.rest) {
        st.v.y -= G_MM * dt;
        st.p.addScaledVector(st.v, dt * SLOW_MOTION);
        st.r.x += st.w.x * dt;
        st.r.y += st.w.y * dt;
        st.r.z += st.w.z * dt;
        const fl = floorAt(st.p.x, st.p.z) + st.s * 0.5;
        if (st.p.y < fl) {
          st.p.y = fl;
          st.v.y = -st.v.y * 0.28;
          st.v.x *= 0.55;
          st.v.z *= 0.55;
          st.w.multiplyScalar(0.5);
          if (Math.abs(st.v.y) < 25) st.rest = true;
        }
      }
      m4.compose(st.p, q.setFromEuler(st.r), sv.setScalar(st.s));
      frags.setMatrixAt(i, m4);
    }
    frags.instanceMatrix.needsUpdate = true;
  }

  function stepFall(dt) {
    const pv = part.pivot;
    fall.v.y -= G_MM * dt;
    pv.position.x += fall.v.x * dt * SLOW_MOTION;
    pv.position.y += fall.v.y * dt * SLOW_MOTION;
    pv.rotation.z += fall.w * dt;
    pv.updateMatrix();
    let lowest = Infinity;
    for (const [x, y] of part.hull) {
      sv.set(x - part.pivotOrigin.x, y - part.pivotOrigin.y, 0).applyMatrix4(pv.matrix);
      lowest = Math.min(lowest, sv.y);
    }
    if (lowest < part.floor) {
      pv.position.y += part.floor - lowest;
      fall.v.y = Math.abs(fall.v.y) > 60 ? -fall.v.y * 0.25 : 0;
      fall.v.x *= 0.6;
      fall.w *= 0.45;
    }
  }

  function reset() {
    t = 0;
    designPassed = false;
    frags.count = 0;
    if (part.pivot) {
      part.pivot.position.copy(part.pivotOrigin);
      part.pivot.rotation.set(0, 0, 0);
    }
    pieces().forEach(restore);
    if (part.brick) part.brick.mesh.visible = true;
    applyLoad(0);
    paintAll(0, 0);
    hud.set(0, test);
    setPhase('idle');
  }

  function build(partId) {
    if (part) {
      root.remove(part.group);
      part.group.remove(frags);
      disposeGroup(part.group);
    }
    const mat = stressMaterial();
    part = { id: partId, mat, ...BUILDERS[partId](mat) };
    part.pivotOrigin = part.pivot ? part.pivot.position.clone() : null;
    arrow = loadArrow();
    part.group.add(arrow, frags);
    const s = part.scale;
    part.group.scale.setScalar(s);
    part.group.position.set(-part.center[0] * s, STAGE_FLOOR - part.floor * s, 0);
    root.add(part.group);
    stage.setHome(...part.camera, 1.1);
    reset();
  }

  stage.onFrame((dt) => {
    if (!part || phase === 'idle' || phase === 'done') return;
    t += dt;
    if (phase === 'loading') {
      const f = Math.min(1, t / LOAD_SECONDS);
      const load = f * test.failLoad;
      applyLoad(f);
      paintAll(f, smoothstep(0, 0.12, f));
      hud.set(f, test);
      sound.creak(f);
      if (!designPassed && load >= test.designLoad && test.designLoad < test.failLoad) {
        designPassed = true;
        sound.chime();
        hud.flash('design');
      }
      if (f >= 1) {
        sound.creak(null);
        t = 0;
        setPhase('failed');
        if (part.id === 'brick') {
          part.brick.mesh.visible = false;
          spawn(part.crush, part.crush.count);
          sound.crunch();
        } else {
          // The broken piece springs back straight as it lets go.
          part.moving.forEach(restore);
          part.onBend?.(0);
          arrow.visible = false;
          spawn(part.crack, part.crack.count);
          fall.v.set(25, 40);
          fall.w = -1.6 - Math.random() * 0.6;
          sound.crack();
        }
        hud.flash('fail');
      }
    } else if (phase === 'failed') {
      if (part.pivot) stepFall(dt);
      if (part.top) part.top.position.y += (-12 - part.top.position.y) * (1 - Math.exp(-dt * 3));
      stepFragments(dt);
      if (t > SETTLE_SECONDS) setPhase('done');
    }
  });

  return {
    setPart(partId) {
      if (!part || part.id !== partId) {
        build(partId);
        sound.blip(520);
      }
    },
    setTest(next, color) {
      test = next;
      baseColor.set(color);
      if (!part) return;
      if (phase === 'idle') reset();
      else if (phase === 'loading') {
        // Inputs changed mid-test: start over with the new numbers.
        sound.creak(null);
        reset();
      }
    },
    run() {
      if (phase !== 'idle') reset();
      setPhase('loading');
      stage.setAutoRotate(false);
      sound.whoosh();
    },
    reset() {
      sound.creak(null);
      reset();
      stage.setAutoRotate(true);
    },
    dispose() {
      sound.creak(null);
      if (part) disposeGroup(part.group);
      frags.geometry.dispose();
      fragMat.dispose();
    },
  };
}
