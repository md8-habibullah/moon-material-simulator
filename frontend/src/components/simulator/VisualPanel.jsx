import { Suspense, lazy, useId, useState } from 'react';
import { Box, ChartLine, Microscope } from 'lucide-react';
import Micrograph from './Micrograph';
import PropertyCurves from './PropertyCurves';
import catalog from '../../lib/catalog';
import { volumeFractions } from '../../lib/engine/physics';

// three.js is the heaviest dependency, so the 3D tab loads on demand.
const ThreeDViewer = lazy(() => import('./ThreeDViewer'));

const TABS = [
  { id: '3d', label: '3D structure', icon: Box },
  { id: 'micro', label: 'Polarised light', icon: Microscope },
  { id: 'curves', label: 'Property curves', icon: ChartLine },
];

export default function VisualPanel({ engine, composition }) {
  const [tab, setTab] = useState('3d');
  const baseId = useId();
  const [phiR, phiF] = volumeFractions(catalog, composition.regolith_wt, composition.fiber_wt, composition.binder, composition.regolith);

  return (
    <section className="card visual-card" aria-labelledby={`${baseId}-title`}>
      <div className="card-head">
        <div>
          <p className="kicker">Step 2 · Test</p>
          <h2 id={`${baseId}-title`}>Microstructure</h2>
        </div>
        <span className="chip">{((phiR + phiF) * 100).toFixed(1)}% filler by volume</span>
      </div>

      <div className="tabs" role="tablist" aria-label="Visualisation">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            id={`${baseId}-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls={`${baseId}-panel`}
            className={`tab ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            <t.icon size={15} aria-hidden="true" />
            {t.label}
          </button>
        ))}
      </div>

      <div id={`${baseId}-panel`} role="tabpanel" aria-labelledby={`${baseId}-${tab}`} className="tab-panel">
        {tab === '3d' && (
          <Suspense fallback={<div className="viewer skeleton" aria-busy="true" />}>
            <ThreeDViewer composition={composition} />
          </Suspense>
        )}
        {tab === 'micro' && <Micrograph composition={composition} />}
        {tab === 'curves' && <PropertyCurves engine={engine} composition={composition} />}
      </div>
    </section>
  );
}
