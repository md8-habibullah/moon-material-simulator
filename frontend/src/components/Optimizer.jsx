import { useEffect, useState } from 'react';
import { ArrowRight, Sparkles, TriangleAlert } from 'lucide-react';
import catalog, { PROPERTY, describeMix, formatValue } from '../lib/catalog';
import { optimize } from '../lib/engine/optimizer';
import { APP_ICONS } from './simulator/OutputPanel';

function Requirement({ name, rule }) {
  const unit = catalog.units[name];
  return (
    <li className="tag">
      {PROPERTY[name].short} {rule.min !== undefined ? `≥ ${rule.min}` : `≤ ${rule.max}`} {unit}
    </li>
  );
}

export default function Optimizer({ engine, onApply }) {
  const [appId, setAppId] = useState('wrench');
  const [localOnly, setLocalOnly] = useState(false);
  const [state, setState] = useState({ status: 'running', result: null });
  const app = catalog.applications.find((a) => a.id === appId);

  useEffect(() => {
    setState((s) => ({ ...s, status: 'running' }));
    // Let the "searching" state paint before the ~2,400-mix search runs.
    const timer = setTimeout(() => {
      const binders = localOnly ? Object.keys(catalog.binders).filter((b) => catalog.binders[b].made_on_site) : undefined;
      setState({ status: 'done', result: optimize(engine, catalog, app, { binders }) });
    }, 30);
    return () => clearTimeout(timer);
  }, [engine, app, localOnly]);

  const result = state.result;
  const apply = (composition) => onApply({ ...composition, temperature: app.temps[app.temps.length - 1] });

  return (
    <div className="section-grid optimizer">
      <div className="card app-picker" role="radiogroup" aria-label="What are you building?">
        <p className="group-label">What are you building?</p>
        {catalog.applications.map((a) => {
          const Icon = APP_ICONS[a.icon];
          return (
            <button key={a.id} type="button" role="radio" aria-checked={a.id === appId} className={`app-option ${a.id === appId ? 'active' : ''}`} onClick={() => setAppId(a.id)}>
              <span className="app-icon">
                <Icon size={18} aria-hidden="true" />
              </span>
              <span>
                <strong>{a.label}</strong>
                <small>{a.where}</small>
              </span>
            </button>
          );
        })}
        <label className="toggle">
          <input type="checkbox" checked={localOnly} onChange={(e) => setLocalOnly(e.target.checked)} />
          <span className="toggle-ui" aria-hidden="true" />
          Only binders we can grow on site
        </label>
      </div>

      <div className="card optimizer-results" aria-live="polite" aria-busy={state.status === 'running'}>
        <div className="card-head">
          <div>
            <p className="kicker">Step 3 · Optimize</p>
            <h3>{app.label}</h3>
            <p className="card-sub">{app.summary}</p>
          </div>
        </div>
        <ul className="tag-row">
          {Object.entries(app.requirements).map(([k, rule]) => (
            <Requirement key={k} name={k} rule={rule} />
          ))}
          <li className="tag tag-muted">at {app.temps.map((t) => `${t} °C`).join(' and ')}</li>
        </ul>

        {!result || state.status === 'running' ? (
          <div className="skeleton-list" aria-label="Searching mixes">
            {[0, 1, 2].map((i) => (
              <div key={i} className="skeleton skeleton-row" />
            ))}
          </div>
        ) : result.feasible.length > 0 ? (
          <>
            <p className="result-summary">
              <Sparkles size={16} aria-hidden="true" />
              {result.feasibleCount} of {result.evaluated.toLocaleString()} mixes pass. Best options, most locally sourced first:
            </p>
            <ol className="ranked">
              {result.feasible.map((c, i) => (
                <li key={describeMix(c.composition) + i}>
                  <span className="rank">{i + 1}</span>
                  <div className="ranked-main">
                    <strong>{describeMix(c.composition)}</strong>
                    <small>
                      {c.composition.particle_size} µm grains · {Math.round(c.inSitu * 100)}% local · tightest margin +{(c.margin * 100).toFixed(0)}% on{' '}
                      {PROPERTY[c.worst.key].label.toLowerCase()}
                    </small>
                    <span className="ranked-values">
                      {Object.keys(app.requirements).map((k) => {
                        const check = c.checks.filter((x) => x.key === k).reduce((a, b) => (b.slack < a.slack ? b : a));
                        return (
                          <span key={k}>
                            {PROPERTY[k].short} <b>{formatValue(check.value, k)}</b> {catalog.units[k]}
                          </span>
                        );
                      })}
                    </span>
                  </div>
                  <button type="button" className="button button-small" onClick={() => apply(c.composition)}>
                    Load <ArrowRight size={14} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ol>
          </>
        ) : (
          <div className="infeasible" role="status">
            <p>
              <TriangleAlert size={18} aria-hidden="true" />
              <strong>No mix meets this.</strong> Searched {result.evaluated.toLocaleString()} compositions.
            </p>
            {app.infeasible_note && <p>{app.infeasible_note}</p>}
            {result.nearest.length > 0 && (
              <>
                <p className="group-label">Closest misses</p>
                <ul className="nearest">
                  {result.nearest.map((c) => (
                    <li key={describeMix(c.composition)}>
                      <span>{describeMix(c.composition)}</span>
                      <small>
                        {PROPERTY[c.worst.key].label}: {formatValue(c.worst.value, c.worst.key)} {catalog.units[c.worst.key]} (needs{' '}
                        {c.worst.kind === 'min' ? '≥' : '≤'} {c.worst.limit})
                      </small>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
