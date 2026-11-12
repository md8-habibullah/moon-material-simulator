import { ArrowRight, ExternalLink, Play } from 'lucide-react';
import catalog, { VIDEO_URL } from '../lib/catalog';

export default function Hero() {
  const article = catalog.sources.find((s) => s.id === 'nasa-glenn-2026');
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
        <a className="eyebrow-link" href={article.url} target="_blank" rel="noreferrer">
          <span className="dot" aria-hidden="true" />
          Built on NASA Glenn’s 2026 bacteria-grown bioplastic
          <ExternalLink size={13} aria-hidden="true" />
        </a>
        <h1>
          Design a building material from <span className="gradient-text">moon dust</span>, then see how it holds up.
        </h1>
        <p className="lede">
          Mix NASA’s bioplastic (or PLA, PEEK, LDPE, PEI, PPSU) with lunar or Martian regolith and choose how to make it. A physics
          model, corrected by machine learning on real lab measurements, predicts strength, stiffness, heat limits and more in real time,
          shows the lab data behind every number, then finds the best mix for a wrench, a bracket or a wall panel.
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
