import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import catalog from '../../lib/catalog';
import { volumeFractions } from '../../lib/engine/physics';

const MATRIX_COLORS = { PHB: 0xf1d9a7, PLA: 0x9fd4ff, PEEK: 0xd9b27a, LDPE: 0xe6eef4 };
const MAX_GRAINS = 900;
const MAX_FIBRES = 140;
const FULL_FRACTION = 0.62; // ~80 wt% regolith fills the whole grain budget

function mulberry32(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export default function ThreeDViewer({ composition }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const [phiR, phiF] = volumeFractions(catalog, composition.regolith_wt, composition.fiber_wt, composition.binder, composition.regolith);
  const grainCount = Math.round(Math.min(phiR / FULL_FRACTION, 1) * MAX_GRAINS);
  const fibreCount = Math.round(Math.min(phiF / 0.12, 1) * MAX_FIBRES);
  const grainScale = 0.55 + 0.75 * ((composition.particle_size - 10) / 140);

  useEffect(() => {
    const mount = mountRef.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100);
    camera.position.set(3.5, 2.6, 3.9);
    camera.lookAt(0, 0, 0);
    scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x2a1e14, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 1.8);
    key.position.set(4, 6, 3);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0x88aaff, 0.6);
    rim.position.set(-4, -2, -3);
    scene.add(rim);

    const group = new THREE.Group();
    scene.add(group);

    const boxGeo = new THREE.BoxGeometry(2, 2, 2);
    const edgesGeo = new THREE.EdgesGeometry(boxGeo);
    const matrixMat = new THREE.MeshPhysicalMaterial({ transparent: true, opacity: 0.16, depthWrite: false, roughness: 0.2, transmission: 0.2 });
    const edgesMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 });
    group.add(new THREE.Mesh(boxGeo, matrixMat), new THREE.LineSegments(edgesGeo, edgesMat));

    const rand = mulberry32(2026);
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const e = new THREE.Euler();
    const p = new THREE.Vector3();
    const s = new THREE.Vector3();

    // Low-poly icosahedra read as angular, glassy regolith grains.
    const grainGeo = new THREE.IcosahedronGeometry(1, 0);
    const grainMat = new THREE.MeshStandardMaterial({ roughness: 0.85, metalness: 0.05, flatShading: true });
    const grains = new THREE.InstancedMesh(grainGeo, grainMat, MAX_GRAINS);
    const grainBase = [];
    for (let i = 0; i < MAX_GRAINS; i += 1) {
      grainBase.push({
        pos: [(rand() - 0.5) * 1.82, (rand() - 0.5) * 1.82, (rand() - 0.5) * 1.82],
        rot: [rand() * Math.PI, rand() * Math.PI, rand() * Math.PI],
        size: 0.022 + rand() ** 2 * 0.05,
        squash: 0.7 + rand() * 0.5,
      });
    }
    group.add(grains);

    // Short basalt fibres as thin cylinders.
    const fibreGeo = new THREE.CylinderGeometry(0.008, 0.008, 1, 6);
    const fibreMat = new THREE.MeshStandardMaterial({ color: 0x3a3f47, roughness: 0.4, metalness: 0.3 });
    const fibres = new THREE.InstancedMesh(fibreGeo, fibreMat, MAX_FIBRES);
    for (let i = 0; i < MAX_FIBRES; i += 1) {
      const len = 0.25 + rand() * 0.35;
      e.set(rand() * Math.PI, rand() * Math.PI, rand() * Math.PI);
      m.compose(p.set((rand() - 0.5) * 1.6, (rand() - 0.5) * 1.6, (rand() - 0.5) * 1.6), q.setFromEuler(e), s.set(1, len, 1));
      fibres.setMatrixAt(i, m);
    }
    group.add(fibres);

    const layoutGrains = (scale) => {
      grainBase.forEach((g, i) => {
        const size = g.size * scale;
        e.set(...g.rot);
        m.compose(p.set(...g.pos), q.setFromEuler(e), s.set(size, size * g.squash, size));
        grains.setMatrixAt(i, m);
      });
      grains.instanceMatrix.needsUpdate = true;
    };
    sceneRef.current = { grains, fibres, grainMat, matrixMat, edgesMat, layoutGrains };

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = mount;
      if (!w || !h) return;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(mount);
    resize();

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let dragging = null;
    let visible = true;
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
    // Stop rendering while scrolled out of view.
    const io = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
    });
    io.observe(mount);

    renderer.setAnimationLoop(() => {
      if (!visible) return;
      if (!dragging && !reduceMotion) group.rotation.y += 0.0022;
      renderer.render(scene, camera);
    });

    return () => {
      renderer.setAnimationLoop(null);
      observer.disconnect();
      io.disconnect();
      mount.removeEventListener('pointerdown', onDown);
      mount.removeEventListener('pointermove', onMove);
      mount.removeEventListener('pointerup', onUp);
      mount.removeEventListener('pointercancel', onUp);
      [boxGeo, edgesGeo, grainGeo, fibreGeo, matrixMat, edgesMat, grainMat, fibreMat].forEach((r) => r.dispose());
      grains.dispose();
      fibres.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
      sceneRef.current = null;
    };
  }, []);

  useEffect(() => {
    const sc = sceneRef.current;
    if (!sc) return;
    sc.layoutGrains(grainScale);
    sc.grains.count = grainCount;
    sc.fibres.count = fibreCount;
    sc.grainMat.color.set(catalog.regoliths[composition.regolith].color);
    sc.matrixMat.color.setHex(MATRIX_COLORS[composition.binder]);
    sc.edgesMat.color.setHex(MATRIX_COLORS[composition.binder]);
  }, [grainCount, fibreCount, grainScale, composition.regolith, composition.binder]);

  return (
    <div className="viewer-wrap">
      <div ref={mountRef} className="viewer" role="img" aria-label={`3D view: ${grainCount} regolith grains and ${fibreCount} fibres in a ${catalog.binders[composition.binder].label} matrix`} />
      <div className="viewer-legend">
        <span>
          <i className="swatch" style={{ background: catalog.regoliths[composition.regolith].color }} />
          Regolith grains
        </span>
        <span>
          <i className="swatch" style={{ background: `#${MATRIX_COLORS[composition.binder].toString(16)}` }} />
          {catalog.binders[composition.binder].label} matrix
        </span>
        {fibreCount > 0 && (
          <span>
            <i className="swatch" style={{ background: '#3a3f47' }} />
            Basalt fibre
          </span>
        )}
        <span className="viewer-hint">Drag to rotate</span>
      </div>
    </div>
  );
}
