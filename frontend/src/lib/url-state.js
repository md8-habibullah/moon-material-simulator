// Keep the current mix in the URL so a design can be shared as a link.
import catalog, { DEFAULT_COMPOSITION, maxFiberFor } from './catalog.js';

const PARAMS = { b: 'binder', r: 'regolith', w: 'regolith_wt', f: 'fiber_wt', d: 'particle_size', t: 'temperature' };

const clamp = (value, [lo, hi]) => Math.min(hi, Math.max(lo, value));

export function readComposition() {
  const params = new URLSearchParams(window.location.search);
  const c = { ...DEFAULT_COMPOSITION };
  if (catalog.binders[params.get('b')]) c.binder = params.get('b');
  if (catalog.regoliths[params.get('r')]) c.regolith = params.get('r');
  for (const [short, key] of Object.entries(PARAMS)) {
    if (key === 'binder' || key === 'regolith') continue;
    const n = Number(params.get(short));
    if (params.has(short) && Number.isFinite(n)) c[key] = clamp(Math.round(n), catalog.ranges[key]);
  }
  c.fiber_wt = Math.min(c.fiber_wt, maxFiberFor(c.regolith_wt));
  return c;
}

export function compositionUrl(c) {
  const params = new URLSearchParams(Object.entries(PARAMS).map(([short, key]) => [short, String(c[key])]));
  return `${window.location.origin}${window.location.pathname}?${params}`;
}

export function writeComposition(c) {
  const params = new URLSearchParams(Object.entries(PARAMS).map(([short, key]) => [short, String(c[key])]));
  window.history.replaceState(null, '', `${window.location.pathname}?${params}${window.location.hash}`);
}
