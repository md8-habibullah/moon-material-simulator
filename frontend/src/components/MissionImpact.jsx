import { useId, useState } from 'react';
import { Rocket, Scale } from 'lucide-react';
import catalog, { describeMix } from '../lib/catalog';
import { missionImpact } from '../lib/engine/mission';

const COST_PRESETS = [
  { label: '$4,000 / kg · low end', value: 4000 },
  { label: '$1M / kg · high end', value: 1000000 },
];

const money = (v) => v.toLocaleString('en-US', { style: 'currency', currency: 'USD', notation: v >= 1e6 ? 'compact' : 'standard', maximumFractionDigits: v >= 1e6 ? 2 : 0 });
const kg = (v) => `${v.toLocaleString('en-US', { maximumFractionDigits: v < 10 ? 2 : 1 })} kg`;

function NumberField({ label, value, onChange, min, max, step, suffix }) {
  const id = useId();
  return (
    <div className="number-field">
      <label htmlFor={id}>{label}</label>
      <div className="input-affix">
        <input id={id} type="number" inputMode="decimal" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Math.min(max, Math.max(min, Number(e.target.value) || 0)))} />
        {suffix && <span>{suffix}</span>}
      </div>
    </div>
  );
}

export default function MissionImpact({ composition }) {
  const [partMassKg, setPartMass] = useState(0.4);
  const [quantity, setQuantity] = useState(25);
  const [costPerKg, setCost] = useState(1000000);
  const [growBinderOnSite, setGrow] = useState(true);
  const [drawFibreOnSite, setFibre] = useState(true);
  const binder = catalog.binders[composition.binder];
  const r = missionImpact(catalog, composition, { partMassKg, quantity, growBinderOnSite, drawFibreOnSite, costPerKg });

  return (
    <div className="section-grid impact">
      <div className="card impact-inputs">
        <p className="group-label">Your part</p>
        <p className="impact-mix">{describeMix(composition)}</p>
        <div className="number-row">
          <NumberField label="Mass per part" value={partMassKg} onChange={setPartMass} min={0.01} max={5000} step={0.1} suffix="kg" />
          <NumberField label="How many" value={quantity} onChange={setQuantity} min={1} max={100000} step={1} />
        </div>
        <p className="group-label">Delivered cost to the surface</p>
        <div className="presets" role="group" aria-label="Launch cost presets">
          {COST_PRESETS.map((p) => (
            <button key={p.value} type="button" className={`chip-button ${costPerKg === p.value ? 'active' : ''}`} aria-pressed={costPerKg === p.value} onClick={() => setCost(p.value)}>
              {p.label}
            </button>
          ))}
        </div>
        <NumberField label="Custom" value={costPerKg} onChange={setCost} min={0} max={10000000} step={1000} suffix="$/kg" />
        <label className={`toggle ${binder.made_on_site ? '' : 'disabled'}`}>
          <input type="checkbox" checked={binder.made_on_site && growBinderOnSite} disabled={!binder.made_on_site} onChange={(e) => setGrow(e.target.checked)} />
          <span className="toggle-ui" aria-hidden="true" />
          Grow the bioplastic on site {binder.made_on_site ? '' : `(not possible for ${binder.label})`}
        </label>
        <label className="toggle">
          <input type="checkbox" checked={drawFibreOnSite} onChange={(e) => setFibre(e.target.checked)} />
          <span className="toggle-ui" aria-hidden="true" />
          Draw basalt fibre on site
        </label>
      </div>

      <div className="card impact-results" aria-live="polite">
        <div className="stat-row">
          <div className="stat">
            <Scale size={18} aria-hidden="true" />
            <p className="stat-value">{kg(r.savedKg)}</p>
            <p className="stat-label">launch mass avoided</p>
          </div>
          <div className="stat">
            <Rocket size={18} aria-hidden="true" />
            <p className="stat-value">{Math.round(r.savedShare * 100)}%</p>
            <p className="stat-label">less mass shipped vs finished spares</p>
          </div>
          <div className="stat stat-accent">
            <p className="stat-value">{money(r.savedCost)}</p>
            <p className="stat-label">delivery cost avoided</p>
          </div>
        </div>

        <p className="group-label">Where the material comes from</p>
        <div className="source-bar" role="img" aria-label={r.breakdown.map((b) => `${b.label} ${Math.round(b.share * 100)}% ${b.local ? 'local' : 'from Earth'}`).join(', ')}>
          {r.breakdown.map((b) => (
            <span key={b.key} className={b.local ? 'local' : 'earth'} style={{ flexGrow: b.share }}>
              {b.share > 0.08 && `${b.label} ${Math.round(b.share * 100)}%`}
            </span>
          ))}
        </div>
        <div className="source-legend">
          <span>
            <i className="swatch local" /> Made on site
          </span>
          <span>
            <i className="swatch earth" /> Shipped from Earth: {kg(r.shippedKg)} ({money(r.shippedCost)})
          </span>
        </div>
        <p className="footnote">
          NASA Glenn puts payload launch prices at “$4,000 to more than $1 million per kg” (NTRS 20260007758). Pick the end that
          matches your destination. Excludes the printer, bioreactor and starter culture, which ship once and are reused.
        </p>
      </div>
    </div>
  );
}
