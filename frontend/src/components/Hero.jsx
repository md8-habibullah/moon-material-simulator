import { ArrowRight, Play, Rocket } from 'lucide-react';
import catalog, { VIDEO_URL } from '../lib/catalog';

export default function Hero() {
  const evidence = Object.values(catalog.evidence ?? {});
  const measured = evidence.reduce((n, e) => n + e.n_train, 0);
  const studies = new Set(evidence.flatMap((e) => e.sources)).size;
  const stats = [
    { value: '8', label: 'properties predicted live' },
    { value: String(measured), label: 'lab measurements the model learns from' },
    { value: String(studies), label: 'studies, every value traced to its page' },
    { value: '0 kg', label: 'binder shipped, if grown on site' },
  ];

  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <a className="eyebrow-link" href="#stories">
          <span className="dot" aria-hidden="true" />
          NASA Space Apps 2026 · Abandoned but not Forgotten
        </a>
        <h1>
          What NASA left behind teaches us to build from <span className="gradient-text">moon dust</span>.
        </h1>
        <p className="lede">
          Eight NASA machines still sit on the Moon and Mars. Hear their stories and what those worlds did to their materials. Then mix
          NASA Glenn’s bacteria-grown bioplastic with lunar or Martian dust: a physics model, corrected by machine learning on real lab
          measurements, predicts strength, stiffness and heat limits, shows the lab data behind every number, and breaks your part on
          screen before anyone prints it.
        </p>
        <div className="hero-actions">
          <a href="#stories" className="button button-primary">
            <Rocket size={16} aria-hidden="true" /> Meet the machines
          </a>
          <a href="#simulator" className="button button-ghost">
            Start designing <ArrowRight size={16} aria-hidden="true" />
          </a>
          <a href={VIDEO_URL} className="button button-ghost" target="_blank" rel="noreferrer">
            <Play size={15} aria-hidden="true" /> Watch the 4-minute pitch
          </a>
        </div>
      </div>
      <dl className="hero-stats">
        {stats.map((s) => (
          <div key={s.label}>
            <dt>{s.label}</dt>
            <dd>{s.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
