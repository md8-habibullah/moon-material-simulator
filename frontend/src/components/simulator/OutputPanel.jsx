import { useMemo } from 'react';
import { Armchair, BrickWall, CircleCheck, CircleX, Flame, PanelsTopLeft, SquareStack, Wrench } from 'lucide-react';
import catalog, { PROPERTIES, PROPERTY, formatValue } from '../../lib/catalog';
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

export default function OutputPanel({ engine, composition, result, baseline }) {
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
        <span className="chip chip-accent" title={`Random Forest with ${engine.treeCount} trees, running in your browser`}>
          <span className="pulse" aria-hidden="true" />
          Live · {engine.treeCount} trees
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
            <p className="property-meta">± {formatValue(result.uncertainty[p.key], p.key)}</p>
            <Delta value={result.properties[p.key]} base={baseline?.properties[p.key]} better={p.better} />
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
