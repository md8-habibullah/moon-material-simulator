import { useMemo } from 'react';
import { Bar, Scatter } from 'react-chartjs-2';
import { Atom, Cpu, Thermometer } from 'lucide-react';
import catalog, { PROPERTY, formatValue } from '../lib/catalog';
import { axis, baseOptions } from '../lib/charts';
import { useThemeColors } from '../lib/theme';

const FEATURE_LABELS = {
  regolith_wt: 'Regolith wt%',
  fiber_wt: 'Fibre wt%',
  particle_size: 'Grain size',
  phi_regolith: 'Regolith volume share',
  phi_fiber: 'Fibre volume share',
  bond: 'Grain–binder bond',
  reinforcement: 'Bond × volume',
  porosity: 'Porosity',
  grain_modulus: 'Grain stiffness',
  density_estimate: 'Density estimate',
};
const featureLabel = (f) =>
  FEATURE_LABELS[f] ??
  (f.startsWith('binder_') ? `Binder: ${catalog.binders[f.slice(7)].label}` : `Soil: ${catalog.regoliths[f.slice(9)]?.label ?? f}`);

const DATASETS = [
  { id: 'glenn', label: 'NASA Glenn · PHB (2026)', match: (v) => v.binder === 'PHB' },
  { id: 'kennedy', label: 'NASA Kennedy · PLA (2023)', match: (v) => v.binder === 'PLA' },
];

const STEPS = [
  { icon: Atom, title: 'Physics-informed features', text: 'Volume fractions, grain bond, porosity and density are computed from the mix, the same way in Python and in your browser.' },
  { icon: Cpu, title: 'Random Forest', text: `${catalog.model.params.n_estimators} decision trees predict room-temperature properties as ratios to the pure binder. Their spread is the ± band.` },
  { icon: Thermometer, title: 'Temperature physics', text: "NASA's measured 77 K ratios on the cold side; softening around the predicted service temperature on the hot side." },
];

export default function ModelInsight() {
  const colors = useThemeColors();
  const metrics = catalog.model.holdout_metrics;
  const validation = catalog.validation;

  const stats = useMemo(
    () =>
      DATASETS.map((d) => {
        const pts = validation.filter(d.match);
        return { ...d, count: pts.length, mae: pts.reduce((s, v) => s + Math.abs(v.error_pct), 0) / pts.length };
      }),
    [validation],
  );

  const importance = Object.entries(catalog.model.feature_importance)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  const importanceData = {
    labels: importance.map(([f]) => featureLabel(f)),
    datasets: [{ data: importance.map(([, v]) => v * 100), backgroundColor: colors.accent, borderRadius: 4, barThickness: 14 }],
  };
  const importanceOptions = {
    ...baseOptions(colors),
    indexAxis: 'y',
    scales: {
      x: axis(colors, { ticks: { color: colors.muted, callback: (v) => `${v}%` } }),
      y: axis(colors, { grid: { display: false } }),
    },
    plugins: { ...baseOptions(colors).plugins, tooltip: { ...baseOptions(colors).plugins.tooltip, callbacks: { label: (c) => `${c.parsed.x.toFixed(1)}% of splits` } } },
  };

  const parityData = {
    datasets: [
      {
        label: 'Perfect agreement',
        data: [
          { x: 3, y: 3 },
          { x: 400, y: 400 },
        ],
        showLine: true,
        borderColor: colors.grid,
        borderDash: [6, 6],
        borderWidth: 1.5,
        pointRadius: 0,
      },
      ...DATASETS.map((d, i) => ({
        label: d.label,
        data: validation.filter(d.match).map((v) => ({ x: v.measured, y: v.predicted, v })),
        backgroundColor: i === 0 ? colors.nasa : colors.series[1],
        pointRadius: 4.5,
        pointHoverRadius: 6,
        pointStyle: i === 0 ? 'rectRot' : 'circle',
      })),
    ],
  };
  const parityOptions = {
    ...baseOptions(colors),
    scales: {
      x: axis(colors, { type: 'logarithmic', min: 3, max: 400, title: { display: true, text: 'NASA measured', color: colors.muted }, ticks: { color: colors.muted, callback: (v) => ([5, 10, 20, 50, 100, 200].includes(v) ? v : '') } }),
      y: axis(colors, { type: 'logarithmic', min: 3, max: 400, title: { display: true, text: 'Model predicted', color: colors.muted }, ticks: { color: colors.muted, callback: (v) => ([5, 10, 20, 50, 100, 200].includes(v) ? v : '') } }),
    },
    plugins: {
      ...baseOptions(colors).plugins,
      legend: { display: true, position: 'bottom', labels: { color: colors.muted, usePointStyle: true, boxWidth: 8, filter: (item) => item.text !== 'Perfect agreement' } },
      tooltip: {
        ...baseOptions(colors).plugins.tooltip,
        filter: (item) => item.dataset.label !== 'Perfect agreement',
        callbacks: {
          title: (items) => {
            const v = items[0].raw.v;
            return `${PROPERTY[v.property].label} · ${v.simulant ?? 'neat'} ${v.regolith_wt} wt%${v.orientation ? ` · ${v.orientation}` : ''}`;
          },
          label: (item) => {
            const v = item.raw.v;
            const unit = catalog.units[v.property];
            return [`Measured ${formatValue(v.measured, v.property)} ${unit}`, `Model ${formatValue(v.predicted, v.property)} ${unit} (${v.error_pct > 0 ? '+' : ''}${v.error_pct}%)`, `${v.source} ${v.table}`];
          },
        },
      },
    },
  };

  return (
    <div className="science">
      <ol className="how-steps">
        {STEPS.map((s, i) => (
          <li key={s.title} className="card">
            <span className="step-index">{i + 1}</span>
            <s.icon size={20} aria-hidden="true" />
            <strong>{s.title}</strong>
            <p>{s.text}</p>
          </li>
        ))}
      </ol>

      <div className="section-grid science-grid">
        <div className="card">
          <div className="card-head compact">
            <h3>Checked against NASA measurements</h3>
          </div>
          <p className="card-sub">
            {validation.length} measured points from two NASA studies. Same mix in, model out. 0° and 90° print directions are plotted
            separately, so some scatter is the material itself.
          </p>
          <div className="stat-row compact">
            {stats.map((s) => (
              <div key={s.id} className="stat">
                <p className="stat-value">{s.mae.toFixed(0)}%</p>
                <p className="stat-label">
                  mean error · {s.label} ({s.count} pts)
                </p>
              </div>
            ))}
          </div>
          <div className="chart-box tall">
            <Scatter data={parityData} options={parityOptions} aria-label="Predicted versus NASA-measured values" role="img" />
          </div>
        </div>

        <div className="card">
          <div className="card-head compact">
            <h3>Hold-out accuracy</h3>
          </div>
          <p className="card-sub">R² on {Math.round(catalog.model.training_rows / 4).toLocaleString()} mixes the forest never saw. 1.00 is perfect.</p>
          <ul className="r2-list">
            {Object.entries(metrics).map(([k, m]) => (
              <li key={k}>
                <span>{PROPERTY[k].label}</span>
                <span className="bar">
                  <i style={{ width: `${Math.max(0, (m.r2 - 0.9) / 0.1) * 100}%` }} />
                </span>
                <strong>{m.r2.toFixed(3)}</strong>
              </li>
            ))}
          </ul>
          <div className="card-head compact spaced">
            <h3>What drives the predictions</h3>
          </div>
          <div className="chart-box">
            <Bar data={importanceData} options={importanceOptions} aria-label="Feature importance" role="img" />
          </div>
        </div>
      </div>
    </div>
  );
}
