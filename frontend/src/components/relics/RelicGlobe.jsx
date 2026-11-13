import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { WORLDS } from '../../lib/relics';

// A NASA map wrapped on a sphere, with a glowing marker where each machine still sits.
// Drag to spin, click a marker to open its story; selecting a story flies the camera to it.

const R = 1;
const BASE = import.meta.env.BASE_URL;

// Longitude east-positive, 0° facing +X, matching three.js sphere UVs for a map centred on 0°.
export function surfacePoint(lat, lon, r = R) {
  const phi = THREE.MathUtils.degToRad(lat);
  const lam = THREE.MathUtils.degToRad(lon);
  return new THREE.Vector3(r * Math.cos(phi) * Math.cos(lam), r * Math.sin(phi), -r * Math.cos(phi) * Math.sin(lam));
}

function dotTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.22, 'rgba(255,255,255,0.95)');
  grad.addColorStop(0.42, 'rgba(255,255,255,0.35)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function starfield() {
  // Deterministic stars (seeded), so every visit looks the same.
  let s = 11;
  const rand = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
  const n = 1200;
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i += 1) {
    const u = rand() * 2 - 1;
    const th = rand() * Math.PI * 2;
    const r = 30 + rand() * 30;
    const k = Math.sqrt(1 - u * u);
    pos.set([r * k * Math.cos(th), r * u, r * k * Math.sin(th)], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  return new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xcfe0ff, size: 0.09, sizeAttenuation: true, transparent: true, opacity: 0.8 }));
}

// Soft rim glow: brighter where the surface turns away from the camera.
function atmosphere(color, strength) {
  return new THREE.Mesh(
    new THREE.SphereGeometry(R * 1.035, 64, 32),
    new THREE.ShaderMaterial({
      uniforms: { glow: { value: new THREE.Color(color) }, strength: { value: strength } },
      vertexShader: 'varying vec3 vN; varying vec3 vV; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }',
      fragmentShader: 'uniform vec3 glow; uniform float strength; varying vec3 vN; varying vec3 vV; void main(){ float f = pow(1.0 - abs(dot(vN, vV)), 4.0); gl_FragColor = vec4(glow, f * strength); }',
      side: THREE.BackSide,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
}

export default function RelicGlobe({ world, relics, selectedId, onSelect, label }) {
  const mountRef = useRef(null);
  const labelRef = useRef(null);
  const api = useRef(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  // One renderer for the life of the section; world changes swap the map and the markers.
  useEffect(() => {
    const mount = mountRef.current;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.05, 200);
    camera.position.set(4.1, 0.7, 0);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 1.7;
    controls.maxDistance = 6;
    controls.rotateSpeed = 0.6;
    controls.autoRotate = !reduceMotion;
    controls.autoRotateSpeed = 0.35;
    // The page scrolls past this view, so the wheel only zooms after a click inside it.
    controls.enableZoom = false;

    scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    const sun = new THREE.DirectionalLight(0xffffff, 2.4);
    scene.add(sun);
    scene.add(starfield());

    const planet = new THREE.Mesh(new THREE.SphereGeometry(R, 128, 64), new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0 }));
    scene.add(planet);
    let glow = atmosphere(0x9fc4ff, 0.3);
    scene.add(glow);

    const markers = new THREE.Group();
    scene.add(markers);
    const dot = dotTexture();
    const loader = new THREE.TextureLoader();
    const textures = {};

    let tween = null;
    let current = { selectedId: null };
    const clock = new THREE.Timer();

    const setWorld = (worldId, list) => {
      const w = WORLDS[worldId];
      const apply = (tex) => {
        planet.material.map = tex;
        planet.material.needsUpdate = true;
      };
      if (textures[worldId]) apply(textures[worldId]);
      else
        loader.load(`${BASE}${w.map}`, (tex) => {
          tex.colorSpace = THREE.SRGBColorSpace;
          tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
          textures[worldId] = tex;
          if (current.world === worldId) apply(tex);
        });
      scene.remove(glow);
      glow.geometry.dispose();
      glow.material.dispose();
      glow = atmosphere(w.glow, w.glowStrength);
      scene.add(glow);
      current.world = worldId;

      markers.children.slice().forEach((m) => {
        markers.remove(m);
        m.material.dispose();
      });
      for (const r of list) {
        const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: dot, color: 0x7fe8ff, transparent: true, depthWrite: false }));
        sprite.position.copy(surfacePoint(r.lat, r.lon, R * 1.012));
        sprite.scale.setScalar(0.075);
        sprite.userData.id = r.id;
        markers.add(sprite);
      }
    };

    const flyTo = (lat, lon) => {
      const dist = camera.position.length();
      const to = surfacePoint(lat + 8, lon, 1).normalize().multiplyScalar(dist);
      if (reduceMotion) {
        camera.position.copy(to);
        return;
      }
      tween = { from: camera.position.clone(), to, t: 0 };
    };

    // Click (not drag) on a marker opens its story.
    const ray = new THREE.Raycaster();
    const ndc = new THREE.Vector2();
    let down = null;
    const pointerDown = (e) => {
      down = { x: e.clientX, y: e.clientY };
      controls.enableZoom = true;
    };
    const pointerUp = (e) => {
      if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) return;
      const rect = renderer.domElement.getBoundingClientRect();
      ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
      ray.setFromCamera(ndc, camera);
      const hits = ray.intersectObjects([planet, ...markers.children]);
      if (!hits.length) return;
      // The first hit decides, so a marker behind the planet can't be clicked; a tap near a marker still counts.
      const marker = hits[0].object === planet ? nearestMarker(hits[0].point) : hits[0].object;
      if (marker && marker.material.opacity > 0.3) onSelectRef.current(marker.userData.id);
    };
    // A forgiving tap target: a click on the planet within ~6° of a marker counts.
    const nearestMarker = (point) => {
      let best = null;
      let bestD = 0.11;
      for (const m of markers.children) {
        const d = m.position.clone().normalize().distanceTo(point.clone().normalize());
        if (d < bestD) {
          best = m;
          bestD = d;
        }
      }
      return best;
    };
    const pointerLeave = () => {
      if (!document.fullscreenElement) controls.enableZoom = false;
    };
    renderer.domElement.addEventListener('pointerdown', pointerDown);
    renderer.domElement.addEventListener('pointerup', pointerUp);
    renderer.domElement.addEventListener('pointerleave', pointerLeave);
    controls.addEventListener('start', () => {
      controls.autoRotate = false;
      tween = null;
    });

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = mount;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      // Narrow screens back the camera off so the whole planet fits.
      camera.zoom = Math.min(1, camera.aspect / 0.95);
      camera.updateProjectionMatrix();
    };
    const ro = new ResizeObserver(resize);
    ro.observe(mount);
    resize();

    const v = new THREE.Vector3();
    let raf = 0;
    let visible = true;
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible && !raf) raf = requestAnimationFrame(frame);
    });
    io.observe(mount);

    function frame(now) {
      raf = 0;
      clock.update(now);
      const t = clock.getElapsed();
      if (tween) {
        tween.t = Math.min(1, tween.t + clock.getDelta() / 1.1);
        const k = tween.t < 0.5 ? 4 * tween.t ** 3 : 1 - (-2 * tween.t + 2) ** 3 / 2;
        const len = THREE.MathUtils.lerp(tween.from.length(), tween.to.length(), k);
        camera.position.copy(tween.from.clone().normalize().lerp(tween.to.clone().normalize(), k).normalize().multiplyScalar(len));
        if (tween.t >= 1) tween = null;
      }
      // Sunlight comes from over the viewer's shoulder, so the side we look at is lit.
      sun.position.copy(camera.position).applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.7).add(new THREE.Vector3(0, 1.5, 0));
      controls.update();

      for (const m of markers.children) {
        const sel = m.userData.id === current.selectedId;
        const pulse = sel && !reduceMotion ? 1 + 0.25 * Math.sin(t * 4) : 1;
        m.scale.setScalar((sel ? 0.12 : 0.075) * pulse);
        m.material.color.set(sel ? 0xffa25a : 0x7fe8ff);
        // Fade markers on the far side instead of letting them shine through.
        const facing = m.position.clone().normalize().dot(camera.position.clone().normalize());
        m.material.opacity = THREE.MathUtils.clamp((facing - 0.05) * 4, 0, 1);
      }

      // The selected relic's label follows its marker.
      const sel = markers.children.find((m) => m.userData.id === current.selectedId);
      if (labelRef.current) {
        if (sel && sel.material.opacity > 0.4) {
          v.copy(sel.position).project(camera);
          const x = ((v.x + 1) / 2) * mount.clientWidth;
          labelRef.current.style.transform = `translate(${x}px, ${((1 - v.y) / 2) * mount.clientHeight}px)`;
          // Near the right edge the label sits on the marker's left so it never runs off screen.
          labelRef.current.toggleAttribute('data-flip', x > mount.clientWidth - 190);
          labelRef.current.style.opacity = '1';
        } else labelRef.current.style.opacity = '0';
      }

      renderer.render(scene, camera);
      if (visible) raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);

    api.current = {
      setWorld,
      select(id, relic) {
        current.selectedId = id;
        if (relic) flyTo(relic.lat, relic.lon);
      },
    };

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener('pointerdown', pointerDown);
      renderer.domElement.removeEventListener('pointerup', pointerUp);
      renderer.domElement.removeEventListener('pointerleave', pointerLeave);
      Object.values(textures).forEach((tx) => tx.dispose());
      dot.dispose();
      scene.traverse((o) => {
        o.geometry?.dispose();
        o.material?.dispose?.();
      });
      renderer.dispose();
      renderer.domElement.remove();
      api.current = null;
    };
  }, []);

  useEffect(() => {
    api.current?.setWorld(world, relics);
  }, [world, relics]);

  useEffect(() => {
    api.current?.select(
      selectedId,
      relics.find((r) => r.id === selectedId),
    );
  }, [selectedId, relics]);

  return (
    <div className="relic-globe" ref={mountRef}>
      <div className="relic-pin" ref={labelRef} aria-hidden="true">
        <span>{label}</span>
      </div>
    </div>
  );
}
