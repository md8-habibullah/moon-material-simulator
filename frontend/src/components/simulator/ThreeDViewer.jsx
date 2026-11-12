import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Printer } from 'lucide-react';
import catalog from '../../lib/catalog';
import { volumeFractions } from '../../lib/engine/physics';
import { sound } from '../../lib/sound';
import { createStage, mulberry32 } from './three/stage';
import ViewerToolbar from './three/ViewerToolbar';
import { MATRIX_COLORS } from './three/palette';

const MAX_GRAINS = 900;
const MAX_FIBRES = 140;
const FULL_FRACTION = 0.62; // ~80 wt% regolith fills the whole grain budget
const PRINT_SECONDS = 6;
const LAYERS = 32;

function buildScene(stage) {
  const { scene } = stage;
  const sample = new THREE.Group();
  scene.add(sample);

  // Everything inside the sample is cut by this plane while it is being "printed".
  const clip = new THREE.Plane(new THREE.Vector3(0, -1, 0), 100);
  const clipping = [clip];

  const boxGeo = new THREE.BoxGeometry(2, 2, 2);
  const matrixMat = new THREE.MeshPhysicalMaterial({
    transparent: true,
    opacity: 0.13,
    roughness: 0.12,
    clearcoat: 1,
    depthWrite: false,
    clippingPlanes: clipping,
  });
  const edgesMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.9, toneMapped: false, clippingPlanes: clipping });
  sample.add(new THREE.Mesh(boxGeo, matrixMat), new THREE.LineSegments(new THREE.EdgesGeometry(boxGeo), edgesMat));

  // Glowing corner brackets: a HUD-style frame that stays visible while printing.
  const cornerMat = new THREE.LineBasicMaterial({ color: new THREE.Color(0x5fd4ff).multiplyScalar(2.4), toneMapped: false });
  const c = 1.12;
  const arm = 0.22;
  const pts = [];
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
    const p = new THREE.Vector3(sx * c, sy * c, sz * c);
    pts.push(p, p.clone().add(new THREE.Vector3(-sx * arm, 0, 0)));
    pts.push(p, p.clone().add(new THREE.Vector3(0, -sy * arm, 0)));
    pts.push(p, p.clone().add(new THREE.Vector3(0, 0, -sz * arm)));
  }
  const corners = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), cornerMat);
  sample.add(corners);

  const rand = mulberry32(2026);
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const e = new THREE.Euler();
  const p = new THREE.Vector3();
  const s = new THREE.Vector3();

  // Low-poly icosahedra read as angular, glassy regolith grains.
  const grainMat = new THREE.MeshStandardMaterial({ roughness: 0.8, metalness: 0.08, flatShading: true, clippingPlanes: clipping });
  const grains = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), grainMat, MAX_GRAINS);
  const grainBase = [];
  for (let i = 0; i < MAX_GRAINS; i += 1) {
    grainBase.push({
      pos: [(rand() - 0.5) * 1.8, (rand() - 0.5) * 1.8, (rand() - 0.5) * 1.8],
      rot: [rand() * Math.PI, rand() * Math.PI, rand() * Math.PI],
      size: 0.022 + rand() ** 2 * 0.05,
      squash: 0.7 + rand() * 0.5,
      shade: 0.7 + rand() * 0.5,
      cur: 0,
      tgt: 0,
    });
    grains.setColorAt(i, new THREE.Color(1, 1, 1));
  }
  sample.add(grains);

  // Short basalt fibres as thin cylinders.
  const fibreMat = new THREE.MeshStandardMaterial({ color: 0x3a3f47, roughness: 0.35, metalness: 0.4, clippingPlanes: clipping });
  const fibres = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.008, 0.008, 1, 6), fibreMat, MAX_FIBRES);
  const fibreBase = [];
  for (let i = 0; i < MAX_FIBRES; i += 1) {
    fibreBase.push({
      pos: [(rand() - 0.5) * 1.6, (rand() - 0.5) * 1.6, (rand() - 0.5) * 1.6],
      rot: [rand() * Math.PI, rand() * Math.PI, rand() * Math.PI],
      len: 0.25 + rand() * 0.35,
      cur: 0,
      tgt: 0,
    });
  }
  sample.add(fibres);

  // A scanner plane sweeping through the sample.
  const accent = new THREE.Color(0x5fd4ff);
  const scan = new THREE.Group();
  const scanPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(2.06, 2.06),
    new THREE.MeshBasicMaterial({ color: accent, transparent: true, opacity: 0.07, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }),
  );
  scanPlane.rotation.x = -Math.PI / 2;
  const square = [[-1.03, -1.03], [1.03, -1.03], [1.03, 1.03], [-1.03, 1.03]].map(([x, z]) => new THREE.Vector3(x, 0, z));
  const scanLine = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(square), new THREE.LineBasicMaterial({ color: accent.clone().multiplyScalar(2.5), toneMapped: false, transparent: true, opacity: 0.8 }));
  scan.add(scanPlane, scanLine);
  sample.add(scan);

  // Printing: a hot layer outline, a glowing nozzle and a heat haze at the build height.
  const hot = new THREE.Color(0xff8a3d);
  const printer = new THREE.Group();
  const layerLine = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(square), new THREE.LineBasicMaterial({ color: hot.clone().multiplyScalar(3), toneMapped: false }));
  const heat = new THREE.Mesh(
    new THREE.PlaneGeometry(2.06, 2.06),
    new THREE.MeshBasicMaterial({ color: hot, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }),
  );
  heat.rotation.x = -Math.PI / 2;
  const nozzle = new THREE.Group();
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.18, 20), new THREE.MeshStandardMaterial({ color: 0xb8c2cc, metalness: 0.9, roughness: 0.25 }));
  tip.rotation.x = Math.PI;
  tip.position.y = 0.12;
  const glowDot = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 12), new THREE.MeshBasicMaterial({ color: hot.clone().multiplyScalar(4), toneMapped: false }));
  const feed = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 3, 8), new THREE.MeshStandardMaterial({ color: 0x8892a0, metalness: 0.8, roughness: 0.3 }));
  feed.position.y = 1.7;
  nozzle.add(tip, glowDot, feed);
  printer.add(layerLine, heat, nozzle);
  printer.visible = false;
  sample.add(printer);

  const matrixTarget = new THREE.Color();
  let grainsDirty = true;
  let scale = 1;
  let print = null;

  const layout = (dt) => {
    const k = 1 - Math.exp(-dt * 7);
    let moving = false;
    grainBase.forEach((g, i) => {
      if (Math.abs(g.tgt - g.cur) > 1e-4) {
        g.cur += (g.tgt - g.cur) * k;
        moving = true;
      }
      const size = g.cur * g.size * scale;
      e.set(...g.rot);
      m.compose(p.set(...g.pos), q.setFromEuler(e), s.set(size, size * g.squash, size));
      grains.setMatrixAt(i, m);
    });
    fibreBase.forEach((f, i) => {
      if (Math.abs(f.tgt - f.cur) > 1e-4) {
        f.cur += (f.tgt - f.cur) * k;
        moving = true;
      }
      e.set(...f.rot);
      m.compose(p.set(...f.pos), q.setFromEuler(e), s.set(f.cur, f.len * f.cur, f.cur));
      fibres.setMatrixAt(i, m);
    });
    grains.instanceMatrix.needsUpdate = true;
    fibres.instanceMatrix.needsUpdate = true;
    return moving;
  };

  let lastLayer = -1;
  stage.onFrame((dt, t) => {
    if (grainsDirty) grainsDirty = layout(dt);
    matrixMat.color.lerp(matrixTarget, 1 - Math.exp(-dt * 5));
    edgesMat.color.copy(matrixMat.color).multiplyScalar(1.9);

    if (print) {
      print.t += dt;
      const f = Math.min(print.t / PRINT_SECONDS, 1);
      const h = -1 + 2 * f;
      clip.constant = h;
      printer.position.y = h;
      // The nozzle rasters back and forth across each layer.
      const layerF = (f * LAYERS) % 1;
      const layer = Math.floor(f * LAYERS);
      const dir = layer % 2 ? -1 : 1;
      nozzle.position.set(Math.sin(layerF * Math.PI * 6) * 0.9, 0, dir * (layerF * 1.8 - 0.9));
      heat.material.opacity = 0.16 + 0.08 * Math.sin(t * 30);
      if (layer !== lastLayer) {
        lastLayer = layer;
        sound.tick();
      }
      if (f >= 1) {
        print = null;
        clip.constant = 100;
        printer.visible = false;
        scan.visible = true;
        stage.setAutoRotate(true);
        sound.chime();
      }
    } else {
      scan.position.y = Math.sin(t * 0.55) * 0.97;
    }
    cornerMat.color.copy(accent).multiplyScalar(2 + 0.6 * Math.sin(t * 2));
  });

  return {
    update({ grainCount, fibreCount, grainScale, regolithColor, binderColor }) {
      scale = grainScale;
      grainBase.forEach((g, i) => {
        g.tgt = i < grainCount ? 1 : 0;
      });
      fibreBase.forEach((f, i) => {
        f.tgt = i < fibreCount ? 1 : 0;
      });
      const base = new THREE.Color(regolithColor);
      const tmp = new THREE.Color();
      grainBase.forEach((g, i) => grains.setColorAt(i, tmp.copy(base).multiplyScalar(g.shade)));
      grains.instanceColor.needsUpdate = true;
      matrixTarget.setHex(binderColor);
      grainsDirty = true;
    },
    startPrint() {
      print = { t: 0 };
      lastLayer = -1;
      clip.constant = -1;
      printer.visible = true;
      scan.visible = false;
      stage.setAutoRotate(false);
      stage.flyTo(new THREE.Vector3(3.6, 2.7, 4.2), new THREE.Vector3(0, -0.1, 0), 1.2);
      sound.whoosh();
    },
  };
}

export default function ThreeDViewer({ composition }) {
  const wrapRef = useRef(null);
  const mountRef = useRef(null);
  const stageRef = useRef(null);
  const viewRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [phiR, phiF] = volumeFractions(catalog, composition.regolith_wt, composition.fiber_wt, composition.binder, composition.regolith);
  const grainCount = Math.round(Math.min(phiR / FULL_FRACTION, 1) * MAX_GRAINS);
  const fibreCount = Math.round(Math.min(phiF / 0.12, 1) * MAX_FIBRES);
  const grainScale = 0.55 + 0.75 * ((composition.particle_size - 10) / 140);
  const regolithColor = catalog.regoliths[composition.regolith].color;
  const binderColor = MATRIX_COLORS[composition.binder];

  useEffect(() => {
    const stage = createStage(mountRef.current, { floorY: -1.45, floorRadius: 2.6 });
    stageRef.current = stage;
    viewRef.current = buildScene(stage);
    const offVisible = stage.onVisible((on) => sound.ambient(on));
    setReady(true);
    return () => {
      offVisible();
      sound.ambient(false);
      stage.dispose();
      stageRef.current = null;
      viewRef.current = null;
    };
  }, []);

  useEffect(() => {
    viewRef.current?.update({ grainCount, fibreCount, grainScale, regolithColor, binderColor });
  }, [ready, grainCount, fibreCount, grainScale, regolithColor, binderColor]);

  // A soft cue when the material itself changes (not on every slider step).
  const firstRender = useRef(true);
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    sound.blip(composition.binder === 'PHB' ? 660 : 740);
  }, [composition.binder, composition.regolith, composition.process]);

  return (
    <div className="viewer-wrap" ref={wrapRef}>
      <div className="viewer-stage">
        <div ref={mountRef} className="viewer viewer-3d" role="img" aria-label={`3D view: ${grainCount} regolith grains and ${fibreCount} fibres in a ${catalog.binders[composition.binder].label} matrix`} />
        <div className="viewer-hud" aria-hidden="true">
          <span className="hud-kicker">Microstructure</span>
          <span>
            {(phiR * 100).toFixed(1)}% regolith{phiF > 0 ? ` · ${(phiF * 100).toFixed(1)}% fibre` : ''} by volume
          </span>
        </div>
        <ViewerToolbar stageRef={stageRef} wrapRef={wrapRef} />
        <button type="button" className="viewer-action" onClick={() => viewRef.current?.startPrint()}>
          <Printer size={15} aria-hidden="true" /> Print it
        </button>
      </div>
      <div className="viewer-legend">
        <span>
          <i className="swatch" style={{ background: regolithColor }} />
          Regolith grains
        </span>
        <span>
          <i className="swatch" style={{ background: `#${binderColor.toString(16)}` }} />
          {catalog.binders[composition.binder].label} matrix
        </span>
        {fibreCount > 0 && (
          <span>
            <i className="swatch" style={{ background: '#3a3f47' }} />
            Basalt fibre
          </span>
        )}
        <span className="viewer-hint">Drag: rotate · click, then scroll: zoom · right-drag: pan</span>
      </div>
    </div>
  );
}
