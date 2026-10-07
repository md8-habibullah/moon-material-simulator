import { Suspense, lazy, useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import SliderControl, { SegmentedControl } from './components/SliderControl';
import PredictionCard from './components/PredictionCard';
import ComparisonMode, { MAX_COMPARE } from './components/ComparisonMode';
import { compare, getModelInfo } from './lib/api';
import { POLYMERS, REGOLITHS, TEMPERATURE_PRESETS, formatNumber } from './lib/materials';

// three.js is most of the bundle; load it after the first paint.
const ThreeDViewer = lazy(() => import('./components/ThreeDViewer'));

const DEBOUNCE_MS = 200;

export default function App() {
  const [regolithWt, setRegolithWt] = useState(30);
  const [regolithType, setRegolithType] = useState('lunar');
  const [polymerType, setPolymerType] = useState('PLA');
  const [temperature, setTemperature] = useState(23);

  const [prediction, setPrediction] = useState({ result: null, baseline: null, status: 'loading', error: null });
  const [saved, setSaved] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);

  const composition = { regolith_wt: regolithWt, regolith_type: regolithType, polymer_type: polymerType, temperature };

  // One request returns the current mix and the same polymer with no regolith, for the "vs pure" deltas.
  useEffect(() => {
    const controller = new AbortController();
    setPrediction((p) => ({ ...p, status: 'loading' }));
    const timer = setTimeout(() => {
      compare([composition, { ...composition, regolith_wt: 0 }], controller.signal)
        .then(({ results: [result, baseline] }) => setPrediction({ result, baseline, status: 'ready', error: null }))
        .catch((error) => {
          if (error.name !== 'AbortError') setPrediction((p) => ({ ...p, status: 'error', error }));
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [regolithWt, regolithType, polymerType, temperature]);

  useEffect(() => {
    const controller = new AbortController();
    getModelInfo(controller.signal)
      .then(setModelInfo)
      .catch(() => {});
    return () => controller.abort();
  }, []);

  const isSaved = saved.some(
    (c) => c.regolith_wt === regolithWt && c.regolith_type === regolithType && c.polymer_type === polymerType && c.temperature === temperature,
  );
  const addToComparison = () => setSaved((list) => [...list, { ...composition, id: crypto.randomUUID() }]);

  const r2 = modelInfo && Object.values(modelInfo.holdout_metrics).map((m) => m.r2);

  return (
    <div className="app">
      <Navbar />

      <main className="container">
        <section className="intro">
          <p className="eyebrow">Biopolymer + regolith composites</p>
          <h1>Design a building material from moon dust, then see how it holds up.</h1>
          <p className="lede">
            Mix a polymer with lunar or Martian regolith, pick the temperature it has to survive, and a machine-learning model
            predicts strength, stiffness and heat tolerance in real time.
          </p>
        </section>

        <div className="workspace">
          <section className="card controls" aria-labelledby="controls-title">
            <div className="card-head">
              <h2 id="controls-title">Composition</h2>
            </div>

            <SegmentedControl
              label="Polymer matrix"
              value={polymerType}
              onChange={setPolymerType}
              options={Object.entries(POLYMERS).map(([value, p]) => ({ value, label: p.label, note: p.note }))}
            />
            <SegmentedControl
              label="Regolith"
              value={regolithType}
              onChange={setRegolithType}
              options={Object.entries(REGOLITHS).map(([value, r]) => ({ value, label: r.label }))}
            />
            <SliderControl label="Regolith content" value={regolithWt} onChange={setRegolithWt} min={0} max={50} unit="wt%" />
            <SliderControl label="Operating temperature" value={temperature} onChange={setTemperature} min={-180} max={150} unit="°C">
              <div className="presets" role="group" aria-label="Temperature presets">
                {TEMPERATURE_PRESETS.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    className={`chip-button ${temperature === p.value ? 'active' : ''}`}
                    aria-pressed={temperature === p.value}
                    onClick={() => setTemperature(p.value)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </SliderControl>

            <button type="button" className="button button-primary" onClick={addToComparison} disabled={isSaved || saved.length >= MAX_COMPARE}>
              {isSaved ? 'Saved to comparison' : saved.length >= MAX_COMPARE ? `Comparison full (${MAX_COMPARE})` : 'Add to comparison'}
            </button>
          </section>

          <div className="results">
            <Suspense fallback={<section className="card viewer-card" aria-busy="true"><div className="viewer" /></section>}>
              <ThreeDViewer regolithWt={regolithWt} regolithType={regolithType} polymerType={polymerType} />
            </Suspense>
            <PredictionCard {...prediction} regolithType={regolithType} polymerType={polymerType} />
          </div>
        </div>

        <ComparisonMode
          items={saved}
          onRemove={(id) => setSaved((list) => list.filter((c) => c.id !== id))}
          onClear={() => setSaved([])}
        />
      </main>

      <footer className="footer container">
        <p>
          <strong>About the model.</strong> Random Forest regressor
          {modelInfo && (
            <>
              {' '}
              trained on {modelInfo.training_rows.toLocaleString()} samples, hold-out R² {formatNumber(Math.min(...r2), 2)}–
              {formatNumber(Math.max(...r2), 2)}
            </>
          )}
          . The training set is synthetic and physics-informed (rule-of-mixtures style models with lab-like scatter); it is
          a prototype until it is calibrated against measured coupon data. Values are estimates, not design allowables.
        </p>
        <p>Team Dreams of X · NASA Space Apps Challenge 2026 · MIT License</p>
      </footer>
    </div>
  );
}
