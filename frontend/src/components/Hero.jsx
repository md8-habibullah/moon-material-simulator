import { ArrowRight, ExternalLink, Play } from 'lucide-react';
import catalog, { VIDEO_URL } from '../lib/catalog';

export default function Hero() {
  const article = catalog.sources.find((s) => s.id === 'nasa-glenn-2026');
  const r2 = Object.values(catalog.model.holdout_metrics).map((m) => m.r2);
  const stats = [
    { value: '8', label: 'properties predicted live' },
    { value: String(catalog.validation.length), label: 'NASA measurements checked' },
    { value: `≥ ${Math.min(...r2).toFixed(2)}`, label: 'hold-out R²' },
    { value: '0 kg', label: 'binder shipped, if grown on site' },
  ];

  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <a className="eyebrow-link" href={article.url} target="_blank" rel="noreferrer">
          <span className="dot" aria-hidden="true" />
          Built on NASA Glenn’s 2026 bacteria-grown bioplastic
          <ExternalLink size={13} aria-hidden="true" />
        </a>
        <h1>
          Design a building material from <span className="gradient-text">moon dust</span>, then see how it holds up.
        </h1>
        <p className="lede">
          Mix NASA’s bioplastic (or PLA, PEEK, LDPE) with lunar or Martian regolith. A Random Forest calibrated on NASA measurements
          predicts strength, stiffness, heat limits and more in real time, then finds the best mix for a wrench, a bracket or a wall
          panel.
        </p>
        <div className="hero-actions">
          <a href="#simulator" className="button button-primary">
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
