import { useEffect, useMemo, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js';
import { compare } from '../lib/api';
import { POLYMERS, PROPERTIES, REGOLITHS, formatNumber } from '../lib/materials';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export const MAX_COMPARE = 4;
const SERIES_COLORS = ['#ff7a1a', '#3d8bff', '#1fbf8f', '#b06bff'];

export const describe = (c) =>
  `${c.regolith_wt}% ${REGOLITHS[c.regolith_type].label} + ${POLYMERS[c.polymer_type].label} @ ${c.temperature} °C`;

export default function ComparisonMode({ items, onRemove, onClear }) {
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (items.length === 0) {
      setResults([]);
      return undefined;
    }
    const controller = new AbortController();
    compare(
      items.map(({ id, ...c }) => c),
      controller.signal,
    )
      .then((data) => {
        setResults(data.results);
        setError(null);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') setError(err);
      });
    return () => controller.abort();
  }, [items]);

  // Units differ per property, so bars show each value as % of the best saved option.
  const chartData = useMemo(() => {
    const best = Object.fromEntries(PROPERTIES.map((p) => [p.key, Math.max(...results.map((r) => r.properties[p.key]))]));
    return {
      labels: PROPERTIES.map((p) => p.label),
      datasets: results.map((r, i) => ({
        label: describe(r.inputs),
        data: PROPERTIES.map((p) => (r.properties[p.key] / best[p.key]) * 100),
        raw: PROPERTIES.map((p) => `${formatNumber(r.properties[p.key], p.unit === 'GPa' ? 2 : 1)} ${p.unit}`),
        backgroundColor: SERIES_COLORS[i % SERIES_COLORS.length],
        borderRadius: 6,
        maxBarThickness: 36,
      })),
    };
  }, [results]);

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      scales: {
        y: { min: 0, max: 100, ticks: { callback: (v) => `${v}%`, color: '#8a94a6' }, grid: { color: 'rgba(138,148,166,0.15)' } },
        x: { ticks: { color: '#8a94a6' }, grid: { display: false } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.dataset.raw[ctx.dataIndex]}`,
          },
        },
      },
    }),
    [],
  );

  return (
    <section className="card comparison" aria-labelledby="compare-title">
      <div className="card-head">
        <div>
          <h2 id="compare-title">Comparison mode</h2>
          <p className="card-sub">Save up to {MAX_COMPARE} mixes and see which one wins each property.</p>
        </div>
        {items.length > 0 && (
          <button type="button" className="button button-ghost" onClick={onClear}>
            Clear all
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <p>No mixes saved yet.</p>
          <small>Tune a composition above and press “Add to comparison”.</small>
        </div>
      ) : (
        <>
          <ul className="compare-list">
            {items.map((c, i) => (
              <li key={c.id}>
                <span className="swatch" style={{ background: SERIES_COLORS[i % SERIES_COLORS.length] }} />
                <span>{describe(c)}</span>
                <button type="button" className="icon-button" onClick={() => onRemove(c.id)} aria-label={`Remove ${describe(c)}`}>
                  ×
                </button>
              </li>
            ))}
          </ul>
          {error && <p className="inline-error" role="alert">Couldn’t load the comparison. Is the API running?</p>}
          {results.length > 0 && (
            <>
              <div className="chart-wrap">
                <Bar data={chartData} options={options} aria-label="Bar chart comparing saved mixes" role="img" />
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Mix</th>
                      {PROPERTIES.map((p) => (
                        <th scope="col" key={p.key}>
                          {p.label} <span className="unit">{p.unit}</span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r, i) => (
                      <tr key={items[i]?.id ?? i}>
                        <th scope="row">
                          <span className="swatch" style={{ background: SERIES_COLORS[i % SERIES_COLORS.length] }} />
                          {describe(r.inputs)}
                        </th>
                        {PROPERTIES.map((p) => (
                          <td key={p.key}>{formatNumber(r.properties[p.key], p.unit === 'GPa' ? 2 : 1)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}
