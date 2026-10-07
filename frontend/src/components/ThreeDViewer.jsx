import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { POLYMERS, REGOLITHS, formatNumber, volumeFraction } from '../lib/materials';

const GRAIN_COLORS = { lunar: 0xb4b8c2, martian: 0xc8643a };
const MATRIX_COLORS = { PLA: 0x8fd3ff, PEEK: 0xe8b66a, LDPE: 0xdfe9f1 };
// 50 wt% lunar regolith in PLA is ~31% by volume; that maps to the full grain budget.
const MAX_GRAINS = 650;
const MAX_FRACTION = 0.32;

// Small seeded PRNG so the microstructure looks the same on every load.
function mulberry32(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export default function ThreeDViewer({ regolithWt, regolithType, polymerType }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const phi = volumeFraction(regolithWt, polymerType, regolithType);
  const grainCount = Math.round(Math.min(phi / MAX_FRACTION, 1) * MAX_GRAINS);

  useEffect(() => {
    const mount = mountRef.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.set(3.4, 2.5, 3.8);
    camera.lookAt(0, 0, 0);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(4, 6, 3);
    scene.add(sun);

    const group = new THREE.Group();
    scene.add(group);

    const boxGeo = new THREE.BoxGeometry(2, 2, 2);
    const edgesGeo = new THREE.EdgesGeometry(boxGeo);
    const matrixMat = new THREE.MeshStandardMaterial({ transparent: true, opacity: 0.14, depthWrite: false, roughness: 0.25 });
    const edgesMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.55 });
    group.add(new THREE.Mesh(boxGeo, matrixMat), new THREE.LineSegments(edgesGeo, edgesMat));

    // Low-poly icosahedra read as angular, glassy regolith grains.
    const grainGeo = new THREE.IcosahedronGeometry(1, 0);
    const grainMat = new THREE.MeshStandardMaterial({ roughness: 0.85, flatShading: true });
    const grains = new THREE.InstancedMesh(grainGeo, grainMat, MAX_GRAINS);
    const rand = mulberry32(2026);
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const e = new THREE.Euler();
    for (let i = 0; i < MAX_GRAINS; i += 1) {
      const s = 0.03 + rand() ** 2 * 0.07;
      e.set(rand() * Math.PI, rand() * Math.PI, rand() * Math.PI);
      m.compose(
        new THREE.Vector3((rand() - 0.5) * 1.84, (rand() - 0.5) * 1.84, (rand() - 0.5) * 1.84),
        q.setFromEuler(e),
        new THREE.Vector3(s, s * (0.7 + rand() * 0.5), s),
      );
      grains.setMatrixAt(i, m);
    }
    group.add(grains);
    sceneRef.current = { grains, grainMat, matrixMat, edgesMat };

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = mount;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(mount);
    resize();

    // Drag to rotate; otherwise a slow idle spin unless the user prefers reduced motion.
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let dragging = null;
    const onDown = (ev) => {
      dragging = { x: ev.clientX, y: ev.clientY };
      mount.setPointerCapture(ev.pointerId);
    };
    const onMove = (ev) => {
      if (!dragging) return;
      group.rotation.y += (ev.clientX - dragging.x) * 0.01;
      group.rotation.x = THREE.MathUtils.clamp(group.rotation.x + (ev.clientY - dragging.y) * 0.01, -1, 1);
      dragging = { x: ev.clientX, y: ev.clientY };
    };
    const onUp = () => {
      dragging = null;
    };
    mount.addEventListener('pointerdown', onDown);
    mount.addEventListener('pointermove', onMove);
    mount.addEventListener('pointerup', onUp);
    mount.addEventListener('pointercancel', onUp);

    renderer.setAnimationLoop(() => {
      if (!dragging && !reduceMotion) group.rotation.y += 0.0025;
      renderer.render(scene, camera);
    });

    return () => {
      renderer.setAnimationLoop(null);
      observer.disconnect();
      mount.removeEventListener('pointerdown', onDown);
      mount.removeEventListener('pointermove', onMove);
      mount.removeEventListener('pointerup', onUp);
      mount.removeEventListener('pointercancel', onUp);
      [boxGeo, edgesGeo, grainGeo, matrixMat, edgesMat, grainMat].forEach((r) => r.dispose());
      grains.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
      sceneRef.current = null;
    };
  }, []);

  useEffect(() => {
    const s = sceneRef.current;
    if (!s) return;
    s.grains.count = grainCount;
    s.grainMat.color.setHex(GRAIN_COLORS[regolithType]);
    s.matrixMat.color.setHex(MATRIX_COLORS[polymerType]);
    s.edgesMat.color.setHex(MATRIX_COLORS[polymerType]);
  }, [grainCount, regolithType, polymerType]);

  return (
    <section className="card viewer-card" aria-labelledby="viewer-title">
      <div className="card-head">
        <h2 id="viewer-title">Microstructure</h2>
        <span className="chip">{formatNumber(phi * 100)}% filler by volume</span>
      </div>
      <div ref={mountRef} className="viewer" aria-hidden="true" />
      <p className="viewer-caption">
        <span className="swatch" style={{ background: `#${GRAIN_COLORS[regolithType].toString(16)}` }} />
        {REGOLITHS[regolithType].label} regolith grains
        <span className="swatch matrix" style={{ background: `#${MATRIX_COLORS[polymerType].toString(16)}` }} />
        {POLYMERS[polymerType].label} matrix
        <span className="viewer-hint">Drag to rotate</span>
      </p>
    </section>
  );
}
