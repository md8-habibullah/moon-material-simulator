import { useMemo } from 'react';
import { Radar } from 'react-chartjs-2';
import { Download, Trash2, X } from 'lucide-react';
import catalog, { PROPERTIES, describeMix, formatValue } from '../lib/catalog';
import { baseOptions } from '../lib/charts';
import { useThemeColors } from '../lib/theme';

export const MAX_COMPARE = 4;
const LETTERS = ['A', 'B', 'C', 'D'];

function toCsv(rows) {
  const header = ['formula', 'binder', 'regolith', 'regolith_wt', 'fiber_wt', 'particle_size_um', 'temperature_c', 'in_situ_pct', ...PROPERTIES.map((p) => `${p.key} (${catalog.units[p.key]})`)];
  const lines = rows.map(({ letter, item, result }) =>
    [letter, item.binder, item.regolith, item.regolith_wt, item.fiber_wt, item.particle_size, item.temperature, Math.round(result.in_situ_fraction * 100), ...PROPERTIES.map((p) => result.properties[p.key].toFixed(4))].join(','),
  );
  return [header.join(','), ...lines].join('\n');
}

export default function ComparisonMode({ engine, items, onRemove, onClear, onLoad }) {
  const colors = useThemeColors();
  const rows = useMemo(
    () => items.map((item, i) => ({ letter: LETTERS[i], item, result: engine.predict(item), color: colors.series[i] })),
    [engine, items, colors.series],
  );

  // Who wins each property ("neutral" ones like density have no winner).
  const winners = useMemo(() => {
    const out = {};
    if (rows.length < 2) return out;
    for (const p of PROPERTIES) {
      if (p.better === 'neutral') continue;
      out[p.key] = rows.reduce((a, b) => (b.result.properties[p.key] > a.result.properties[p.key] ? b : a)).letter;
    }
    return out;
  }, [rows]);

  const radarKeys = PROPERTIES.filter((p) => p.better !== 'neutral');
  const radarData = {
    labels: radarKeys.map((p) => p.short),
    datasets: rows.map((r) => ({
      label: `Formula ${r.letter}`,
      data: radarKeys.map((p) => {
        const best = Math.max(...rows.map((x) => x.result.properties[p.key]));
        return (r.result.properties[p.key] / best) * 100;
      }),
      raw: radarKeys.map((p) => `${formatValue(r.result.properties[p.key], p.key)} ${catalog.units[p.key]}`),
      borderColor: r.color,
      backgroundColor: `${r.color}26`,
      pointBackgroundColor: r.color,
      borderWidth: 2,
      pointRadius: 3,
    })),
  };
  const radarOptions = {
    ...baseOptions(colors),
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: { display: false, stepSize: 25 },
        grid: { color: colors.grid },
        angleLines: { color: colors.grid },
        pointLabels: { color: colors.muted, font: { size: 11 } },
      },
    },
    plugins: {
      ...baseOptions(colors).plugins,
      tooltip: { ...baseOptions(colors).plugins.tooltip, callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.dataset.raw[ctx.dataIndex]}` } },
    },
  };

  const downloadCsv = () => {
    const blob = new Blob([toCsv(rows)], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement('a'), { href: url, download: 'moon-material-comparison.csv' });
    a.click();
    URL.revokeObjectURL(url);
  };

  if (items.length === 0) {
    return (
      <div className="card empty-state">
        <p>No formulas saved yet.</p>
        <small>Design a mix in the simulator and press “Save to compare”. Save up to {MAX_COMPARE} to see them side by side.</small>
      </div>
    );
  }

  return (
    <div className="card comparison">
      <div className="card-head">
        <div>
          <h3>
            {rows.length} formula{rows.length > 1 ? 's' : ''} side by side
          </h3>
          <p className="card-sub">Radar shows each value as % of the best saved formula; the table has the exact numbers.</p>
        </div>
        <div className="head-actions">
          <button type="button" className="button button-ghost button-small" onClick={downloadCsv}>
            <Download size={14} aria-hidden="true" /> CSV
          </button>
          <button type="button" className="button button-ghost button-small" onClick={onClear}>
            <Trash2 size={14} aria-hidden="true" /> Clear
          </button>
        </div>
      </div>

      <div className="formula-cards">
        {rows.map((r) => {
          const wins = Object.entries(winners).filter(([, l]) => l === r.letter).map(([k]) => PROPERTIES.find((p) => p.key === k).short);
          return (
            <article key={r.item.id} className="formula" style={{ '--formula': r.color }}>
              <header>
                <span className="formula-letter">{r.letter}</span>
                <button type="button" className="icon-button" onClick={() => onRemove(r.item.id)} aria-label={`Remove formula ${r.letter}`}>
                  <X size={14} />
                </button>
              </header>
              <button type="button" className="formula-name" onClick={() => onLoad(r.item)} title="Load into the simulator">
                {describeMix(r.item)}
              </button>
              <small>
                {r.item.particle_size} µm · {r.item.temperature} °C · {Math.round(r.result.in_situ_fraction * 100)}% local
              </small>
              {wins.length > 0 && <p className="wins">Best: {wins.join(', ')}</p>}
            </article>
          );
        })}
      </div>

      {rows.length > 1 && (
        <div className="radar-wrap">
          <Radar data={radarData} options={radarOptions} aria-label="Radar chart comparing saved formulas" role="img" />
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Property</th>
              {rows.map((r) => (
                <th scope="col" key={r.item.id}>
                  <span className="swatch" style={{ background: r.color }} /> {r.letter}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PROPERTIES.map((p) => (
              <tr key={p.key}>
                <th scope="row">
                  {p.label} <span className="unit">{catalog.units[p.key]}</span>
                </th>
                {rows.map((r) => (
                  <td key={r.item.id} className={winners[p.key] === r.letter ? 'winner' : ''}>
                    {formatValue(r.result.properties[p.key], p.key)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
