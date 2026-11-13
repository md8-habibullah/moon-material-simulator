import { useEffect, useMemo, useRef, useState } from 'react';
import { BrickWall, FlaskConical, Hammer, House, Moon, RotateCcw, Sigma, SquareStack, Sun, Wrench } from 'lucide-react';
import catalog, { PROPERTY, formatValue } from '../../lib/catalog';
import { ENVIRONMENTS, PARTS, formatFactor, formatForce, formatMass, massEquivalent, partTest } from '../../lib/engine/parts';
import { supportLevel } from '../../lib/engine/evidence';
import { volumeFractions } from '../../lib/engine/physics';
import { createStage } from './three/stage';
import { createPartScene, SLOW_MOTION } from './three/partScene';
import { MATRIX_COLORS, STRESS_GRADIENT } from './three/palette';
import ViewerToolbar from './three/ViewerToolbar';

const PART_ICONS = { wrench: Wrench, bracket: SquareStack, brick: BrickWall };
const ENV_ICONS = { habitat: House, noon: Sun, night: Moon };
const SUPPORT = { measured: ['Lab-backed', FlaskConical], related: ['Related data', FlaskConical], physics: ['Physics estimate', Sigma] };

// Lighting per environment. The Moon has no air, so its noon sky is black and shadows are hard.
const LIGHTING = {
  habitat: { bg: ['#14284a', '#02040a'], key: [0xffffff, 2.2], hemi: 0.9, rim: 1.1 },
  noon: { bg: ['#0d0f14', '#000000'], key: [0xfff1dc, 3.8], hemi: 0.4, rim: 0.35 },
  night: { bg: ['#0a1838', '#000208'], key: [0x9ec0ff, 1.1], hemi: 0.6, rim: 2.4 },
};

function verdict(test) {
  const lo = test.failRange[0] / test.designLoad;
  if (test.safetyFactor < 1) return { tone: 'fail', text: 'Breaks before reaching the design load' };
  if (lo < 1) return { tone: 'warn', text: 'Holds on average, but not at the low end of the likely range: test it in the lab' };
  return { tone: 'pass', text: 'Holds the design load, even at the low end of the likely range' };
}

function mixColor(composition) {
  const [phiR] = volumeFractions(catalog, composition.regolith_wt, composition.fiber_wt, composition.binder, composition.regolith);
  const binder = MATRIX_COLORS[composition.binder];
  const soil = parseInt(catalog.regoliths[composition.regolith].color.slice(1), 16);
  const k = Math.min(0.85, phiR * 1.3);
  const ch = (c, s) => Math.round(((c >> s) & 255) * (1 - k) + ((soil >> s) & 255) * k);
  return (ch(binder, 16) << 16) | (ch(binder, 8) << 8) | ch(binder, 0);
}

let lastAppliedRequest = 0;

export default function PartTest({ engine, composition, request }) {
  const wrapRef = useRef(null);
  const mountRef = useRef(null);
  const stageRef = useRef(null);
  const sceneRef = useRef(null);
  const fillRef = useRef(null);
  const loadRef = useRef(null);
  const stressRef = useRef(null);
  const [partId, setPartId] = useState('wrench');
  const [envId, setEnvId] = useState('habitat');
  const [phase, setPhase] = useState('idle');
  const [designFlash, setDesignFlash] = useState(false);

  // Opened from a story: switch to the part and place it asked for (once, so a later tab switch keeps the user's choice).
  useEffect(() => {
    if (!request || request.n === lastAppliedRequest) return;
    lastAppliedRequest = request.n;
    if (PARTS[request.part]) setPartId(request.part);
    if (ENVIRONMENTS.some((e) => e.id === request.env)) setEnvId(request.env);
  }, [request]);

  const part = PARTS[partId];
  const env = ENVIRONMENTS.find((e) => e.id === envId);
  const test = useMemo(() => partTest(engine, part, composition, env.temperature), [engine, part, composition, env.temperature]);
  const color = mixColor(composition);
  const gaugeMax = Math.max(test.failRange[1], test.designLoad) * 1.06;
  const pct = (v) => `${Math.min(100, (v / gaugeMax) * 100)}%`;

  // Live readouts are written straight to the DOM every frame, so React does not re-render 60 times a second.
  const live = useRef({ gaugeMax, part });
  live.current = { gaugeMax, part };

  useEffect(() => {
    const stage = createStage(mountRef.current, { camera: [1.1, 1.2, 6.4], floorY: -1.3, floorRadius: 3.4, autoRotateSpeed: 0.35, minDistance: 1.5, maxDistance: 16 });
    stageRef.current = stage;
    let flashTimer = null;
    const hud = {
      set(f, t) {
        if (!t || !fillRef.current) return;
        const load = f * t.failLoad;
        fillRef.current.style.width = `${Math.min(100, (load / live.current.gaugeMax) * 100)}%`;
        const torque = live.current.part.id === 'wrench' ? ` · ${((load * PARTS.wrench.dims.hand) / 1000).toFixed(1)} N·m` : '';
        loadRef.current.textContent = `${formatForce(load)}${torque}`;
        stressRef.current.textContent = `${formatValue(t.stressAt(load), 'tensile_strength')} of ${formatValue(t.strength, 'tensile_strength')} MPa`;
      },
      flash(kind) {
        if (kind === 'design') {
          setDesignFlash(true);
          clearTimeout(flashTimer);
          flashTimer = setTimeout(() => setDesignFlash(false), 1800);
        }
      },
    };
    sceneRef.current = createPartScene(stage, { onPhase: setPhase, hud });
    return () => {
      clearTimeout(flashTimer);
      sceneRef.current.dispose();
      stage.dispose();
      sceneRef.current = null;
      stageRef.current = null;
    };
  }, []);

  useEffect(() => {
    sceneRef.current?.setTest(test, color);
  }, [test, color]);

  useEffect(() => {
    sceneRef.current?.setPart(partId);
  }, [partId]);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    const l = LIGHTING[envId];
    stage.setBackground(...l.bg);
    stage.lights.key.color.setHex(l.key[0]);
    stage.lights.key.intensity = l.key[1];
    stage.lights.hemi.intensity = l.hemi;
    stage.lights.rim.intensity = l.rim;
  }, [envId]);

  const v = verdict(test);
  const level = supportLevel(test.result.evidence?.[part.limit] ?? { same: 0, binder: 0 });
  const [supportLabel, SupportIcon] = SUPPORT[level];
  const strengthLabel = PROPERTY[part.limit].label.toLowerCase();
  const broken = phase === 'failed' || phase === 'done';

  return (
    <div className="part-test">
      <div className="viewer-wrap" ref={wrapRef}>
        <div className="viewer-stage">
          <div ref={mountRef} className="viewer viewer-3d viewer-tall" role="img" aria-label={`3D load test of a ${part.label.toLowerCase()} made of this mix`} />
          <div className="viewer-hud" aria-hidden="true">
            <span className="hud-kicker">
              Load test · {part.label}
            </span>
            <span>
              {part.test} · {env.label}, {env.temperature} °C
            </span>
          </div>
          <ViewerToolbar stageRef={stageRef} wrapRef={wrapRef} />
          {designFlash && !broken && <div className="part-banner pass">Design load held</div>}
          {broken && (
            <div className="part-banner fail" role="status">
              Broke at {formatForce(test.failLoad)}: like {formatMass(massEquivalent(test.failLoad))} on the Moon
            </div>
          )}
          <div className="load-gauge" aria-hidden="true">
            <div className="gauge-track">
              <span className="gauge-range" style={{ left: pct(test.failRange[0]), width: `calc(${pct(test.failRange[1])} - ${pct(test.failRange[0])})` }} />
              <span className="gauge-fill" ref={fillRef} />
              <span className="gauge-mark" style={{ left: pct(test.designLoad) }} />
            </div>
            <div className="gauge-labels">
              <span>
                Load <strong ref={loadRef}>0 N</strong>
              </span>
              <span>
                <span className="hide-sm">Peak stress </span>
                <strong ref={stressRef}>0</strong>
              </span>
            </div>
          </div>
        </div>

        <div className="part-controls">
          <div className="seg" role="radiogroup" aria-label="Part">
            {Object.values(PARTS).map((p) => {
              const Icon = PART_ICONS[p.id];
              return (
                <button key={p.id} type="button" role="radio" aria-checked={partId === p.id} className={partId === p.id ? 'active' : ''} onClick={() => setPartId(p.id)}>
                  <Icon size={14} aria-hidden="true" /> {p.label}
                </button>
              );
            })}
          </div>
          <div className="seg" role="radiogroup" aria-label="Where it is used">
            {ENVIRONMENTS.map((e) => {
              const Icon = ENV_ICONS[e.id];
              return (
                <button key={e.id} type="button" role="radio" aria-checked={envId === e.id} className={envId === e.id ? 'active' : ''} onClick={() => setEnvId(e.id)} title={`${e.label}, ${e.temperature} °C`}>
                  <Icon size={14} aria-hidden="true" /> {e.short} <small>{e.temperature} °C</small>
                </button>
              );
            })}
          </div>
          {phase === 'idle' ? (
            <button type="button" className="run-test" onClick={() => sceneRef.current?.run()}>
              <Hammer size={15} aria-hidden="true" /> Load it until it breaks
            </button>
          ) : (
            <button type="button" className="run-test secondary" onClick={() => sceneRef.current?.reset()}>
              <RotateCcw size={15} aria-hidden="true" /> {phase === 'loading' ? 'Stop' : 'Reset'}
            </button>
          )}
        </div>
      </div>

      <dl className="part-facts">
        <div>
          <dt>{PROPERTY[part.limit].label}</dt>
          <dd>
            {formatValue(test.strength, part.limit)} <span className="unit">MPa</span>
            <small>
              likely {formatValue(test.strengthRange[0], part.limit)}–{formatValue(test.strengthRange[1], part.limit)}
            </small>
            <span className={`support-chip support-${level} static`}>
              <SupportIcon size={11} aria-hidden="true" /> {supportLabel}
            </span>
          </dd>
        </div>
        <div>
          <dt>Breaks at</dt>
          <dd>
            {formatForce(test.failLoad)}
            <small>
              like {formatMass(massEquivalent(test.failLoad))} on the Moon ({formatMass(massEquivalent(test.failLoad, 'earth'))} on Earth) · likely {formatForce(test.failRange[0])}–{formatForce(test.failRange[1])}
            </small>
          </dd>
        </div>
        <div>
          <dt>Design load</dt>
          <dd>
            {formatForce(test.designLoad)}
            <small>{part.design.label}</small>
          </dd>
        </div>
        <div className={`sf-${v.tone}`}>
          <dt>Safety factor</dt>
          <dd>
            {formatFactor(test.safetyFactor)}
            <small>{v.text}</small>
          </dd>
        </div>
        <div>
          <dt>How it breaks</dt>
          <dd>
            {test.brittle ? 'Snaps suddenly' : 'Bends, then breaks'}
            <small>{formatValue(test.elongation, 'elongation_at_break')}% stretch before breaking</small>
          </dd>
        </div>
        {part.id === 'brick' && (
          <div>
            <dt>Tallest tower on the Moon</dt>
            <dd>
              {test.selfSupportKm.toFixed(1)} km
              <small>before a column of this material crushes its own base (buckling ignored)</small>
            </dd>
          </div>
        )}
      </dl>

      <div className="viewer-legend">
        <span className="stress-legend">
          Stress
          <i style={{ background: STRESS_GRADIENT }} />
          breaks
        </span>
        <span>
          <i className="swatch gauge-design" /> design load
        </span>
        <span>
          <i className="swatch gauge-likely" /> likely breaking range
        </span>
        <span className="viewer-hint">Drag: rotate · click, then scroll: zoom · right-drag: pan</span>
      </div>
      <p className="part-note">
        {part.why} Stress comes from textbook beam and column formulas applied to the model&apos;s predicted {strengthLabel} and stiffness at {env.temperature} °C. Bending is drawn exaggerated so it is visible, and falling pieces move at {Math.round(SLOW_MOTION * 100)}% speed under lunar gravity. Part sizes and design loads are stated assumptions; the material numbers are the model&apos;s.
      </p>
    </div>
  );
}
