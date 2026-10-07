import { Factory, Filter, Mountain, Printer, Rocket, Sprout } from 'lucide-react';
import catalog from '../../lib/catalog';

export default function ProcessPipeline({ composition }) {
  const binder = catalog.binders[composition.binder];
  const regolith = catalog.regoliths[composition.regolith];
  const grown = binder.made_on_site;

  const steps = [
    { icon: Mountain, title: 'Collect regolith', detail: `${regolith.label} soil`, local: true },
    { icon: Filter, title: 'Sieve & dry', detail: `~${composition.particle_size} µm, dried at 204 °C`, local: true },
    grown
      ? { icon: Sprout, title: 'Grow bioplastic', detail: 'Bacteria turn CO₂ or crew waste into PHB', local: true }
      : { icon: Rocket, title: 'Ship binder', detail: `${binder.label} launched from Earth`, local: false },
    {
      icon: Factory,
      title: 'Compound & extrude',
      detail: `${composition.regolith_wt}% regolith${composition.fiber_wt ? ` + ${composition.fiber_wt}% fibre` : ''} into filament`,
      local: true,
    },
    { icon: Printer, title: 'Print the part', detail: grown ? 'Re-melt or bio-recycle at end of life' : 'Re-melt and reprint at end of life', local: true },
  ];

  // Re-keying on the mix replays the sweep animation whenever the design changes.
  const key = `${composition.binder}-${composition.regolith}-${composition.regolith_wt}-${composition.fiber_wt}-${composition.particle_size}`;

  return (
    <section className="card pipeline-card" aria-labelledby="pipeline-title">
      <div className="card-head compact">
        <h3 id="pipeline-title">On-site process</h3>
        <span className="muted-small">Moon or Mars, no resupply</span>
      </div>
      <ol className="pipeline" key={key}>
        {steps.map((s, i) => (
          <li key={s.title} className={s.local ? '' : 'earth'} style={{ '--i': i }}>
            <span className="pipeline-icon">
              <s.icon size={16} aria-hidden="true" />
            </span>
            <span className="pipeline-text">
              <strong>{s.title}</strong>
              <small>{s.detail}</small>
            </span>
            {!s.local && <span className="tag tag-warn">From Earth</span>}
          </li>
        ))}
      </ol>
    </section>
  );
}
