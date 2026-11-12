import { useMemo, useState } from 'react';
import { Armchair, BrickWall, CircleCheck, CircleX, FlaskConical, Flame, PanelsTopLeft, Sigma, SquareStack, Wrench } from 'lucide-react';
import EvidenceDrawer from './EvidenceDrawer';
import { supportLevel } from '../../lib/engine/evidence';
import catalog, { PROPERTIES, PROPERTY, formatSpread, formatValue } from '../../lib/catalog';
import { evaluate } from '../../lib/engine/optimizer';
import { porosity, volumeFractions } from '../../lib/engine/physics';

export const APP_ICONS = { wrench: Wrench, bracket: SquareStack, chair: Armchair, panel: PanelsTopLeft, block: BrickWall, flame: Flame };

function Delta({ value, base, better }) {
  if (!base) return null;
  const pct = ((value - base) / base) * 100;
  if (Math.abs(pct) < 1) return <span className="delta">≈ pure binder</span>;
  const tone = better === 'neutral' ? '' : (pct > 0) === (better === 'higher') ? 'up' : 'down';
  return (
    <span className={`delta ${tone}`}>
      {pct > 0 ? '▲' : '▼'} {Math.abs(pct).toFixed(0)}% vs pure
    </span>
  );
}

function CompositionDonut({ composition }) {
  const regolith = catalog.regoliths[composition.regolith];
  const [phiR, phiF] = volumeFractions(catalog, composition.regolith_wt, composition.fiber_wt, composition.binder, composition.regolith);
  const voids = porosity(catalog.physics, phiR + phiF, regolith.void_factor);
  const solid = 1 - voids;
  const parts = [
    { label: catalog.binders[composition.binder].label, value: (1 - phiR - phiF) * solid, color: 'var(--binder-color)' },
    { label: 'Regolith', value: phiR * solid, color: regolith.color },
    { label: 'Basalt fibre', value: phiF * solid, color: '#4b525c' },
    { label: 'Voids', value: voids, color: 'var(--void-color)' },
  ].filter((p) => p.value > 0.0005);

  let acc = 0;
  const stops = parts.map((p) => {
    const from = acc * 360;
    acc += p.value;
    return `${p.color} ${from}deg ${acc * 360}deg`;
  });

  return (
    <div className="donut-row">
      <div className="donut" style={{ background: `conic-gradient(${stops.join(', ')})` }} role="img" aria-label={`Composition by volume: ${parts.map((p) => `${p.label} ${(p.value * 100).toFixed(1)}%`).join(', ')}`}>
        <span>
          <strong>{Math.round(composition.regolith_wt + composition.fiber_wt)}%</strong>
          <small>filler wt</small>
        </span>
      </div>
      <ul className="donut-legend">
        {parts.map((p) => (
          <li key={p.label}>
            <i className="swatch" style={{ background: p.color }} />
            <span>{p.label}</span>
            <strong>{(p.value * 100).toFixed(1)}%</strong>
          </li>
        ))}
        <li className="legend-note">by volume</li>
      </ul>
    </div>
  );
}

const SUPPORT = {
  measured: { label: 'Lab-backed', icon: FlaskConical },
  related: { label: 'Related data', icon: FlaskConical },
  physics: { label: 'Physics estimate', icon: Sigma },
};

export default function OutputPanel({ engine, composition, result, baseline }) {
  const [evidenceFor, setEvidenceFor] = useState(null);
  const fits = useMemo(
    () => catalog.applications.map((app) => ({ app, ...evaluate(engine, app, composition) })),
    [engine, composition],
  );
  const regolith = catalog.regoliths[composition.regolith];

  return (
    <section className="card output-card" aria-labelledby="output-title" aria-live="polite">
      <div className="card-head">
        <div>
          <p className="kicker">Results</p>
          <h2 id="output-title">Simulation output</h2>
        </div>
        <span className="chip chip-accent" title={`Physics emulated by a ${engine.treeCount}-tree Random Forest, corrected by a Gaussian process trained on real lab measurements; all in your browser`}>
          <span className="pulse" aria-hidden="true" />
          Live · physics + lab data
        </span>
      </div>

      <CompositionDonut composition={composition} />

      <div className="in-situ">
        <div>
          <p className="in-situ-value">{Math.round(result.in_situ_fraction * 100)}%</p>
          <p className="in-situ-label">of this part can be made from local resources</p>
        </div>
        <div className="meter" aria-hidden="true">
          <span style={{ width: `${result.in_situ_fraction * 100}%` }} />
        </div>
      </div>

      <div className="property-grid">
        {PROPERTIES.map((p) => (
          <article key={p.key} className="property">
            <p className="property-label" title={p.hint}>
              {p.label}
            </p>
            <p className="property-value">
              {formatValue(result.properties[p.key], p.key)}
              <span className="unit">{catalog.units[p.key]}</span>
            </p>
            <p className="property-meta" title="About 68% likely range (model spread plus the error measured on real lab data)">
              {formatSpread(result, p.key)}
            </p>
            <Delta value={result.properties[p.key]} base={baseline?.properties[p.key]} better={p.better} />
            {(() => {
              const level = supportLevel(result.evidence?.[p.key] ?? { same: 0, binder: 0 });
              const S = SUPPORT[level];
              return (
                <button type="button" className={`support-chip support-${level}`} onClick={() => setEvidenceFor(p.key)} aria-label={`${S.label}: see the lab evidence for ${p.label}`}>
                  <S.icon size={11} aria-hidden="true" /> {S.label}
                </button>
              );
            })()}
          </article>
        ))}
      </div>

      <div className="fit-block">
        <p className="group-label">Fit for use at {composition.regolith_wt}% regolith</p>
        <ul className="fit-list">
          {fits.map(({ app, pass, worst }) => {
            const Icon = APP_ICONS[app.icon] ?? Wrench;
            const why = pass
              ? `Meets every requirement (closest: ${PROPERTY[worst.key].label.toLowerCase()})`
              : `${PROPERTY[worst.key].label} ${formatValue(worst.value, worst.key)} ${catalog.units[worst.key]} at ${worst.temperature} °C; needs ${worst.kind === 'min' ? '≥' : '≤'} ${worst.limit}`;
            return (
              <li key={app.id} className={pass ? 'pass' : 'fail'} title={why}>
                <Icon size={15} aria-hidden="true" />
                <span>{app.label}</span>
                {pass ? <CircleCheck size={15} aria-label="passes" /> : <CircleX size={15} aria-label="fails" />}
                <small>{why}</small>
              </li>
            );
          })}
        </ul>
      </div>

      <EvidenceDrawer propertyKey={evidenceFor} composition={composition} result={result} onClose={() => setEvidenceFor(null)} />

      <div className="oxides">
        <p className="group-label">
          {regolith.label} oxide profile <span className="muted-small">approx. wt%</span>
        </p>
        <ul>
          {Object.entries(regolith.oxides).map(([name, value]) => (
            <li key={name}>
              <span>{name}</span>
              <span className="bar">
                <i style={{ width: `${value * 2}%` }} />
              </span>
              <strong>{value}</strong>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
