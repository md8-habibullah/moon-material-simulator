// Shared three.js stage for the 3D views: renderer with glow (bloom), mouse/touch camera controls,
// a starfield and a holographic floor. Each view adds its own objects and per-frame updates.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

function mulberry32(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export { mulberry32 };

function gradientTexture(inner, outer) {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(256, 220, 10, 256, 256, 380);
  grad.addColorStop(0, inner);
  grad.addColorStop(1, outer);
  g.fillStyle = grad;
  g.fillRect(0, 0, 512, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function glowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grad.addColorStop(0, 'rgba(255,255,255,0.9)');
  grad.addColorStop(0.35, 'rgba(255,255,255,0.25)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);

export function createStage(mount, opts = {}) {
  const {
    camera: camPos = [3.6, 2.6, 4.2],
    target = [0, 0, 0],
    fov = 36,
    minDistance = 2,
    maxDistance = 14,
    floorY = -1.35,
    floorRadius = 3.2,
    bloom = { strength: 0.75, radius: 0.5, threshold: 0.72 },
    autoRotateSpeed = 0.55,
    accent = 0x5fd4ff,
  } = opts;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.localClippingEnabled = true;
  mount.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const bgTexture = gradientTexture('#14284a', '#02040a');
  scene.background = bgTexture;
  scene.fog = new THREE.Fog(0x02040a, 18, 60);

  const camera = new THREE.PerspectiveCamera(fov, 1, 0.05, 200);
  camera.position.set(...camPos);
  const home = { pos: new THREE.Vector3(...camPos), target: new THREE.Vector3(...target) };
  // On tall, narrow screens (phones) the camera backs off so the subject still fits.
  const homePos = () => {
    const fit = Math.max(1, 1.5 / Math.max(camera.aspect, 0.3));
    return home.pos.clone().sub(home.target).multiplyScalar(fit).add(home.target);
  };
  let interacted = false;
  let tween = null;

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(home.target);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = minDistance;
  controls.maxDistance = maxDistance;
  controls.maxPolarAngle = Math.PI * 0.92;
  controls.autoRotate = !reduceMotion;
  controls.autoRotateSpeed = autoRotateSpeed;
  // The page scrolls past this view, so the mouse wheel only zooms after a click inside it.
  controls.enableZoom = false;
  controls.update();

  let resumeTimer = null;
  let autoRotateWanted = !reduceMotion;
  controls.addEventListener('start', () => {
    interacted = true;
    controls.autoRotate = false;
    clearTimeout(resumeTimer);
  });
  controls.addEventListener('end', () => {
    clearTimeout(resumeTimer);
    resumeTimer = setTimeout(() => {
      controls.autoRotate = autoRotateWanted;
    }, 4000);
  });
  const onDown = () => {
    controls.enableZoom = true;
  };
  const onLeave = () => {
    if (!document.fullscreenElement) controls.enableZoom = false;
  };
  renderer.domElement.addEventListener('pointerdown', onDown);
  renderer.domElement.addEventListener('pointerleave', onLeave);

  // Lights
  const hemi = new THREE.HemisphereLight(0xcfe0ff, 0x1a1208, 0.9);
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(4, 7, 3);
  const rim = new THREE.DirectionalLight(accent, 1.1);
  rim.position.set(-5, 1.5, -4);
  scene.add(hemi, key, rim);

  // Starfield
  const rand = mulberry32(7);
  const starCount = 1400;
  const starPos = new Float32Array(starCount * 3);
  const starCol = new Float32Array(starCount * 3);
  for (let i = 0; i < starCount; i += 1) {
    const u = rand() * 2 - 1;
    const th = rand() * Math.PI * 2;
    const r = 35 + rand() * 40;
    const s = Math.sqrt(1 - u * u);
    starPos.set([r * s * Math.cos(th), r * u, r * s * Math.sin(th)], i * 3);
    const b = 0.45 + rand() ** 3 * 1.6;
    const tint = rand();
    starCol.set([b * (tint > 0.85 ? 1.1 : 0.9), b * 0.95, b * (tint < 0.2 ? 0.8 : 1.15)], i * 3);
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
  starGeo.setAttribute('color', new THREE.BufferAttribute(starCol, 3));
  const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({ size: 0.16, vertexColors: true, transparent: true, opacity: 0.9, fog: false, toneMapped: false }));
  scene.add(stars);

  // Holographic floor: polar grid plus a soft glow under the subject.
  const floor = new THREE.Group();
  floor.position.y = floorY;
  const grid = new THREE.PolarGridHelper(floorRadius, 24, 7, 96, accent, accent);
  grid.material.transparent = true;
  grid.material.opacity = 0.22;
  grid.material.toneMapped = false;
  const glowTex = glowTexture();
  const glow = new THREE.Mesh(
    new THREE.CircleGeometry(floorRadius * 1.15, 64),
    new THREE.MeshBasicMaterial({ map: glowTex, color: accent, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false }),
  );
  glow.rotation.x = -Math.PI / 2;
  glow.position.y = -0.002;
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(floorRadius * 0.995, floorRadius * 1.01, 128),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(accent).multiplyScalar(2.2), transparent: true, opacity: 0.8, side: THREE.DoubleSide, toneMapped: false }),
  );
  ring.rotation.x = -Math.PI / 2;
  floor.add(glow, grid, ring);
  scene.add(floor);

  // Post-processing
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloomPass = new UnrealBloomPass(new THREE.Vector2(256, 256), bloom.strength, bloom.radius, bloom.threshold);
  composer.addPass(bloomPass);
  composer.addPass(new OutputPass());

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = mount;
    if (!w || !h) return;
    renderer.setSize(w, h);
    composer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    if (!interacted && !tween) camera.position.copy(homePos());
  };
  const ro = new ResizeObserver(resize);
  ro.observe(mount);
  resize();

  let visible = true;
  const visibility = new Set();
  const io = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    visibility.forEach((fn) => fn(visible && !document.hidden));
  });
  io.observe(mount);
  const onVis = () => visibility.forEach((fn) => fn(visible && !document.hidden));
  document.addEventListener('visibilitychange', onVis);

  // Camera tweens (reset, zoom buttons).
  const flyTo = (pos, tgt, duration = 0.9) => {
    tween = { from: camera.position.clone(), fromT: controls.target.clone(), to: pos.clone(), toT: tgt.clone(), t: 0, duration };
  };

  const frameFns = new Set();
  const timer = new THREE.Timer();
  let elapsed = 0;
  renderer.setAnimationLoop(() => {
    timer.update();
    const dt = Math.min(timer.getDelta(), 0.05);
    if (!visible || document.hidden) return;
    elapsed += dt;
    if (tween) {
      tween.t = Math.min(1, tween.t + dt / tween.duration);
      const k = ease(tween.t);
      camera.position.lerpVectors(tween.from, tween.to, k);
      controls.target.lerpVectors(tween.fromT, tween.toT, k);
      if (tween.t >= 1) tween = null;
    }
    stars.rotation.y += dt * 0.004;
    ring.material.opacity = 0.55 + 0.25 * Math.sin(elapsed * 1.4);
    frameFns.forEach((fn) => fn(dt, elapsed));
    controls.update(dt);
    composer.render(dt);
  });

  return {
    THREE,
    renderer,
    scene,
    camera,
    controls,
    bloomPass,
    lights: { hemi, key, rim },
    floor,
    reduceMotion,
    onFrame(fn) {
      frameFns.add(fn);
      return () => frameFns.delete(fn);
    },
    onVisible(fn) {
      visibility.add(fn);
      fn(visible && !document.hidden);
      return () => visibility.delete(fn);
    },
    setAutoRotate(on) {
      autoRotateWanted = on && !reduceMotion;
      controls.autoRotate = autoRotateWanted;
    },
    setBackground(inner, outer) {
      const old = scene.background;
      scene.background = gradientTexture(inner, outer);
      if (old && old !== bgTexture) old.dispose();
    },
    resetView() {
      flyTo(homePos(), home.target);
    },
    // A new subject: make this its home view and fly there.
    setHome(pos, tgt, duration = 1) {
      home.pos.set(...pos);
      home.target.set(...tgt);
      flyTo(homePos(), home.target, duration);
    },
    flyTo,
    zoom(factor) {
      const dir = camera.position.clone().sub(controls.target);
      const len = THREE.MathUtils.clamp(dir.length() * factor, minDistance, maxDistance);
      flyTo(controls.target.clone().add(dir.setLength(len)), controls.target.clone(), 0.45);
    },
    setWheelZoom(on) {
      controls.enableZoom = on;
    },
    dispose() {
      renderer.setAnimationLoop(null);
      timer.dispose();
      clearTimeout(resumeTimer);
      ro.disconnect();
      io.disconnect();
      document.removeEventListener('visibilitychange', onVis);
      renderer.domElement.removeEventListener('pointerdown', onDown);
      renderer.domElement.removeEventListener('pointerleave', onLeave);
      controls.dispose();
      scene.traverse((o) => {
        o.geometry?.dispose();
        const mats = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
        mats.forEach((m) => {
          m.map?.dispose();
          m.dispose();
        });
      });
      if (scene.background?.dispose) scene.background.dispose();
      bgTexture.dispose();
      glowTex.dispose();
      composer.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
