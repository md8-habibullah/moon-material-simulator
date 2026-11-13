import { Component, useEffect, useMemo, useState } from 'react';
import { RotateCcw } from 'lucide-react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ControlsPanel from './components/simulator/ControlsPanel';
import VisualPanel from './components/simulator/VisualPanel';
import OutputPanel from './components/simulator/OutputPanel';
import ProcessPipeline from './components/simulator/ProcessPipeline';
import Optimizer from './components/Optimizer';
import ComparisonMode, { MAX_COMPARE } from './components/ComparisonMode';
import MissionImpact from './components/MissionImpact';
import ModelInsight from './components/ModelInsight';
import ResearchPanel from './components/ResearchPanel';
import RelicsSection from './components/relics/RelicsSection';
import Footer from './components/Footer';
import { ACCENT_BY_REGOLITH, DEFAULT_COMPOSITION } from './lib/catalog';
import { ENVIRONMENTS } from './lib/engine/parts';
import { useEngine } from './lib/engine/load';
import { useThemePreference } from './lib/theme';
import { readComposition, writeComposition } from './lib/url-state';
import './lib/charts';

const sameMix = (a, b) => ['binder', 'process', 'regolith', 'regolith_wt', 'fiber_wt', 'particle_size', 'temperature'].every((k) => a[k] === b[k]);

// If one section hits a bug, show a small notice there instead of blanking the whole page.
class SectionBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Section crashed:', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="card empty-state" role="alert">
        <p>This part of the page hit a problem.</p>
        <small>The rest of the simulator still works.</small>
        <button type="button" className="button button-ghost button-small" onClick={() => this.setState({ error: null })}>
          <RotateCcw size={14} aria-hidden="true" /> Try again
        </button>
      </div>
    );
  }
}

function Section({ id, kicker, title, lede, children }) {
  return (
    <section id={id} className="section" aria-labelledby={`${id}-title`}>
      <header className="section-head">
        <p className="kicker">{kicker}</p>
        <h2 id={`${id}-title`}>{title}</h2>
        {lede && <p className="section-lede">{lede}</p>}
      </header>
      <SectionBoundary>{children}</SectionBoundary>
    </section>
  );
}

function EngineGate({ engine, error, retry, children }) {
  if (error) {
    return (
      <div className="card empty-state" role="alert">
        <p>The prediction model didn’t load.</p>
        <small>{error.message}. Check your connection and try again.</small>
        <button type="button" className="button button-ghost button-small" onClick={retry}>
          <RotateCcw size={14} aria-hidden="true" /> Retry
        </button>
      </div>
    );
  }
  if (!engine) {
    return (
      <div className="simulator-grid" aria-busy="true" aria-label="Loading the model">
        <div className="card skeleton tall-skeleton" />
        <div className="card skeleton tall-skeleton" />
        <div className="card skeleton tall-skeleton" />
      </div>
    );
  }
  return children(engine);
}

export default function App() {
  const [theme, setTheme] = useThemePreference();
  const { engine, error, retry } = useEngine();
  const [composition, setComposition] = useState(readComposition);
  const [saved, setSaved] = useState([]);
  // A story's "Try it" button opens the part test with that machine's part, place and local dust.
  const [partRequest, setPartRequest] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => writeComposition(composition), 250);
    return () => clearTimeout(timer);
  }, [composition]);

  // The accent colour follows the selected soil: silver-blue highlands, teal mare, rust Mars.
  useEffect(() => {
    document.documentElement.dataset.accent = ACCENT_BY_REGOLITH[composition.regolith];
  }, [composition.regolith]);

  const result = useMemo(() => engine?.predict(composition), [engine, composition]);
  const baseline = useMemo(() => engine?.predict({ ...composition, regolith_wt: 0, fiber_wt: 0 }), [engine, composition]);

  const isSaved = saved.some((c) => sameMix(c, composition));
  const full = saved.length >= MAX_COMPARE;
  const save = () => setSaved((list) => [...list, { ...composition, id: crypto.randomUUID() }]);
  const load = (c) => {
    const { id: _id, ...mix } = c;
    setComposition(mix);
    document.getElementById('simulator')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const tryRelic = (relic) => {
    const { part, env, regolith } = relic.tryIt;
    const temperature = ENVIRONMENTS.find((e) => e.id === env).temperature;
    setComposition({ ...DEFAULT_COMPOSITION, regolith, temperature });
    setPartRequest({ part, env, from: relic.name, n: Date.now() });
  };

  return (
    <>
      <a className="skip-link" href="#simulator">
        Skip to the simulator
      </a>
      <Navbar theme={theme} onTheme={setTheme} />
      <main className="container">
        <Hero />

        <Section
          id="stories"
          kicker="NASA Space Apps 2026 · Abandoned but not Forgotten"
          title="The machines NASA left behind"
          lede="Eight machines still sit where they stopped, on the Moon and on Mars. Each one is a materials experiment that never ended. Spin the globe, pick a machine, hear its story, then try to rebuild its parts from local dust."
        >
          <RelicsSection onTry={tryRelic} />
        </Section>

        <Section id="simulator" kicker="Design · Test" title="Simulator" lede="Every change re-runs the model instantly, right in your browser.">
          <EngineGate engine={engine} error={error} retry={retry}>
            {(eng) => (
              <div className="simulator-grid">
                <ControlsPanel
                  composition={composition}
                  onChange={setComposition}
                  onSave={save}
                  canSave={!isSaved && !full}
                  saveLabel={isSaved ? 'Saved' : full ? `Compare is full (${MAX_COMPARE})` : 'Save to compare'}
                />
                <div className="center-column">
                  <VisualPanel engine={eng} composition={composition} request={partRequest} />
                  <ProcessPipeline composition={composition} />
                </div>
                <OutputPanel engine={eng} composition={composition} result={result} baseline={baseline} />
              </div>
            )}
          </EngineGate>
        </Section>

        <Section
          id="optimize"
          kicker="Optimize"
          title="Find the best mix for the job"
          lede="Pick a use. The optimizer tests about 5,000 compositions (every binder, with each way of making it that has lab data) against its requirements and ranks the ones that pass, most locally sourced first."
        >
          <EngineGate engine={engine} error={error} retry={retry}>
            {(eng) => <Optimizer engine={eng} onApply={load} />}
          </EngineGate>
        </Section>

        <Section id="compare" kicker="Compare" title="Formulas side by side" lede="For mission planners: save up to four mixes and see which one wins each property.">
          <EngineGate engine={engine} error={error} retry={retry}>
            {(eng) => (
              <ComparisonMode engine={eng} items={saved} onRemove={(id) => setSaved((l) => l.filter((c) => c.id !== id))} onClear={() => setSaved([])} onLoad={load} />
            )}
          </EngineGate>
        </Section>

        <Section id="impact" kicker="Mission impact" title="What printing on site saves" lede="Launch mass and cost avoided by making parts from local regolith instead of shipping spares.">
          <MissionImpact composition={composition} />
        </Section>

        <Section
          id="science"
          kicker="Under the hood"
          title="How the model works, and how well"
          lede="A hybrid of machine learning and physics, calibrated on NASA Glenn and NASA Kennedy measurements."
        >
          <ModelInsight />
        </Section>

        <Section id="research" kicker="NASA open data" title="The research behind it" lede="Every NASA source we used, plus a searchable index of related NASA technical reports.">
          <ResearchPanel />
        </Section>
      </main>
      <Footer />
    </>
  );
}
