import { useEffect, useMemo, useState } from 'react';
import { ExternalLink, FileText, FlaskConical, Search, Zap } from 'lucide-react';
import catalog from '../lib/catalog';
import snapshot from '../generated/ntrs_snapshot.json';
import { apiAvailable, searchNtrs } from '../lib/api';

const FINDINGS = [
  { text: 'PHB was processed with up to 80 wt% lunar or Martian simulant.', cite: 'NTRS 20260003641' },
  { text: 'With 20% LMS-1, PHB starts crystallising at 125 °C after 6.5 min, versus 45 °C after 14.5 min for neat PHB: regolith makes it easier to process.', cite: 'NTRS 20260007758' },
  { text: 'Injection-molded and printed PHB composites sat 24 h at 12 K in vacuum (Glenn LESTR) with no catastrophic failure.', cite: 'NTRS 20260007758' },
  { text: 'Iron-rich Martian simulants lower PHB’s decomposition temperature by 12–22 °C; lunar ones barely change it.', cite: 'NTRS 20260007758' },
  { text: 'Samples are flying on MISSE-23 and MISSE-24 for space exposure.', cite: 'NASA, Sep 2026' },
  { text: 'NASA lists “computational modeling to predict materials performance” as a next step. That is what this simulator does.', cite: 'NTRS 20260007758' },
];

function ResultItem({ r }) {
  return (
    <li className="ntrs-item">
      <a href={r.url} target="_blank" rel="noreferrer">
        {r.title}
        <ExternalLink size={13} aria-hidden="true" />
      </a>
      <p className="ntrs-meta">
        {[r.center, r.type, r.year].filter(Boolean).join(' · ')}
        {r.authors?.length > 0 && ` · ${r.authors.slice(0, 2).join(', ')}${r.authors.length > 2 ? ' et al.' : ''}`}
      </p>
      {r.abstract && <p className="ntrs-abstract">{r.abstract}</p>}
    </li>
  );
}

export default function ResearchPanel() {
  const [query, setQuery] = useState('');
  const [live, setLive] = useState({ available: false, results: null, status: 'idle' });

  useEffect(() => {
    const controller = new AbortController();
    apiAvailable(controller.signal).then((available) => setLive((s) => ({ ...s, available })));
    return () => controller.abort();
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return snapshot.results;
    return snapshot.results.filter((r) => `${r.title} ${r.abstract} ${r.center}`.toLowerCase().includes(q));
  }, [query]);

  const runLive = async (e) => {
    e.preventDefault();
    if (!live.available || query.trim().length < 2) return;
    setLive((s) => ({ ...s, status: 'loading' }));
    try {
      const data = await searchNtrs(query.trim());
      setLive((s) => ({ ...s, results: data.results, status: 'done' }));
    } catch {
      setLive((s) => ({ ...s, results: null, status: 'error' }));
    }
  };

  const shown = live.results ?? filtered;

  return (
    <div className="section-grid research">
      <div className="research-side">
        <div className="card">
          <div className="card-head compact">
            <h3>NASA sources we built on</h3>
          </div>
          <ul className="source-list">
            {catalog.sources.map((s) => (
              <li key={s.id}>
                <FileText size={16} aria-hidden="true" />
                <div>
                  <a href={s.url} target="_blank" rel="noreferrer">
                    {s.title}
                  </a>
                  <p className="ntrs-meta">
                    {s.kind} · {s.publisher} · {s.date}
                  </p>
                  <p className="source-use">{s.used_for}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <div className="card-head compact">
            <h3>
              <FlaskConical size={16} aria-hidden="true" /> What NASA has already shown
            </h3>
          </div>
          <ul className="findings">
            {FINDINGS.map((f) => (
              <li key={f.text}>
                {f.text} <cite>{f.cite}</cite>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card ntrs">
        <div className="card-head compact">
          <div>
            <h3>NASA Technical Reports Server</h3>
            <p className="card-sub">
              {live.results
                ? `${live.results.length} live results from ntrs.nasa.gov`
                : `${snapshot.results.length} related reports, snapshot of ${snapshot.fetched}`}
            </p>
          </div>
          {live.available && (
            <span className="chip chip-accent">
              <Zap size={12} aria-hidden="true" /> Live search on
            </span>
          )}
        </div>
        <form className="search" role="search" onSubmit={runLive}>
          <Search size={16} aria-hidden="true" />
          <input
            type="search"
            value={query}
            maxLength={100}
            placeholder={live.available ? 'Search NTRS, e.g. "regolith sintering"' : 'Filter reports, e.g. "PHB" or "Glenn"'}
            onChange={(e) => {
              setQuery(e.target.value);
              if (live.results) setLive((s) => ({ ...s, results: null, status: 'idle' }));
            }}
            aria-label="Search NASA reports"
          />
          {live.available && (
            <button type="submit" className="button button-small" disabled={query.trim().length < 2 || live.status === 'loading'}>
              {live.status === 'loading' ? 'Searching…' : 'Search live'}
            </button>
          )}
        </form>
        {live.status === 'error' && <p className="inline-error">NTRS didn’t answer. Showing the saved snapshot instead.</p>}
        {shown.length === 0 ? (
          <div className="empty-state slim">
            <p>No reports match “{query}”.</p>
            <small>Try a broader word like “regolith” or “polymer”.</small>
          </div>
        ) : (
          <ul className="ntrs-list">
            {shown.slice(0, 12).map((r) => (
              <ResultItem key={r.id} r={r} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
