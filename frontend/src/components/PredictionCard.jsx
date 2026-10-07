import { PROPERTIES, REGOLITHS, POLYMERS, formatNumber } from '../lib/materials';

function Delta({ value, base }) {
  if (!base) return null;
  const pct = ((value - base) / base) * 100;
  if (Math.abs(pct) < 0.5) return <span className="delta">same as pure polymer</span>;
  return (
    <span className={`delta ${pct > 0 ? 'up' : 'down'}`}>
      {pct > 0 ? '▲' : '▼'} {formatNumber(Math.abs(pct), 0)}% vs pure polymer
    </span>
  );
}

export default function PredictionCard({ result, baseline, status, error, regolithType, polymerType }) {
  const env = REGOLITHS[regolithType];

  return (
    <section className="card" aria-labelledby="predictions-title" aria-busy={status === 'loading'}>
      <div className="card-head">
        <h2 id="predictions-title">Predicted properties</h2>
        <span className={`status-dot ${status}`}>{status === 'loading' ? 'Updating' : status === 'error' ? 'Offline' : 'Live'}</span>
      </div>

      {error && !result && (
        <div className="empty-state" role="alert">
          <p>Can’t reach the prediction API.</p>
          <small>Start the backend with <code>uvicorn main:app --port 8000</code> and this panel updates on its own.</small>
        </div>
      )}

      {result && (
        <>
          <div className={`property-grid ${status === 'loading' ? 'is-stale' : ''}`}>
            {PROPERTIES.map((p) => (
              <article key={p.key} className="property">
                <p className="property-label">{p.label}</p>
                <p className="property-value">
                  {formatNumber(result.properties[p.key], p.unit === 'GPa' ? 2 : 1)}
                  <span className="unit">{p.unit}</span>
                </p>
                <p className="property-meta">
                  ± {formatNumber(result.uncertainty[p.key], p.unit === 'GPa' ? 2 : 1)} · {p.hint}
                </p>
                <Delta value={result.properties[p.key]} base={baseline?.properties[p.key]} />
              </article>
            ))}
          </div>

          <p className={`verdict ${result.survives_surface_max_temp ? 'ok' : 'warn'}`}>
            {result.survives_surface_max_temp
              ? `Holds its shape at ${env.place} (${env.maxTemp} °C).`
              : `Softens before ${env.place} (${env.maxTemp} °C): shield it from sunlight or try a higher-temperature polymer than ${POLYMERS[polymerType].label}.`}
          </p>
        </>
      )}
    </section>
  );
}
