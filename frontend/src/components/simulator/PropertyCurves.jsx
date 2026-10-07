import { useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';
import catalog, { LOADING_ZONES, PROPERTY, formatValue } from '../../lib/catalog';
import { axis, baseOptions } from '../../lib/charts';
import { useThemeColors } from '../../lib/theme';

const WT_STEPS = Array.from({ length: 41 }, (_, i) => i * 2);
const CURVE_KEYS = ['tensile_strength', 'elastic_modulus', 'compressive_strength', 'elongation_at_break', 'max_service_temp', 'decomposition_temp', 'density'];

// Shades the "tools" and "structures" loading zones from the pitch behind the curve.
const zonesPlugin = {
  id: 'zones',
  beforeDatasetsDraw(chart, _args, opts) {
    const { ctx, chartArea, scales } = chart;
    ctx.save();
    for (const z of LOADING_ZONES) {
      const x0 = scales.x.getPixelForValue(z.from);
      const x1 = scales.x.getPixelForValue(z.to);
      ctx.fillStyle = opts.fill;
      ctx.fillRect(x0, chartArea.top, x1 - x0, chartArea.bottom - chartArea.top);
      ctx.fillStyle = opts.label;
      ctx.font = '600 10px "Space Grotesk", system-ui';
      ctx.fillText(z.label.toUpperCase(), x0 + 6, chartArea.top + 14);
    }
    ctx.restore();
  },
};

export default function PropertyCurves({ engine, composition }) {
  const colors = useThemeColors();
  const [key, setKey] = useState('tensile_strength');

  const curve = useMemo(() => {
    const maxWt = catalog.physics.max_total_filler_wt - composition.fiber_wt;
    return WT_STEPS.filter((w) => w <= maxWt).map((w) => {
      const r = engine.predict({ ...composition, regolith_wt: w });
      return { x: w, y: r.properties[key], sd: r.uncertainty[key] };
    });
  }, [engine, composition, key]);

  // NASA measurements for this binder and property (at room temperature).
  const nasa = useMemo(
    () =>
      catalog.validation.filter((v) => v.binder === composition.binder && v.property === key && v.temperature === 23),
    [composition.binder, key],
  );
  const current = engine.predict(composition).properties[key];
  const unit = catalog.units[key];

  const data = {
    datasets: [
      { label: 'Upper band', data: curve.map((p) => ({ x: p.x, y: p.y + p.sd })), borderWidth: 0, pointRadius: 0, fill: '+1', backgroundColor: colors.accentSoft },
      { label: 'Lower band', data: curve.map((p) => ({ x: p.x, y: Math.max(0, p.y - p.sd) })), borderWidth: 0, pointRadius: 0, fill: false },
      { label: 'Model', data: curve.map((p) => ({ x: p.x, y: p.y })), borderColor: colors.accent, borderWidth: 2.5, pointRadius: 0, tension: 0.3 },
      {
        label: 'NASA measured',
        data: nasa.map((v) => ({ x: v.regolith_wt, y: v.measured, source: `${v.source} ${v.table}${v.simulant ? ` · ${v.simulant}` : ''}${v.orientation ? ` · ${v.orientation}` : ''}` })),
        showLine: false,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointStyle: 'rectRot',
        backgroundColor: colors.nasa,
        borderColor: colors.surface,
        borderWidth: 1.5,
      },
      {
        label: 'Your mix',
        data: [{ x: composition.regolith_wt, y: current }],
        showLine: false,
        pointRadius: 7,
        pointHoverRadius: 8,
        backgroundColor: colors.accent,
        borderColor: colors.surface,
        borderWidth: 3,
      },
    ],
  };

  const options = {
    ...baseOptions(colors),
    parsing: false,
    interaction: { mode: 'nearest', intersect: false },
    scales: {
      x: axis(colors, { type: 'linear', min: 0, max: 80, title: { display: true, text: 'Regolith (wt%)', color: colors.muted } }),
      y: axis(colors, { beginAtZero: key !== 'decomposition_temp' && key !== 'max_service_temp', title: { display: true, text: unit, color: colors.muted } }),
    },
    plugins: {
      ...baseOptions(colors).plugins,
      zones: { fill: colors.zone, label: colors.muted },
      tooltip: {
        ...baseOptions(colors).plugins.tooltip,
        filter: (item) => !item.dataset.label.endsWith('band'),
        callbacks: {
          title: (items) => `${items[0].parsed.x} wt% regolith`,
          label: (item) => {
            const base = `${item.dataset.label}: ${formatValue(item.parsed.y, key)} ${unit}`;
            return item.raw.source ? [base, item.raw.source] : base;
          },
        },
      },
    },
  };

  return (
    <div className="viewer-wrap">
      <div className="curve-tabs" role="tablist" aria-label="Property to plot">
        {CURVE_KEYS.map((k) => (
          <button key={k} type="button" role="tab" aria-selected={k === key} className={`chip-button ${k === key ? 'active' : ''}`} onClick={() => setKey(k)}>
            {PROPERTY[k].short}
          </button>
        ))}
      </div>
      <div className="curve-chart">
        <Line data={data} options={options} plugins={[zonesPlugin]} aria-label={`${PROPERTY[key].label} versus regolith content`} role="img" />
      </div>
      <div className="viewer-legend">
        <span>
          <i className="swatch line" style={{ background: colors.accent }} />
          Model ± spread across trees, at {composition.temperature} °C
        </span>
        {nasa.length > 0 && (
          <span>
            <i className="swatch diamond" style={{ background: colors.nasa }} />
            NASA measured ({nasa.length}, at 23 °C)
          </span>
        )}
        {nasa.length === 0 && <span className="viewer-hint">No NASA measurement for this binder and property yet</span>}
      </div>
    </div>
  );
}
