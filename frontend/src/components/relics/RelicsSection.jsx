import { Suspense, lazy, useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, ExternalLink, FlaskConical, Hammer, Lightbulb, MousePointerClick } from 'lucide-react';
import { RELICS, WORLDS } from '../../lib/relics';
import { sound } from '../../lib/sound';

// three.js is heavy, so the globe loads on demand like the other 3D views.
const RelicGlobe = lazy(() => import('./RelicGlobe'));
const BASE = import.meta.env.BASE_URL;

const STORY = [
  { key: 'did', title: 'What it did' },
  { key: 'why', title: 'Why it is still there' },
  { key: 'science', title: 'What it taught us' },
];

export default function RelicsSection({ onTry }) {
  const [worldId, setWorldId] = useState('moon');
  const [selectedId, setSelectedId] = useState(RELICS[0].id);
  const [imageIndex, setImageIndex] = useState(0);

  const relics = useMemo(() => RELICS.filter((r) => r.world === worldId), [worldId]);
  const relic = RELICS.find((r) => r.id === selectedId);
  const order = RELICS.findIndex((r) => r.id === selectedId);
  const image = relic.images[Math.min(imageIndex, relic.images.length - 1)];

  const select = (id) => {
    if (id === selectedId) return;
    const next = RELICS.find((r) => r.id === id);
    setSelectedId(id);
    setImageIndex(0);
    if (next.world !== worldId) setWorldId(next.world);
    sound.blip(next.world === 'mars' ? 520 : 760);
  };
  const step = (d) => select(RELICS[(order + d + RELICS.length) % RELICS.length].id);
  const switchWorld = (id) => {
    if (id === worldId) return;
    setWorldId(id);
    select(RELICS.find((r) => r.world === id).id);
  };

  return (
    <div className="relics">
      <div className="card relics-explorer">
        <div className="relics-top">
          <div className="seg" role="radiogroup" aria-label="World">
            {Object.entries(WORLDS).map(([id, w]) => (
              <button key={id} type="button" role="radio" aria-checked={worldId === id} className={worldId === id ? 'active' : ''} onClick={() => switchWorld(id)}>
                {w.label} <small>{RELICS.filter((r) => r.world === id).length} machines</small>
              </button>
            ))}
          </div>
          <span className="relics-hint">
            <MousePointerClick size={14} aria-hidden="true" /> Drag to spin · tap a light
          </span>
        </div>

        <Suspense fallback={<div className="relic-globe skeleton" aria-busy="true" />}>
          <RelicGlobe world={worldId} relics={relics} selectedId={selectedId} onSelect={select} label={relic.name} />
        </Suspense>
        <p className="relic-map-credit">
          Map: NASA ({worldId === 'moon' ? 'Lunar Reconnaissance Orbiter, SVS CGI Moon Kit' : 'NASA 3D Resources'}). Lights mark where each machine still sits.
        </p>

        <ol className="relic-list" aria-label={`Machines left on the ${WORLDS[worldId].label}`}>
          {relics.map((r) => (
            <li key={r.id}>
              <button type="button" className={r.id === selectedId ? 'active' : ''} aria-current={r.id === selectedId ? 'true' : undefined} onClick={() => select(r.id)}>
                <strong>{r.name}</strong>
                <small>
                  {r.year} · {r.place}
                </small>
              </button>
            </li>
          ))}
        </ol>
      </div>

      <article className="card relic-story" aria-live="polite" aria-labelledby="relic-title">
        <figure className="relic-photo">
          <img key={image.src} src={`${BASE}${image.src}`} alt={image.alt} loading="lazy" className={image.fit === 'contain' ? 'fit-contain' : undefined} style={image.position ? { objectPosition: image.position } : undefined} />
          <figcaption>
            <a href={image.link} target="_blank" rel="noreferrer">
              Photo: {image.credit} <ExternalLink size={11} aria-hidden="true" />
            </a>
          </figcaption>
          {relic.images.length > 1 && (
            <div className="relic-thumbs" role="group" aria-label="Photos">
              {relic.images.map((im, i) => (
                <button key={im.src} type="button" aria-pressed={i === imageIndex} aria-label={`Photo ${i + 1}: ${im.alt}`} onClick={() => setImageIndex(i)}>
                  <img src={`${BASE}${im.src}`} alt="" />
                </button>
              ))}
            </div>
          )}
        </figure>

        <div className="relic-body">
          <p className="kicker">
            {relic.kind} · {WORLDS[relic.world].label} · {relic.year}
          </p>
          <h3 id="relic-title">{relic.name}</h3>
          <p className="relic-place">{relic.place}</p>

          {STORY.map((s) => (
            <section key={s.key} className="relic-beat">
              <h4>{s.title}</h4>
              <p>{relic[s.key]}</p>
            </section>
          ))}

          <section className="relic-lesson">
            <h4>
              <FlaskConical size={15} aria-hidden="true" /> The materials lesson
            </h4>
            <p>{relic.lesson}</p>
          </section>

          <p className="relic-fact">
            <Lightbulb size={15} aria-hidden="true" />
            <span>
              <b>Fun fact:</b> {relic.fact}
            </span>
          </p>

          <button type="button" className="button button-primary relic-try" onClick={() => onTry(relic)}>
            <Hammer size={16} aria-hidden="true" /> Try it: {relic.tryIt.label}
          </button>

          <div className="relic-foot">
            <span className="relic-sources">
              Sources:{' '}
              {relic.sources.map((s, i) => (
                <span key={s.url}>
                  {i > 0 && ' · '}
                  <a href={s.url} target="_blank" rel="noreferrer">
                    {s.label}
                  </a>
                </span>
              ))}
            </span>
            <span className="relic-nav">
              <button type="button" className="icon-button" onClick={() => step(-1)} aria-label="Previous machine">
                <ArrowLeft size={16} aria-hidden="true" />
              </button>
              <span>
                {order + 1} / {RELICS.length}
              </span>
              <button type="button" className="icon-button" onClick={() => step(1)} aria-label="Next machine">
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            </span>
          </div>
        </div>
      </article>
    </div>
  );
}
