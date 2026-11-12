import { useEffect, useMemo, useRef } from 'react';
import { BadgeCheck, ExternalLink, FileSearch, LineChart, ScanLine, X } from 'lucide-react';
import points from '../../generated/evidence_points.json';
import catalog, { PROPERTY, formatValue, processOf } from '../../lib/catalog';
import { physicsFeatures } from '../../lib/engine/physics';
import { supportLevel } from '../../lib/engine/evidence';

const VERDICT = {
  CELL_MATCH: { label: 'Verified in table cell', icon: BadgeCheck, tone: 'ok' },
  ROW_MATCH: { label: 'Verified on table row', icon: BadgeCheck, tone: 'ok' },
  TEXT_MATCH: { label: 'Verified in text', icon: BadgeCheck, tone: 'ok' },
  SPLIT_MATCH: { label: 'Verified (split text)', icon: BadgeCheck, tone: 'ok' },
  PAGE_MATCH: { label: 'Found on page', icon: FileSearch, tone: 'info' },
  CHART_ESTIMATE: { label: 'Read from a chart', icon: LineChart, tone: 'info' },
  SCAN_VISUAL: { label: 'Scanned page, checked by eye', icon: ScanLine, tone: 'info' },
};

const SUPPORT_COPY = {
  measured: 'Real coupons of this binder, made this way, were tested near this loading.',
  related: 'This binder was tested near this loading, but made a different way.',
  physics: 'No lab data near this mix: the value comes from the physics model alone, so treat it as an estimate.',
};

function cite(sourceId) {
  const s = catalog.evidence_sources?.[sourceId];
  if (!s) return { short: sourceId, title: '', url: null };
  const first = (s.authors || '').split(/[.,;]/)[0].trim();
  const who = s.ntrs_id ? `NASA (NTRS ${s.ntrs_id})` : first ? `${first} et al.` : '';
  return { short: `${who} ${s.year}`.trim(), title: s.title, url: s.url, venue: s.venue, licence: s.licence };
}

function mixLabel(p) {
  const filler = p.filler && p.filler.toLowerCase() !== 'none' ? `${p.wt}% ${p.filler}` : 'neat (no regolith)';
  const process = catalog.processes[p.process]?.label.toLowerCase();
  return [p.binder, filler, process, p.orientation].filter(Boolean).join(' · ');
}

export default function EvidenceDrawer({ propertyKey, composition, result, onClose }) {
  const ref = useRef(null);
  const open = Boolean(propertyKey);
  const process = processOf(composition);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const { phi, list, counts } = useMemo(() => {
    if (!propertyKey) return { phi: 0, list: [], counts: {} };
    const f = physicsFeatures(catalog, composition);
    const phiNow = f.phi_regolith + f.phi_fiber;
    const rank = (p) => (p.binder === composition.binder ? (p.process === process ? 0 : 1) : 2);
    const forTarget = points.filter((p) => p.target === propertyKey);
    const sorted = [...forTarget].sort((a, b) => rank(a) - rank(b) || Math.abs(a.phi - phiNow) - Math.abs(b.phi - phiNow));
    return {
      phi: phiNow,
      list: sorted.slice(0, 14),
      counts: { total: forTarget.length, sources: new Set(forTarget.map((p) => p.source)).size },
    };
  }, [propertyKey, composition, process]);

  if (!propertyKey) return <dialog ref={ref} className="evidence-dialog" onClose={onClose} />;
  const prop = PROPERTY[propertyKey];
  const unit = catalog.units[propertyKey];
  const level = supportLevel(result.evidence?.[propertyKey] ?? { same: 0, binder: 0 });
  const summary = catalog.evidence?.[propertyKey];
  const base = import.meta.env.BASE_URL;

  return (
    <dialog ref={ref} className="evidence-dialog" onClose={onClose} aria-labelledby="evidence-title">
      <header className="evidence-head">
        <div>
          <p className="kicker">Evidence</p>
          <h2 id="evidence-title">{prop.label}: what labs actually measured</h2>
        </div>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Close evidence">
          <X size={16} />
        </button>
      </header>

      <div className="evidence-summary">
        <p>
          This mix predicts <strong>{formatValue(result.properties[propertyKey], propertyKey)} {unit}</strong> ± {formatValue(result.uncertainty[propertyKey], propertyKey)}{' '}
          at {composition.temperature} °C (filler {Math.round(phi * 100)}% by volume).
        </p>
        <p className={`support support-${level}`}>{SUPPORT_COPY[level]}</p>
        {summary?.validation?.new_mix && (
          <p className="muted-small">
            Tested on mixes it never saw ({summary.validation.new_mix.n} measurements): average error {Math.round(summary.validation.new_mix.hybrid_mape * 100)}% (physics alone:{' '}
            {Math.round(summary.validation.new_mix.physics_mape * 100)}%).
          </p>
        )}
        <p className="muted-small">
          {counts.total} measurements of {prop.label.toLowerCase()} from {counts.sources} studies. Closest to your mix first.
        </p>
      </div>

      {list.length === 0 ? (
        <p className="empty-state">No lab measurements of this property yet. It is a physics-model estimate.</p>
      ) : (
        <ol className="evidence-list">
          {list.map((p) => {
            const c = cite(p.source);
            const v = VERDICT[p.verdict] ?? { label: p.verdict ?? 'Unchecked', icon: FileSearch, tone: 'info' };
            const Icon = v.icon;
            const where = [`p. ${p.page}`, p.anchor, p.row && `row “${p.row}”`, p.col && `column “${p.col}”`].filter(Boolean).join(' · ');
            return (
              <li key={p.id} className="evidence-item">
                <div className="evidence-value">
                  <strong>
                    {formatValue(p.value, propertyKey)} <span className="unit">{unit}</span>
                  </strong>
                  {p.std != null && <small>± {formatValue(p.std, propertyKey)}</small>}
                </div>
                <div className="evidence-body">
                  <p className="evidence-mix">{mixLabel(p)}</p>
                  <p className="evidence-source">
                    {c.url ? (
                      <a href={c.url} target="_blank" rel="noreferrer" title={c.title}>
                        {c.short} <ExternalLink size={11} aria-hidden="true" />
                      </a>
                    ) : (
                      c.short
                    )}{' '}
                    <span className="muted-small">
                      {p.source} · {where}
                    </span>
                  </p>
                  <p className={`verdict verdict-${v.tone}`} title={p.audit ?? ''}>
                    <Icon size={12} aria-hidden="true" /> {v.label}
                    {p.extraction === 'chart_digitized' && p.confidence && <span className="muted-small"> · {p.confidence} confidence</span>}
                    {!p.used && <span className="muted-small"> · shown for context, not used in training</span>}
                  </p>
                  {p.img && (
                    <details className="evidence-crop">
                      <summary>Show it in the paper</summary>
                      <img src={`${base}evidence/${p.img}`} alt={`${c.short}, page ${p.page}: ${where}`} loading="lazy" />
                    </details>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
      <footer className="evidence-foot muted-small">
        Every number was re-found in its source PDF by our Evidence Auditor, which flags errors but never edits data. Green boxes show the
        exact cell or value; chart readings are approximate.
      </footer>
    </dialog>
  );
}
